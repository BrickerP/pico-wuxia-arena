package com.example.wuxiaarena.core.input

/** Receipt time belongs to this observation, not to the other tracking sources. */
data class PoseObservation(val stamp: ObservationStamp, val pose: ObservedPose?)

data class TrackingSnapshot(
    val head: PoseObservation?,
    val left: PoseObservation?,
    val right: PoseObservation?,
    val dominantHand: Hand,
    val headContinuity: Long,
    val leftContinuity: Long,
    val rightContinuity: Long,
    /** Required sources must be observed at or after this application sequence. */
    val requiredSinceSequence: Long = -1,
) {
    /** Presence is not motion readiness or a claim about hardware tracking quality. */
    val hasRequiredObservations: Boolean
        get() {
            val headObservation = head ?: return false
            val handObservation = (if (dominantHand == Hand.LEFT) left else right) ?: return false
            return headObservation.poseHasPosition() && handObservation.poseHasPosition() && handObservation.poseHasRotation() &&
                headObservation.stamp.sequence >= requiredSinceSequence && handObservation.stamp.sequence >= requiredSinceSequence
        }
}

private fun PoseObservation?.poseHasPosition(): Boolean =
    this?.pose?.let { it.quality != TrackingQuality.SOURCE_REPORTED_INVALID && it.position?.isFinite() == true } == true

private fun PoseObservation?.poseHasRotation(): Boolean =
    this?.pose?.let {
        it.quality != TrackingQuality.SOURCE_REPORTED_INVALID && it.rotation?.normalizedOrNull() != null
    } == true

/** Consumed on one thread, in the order provided by [TrackingEventBuffer]. */
class TrackingState(initialHand: Hand) {
    var snapshot = TrackingSnapshot(null, null, null, initialHand, 0, 0, 0)
        private set

    private var lastStamp: ObservationStamp? = null

    /** Older or time-regressing input invalidates history; a duplicate is ignored. */
    fun accept(event: TrackingEvent): Boolean {
        val stamp = event.stamp
        val last = lastStamp
        if (last != null && stamp.coordinateEpoch < last.coordinateEpoch) {
            invalidateAll()
            requireNewObservations(maxOf(last.sequence, stamp.sequence))
            lastStamp = last.copy(
                sequence = maxOf(last.sequence, stamp.sequence),
                receivedAtNanos = maxOf(last.receivedAtNanos, stamp.receivedAtNanos),
            )
            return false
        }
        if (last != null && stamp.sequence <= last.sequence) {
            if (stamp.sequence < last.sequence) {
                invalidateAll()
                requireNewObservations(last.sequence)
            }
            return false
        }
        if (last != null && stamp.receivedAtNanos < last.receivedAtNanos) {
            invalidateAll()
            requireNewObservations(stamp.sequence)
            lastStamp = last.copy(sequence = stamp.sequence)
            return false
        }

        val reset = last != null && (
            stamp.sequence - last.sequence != 1L ||
                stamp.coordinateEpoch != last.coordinateEpoch
            )
        if (reset) {
            invalidateAll()
            requireNewObservations(stamp.sequence)
        }
        lastStamp = stamp

        when (event) {
            is TrackingEvent.Head -> {
                val observation = PoseObservation(stamp, event.pose)
                val sourceChanged = snapshot.head != null && snapshot.head?.stamp?.origin != stamp.origin
                if (sourceChanged) requireNewObservations(stamp.sequence)
                if (sourceChanged ||
                    (snapshot.head.poseHasPosition() && !observation.poseHasPosition()) ||
                    (snapshot.head.poseHasRotation() && !observation.poseHasRotation())
                ) invalidateHead()
                snapshot = snapshot.copy(head = observation)
                if (!observation.poseHasPosition()) requireNewObservations(stamp.sequence)
            }
            is TrackingEvent.Controllers -> {
                val left = PoseObservation(stamp, event.left)
                val right = PoseObservation(stamp, event.right)
                val leftSourceChanged = snapshot.left != null && snapshot.left?.stamp?.origin != stamp.origin
                val rightSourceChanged = snapshot.right != null && snapshot.right?.stamp?.origin != stamp.origin
                if ((snapshot.dominantHand == Hand.LEFT && leftSourceChanged) ||
                    (snapshot.dominantHand == Hand.RIGHT && rightSourceChanged)
                ) requireNewObservations(stamp.sequence)
                if (leftSourceChanged ||
                    (snapshot.left.poseHasPosition() && !left.poseHasPosition()) ||
                    (snapshot.left.poseHasRotation() && !left.poseHasRotation())
                ) invalidateLeft()
                if (rightSourceChanged ||
                    (snapshot.right.poseHasPosition() && !right.poseHasPosition()) ||
                    (snapshot.right.poseHasRotation() && !right.poseHasRotation())
                ) invalidateRight()
                snapshot = snapshot.copy(left = left, right = right)
                val required = if (snapshot.dominantHand == Hand.LEFT) left else right
                if (!required.poseHasPosition() || !required.poseHasRotation()) requireNewObservations(stamp.sequence)
            }
            is TrackingEvent.DominantHandChanged -> {
                if (event.hand != snapshot.dominantHand) {
                    requireNewObservations(stamp.sequence)
                    if (!reset) {
                        invalidateLeft()
                        invalidateRight()
                    }
                    snapshot = snapshot.copy(dominantHand = event.hand)
                }
            }
            is TrackingEvent.Discontinuity -> {
                if (event.target.affectsRequired(snapshot.dominantHand)) requireNewObservations(stamp.sequence)
                if (!reset) invalidate(event.target)
            }
        }
        return true
    }

    private fun invalidate(target: TrackingTarget) {
        when (target) {
            TrackingTarget.HEAD -> invalidateHead()
            TrackingTarget.LEFT_HAND -> invalidateLeft()
            TrackingTarget.RIGHT_HAND -> invalidateRight()
            TrackingTarget.BOTH_HANDS -> {
                invalidateLeft()
                invalidateRight()
            }
            TrackingTarget.ALL -> invalidateAll()
        }
    }

    private fun TrackingTarget.affectsRequired(hand: Hand): Boolean =
        this == TrackingTarget.ALL || this == TrackingTarget.HEAD || this == TrackingTarget.BOTH_HANDS ||
            (this == TrackingTarget.LEFT_HAND && hand == Hand.LEFT) ||
            (this == TrackingTarget.RIGHT_HAND && hand == Hand.RIGHT)

    private fun requireNewObservations(sequence: Long) {
        snapshot = snapshot.copy(requiredSinceSequence = maxOf(snapshot.requiredSinceSequence, sequence))
    }

    private fun invalidateHead() {
        snapshot = snapshot.copy(head = null, headContinuity = snapshot.headContinuity + 1)
    }

    private fun invalidateLeft() {
        snapshot = snapshot.copy(left = null, leftContinuity = snapshot.leftContinuity + 1)
    }

    private fun invalidateRight() {
        snapshot = snapshot.copy(right = null, rightContinuity = snapshot.rightContinuity + 1)
    }

    private fun invalidateAll() {
        invalidateHead()
        invalidateLeft()
        invalidateRight()
    }
}
