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
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.p0d2f0182.runtime.HandPosePresenter
import java.util.concurrent.CancellationException
import kotlin.math.abs
import kotlin.math.hypot
import com.example.wuxiaarena.core.math.Vector3 as TrackingVector3

private const val TAG = "TavernScene"
private const val TAVERN_ASSET = "asset://models/tavern_slice.glb"
private const val ENEMY_ASSET = "asset://models/tripo_warrior.glb"
private const val PLAYER_DAO_ASSET = "asset://models/dao_grip.glb"

private class SceneOwner(
    private val onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    private val onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
) {
    var root: Entity? = null
    var playerWeapon: Entity? = null

    fun presentPlayerHand(pose: ObservedPose?) {
        val parent = root ?: return
        val weapon = playerWeapon ?: return
        if (!parent.valid || !weapon.valid) return
        val position = pose?.position
        val rotation = pose?.rotation?.normalizedOrNull()
        if (position == null || !position.isFinite() || rotation == null ||
            pose?.quality == TrackingQuality.SOURCE_REPORTED_INVALID
        ) {
            if (weapon.enabled) weapon.enabled = false
            return
        }
        val x = position.x.toFloat()
        val y = position.y.toFloat()
        val z = position.z.toFloat()
        if (!x.isFinite() || !y.isFinite() || !z.isFinite()) {
            weapon.enabled = false
            return
        }
        val transform = checkNotNull(weapon.components[TransformComponent::class.java])
        transform.setPosition(parent.convertPositionFrom(Vector3(x, y, z), null))
        transform.setQuaternion(
            parent.convertRotationFrom(
                Quat(rotation.x.toFloat(), rotation.y.toFloat(), rotation.z.toFloat(), rotation.w.toFloat()),
                null,
            )
        )
        if (!weapon.enabled) weapon.enabled = true
    }

    fun release() {
        val current = root ?: return
        root = null
        playerWeapon = null
        onPlayerHandPresenter(null)
        onEnemyGeometry(null, 0.0)
        if (current.valid) current.destroy()
    }
}

@Composable
fun HomeStage(
    onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
) {
    val owner = remember { SceneOwner(onEnemyGeometry, onPlayerHandPresenter) }

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
        var playerWeapon: Entity? = null
        var playerWeaponAttached = false
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

            playerWeapon = Entity.loadSuspend(PLAYER_DAO_ASSET)
            if (owner.root !== root) {
                playerWeapon.destroy()
                return@SpatialView
            }
            playerWeapon.enabled = false
            check(root.addChild(playerWeapon)) { "Could not attach player dao" }
            playerWeaponAttached = true
            owner.playerWeapon = playerWeapon
            onPlayerHandPresenter(owner::presentPlayerHand)
            Log.i(TAG, "Player dao attached; grip origin=0, blade forward=-Z, driven by shared hand observations")

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
                val localBounds = enemy.getVisualBounds(enemy)
                val reachX = abs(localBounds.center.x) + localBounds.size.x / 2f
                val reachZ = abs(localBounds.center.z) + localBounds.size.z / 2f
                Log.i(TAG, "Enemy local bounds center=${localBounds.center}, size=${localBounds.size}; stage origin=$origin")
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
            if (!playerWeaponAttached) playerWeapon?.destroy()
            if (!lightAttached) light?.destroy()
            if (owner.root === root) owner.release()
            if (error is CancellationException) throw error
            Log.e(TAG, "Unable to load the tavern scene", error)
        }
    }
}
