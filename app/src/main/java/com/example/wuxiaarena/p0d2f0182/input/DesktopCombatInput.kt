package com.example.wuxiaarena.p0d2f0182.input

import android.view.KeyEvent
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin

/** These controls author poses for the desktop preview, never combat results. */
enum class DesktopCombatAction {
    SLASH, LEFT_SLASH, RIGHT_SLASH, THRUST,
    GUARD_OVERHEAD, GUARD_LEFT, GUARD_RIGHT,
    DODGE_LEFT, DODGE_RIGHT, DUCK, SKILL,
}

internal data class DesktopPoseFrame(
    val head: ObservedPose,
    val left: ObservedPose,
    val right: ObservedPose,
)

object DesktopCombatInput {
    private val gate = Any()
    @Volatile
    var enabled: Boolean = false
        private set

    private val zero = Vector3(0.0, 0.0, 0.0)
    private val identity = Quaternion(0.0, 0.0, 0.0, 1.0)
    private val restingLeft = HandPose(Vector3(-0.25, -0.4, -0.35), identity)
    private val restingRight = HandPose(Vector3(0.25, -0.4, -0.35), identity)
    private var action: DesktopCombatAction? = null
    private var startedAtNanos = 0L
    private var guardHeld = false
    private var guardReleasedAtNanos: Long? = null
    private val pressedKeys = mutableSetOf<Int>()
    private var entryPose: LocalPose? = null
    private var lastLocalPose: LocalPose? = null

    private data class HandPose(val position: Vector3, val rotation: Quaternion)
    private data class LocalPose(
        val headOffset: Vector3,
        val left: HandPose,
        val right: HandPose,
    )
    private data class Keyframe(val seconds: Double, val pose: LocalPose)

    internal fun configure(active: Boolean) = synchronized(gate) {
        if (enabled != active) clearAction()
        enabled = active
    }

    fun trigger(action: DesktopCombatAction) = synchronized(gate) {
        if (enabled) startAction(action, System.nanoTime(), held = false)
    }

    fun reset() = synchronized(gate) { clearAction() }

    /** Key values are Android key codes. Only this bounded whitelist is handled. */
    internal fun handleKey(keyCode: Int, down: Boolean, repeatCount: Int): Boolean = synchronized(gate) {
        val requested = actionForKey(keyCode) ?: return false
        if (!enabled) return false
        if (down) {
            if (repeatCount == 0 && pressedKeys.add(keyCode)) {
                startAction(requested, System.nanoTime(), held = requested.isGuard())
            }
        } else {
            pressedKeys.remove(keyCode)
            if (action == requested && guardHeld && pressedKeys.none { actionForKey(it) == requested }) {
                guardHeld = false
                guardReleasedAtNanos = System.nanoTime()
            }
        }
        true
    }

    internal fun frame(sourceHead: ObservedPose, nowNanos: Long): DesktopPoseFrame? = synchronized(gate) {
        if (!enabled || sourceHead.quality == TrackingQuality.SOURCE_REPORTED_INVALID) return null
        val sourcePosition = sourceHead.position?.takeIf { it.isFinite() } ?: return null
        val sourceRotation = sourceHead.rotation?.normalizedOrNull() ?: return null
        val currentAction = action
        val age = if (currentAction == null) 0.0 else (nowNanos - startedAtNanos) / 1_000_000_000.0
        if (age < 0.0 || !age.isFinite()) clearAction()
        val local = if (currentAction == null || age < 0.0) rest() else poseFor(currentAction, age, nowNanos)
        lastLocalPose = local
        val forward = sourceRotation.rotate(Vector3(0.0, 0.0, -1.0)) ?: return null
        val heading = yaw(atan2(-forward.x, -forward.z))
        val headOffset = heading.rotate(local.headOffset) ?: return null
        val headPosition = sourcePosition + headOffset
        fun observe(hand: HandPose): ObservedPose {
            val offset = checkNotNull(sourceRotation.rotate(hand.position))
            return ObservedPose(headPosition + offset, (sourceRotation * hand.rotation).normalizedOrNull(), TrackingQuality.UNKNOWN)
        }
        DesktopPoseFrame(
            ObservedPose(headPosition, sourceRotation, TrackingQuality.UNKNOWN),
            observe(local.left),
            observe(local.right),
        )
    }

    private fun startAction(requested: DesktopCombatAction, now: Long, held: Boolean) {
        entryPose = lastLocalPose ?: rest()
        action = requested
        startedAtNanos = now
        guardHeld = held
        guardReleasedAtNanos = null
    }

    private fun clearAction() {
        action = null
        startedAtNanos = 0L
        guardHeld = false
        guardReleasedAtNanos = null
        pressedKeys.clear()
        entryPose = null
        lastLocalPose = null
    }

    private fun rest() = LocalPose(zero, restingLeft, restingRight)

    private fun poseFor(requested: DesktopCombatAction, age: Double, now: Long): LocalPose {
        if (requested.isGuard()) return guardPose(requested, age, now)
        val keys = when (requested) {
            DesktopCombatAction.SLASH -> listOf(
                Keyframe(0.0, rest()),
                Keyframe(0.13, rightHand(0.12, 0.08, -0.25, pitch(100.0))),
                Keyframe(0.29, rightHand(0.10, -0.28, -0.58, identity)),
                Keyframe(0.44, rightHand(0.10, -0.70, -0.45, pitch(-65.0))),
                Keyframe(0.66, rest()),
            )
            DesktopCombatAction.LEFT_SLASH -> sideSlash(-1.0)
            DesktopCombatAction.RIGHT_SLASH -> sideSlash(1.0)
            DesktopCombatAction.THRUST -> listOf(
                Keyframe(0.0, rest()),
                Keyframe(0.12, rightHand(0.12, -0.35, -0.12, identity)),
                Keyframe(0.29, rightHand(0.12, -0.30, -0.72, identity)),
                Keyframe(0.40, rightHand(0.12, -0.30, -0.72, identity)),
                Keyframe(0.62, rest()),
            )
            DesktopCombatAction.DODGE_LEFT -> dodge(-0.42, 0.0)
            DesktopCombatAction.DODGE_RIGHT -> dodge(0.42, 0.0)
            DesktopCombatAction.DUCK -> dodge(0.0, -0.38)
            DesktopCombatAction.SKILL -> twoHandThrust()
            else -> error("Guard action must use its hold path")
        }
        if (age >= keys.last().seconds) {
            action = null
            return rest()
        }
        val end = keys.indexOfFirst { it.seconds >= age }.coerceAtLeast(1)
        val from = keys[end - 1]
        val to = keys[end]
        val fraction = ((age - from.seconds) / (to.seconds - from.seconds)).coerceIn(0.0, 1.0)
        return interpolate(if (end == 1) entryPose ?: from.pose else from.pose, to.pose, smooth(fraction))
    }

    private fun sideSlash(side: Double): List<Keyframe> = listOf(
        Keyframe(0.0, rest()),
        Keyframe(0.13, rightHand(side * 0.36, -0.22, -0.14, yawDegrees(side * 100.0) * pitch(10.0))),
        Keyframe(0.29, rightHand(0.08, -0.32, -0.59, identity)),
        Keyframe(0.44, rightHand(-side * 0.40, -0.42, -0.34, yawDegrees(-side * 80.0))),
        Keyframe(0.66, rest()),
    )

    private fun dodge(x: Double, y: Double): List<Keyframe> {
        val shifted = rest().copy(headOffset = Vector3(x, y, 0.0))
        return listOf(Keyframe(0.0, rest()), Keyframe(0.14, shifted), Keyframe(0.43, shifted), Keyframe(0.68, rest()))
    }

    private fun twoHandThrust(): List<Keyframe> {
        val charged = LocalPose(
            zero,
            HandPose(Vector3(-0.06, -0.38, -0.28), identity),
            HandPose(Vector3(0.06, -0.38, -0.30), identity),
        )
        val extended = charged.copy(
            left = charged.left.copy(position = Vector3(-0.06, -0.30, -0.78)),
            right = charged.right.copy(position = Vector3(0.06, -0.30, -0.80)),
        )
        return listOf(
            Keyframe(0.0, rest()), Keyframe(0.16, charged), Keyframe(0.70, charged),
            Keyframe(0.92, extended), Keyframe(1.04, extended), Keyframe(1.30, rest()),
        )
    }

    private fun guardPose(requested: DesktopCombatAction, age: Double, now: Long): LocalPose {
        val guarded = when (requested) {
            DesktopCombatAction.GUARD_OVERHEAD -> rightHand(0.40, 0.08, -0.45, yawDegrees(90.0))
            DesktopCombatAction.GUARD_LEFT -> rightHand(-0.38, -0.30, -0.40, pitch(90.0))
            DesktopCombatAction.GUARD_RIGHT -> rightHand(0.38, -0.30, -0.40, pitch(90.0))
            else -> error("Expected guard pose")
        }
        val release = guardReleasedAtNanos
        val releaseAge = if (release == null) (age - 2.0) else (now - release) / 1_000_000_000.0
        if (!guardHeld && releaseAge >= 0.0) {
            if (releaseAge >= 0.18) {
                action = null
                return rest()
            }
            val releasePose = if (release == null) guarded else {
                val heldAge = (release - startedAtNanos) / 1_000_000_000.0
                interpolate(entryPose ?: rest(), guarded, smooth((heldAge / 0.14).coerceIn(0.0, 1.0)))
            }
            return interpolate(releasePose, rest(), smooth((releaseAge / 0.18).coerceIn(0.0, 1.0)))
        }
        return interpolate(entryPose ?: rest(), guarded, smooth((age / 0.14).coerceIn(0.0, 1.0)))
    }

    private fun rightHand(x: Double, y: Double, z: Double, rotation: Quaternion) =
        rest().copy(right = HandPose(Vector3(x, y, z), rotation))

    private fun interpolate(from: LocalPose, to: LocalPose, amount: Double): LocalPose {
        fun hand(a: HandPose, b: HandPose) = HandPose(
            a.position + (b.position - a.position) * amount,
            interpolateRotation(a.rotation, b.rotation, amount),
        )
        return LocalPose(
            from.headOffset + (to.headOffset - from.headOffset) * amount,
            hand(from.left, to.left), hand(from.right, to.right),
        )
    }

    private fun interpolateRotation(from: Quaternion, to: Quaternion, amount: Double): Quaternion {
        val sign = if (from.x * to.x + from.y * to.y + from.z * to.z + from.w * to.w < 0.0) -1.0 else 1.0
        return checkNotNull(Quaternion(
            from.x + (to.x * sign - from.x) * amount,
            from.y + (to.y * sign - from.y) * amount,
            from.z + (to.z * sign - from.z) * amount,
            from.w + (to.w * sign - from.w) * amount,
        ).normalizedOrNull())
    }

    private fun smooth(value: Double) = value * value * (3.0 - 2.0 * value)
    private fun pitch(degrees: Double): Quaternion {
        val half = Math.toRadians(degrees) / 2.0
        return Quaternion(sin(half), 0.0, 0.0, cos(half))
    }
    private fun yawDegrees(degrees: Double) = yaw(Math.toRadians(degrees))
    private fun yaw(radians: Double) = Quaternion(0.0, sin(radians / 2.0), 0.0, cos(radians / 2.0))
    private fun DesktopCombatAction.isGuard() = this == DesktopCombatAction.GUARD_OVERHEAD ||
        this == DesktopCombatAction.GUARD_LEFT || this == DesktopCombatAction.GUARD_RIGHT

    private fun actionForKey(keyCode: Int): DesktopCombatAction? = when (keyCode) {
        KeyEvent.KEYCODE_1, KeyEvent.KEYCODE_J -> DesktopCombatAction.SLASH
        KeyEvent.KEYCODE_2 -> DesktopCombatAction.LEFT_SLASH
        KeyEvent.KEYCODE_3 -> DesktopCombatAction.RIGHT_SLASH
        KeyEvent.KEYCODE_4, KeyEvent.KEYCODE_K -> DesktopCombatAction.THRUST
        KeyEvent.KEYCODE_5, KeyEvent.KEYCODE_V -> DesktopCombatAction.GUARD_OVERHEAD
        KeyEvent.KEYCODE_6, KeyEvent.KEYCODE_B -> DesktopCombatAction.GUARD_LEFT
        KeyEvent.KEYCODE_7, KeyEvent.KEYCODE_N -> DesktopCombatAction.GUARD_RIGHT
        KeyEvent.KEYCODE_8, KeyEvent.KEYCODE_Z -> DesktopCombatAction.DODGE_LEFT
        KeyEvent.KEYCODE_9, KeyEvent.KEYCODE_X -> DesktopCombatAction.DODGE_RIGHT
        KeyEvent.KEYCODE_C -> DesktopCombatAction.DUCK
        KeyEvent.KEYCODE_G -> DesktopCombatAction.SKILL
        else -> null
    }
}
