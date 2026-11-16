package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.combat.PlayerMotionFrame
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.*
import org.junit.Test

/** Every observation comes from TrackingState.accept; no direct skill calls or synthetic snapshots. */
class SkillMotionRegressionTest {
    @Test fun stationaryWorldHandsCannotCastWhenOnlyTheHeadMovesBackward() {
        val f=Fixture();f.charge()
        val frames=(1..2).map { i->f.sample(100_000_000L,head=HEAD+Vector3(0.0,0.0,.15*i)) }
        assertTrue("The player's actual hand positions remain unchanged",frames.all {
            it.rawWeaponGrip?.position==RIGHT
        })
        assertEquals(LEFT,requireNotNull(f.tracking.snapshot.left).pose?.position)
        assertEquals(RIGHT,requireNotNull(f.tracking.snapshot.right).pose?.position)
        println("SKILL_HEAD_ONLY headDeltaM=.30 intervalS=.20 leftWorldDeltaM=0 rightWorldDeltaM=0 castFlags=${frames.map { it.skillGesture }}")
        assertFalse("Head translation is not a physical two-hand thrust",frames.any { it.skillGesture })
    }

    @Test fun chargedWorldHandsPushingForwardCastExactlyOnce() {
        val f=Fixture();f.charge()
        val frames=f.push()
        assertFalse("Half of a .30m thrust has not reached the unchanged .25m requirement",frames.first().skillGesture)
        println("SKILL_WORLD_THRUST handsDeltaM=.30 intervalS=.20 headDeltaM=0 castFlags=${frames.map { it.skillGesture }}")
        assertEquals("A true .30m world thrust over .20s must cast once",1,frames.count { it.skillGesture })
        assertTrue(frames.last().releaseRequired)
        repeat(4) {
            assertFalse("Holding the extended hands cannot repeat the cast",
                f.sample(50_000_000L,left=LEFT+THRUST,right=RIGHT+THRUST).skillGesture)
        }
    }

    @Test fun wholeBodyWorldTranslationCannotReplaceRelativeHandExtension() {
        val f=Fixture();f.charge()
        val frames=(1..2).map { i->
            val delta=Vector3(0.0,0.0,-.15*i)
            f.sample(100_000_000L,head=HEAD+delta,left=LEFT+delta,right=RIGHT+delta)
        }
        assertFalse("Moving head and both hands together has no extension from the charged pose",
            frames.any { it.skillGesture })
    }

    @Test fun losingTheOtherHandCancelsChargeAndOnlyARechargedThrustCanCast() {
        val f=Fixture();f.charge()
        val lost=f.sample(50_000_000L,left=null)
        assertFalse(lost.skillGesture)
        assertEquals(0f,lost.chargeProgress,0f)
        assertFalse("Returning a hand cannot reuse the old charge",f.push().any { it.skillGesture })
        f.sample(100_000_000L)
        f.charge()
        assertEquals(1,f.push().count { it.skillGesture })
    }

    @Test fun otherHandContinuityChangeCancelsChargeWithoutLosingTheDominantHand() {
        val f=Fixture();f.charge()
        val before=f.tracking.snapshot
        f.discontinueOtherHand()
        assertEquals(before.right,f.tracking.snapshot.right)
        assertTrue(f.tracking.snapshot.leftContinuity>before.leftContinuity)
        assertFalse("Other-hand continuity is part of skill readiness",f.push().any { it.skillGesture })
        f.sample(100_000_000L)
        f.charge()
        assertEquals(1,f.push().count { it.skillGesture })
    }

    @Test fun staleControllerPairBeyondSampleGapClearsChargeBeforeFreshInputCanCast() {
        val f=Fixture();f.charge()
        val oldPairTime=requireNotNull(f.tracking.snapshot.right).stamp.receivedAtNanos
        val unavailable=f.headOnly(300_000_000L)
        assertTrue(f.now-oldPairTime>250_000_000L)
        assertNull("A pair older than the frozen .25s MAX_SAMPLE_GAP is unavailable",unavailable)
        assertFalse("Fresh data after a stale pair requires charging again",f.push().any { it.skillGesture })
        f.sample(100_000_000L)
        f.charge()
        assertEquals(1,f.push().count { it.skillGesture })
    }

    @Test fun coordinateEpochChangeCannotPairWithOldControllersOrCarryTheOldCharge() {
        val f=Fixture();f.charge()
        assertNull("New epoch head cannot pair with old epoch controller data",f.headOnly(50_000_000L,epoch=2L))
        assertFalse(f.tracking.snapshot.hasRequiredObservations)
        val stale=TrackingEvent.Controllers(f.stamp(epoch=1L),pose(LEFT),pose(RIGHT))
        assertFalse("TrackingState itself must reject a controller from the previous epoch",f.tracking.accept(stale))
        assertNull(f.resolver.observe(f.tracking.snapshot,ENEMY))
        f.epoch=2L
        assertFalse("Changing coordinates establishes a new gesture baseline",f.push().any { it.skillGesture })
        assertEquals(2L,requireNotNull(f.tracking.snapshot.head).stamp.coordinateEpoch)
        assertEquals(2L,requireNotNull(f.tracking.snapshot.right).stamp.coordinateEpoch)
        f.sample(100_000_000L)
        f.charge()
        assertEquals(1,f.push().count { it.skillGesture })
    }

    private class Fixture {
        val tracking=TrackingState(Hand.RIGHT)
        val resolver=PlayerCombatResolver()
        var now=1_000_000_000L
            private set
        var epoch=1L
        private var sequence=0L
        init { sample(0L) }
        fun stamp(epoch:Long=this.epoch)=ObservationStamp(sequence++,now,epoch,InputOrigin.PICO)
        private fun accept(event:TrackingEvent) {
            assertTrue("Fresh ordered source observation must be accepted",tracking.accept(event))
        }
        fun sample(delta:Long,head:Vector3=HEAD,left:Vector3?=LEFT,right:Vector3=RIGHT):PlayerMotionFrame {
            now+=delta
            // Both sources get a new sequence even when world positions are stationary.
            accept(TrackingEvent.Head(stamp(),pose(head)))
            accept(TrackingEvent.Controllers(stamp(),left?.let(::pose),pose(right)))
            return requireNotNull(resolver.observe(tracking.snapshot,ENEMY))
        }
        fun headOnly(delta:Long,epoch:Long=this.epoch):PlayerMotionFrame? {
            now+=delta
            accept(TrackingEvent.Head(stamp(epoch),pose(HEAD)))
            return resolver.observe(tracking.snapshot,ENEMY)
        }
        fun discontinueOtherHand() {
            now+=1_000_000L
            accept(TrackingEvent.Discontinuity(stamp(),TrackingTarget.LEFT_HAND,DiscontinuityReason.PROVIDER_UNAVAILABLE))
            resolver.observe(tracking.snapshot,ENEMY)
        }
        fun charge() {
            var last:PlayerMotionFrame?=null
            // Frozen source requires .40s; .50s includes the first updateSkill baseline sample.
            repeat(10) {
                last=sample(50_000_000L)
                assertFalse("Charging itself must not cast",requireNotNull(last).skillGesture)
            }
            assertEquals("Chest pose with .20m hand spacing must complete charge",1f,requireNotNull(last).chargeProgress,0f)
        }
        fun push():List<PlayerMotionFrame> =(1..2).map { i->
            val offset=THRUST*(i/2.0)
            sample(100_000_000L,left=LEFT+offset,right=RIGHT+offset)
        }
    }
    private companion object {
        val HEAD=Vector3(0.0,1.6,0.0)
        val LEFT=Vector3(-.1,1.3,-.2)
        val RIGHT=Vector3(.1,1.3,-.2)
        val ENEMY=Vector3(0.0,0.0,-1.3)
        val THRUST=Vector3(0.0,0.0,-.3)
        val ROTATION=Quaternion(0.0,0.0,0.0,1.0)
        fun pose(position:Vector3)=ObservedPose(position,ROTATION)
    }
}
