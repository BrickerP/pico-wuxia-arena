"""Low courtyard dust, authored only through the shared contact-polish entry."""
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'ArtSource/refinement/effects'))
from build_contact_effects import Effect, Layer
from prepare_rigged_warrior import write_glb


def dust_volume(width, height, angle):
    """Two upright alpha fans. Origin is the base and all local Z is nonnegative."""
    volume = Layer()
    for turn in (angle, angle + math.pi / 2):
        card = Layer()
        card.puff((0.0, 0.0, 0.0), width / 2, (1.0, 1.0, 1.0, 0.70),
                  squash=height / width, sides=12)
        offset = len(volume.vertices)
        for x, y, _ in card.vertices:
            volume.vertices.append((x * math.cos(turn), x * math.sin(turn), max(0.0, y + height / 2)))
        volume.colors.extend(card.colors)
        volume.indices.extend(index + offset for index in card.indices)
    return volume


def opacity_keys(lifetime, peak):
    return [[0.0, 0.0], [0.025, peak], [round(lifetime * 0.36, 6), peak * 0.70], [lifetime, 0.0]]


def make_asset(output_dir, kind):
    landing = kind == 'landing'
    name = 'landing_ground_polish' if landing else 'dodge_ground_polish'
    effect = Effect(name, '', 0.42, 'XY ground plane; local +Z=actual ground normal; +X=motion tangent')
    effect.document.pop('animations')
    extras = effect.document['nodes'][0]['extras']
    extras.pop('clip', None)
    extras.update({'driver': 'Independent base-clamped Entity transforms and opacity',
                   'meshOrigin': 'particle base', 'minimumGeometryLocalZ': 0.0})
    material = effect.material('Damp courtyard | low grey silt', (0.46, 0.44, 0.38, 0.28),
                               emission=(0.0, 0.0, 0.0), roughness=1.0)
    particles = []
    for index in range(8):
        width = (0.045, 0.060, 0.052, 0.068, 0.048, 0.064, 0.055, 0.058)[index]
        height = (0.020, 0.024, 0.022, 0.028, 0.021, 0.026, 0.023, 0.025)[index]
        lifetime = ((0.32, 0.38, 0.34, 0.42, 0.30, 0.40, 0.36, 0.39) if landing else
                    (0.28, 0.34, 0.30, 0.38, 0.26, 0.36, 0.32, 0.35))[index]
        angle = index * math.tau / 8
        if landing:
            radius = 0.025 + (index % 3) * 0.010
            speed = 0.16 + (index % 4) * 0.020
            start = (math.cos(angle) * radius, math.sin(angle) * radius, 0.0)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed, 0.22 + (index % 3) * 0.04)
        else:
            start = (-0.04 - index * 0.011, (-1 if index % 2 else 1) * (0.015 + (index % 3) * 0.010), 0.0)
            velocity = (-0.04 - (index % 4) * 0.020,
                        (-1 if index % 2 else 1) * (0.045 + (index % 3) * 0.020),
                        0.16 + (index % 4) * 0.030)
        node = f'dust_{index:02d}'
        volume = dust_volume(width, height, angle * 0.37)
        effect.node(node, volume.vertices, volume.indices, volume.colors, material, translation=start)
        particles.append({'node': node, 'type': 'ground_dust', 'width_m': width, 'height_m': height,
                          'mesh_origin': 'base', 'minimum_geometry_local_z_m': 0.0,
                          'initial_position_local_m': list(start), 'initial_velocity_local_mps': list(velocity),
                          'lifetime_s': lifetime, 'opacity_keys': opacity_keys(lifetime, 0.64 if landing else 0.55),
                          'orientation_policy': 'fixed TBN; optional rotation only around N'})
    effect.document['buffers'][0]['byteLength'] = len(effect.binary)
    asset = output_dir / (name + '.glb')
    information = write_glb(asset, effect.document, bytes(effect.binary))
    motion = {
        'asset': asset.name, 'units': 'metres / seconds',
        'basis': {'x': 'actual player ground-displacement tangent' if not landing else 'actual surface-plane tangent',
                  'z': 'actual ground outward normal', 'y': 'z cross x'},
        'gravity_stage_mps2': [0.0, -9.81, 0.0], 'anchor_normal_offset_m': 0.002,
        'mesh_origin': 'particle base', 'ground_constraint': 'particle base >= anchor plane',
        'orientation_policy': 'fixed TBN; optional rotation only around N',
        'clock': 'presentation seconds since a fresh resolved ground event',
        'transform_equation': 'q=p0Local+v0Local*t+0.5*(basisTranspose*gravityStage)*t*t; q.z=max(q.z,0); pStage=pointStage+normalStage*0.002+basis*q',
        'opacity_interpolation': 'linear opacity_keys; zero before birth and at/after lifetime',
        'trigger_requirement': ('Root-resolved successful dodge with actual near-ground player displacement' if not landing else
                                'Root-resolved actual foot/body ground contact from current pose and ground geometry'),
        'surface_requirement': 'Existing courtyard paving with small loose grit; actual point, normal and material are supplied by Root',
        'visual_approximation': 'Low-opacity upright cross-card silt, no volumetric shader or external texture',
        'particles': particles, 'waves': [],
        'source': 'Original deterministic procedural mesh; project static GLB helpers',
    }
    motion_path = output_dir / (kind + '_motion.json')
    motion_path.write_text(json.dumps(motion, ensure_ascii=False, indent=2) + '\n')
    return {**information, 'asset': asset.name, 'motion': motion_path.name, 'particles': 8,
            'mesh_nodes': 8, 'triangles': effect.triangles, 'animations': 0,
            'mesh_height_m': [min(p['height_m'] for p in particles), max(p['height_m'] for p in particles)],
            'lifetime_s': [min(p['lifetime_s'] for p in particles), max(p['lifetime_s'] for p in particles)],
            'minimum_geometry_local_z_m': 0.0}


def build(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = {kind: make_asset(output_dir, kind) for kind in ('dodge', 'landing')}
    metrics = {'status': 'offline source candidate', 'assets': assets,
               'ground_frame': 'local [T,B,N], Stage normal and tangent supplied by Root',
               'anchor_normal_offset_m': 0.002, 'particle_orientation': 'fixed TBN',
               'source': 'Project-original procedural geometry, no paid service'}
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return metrics
