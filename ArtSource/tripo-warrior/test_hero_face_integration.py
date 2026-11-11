"""Offline coverage for multiple body primitives and explicit NPC dao input.

The fixture partitions a published body primitive into eight triangle groups,
each with a copied material. It preserves the real 78-joint skin and ten clips.
Actual grafted-head validation belongs to its separate candidate review products.
"""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_character_library as library
import prepare_rigged_warrior as producer


WEAPON = library.HERE.parent / 'refinement/weapon/stage2/dao_refined.glb'
WEAPON_SHA = '4834a555d70f80151bbe19358c0a94c11e1c3f76ab2e501bf6e70c2860bcf452'


class MultiPrimitiveWeaponTests(unittest.TestCase):
    def test_cross_directory_generation_publishes_together_and_rolls_back_on_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            library_path = root / 'library/base.glb'
            runtime_path = root / 'app/models/opponents/base.glb'
            player_path = root / 'app/models/dao_grip.glb'
            for path in (library_path, runtime_path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'old-generation')
            generation = ((library_path, b'new-model'), (player_path, b'new-player'), (runtime_path, b'new-model'))
            replace = Path.replace
            calls = []

            def fail_runtime_once(source, destination):
                calls.append(destination)
                if destination == runtime_path and calls.count(destination) == 1:
                    raise OSError('injected runtime publication failure')
                return replace(source, destination)

            with patch.object(Path, 'replace', fail_runtime_once):
                with self.assertRaisesRegex(OSError, 'injected'):
                    producer.publish_outputs(generation)
            self.assertEqual(library_path.read_bytes(), b'old-generation')
            self.assertEqual(runtime_path.read_bytes(), b'old-generation')
            self.assertFalse(player_path.exists())
            producer.publish_outputs(generation)
            self.assertEqual(library_path.read_bytes(), runtime_path.read_bytes())
            self.assertEqual(player_path.read_bytes(), b'new-player')

    def body_and_mount(self):
        published = library.HERE / 'library'
        model, binary = producer.read_glb(published / 'base.glb')
        body = copy.deepcopy(model)
        mesh_node = next(node for node in body['nodes'] if 'mesh' in node)
        mesh = body['meshes'][mesh_node['mesh']]
        body_indices = mesh['extras']['body_primitive_indices']
        self.assertTrue(body_indices)
        # Keep one real body primitive. Published dao draw references are excluded
        # before partitioning, while real buffers, nodes, skin and clips are retained.
        mesh['primitives'] = [mesh['primitives'][body_indices[0]]]
        original = mesh['primitives'][0]
        indices = body['accessors'][original['indices']]
        index_width = {5121: 1, 5123: 2, 5125: 4}[indices['componentType']]
        view = body['bufferViews'][indices['bufferView']]
        self.assertEqual(original.get('mode', 4), 4)
        self.assertEqual(indices['type'], 'SCALAR')
        self.assertEqual(indices['count'] % 3, 0)
        self.assertEqual(view.get('byteStride', index_width), index_width)
        triangle_count = indices['count'] // 3
        self.assertGreaterEqual(triangle_count, 8)
        primitives = []
        for part in range(8):
            start = (part * triangle_count // 8) * 3
            end = ((part + 1) * triangle_count // 8) * 3
            section = copy.deepcopy(indices)
            section['byteOffset'] = indices.get('byteOffset', 0) + start * index_width
            section['count'] = end - start
            section.pop('min', None)
            section.pop('max', None)
            material = copy.deepcopy(body['materials'][original['material']])
            material['name'] = 'tripo_fixture_part_' + str(part)
            primitive = copy.deepcopy(original)
            primitive['indices'] = len(body['accessors'])
            primitive['material'] = len(body['materials'])
            body['accessors'].append(section)
            body['materials'].append(material)
            primitives.append(primitive)
        mesh['primitives'] = primitives
        mesh['extras']['body_primitive_indices'] = list(range(8))
        mesh['extras']['weapon_primitive_indices'] = []
        mount = producer.local_matrix(next(node for node in model['nodes'] if node.get('name') == 'HandGrip_R'))
        hand = next(i for i, node in enumerate(body['nodes']) if node.get('name') == 'R_Hand')
        return body, binary, hand, mount

    def test_eight_body_primitives_and_new_weapon_share_the_unchanged_skin(self):
        document, binary, hand, mount = self.body_and_mount()
        original = copy.deepcopy(document)
        signatures = [producer.animation_signature(document, binary, clip) for clip in document['animations']]
        combined, _, binding = producer.append_dao(document, binary, hand, mount, WEAPON, WEAPON_SHA)
        self.assertEqual(binding['body_primitive_indices'], list(range(8)))
        self.assertEqual(binding['weapon_primitive_indices'], list(range(8, 23)))
        self.assertEqual(binding['source_sha256'], WEAPON_SHA)
        self.assertEqual(document['skins'], original['skins'])
        self.assertEqual(document['animations'], original['animations'])
        self.assertEqual(document['meshes'][0]['primitives'][:8], original['meshes'][0]['primitives'])
        self.assertEqual(combined[:len(binary)], binary)
        self.assertEqual(signatures, [producer.animation_signature(document, combined, clip)
                                      for clip in document['animations']])
        for primitive in document['meshes'][0]['primitives'][:8]:
            self.assertTrue(document['materials'][primitive['material']]['name'].startswith('tripo_'))
        canonical, _ = producer.read_glb(producer.DAO_SOURCE)
        weapon, _ = producer.read_glb(WEAPON)
        for name in ('Grip', 'Blade_Base', 'Blade_Tip'):
            self.assertEqual(next(n for n in weapon['nodes'] if n.get('name') == name),
                             next(n for n in canonical['nodes'] if n.get('name') == name))

    def test_wrong_weapon_hash_and_missing_normal_uv_are_rejected(self):
        document, binary, hand, mount = self.body_and_mount()
        with self.assertRaisesRegex(ValueError, 'dao source hash'):
            producer.append_dao(copy.deepcopy(document), binary, hand, mount, WEAPON, '0' * 64)
        weapon, payload = producer.read_glb(WEAPON)
        primitive = next(p for mesh in weapon['meshes'] for p in mesh['primitives']
                         if weapon['materials'][p['material']].get('normalTexture') is not None)
        texture = weapon['materials'][primitive['material']]['normalTexture']
        del primitive['attributes']['TEXCOORD_' + str(texture.get('texCoord', 0))]
        damaged = producer.encode_glb(weapon, payload)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'missing_uv.glb'
            path.write_bytes(damaged)
            with self.assertRaisesRegex(ValueError, 'normal/UV'):
                producer.append_dao(copy.deepcopy(document), binary, hand, mount, path,
                                    hashlib.sha256(damaged).hexdigest())

    def test_weapon_identity_is_part_of_the_production_review_binding(self):
        manifest = json.loads((library.HERE / 'motion_library.json').read_text())
        manifest['weapon_source'] = {'source': '../dao/dao_study.glb',
                                      'source_sha256': '0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616'}
        original = library.production_binding(manifest)
        manifest['weapon_source'] = {'source': str(WEAPON), 'source_sha256': WEAPON_SHA}
        changed = library.production_binding(manifest)
        self.assertNotEqual(library.canonical_hash(original), library.canonical_hash(changed))
        self.assertEqual(changed['weapon_source']['source_sha256'], WEAPON_SHA)
        del manifest['weapon_source']
        with self.assertRaisesRegex(ValueError, 'explicit weapon_source'):
            library.validate_manifest(manifest)
        with self.assertRaises(KeyError):
            library.production_binding(manifest)


if __name__ == '__main__':
    unittest.main(argv=[__file__])
