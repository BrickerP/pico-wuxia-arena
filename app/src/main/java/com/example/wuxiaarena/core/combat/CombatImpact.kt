package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3

enum class CombatImpactKind {
    SOFT_HIT, HARD_HIT, GUARDED_HIT, BLOCK, PARRY, PLAYER_HIT, SKILL, EXECUTION,
}

/** A resolved physical contact, expressed in Stage metres and emitted once. */
data class CombatImpact(
    val id: Long,
    val kind: CombatImpactKind,
    val point: Vector3,
    val normal: Vector3,
    val strength: Double,
    val hand: Hand,
    override val atNanos: Long,
) : EnemyCombatEvent
