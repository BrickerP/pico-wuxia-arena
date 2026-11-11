package com.pico.spatial.core.ecs.resource

import com.pico.spatial.core.ecs.LoadType
import com.pico.spatial.core.ecs.NativeProbe
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

enum class TextureEncoding { LINEAR }
class TextureCreateOption { var textureEncoding = TextureEncoding.LINEAR }

class LoadPlan(val texture: TextureResource, block: Boolean = true) {
    val entered = CountDownLatch(1)
    val release = CountDownLatch(if (block) 1 else 0)
}

object TextureProbe {
    @Volatile var plan: LoadPlan? = null
    val loads = AtomicInteger()
    fun reset() { plan = null; loads.set(0) }
}

class TextureResource(var closeFailures: Int = 0) {
    var closeCalls = 0
        private set
    var closed = false
        private set

    fun close() {
        NativeProbe.assertSceneThread()
        closeCalls++
        if (closeFailures > 0) {
            closeFailures--
            throw IllegalStateException("Injected texture close failure")
        }
        check(!closed) { "Texture closed twice" }
        closed = true
    }

    companion object {
        @Suppress("UNUSED_PARAMETER")
        fun load(path: String, loadType: LoadType, option: TextureCreateOption): TextureResource {
            check(Thread.currentThread() !== NativeProbe.sceneThread) { "Texture decoding blocked the scene thread" }
            val plan = checkNotNull(TextureProbe.plan)
            TextureProbe.loads.incrementAndGet()
            plan.entered.countDown()
            check(plan.release.await(5, TimeUnit.SECONDS)) { "Timed out waiting for the deterministic IO gate" }
            return plan.texture
        }
    }
}
