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
    /** Actual enemy health removed by this contact, after guard and remaining health. */
    val appliedDamage: Int = 0,
    val zone: HitZone? = null,
    val fatal: Boolean = false,
    /** Real cutting direction at this contact in Stage space; absent for a resting/unknown blade. */
    val tangent: Vector3? = null,
) : EnemyCombatEvent {
    init {
        require(appliedDamage >= 0) { "applied damage must be non-negative" }
        require(!fatal || appliedDamage > 0) { "a fatal enemy contact must apply damage" }
    }
}
