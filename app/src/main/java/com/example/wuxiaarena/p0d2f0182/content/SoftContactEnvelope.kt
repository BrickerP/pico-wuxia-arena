package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.pow
import kotlin.math.sin

internal data class SoftLayerEnvelope(val scale: Vector3, val rotation: Quaternion, val opacity: Float)
internal data class SoftDebrisEnvelope(
    val scale: Vector3, val velocityGain: Double, val lifetime: Double, val opacity: Float,
)

/** Presentation of the existing dry SOFT meshes; no new geometry, surface type or combat clock. */
internal object SoftContactEnvelope {
    private val identity = Quaternion(0.0, 0.0, 0.0, 1.0)
    private const val CORE_SECONDS = 0.038
    private const val SCAR_SECONDS = 0.060
    // The published scar's measured long axis is 34.384 degrees in its local XY plane.
    private const val SCAR_SOURCE_RADIANS = 0.600114010016557

    fun layer(node: String, age: Double, size: Float, hasTangent: Boolean): SoftLayerEnvelope {
        val gain = size.toDouble()
        if (node == "scar") {
            val x = 0.65
            val y = 0.08
            // Correct the source mesh's intrinsic slope AFTER anisotropic scale. Anchor X is actual T.
            val roll = -atan2(y * sin(SCAR_SOURCE_RADIANS), x * cos(SCAR_SOURCE_RADIANS))
            return SoftLayerEnvelope(Vector3(x * gain, y * gain, gain),
                Quaternion(0.0, 0.0, sin(roll / 2.0), cos(roll / 2.0)),
                if (hasTangent) fade(age, SCAR_SECONDS, 0.70, 1.2) else 0f)
        }
        if (!hasTangent) {
            // Without T/B a small symmetric contact remains; never orient a guessed cutting line.
            return SoftLayerEnvelope(Vector3(0.17 * gain, 0.17 * gain, 0.17 * gain), identity,
                fade(age, 0.032, 0.50, 1.0))
        }
        return SoftLayerEnvelope(Vector3(0.70 * gain, 0.045 * gain, gain), identity,
            fade(age, CORE_SECONDS, 0.72, 0.8))
    }

    fun debris(index: Int, age: Double, size: Float, sourceLifetime: Double): SoftDebrisEnvelope {
        val tier = Math.floorMod(index, 3)
        val x = when (tier) { 0 -> 0.18; 1 -> 0.32; else -> 0.50 }
        val y = when (tier) { 0 -> 0.065; 1 -> 0.11; else -> 0.16 }
        val speed = when (tier) { 0 -> 1.55; 1 -> 1.05; else -> 0.65 }
        val lifetime = minOf(sourceLifetime, when (tier) { 0 -> 0.135; 1 -> 0.190; else -> 0.250 })
        // Eight unequal fragments read as dry flakes; four overlapping puff nodes stay disabled.
        val peak = if (index == 3 || index == 7 || index == 8 || index == 9) 0.0
            else when (tier) { 0 -> 0.60; 1 -> 0.45; else -> 0.32 }
        val delay = when (tier) { 0 -> 0.004; 1 -> 0.012; else -> 0.020 } + (index.coerceAtLeast(0) / 3) * 0.002
        val gain = size.toDouble()
        val opacity = if (!age.isFinite() || age < delay || age >= lifetime || lifetime <= 0.0) 0f else {
            val enter = ((age - delay) / 0.012).coerceIn(0.0, 1.0)
            val smoothEnter = enter * enter * (3.0 - 2.0 * enter)
            (peak * smoothEnter * (1.0 - (age / lifetime).pow(1.5))).coerceIn(0.0, 1.0).toFloat()
        }
        return SoftDebrisEnvelope(Vector3(x * gain, y * gain, gain), speed, lifetime, opacity)
    }

    fun duration(particles: List<ContactParticleDefinition>): Double =
        maxOf(SCAR_SECONDS, particles.mapIndexed { index, p -> debris(index, 0.0, 1f, p.lifetime).lifetime }.maxOrNull() ?: 0.0)

    private fun fade(age: Double, lifetime: Double, peak: Double, exponent: Double): Float =
        if (!age.isFinite() || age < 0.0 || age >= lifetime) 0f
        else (peak * (1.0 - age / lifetime).pow(exponent)).toFloat()
}
