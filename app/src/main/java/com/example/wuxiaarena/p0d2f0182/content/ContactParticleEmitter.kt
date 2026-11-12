package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.OpacityControllerComponent
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3 as SpatialVector3

/** One GLB instance per slot, one transform and opacity controller per independent mesh. */
internal class ContactParticleEmitter private constructor(private val root: Entity, private val slots: List<Slot>) : AutoCloseable {
    private class Slot(
        val definition: ContactEffectDefinition, val anchor: Entity,
        val nodes: Map<String, Entity>,
    ) {
        private val softDuration = if (definition.family == ContactEffectFamily.SOFT) {
            SoftContactEnvelope.duration(definition.particles)
        } else 0.0
        var start: Long? = null
        var basis: ContactBasis? = null
        var parry = false
        var softBodyCut = false
        var size = 1f
        var failed = false

        fun hide() {
            start = null
            if (anchor.valid) anchor.enabled = false
        }

        fun update(now: Long) {
            val began = start ?: return
            if (!anchor.valid || failed) return hide()
            val age = (now.toDouble() - began.toDouble()) / 1_000_000_000.0
            var visible = false
            for (core in definition.cores) {
                if (softBodyCut) {
                    val layer = SoftContactEnvelope.layer(core.node, age, size, basis != null)
                    show(checkNotNull(nodes[core.node]), core.position, layer.rotation, layer.scale, layer.opacity)
                    visible = visible || layer.opacity > 0.005f
                    continue
                }
                val keys = if (parry) core.parry else core.normal
                val opacity = if (age < 0.0 || age >= keys.last().seconds || (core.directional && basis == null)) 0f
                    else opacityAt(keys, age)
                val coreScale = if (definition.family == ContactEffectFamily.METAL) {
                    if (parry) 2.6f else 1.9f
                } else if (parry) 1.7f else 1.15f
                val growth = (0.85 + minOf(age, 0.09) * 3.0).toFloat() * size * coreScale
                show(checkNotNull(nodes[core.node]), core.position, Quaternion(0.0, 0.0, 0.0, 1.0), growth, opacity)
                visible = visible || opacity > 0.005f
            }
            for ((index, particle) in definition.particles.withIndex()) {
                val soft = if (softBodyCut) {
                    SoftContactEnvelope.debris(index, age, size, particle.lifetime)
                } else null
                val frame = if (soft != null && soft.opacity <= 0.005f) null else basis?.let {
                    sampleContactParticle(particle, age, it, soft?.velocityGain ?: if (parry) 1.8 else 1.0)
                }
                val node = checkNotNull(nodes[particle.node])
                if (frame == null) node.enabled = false else {
                    if (soft != null) {
                        show(node, frame.position, frame.rotation, soft.scale, soft.opacity)
                        visible = visible || soft.opacity > 0.005f
                        continue
                    }
                    // Size changes the cross-section, never Stage gravity or the physical trajectory.
                    val scale = size * if (definition.family == ContactEffectFamily.METAL) {
                        if (parry) 1.65f else 1.25f
                    } else 1f
                    show(node, frame.position, frame.rotation, scale, frame.opacity)
                    visible = visible || frame.opacity > 0.005f
                }
            }
            // Keep each slot alive until its actual lifetime, including initially invisible frames.
            val end = if (softBodyCut) softDuration
                else maxOf(definition.particles.maxOfOrNull { it.lifetime } ?: 0.0,
                    definition.cores.maxOfOrNull { (if (parry) it.parry else it.normal).last().seconds } ?: 0.0)
            if (!visible && age >= end) hide()
        }

        private fun show(entity: Entity, position: Vector3, rotation: Quaternion, size: Float, opacity: Float) {
            show(entity, position, rotation, Vector3(size.toDouble(), size.toDouble(), size.toDouble()), opacity)
        }

        private fun show(entity: Entity, position: Vector3, rotation: Quaternion, scale: Vector3, opacity: Float) {
            entity.enabled = opacity > 0.005f
            if (!entity.enabled) return
            transform(entity).setPosition(position.spatial())
            transform(entity).setQuaternion(rotation.spatial())
            transform(entity).setScaleVector(scale.spatial())
            checkNotNull(entity.components[OpacityControllerComponent::class.java]).opacity = opacity
        }
    }

    private val reserved = mutableSetOf<Slot>()
    private var closed = false

    fun update(now: Long) {
        if (closed) return
        reserved.clear()
        slots.forEach { slot -> safely(slot) { slot.update(now) } }
    }

    /** Caller provides a fresh resolved event; no delayed queue exists. */
    fun emit(
        family: ContactEffectFamily, point: Vector3, normal: Vector3, tangent: Vector3?,
        now: Long, ageNanos: Long, parry: Boolean = false, size: Float = 1f, softBodyCut: Boolean = false,
    ): Boolean {
        if (closed || !root.valid || ageNanos !in 0L..120_000_000L || !point.isFinite() ||
            !size.isFinite() || size <= 0f) return false
        val n = normal.normalizedOrNull() ?: return false
        val basis = ContactBasis.from(n, tangent)
        val slot = slots.filter { it.definition.family == family && !it.failed && it.anchor.valid && it !in reserved }
            .minWithOrNull(compareBy<Slot> { it.start != null }.thenBy { it.start ?: Long.MIN_VALUE }) ?: return false
        reserved.add(slot)
        val position = (point + n * 0.008).spatial()
        if (!position.x.isFinite() || !position.y.isFinite() || !position.z.isFinite()) return false
        val orientation = basis?.rotation() ?: normalFacingRotation(n) ?: return false
        return safely(slot) {
            slot.hide()
            transform(slot.anchor).setPosition(root.convertPositionFrom(position, null))
            transform(slot.anchor).setQuaternion(root.convertRotationFrom(orientation.spatial(), null))
            slot.start = now - ageNanos
            slot.basis = basis
            slot.parry = parry
            slot.softBodyCut = softBodyCut && family == ContactEffectFamily.SOFT
            slot.size = size.coerceIn(0.75f, 1.5f)
            slot.anchor.enabled = true
            slot.update(now)
        }
    }

    fun clear() {
        reserved.clear()
        slots.forEach { slot -> safely(slot) { slot.hide() } }
    }

    override fun close() {
        if (closed) return
        closed = true
        slots.forEach { slot -> safely(slot) { if (slot.anchor.valid) slot.anchor.destroy() } }
    }

    private fun safely(slot: Slot, block: () -> Unit): Boolean = try {
        block()
        true
    } catch (error: Exception) {
        slot.failed = true
        slot.start = null
        try { if (slot.anchor.valid) slot.anchor.enabled = false } catch (_: Exception) { }
        Log.w("ArenaParticles", "Contact slot unavailable: ${slot.definition.family}", error)
        false
    }

    companion object {
        suspend fun load(root: Entity): ContactParticleEmitter {
            val owned = mutableListOf<Slot>()
            try {
                for (definition in CONTACT_EFFECT_DEFINITIONS) {
                    repeat(3) { owned.add(loadSlot(root, definition)) }
                }
                return ContactParticleEmitter(root, owned)
            } catch (error: Exception) {
                owned.forEach { try { it.anchor.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) } }
                throw error
            }
        }

        private suspend fun loadSlot(root: Entity, definition: ContactEffectDefinition): Slot {
            val model = Entity.loadSuspend("asset://models/effects/contact-polish/${definition.asset}")
            var anchor: Entity? = null
            var attached = false
            try {
                check(root.valid) { "Contact scene released while loading" }
                val parent = Entity()
                anchor = parent
                parent.enabled = false
                check(root.addChild(parent))
                check(parent.addChild(model))
                attached = true
                val names = definition.particles.map { it.node } + definition.cores.map { it.node }
                val nodes = names.associateWith { name ->
                    checkNotNull(model.findEntity(name)) { "Missing independent contact node $name" }.also {
                        it.components.set(OpacityControllerComponent(0f))
                        it.enabled = false
                    }
                }
                return Slot(definition, parent, nodes)
            } catch (error: Exception) {
                if (!attached) try { model.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                try { anchor?.destroy() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                throw error
            }
        }

        private fun transform(entity: Entity) = checkNotNull(entity.components[TransformComponent::class.java])
        private fun Vector3.spatial() = SpatialVector3(x.toFloat(), y.toFloat(), z.toFloat())
        private fun Quaternion.spatial() = Quat(x.toFloat(), y.toFloat(), z.toFloat(), w.toFloat())
    }
}
