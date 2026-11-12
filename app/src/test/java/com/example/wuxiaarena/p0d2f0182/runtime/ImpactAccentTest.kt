package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ImpactAccentTest {
    @Test
    fun headAndFatalResultsChangeAudioHapticsAndVisualScale() {
        val ordinary = CombatFeedbackProfile.accent(impact())
        val head = CombatFeedbackProfile.accent(impact().copy(zone = HitZone.HEAD))
        val fatal = CombatFeedbackProfile.accent(impact().copy(zone = HitZone.HEAD, fatal = true))

        assertTrue(head.soundRate > ordinary.soundRate)
        assertTrue(head.hapticLevel > ordinary.hapticLevel)
        assertTrue(head.hapticDurationMillis > ordinary.hapticDurationMillis)
        assertTrue(head.visualScale > ordinary.visualScale)
        assertTrue(fatal.soundRate < ordinary.soundRate)
        assertTrue(fatal.hapticLevel > head.hapticLevel)
        assertTrue(fatal.hapticDurationMillis > head.hapticDurationMillis)
        assertTrue(fatal.visualScale > head.visualScale)
    }

    @Test
    fun zeroDamageHeadContactsKeepTheMaterialFeedback() {
        val guarded = impact().copy(kind = CombatImpactKind.BLOCK, appliedDamage = 0, zone = HitZone.HEAD)
        val profile = CombatFeedbackProfile.accent(guarded)

        assertEquals(1f, profile.soundRate, 0f)
        assertEquals(1f, profile.visualScale, 0f)
        assertEquals(28, profile.hapticDurationMillis)
    }

    @Test
    fun parryIsSharperAndShorterThanAHeavyBlock() {
        val block = CombatFeedbackProfile.accent(impact().copy(kind = CombatImpactKind.BLOCK, appliedDamage = 0, strength = 1.0))
        val parry = CombatFeedbackProfile.accent(impact().copy(kind = CombatImpactKind.PARRY, appliedDamage = 0, strength = 1.0))
        assertTrue(parry.hapticLevel > block.hapticLevel)
        assertTrue(parry.hapticFrequency > block.hapticFrequency)
        assertTrue(parry.hapticDurationMillis < block.hapticDurationMillis)
    }

    @Test
    fun fatalAccentHasMoreWeightThanARegularParryWithoutChangingCombatTime() {
        val parry = CombatFeedbackProfile.accent(impact().copy(kind = CombatImpactKind.PARRY, strength = 1.0))
        val lethal = impact().copy(appliedDamage = 1, fatal = true)
        val fatal = CombatFeedbackProfile.accent(lethal)
        assertTrue(fatal.hapticLevel >= parry.hapticLevel)
        assertTrue(fatal.hapticDurationMillis > parry.hapticDurationMillis)
        assertTrue(fatal.hapticFrequency < parry.hapticFrequency)
        assertEquals(150_000_000L, CombatFeedbackProfile.hitStopNanos(lethal))
        assertEquals(77_000_000L, CombatFeedbackProfile.deathElapsedNanos(220_000_000L))
    }

    @Test
    fun everyMaterialKeepsFiniteOutputAndBoundedHapticParametersAtInvalidStrength() {
        for (kind in CombatImpactKind.entries) {
            for (strength in listOf(Double.NaN, Double.POSITIVE_INFINITY, -1.0, 0.0, 1.0, 2.0)) {
                val accent = CombatFeedbackProfile.accent(impact().copy(kind = kind, appliedDamage = 0, strength = strength))
                assertTrue(accent.soundRate.isFinite() && accent.soundRate in 0.5f..2f)
                assertTrue(accent.hapticLevel in 0..255)
                assertTrue(accent.hapticFrequency in 1..320)
                assertTrue(accent.hapticDurationMillis in 1..100)
                assertTrue(accent.strength.isFinite() && accent.strength in 0.0..1.0)
            }
        }
    }

    private fun impact() = CombatImpact(
        1L, CombatImpactKind.SOFT_HIT, Vector3(0.0, 1.0, -1.0),
        Vector3(0.0, 0.0, 1.0), 0.5, Hand.RIGHT, 0L, appliedDamage = 25,
    )
}
