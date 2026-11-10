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
import com.pico.spatial.core.ecs.GroundShadowComponent
import com.pico.spatial.core.ecs.ModelComponent
import com.pico.spatial.core.ecs.PointLightComponent
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
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedbackProfile
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.p0d2f0182.runtime.arenaOpponents
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
private const val COURTYARD_DETAILS_ASSET = "asset://models/courtyard_details.glb"
private const val PLAYER_DAO_ASSET = "asset://models/dao_grip.glb"
private const val CONTROL_PANEL_ID = "trial-control"
private const val STATUS_PANEL_ID = "combat-status"
private const val HUD_WORLD_SCALE = 1.4f
private const val ENEMY_STAGE_Z = -2.4f
private val KEY_LIGHT_COLOR = Color4(0.92f, 0.95f, 1f, 1f)
private const val KEY_LIGHT_LUX = 1100f
// Local -Z travels down and into the arena: Stage ray (0.5014, -0.6217, -0.6017).
private val KEY_LIGHT_ROTATION = Quat(-0.347382f, -0.280147f, 0f, 0.894899f)
private val WARM_FILL_POSITION = Vector3(-1.30f, 1.80f, -1.10f)
private const val WARM_FILL_LUMENS = 2300f
private const val WARM_FILL_RADIUS_METERS = 4.2f
private val COOL_FILL_POSITION = Vector3(1.25f, 1.65f, -1.55f)
private const val COOL_FILL_LUMENS = 1300f
private const val COOL_FILL_RADIUS_METERS = 4.0f

private class SceneOwner(
    private val onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    private val onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
    private val onEnemyPresenter: (ArenaPresenter?) -> Unit,
) {
    var root: Entity? = null
    var playerWeapon: Entity? = null
    var enemyAnimator: EnemyAnimator? = null
    var enemyModel: Entity? = null
    val enemies = mutableListOf<Entity>()
    val animators = mutableListOf<EnemyAnimator>()
    val hitFlashes = mutableListOf<EnemyHitFlash>()
    var effects: CombatEffects? = null
    var bladeTrail: PlayerBladeTrail? = null
    var contactLight: Entity? = null
    val panelAnchors = mutableMapOf<String, Entity>()
    var enemyWorldPosition: TrackingVector3? = null
    var statusPanelY = 2.15f
    private var impactRound = -1L
    private var lastImpact = Long.MIN_VALUE
    private var pulseUntil = 0L

    fun presentArena(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        val parent = root ?: return
        if (enemies.isNotEmpty()) {
            val index = state.roundNumber - 1
            enemies.forEachIndexed { candidate, entity ->
                val visible = candidate == index
                if (entity.valid && entity.enabled != visible) {
                    if (!visible) {
                        animators[candidate].suspend()
                        hitFlashes[candidate].suspend()
                    }
                    entity.enabled = visible
                }
            }
            enemyModel = enemies[index]
            enemyAnimator = animators[index]
        }
        val enemy = enemyModel ?: return
        if (!parent.valid || !enemy.valid) return
        state.enemyPosition?.let { position ->
            val displayPosition = position + state.enemyRecoilOffset
            enemyWorldPosition = displayPosition
            val transform = checkNotNull(enemy.components[TransformComponent::class.java])
            transform.setPosition(parent.convertPositionFrom(Vector3(displayPosition.x.toFloat(), displayPosition.y.toFloat(), displayPosition.z.toFloat()), null))
            val halfYaw = state.enemyYawRadians / 2f
            transform.setQuaternion(parent.convertRotationFrom(Quat(0f, sin(halfYaw), 0f, cos(halfYaw)), null))
            panelAnchors[STATUS_PANEL_ID]?.let { anchor ->
                placeAttachment(parent, anchor, Vector3(position.x.toFloat(), statusPanelY, position.z.toFloat()), Quat.identity())
            }
        }
        presentImpactLight(state, events)
        enemyAnimator?.present(state, events)
        hitFlashes[state.roundNumber - 1].present(state, events)
        effects?.present(state, events)
        bladeTrail?.present(state)
    }

    private fun presentImpactLight(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        val parent = root ?: return
        val light = contactLight?.takeIf { it.valid } ?: return
        val now = System.nanoTime()
        if (impactRound != state.roundGeneration) {
            impactRound = state.roundGeneration
            lastImpact = Long.MIN_VALUE
            pulseUntil = 0L
        }
        val fresh = events.filterIsInstance<CombatImpact>().filter { it.id > lastImpact }
        if (fresh.isNotEmpty()) lastImpact = fresh.maxOf { it.id }
        val impact = currentContactImpacts(fresh, state.simulationNanos).firstOrNull()
        if (impact != null) {
            val accent = CombatFeedbackProfile.accent(impact)
            val strength = accent.strength.toFloat()
            val direction = impact.normal.normalizedOrNull() ?: TrackingVector3(0.0, 0.0, 1.0)
            val point = impact.point + direction * 0.035
            val position = Vector3(point.x.toFloat(), point.y.toFloat(), point.z.toFloat())
            if (position.x.isFinite() && position.y.isFinite() && position.z.isFinite()) {
                val hard = impact.kind == CombatImpactKind.HARD_HIT || impact.kind == CombatImpactKind.GUARDED_HIT ||
                    impact.kind == CombatImpactKind.BLOCK || impact.kind == CombatImpactKind.PARRY
                val color = if (hard) Color4(1f, 0.82f, 0.46f, 1f) else Color4(1f, 0.91f, 0.78f, 1f)
                light.components.set(PointLightComponent(color, 110f + 180f * strength, 0.60f))
                checkNotNull(light.components[TransformComponent::class.java]).setPosition(parent.convertPositionFrom(position, null))
                pulseUntil = now + accent.lightDurationNanos
            }
        }
        val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
        val available = state.sceneReady && (terminal || (state.pauseReason == null && state.inputReady))
        if (!available) pulseUntil = 0L
        val visible = available && now < pulseUntil
        if (light.enabled != visible) light.enabled = visible
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
        contactLight = null
        panelAnchors.clear()
        enemyAnimator = null
        try {
            try {
                onPlayerHandPresenter(null)
            } catch (error: Exception) {
                Log.w(TAG, "Player presenter cleanup failed", error)
            }
            try {
                onEnemyPresenter(null)
            } catch (error: Exception) {
                Log.w(TAG, "Arena presenter cleanup failed", error)
            }
            for (animator in animators) {
                try {
                    animator.close()
                } catch (error: Exception) {
                    Log.w(TAG, "Enemy animation cleanup failed", error)
                }
            }
            animators.clear()
            for (flash in hitFlashes) {
                try {
                    flash.close()
                } catch (error: Exception) {
                    Log.w(TAG, "Enemy flash cleanup failed", error)
                }
            }
            hitFlashes.clear()
            enemies.clear()
            try {
                effects?.close()
            } catch (error: Exception) {
                Log.w(TAG, "Combat effect cleanup failed", error)
            }
            effects = null
            try {
                bladeTrail?.close()
            } catch (error: Exception) {
                Log.w(TAG, "Blade trail cleanup failed", error)
            }
            bladeTrail = null
        } finally {
            try {
                onEnemyGeometry(null, 0.0)
            } finally {
                if (current.valid) current.destroy()
            }
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
        var details: Entity? = null
        var detailsAttached = false
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
            bindGroundShadow(
                checkNotNull(model.findEntity("Paving")) { "Tavern paving mesh is unavailable" },
                casts = false, receives = true, label = "tavern paving",
            )

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
            bindGroundShadow(
                checkNotNull(forecourt.findEntity("Paving")) { "Forecourt paving mesh is unavailable" },
                casts = false, receives = true, label = "forecourt paving",
            )

            details = Entity.loadSuspend(COURTYARD_DETAILS_ASSET)
            if (owner.root !== root) {
                details.destroy()
                return@SpatialView
            }
            check(root.addChild(details)) { "Could not attach courtyard details" }
            detailsAttached = true
            val detailsTransform = checkNotNull(details.components[TransformComponent::class.java])
            detailsTransform.setPosition(root.convertPositionFrom(Vector3(0f, 0f, 0f), null))
            detailsTransform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))
            bindGroundShadow(
                checkNotNull(details.findEntity("SidePaving_Geometry")) { "Side paving mesh is unavailable" },
                casts = false, receives = true, label = "side paving",
            )

            for ((index, opponent) in arenaOpponents.withIndex()) {
                enemyAttached = false
                enemy = Entity.loadSuspend(opponent.asset)
                if (owner.root !== root) {
                    enemy.destroy()
                    return@SpatialView
                }
                check(root.addChild(enemy)) { "Could not attach ${opponent.name}" }
                enemyAttached = true
                owner.enemies += enemy
                val enemyTransform = checkNotNull(enemy.components[TransformComponent::class.java]) {
                    "Tripo enemy has no transform"
                }
                enemyTransform.setPosition(root.convertPositionFrom(Vector3(0f, 0.028f, ENEMY_STAGE_Z), null))
                enemyTransform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))
                bindGroundShadow(enemy, casts = true, receives = false, label = opponent.name)
                // The three rounds reuse loaded opponents. Only the current fighter is visible.
                owner.animators += EnemyAnimator(enemy)
                owner.hitFlashes += EnemyHitFlash(enemy)
                enemy.enabled = index == 0
            }
            owner.enemyModel = owner.enemies.first()
            owner.enemyAnimator = owner.animators.first()
            val firstEnemy = owner.enemies.first()

            val effects = CombatEffects.load(root)
            if (owner.root !== root) {
                effects.close()
                return@SpatialView
            }
            owner.effects = effects
            owner.bladeTrail = PlayerBladeTrail(root)

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
            check(root.addChild(light)) { "Could not attach scene light" }
            lightAttached = true
            light.components.set(DirectionalLightComponent(KEY_LIGHT_COLOR, KEY_LIGHT_LUX, castsShadowEnabled = false))
            val lightTransform = checkNotNull(light.components[TransformComponent::class.java]) {
                "Scene light has no transform"
            }
            lightTransform.setQuaternion(root.convertRotationFrom(KEY_LIGHT_ROTATION, null))
            owner.contactLight = addPointLight(
                root, Vector3(0f, 0f, 0f), Color4(1f, 0.9f, 0.7f, 1f), 0f, 0.60f, enabled = false,
            )
            addPointLight(
                root, WARM_FILL_POSITION, Color4(1f, 0.72f, 0.46f, 1f),
                WARM_FILL_LUMENS, WARM_FILL_RADIUS_METERS,
            )
            addPointLight(
                root, COOL_FILL_POSITION, Color4(0.58f, 0.74f, 1f, 1f),
                COOL_FILL_LUMENS, COOL_FILL_RADIUS_METERS,
            )
            try {
                val bounds = model.getVisualBounds(null)
                Log.i(TAG, "Tavern attached; stage bounds center=${bounds.center}, size=${bounds.size}")
                val enemyBounds = firstEnemy.getVisualBounds(null)
                Log.i(TAG, "Tripo enemy attached; stage bounds center=${enemyBounds.center}, size=${enemyBounds.size}")
                val origin = firstEnemy.convertPositionTo(Vector3(0f, 0f, 0f), null)
                val localBounds = firstEnemy.getVisualBounds(firstEnemy)
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
            onEnemyPresenter(owner::presentArena)
        } catch (error: Exception) {
            for ((entity, attached) in listOf(
                model to modelAttached,
                forecourt to forecourtAttached,
                details to detailsAttached,
                enemy to enemyAttached,
                playerWeapon to playerWeaponAttached,
                light to lightAttached,
            )) {
                if (!attached) {
                    try {
                        if (entity?.valid == true) entity.destroy()
                    } catch (cleanup: Exception) {
                        error.addSuppressed(cleanup)
                    }
                }
            }
            if (owner.root === root) {
                try {
                    owner.release()
                } catch (cleanup: Exception) {
                    error.addSuppressed(cleanup)
                }
            }
            if (error is CancellationException) throw error
            Log.e(TAG, "Unable to load the tavern scene", error)
        }
    }
}

/** GroundShadow does not inherit; bind each actual mesh inside the selected subtree. */
private fun bindGroundShadow(entity: Entity, casts: Boolean, receives: Boolean, label: String) {
    val pending = ArrayDeque<Entity>()
    pending.addLast(entity)
    var meshes = 0
    while (pending.isNotEmpty()) {
        val current = pending.removeFirst()
        if (current.components[ModelComponent::class.java] != null) {
            current.components.set(GroundShadowComponent(castsShadowEnabled = casts, receivesShadowEnabled = receives))
            meshes++
        }
        current.getChildren().forEach { pending.addLast(it) }
    }
    check(meshes > 0) { "Ground shadow has no render mesh for $label" }
    Log.i(TAG, "GroundShadow bound label=$label meshes=$meshes casts=$casts receives=$receives")
}

/** Root ownership releases all lights, including partial initialization failures. */
private fun addPointLight(
    root: Entity,
    position: Vector3,
    color: Color4,
    lumens: Float,
    radiusMeters: Float,
    enabled: Boolean = true,
): Entity {
    val light = Entity()
    try {
        check(root.addChild(light)) { "Could not attach point light" }
        light.components.set(PointLightComponent(color, lumens, radiusMeters))
        checkNotNull(light.components[TransformComponent::class.java]).setPosition(root.convertPositionFrom(position, null))
        light.enabled = enabled
        return light
    } catch (error: Exception) {
        try {
            if (light.valid) light.destroy()
        } catch (cleanup: Exception) {
            error.addSuppressed(cleanup)
        }
        throw error
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
