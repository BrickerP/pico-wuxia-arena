package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatAction
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput
import java.io.File

private fun Vector3.json() = "[$x,$y,$z]"
private fun meshJson(positions: List<Vector3>, indices: List<Int>, alpha: List<Float>, coreOffset: Int) =
    """{"positions":${positions.joinToString(prefix="[",postfix="]") { it.json() }},"indices":$indices,"alphas":$alpha,"core_vertex_offset":$coreOffset}"""

fun main(args: Array<String>) {
    val output = File(args[0])
    val head = ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))
    val state = TrackingState(Hand.RIGHT)
    val resolver = PlayerCombatResolver()
    val old = BaselineBladeTrailGeometry()
    val candidate = BladeTrailGeometry()
    DesktopCombatInput.configure(true)
    DesktopCombatInput.reset()
    DesktopCombatInput.trigger(DesktopCombatAction.LEFT_SLASH)
    // Read the real producer clock as existing DesktopCombatInputFrameTest does; do not replace its path.
    val origin = DesktopCombatInput::class.java.getDeclaredField("startedAtNanos").let {
        it.isAccessible = true
        it.getLong(DesktopCombatInput)
    }
    val frames = mutableListOf<String>()
    for (index in 0..48) {
        val age = index * 11_111_111L
        val now = origin + age
        val pose = checkNotNull(DesktopCombatInput.frame(head, now))
        check(state.accept(TrackingEvent.Head(ObservationStamp(index * 2L, now, 0L, InputOrigin.DESKTOP), pose.head)))
        check(state.accept(TrackingEvent.Controllers(ObservationStamp(index * 2L + 1, now, 0L, InputOrigin.DESKTOP), pose.left, pose.right)))
        val frame = checkNotNull(resolver.observe(state.snapshot, Vector3(0.0, 0.0, -1.25)))
        val a = old.sample(frame.bladeBase, frame.bladeTip, age, frame.bladeTipSpeed, frame.bladeAtRest, frame.motionGeneration)
        val b = candidate.sample(frame.bladeBase, frame.bladeTip, age, frame.bladeTipSpeed, frame.bladeAtRest, frame.motionGeneration)
        val before = a?.let { meshJson(it.positions, it.triangleIndices, it.alphas, it.positions.size) } ?: "null"
        val after = b?.let { meshJson(it.positions, it.triangleIndices, it.alphas, it.coreVertexOffset) } ?: "null"
        frames.add("""{"index":$index,"age_ns":$age,"base":${frame.bladeBase.json()},"tip":${frame.bladeTip.json()},"tip_speed":${frame.bladeTipSpeed},"at_rest":${frame.bladeAtRest},"motion_generation":${frame.motionGeneration},"before":$before,"after":$after}""")
    }
    DesktopCombatInput.configure(false)
    output.writeText("""{"source":"production DesktopCombatInput.LEFT_SLASH -> TrackingState -> PlayerCombatResolver; desktop synthetic input, not device recording","rate_hz":90,"head":[0,1.6,0],"frames":[${frames.joinToString(",")}]}""")
}
