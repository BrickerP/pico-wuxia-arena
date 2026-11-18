package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.playerBladeAxis
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingControlOverflowException
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.content.presentedPlayerHandTransform
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class ReadyHandSelectionTest {
    @Test
    fun readySelectionFlowsThroughTheRealBufferReducerArenaAndFinalLeftHand() {
        val f = Fixture()
        assertEquals(Hand.RIGHT, f.arena.viewState.dominantHand)
        assertTrue(f.select(Hand.LEFT))
        assertEquals(Hand.LEFT, f.arena.viewState.dominantHand)
        assertFalse(f.arena.viewState.inputReady)
        assertNull(f.arena.viewState.playerWeaponGrip)
        assertFalse(f.arena.startTrial())

        f.observe()
        assertTrue(f.arena.viewState.inputReady)
        assertNull(f.arena.viewState.pauseReason)
        val grip = requireNotNull(f.arena.viewState.playerWeaponGrip)
        assertVector(requireNotNull(f.left.position), grip.position)
        val hand = requireNotNull(presentedPlayerHandTransform(f.snapshot, grip, Hand.LEFT))
        assertEquals(grip.position, hand.position)
        assertVector(playerBladeAxis(grip).base, f.arena.viewState.playerBladeBase)
        assertTrue(f.arena.startTrial())
    }

    @Test
    fun queuedOldObservationsCannotBecomeTheNewSideBaseline() {
        val f = Fixture()
        f.offerObservations()
        assertTrue(enqueueReadyHandSelection(f.buffer, InputOrigin.PICO, Hand.LEFT) {
            f.arena.viewState.result == TrialResult.READY
        })
        f.drain()
        assertEquals(Hand.LEFT, f.arena.viewState.dominantHand)
        assertFalse(f.arena.viewState.inputReady)
        assertNull(f.arena.viewState.playerWeaponGrip)
        assertNull(presentedPlayerHandTransform(f.snapshot, null, Hand.LEFT))
        f.observe()
        assertVector(requireNotNull(f.left.position), f.arena.viewState.playerWeaponGrip?.position)
    }

    @Test
    fun aStaleReadyClickIsRejectedAfterTheActualTrialStartsFighting() {
        val f = Fixture()
        val readyClick = { f.select(Hand.LEFT) }
        assertTrue(f.arena.startTrial())
        repeat(40) {
            if (f.arena.viewState.result != TrialResult.FIGHTING) {
                f.now += 100_000_000L
                f.observe()
                f.arena.onTick(f.now)
            }
        }
        assertEquals(TrialResult.FIGHTING, f.arena.viewState.result)
        val previous = f.arena.viewState.dominantHand
        assertFalse(readyClick())
        assertEquals(previous, f.arena.viewState.dominantHand)
        assertTrue(f.buffer.drain().events.isEmpty())
    }

    @Test
    fun countdownAlsoRejectsHandSelection() {
        val f = Fixture()
        assertTrue(f.arena.startTrial())
        assertEquals(TrialResult.COUNTDOWN, f.arena.viewState.result)
        assertFalse(f.select(Hand.LEFT))
        assertEquals(Hand.RIGHT, f.arena.viewState.dominantHand)
        assertTrue(f.buffer.drain().events.isEmpty())
    }

    @Test
    fun roundResetAndRelocationPreserveTheActualSelectedSideWhileRequiringNewObservations() {
        val f = Fixture()
        assertTrue(f.select(Hand.LEFT))
        f.observe()
        for (reason in listOf(DiscontinuityReason.ROUND_RESET, DiscontinuityReason.RECENTERED)) {
            f.now += 1_000_000L
            f.buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, reason)
            f.drain()
            assertEquals(Hand.LEFT, f.arena.viewState.dominantHand)
            assertFalse(f.arena.viewState.inputReady)
            assertNull(f.arena.viewState.playerWeaponGrip)
            f.observe()
            assertEquals(Hand.LEFT, f.arena.viewState.dominantHand)
            assertVector(requireNotNull(f.left.position), f.arena.viewState.playerWeaponGrip?.position)
        }
    }

    @Test
    fun readyHandSelectionKeepsThePauseAndRevokesItsEarlierResumeConfirmation() {
        val f = Fixture()
        f.now += 1_000_000L
        f.buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.USER_PAUSED)
        f.drain()
        assertEquals(PauseReason.USER, f.arena.viewState.pauseReason)
        val earlierPauseId = requireNotNull(f.arena.viewState.pauseId)
        assertTrue(f.select(Hand.LEFT))
        f.observe()
        assertEquals(Hand.LEFT, f.arena.viewState.dominantHand)
        assertEquals(PauseReason.TRACKING_INTERRUPTION, f.arena.viewState.pauseReason)
        assertNotEquals(earlierPauseId, f.arena.viewState.pauseId)
        assertFalse(f.arena.confirmResume(earlierPauseId))
        assertFalse(f.arena.startTrial())
    }

    @Test
    fun readyHandSelectionCannotClearAnEarlierTrackingInterruption() {
        val f = Fixture()
        f.now += 1_000_000L
        f.buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        f.drain()
        assertEquals(PauseReason.TRACKING_INTERRUPTION, f.arena.viewState.pauseReason)
        assertTrue(f.select(Hand.LEFT))
        f.observe()
        assertEquals(Hand.LEFT, f.arena.viewState.dominantHand)
        assertEquals(PauseReason.TRACKING_INTERRUPTION, f.arena.viewState.pauseReason)
        assertFalse(f.arena.startTrial())
    }

    @Test
    fun providerCanFillTheControlQueueAfterTheReadyCheckWithoutLatchingAHandBarrier() {
        val f = Fixture()
        val pool = Executors.newSingleThreadExecutor()
        val filled = CountDownLatch(1)
        try {
            val accepted = enqueueReadyHandSelection(f.buffer, InputOrigin.PICO, Hand.LEFT) {
                val producer = pool.submit {
                    repeat(64) {
                        f.now += 1_000_000L
                        f.buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.PROVIDER_UNAVAILABLE)
                    }
                    filled.countDown()
                }
                assertTrue(filled.await(5, TimeUnit.SECONDS))
                producer.get(5, TimeUnit.SECONDS)
                f.arena.viewState.result == TrialResult.READY
            }
            assertFalse(accepted)
            // Stop still uses its required same-control retry contract at saturation.
            assertThrows(TrackingControlOverflowException::class.java) {
                f.buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.APP_PAUSED)
            }
            f.drain()
            assertEquals(Hand.RIGHT, f.arena.viewState.dominantHand)
            f.now += 1_000_000L
            f.buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.APP_PAUSED)
            f.drain()
            f.now += 1_000_000L
            assertTrue(f.buffer.offerHead(InputOrigin.PICO, f.head))
            assertTrue(f.buffer.offerControllers(InputOrigin.PICO, f.left, f.right))
            f.drain()
            assertEquals(Hand.RIGHT, f.arena.viewState.dominantHand)
            assertTrue(f.arena.viewState.inputReady)
            assertTrue(f.buffer.drain().events.isEmpty())
        } finally {
            pool.shutdownNow()
        }
    }

    @Test
    fun providerPoseSaturationBetweenTheGateAndEnqueueRejectsTheSelectionWithoutDroppingPoses() {
        val f = Fixture()
        val accepted = enqueueReadyHandSelection(f.buffer, InputOrigin.PICO, Hand.LEFT) {
            repeat(32) { assertTrue(f.buffer.offerHead(InputOrigin.PICO, f.head)) }
            f.arena.viewState.result == TrialResult.READY
        }
        assertFalse(accepted)
        val batch = f.buffer.drain()
        assertEquals(32, batch.events.size)
        assertEquals(0L, batch.droppedEvents)
        assertTrue(batch.events.all { it is com.example.wuxiaarena.core.input.TrackingEvent.Head })
    }

    private fun assertVector(expected: Vector3, actual: Vector3?) {
        val point = requireNotNull(actual)
        assertEquals(expected.x, point.x, 1e-9)
        assertEquals(expected.y, point.y, 1e-9)
        assertEquals(expected.z, point.z, 1e-9)
    }

    private class Fixture {
        var now = 0L
        val buffer = TrackingEventBuffer(32) { now }
        val processor = TrackingProcessor()
        val arena = ArenaSession(logMessage = {})
        private val identity = Quaternion(0.0, 0.0, 0.0, 1.0)
        val head = ObservedPose(Vector3(0.0, 1.6, 0.0), identity)
        val left = ObservedPose(Vector3(-0.28, 1.24, -0.43), identity)
        val right = ObservedPose(Vector3(0.28, 1.24, -0.43), identity)
        var snapshot: TrackingSnapshot? = null

        init {
            arena.setEnemyGeometry(Vector3(0.0, 0.028, -2.4), 2.0)
            observe()
            observe()
        }

        fun offerObservations() {
            now += 10_000_000L
            buffer.offerHead(InputOrigin.PICO, head)
            now += 1_000_000L
            buffer.offerControllers(InputOrigin.PICO, left, right)
        }

        fun observe() {
            offerObservations()
            drain()
        }

        fun drain() = processor.process(buffer.drain()) { event, accepted, state ->
            snapshot = state
            arena.onTrackingEvent(event, accepted, state)
        }

        fun select(hand: Hand): Boolean {
            val accepted = enqueueReadyHandSelection(buffer, InputOrigin.PICO, hand) {
                arena.viewState.result == TrialResult.READY
            }
            drain()
            return accepted
        }
    }
}
