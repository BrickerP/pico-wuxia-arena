package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.animation.AnimationPlayConfig
import com.pico.spatial.core.ecs.animation.AnimationPlaybackController
import com.pico.spatial.core.ecs.animation.AnimationTransitionMode
import com.pico.spatial.core.ecs.resource.AnimationResource

private const val TAG = "ArenaAnimation"

/** Plays the four clips authored against this model's own skeleton. */
internal class EnemyAnimator(enemy: Entity) {
    private data class PlaybackKey(val clip: String, val round: Long, val attackId: Long?, val reacting: Boolean)

    private val target = enemy.findSkeletonRootEntity().single()
    private val importedResources = enemy.findSkinnedMeshEntity().single().getAnimationResources()
    private val importedClips = importedResources.associateBy { it.getName() }
    private val singleClips = mutableMapOf<String, AnimationResource>()
    private var controller: AnimationPlaybackController? = null
    private var playbackKey: PlaybackKey? = null
    private var lastPhase: EnemyPhase? = null
    private var lastPaused: Boolean? = null

    init {
        check(importedClips.keys.containsAll(listOf("idle", "slash", "hurt", "fall"))) {
            "Missing enemy animation clips: ${importedClips.keys}"
        }
        try {
            for (name in listOf("slash", "fall")) {
                singleClips[name] = importedClips.getValue(name).repeat(0)
            }
        } catch (error: Exception) {
            singleClips.values.forEach { it.close() }
            throw error
        }
        Log.i(TAG, "Bound one skeleton with clips=${importedClips.keys}")
    }

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (!target.valid) return
        val clip = when (state.phase) {
            EnemyPhase.IDLE -> "idle"
            EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE, EnemyPhase.RECOVERING -> "slash"
            EnemyPhase.HIT -> "fall"
            EnemyPhase.DEAD -> "fall"
        }
        val key = PlaybackKey(clip, state.roundGeneration, state.attackId, state.phase == EnemyPhase.HIT)
        val restartHit = state.phase == EnemyPhase.HIT && events.any { it is EnemyCombatEvent.HitReactionStarted }
        if (key != playbackKey || restartHit) {
            val resource = if (clip == "idle") importedClips.getValue(clip) else singleClips.getValue(clip)
            val previous = controller
            val next = target.playAnimation(
                resource,
                AnimationPlayConfig(
                    transitionDuration = 0.14f,
                    transitionMode = AnimationTransitionMode.STOP_AND_CROSSFADE,
                ),
            )
            controller = next
            playbackKey = key
            previous?.close()
            if (state.phase == EnemyPhase.DEAD) {
                next.setTime(state.deathElapsedSeconds.coerceAtMost(next.getDuration()))
                if (state.executing) next.setSpeed(0.65f)
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
            EnemyPhase.RECOVERING -> seekPhase(active, state, 2.167f, 3.0f)
            // The supplied hurt clip is seated. The standing fall introduction supplies this short cue.
            EnemyPhase.HIT -> seekPhase(active, state, 0.05f, 0.85f)
            EnemyPhase.DEAD -> active.setTime(state.deathElapsedSeconds.coerceAtMost(active.getDuration()))
            EnemyPhase.IDLE -> Unit
        }

        val paused = (state.pauseReason != null && state.result != TrialResult.VICTORY) ||
            !state.inputReady || state.hitStop || state.result == TrialResult.DEFEAT
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

    fun close() {
        val resources = buildList<AutoCloseable> {
            controller?.let(::add)
            addAll(singleClips.values)
            addAll(importedResources)
        }
        controller = null
        singleClips.clear()
        var failure: Exception? = null
        for (resource in resources) {
            try {
                resource.close()
            } catch (error: Exception) {
                if (failure == null) failure = error else failure.addSuppressed(error)
            }
        }
        failure?.let { throw it }
    }
}
