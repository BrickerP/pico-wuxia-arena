package com.example.wuxiaarena.p0d2f0182.content

import androidx.annotation.MainThread
import com.pico.spatial.core.ecs.DirectionalLightComponent
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.ImageBasedLightSource
import com.pico.spatial.core.ecs.LoadType
import com.pico.spatial.core.ecs.PointLightComponent
import com.pico.spatial.core.ecs.SpotLightComponent
import com.pico.spatial.core.ecs.StageEnvironmentLightingComponent
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.ecs.resource.TextureCreateOption
import com.pico.spatial.core.ecs.resource.TextureEncoding
import com.pico.spatial.core.ecs.resource.TextureResource
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import java.util.concurrent.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext

/**
 * Rain-night lighting in Stage metres. The scene owner creates and closes this once.
 * Replaces HomeStage's old key and fills; the contact flash stays with combat presentation.
 * Public calls run on the SpatialView scene thread; only texture decoding runs on IO.
 */
@MainThread
internal class SceneLighting private constructor(private val rig: Entity) : AutoCloseable {
    private var environment: TextureResource? = null
    private var closing = false
    private var loadingEnvironment = false
    private var loadCompletion: CompletableDeferred<Unit>? = null

    /** close() can finish before an in-flight IO load; retain this owner until true. */
    val isReleased: Boolean
        get() = closing && !loadingEnvironment && environment == null && !rig.valid

    /**
     * Bind one published cubemap, using its real assets-relative path (without asset://).
     * This owner retains the resource until the lighting Entity has been destroyed.
     * A load/bind failure propagates; it is never reported as an active IBL.
     */
    suspend fun loadEnvironment(assetPath: String, stillOwned: () -> Boolean) {
        check(!closing && rig.valid) { "Lighting owner is closing" }
        check(environment == null && !loadingEnvironment) { "The scene already owns or is loading an environment map" }
        require(assetPath.isNotBlank()) { "An assets-relative environment path is required" }
        if (!stillOwned()) throw CancellationException("Lighting scene was replaced")
        // Independent of the old builder Job: its cancellation must not cancel new waiters.
        val completion = CompletableDeferred<Unit>()
        loadCompletion = completion
        loadingEnvironment = true
        var pending: TextureResource? = null
        try {
            // Official RoomLighting.kt sample permits TextureResource.load on IO.
            // Assign inside the block: cancellation at return dispatch cannot lose the handle.
            withContext(Dispatchers.IO) {
                pending = TextureResource.load(
                    assetPath,
                    LoadType.FROM_ASSETS,
                    TextureCreateOption().apply { textureEncoding = TextureEncoding.LINEAR },
                )
            }
            currentCoroutineContext().ensureActive()
            if (closing || !rig.valid || !stillOwned()) {
                throw CancellationException("Lighting scene was disposed during environment loading")
            }
            val texture = checkNotNull(pending)
            rig.components.set(StageEnvironmentLightingComponent(ImageBasedLightSource.Single(texture), 4f))
            environment = texture
            pending = null
        } catch (error: Exception) {
            pending?.let { texture ->
                try {
                    texture.close()
                } catch (cleanup: Exception) {
                    // Retain failed cleanup, even if close() ran while IO was in flight.
                    environment = texture
                    error.addSuppressed(cleanup)
                }
            }
            throw error
        } finally {
            loadingEnvironment = false
            // Pending cleanup (or retained cleanup failure) is settled before waking a builder.
            completion.complete(Unit)
        }
    }

    /**
     * Suspend once for any old IO, then retry native release once on the scene thread.
     * A cancelled waiter leaves the completion signal and this closing owner intact.
     * The caller owns its timeout and must retain this owner if waiting/release fails.
     */
    suspend fun awaitRelease() {
        closing = true
        val completion = loadCompletion
        completion?.await()
        currentCoroutineContext().ensureActive()
        close()
        check(isReleased) { "Lighting still owns resources after release" }
    }

    override fun close() {
        if (isReleased) return
        closing = true
        // Keep the owner and its texture retryable if native destruction fails.
        if (rig.valid) check(rig.destroy()) { "Could not destroy the lighting rig" }
        environment?.close()
        environment = null
    }

    companion object {
        /** Direct lights work independently of the separately tested IBL candidate. */
        fun attach(parent: Entity): SceneLighting {
            check(parent.valid) { "Lighting needs a live scene owner" }
            val rig = Entity()
            try {
                check(parent.addChild(rig)) { "Could not attach lighting rig" }
                val moon = Entity()
                try {
                    check(rig.addChild(moon)) { "Could not attach moon key" }
                    // Cheap per-mesh GroundShadow remains the scene's shadow path.
                    moon.components.set(DirectionalLightComponent(Color4(0.57f, 0.73f, 1f, 1f), 650f, false))
                    checkNotNull(moon.components[TransformComponent::class.java]).setQuaternion(
                        rig.convertRotationFrom(Quat(-0.347382f, -0.280147f, 0f, 0.894899f), null),
                    )
                } catch (error: Exception) {
                    try {
                        if (moon.valid) moon.destroy()
                    } catch (cleanup: Exception) {
                        error.addSuppressed(cleanup)
                    }
                    throw error
                }
                // EH_Light_Lantern_01..04 in the world-space courtyard_hero candidate.
                point(rig, Vector3(-2.15f, 2.7f, -4.7f), Color4(1f, 0.49f, 0.20f, 1f), 1500f, 3.8f)
                point(rig, Vector3(2.15f, 2.7f, -4.7f), Color4(1f, 0.49f, 0.20f, 1f), 1500f, 3.8f)
                point(rig, Vector3(-4.03f, 2.25f, 0.56f), Color4(1f, 0.49f, 0.20f, 1f), 1100f, 3.4f)
                point(rig, Vector3(4.03f, 2.25f, -1.32f), Color4(1f, 0.49f, 0.20f, 1f), 1100f, 3.4f)
                faceKey(rig)
                point(rig, Vector3(1.9f, 2.5f, -3.4f), Color4(0.38f, 0.65f, 1f, 1f), 900f, 4.5f)
                point(rig, Vector3(1.15f, 1.65f, 0.25f), Color4(0.72f, 0.85f, 1f, 1f), 12000f, 4.2f)
                return SceneLighting(rig)
            } catch (error: Exception) {
                try {
                    if (rig.valid) rig.destroy()
                } catch (cleanup: Exception) {
                    error.addSuppressed(cleanup)
                }
                throw error
            }
        }

        private fun faceKey(parent: Entity) {
            val entity = Entity()
            try {
                check(parent.addChild(entity)) { "Could not attach face key" }
                // Native spot intensity is total lumens, not directional-light lux.
                entity.components.set(SpotLightComponent(Color4(1f, 0.91f, 0.82f, 1f), 20000f, 4.8f, 45f, 75f, false))
                val transform = checkNotNull(entity.components[TransformComponent::class.java])
                transform.setPosition(parent.convertPositionFrom(Vector3(-0.35f, 2.1f, 0.45f), null))
                // Local -Z targets Stage (0, 1.3, -1.75); no camera or head tracking is changed.
                transform.setQuaternion(parent.convertRotationFrom(Quat(-0.17205445f, -0.07527382f, 0f, 0.98220727f), null))
            } catch (error: Exception) {
                try {
                    if (entity.valid) entity.destroy()
                } catch (cleanup: Exception) {
                    error.addSuppressed(cleanup)
                }
                throw error
            }
        }

        private fun point(parent: Entity, position: Vector3, color: Color4, lumens: Float, radius: Float) {
            val entity = Entity()
            try {
                check(parent.addChild(entity)) { "Could not attach atmosphere light" }
                entity.components.set(PointLightComponent(color, lumens, radius))
                checkNotNull(entity.components[TransformComponent::class.java])
                    .setPosition(parent.convertPositionFrom(position, null))
            } catch (error: Exception) {
                try {
                    if (entity.valid) entity.destroy()
                } catch (cleanup: Exception) {
                    error.addSuppressed(cleanup)
                }
                throw error
            }
        }
    }
}
