"""Pure, shared production identity for model publication and typed-data publication.

Policy values live here so consumers cannot approve a different projection without
changing the actual model producer. This module intentionally imports no Blender APIs.
"""
import hashlib
import json


LEFT_HAND_POSES = {
    'turn': ('loose turning guard', ((0.0, 0.20), (0.5, 0.28), (1.0, 0.20))),
    'hit_body': ('protect the body', ((0.0, 0.18), (0.22, 0.52), (0.6, 0.32), (1.0, 0.18))),
    'hit_head': ('open protective palm', ((0.0, 0.18), (0.22, 0.10), (0.55, 0.16), (1.0, 0.18))),
    'hit_side': ('soft protective curl', ((0.0, 0.18), (0.22, 0.38), (0.6, 0.26), (1.0, 0.18))),
    'fall': ('release the empty hand', ((0.0, 0.18), (0.4, 0.12), (1.0, 0.04))),
}


HAND_POLICY = {'version': 1, 'right': 'target native grip sample, then right-only offsets once',
               'movement_left': LEFT_HAND_POSES, 'movement_left_thumb_multiplier': .55,
               'attack_left': 'authored dynamic source transferred by world-rest delta',
               'locomotion_left': 'frozen canonical source transferred by world-rest delta'}


GROUNDING_POLICY = {
    'version': 2,
    'method': 'one constant prepared +Y BoneRoot translation from target idle at source zero',
    'target_plane_metres': -.028,
    'region': 'body vertices with total same-side Foot/Toe skin weight greater than 0.5',
    'canonical_clip': 'idle',
    'canonical_source_seconds': 0.0,
    'scope': 'idle, walk and three attacks share one target guard shift; no per-frame grounding or IK',
    'residual_policy': 'measure keys and midpoints without modifying authored relative foot heights',
    'runtime_entity_lift_metres': .028,
    'runtime_entity_lift_application_count': 1,
}

ANIMATION_SAMPLING_POLICY = {
    'version': 1,
    'rotation': 'normalize the stored quaternion at every exact key; SLERP only strictly inside nonconstant LINEAR spans',
    'translation_and_scale': 'preserve exact keys and authored LINEAR or STEP interpolation',
}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def production_binding(manifest):
    return {'schema_version': 3, 'motion_source': manifest['motion_source'],
            'locomotion_source': manifest['locomotion_source'],
            'body_coverage_calibration': manifest['body_coverage_calibration'],
            'runtime_texture_encoding': manifest['runtime_texture_encoding'],
            'player_weapon_source': manifest['player_weapon_source'],
            'attack_source': manifest['attack_source'], 'hand_policy': HAND_POLICY,
            'canonical_root_grounding': GROUNDING_POLICY,
            'animation_sampling': ANIMATION_SAMPLING_POLICY,
            'weapon_source': manifest['weapon_source'],
            'characters': [{key: character.get(key) for key in
                            ('id', 'name', 'source', 'source_sha256', 'grip_source',
                             'height_metres', 'output', 'grip_frame', 'finger_rotation_offsets')}
                           for character in manifest['characters']]}
