package com.example.wuxiaarena.core.combat
import com.example.wuxiaarena.core.math.*
import org.junit.Test
import org.junit.Assert.*

class NativeUnsafeTurnTest {
    @Test fun aRecordedLargeClearTargetReallySweepsIntoTheFrozenWholeSteel() {
        val f=NativeFreezeFixture;val shape=DaoBladeShape.shape;val enemy=shape.at(f.enemy)
        fun gap(grip:WeaponGrip)=shape.at(grip).minOf {p->enemy.minOf {e->
            val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip));pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters
        }}
        val raw=f.raw.first {gap(it)>.025+f.sourceError}
        assertTrue(gap(raw)>.025+f.sourceError)
        // One actual interior-pose witness proves penetration. Sampling is used only
        // to find this negative witness, never to claim that a complete path is safe.
        val witness=(1 until 128).map {it/128.0}.map {t->t to gap(interpolateGrip(f.held,raw,t))}.minBy {it.second}
        assertTrue("Even allowing the full FK envelope, this interior whole-solid pose overlaps",witness.second < -f.sourceError-.001)
        assertFalse(separatingBladeShapePairs(BladeShapeSweep(shape,f.held,raw,0.0),f.enemySweep))
        val constraint=WeaponContactConstraint();constraint.lock(raw,f.held,f.normal)
        assertFalse(constraint.releaseForPlayerWithdrawal(f.enemySweep,raw))
        assertTrue(constraint.constrained)
        println("NATIVE_UNSAFE_TURN rawEndpointGap=${gap(raw)} interiorFraction=${witness.first} nominalInteriorGap=${witness.second} sourceError=${f.sourceError}")
    }
}
