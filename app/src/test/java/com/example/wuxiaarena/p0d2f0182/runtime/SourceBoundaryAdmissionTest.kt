package com.example.wuxiaarena.p0d2f0182.runtime
import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

class SourceBoundaryAdmissionTest {
 private val f=Native414Fixture
 @Test fun old414BodyToIdleCannotCommitAnUnqueried713mmWeaponJump() = withFrozenBodyRecipe {
  val s=fixture(f.held)
  advance(s,60_000_000L)
  val pose=pose(s)
  assertTrue("An unsafe new source must not be published already penetrating",gap(f.held,pose.bladeGrip)>=-1e-7)
  assertEquals("The actual old source remains visible/queryable, not a fake interpolated skeleton", "hit_body",s.viewState.enemyPoseClip)
  assertEquals(.72,pose.sourceSeconds,1e-12)
  assertNotNull(fieldOrNull(s,"heldEnemySourceJoin"))
  assertFalse((field(s,"motion") as PlayerCombatResolver).weaponConstrained)
 }
 @Test fun actualRebasedGuardBodyToIdleIsAdmittedWithoutClockDelayOrActorTurn() {
  withBodyRecipe {
   val s=fixture(f.raw[3]);val beforeYaw=s.viewState.enemyYawRadians
   advance(s,50_000_000L)
   assertEquals(EnemyPhase.IDLE,s.viewState.phase)
   assertEquals("idle",s.viewState.enemyPoseClip)
   assertNull(fieldOrNull(s,"heldEnemySourceJoin"));assertNull(field(s,"steelWithdrawal"))
   assertEquals(beforeYaw,s.viewState.enemyYawRadians,1e-6f)
   assertEquals(0L,s.viewState.phaseElapsedNanos)
   assertEquals(.491168064,checkNotNull(s.viewState.enemyPoseSourceSeconds),1e-9)
   assertEquals(75,s.viewState.health)
  }
 }
 @Test fun endpointOnlyClearCannotAdmitAnUnrenderedLargeBridge() {
  val old=EnemyPoseFrame("hit_body",Frozen414BodyRecipe.body().sample(.72))
  val target=EnemyPoseFrame("idle",arenaOpponents.first().locomotionProfile().idle.sample(f.source))
  val raw=f.raw[2]
  assertTrue(gap(raw,target.pose.inStage(f.origin,f.yaw.toFloat()).bladeGrip)>0.1)
  val result=admitEnemySourceJoin(old,target,raw,f.origin,f.yaw.toFloat(),arenaOpponents.first().locomotionProfile().idle.samples)
  assertEquals(EnemySourceJoinStatus.NEEDS_AUTHORED_TRANSITION,result.status)
  assertTrue(result.maximumSteelEndpointChangeMeters>.7)
 }
 @Test fun realRebasedGuardEndpointsMatchWithinActualSourceUncertainty() {
  val body=ActualBodyGuardRecipe.body();val idle=arenaOpponents.first().locomotionProfile().idle.sample(f.source)
  for(time in listOf(.05,.72)) {
   val result=admitEnemySourceJoin(EnemyPoseFrame("hit_body",body.sample(time)),EnemyPoseFrame("idle",idle),f.raw[3],f.origin,f.yaw.toFloat(),arenaOpponents.first().locomotionProfile().idle.samples)
   assertEquals(EnemySourceJoinStatus.ADMITTED,result.status)
   assertTrue(result.maximumSteelEndpointChangeMeters<2e-6)
  }
 }
 @Test fun hurtIntervalsSplitAtTheirRealProfileKeysAndRecoilClamp() {
  withBodyRecipe {
   val s=fixture(f.raw[3]);set(s,"recoilElapsedNanos",219_000_000L)
   val next=ArenaSession::class.java.getDeclaredMethod("nextPoseInterval",java.lang.Long.TYPE).apply {isAccessible=true}
   val dt=next.invoke(s,10_000_000L) as Long
   assertTrue(dt in 1..1_000_000L)
   set(s,"recoilElapsedNanos",220_000_000L)
   val interval=next.invoke(s,10_000_000L) as Long
   val current=pose(s);val after=ArenaSession::class.java.getDeclaredMethod("effectiveEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,interval) as EnemyPoseFrame
   val keys=ActualBodyGuardRecipe.body().samples.filter {it.sourceSeconds>current.sourceSeconds+1e-9 && it.sourceSeconds<after.pose.sourceSeconds-1e-9}
   assertTrue("A whole FK/source interval may not be skipped by a HIT query",keys.isEmpty())
  }
 }
 @Test fun attackMidpointReturnsAtNormalSourceRateThenPlaysTheFullHurtDuration() {
  val from=EnemyPoseFrame("attack_right",arenaOpponents.first().attackProfile(AttackDirection.RIGHT).sample(.5))
  val body=ActualBodyGuardRecipe.body();val start=EnemyPoseFrame("hit_body",body.sample(.05))
  val route=checkNotNull(makeEnemySourceReturn(from,start,arenaOpponents.first().attackProfile(AttackDirection.RIGHT).samples,listOf(0.0,1.75)))
  assertEquals(500_000_000L,route.returnNanos)
  assertEquals(0.0,route.guardSeconds,0.0)
  assertEquals(from,route.frame(0L))
  for(elapsed in listOf(0L,100_000_000L,250_000_000L,500_000_000L)) {
   val actual=route.frame(elapsed)
   val expected=arenaOpponents.first().attackProfile(AttackDirection.RIGHT).sample(.5*(1-elapsed/500_000_000.0))
   assertEquals("attack_right",actual.clip);assertEquals(expected,actual.pose)
  }
  val join=admitEnemySourceJoin(route.frame(route.returnNanos),start,f.raw[3],f.origin,f.yaw.toFloat(),arenaOpponents.first().locomotionProfile().idle.samples)
  assertEquals(EnemySourceJoinStatus.ADMITTED,join.status)
  val reactions=ReactionProfiles(body,arenaOpponents.first().reactionProfiles().head,arenaOpponents.first().reactionProfiles().side)
  assertEquals(.05,reactions.frame(HitReaction.PLAYER_HIT,HitZone.BODY,0L,300_000_000L).pose.sourceSeconds,0.0)
  assertEquals(.72,reactions.frame(HitReaction.PLAYER_HIT,HitZone.BODY,300_000_000L,0L).pose.sourceSeconds,0.0)
 }
 @Test fun repeatedHurtUsesItsExistingActualReturnCurveRatherThanTimeJumpingToStart() {
  val body=ActualBodyGuardRecipe.body();val from=EnemyPoseFrame("hit_body",body.sample(.4));val start=EnemyPoseFrame("hit_body",body.sample(.05))
  val route=makeEnemySourceReturn(from,start,body.samples,listOf(.05,.72))
  if(route!=null) {
   assertTrue(route.returnNanos in 1..320_000_001L)
   for(t in listOf(0L,route.returnNanos/2,route.returnNanos))assertEquals("hit_body",route.frame(t).clip)
   assertEquals(EnemySourceJoinStatus.ADMITTED,admitEnemySourceJoin(route.frame(route.returnNanos),start,f.raw[3],f.origin,f.yaw.toFloat(),arenaOpponents.first().locomotionProfile().idle.samples).status)
  } else assertEquals(EnemySourceJoinStatus.ADMITTED,admitEnemySourceJoin(from,start,f.raw[3],f.origin,f.yaw.toFloat(),arenaOpponents.first().locomotionProfile().idle.samples).status)
 }
 @Test fun stateMachineIncludesNormalRateReturnThenFullHurtWithoutDelayingDamageOrHitstop() {
  withBodyRecipe {
   val player=WeaponGrip(Vector3(2.0,1.4,-.45),Quaternion(0.0,0.0,0.0,1.0))
   val session=fixture(player)
   val combat=EnemyCombatStateMachine();combat.advanceBy(800_000_000L,true);combat.tryStartAttack(AttackDirection.RIGHT,true);combat.advanceBy(423_076_923L,true)
   set(session,"combat",combat)
   val incoming=ArenaSession::class.java.getDeclaredMethod("effectiveEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(session,0L) as EnemyPoseFrame
   if(session.javaClass.declaredFields.any {it.name=="acceptedEnemySource"})set(session,"acceptedEnemySource",incoming)
   val frame=(field(session,"simulationMotion") as PlayerMotionFrame).copy(strike=MotionStrike(71,HitZone.BODY,1.0,MotionContact(HitZone.BODY,Vector3(0.0,1.1,-1.3),Vector3(1.0,0.0,0.0))))
   val events=mutableListOf<EnemyCombatEvent>()
   ArenaSession::class.java.getDeclaredMethod("applyPlayerMotion",PlayerMotionFrame::class.java,MutableList::class.java).apply {isAccessible=true}.invoke(session,frame,events)
   assertEquals("Damage is immediate",75,session.viewState.health)
   assertEquals("Return is added to the complete original hurt duration",800_000_000L,checkNotNull(combat.nanosUntilPhaseTransition))
   val route=checkNotNull(fieldOrNull(session,"enemySourceReturn") as EnemySourceReturn?)
   assertEquals(500_000_000L,route.returnNanos)
   val impact=events.filterIsInstance<CombatImpact>().single {it.appliedDamage>0}
   assertEquals(70_000_000L,CombatFeedbackProfile.hitStopNanos(impact))
   session.setArenaPresenter {_,_->}
   advance(session,70_000_000L+100_000_000L)
   assertEquals(100_000_000L,combat.phaseElapsedNanos)
   assertEquals("attack_right",session.viewState.enemyPoseClip)
   assertEquals(incoming.pose.sourceSeconds-.1,checkNotNull(session.viewState.enemyPoseSourceSeconds),1e-9)
   advance(session,400_000_000L)
   assertEquals(500_000_000L,combat.phaseElapsedNanos)
   assertEquals("hit_body",session.viewState.enemyPoseClip)
   assertEquals(.05,checkNotNull(session.viewState.enemyPoseSourceSeconds),1e-9)
   advance(session,300_000_000L)
   assertEquals(EnemyPhase.IDLE,combat.phase)
   assertEquals(75,session.viewState.health)
   println("HURT_SOURCE_RETURN returnMs=${route.returnNanos/1e6} hurtMs=300 hitstopMs=70 sourceRate=1.0 damageImmediate=true")
  }
 }
 @Test fun correctedActualHurtSourceCannotIntroduce414DeepOverlapWhileReturningToIdle() {
  withBodyRecipe {
   val session=fixture(f.raw[3],200_000_000L)
   val before=field(session,"simulationMotion") as PlayerMotionFrame
   fun step(delta:Long,raw:WeaponGrip) {
    val start=field(session,"simulationMotion") as PlayerMotionFrame
    val axis=playerBlade(raw)
    val target=start.copy(receivedAtNanos=start.receivedAtNanos+delta,weaponGrip=raw,rawWeaponGrip=raw,bladeBase=axis.base,bladeTip=axis.tip,strike=null,swing=null)
    ArenaSession::class.java.getDeclaredMethod("advanceEnemy",java.lang.Long.TYPE,MutableList::class.java,java.lang.Long.TYPE,PlayerMotionFrame::class.java).apply {isAccessible=true}
     .invoke(session,delta,mutableListOf<EnemyCombatEvent>(),start.receivedAtNanos,target)
    session.setArenaPresenter {_,_->}
    val state=session.viewState;val virtual=checkNotNull(state.playerWeaponGrip)
    val separation=gap(virtual,pose(session).bladeGrip)
    assertTrue("A source/phase boundary may never commit the old414 2.9mm overlap: $separation clip=${state.enemyPoseClip}",separation>=-1e-7)
   }
   // These are actual observed PC poses; the bounded intermediate steps use the
   // same rigid SLERP model as production, never an invented skeleton blend.
   var previous=f.raw[3];var clear=false
   replay@for(raw in listOf(f.held)+f.raw) {
    val a=checkNotNull(previous.rotation.normalizedOrNull());val b=checkNotNull(raw.rotation.normalizedOrNull())
    val angle=2*kotlin.math.acos(kotlin.math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w).coerceIn(0.0,1.0))
    val count=kotlin.math.ceil(angle/.02).toInt().coerceAtLeast(1)
    for(i in 1..count) {
     step(10_000_000L,interpolateGrip(previous,raw,i.toDouble()/count))
     if(session.viewState.phase==EnemyPhase.IDLE && fieldOrNull(session,"heldEnemySourceJoin")==null) {clear=true;break@replay}
    }
    previous=raw
   }
   assertTrue("The corrected source plus boundary admission returns to real idle, not a held bad recipe",clear)
   assertEquals(75,session.viewState.health)
  }
 }
 @Test fun armingGuardDuringHurtKeepsTheAlreadyPlayingSourceUntilItsActualGuardEndpoint() {
  withBodyRecipe {
   val session=fixture(f.raw[3],100_000_000L)
   val before=pose(session)
   val frame=(field(session,"simulationMotion") as PlayerMotionFrame).copy(strike=MotionStrike(72,HitZone.BODY,1.0,
    MotionContact(HitZone.BODY,Vector3(0.0,1.1,-1.3),Vector3(1.0,0.0,0.0))))
   val events=mutableListOf<EnemyCombatEvent>()
   ArenaSession::class.java.getDeclaredMethod("applyPlayerMotion",PlayerMotionFrame::class.java,MutableList::class.java)
    .apply {isAccessible=true}.invoke(session,frame,events)
   val combat=field(session,"combat") as EnemyCombatStateMachine
   assertTrue(combat.guarding);assertEquals(65,combat.health)
   session.setArenaPresenter {_,_->}
   val hold=CombatFeedbackProfile.hitStopNanos(events.filterIsInstance<CombatImpact>().single())
   advance(session,hold+50_000_000L)
   assertEquals("hit_body",session.viewState.enemyPoseClip)
   assertEquals(.05+(.72-.05)*.5,checkNotNull(session.viewState.enemyPoseSourceSeconds),1e-9)
   assertNull(fieldOrNull(session,"heldEnemySourceJoin"))
   assertTrue(pose(session).sourceSeconds>before.sourceSeconds)
  }
 }
 @Test fun invalidReturnDurationCannotApplyDamageBeforeRejectingTheClock() {
  for(duration in listOf(-1L,Long.MAX_VALUE)) {
   val combat=EnemyCombatStateMachine()
   val method=checkNotNull(combat.javaClass.methods.singleOrNull {it.name=="receivePlayerHit" && it.parameterTypes.size==5})
   try {method.invoke(combat,25,true,false,AttackDirection.OVERHEAD,duration);fail("Invalid source return must be rejected")}
   catch(expected:java.lang.reflect.InvocationTargetException) {assertTrue(expected.targetException is IllegalArgumentException)}
   assertEquals(100,combat.health);assertEquals(EnemyPhase.IDLE,combat.phase)
  }
 }
 @Test fun trackingCancellationReturnsOnTheActualSourceInRecoveringWithoutDamageOrReusingTheAttackId() {
  for(origin in listOf(InputOrigin.DESKTOP,InputOrigin.PICO)) {
   val player=WeaponGrip(Vector3(2.0,1.4,-.45),Quaternion(0.0,0.0,0.0,1.0))
   val session=fixture(player);val combat=EnemyCombatStateMachine()
   combat.advanceBy(800_000_000L,true);combat.tryStartAttack(AttackDirection.RIGHT,true);combat.advanceBy(423_076_923L,true)
   val oldId=checkNotNull(combat.currentAttackId);set(session,"combat",combat)
   val incoming=EnemyPoseFrame("attack_right",arenaOpponents.first().attackProfile(AttackDirection.RIGHT).sample(.5))
   if(session.javaClass.declaredFields.any {it.name=="acceptedEnemySource"})set(session,"acceptedEnemySource",incoming)
   val events=mutableListOf<EnemyCombatEvent>();session.setArenaPresenter {_,batch->events.addAll(batch)}
   val tracking=TrackingState(Hand.RIGHT);var seq=0L;var now=0L
   fun stamp()=ObservationStamp(seq++,now,0L,origin)
   fun head()=TrackingEvent.Head(stamp(),ObservedPose(Vector3(0.0,1.649999976158142,0.0),Quaternion(0.0,0.0,0.0,1.0)))
   fun hand(grip:WeaponGrip?)=TrackingEvent.Controllers(stamp(),null,grip?.let {ObservedPose(it.position,it.rotation)})
   fun send(e:TrackingEvent) {val accepted=tracking.accept(e);assertTrue(accepted);session.onTrackingEvent(e,accepted,tracking.snapshot)}
   assertTrue(tracking.accept(head()));assertTrue(tracking.accept(hand(player)))
   now+=1_000_000L;send(hand(null))
   assertEquals(PauseReason.TRACKING_INTERRUPTION,combat.pauseReason)
   now+=1_000_000L;send(head());send(hand(player))
   assertTrue(session.viewState.resumeReady)
   assertTrue(session.confirmResume(checkNotNull(combat.currentPauseId)))
   assertEquals(EnemyPhase.RECOVERING,combat.phase)
   assertNull(combat.currentAttackId);assertNull(combat.hitReaction)
   assertEquals("attack_right",session.viewState.enemyPoseClip)
   assertEquals(.5,checkNotNull(session.viewState.enemyPoseSourceSeconds),1e-9)
   val cancellations=events.filterIsInstance<EnemyCombatEvent.AttackCancelled>()
   assertEquals(1,cancellations.size);assertEquals(oldId,cancellations.single().attackId)
   // No current motion frame exists immediately after confirmation. It must not
   // advance the visual source until fresh accepted tracking establishes baseline.
   session.onTick(now);session.onTick(now+10_000_000L)
   assertEquals(.5,checkNotNull(session.viewState.enemyPoseSourceSeconds),1e-9)
   repeat(65) {now+=10_000_000L;send(head());send(hand(player));session.onTick(now)}
   assertEquals(EnemyPhase.IDLE,combat.phase)
   assertNull(fieldOrNull(session,"heldEnemySourceJoin"))
   assertEquals(100,combat.health)
   assertTrue(events.none {it is EnemyCombatEvent.EnemyDamaged || it is CombatImpact || it is EnemyCombatEvent.HitReactionStarted})
  }
 }
 @Test fun actualGuardSeamsUseNoBreathingCycleWaitAndStillRequireRouteClearance() {
  val far=WeaponGrip(Vector3(3.0,1.4,0.0),Quaternion(0.0,0.0,0.0,1.0))
  for(opponent in arenaOpponents) {
   val locomotion=opponent.locomotionProfile()
   for(guard in listOf(locomotion.idle,locomotion.walk))for(hurt in listOf(opponent.reactionProfiles().body,opponent.reactionProfiles().head)) {
    val from=EnemyPoseFrame(guard.clip,guard.sample(.75));val to=EnemyPoseFrame(hurt.clip,hurt.sample(.05))
    assertTrue("Actual ${opponent.asset}/${guard.clip}/${hurt.clip} guard anchors stay in the breathing envelope and certified Steel fits 2mm",boundedGuardPoseJoin(from,to,guard.samples))
    val route=makeEnemySourceReturn(from,to,guard.samples,listOf(guard.samples.first().sourceSeconds,guard.samples.last().sourceSeconds))
    assertNull("A bounded guard seam must not wait 750ms for a breathing source cycle",route)
    assertEquals(EnemySourceJoinStatus.ADMITTED,admitEnemySourceJoin(from,to,far,f.origin,f.yaw.toFloat(),guard.samples).status)
    val end=EnemyPoseFrame(hurt.clip,hurt.sample(.72))
    assertEquals(EnemySourceJoinStatus.ADMITTED,admitEnemySourceJoin(end,from,far,f.origin,f.yaw.toFloat(),guard.samples).status)
   }
  }
 }
 @Test fun guardPoseCommitRejectsAnchorsOutsideTheActualBreathingEnvelope() {
  val opponent=arenaOpponents.first();val guard=opponent.locomotionProfile().idle
  val from=EnemyPoseFrame("idle",guard.sample(.75));val pose=opponent.reactionProfiles().body.sample(.05)
  val invalid=EnemyPoseFrame("hit_body",pose.copy(contact=pose.contact.copy(head=pose.contact.head+Vector3(0.0,.1,0.0))))
  val far=WeaponGrip(Vector3(3.0,1.4,0.0),Quaternion(0.0,0.0,0.0,1.0))
  assertFalse(boundedGuardPoseJoin(from,invalid,guard.samples))
  assertEquals(EnemySourceJoinStatus.NEEDS_AUTHORED_TRANSITION,admitEnemySourceJoin(from,invalid,far,f.origin,f.yaw.toFloat(),guard.samples).status)
 }
 @Test fun aSmallGuardPoseSeamCannotCommitThroughSteelEvenWithClearEndpoints() {
  val shape=DaoBladeShape.shape
  val original=arenaOpponents.first().locomotionProfile().idle.sample(0.0)
  val support=shape.parts.flatMap {part->listOf(part.base to part.radiusMeters,part.tip to part.radiusMeters)}
   .maxBy { (point,radius)->kotlin.math.hypot(point.x,point.z)+radius }
  val point=support.first;val radius=support.second
  val normal=checkNotNull(Vector3(point.x,0.0,point.z).normalizedOrNull())
  val angle=.00115
  val before=WeaponGrip(Vector3(0.0,0.0,0.0),Quaternion(0.0,kotlin.math.sin(-angle/2),0.0,kotlin.math.cos(angle/2)))
  val after=before.copy(rotation=Quaternion(0.0,kotlin.math.sin(angle/2),0.0,kotlin.math.cos(angle/2)))
  val middle=before.copy(rotation=Quaternion(0.0,0.0,0.0,1.0))
  // Opposed copies touch at the descriptor's radial extreme. Its arc passes
  // 0.2 micrometers inside the static blade although both endpoints are clear.
  val player=WeaponGrip(Vector3(2*point.x,0.0,2*point.z)+normal*(2*radius-2e-7),Quaternion(0.0,1.0,0.0,0.0))
  fun frame(clip:String,g:WeaponGrip)=EnemyPoseFrame(clip,original.copy(sourceSeconds=if(clip=="hit_body").05 else 0.0,bladeGrip=g,
   bladeBase=playerBlade(g).base,bladeTip=playerBlade(g).tip,bladeGripInterpolationErrorToNextMeters=0.0))
  val a=frame("idle",before);val b=frame("hit_body",after)
  assertTrue(boundedGuardPoseJoin(a,b,listOf(original)))
  val initialGap=gap(player,before);val targetGap=gap(player,after);val interiorGap=gap(player,middle)
  assertTrue("Actual complete-chain start is clear: $initialGap",initialGap>1e-7)
  assertTrue("Actual complete-chain target is clear: $targetGap",targetGap>1e-7)
  assertTrue("Actual arc enters steel: $interiorGap",interiorGap< -1e-7)
  assertEquals(EnemySourceJoinStatus.CONTACT_BLOCKED,admitEnemySourceJoin(a,b,player,Vector3(0.0,0.0,0.0),0f,listOf(original)).status)
 }
 @Test fun aContactBlockedGuardJoinStillCertifiesTheEntireUpcomingHurtAndIdleDomain() {
  withBodyRecipe {
   val far=WeaponGrip(Vector3(3.0,1.4,0.0),Quaternion(0.0,0.0,0.0,1.0))
   val session=fixture(far,0L)
   val old=EnemyPoseFrame("idle",arenaOpponents.first().locomotionProfile().idle.sample(.75))
   set(session,"heldEnemySourceJoin",old)
   set(session,"heldEnemySourceJoinStatus",EnemySourceJoinStatus.CONTACT_BLOCKED)
   @Suppress("UNCHECKED_CAST")
   val domain=ArenaSession::class.java.getDeclaredMethod("steelRecoverySamples",AttackPoseSample::class.java)
    .apply {isAccessible=true}.invoke(session,old.pose) as List<AttackPoseSample>
   for(row in ActualBodyGuardRecipe.body().samples.filter {it.sourceSeconds in .05.. .72})
    assertTrue("A blocked seam still owes hurt source ${row.sourceSeconds}",domain.any {it.bladeGrip==row.bladeGrip && it.contact==row.contact})
   for(row in arenaOpponents.first().locomotionProfile().idle.samples)
    assertTrue("All actual future breathing poses remain in the actor certificate",domain.any {it.bladeGrip==row.bladeGrip && it.contact==row.contact})
  }
 }
 private fun fixture(player:WeaponGrip,elapsed:Long=250_000_000L):ArenaSession {
  val s=ArenaSession(logMessage={},logFailure={_,e->throw e});s.setEnemyGeometry(f.origin,2.0)
  val tracking=TrackingState(Hand.RIGHT);var seq=0L
  fun send(e:TrackingEvent){val accepted=tracking.accept(e);assertTrue(accepted);s.onTrackingEvent(e,accepted,tracking.snapshot)}
  send(TrackingEvent.Head(ObservationStamp(seq++,0L,0L,InputOrigin.PICO),ObservedPose(Vector3(0.0,1.649999976158142,0.0),Quaternion(0.0,0.0,0.0,1.0))))
  send(TrackingEvent.Controllers(ObservationStamp(seq++,0L,0L,InputOrigin.PICO),null,ObservedPose(player.position,player.rotation)))
  val combat=EnemyCombatStateMachine();combat.receivePlayerHit(25,true);combat.advanceBy(elapsed,true)
  set(s,"combat",combat);set(s,"result",TrialResult.FIGHTING);set(s,"trialStarted",true);set(s,"enemyYaw",f.yaw.toFloat());set(s,"enemyMotionNanos",491168064L-(300_000_000L-elapsed))
  val frame=field(s,"latestMotion") as PlayerMotionFrame
  set(s,"simulationMotion",frame)
  val accepted=EnemyPoseFrame("hit_body",arenaOpponents.first().reactionProfiles().body.sample(.05+(.72-.05)*elapsed/300_000_000.0))
  // This is the actual last safe old source at the beginning of the reproduced boundary.
  if(s.javaClass.declaredFields.any {it.name=="acceptedEnemySource"})set(s,"acceptedEnemySource",accepted)
  return s
 }
 private fun advance(s:ArenaSession,delta:Long) {
  val frame=field(s,"simulationMotion") as PlayerMotionFrame
  ArenaSession::class.java.getDeclaredMethod("advanceEnemy",java.lang.Long.TYPE,MutableList::class.java,java.lang.Long.TYPE,PlayerMotionFrame::class.java)
   .apply {isAccessible=true}.invoke(s,delta,mutableListOf<EnemyCombatEvent>(),frame.receivedAtNanos,frame.copy(receivedAtNanos=frame.receivedAtNanos+delta))
 }
 private fun pose(s:ArenaSession)=ArenaSession::class.java.getDeclaredMethod("enemyAttackPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as AttackPoseSample
 private fun gap(player:WeaponGrip,enemy:WeaponGrip)=DaoBladeShape.shape.at(player).minOf {p->DaoBladeShape.shape.at(enemy).minOf {e->val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip));pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters}}
 private fun withFrozenBodyRecipe(block:()->Unit) {
  @Suppress("UNCHECKED_CAST") val map=AttackBankProfileData.characters as MutableMap<String,CharacterAttackProfiles>
  val key=arenaOpponents.first().asset;val old=map.getValue(key)
  map[key]=old.copy(reactions=ReactionProfiles(Frozen414BodyRecipe.body(),old.reactions.head,old.reactions.side))
  try {block()}finally {map[key]=old}
 }
 private fun withBodyRecipe(block:()->Unit) {
  @Suppress("UNCHECKED_CAST") val map=AttackBankProfileData.characters as MutableMap<String,CharacterAttackProfiles>
  val key=arenaOpponents.first().asset;val old=map.getValue(key)
  map[key]=old.copy(modelSha256=ActualBodyGuardRecipe.modelSha,profileSha256=ActualBodyGuardRecipe.profileSha,
   reactions=ReactionProfiles(ActualBodyGuardRecipe.body(),old.reactions.head,old.reactions.side))
  try {block()}finally {map[key]=old}
 }
 private fun fieldOrNull(o:Any,n:String)=o.javaClass.declaredFields.firstOrNull {it.name==n}?.apply {isAccessible=true}?.get(o)
 private fun field(o:Any,n:String)=o.javaClass.getDeclaredField(n).apply {isAccessible=true}.get(o)
 private fun set(o:Any,n:String,v:Any)=o.javaClass.getDeclaredField(n).apply {isAccessible=true}.set(o,v)
}
