"""Layered wet-cloth source for normal combat distance, built through the shared entry."""
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'ArtSource/refinement/effects'))
from build_contact_effects import Effect, Layer
from prepare_rigged_warrior import write_glb


def teardrop(length, cross_diameter, axis='Y'):
    """Closed 32-triangle drop; cross_diameter is the measured lower-ring width."""
    vertices = [(0.0, -length / 2, 0.0), (0.0, length / 2, 0.0)]
    for height, radius in ((-0.18, 0.50), (0.15, 0.43)):
        for side in range(8):
            angle = side * math.tau / 8
            vertices.append((cross_diameter * radius * math.cos(angle), length * height,
                             cross_diameter * radius * math.sin(angle)))
    triangles = []
    for side in range(8):
        following = (side + 1) % 8
        low, next_low, high, next_high = 2 + side, 2 + following, 10 + side, 10 + following
        triangles.extend((0, low, next_low, 1, next_high, high,
                          low, high, next_high, low, next_high, next_low))
    normals = []
    radial = cross_diameter / 2
    for x, y, z in vertices:
        gradient = (x / (radial*radial), y / ((length/2)*(length/2)), z / (radial*radial))
        magnitude = math.sqrt(sum(v*v for v in gradient))
        normals.append(tuple(v / magnitude for v in gradient))
    if axis == 'X':
        vertices = [(y, -x, z) for x, y, z in vertices]
        normals = [(y, -x, z) for x, y, z in normals]
    return vertices, triangles, normals


def opacity_keys(lifetime, peak, linger_fraction):
    return [[0.0, 0.0], [0.008, peak],
            [round(lifetime * linger_fraction, 6), peak * 0.76], [lifetime, 0.0]]


def build(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    effect = Effect('wet_cloth_contact', '', 0.40, 'XY contact plane; local +X tangent, +Z outward normal')
    effect.document.pop('animations')
    extras = effect.document['nodes'][0]['extras']
    extras.pop('clip', None)
    extras.update({'driver': 'Independent Entity transform / opacity', 'droplets': 18, 'fibers': 5,
                   'viewTargetMeters': [1.5, 2.5], 'sourceVersion': 'visibility-v3'})
    main_water = effect.material('Wet cloth | clear cold highlight', (0.74, 0.86, 0.92, 0.88),
                                 emission=(0.0, 0.0, 0.0), roughness=0.14)
    fine_water = effect.material('Wet cloth | cool fine spray', (0.57, 0.70, 0.78, 0.72),
                                 emission=(0.0, 0.0, 0.0), roughness=0.22)
    fiber_material = effect.material('Wet cloth | pale frayed threads', (0.47, 0.54, 0.57, 0.86),
                                     emission=(0.0, 0.0, 0.0), roughness=0.82)
    # (tier, body length, cross width, long axis, lifetime, velocity T/B/N)
    definitions = [
        ('hero', .0090, .00774, 'Y', .18, (1.55, .28, .62)),
        ('hero', .0085, .00731, 'Y', .22, (1.32, -.24, .56)),
        ('main', .0070, .00602, 'Y', .24, (1.10, .38, .47)),
        ('main', .0065, .00559, 'Y', .23, (1.28, -.35, .53)),
        ('main', .0060, .00516, 'Y', .27, (.96, .12, .44)),
        ('main', .0055, .00473, 'Y', .25, (1.17, -.16, .37)),
        ('stretched', .0120, .0036, 'X', .24, (1.64, .18, .48)),
        ('stretched', .0150, .0042, 'X', .26, (1.46, -.30, .52)),
        ('stretched', .0180, .0045, 'X', .28, (1.30, .32, .40)),
        ('stretched', .0100, .0038, 'X', .30, (1.08, -.22, .35)),
        ('fine', .0030, .00258, 'Y', .25, (.45, .19, .20)),
        ('fine', .0035, .00301, 'Y', .28, (.72, -.14, .28)),
        ('fine', .0040, .00344, 'Y', .32, (.58, .34, .25)),
        ('fine', .0045, .00387, 'Y', .34, (.87, -.27, .32)),
        ('fine', .0032, .00275, 'Y', .36, (.64, .08, .22)),
        ('fine', .0038, .00327, 'Y', .31, (.38, -.32, .18)),
        ('fine', .0042, .00361, 'Y', .29, (.79, .26, .30)),
        ('fine', .0034, .00292, 'Y', .33, (.52, -.06, .24)),
    ]
    particles = []
    geometry_stats = []
    for index, (tier, length, width, axis, life, velocity) in enumerate(definitions):
        node_name = f'drop_{index:02d}'
        start = ((index % 5 - 2) * .003, (index % 4 - 1.5) * .002, .003 + (index % 3) * .001)
        vertices, indices, normals = teardrop(length, width, axis)
        material = fine_water if tier == 'fine' else main_water
        node = effect.node(node_name, vertices, indices, [(1.0, 1.0, 1.0, 1.0)] * len(vertices),
                           material, translation=start)
        primitive = effect.document['meshes'][effect.document['nodes'][node]['mesh']]['primitives'][0]
        primitive['attributes']['NORMAL'] = effect.accessor(normals, 'VEC3', target=34962)
        particle = {'node': node_name, 'type': 'droplet', 'tier': tier,
                    'shape': 'stretched' if axis == 'X' else 'round',
                    'priority': {'hero': 100, 'main': 85, 'stretched': 80, 'fine': 45}[tier],
                    'orientation_axis_local': [1.0, 0.0, 0.0] if axis == 'X' else [0.0, 1.0, 0.0],
                    'initial_position_local_m': list(start), 'initial_velocity_local_mps': list(velocity),
                    'lifetime_s': life, 'opacity_keys': opacity_keys(life, .98 if tier != 'fine' else .86, .30 if tier != 'fine' else .40),
                    'geometry_long_axis_local': axis, 'orientation_policy': 'source TBN; optional velocity alignment by 08',
                    'cross_section_diameter_m': width}
        if axis == 'X':
            particle['length_m'] = length
        else:
            particle['diameter_m'] = length
        particles.append(particle)
        geometry_stats.append({'node': node_name, 'triangles': 32, 'tier': tier,
                               'bounds_min_m': [min(v[a] for v in vertices) for a in range(3)],
                               'bounds_max_m': [max(v[a] for v in vertices) for a in range(3)]})
    fibers = [(.008, .0012, .29, (.72, .24, .18)), (.010, .0015, .33, (.61, -.20, .22)),
              (.012, .0017, .36, (.52, .12, .16)), (.014, .0020, .40, (.44, -.28, .19)),
              (.015, .0022, .38, (.68, .31, .25))]
    for index, (length, width, life, velocity) in enumerate(fibers):
        node_name = f'fiber_{index:02d}'
        layer = Layer()
        for rotate in (False, True):
            card = Layer()
            card.streak((0, 0, 0), length, width/2, 0, (1, 1, 1, 1))
            offset = len(layer.vertices)
            layer.vertices.extend((x, 0, y) if rotate else (x, y, 0) for x, y, _ in card.vertices)
            layer.colors.extend(card.colors)
            layer.indices.extend(offset + value for value in card.indices)
        start = ((index-2)*.002, (index%2-.5)*.003, .003)
        effect.node(node_name, layer.vertices, layer.indices, layer.colors, fiber_material, translation=start)
        particles.append({'node': node_name, 'type': 'fiber', 'shape': 'ribbon_cross', 'tier': 'trailing_fiber',
                          'priority': 55, 'orientation_axis_local': [1.0, 0.0, 0.0],
                          'length_m': length, 'width_m': width,
                          'initial_position_local_m': list(start), 'initial_velocity_local_mps': list(velocity),
                          'lifetime_s': life, 'opacity_keys': opacity_keys(life, .88, .52),
                          'geometry_long_axis_local': 'X', 'orientation_policy': 'source TBN; optional velocity alignment by 08'})
        geometry_stats.append({'node': node_name, 'triangles': 4, 'tier': 'trailing_fiber',
                               'bounds_min_m': [min(v[a] for v in layer.vertices) for a in range(3)],
                               'bounds_max_m': [max(v[a] for v in layer.vertices) for a in range(3)]})
    effect.document['buffers'][0]['byteLength'] = len(effect.binary)
    path = output_dir / 'wet_cloth_contact.glb'
    information = write_glb(path, effect.document, bytes(effect.binary))
    motion = {'schema': 'contact-particle-motion/v2', 'asset': path.name, 'version': 'wet-visibility-v3', 'units': 'metres / seconds',
              'basis': {'x': 'normalized real cut tangent projected onto contact plane', 'y': 'normal cross tangent',
                        'z': 'normalized real outward contact normal'},
              'gravity_stage_mps2': [0.0, -9.81, 0.0], 'anchor_normal_offset_m': .008,
              'clock': 'presentation seconds since fresh contact, continues during NPC pose hitstop',
              'transform_equation': 'p=point+normal*anchorOffset+basis*p0+basis*v0*t+0.5*gravityStage*t*t',
              'opacity_interpolation': 'linear opacity_keys; zero before birth and at/after lifetime',
              'contact_semantics': 'Only Root/08-confirmed wet cloth. Bare head and generic SOFT classification do not identify wet cloth.',
              'tangent_requirement': '08 supplies real blade-tip sweep tangent; data is not a synthetic input implementation.',
              'view_target_m': [1.5, 2.5],
              'material_approximation': 'Ordinary PBR alpha highlight; three materials, no emissive, transmission or shader extensions.',
              'particles': particles, 'cores': [], 'accents': [], 'source': 'Project-original deterministic procedural source using existing Effect/Layer writer'}
    (output_dir / 'motion.json').write_text(json.dumps(motion, ensure_ascii=False, indent=2) + '\n')
    metrics = {**information, 'asset': path.name, 'motion': 'motion.json', 'droplets': 18, 'fibers': 5,
               'mesh_nodes': len(particles), 'triangles': effect.triangles, 'materials': 3, 'animations': 0,
               'round_drop_diameter_range_m': [.003, .009], 'hero_drops': 2,
               'stretched_drop_cross_section_range_m': [.0036, .0045], 'stretched_drop_length_range_m': [.010, .018],
               'fiber_length_range_m': [.008, .015], 'fiber_width_range_m': [.0012, .0022],
               'lifetime_range_s': [.18, .40], 'geometry': geometry_stats,
               'view_target_m': [1.5, 2.5], 'runtime_validation': '08 / Root integration and headset review pending'}
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return metrics
