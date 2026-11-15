"""Exercise this independent audit against real data and controlled real-data faults."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[4]
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location('left_hand_math_review', BASE / 'left-rebuild-math-review.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def clone(asset):
    return AUDIT.Asset(copy.deepcopy(asset.doc), asset.binary)


def change_component(asset, index, row, component, value):
    data = bytearray(asset.binary)
    accessor = asset.doc['accessors'][index]
    view = asset.doc['bufferViews'][accessor['bufferView']]
    dtype = np.dtype(AUDIT.TYPES[accessor['componentType']])
    width = AUDIT.WIDTHS[accessor['type']]
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    offset += row * view.get('byteStride', dtype.itemsize * width) + component * dtype.itemsize
    encoded = np.asarray([value], dtype=dtype).tobytes()
    data[offset:offset + dtype.itemsize] = encoded
    asset.binary = bytes(data)


def add_tangents(asset):
    primitive = asset.doc['meshes'][0]['primitives'][0]
    normal = asset.accessor(primitive['attributes']['NORMAL']).astype(float)
    reference = np.tile([0., 1., 0.], (len(normal), 1))
    parallel = np.abs(normal[:, 1]) > .9
    reference[parallel] = [1., 0., 0.]
    tangent = AUDIT.unit(np.cross(reference, normal))
    return np.column_stack((tangent, np.ones(len(tangent)))).astype('<f4')


def append_tangent(asset, array):
    data = bytearray(asset.binary)
    data.extend(b'\0' * (-len(data) % 4))
    view = len(asset.doc['bufferViews'])
    payload = np.asarray(array, dtype='<f4').tobytes()
    asset.doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(data), 'byteLength': len(payload)})
    data.extend(payload)
    asset.doc['buffers'][0]['byteLength'] = len(data)
    asset.binary = bytes(data)
    index = len(asset.doc['accessors'])
    asset.doc['accessors'].append({'bufferView': view, 'componentType': 5126, 'type': 'VEC4', 'count': len(array)})
    asset.doc['meshes'][0]['primitives'][0]['attributes']['TANGENT'] = index
    return index


class ReflectionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.right = AUDIT.Asset.load(REPO / 'app/src/main/assets/models/player_hands/right_hand.glb')
        cls.left = AUDIT.Asset.load(BASE / 'left-rebuild/left_hand_rebuilt.glb')

    def test_real_pair_all_vertices_and_intermediate_poses(self):
        report = AUDIT.audit(self.right, self.left)
        self.assertEqual(report['status'], 'PASS_COMMON_GRIP_REFLECTION_MATH')
        self.assertEqual(report['joint_palette_count'], 78)
        self.assertEqual((report['vertices'], report['triangles']), (3021, 4936))
        self.assertGreaterEqual(len(report['sampling']), 9)
        self.assertTrue(all(row['source_right_chirality'] * row['candidate_left_chirality'] < 0
                            for row in report['sampling']))

    def test_wrong_triangle_winding_is_rejected(self):
        broken = clone(self.left)
        index = broken.doc['meshes'][0]['primitives'][0]['indices']
        values = broken.accessor(index, False).ravel()
        change_component(broken, index, 1, 0, values[2])
        change_component(broken, index, 2, 0, values[1])
        with self.assertRaisesRegex(AUDIT.ReviewError, 'triangle winding'):
            AUDIT.audit(self.right, broken)

    def test_real_used_joint_ibm_translation_fault_is_rejected(self):
        broken = clone(self.left)
        primitive = broken.doc['meshes'][0]['primitives'][0]
        weights = broken.accessor(primitive['attributes']['WEIGHTS_0'])
        joints = broken.accessor(primitive['attributes']['JOINTS_0'], False)
        joint = int(joints[0, int(np.argmax(weights[0]))])
        index = broken.doc['skins'][0]['inverseBindMatrices']
        # glTF MAT4 is column-major; component12 is the x translation.
        before = broken.accessor(index)[joint, 12]
        change_component(broken, index, joint, 12, before + .01)
        with self.assertRaisesRegex(AUDIT.ReviewError, 'IBM conjugation'):
            AUDIT.audit(self.right, broken)

    def test_leftover_wrist_compensation_is_rejected(self):
        broken = clone(self.left)
        node = next(n for n in broken.doc['nodes'] if n.get('name') == 'SourceHandRigidConversion')
        matrix = node['matrix']
        matrix[12] += .076593
        with self.assertRaisesRegex(AUDIT.ReviewError, 'Node .* conjugation'):
            AUDIT.audit(self.right, broken)

    def test_extra_compensation_frame_is_rejected(self):
        broken = clone(self.left)
        root = broken.doc['scenes'][broken.doc['scene']]['nodes'][0]
        broken.doc['nodes'].append({'name': 'LegacyLeftWristC', 'children': [root], 'translation': [.1, 0, 0]})
        broken.doc['scenes'][broken.doc['scene']]['nodes'] = [len(broken.doc['nodes'])-1]
        with self.assertRaisesRegex(AUDIT.ReviewError, 'Node count'):
            AUDIT.audit(self.right, broken)

    def test_nonidentity_outer_root_is_rejected(self):
        broken = clone(self.left)
        root = broken.doc['scenes'][broken.doc['scene']]['nodes'][0]
        broken.doc['nodes'][root]['translation'] = [.001, 0, 0]
        with self.assertRaisesRegex(AUDIT.ReviewError, 'outer root must be identity'):
            AUDIT.audit(self.right, broken)

    def test_one_way_bone_rename_duplicate_is_rejected(self):
        broken = clone(self.left)
        broken.doc['nodes'][43]['name'] = 'L_Hand'  # original unused L_Hand must have become R_Hand
        with self.assertRaisesRegex(AUDIT.ReviewError, 'duplicate node names'):
            AUDIT.audit(self.right, broken)

    def test_aabb_drift_is_rejected(self):
        broken = clone(self.left)
        index = broken.doc['meshes'][0]['primitives'][0]['attributes']['POSITION']
        broken.doc['accessors'][index]['min'][0] += .01
        with self.assertRaisesRegex(AUDIT.ReviewError, 'accessor .* min'):
            AUDIT.audit(self.right, broken)

    def test_image_encoding_label_drift_is_rejected(self):
        broken = clone(self.left)
        broken.doc['images'][0]['mimeType'] = 'image/png'
        with self.assertRaisesRegex(AUDIT.ReviewError, 'Image metadata'):
            AUDIT.audit(self.right, broken)

    def test_zero_or_negative_bone_scale_is_rejected(self):
        broken = clone(self.left)
        broken.doc['nodes'][67]['scale'] = [-1, 1, 1]
        with self.assertRaisesRegex(AUDIT.ReviewError, 'negative/zero scale'):
            AUDIT.audit(self.right, broken)

    def test_asymmetric_geometry_fault_is_rejected(self):
        broken = clone(self.left)
        index = broken.doc['meshes'][0]['primitives'][0]['attributes']['POSITION']
        value = broken.accessor(index)[100, 0]
        change_component(broken, index, 100, 0, value + .002)
        with self.assertRaisesRegex(AUDIT.ReviewError, 'POSITION'):
            AUDIT.audit(self.right, broken)

    def test_unmodeled_morph_target_is_rejected(self):
        broken = clone(self.left)
        broken.doc['meshes'][0]['primitives'][0]['targets'] = [{'POSITION': 0}]
        with self.assertRaisesRegex(AUDIT.ReviewError, 'morph targets'):
            AUDIT.audit(self.right, broken)

    def test_synthetic_tangent_basis_on_real_skinning_passes(self):
        right, left = clone(self.right), clone(self.left)
        rtangent = add_tangents(right)
        ltangent = rtangent.copy()
        ltangent[:, [0, 3]] *= -1
        append_tangent(right, rtangent)
        append_tangent(left, ltangent)
        report = AUDIT.audit(right, left)
        self.assertEqual(report['tangent_scope'], 'present and checked')
        self.assertTrue(all(row['primitives'][0]['tangent_error'] < 1e-9 for row in report['sampling']))

    def test_missing_tangent_w_flip_is_rejected(self):
        right, left = clone(self.right), clone(self.left)
        rtangent = add_tangents(right)
        wrong = rtangent.copy()
        wrong[:, 0] *= -1
        append_tangent(right, rtangent)
        append_tangent(left, wrong)
        with self.assertRaisesRegex(AUDIT.ReviewError, 'TANGENT'):
            AUDIT.audit(right, left)


if __name__ == '__main__':
    unittest.main(verbosity=2)
