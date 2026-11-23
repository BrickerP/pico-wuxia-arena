package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.cos
import kotlin.math.sin
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ActorWithdrawalPlanTest {
    private val origin = Vector3(-.20, 0.0, 0.0)
    private val up = Vector3(0.0, 1.0, 0.0)
    private val player = BladeSegment(Vector3(0.0, .02, -.50), Vector3(0.0, .02, .80), .01)
    private fun transverseBlade(z: Double) =
        BladeSegment(Vector3(.20, 0.0, z), Vector3(.30, 0.0, z), .01)

    @Test fun yawCanClearTheBaseWhenRetreatAloneLeavesTheRecoveryInside() {
        val held = transverseBlade(-.50)
        val recovering = transverseBlade(-.46)
        val plan = requireNotNull(ActorWithdrawalPlan.create(origin, 0.0, held, listOf(player), up, listOf(held, recovering)))
        assertEquals("PLAYER_BASE", plan.exitSide)
        val finalPose = plan.at(plan.durationSeconds)
        assertEquals(-.0495, finalPose.position.z, 1e-10)
        assertTrue("A positive turn is necessary to carry the recovered blade behind the base", finalPose.yawRadians in .20.. .35)
        for (endpoint in listOf(held.base, held.tip, recovering.base, recovering.tip)) {
            val worldZ = finalPose.position.z - endpoint.x * sin(finalPose.yawRadians) + endpoint.z * cos(finalPose.yawRadians)
            assertTrue("The complete recovery hull must clear the base by 25 mm",
                player.base.z - worldZ - player.radiusMeters - held.radiusMeters >= .025 - 1e-9)
        }
    }

    @Test fun noPlanWhenTheRecoveryCanClearNeitherTheNormalPlaneNorAnEndpoint() {
        val held = transverseBlade(-.50)
        // The inner endpoint's rotation radius is hypot(.20, .41) < .457 m.
        // Even with 49.5 mm retreat it cannot reach the required base plane z = -.545.
        assertNull(ActorWithdrawalPlan.create(origin, 0.0, held, listOf(player), up,
            listOf(held, transverseBlade(-.41))))
    }

    @Test fun unrestrictedYawKeepsTheStraightRetreatWhenItAlreadyClearsTheNormalPlane() {
        val enemy = BladeSegment(Vector3(0.0, -.10, 0.0), Vector3(0.0, .10, 0.0), .01)
        val guard = BladeSegment(Vector3(-.5, 0.0, .02), Vector3(.5, 0.0, .02), .01)
        val plan = requireNotNull(ActorWithdrawalPlan.create(Vector3(0.0,0.0,0.0), 0.0, enemy,
            listOf(guard), Vector3(0.0,0.0,1.0), listOf(enemy)))
        val end = plan.at(plan.durationSeconds)
        assertEquals(.0495, plan.retreatMeters, 1e-10)
        assertEquals("No material yaw is needed", 0.0, end.yawRadians, 1.1e-7)
        assertEquals(.0495, guard.base.z - end.position.z - guard.radiusMeters - enemy.radiusMeters, 1e-9)
    }
}
