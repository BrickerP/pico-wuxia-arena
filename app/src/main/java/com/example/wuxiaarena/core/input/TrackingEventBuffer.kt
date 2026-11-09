package com.example.wuxiaarena.core.input

/** A single consumer must process each returned batch before taking the next one. */
data class TrackingBatch(val events: List<TrackingEvent>, val droppedEvents: Long)

/**
 * Serializes application observations from multiple producer threads.
 * A full buffer stops accepting poses until the consumer receives an explicit gap.
 * A false offer reports a discarded pose; the gap batch counts discarded events and
 * reissues the latest pending hand selection and discontinuity after that gap.
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
    private var deferredHand: TrackingEvent.DominantHandChanged? = null
    private var deferredDiscontinuity: TrackingEvent.Discontinuity? = null
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
        if (gap == null && events.size == capacity) beginGap(origin, events.size.toLong())
        val event = TrackingEvent.DominantHandChanged(stamp(origin), hand)
        if (gap == null) {
            events.addLast(event)
        } else {
            if (deferredHand != null) dropped++
            deferredHand = event
        }
    }

    fun discontinuity(
        origin: InputOrigin,
        target: TrackingTarget,
        reason: DiscontinuityReason,
    ) = synchronized(lock) {
        if (reason == DiscontinuityReason.RECENTERED || reason == DiscontinuityReason.ROUND_RESET) {
            coordinateEpoch++
        }
        if (gap == null && events.size == capacity) beginGap(origin, events.size.toLong())
        val event = TrackingEvent.Discontinuity(stamp(origin), target, reason)
        if (gap == null) {
            events.addLast(event)
        } else {
            if (deferredDiscontinuity != null) dropped++
            deferredDiscontinuity = event
        }
    }

    fun drain(): TrackingBatch = synchronized(lock) {
        val result = if (gap == null) {
            events.toList()
        } else {
            listOfNotNull(gap, deferredHand, deferredDiscontinuity).sortedBy { it.stamp.sequence }
        }
        val batch = TrackingBatch(result, dropped)
        events.clear()
        gap = null
        deferredHand = null
        deferredDiscontinuity = null
        dropped = 0
        batch
    }

    private fun offerPose(
        origin: InputOrigin,
        create: (ObservationStamp) -> TrackingEvent,
    ): Boolean {
        if (gap != null) {
            dropped++
            return false
        }
        if (events.size == capacity) {
            beginGap(origin, events.size.toLong() + 1)
            return false
        }
        events.addLast(create(stamp(origin)))
        return true
    }

    private fun beginGap(origin: InputOrigin, lost: Long) {
        val lastHand = events.filterIsInstance<TrackingEvent.DominantHandChanged>().lastOrNull()
        val lastDiscontinuity = events.filterIsInstance<TrackingEvent.Discontinuity>().lastOrNull()
        val controls = listOfNotNull(lastHand, lastDiscontinuity).sortedBy { it.stamp.sequence }
        dropped += lost
        events.clear()
        gap = TrackingEvent.Discontinuity(stamp(origin), TrackingTarget.ALL, DiscontinuityReason.QUEUE_GAP)
        for (control in controls) {
            when (control) {
                is TrackingEvent.DominantHandChanged ->
                    deferredHand = TrackingEvent.DominantHandChanged(stamp(control.stamp.origin), control.hand)
                is TrackingEvent.Discontinuity ->
                    deferredDiscontinuity = TrackingEvent.Discontinuity(stamp(control.stamp.origin), control.target, control.reason)
                else -> error("unexpected control event")
            }
        }
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
