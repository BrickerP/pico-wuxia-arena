package com.example.wuxiaarena.core.combat

private const val NANOS_PER_MILLISECOND = 1_000_000L
private const val IDLE_DELAY = 800L * NANOS_PER_MILLISECOND
private const val HIT_DURATION = 300L * NANOS_PER_MILLISECOND
private const val PARRY_DURATION = 550L * NANOS_PER_MILLISECOND
private const val NORMAL_DAMAGE = 25
private const val GUARDED_DAMAGE = 10

/** Directions are named from the player's point of view. */
enum class AttackDirection(
    val preparationNanos: Long,
    val startupNanos: Long,
    val activeNanos: Long,
    val recoveryNanos: Long,
) {
    LEFT(
        550L * NANOS_PER_MILLISECOND, 180L * NANOS_PER_MILLISECOND,
        200L * NANOS_PER_MILLISECOND, 600L * NANOS_PER_MILLISECOND,
    ),
    RIGHT(
        550L * NANOS_PER_MILLISECOND, 180L * NANOS_PER_MILLISECOND,
        200L * NANOS_PER_MILLISECOND, 600L * NANOS_PER_MILLISECOND,
    ),
    OVERHEAD(
        650L * NANOS_PER_MILLISECOND, 250L * NANOS_PER_MILLISECOND,
        200L * NANOS_PER_MILLISECOND, 650L * NANOS_PER_MILLISECOND,
    ),
}

enum class EnemyPhase { IDLE, PREPARING, STARTUP, ACTIVE, RECOVERING, HIT, DEAD }
enum class HitReaction { PLAYER_HIT, PARRIED }
enum class AttackOutcome { BLOCKED, PARRIED, HIT_PLAYER, MISSED }
enum class AttackCancelReason { PLAYER_HIT, TRACKING_INTERRUPTION, ENEMY_DEFEATED }
enum class PauseReason { USER, TRACKING_INTERRUPTION }

sealed interface EnemyCombatEvent {
    val atNanos: Long

    data class PhaseChanged(
        val previous: EnemyPhase,
        val current: EnemyPhase,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    data class AttackStarted(
        val attackId: Long,
        val direction: AttackDirection,
        val counterattack: Boolean,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    data class AttackResolved(
        val attackId: Long,
        val outcome: AttackOutcome,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    data class AttackCancelled(
        val attackId: Long,
        val reason: AttackCancelReason,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    data class EnemyDamaged(
        val nominalDamage: Int,
        val appliedDamage: Int,
        val healthBefore: Int,
        val healthAfter: Int,
        val guarded: Boolean,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    data class GuardChanged(val active: Boolean, override val atNanos: Long) : EnemyCombatEvent

    data class HitReactionStarted(
        val reaction: HitReaction,
        val durationNanos: Long,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    data class PauseChanged(
        val previous: PauseReason?,
        val current: PauseReason?,
        val pauseId: Long,
        override val atNanos: Long,
    ) : EnemyCombatEvent

    /** The clock restarts with the round; the caller owns round identity. */
    data class RoundReset(override val atNanos: Long = 0L) : EnemyCombatEvent
}

/**
 * Single-owner, deterministic enemy rules. This class does not read tracking, recognize
 * gestures or detect contacts. The caller must supply already-resolved domain events and
 * deduplicate hits before calling receivePlayerHit. The caller also serializes access and
 * orders simultaneous events: interruption first, then blade defense, player hit and
 * enemy hit. Event times are simulation time, not device observation timestamps.
 */
class EnemyCombatStateMachine(
    private val initialHealth: Int = 100,
    private val idleDelayNanos: Long = IDLE_DELAY,
) {
    init {
        require(initialHealth > 0) { "initial health must be positive" }
        require(idleDelayNanos >= 0L) { "idle delay must be non-negative" }
    }

    var phase: EnemyPhase = EnemyPhase.IDLE
        private set
    var phaseElapsedNanos: Long = 0L
        private set
    var simulationNanos: Long = 0L
        private set
    var health: Int = initialHealth
        private set
    var guarding: Boolean = false
        private set
    var pauseReason: PauseReason? = null
        private set
    var currentPauseId: Long? = null
        private set
    var hitReaction: HitReaction? = null
        private set

    val currentAttackId: Long? get() = attack?.id
    val currentAttackDirection: AttackDirection? get() = attack?.direction
    val nanosUntilPhaseTransition: Long?
        get() = when (phase) {
            EnemyPhase.IDLE, EnemyPhase.DEAD -> null
            else -> phaseDuration() - phaseElapsedNanos
        }

    private data class Attack(
        val id: Long,
        val direction: AttackDirection,
        var resolved: Boolean = false,
    )

    private var attack: Attack? = null
    private var nextAttackId = 1L
    private var nextPauseId = 1L
    private var hitDurationNanos = HIT_DURATION

    /** Reads attack readiness using the caller's range decision without advancing state. */
    fun canStartAttack(targetInRange: Boolean): Boolean =
        pauseReason == null && phase == EnemyPhase.IDLE && phaseElapsedNanos >= idleDelayNanos && targetInRange

    /** The caller decides direction and range; the idle delay is enforced here. */
    fun tryStartAttack(direction: AttackDirection, targetInRange: Boolean): List<EnemyCombatEvent> {
        if (!canStartAttack(targetInRange)) return emptyList()
        return mutableListOf<EnemyCombatEvent>().also { startAttack(direction, false, it) }
    }

    /**
     * Advances one interval on the simulation clock. The caller must split intervals at
     * external contacts, interruptions and decision changes before advancing past them;
     * this state machine cannot retroactively insert a contact into an elapsed window.
     */
    fun advanceBy(
        deltaNanos: Long,
        targetInRange: Boolean,
        counterDirection: AttackDirection = AttackDirection.LEFT,
    ): List<EnemyCombatEvent> {
        require(deltaNanos >= 0L) { "time delta must be non-negative" }
        if (pauseReason != null || phase == EnemyPhase.DEAD || deltaNanos == 0L) return emptyList()
        require(deltaNanos <= Long.MAX_VALUE - simulationNanos) { "simulation clock overflow" }

        val events = mutableListOf<EnemyCombatEvent>()
        var remaining = deltaNanos
        while (remaining > 0L) {
            if (phase == EnemyPhase.IDLE) {
                simulationNanos += remaining
                phaseElapsedNanos += remaining
                break
            }
            val duration = phaseDuration()
            val step = minOf(remaining, duration - phaseElapsedNanos)
            simulationNanos += step
            phaseElapsedNanos += step
            remaining -= step
            if (phaseElapsedNanos == duration) completePhase(targetInRange, counterDirection, events)
        }
        return events
    }

    /**
     * Accepts one already-deduplicated player hit; it does not detect contact. The caller
     * selects any newly armed counterattack's direction without redirecting an existing attack.
     */
    fun receivePlayerHit(
        damage: Int = NORMAL_DAMAGE,
        breakGuard: Boolean = false,
        armGuard: Boolean = false,
        counterDirection: AttackDirection = AttackDirection.OVERHEAD,
    ): List<EnemyCombatEvent> {
        require(damage > 0) { "damage must be positive" }
        if (pauseReason != null || phase == EnemyPhase.DEAD) return emptyList()
        val events = mutableListOf<EnemyCombatEvent>()
        if (breakGuard) endGuard(events)
        if (!breakGuard && !guarding && (armGuard || phase == EnemyPhase.HIT && hitReaction == HitReaction.PLAYER_HIT)) {
            guarding = true
            events += EnemyCombatEvent.GuardChanged(true, simulationNanos)
        }
        val nominal = if (guarding) maxOf(1, (damage.toLong() * GUARDED_DAMAGE / NORMAL_DAMAGE).toInt()) else damage
        val before = health
        health = maxOf(0, health - nominal)
        events += EnemyCombatEvent.EnemyDamaged(nominal, before - health, before, health, guarding, simulationNanos)

        if (health == 0) {
            cancelAttack(AttackCancelReason.ENEMY_DEFEATED, events)
            endGuard(events)
            hitReaction = null
            changePhase(EnemyPhase.DEAD, events)
        } else if (guarding && phase == EnemyPhase.IDLE && armGuard) {
            startAttack(counterDirection, true, events)
        } else if (!guarding) {
            val remainingParry = if (phase == EnemyPhase.HIT && hitReaction == HitReaction.PARRIED) {
                hitDurationNanos - phaseElapsedNanos
            } else {
                0L
            }
            cancelAttack(AttackCancelReason.PLAYER_HIT, events)
            hitDurationNanos = maxOf(HIT_DURATION, remainingParry)
            hitReaction = HitReaction.PLAYER_HIT
            changePhase(EnemyPhase.HIT, events)
            events += EnemyCombatEvent.HitReactionStarted(HitReaction.PLAYER_HIT, hitDurationNanos, simulationNanos)
        }
        return events
    }

    /** The result must belong to the current attack; a miss is emitted at the window end. */
    fun resolveActiveAttack(attackId: Long, outcome: AttackOutcome): List<EnemyCombatEvent> {
        require(outcome != AttackOutcome.MISSED) { "misses are resolved when the active window ends" }
        if (pauseReason != null || phase != EnemyPhase.ACTIVE || attack?.id != attackId) return emptyList()
        return mutableListOf<EnemyCombatEvent>().also { resolveAttack(outcome, it) }
    }

    fun pauseByPlayer(): List<EnemyCombatEvent> {
        if (pauseReason != null) return emptyList()
        val pauseId = allocatePauseId()
        pauseReason = PauseReason.USER
        currentPauseId = pauseId
        return listOf(EnemyCombatEvent.PauseChanged(null, pauseReason, pauseId, simulationNanos))
    }

    /** Each call is a new discontinuity; callers must deduplicate repeated source reports. */
    fun interruptTracking(): List<EnemyCombatEvent> {
        val previous = pauseReason
        val pauseId = allocatePauseId()
        pauseReason = PauseReason.TRACKING_INTERRUPTION
        currentPauseId = pauseId
        return listOf(EnemyCombatEvent.PauseChanged(previous, pauseReason, pauseId, simulationNanos))
    }

    /** Confirmation is tied to the current pause and is not stored before both gates are ready. */
    fun tryResume(
        trackingReady: Boolean,
        actionReady: Boolean,
        confirmedPauseId: Long?,
    ): List<EnemyCombatEvent> {
        val reason = pauseReason ?: return emptyList()
        val pauseId = checkNotNull(currentPauseId)
        if (!trackingReady || !actionReady || confirmedPauseId != pauseId) return emptyList()
        val events = mutableListOf<EnemyCombatEvent>()
        if (reason == PauseReason.TRACKING_INTERRUPTION && phase != EnemyPhase.DEAD) {
            cancelAttack(AttackCancelReason.TRACKING_INTERRUPTION, events)
            endGuard(events)
            hitReaction = null
            changePhase(EnemyPhase.IDLE, events)
        }
        pauseReason = null
        currentPauseId = null
        events += EnemyCombatEvent.PauseChanged(reason, null, pauseId, simulationNanos)
        return events
    }

    fun resetRound(): List<EnemyCombatEvent> {
        phase = EnemyPhase.IDLE
        phaseElapsedNanos = 0L
        simulationNanos = 0L
        health = initialHealth
        guarding = false
        pauseReason = null
        currentPauseId = null
        hitReaction = null
        attack = null
        hitDurationNanos = HIT_DURATION
        return listOf(EnemyCombatEvent.RoundReset())
    }

    private fun phaseDuration(): Long = when (phase) {
        EnemyPhase.PREPARING -> checkNotNull(attack).direction.preparationNanos
        EnemyPhase.STARTUP -> checkNotNull(attack).direction.startupNanos
        EnemyPhase.ACTIVE -> checkNotNull(attack).direction.activeNanos
        EnemyPhase.RECOVERING -> checkNotNull(attack).direction.recoveryNanos
        EnemyPhase.HIT -> hitDurationNanos
        EnemyPhase.IDLE, EnemyPhase.DEAD -> error("phase has no timed transition")
    }

    private fun completePhase(
        targetInRange: Boolean,
        counterDirection: AttackDirection,
        events: MutableList<EnemyCombatEvent>,
    ) {
        when (phase) {
            EnemyPhase.PREPARING -> changePhase(EnemyPhase.STARTUP, events)
            EnemyPhase.STARTUP -> changePhase(EnemyPhase.ACTIVE, events)
            EnemyPhase.ACTIVE -> resolveAttack(AttackOutcome.MISSED, events)
            EnemyPhase.RECOVERING -> {
                attack = null
                changePhase(EnemyPhase.IDLE, events)
            }
            EnemyPhase.HIT -> {
                hitReaction = null
                if (guarding && targetInRange) {
                    startAttack(counterDirection, true, events)
                } else {
                    endGuard(events)
                    changePhase(EnemyPhase.IDLE, events)
                }
            }
            EnemyPhase.IDLE, EnemyPhase.DEAD -> error("phase has no timed transition")
        }
    }

    private fun startAttack(
        direction: AttackDirection,
        counterattack: Boolean,
        events: MutableList<EnemyCombatEvent>,
    ) {
        check(nextAttackId < Long.MAX_VALUE) { "attack identifier overflow" }
        val current = Attack(nextAttackId++, direction)
        attack = current
        events += EnemyCombatEvent.AttackStarted(current.id, direction, counterattack, simulationNanos)
        changePhase(EnemyPhase.PREPARING, events)
    }

    private fun allocatePauseId(): Long {
        check(nextPauseId < Long.MAX_VALUE) { "pause identifier overflow" }
        return nextPauseId++
    }

    private fun resolveAttack(outcome: AttackOutcome, events: MutableList<EnemyCombatEvent>) {
        val current = checkNotNull(attack)
        current.resolved = true
        events += EnemyCombatEvent.AttackResolved(current.id, outcome, simulationNanos)
        endGuard(events)
        if (outcome == AttackOutcome.PARRIED) {
            attack = null
            hitReaction = HitReaction.PARRIED
            hitDurationNanos = PARRY_DURATION
            changePhase(EnemyPhase.HIT, events)
            events += EnemyCombatEvent.HitReactionStarted(HitReaction.PARRIED, hitDurationNanos, simulationNanos)
        } else {
            changePhase(EnemyPhase.RECOVERING, events)
        }
    }

    private fun cancelAttack(reason: AttackCancelReason, events: MutableList<EnemyCombatEvent>) {
        val current = attack
        if (current != null && !current.resolved) {
            events += EnemyCombatEvent.AttackCancelled(current.id, reason, simulationNanos)
        }
        attack = null
    }

    private fun endGuard(events: MutableList<EnemyCombatEvent>) {
        if (guarding) {
            guarding = false
            events += EnemyCombatEvent.GuardChanged(false, simulationNanos)
        }
    }

    private fun changePhase(next: EnemyPhase, events: MutableList<EnemyCombatEvent>) {
        val previous = phase
        phase = next
        phaseElapsedNanos = 0L
        events += EnemyCombatEvent.PhaseChanged(previous, next, simulationNanos)
    }
}
