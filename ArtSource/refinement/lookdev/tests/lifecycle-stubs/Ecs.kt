package com.pico.spatial.core.ecs

import com.pico.spatial.core.ecs.resource.TextureResource
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import java.util.concurrent.atomic.AtomicInteger

/** Deterministic native-operation double, not a rendering or SDK compatibility test. */
object NativeProbe {
    lateinit var sceneThread: Thread
    val environmentAttachments = AtomicInteger()

    fun reset() {
        sceneThread = Thread.currentThread()
        environmentAttachments.set(0)
    }

    fun assertSceneThread() {
        check(Thread.currentThread() === sceneThread) { "Scene operation escaped its caller thread" }
    }
}

enum class LoadType { FROM_ASSETS }

class Entity {
    var valid = true
        private set
    val children = mutableListOf<Entity>()
    val components = ComponentSet(this)
    var destroyFailures = 0
    var destroyCalls = 0

    fun addChild(child: Entity): Boolean {
        NativeProbe.assertSceneThread()
        check(valid && child.valid)
        children += child
        return true
    }

    fun destroy(): Boolean {
        NativeProbe.assertSceneThread()
        destroyCalls++
        if (destroyFailures > 0) {
            destroyFailures--
            return false
        }
        valid = false
        children.forEach { if (it.valid) it.destroy() }
        return true
    }

    @Suppress("UNUSED_PARAMETER")
    fun convertPositionFrom(position: Vector3, source: Entity?): Vector3 {
        NativeProbe.assertSceneThread()
        return position
    }

    @Suppress("UNUSED_PARAMETER")
    fun convertRotationFrom(rotation: Quat, source: Entity?): Quat {
        NativeProbe.assertSceneThread()
        return rotation
    }
}

class ComponentSet(private val entity: Entity) {
    private val values = mutableMapOf<Class<*>, Any>(TransformComponent::class.java to TransformComponent())

    operator fun <T> get(type: Class<T>): T? {
        NativeProbe.assertSceneThread()
        return values[type]?.let(type::cast)
    }

    fun set(value: Any) {
        NativeProbe.assertSceneThread()
        check(entity.valid) { "Component bound to a destroyed Entity" }
        if (value is StageEnvironmentLightingComponent) NativeProbe.environmentAttachments.incrementAndGet()
        values[value.javaClass] = value
    }
}

class TransformComponent {
    @Suppress("UNUSED_PARAMETER")
    fun setPosition(value: Vector3) { NativeProbe.assertSceneThread() }
    @Suppress("UNUSED_PARAMETER")
    fun setQuaternion(value: Quat) { NativeProbe.assertSceneThread() }
}

class DirectionalLightComponent(val color: Color4, val intensity: Float, val castsShadowEnabled: Boolean)
class PointLightComponent(val color: Color4, val intensity: Float, val attenuationRadius: Float)
class SpotLightComponent(
    val color: Color4,
    val intensity: Float,
    val attenuationRadius: Float,
    val innerAngle: Float,
    val outerAngle: Float,
    val castsShadowEnabled: Boolean,
)
sealed class ImageBasedLightSource {
    class Single(val resource: TextureResource) : ImageBasedLightSource()
}
class StageEnvironmentLightingComponent(val source: ImageBasedLightSource, val intensityExponent: Float)
