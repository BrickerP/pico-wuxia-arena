package com.example.wuxiaarena.p0d2f0182.runtime

import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import android.util.Log
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.p0d2f0182.R

/** Short material contacts consumed from the arena's resolved event batch. */
internal class CombatAudio(context: Context) {
    private enum class Cue(val resource: Int, val durationSeconds: Double) {
        SOFT_HIT(R.raw.arena_hit, 0.32),
        HARD_HIT(R.raw.arena_hard_hit, 0.48),
        GUARDED_HIT(R.raw.arena_guarded_hit, 0.41),
        BLOCK(R.raw.arena_block, 0.55),
        PARRY(R.raw.arena_parry, 0.72),
        WHOOSH(R.raw.arena_whoosh, 0.28),
        PLAYER_HIT(R.raw.arena_hurt, 0.36),
        SKILL(R.raw.arena_skill, 0.70),
        EXECUTION(R.raw.arena_execution, 0.88),
        VICTORY(R.raw.arena_victory, 0.95),
        DEFEAT(R.raw.arena_defeat, 0.78),
    }

    private data class Stream(val id: Int, val expiresAtNanos: Long)
    private data class PendingImpact(
        val cue: Cue,
        val volume: Float,
        val pan: Float,
        val rate: Float,
        val enqueuedAtNanos: Long,
    )

    private val gate = Any()
    private val soundIds = mutableMapOf<Cue, Int>()
    private val readyIds = mutableSetOf<Int>()
    private val failedIds = mutableSetOf<Int>()
    private val pendingImpacts = mutableListOf<PendingImpact>()
    private val streams = mutableListOf<Stream>()
    private val seenImpactIds = mutableSetOf<Long>()
    private var closed = false
    private var initialized = false
    private var muted = true
    private var roundGeneration = -1L
    private var lastResult = TrialResult.READY
    private var lastAttackId: Long? = null
    private var lastPhase = EnemyPhase.IDLE
    private val pool = try {
        SoundPool.Builder()
            .setMaxStreams(12)
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
                    if (!closed && status != 0) {
                        failedIds += sampleId
                        Log.w(TAG, "Arena sound load failed sample=$sampleId status=$status")
                    }
                }
            }
            val application = context.applicationContext
            for (cue in Cue.entries) {
                try {
                    val id = output.load(application, cue.resource, 1)
                    if (id != 0) {
                        soundIds[cue] = id
                    } else {
                        Log.w(TAG, "Arena sound load rejected ${cue.name}")
                    }
                } catch (error: RuntimeException) {
                    Log.e(TAG, "Unable to load arena sound ${cue.name}", error)
                }
            }
        }
    }

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        synchronized(gate) {
            if (closed || state.roundGeneration < roundGeneration) return
            val changedRound = !initialized || state.roundGeneration != roundGeneration
            val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
            val shouldMute = !state.sceneReady || (!terminal && (state.pauseReason != null || !state.inputReady))
            if (changedRound || (shouldMute && !muted)) stopStreams()
            if (changedRound) seenImpactIds.clear()
            val terminalChange = initialized && !changedRound && state.result != lastResult && terminal
            val newSwing = initialized && !changedRound && state.phase == EnemyPhase.STARTUP &&
                (state.attackId != lastAttackId || lastPhase != EnemyPhase.STARTUP)
            initialized = true
            roundGeneration = state.roundGeneration
            lastResult = state.result
            lastAttackId = state.attackId
            lastPhase = state.phase
            muted = shouldMute

            // Consume the complete batch even on the first callback of a new round.
            for (event in events) {
                if (event is CombatImpact && seenImpactIds.add(event.id) && !muted) {
                    queueImpact(event, state)
                }
            }
            if (muted) return
            playReadyImpacts()
            if (terminalChange) play(if (state.result == TrialResult.VICTORY) Cue.VICTORY else Cue.DEFEAT, volume = 0.45f)
            if (newSwing) play(Cue.WHOOSH, volume = 0.28f)
        }
    }

    private fun queueImpact(impact: CombatImpact, state: ArenaViewState) {
        if (!impact.strength.isFinite() || !impact.point.isFinite()) return
        val cue = when (impact.kind) {
            CombatImpactKind.SOFT_HIT -> Cue.SOFT_HIT
            CombatImpactKind.HARD_HIT -> Cue.HARD_HIT
            CombatImpactKind.GUARDED_HIT -> Cue.GUARDED_HIT
            CombatImpactKind.BLOCK -> Cue.BLOCK
            CombatImpactKind.PARRY -> Cue.PARRY
            CombatImpactKind.PLAYER_HIT -> Cue.PLAYER_HIT
            CombatImpactKind.SKILL -> Cue.SKILL
            CombatImpactKind.EXECUTION -> Cue.EXECUTION
        }
        val head = state.playerHeadPosition
        val distanceGain = if (head != null && head.isFinite()) {
            val dx = impact.point.x - head.x
            val dy = impact.point.y - head.y
            val dz = impact.point.z - head.z
            (1.0 / (1.0 + 0.18 * (dx * dx + dy * dy + dz * dz))).coerceIn(0.4, 1.0)
        } else {
            1.0
        }
        val accent = CombatFeedbackProfile.accent(impact)
        val volume = ((0.34 + 0.38 * accent.strength) * distanceGain).toFloat()
        val pan = if (impact.hand == Hand.LEFT) -0.12f else 0.12f
        val sample = soundIds[cue] ?: return
        if (sample !in failedIds) pendingImpacts += PendingImpact(cue, volume, pan, accent.soundRate, System.nanoTime())
    }

    private fun playReadyImpacts() {
        val now = System.nanoTime()
        val iterator = pendingImpacts.iterator()
        while (iterator.hasNext()) {
            val pending = iterator.next()
            val sample = soundIds[pending.cue]
            if (now - pending.enqueuedAtNanos > 120_000_000L || sample == null || sample in failedIds) {
                iterator.remove()
            } else if (sample in readyIds) {
                iterator.remove()
                play(pending.cue, pending.volume, pending.pan, pending.rate)
            }
        }
    }

    /** Caller holds gate, preventing release between availability checks and play. */
    private fun play(cue: Cue, volume: Float, pan: Float = 0f, rate: Float = 1f) {
        val output = pool ?: return
        val sample = soundIds[cue] ?: return
        if (sample !in readyIds) return
        try {
            val now = System.nanoTime()
            streams.removeAll { it.expiresAtNanos <= now }
            val left = volume * (1f - maxOf(0f, pan))
            val right = volume * (1f + minOf(0f, pan))
            val id = output.play(sample, left, right, 1, 0, rate)
            if (id != 0) {
                val lifetime = ((cue.durationSeconds / rate + 0.25) * 1_000_000_000.0).toLong()
                streams += Stream(id, now + lifetime)
            }
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to play arena sound ${cue.name}", error)
        }
    }

    private fun stopStreams() {
        pendingImpacts.clear()
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
            failedIds.clear()
            seenImpactIds.clear()
        }
        try {
            pool?.setOnLoadCompleteListener(null)
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to detach arena sound listener", error)
        }
        try {
            pool?.release()
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to release arena sound output", error)
        }
    }

    private companion object {
        const val TAG = "ArenaAudio"
    }
}
