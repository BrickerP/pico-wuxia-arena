package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.cos
import kotlin.math.sin

internal data class ArenaOpponent(
    val name: String,
    val asset: String,
    val bodyImpact: CombatImpactKind = CombatImpactKind.SOFT_HIT,
)

internal val arenaOpponents = listOf(
    ArenaOpponent("试刀客", "asset://models/opponents/base.glb"),
    ArenaOpponent("青衫护院", "asset://models/opponents/indigo.glb"),
    ArenaOpponent("玄甲守擂", "asset://models/opponents/veteran.glb", CombatImpactKind.HARD_HIT),
)

/**
 * Source-calibrated bone-anchor approximation, not an exact skinned surface.
 * Calibration preserves the legacy proxy centres at each actor's idle@1.0.
 * Source hashes and independent Blender checks are in ArtSource/refinement/motion.
 */
internal fun ArenaOpponent.contactPose(
    phase: EnemyPhase,
    elapsedNanos: Long,
    remainingNanos: Long?,
    origin: Vector3,
    yaw: Float,
): EnemyContactPose {
    require(origin.isFinite() && yaw.isFinite()) { "Contact pose requires a finite Stage transform" }
    require(elapsedNanos >= 0L && (remainingNanos == null || remainingNanos >= 0L)) {
        "Contact phase time must be non-negative"
    }
    val range = when (phase) {
        EnemyPhase.PREPARING -> 1.55 to 1.85
        EnemyPhase.STARTUP -> 1.85 to 2.067
        EnemyPhase.ACTIVE -> 2.067 to 2.167
        EnemyPhase.RECOVERING -> 2.167 to 3.4
        else -> return STANDING_CONTACT_POSE.inStage(origin, yaw)
    }
    val totalNanos = elapsedNanos.toDouble() + (remainingNanos ?: 0L).toDouble()
    val progress = if (totalNanos > 0.0) (elapsedNanos / totalNanos).coerceIn(0.0, 1.0) else 1.0
    val sourceSeconds = range.first + (range.second - range.first) * progress
    val keys = when (asset) {
        "asset://models/opponents/base.glb" -> BASE_CONTACT_KEYS
        "asset://models/opponents/indigo.glb" -> INDIGO_CONTACT_KEYS
        "asset://models/opponents/veteran.glb" -> VETERAN_CONTACT_KEYS
        else -> error("No source-calibrated contact profile for $asset")
    }
    val nextIndex = keys.indexOfFirst { sourceSeconds <= it.sourceSeconds }
    val pose = when {
        nextIndex == 0 -> keys.first().pose
        nextIndex < 0 -> keys.last().pose
        else -> {
            val before = keys[nextIndex - 1]
            val after = keys[nextIndex]
            val fraction = (sourceSeconds - before.sourceSeconds) / (after.sourceSeconds - before.sourceSeconds)
            EnemyContactPose(
                head = before.pose.head + (after.pose.head - before.pose.head) * fraction,
                bodyBottom = before.pose.bodyBottom + (after.pose.bodyBottom - before.pose.bodyBottom) * fraction,
                bodyTop = before.pose.bodyTop + (after.pose.bodyTop - before.pose.bodyTop) * fraction,
            )
        }
    }
    return pose.inStage(origin, yaw)
}

private fun EnemyContactPose.inStage(origin: Vector3, yaw: Float): EnemyContactPose {
    val cosine = cos(yaw.toDouble())
    val sine = sin(yaw.toDouble())
    fun point(local: Vector3) = origin + Vector3(
        local.x * cosine + local.z * sine,
        local.y,
        -local.x * sine + local.z * cosine,
    )
    return EnemyContactPose(point(head), point(bodyBottom), point(bodyTop))
}

private val STANDING_CONTACT_POSE = EnemyContactPose(
    head = Vector3(0.0, 1.62, 0.0),
    bodyBottom = Vector3(0.0, 0.55, 0.0),
    bodyTop = Vector3(0.0, 1.40, 0.0),
)

private data class ContactPoseKey(val sourceSeconds: Double, val pose: EnemyContactPose)

// base source SHA-256 53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641
private val BASE_CONTACT_KEYS = listOf(
    ContactPoseKey(1.55, EnemyContactPose(
        head = Vector3(0.101406, 1.576134, 0.402927),
        bodyBottom = Vector3(-0.119745, 0.552233, 0.089208),
        bodyTop = Vector3(0.044612, 1.325292, 0.352443),
    )),
    ContactPoseKey(1.85, EnemyContactPose(
        head = Vector3(0.018629, 1.557500, 0.429973),
        bodyBottom = Vector3(-0.079141, 0.565062, 0.017890),
        bodyTop = Vector3(-0.013227, 1.318174, 0.322099),
    )),
    ContactPoseKey(2.067, EnemyContactPose(
        head = Vector3(-0.124829, 1.279570, 0.430015),
        bodyBottom = Vector3(-0.016513, 0.567948, -0.269600),
        bodyTop = Vector3(-0.082459, 1.161940, 0.225511),
    )),
    ContactPoseKey(2.117, EnemyContactPose(
        head = Vector3(-0.153947, 1.190712, 0.422753),
        bodyBottom = Vector3(0.005768, 0.571016, -0.340545),
        bodyTop = Vector3(-0.093046, 1.125134, 0.209637),
    )),
    ContactPoseKey(2.167, EnemyContactPose(
        head = Vector3(-0.196727, 1.068120, 0.429588),
        bodyBottom = Vector3(0.054861, 0.580817, -0.407622),
        bodyTop = Vector3(-0.117289, 1.067601, 0.205517),
    )),
    ContactPoseKey(2.6, EnemyContactPose(
        head = Vector3(-0.226023, 1.119148, 0.403605),
        bodyBottom = Vector3(0.046133, 0.583402, -0.401502),
        bodyTop = Vector3(-0.143797, 1.112621, 0.192952),
    )),
    ContactPoseKey(3.4, EnemyContactPose(
        head = Vector3(-0.252663, 1.433920, 0.192765),
        bodyBottom = Vector3(-0.043096, 0.540623, -0.267459),
        bodyTop = Vector3(-0.164794, 1.299919, 0.019700),
    )),
)

// indigo source SHA-256 7c79d70cbe6bea4eae58759e1faab04f57609a6851b532a24c98a54e90d2b1c6
private val INDIGO_CONTACT_KEYS = listOf(
    ContactPoseKey(1.55, EnemyContactPose(
        head = Vector3(0.071524, 1.573468, 0.270420),
        bodyBottom = Vector3(-0.141772, 0.551800, -0.016523),
        bodyTop = Vector3(0.012357, 1.328624, 0.218974),
    )),
    ContactPoseKey(1.85, EnemyContactPose(
        head = Vector3(-0.023470, 1.561543, 0.329467),
        bodyBottom = Vector3(-0.121586, 0.565331, -0.056317),
        bodyTop = Vector3(-0.055627, 1.322771, 0.221353),
    )),
    ContactPoseKey(2.067, EnemyContactPose(
        head = Vector3(-0.188575, 1.299130, 0.481083),
        bodyBottom = Vector3(-0.093419, 0.569176, -0.184786),
        bodyTop = Vector3(-0.147367, 1.184760, 0.277378),
    )),
    ContactPoseKey(2.117, EnemyContactPose(
        head = Vector3(-0.226512, 1.213050, 0.507957),
        bodyBottom = Vector3(-0.081991, 0.572336, -0.219519),
        bodyTop = Vector3(-0.165550, 1.153519, 0.298080),
    )),
    ContactPoseKey(2.167, EnemyContactPose(
        head = Vector3(-0.283471, 1.096044, 0.543212),
        bodyBottom = Vector3(-0.046940, 0.583012, -0.257134),
        bodyTop = Vector3(-0.202344, 1.103385, 0.325918),
    )),
    ContactPoseKey(2.6, EnemyContactPose(
        head = Vector3(-0.292427, 1.140975, 0.518783),
        bodyBottom = Vector3(-0.033372, 0.585641, -0.250428),
        bodyTop = Vector3(-0.208511, 1.143489, 0.313747),
    )),
    ContactPoseKey(3.4, EnemyContactPose(
        head = Vector3(-0.261301, 1.432133, 0.303174),
        bodyBottom = Vector3(-0.064464, 0.540306, -0.125185),
        bodyTop = Vector3(-0.169320, 1.308160, 0.130680),
    )),
)

// veteran source SHA-256 03e02d53470d41f94355b27e765e86579a02879e2ad30d40c1444bc764ec50a7
private val VETERAN_CONTACT_KEYS = listOf(
    ContactPoseKey(1.55, EnemyContactPose(
        head = Vector3(0.080244, 1.573472, 0.296548),
        bodyBottom = Vector3(-0.143057, 0.551756, -0.008331),
        bodyTop = Vector3(0.025350, 1.316451, 0.253999),
    )),
    ContactPoseKey(1.85, EnemyContactPose(
        head = Vector3(-0.022488, 1.548907, 0.363458),
        bodyBottom = Vector3(-0.128149, 0.562850, -0.047197),
        bodyTop = Vector3(-0.058314, 1.310036, 0.256769),
    )),
    ContactPoseKey(2.067, EnemyContactPose(
        head = Vector3(-0.212993, 1.267172, 0.527820),
        bodyBottom = Vector3(-0.106344, 0.562712, -0.167870),
        bodyTop = Vector3(-0.171724, 1.144163, 0.324516),
    )),
    ContactPoseKey(2.117, EnemyContactPose(
        head = Vector3(-0.254288, 1.184360, 0.554788),
        bodyBottom = Vector3(-0.096731, 0.565444, -0.201377),
        bodyTop = Vector3(-0.196136, 1.105594, 0.342947),
    )),
    ContactPoseKey(2.167, EnemyContactPose(
        head = Vector3(-0.311836, 1.068003, 0.591094),
        bodyBottom = Vector3(-0.066035, 0.573736, -0.237867),
        bodyTop = Vector3(-0.237533, 1.046211, 0.366305),
    )),
    ContactPoseKey(2.6, EnemyContactPose(
        head = Vector3(-0.322072, 1.120590, 0.561536),
        bodyBottom = Vector3(-0.054061, 0.576078, -0.232927),
        bodyTop = Vector3(-0.243078, 1.091948, 0.354470),
    )),
    ContactPoseKey(3.4, EnemyContactPose(
        head = Vector3(-0.285305, 1.434739, 0.324442),
        bodyBottom = Vector3(-0.081253, 0.539954, -0.123568),
        bodyTop = Vector3(-0.205279, 1.287136, 0.163053),
    )),
)
