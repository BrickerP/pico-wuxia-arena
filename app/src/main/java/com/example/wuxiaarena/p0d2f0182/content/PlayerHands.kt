package com.example.wuxiaarena.p0d2f0182.content

import androidx.annotation.MainThread
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.pico.spatial.core.ecs.CollisionComponent
import com.pico.spatial.core.ecs.Entity
import com.pico.spatial.core.ecs.InteractableComponent
import com.pico.spatial.core.ecs.TransformComponent
import com.pico.spatial.core.ecs.animation.AnimationPlayConfig
import com.pico.spatial.core.ecs.animation.AnimationPlaybackController
import com.pico.spatial.core.ecs.animation.AnimationTransitionMode
import com.pico.spatial.core.ecs.resource.AnimationResource
import com.pico.spatial.core.math.Quat
import com.pico.spatial.core.math.Vector3
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext

/** Two visual-only hand hierarchies owned by one HomeStage lifetime. */
@MainThread
internal class PlayerHands(private val parent: Entity) {
    private var right: LoadedHand? = null
    private var left: LoadedHand? = null
    private var loadStarted = false
    private var closed = false

    /** Called once from SpatialView.initial, on the scene's existing main-thread coroutine. */
    suspend fun load(isCurrent: () -> Boolean) {
        check(!loadStarted && !closed) { "Player hands can only load once per scene" }
        loadStarted = true
        try {
            right = loadHand(RIGHT_ASSET, Hand.RIGHT, isCurrent)
            if (right == null) { close(); return }
            left = loadHand(LEFT_ASSET, Hand.LEFT, isCurrent)
            if (left == null) close()
        } catch (error: Exception) {
            try { close() } catch (cleanup: Exception) { if (cleanup !== error) error.addSuppressed(cleanup) }
            throw error
        }
    }

    private suspend fun loadHand(asset: String, hand: Hand, isCurrent: () -> Boolean): LoadedHand? {
        // Native loading may finish after cancellation. Always acquire its returned handle,
        // then dispose it before returning to a cancelled or replaced scene.
        val model = withContext(NonCancellable) { Entity.loadSuspend(asset) }
        var loaded: LoadedHand? = null
        try {
            currentCoroutineContext().ensureActive()
            if (closed || !parent.valid || !isCurrent()) {
                if (model.valid) check(model.destroy()) { "Could not release late $hand hand" }
                return null
            }
            removeInteractionComponents(model)
            loaded = LoadedHand(model)
            loaded.setGripTime(playerHandGripTime(hand, Hand.RIGHT))
            // SDK requires the animated hierarchy enabled when creating playback.
            // It is still unattached here; hide it only after the paused pose is ready.
            model.enabled = false
            check(parent.addChild(model)) { "Could not attach $hand player hand" }
            return loaded
        } catch (error: Exception) {
            try {
                if (loaded != null) loaded.close()
                else if (model.valid) check(model.destroy()) { "Could not release $hand player hand" }
            } catch (cleanup: Exception) {
                if (cleanup !== error) error.addSuppressed(cleanup)
            }
            throw error
        }
    }

    /** Consumes the same accepted controller observations as the existing dao presenter. */
    fun present(snapshot: TrackingSnapshot?) {
        if (closed || !parent.valid) return
        val equippedHand = snapshot?.dominantHand ?: Hand.RIGHT
        var failure: Exception? = null
        try {
            presentHand(right, Hand.RIGHT, playerHandTransform(snapshot?.right?.pose, Hand.RIGHT), equippedHand)
        } catch (error: Exception) {
            failure = error
        }
        try {
            presentHand(left, Hand.LEFT, playerHandTransform(snapshot?.left?.pose, Hand.LEFT), equippedHand)
        } catch (error: Exception) {
            if (failure == null) failure = error else if (failure !== error) failure.addSuppressed(error)
        }
        failure?.let { throw it }
    }

    private fun presentHand(loaded: LoadedHand?, hand: Hand, pose: PlayerHandTransform?, equippedHand: Hand) {
        val model = loaded?.model ?: return
        if (!model.valid) return
        if (pose == null) {
            if (model.enabled) model.enabled = false
            return
        }
        try {
            loaded.setGripTime(playerHandGripTime(hand, equippedHand))
            val transform = checkNotNull(model.components[TransformComponent::class.java])
            // Incoming pose is Stage/container-space. Models are immediate children of parent.
            transform.setPosition(parent.convertPositionFrom(Vector3(
                pose.position.x.toFloat(), pose.position.y.toFloat(), pose.position.z.toFloat(),
            ), null))
            transform.setQuaternion(parent.convertRotationFrom(Quat(
                pose.rotation.x.toFloat(), pose.rotation.y.toFloat(), pose.rotation.z.toFloat(), pose.rotation.w.toFloat(),
            ), null))
            if (!model.enabled) model.enabled = true
        } catch (error: Exception) {
            model.enabled = false
            throw error
        }
    }

    fun close() {
        if (closed) return
        closed = true
        val resources = listOfNotNull(right, left)
        right = null
        left = null
        closePlayerHandResources(resources)
    }

    private class LoadedHand(val model: Entity) : AutoCloseable {
        private var resources = emptyList<AnimationResource>()
        private var gripClip: AnimationResource? = null
        private var controller: AnimationPlaybackController? = null
        private var gripTime: Float? = null
        private var closed = false

        init {
            try {
                val target = model.findSkeletonRootEntity(includeDisabled = true).single()
                resources = model.findSkinnedMeshEntity(includeDisabled = true).single().getAnimationResources().toList()
                val imported = resources.single { it.getName() == "grip" }
                val clip = imported.repeat(0)
                gripClip = clip
                val playback = target.playAnimation(clip, AnimationPlayConfig(
                    transitionDuration = 0f,
                    transitionMode = AnimationTransitionMode.STOP_AND_CROSSFADE,
                ))
                controller = playback
                check(playback.valid && playback.getDuration() >= 1f) { "Player grip animation must span 0..1 seconds" }
                playback.pause()
            } catch (error: Exception) {
                try { close() } catch (cleanup: Exception) { if (cleanup !== error) error.addSuppressed(cleanup) }
                throw error
            }
        }

        fun setGripTime(time: Float) {
            if (gripTime == time) return
            val playback = checkNotNull(controller)
            check(!closed && playback.valid) { "Player grip animation controller is unavailable" }
            playback.setTime(time)
            gripTime = time
        }

        override fun close() {
            if (closed) return
            closed = true
            val handles = buildList<AutoCloseable> {
                controller?.let(::add)
                gripClip?.let(::add)
                addAll(resources)
                add(AutoCloseable {
                    if (model.valid) {
                        model.enabled = false
                        check(model.destroy()) { "Could not destroy player hand" }
                    }
                })
            }
            controller = null
            gripClip = null
            resources = emptyList()
            closePlayerHandResources(handles)
        }
    }

    private companion object {
        const val RIGHT_ASSET = "asset://models/player_hands/right_hand.glb"
        const val LEFT_ASSET = "asset://models/player_hands/left_hand.glb"

        fun removeInteractionComponents(root: Entity) {
            val pending = ArrayDeque<Entity>()
            pending.addLast(root)
            while (pending.isNotEmpty()) {
                val entity = pending.removeFirst()
                entity.components.remove(CollisionComponent::class.java)
                entity.components.remove(InteractableComponent::class.java)
                entity.getChildren().forEach(pending::addLast)
            }
        }
    }
}
