package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NativeImpactLightTest {
    @Test fun ordinaryBodyAndUnknownSoftSurfaceDoNotAddASecondWhiteLayer() {
        assertNull(nativeImpactLight(hit()))
        assertNull(nativeImpactLight(hit().copy(zone = null)))
        assertEquals(0L, remainingNativeImpactLightNanos(hit(), 0L))
    }

    @Test fun parryWithNoEnemyDamageStillHasALocalMetalPulse() {
        val light = nativeImpactLight(hit().copy(kind = CombatImpactKind.PARRY, appliedDamage = 0, strength = 1.0))!!
        assertEquals(120f, light.intensity, 0f)
        assertEquals(0.35f, light.attenuationRadius, 0f)
        assertEquals(70_000_000L, light.durationNanos)
    }

    @Test fun fatalBodyKeepsMoreAccentWithoutAFullActorMaterialOverride() {
        val light = nativeImpactLight(hit().copy(fatal = true, strength = 0.1))!!
        assertEquals(160f, light.intensity, 0f)
        assertEquals(0.45f, light.attenuationRadius, 0f)
        assertEquals(90_000_000L, light.durationNanos)
    }

    @Test fun headAccentIsSmallerThanParryAndNeverAnActorMaterial() {
        val light = nativeImpactLight(hit().copy(zone = HitZone.HEAD))!!
        assertEquals(35f, light.intensity, 0f)
        assertEquals(0.18f, light.attenuationRadius, 0f)
        assertEquals(45_000_000L, light.durationNanos)
    }

    @Test fun nearHeadPlayerDamageDoesNotAddAnUnrequestedLight() {
        assertNull(nativeImpactLight(hit().copy(kind = CombatImpactKind.PLAYER_HIT)))
    }

    @Test fun ageBoundaryAndFutureDeliveryNeverRestartThePulse() {
        val parry = hit().copy(kind = CombatImpactKind.PARRY, appliedDamage = 0, strength = 1.0)
        assertEquals(70_000_000L, remainingNativeImpactLightNanos(parry, 0L))
        assertEquals(1L, remainingNativeImpactLightNanos(parry, 69_999_999L))
        assertEquals(0L, remainingNativeImpactLightNanos(parry, 70_000_000L))
        assertEquals(0L, remainingNativeImpactLightNanos(parry, 120_000_000L))
        assertEquals(0L, remainingNativeImpactLightNanos(parry.copy(atNanos = 1L), 0L))
        assertEquals(0L, remainingNativeImpactLightNanos(parry.copy(atNanos = -1L), 0L))
        assertEquals(0L, remainingNativeImpactLightNanos(parry, -1L))
    }

    @Test fun strengthAndEveryResolvedMaterialRemainBounded() {
        for (kind in CombatImpactKind.entries) for (strength in listOf(-1.0, 0.0, 0.5, 1.0, 100.0)) {
            val light = nativeImpactLight(hit().copy(kind = kind, strength = strength)) ?: continue
            assertTrue(light.intensity in 0f..160f)
            assertTrue(light.attenuationRadius in 0.18f..0.45f)
            assertTrue(light.durationNanos in 1L..90_000_000L)
        }
        for (strength in listOf(Double.NaN, Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY)) {
            assertNull(nativeImpactLight(hit().copy(kind = CombatImpactKind.PARRY, strength = strength)))
        }
    }

    private fun hit() = CombatImpact(1L, CombatImpactKind.SOFT_HIT,
        Vector3(0.0, 1.0, -1.0), Vector3(0.0, 0.0, 1.0),
        0.625, Hand.RIGHT, 0L, appliedDamage = 25, zone = HitZone.BODY)
}
