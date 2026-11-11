"""Hero metal-contact source for normal viewing distances; Root imports build only."""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / 'ArtSource/refinement/effects'))
from build_contact_effects import Effect, Layer
from prepare_rigged_warrior import write_glb


def build(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    effect = Effect('metal_hero_v3', '', .42, 'XY contact plane; +X real tangent, +Z outward normal')
    effect.document.pop('animations')
    effect.document['nodes'][0]['extras'].pop('clip')
    effect.document['nodes'][0]['extras']['driver'] = 'Independent Entity/Opacity particles and contact accents'
    hot = effect.material('White hot steel', (1, .96, .85, 1), (1, .89, .60), roughness=.32)
    warm = effect.material('Tempered gold sparks', (1, .78, .37, 1), (1, .43, .085), roughness=.45)
    cool = effect.material('Cooling steel embers', (.66, .76, .89, 1), (.28, .40, .62), roughness=.58)
    core = Layer()
    for length, width, angle, alpha in ((.140, .0030, 0, 1), (.105, .0023, math.pi / 2, .90),
                                        (.085, .0016, math.pi / 4, .75), (.070, .0015, -math.pi / 4, .67)):
        core.streak((0, 0, .0005), length, width, angle, (1, .96, .81, alpha))
    core.polygon([(-.007, 0, .001), (0, -.007, .001), (.007, 0, .001), (0, .007, .001)], (1, .96, .8, 1))
    effect.node('core_star', core.vertices, core.indices, core.colors, hot)
    rng = random.Random(350411)
    particles = []
    dimensions = []
    tiers = [('hot_near', 12, (.060, .100), (.0050, .0080), (.18, .26), hot),
             ('warm_mid', 12, (.040, .070), (.0035, .0060), (.23, .32), warm),
             ('cool_ember', 8, (.020, .045), (.0030, .0050), (.27, .40), cool)]
    index = 0
    for tier, count, lengths, widths, lives, material in tiers:
        for local in range(count):
            node = f'spark_{index:02d}'
            length = rng.uniform(*lengths)
            width = rng.uniform(*widths)
            lifetime = rng.uniform(*lives)
            # Most streaks follow +T. A smaller counterfan expresses metal fracture.
            tangent = rng.uniform(.85, 1.70) if tier == 'hot_near' else rng.uniform(.42, 1.25)
            if local % 5 == 4:
                tangent *= -.40
            velocity = [tangent, rng.uniform(-.75, .85), rng.uniform(.16, .55)]
            layer = Layer()
            layer.streak((0, 0, 0), length, width / 2, 0, (1, .92 if tier == 'hot_near' else .78, .46, 1))
            if tier == 'hot_near':
                # A thin crossing hot edge adds depth without making a broad billboard.
                layer.streak((0, 0, .0006), length * .78, width * .18, .055, (1, 1, .90, .90))
            effect.node(node, layer.vertices, layer.indices, layer.colors, material)
            particles.append({'node': node, 'type': 'metal_spark', 'tier': tier,
                              'priority': 3 if tier == 'hot_near' else 2 if tier == 'warm_mid' else 1,
                              'shape': 'streak', 'orientation_axis_local': [1, 0, 0], 'orientation_policy': 'velocity',
                              'initial_position_local_m': [0, 0, .002],
                              'initial_velocity_local_mps': velocity,
                              'length_m': length, 'width_m': width, 'lifetime_s': lifetime,
                              'opacity_keys': [[0, 1], [.035, .97], [lifetime * .65, .64], [lifetime, 0]]})
            dimensions.append({'node': node, 'tier': tier, 'length_m': length, 'width_m': width})
            index += 1
    accents = []
    for number, (radius, half_span, width, lifetime) in enumerate(((.13, .65, .0030, .11), (.105, .56, .0018, .085))):
        layer = Layer()
        layer.arc(radius, width, math.pi / 2 - half_span, math.pi / 2 + half_span,
                  (1, .86, .57, .88), depth=.0015, sides=20)
        # Put the middle of the contact arc at the actual contact point, tangent +X.
        layer.vertices = [(x, y - radius, z) for x, y, z in layer.vertices]
        node = f'arc_{number:02d}'
        effect.node(node, layer.vertices, layer.indices, layer.colors, warm)
        accents.append({'node': node, 'type': 'contact_arc', 'initial_position_local_m': [0, 0, .0015],
                        'lifetime_s': lifetime, 'opacity_keys': [[0, .95], [.025, .9], [lifetime, 0]],
                        'requires_real_tangent': True,
                        'scope': 'Short static contact accent oriented by the real tangent; not blade-tip history or runtime ribbon'})
    effect.document['buffers'][0]['byteLength'] = len(effect.binary)
    asset = output_dir / 'metal_hero_v3.glb'
    information = write_glb(asset, effect.document, bytes(effect.binary))
    motion = {'schema': 'contact-particle-motion/v2',
              'mesh_coverage_policy': 'Every mesh must occur exactly once in particles/cores/accents; unknown or undriven layers must reject emission', 'units': 'metres_seconds', 'asset': asset.name,
              'basis': {'local_x': 'real_tangent', 'local_y': 'binormal', 'local_z': 'outward_normal'},
              'gravity_stage_mps2': [0, -9.81, 0], 'anchor_normal_offset_m': .008,
              'runtime_tangent_required': '08 must supply actual projected blade-tip delta. Offline fixed basis is only a source viewing example.',
              'orientation': 'Each spark long axis follows instantaneous Stage velocity; gravity stays Stage -Y',
              'particles': particles, 'accents': accents,
              'cores': [{'node': 'core_star', 'diameter_m': .140, 'opaque_center_diagonal_m': .014, 'requires_real_tangent': False,
                         'initial_position_local_m': [0, 0, .001],
                         'normal': {'lifetime_s': .065, 'opacity_keys': [[0, 1], [.012, .96], [.065, 0]]},
                         'parry': {'lifetime_s': .090, 'opacity_keys': [[0, 1], [.020, 1], [.090, 0]]},
                         'fatal': {'lifetime_s': .150, 'scale': 1.12, 'opacity_keys': [[0, 1], [.035, 1], [.150, 0]],
                                   'clock_owner': 'Root/08 select fatal profile and control event/presentation clock'}}]}
    motion_path = output_dir / 'motion.json'
    motion_path.write_text(json.dumps(motion, ensure_ascii=False, indent=2) + '\n')
    metrics = {**information, 'particle_count': 32, 'mesh_count': len(effect.document['meshes']),
               'triangles': effect.triangles, 'textures': 0, 'animations': 0, 'extensions': 0,
               'core_span_m': .140, 'normal_core_lifetime_s': .065, 'parry_core_lifetime_s': .090,
               'tiers': [{'name': tier, 'count': count, 'length_range_m': lengths, 'width_range_m': widths, 'life_range_s': lives}
                         for tier, count, lengths, widths, lives, material in tiers],
               'particle_dimensions': dimensions, 'contact_arc_count': 2,
               'maximum_entity_count_per_contact': 35,
               'budget_note': '35 individually faded mesh Entities per full contact. 08 must enforce simultaneous-contact/particle budgets; source geometry budget alone does not prove XR performance.',
               'source': 'Original procedural static geometry; no paid generation, no runtime/source overwrite'}
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
    return {'asset': str(asset), 'motion': str(motion_path), 'metrics': metrics}
