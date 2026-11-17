package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

/** The real input state, observation recognizer, pending queue and Arena damage path. */
class NativeBladeShapeAdmissionTest {
    @Test fun old44994mmMissDoesNotBlockSwingAdmissionOrFullChainBodyDamage() {
        val identity=Quaternion(0.0,0.0,0.0,1.0)
        val origin=Vector3(0.0,0.0,-1.3)
        val before=arenaOpponents.first().locomotionProfile().idle.samples.first().inStage(origin,0f)
        val body=(before.contact.bodyBottom+before.contact.bodyTop)*.5
        val vertex2046=Vector3(-.014000000432133675,-.0018720000516624373,-.6140000000596048)
        val target=WeaponGrip(body+Vector3(.24,0.0,0.0)-vertex2046,identity)
        var raw=target.copy(position=target.position+Vector3(.16,0.0,0.0))
        var now=1_000_000_000L;var sequence=0L
        val tracking=TrackingState(Hand.RIGHT)
        val events=mutableListOf<EnemyCombatEvent>()
        val session=ArenaSession(logMessage={},logFailure={_,e->throw e})
        session.setArenaPresenter {_,batch->events.addAll(batch)}
        session.setEnemyGeometry(origin,2.0)
        fun stamp()=ObservationStamp(sequence++,now,1L,InputOrigin.PICO)
        fun send(event:TrackingEvent) {
            val accepted=tracking.accept(event);assertTrue(accepted)
            session.onTrackingEvent(event,accepted,tracking.snapshot)
        }
        fun observe() {
            send(TrackingEvent.Head(stamp(),ObservedPose(Vector3(0.0,1.6,0.0),identity)))
            send(TrackingEvent.Controllers(stamp(),null,ObservedPose(raw.position,raw.rotation)))
        }
        observe();assertTrue(session.startTrial());session.onTick(now)
        now+=3_000_000_000L;observe();session.onTick(now)
        assertEquals(TrialResult.FIGHTING,session.viewState.result)
        val from=raw
        val health=session.viewState.health
        raw=target.copy(position=target.position+Vector3(-.008,0.0,0.0))
        now+=80_000_000L;observe();session.onTick(now)
        val after=arenaOpponents.first().locomotionProfile().idle.sample(.08).inStage(origin,0f)
        fun capsule(p:EnemyContactPose)=BladeSegment(p.bodyBottom,p.bodyTop,.24)
        assertNull("Old semantic centreline still misses this boundary stroke",firstRigidBladeContact(from,raw,BladeSweep(capsule(before.contact),capsule(after.contact))))
        assertTrue("Real observed semantic motion admits a swing; full steel edge damages",session.viewState.health<health)
        assertEquals(1,events.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().size)
        assertTrue(events.filterIsInstance<CombatImpact>().any {it.appliedDamage>0 && it.zone==HitZone.BODY})
    }
}
