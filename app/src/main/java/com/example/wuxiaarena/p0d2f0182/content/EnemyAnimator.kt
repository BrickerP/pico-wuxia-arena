package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.animation.AnimationPlayConfig
import com.pico.spatial.core.ecs.animation.AnimationPlaybackController
import com.pico.spatial.core.ecs.animation.AnimationTransitionMode
import com.pico.spatial.core.ecs.resource.AnimationResource

private const val TAG = "ArenaAnimation"

/** Plays this opponent's native slash and rest-pose-retargeted movement and reactions. */
internal class EnemyAnimator(enemy: Entity) {
    private data class PlaybackKey(
        val clip: String,
        val round: Long,
        val opponentRound: Int,
        val attackId: Long?,
        val reacting: Boolean,
    )

    private val target = enemy.findSkeletonRootEntity().single()
    private val importedResources = enemy.findSkinnedMeshEntity().single().getAnimationResources()
    private val importedClips = mutableMapOf<String, AnimationResource>()
    private val playbackClips = mutableMapOf<String, AnimationResource>()
    private var controller: AnimationPlaybackController? = null
    private var playbackKey: PlaybackKey? = null
    private var lastPhase: EnemyPhase? = null
    private var lastPaused: Boolean? = null
    private var closed = false
    private var lastImpactId = Long.MIN_VALUE
    private var holdingImpactPose = false
    private var pendingHitRestart = false
    private var reactionStrength = 0f

    init {
        try {
            for (resource in importedResources) {
                importedClips[resource.getName()] = resource
            }
            check(importedClips.keys.containsAll(listOf("idle", "walk", "slash", "hit_body", "hit_head", "hit_side", "fall"))) {
                "Missing enemy animation clips: ${importedClips.keys}"
            }
            for (name in importedClips.keys) {
                playbackClips[name] = importedClips.getValue(name).repeat(if (name == "idle" || name == "walk") -1 else 0)
            }
            Log.i(TAG, "Bound one skeleton with clips=${importedClips.keys}")
        } catch (error: Exception) {
            try {
                close()
            } catch (cleanup: Exception) {
                if (cleanup !== error) error.addSuppressed(cleanup)
            }
            throw error
        }
    }

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (closed || !target.valid) return
        val roundChanged = playbackKey?.let {
            it.round != state.roundGeneration || it.opponentRound != state.roundNumber
        } ?: true
        if (roundChanged) {
            lastImpactId = Long.MIN_VALUE
            holdingImpactPose = false
            pendingHitRestart = false
            reactionStrength = 0f
        }
        val impacts = events.filterIsInstance<CombatImpact>()
        val impact = impacts
            .filter { it.id > lastImpactId && it.kind.affectsEnemyPose() }
            .maxByOrNull { it.strength }
        if (impact != null) {
            lastImpactId = impacts.maxOf { it.id }
            reactionStrength = impact.strength.takeIf { it.isFinite() }?.coerceIn(0.0, 1.0)?.toFloat() ?: 0f
        }
        val hitReactionStarted = state.phase == EnemyPhase.HIT &&
            events.any { it is EnemyCombatEvent.HitReactionStarted }
        pendingHitRestart = pendingHitRestart || hitReactionStarted
        val existing = controller?.takeIf { it.valid }
        if (!roundChanged && existing != null && state.hitStop && (impact != null || holdingImpactPose)) {
            // Keep the pose that was visible at contact. Switching or seeking first would
            // freeze the beginning of the hurt clip instead of the actual impact pose.
            holdingImpactPose = true
            if (!existing.isPaused()) existing.pause()
            lastPaused = true
            return
        }
        holdingImpactPose = false
        if (!roundChanged && existing != null &&
            ((state.pauseReason != null && state.result != TrialResult.VICTORY) || !state.inputReady || !state.sceneReady)
        ) {
            if (!existing.isPaused()) existing.pause()
            lastPaused = true
            return
        }
        val clip = when (state.phase) {
            EnemyPhase.IDLE -> if (state.enemyMoveDirection != 0f) "walk" else "idle"
            EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE, EnemyPhase.RECOVERING -> "slash"
            EnemyPhase.HIT -> when {
                state.guarding -> "slash"
                state.hitReaction == HitReaction.PARRIED -> "hit_side"
                state.enemyHitZone == HitZone.HEAD -> "hit_head"
                else -> "hit_body"
            }
            EnemyPhase.DEAD -> if (state.executing && state.deathElapsedSeconds < EXECUTION_RECOIL_SECONDS) "hit_head" else "fall"
        }
        val key = PlaybackKey(clip, state.roundGeneration, state.roundNumber, state.attackId, state.phase == EnemyPhase.HIT)
        val restartHit = state.phase == EnemyPhase.HIT && pendingHitRestart
        pendingHitRestart = false
        if (key != playbackKey || restartHit) {
            val resource = playbackClips.getValue(clip)
            val previous = controller
            val next = target.playAnimation(
                resource,
                AnimationPlayConfig(
                    transitionDuration = if (state.phase == EnemyPhase.HIT) 0.055f - 0.03f * reactionStrength else 0.12f,
                    transitionMode = AnimationTransitionMode.STOP_AND_CROSSFADE,
                ),
            )
            controller = next
            playbackKey = key
            previous?.close()
            if (state.phase == EnemyPhase.DEAD) {
                next.setTime(0f)
            }
            Log.i(TAG, "Playing clip=$clip, round=${state.roundGeneration}, attackId=${state.attackId}")
        }

        val active = controller ?: return
        if (!active.valid) return
        when (state.phase) {
            // Source frames 39-45 touch the off-hand. The selected preparation starts later.
            EnemyPhase.PREPARING -> seekPhase(active, state, 1.55f, 1.85f)
            EnemyPhase.STARTUP -> seekPhase(active, state, 1.85f, 2.067f)
            EnemyPhase.ACTIVE -> seekPhase(active, state, 2.067f, 2.167f)
            // Include the native return from the forward bend before crossfading to idle.
            EnemyPhase.RECOVERING -> seekPhase(active, state, 2.167f, 3.4f)
            EnemyPhase.HIT -> {
                if (state.guarding) {
                    active.setTime(1.55f.coerceAtMost(active.getDuration()))
                } else {
                    val end = if (state.hitReaction == HitReaction.PARRIED) 1.18f else 0.72f
                    seekPhase(active, state, 0.05f, end)
                }
            }
            EnemyPhase.DEAD -> {
                val elapsed = state.deathElapsedSeconds
                val sourceTime = when {
                    !state.executing -> elapsed
                    elapsed < EXECUTION_RECOIL_SECONDS -> 0.10f + elapsed * 1.1f
                    else -> 0.10f + (elapsed - EXECUTION_RECOIL_SECONDS) * 0.8f
                }
                active.setTime(sourceTime.coerceAtMost(active.getDuration()))
            }
            EnemyPhase.IDLE -> if (clip == "walk") {
                val duration = active.getDuration()
                val phase = ((state.enemyGaitMeters / WALK_STRIDE_METERS % 1.0 + 1.0) % 1.0).toFloat()
                active.setTime((WALK_LOOP_START + phase * WALK_LOOP_DURATION).coerceIn(0f, duration))
                active.setSpeed((0.65 / WALK_STRIDE_METERS * WALK_LOOP_DURATION).toFloat())
            }
        }

        val paused = (state.pauseReason != null && state.result != TrialResult.VICTORY) ||
            !state.inputReady || state.hitStop || state.result == TrialResult.DEFEAT ||
            clip == "walk" || state.phase == EnemyPhase.HIT && state.guarding
        if (paused && !active.isPaused()) active.pause()
        if (!paused && active.isPaused()) active.resume()
        if (lastPhase != state.phase || lastPaused != paused) {
            Log.i(TAG, "Presented phase=${state.phase}, paused=$paused, clip=$clip, sourceSeconds=${active.getTime()}")
            lastPhase = state.phase
            lastPaused = paused
        }
    }

    private fun seekPhase(
        playback: AnimationPlaybackController,
        state: ArenaViewState,
        startSeconds: Float,
        endSeconds: Float,
    ) {
        val duration = playback.getDuration()
        check(duration.isFinite() && duration > 0f) { "Enemy animation has no finite duration" }
        val start = startSeconds.coerceIn(0f, duration)
        val end = endSeconds.coerceIn(start, duration)
        val phaseNanos = state.phaseElapsedNanos.toDouble() + (state.phaseRemainingNanos ?: 0L).toDouble()
        val progress = if (phaseNanos > 0.0) (state.phaseElapsedNanos / phaseNanos).coerceIn(0.0, 1.0) else 1.0
        playback.setTime(start + (end - start) * progress.toFloat())
        if (phaseNanos > 0.0) {
            playback.setSpeed(((end - start) / (phaseNanos / 1_000_000_000.0)).toFloat())
        }
    }

    fun suspend() {
        controller?.takeIf { it.valid && !it.isPaused() }?.pause()
    }

    private fun CombatImpactKind.affectsEnemyPose(): Boolean = when (this) {
        CombatImpactKind.SOFT_HIT, CombatImpactKind.HARD_HIT, CombatImpactKind.GUARDED_HIT,
        CombatImpactKind.BLOCK, CombatImpactKind.PARRY, CombatImpactKind.SKILL, CombatImpactKind.EXECUTION -> true
        CombatImpactKind.PLAYER_HIT -> false
    }

    private companion object {
        const val WALK_STRIDE_METERS = 1.45
        const val WALK_LOOP_START = 1f / 3f
        const val WALK_LOOP_DURATION = 7f / 6f
        const val EXECUTION_RECOIL_SECONDS = 0.45f
    }

    fun close() {
        if (closed) return
        closed = true
        val resources = buildList<AutoCloseable> {
            controller?.let(::add)
            addAll(playbackClips.values)
            addAll(importedResources)
        }
        controller = null
        holdingImpactPose = false
        pendingHitRestart = false
        playbackClips.clear()
        var failure: Exception? = null
        for (resource in resources) {
            try {
                resource.close()
            } catch (error: Exception) {
                if (failure == null) {
                    failure = error
                } else if (failure !== error) {
                    failure.addSuppressed(error)
                }
            }
        }
        failure?.let { throw it }
    }
}
