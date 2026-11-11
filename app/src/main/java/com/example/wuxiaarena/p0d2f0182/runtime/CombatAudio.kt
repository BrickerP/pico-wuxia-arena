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

/** The small output boundary also allows the event/lifecycle policy to run without an Android device. */
internal interface CombatAudioOutput {
    fun onLoad(listener: ((Int, Int) -> Unit)?)
    fun load(resource: Int): Int
    fun play(sample: Int, left: Float, right: Float, priority: Int, loop: Int, rate: Float): Int
    fun volume(stream: Int, left: Float, right: Float)
    fun stop(stream: Int)
    fun release()
}

private class SoundPoolOutput(context: Context) : CombatAudioOutput {
    private val application = context.applicationContext
    private val pool = SoundPool.Builder().setMaxStreams(12).setAudioAttributes(
        AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build(),
    ).build()

    override fun onLoad(listener: ((Int, Int) -> Unit)?) {
        if (listener == null) pool.setOnLoadCompleteListener(null)
        else pool.setOnLoadCompleteListener { _, sample, status -> listener(sample, status) }
    }
    override fun load(resource: Int) = pool.load(application, resource, 1)
    override fun play(sample: Int, left: Float, right: Float, priority: Int, loop: Int, rate: Float) =
        pool.play(sample, left, right, priority, loop, rate)
    override fun volume(stream: Int, left: Float, right: Float) = pool.setVolume(stream, left, right)
    override fun stop(stream: Int) = pool.stop(stream)
    override fun release() = pool.release()
}

/** Short material contacts consumed from the arena's resolved event batch. No HRTF is claimed. */
internal class CombatAudio(
    private val pool: CombatAudioOutput?,
    private val logWarning: (String) -> Unit = { message -> Log.w(TAG, message) },
    private val nanoTime: () -> Long = System::nanoTime,
) {
    constructor(context: Context) : this(createOutput(context))
    private enum class Cue(val resource: Int, val durationSeconds: Double, val priority: Int = 3) {
        SOFT_HIT(R.raw.arena_hit, 0.38),
        HARD_HIT(R.raw.arena_hard_hit, 0.56),
        GUARDED_HIT(R.raw.arena_guarded_hit, 0.42),
        BLOCK(R.raw.arena_block, 0.62, 4),
        PARRY(R.raw.arena_parry, 0.80, 5),
        WHOOSH(R.raw.arena_whoosh, 0.28, 1),
        PLAYER_HIT(R.raw.arena_hurt, 0.36, 4),
        SKILL(R.raw.arena_skill, 0.70, 5),
        EXECUTION(R.raw.arena_execution, 0.88, 6),
        VICTORY(R.raw.arena_victory, 0.95, 2),
        DEFEAT(R.raw.arena_defeat, 0.78, 2),
        STEP(R.raw.arena_step, 0.32, 1),
        RAIN(R.raw.arena_rain, 8.0, 0),
    }

    private data class Stream(val id: Int, val expiresAtNanos: Long, val priority: Int)
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
    private var playerMotionGeneration = -1L
    private var swingArmed = false
    private var lastPlayerSwing = Long.MIN_VALUE
    private var previousGait: Double? = null
    private var previousLocomotion: LocomotionProfile? = null
    private var rainStream = 0
    private var rainGain = -1f
    private var duckUntilNanos = 0L

    init {
        pool?.let { output ->
            output.onLoad { sampleId, status ->
                synchronized(gate) {
                    if (!closed && status == 0) readyIds += sampleId
                    if (!closed && status != 0) {
                        failedIds += sampleId
                        logWarning("Arena sound load failed sample=$sampleId status=$status")
                    }
                }
            }
            for (cue in Cue.entries) {
                try {
                    val id = output.load(cue.resource)
                    if (id != 0) {
                        soundIds[cue] = id
                    } else {
                        logWarning("Arena sound load rejected ${cue.name}")
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
            val now = nanoTime()
            if (changedRound || (shouldMute && !muted)) stopStreams()
            val resetPresentation = changedRound || shouldMute || muted
            if (resetPresentation || state.playerMotionGeneration != playerMotionGeneration) {
                swingArmed = false
                lastPlayerSwing = Long.MIN_VALUE
            }
            if (resetPresentation) {
                previousGait = null
                previousLocomotion = null
            }
            playerMotionGeneration = state.playerMotionGeneration
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
            if (state.result == TrialResult.FIGHTING) {
                if (newSwing) play(Cue.WHOOSH, volume = 0.24f)
                presentPlayerSwing(state, now)
                presentSteps(state)
                presentRain(now)
            } else {
                stopRain()
                previousGait = null
                previousLocomotion = null
                swingArmed = false
            }
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
        val damageGain = if (impact.appliedDamage > 0) {
            0.85 + 0.15 * (impact.appliedDamage / 40.0).coerceIn(0.0, 1.0)
        } else 1.0
        val volume = ((0.34 + 0.38 * accent.strength) * distanceGain * damageGain).toFloat()
        val pan = if (impact.hand == Hand.LEFT) -0.12f else 0.12f
        val variation = ((impact.id % 7L).toInt() - 3) * 0.008f
        enqueue(cue, volume, pan, accent.soundRate + variation)
        // Preserve the resolved material; the lethal low/cloth layer adds weight over that contact.
        if (impact.fatal && impact.appliedDamage > 0 && cue != Cue.EXECUTION) {
            enqueue(Cue.EXECUTION, volume * 0.52f, pan, 0.90f)
        }
    }

    private fun enqueue(cue: Cue, volume: Float, pan: Float, rate: Float) {
        val sample = soundIds[cue] ?: return
        if (sample in failedIds) return
        val now = nanoTime()
        pendingImpacts.removeAll { now - it.enqueuedAtNanos > IMPACT_FRESHNESS_NANOS }
        if (pendingImpacts.size >= MAX_PENDING_IMPACTS) {
            val lowest = pendingImpacts.minBy { it.cue.priority }
            if (lowest.cue.priority > cue.priority) return
            pendingImpacts.remove(lowest)
        }
        pendingImpacts += PendingImpact(cue, volume, pan, rate, now)
    }

    private fun playReadyImpacts() {
        val now = nanoTime()
        val iterator = pendingImpacts.iterator()
        while (iterator.hasNext()) {
            val pending = iterator.next()
            val sample = soundIds[pending.cue]
            if (now - pending.enqueuedAtNanos > IMPACT_FRESHNESS_NANOS || sample == null || sample in failedIds) {
                iterator.remove()
            } else if (sample in readyIds) {
                iterator.remove()
                play(pending.cue, pending.volume, pending.pan, pending.rate)
            }
        }
    }

    private fun presentPlayerSwing(state: ArenaViewState, now: Long) {
        val speed = state.playerBladeTipSpeed
        if (!speed.isFinite() || state.playerBladeTip?.isFinite() != true) {
            swingArmed = false
            return
        }
        if (state.playerBladeAtRest || speed < 0.70) swingArmed = true
        val cooled = lastPlayerSwing == Long.MIN_VALUE || now - lastPlayerSwing >= 180_000_000L
        if (swingArmed && cooled && speed >= 1.45 && !state.playerBladeAtRest) {
            play(Cue.WHOOSH, (0.18 + speed.coerceAtMost(5.0) * 0.045).toFloat(),
                if (state.dominantHand == Hand.LEFT) -0.16f else 0.16f,
                (0.90 + speed.coerceAtMost(5.0) * 0.035).toFloat())
            lastPlayerSwing = now
            swingArmed = false
        }
    }

    private fun presentSteps(state: ArenaViewState) {
        val profile = arenaOpponents.getOrNull(state.roundNumber - 1)?.locomotionProfile()
        val gait = state.enemyGaitMeters
        val previous = previousGait
        val sameProfile = profile === previousLocomotion
        // Advance even for a stopped actor or a failed/unready sound. Never queue missed footfalls.
        previousGait = gait.takeIf { it.isFinite() }
        previousLocomotion = profile
        if (profile == null || !sameProfile || previous == null || !gait.isFinite()) return
        if (state.phase != EnemyPhase.IDLE || !state.enemyMoveDirection.isFinite() || state.enemyMoveDirection == 0f) return
        val delta = gait - previous
        // Preserve the existing audio discontinuity guard; this is not a walk-clock constant.
        if (!delta.isFinite() || kotlin.math.abs(delta) > 0.75 || delta == 0.0) return

        val foot = latestAudioFootfall(profile, previous, gait) ?: return
        val left = foot == EnemyFoot.LEFT
        play(Cue.STEP, 0.16f, if (left) -0.07f else 0.07f, if (left) 0.96f else 1.03f)
    }

    private fun presentRain(now: Long) {
        if (rainStream == 0) rainStream = play(Cue.RAIN, 0.10f, loop = -1)
        val gain = if (now < duckUntilNanos) 0.045f else 0.10f
        if (rainStream != 0 && gain != rainGain) {
            try { pool?.volume(rainStream, gain, gain); rainGain = gain }
            catch (error: RuntimeException) { Log.w(TAG, "Unable to set rain level", error) }
        }
    }

    private fun stopRain() {
        if (rainStream != 0) {
            try { pool?.stop(rainStream) }
            catch (error: RuntimeException) { Log.w(TAG, "Unable to stop rain", error) }
        }
        rainStream = 0
        rainGain = -1f
    }

    /** Caller holds gate, preventing release between availability checks and play. */
    private fun play(cue: Cue, volume: Float, pan: Float = 0f, rate: Float = 1f, loop: Int = 0): Int {
        val output = pool ?: return 0
        val sample = soundIds[cue] ?: return 0
        if (sample !in readyIds) return 0
        try {
            val now = nanoTime()
            streams.removeAll { it.expiresAtNanos <= now }
            // Reserve a voice for rain. SoundPool does not notify us when it steals a stream.
            if (loop == 0 && streams.size >= MAX_SHORT_STREAMS) {
                val oldestLow = streams.minBy { it.priority }
                if (oldestLow.priority > cue.priority) return 0
                output.stop(oldestLow.id)
                streams.remove(oldestLow)
            }
            val left = volume * (1f - maxOf(0f, pan))
            val right = volume * (1f + minOf(0f, pan))
            val id = output.play(sample, left, right, cue.priority, loop, rate)
            if (id != 0) {
                val lifetime = ((cue.durationSeconds / rate + 0.25) * 1_000_000_000.0).toLong()
                if (loop == 0) streams += Stream(id, now + lifetime, cue.priority)
                if (cue.priority >= 3) duckUntilNanos = now + 180_000_000L
            }
            return id
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to play arena sound ${cue.name}", error)
            return 0
        }
    }

    private fun stopStreams() {
        pendingImpacts.clear()
        stopRain()
        streams.forEach { stream ->
            try { pool?.stop(stream.id) }
            catch (error: RuntimeException) { Log.e(TAG, "Unable to stop arena sound stream", error) }
        }
        streams.clear()
        duckUntilNanos = 0L
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
            pool?.onLoad(null)
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
        const val MAX_PENDING_IMPACTS = 24
        const val MAX_SHORT_STREAMS = 10
        const val IMPACT_FRESHNESS_NANOS = 120_000_000L

        fun createOutput(context: Context): CombatAudioOutput? = try {
            SoundPoolOutput(context)
        } catch (error: RuntimeException) {
            Log.e(TAG, "Unable to create arena sound output", error)
            null
        }
    }
}

/** Latest support entry consumed by Audio. Phase belongs exclusively to the shared profile clock. */
internal fun latestAudioFootfall(profile: LocomotionProfile, previousGait: Double, gait: Double): EnemyFoot? {
    val delta = gait - previousGait
    if (!previousGait.isFinite() || !gait.isFinite() || delta == 0.0) return null
    val source = profile.sourceSeconds(moving = true, gaitMeters = gait)
    val phase = (source - profile.loopStartSeconds) / (profile.loopEndSeconds - profile.loopStartSeconds)
    val forward = delta > 0.0
    val cycle = kotlin.math.round(gait / profile.strideMeters - phase)
    // If even one step fraction is below the cycle's representable precision, use the shared
    // wrapped clock instead. Distinct marker distances cannot be expressed in this numeric range.
    if (!cycle.isFinite() || cycle + profile.stepEvents[1].phase == cycle) {
        val latest = if (forward) {
            profile.stepEvents.lastOrNull { it.phase <= phase } ?: profile.stepEvents.last()
        } else {
            profile.stepEvents.firstOrNull { it.phase >= phase } ?: profile.stepEvents.first()
        }
        return if (forward) latest.forwardFoot else latest.reverseFoot
    }
    // Recover only the integer loop number. Compare markers in signed gait, since reconstructing
    // marker source seconds can differ from sourceSeconds() by an ULP at an exact negative boundary.
    var latest: GaitStepEvent? = null
    var latestDistance = if (forward) Double.NEGATIVE_INFINITY else Double.POSITIVE_INFINITY
    // A rounded seam may map to the previous loop. Exact predicates exclude future/departed markers.
    for (offset in -1..1) {
        for (step in profile.stepEvents) {
            val distance = profile.strideMeters * (cycle + offset + step.phase)
            val crossed = if (forward) distance > previousGait && distance <= gait
                else distance >= gait && distance < previousGait
            if (crossed && if (forward) distance > latestDistance else distance < latestDistance) {
                latest = step
                latestDistance = distance
            }
        }
    }
    val crossing = latest ?: return null
    return if (forward) crossing.forwardFoot else crossing.reverseFoot
}
