package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DamagePopupTimelineTest {
    @Test
    fun batchContactsKeepTheirActualDamageAndIndividualEmphasis() {
        val body = impact(1, 25)
        val guarded = impact(2, 6).copy(kind = CombatImpactKind.GUARDED_HIT)
        val head = impact(3, 30).copy(zone = HitZone.HEAD)
        val fatal = impact(4, 4).copy(fatal = true)
        val frames = update(DamagePopupTimeline(), listOf(body, guarded, head, fatal))

        assertEquals(listOf(25, 6, 30, 4), frames.map { it.content.amount })
        assertEquals(4, frames.map { it.slot }.distinct().size)
        assertTrue(frames[1].content.guarded)
        assertTrue(frames[2].content.headHit)
        assertTrue(frames[3].content.fatal)
        assertTrue(frames[3].scale > frames[2].scale)
    }

    @Test
    fun duplicateContactsDoNotAddSlotsOrRestartExpiredNumbers() {
        val timeline = DamagePopupTimeline()
        val first = impact(1)
        assertEquals(1, update(timeline, listOf(first, first)).size)
        assertEquals(1, update(timeline, listOf(first), 100_000_000L).size)
        assertTrue(update(timeline, listOf(first), 600_000_000L).isEmpty())
    }

    @Test
    fun zeroDamageAndPlayerOrBladeDefenseContactsHaveNoEnemyNumber() {
        val contacts = listOf(
            impact(1, 0),
            impact(2).copy(kind = CombatImpactKind.BLOCK),
            impact(3).copy(kind = CombatImpactKind.PARRY),
            impact(4).copy(kind = CombatImpactKind.PLAYER_HIT),
        )
        assertTrue(update(DamagePopupTimeline(), contacts).isEmpty())
    }

    @Test
    fun aBusyBatchIsBoundedToFourSlotsAndRetainsItsFatalContact() {
        val contacts = (1L..6L).map { impact(it).copy(fatal = it == 1L) }
        val frames = update(DamagePopupTimeline(), contacts)

        assertEquals(4, frames.size)
        assertTrue(frames.any { it.content.impactId == 1L && it.content.fatal })
        assertEquals(4, frames.map { it.slot }.distinct().size)
    }

    @Test
    fun pausedContactsAreConsumedAndCannotReplayOnResume() {
        val timeline = DamagePopupTimeline()
        update(timeline, listOf(impact(1)))
        assertTrue(update(timeline, listOf(impact(2)), 10_000_000L, active = false).isEmpty())
        assertTrue(update(timeline, listOf(impact(2)), 20_000_000L).isEmpty())
        assertEquals(3L, update(timeline, listOf(impact(3)), 30_000_000L).single().content.impactId)
    }

    @Test
    fun switchingOpponentClearsNumbersAndGenerationDefinesTheirIdentity() {
        val timeline = DamagePopupTimeline()
        update(timeline, listOf(impact(1)))
        assertTrue(update(timeline, listOf(impact(1)), 10_000_000L, round = 2).isEmpty())
        assertEquals(2L, update(timeline, listOf(impact(2)), 20_000_000L, round = 2).single().content.impactId)
        val restarted = update(timeline, listOf(impact(1)), 30_000_000L, generation = 2, round = 1)
        assertEquals(1L, restarted.single().content.impactId)
    }

    @Test
    fun clockRollbackAndExplicitClearDiscardOldMotionWithoutReplayingHits() {
        val timeline = DamagePopupTimeline()
        update(timeline, listOf(impact(1)), 100_000_000L)
        assertTrue(update(timeline, emptyList(), 90_000_000L).isEmpty())
        update(timeline, listOf(impact(2)), 110_000_000L)
        timeline.clear()
        assertTrue(update(timeline, listOf(impact(2)), 120_000_000L).isEmpty())
    }

    @Test
    fun numbersRiseEightCentimetresBounceOnceAndFadeAtSixHundredMilliseconds() {
        val timeline = DamagePopupTimeline()
        val initial = update(timeline, listOf(impact(1))).single()
        val bounce = update(timeline, emptyList(), 90_000_000L).single()
        val middle = update(timeline, emptyList(), 300_000_000L).single()
        val fading = update(timeline, emptyList(), 450_000_000L).single()

        assertEquals(1f, initial.opacity, 0f)
        assertTrue(bounce.scale > initial.scale)
        assertEquals(0.06, middle.position.y - initial.position.y, 0.000001)
        assertEquals(initial.position.z, middle.position.z, 0.0)
        assertTrue(fading.opacity in 0f..1f && fading.opacity < middle.opacity)
        assertTrue(update(timeline, emptyList(), 600_000_000L).isEmpty())
    }

    @Test
    fun oldFutureAndInvalidContactsAreRejected() {
        val timeline = DamagePopupTimeline()
        val boundary = impact(1).copy(atNanos = 880_000_000L)
        val expired = impact(2).copy(atNanos = 879_999_999L)
        val future = impact(3).copy(atNanos = 1_000_000_001L)
        val invalid = impact(4).copy(point = Vector3(Double.NaN, 1.0, -1.0))
        val frames = update(timeline, listOf(boundary, expired, future, invalid),
            1_000_000_000L, simulation = 1_000_000_000L)

        assertEquals(1L, frames.single().content.impactId)
    }

    @Test
    fun anUnavailableViewerUsesAFiniteStableContactOffset() {
        val frames = DamagePopupTimeline().update(1, 1, true, 0, 0,
            Vector3(Double.NaN, 1.6, 0.0), listOf(impact(1)))
        assertTrue(frames.single().position.isFinite())
    }

    @Test
    fun controlLayoutKeepsPreparationAndPausedGuidesAndDesktopFightActions() {
        assertFalse(arenaControlsAreCompact(TrialResult.READY, null))
        assertFalse(arenaControlsAreCompact(TrialResult.FIGHTING, PauseReason.USER))
        assertFalse(arenaControlsAreCompact(TrialResult.FIGHTING, PauseReason.TRACKING_INTERRUPTION))
        assertTrue(arenaControlsAreCompact(TrialResult.FIGHTING, null))
        assertTrue(arenaControlsAreCompact(TrialResult.ROUND_CLEAR, null))
        assertEquals(160, arenaControlPanelHeightDp(TrialResult.FIGHTING, null, false))
        assertEquals(240, arenaControlPanelHeightDp(TrialResult.FIGHTING, null, true))
        assertEquals(400, arenaControlPanelHeightDp(TrialResult.FIGHTING, PauseReason.USER, true))
    }

    @Test
    fun closeOpponentsCannotPullTheStatusBoardInsideItsReadingDistance() {
        val viewer = Vector3(0.0, 1.6, 0.0)
        val close = readableStatusPosition(Vector3(0.0, 0.0, -0.6), viewer, 2.15)
        val distant = readableStatusPosition(Vector3(0.0, 0.0, -2.4), viewer, 2.15)

        assertEquals(Vector3(0.0, 2.15, -1.8), close)
        assertEquals(Vector3(0.0, 2.15, -2.4), distant)
    }

    @Test
    fun simultaneousOverflowKeepsTheNewestFourContacts() {
        val frames = update(DamagePopupTimeline(), (1L..6L).map { impact(it) })
        assertEquals(listOf(3L, 4L, 5L, 6L), frames.map { it.content.impactId }.sorted())
    }

    @Test
    fun ordinaryContactsCannotEvictFourLiveFatalNumbers() {
        val timeline = DamagePopupTimeline()
        val frames = update(timeline, (1L..6L).map { impact(it).copy(fatal = true) })
        assertEquals(listOf(3L, 4L, 5L, 6L), frames.map { it.content.impactId }.sorted())
        val later = update(timeline, listOf(impact(7), impact(8)), 50_000_000L)
        assertEquals(listOf(3L, 4L, 5L, 6L), later.map { it.content.impactId }.sorted())
        assertTrue(later.all { it.content.fatal })
    }

    @Test
    fun lateralViewerMotionRotatesTheBoardTowardTheViewer() {
        val position = Vector3(0.0, 2.15, -2.0)
        val viewer = Vector3(1.0, 1.6, 0.0)
        val rotation = readableStatusRotation(position, viewer)
        val forward = checkNotNull(rotation.rotate(Vector3(0.0, 0.0, 1.0)))
        val expected = checkNotNull(Vector3(1.0, 0.0, 2.0).normalizedOrNull())
        assertEquals(1.0, forward.dot(expected), 0.000001)
        val neutral = readableStatusRotation(position, null)
        assertEquals(Vector3(0.0, 0.0, 1.0), neutral.rotate(Vector3(0.0, 0.0, 1.0)))
    }

    private fun impact(id: Long, damage: Int = 25) = CombatImpact(
        id, CombatImpactKind.SOFT_HIT, Vector3(0.0, 1.2, -1.2),
        Vector3(0.0, 0.0, 1.0), 0.5, Hand.RIGHT, 0L, appliedDamage = damage,
    )

    private fun update(
        timeline: DamagePopupTimeline,
        events: List<EnemyCombatEvent>,
        now: Long = 0L,
        active: Boolean = true,
        generation: Long = 1L,
        round: Int = 1,
        simulation: Long = 0L,
    ) = timeline.update(generation, round, active, simulation, now, Vector3(0.0, 1.6, 0.0), events)
}
