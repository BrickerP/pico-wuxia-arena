package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotSame
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Test

class TerminalControlPlacementTest {
    private val head = Vector3(0.0, 1.6, 0.0)
    private val facing = Quaternion(0.0, 0.0, 0.0, 1.0)
    private val facingRight = Quaternion(0.0, -1.0, 0.0, 1.0)

    @Test
    fun terminalPanelUsesTheRealFullHeightAndStaysEightCentimetersBelowTheHead() {
        val placement = TerminalControlPlacement()
        val pose = requireNotNull(placement.update(0, true, true, head, facing, 0.56))
        assertEquals(0.0, pose.position.x, 1e-12)
        assertEquals(-0.85, pose.position.z, 1e-12)
        assertEquals(head.y - 0.08, pose.position.y + pose.fullHeightMeters / 2, 1e-12)
        assertEquals(head, pose.capturedHead)
    }

    @Test
    fun turningRightBeforeTheResultCentersThePanelInThePlayersNewView() {
        val pose = requireNotNull(TerminalControlPlacement().update(
            2, true, true, head, facingRight, 0.4,
        ))
        assertEquals(0.85, pose.position.x, 1e-12)
        assertEquals(0.0, pose.position.z, 1e-12)
        assertEquals(head.y - 0.28, pose.position.y, 1e-12)
    }

    @Test
    fun validSameGenerationMovementDoesNotMoveTheCapturedWorldAnchor() {
        val placement = TerminalControlPlacement()
        val first = placement.update(3, true, true, head, facing, 0.5)
        assertSame(first, placement.update(3, true, true,
            Vector3(0.3, 1.7, 0.2), facingRight, 0.5))
    }

    @Test
    fun olderGenerationCannotClearOrReplaceTheCurrentTerminalAnchor() {
        val placement = TerminalControlPlacement()
        val first = placement.update(4, true, true, head, facing, 0.5)
        assertSame(first, placement.update(3, false, false, null, null, 0.0))
        assertSame(first, placement.update(2, true, true, Vector3(10.0, 1.0, 2.0), facing, 0.5))
    }

    @Test
    fun nonTerminalAndNewGenerationClearTheTerminalOverrideUntilTheNextValidTerminalState() {
        val placement = TerminalControlPlacement()
        val first = placement.update(4, true, true, head, facing, 0.5)
        assertNull(placement.update(5, false, true, head, facing, 0.5))
        assertNull(placement.pose)
        assertNull(placement.update(5, false, true, head, facing, 0.5))
        val next = placement.update(5, true, true, Vector3(0.2, 1.6, 0.0), facing, 0.5)
        assertNotSame(first, next)
        assertEquals(5L, next?.generation)
    }

    @Test
    fun losingValidInputDropsTheCaptureAndRestorationCapturesCurrentHeadAgain() {
        val placement = TerminalControlPlacement()
        val first = placement.update(6, true, true, head, facing, 0.5)
        assertNull(placement.update(6, true, false, head, facing, 0.5))
        val restoredHead = Vector3(0.3, 1.5, 0.2)
        val restored = placement.update(6, true, true, restoredHead, facing, 0.5)
        assertNotSame(first, restored)
        assertEquals(restoredHead, restored?.capturedHead)
    }

    @Test
    fun invalidOrDegenerateReferencesAndInvalidPhysicalHeightsDoNotCreateAnAnchor() {
        for ((h, e, height) in listOf(
            Triple(null, facing, 0.5), Triple(head, null, 0.5),
            Triple(Vector3(Double.NaN, 1.6, 0.0), facing, 0.5),
            Triple(head, Quaternion(0.0, Double.POSITIVE_INFINITY, 0.0, 1.0), 0.5),
            Triple(head, Quaternion(0.0, 0.0, 0.0, 0.0), 0.5),
            Triple(head, facing, 0.0), Triple(head, facing, -1.0),
            Triple(head, facing, Double.NaN), Triple(head, facing, Double.POSITIVE_INFINITY),
        )) assertNull(TerminalControlPlacement().update(0, true, true, h, e, height))
    }

    @Test
    fun invalidSameGenerationReferenceClearsAnExistingCapture() {
        val placement = TerminalControlPlacement()
        placement.update(7, true, true, head, facing, 0.5)
        assertNull(placement.update(7, true, true, head, Quaternion(0.0, 0.0, 0.0, 0.0), 0.5))
        assertNull(placement.pose)
    }

    @Test
    fun lookingStraightUpUsesHeadYawWithoutAStandingOpponent() {
        val pose = requireNotNull(TerminalControlPlacement().update(
            8, true, true, head, Quaternion(1.0, 0.0, 0.0, 1.0), 0.5,
        ))
        assertEquals(0.0, pose.position.x, 1e-12)
        assertEquals(-0.85, pose.position.z, 1e-12)
    }

    @Test
    fun releaseAllowsAFreshSceneToStartAtItsOwnGeneration() {
        val placement = TerminalControlPlacement()
        placement.update(9, true, true, head, facing, 0.5)
        placement.clear()
        assertNull(placement.pose)
        val next = placement.update(0, true, true, head, facing, 0.5)
        assertEquals(0L, next?.generation)
    }
}
