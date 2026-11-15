"""Real-asset controls and RAM-only negative fixtures; no asset writes."""
import copy
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_left_rebuild as v


def replace_accessor(document, binary, index, values):
    packed = bytearray(binary)
    spec = document['accessors'][index]
    view = document['bufferViews'][spec['bufferView']]
    old = v.h.values(document, binary, index)
    values = np.asarray(values, dtype=old.dtype).reshape(old.shape)
    stride = view.get('byteStride', old.shape[1]*old.dtype.itemsize)
    start = view.get('byteOffset', 0)+spec.get('byteOffset', 0)
    for i, row in enumerate(values):
        packed[start+i*stride:start+i*stride+row.nbytes] = row.tobytes()
    return bytes(packed)


def append_accessor(document, binary, values, kind):
    values = np.asarray(values, dtype='<f4')
    packed = bytearray(binary)
    packed.extend(b'\0'*(-len(packed) % 4))
    document['bufferViews'].append({'buffer': 0, 'byteOffset': len(packed), 'byteLength': values.nbytes})
    document['accessors'].append({'bufferView': len(document['bufferViews'])-1, 'componentType': 5126, 'type': kind, 'count': len(values)})
    packed.extend(values.tobytes())
    document['buffers'][0]['byteLength'] = len(packed)
    return len(document['accessors'])-1, bytes(packed)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.sb = v.h.read(v.SOURCE)
        cls.left, cls.lb = v.h.read(v.CANDIDATE)

    def run_check(self, left=None, binary=None, source=None, sb=None):
        return v.verify_contract(self.source if source is None else source, self.sb if sb is None else sb,
                                 self.left if left is None else left, self.lb if binary is None else binary)

    def reject(self, left=None, binary=None, match=None):
        with self.assertRaisesRegex(ValueError, match or '.'):
            self.run_check(left, binary)

    def changed_data(self, semantic, operation):
        index = self.left['meshes'][0]['primitives'][0]['attributes'][semantic]
        values = v.h.values(self.left, self.lb, index)
        operation(values)
        return replace_accessor(self.left, self.lb, index, values)

    def test_actual_pinned_common_Grip(self):
        for role, path in [('source', v.SOURCE), ('candidate', v.CANDIDATE), ('dao', v.DAO)]:
            self.assertEqual(v.h.digest(path), v.PINS[role])
        report = self.run_check()
        self.assertEqual(report['full_palette_joints'], 78)
        self.assertEqual([r['time'] for r in report['states']], ['default', 0., .5, 1.])
        self.assertTrue(report['passed'])

    def test_shifted_root_rejected(self):
        d = copy.deepcopy(self.left)
        d['nodes'][d['scenes'][0]['nodes'][0]]['translation'] = [.01, 0, 0]
        self.reject(d, match='outer identity')

    def test_legacy_derived_marker_rejected(self):
        d = copy.deepcopy(self.left)
        d['nodes'][83]['name'] = 'DerivedHandGrip_L'
        self.reject(d, match='legacy derived')

    def test_extra_frame_rejected(self):
        d = copy.deepcopy(self.left)
        d['nodes'].append({'name': 'LegacyCorrectionFrame'})
        self.reject(d, match='count')

    def test_palette_pruning_rejected(self):
        d = copy.deepcopy(self.left)
        d['skins'][0]['joints'].pop()
        self.reject(d, match='78')

    def test_palette_reordering_rejected(self):
        d = copy.deepcopy(self.left)
        a = d['skins'][0]['joints']
        a[0], a[1] = a[1], a[0]
        self.reject(d, match='palette order')

    def test_one_way_rename_duplicate_rejected(self):
        d = copy.deepcopy(self.left)
        d['nodes'][0]['name'] = d['nodes'][10]['name']
        self.reject(d, match='duplicate')

    def test_wrong_side_name_rejected(self):
        d = copy.deepcopy(self.left)
        d['nodes'][67]['name'] = 'WrongHand'
        self.reject(d, match='bilateral')

    def test_negative_scale_rejected(self):
        d = copy.deepcopy(self.left)
        d['nodes'][0]['scale'] = [-1, 1, 1]
        self.reject(d, match='scale')

    def test_wrong_quaternion_conjugation_rejected(self):
        d = copy.deepcopy(self.left)
        index = next(i for i, n in enumerate(self.source['nodes']) if n.get('rotation') and not np.allclose(n['rotation'], [0, 0, 0, 1]))
        d['nodes'][index]['rotation'] = self.source['nodes'][index]['rotation']
        self.reject(d, match='local S M S')

    def test_unmirrored_position_rejected(self):
        self.reject(binary=self.changed_data('POSITION', lambda x: x.__setitem__((slice(None), 0), -x[:, 0])), match='POSITION')

    def test_unmirrored_normal_rejected(self):
        self.reject(binary=self.changed_data('NORMAL', lambda x: x.__setitem__((slice(None), 0), -x[:, 0])), match='NORMAL')

    def test_unchanged_uv_rejected(self):
        self.reject(binary=self.changed_data('TEXCOORD_0', lambda x: x.__setitem__((0, 0), x[0, 0]+.01)), match='TEXCOORD')

    def test_changed_weight_rejected(self):
        self.reject(binary=self.changed_data('WEIGHTS_0', lambda x: x.__setitem__((0, 0), x[0, 0]+.01)), match='WEIGHTS')

    def test_changed_joint_rejected(self):
        self.reject(binary=self.changed_data('JOINTS_0', lambda x: x.__setitem__((0, 0), (x[0, 0]+1) % 78)), match='JOINTS')

    def test_original_winding_rejected(self):
        p = self.left['meshes'][0]['primitives'][0]
        values = v.h.values(self.left, self.lb, p['indices']).reshape(-1, 3)
        self.reject(binary=replace_accessor(self.left, self.lb, p['indices'], values[:, [0, 2, 1]]), match='winding')

    def test_unconjugated_IBM_rejected(self):
        old = self.source['skins'][0]['inverseBindMatrices']
        new = self.left['skins'][0]['inverseBindMatrices']
        self.reject(binary=replace_accessor(self.left, self.lb, new, v.h.values(self.source, self.sb, old)), match='IBM')

    def test_wrong_animation_rejected(self):
        sampler = self.left['animations'][0]['samplers'][0]
        values = v.h.values(self.left, self.lb, sampler['output'])
        values[-1] = [0, 0, 0, 1]
        self.reject(binary=replace_accessor(self.left, self.lb, sampler['output'], values), match='animation output')

    def test_KTX_byte_mutation_rejected(self):
        d = self.left
        view = d['bufferViews'][d['images'][0]['bufferView']]
        packed = bytearray(self.lb)
        packed[view.get('byteOffset', 0)+80] ^= 1
        self.reject(binary=bytes(packed), match='image bytes')

    def tangent_fixture(self):
        source, left = copy.deepcopy(self.source), copy.deepcopy(self.left)
        count = source['accessors'][source['meshes'][0]['primitives'][0]['attributes']['POSITION']]['count']
        tangents = np.tile(np.array([.6, .8, 0., 1.], dtype='<f4'), (count, 1))
        tangents[1::2, 3] = -1
        li = tangents * [-1, 1, 1, -1]
        si, sb = append_accessor(source, self.sb, tangents, 'VEC4')
        ti, lb = append_accessor(left, self.lb, li, 'VEC4')
        source['meshes'][0]['primitives'][0]['attributes']['TANGENT'] = si
        left['meshes'][0]['primitives'][0]['attributes']['TANGENT'] = ti
        return source, sb, left, lb, ti

    def test_synthetic_tangent_xyz_w_and_bitangent(self):
        source, sb, left, lb, _ = self.tangent_fixture()
        report = self.run_check(left, lb, source, sb)
        self.assertEqual(report['TANGENT_primitives_in_actual_source'], 1)
        n, t, w = np.array([0., 0., 1.]), np.array([.6, .8, 0.]), -1.
        reflection = v.S[:3, :3]
        np.testing.assert_allclose(np.cross(reflection@n, reflection@t)*(-w), reflection@(np.cross(n, t)*w))

    def test_synthetic_missing_tangent_w_flip_rejected(self):
        source, sb, left, lb, ti = self.tangent_fixture()
        values = v.h.values(left, lb, ti)
        values[:, 3] *= -1
        with self.assertRaisesRegex(ValueError, 'TANGENT'):
            self.run_check(left, replace_accessor(left, lb, ti, values), source, sb)

    def test_synthetic_missing_tangent_x_flip_rejected(self):
        source, sb, left, lb, ti = self.tangent_fixture()
        values = v.h.values(left, lb, ti)
        values[:, 0] *= -1
        with self.assertRaisesRegex(ValueError, 'TANGENT'):
            self.run_check(left, replace_accessor(left, lb, ti, values), source, sb)


class GeometryControls(unittest.TestCase):
    def test_actual_DAO_topology_controls_solid_vs_surface(self):
        components = v.actual_dao_components()
        self.assertEqual(len(components), 13)
        self.assertTrue(components['Handle core']['closed'])
        self.assertFalse(components['Grip | cord wrap']['closed'])
        self.assertEqual(components['Grip | cord wrap']['topology']['open_edges'], 1442)
        for name in ('Blade collar', 'Grip ferrule', 'Guard pin 1', 'Guard pin 2',
                     'Guard | flared oval', 'Guard | outer rim', 'Pommel ring', 'Pommel | brass'):
            self.assertTrue(components[name]['closed'], name)
        for name in ('Blade', 'Blade | asymmetric wear', 'Blade | shallow fuller'):
            self.assertFalse(components[name]['closed'], name)

    def test_closed_tetrahedron_inside_outside(self):
        points = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        faces = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])
        topology, _, _ = v.h.edge_topology(points, faces)
        self.assertEqual(topology['open_edges'], 0)
        data = v.solid_distances(np.array([[.1, .1, .1], [2, 0, 0]]), points[faces], True)
        self.assertEqual(data['inside_sample_ids'], [0])
        self.assertAlmostEqual(data['maximum_sampled_penetration_mm'], 100)

    def test_open_surface_never_claims_volume(self):
        triangle = np.array([[[0., 0, 0], [1, 0, 0], [0, 1, 0]]])
        data = v.solid_distances(np.array([[.1, .1, -.1]]), triangle, False)
        self.assertFalse(data['signed_volume_test'])
        self.assertEqual(data['inside_samples'], 0)
        self.assertAlmostEqual(v.minimum_sample_gap(np.array([[.1, .1, -.1], [2., 0, 0]]), triangle), 100)

    def test_nonadjacent_triangle_crossing_and_adjacent_UV_seam(self):
        points = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [.2, .2, -1], [.2, .2, 1], [.8, .2, 0]])
        faces = np.array([[0, 1, 2], [3, 4, 5]])
        self.assertEqual(v.crossing_pairs(points[faces], points[faces], True, faces, np.arange(6)), [[0, 1]])
        # A candidate coincidence does not alter this fixed source adjacency.
        weld = np.arange(6)
        weld[3] = weld[0]
        self.assertEqual(v.crossing_pairs(points[faces], points[faces], True, faces, weld), [])

    def test_coplanar_positive_area_overlap(self):
        first = np.array([[[0., 0, 0], [1, 0, 0], [0, 1, 0]]])
        second = first + [.1, .1, 0]
        self.assertEqual(v.crossing_pairs(first, second), [[0, 0]])
        self.assertEqual(v.crossing_pairs(first, second+[0, 0, .01]), [])

    def test_actual_anatomical_chirality_is_opposite(self):
        a, ab = v.h.read(v.SOURCE)
        b, bb = v.h.read(v.CANDIDATE)
        right, left = v.anatomy.inspect_asset(a, ab, 'R'), v.anatomy.inspect_asset(b, bb, 'L')
        self.assertGreater(right['surface'][0]['signed_chirality'], .9)
        self.assertLess(left['surface'][0]['signed_chirality'], -.9)
        self.assertAlmostEqual(right['surface'][0]['signed_chirality'], -left['surface'][0]['signed_chirality'])


if __name__ == '__main__': unittest.main()
