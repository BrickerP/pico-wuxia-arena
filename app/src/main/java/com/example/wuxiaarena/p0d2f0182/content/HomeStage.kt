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
import kotlin.math.abs
import kotlin.math.hypot
import com.example.wuxiaarena.core.math.Vector3 as TrackingVector3

private const val TAG = "TavernScene"
private const val TAVERN_ASSET = "asset://models/tavern_slice.glb"
private const val ENEMY_ASSET = "asset://models/tripo_warrior.glb"

private class SceneOwner(private val onEnemyGeometry: (TrackingVector3?, Double) -> Unit) {
    var root: Entity? = null

    fun release() {
        val current = root ?: return
        root = null
        onEnemyGeometry(null, 0.0)
        if (current.valid) current.destroy()
    }
}

@Composable
fun HomeStage(onEnemyGeometry: (TrackingVector3?, Double) -> Unit) {
    val owner = remember { SceneOwner(onEnemyGeometry) }

    DisposableEffect(owner) {
        onDispose { owner.release() }
    }

    SpatialView(modifier = Modifier.fillMaxSize()) { content, _ ->
        owner.release()
        val root = Entity()
        owner.root = root
        var model: Entity? = null
        var modelAttached = false
        var enemy: Entity? = null
        var enemyAttached = false
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

            enemy = Entity.loadSuspend(ENEMY_ASSET)
            if (owner.root !== root) {
                enemy.destroy()
                return@SpatialView
            }
            check(root.addChild(enemy)) { "Could not attach Tripo enemy" }
            enemyAttached = true
            val enemyTransform = checkNotNull(enemy.components[TransformComponent::class.java]) {
                "Tripo enemy has no transform"
            }
            // The prepared GLB is metre-scaled, feet at Y=0 and faces +Z.
            // Paving's highest source surface is Y=0.02794 m.
            enemyTransform.setPosition(root.convertPositionFrom(Vector3(0f, 0.028f, -2.4f), null))
            enemyTransform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))

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
                val enemyBounds = enemy.getVisualBounds(null)
                Log.i(TAG, "Tripo enemy attached; static=true, stage bounds center=${enemyBounds.center}, size=${enemyBounds.size}")
                val origin = enemy.convertPositionTo(Vector3(0f, 0f, 0f), null)
                val reachX = abs(enemyBounds.center.x - origin.x) + enemyBounds.size.x / 2f
                val reachZ = abs(enemyBounds.center.z - origin.z) + enemyBounds.size.z / 2f
                onEnemyGeometry(
                    TrackingVector3(origin.x.toDouble(), origin.y.toDouble(), origin.z.toDouble()),
                    hypot(reachX.toDouble(), reachZ.toDouble()),
                )
            } catch (error: Exception) {
                Log.w(TAG, "Tavern attached but visual bounds are unavailable", error)
            }
        } catch (error: Exception) {
            if (!modelAttached) model?.destroy()
            if (!enemyAttached) enemy?.destroy()
            if (!lightAttached) light?.destroy()
            if (owner.root === root) owner.release()
            if (error is CancellationException) throw error
            Log.e(TAG, "Unable to load the tavern scene", error)
        }
    }
}
