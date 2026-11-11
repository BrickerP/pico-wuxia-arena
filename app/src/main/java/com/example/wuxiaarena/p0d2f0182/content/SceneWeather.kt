package com.example.wuxiaarena.p0d2f0182.content

import androidx.annotation.MainThread
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import java.util.concurrent.CancellationException
import kotlin.math.sin

private const val RAIN_CYCLE_NANOS = 2_500_000_000L

/** Three contiguous 2 m tiles fall at 2.4 m/s; the seam recycles below the floor. */
internal fun weatherTileHeight(tile: Int, nowNanos: Long): Float {
    require(tile in 0..2)
    val fall = Math.floorMod(nowNanos, RAIN_CYCLE_NANOS) * (6.0 / RAIN_CYCLE_NANOS)
    return (-2.0 + (tile * 2.0 + 6.0 - fall) % 6.0).toFloat()
}

/** Bounded, independent drift for the two low side strips, never across the fighter. */
internal fun weatherHazeDrift(side: Int, nowNanos: Long): Float {
    require(side in 0..1)
    val seconds = Math.floorMod(nowNanos, 40_000_000_000L) / 1_000_000_000.0
    return (0.12 * sin(seconds * Math.PI / 20.0 + side * Math.PI)).toFloat()
}

/**
 * Explicit mesh rain and side haze, not an SDK ParticleComponent or volumetric fog.
 * The sky is an unlit 30 m shell and does not illuminate PBR materials.
 * Scene owner supplies published assets, updates this on the scene thread, and closes it.
 */
@MainThread
internal class SceneWeather private constructor(
    private val rig: Entity,
    private val rain: List<Entity>,
    private val haze: List<Entity>,
) : AutoCloseable {
    private var closed = false

    fun update(nowNanos: Long, visible: Boolean) {
        if (closed || !rig.valid) return
        rig.enabled = visible
        if (!visible) return
        for ((index, tile) in rain.withIndex()) {
            val x = if (index < 3) -2.7f else 2.7f
            checkNotNull(tile.components[TransformComponent::class.java]).setPosition(
                rig.convertPositionFrom(Vector3(x, weatherTileHeight(index % 3, nowNanos), -2.8f), null),
            )
        }
        for ((index, strip) in haze.withIndex()) {
            val x = if (index == 0) -3f else 3f
            checkNotNull(strip.components[TransformComponent::class.java]).setPosition(
                rig.convertPositionFrom(Vector3(x + weatherHazeDrift(index, nowNanos), 0f, -4.4f), null),
            )
        }
    }

    override fun close() {
        if (closed) return
        if (rig.valid) check(rig.destroy()) { "Could not destroy weather rig" }
        closed = true
    }

    companion object {
        /**
         * Entity.loadSuspend owns model resources. Each result is attached immediately;
         * stale parents and cancellation destroy the partial hierarchy before rethrowing.
         */
        suspend fun load(parent: Entity, rainAsset: String, hazeAsset: String, skyAsset: String): SceneWeather {
            check(parent.valid) { "Weather needs a live scene owner" }
            val rig = Entity()
            val rain = mutableListOf<Entity>()
            val haze = mutableListOf<Entity>()
            try {
                check(parent.addChild(rig)) { "Could not attach weather rig" }
                rig.enabled = false
                for (index in 0..5) {
                    rain += loadChild(rig, rainAsset, Vector3(if (index < 3) -2.7f else 2.7f, index % 3 * 2f, -2.8f))
                }
                for (index in 0..1) {
                    haze += loadChild(rig, hazeAsset, Vector3(if (index == 0) -3f else 3f, 0f, -4.4f))
                }
                loadChild(rig, skyAsset, Vector3(0f, 0f, 0f))
                return SceneWeather(rig, rain, haze)
            } catch (error: Exception) {
                try {
                    if (rig.valid) rig.destroy()
                } catch (cleanup: Exception) {
                    error.addSuppressed(cleanup)
                }
                throw error
            }
        }

        private suspend fun loadChild(parent: Entity, asset: String, position: Vector3): Entity {
            val entity = Entity.loadSuspend(asset)
            try {
                if (!parent.valid) throw CancellationException("Weather scene was disposed during asset loading")
                check(parent.addChild(entity)) { "Could not attach weather asset $asset" }
                val transform = checkNotNull(entity.components[TransformComponent::class.java])
                transform.setPosition(parent.convertPositionFrom(position, null))
                transform.setQuaternion(parent.convertRotationFrom(Quat.identity(), null))
                return entity
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
