package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CombatEffectsTimingTest {
    @Test
    fun fatalThenParryReceiveTheAvailableVisualSlotsBeforeOrdinaryContacts() {
        val normal = impact(5)
        val parry = impact(2).copy(kind = CombatImpactKind.PARRY)
        val fatal = impact(1).copy(appliedDamage = 8, fatal = true)

        assertEquals(listOf(fatal, parry, normal), currentContactImpacts(listOf(normal, parry, fatal), 1_000_000_000L))
    }

    @Test
    fun expiredAndFutureContactsAreNotReplayed() {
        val boundary = impact(1).copy(atNanos = 880_000_000L)
        val expired = impact(2).copy(atNanos = 879_999_999L)
        val future = impact(3).copy(atNanos = 1_000_000_001L)

        assertEquals(listOf(boundary), currentContactImpacts(listOf(expired, boundary, future), 1_000_000_000L))
    }

    @Test
    fun invalidPositionsNormalsAndStrengthAreRejected() {
        val point = impact(1).copy(point = Vector3(Double.NaN, 0.0, 0.0))
        val normal = impact(2).copy(normal = Vector3(0.0, 0.0, 0.0))
        val strength = impact(3).copy(strength = Double.POSITIVE_INFINITY)

        assertTrue(currentContactImpacts(listOf(point, normal, strength), 1_000_000_000L).isEmpty())
    }

    private fun impact(id: Long) = CombatImpact(
        id, CombatImpactKind.SOFT_HIT, Vector3(0.0, 1.0, -1.0),
        Vector3(0.0, 0.0, 1.0), 0.5, Hand.RIGHT, 1_000_000_000L,
    )
}
