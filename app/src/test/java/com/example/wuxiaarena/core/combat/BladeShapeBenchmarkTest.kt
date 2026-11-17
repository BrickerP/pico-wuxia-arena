package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.p0d2f0182.runtime.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.*

/** Deterministic same-input host JVM comparison. Timing is never a PICO/device estimate. */
class BladeShapeBenchmarkTest {
    private data class Case(val category:String,val player:BladeShapeSweep,val before:AttackPoseSample,val after:AttackPoseSample)
    private data class Receipt(var count:Int=0,var chainHits:Int=0,var oldHits:Int=0,var chainUnresolved:Int=0,var oldUnresolved:Int=0,
        var chainNanos:Long=0,var oldNanos:Long=0,val stats:BladeQueryStats=BladeQueryStats())
    @Test fun compareRealCurrentAttacksAirNearCutRollAndOldMissWitness() {
        val shape=DaoBladeShape.shape;val cases=mutableListOf<Case>()
        val identity=Quaternion(0.0,0.0,0.0,1.0)
        for(character in AttackBankProfileData.characters.values)for(profile in character.attacks.values) {
            for(i in 0 until profile.samples.lastIndex step 3) {
                val a=profile.samples[i].inStage(Vector3(0.0,0.0,-1.3),0f)
                val b=profile.samples[i+1].inStage(Vector3(0.0,0.0,-1.3),0f)
                for(category in listOf("current_attack","air_swing","near_cut","roll")) {
                    val q=if(category=="roll")Quaternion(0.0,0.0,sin(PI/4),cos(PI/4)) else identity
                    val x=when(category){"air_swing"->2.5;"near_cut"->.075;else->0.0}
                    val g=WeaponGrip(Vector3(x,1.25,0.0),q)
                    // A small physical translation is the same on both queries.
                    val g1=g.copy(position=g.position+Vector3(.003,0.0,0.0))
                    cases+=Case(category,BladeShapeSweep(shape,g,g1,0.0),a,b)
                }
            }
        }
        fun run(c:Case,r:Receipt) {
            val error=maxOf(c.before.bladeGripInterpolationErrorToNextMeters,c.after.bladeGripInterpolationErrorToNextMeters)
            val enemy=BladeShapeSweep(shape,c.before.bladeGrip,c.after.bladeGrip,error)
            var started=System.nanoTime()
            try {if(firstBladeShapeContact(c.player,enemy,r.stats)!=null)r.chainHits++}catch(_:BladeContactUncertainException){r.chainUnresolved++}
            r.chainNanos+=System.nanoTime()-started
            val a=BladeSegment(c.before.bladeBase,c.before.bladeTip,.0125);val b=BladeSegment(c.after.bladeBase,c.after.bladeTip,.0125)
            started=System.nanoTime()
            try {if(firstRigidBladeContact(c.player.previous,c.player.current,BladeSweep(a,b))!=null)r.oldHits++}catch(_:BladeContactUncertainException){r.oldUnresolved++}
            r.oldNanos+=System.nanoTime()-started;r.count++
        }
        // Warm both implementations on this same deterministic corpus, then record one full pass.
        cases.take(128).forEach {run(it,Receipt())}
        val rows=linkedMapOf<String,Receipt>()
        for(c in cases)run(c,rows.getOrPut(c.category){Receipt()})
        for((category,r)in rows) {
            assertEquals(0,r.chainUnresolved);assertEquals(0,r.oldUnresolved)
            assertTrue(r.stats.capsuleQueries<r.count.toLong()*324)
            println("BLADE_CHAIN_BENCH {\"category\":\"$category\",\"queries\":${r.count},\"old_capsule_queries\":${r.count},\"chain_capsule_queries\":${r.stats.capsuleQueries},\"whole_aabb_queries\":${r.stats.wholeBounds},\"group_aabb_queries\":${r.stats.groupBounds},\"old_hits\":${r.oldHits},\"chain_hits\":${r.chainHits},\"old_unresolved\":${r.oldUnresolved},\"chain_unresolved\":${r.chainUnresolved},\"old_wall_ms\":${r.oldNanos/1e6},\"chain_wall_ms\":${r.chainNanos/1e6}}")
        }
        val point=Vector3(-.014000000432133675,-.0018720000516624373,-.6140000000596048)
        val body=BladeSegment(point,point,.0001).let {BladeSweep(it,it)}
        val g=WeaponGrip(Vector3(0.0,0.0,0.0),identity);val stats=BladeQueryStats()
        val start=System.nanoTime();val old=firstRigidBladeContact(g,g,body);val oldNanos=System.nanoTime()-start
        val next=System.nanoTime();val chain=firstBladeShapeBodyContact(BladeShapeSweep(shape,g,g,0.0),body,stats);val chainNanos=System.nanoTime()-next
        assertNull(old);assertNotNull(chain)
        println("BLADE_CHAIN_BENCH {\"category\":\"old_44.994mm_vertex2046_witness\",\"queries\":1,\"old_capsule_queries\":1,\"chain_capsule_queries\":${stats.capsuleQueries},\"old_hits\":0,\"chain_hits\":1,\"old_wall_ms\":${oldNanos/1e6},\"chain_wall_ms\":${chainNanos/1e6}}")
    }
}
