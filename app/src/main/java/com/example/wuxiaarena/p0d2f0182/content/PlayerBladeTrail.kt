package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.core.ecs.BoundingBox
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.ModelEntity
import com.pico.spatial.core.ecs.resource.BlendingMode
import com.pico.spatial.core.ecs.resource.MaterialCullingMode
import com.pico.spatial.core.ecs.resource.MeshModel
import com.pico.spatial.core.ecs.resource.MeshResource
import com.pico.spatial.core.ecs.resource.UnlitMaterial
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Vector3

/** A translucent 65ms wake and a 12ms hot edge swept by the actual Stage-space blade samples. */
internal class PlayerBladeTrail(private val root: Entity) : AutoCloseable {
    private val history = BladeTrailGeometry()
    private var entity: ModelEntity? = null
    private var mesh: MeshResource? = null
    private var material: UnlitMaterial? = null
    private var round = Long.MIN_VALUE
    private var opponentRound = 0
    private var hand: Hand? = null
    private var inputOrigin: InputOrigin? = null
    private var closed = false
    private var failed = false

    fun present(state: ArenaViewState) {
        if (closed || failed || !root.valid || state.roundGeneration < round) return
        try {
            if (state.roundGeneration != round || state.roundNumber != opponentRound ||
                state.dominantHand != hand || state.inputOrigin != inputOrigin
            ) {
                clear()
                round = state.roundGeneration
                opponentRound = state.roundNumber
                hand = state.dominantHand
                inputOrigin = state.inputOrigin
            }
            val base = state.playerBladeBase
            val tip = state.playerBladeTip
            val active = state.sceneReady && state.inputReady && state.pauseReason == null &&
                (state.result == TrialResult.FIGHTING || state.result == TrialResult.ROUND_CLEAR)
            if (!active || base == null || tip == null) {
                clear()
                return
            }
            val ribbon = history.sample(
                base, tip, System.nanoTime(), state.playerBladeTipSpeed,
                state.playerBladeAtRest, state.playerMotionGeneration,
            )
            if (ribbon == null) {
                entity?.takeIf { it.valid }?.enabled = false
                return
            }
            // The entity is root-local, while tracking samples are in Stage coordinates.
            val positions = ribbon.positions.map { point ->
                root.convertPositionFrom(Vector3(point.x.toFloat(), point.y.toFloat(), point.z.toFloat()), null)
                    .also { check(it.x.isFinite() && it.y.isFinite() && it.z.isFinite()) }
            }
            val model = MeshModel(
                positions = positions,
                triangleIndices = ribbon.triangleIndices,
                colors = ribbon.alphas.mapIndexed { index, alpha ->
                    if (index < ribbon.coreVertexOffset) Color4(0.70f, 0.79f, 0.83f, alpha * 0.38f)
                    else Color4(1.0f, 0.94f, 0.76f, alpha * 0.82f)
                },
            )
            val bounds = boundsOf(positions)
            val existing = mesh
            if (existing == null) {
                create(model, bounds)
            } else {
                check(existing.replaceWithMeshModel(model, bounds)) { "Blade ribbon mesh update was rejected" }
            }
            checkNotNull(entity).enabled = true
        } catch (error: Exception) {
            failed = true
            close()
            Log.w(TAG, "Player blade trail became unavailable", error)
        }
    }

    /** Call before destroying root, including partially initialized scenes. */
    override fun close() {
        if (closed) return
        closed = true
        history.clear()
        try { entity?.takeIf { it.valid }?.destroy() } catch (error: Exception) {
            Log.w(TAG, "Unable to destroy blade trail entity", error)
        }
        entity = null
        try { mesh?.close() } catch (error: Exception) {
            Log.w(TAG, "Unable to release blade trail mesh", error)
        }
        mesh = null
        try { material?.close() } catch (error: Exception) {
            Log.w(TAG, "Unable to release blade trail material", error)
        }
        material = null
    }

    private fun clear() {
        history.clear()
        entity?.takeIf { it.valid }?.enabled = false
    }

    private fun create(model: MeshModel, bounds: BoundingBox) {
        MeshModel.validateOrThrow(model)
        val nextMesh = MeshResource.createWithMeshModel(model, bounds, "player_blade_trail")
        mesh = nextMesh
        nextMesh.toGlobal()
        val nextMaterial = UnlitMaterial.create(BlendingMode.TRANSPARENT)
        material = nextMaterial
        nextMaterial.toGlobal()
        nextMaterial.setBaseColor(Color4(1f, 1f, 1f, 1f))
        nextMaterial.setCullingMode(MaterialCullingMode.NONE)
        nextMaterial.setDepthTest(true)
        nextMaterial.setDepthWrite(false)
        nextMaterial.setApplyToneMapping(true)
        val nextEntity = ModelEntity(nextMesh, nextMaterial)
        entity = nextEntity
        nextEntity.enabled = false
        check(root.addChild(nextEntity)) { "Unable to attach player blade trail" }
    }

    private fun boundsOf(positions: List<Vector3>): BoundingBox {
        val minX = positions.minOf { it.x }
        val minY = positions.minOf { it.y }
        val minZ = positions.minOf { it.z }
        val maxX = positions.maxOf { it.x }
        val maxY = positions.maxOf { it.y }
        val maxZ = positions.maxOf { it.z }
        return BoundingBox(
            center = Vector3((minX + maxX) * 0.5f, (minY + maxY) * 0.5f, (minZ + maxZ) * 0.5f),
            halfExtent = Vector3((maxX - minX) * 0.5f, (maxY - minY) * 0.5f, (maxZ - minZ) * 0.5f),
        )
    }

    private companion object {
        const val TAG = "ArenaBladeTrail"
    }
}
