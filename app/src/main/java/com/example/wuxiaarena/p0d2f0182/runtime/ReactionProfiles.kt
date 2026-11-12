package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.HitZone

/** Existing hurt clips, sampled from the same final rig and bone-local offsets as the attacks. */
internal class ReactionProfiles(
    val body: PoseClipProfile,
    val head: PoseClipProfile,
    val side: PoseClipProfile,
) {
    init {
        require(body.clip == "hit_body" && head.clip == "hit_head" && side.clip == "hit_side") {
            "Reactions require all three prepared hurt clips"
        }
        for (profile in listOf(body, head, side)) {
            require(profile.samples.first().sourceSeconds <= START_SECONDS &&
                profile.samples.last().sourceSeconds >= endSeconds(profile)) {
                "Hurt samples must cover the current source playback window"
            }
        }
    }

    fun frame(reaction: HitReaction?, zone: HitZone?, elapsedNanos: Long, remainingNanos: Long?): EnemyPoseFrame {
        require(elapsedNanos >= 0L && (remainingNanos == null || remainingNanos >= 0L)) {
            "Hurt phase time must be non-negative"
        }
        val profile = when {
            reaction == HitReaction.PARRIED -> side
            zone == HitZone.HEAD -> head
            else -> body
        }
        val total = elapsedNanos.toDouble() + (remainingNanos ?: 0L).toDouble()
        val progress = if (total > 0.0) (elapsedNanos.toDouble() / total).coerceIn(0.0, 1.0) else 1.0
        val time = START_SECONDS + (endSeconds(profile) - START_SECONDS) * progress
        return EnemyPoseFrame(profile.clip, profile.sample(time))
    }

    private fun endSeconds(profile: PoseClipProfile) = if (profile === side) 1.18 else .72

    private companion object {
        const val START_SECONDS = .05
    }
}
