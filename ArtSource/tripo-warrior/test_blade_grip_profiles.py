"""Canonical full blade-grip production regressions; run with Blender Python.

The module under test and its fixtures use only public producer code.
No frozen private delivery or previously published profile is required.
"""
import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import blade_grip_profiles as grip
import prepare_character_library as library
import production_contract
import test_attack_profiles as fixtures


SECTIONS = ('attacks', 'locomotion', 'reactions')




def rotation(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) * math.cos(angle) + (1-math.cos(angle)) * np.outer(axis, axis) + math.sin(angle) * cross


def matrix(angle=.7, axis=(0, 1, 0)):
    result = np.eye(4)
    result[:3, :3] = rotation(axis, angle)
    result[:3, 3] = [.2, 1.3, -.4]
    return result


def synthetic_prepared(rotation_tracks, radius=.851):
    prepared=grip.PreparedGrip.__new__(grip.PreparedGrip);count=len(rotation_tracks)
    prepared.asset=SimpleNamespace(nodes=[{} for _ in range(count)],parents={i:i-1 for i in range(1,count)})
    prepared.chain=prepared.hand_chain=list(range(count));prepared.grip=count-1;prepared.cache={}
    prepared.tracks={'synthetic':{(i,'rotation'):(np.asarray(times,dtype=float),np.asarray([[0,0,math.sin(a/2),math.cos(a/2)] for a in angles]),'LINEAR') for i,(times,angles) in enumerate(rotation_tracks)}}
    prepared.local_hand_radius=prepared.support_radius=radius;prepared.mesh_error=0
    return prepared


def seed_profile():
    """A valid schema-3 seed with no dependency on the old export return schema."""
    from attack_profiles import hierarchy, animation_tracks, profile_sample, landmark_indices
    from mathutils import Vector
    document, binary = fixtures.actor()
    _, parents, order = hierarchy(document)
    landmarks = landmark_indices(document, 0, parents)
    offsets = {'head': Vector((0, 0, 0)), 'body_bottom': Vector((0, 0, 0)), 'body_top': Vector((0, 0, 0))}
    profile = {'schema_version': 3, 'units': 'metres', 'space': 'prepared actor root',
               'proxy_calibration': {'bone_local_offsets': {name:list(offset) for name,offset in offsets.items()}},
               'attacks': {}, 'locomotion': {}, 'reactions': {}}
    for group, names in [('attacks', {'OVERHEAD':'attack_overhead','LEFT':'attack_left','RIGHT':'attack_right'}),
                         ('locomotion', {'idle':'idle','walk':'walk'}),
                         ('reactions', {'hit_body':'hit_body','hit_head':'hit_head','hit_side':'hit_side'})]:
        for name, clip in names.items():
            animation = next(row for row in document['animations'] if row['name'] == clip)
            tracks, keys = animation_tracks(document, binary, animation, require_attack_range=False)
            times = sorted(keys)
            profile[group][name] = {'clip':clip, 'samples':[profile_sample(document, tracks, t, parents, order, landmarks, offsets) for t in times]}
    return document, binary, profile


class BladeGripMathTests(unittest.TestCase):
    def test_rigid_roundtrip_and_half_turns(self):
        for angle, axis in [(1.7,[.3,-.4,.8]), (math.pi,[1,0,0]), (math.pi,[0,1,0]), (math.pi,[0,0,1])]:
            with self.subTest(angle=angle, axis=axis):
                actual = matrix(angle, axis)
                exported = grip.extract_rigid(actual)
                np.testing.assert_allclose(grip.grip_matrix(exported), actual, atol=2e-12)
                self.assertAlmostEqual(np.linalg.norm(exported['rotation_xyzw']), 1, places=12)

    def test_tiny_float32_scale_is_recorded_as_rigid_approximation(self):
        actual = matrix()
        actual[:3,:3] = actual[:3,:3] @ np.diag([1+5e-7, 1-4e-7, 1+2e-7])
        restored = grip.grip_matrix(grip.extract_rigid(actual))
        np.testing.assert_allclose(restored[:3,:3].T @ restored[:3,:3], np.eye(3), atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(restored[:3,:3]), 1, places=12)

    def test_reflection_singular_scale_shear_and_nonfinite_fail(self):
        invalid = []
        for diagonal in [(-1,1,1),(0,1,1),(1.01,1,1),(.55,.55,.55)]:
            actual = np.eye(4)
            actual[:3,:3] = np.diag(diagonal)
            invalid.append(actual)
        actual = np.eye(4); actual[0,1] = .005; invalid.append(actual)
        for value in [math.nan,math.inf,-math.inf]:
            actual = np.eye(4); actual[0,3] = value; invalid.append(actual)
        invalid += [np.eye(3),np.ones((4,3)),np.diag([1,1,1,2])]
        for actual in invalid:
            with self.subTest(matrix=actual.tolist()):
                with self.assertRaises(ValueError):grip.extract_rigid(actual)

    def test_invalid_required_quaternion_and_fraction_fail(self):
        invalid = [([0,0],[0,0,0,1]),([0,0,0],[0,0,1]),([0,0,0],[0,0,0,0]),
                   ([0,math.inf,0],[0,0,0,1]),([0,0,0],[math.nan,0,0,1]),([0,0,0],[0,0,0,2])]
        for p,q in invalid:
            with self.subTest(position=p,rotation=q):
                with self.assertRaises(ValueError):grip.grip_matrix({'position_m':p,'rotation_xyzw':q})
        valid = grip.extract_rigid(np.eye(4))
        for fraction in [-.01,1.01,math.nan,math.inf]:
            with self.subTest(fraction=fraction):
                with self.assertRaises(ValueError):grip.interpolate_grip(valid,valid,fraction)

    def test_slerp_shortest_arc_and_antipodal_no_fake_spin(self):
        a = grip.extract_rigid(np.eye(4)); b = grip.extract_rigid(matrix(2*math.pi/3))
        b['position_m'] = [2,4,6]
        result = grip.grip_matrix(grip.interpolate_grip(a,b,.5))
        np.testing.assert_allclose(result[:3,:3],rotation([0,1,0],math.pi/3),atol=1e-12)
        np.testing.assert_allclose(result[:3,3],[1,2,3],atol=1e-12)
        opposite = copy.deepcopy(b); opposite['rotation_xyzw'] = (-np.array(b['rotation_xyzw'])).tolist()
        np.testing.assert_allclose(grip.grip_matrix(grip.interpolate_grip(b,opposite,.5)),grip.grip_matrix(b),atol=1e-12)

    def test_endpoint_agreement_does_not_determine_flat_blade_roll(self):
        base, tip = np.array([.022,0,-.129]), np.array([.0532,0,-.849])
        wrong = np.eye(4); wrong[:3,:3] = rotation(tip-base,math.pi/2); wrong[:3,3] = base-wrong[:3,:3]@base
        np.testing.assert_allclose(grip.transform(wrong,np.array([base,tip])),[base,tip],atol=3e-15)
        points = np.array([base+[-.04,0,0],tip+[-.03,.003,0]])
        self.assertGreater(grip.point_reconstruction_error(points,grip.extract_rigid(wrong),points),.05)

    def test_continuous_bound_catches_source_key_excursion_hidden_at_midpoint(self):
        prepared=synthetic_prepared([([0,.3,.7,1],[0,.8,-.8,0])]);points=np.array([[0,0,-prepared.support_radius]])
        a=grip.extract_rigid(prepared.true_matrix('synthetic',0));b=grip.extract_rigid(prepared.true_matrix('synthetic',1))
        mid=grip.point_reconstruction_error(grip.transform(prepared.true_matrix('synthetic',.5),points),grip.interpolate_grip(a,b,.5),points)
        hidden=grip.point_reconstruction_error(grip.transform(prepared.true_matrix('synthetic',.3),points),grip.interpolate_grip(a,b,.3),points)
        bound,spans=prepared.interval_bound('synthetic',0,1,a,b)
        self.assertLess(mid,1e-12);self.assertGreater(hidden,.6);self.assertGreaterEqual(bound,hidden)
        boundaries={row[key] for row in spans for key in ['source_start_s','source_end_s']}
        self.assertTrue({.3,.7}.issubset(boundaries))
        self.assertTrue(all(not(row['source_start_s']<key<row['source_end_s']) for row in spans for key in [.3,.7]))

    def test_nested_rotation_acceleration_keeps_cross_term_and_bounds_short_arc_error(self):
        rate,radius=1.7,.851;prepared=synthetic_prepared([([0,1],[0,rate]),([0,1],[0,rate])],radius)
        speed,accel=prepared.speed_acceleration_bounds('synthetic',0,1)
        self.assertAlmostEqual(speed,2*rate*radius,places=11);self.assertAlmostEqual(accel,(2*rate)**2*radius,places=11)
        a=grip.extract_rigid(prepared.true_matrix('synthetic',0));b=grip.extract_rigid(prepared.true_matrix('synthetic',1));points=np.array([[0,0,-radius]])
        error=grip.point_reconstruction_error(grip.transform(prepared.true_matrix('synthetic',.5),points),grip.interpolate_grip(a,b,.5),points)
        bound,_=prepared.interval_bound('synthetic',0,1,a,b)
        self.assertAlmostEqual(error,2*radius,places=11);self.assertGreaterEqual(bound,error)


class BladeGripProducerTests(unittest.TestCase):
    def test_animation_tracks_decodes_once_and_reuses_cached_arrays(self):
        import attack_profiles
        document,binary=fixtures.actor();prepared=grip.PreparedDocument(document,binary)
        with mock.patch.object(attack_profiles,'animation_tracks',wraps=attack_profiles.animation_tracks) as decoder:
            first=prepared.tracks('attack_overhead')
            snapshots=[(row[2].copy(),row[3].copy()) for row in first]
            second=prepared.tracks('attack_overhead')
            self.assertEqual(decoder.call_count,1)
            self.assertIs(first,second)
            self.assertTrue(first)
            for before,after,snapshot in zip(first,second,snapshots):
                self.assertEqual((before[0],before[1],before[4]),(after[0],after[1],after[4]))
                self.assertIs(before[2],after[2]);self.assertIs(before[3],after[3])
                np.testing.assert_array_equal(after[2],snapshot[0])
                np.testing.assert_array_equal(after[3],snapshot[1])

    def test_synthetic_real_steel_export_is_schema4_and_keeps_seed_subsequence(self):
        document,binary,seed = seed_profile(); original = copy.deepcopy(seed)
        candidate,report = grip.refine_blade_grip_profiles(document,binary,seed,fixtures.common_blade_points(),fixtures.COMMON_SUPPORT_RADIUS_M)
        self.assertEqual(seed,original)
        self.assertEqual(candidate['schema_version'],4)
        self.assertTrue(report['shared_shape_validated'])
        for group in SECTIONS:
            for name,old_clip in seed[group].items():
                new = candidate[group][name]['samples']; by_time = {r['source_seconds']:r for r in new}
                self.assertEqual([r['source_seconds'] for r in new if r['source_seconds'] in {s['source_seconds'] for s in old_clip['samples']}],[r['source_seconds'] for r in old_clip['samples']])
                for old in old_clip['samples']:
                    actual = copy.deepcopy(by_time[old['source_seconds']]); actual.pop('blade_grip')
                    self.assertEqual(actual,old)
                self.assertEqual(new[-1]['blade_grip']['interpolation_error_to_next_m'],0)
                self.assertTrue(all(0<=r['blade_grip']['interpolation_error_to_next_m']<=.001 for r in new))

    def test_missing_grip_wrong_axes_bad_ibm_and_nonrigid_steel_fail(self):
        document,binary,seed = seed_profile(); points = fixtures.common_blade_points()
        missing = copy.deepcopy(document)
        next(node for node in missing['nodes'] if node.get('name')=='Grip')['name']='MissingGrip'
        with self.assertRaises(ValueError):grip.refine_blade_grip_profiles(missing,binary,seed,points,1.)
        with mock.patch.object(grip,'C',np.eye(4)):
            with self.assertRaisesRegex(ValueError,'shape|common Grip'):grip.refine_blade_grip_profiles(document,binary,seed,points,1.)
        wrong = bytearray(binary); accessor=document['accessors'][document['skins'][0]['inverseBindMatrices']]; view=document['bufferViews'][accessor['bufferView']]
        import struct
        struct.pack_into('<f',wrong,view['byteOffset']+3*64+12*4,.02)
        with self.assertRaisesRegex(ValueError,'shape|common Grip'):grip.refine_blade_grip_profiles(document,bytes(wrong),seed,points,1.)
        malformed = copy.deepcopy(document); steel=malformed['meshes'][0]['primitives'][1]; ja=malformed['accessors'][steel['attributes']['JOINTS_0']]; jv=malformed['bufferViews'][ja['bufferView']]
        wrong=bytearray(binary);wrong[jv['byteOffset']]=0
        with self.assertRaisesRegex(ValueError,'R_Hand'):grip.refine_blade_grip_profiles(malformed,bytes(wrong),seed,points,1.)

    def test_missing_or_too_small_support_and_material_scale_fail(self):
        document,binary,seed=seed_profile();points=fixtures.common_blade_points()
        for support in [math.nan,math.inf,-1,.2]:
            with self.subTest(support=support):
                with self.assertRaises(ValueError):grip.refine_blade_grip_profiles(document,binary,seed,points,support)
        broken=copy.deepcopy(document);broken['nodes'][6]['scale']=[-.5,.5,.5]
        with self.assertRaises(ValueError):grip.refine_blade_grip_profiles(broken,binary,seed,points,1.)

    def test_export_requires_geometry_contract_and_has_no_schema3_fallback(self):
        from attack_profiles import export_attack_profiles
        document,binary=fixtures.actor()
        with self.assertRaises(TypeError):export_attack_profiles(document,binary,fixtures.BANK,fixtures.attack_contracts(),fixtures.frozen_contract(),fixtures.coverage_contract())
        exported=export_attack_profiles(document,binary,fixtures.BANK,fixtures.attack_contracts(),fixtures.frozen_contract(),fixtures.coverage_contract(),fixtures.common_blade_points(),fixtures.COMMON_SUPPORT_RADIUS_M)
        self.assertEqual(exported['schema_version'],4)
        self.assertTrue(all('blade_grip' in row for group in SECTIONS for clip in exported[group].values() for row in clip['samples']))


class RequiredWristGateTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((library.HERE/'motion_library.json').read_text())

    def test_required_wrist_missing_and_tampering_still_fail(self):
        solver,recipe=library.prepared_wrist_contract(self.manifest)
        self.assertTrue(callable(solver.apply_prepared_character));self.assertIsInstance(recipe,dict)
        bound=library.production_binding(self.manifest)
        self.assertEqual(bound['prepared_wrist_constraint'],self.manifest['prepared_wrist_constraint'])
        self.assertEqual(bound['blade_grip_sampling'],production_contract.BLADE_GRIP_PROFILE_POLICY)
        for role in ['implementation','recipe']:
            broken=copy.deepcopy(self.manifest);broken['prepared_wrist_constraint'][role]['source_sha256']='0'*64
            self.assertNotEqual(library.canonical_hash(bound),library.canonical_hash(library.production_binding(broken)))
            with self.assertRaisesRegex(ValueError,'constraint identity changed'):library.prepared_wrist_contract(broken)
        broken=copy.deepcopy(self.manifest);broken.pop('prepared_wrist_constraint')
        with self.assertRaisesRegex(ValueError,'requires its pinned prepared wrist constraint'):library.prepared_wrist_contract(broken)
        with self.assertRaises((ValueError,KeyError)):library.production_binding(broken)

    def test_missing_wrist_fails_before_any_publication(self):
        broken=copy.deepcopy(self.manifest);broken.pop('prepared_wrist_constraint')
        # Reuse the existing pipeline's isolated authoring fixture, so no earlier
        # stale authoring hash can hide the required wrist failure.
        import test_attack_bank_pipeline as bank_tests
        fixture=bank_tests.AttackBankContracts('test_frozen_manifest_and_retired_fields');fixture.setUp();self.addCleanup(fixture.doCleanups)
        broken=copy.deepcopy(fixture.manifest);broken.pop('prepared_wrist_constraint')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'manifest.json';path.write_text(json.dumps(broken))
            with mock.patch.object(library,'publish_outputs') as publish:
                with self.assertRaisesRegex(ValueError,'requires its pinned prepared wrist constraint'):library.build_library(path,candidate_dir=Path(folder)/'candidate')
                publish.assert_not_called()




if __name__=='__main__':
    unittest.main(argv=[__file__])
