package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin

internal data class HandImpact(val hand: Hand, val impact: CombatImpact)

/** Consume each contact once and submit one meaningful pulse per hand per presentation. */
internal class CombatHapticContacts {
    private var round = Long.MIN_VALUE
    private val seen = mutableSetOf<Long>()

    fun select(state: ArenaViewState, events: List<EnemyCombatEvent>): List<HandImpact> {
        if (state.roundGeneration < round) return emptyList()
        if (state.roundGeneration != round) {
            round = state.roundGeneration
            seen.clear()
        }
        val fresh = events.filterIsInstance<CombatImpact>().filter { seen.add(it.id) }
        val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
        if (state.inputOrigin != InputOrigin.PICO || !state.sceneReady ||
            (!terminal && (!state.inputReady || state.pauseReason != null))
        ) return emptyList()
        val selected = linkedMapOf<Hand, CombatImpact>()
        val ranking = compareBy<CombatImpact> { priority(it) }.thenBy { it.strength }
        for (impact in fresh) {
            if (!impact.strength.isFinite()) continue
            val hands = if (impact.kind == CombatImpactKind.SKILL || impact.kind == CombatImpactKind.EXECUTION) {
                listOf(Hand.LEFT, Hand.RIGHT)
            } else listOf(impact.hand)
            for (hand in hands) {
                val current = selected[hand]
                if (current == null || ranking.compare(impact, current) > 0) selected[hand] = impact
            }
        }
        return selected.map { (hand, impact) -> HandImpact(hand, impact) }
    }

    private fun priority(impact: CombatImpact): Int = when {
        impact.fatal || impact.kind == CombatImpactKind.EXECUTION -> 6
        impact.kind == CombatImpactKind.PARRY -> 5
        impact.kind == CombatImpactKind.SKILL || impact.kind == CombatImpactKind.PLAYER_HIT -> 4
        impact.appliedDamage > 0 && impact.zone == HitZone.HEAD -> 3
        else -> 2
    }
}
