package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.math.Vector3

internal data class ArenaOpponent(
    val name: String,
    val asset: String,
    val bodyImpact: CombatImpactKind = CombatImpactKind.SOFT_HIT,
)

internal val arenaOpponents = listOf(
    ArenaOpponent("试刀客", "asset://models/opponents/base.glb"),
    ArenaOpponent("青衫护院", "asset://models/opponents/indigo.glb"),
    ArenaOpponent("玄甲守擂", "asset://models/opponents/veteran.glb", CombatImpactKind.HARD_HIT),
)

/** The visual clip, body proxies and blade anchors all use the same prepared actor profile. */
internal fun ArenaOpponent.attackProfile(direction: AttackDirection): AttackProfile =
    AttackBankProfiles.forAsset(asset, direction)

internal fun ArenaOpponent.attackPose(
    phase: EnemyPhase,
    elapsedNanos: Long,
    remainingNanos: Long?,
    origin: Vector3,
    yaw: Float,
    direction: AttackDirection,
    guarding: Boolean,
    moving: Boolean = false,
    recoveryFromContact: Boolean = false,
): AttackPoseSample? {
    require(origin.isFinite() && yaw.isFinite()) { "Attack pose requires a finite Stage transform" }
    require(elapsedNanos >= 0L && (remainingNanos == null || remainingNanos >= 0L)) {
        "Contact phase time must be non-negative"
    }
    if (phase in ATTACK_PHASES || phase == EnemyPhase.HIT && guarding || phase == EnemyPhase.IDLE && !moving) {
        val profile = attackProfile(direction)
        return profile.sample(profile.sourceSeconds(phase, elapsedNanos, remainingNanos, recoveryFromContact)).inStage(origin, yaw)
    }
    return null
}

internal fun ArenaOpponent.contactPose(
    phase: EnemyPhase,
    elapsedNanos: Long,
    remainingNanos: Long?,
    origin: Vector3,
    yaw: Float,
    direction: AttackDirection,
    guarding: Boolean,
    moving: Boolean = false,
    recoveryFromContact: Boolean = false,
): EnemyContactPose = attackPose(phase, elapsedNanos, remainingNanos, origin, yaw, direction, guarding, moving, recoveryFromContact)
    ?.contact ?: EnemyContactPose.standing(origin)

private val ATTACK_PHASES = setOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE, EnemyPhase.RECOVERING)
