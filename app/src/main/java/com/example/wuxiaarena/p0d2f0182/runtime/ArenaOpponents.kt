package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.HitZone
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

/** A source selection shared by native playback and actor-local body/blade consumers. */
internal data class EnemyPoseFrame(val clip: String, val pose: AttackPoseSample)

internal fun selectEnemyPose(
    attack: AttackProfile,
    locomotion: LocomotionProfile,
    reactions: ReactionProfiles,
    phase: EnemyPhase,
    elapsedNanos: Long,
    remainingNanos: Long?,
    guarding: Boolean,
    moving: Boolean,
    gaitMeters: Double,
    recoveryFromContact: Boolean = false,
    hitReaction: HitReaction? = null,
    hitZone: HitZone? = null,
): EnemyPoseFrame? = when {
    phase == EnemyPhase.IDLE -> EnemyPoseFrame(locomotion.clip(moving), locomotion.sample(moving, gaitMeters))
    phase == EnemyPhase.HIT && guarding -> EnemyPoseFrame(locomotion.clip(false), locomotion.sample(false, gaitMeters))
    phase == EnemyPhase.HIT -> reactions.frame(hitReaction, hitZone, elapsedNanos, remainingNanos)
    phase in ATTACK_PHASES -> EnemyPoseFrame(attack.clip,
        attack.sample(attack.sourceSeconds(phase, elapsedNanos, remainingNanos, recoveryFromContact)))
    else -> null
}

/** The visual clip, body proxies and blade anchors all use the same prepared actor profile. */
internal fun ArenaOpponent.attackProfile(direction: AttackDirection): AttackProfile =
    AttackBankProfiles.forAsset(asset, direction)

internal fun ArenaOpponent.locomotionProfile(): LocomotionProfile = AttackBankProfiles.locomotionForAsset(asset)

internal fun ArenaOpponent.reactionProfiles(): ReactionProfiles = AttackBankProfiles.reactionsForAsset(asset)

internal fun ArenaOpponent.poseFrame(
    phase: EnemyPhase,
    elapsedNanos: Long,
    remainingNanos: Long?,
    direction: AttackDirection,
    guarding: Boolean,
    moving: Boolean,
    recoveryFromContact: Boolean,
    gaitMeters: Double,
    hitReaction: HitReaction? = null,
    hitZone: HitZone? = null,
): EnemyPoseFrame? = selectEnemyPose(attackProfile(direction), locomotionProfile(), reactionProfiles(), phase,
    elapsedNanos, remainingNanos, guarding, moving, gaitMeters, recoveryFromContact, hitReaction, hitZone)

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
    gaitMeters: Double,
    hitReaction: HitReaction? = null,
    hitZone: HitZone? = null,
): AttackPoseSample? {
    require(origin.isFinite() && yaw.isFinite()) { "Attack pose requires a finite Stage transform" }
    require(elapsedNanos >= 0L && (remainingNanos == null || remainingNanos >= 0L)) {
        "Contact phase time must be non-negative"
    }
    return poseFrame(phase, elapsedNanos, remainingNanos, direction, guarding, moving,
        recoveryFromContact, gaitMeters, hitReaction, hitZone)?.pose?.inStage(origin, yaw)
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
    gaitMeters: Double,
    hitReaction: HitReaction? = null,
    hitZone: HitZone? = null,
): EnemyContactPose = attackPose(phase, elapsedNanos, remainingNanos, origin, yaw, direction,
    guarding, moving, recoveryFromContact, gaitMeters, hitReaction, hitZone)?.contact ?: EnemyContactPose.standing(origin)

private val ATTACK_PHASES = setOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE, EnemyPhase.RECOVERING)
