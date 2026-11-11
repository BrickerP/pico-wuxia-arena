package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.Quaternion
import kotlin.math.PI
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin

/** Keep the overhead board in front of the venue when the opponent steps close. */
internal fun readableStatusPosition(enemy: Vector3, head: Vector3?, height: Double): Vector3 {
    require(enemy.isFinite() && height.isFinite())
    val viewer = head?.takeIf { it.isFinite() } ?: return Vector3(enemy.x, height, enemy.z)
    val horizontal = Vector3(enemy.x - viewer.x, 0.0, enemy.z - viewer.z)
    val distance = horizontal.length()
    val direction = horizontal.normalizedOrNull() ?: Vector3(0.0, 0.0, -1.0)
    val position = viewer + direction * maxOf(distance, 1.8)
    return Vector3(position.x, height, position.z)
}

internal fun readableStatusRotation(position: Vector3, head: Vector3?): Quaternion {
    val viewer = head?.takeIf { it.isFinite() } ?: return Quaternion(0.0, 0.0, 0.0, 1.0)
    val horizontal = Vector3(viewer.x - position.x, 0.0, viewer.z - position.z)
    if (horizontal.normalizedOrNull() == null) return Quaternion(0.0, 0.0, 0.0, 1.0)
    val halfYaw = atan2(horizontal.x, horizontal.z) / 2.0
    return Quaternion(0.0, sin(halfYaw), 0.0, cos(halfYaw))
}

internal data class DamagePopupContent(
    val impactId: Long,
    val amount: Int,
    val headHit: Boolean,
    val fatal: Boolean,
    val guarded: Boolean,
)

internal data class DamagePopupFrame(
    val slot: Int,
    val content: DamagePopupContent,
    val position: Vector3,
    val opacity: Float,
    val scale: Float,
)

/** Four current contacts, aged in wall time independently of the enemy's hit-stop. */
internal class DamagePopupTimeline {
    private data class Entry(val content: DamagePopupContent, val origin: Vector3, val startedAt: Long)

    private val entries = arrayOfNulls<Entry>(SLOT_COUNT)
    private var round = Long.MIN_VALUE
    private var opponentRound = 0
    private var lastImpactId = Long.MIN_VALUE
    private var lastNow: Long? = null

    fun update(
        generation: Long,
        roundNumber: Int,
        active: Boolean,
        simulationNanos: Long,
        nowNanos: Long,
        headPosition: Vector3?,
        events: List<EnemyCombatEvent>,
    ): List<DamagePopupFrame> {
        if (generation < round) return emptyList()
        if (generation != round || roundNumber != opponentRound) {
            clear()
            if (generation != round) lastImpactId = Long.MIN_VALUE
            round = generation
            opponentRound = roundNumber
        }
        if (lastNow?.let { nowNanos < it } == true) clear()
        lastNow = nowNanos
        for (index in entries.indices) {
            if (entries[index]?.let { elapsed(nowNanos, it.startedAt) >= LIFETIME_NANOS } == true) {
                entries[index] = null
            }
        }
        val fresh = events.filterIsInstance<CombatImpact>().filter { it.id > lastImpactId }
            .distinctBy { it.id }.sortedBy { it.id }
        if (fresh.isNotEmpty()) lastImpactId = fresh.last().id
        if (!active) {
            clear()
            return emptyList()
        }
        for (impact in fresh.sortedBy { it.fatal }) {
            if (impact.appliedDamage == 0 || !impact.kind.damagesEnemy() || !impact.point.isFinite() ||
                impact.atNanos < 0L || impact.atNanos > simulationNanos
            ) continue
            val age = simulationNanos - impact.atNanos
            if (age > MAX_EVENT_AGE_NANOS) continue
            val slot = entries.indices.filter { impact.fatal || entries[it]?.content?.fatal != true }
                .minWithOrNull(compareBy<Int> { entries[it]?.content?.fatal == true }
                    .thenBy { entries[it]?.startedAt ?: Long.MIN_VALUE }
                    .thenBy { entries[it]?.content?.impactId ?: Long.MIN_VALUE }) ?: continue
            val toViewer = headPosition?.takeIf { it.isFinite() }?.minus(impact.point)
            val right = toViewer?.let { Vector3(it.z, 0.0, -it.x).normalizedOrNull() }
                ?: Vector3(1.0, 0.0, 0.0)
            val outward = toViewer?.normalizedOrNull() ?: Vector3(0.0, 0.0, 1.0)
            val side = if (slot % 2 == 0) 1.0 else -1.0
            val origin = impact.point + right * (side * (0.23 + slot / 2 * 0.05)) +
                outward * 0.025 + Vector3(0.0, 0.025 + slot / 2 * 0.035, 0.0)
            entries[slot] = Entry(
                DamagePopupContent(impact.id, impact.appliedDamage, impact.zone == HitZone.HEAD,
                    impact.fatal, impact.kind == CombatImpactKind.GUARDED_HIT),
                origin, nowNanos - age,
            )
        }
        return entries.mapIndexedNotNull { slot, entry ->
            entry ?: return@mapIndexedNotNull null
            val progress = elapsed(nowNanos, entry.startedAt).toDouble() / LIFETIME_NANOS
            val rise = 0.08 * (1.0 - (1.0 - progress) * (1.0 - progress))
            val bounce = if (progress < 0.3) sin(progress / 0.3 * PI) else 0.0
            val emphasis = when {
                entry.content.fatal -> 1.12
                entry.content.headHit -> 1.06
                else -> 1.0
            }
            val opacity = ((1.0 - progress) / 0.3).coerceIn(0.0, 1.0).toFloat()
            DamagePopupFrame(slot, entry.content, entry.origin + Vector3(0.0, rise + bounce * 0.012, 0.0),
                opacity, (emphasis * (1.0 + bounce * 0.08)).toFloat())
        }
    }

    fun clear() {
        entries.fill(null)
        lastNow = null
    }

    private fun elapsed(now: Long, start: Long): Long =
        (now - start).takeIf { it >= 0L } ?: Long.MAX_VALUE

    private fun CombatImpactKind.damagesEnemy(): Boolean = when (this) {
        CombatImpactKind.SOFT_HIT, CombatImpactKind.HARD_HIT, CombatImpactKind.GUARDED_HIT,
        CombatImpactKind.SKILL, CombatImpactKind.EXECUTION -> true
        CombatImpactKind.BLOCK, CombatImpactKind.PARRY, CombatImpactKind.PLAYER_HIT -> false
    }

    companion object {
        const val SLOT_COUNT = 4
        private const val LIFETIME_NANOS = 600_000_000L
        private const val MAX_EVENT_AGE_NANOS = 120_000_000L
    }
}
