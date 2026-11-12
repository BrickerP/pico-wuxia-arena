package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.sqrt

/** Right handed contact coordinates. Gravity always remains in Stage -Y. */
internal data class ContactBasis(val tangent: Vector3, val binormal: Vector3, val normal: Vector3) {
    fun toStage(local: Vector3) = tangent * local.x + binormal * local.y + normal * local.z
    fun toLocal(stage: Vector3) = Vector3(stage.dot(tangent), stage.dot(binormal), stage.dot(normal))
    fun rotation() = rotationFromAxes(tangent, binormal, normal)

    companion object {
        fun from(normal: Vector3, tangent: Vector3?): ContactBasis? {
            val n = normal.normalizedOrNull() ?: return null
            val incoming = tangent?.normalizedOrNull() ?: return null
            val projected = incoming - n * incoming.dot(n)
            if (projected.length() < 1e-6) return null
            val t = projected.normalizedOrNull() ?: return null
            return ContactBasis(t, n.cross(t), n)
        }
    }
}

internal data class OpacityKey(val seconds: Double, val opacity: Float)

internal data class ContactParticleDefinition(
    val node: String,
    val initialPosition: Vector3,
    val initialVelocity: Vector3,
    val lifetime: Double,
    val opacityKeys: List<OpacityKey>,
    val followsVelocity: Boolean = true,
    val grounded: Boolean = false,
)

internal data class ContactParticleSample(val position: Vector3, val rotation: Quaternion, val opacity: Float)

internal fun sampleContactParticle(
    particle: ContactParticleDefinition, age: Double, basis: ContactBasis, velocityGain: Double = 1.0,
): ContactParticleSample? {
    if (!age.isFinite() || age < 0.0 || age >= particle.lifetime || !velocityGain.isFinite()) return null
    val gravity = basis.toLocal(Vector3(0.0, -9.81, 0.0))
    val velocity = particle.initialVelocity * velocityGain
    val displacement = particle.initialPosition + velocity * age + gravity * (0.5 * age * age)
    val position = if (particle.grounded && displacement.z < 0.0) displacement.copy(z = 0.0) else displacement
    val rotation = if (particle.followsVelocity) rotationAlongX(velocity + gravity * age) else IDENTITY_ROTATION
    return ContactParticleSample(position, rotation, opacityAt(particle.opacityKeys, age))
}

internal fun opacityAt(keys: List<OpacityKey>, age: Double): Float {
    if (keys.isEmpty() || !age.isFinite()) return 0f
    if (age <= keys.first().seconds) return keys.first().opacity.coerceIn(0f, 1f)
    for (index in 1 until keys.size) {
        val left = keys[index - 1]
        val right = keys[index]
        if (age <= right.seconds) {
            val amount = ((age - left.seconds) / (right.seconds - left.seconds)).toFloat()
            return (left.opacity + amount * (right.opacity - left.opacity)).coerceIn(0f, 1f)
        }
    }
    return keys.last().opacity.coerceIn(0f, 1f)
}

/** Missing cutting tangent permits a symmetric core only, never a guessed blade scar or spray. */
internal fun normalFacingRotation(normal: Vector3): Quaternion? {
    val n = normal.normalizedOrNull() ?: return null
    return Quaternion(-n.y, n.x, 0.0, 1.0 + n.z).normalizedOrNull()
        ?: Quaternion(0.0, 1.0, 0.0, 0.0)
}

private val IDENTITY_ROTATION = Quaternion(0.0, 0.0, 0.0, 1.0)

private fun rotationAlongX(velocity: Vector3): Quaternion {
    val x = velocity.normalizedOrNull() ?: return IDENTITY_ROTATION
    val reference = if (kotlin.math.abs(x.z) < 0.95) Vector3(0.0, 0.0, 1.0) else Vector3(0.0, 1.0, 0.0)
    val y = checkNotNull(reference.cross(x).normalizedOrNull())
    return rotationFromAxes(x, y, x.cross(y))
}

private fun rotationFromAxes(x: Vector3, y: Vector3, z: Vector3): Quaternion {
    val trace = x.x + y.y + z.z
    val q = when {
        trace > 0.0 -> {
            val s = sqrt(trace + 1.0) * 2.0
            Quaternion((y.z - z.y) / s, (z.x - x.z) / s, (x.y - y.x) / s, s / 4.0)
        }
        x.x > y.y && x.x > z.z -> {
            val s = sqrt(1.0 + x.x - y.y - z.z) * 2.0
            Quaternion(s / 4.0, (y.x + x.y) / s, (z.x + x.z) / s, (y.z - z.y) / s)
        }
        y.y > z.z -> {
            val s = sqrt(1.0 + y.y - x.x - z.z) * 2.0
            Quaternion((y.x + x.y) / s, s / 4.0, (z.y + y.z) / s, (z.x - x.z) / s)
        }
        else -> {
            val s = sqrt(1.0 + z.z - x.x - y.y) * 2.0
            Quaternion((z.x + x.z) / s, (z.y + y.z) / s, s / 4.0, (x.y - y.x) / s)
        }
    }
    return checkNotNull(q.normalizedOrNull())
}

internal enum class ContactEffectFamily { SOFT, METAL }

internal data class ContactCoreDefinition(
    val node: String, val position: Vector3, val normal: List<OpacityKey>, val parry: List<OpacityKey>,
    val directional: Boolean = false,
)

internal data class ContactEffectDefinition(
    val family: ContactEffectFamily, val asset: String,
    val particles: List<ContactParticleDefinition>, val cores: List<ContactCoreDefinition>,
)
