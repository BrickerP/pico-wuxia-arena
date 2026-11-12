package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedbackProfile
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.OpacityControllerComponent
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3 as SpatialVector3

/** Keep transient visuals on the contact beat, including after a delayed frame. */
internal fun currentContactImpacts(impacts: List<CombatImpact>, simulationNanos: Long): List<CombatImpact> =
    impacts.filter { impact ->
        impact.atNanos >= 0L && impact.atNanos <= simulationNanos &&
            simulationNanos - impact.atNanos <= 120_000_000L &&
            impact.point.isFinite() && impact.normal.normalizedOrNull() != null && impact.strength.isFinite()
    }.sortedWith(compareByDescending<CombatImpact> { it.fatal }
        .thenByDescending { it.kind == CombatImpactKind.PARRY }.thenByDescending { it.id })

/** Contact events use independent meshes. Force layers remain the authored skill envelope. */
internal class CombatEffects private constructor(
    private val root: Entity,
    private val particles: ContactParticleEmitter,
    private val forceSlots: List<ForceSlot>,
) : AutoCloseable {
    private class ForceSlot(val anchor: Entity, val core: Entity, val debris: Entity, val scar: Entity) {
        var start: Long? = null
        var directional = false
        var failed = false

        fun hide() { start = null; if (anchor.valid) anchor.enabled = false }

        fun update(now: Long) {
            val began = start ?: return
            val age = ((now.toDouble() - began.toDouble()) / 1_000_000_000.0).toFloat()
            if (!anchor.valid || failed || age >= 0.72f) return hide()
            val progress = age / 0.72f
            layer(core, 0.9f + age * 3f, 0.9f + age * 3f, (1f - age / 0.12f).coerceIn(0f, 1f), 0f, 0f)
            val spread = 0.22f + progress * 1.1f
            layer(debris, spread, spread, (1f - progress) * (1f - progress), -0.32f * age * age, 0.14f * age)
            val alpha = if (directional) (1f - age / 0.10f).coerceIn(0f, 1f) else 0f
            layer(scar, 1f, alpha.coerceAtLeast(0.08f), alpha, 0f, 0.004f)
        }

        private fun layer(entity: Entity, width: Float, height: Float, opacity: Float, y: Float, z: Float) {
            entity.enabled = opacity > 0.005f
            transform(entity).setScaleVector(SpatialVector3(width, height, 1f))
            transform(entity).setPosition(SpatialVector3(0f, y, z))
            checkNotNull(entity.components[OpacityControllerComponent::class.java]).opacity = opacity
        }
    }

    private var closed = false
    private var round = Long.MIN_VALUE
    private val seenImpacts = mutableSetOf<Long>()

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (closed || !root.valid || state.roundGeneration < round) return
        val now = System.nanoTime()
        if (state.roundGeneration != round) {
            clear()
            seenImpacts.clear()
            round = state.roundGeneration
        }
        // Consume while paused as well, so a resumed frame cannot replay a queued core.
        val impacts = events.filterIsInstance<CombatImpact>().filter { seenImpacts.add(it.id) }
        val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
        if (!state.sceneReady || (!terminal && (state.pauseReason != null || !state.inputReady))) {
            clear()
            return
        }
        particles.update(now)
        forceSlots.forEach { slot -> safely(slot) { slot.update(now) } }
        val reservedForce = mutableSetOf<ForceSlot>()
        for (impact in currentContactImpacts(impacts, state.simulationNanos)) {
            val accent = CombatFeedbackProfile.accent(impact)
            val scale = ((0.72 + 0.46 * accent.strength).toFloat() * accent.visualScale).coerceIn(0.75f, 1.5f)
            val age = state.simulationNanos - impact.atNanos
            if (impact.kind == CombatImpactKind.SKILL || impact.kind == CombatImpactKind.EXECUTION) {
                val slot = forceSlots.filter { !it.failed && it.anchor.valid && it !in reservedForce }
                    .minWithOrNull(compareBy<ForceSlot> { it.start != null }.thenBy { it.start ?: Long.MIN_VALUE }) ?: continue
                reservedForce.add(slot)
                emitForce(slot, impact, scale, now, age)
            } else {
                val family = when (impact.kind) {
                    CombatImpactKind.SOFT_HIT, CombatImpactKind.PLAYER_HIT -> ContactEffectFamily.SOFT
                    else -> ContactEffectFamily.METAL
                }
                val accepted = particles.emit(family, impact.point, impact.normal, impact.tangent, now, age,
                    parry = impact.kind == CombatImpactKind.PARRY, size = scale,
                    softBodyCut = impact.kind == CombatImpactKind.SOFT_HIT && impact.zone == HitZone.BODY)
                // Receipt evidence only: a consumed event does not prove SDK pixels or native input.
                val mode = if (ContactBasis.from(impact.normal, impact.tangent) != null) "core_particles" else "core_only"
                Log.i(TAG, "Contact consumed id=${impact.id} kind=${impact.kind} family=$family " +
                    "accepted=$accepted mode=$mode ageNs=$age round=${state.roundGeneration} origin=${state.inputOrigin}")
            }
        }
    }

    private fun emitForce(slot: ForceSlot, impact: CombatImpact, scale: Float, now: Long, age: Long) {
        val normal = impact.normal.normalizedOrNull() ?: return
        val basis = ContactBasis.from(normal, impact.tangent)
        val rotation = basis?.rotation() ?: normalFacingRotation(normal) ?: return
        val point = impact.point + normal * 0.008
        val stagePoint = SpatialVector3(point.x.toFloat(), point.y.toFloat(), point.z.toFloat())
        if (!stagePoint.x.isFinite() || !stagePoint.y.isFinite() || !stagePoint.z.isFinite()) return
        safely(slot) {
            transform(slot.anchor).setPosition(root.convertPositionFrom(stagePoint, null))
            transform(slot.anchor).setQuaternion(root.convertRotationFrom(
                Quat(rotation.x.toFloat(), rotation.y.toFloat(), rotation.z.toFloat(), rotation.w.toFloat()), null))
            transform(slot.anchor).setScaleVector(SpatialVector3(scale, scale, scale))
            slot.directional = basis != null
            slot.start = now - age
            slot.anchor.enabled = true
            slot.update(now)
        }
    }

    private fun clear() {
        particles.clear()
        forceSlots.forEach { slot -> safely(slot) { slot.hide() } }
    }

    private fun safely(slot: ForceSlot, block: () -> Unit) {
        try { block() } catch (error: Exception) {
            slot.failed = true
            slot.start = null
            try { if (slot.anchor.valid) slot.anchor.enabled = false } catch (_: Exception) { }
            Log.w(TAG, "Force slot became unavailable", error)
        }
    }

    override fun close() {
        if (closed) return
        closed = true
        particles.close()
        forceSlots.forEach { slot -> safely(slot) { if (slot.anchor.valid) slot.anchor.destroy() } }
    }

    companion object {
        private const val TAG = "ArenaEffects"
        suspend fun load(root: Entity): CombatEffects {
            val particles = ContactParticleEmitter.load(root)
            val force = mutableListOf<ForceSlot>()
            try {
                repeat(2) { force.add(loadForce(root)) }
                return CombatEffects(root, particles, force)
            } catch (error: Exception) {
                particles.close()
                force.forEach { try { it.anchor.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) } }
                throw error
            }
        }

        private suspend fun loadForce(root: Entity): ForceSlot {
            val model = Entity.loadSuspend("asset://models/effects/force_contact.glb")
            var anchor: Entity? = null
            var attached = false
            try {
                check(root.valid)
                val parent = Entity()
                anchor = parent
                parent.enabled = false
                check(root.addChild(parent))
                check(parent.addChild(model))
                attached = true
                val layers = listOf("core", "debris", "scar").map { name ->
                    checkNotNull(model.findEntity(name)).also { it.components.set(OpacityControllerComponent(1f)) }
                }
                return ForceSlot(parent, layers[0], layers[1], layers[2])
            } catch (error: Exception) {
                if (!attached) try { model.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                try { anchor?.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                throw error
            }
        }

        private fun transform(entity: Entity): TransformComponent = checkNotNull(entity.components[TransformComponent::class.java])
    }
}
