package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.*
import org.junit.Test

class ContactParticleMotionTest {
    private val z = Vector3(0.0, 0.0, 1.0)
    private val x = Vector3(1.0, 0.0, 0.0)
    private val particle = ContactParticleDefinition("spark", Vector3(0.0, 0.0, 0.002),
        Vector3(1.0, 0.5, 0.2), 0.3, listOf(OpacityKey(0.0, 1f), OpacityKey(0.3, 0f)))

    @Test fun gravityRemainsDownWhenContactNormalRotates() {
        for (basis in listOf(ContactBasis.from(z, x)!!, ContactBasis.from(x, Vector3(0.0, 1.0, 0.0))!!)) {
            val sample = sampleContactParticle(particle, 0.1, basis)!!
            val actual = basis.toStage(sample.position)
            val expected = basis.toStage(particle.initialPosition + particle.initialVelocity * 0.1) + Vector3(0.0, -0.04905, 0.0)
            assertVector(expected, actual)
            assertVector(basis.tangent, basis.rotation().rotate(x)!!)
            assertVector(basis.normal, basis.rotation().rotate(z)!!)
        }
    }

    @Test fun missingInvalidAndParallelTangentsDoNotCreateDirection() {
        assertNull(ContactBasis.from(z, null))
        assertNull(ContactBasis.from(z, z))
        assertNull(ContactBasis.from(z, Vector3(Double.NaN, 0.0, 0.0)))
        assertNull(ContactBasis.from(Vector3(0.0, 0.0, 0.0), x))
        assertNotNull(normalFacingRotation(z))
        assertNotNull(normalFacingRotation(z * -1.0))
    }

    @Test fun actualTangentIsProjectedOntoSurface() {
        val basis = ContactBasis.from(z, Vector3(1.0, 2.0, 5.0))!!
        assertEquals(0.0, basis.tangent.dot(z), 1e-10)
        assertVector(z, basis.tangent.cross(basis.binormal))
        assertVector(Vector3(1.0, 2.0, 3.0), basis.toLocal(basis.toStage(Vector3(1.0, 2.0, 3.0))))
    }

    @Test fun negativeExpiredAndNonfiniteAgesNeverRestartParticles() {
        val basis = ContactBasis.from(z, x)!!
        for (age in listOf(-0.001, 0.3, 12.0, Double.NaN, Double.POSITIVE_INFINITY)) {
            assertNull(sampleContactParticle(particle, age, basis))
        }
        assertNotNull(sampleContactParticle(particle, 0.299, basis))
    }

    @Test fun parryVelocityAccentDoesNotScaleGravity() {
        val basis = ContactBasis.from(z, x)!!
        val normal = sampleContactParticle(particle, 0.1, basis)!!
        val parry = sampleContactParticle(particle, 0.1, basis, 1.8)!!
        assertVector(particle.initialVelocity * 0.08, parry.position - normal.position)
        val direction = (particle.initialVelocity * 1.8 + Vector3(0.0, -0.981, 0.0)).normalizedOrNull()!!
        assertVector(direction, parry.rotation.rotate(x)!!)
    }

    @Test fun groundBaseNeverFallsBelowActualInclinedPlane() {
        for (n in listOf(z, Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, 1.0))) {
            val basis = ContactBasis.from(n, x)!!
            val sample = sampleContactParticle(particle.copy(grounded = true, followsVelocity = false), 0.29, basis)!!
            assertTrue(sample.position.z >= 0.0)
        }
    }

    @Test fun allReviewedPresetsHaveIndependentNodesAndBoundedLifetimes() {
        assertEquals(5, CONTACT_EFFECT_DEFINITIONS.size)
        for (effect in CONTACT_EFFECT_DEFINITIONS) {
            val names = effect.particles.map { it.node } + effect.cores.map { it.node }
            assertEquals(names.size, names.toSet().size)
            assertTrue(effect.particles.size in 1..12)
            assertTrue(effect.particles.map { it.initialVelocity }.distinct().size > 1)
            for (p in effect.particles) {
                assertTrue(p.lifetime in 0.18..0.42)
                assertNull(sampleContactParticle(p, p.lifetime, ContactBasis.from(z, x)!!))
            }
        }
    }

    @Test fun parryCoreOutlivesOrdinaryCoreWithoutLastingIntoRecovery() {
        val core = CONTACT_EFFECT_DEFINITIONS.single { it.family == ContactEffectFamily.METAL }.cores.single()
        assertEquals(0f, opacityAt(core.normal, 0.067), 0f)
        assertTrue(opacityAt(core.parry, 0.067) > 0f)
        assertEquals(0f, opacityAt(core.parry, 0.091), 0f)
    }

    private fun assertVector(expected: Vector3, actual: Vector3) {
        assertEquals(expected.x, actual.x, 1e-9)
        assertEquals(expected.y, actual.y, 1e-9)
        assertEquals(expected.z, actual.z, 1e-9)
    }
}
