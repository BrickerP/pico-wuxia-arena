package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.TrackingEventBuffer

/** Evaluate the live trial gate at the enqueue point; the input owner drains before returning. */
internal fun enqueueReadyHandSelection(
    buffer: TrackingEventBuffer,
    origin: InputOrigin,
    hand: Hand,
    canChangeDominantHand: () -> Boolean,
): Boolean {
    if (!canChangeDominantHand()) return false
    return buffer.tryChangeDominantHand(origin, hand)
}
