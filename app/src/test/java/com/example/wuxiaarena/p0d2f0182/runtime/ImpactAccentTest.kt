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
    fun headAndFatalResultsChangeAudioHapticsLightAndVisualScale() {
        val ordinary = CombatFeedbackProfile.accent(impact())
        val head = CombatFeedbackProfile.accent(impact().copy(zone = HitZone.HEAD))
        val fatal = CombatFeedbackProfile.accent(impact().copy(zone = HitZone.HEAD, fatal = true))

        assertTrue(head.soundRate > ordinary.soundRate)
        assertTrue(head.hapticLevel > ordinary.hapticLevel)
        assertTrue(head.hapticDurationMillis > ordinary.hapticDurationMillis)
        assertTrue(head.lightDurationNanos > ordinary.lightDurationNanos)
        assertTrue(head.visualScale > ordinary.visualScale)
        assertTrue(fatal.soundRate < ordinary.soundRate)
        assertTrue(fatal.hapticLevel > head.hapticLevel)
        assertTrue(fatal.hapticDurationMillis > head.hapticDurationMillis)
        assertTrue(fatal.lightDurationNanos > head.lightDurationNanos)
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

    private fun impact() = CombatImpact(
        1L, CombatImpactKind.SOFT_HIT, Vector3(0.0, 1.0, -1.0),
        Vector3(0.0, 0.0, 1.0), 0.5, Hand.RIGHT, 0L, appliedDamage = 25,
    )
}
