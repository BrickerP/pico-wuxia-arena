"""Original independent metal-contact particles. Imported by the Root builder only."""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / 'ArtSource/refinement/effects'))
from build_contact_effects import Effect, Layer
from prepare_rigged_warrior import write_glb


def build(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    effect = Effect('metal_contact_polish', '', .30, 'XY contact plane, X tangent, +Z outward normal')
    effect.document.pop('animations')
    effect.document['nodes'][0]['extras'].pop('clip')
    effect.document['nodes'][0]['extras']['driver'] = 'Independent Entity particles; Stage gravity'
    star_material = effect.material('Ivory hot steel core', (1, 1, 1, 1), (.90, .78, .50), roughness=.55)
    spark_material = effect.material('Tempered orange sparks', (1, 1, 1, 1), (1, .43, .065), roughness=.5)
    core = Layer()
    core.streak((0, 0, 0), .070, .0012, 0, (1, .96, .81, 1))
    core.streak((0, 0, .0002), .043, .0011, math.pi / 2, (1, .94, .74, .92))
    core.streak((0, 0, .0004), .037, .00075, math.pi / 4, (1, .85, .58, .8))
    core.polygon([(-.0035, 0, .0006), (0, -.0035, .0006), (.0035, 0, .0006), (0, .0035, .0006)], (1, .96, .8, .96))
    effect.node('core_star', core.vertices, core.indices, core.colors, star_material)
    randomizer = random.Random(31904)
    particles = []
    dimensions = []
    for index in range(12):
        node = f'spark_{index:02d}'
        length = randomizer.uniform(.012, .028)
        width = randomizer.uniform(.0020, .0028)
        lifetime = .180 + index * .010
        velocity = [randomizer.uniform(.30, .96), randomizer.uniform(-.38, .44), randomizer.uniform(.10, .34)]
        layer = Layer()
        layer.streak((0, 0, 0), length, width / 2, 0, (1, randomizer.uniform(.70, .93), .36, 1))
        effect.node(node, layer.vertices, layer.indices, layer.colors, spark_material)
        particles.append({'node': node, 'type': 'metal_spark',
                          'initial_position_local_m': [0, 0, .002],
                          'initial_velocity_local_mps': velocity,
                          'length_m': length, 'width_m': width, 'cross_section_m': width,
                          'lifetime_s': lifetime,
                          'opacity_keys': [[0, 1], [.025, .92], [lifetime * .65, .52], [lifetime, 0]]})
        dimensions.append({'node': node, 'length_m': length, 'width_m': width})
    effect.document['buffers'][0]['byteLength'] = len(effect.binary)
    asset = output_dir / 'metal_contact_polish.glb'
    info = write_glb(asset, effect.document, bytes(effect.binary))
    motion = {'schema': 'contact-particle-motion/v1', 'units': 'metres_seconds',
              'asset': asset.name, 'basis': {'local_x': 'tangent', 'local_y': 'binormal', 'local_z': 'outward_normal'},
              'gravity_stage_mps2': [0, -9.81, 0],
              'trajectory': 'p_stage = contact_point + T*p.x + B*p.y + N*p.z + velocity_stage*t + 0.5*gravity_stage*t^2',
              'velocity_basis': 'initial_velocity_local_mps in [T,B,N]; gravity is never rotated as local Y',
              'orientation': 'Local mesh X follows instantaneous Stage velocity; width remains the authored cross-section',
              'normal_offset_owner': 'Root anchor adds the shared surface offset; positions below are relative to it',
              'runtime_tangent_required': 'CombatImpact currently lacks tangent. Root must supply projected real blade-tip delta; this asset is not a runtime trajectory integration.',
              'particles': particles,
              'cores': [{'node': 'core_star', 'diameter_m': .070,
                         'initial_position_local_m': [0, 0, .001],
                         'normal': {'lifetime_s': .065, 'opacity_keys': [[0, 1], [.012, .88], [.065, 0]]},
                         'parry': {'lifetime_s': .090, 'opacity_keys': [[0, 1], [.018, .94], [.090, 0]]}}]}
    motion_path = output_dir / 'motion.json'
    motion_path.write_text(json.dumps(motion, indent=2) + '\n')
    metrics = {**info, 'node_names': [node['name'] for node in effect.document['nodes']],
               'mesh_count': len(effect.document['meshes']), 'particle_count': len(particles),
               'triangles': effect.triangles, 'animation_count': 0,
               'materials': 'PBR emissive, vertex alpha, BLEND, double-sided; no extensions',
               'core_max_diameter_m': .070, 'normal_core_lifetime_s': .065, 'parry_core_lifetime_s': .090,
               'particle_dimensions': dimensions,
               'lifetime_range_s': [min(p['lifetime_s'] for p in particles), max(p['lifetime_s'] for p in particles)],
               'source': 'Original project-authored independent streaks and small star; no remote generation'}
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return {'asset': str(asset), 'motion': str(motion_path), 'metrics': metrics}
