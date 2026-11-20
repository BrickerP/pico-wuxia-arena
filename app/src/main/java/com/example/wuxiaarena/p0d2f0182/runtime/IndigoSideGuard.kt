package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestPoint

private val indigoRibHeights by lazy {
    listOf(AttackDirection.LEFT, AttackDirection.RIGHT).associateWith { direction ->
        val profile = arenaOpponents[1].attackProfile(direction)
        val cue = profile.sample(profile.contactSourceSeconds)
        (cue.bladeBase.y + cue.bladeTip.y) * .5
    }
}

internal fun indigoGuardCoversRibs(direction: AttackDirection, head: Vector3, enemy: Vector3,
    bladeBase: Vector3, bladeTip: Vector3): Boolean {
    val height = indigoRibHeights[direction] ?: return false
    val forward = Vector3(enemy.x - head.x, 0.0, enemy.z - head.z).normalizedOrNull() ?: return false
    val right = Vector3(-forward.z, 0.0, forward.x)
    val side = if (direction == AttackDirection.LEFT) -.31 else .31
    val target = Vector3(head.x, enemy.y + height, head.z) + forward * .42 + right * side
    return closestPoint(target, bladeBase, bladeTip).distanceTo(target) <= .15
}
