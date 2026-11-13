package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
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
    )

    private val target = enemy.findSkeletonRootEntity(includeDisabled = true).single()
    private val importedResources = enemy.findSkinnedMeshEntity(includeDisabled = true).single().getAnimationResources()
    private val importedClips = mutableMapOf<String, AnimationResource>()
    private val playbackClips = mutableMapOf<String, AnimationResource>()
    private var controller: AnimationPlaybackController? = null
    private var playbackKey: PlaybackKey? = null
    private var lastPhase: EnemyPhase? = null
    private var lastPaused: Boolean? = null
    private var closed = false

    init {
        try {
            for (resource in importedResources) {
                importedClips[resource.getName()] = resource
            }
            check(importedClips.keys.containsAll(listOf("idle", "walk", "attack_overhead", "attack_left", "attack_right", "hit_body", "hit_head", "hit_side", "fall"))) {
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

    fun present(state: ArenaViewState) {
        if (closed || !target.valid) return
        // Every living pose, including contact hold/withdrawal, comes from the same
        // effective clip/source that generated the collision blade and body points.
        // Null means resources/selection unavailable, not an idle-pose fallback.
        val clip: String
        val sourceSeconds: Double?
        if (state.phase == EnemyPhase.DEAD) {
            clip = if (state.executing && state.deathElapsedSeconds < EXECUTION_RECOIL_SECONDS) "hit_head" else "fall"
            sourceSeconds = null
        } else {
            clip = state.enemyPoseClip ?: run { suspend(); return }
            sourceSeconds = state.enemyPoseSourceSeconds?.takeIf { it.isFinite() && it >= 0.0 }
                ?: run { suspend(); return }
        }
        val key = PlaybackKey(clip, state.roundGeneration, state.roundNumber, state.attackId)
        if (key != playbackKey) {
            val resource = playbackClips.getValue(clip)
            val previous = controller
            val next = target.playAnimation(
                resource,
                AnimationPlayConfig(
                    // Living poses must match the queried frame without blending an old clip.
                    // Preserve the existing death/fall transition lifecycle.
                    transitionDuration = if (state.phase == EnemyPhase.DEAD) 0.12f else 0f,
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
        val duration = active.getDuration()
        check(duration.isFinite() && duration > 0f) { "Enemy animation has no finite duration" }
        if (state.phase == EnemyPhase.DEAD) {
            val elapsed = state.deathElapsedSeconds
            val sourceTime = when {
                !state.executing -> elapsed
                elapsed < EXECUTION_RECOIL_SECONDS -> 0.10f + elapsed * 1.1f
                else -> 0.10f + (elapsed - EXECUTION_RECOIL_SECONDS) * 0.8f
            }
            active.setTime(sourceTime.coerceAtMost(duration))
        } else {
            val source = checkNotNull(sourceSeconds).toFloat()
            check(source.isFinite()) { "Enemy animation source exceeds SDK time range" }
            active.setTime(source.coerceAtMost(duration))
        }
        // All clips are manually sampled. The state clock owns pause, hit-stop and recovery.
        val paused = true
        if (!active.isPaused()) active.pause()
        if (lastPhase != state.phase || lastPaused != paused) {
            Log.i(TAG, "Presented phase=${state.phase}, paused=$paused, clip=$clip, sourceSeconds=${active.getTime()}")
            lastPhase = state.phase
            lastPaused = paused
        }
    }

    fun suspend() {
        controller?.takeIf { it.valid && !it.isPaused() }?.pause()
    }

    private companion object {
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
