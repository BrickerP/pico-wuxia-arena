package com.example.wuxiaarena.p0d2f0182.content

import android.util.Log
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.pico.spatial.core.ecs.AttachmentPanelComponent
import com.pico.spatial.core.ecs.GroundShadowComponent
import com.pico.spatial.core.ecs.ModelComponent
import com.pico.spatial.core.ecs.LookAtComponent
import com.pico.spatial.core.ecs.LookAtForwardDirection
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
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.p0d2f0182.runtime.HandPosePresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaPresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.p0d2f0182.runtime.arenaOpponents
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import java.util.concurrent.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.sin
import kotlin.math.cos
import com.example.wuxiaarena.core.math.Vector3 as TrackingVector3

private const val TAG = "TavernScene"
private const val COURTYARD_ASSET = "asset://models/courtyard_hero.glb"
private const val PLAYER_DAO_ASSET = "asset://models/dao_grip.glb"
private const val CONTROL_PANEL_ID = "trial-control"
private const val STATUS_PANEL_ID = "combat-status"
private const val HUD_WORLD_SCALE = 1.4f
private const val STATUS_WORLD_SCALE = 1.65f
private val DAMAGE_PANEL_IDS = List(DamagePopupTimeline.SLOT_COUNT) { "contact-damage-$it" }
private const val ENEMY_STAGE_Z = -2.4f

private class SceneOwner(
    private val onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    private val onOpponentChange: (Long, Int) -> Boolean,
    private val sceneScope: CoroutineScope,
    private val onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
    private val onEnemyPresenter: (ArenaPresenter?) -> Unit,
    private val damageTextStates: List<DamagePopupTextState>,
) {
    var root: Entity? = null
    var playerWeapon: Entity? = null
    var playerHands: PlayerHands? = null
    private data class OpponentRequest(val generation: Long, val roundNumber: Int)

    private class LoadedOpponent(val roundNumber: Int, val entity: Entity) {
        var animator: EnemyAnimator? = null
        var ready = false

        fun close() {
            ready = false
            // Keep each failed owner for an explicit retry instead of loading over it.
            animator?.close()
            animator = null
            if (entity.valid) check(entity.destroy()) { "Could not destroy the previous opponent" }
        }
    }

    private var opponent: LoadedOpponent? = null
    private var opponentRequest: OpponentRequest? = null
    private var failedOpponentRequest: OpponentRequest? = null
    private var opponentJob: Job? = null
    private var opponentCompletion: CompletableDeferred<Unit>? = null
    var lighting: SceneLighting? = null
    var weather: SceneWeather? = null
    private var teardownRoot: Entity? = null
    val teardownPending: Boolean
        get() = teardownRoot != null || lighting != null || weather != null || opponent != null ||
            opponentCompletion?.isCompleted == false
    var effects: CombatEffects? = null
    var bladeTrail: PlayerBladeTrail? = null
    var contactLight: Entity? = null
    val panelAnchors = mutableMapOf<String, Entity>()
    val damageAnchors = mutableListOf<Entity>()
    private val damageTimeline = DamagePopupTimeline()
    private var damageUnavailable = false
    var damageWorldScale = 1f
    var statusWorldPosition: Vector3? = null
    var statusWorldRotation: Quat = Quat.identity()
    var statusPanelY = 2.15f
    private var impactRound = -1L
    private val seenImpactLights = mutableSetOf<Long>()
    private var pulseUntil = 0L

    fun presentArena(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        val parent = root ?: return
        if (!parent.valid) return
        requestOpponent(state, parent)
        weather?.update(System.nanoTime(), state.sceneReady)
        presentImpactLight(state, events)
        effects?.present(state, events)
        bladeTrail?.present(state)
        presentDamagePopups(state, events)
        val loaded = opponent?.takeIf { it.ready && it.roundNumber == state.roundNumber } ?: return
        val enemy = loaded.entity
        if (!enemy.valid) return
        state.enemyPosition?.let { position ->
            val displayPosition = position + state.enemyRecoilOffset
            val transform = checkNotNull(enemy.components[TransformComponent::class.java])
            transform.setPosition(parent.convertPositionFrom(Vector3(displayPosition.x.toFloat(), displayPosition.y.toFloat(), displayPosition.z.toFloat()), null))
            val halfYaw = state.enemyYawRadians / 2f
            transform.setQuaternion(parent.convertRotationFrom(Quat(0f, sin(halfYaw), 0f, cos(halfYaw)), null))
            panelAnchors[STATUS_PANEL_ID]?.let { anchor ->
                val readablePosition = readableStatusPosition(position, state.playerHeadPosition, statusPanelY.toDouble())
                val location = Vector3(readablePosition.x.toFloat(), readablePosition.y.toFloat(), readablePosition.z.toFloat())
                val facing = readableStatusRotation(readablePosition, state.playerHeadPosition)
                val rotation = Quat(facing.x.toFloat(), facing.y.toFloat(), facing.z.toFloat(), facing.w.toFloat())
                statusWorldPosition = location
                statusWorldRotation = rotation
                placeAttachment(parent, anchor, location, rotation, STATUS_WORLD_SCALE)
            }
        }
        loaded.animator?.present(state, events)
    }

    private fun requestOpponent(state: ArenaViewState, parent: Entity) {
        val request = OpponentRequest(state.roundGeneration, state.roundNumber)
        val previous = opponentRequest
        if (previous != null && request.generation < previous.generation) return
        check(state.roundNumber in 1..arenaOpponents.size) { "Unknown opponent round ${state.roundNumber}" }
        opponentRequest = request
        // Hide before dispatch: a new round must never render the previous opponent for one frame.
        opponent?.takeIf { it.roundNumber != request.roundNumber }?.let { previousOpponent ->
            previousOpponent.ready = false
            if (previousOpponent.entity.valid) previousOpponent.entity.enabled = false
        }
        if (opponent?.let { it.ready && it.roundNumber == request.roundNumber } == true ||
            failedOpponentRequest == request || opponentJob?.isActive == true) return
        val completion = CompletableDeferred<Unit>()
        opponentCompletion = completion
        val job = sceneScope.launch(start = CoroutineStart.LAZY) {
            var attempted: OpponentRequest? = null
            try {
                // Requests are serialized. A newer round replaces a pending target, never overlaps its load.
                while (root === parent && parent.valid) {
                    val target = opponentRequest ?: break
                    attempted = target
                    if (opponent?.let { it.ready && it.roundNumber == target.roundNumber } == true) break
                    if (!onOpponentChange(target.generation, target.roundNumber)) {
                        failedOpponentRequest = target
                        break
                    }
                    closeOpponent()
                    val definition = arenaOpponents[target.roundNumber - 1]
                    // Native load returns an Entity handle. Finish acquisition even on disposal so it can be destroyed.
                    val entity = withContext(NonCancellable) { Entity.loadSuspend(definition.asset) }
                    val loaded = LoadedOpponent(target.roundNumber, entity)
                    opponent = loaded
                    currentCoroutineContext().ensureActive()
                    if (root !== parent || !parent.valid || opponentRequest != target) {
                        closeOpponent()
                        continue
                    }
                    entity.enabled = false
                    check(parent.addChild(entity)) { "Could not attach ${definition.name}" }
                    val transform = checkNotNull(entity.components[TransformComponent::class.java]) {
                        "Tripo enemy has no transform"
                    }
                    transform.setPosition(parent.convertPositionFrom(Vector3(0f, 0.028f, ENEMY_STAGE_Z), null))
                    transform.setQuaternion(parent.convertRotationFrom(Quat.identity(), null))
                    bindGroundShadow(entity, casts = true, receives = false, label = definition.name)
                    loaded.animator = EnemyAnimator(entity)
                    val origin = entity.convertPositionTo(Vector3(0f, 0f, 0f), null)
                    val bounds = entity.getVisualBounds(entity)
                    val reachX = abs(bounds.center.x) + bounds.size.x / 2f
                    val reachZ = abs(bounds.center.z) + bounds.size.z / 2f
                    loaded.ready = true
                    entity.enabled = true
                    failedOpponentRequest = null
                    Log.i(TAG, "Tripo enemy attached; round=${target.roundNumber}, generation=${target.generation}, " +
                        "local bounds center=${bounds.center}, size=${bounds.size}; stage origin=$origin")
                    onEnemyGeometry(
                        TrackingVector3(origin.x.toDouble(), origin.y.toDouble(), origin.z.toDouble()),
                        hypot(reachX.toDouble(), reachZ.toDouble()),
                    )
                    if (opponentRequest == target) break
                }
            } catch (error: Exception) {
                try { closeOpponent() } catch (cleanup: Exception) { error.addSuppressed(cleanup) }
                if (error is CancellationException) throw error
                failedOpponentRequest = attempted
                Log.e(TAG, "Unable to load the current opponent", error)
            } finally {
                opponentJob = null
            }
        }
        opponentJob = job
        // Also completes when the composition scope was cancelled before a lazy job could start.
        job.invokeOnCompletion { completion.complete(Unit) }
        job.start()
    }

    private fun closeOpponent() {
        val current = opponent ?: return
        current.close()
        opponent = null
    }

    private fun presentDamagePopups(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (damageUnavailable) return
        val parent = root ?: return
        try {
            val active = state.sceneReady && state.inputReady && state.pauseReason == null &&
                (state.result == TrialResult.FIGHTING || state.result == TrialResult.ROUND_CLEAR)
            val frames = damageTimeline.update(state.roundGeneration, state.roundNumber, active,
                state.simulationNanos, System.nanoTime(), state.playerHeadPosition, events)
            for ((index, anchor) in damageAnchors.withIndex()) {
                val frame = frames.firstOrNull { it.slot == index }
                val text = damageTextStates[index]
                text.content = frame?.content
                text.opacity = frame?.opacity ?: 0f
                if (!anchor.valid) continue
                if (frame == null) {
                    anchor.enabled = false
                    continue
                }
                val point = Vector3(frame.position.x.toFloat(), frame.position.y.toFloat(), frame.position.z.toFloat())
                check(point.x.isFinite() && point.y.isFinite() && point.z.isFinite()) {
                    "Damage contact exceeds the Stage presentation range"
                }
                val transform = checkNotNull(anchor.components[TransformComponent::class.java])
                transform.setPosition(parent.convertPositionFrom(point, null))
                val scale = damageWorldScale * frame.scale
                transform.setScaleVector(Vector3(scale, scale, scale))
                anchor.enabled = true
            }
        } catch (error: Exception) {
            damageUnavailable = true
            clearDamagePopups()
            Log.w(TAG, "Damage readouts became unavailable", error)
        }
    }

    private fun clearDamagePopups() {
        damageTimeline.clear()
        damageTextStates.forEach {
            it.content = null
            it.opacity = 0f
        }
        for (anchor in damageAnchors) {
            try {
                if (anchor.valid) anchor.enabled = false
            } catch (error: Exception) {
                Log.w(TAG, "Unable to hide damage readout", error)
            }
        }
    }

    private fun presentImpactLight(state: ArenaViewState, events: List<EnemyCombatEvent>) {
        if (state.roundGeneration < impactRound) return
        val parent = root ?: return
        val light = contactLight?.takeIf { it.valid } ?: return
        val now = System.nanoTime()
        if (impactRound != state.roundGeneration) {
            impactRound = state.roundGeneration
            seenImpactLights.clear()
            pulseUntil = 0L
        }
        val fresh = events.filterIsInstance<CombatImpact>().filter { seenImpactLights.add(it.id) }
        val impact = currentContactImpacts(fresh, state.simulationNanos).firstOrNull {
            remainingNativeImpactLightNanos(it, state.simulationNanos) > 0L
        }
        if (impact != null) {
            val cue = checkNotNull(nativeImpactLight(impact))
            val remaining = remainingNativeImpactLightNanos(impact, state.simulationNanos)
            val direction = impact.normal.normalizedOrNull() ?: TrackingVector3(0.0, 0.0, 1.0)
            val point = impact.point + direction * 0.035
            val position = Vector3(point.x.toFloat(), point.y.toFloat(), point.z.toFloat())
            if (position.x.isFinite() && position.y.isFinite() && position.z.isFinite()) {
                light.components.set(PointLightComponent(
                    Color4(cue.red, cue.green, cue.blue, 1f), cue.intensity, cue.attenuationRadius,
                ))
                checkNotNull(light.components[TransformComponent::class.java]).setPosition(parent.convertPositionFrom(position, null))
                pulseUntil = now + remaining
            }
        }
        val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
        val available = state.sceneReady && (terminal || (state.pauseReason == null && state.inputReady))
        if (!available) pulseUntil = 0L
        val visible = available && now < pulseUntil
        if (light.enabled != visible) light.enabled = visible
    }

    fun presentPlayerHand(snapshot: TrackingSnapshot?) {
        try {
            playerHands?.present(snapshot)
        } catch (error: Exception) {
            Log.w(TAG, "Player-hand presentation failed", error)
        }
        val pose = if (snapshot?.hasRequiredObservations == true) {
            (if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right)?.pose
        } else null
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
        opponentRequest = null
        failedOpponentRequest = null
        opponentJob?.cancel()
        val current = root ?: teardownRoot
        if (current == null) {
            try { closeOpponent() } catch (error: Exception) { Log.w(TAG, "Opponent cleanup will be retried", error) }
            closeAtmosphere()
            return
        }
        clearDamagePopups()
        damageAnchors.clear()
        damageUnavailable = false
        statusWorldPosition = null
        statusWorldRotation = Quat.identity()
        teardownRoot = current
        root = null
        playerWeapon = null
        contactLight = null
        panelAnchors.clear()
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
            try {
                closeOpponent()
            } catch (error: Exception) {
                Log.w(TAG, "Opponent cleanup will be retried", error)
            }
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
            try {
                playerHands?.close()
            } catch (error: Exception) {
                Log.w(TAG, "Player-hand cleanup failed", error)
            }
            playerHands = null
            closeAtmosphere()
        } finally {
            try {
                onEnemyGeometry(null, 0.0)
            } finally {
                try {
                    if (current.valid) check(current.destroy()) { "Unable to destroy scene root" }
                    teardownRoot = null
                } catch (error: Exception) {
                    Log.w(TAG, "Scene root cleanup will be retried", error)
                } finally {
                    // A failed child close can finish after its parent releases native users.
                    closeAtmosphere()
                }
            }
        }
    }

    private fun closeAtmosphere() {
        try {
            weather?.close()
            weather = null
        } catch (error: Exception) {
            Log.w(TAG, "Weather cleanup failed", error)
        }
        try {
            val currentLighting = lighting
            currentLighting?.close()
            if (currentLighting?.isReleased != false) lighting = null
        } catch (error: Exception) {
            Log.w(TAG, "Lighting cleanup failed", error)
        }
    }

    suspend fun releasePreviousScene() {
        release()
        // The same builder continues after old IO; returning early would leave an empty scene.
        opponentCompletion?.await()
        lighting?.awaitRelease()
        release()
        check(!teardownPending) { "Previous scene still owns native resources" }
    }
}

@Composable
internal fun HomeStage(
    onEnemyGeometry: (TrackingVector3?, Double) -> Unit,
    onOpponentChange: (Long, Int) -> Boolean,
    onPlayerHandPresenter: (HandPosePresenter?) -> Unit,
    onEnemyPresenter: (ArenaPresenter?) -> Unit,
    controlsHeightDp: Int,
    controlsPanel: @Composable () -> Unit,
    statusPanel: @Composable () -> Unit,
) {
    val damageTextStates = remember { List(DamagePopupTimeline.SLOT_COUNT) { DamagePopupTextState() } }
    val sceneScope = rememberCoroutineScope()
    val owner = remember { SceneOwner(onEnemyGeometry, onOpponentChange, sceneScope,
        onPlayerHandPresenter, onEnemyPresenter, damageTextStates) }
    val currentControls = rememberUpdatedState(controlsPanel)
    val currentStatus = rememberUpdatedState(statusPanel)
    val currentControlHeight = rememberUpdatedState(controlsHeightDp)
    val converter = LocalPhysicalLengthConverter.current
    val statusHeightMeters = converter.dpToLength(260.dp, LengthUnit.Meters) * STATUS_WORLD_SCALE
    val statusPosition = Vector3(0f, maxOf(2.15f, 1.95f + statusHeightMeters / 2f), ENEMY_STAGE_Z)
    owner.statusPanelY = statusPosition.y
    owner.damageWorldScale = 0.18f / converter.dpToLength(128.dp, LengthUnit.Meters)
    val controlPosition = remember { Vector3(-0.6f, 1.2f, -1.75f) }
    val controlRotation = remember { Quat(0f, 0.17364818f, 0f, 0.98480775f) }
    val panels = remember<AttachmentPanelBuilder.() -> Unit> {
        {
            AttachmentPanel(CONTROL_PANEL_ID, alignment = AttachmentPanelComponent.Alignment.CENTER) {
                Box(Modifier.size(width = 400.dp, height = currentControlHeight.value.dp)) {
                    currentControls.value()
                }
            }
            AttachmentPanel(STATUS_PANEL_ID, alignment = AttachmentPanelComponent.Alignment.CENTER) {
                Box(Modifier.size(width = 500.dp, height = 260.dp)) { currentStatus.value() }
            }
            for ((index, id) in DAMAGE_PANEL_IDS.withIndex()) {
                AttachmentPanel(id, alignment = AttachmentPanelComponent.Alignment.CENTER) {
                    DamagePopupText(damageTextStates[index])
                }
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
                val location = owner.statusWorldPosition ?: statusPosition
                placeAttachment(root, owner.panelAnchors.getValue(STATUS_PANEL_ID), location, owner.statusWorldRotation, STATUS_WORLD_SCALE)
            }
        },
    ) { content, attachments ->
        try {
            withTimeout(15_000L) { owner.releasePreviousScene() }
        } catch (error: Exception) {
            Log.e(TAG, "Previous scene release failed; scene is unavailable", error)
            onEnemyGeometry(null, 0.0)
            if (error is CancellationException) throw error
            return@SpatialView
        }
        val root = Entity()
        owner.root = root
        var model: Entity? = null
        var modelAttached = false
        var playerWeapon: Entity? = null
        var playerWeaponAttached = false

        try {
            content.addEntity(root)
            for (id in listOf(CONTROL_PANEL_ID, STATUS_PANEL_ID)) {
                val panel = checkNotNull(attachments.entity(id)) { "Missing attachment $id" }
                val anchor = Entity()
                check(root.addChild(anchor)) { "Could not attach anchor $id" }
                owner.panelAnchors[id] = anchor
                check(anchor.addChild(panel)) { "Could not attach $id" }
            }
            for (id in DAMAGE_PANEL_IDS) {
                val panel = checkNotNull(attachments.entity(id)) { "Missing attachment $id" }
                val anchor = Entity()
                try {
                    check(root.addChild(anchor)) { "Could not attach damage anchor $id" }
                    owner.damageAnchors += anchor
                    anchor.enabled = false
                    check(anchor.addChild(panel)) { "Could not attach damage label $id" }
                    anchor.components.set(LookAtComponent().apply {
                        alignLocalUpToWorldUp = true
                        lookAtForwardDirection = LookAtForwardDirection.POSITIVE_Z
                        setViewerAsTarget()
                    })
                } catch (error: Exception) {
                    try {
                        if (anchor.valid) anchor.destroy()
                    } catch (cleanup: Exception) {
                        error.addSuppressed(cleanup)
                    }
                    throw error
                }
            }
            placeAttachment(root, owner.panelAnchors.getValue(CONTROL_PANEL_ID), controlPosition, controlRotation)
            placeAttachment(root, owner.panelAnchors.getValue(STATUS_PANEL_ID), statusPosition, Quat.identity(), STATUS_WORLD_SCALE)
            model = Entity.loadSuspend(COURTYARD_ASSET)
            if (owner.root !== root) {
                model.destroy()
                return@SpatialView
            }
            check(root.addChild(model)) { "Could not attach courtyard model" }
            modelAttached = true
            val transform = checkNotNull(model.components[TransformComponent::class.java]) {
                "Courtyard model has no transform"
            }
            transform.setPosition(root.convertPositionFrom(Vector3(0f, 0f, 0f), null))
            transform.setQuaternion(root.convertRotationFrom(Quat.identity(), null))
            for (name in listOf("EH_GroundReceiver", "EH_MortarAndDrain")) {
                bindGroundShadow(
                    checkNotNull(model.findEntity(name)) { "Courtyard receiver is unavailable: $name" },
                    casts = false, receives = true, label = name,
                )
            }

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
            val hands = PlayerHands(root)
            owner.playerHands = hands
            hands.load { owner.root === root && owner.playerHands === hands }
            if (owner.root !== root) {
                hands.close()
                return@SpatialView
            }
            onPlayerHandPresenter(owner::presentPlayerHand)
            Log.i(TAG, "Player dao attached; grip origin=0, blade forward=-Z, driven by shared hand observations")

            val lighting = SceneLighting.attach(root)
            owner.lighting = lighting
            try {
                lighting.loadEnvironment("textures/rain_night_ibl.ktx") {
                    owner.root === root && owner.lighting === lighting
                }
            } catch (error: Exception) {
                try {
                    lighting.close()
                    if (owner.lighting === lighting) owner.lighting = null
                } catch (cleanup: Exception) {
                    error.addSuppressed(cleanup)
                }
                throw error
            }
            if (owner.root !== root) {
                lighting.close()
                return@SpatialView
            }
            val weather = SceneWeather.load(
                root,
                "asset://models/weather/rain_tile.glb",
                "asset://models/weather/side_haze.glb",
                "asset://models/weather/rain_night_sky.glb",
            )
            if (owner.root !== root) {
                weather.close()
                return@SpatialView
            }
            owner.weather = weather
            weather.update(System.nanoTime(), true)
            owner.contactLight = addPointLight(
                root, Vector3(0f, 0f, 0f), Color4(1f, 0.9f, 0.7f, 1f), 0f, 0.60f, enabled = false,
            )
            try {
                val bounds = model.getVisualBounds(null)
                Log.i(TAG, "Tavern attached; stage bounds center=${bounds.center}, size=${bounds.size}")
            } catch (error: Exception) {
                Log.w(TAG, "Tavern attached but visual bounds are unavailable", error)
            }
            onEnemyPresenter(owner::presentArena)
        } catch (error: Exception) {
            for ((entity, attached) in listOf(
                model to modelAttached,
                playerWeapon to playerWeaponAttached,
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
    scale: Float = HUD_WORLD_SCALE,
) {
    if (!panel.valid) return
    val transform = checkNotNull(panel.components[TransformComponent::class.java])
    transform.setPosition(root.convertPositionFrom(position, null))
    transform.setQuaternion(root.convertRotationFrom(rotation, null))
    transform.setScaleVector(Vector3(scale, scale, scale))
}
