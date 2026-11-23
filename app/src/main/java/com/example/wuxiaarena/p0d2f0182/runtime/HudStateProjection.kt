package com.example.wuxiaarena.p0d2f0182.runtime

internal fun shouldPublishControlState(previous: ArenaViewState, state: ArenaViewState): Boolean {
    if (previous.result != TrialResult.FIGHTING || state.result != TrialResult.FIGHTING ||
        previous.pauseReason != null || state.pauseReason != null) return shouldPublishHudState(previous, state)
    return previous.roundGeneration != state.roundGeneration ||
        previous.sceneReady != state.sceneReady || previous.inputReady != state.inputReady ||
        previous.resumeReady != state.resumeReady || previous.actionReady != state.actionReady ||
        previous.inputOrigin != state.inputOrigin
}

internal fun shouldPublishHudState(previous: ArenaViewState, state: ArenaViewState): Boolean {
    val hudComparable = state.copy(
        simulationNanos = previous.simulationNanos,
        phaseElapsedNanos = previous.phaseElapsedNanos,
        phaseRemainingNanos = previous.phaseRemainingNanos,
        enemyPosition = previous.enemyPosition,
        enemyYawRadians = previous.enemyYawRadians,
        hitStop = previous.hitStop,
        deathElapsedSeconds = previous.deathElapsedSeconds,
        enemyTravelMeters = previous.enemyTravelMeters,
        enemyGaitMeters = previous.enemyGaitMeters,
        enemyMoveDirection = previous.enemyMoveDirection,
        playerBladeBase = previous.playerBladeBase,
        playerBladeTip = previous.playerBladeTip,
        playerBladeTipSpeed = previous.playerBladeTipSpeed,
        playerBladeAtRest = previous.playerBladeAtRest,
        playerMotionGeneration = previous.playerMotionGeneration,
        playerHeadPosition = previous.playerHeadPosition,
        enemyRecoilOffset = previous.enemyRecoilOffset,
        enemyBladeBase = previous.enemyBladeBase,
        enemyBladeTip = previous.enemyBladeTip,
        playerWeaponGrip = previous.playerWeaponGrip,
        enemyPoseClip = previous.enemyPoseClip,
        enemyPoseSourceSeconds = previous.enemyPoseSourceSeconds,
        enemyPoseDirection = previous.enemyPoseDirection,
        diagnosticUiFrameNanos = previous.diagnosticUiFrameNanos,
        diagnosticPublishSource = previous.diagnosticPublishSource,
        diagnosticHandStamp = previous.diagnosticHandStamp,
    )
    return hudComparable != previous
}
