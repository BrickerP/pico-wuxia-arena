package com.example.wuxiaarena.core.input

/** A single consumer must process each returned batch before taking the next one. */
data class TrackingBatch(val events: List<TrackingEvent>, val droppedEvents: Long)

/** The caller must drain and retry the same rejected control before applying it. */
class TrackingControlOverflowException : IllegalStateException("tracking control queue is full; drain and retry the same control")

/**
 * Serializes application observations from multiple producer threads.
 * A full buffer stops accepting poses until the consumer receives an explicit gap.
 * Controls keep their original order; an overloaded control queue rejects the new
 * control explicitly instead of overwriting an earlier reset or pause.
 */
class TrackingEventBuffer(
    private val capacity: Int,
    private val clockNanos: () -> Long = System::nanoTime,
) {
    init {
        require(capacity > 0) { "capacity must be positive" }
    }

    private val lock = Any()
    private val events = ArrayDeque<TrackingEvent>()
    private var sequence = 0L
    private var coordinateEpoch = 0L
    private var lastTime: Long? = null
    private var gap: TrackingEvent.Discontinuity? = null
    private val controlsBeforeGap = ArrayDeque<TrackingEvent>()
    private val controlsAfterGap = ArrayDeque<TrackingEvent>()
    private val controlCapacity = maxOf(capacity, 2)
    private var blockedControl: ControlRequest? = null
    private var dropped = 0L

    fun offerHead(origin: InputOrigin, pose: ObservedPose?): Boolean = synchronized(lock) {
        offerPose(origin) { TrackingEvent.Head(it, pose) }
    }

    fun offerControllers(
        origin: InputOrigin,
        left: ObservedPose?,
        right: ObservedPose?,
    ): Boolean = synchronized(lock) {
        offerPose(origin) { TrackingEvent.Controllers(it, left, right) }
    }

    fun changeDominantHand(origin: InputOrigin, hand: Hand) = synchronized(lock) {
        val request = ControlRequest.HandChange(origin, hand)
        prepareControl(request)
        val event = TrackingEvent.DominantHandChanged(stamp(origin), hand)
        if (gap == null) {
            events.addLast(event)
        } else {
            controlsAfterGap.addLast(event)
        }
        if (blockedControl == request) blockedControl = null
    }

    fun discontinuity(
        origin: InputOrigin,
        target: TrackingTarget,
        reason: DiscontinuityReason,
    ) = synchronized(lock) {
        val request = ControlRequest.Discontinuity(origin, target, reason)
        prepareControl(request)
        if (reason == DiscontinuityReason.RECENTERED || reason == DiscontinuityReason.ROUND_RESET) coordinateEpoch++
        val event = TrackingEvent.Discontinuity(stamp(origin), target, reason)
        if (gap == null) {
            events.addLast(event)
        } else {
            controlsAfterGap.addLast(event)
        }
        if (blockedControl == request) blockedControl = null
    }

    fun drain(): TrackingBatch = synchronized(lock) {
        val result = if (gap == null) {
            events.toList()
        } else {
            controlsBeforeGap.toList() + listOfNotNull(gap) + controlsAfterGap.toList()
        }
        val batch = TrackingBatch(result, dropped)
        events.clear()
        gap = null
        controlsBeforeGap.clear()
        controlsAfterGap.clear()
        dropped = 0
        batch
    }

    private fun offerPose(
        origin: InputOrigin,
        create: (ObservationStamp) -> TrackingEvent,
    ): Boolean {
        if (blockedControl != null && gap == null) {
            beginGap(origin, 1)
            return false
        }
        if (gap != null) {
            dropped++
            return false
        }
        if (events.size == capacity) {
            beginGap(origin, 1)
            return false
        }
        events.addLast(create(stamp(origin)))
        return true
    }

    private fun beginGap(origin: InputOrigin, rejectedPoses: Long) {
        for (event in events) {
            when (event) {
                is TrackingEvent.Head, is TrackingEvent.Controllers -> dropped++
                is TrackingEvent.DominantHandChanged, is TrackingEvent.Discontinuity -> controlsBeforeGap.addLast(event)
            }
        }
        dropped += rejectedPoses
        events.clear()
        gap = TrackingEvent.Discontinuity(stamp(origin), TrackingTarget.ALL, DiscontinuityReason.QUEUE_GAP)
    }

    private fun prepareControl(request: ControlRequest) {
        if (blockedControl != null && blockedControl != request) throw TrackingControlOverflowException()
        if (gap == null && events.size == capacity) beginGap(request.origin, 0)
        if (gap != null && controlsAfterGap.size >= controlCapacity) {
            blockedControl = request
            throw TrackingControlOverflowException()
        }
    }

    private sealed interface ControlRequest {
        val origin: InputOrigin

        data class HandChange(override val origin: InputOrigin, val hand: Hand) : ControlRequest
        data class Discontinuity(
            override val origin: InputOrigin,
            val target: TrackingTarget,
            val reason: DiscontinuityReason,
        ) : ControlRequest
    }

    private fun stamp(origin: InputOrigin): ObservationStamp {
        val now = clockNanos()
        check(lastTime == null || now >= lastTime!!) { "observation clock moved backwards" }
        val result = ObservationStamp(sequence, now, coordinateEpoch, origin)
        sequence++
        lastTime = now
        return result
    }
}
