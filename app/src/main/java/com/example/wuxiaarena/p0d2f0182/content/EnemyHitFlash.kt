package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.ModelComponent
import com.pico.spatial.core.ecs.resource.BlendingMode
import com.pico.spatial.core.ecs.resource.PhysicallyBasedMaterial
import com.pico.spatial.core.ecs.resource.UnlitMaterial
import com.pico.spatial.core.math.Color4

/** Owns the short body-material override for one opponent, without modifying its PBR resources. */
internal class EnemyHitFlash(enemy: Entity) : AutoCloseable {
    private class Binding(
        val entity: Entity,
        val model: ModelComponent,
        val index: Int,
        val original: PhysicallyBasedMaterial,
        val flash: UnlitMaterial,
        var overridden: Boolean = false,
    )

    private val bindings = mutableListOf<Binding>()
    private val flashes = mutableMapOf<PhysicallyBasedMaterial, UnlitMaterial>()
    private val pulse = EnemyHitFlashPulse()
    private var round = Long.MIN_VALUE
    private var closed = false
    private var failed = false

    init {
        try {
            for (entity in enemy.findSkinnedMeshEntity(includeDisabled = true)) {
                val model = entity.components[ModelComponent::class.java] ?: continue
                for (index in 0 until model.materials.size) {
                    val original = model.materials[index] as? PhysicallyBasedMaterial ?: continue
                    if (!original.getName().startsWith("tripo_", ignoreCase = true)) continue
                    // The mesh and DAO share a ModelComponent. Only the named body slots change.
                    val retained = flashes[original]
                    if (retained != null) {
                        bindings += Binding(entity, model, index, original, retained)
                        continue
                    }
                    original.toGlobal()
                    var flash: UnlitMaterial? = null
                    try {
                        flash = UnlitMaterial.create(BlendingMode.OPAQUE)
                        flash.toGlobal()
                        flash.setBaseColor(Color4(0.94f, 0.90f, 0.79f, 1f))
                        flash.setCullingMode(original.getCullingMode())
                        flash.setDepthTest(original.getDepthTest())
                        flash.setDepthWrite(original.getDepthWrite())
                        flash.setApplyToneMapping(true)
                        flashes[original] = flash
                        bindings += Binding(entity, model, index, original, flash)
                    } catch (error: Exception) {
                        try { flash?.close() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                        try { original.close() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                        throw error
                    }
                }
            }
            check(bindings.isNotEmpty()) { "Opponent has no named Tripo body material slots" }
        } catch (error: Exception) {
            try { close() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
            throw error
        }
    }

    fun present(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (closed || state.roundGeneration < round) return
        if (failed) {
            restore()
            return
        }
        round = state.roundGeneration
        val active = state.sceneReady && state.inputReady && state.pauseReason == null &&
            (state.result == TrialResult.FIGHTING || state.result == TrialResult.ROUND_CLEAR ||
                state.result == TrialResult.VICTORY)
        val visible = pulse.update(state.roundGeneration, active, events, System.nanoTime())
        if (!visible) {
            restore()
            return
        }
        try {
            for (binding in bindings) {
                if (!binding.overridden && binding.entity.valid) {
                    binding.model.materials[binding.index] = binding.flash
                    binding.overridden = true
                }
            }
        } catch (error: Exception) {
            failed = true
            restore()
            Log.w(TAG, "Opponent body flash became unavailable", error)
        }
    }

    /** Restores a hidden or suspended opponent while retaining contact de-duplication. */
    fun suspend() {
        if (closed) return
        pulse.suspend()
        restore()
    }

    /** Call before destroying the opponent's scene subtree. */
    override fun close() {
        if (closed) return
        closed = true
        restore()
        for ((original, flash) in flashes) {
            try { flash.close() } catch (error: Exception) {
                Log.w(TAG, "Unable to release flash material", error)
            }
            try { original.close() } catch (error: Exception) {
                Log.w(TAG, "Unable to release original material hold", error)
            }
        }
        bindings.clear()
        flashes.clear()
    }

    private fun restore() {
        for (binding in bindings) {
            if (!binding.overridden) continue
            try {
                if (binding.entity.valid) binding.model.materials[binding.index] = binding.original
                binding.overridden = false
            } catch (error: Exception) {
                // A failed slot must not prevent the remaining slots from returning to PBR.
                Log.w(TAG, "Unable to restore body material slot ${binding.index}", error)
            }
        }
    }

    private companion object {
        const val TAG = "ArenaHitFlash"
    }
}

/** Wall-time pulse policy, isolated so event identity and boundary timing can be verified on the host. */
internal class EnemyHitFlashPulse {
    private var round = Long.MIN_VALUE
    private val seen = mutableSetOf<Long>()
    private var startedAt: Long? = null
    private var duration = 0L
    private var lastNow: Long? = null

    fun suspend() {
        startedAt = null
    }

    fun update(generation: Long, active: Boolean, events: List<EnemyCombatEvent>, nowNanos: Long): Boolean {
        if (generation < round) return isVisible(nowNanos)
        if (generation != round) {
            round = generation
            seen.clear()
            startedAt = null
            lastNow = null
        }
        if (lastNow?.let { nowNanos < it } == true) startedAt = null
        lastNow = nowNanos
        val fresh = events.filterIsInstance<CombatImpact>().filter { seen.add(it.id) }
        if (!active) {
            startedAt = null
            return false
        }
        val nextDuration = fresh.filter { it.appliedDamage > 0 && it.kind.affectsEnemyBody() }
            .maxOfOrNull { if (it.fatal) 40_000_000L else 28_000_000L }
        if (nextDuration != null && (!isVisible(nowNanos) || nextDuration >= duration)) {
            startedAt = nowNanos
            duration = nextDuration
        }
        return isVisible(nowNanos)
    }

    private fun isVisible(nowNanos: Long): Boolean =
        startedAt?.let { nowNanos >= it && nowNanos - it < duration } == true

    private fun CombatImpactKind.affectsEnemyBody(): Boolean = when (this) {
        CombatImpactKind.SOFT_HIT, CombatImpactKind.HARD_HIT, CombatImpactKind.GUARDED_HIT,
        CombatImpactKind.SKILL, CombatImpactKind.EXECUTION -> true
        CombatImpactKind.BLOCK, CombatImpactKind.PARRY, CombatImpactKind.PLAYER_HIT -> false
    }
}
