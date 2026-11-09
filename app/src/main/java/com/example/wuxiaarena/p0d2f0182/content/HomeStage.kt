package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.pico.spatial.core.ecs.AttachmentPanelComponent
import com.pico.spatial.core.ecs.DirectionalLightComponent
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.math.Color4
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import com.pico.spatial.ui.foundation.content.SpatialView
import com.pico.spatial.ui.foundation.content.AttachmentPanelBuilder
import com.pico.spatial.ui.foundation.content.SpatialViewAttachments
import com.pico.spatial.ui.platform.LengthUnit
import com.pico.spatial.ui.platform.LocalPhysicalLengthConverter
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.p0d2f0182.runtime.HandPosePresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaPresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import java.util.concurrent.CancellationException
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.sin
import kotlin.math.cos
import com.example.wuxiaarena.core.math.Vector3 as TrackingVector3

private const val TAG = "TavernScene"
private const val TAVERN_ASSET = "asset://models/tavern_slice.glb"
private const val FORECOURT_ASSET = "asset://models/forecourt.glb"
private const val ENEMY_ASSET = "asset://models/tripo_warrior.glb"
private const val PLAYER_DAO_ASSET = "asset://models/dao_grip.glb"
private const val CONTROL_PANEL_ID = "trial-control"
private const val STATUS_PANEL_ID = "combat-status"
private const val HUD_WORLD_SCALE = 1.4f
private const val ENEMY_STAGE_Z = -2.4f

private class SceneOwner(
    private val onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    private val onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
    private val onEnemyPresenter: (ArenaPresenter?) -> Unit,
) {
    var root: Entity? = null
    var playerWeapon: Entity? = null
    var enemyAnimator: EnemyAnimator? = null
    var enemyModel: Entity? = null
    var keyLight: Entity? = null
    val panelAnchors = mutableMapOf<String, Entity>()
    var enemyWorldPosition: TrackingVector3? = null
    var statusPanelY = 2.15f
    private var lastFeedback = -1L
    private var pulseUntil = 0L
    private var pulseLit = false

    fun presentArena(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        val parent = root ?: return
        val enemy = enemyModel ?: return
        if (!parent.valid || !enemy.valid) return
        state.enemyPosition?.let { position ->
            enemyWorldPosition = position
            val transform = checkNotNull(enemy.components[TransformComponent::class.java])
            transform.setPosition(parent.convertPositionFrom(Vector3(position.x.toFloat(), position.y.toFloat(), position.z.toFloat()), null))
            val halfYaw = state.enemyYawRadians / 2f
            transform.setQuaternion(parent.convertRotationFrom(Quat(0f, sin(halfYaw), 0f, cos(halfYaw)), null))
            panelAnchors[STATUS_PANEL_ID]?.let { anchor ->
                placeAttachment(parent, anchor, Vector3(position.x.toFloat(), statusPanelY, position.z.toFloat()), Quat.identity())
            }
        }
        if (lastFeedback != state.feedbackSequence) {
            lastFeedback = state.feedbackSequence
            if (state.feedback in listOf(CombatFeedback.HIT, CombatFeedback.HEADSHOT, CombatFeedback.PARRY,
                    CombatFeedback.SKILL, CombatFeedback.EXECUTION)) {
                pulseUntil = System.nanoTime() + 100_000_000L
            }
        }
        val illuminated = System.nanoTime() < pulseUntil
        if (illuminated != pulseLit) {
            keyLight?.takeIf { it.valid }?.components?.set(DirectionalLightComponent(Color4.WHITE, if (illuminated) 1300f else 800f))
            pulseLit = illuminated
        }
        enemyAnimator?.present(state, events)
    }

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
        enemyModel = null
        keyLight = null
        panelAnchors.clear()
        onPlayerHandPresenter(null)
        onEnemyPresenter(null)
        val animator = enemyAnimator
        enemyAnimator = null
        try {
            animator?.close()
        } catch (error: Exception) {
            Log.w(TAG, "Enemy animation cleanup failed", error)
        } finally {
            onEnemyGeometry(null, 0.0)
            if (current.valid) current.destroy()
        }
    }
}

@Composable
internal fun HomeStage(
    onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
    onEnemyPresenter: (ArenaPresenter?) -> Unit,
    controlsPanel: @Composable () -> Unit,
    statusPanel: @Composable () -> Unit,
) {
    val owner = remember { SceneOwner(onEnemyGeometry, onPlayerHandPresenter, onEnemyPresenter) }
    val currentControls = rememberUpdatedState(controlsPanel)
    val currentStatus = rememberUpdatedState(statusPanel)
    val converter = LocalPhysicalLengthConverter.current
    val statusHeightMeters = converter.dpToLength(260.dp, LengthUnit.Meters) * HUD_WORLD_SCALE
    val statusPosition = Vector3(0f, maxOf(2.15f, 1.95f + statusHeightMeters / 2f), ENEMY_STAGE_Z)
    owner.statusPanelY = statusPosition.y
    val controlPosition = remember { Vector3(-0.85f, 1.15f, -1.45f) }
    val controlRotation = remember { Quat(0f, 0.2923717f, 0f, 0.9563048f) }
    val panels = remember<AttachmentPanelBuilder.() -> Unit> {
        {
            AttachmentPanel(CONTROL_PANEL_ID, alignment = AttachmentPanelComponent.Alignment.CENTER) {
                Box(Modifier.size(width = 400.dp, height = 400.dp)) { currentControls.value() }
            }
            AttachmentPanel(STATUS_PANEL_ID, alignment = AttachmentPanelComponent.Alignment.CENTER) {
                Box(Modifier.size(width = 500.dp, height = 260.dp)) { currentStatus.value() }
            }
        }
    }

    DisposableEffect(owner) {
        onDispose { owner.release() }
    }

    SpatialView(
        modifier = Modifier.fillMaxSize(),
        attachments = panels,
        update = { _, attachments ->
            val root = owner.root
            if (root != null && root.valid) {
                placeAttachment(root, owner.panelAnchors.getValue(CONTROL_PANEL_ID), controlPosition, controlRotation)
                val enemy = owner.enemyWorldPosition
                val location = if (enemy == null) statusPosition else Vector3(enemy.x.toFloat(), statusPosition.y, enemy.z.toFloat())
                placeAttachment(root, owner.panelAnchors.getValue(STATUS_PANEL_ID), location, Quat.identity())
            }
        },
    ) { content, attachments ->
        owner.release()
        val root = Entity()
        owner.root = root
        var model: Entity? = null
        var modelAttached = false
        var forecourt: Entity? = null
        var forecourtAttached = false
        var enemy: Entity? = null
        var enemyAttached = false
        var playerWeapon: Entity? = null
        var playerWeaponAttached = false
        var light: Entity? = null
        var lightAttached = false

        try {
            content.addEntity(root)
            for (id in listOf(CONTROL_PANEL_ID, STATUS_PANEL_ID)) {
                val panel = checkNotNull(attachments.entity(id)) { "Missing attachment $id" }
                val anchor = Entity()
                check(root.addChild(anchor)) { "Could not attach anchor $id" }
                owner.panelAnchors[id] = anchor
                check(anchor.addChild(panel)) { "Could not attach $id" }
            }
            placeAttachment(root, owner.panelAnchors.getValue(CONTROL_PANEL_ID), controlPosition, controlRotation)
            placeAttachment(root, owner.panelAnchors.getValue(STATUS_PANEL_ID), statusPosition, Quat.identity())
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

            forecourt = Entity.loadSuspend(FORECOURT_ASSET)
            if (owner.root !== root) {
                forecourt.destroy()
                return@SpatialView
            }
            check(root.addChild(forecourt)) { "Could not attach forecourt paving" }
            forecourtAttached = true
            val pavingTransform = checkNotNull(forecourt.components[TransformComponent::class.java])
            pavingTransform.setPosition(root.convertPositionFrom(Vector3(0f, 0f, -4f), null))
            pavingTransform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))

            enemy = Entity.loadSuspend(ENEMY_ASSET)
            if (owner.root !== root) {
                enemy.destroy()
                return@SpatialView
            }
            check(root.addChild(enemy)) { "Could not attach Tripo enemy" }
            enemyAttached = true
            owner.enemyModel = enemy
            val enemyTransform = checkNotNull(enemy.components[TransformComponent::class.java]) {
                "Tripo enemy has no transform"
            }
            // The prepared GLB is metre-scaled, feet at Y=0 and faces +Z.
            // Paving's highest source surface is Y=0.02794 m.
            enemyTransform.setPosition(root.convertPositionFrom(Vector3(0f, 0.028f, ENEMY_STAGE_Z), null))
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
            owner.keyLight = light
            try {
                val bounds = model.getVisualBounds(null)
                Log.i(TAG, "Tavern attached; stage bounds center=${bounds.center}, size=${bounds.size}")
                val enemyBounds = enemy.getVisualBounds(null)
                Log.i(TAG, "Tripo enemy attached; stage bounds center=${enemyBounds.center}, size=${enemyBounds.size}")
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
            val animator = EnemyAnimator(enemy)
            owner.enemyAnimator = animator
            onEnemyPresenter(owner::presentArena)
        } catch (error: Exception) {
            if (!modelAttached) model?.destroy()
            if (!forecourtAttached) forecourt?.destroy()
            if (!enemyAttached) enemy?.destroy()
            if (!playerWeaponAttached) playerWeapon?.destroy()
            if (!lightAttached) light?.destroy()
            if (owner.root === root) owner.release()
            if (error is CancellationException) throw error
            Log.e(TAG, "Unable to load the tavern scene", error)
        }
    }
}

private fun placeAttachment(
    root: Entity,
    panel: Entity,
    position: Vector3,
    rotation: Quat,
) {
    if (!panel.valid) return
    val transform = checkNotNull(panel.components[TransformComponent::class.java])
    transform.setPosition(root.convertPositionFrom(position, null))
    transform.setQuaternion(root.convertRotationFrom(rotation, null))
    transform.setScaleVector(Vector3(HUD_WORLD_SCALE, HUD_WORLD_SCALE, HUD_WORLD_SCALE))
}
