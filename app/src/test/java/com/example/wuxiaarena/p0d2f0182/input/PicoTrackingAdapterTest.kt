package com.example.wuxiaarena.p0d2f0182.input

import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.TrackingControlOverflowException
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.TrackingTarget
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import com.pico.spatial.tracking.DataProvider
import com.pico.spatial.tracking.controller.ControllerPose
import com.pico.spatial.tracking.controller.ControllerTrackingData
import com.pico.spatial.tracking.hmd.HMDPose
import com.pico.spatial.tracking.hmd.HMDTrackingData
import java.util.concurrent.CountDownLatch
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Test

class PicoTrackingAdapterTest {
    private class FakeProvider<T : Any> : DataProvider<T> {
        @Volatile private var currentState = DataProvider.State.CREATED
        @Volatile var failStateReadOnce = false
        override var state: DataProvider.State
            get() {
                if (failStateReadOnce) {
                    failStateReadOnce = false
                    throw IllegalStateException("state unavailable")
                }
                return currentState
            }
            set(value) { currentState = value }
        @Volatile override var supportState = DataProvider.SupportState.SUPPORTED
        override val dataFlow: SharedFlow<T> = MutableSharedFlow()
        override val latestData: T get() = error("latestData must not be polled")
        val listeners = CopyOnWriteArrayList<DataProvider.DataListener<T>>()
        var result = DataProvider.StartResult.SUCCESS
        var starts = 0
        var stops = 0
        var failRemoveOnce = false
        var failStartOnce = false
        var emitOnStart: T? = null

        override fun start(): DataProvider.StartResult {
            starts++
            if (failStartOnce) {
                failStartOnce = false
                throw IllegalStateException("start failed")
            }
            state = if (result == DataProvider.StartResult.SUCCESS) DataProvider.State.STARTED else DataProvider.State.PENDING
            emitOnStart?.let(::emit)
            return result
        }

        override fun stop() {
            stops++
            state = DataProvider.State.STOPPED
        }

        override fun addListener(listener: DataProvider.DataListener<T>) {
            listeners.add(listener)
        }

        override fun removeListener(listener: DataProvider.DataListener<T>) {
            if (failRemoveOnce) {
                failRemoveOnce = false
                throw IllegalStateException("remove failed")
            }
            listeners.remove(listener)
        }

        fun emit(value: T) = listeners.forEach { it.onProvideData(value) }
    }

    private fun head(rotation: Quat = Quat.identity()) = HMDTrackingData(HMDPose(Vector3(0f, 1.6f, 0f), rotation), 0L)
    private fun controller(x: Float) = ControllerPose(Vector3(x, 1.2f, -0.4f), Quat.identity())
    private fun hands(left: ControllerPose? = controller(-0.2f), right: ControllerPose? = controller(0.2f)) =
        ControllerTrackingData(left, right, 0L)

    @Test
    fun callbacksDeliverIndependentPosesWithoutClaimingHardwareQuality() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        adapter.start()
        assertEquals(1, hmd.starts)
        assertEquals(1, controllers.starts)

        val state = TrackingState(Hand.RIGHT)
        buffer.drain().events.forEach(state::accept)
        hmd.emit(head())
        controllers.emit(hands())
        buffer.drain().events.forEach(state::accept)
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(TrackingQuality.UNKNOWN, state.snapshot.right?.pose?.quality)
        val rightRevision = state.snapshot.rightContinuity

        controllers.emit(hands(left = null))
        val events = buffer.drain().events
        assertEquals(TrackingTarget.LEFT_HAND, (events.first() as TrackingEvent.Discontinuity).target)
        events.forEach(state::accept)
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(rightRevision, state.snapshot.rightContinuity)
        adapter.stop()
    }

    @Test
    fun emulatorPreviewPairsDesktopHeadAndHandsAndIgnoresRealControllers() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers, emulatorPreview = true)
        val state = TrackingState(Hand.RIGHT)
        adapter.start()
        assertEquals(1, controllers.starts)
        assertTrue(controllers.listeners.isEmpty())
        buffer.drain().events.forEach(state::accept)

        controllers.emit(hands(left = controller(-9f), right = controller(9f)))
        assertTrue(buffer.drain().events.isEmpty())
        assertFalse(state.snapshot.hasRequiredObservations)

        hmd.emit(head())
        adapter.pollDesktopPreview(1L)
        val pair = buffer.drain().events
        assertEquals(2, pair.size)
        val headEvent = pair[0] as TrackingEvent.Head
        val handEvent = pair[1] as TrackingEvent.Controllers
        assertEquals(InputOrigin.DESKTOP, headEvent.stamp.origin)
        assertEquals(InputOrigin.DESKTOP, handEvent.stamp.origin)
        assertEquals(headEvent.stamp.sequence + 1, handEvent.stamp.sequence)
        assertEquals(headEvent.stamp.coordinateEpoch, handEvent.stamp.coordinateEpoch)
        assertEquals(TrackingQuality.UNKNOWN, requireNotNull(headEvent.pose).quality)
        assertEquals(TrackingQuality.UNKNOWN, requireNotNull(handEvent.left).quality)
        assertEquals(TrackingQuality.UNKNOWN, requireNotNull(handEvent.right).quality)

        assertTrue(state.accept(headEvent))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertTrue(state.accept(handEvent))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(headEvent.stamp, state.snapshot.head?.stamp)
        assertEquals(handEvent.stamp, state.snapshot.left?.stamp)
        assertEquals(handEvent.stamp, state.snapshot.right?.stamp)

        controllers.emit(hands())
        assertTrue(buffer.drain().events.isEmpty())
        adapter.stop()
        assertEquals(1, controllers.stops)
    }

    @Test
    fun emulatorPreviewLossClearsThePairAndRecoveryRequiresNewObservations() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers, emulatorPreview = true)
        val state = TrackingState(Hand.RIGHT)
        val sample = head()
        adapter.start()
        buffer.drain().events.forEach(state::accept)
        hmd.emit(sample)
        adapter.pollDesktopPreview(1L)
        val oldPair = buffer.drain().events
        assertEquals(2, oldPair.size)
        oldPair.forEach { assertTrue(state.accept(it)) }
        assertTrue(state.snapshot.hasRequiredObservations)
        val beforeLoss = state.snapshot

        hmd.state = DataProvider.State.PENDING
        hmd.supportState = DataProvider.SupportState.DEVICE_NOT_SUPPORTED
        adapter.pollAvailability()
        adapter.pollAvailability()
        val loss = buffer.drain().events.single() as TrackingEvent.Discontinuity
        assertEquals(InputOrigin.DESKTOP, loss.stamp.origin)
        assertEquals(TrackingTarget.ALL, loss.target)
        assertEquals(DiscontinuityReason.PROVIDER_UNAVAILABLE, loss.reason)
        assertTrue(state.accept(loss))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertNull(state.snapshot.head)
        assertNull(state.snapshot.left)
        assertNull(state.snapshot.right)
        assertEquals(beforeLoss.headContinuity + 1, state.snapshot.headContinuity)
        assertEquals(beforeLoss.leftContinuity + 1, state.snapshot.leftContinuity)
        assertEquals(beforeLoss.rightContinuity + 1, state.snapshot.rightContinuity)

        hmd.emit(sample)
        controllers.emit(hands())
        assertTrue(buffer.drain().events.isEmpty())
        assertFalse(state.snapshot.hasRequiredObservations)

        hmd.state = DataProvider.State.STARTED
        hmd.supportState = DataProvider.SupportState.SUPPORTED
        adapter.pollAvailability()
        assertTrue(buffer.drain().events.isEmpty())
        assertFalse(state.snapshot.hasRequiredObservations)
        oldPair.forEach {
            assertFalse(state.accept(it))
            assertFalse(state.snapshot.hasRequiredObservations)
        }
        val beforeRecovery = state.snapshot

        hmd.emit(sample)
        adapter.pollDesktopPreview(2L)
        val newPair = buffer.drain().events
        assertEquals(2, newPair.size)
        assertTrue(newPair.first().stamp.sequence > loss.stamp.sequence)
        assertEquals(loss.stamp.coordinateEpoch, newPair.first().stamp.coordinateEpoch)
        assertTrue(state.accept(newPair[0]))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertTrue(state.accept(newPair[1]))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(newPair[0].stamp, state.snapshot.head?.stamp)
        assertEquals(newPair[1].stamp, state.snapshot.left?.stamp)
        assertEquals(newPair[1].stamp, state.snapshot.right?.stamp)
        assertEquals(beforeRecovery.headContinuity, state.snapshot.headContinuity)
        assertEquals(beforeRecovery.leftContinuity, state.snapshot.leftContinuity)
        assertEquals(beforeRecovery.rightContinuity, state.snapshot.rightContinuity)
        adapter.stop()
    }

    @Test
    fun pendingPreviewControllerStartStillKeepsOnlyHmdDerivedPoses() {
        val clock = AtomicLong(0L)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>().apply { result = DataProvider.StartResult.PENDING }
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers, emulatorPreview = true)
        try {
            adapter.start()
            assertEquals(DataProvider.StartResult.PENDING, adapter.lastControllerStartResult)
            assertEquals(1, controllers.starts)
            assertTrue(controllers.listeners.isEmpty())
            buffer.drain()
            hmd.emit(head())
            adapter.pollDesktopPreview(1L)
            val poses = buffer.drain().events
            assertEquals(2, poses.size)
            assertTrue(poses.all { it.stamp.origin == InputOrigin.DESKTOP })
            controllers.emit(hands())
            assertTrue(buffer.drain().events.isEmpty())
        } finally {
            adapter.stop()
        }
        assertEquals(1, controllers.stops)
    }

    @Test
    fun unchangedCallbacksRemainDistinctApplicationObservations() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val sample = head()
        hmd.emit(sample)
        hmd.emit(sample)
        val events = buffer.drain().events.filterIsInstance<TrackingEvent.Head>()
        assertEquals(2, events.size)
        assertTrue(events[0].stamp.receivedAtNanos < events[1].stamp.receivedAtNanos)
        assertEquals(TrackingQuality.UNKNOWN, events[1].pose?.quality)
        adapter.stop()
    }

    @Test
    fun concurrentHeadAndControllerCallbacksShareOneObservationOrder() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(256) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val headSample = head()
        val handSample = hands()
        val begin = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(2)
        try {
            val headTask = pool.submit {
                begin.await()
                repeat(100) { hmd.emit(headSample) }
            }
            val handTask = pool.submit {
                begin.await()
                repeat(100) { controllers.emit(handSample) }
            }
            begin.countDown()
            headTask.get(10, TimeUnit.SECONDS)
            handTask.get(10, TimeUnit.SECONDS)
        } finally {
            pool.shutdownNow()
        }
        val batch = buffer.drain()
        assertEquals(0, batch.droppedEvents)
        assertEquals(100, batch.events.count { it is TrackingEvent.Head })
        assertEquals(100, batch.events.count { it is TrackingEvent.Controllers })
        assertEquals((0L until 200L).toList(), batch.events.map { it.stamp.sequence })
        adapter.stop()
    }

    @Test
    fun pendingProviderDoesNotPublishUntilAvailableAndANewCallbackArrives() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>().apply {
            result = DataProvider.StartResult.PENDING
            supportState = DataProvider.SupportState.NOT_IN_FULL_SPACE
        }
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val initial = buffer.drain().events
        assertTrue(initial.filterIsInstance<TrackingEvent.Discontinuity>().any { it.reason == DiscontinuityReason.NOT_IN_FULL_SPACE })
        hmd.emit(head())
        assertTrue(buffer.drain().events.isEmpty())

        hmd.state = DataProvider.State.STARTED
        hmd.supportState = DataProvider.SupportState.SUPPORTED
        adapter.pollAvailability()
        assertTrue(buffer.drain().events.isEmpty())
        hmd.emit(head())
        assertTrue(buffer.drain().events.single() is TrackingEvent.Head)
        adapter.stop()
    }

    @Test
    fun stoppedOrOldGenerationCallbacksCannotEnterANewSession() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val old = hmd.listeners.single()
        buffer.drain()
        adapter.stop()
        assertEquals(DiscontinuityReason.APP_PAUSED, (buffer.drain().events.single() as TrackingEvent.Discontinuity).reason)
        old.onProvideData(head())
        assertTrue(buffer.drain().events.isEmpty())

        adapter.start()
        buffer.drain()
        old.onProvideData(head())
        assertTrue(buffer.drain().events.isEmpty())
        hmd.emit(head())
        assertTrue(buffer.drain().events.single() is TrackingEvent.Head)
        adapter.stop()
    }

    @Test
    fun recenterAndRestartRejectCallbacksFromThePreviousCoordinateEpoch() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val old = hmd.listeners.single()
        hmd.emit(head())
        buffer.drain()
        adapter.stop(DiscontinuityReason.RECENTERED)
        val marker = buffer.drain().events.single() as TrackingEvent.Discontinuity
        assertEquals(DiscontinuityReason.RECENTERED, marker.reason)
        assertEquals(1, marker.stamp.coordinateEpoch)
        adapter.start()
        old.onProvideData(head())
        assertTrue(buffer.drain().events.isEmpty())
        hmd.emit(head())
        assertEquals(1, buffer.drain().events.single().stamp.coordinateEpoch)
        adapter.stop()
    }

    @Test
    fun providerLossIsObservedOnceAndRecoveryNeedsANewCallback() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        val state = TrackingState(Hand.RIGHT)
        adapter.start()
        buffer.drain().events.forEach(state::accept)
        hmd.emit(head())
        controllers.emit(hands())
        buffer.drain().events.forEach(state::accept)
        assertTrue(state.snapshot.hasRequiredObservations)

        hmd.state = DataProvider.State.PENDING
        hmd.supportState = DataProvider.SupportState.DEVICE_NOT_SUPPORTED
        adapter.pollAvailability()
        adapter.pollAvailability()
        val loss = buffer.drain().events
        assertEquals(1, loss.size)
        assertEquals(TrackingTarget.HEAD, (loss.single() as TrackingEvent.Discontinuity).target)
        loss.forEach(state::accept)
        assertFalse(state.snapshot.hasRequiredObservations)
        hmd.state = DataProvider.State.STARTED
        hmd.supportState = DataProvider.SupportState.SUPPORTED
        adapter.pollAvailability()
        assertTrue(buffer.drain().events.isEmpty())
        assertFalse(state.snapshot.hasRequiredObservations)
        hmd.emit(head())
        buffer.drain().events.forEach(state::accept)
        assertFalse(state.snapshot.hasRequiredObservations)
        controllers.emit(hands())
        buffer.drain().events.forEach(state::accept)
        assertTrue(state.snapshot.hasRequiredObservations)
        adapter.stop()
    }

    @Test
    fun statusReadFailureInvalidatesTheSourceAndRemainsObservable() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        hmd.emit(head())
        buffer.drain()
        hmd.failStateReadOnce = true
        hmd.emit(head())
        assertTrue(buffer.drain().events.single() is TrackingEvent.Head)
        adapter.pollAvailability()
        val event = buffer.drain().events.single() as TrackingEvent.Discontinuity
        assertEquals(TrackingTarget.HEAD, event.target)
        assertEquals(DiscontinuityReason.PROVIDER_UNAVAILABLE, event.reason)
        assertEquals(TrackingTarget.HEAD, adapter.lastProviderFailure?.target)
        assertEquals("state unavailable", adapter.lastProviderFailure?.cause?.message)
        adapter.stop()
    }

    @Test
    fun racingCallbacksCannotAppearAfterThePauseMarker() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1_000) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val old = hmd.listeners.single()
        val sample = head()
        buffer.drain()
        old.onProvideData(sample)
        val begin = CountDownLatch(1)
        val pool = Executors.newSingleThreadExecutor()
        try {
            val task = pool.submit {
                begin.await()
                repeat(400) { old.onProvideData(sample) }
            }
            begin.countDown()
            adapter.stop()
            task.get(10, TimeUnit.SECONDS)
        } finally {
            pool.shutdownNow()
        }
        val events = buffer.drain().events
        val pause = events.indexOfLast { it is TrackingEvent.Discontinuity && it.reason == DiscontinuityReason.APP_PAUSED }
        assertTrue(pause >= 0)
        assertTrue(events.first() is TrackingEvent.Head)
        assertTrue(events.drop(pause + 1).none { it is TrackingEvent.Head })
    }

    @Test
    fun callbacksBeforeInitialAvailabilityProduceAnExplicitGap() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        hmd.emitOnStart = head()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val gap = buffer.drain().events.single() as TrackingEvent.Discontinuity
        assertEquals(TrackingTarget.HEAD, gap.target)
        assertEquals(DiscontinuityReason.QUEUE_GAP, gap.reason)
        hmd.emit(head())
        assertTrue(buffer.drain().events.single() is TrackingEvent.Head)
        adapter.stop()
    }

    @Test
    fun dominantHandLossExplicitlyInvalidatesTheRequiredObservation() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        val state = TrackingState(Hand.RIGHT)
        buffer.drain().events.forEach(state::accept)
        hmd.emit(head())
        controllers.emit(hands())
        buffer.drain().events.forEach(state::accept)
        assertTrue(state.snapshot.hasRequiredObservations)
        controllers.emit(hands(right = null))
        val events = buffer.drain().events
        assertEquals(TrackingTarget.RIGHT_HAND, (events.first() as TrackingEvent.Discontinuity).target)
        events.forEach(state::accept)
        assertFalse(state.snapshot.hasRequiredObservations)
        adapter.stop()
    }

    @Test
    fun cleanupContinuesAfterFailureAndCanBeRetried() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        controllers.failRemoveOnce = true
        assertThrows(IllegalStateException::class.java) { adapter.stop() }
        assertEquals(1, hmd.stops)
        assertEquals(1, controllers.stops)
        assertFalse(controllers.listeners.isEmpty())
        adapter.stop()
        assertTrue(controllers.listeners.isEmpty())
        assertEquals(1, controllers.stops)
    }

    @Test
    fun controlOverflowInACallbackBlocksSamplesUntilRecoveryWithGap() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        controllers.emit(hands())
        controllers.emit(hands())
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        controllers.emit(hands(right = null))
        assertTrue(adapter.lastProviderFailure?.cause is TrackingControlOverflowException)
        assertEquals(TrackingTarget.RIGHT_HAND, adapter.lastProviderFailure?.target)
        assertFalse(adapter.recoverControlOverflow())
        hmd.emit(head())
        assertEquals(1, adapter.droppedCallbacksDuringControlFault)
        val first = buffer.drain().events
        assertTrue(first.none { it is TrackingEvent.Head })
        assertEquals(DiscontinuityReason.ROUND_RESET, (first[1] as TrackingEvent.Discontinuity).reason)

        assertTrue(adapter.recoverControlOverflow())
        val recovery = buffer.drain().events.filterIsInstance<TrackingEvent.Discontinuity>()
        assertTrue(recovery.any { it.reason == DiscontinuityReason.QUEUE_GAP })
        adapter.pollAvailability()
        hmd.emit(head())
        assertTrue(buffer.drain().events.single() is TrackingEvent.Head)
        adapter.stop()
    }

    @Test
    fun providerRecoveryCannotBypassAnEarlierRejectedExternalControl() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        controllers.emit(hands())
        controllers.emit(hands())
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        assertThrows(TrackingControlOverflowException::class.java) {
            buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        }
        controllers.emit(hands(right = null))
        buffer.drain()
        assertFalse(adapter.recoverControlOverflow())
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        assertTrue(adapter.recoverControlOverflow())
        val events = buffer.drain().events
        assertEquals(DiscontinuityReason.RECENTERED, (events.first() as TrackingEvent.Discontinuity).reason)
        assertTrue(events.any { it is TrackingEvent.Discontinuity && it.target == TrackingTarget.RIGHT_HAND })
        adapter.stop()
    }

    @Test
    fun rejectedStopIsRetriedBeforeAProviderCanRestart() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        buffer.offerHead(InputOrigin.PICO, null)
        buffer.offerHead(InputOrigin.PICO, null)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        assertThrows(TrackingControlOverflowException::class.java) { adapter.stop(DiscontinuityReason.RECENTERED) }
        assertEquals(1, hmd.stops)
        assertEquals(1, controllers.stops)
        assertThrows(IllegalStateException::class.java) { adapter.start() }

        buffer.drain()
        assertThrows(IllegalArgumentException::class.java) { adapter.stop() }
        adapter.stop(DiscontinuityReason.RECENTERED)
        val retried = buffer.drain().events.single() as TrackingEvent.Discontinuity
        assertEquals(DiscontinuityReason.RECENTERED, retried.reason)
        assertEquals(2, retried.stamp.coordinateEpoch)
        adapter.start()
        assertTrue(buffer.drain().events.any { it is TrackingEvent.Discontinuity && it.reason == DiscontinuityReason.QUEUE_GAP })
        adapter.stop()
    }

    @Test
    fun userPauseIsNotAcceptedUntilControlOverflowIsDrainedAndRetried() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        buffer.offerHead(InputOrigin.PICO, null)
        buffer.offerHead(InputOrigin.PICO, null)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        assertThrows(TrackingControlOverflowException::class.java) { adapter.markUserPause() }
        assertTrue(buffer.drain().events.none { it is TrackingEvent.Discontinuity && it.reason == DiscontinuityReason.USER_PAUSED })
        assertFalse(adapter.recoverControlOverflow())
        adapter.markUserPause()
        assertTrue(adapter.recoverControlOverflow())
        val recovered = buffer.drain().events.filterIsInstance<TrackingEvent.Discontinuity>()
        assertTrue(recovered.any { it.reason == DiscontinuityReason.USER_PAUSED })
        assertTrue(recovered.any { it.reason == DiscontinuityReason.QUEUE_GAP })
        adapter.stop()
    }

    @Test
    fun partialStartFailureStopsBothAttemptedProvidersAndCanRestart() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>().apply { failStartOnce = true }
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        assertThrows(IllegalStateException::class.java) { adapter.start() }
        assertTrue(hmd.listeners.isEmpty())
        assertTrue(controllers.listeners.isEmpty())
        assertEquals(1, hmd.stops)
        assertEquals(1, controllers.stops)
        adapter.start()
        assertEquals(1, hmd.listeners.size)
        adapter.stop()
    }

    @Test
    fun stopStillReleasesProvidersIfObservationClockFails() {
        val times = ArrayDeque(listOf(10L, 9L))
        val buffer = TrackingEventBuffer(16) { times.removeFirst() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        buffer.offerHead(com.example.wuxiaarena.core.input.InputOrigin.PICO, null)
        adapter.start()
        assertThrows(IllegalStateException::class.java) { adapter.stop() }
        assertTrue(hmd.listeners.isEmpty())
        assertTrue(controllers.listeners.isEmpty())
        assertEquals(1, hmd.stops)
        assertEquals(1, controllers.stops)
    }

    @Test
    fun pureUserPauseAndResumeDoNotInventAProviderFailure() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        hmd.emit(head())
        controllers.emit(hands())
        buffer.drain()
        adapter.markUserPause()
        assertEquals(DiscontinuityReason.USER_PAUSED, (buffer.drain().events.single() as TrackingEvent.Discontinuity).reason)
        assertEquals(1, hmd.listeners.size)
        assertThrows(IllegalArgumentException::class.java) { adapter.stop(DiscontinuityReason.USER_PAUSED) }
        hmd.emit(head())
        controllers.emit(hands())
        assertTrue(buffer.drain().events.none { it is TrackingEvent.Discontinuity })
        adapter.stop()
    }

    @Test
    fun lossDuringUserPauseIsStillReported() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(16) { clock.getAndIncrement() }
        val hmd = FakeProvider<HMDTrackingData>()
        val controllers = FakeProvider<ControllerTrackingData>()
        val adapter = PicoTrackingAdapter(buffer, hmd, controllers)
        adapter.start()
        adapter.markUserPause()
        buffer.drain()
        hmd.state = DataProvider.State.PENDING
        hmd.supportState = DataProvider.SupportState.DEVICE_NOT_SUPPORTED
        adapter.pollAvailability()
        val loss = buffer.drain().events.single() as TrackingEvent.Discontinuity
        assertEquals(TrackingTarget.HEAD, loss.target)
        assertEquals(DiscontinuityReason.PROVIDER_UNAVAILABLE, loss.reason)
        adapter.stop()
    }
}
