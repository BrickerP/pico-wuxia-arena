package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.cos
import kotlin.math.sin

/** Body contacts and the actual blade endpoints sampled from the same actor-local pose. */
internal data class AttackPoseSample(
    val sourceSeconds: Double,
    val contact: EnemyContactPose,
    val bladeBase: Vector3,
    val bladeTip: Vector3,
) {
    init {
        require(sourceSeconds.isFinite() && sourceSeconds >= 0.0) { "Sample time must be finite and non-negative" }
        require(contact.isFinite() && bladeBase.isFinite() && bladeTip.isFinite()) { "Sample points must be finite" }
    }

    fun nearestBladePoint(point: Vector3): Vector3 {
        require(point.isFinite()) { "Blade contact target must be finite" }
        val blade = bladeTip - bladeBase
        val lengthSquared = blade.dot(blade)
        if (lengthSquared == 0.0) return bladeBase
        val fraction = ((point - bladeBase).dot(blade) / lengthSquared).coerceIn(0.0, 1.0)
        return bladeBase + blade * fraction
    }

    fun inStage(origin: Vector3, yaw: Float): AttackPoseSample {
        require(origin.isFinite() && yaw.isFinite()) { "Attack pose requires a finite Stage transform" }
        val cosine = cos(yaw.toDouble())
        val sine = sin(yaw.toDouble())
        fun point(local: Vector3) = origin + Vector3(
            local.x * cosine + local.z * sine,
            local.y,
            -local.x * sine + local.z * cosine,
        )
        return copy(
            contact = EnemyContactPose(point(contact.head), point(contact.bodyBottom), point(contact.bodyTop)),
            bladeBase = point(bladeBase),
            bladeTip = point(bladeTip),
        )
    }
}

/** A single source of phase timing for both clip playback and contact geometry. */
internal class AttackProfile(
    val clip: String,
    sourcePhaseSeconds: List<Double>,
    val contactSourceSeconds: Double,
    samples: List<AttackPoseSample>,
) {
    val sourcePhaseSeconds: List<Double> = sourcePhaseSeconds.toList()
    val samples: List<AttackPoseSample> = samples.toList()

    init {
        require(clip.isNotBlank()) { "Attack clip must have a name" }
        require(this.sourcePhaseSeconds.size == 5 && this.sourcePhaseSeconds.all { it.isFinite() && it >= 0.0 }) {
            "Attack phases require five finite non-negative source times"
        }
        require(this.sourcePhaseSeconds.zipWithNext().all { (before, after) -> before < after }) {
            "Attack phase times must be strictly increasing"
        }
        require(contactSourceSeconds.isFinite() &&
            contactSourceSeconds > this.sourcePhaseSeconds[2] && contactSourceSeconds < this.sourcePhaseSeconds[3]) {
            "Contact time must be strictly inside ACTIVE"
        }
        require(this.samples.size >= 2 && this.samples.zipWithNext().all { (before, after) ->
            before.sourceSeconds < after.sourceSeconds
        }) { "Attack samples require at least two strictly increasing times" }
        require(this.samples.first().sourceSeconds <= this.sourcePhaseSeconds.first() &&
            this.samples.last().sourceSeconds >= this.sourcePhaseSeconds.last()) {
            "Attack samples must cover every source phase"
        }
    }

    fun sourceSeconds(
        phase: EnemyPhase,
        elapsedNanos: Long,
        remainingNanos: Long?,
        recoveryFromContact: Boolean = false,
    ): Double {
        require(elapsedNanos >= 0L && (remainingNanos == null || remainingNanos >= 0L)) {
            "Attack phase time must be non-negative"
        }
        val index = when (phase) {
            EnemyPhase.PREPARING -> 0
            EnemyPhase.STARTUP -> 1
            EnemyPhase.ACTIVE -> 2
            EnemyPhase.RECOVERING -> 3
            else -> return sourcePhaseSeconds.first()
        }
        // Convert before adding, so valid Long clocks cannot overflow the phase duration.
        val total = elapsedNanos.toDouble() + (remainingNanos ?: 0L).toDouble()
        val progress = if (total > 0.0) elapsedNanos.toDouble() / total else 0.0
        // A successful contact resolves ACTIVE immediately; continue from that source key.
        val start = if (phase == EnemyPhase.RECOVERING && recoveryFromContact) contactSourceSeconds
            else sourcePhaseSeconds[index]
        val end = sourcePhaseSeconds[index + 1]
        return if (phase == EnemyPhase.ACTIVE) {
            if (progress <= 0.5) {
                interpolate(start, contactSourceSeconds, progress * 2.0)
            } else {
                interpolate(contactSourceSeconds, end, (progress - 0.5) * 2.0)
            }
        } else {
            interpolate(start, end, progress)
        }
    }

    fun sample(sourceSeconds: Double): AttackPoseSample {
        require(sourceSeconds.isFinite()) { "Requested attack sample time must be finite" }
        if (sourceSeconds <= samples.first().sourceSeconds) return samples.first()
        if (sourceSeconds >= samples.last().sourceSeconds) return samples.last()
        val index = samples.binarySearchBy(sourceSeconds) { it.sourceSeconds }
        if (index >= 0) return samples[index]
        val after = samples[-index - 1]
        val before = samples[-index - 2]
        val progress = (sourceSeconds - before.sourceSeconds) / (after.sourceSeconds - before.sourceSeconds)
        fun point(start: Vector3, end: Vector3) = start * (1.0 - progress) + end * progress
        return AttackPoseSample(
            sourceSeconds,
            EnemyContactPose(
                point(before.contact.head, after.contact.head),
                point(before.contact.bodyBottom, after.contact.bodyBottom),
                point(before.contact.bodyTop, after.contact.bodyTop),
            ),
            point(before.bladeBase, after.bladeBase),
            point(before.bladeTip, after.bladeTip),
        )
    }

    private fun interpolate(start: Double, end: Double, progress: Double): Double = when (progress) {
        0.0 -> start
        1.0 -> end
        else -> start + (end - start) * progress
    }
}

internal data class CharacterAttackProfiles(
    val modelSha256: String,
    val profileSha256: String,
    val attacks: Map<AttackDirection, AttackProfile>,
)

internal object AttackBankProfiles {
    fun forAsset(asset: String, direction: AttackDirection): AttackProfile =
        AttackBankProfileData.characters.getValue(asset).attacks.getValue(direction)
}
