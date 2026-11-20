package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import kotlin.math.sqrt

class CounterShoulderCueTest {
    private val head = Vector3(0.0, 1.65, 0.0)
    private val facing = Quaternion(0.0, 0.0, 0.0, 1.0)
    private val torso = EnemyContactPose(Vector3(0.0, 1.65, -1.40),
        Vector3(0.0, 0.65, -1.40), Vector3(0.0, 1.40, -1.40))

    private fun pose(base: Vector3, tip: Vector3) = AttackPoseSample(0.0, torso, base, tip)
    private fun verticalBlade(x: Double) = pose(Vector3(x, 1.14, -.70), Vector3(x, 1.87, -.70))

    @Test fun shoulderNamesFollowThePlayerThroughAMirroredOpeningAndAStageTurn() {
        val quarterTurn = Quaternion(0.0, sqrt(.5), 0.0, sqrt(.5))
        val shift = Vector3(2.0, -.30, 1.10)
        for ((bladeX, expected) in listOf(-.22 to CounterTargetHint.RIGHT_SHOULDER, .22 to CounterTargetHint.LEFT_SHOULDER)) {
            val actor = verticalBlade(bladeX)
            assertEquals(expected, lessonCounterTarget(head, facing, actor))
            val turned = actor.inStage(shift, (Math.PI / 2.0).toFloat())
            assertEquals(expected, lessonCounterTarget(shift + requireNotNull(quarterTurn.rotate(head)), quarterTurn, turned))
        }
    }

    @Test fun twoOpenLanesGiveANeutralCueAndCoveredOrUnseenTargetsGiveNone() {
        assertEquals(CounterTargetHint.SHOULDER_LINE, lessonCounterTarget(head, facing,
            pose(Vector3(-.35, .72, -.70), Vector3(.35, .72, -.70))))
        assertNull(lessonCounterTarget(head, facing, pose(Vector3(-.35, 1.525, -.70), Vector3(.35, 1.525, -.70))))
        assertNull(lessonCounterTarget(head, Quaternion(0.0, 1.0, 0.0, 0.0), verticalBlade(-.22)))
    }

    @Test fun theRecordedOpeningAfterTheActorTurnsDoesNotPointAtTheOppositeSideOfTheBladeTip() {
        val overhead = arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD)
        val heldPose = overhead.sample(.8966735)
        val root = Vector3(0.0, .028, -1.55)
        val recordedHead = Vector3(0.0, 1.695, 0.0)
        assertEquals(CounterTargetHint.RIGHT_SHOULDER,
            lessonCounterTarget(recordedHead, facing, heldPose.inStage(root, 0f)))
        assertEquals(CounterTargetHint.SHOULDER_LINE,
            lessonCounterTarget(recordedHead, facing, heldPose.inStage(root, .7219399f)))
    }
}
