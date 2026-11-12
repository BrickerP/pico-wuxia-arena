"""Independent native-hand asset verification; never modifies producer assets.

Run with host Python (NumPy/Pillow already used by the repository). This is an
asset/schema and numeric audit, not a Spatial SDK, decoder or device test.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from verify_weapon import read, values, local

FORMAL_SHA = 'ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20'
PNG_SHA = 'b3fbfe66727d0dd90bd741420937a6c57dbb9e083d76ecd983cd9383ab5bbf96'
DAO_SHA = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'
DAO_PNG_SHA = 'a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def path(value):
    result = Path(value)
    return result if result.is_absolute() else REPO / result


def digest(value):
    return hashlib.sha256(value.read_bytes()).hexdigest()


def view_bytes(document, binary, index):
    view = document['bufferViews'][index]
    start = view.get('byteOffset', 0)
    require(view.get('buffer', 0) == 0 and 0 <= start <= start + view['byteLength'] <= len(binary), 'Invalid embedded bufferView')
    return binary[start:start + view['byteLength']]


def image_bytes(document, binary, index):
    image = document['images'][index]
    require('uri' not in image and 'bufferView' in image, 'External image is not embedded')
    return view_bytes(document, binary, image['bufferView'])


def image_variant_equivalence(a, ab, b, bb):
    ignored = {'buffers', 'bufferViews', 'images', 'textures', 'extensionsUsed', 'extensionsRequired'}
    require({k: v for k, v in a.items() if k not in ignored} == {k: v for k, v in b.items() if k not in ignored}, 'Non-image JSON differs')
    image_views_a = {image['bufferView'] for image in a['images']}
    image_views_b = {image['bufferView'] for image in b['images']}
    require(image_views_a == image_views_b, 'Image resource ordering differs')
    require(len(a['bufferViews']) == len(b['bufferViews']), 'bufferView count differs')
    compared = 0
    for index, (first, second) in enumerate(zip(a['bufferViews'], b['bufferViews'])):
        if index in image_views_a:
            continue
        require({k: v for k, v in first.items() if k != 'byteOffset'} == {k: v for k, v in second.items() if k != 'byteOffset'}, 'Non-image view descriptor differs')
        require(view_bytes(a, ab, index) == view_bytes(b, bb, index), 'Non-image payload differs')
        compared += 1
    def textures(document):
        result = copy.deepcopy(document.get('textures', []))
        for texture in result:
            basis = texture.get('extensions', {}).pop('KHR_texture_basisu', None)
            if basis:
                texture['source'] = basis['source']
            if not texture.get('extensions'):
                texture.pop('extensions', None)
        return result
    require(textures(a) == textures(b), 'Texture role/sampler semantics differ')
    for key in ('extensionsUsed', 'extensionsRequired'):
        require([x for x in a.get(key, []) if x != 'KHR_texture_basisu'] == [x for x in b.get(key, []) if x != 'KHR_texture_basisu'], 'Non-image extension differs')
    return {'passed': True, 'non_image_json_exact': True, 'non_image_buffer_views_exact': compared, 'texture_role_and_sampler_semantics_exact': True}


def quat_matrix(q):
    q = np.asarray(q, float)
    require(q.shape == (4,) and np.isfinite(q).all() and np.linalg.norm(q) > 1e-12, 'Invalid quaternion')
    return local({'rotation': (q / np.linalg.norm(q)).tolist()})


def sampled_worlds(document, binary, clip_name=None, time=0):
    nodes = copy.deepcopy(document['nodes'])
    if clip_name is not None:
        clip = next(clip for clip in document['animations'] if clip.get('name') == clip_name)
        for channel in clip['channels']:
            target = channel['target']
            sampler = clip['samplers'][channel['sampler']]
            times = values(document, binary, sampler['input']).reshape(-1)
            outputs = values(document, binary, sampler['output']).astype(float)
            require(len(times) == len(outputs) and len(times) >= 2 and np.isfinite(times).all() and np.isfinite(outputs).all() and np.all(np.diff(times) > 0), 'Empty, nonfinite or unordered animation')
            require('matrix' not in nodes[target['node']], 'Animated node uses a matrix instead of TRS')
            right = int(np.searchsorted(times, time, side='right'))
            if right == 0:
                result = outputs[0]
            elif right >= len(times):
                result = outputs[-1]
            else:
                left = right - 1
                fraction = float((time - times[left]) / (times[right] - times[left]))
                if sampler.get('interpolation', 'LINEAR') == 'STEP':
                    result = outputs[left]
                else:
                    require(sampler.get('interpolation', 'LINEAR') == 'LINEAR', 'Unsupported animation interpolation')
                    first, second = outputs[left], outputs[right]
                    if target['path'] == 'rotation':
                        first, second = first / np.linalg.norm(first), second / np.linalg.norm(second)
                        cosine = float(first @ second)
                        if cosine < 0:
                            second, cosine = -second, -cosine
                        if cosine < .9995:
                            angle = math.acos(np.clip(cosine, -1, 1))
                            result = (math.sin((1-fraction)*angle)*first + math.sin(fraction*angle)*second) / math.sin(angle)
                        else:
                            result = (1-fraction)*first + fraction*second
                        result /= np.linalg.norm(result)
                    else:
                        result = (1-fraction)*first + fraction*second
            nodes[target['node']][target['path']] = result.tolist()
    parents = {child: index for index, node in enumerate(nodes) for child in node.get('children', [])}
    result = {}
    def world(index, stack=()):
        require(index not in stack, 'Node hierarchy cycle')
        if index not in result:
            matrix = local(nodes[index])
            result[index] = world(parents[index], (*stack, index)) @ matrix if index in parents else matrix
        return result[index]
    for index in range(len(nodes)):
        world(index)
    return result


def skin(document, binary, primitive, worlds, skin_index=0):
    attributes = primitive['attributes']
    points = values(document, binary, attributes['POSITION']).astype(float)
    palettes = values(document, binary, attributes['JOINTS_0']).astype(int)
    weights = values(document, binary, attributes['WEIGHTS_0']).astype(float)
    spec = document['accessors'][attributes['WEIGHTS_0']]
    if spec.get('normalized'):
        weights /= np.iinfo(values(document, binary, attributes['WEIGHTS_0']).dtype).max
    joints = document['skins'][skin_index]['joints']
    require(np.isfinite(points).all() and np.isfinite(weights).all() and np.all(weights >= 0), 'Nonfinite or negative skin data')
    require(palettes.min() >= 0 and palettes.max() < len(joints), 'Skin palette out of bounds')
    require(np.max(abs(weights.sum(axis=1)-1)) < 1e-4, 'Unnormalized skin weights')
    binds = values(document, binary, document['skins'][skin_index]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    require(len(binds) == len(joints) and np.isfinite(binds).all(), 'Invalid inverse bind matrices')
    transforms = np.array([worlds[index] for index in joints]) @ binds
    blended = np.sum(transforms[palettes] * weights[:, :, None, None], axis=1)
    return np.einsum('vij,vj->vi', blended, np.column_stack((points, np.ones(len(points)))))[:, :3]


def rigid(matrix):
    u, _, vt = np.linalg.svd(matrix[:3, :3])
    rotation = u @ vt
    require(np.linalg.det(rotation) > 0, 'Reflected anchor frame')
    result = np.eye(4)
    result[:3, :3], result[:3, 3] = rotation, matrix[:3, 3]
    return result


def source_and_selection():
    formal = REPO/'ArtSource/tripo-warrior/library/base.glb'
    png = formal.with_name('base_prepared_png.glb')
    require(digest(formal) == FORMAL_SHA and digest(png) == PNG_SHA, 'Pinned source mismatch')
    a, ab = read(formal)
    b, bb = read(png)
    report = {'formal_sha256': FORMAL_SHA, 'png_sha256': PNG_SHA, 'equivalence': image_variant_equivalence(a, ab, b, bb)}
    selection = json.loads((HERE/'selection.json').read_text())
    require(digest(path(selection['npz'])) == selection['npz_sha256'], 'Selection NPZ pin mismatch')
    data = np.load(path(selection['npz']))
    names = [b['nodes'][index]['name'] for index in b['skins'][0]['joints']]
    summaries = {}
    for side in ('R', 'L'):
        region = re.compile('^' + side + r'_(Forearm(?:Twist\d+)?|Hand|(?:Thumb|Index|Mid|Ring|Pinky)[123])$')
        total = 0
        for row in selection['sides'][side]['primitives']:
            primitive = b['meshes'][row['source_mesh']]['primitives'][row['source_primitive']]
            require(row['source_primitive'] in b['meshes'][row['source_mesh']]['extras']['body_primitive_indices'], 'Selection includes weapon/non-body primitive')
            prefix = row['npz_prefix']
            vertices, face_ids = data[prefix+'_source_vertex_ids'], data[prefix+'_source_face_ids']
            faces = values(b, bb, primitive['indices']).reshape(-1, 3).astype(int)
            palettes = values(b, bb, primitive['attributes']['JOINTS_0']).astype(int)
            weights = values(b, bb, primitive['attributes']['WEIGHTS_0'])
            dominant = palettes[np.arange(len(palettes)), weights.argmax(axis=1)]
            eligible = np.array([bool(region.fullmatch(names[index])) for index in dominant])
            expected = np.flatnonzero(eligible[faces].all(axis=1))
            require(np.array_equal(face_ids, expected), 'Selected face IDs differ from anatomical dominant-side rule')
            require(np.array_equal(data[prefix+'_source_triangles'], faces[face_ids]), 'Source face mapping changed')
            require(np.array_equal(vertices[data[prefix+'_indices']], faces[face_ids]), 'Compact topology remap incorrect')
            for attribute, index in primitive['attributes'].items():
                require(np.array_equal(data[prefix+'_'+attribute], values(b, bb, index)[vertices]), 'Selected attribute differs: '+attribute)
            total += len(face_ids)
        summaries[side] = {'triangles': total, 'vertices': selection['sides'][side]['vertices'], 'source_mapping_and_all_attributes_exact': True, 'head_torso_wrong_side_faces': 0}
    require(sum(row['triangles'] for row in summaries.values()) <= 20000, 'Combined triangle budget exceeded')
    report['selection'] = summaries
    dao = REPO/'app/src/main/assets/models/dao_grip.glb'
    dao_png = HERE.parent/'stage2/dao_grip_refined.glb'
    require(digest(dao) == DAO_SHA and digest(dao_png) == DAO_PNG_SHA, 'Formal dao/PNG companion pin mismatch')
    da, dab = read(dao)
    dp, dpb = read(dao_png)
    report['formal_dao_png_equivalence'] = image_variant_equivalence(da, dab, dp, dpb)
    return report, b, bb, selection, data, dp, dpb


def bilinear(image, uv, repeat=False):
    height, width = image.shape[:2]
    xy = uv * [width, height] - .5
    low = np.floor(xy).astype(int)
    fraction = xy - low
    if repeat:
        x0, y0 = low[:,0] % width, low[:,1] % height
        x1, y1 = (low[:,0]+1) % width, (low[:,1]+1) % height
    else:
        x0, y0 = np.clip(low[:,0], 0, width-1), np.clip(low[:,1], 0, height-1)
        x1, y1 = np.clip(low[:,0]+1, 0, width-1), np.clip(low[:,1]+1, 0, height-1)
    fx, fy = fraction[:,0,None], fraction[:,1,None]
    return (1-fy)*((1-fx)*image[y0,x0]+fx*image[y0,x1])+fy*((1-fx)*image[y1,x0]+fx*image[y1,x1])


def atlas_checks(document, binary, selection, selected):
    manifest = json.loads((HERE/'atlas_manifest.json').read_text())
    mapping = np.load(path(manifest['uv_remap_npz']))
    require(digest(path(manifest['uv_remap_npz'])) == manifest['uv_remap_npz_sha256'], 'Atlas UV NPZ pin mismatch')
    source_images = {}
    for role, spec in manifest['source_images'].items():
        source_images[role] = np.asarray(Image.open(io.BytesIO(image_bytes(document, binary, spec['source_image']))).convert('RGB'), dtype=np.uint8)
    result = {'sides': {}, 'sdk_tangent_generation': 'UNVERIFIED', 'normal_tangent_scope': 'Positive UV derivatives preserve existing parameter directions. Missing source TANGENT and collapsed source UV faces do not establish a valid SDK TBN.'}
    for side in ('R','L'):
        prefix = manifest['sides'][side]['npz_prefix']
        old = selected[prefix+'_TEXCOORD_0'].astype(float)
        new = mapping[prefix+'_TEXCOORD_0'].astype(float)
        island = mapping[prefix+'_vertex_island_ids']
        scale = float(mapping[prefix+'_uniform_uv_scale'][0])
        offsets = mapping[prefix+'_island_uv_offsets']
        require(scale > 0 and np.isfinite(new).all() and new.min() >= 0 and new.max() <= 1, 'UV reflection/nonfinite/outside atlas')
        require(np.array_equal(mapping[prefix+'_source_vertex_ids'], selected[prefix+'_source_vertex_ids']) and np.array_equal(mapping[prefix+'_source_uv'], old), 'Atlas compact/source UV identities differ')
        error = float(abs(new - (old*scale + offsets[island])).max())
        require(error < 1e-6, 'Atlas UV is not positive uniform scale + translation')
        faces = selected[prefix+'_indices'].astype(int)
        def determinant(uv):
            tri = uv[faces]
            first, second = tri[:,1]-tri[:,0], tri[:,2]-tri[:,0]
            return first[:,0]*second[:,1]-first[:,1]*second[:,0]
        before_area, after_area = determinant(old), determinant(new)
        valid = abs(before_area) > 1e-14
        require(np.all(before_area[valid]*after_area[valid] > 0), 'Atlas changed UV winding')
        zero_faces = selected[prefix+'_source_face_ids'][~valid]
        zero_islands = np.unique(island[faces[~valid]])
        samples_old = np.concatenate((old, old[faces].mean(axis=1)))
        samples_new = np.concatenate((new, new[faces].mean(axis=1)))
        textures = {}
        for role, spec in manifest['sides'][side]['textures'].items():
            filename = spec['path']
            require(digest(path(filename)) == spec['sha256'], 'Atlas image pin mismatch')
            with Image.open(path(filename)) as image:
                require(max(image.size) <= 2048 and image.mode == 'RGB', 'Atlas exceeds2K/RGB contract')
                image_data = np.asarray(image, dtype=np.uint8)
                dimensions = list(image.size)
            difference = float(abs(bilinear(source_images[role], samples_old, repeat=True)-bilinear(image_data, samples_new)).max())
            require(difference < .05, 'Atlas sampled source colors/directions differ')
            textures[role] = {'dimensions': dimensions, 'source_sample_max_byte_difference': difference, 'sample_positions': len(samples_old)}
        result['sides'][side] = {'positive_uniform_scale': scale, 'UV_transform_max_error': error, 'UV_winding_retained': True, 'degenerate_source_UV_face_ids': zero_faces.tolist(), 'degenerate_source_UV_face_count': len(zero_faces), 'degenerate_UV_island_ids': zero_islands.tolist(), 'degenerate_UV_island_count': len(zero_islands), 'textures': textures}
    return result


def accessor_storage(document,binary):
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    components={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}
    groups={}
    rows=[]
    for index,accessor in enumerate(document.get('accessors',[])):
        require('sparse' not in accessor,'Sparse accessor needs explicit storage support')
        require(accessor['type'] in widths and accessor['componentType'] in components,'Unsupported accessor encoding')
        count=accessor['count']
        require(isinstance(count,int) and count>0,'Empty/invalid accessor count')
        view=document['bufferViews'][accessor['bufferView']]
        width=components[accessor['componentType']]
        element=widths[accessor['type']]*width
        offset=accessor.get('byteOffset',0)
        stride=view.get('byteStride',element)
        require(offset>=0 and offset%width==0 and stride>=element,'Invalid accessor component alignment/stride')
        if 'byteStride' in view:
            require(stride%4==0 and 4<=stride<=252 and offset+element<=stride,'Invalid interleaved vertex row')
        span=(count-1)*stride+element
        require(offset+span<=view['byteLength'],'Accessor exceeds declared view payload')
        view_bytes(document,binary,accessor['bufferView'])
        groups.setdefault(accessor['bufferView'],[]).append((offset,offset+span,count,stride,element))
        rows.append({'accessor':index,'component_width_bytes':width,'components':widths[accessor['type']],
                     'count':count,'declared_element_bytes':element,'actual_row_stride':stride,'required_span_bytes':span})
    for index,spans in groups.items():
        view=document['bufferViews'][index]
        maximum=max(span[1] for span in spans)
        if 'byteStride' not in view:
            # This candidate writer emits tightly packed accessor payloads.
            # A u16 array labelled u8 is otherwise merely decoded as alternating
            # joint IDs/zeros and can still appear to have valid palette values.
            require(maximum==view['byteLength'],'Unaccounted no-stride payload bytes: possible componentType/dtype mismatch in view '+str(index))
        else:
            require(len({span[2] for span in spans})==1,'Interleaved view row counts disagree')
            require(maximum<=view['byteLength']<=spans[0][2]*view['byteStride'],'Unaccounted interleaved row payload')
    return {'all_declared_payloads_accounted':True,'views_checked':len(groups),'accessors':rows,
            'scope':'No-stride native candidate streams must exactly cover each payload; explicit valid interleaved row padding is allowed.'}


def validate_asset(document, binary, side):
    storage=accessor_storage(document,binary)
    for node in document['nodes']:
        require(np.isfinite(local(node)).all(),'Nonfinite node transform')
        require(not ('matrix' in node and any(k in node for k in ('translation','rotation','scale'))),'Node mixes matrix and TRS')
        if 'rotation' in node:
            require(abs(np.linalg.norm(node['rotation'])-1)<1e-3,'Invalid node quaternion')
    require(bool(document.get('skins')) and bool(document.get('meshes')) and bool(document.get('animations')), 'Missing skin/mesh/animation')
    require(len(document['scenes'][document.get('scene',0)]['nodes']) == 1, 'Expected one logical root')
    roots = document['scenes'][document.get('scene',0)]['nodes']
    require(np.allclose(local(document['nodes'][roots[0]]), np.eye(4), atol=1e-6), 'Logical scene root not identity')
    expected = {side+'_'+finger+str(segment) for finger in ('Thumb','Index','Mid','Ring','Pinky') for segment in (1,2,3)}
    clip = next((clip for clip in document['animations'] if clip.get('name') == 'grip'), None)
    require(clip is not None and bool(clip.get('channels')), 'Empty/missing grip animation')
    require(len(document['animations'])==1 and len(clip['channels'])==15,'Unexpected/duplicate animation channels')
    targets = set()
    for channel in clip['channels']:
        name = document['nodes'][channel['target']['node']]['name']
        require(channel['target']['path'] == 'rotation' and name in expected, 'Animation changes non-finger/TRS channel')
        targets.add(name)
        sampler = clip['samplers'][channel['sampler']]
        times = values(document,binary,sampler['input']).reshape(-1)
        output = values(document,binary,sampler['output'])
        require(len(times) >= 2 and len(output) == len(times) and np.isfinite(times).all() and np.isfinite(output).all(), 'Empty/nonfinite grip keys')
        require(abs(float(times[0])) < 1e-7 and abs(float(times[-1])-1) < 1e-7 and np.all(np.diff(times)>0), 'Grip time range not0open→1closed')
        require(np.max(abs(np.linalg.norm(output,axis=1)-1)) < 1e-4, 'Non-unit finger quaternion')
    require(targets == expected, 'Grip does not cover all15 real finger joints')
    worlds = {time: sampled_worlds(document,binary,'grip',time) for time in (0,.5,1)}
    summary = []
    for node in document['nodes']:
        if 'mesh' not in node:
            continue
        require('skin' in node, 'Hand primitive is not skinned')
        for primitive in document['meshes'][node['mesh']]['primitives']:
            attributes = primitive['attributes']
            require({'POSITION','NORMAL','JOINTS_0','WEIGHTS_0'} <= set(attributes), 'Hand attributes missing')
            material = document['materials'][primitive['material']]
            if 'normalTexture' in material or any(k.endswith('Texture') for k in material.get('pbrMetallicRoughness',{})):
                require('TEXCOORD_0' in attributes, 'Textured primitive UV missing')
            points = values(document,binary,attributes['POSITION'])
            indices = values(document,binary,primitive['indices']).reshape(-1)
            require(len(indices)>0 and len(indices)%3==0 and indices.min()>=0 and indices.max()<len(points), 'Invalid/empty triangle indices')
            require(all(np.isfinite(values(document,binary,index)).all() for index in attributes.values()), 'Nonfinite attribute')
            normal_lengths=np.linalg.norm(values(document,binary,attributes['NORMAL']),axis=1)
            require(np.max(abs(normal_lengths-1))<1e-3,'Invalid normal magnitude')
            posed = {time: skin(document,binary,primitive,world,node['skin']) for time,world in worlds.items()}
            referenced = np.unique(indices.astype(int))
            movement = np.linalg.norm(posed[1][referenced]-posed[0][referenced],axis=1)
            summary.append({'triangles':len(indices)//3, 'accessor_vertices':len(points), 'surface_referenced_vertices':len(referenced), 'unreferenced_accessor_vertices':len(points)-len(referenced), 'open_closed_skin_max_metres':float(movement.max()), 'open_closed_skin_p95_metres':float(np.percentile(movement,95)), 'closed_surface_bounds_metres':[posed[1][referenced].min(axis=0).tolist(),posed[1][referenced].max(axis=0).tolist()]})
    require(max(row['open_closed_skin_max_metres'] for row in summary) > .001, 'Grip keys do not produce actual skin deformation')
    root = roots[0]
    require(np.allclose(worlds[0][root],worlds[1][root],atol=1e-8), 'Logical root moves during grip')
    return {'accessor_storage':storage,'side':side,'logical_root_identity':True,'real15_joint_grip':True,'mid_pose_evaluated':True,'primitives':summary}


def named_worlds(document, binary, clip=None, time=0):
    worlds = sampled_worlds(document,binary,clip,time)
    return {node["name"]: worlds[index] for index,node in enumerate(document["nodes"])}


def rotation_x(angle):
    result=np.eye(4)
    result[1:3,1:3]=[[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]
    return result


def endpoint_rotation(document,binary,name,time):
    clip=next(clip for clip in document["animations"] if clip["name"]=="grip")
    channel=next(channel for channel in clip["channels"] if document["nodes"][channel["target"]["node"]]["name"]==name)
    output=values(document,binary,clip["samplers"][channel["sampler"]]["output"])
    return quat_matrix(output[0 if time==0 else -1])[:3,:3]


def source_idle_rotation(document,binary,name):
    node=next(i for i,n in enumerate(document["nodes"]) if n["name"]==name)
    clip=next(clip for clip in document["animations"] if clip["name"]=="idle")
    channel=next(c for c in clip["channels"] if c["target"]=={"node":node,"path":"rotation"})
    return quat_matrix(values(document,binary,clip["samplers"][channel["sampler"]]["output"])[0])[:3,:3]


def frames_and_correspondence(document,binary,side,record,source,source_binary,selected,mapping,dao,dao_binary):
    source_world=named_worlds(source,source_binary)
    output_world={t:named_worlds(document,binary,"grip",t) for t in (0,.5,1)}
    if side=="R":
        conversion=rotation_x(-math.pi/2)@np.linalg.inv(rigid(source_world["HandGrip_R"]))
    else:
        wrist=source_world["L_Hand"][:3,3]
        forward=np.mean([source_world["L_"+finger+"3"][:3,3] for finger in ("Index","Mid","Ring","Pinky")],axis=0)-wrist
        forward/=np.linalg.norm(forward)
        radial=source_world["L_Index1"][:3,3]-source_world["L_Pinky1"][:3,3]
        radial-=forward*(radial@forward)
        radial/=np.linalg.norm(radial)
        dorsal=np.cross(radial,forward)
        frame=np.eye(4)
        frame[:3,:3]=np.column_stack((radial,dorsal,-forward))
        frame[:3,3]=wrist
        conversion=np.linalg.inv(frame)
    declared=np.array(record["source_asset_to_output_matrix_gltf"]).reshape(4,4).T
    require(np.allclose(conversion,declared,atol=3e-6,rtol=0),"Declared logical-frame transform differs from actual source anatomy")
    names={n["name"]:i for i,n in enumerate(source["nodes"])}
    fingers={side+"_"+finger+str(segment) for finger in ("Thumb","Index","Mid","Ring","Pinky") for segment in (1,2,3)}
    maximum_rest_error=maximum_root_drift=0.0
    for name,old in source_world.items():
        if name not in output_world[0]:
            continue
        maximum_rest_error=max(maximum_rest_error,float(abs(output_world[0][name]-conversion@old).max()))
        if name not in fingers:
            maximum_root_drift=max(maximum_root_drift,float(abs(output_world[0][name]-output_world[1][name]).max()))
    require(maximum_rest_error<3e-6 and maximum_root_drift<1e-8,"Source default pose/frame scale or non-finger pose changed")
    old_scales=np.linalg.svd(source_world[side+"_Hand"][:3,:3],compute_uv=False)
    new_scales=np.linalg.svd(output_world[0][side+"_Hand"][:3,:3],compute_uv=False)
    require(np.max(abs(new_scales-old_scales))<2e-6 and old_scales.min()>1.7,"Source normalization cancelled or altered")
    source_joints=source["skins"][0]["joints"]
    output_joints=document["skins"][0]["joints"]
    require([source["nodes"][i]["name"] for i in source_joints]==[document["nodes"][i]["name"] for i in output_joints],"Joint palette identity/order changed")
    require(values(source,source_binary,source["skins"][0]["inverseBindMatrices"]).tobytes()==values(document,binary,document["skins"][0]["inverseBindMatrices"]).tobytes(),"Source inverse binds changed")
    default_world=sampled_worlds(document,binary)
    default_expected_world=sampled_worlds(document,binary,'grip',1 if side=='R' else 0)
    default_skin_error=0.0
    for primitive in document['meshes'][0]['primitives']:
        default_points=skin(document,binary,primitive,default_world)
        target_points=skin(document,binary,primitive,default_expected_world)
        default_skin_error=max(default_skin_error,float(np.linalg.norm(default_points-target_points,axis=1).max()))
    require(default_skin_error<1e-6,'Actual default LBS does not match Rclosed/Lopen endpoint')
    correspondence=[]
    uv=np.load(path(mapping["uv_remap_npz"]))
    for item in record["primitive_mapping"]:
        primitive=document["meshes"][0]["primitives"][item["output_primitive"]]
        prefix=item["npz_prefix"]
        require(np.array_equal(values(document,binary,primitive["indices"]).reshape(-1,3),selected[prefix+"_indices"]),"Selected hand topology changed")
        for semantic,index in primitive["attributes"].items():
            expected=uv[prefix+"_TEXCOORD_0"] if semantic=="TEXCOORD_0" else selected[prefix+"_"+semantic]
            require(np.array_equal(values(document,binary,index),expected),"Selected hand attribute changed: "+semantic)
        source_primitive=source["meshes"][item["source_mesh"]]["primitives"][item["source_primitive"]]
        original=skin(source,source_binary,source_primitive,sampled_worlds(source,source_binary))[selected[prefix+"_source_vertex_ids"]]
        expected=(np.column_stack((original,np.ones(len(original))))@conversion.T)[:,:3]
        actual=skin(document,binary,primitive,sampled_worlds(document,binary,"grip",0))
        error=float(np.max(abs(actual-expected)))
        require(error<3e-6,"Actual skinned open hand differs from rigid-stripped source")
        correspondence.append({"source_vertex_mapping_exact":True,"maximum_open_world_component_error_metres":error})
    default_errors={}
    target_names={node['name']:i for i,node in enumerate(document['nodes'])}
    for name,index in names.items():
        if name not in target_names:continue
        candidate_local=local(document['nodes'][target_names[name]])
        expected_local=local(source['nodes'][index])
        if side=='R' and name in fingers:
            expected_local=expected_local.copy()
            scales=np.linalg.norm(expected_local[:3,:3],axis=0)
            expected_local[:3,:3]=source_idle_rotation(source,source_binary,name)@np.diag(scales)
        error=float(abs(candidate_local-expected_local).max())
        require(error<3e-6,'Default node pose differs from Rclosed/Lopen contract: '+name)
        default_errors[name]=error
    closed_errors={}
    reflection=np.diag([-1,1,1])
    for name in sorted(fingers):
        actual=endpoint_rotation(document,binary,name,1)
        right="R_"+name[2:]
        right_closed=source_idle_rotation(source,source_binary,right)
        if side=="R":
            expected=right_closed
        else:
            right_open=rigid(local(source["nodes"][names[right]]))[:3,:3]
            left_open=rigid(local(source["nodes"][names[name]]))[:3,:3]
            delta=right_open.T@right_closed
            right_basis=rigid(source_world[right])[:3,:3]
            left_basis=rigid(source_world[name])[:3,:3]
            mirrored=reflection@right_basis@delta@right_basis.T@reflection
            expected=left_open@left_basis.T@mirrored@left_basis
        error=float(abs(actual-expected).max())
        require(error<2e-6,"Closed finger provenance/orientation mismatch: "+name)
        closed_errors[name]=error
    frames={}
    if side=="R":
        native=rigid(output_world[0]["HandGrip_R"])
        converted=native@rotation_x(math.pi/2)
        require(np.allclose(converted,np.eye(4),atol=2e-6),"Converted actual right grip is not player Grip identity")
        dao_world=named_worlds(dao,dao_binary)
        marker_data={}
        for name in ("Blade_Base","Blade_Tip"):
            error=float(abs(output_world[0][name]-dao_world[name]).max())
            require(error<3e-6,"Actual blade marker full matrix differs from formal dao: "+name)
            marker_data[name]={"output_world_matrix_gltf":output_world[0][name].T.reshape(-1).tolist(),"formal_dao_world_matrix_gltf":dao_world[name].T.reshape(-1).tolist(),"maximum_matrix_error":error,"position_error_metres":float(np.linalg.norm(output_world[0][name][:3,3]-dao_world[name][:3,3])),"linear_axes_max_error":float(abs(output_world[0][name][:3,:3]-dao_world[name][:3,:3]).max())}
        frames={"source_internal_grip_rigid_matrix_gltf":native.T.reshape(-1).tolist(),"converted_grip_matrix_gltf":converted.T.reshape(-1).tolist(),"converted_axes_identity_error":float(abs(converted[:3,:3]-np.eye(3)).max()),"converted_grip_origin_error_metres":float(np.linalg.norm(converted[:3,3])),"actual_formal_dao_markers":marker_data}
    else:
        wrist=output_world[0]["L_Hand"][:3,3]
        require(np.linalg.norm(wrist)<2e-6,"Left anatomical wrist is not logical origin")
        frames={"actual_anatomical_wrist_position_metres":wrist.tolist(),"closed_pose_provenance":"rest-basis mirrored R curl; derived, not authored/calibrated L closed"}
    return {"source_open_world_correspondence":correspondence,"independent_f64_vs_declared_f32_frame_max_error":float(abs(conversion-declared).max()),"numeric_matrix_comparison_bound":3e-6,"maximum_open_pose_node_matrix_error":maximum_rest_error,"default_pose_contract":"R actual source idle0 closed; L source rest open; only R default15 finger rotation may change","actual_default_to_required_clip_LBS_max_error_metres":default_skin_error,"maximum_default_local_matrix_error":max(default_errors.values()),"maximum_nonfinger_root_pose_drift":maximum_root_drift,"source_wrist_singular_scales":old_scales.tolist(),"output_wrist_singular_scales":new_scales.tolist(),"source_normalization_scale_preserved":True,"all78_joint_palette_and_inverse_binds_exact":True,"closed_finger_provenance_matrix_errors":closed_errors,"frames":frames}


def embedded_atlas(document,binary,side,manifest):
    material=document["materials"][0]
    original=manifest["source_material_json"]
    require(material==original,"Hand source material scalars/texture role indices changed")
    role_indices={"normal":material["normalTexture"]["index"],"base_color":material["pbrMetallicRoughness"]["baseColorTexture"]["index"],"metallic_roughness":material["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"]}
    result={}
    for role,index in role_indices.items():
        texture=document["textures"][index]
        sampler=document["samplers"][texture["sampler"]]
        require(sampler.get("wrapS")==sampler.get("wrapT")==33071,"Hand atlas sampler not clamp")
        data=image_bytes(document,binary,texture["source"])
        spec=manifest["sides"][side]["textures"][role]
        require(hashlib.sha256(data).hexdigest()==spec["sha256"],"Bound atlas pixels/payload differ from reviewed PNG")
        with Image.open(io.BytesIO(data)) as image:
            require(image.size==(1536,1536) and image.mode=="RGB","Hand texture dimensions/channels invalid")
        result[role]={"embedded_exact_png":True,"dimensions":[1536,1536],"sampler_clamp":True}
    return result


def contract_negative_tests(document,binary,side):
    cases=[]
    changed=copy.deepcopy(document)
    changed["animations"]=[]
    mutations=[("empty_animation",changed,binary)]
    changed=copy.deepcopy(document)
    root=changed["scenes"][changed.get("scene",0)]["nodes"][0]
    changed["nodes"][root]["translation"]=[.001,0,0]
    mutations.append(("logical_root_offset",changed,binary))
    primitive=document["meshes"][0]["primitives"][0]
    for label,index,payload in (("nonfinite_position",primitive["attributes"]["POSITION"],struct.pack("<f",float("nan"))), ("out_of_range_index",primitive["indices"],None)):
        accessor=document["accessors"][index]
        view=document["bufferViews"][accessor["bufferView"]]
        offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
        changed=bytearray(binary)
        if payload is None:
            width={5121:1,5123:2,5125:4}[accessor["componentType"]]
            payload=((1<<(8*width))-1).to_bytes(width,"little")
        changed[offset:offset+len(payload)]=payload
        mutations.append((label,document,bytes(changed)))
    for label,doc,payload in mutations:
        try:
            validate_asset(doc,payload,side)
        except (ValueError,StopIteration,IndexError):
            cases.append(label)
        else:
            raise ValueError("Invalid candidate contract accepted: "+label)
    return {"scope":"Candidate asset/schema validation only, not SDK grip-input behavior","normal_asset_passed":True,"mutations_rejected":cases}


def compression_checks(png_doc,png_bin,final_path):
    compressed,binary=read(final_path)
    equivalence=image_variant_equivalence(png_doc,png_bin,compressed,binary)
    sys.path.insert(0,str(REPO/"ArtSource/refinement/pbr-compression"))
    from compress_pbr import check_ktx
    roles={}
    material=compressed["materials"][0]
    indices={"normal":material["normalTexture"]["index"],"base_color":material["pbrMetallicRoughness"]["baseColorTexture"]["index"],"metallic_roughness":material["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"]}
    for role,index in indices.items():
        texture=compressed["textures"][index]
        require("KHR_texture_basisu" in texture.get("extensions",{}),"Missing BasisU texture binding")
        image=texture["extensions"]["KHR_texture_basisu"]["source"]
        roles[role]=check_ktx(image_bytes(compressed,binary,image),"srgb" if role=="base_color" else "linear",[1536,1536])
    return {"sha256":digest(final_path),"PNG_KTX_nonimage_equivalence":equivalence,"embedded_KTX_roles":roles,"SDK_decode_and_gpu_memory_unverified":True}


def weld_positions(points,epsilon=1e-7):
    # Neighbour-cell lookup avoids treating legitimate UV/normal seams or
    # points straddling a rounding boundary as distinct topological vertices.
    cells={}
    representatives=[]
    aliases=np.empty(len(points),int)
    for index,point in enumerate(points):
        cell=tuple(np.floor(point/epsilon).astype(np.int64))
        found=None
        for x in (-1,0,1):
            for y in (-1,0,1):
                for z in (-1,0,1):
                    for candidate in cells.get((cell[0]+x,cell[1]+y,cell[2]+z),()):
                        if np.linalg.norm(point-representatives[candidate])<=epsilon:
                            found=candidate
                            break
                    if found is not None:break
                if found is not None:break
            if found is not None:break
        if found is None:
            found=len(representatives)
            representatives.append(point)
            cells.setdefault(cell,[]).append(found)
        aliases[index]=found
    return np.asarray(representatives),aliases


def edge_topology(points,faces):
    unique,weld=weld_positions(points)
    welded_faces=weld[faces]
    directed=np.concatenate((welded_faces[:,[0,1]],welded_faces[:,[1,2]],welded_faces[:,[2,0]]))
    edges=np.sort(directed,axis=1)
    unique_edges,inverse,counts=np.unique(edges,axis=0,return_inverse=True,return_counts=True)
    winding=np.bincount(inverse,weights=np.where(directed[:,0]<directed[:,1],1,-1),minlength=len(unique_edges))
    return {'position_weld_epsilon_metres':1e-7,'welded_vertices':len(np.unique(welded_faces)),
            'open_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),
            'inconsistent_two_face_edge_orientation':int(((counts==2)&(winding!=0)).sum())},weld,unique_edges[counts==1]


def triangle_pair_intersection(a,b,shared_vertices):
    epsilon=1e-7
    normals=[np.cross(t[1]-t[0],t[2]-t[0]) for t in (a,b)]
    lengths=[np.linalg.norm(n) for n in normals]
    if min(lengths)<1e-14:return False
    na,nb=[normal/length for normal,length in zip(normals,lengths)]
    if max(abs((a-b[0])@nb).max(),abs((b-a[0])@na).max())<=epsilon:
        axis=int(abs(na).argmax())
        first,second=np.delete(a,axis,axis=1),np.delete(b,axis,axis=1)
        cross=lambda x,y:float(x[0]*y[1]-x[1]*y[0])
        orientation=1 if cross(second[1]-second[0],second[2]-second[0])>=0 else -1
        polygon=list(first)
        for start,end in zip(second,np.roll(second,-1,axis=0)):
            if not polygon:return False
            output=[]
            previous=polygon[-1]
            dp=cross(end-start,previous-start)*orientation
            for point in polygon:
                dc=cross(end-start,point-start)*orientation
                if (dp>=-1e-14)!=(dc>=-1e-14):
                    output.append(previous+dp/(dp-dc)*(point-previous))
                if dc>=-1e-14:output.append(point)
                previous,dp=point,dc
            polygon=output
        if len(polygon)<3:return False
        polygon=np.asarray(polygon)
        area=abs(np.sum(polygon[:,0]*np.roll(polygon[:,1],-1)-polygon[:,1]*np.roll(polygon[:,0],-1)))*.5
        return area>1e-12
    # Adjacent noncoplanar triangles meet only on their shared edge.
    if shared_vertices>=2:return False
    intersections=[]
    def in_triangle(point,t):
        e,f=t[1]-t[0],t[2]-t[0]
        d=point-t[0]
        aa,ab,bb=e@e,e@f,f@f
        denominator=aa*bb-ab*ab
        if abs(denominator)<1e-24:return False
        u=(bb*(d@e)-ab*(d@f))/denominator
        v=(aa*(d@f)-ab*(d@e))/denominator
        return u>=-1e-7 and v>=-1e-7 and u+v<=1+1e-7
    for triangle,target,normal in ((a,b,nb),(b,a,na)):
        distances=(triangle-target[0])@normal
        for index in range(3):
            after=(index+1)%3
            d0,d1=distances[index],distances[after]
            if abs(d0-d1)<1e-12:continue
            fraction=d0/(d0-d1)
            if -1e-8<=fraction<=1+1e-8:
                point=triangle[index]+fraction*(triangle[after]-triangle[index])
                if in_triangle(point,target) and not any(np.linalg.norm(point-old)<epsilon for old in intersections):intersections.append(point)
    return len(intersections)>=2 and max(np.linalg.norm(a-b) for a in intersections for b in intersections)>epsilon


def cap_checks(document,binary,record):
    original_count=len(record['primitive_mapping'])
    mesh=document['meshes'][0]
    if len(mesh['primitives'])==original_count:
        return {'present':False,'status':'Awaiting approved cuff closure; pre-cap mesh is not a final candidate'}
    positions=[]
    triangles=[]
    palettes=[]
    weights=[]
    labels=[]
    offset=0
    default_world=sampled_worlds(document,binary,'grip',0)
    for index,primitive in enumerate(mesh['primitives']):
        attributes=primitive['attributes']
        p=values(document,binary,attributes['POSITION']).astype(float)
        f=values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
        j=values(document,binary,attributes['JOINTS_0']).astype(int)
        w=values(document,binary,attributes['WEIGHTS_0']).astype(float)
        require(np.isfinite(p).all() and np.isfinite(w).all() and j.shape[1]==w.shape[1]==4 and np.all(w>=0) and abs(w.sum(axis=1)-1).max()<1e-4,'Invalid cap max4 normalized skin')
        positions.append(skin(document,binary,primitive,default_world))
        triangles.append(f+offset)
        palettes.append(j)
        weights.append(w)
        labels.extend([index]*len(f))
        offset+=len(p)
        if index>=original_count:
            material=document['materials'][primitive['material']]
            pbr=material.get('pbrMetallicRoughness',{})
            color=pbr.get('baseColorFactor',[1,1,1,1])
            require('normalTexture' not in material and 'baseColorTexture' not in pbr,'Cuff cap must use explicit solid cloth material without normal map')
            require(max(color[:3])>1e-8,'Pure black occlusion patch is not accepted')
    points=np.concatenate(positions)
    faces=np.concatenate(triangles)
    joints=np.concatenate(palettes)
    influence=np.concatenate(weights)
    label=np.asarray(labels)
    cap_faces=np.flatnonzero(label>=original_count)
    old_faces=np.flatnonzero(label<original_count)
    before,_,_=edge_topology(points,faces[old_faces])
    after,weld,boundary=edge_topology(points,faces)
    require(after['open_edges']==after['nonmanifold_edges']==after['inconsistent_two_face_edge_orientation']==0,'Combined hand/cap is not closed oriented manifold after position welding')
    skin_names=document['skins'][0]['joints']
    dense=np.zeros((len(points),len(skin_names)))
    for slot in range(4):np.add.at(dense,(np.arange(len(points)),joints[:,slot]),influence[:,slot])
    old_vertex_count=sum(len(p) for p in positions[:original_count])
    decoded_cap_palette=[]
    for index in range(original_count,len(palettes)):
        active=palettes[index][weights[index]>0]
        decoded_cap_palette.append({'primitive':index,'componentType':document['accessors'][mesh['primitives'][index]['attributes']['JOINTS_0']]['componentType'],'actual_decoded_palette_min':int(palettes[index].min()),'actual_decoded_palette_max':int(palettes[index].max()),'effective_joint_names':[document['nodes'][skin_names[i]]['name'] for i in np.unique(active)]})
    shared_error=0.0
    for group in np.unique(weld[:old_vertex_count]):
        aliases=np.flatnonzero(weld==group)
        if np.any(aliases>=old_vertex_count):shared_error=max(shared_error,float(abs(dense[aliases]-dense[aliases[0]]).max()))
    require(shared_error<1e-6,'Cap boundary skin weights differ from original source aliases')
    tri=points[faces]
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5
    require(np.all(area[cap_faces]>1e-12),'Degenerate new cap triangle')
    default_joints=document['skins'][0]['joints']
    inverse_bind=values(document,binary,document['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    skin_matrices=np.array([default_world[index] for index in default_joints])@inverse_bind
    posed_normals=[]
    for index,primitive in enumerate(mesh['primitives']):
        normal=values(document,binary,primitive['attributes']['NORMAL']).astype(float)
        blend=np.sum(skin_matrices[palettes[index]]*weights[index][:,:,None,None],axis=1)
        transformed=np.einsum('vij,vj->vi',np.linalg.inv(blend[:,:3,:3]).transpose(0,2,1),normal)
        transformed/=np.linalg.norm(transformed,axis=1)[:,None]
        posed_normals.append(transformed)
    posed_normals=np.concatenate(posed_normals)
    face_normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])/(2*area[:,None])
    vertex_normals=posed_normals[faces].mean(axis=1)
    normal_cosine=np.einsum('ij,ij->i',face_normals[cap_faces],vertex_normals[cap_faces])
    original_normal_dot=np.einsum('ij,ij->i',face_normals[old_faces],vertex_normals[old_faces])
    inherited_normal_ids=old_faces[original_normal_dot<-1e-5]
    source_arrays=np.load(HERE/'selection.npz')
    inherited_normal_source=[]
    offsets=np.cumsum([0]+[len(values(document,binary,p['indices']).reshape(-1,3)) for p in mesh['primitives']])
    for face in inherited_normal_ids:
        primitive_index=int(label[face])
        source_mapping=next(item for item in record['primitive_mapping'] if item['output_primitive']==primitive_index)
        local_face=int(face-offsets[primitive_index])
        inherited_normal_source.append(int(source_arrays[source_mapping['npz_prefix']+'_source_face_ids'][local_face]))
    cap_errors=[]
    normal_disagreement=cap_faces[normal_cosine<-1e-5]
    if len(normal_disagreement):
        cap_errors.append('New cap signed-average vertex-normal/geometry-face dot is negative; smooth-fan crease conflict, not by itself a geometric winding inversion claim')
    endpoint_topology={}
    for time in (.5,1):
        world=sampled_worlds(document,binary,'grip',time)
        endpoint=np.concatenate([skin(document,binary,primitive,world) for primitive in mesh['primitives']])
        endpoint_report,_,_=edge_topology(endpoint,faces)
        require(endpoint_report['open_edges']==endpoint_report['nonmanifold_edges']==endpoint_report['inconsistent_two_face_edge_orientation']==0,'Closure fails in actual animated pose')
        endpoint_topology[str(time)]=endpoint_report
    low,high=tri.min(axis=1),tri.max(axis=1)
    crossings=[]
    for first in cap_faces:
        candidates=np.flatnonzero(((high+1e-7>=low[first])&(low-1e-7<=high[first])).all(axis=1))
        for second in candidates:
            if first==second or (second in cap_faces and second<first):continue
            shared=len(set(weld[faces[first]])&set(weld[faces[second]]))
            if triangle_pair_intersection(tri[first],tri[second],shared):crossings.append([int(first),int(second)])
    if crossings:
        cap_errors.append('New cap surface intersections detected: '+str(crossings[:12]))
    return {'inherited_original_normal_face_disagreements':{'count':len(inherited_normal_ids),'compact_face_ids':inherited_normal_ids.tolist(),'source_face_ids':inherited_normal_source,'scope':'Existing source grip0/open smooth-normal disagreement; limitation only, not generated-cap blocking count'},'present':True,'passed':not cap_errors,'errors':cap_errors,'new_cap_normal_disagreement_combined_face_ids':normal_disagreement.tolist(),'original_boundary_topology':before,'closed_combined_topology':after,
            'actual_decoded_cap_joint_palettes':decoded_cap_palette,'new_primitives':len(mesh['primitives'])-original_count,'new_triangles':len(cap_faces),'animated_mid_closed_topology':endpoint_topology,'new_cap_minimum_signed_average_vertex_normal_face_dot':float(normal_cosine.min()),'normal_metric_formula':'mean_i(dot(unit(actual geometric face normal), unit(actual LBS transformed vertex normal_i)))',
            'cap_materials':[document['materials'][p['material']] for p in mesh['primitives'][original_count:]],
            'minimum_new_world_triangle_area_m2':float(area[cap_faces].min()),'boundary_dense_skin_max_error':shared_error,
            'new_surface_intersection_count':len(crossings),'self_intersection_scope':'New-vs-original/new triangles, welded-edge adjacency and coplanar positive-area overlaps handled; existing original-vs-original contacts are not reclassified.'}


def geometry_control_tests():
    points=np.array(((0,0,0),(1,0,0),(0,1,0),(0,0,1)),float)
    faces=np.array(((0,2,1),(0,1,3),(0,3,2),(1,2,3)),int)
    # Every triangle gets distinct accessor vertices, as legitimate UV seams do.
    split_points=points[faces].reshape(-1,3)
    split_faces=np.arange(12).reshape(-1,3)
    closed,_,_=edge_topology(split_points,split_faces)
    require(closed['open_edges']==closed['nonmanifold_edges']==closed['inconsistent_two_face_edge_orientation']==0,'UV-seam topology control failed')
    opened,_,_=edge_topology(points,faces[:-1])
    require(opened['open_edges']==3,'Open-boundary control failed')
    nonmanifold,_,_=edge_topology(points,np.concatenate((faces,faces[:1])))
    require(nonmanifold['nonmanifold_edges']==3,'Nonmanifold control failed')
    first=np.array(((-1,-1,0),(1,-1,0),(0,1,0)),float)
    crossing=np.array(((0,-.5,-1),(0,-.5,1),(0,.5,0)),float)
    require(triangle_pair_intersection(first,crossing,0),'Noncoplanar crossing control failed')
    require(triangle_pair_intersection(first,first+[.2,0,0],0),'Coplanar overlap control failed')
    adjacent=np.array(((-1,-1,0),(1,-1,0),(0,-2,0)),float)
    require(not triangle_pair_intersection(first,adjacent,2),'Legal shared-edge control failed')
    require(not triangle_pair_intersection(first,first+[0,0,.1],0),'Separated triangle control failed')
    tight={'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':4}],
           'accessors':[{'bufferView':0,'count':1,'type':'VEC4','componentType':5121}]}
    accessor_storage(tight,b'\x00'*4)
    mismatch=copy.deepcopy(tight)
    mismatch['bufferViews'][0]['byteLength']=8
    try:
        accessor_storage(mismatch,b'\x00'*8)
    except ValueError:
        pass
    else:
        raise ValueError('u16 payload with u8 descriptor was accepted')
    interleaved={'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':32,'byteStride':16}],
                 'accessors':[{'bufferView':0,'count':2,'type':'VEC3','componentType':5126}]}
    accessor_storage(interleaved,b'\x00'*32)
    return {'storage_controls':['valid tightly packed u8','u16/u8 payload mismatch rejected','valid explicit interleaved stride'], 'passed':True,'cases':['UV-split closed manifold','open boundary','nonmanifold','noncoplanar crossing','coplanar positive-area overlap','legal shared edge','separated triangles'],'scope':'Offline geometry/contract helper controls only'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources-only',action='store_true')
    parser.add_argument('--pre-cap',action='store_true')
    parser.add_argument('--png-only',action='store_true')
    args=parser.parse_args()
    snapshots={}
    report={'geometry_controls':geometry_control_tests(),'scope':'Independent offline assets/schema/skin/texture audit only; no native SDK input, decode, render or device acceptance.','errors':[],'pending':[]}
    try:
        source,document,binary,selection,selected,dao,dao_binary=source_and_selection()
        report['source_and_selection']=source
        if (HERE/'atlas_manifest.json').exists():
            report['atlas']=atlas_checks(document,binary,selection,selected)
        if not args.sources_only:
            rig=json.loads((HERE/'rig_manifest.json').read_text())
            atlas=json.loads((HERE/'atlas_manifest.json').read_text())
            require(digest(HERE/'atlas_manifest.json')==rig['atlas_manifest_sha256'],'Rig atlas pin mismatch')
            require(digest(HERE/'uv_remap.npz')==rig['uv_remap_npz_sha256'],'Rig remap pin mismatch')
            for side,name in [('R','right'),('L','left')]:
                f=HERE/(name+'_hand_png.glb')
                if not f.exists():
                    report['pending'].append(str(f.relative_to(REPO)))
                    continue
                require(digest(f)==rig['sides'][side]['sha256'],'PNG hand identity differs from rig manifest')
                snapshots[f]=rig['sides'][side]['sha256']
                d,b=read(f)
                hand={'sha256':digest(f),**validate_asset(d,b,side)}
                hand['source_rig_frames_and_skin']=frames_and_correspondence(d,b,side,rig['sides'][side],document,binary,selected,atlas,dao,dao_binary)
                hand['embedded_atlas']=embedded_atlas(d,b,side,atlas)
                hand['negative_contract_tests']=contract_negative_tests(d,b,side)
                hand['cuff_closure']=cap_checks(d,b,rig['sides'][side])
                report['errors'].extend(side+': '+message for message in hand['cuff_closure'].get('errors',[]))
                if not hand['cuff_closure']['present']:
                    report['pending'].append(side+' approved cuff closure not present')
                final=HERE/(name+'_hand.glb')
                if final.exists() and not args.png_only:
                    cm_path=HERE/'compression_manifest.json'
                    cm=json.loads(cm_path.read_text())
                    require(cm['source_job']['rig_manifest_sha256']==digest(HERE/'rig_manifest.json'),'Compression rig source pin mismatch')
                    require(cm['hands'][name]['source_sha256']==snapshots[f],'Compression PNG source pin mismatch')
                    require(digest(final)==cm['hands'][name]['artifact']['sha256'],'Final KTX artifact pin mismatch')
                    snapshots[final]=digest(final)
                    hand['compression']=compression_checks(d,b,final)
                    decoded=cm['hands'][name]['decoded_companion']
                    decoded_path=path(decoded['path'])
                    require(digest(decoded_path)==decoded['sha256'] and decoded['compressed_input_sha256']==snapshots[final],'Decoded companion identity mismatch')
                    decoded_doc,decoded_bin=read(decoded_path)
                    hand['compression']['actual_ktx_decoded_companion']={'sha256':decoded['sha256'],'source_compressed_sha256':decoded['compressed_input_sha256'],'nonimage_equivalence':image_variant_equivalence(d,b,decoded_doc,decoded_bin),'scope':'Companion identity and non-image bytes independently checked; decoder execution/provenance supplied by pinned compression manifest, no SDK decode claim'}
                    report['compression_manifest_sha256']=digest(cm_path)
                else:
                    report['pending'].append(str(final.relative_to(REPO)))
                report.setdefault('hands',{})[side]=hand
    except Exception as error:
        report['errors'].append(str(error))
    if report.get('hands'):
        report['actual_two_hand_triangle_total']=sum(p['triangles'] for hand in report['hands'].values() for p in hand['primitives'])
        require(report['actual_two_hand_triangle_total']<=20000,'Actual hands+caps exceed20k triangle budget')
    report['PNG_assets_passed']=not report['errors'] and len(report.get('hands',{}))==2 and all(hand['cuff_closure'].get('passed',False) for hand in report['hands'].values())
    if args.pre_cap:
        report['pending'].append('Final cuff-closure PNG/KTX assets pending; current hand PNGs are before the authorized cap repair')
    report['stable_artifact_snapshot']=all(digest(f)==sha for f,sha in snapshots.items())
    if not report['stable_artifact_snapshot']:
        report['errors'].append('Artifact changed during independent audit')
        report['PNG_assets_passed']=False
    report['passed']=not report['errors'] and not report['pending'] and not args.sources_only
    report['source_checks_completed']='source_and_selection' in report and 'atlas' in report
    report['phase']='OFFLINE_INDEPENDENT_ASSET_PASS_RUNTIME_UNVERIFIED' if report['passed'] else 'PENDING_OR_BLOCKED_OFFLINE_ASSET_AUDIT'
    report['limitations']=['Normal metric is signed average dot against geometric face direction; negative values can require a true crease split and are not alone a geometric inversion proof.','Source L original normal/face disagreements are inherited limitations and do not count as newly generated cap defects.','Left closed pose provenance must remain explicitly rest-derived unless an authored calibration is independently supplied.','Collapsed source UV faces/islands cannot establish tangent basis validity; no source faces silently dropped.','No PICO SDK input validation or device/GPU texture-allocation claim.']
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'source_checks_completed':report['source_checks_completed'],'errors':report['errors'],'pending':report['pending']}))
    return 0 if not report['errors'] else 1

if __name__=='__main__':
    raise SystemExit(main())
