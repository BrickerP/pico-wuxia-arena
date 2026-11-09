package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.TrackingBatch
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingState

internal class TrackingProcessor(initialHand: Hand = Hand.RIGHT) {
    private val state = TrackingState(initialHand)

    fun process(
        batch: TrackingBatch,
        onEvent: (TrackingEvent, Boolean, TrackingSnapshot) -> Unit,
    ) {
        for (event in batch.events) {
            val accepted = state.accept(event)
            onEvent(event, accepted, state.snapshot)
        }
    }
}
