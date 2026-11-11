"""Wet-cloth contact source, built only by the shared contact-polish entry point."""
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'ArtSource/refinement/effects'))
from build_contact_effects import Effect, Layer
from prepare_rigged_warrior import write_glb


def droplet(diameter):
    """Closed 24-triangle tear with smooth outward vertex normals, maximum size=diameter."""
    vertices = [(0.0, -diameter / 2, 0.0), (0.0, diameter / 2, 0.0)]
    for height, radius in ((-0.18, 0.38), (0.15, 0.34)):
        for side in range(6):
            angle = side * math.tau / 6
            vertices.append((diameter * radius * math.cos(angle), diameter * height,
                             diameter * radius * math.sin(angle)))
    indices = []
    for side in range(6):
        following = (side + 1) % 6
        lower, next_lower = 2 + side, 2 + following
        upper, next_upper = 8 + side, 8 + following
        indices.extend((0, lower, next_lower, 1, next_upper, upper,
                        lower, upper, next_upper, lower, next_upper, next_lower))
    normals = []
    for x, y, z in vertices:
        length = math.sqrt(x*x + y*y + z*z)
        normals.append((x / length, y / length, z / length))
    return vertices, indices, normals


def opacity_keys(lifetime, peak=0.92):
    return [[0.0, 0.0], [0.008, peak], [round(lifetime * 0.34, 6), peak * 0.78], [lifetime, 0.0]]


def build(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    effect = Effect('wet_cloth_contact', '', 0.32, 'XY contact plane; +Z outward normal; +X tangent')
    effect.document.pop('animations')
    root_extras = effect.document['nodes'][0]['extras']
    root_extras.pop('clip', None)
    root_extras['driver'] = 'Independent Entity transforms and opacity from resolved wet-cloth contact'
    root_extras['physicalParticleCount'] = 10
    water = effect.material('Water | plain PBR alpha approximation', (0.56, 0.70, 0.80, 0.56),
                            emission=(0.0, 0.0, 0.0), roughness=0.18)
    fiber = effect.material('Wet cloth | short grey fibers', (0.30, 0.32, 0.31, 0.72),
                            emission=(0.0, 0.0, 0.0), roughness=0.88)
    diameters = (0.0022, 0.0034, 0.0028, 0.0039, 0.0025, 0.0031, 0.0036, 0.0020)
    lifetimes = (0.18, 0.24, 0.22, 0.30, 0.26, 0.32, 0.28, 0.21)
    velocities = ((0.32, 0.15, 0.19), (0.72, 0.20, 0.28), (0.46, -0.08, 0.16),
                  (0.90, 0.12, 0.33), (0.56, 0.27, 0.23), (0.80, -0.12, 0.31),
                  (0.63, 0.04, 0.25), (0.40, -0.20, 0.14))
    particles = []
    for index, (diameter, lifetime, velocity) in enumerate(zip(diameters, lifetimes, velocities)):
        name = f'drop_{index:02d}'
        start = (round((index - 3.5) * 0.0010, 6), -0.0007 if index % 2 else 0.0007,
                 0.0010 + (index % 3) * 0.0005)
        vertices, triangles, normals = droplet(diameter)
        node = effect.node(name, vertices, triangles, [(1.0, 1.0, 1.0, 1.0)] * len(vertices), water,
                           translation=start)
        primitive = effect.document['meshes'][effect.document['nodes'][node]['mesh']]['primitives'][0]
        primitive['attributes']['NORMAL'] = effect.accessor(normals, 'VEC3', target=34962)
        particles.append({'node': name, 'type': 'droplet', 'diameter_m': diameter,
                          'initial_position_local_m': list(start), 'initial_velocity_local_mps': list(velocity),
                          'lifetime_s': lifetime, 'opacity_keys': opacity_keys(lifetime),
                          'mesh_orientation': 'Source local +Y tear axis; renderer may align to velocity'})
    for index, (length, width, velocity, lifetime) in enumerate((
            (0.0038, 0.00038, (0.45, 0.16, 0.13), 0.24),
            (0.0034, 0.00044, (0.66, -0.06, 0.20), 0.29))):
        name = f'fiber_{index:02d}'
        layer = Layer()
        layer.streak((0.0, 0.0, 0.0), length, width / 2, 0.16 + index * 0.55, (1.0, 1.0, 1.0, 1.0))
        start = (-0.001 + index * 0.002, 0.0004, 0.001)
        effect.node(name, layer.vertices, layer.indices, layer.colors, fiber, translation=start)
        particles.append({'node': name, 'type': 'fiber', 'length_m': length, 'width_m': width,
                          'initial_position_local_m': list(start), 'initial_velocity_local_mps': list(velocity),
                          'lifetime_s': lifetime, 'opacity_keys': opacity_keys(lifetime, peak=0.78)})
    effect.document['buffers'][0]['byteLength'] = len(effect.binary)
    asset = output_dir / 'wet_cloth_contact.glb'
    information = write_glb(asset, effect.document, bytes(effect.binary))
    motion = {
        'asset': asset.name,
        'units': 'metres / seconds',
        'basis': {'x': 'normalized actual cut tangent projected onto contact plane',
                  'z': 'normalized actual contact outward normal', 'y': 'z cross x'},
        'gravity_stage_mps2': [0.0, -9.81, 0.0],
        'anchor_normal_offset_m': 0.008,
        'clock': 'presentation seconds since accepted fresh contact; continues through NPC pose hitstop',
        'transform_equation': 'pStage(t)=pointStage+normalStage*anchorNormalOffset+basis*p0Local+basis*v0Local*t+0.5*gravityStage*t*t',
        'opacity_interpolation': 'linear between opacity_keys; zero before birth and at/after lifetime',
        'contact_semantics': 'Only Root-confirmed wet cloth; bare head and generic soft contact do not imply water.',
        'tangent_requirement': 'Root supplies actual sampled blade-tip sweep tangent. CombatImpact currently has no tangent field.',
        'material_approximation': 'Ordinary alpha-blended PBR highlight, no transmission or refraction extension.',
        'particles': particles,
        'source': 'Original procedural geometry, deterministic sizes and motion. No external texture or paid service.',
    }
    (output_dir / 'motion.json').write_text(json.dumps(motion, ensure_ascii=False, indent=2) + '\n')
    metrics = {**information, 'asset': asset.name, 'motion': 'motion.json', 'animations': 0,
               'triangles': effect.triangles, 'mesh_nodes': 10, 'droplets': 8, 'fibers': 2,
               'droplet_diameter_m': [min(diameters), max(diameters)], 'lifetime_s': [min(lifetimes), max(lifetimes)],
               'gravity_space': 'Stage', 'default_pose_bounds_m': {
                   'min': [min(point[axis] for point in effect.positions) for axis in range(3)],
                   'max': [max(point[axis] for point in effect.positions) for axis in range(3)]}}
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return metrics
