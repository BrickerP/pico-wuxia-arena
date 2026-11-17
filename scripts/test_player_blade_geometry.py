"""Actual displayed GLB -> checked-in runtime capsule table, without an emulator."""
import hashlib
import re
import tempfile
from pathlib import Path
import unittest

import numpy as np

import fit_player_blade as fit


def checked_in_capsules():
    rows=re.findall(r'BladeSegment\(Vector3\(([^)]+)\), Vector3\(([^)]+)\), ([^)]+)\)',fit.KOTLIN.read_text())
    if not rows:
        raise AssertionError('No actual Kotlin capsule coefficients')
    return (np.array([[float(v) for v in a.split(',')] for a,b,r in rows]),
            np.array([[float(v) for v in b.split(',')] for a,b,r in rows]),
            np.array([float(r) for a,b,r in rows]))


class DisplayedPlayerBladeGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points=fit.load_steel()
        cls.bases,cls.tips,cls.radii=checked_in_capsules()

    def test_formal_default_scene_steel_identity_and_original_undercoverage(self):
        self.assertEqual(fit.ASSET_SHA256,hashlib.sha256(fit.ASSET.read_bytes()).hexdigest())
        self.assertEqual(5533,len(self.points))
        before=fit.axis_distances(self.points,np.array([[.022,0.,-.129]]),np.array([[.0532,0.,-.849]]))[:,0]
        self.assertEqual(4469,int(np.sum(before>.012)))
        self.assertAlmostEqual(.056993961825,float(before.max()),places=11)
        print(f'BEFORE Steel5533 max_axis_mm={before.max()*1000:.9f} old12mm_outside_mm={(before.max()-.012)*1000:.9f}')

    def test_fixed_seven_thin_strips_are_deterministically_asset_derived(self):
        generated=fit.fit(self.points)
        self.assertEqual(7,len(self.radii))
        self.assertTrue(np.all(self.radii==.006))
        self.assertLessEqual(len(self.radii),16)
        self.assertEqual(fit.kotlin_source(*generated),fit.KOTLIN.read_text())
        for actual,expected in zip((self.bases,self.tips,self.radii),generated):
            self.assertTrue(np.array_equal(actual,expected))
        # The strips span the wide face, not a repeated chain on its old centreline.
        self.assertGreater(float(self.bases[:,0].max()-self.bases[:,0].min()),.068)
        self.assertTrue(np.all(np.diff(self.bases[:,0]) <= 2*self.radii[0]))

    def test_every_real_steel_vertex_is_within_two_mm_of_the_runtime_union(self):
        outside=np.maximum(0.,(fit.axis_distances(self.points,self.bases,self.tips)-self.radii).min(axis=1))
        self.assertEqual(5533,len(outside))
        self.assertTrue(np.all(outside<=.002),f'Worst Steel outside={outside.max()*1000}mm')
        self.assertAlmostEqual(.000415498761,float(outside.max()),places=11)
        print(f'AFTER runtime_capsules=7 radii_mm={[float(r)*1000 for r in self.radii]} checked_vertices={len(outside)} max_outside_mm={outside.max()*1000:.9f}')

    def test_exposed_union_surface_to_steel_maximum_has_a_continuous_bound(self):
        result=fit.surface_distance_interval(self.points,self.bases,self.tips,self.radii)
        self.assertGreater(result['lower'],.0127)
        self.assertLess(result['upper'],.01285)
        self.assertLessEqual(result['upper']-result['lower'],.00005)
        witness=np.array(result['witness'])
        gaps=fit.axis_distances(witness[None],self.bases,self.tips)[0]-self.radii
        self.assertGreaterEqual(float(gaps.min()),-1e-12)
        self.assertLess(float(np.min(np.abs(gaps))),1e-12)
        nearest=float(np.sqrt(np.min(np.sum((self.points-witness)**2,axis=1))))
        self.assertAlmostEqual(result['lower'],nearest,places=13)
        print(f'SURFACE exposed_union_to_nearest_Steel_vertex_maximum_mm=[{result["lower"]*1000:.9f},{result["upper"]*1000:.9f}] interval_width_mm={(result["upper"]-result["lower"])*1000:.9f} evaluations={result["evaluations"]}')

    def test_a_changed_display_asset_cannot_silently_reuse_the_table(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'changed.glb'
            changed=bytearray(fit.ASSET.read_bytes())
            changed[-1]^=1
            path.write_bytes(changed)
            with self.assertRaisesRegex(ValueError,'Displayed dao changed'):
                fit.load_steel(path)

    def test_wider_geometry_cannot_silently_increase_the_capsule_budget(self):
        wide=self.points.copy()
        wide[:,0]*=10
        with self.assertRaisesRegex(ValueError,'more than the permitted16'):
            fit.fit(wide)


if __name__=='__main__':
    unittest.main(verbosity=2)
