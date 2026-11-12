package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.cos
import kotlin.math.sin

class SoftContactEnvelopeTest {
    private val soft = CONTACT_EFFECT_DEFINITIONS.single { it.family == ContactEffectFamily.SOFT }

    @Test fun contactIsThinAlongTheMeasuredCutAndLeavesBeforeTheNextBeat() {
        val core = SoftContactEnvelope.layer("core", 0.0, 1f, true)
        assertTrue(core.scale.y / core.scale.x < 0.10)
        assertTrue(core.opacity > 0.5f)
        assertEquals(0f, SoftContactEnvelope.layer("core", 0.040, 1f, true).opacity, 0f)
        assertEquals(0f, SoftContactEnvelope.layer("scar", 0.061, 1f, true).opacity, 0f)
    }

    @Test fun intrinsicScarSlopeIsCorrectedAfterItsAnisotropicScale() {
        val state = SoftContactEnvelope.layer("scar", 0.0, 1f, true)
        val sourceAxis = Vector3(cos(0.600114010016557), sin(0.600114010016557), 0.0)
        val scaled = Vector3(sourceAxis.x * state.scale.x, sourceAxis.y * state.scale.y, 0.0)
        val finalAxis = requireNotNull(state.rotation.rotate(scaled)).normalizedOrNull()!!
        assertEquals(1.0, finalAxis.x, 1e-9)
        assertEquals(0.0, finalAxis.y, 1e-9)
    }

    @Test fun missingTangentHasOnlyASmallSymmetricCore() {
        val state = SoftContactEnvelope.layer("core", 0.0, 1f, false)
        assertEquals(state.scale.x, state.scale.y, 0.0)
        assertEquals(state.scale.x, state.scale.z, 0.0)
        assertTrue(state.scale.x < 0.20)
        assertEquals(0f, SoftContactEnvelope.layer("scar", 0.0, 1f, false).opacity, 0f)
        assertEquals(0f, SoftContactEnvelope.layer("core", 0.033, 1f, false).opacity, 0f)
    }

    @Test fun twelveFragmentsDoNotAppearAsOneOpaqueBirthCluster() {
        val first = soft.particles.mapIndexed { index, p -> SoftContactEnvelope.debris(index, 0.0, 1f, p.lifetime) }
        assertTrue(first.all { it.opacity == 0f })
        assertEquals(3, first.map { it.scale }.distinct().size)
        assertEquals(3, first.map { it.velocityGain }.distinct().size)
        val entering = soft.particles.mapIndexed { index, p -> SoftContactEnvelope.debris(index, 0.015, 1f, p.lifetime) }
        assertTrue(entering.any { it.opacity > 0f })
        assertTrue(entering.any { it.opacity == 0f })
        assertEquals(8, soft.particles.mapIndexed { index, p ->
            SoftContactEnvelope.debris(index, 0.050, 1f, p.lifetime)
        }.count { it.opacity > 0f })
        for (millis in 0..300) {
            val sum = soft.particles.mapIndexed { index, p ->
                SoftContactEnvelope.debris(index, millis / 1000.0, 1f, p.lifetime).opacity.toDouble()
            }.sum()
            assertTrue("Excessive overlapping opacity at ${millis}ms: $sum", sum < 3.5)
        }
    }

    @Test fun tiersAreStatelessAndDoNotExtendTheirSourceLifetime() {
        soft.particles.forEachIndexed { index, p ->
            val state = SoftContactEnvelope.debris(index, 0.08, 1f, p.lifetime)
            assertEquals(state, SoftContactEnvelope.debris(index, 0.08, 1f, p.lifetime))
            assertTrue(state.lifetime <= p.lifetime)
            assertTrue(state.scale.y < state.scale.x)
            assertEquals(0f, SoftContactEnvelope.debris(index, state.lifetime, 1f, p.lifetime).opacity, 0f)
        }
        assertTrue(SoftContactEnvelope.duration(soft.particles) <= 0.25)
    }

    @Test fun aLateEventDoesNotRestartContactOrCompletedFragments() {
        assertEquals(0f, SoftContactEnvelope.layer("core", 0.1, 1f, true).opacity, 0f)
        assertEquals(0f, SoftContactEnvelope.layer("scar", 0.1, 1f, true).opacity, 0f)
        for ((index, p) in soft.particles.withIndex()) {
            assertEquals(0f, SoftContactEnvelope.debris(index, 0.3, 1f, p.lifetime).opacity, 0f)
            assertEquals(0f, SoftContactEnvelope.debris(index, Double.NaN, 1f, p.lifetime).opacity, 0f)
        }
    }

    @Test fun velocityAccentNeverScalesStageGravityOrRestartsAtOpacityDelay() {
        val basis = ContactBasis.from(Vector3(0.0, 0.0, 1.0), Vector3(1.0, 0.0, 0.0))!!
        for ((index, p) in soft.particles.withIndex()) {
            val age = 0.08
            val modifier = SoftContactEnvelope.debris(index, age, 1f, p.lifetime)
            val frame = sampleContactParticle(p, age, basis, modifier.velocityGain)!!
            val residual = frame.position - p.initialPosition - p.initialVelocity * (modifier.velocityGain * age)
            assertEquals(0.0, residual.x, 1e-9)
            assertEquals(-9.81 * 0.5 * age * age, residual.y, 1e-9)
            assertEquals(0.0, residual.z, 1e-9)
        }
    }
}
