package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import com.pico.spatial.core.ecs.DirectionalLightComponent
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import com.pico.spatial.ui.foundation.content.SpatialView
import java.util.concurrent.CancellationException

private const val TAG = "TavernScene"
private const val TAVERN_ASSET = "asset://models/tavern_slice.glb"

private class SceneOwner {
    var root: Entity? = null

    fun release() {
        val current = root ?: return
        root = null
        if (current.valid) current.destroy()
    }
}

@Composable
fun HomeStage() {
    val owner = remember { SceneOwner() }

    DisposableEffect(owner) {
        onDispose { owner.release() }
    }

    SpatialView(modifier = Modifier.fillMaxSize()) { content, _ ->
        owner.release()
        val root = Entity()
        owner.root = root
        var model: Entity? = null
        var modelAttached = false
        var light: Entity? = null
        var lightAttached = false

        try {
            content.addEntity(root)
            model = Entity.loadSuspend(TAVERN_ASSET)
            if (owner.root !== root) {
                model.destroy()
                return@SpatialView
            }

            check(root.addChild(model)) { "Could not attach tavern model" }
            modelAttached = true
            val transform = checkNotNull(model.components[TransformComponent::class.java]) {
                "Tavern model has no transform"
            }
            transform.setPosition(root.convertPositionFrom(Vector3(0f, 0f, -4f), null))
            transform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))

            light = Entity()
            light.components.set(DirectionalLightComponent(Color4.WHITE, 800f))
            val lightTransform = checkNotNull(light.components[TransformComponent::class.java]) {
                "Scene light has no transform"
            }
            lightTransform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))
            check(root.addChild(light)) { "Could not attach scene light" }
            lightAttached = true
            try {
                val bounds = model.getVisualBounds(null)
                Log.i(TAG, "Tavern attached; stage bounds center=${bounds.center}, size=${bounds.size}")
            } catch (error: Exception) {
                Log.w(TAG, "Tavern attached but visual bounds are unavailable", error)
            }
        } catch (error: Exception) {
            if (!modelAttached) model?.destroy()
            if (!lightAttached) light?.destroy()
            if (owner.root === root) owner.release()
            if (error is CancellationException) throw error
            Log.e(TAG, "Unable to load the tavern scene", error)
        }
    }
}
