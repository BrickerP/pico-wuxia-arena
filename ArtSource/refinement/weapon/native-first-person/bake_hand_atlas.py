"""Pack selected hand UV islands without rotation, reflection or resampling.

Run with the existing Python numpy/Pillow installation. Only this private
candidate directory is written; the formal actor and prepared PNG stay read-only.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from build_weapon import read_glb
import numpy as np
from PIL import Image

PNG_SHA = 'b3fbfe66727d0dd90bd741420937a6c57dbb9e083d76ecd983cd9383ab5bbf96'
FORMAL_SHA = 'ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20'
EDGE = 1536
PADDING = 20
SAMPLING_GUARD = 2
EXTRUSION = 16
ROLES = ('normal', 'base_color', 'metallic_roughness')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require_pin(path, expected):
    if sha(path.read_bytes()) != expected:
        raise ValueError('Source identity changed: ' + str(path))


def components(vertex_count, faces):
    """Use indexed UV connectivity, preserving every authored seam split."""
    parents = np.arange(vertex_count)

    def root(vertex):
        while parents[vertex] != vertex:
            parents[vertex] = parents[parents[vertex]]
            vertex = parents[vertex]
        return int(vertex)

    for face in faces:
        for vertex in face[1:]:
            parents[root(int(vertex))] = root(int(face[0]))
    groups = {}
    for vertex in range(vertex_count):
        groups.setdefault(root(vertex), []).append(vertex)
    return sorted((np.asarray(group, dtype=np.int32) for group in groups.values()),
                  key=lambda group: int(group[0]))


def pack_rectangles(sizes, edge):
    """Deterministic nonrotating MaxRects placement; fail rather than shrink."""
    free = [(0, 0, edge, edge)]
    placed = {}
    order = sorted(range(len(sizes)),
                   key=lambda i: (-max(sizes[i]), -sizes[i][0] * sizes[i][1], i))
    for island in order:
        width, height = sizes[island]
        options = [(min(w - width, h - height), max(w - width, h - height), y, x)
                   for x, y, w, h in free if w >= width and h >= height]
        if not options:
            raise ValueError('Unrotated UV islands exceed the fixed atlas budget')
        _, _, y, x = min(options)
        placed[island] = (x, y, width, height)
        split = []
        for left, top, w, h in free:
            if x >= left + w or x + width <= left or y >= top + h or y + height <= top:
                split.append((left, top, w, h))
                continue
            if x > left:
                split.append((left, top, x - left, h))
            if x + width < left + w:
                split.append((x + width, top, left + w - x - width, h))
            if y > top:
                split.append((left, top, w, y - top))
            if y + height < top + h:
                split.append((left, y + height, w, top + h - y - height))
        free = [rect for i, rect in enumerate(split)
                if not any(i != j and rect[0] >= other[0] and rect[1] >= other[1]
                           and rect[0] + rect[2] <= other[0] + other[2]
                           and rect[1] + rect[3] <= other[1] + other[3]
                           and (rect != other or j < i)
                           for j, other in enumerate(split))]
    return [placed[i] for i in range(len(sizes))]


def conservative_mask(points, faces, shape):
    """Copy all texels within two pixels of each selected UV triangle.

    This includes every level-zero bilinear footprint, even for the original
    collapsed UV triangles. Pixel coordinates use glTF's image row direction.
    """
    mask = np.zeros(shape, dtype=bool)
    radius_squared = float(SAMPLING_GUARD ** 2)
    for face in faces:
        triangle = points[face]
        lower = np.maximum(np.floor(triangle.min(axis=0) - SAMPLING_GUARD).astype(int), 0)
        upper = np.minimum(np.ceil(triangle.max(axis=0) + SAMPLING_GUARD).astype(int), shape[::-1])
        xx, yy = np.meshgrid(np.arange(lower[0], upper[0]) + .5,
                             np.arange(lower[1], upper[1]) + .5)
        sample = np.stack((xx, yy), axis=-1)
        inside = np.zeros(xx.shape, dtype=bool)
        crosses = []
        for first, second in zip(triangle, np.roll(triangle, -1, axis=0)):
            edge = second - first
            relative = sample - first
            length_squared = float(edge @ edge)
            fraction = np.clip(np.sum(relative * edge, axis=-1) / max(length_squared, 1e-30), 0, 1)
            distance = relative - fraction[..., None] * edge
            inside |= np.sum(distance * distance, axis=-1) <= radius_squared
            crosses.append(edge[0] * relative[..., 1] - edge[1] * relative[..., 0])
        crosses = np.stack(crosses)
        first_edge = triangle[1] - triangle[0]
        second_edge = triangle[2] - triangle[0]
        signed_area = first_edge[0] * second_edge[1] - first_edge[1] * second_edge[0]
        if abs(signed_area) > 1e-20:
            inside |= (crosses >= 0).all(axis=0) | (crosses <= 0).all(axis=0)
        mask[lower[1]:upper[1], lower[0]:upper[0]] |= inside
    if not mask.any():
        raise ValueError('UV component has no source sampling footprint')
    return mask


def extrude_coordinates(mask, count):
    """Propagate source-pixel donors; seed bytes remain exactly unchanged."""
    height, width = mask.shape
    donors = np.arange(height * width, dtype=np.int32).reshape(height, width)
    donors[~mask] = -1
    for _ in range(count):
        before = donors.copy()
        for dy, dx in ((-1, 0), (0, -1), (0, 1), (1, 0),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)):
            target_y = slice(max(0, dy), min(height, height + dy))
            target_x = slice(max(0, dx), min(width, width + dx))
            source_y = slice(max(0, -dy), min(height, height - dy))
            source_x = slice(max(0, -dx), min(width, width - dx))
            target = donors[target_y, target_x]
            source = before[source_y, source_x]
            use = (target < 0) & (source >= 0)
            target[use] = source[use]
    return donors


def bilinear(pixels, uv, repeat=False):
    height, width = pixels.shape[:2]
    point = np.asarray(uv, dtype=float) * [width, height] - .5
    lower = np.floor(point).astype(int)
    blend = point - lower
    result = np.zeros((len(point), 3), dtype=float)
    for dy in (0, 1):
        for dx in (0, 1):
            coordinate = lower + [dx, dy]
            if repeat:
                coordinate %= [width, height]
            else:
                coordinate = np.clip(coordinate, [0, 0], [width - 1, height - 1])
            weight = (blend[:, 0] if dx else 1 - blend[:, 0]) * (blend[:, 1] if dy else 1 - blend[:, 1])
            result += pixels[coordinate[:, 1], coordinate[:, 0]] * weight[:, None]
    return result


def load_source(selection):
    source = REPO / selection['png_source']
    require_pin(source, PNG_SHA)
    require_pin(REPO / selection['formal_source'], FORMAL_SHA)
    if selection['png_sha256'] != PNG_SHA or selection['formal_sha256'] != FORMAL_SHA:
        raise ValueError('Selection uses a different formal actor')
    require_pin(REPO / selection['npz'], selection['npz_sha256'])
    document, binary = read_glb(source)
    material = document['materials'][0]
    texture_infos = {
        'normal': material['normalTexture'],
        'base_color': material['pbrMetallicRoughness']['baseColorTexture'],
        'metallic_roughness': material['pbrMetallicRoughness']['metallicRoughnessTexture'],
    }
    pixels = {}
    records = {}
    for role, info in texture_infos.items():
        if info.get('texCoord', 0) != 0 or info.get('extensions'):
            raise ValueError('Atlas requires untransformed TEXCOORD_0 source textures')
        texture = document['textures'][info['index']]
        sampler = document['samplers'][texture['sampler']]
        if sampler.get('wrapS', 10497) != 10497 or sampler.get('wrapT', 10497) != 10497:
            raise ValueError('Source footprint wrapping no longer matches REPEAT')
        image_index = texture['source']
        image = document['images'][image_index]
        view = document['bufferViews'][image['bufferView']]
        if view['buffer'] != 0:
            raise ValueError('Expected embedded source PNG')
        offset = view.get('byteOffset', 0)
        raw = binary[offset:offset + view['byteLength']]
        decoded = Image.open(io.BytesIO(raw))
        if decoded.mode != 'RGB' or decoded.size != (4096, 4096):
            raise ValueError('Source role image format or size changed')
        pixels[role] = np.array(decoded)
        records[role] = {
            'source_texture': info['index'], 'source_image': image_index,
            'source_buffer_view': image['bufferView'], 'source_png_sha256': sha(raw),
            'source_png_bytes': len(raw), 'dimensions': list(decoded.size),
            'channels': 'RGB', 'color_space': 'sRGB' if role == 'base_color' else 'linear',
            'source_texture_info': info, 'source_sampler': sampler,
        }
    return pixels, records, material


def build_side(side, record, arrays, source_pixels, source_records, output, remap):
    if len(record['primitives']) != 1 or record['primitives'][0]['source_material'] != 0:
        raise ValueError('Only the approved body material-zero selection is supported')
    prefix = record['primitives'][0]['npz_prefix']
    source_uv = arrays[prefix + '_TEXCOORD_0'].astype(float)
    faces = arrays[prefix + '_indices'].astype(int)
    if not np.isfinite(source_uv).all() or source_uv.min() < 0 or source_uv.max() > 1:
        raise ValueError('Unexpected source UV range')
    groups = components(len(source_uv), faces)
    bounds = [(np.floor(source_uv[group].min(axis=0) * 4096).astype(int),
               np.floor(source_uv[group].max(axis=0) * 4096).astype(int) + 1)
              for group in groups]
    sizes = [tuple(map(int, upper - lower + 2 * PADDING)) for lower, upper in bounds]
    rectangles = pack_rectangles(sizes, EDGE)
    atlas = {role: np.zeros((EDGE, EDGE, 3), dtype=np.uint8) for role in ROLES}
    atlas['normal'][:] = [128, 128, 255]
    atlas['metallic_roughness'][:] = [255, 255, 0]
    coverage = np.zeros((EDGE, EDGE), dtype=np.uint8)
    target_uv = np.empty_like(source_uv, dtype=np.float32)
    vertex_islands = np.full(len(source_uv), -1, dtype=np.int32)
    island_records = []
    degenerate_faces = []
    source_area = 0.0
    for island, (vertices, (lower, upper), rectangle) in enumerate(zip(groups, bounds, rectangles)):
        x, y, width, height = rectangle
        vertex_islands[vertices] = island
        selected_faces = np.flatnonzero(np.isin(faces[:, 0], vertices))
        island_faces = faces[selected_faces]
        if not np.isin(island_faces, vertices).all():
            raise ValueError('UV component split an indexed face')
        local_points = source_uv * 4096 - lower + PADDING
        seed = conservative_mask(local_points, island_faces, (height, width))
        donors = extrude_coordinates(seed, EXTRUSION)
        valid = donors >= 0
        rows = (np.arange(height) + lower[1] - PADDING) % 4096
        columns = (np.arange(width) + lower[0] - PADDING) % 4096
        for role in ROLES:
            patch = source_pixels[role][rows[:, None], columns[None, :]]
            cropped = atlas[role][y:y + height, x:x + width]
            cropped[valid] = patch.reshape(-1, 3)[donors[valid]]
            if not np.array_equal(cropped[seed], patch[seed]):
                raise ValueError('Source sampling footprint was altered')
        coverage_patch = coverage[y:y + height, x:x + width]
        coverage_patch[valid] = 80
        coverage_patch[seed] = 255
        translation = (np.array([x, y]) + PADDING - lower) / EDGE
        target_uv[vertices] = source_uv[vertices] * (4096 / EDGE) + translation
        points = source_uv[island_faces]
        area = ((points[:, 1, 0] - points[:, 0, 0]) * (points[:, 2, 1] - points[:, 0, 1])
                - (points[:, 1, 1] - points[:, 0, 1]) * (points[:, 2, 0] - points[:, 0, 0])) * .5
        collapsed = selected_faces[np.abs(area) < 1e-14]
        degenerate_faces.extend(collapsed.tolist())
        source_area += float(np.abs(area).sum())
        island_records.append({
            'island_id': island, 'vertices': len(vertices), 'faces': len(selected_faces),
            'source_uv_min': source_uv[vertices].min(axis=0).tolist(),
            'source_uv_max': source_uv[vertices].max(axis=0).tolist(),
            'source_core_pixel_rect_xyxy': [*lower.tolist(), *upper.tolist()],
            'atlas_padded_rect_xywh': list(rectangle),
            'uniform_uv_scale': 4096 / EDGE, 'uv_offset': translation.tolist(),
            'rotation_degrees': 0, 'reflection': False,
            'copied_sampling_footprint_pixels': int(seed.sum()),
            'copied_plus_extruded_pixels': int(valid.sum()),
            'zero_area_source_face_ids': arrays[prefix + '_source_face_ids'][collapsed].tolist(),
        })
    if (vertex_islands < 0).any() or target_uv.min() <= 0 or target_uv.max() >= 1:
        raise ValueError('Incomplete or out-of-bounds atlas UV mapping')
    remap[prefix + '_TEXCOORD_0'] = target_uv
    remap[prefix + '_source_uv'] = arrays[prefix + '_TEXCOORD_0']
    remap[prefix + '_source_vertex_ids'] = arrays[prefix + '_source_vertex_ids']
    remap[prefix + '_source_face_ids'] = arrays[prefix + '_source_face_ids']
    remap[prefix + '_vertex_island_ids'] = vertex_islands
    remap[prefix + '_uniform_uv_scale'] = np.array([4096 / EDGE])
    remap[prefix + '_island_uv_offsets'] = np.array([i['uv_offset'] for i in island_records])
    textures = {}
    # Vertices, face centers and two interior barycentric points per triangle.
    barycentric = np.array([[1/3, 1/3, 1/3], [.6, .25, .15], [.15, .6, .25]])
    source_samples = np.concatenate([source_uv, np.einsum('bf,tfc->tbc', barycentric, source_uv[faces]).reshape(-1, 2)])
    target_samples = np.concatenate([target_uv, np.einsum('bf,tfc->tbc', barycentric, target_uv[faces]).reshape(-1, 2)])
    for role in ROLES:
        path = output / (side + '_' + role + '.png')
        Image.fromarray(atlas[role]).save(path, compress_level=9)
        decoded = np.array(Image.open(path))
        if not np.array_equal(decoded, atlas[role]):
            raise ValueError('PNG round trip changed pixels')
        error = np.abs(bilinear(source_pixels[role], source_samples, repeat=True)
                       - bilinear(decoded, target_samples))
        if error.max() > .05:
            raise ValueError('Atlas bilinear sample mismatch: ' + role + ': ' + str(error.max()))
        textures[role] = {
            'path': str(path.relative_to(REPO)), 'sha256': sha(path.read_bytes()),
            'bytes': path.stat().st_size, 'dimensions': [EDGE, EDGE], 'channels': 'RGB',
            'color_space': source_records[role]['color_space'], 'texCoord': 0,
            'source_png_sha256': source_records[role]['source_png_sha256'],
            'comparison': {'source_target_bilinear_samples': len(source_samples),
                           'max_rgb_byte_error': float(error.max()),
                           'mean_rgb_byte_error': float(error.mean()),
                           'copied_footprint_pixels_byte_exact': True},
        }
    Image.fromarray(coverage).save(output / (side + '_coverage.png'), compress_level=9)
    source_deltas = source_uv[faces[:, 1:]] - source_uv[faces[:, :1]]
    target_deltas = target_uv[faces[:, 1:]].astype(float) - target_uv[faces[:, :1]]
    derivative_error = np.abs(target_deltas - source_deltas * (4096 / EDGE))
    return {
        'npz_prefix': prefix, 'source_material': 0,
        'material_name': record['primitives'][0]['material_name'],
        'vertices': len(source_uv), 'triangles': len(faces),
        'uv_npz_key': prefix + '_TEXCOORD_0',
        'compact_vertex_order_unchanged': True, 'additional_vertex_splits': 0,
        'dimensions': [EDGE, EDGE], 'islands': island_records, 'textures': textures,
        'source_uv_triangle_area': source_area,
        'source_uv_area_texels': source_area * 4096 ** 2,
        'atlas_triangle_area_fraction': source_area * (4096 / EDGE) ** 2,
        'packed_rect_fraction': sum(w * h for w, h in sizes) / EDGE ** 2,
        'sampling_footprint_pixels': int((coverage == 255).sum()),
        'sampling_plus_gutter_pixels': int((coverage > 0).sum()),
        'zero_area_source_face_ids': arrays[prefix + '_source_face_ids'][degenerate_faces].tolist(),
        'float32_uv_derivative_max_abs_error': float(derivative_error.max()),
        'sampler': {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071},
    }


def build():
    selection_path = HERE / 'selection.json'
    selection = json.loads(selection_path.read_text())
    source_pixels, source_records, material = load_source(selection)
    arrays = np.load(REPO / selection['npz'], allow_pickle=False)
    output = HERE / 'atlas'
    output.mkdir(exist_ok=True)
    remap = {}
    sides = {side: build_side(side, selection['sides'][side], arrays,
                             source_pixels, source_records, output, remap)
             for side in ('R', 'L')}
    mapping_path = HERE / 'uv_remap.npz'
    np.savez_compressed(mapping_path, **remap)
    mapping = {
        'schema_version': 1, 'source_selection': str(selection_path.relative_to(REPO)),
        'source_selection_sha256': sha(selection_path.read_bytes()),
        'source_selection_npz_sha256': selection['npz_sha256'],
        'npz': str(mapping_path.relative_to(REPO)), 'npz_sha256': sha(mapping_path.read_bytes()),
        'row_contract': 'Exactly selection compact vertex order; source_vertex_ids unchanged; no vertex/face splitting.',
        'transform': 'new_uv = source_uv * uniform_uv_scale + island_uv_offset; positive scalar, no rotation/reflection.',
        'image_row_contract': 'glTF image rows and TEXCOORD_0 V grow together; PNG rows are copied without Y flipping.',
        'sides': sides,
    }
    mapping_json = HERE / 'uv_remap.json'
    mapping_json.write_text(json.dumps(mapping, indent=2) + '\n')
    mip_sizes = []
    size = EDGE
    while True:
        mip_sizes.append(size)
        if size == 1:
            break
        size = max(1, size // 2)
    manifest = {
        'schema_version': 1, 'status': 'ATLAS_READY_AWAITING_BOUND_GLB_RENDER_AND_KTX_REVIEW',
        'formal_source': selection['formal_source'], 'formal_sha256': FORMAL_SHA,
        'png_source': selection['png_source'], 'png_sha256': PNG_SHA,
        'source_images': source_records, 'source_material_json': material,
        'selection': str(selection_path.relative_to(REPO)),
        'selection_sha256': mapping['source_selection_sha256'],
        'uv_remap': str(mapping_json.relative_to(REPO)), 'uv_remap_sha256': sha(mapping_json.read_bytes()),
        'uv_remap_npz': str(mapping_path.relative_to(REPO)), 'uv_remap_npz_sha256': sha(mapping_path.read_bytes()),
        'layout': {'atlas_edge': EDGE, 'source_texels_per_atlas_texel': 1,
                   'resampling': False, 'rotation': False, 'reflection': False,
                   'padded_rect_margin_pixels': PADDING,
                   'conservative_original_bilinear_guard_pixels': SAMPLING_GUARD,
                   'additional_nearest_seed_extrusion_pixels': EXTRUSION,
                   'gutter_limit': '16-pixel dilation protects local filtering only; coarse mips eventually blend islands. Runtime anisotropy and KTX mips require visual review.'},
        'normal_tangent_contract': {
            'source_has_tangent': False, 'atlas_adds_tangent': False,
            'normals_unchanged_by_atlas': True, 'normal_rgb_bytes_transformed': False,
            'uv_jacobian': 'Positive uniform scale on each original indexed UV island preserves tangent and bitangent directions and handedness before float32 rounding.',
            'runtime_requirement': 'Generate MikkTSpace tangent basis from valid NORMAL and remapped TEXCOORD_0. Runtime SDK behavior remains unverified.',
            'inherited_degenerate_uv': 'Original collapsed UV triangles retain one constant sample, and cannot define a tangent basis; no invented unwrap.'},
        'budget': {'source_three_rgb_level_zero_bytes': 3 * 4096 ** 2 * 3,
                   'atlas_six_rgb_level_zero_bytes': 6 * EDGE ** 2 * 3,
                   'atlas_six_rgb_complete_mips_theoretical_bytes': 6 * sum(s ** 2 for s in mip_sizes) * 3,
                   'mip_edges': mip_sizes,
                   'actual_png_bytes': sum(t['bytes'] for side in sides.values() for t in side['textures'].values()),
                   'ktx_actual_bytes': None, 'ktx_responsibility': 'Compression agent measures actual encoded KTX blocks and runtime-decoded allocation.'},
        'sides': sides,
        'verification': {'all_seed_pixels_byte_exact': True,
                         'png_round_trip_byte_exact': True,
                         'bilinear_rgb_max_byte_error': max(t['comparison']['max_rgb_byte_error'] for side in sides.values() for t in side['textures'].values()),
                         'source_images_not_copied_wholesale': True,
                         'source_and_selection_hash_guards': True,
                         'pending': ['independent mapped geometry checks', 'bound GLB PBR views', 'KTX compression pixel/mip review', 'PICO runtime tangent generation']},
        'phase': '阶段结束，等待 Root review；贴图产物已就绪，绑定与压缩验收仍待完成。',
    }
    manifest_path = HERE / 'atlas_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'atlas_manifest': str(manifest_path.relative_to(REPO)),
                      'sha256': sha(manifest_path.read_bytes()), 'budget': manifest['budget'],
                      'max_bilinear_byte_error': manifest['verification']['bilinear_rgb_max_byte_error']}))


class AtlasTests(unittest.TestCase):
    def test_source_pin_rejection_is_read_only(self):
        path = Path(__file__)
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            require_pin(path, '0' * 64)
        self.assertEqual(path.read_bytes(), before)

    def test_disconnected_islands_preserve_compact_vertex_order(self):
        groups = components(6, np.array([[0, 2, 1], [3, 4, 5]]))
        self.assertEqual([g.tolist() for g in groups], [[0, 1, 2], [3, 4, 5]])
        rectangles = pack_rectangles([(16, 8), (8, 16)], 24)
        self.assertEqual([rect[2:] for rect in rectangles], [(16, 8), (8, 16)])

    def test_overflow_is_rejected_without_resizing(self):
        with self.assertRaisesRegex(ValueError, 'exceed'):
            pack_rectangles([(20, 10)], 16)

    def test_collapsed_uv_keeps_nonempty_sampling_footprint(self):
        mask = conservative_mask(np.array([[5., 5.]] * 3), np.array([[0, 1, 2]]), (12, 12))
        self.assertTrue(mask[5, 5])
        donors = extrude_coordinates(mask, 2)
        ids = np.arange(144).reshape(12, 12)
        np.testing.assert_array_equal(donors[mask], ids[mask])

    def test_positive_uniform_map_preserves_derivative(self):
        uv = np.array([[.1, .2], [.2, .3], [.4, .1]])
        mapped = uv * (4096 / EDGE) + [.2, .15]
        np.testing.assert_allclose(np.diff(mapped, axis=0), np.diff(uv, axis=0) * (4096 / EDGE))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=[sys.argv[0]])
    else:
        build()
