package com.example.wuxiaarena.core.input

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3

enum class InputOrigin { PICO, DESKTOP, SYNTHETIC }

enum class TrackingQuality { UNKNOWN, SOURCE_REPORTED_VALID, SOURCE_REPORTED_INVALID }

enum class Hand { LEFT, RIGHT }

enum class TrackingTarget { HEAD, LEFT_HAND, RIGHT_HAND, BOTH_HANDS, ALL }

enum class DiscontinuityReason {
    PROVIDER_UNAVAILABLE,
    NOT_IN_FULL_SPACE,
    RECENTERED,
    USER_PAUSED,
    APP_PAUSED,
    QUEUE_GAP,
    ROUND_RESET,
}

/** Sequence and time describe application receipt, not a device sampling clock. */
data class ObservationStamp(
    val sequence: Long,
    val receivedAtNanos: Long,
    val coordinateEpoch: Long,
    val origin: InputOrigin,
) {
    init {
        require(sequence >= 0) { "sequence must be non-negative" }
        require(coordinateEpoch >= 0) { "coordinate epoch must be non-negative" }
    }
}

/** A missing component is unavailable; UNKNOWN quality does not assert hardware validity. */
data class ObservedPose(
    val position: Vector3?,
    val rotation: Quaternion?,
    val quality: TrackingQuality = TrackingQuality.UNKNOWN,
)

sealed interface TrackingEvent {
    val stamp: ObservationStamp

    data class Head(
        override val stamp: ObservationStamp,
        val pose: ObservedPose?,
    ) : TrackingEvent

    data class Controllers(
        override val stamp: ObservationStamp,
        val left: ObservedPose?,
        val right: ObservedPose?,
    ) : TrackingEvent

    /** Switching hands ends the previous gesture and requires a new baseline. */
    data class DominantHandChanged(
        override val stamp: ObservationStamp,
        val hand: Hand,
    ) : TrackingEvent

    data class Discontinuity(
        override val stamp: ObservationStamp,
        val target: TrackingTarget,
        val reason: DiscontinuityReason,
    ) : TrackingEvent
}
