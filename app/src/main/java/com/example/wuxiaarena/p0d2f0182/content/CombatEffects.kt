package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.OpacityControllerComponent
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.math.Quat
import kotlin.math.cos
import kotlin.math.sin
import com.pico.spatial.core.math.Vector3 as SpatialVector3

/** Main-thread contact presentation. Static GLB layers need no imported animation clips. */
internal class CombatEffects private constructor(
    private val root: Entity,
    private val slots: Map<Kind, List<Slot>>,
) : AutoCloseable {
    private enum class Kind(val asset: String, val seconds: Float) {
        SOFT("soft_contact", 0.62f),
        METAL("metal_contact", 0.44f),
        FORCE("force_contact", 0.72f),
        DUST("ground_dust", 0.65f),
    }

    private class Slot(
        val kind: Kind,
        val anchor: Entity,
        val core: Entity,
        val debris: Entity,
        val scar: Entity,
    ) {
        var startedAt: Long? = null
        var failed = false
        var impactKind: CombatImpactKind? = null

        fun hide() {
            startedAt = null
            try {
                if (anchor.valid) anchor.enabled = false
            } catch (error: Exception) {
                failed = true
                Log.w(TAG, "Unable to hide ${kind.asset}", error)
            }
        }

        fun update(now: Long) {
            val start = startedAt ?: return
            if (failed || !anchor.valid) return hide()
            val seconds = ((now - start).coerceAtLeast(0L) / 1_000_000_000.0).toFloat()
            val parry = impactKind == CombatImpactKind.PARRY
            val duration = kind.seconds + if (parry) 0.10f else 0f
            if (seconds >= duration) return hide()
            val progress = seconds / duration
            try {
                // A brief contact core, expanding material fragments, and a longer thin cut.
                val coreSize = (0.7f + seconds * 3f) * if (parry) 1.3f else 1f
                val coreDuration = if (parry) 0.22f else 0.18f
                layer(core, coreSize, coreSize,
                    (1f - seconds / coreDuration).coerceIn(0f, 1f), 0f, 0f)
                val spread = 0.22f + progress * 1.1f
                layer(debris, spread, spread, (1f - progress) * (1f - progress),
                    -0.32f * seconds * seconds, 0.14f * seconds)
                val cutAlpha = ((duration - seconds) / 0.24f).coerceIn(0f, 1f)
                val cutWidth = ((duration - seconds) / 0.30f).coerceIn(0.08f, 1f)
                layer(scar, 1f, cutWidth, cutAlpha, 0f, 0.004f)
            } catch (error: Exception) {
                failed = true
                Log.w(TAG, "Contact layer ${kind.asset} became unavailable", error)
                hide()
            }
        }

        fun close() {
            hide()
            try {
                if (anchor.valid) anchor.destroy()
            } catch (error: Exception) {
                Log.w(TAG, "Unable to destroy ${kind.asset}", error)
            }
        }

        private fun layer(entity: Entity, width: Float, height: Float, opacity: Float, y: Float, z: Float) {
            entity.enabled = opacity > 0.005f
            transform(entity).setScaleVector(SpatialVector3(width, height, 1f))
            transform(entity).setPosition(SpatialVector3(0f, y, z))
            checkNotNull(entity.components[OpacityControllerComponent::class.java]).opacity = opacity
        }
    }

    private var closed = false
    private val allSlots = slots.values.flatten()
    private var round = Long.MIN_VALUE
    private val seenImpacts = mutableSetOf<Long>()
    private val pending = ArrayDeque<CombatImpact>()
    private val unavailableKinds = mutableSetOf<Kind>()
    private var lastStepTravel = 0.0
    private var stepSide = 1.0
    private var deathDustPending = false

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (closed || !root.valid || state.roundGeneration < round) return
        val now = System.nanoTime()
        if (state.roundGeneration != round) {
            clear()
            seenImpacts.clear()
            round = state.roundGeneration
            lastStepTravel = state.enemyTravelMeters
        }
        val impacts = events.filterIsInstance<CombatImpact>().filter { seenImpacts.add(it.id) }
        val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
        if (!state.sceneReady || (!terminal && (state.pauseReason != null || !state.inputReady))) {
            clear()
            lastStepTravel = state.enemyTravelMeters
            return
        }
        allSlots.forEach { it.update(now) }
        for (impact in impacts) {
            if (impact.point.isFinite() && impact.normal.normalizedOrNull() != null && impact.strength.isFinite()) {
                pending.addLast(impact)
            } else {
                Log.w(TAG, "Invalid contact presentation id=${impact.id}")
            }
        }
        // Busy slots queue contacts instead of overwriting another contact from the same batch.
        repeat(pending.size) {
            val impact = pending.removeFirst()
            val kind = kindFor(impact.kind)
            val pool = slots.getValue(kind)
            if (pool.none { !it.failed && it.anchor.valid }) {
                if (unavailableKinds.add(kind)) Log.w(TAG, "No valid contact slots for $kind")
            } else {
                val slot = pool.firstOrNull { !it.failed && it.anchor.valid && it.startedAt == null }
                if (slot == null) {
                    pending.addLast(impact)
                } else {
                    val normal = checkNotNull(impact.normal.normalizedOrNull())
                    val strength = impact.strength.coerceIn(0.0, 1.0)
                    val scale = (0.72 + 0.46 * strength).toFloat()
                    val age = (state.simulationNanos - impact.atNanos).coerceAtLeast(0L).coerceAtMost(80_000_000L)
                    slot.impactKind = impact.kind
                    emit(slot, impact.point + normal * 0.008, contactRotation(normal, impact.hand), scale, now, age)
                }
            }
        }
        if (state.result == TrialResult.FIGHTING && state.enemyMoveDirection != 0f &&
            state.enemyTravelMeters.isFinite() && state.enemyTravelMeters - lastStepTravel >= 0.5
        ) {
            lastStepTravel = state.enemyTravelMeters
            state.enemyPosition?.let { enemy ->
                val foot = enemy + Vector3(cos(state.enemyYawRadians.toDouble()) * 0.09 * stepSide,
                    0.0, -sin(state.enemyYawRadians.toDouble()) * 0.09 * stepSide)
                dust(foot, 0.55f, now)
                stepSide = -stepSide
            }
        }
        if (events.any { it is EnemyCombatEvent.PhaseChanged && it.current == EnemyPhase.DEAD }) {
            deathDustPending = true
        }
        val floorImpact = if (state.executing) 2.35f else 1.6f
        if (deathDustPending && state.phase == EnemyPhase.DEAD && state.deathElapsedSeconds >= floorImpact) {
            deathDustPending = false
            state.enemyPosition?.let { dust(it, 1f, now) }
        }
    }

    private fun dust(position: Vector3, scale: Float, now: Long) {
        val slot = slots.getValue(Kind.DUST).firstOrNull { !it.failed && it.anchor.valid && it.startedAt == null } ?: return
        slot.impactKind = null
        // Dust is authored in XY; rotate its outward axis onto Stage +Y at the floor.
        emit(slot, position, Quaternion(-sin(Math.PI / 4), 0.0, 0.0, cos(Math.PI / 4)), scale, now, 0L)
    }

    private fun emit(slot: Slot, position: Vector3, rotation: Quaternion, scale: Float, now: Long, age: Long) {
        val point = SpatialVector3(position.x.toFloat(), position.y.toFloat(), position.z.toFloat())
        if (!point.x.isFinite() || !point.y.isFinite() || !point.z.isFinite()) {
            Log.w(TAG, "Contact position exceeds Stage presentation range")
            return
        }
        val orientation = rotation.normalizedOrNull() ?: return
        try {
            transform(slot.anchor).setPosition(root.convertPositionFrom(point, null))
            transform(slot.anchor).setQuaternion(root.convertRotationFrom(
                Quat(orientation.x.toFloat(), orientation.y.toFloat(), orientation.z.toFloat(), orientation.w.toFloat()), null))
            transform(slot.anchor).setScaleVector(SpatialVector3(scale, scale, scale))
            slot.startedAt = now - age
            slot.anchor.enabled = true
            slot.update(now)
        } catch (error: Exception) {
            slot.failed = true
            Log.w(TAG, "Unable to present ${slot.kind.asset}", error)
            slot.hide()
        }
    }

    private fun clear() {
        allSlots.forEach { it.hide() }
        pending.clear()
        deathDustPending = false
    }

    override fun close() {
        if (closed) return
        closed = true
        clear()
        allSlots.forEach { it.close() }
        seenImpacts.clear()
    }

    companion object {
        private const val TAG = "ArenaEffects"
        private const val SLOTS_PER_KIND = 6

        /** Main-thread owner closes the pool before destroying its scene root. */
        suspend fun load(root: Entity): CombatEffects {
            val loaded = mutableMapOf<Kind, List<Slot>>()
            val owned = mutableListOf<Slot>()
            try {
                for (kind in Kind.entries) {
                    val pool = mutableListOf<Slot>()
                    repeat(SLOTS_PER_KIND) {
                        val slot = loadSlot(root, kind)
                        owned.add(slot)
                        pool.add(slot)
                    }
                    loaded[kind] = pool
                }
                return CombatEffects(root, loaded)
            } catch (error: Exception) {
                owned.forEach { it.close() }
                Log.w(TAG, "Unable to load static contact layers", error)
                throw error
            }
        }

        private suspend fun loadSlot(root: Entity, kind: Kind): Slot {
            val model = Entity.loadSuspend("asset://models/effects/${kind.asset}.glb")
            var anchor: Entity? = null
            var attached = false
            try {
                check(root.valid) { "Effect scene root was released during loading" }
                val parent = Entity()
                anchor = parent
                parent.enabled = false
                check(root.addChild(parent)) { "Unable to attach effect anchor" }
                check(parent.addChild(model)) { "Unable to attach static effect model" }
                attached = true
                val layers = listOf("core", "debris", "scar").map { name ->
                    checkNotNull(model.findEntity(name)) { "Missing contact layer $name in ${kind.asset}" }.also {
                        it.components.set(OpacityControllerComponent(1f))
                    }
                }
                return Slot(kind, parent, layers[0], layers[1], layers[2])
            } catch (error: Exception) {
                if (!attached) try { model.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                try { anchor?.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                throw error
            }
        }

        private fun kindFor(kind: CombatImpactKind): Kind = when (kind) {
            CombatImpactKind.SOFT_HIT, CombatImpactKind.PLAYER_HIT -> Kind.SOFT
            CombatImpactKind.HARD_HIT, CombatImpactKind.GUARDED_HIT,
            CombatImpactKind.BLOCK, CombatImpactKind.PARRY -> Kind.METAL
            CombatImpactKind.SKILL, CombatImpactKind.EXECUTION -> Kind.FORCE
        }

        private fun contactRotation(normal: Vector3, hand: Hand): Quaternion {
            val facing = Quaternion(-normal.y, normal.x, 0.0, 1.0 + normal.z).normalizedOrNull()
                ?: Quaternion(0.0, 1.0, 0.0, 0.0)
            val roll = if (hand == Hand.LEFT) -0.30 else 0.30
            return facing * Quaternion(0.0, 0.0, sin(roll / 2), cos(roll / 2))
        }

        private fun transform(entity: Entity): TransformComponent =
            checkNotNull(entity.components[TransformComponent::class.java]) { "Effect transform is unavailable" }
    }
}
