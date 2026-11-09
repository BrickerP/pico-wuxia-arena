package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.ecs.animation.AnimationPlayConfig
import com.pico.spatial.core.ecs.animation.AnimationPlaybackController
import com.pico.spatial.core.ecs.resource.AnimationResource
import com.pico.spatial.core.math.Quat
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import com.pico.spatial.core.math.Vector3 as SpatialVector3

/** Small pooled effects. Every position supplied here is in Stage metres. */
internal class CombatEffects private constructor(
    private val root: Entity,
    private val slots: Map<Kind, Slot>,
) : AutoCloseable {
    private enum class Kind(val asset: String, val clip: String, val seconds: Float) {
        SPARKS("metal_sparks", "metal_sparks_burst", 0.24f),
        ARC("blade_arc", "blade_arc_cut", 0.18f),
        RING("break_ring", "break_ring_release", 0.44f),
        DUST("foot_dust", "foot_dust_settle", 0.52f),
    }

    private class Slot(
        val kind: Kind,
        val anchor: Entity,
        val resources: List<AnimationResource>,
        val repeated: List<AnimationResource>,
        val controllers: List<AnimationPlaybackController>,
    ) {
        var startedAt: Long? = null
        var failed = controllers.isEmpty()

        fun hide() {
            startedAt = null
            try {
                if (anchor.valid) anchor.enabled = false
            } catch (error: Exception) {
                Log.w(TAG, "Unable to hide ${kind.asset}", error)
            }
        }

        fun update(now: Long) {
            val start = startedAt ?: return
            if (failed || !anchor.valid) return hide()
            val seconds = ((now - start).coerceAtLeast(0L) / 1_000_000_000.0).toFloat()
            if (seconds >= kind.seconds) return hide()
            try {
                for (controller in controllers) {
                    check(controller.valid) { "Effect playback controller became unavailable" }
                    controller.setTime(seconds.coerceAtMost(controller.getDuration()))
                }
            } catch (error: Exception) {
                failed = true
                Log.w(TAG, "Effect ${kind.asset} disabled after presentation failure", error)
                hide()
            }
        }

        fun close() {
            hide()
            controllers.forEach { release(it, kind.asset) }
            repeated.forEach { release(it, kind.asset) }
            resources.forEach { release(it, kind.asset) }
            try {
                if (anchor.valid) anchor.destroy()
            } catch (error: Exception) {
                Log.w(TAG, "Unable to destroy ${kind.asset}", error)
            }
        }
    }

    private var closed = false
    private var round = Long.MIN_VALUE
    private var lastFeedback = Long.MIN_VALUE
    private var lastStepTravel = 0.0
    private var stepSide = 1.0
    private var previousBladeTip: Vector3? = null
    private var sweepDirection: Vector3? = null
    private var deathDustPending = false

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (closed || !root.valid) return
        val now = System.nanoTime()
        if (state.roundGeneration != round) {
            clear()
            round = state.roundGeneration
            lastFeedback = state.feedbackSequence
            lastStepTravel = state.enemyTravelMeters
            return
        }
        val active = state.result == TrialResult.FIGHTING || state.result == TrialResult.ROUND_CLEAR
        if (!active || state.pauseReason != null || !state.inputReady || !state.sceneReady) {
            clear()
            lastFeedback = state.feedbackSequence
            lastStepTravel = state.enemyTravelMeters
            return
        }
        val tip = state.playerBladeTip?.takeIf { it.isFinite() }
        val oldTip = previousBladeTip
        if (tip != null && oldTip != null && tip.distanceTo(oldTip) > 0.003) {
            sweepDirection = (tip - oldTip).normalizedOrNull()
        }
        previousBladeTip = tip

        slots.values.forEach { it.update(now) }
        if (state.feedbackSequence > lastFeedback) {
            lastFeedback = state.feedbackSequence
            feedback(state, now)
        }
        if (state.result == TrialResult.FIGHTING && state.enemyMoveDirection != 0f &&
            state.enemyTravelMeters.isFinite() && state.enemyTravelMeters - lastStepTravel >= 0.5
        ) {
            lastStepTravel = state.enemyTravelMeters
            state.enemyPosition?.let { enemy ->
                val foot = enemy + Vector3(cos(state.enemyYawRadians.toDouble()) * 0.09 * stepSide,
                    0.0, -sin(state.enemyYawRadians.toDouble()) * 0.09 * stepSide)
                emit(Kind.DUST, foot, Quaternion(0.0, 0.0, 0.0, 1.0), 0.55f, now)
                stepSide = -stepSide
            }
        }
        if (events.any { it is EnemyCombatEvent.PhaseChanged && it.current == EnemyPhase.DEAD }) {
            deathDustPending = true
        }
        val floorImpact = if (state.executing) 2.35f else 1.6f
        if (deathDustPending && state.phase == EnemyPhase.DEAD && state.deathElapsedSeconds >= floorImpact) {
            deathDustPending = false
            state.enemyPosition?.let { emit(Kind.DUST, it, identity(), 1f, now) }
        }
    }

    private fun feedback(state: ArenaViewState, now: Long) {
        val enemy = state.enemyPosition ?: return
        val enemyFacing = yaw(state.enemyYawRadians.toDouble())
        val body = enemy + Vector3(0.0, if (state.feedback == CombatFeedback.HEADSHOT) 1.60 else 1.15, 0.0)
        val base = state.playerBladeBase
        val tip = state.playerBladeTip
        val target = if (state.feedback == CombatFeedback.BLOCK || state.feedback == CombatFeedback.PARRY) {
            val head = state.playerHeadPosition ?: return
            val forward = Vector3(enemy.x - head.x, 0.0, enemy.z - head.z).normalizedOrNull() ?: return
            head + forward * 0.32 + Vector3(0.0, 0.05, 0.0)
        } else body
        val contact = if (base != null && tip != null && base.isFinite() && tip.isFinite()) {
            val blade = tip - base
            val squared = blade.dot(blade)
            if (squared > 1e-8) base + blade * (((target - base).dot(blade) / squared).coerceIn(0.0, 1.0)) else target
        } else target
        val arcRotation = bladeRotation(base, tip, enemyFacing)
        when (state.feedback) {
            CombatFeedback.HIT, CombatFeedback.HEADSHOT -> {
                emit(Kind.ARC, base ?: contact, arcRotation, 1f, now)
            }
            CombatFeedback.GUARDED_HIT, CombatFeedback.BLOCK, CombatFeedback.PARRY -> {
                emit(Kind.SPARKS, contact, enemyFacing, if (state.feedback == CombatFeedback.PARRY) 0.85f else 0.60f, now)
            }
            CombatFeedback.SKILL, CombatFeedback.EXECUTION -> {
                emit(Kind.RING, enemy, identity(), if (state.executing) 0.90f else 1.15f, now)
                emit(Kind.ARC, base ?: contact, arcRotation, 1.25f, now)
            }
            CombatFeedback.DODGE, CombatFeedback.GUARD_BREAK -> {
                state.playerHeadPosition?.let { head ->
                    emit(Kind.DUST, Vector3(head.x, enemy.y, head.z), identity(), 0.65f, now)
                }
            }
            else -> Unit
        }
    }

    private fun bladeRotation(base: Vector3?, tip: Vector3?, default: Quaternion): Quaternion {
        val axis = if (base != null && tip != null) (tip - base).normalizedOrNull() else null
        val motion = sweepDirection
        val normal = if (axis != null && motion != null) axis.cross(motion).normalizedOrNull() else null
        if (axis == null || normal == null) return default
        val turn = Quaternion(-normal.y, normal.x, 0.0, 1.0 + normal.z).normalizedOrNull()
            ?: Quaternion(0.0, 1.0, 0.0, 0.0)
        val right = checkNotNull(turn.rotate(Vector3(1.0, 0.0, 0.0)))
        val angle = atan2(normal.dot(right.cross(axis)), right.dot(axis))
        val half = angle / 2.0
        return Quaternion(normal.x * sin(half), normal.y * sin(half), normal.z * sin(half), cos(half)) * turn
    }

    private fun emit(kind: Kind, position: Vector3, rotation: Quaternion, size: Float, now: Long) {
        if (!position.isFinite()) return
        val slot = slots.getValue(kind)
        if (slot.failed || !slot.anchor.valid) return
        val point = SpatialVector3(position.x.toFloat(), position.y.toFloat(), position.z.toFloat())
        if (!point.x.isFinite() || !point.y.isFinite() || !point.z.isFinite()) return
        try {
            val orientation = checkNotNull(rotation.normalizedOrNull())
            transform(slot.anchor).setPosition(root.convertPositionFrom(point, null))
            transform(slot.anchor).setQuaternion(root.convertRotationFrom(
                Quat(orientation.x.toFloat(), orientation.y.toFloat(), orientation.z.toFloat(), orientation.w.toFloat()), null))
            transform(slot.anchor).setScaleVector(SpatialVector3(size, size, size))
            slot.startedAt = now
            for (controller in slot.controllers) controller.setTime(0f)
            slot.anchor.enabled = true
            slot.update(now)
        } catch (error: Exception) {
            slot.failed = true
            Log.w(TAG, "Unable to present ${kind.asset}", error)
            slot.hide()
        }
    }

    private fun clear() {
        slots.values.forEach { it.hide() }
        previousBladeTip = null
        sweepDirection = null
        deathDustPending = false
    }

    override fun close() {
        if (closed) return
        closed = true
        clear()
        slots.values.forEach { it.close() }
    }

    companion object {
        private const val TAG = "ArenaEffects"

        /** Caller owns the returned pool and closes it before destroying the scene root. */
        suspend fun load(root: Entity): CombatEffects {
            val loaded = mutableMapOf<Kind, Slot>()
            try {
                for (kind in Kind.entries) loaded[kind] = loadSlot(root, kind)
                return CombatEffects(root, loaded)
            } catch (error: Exception) {
                loaded.values.forEach { it.close() }
                Log.w(TAG, "Unable to load combat effects", error)
                throw error
            }
        }

        private suspend fun loadSlot(root: Entity, kind: Kind): Slot {
            var model: Entity? = null
            var anchor: Entity? = null
            var modelAttached = false
            val resources = mutableListOf<AnimationResource>()
            val repeated = mutableListOf<AnimationResource>()
            val controllers = mutableListOf<AnimationPlaybackController>()
            try {
                model = Entity.loadSuspend("asset://models/effects/${kind.asset}.glb")
                check(root.valid) { "Effect scene root was released during loading" }
                val parent = Entity()
                anchor = parent
                parent.enabled = false
                check(root.addChild(parent)) { "Unable to attach effect anchor" }
                check(parent.addChild(model)) { "Unable to attach effect model" }
                modelAttached = true
                val pending = ArrayDeque<Entity>()
                pending.addLast(model)
                while (pending.isNotEmpty()) {
                    val owner = pending.removeFirst()
                    for (resource in owner.getAnimationResources()) {
                        resources += resource
                        if (resource.getName() == kind.clip) {
                            val single = resource.repeat(0)
                            repeated += single
                            val controller = owner.playAnimation(single, AnimationPlayConfig(transitionDuration = 0f))
                            controllers += controller
                            controller.pause()
                            controller.setTime(0f)
                        }
                    }
                    owner.getChildren().forEach { pending.addLast(it) }
                }
                if (controllers.isEmpty()) {
                    Log.w(TAG, "Effect ${kind.asset} disabled because its authored animation was not imported")
                }
                return Slot(kind, parent, resources, repeated, controllers)
            } catch (error: Exception) {
                controllers.forEach { release(it, kind.asset) }
                repeated.forEach { release(it, kind.asset) }
                resources.forEach { release(it, kind.asset) }
                if (!modelAttached) {
                    try { model?.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                }
                try { anchor?.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                throw error
            }
        }

        private fun transform(entity: Entity): TransformComponent =
            checkNotNull(entity.components[TransformComponent::class.java]) { "Effect transform is unavailable" }

        private fun release(resource: AutoCloseable, label: String) {
            try {
                resource.close()
            } catch (error: Exception) {
                Log.w(TAG, "Unable to release effect resource $label", error)
            }
        }

        private fun identity() = Quaternion(0.0, 0.0, 0.0, 1.0)
        private fun yaw(angle: Double) = Quaternion(0.0, sin(angle / 2.0), 0.0, cos(angle / 2.0))
    }
}
