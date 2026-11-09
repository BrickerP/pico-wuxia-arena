package com.example.wuxiaarena.p0d2f0182.runtime

import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import android.util.Log
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.p0d2f0182.R

/** Short event sounds owned by the same lifecycle as the arena presentation. */
internal class CombatAudio(context: Context) {
    private enum class Cue(val resource: Int, val durationSeconds: Double) {
        HIT(R.raw.arena_hit, 0.20),
        CLASH(R.raw.arena_clash, 0.44),
        WHOOSH(R.raw.arena_whoosh, 0.28),
        HURT(R.raw.arena_hurt, 0.29),
        SKILL(R.raw.arena_skill, 0.58),
        EXECUTION(R.raw.arena_execution, 0.72),
        VICTORY(R.raw.arena_victory, 0.95),
        DEFEAT(R.raw.arena_defeat, 0.78),
        DRY(R.raw.arena_dry, 0.09),
    }

    private data class Stream(val id: Int, val expiresAtNanos: Long)

    private val gate = Any()
    private val soundIds = mutableMapOf<Cue, Int>()
    private val readyIds = mutableSetOf<Int>()
    private val streams = mutableListOf<Stream>()
    private var closed = false
    private var initialized = false
    private var muted = true
    private var roundGeneration = -1L
    private var feedbackSequence = -1L
    private var lastResult = TrialResult.READY
    private var lastAttackId: Long? = null
    private var lastPhase = EnemyPhase.IDLE
    private val pool = try {
        SoundPool.Builder()
            .setMaxStreams(6)
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build(),
            )
            .build()
    } catch (error: RuntimeException) {
        Log.e(TAG, "Unable to create arena sound output", error)
        null
    }

    init {
        pool?.let { output ->
            output.setOnLoadCompleteListener { _, sampleId, status ->
                synchronized(gate) {
                    if (!closed && status == 0) readyIds += sampleId
                    if (!closed && status != 0) Log.w(TAG, "Arena sound load failed sample=$sampleId status=$status")
                }
            }
            val application = context.applicationContext
            for (cue in Cue.entries) {
                try {
                    val id = output.load(application, cue.resource, 1)
                    if (id != 0) soundIds[cue] = id
                } catch (error: RuntimeException) {
                    Log.e(TAG, "Unable to load arena sound ${cue.name}", error)
                }
            }
        }
    }

    fun present(state: ArenaViewState) {
        synchronized(gate) {
            if (closed || state.roundGeneration < roundGeneration) return
            val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
            val shouldMute = (state.pauseReason != null && !terminal) || !state.inputReady || !state.sceneReady
            if (shouldMute && !muted) stopStreams()
            muted = shouldMute

            if (!initialized || state.roundGeneration != roundGeneration) {
                stopStreams()
                initialized = true
                remember(state)
                return
            }

            val newFeedback = state.feedbackSequence > feedbackSequence
            val terminalChange = state.result != lastResult &&
                (state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT)
            val newSwing = state.phase == EnemyPhase.STARTUP &&
                (state.attackId != lastAttackId || lastPhase != EnemyPhase.STARTUP)
            remember(state)
            if (muted) return

            when {
                terminalChange -> play(if (state.result == TrialResult.VICTORY) Cue.VICTORY else Cue.DEFEAT, volume = 0.55f)
                newFeedback -> playFeedback(state.feedback, state.combo)
                newSwing -> play(Cue.WHOOSH, volume = 0.24f)
            }
        }
    }

    private fun remember(state: ArenaViewState) {
        val changedRound = state.roundGeneration != roundGeneration
        roundGeneration = state.roundGeneration
        feedbackSequence = if (changedRound) state.feedbackSequence else maxOf(feedbackSequence, state.feedbackSequence)
        lastResult = state.result
        lastAttackId = state.attackId
        lastPhase = state.phase
    }

    private fun playFeedback(feedback: CombatFeedback?, combo: Int) {
        when (feedback) {
            CombatFeedback.HIT -> play(Cue.HIT, rate = 1f + 0.025f * combo.coerceIn(0, 4))
            CombatFeedback.HEADSHOT -> play(Cue.HIT, rate = 1.14f)
            CombatFeedback.GUARDED_HIT -> play(Cue.CLASH, rate = 0.80f, volume = 0.34f)
            CombatFeedback.BLOCK -> play(Cue.CLASH, rate = 0.94f)
            CombatFeedback.PARRY -> play(Cue.CLASH, rate = 1.18f, volume = 0.64f)
            CombatFeedback.DODGE -> play(Cue.WHOOSH, rate = 1.18f, volume = 0.30f)
            CombatFeedback.PLAYER_HIT -> play(Cue.HURT)
            CombatFeedback.GUARD_BREAK -> play(Cue.HURT, rate = 0.78f, volume = 0.64f)
            CombatFeedback.SKILL -> play(Cue.SKILL, volume = 0.62f)
            CombatFeedback.EXECUTION -> play(Cue.EXECUTION, volume = 0.65f)
            CombatFeedback.TIMEOUT -> play(Cue.DEFEAT, volume = 0.50f)
            CombatFeedback.LOW_STAMINA, CombatFeedback.LOW_FOCUS, CombatFeedback.OUT_OF_RANGE -> {
                play(Cue.DRY, volume = 0.18f)
            }
            null -> Unit
        }
    }

    /** Caller holds gate, preventing release between availability checks and play. */
    private fun play(cue: Cue, rate: Float = 1f, volume: Float = 0.52f) {
        val output = pool ?: return
        val sample = soundIds[cue] ?: return
        if (sample !in readyIds) return
        try {
            val now = System.nanoTime()
            streams.removeAll { it.expiresAtNanos <= now }
            val id = output.play(sample, volume, volume, 1, 0, rate)
            if (id != 0) {
                val lifetime = ((cue.durationSeconds / rate + 0.25) * 1_000_000_000.0).toLong()
                streams += Stream(id, now + lifetime)
            }
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to play arena sound ${cue.name}", error)
        }
    }

    /** End paused tails instead of replaying them when new observations arrive. */
    private fun stopStreams() {
        val output = pool ?: return
        try {
            output.autoPause()
            streams.forEach { output.stop(it.id) }
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to stop arena sound streams", error)
        }
        streams.clear()
    }

    fun close() {
        synchronized(gate) {
            if (closed) return
            closed = true
            stopStreams()
            soundIds.clear()
            readyIds.clear()
        }
        pool?.setOnLoadCompleteListener(null)
        pool?.release()
    }

    private companion object {
        const val TAG = "ArenaAudio"
    }
}
