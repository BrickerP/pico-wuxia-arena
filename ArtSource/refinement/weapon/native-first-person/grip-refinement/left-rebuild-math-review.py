#!/usr/bin/env python3
"""Independent common-Grip reflection audit; never writes model/runtime assets.

For S=diag(-1,1,1,1), W'=SWS and I'=SIS imply
sum(w W'I' Sv) = S sum(w WIv). Reversing triangle winding and tangent.w
is additionally necessary for front faces and the normal-map basis.
"""
import argparse
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np

S = np.diag([-1.0, 1.0, 1.0, 1.0])
S3 = S[:3, :3]
TIMES = (0.0, .125, .25, .375, .5, .625, .75, .875, 1.0)
RIGHT_SHA = '3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0'
TYPES = {5120: '<i1', 5121: '<u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class ReviewError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ReviewError(message)


def close(actual, expected, label, atol=2e-6):
    require(actual.shape == expected.shape, label + ': shape mismatch')
    require(np.isfinite(actual).all() and np.isfinite(expected).all(), label + ': nonfinite')
    error = float(np.max(np.abs(actual - expected))) if actual.size else 0.0
    require(error <= atol, f'{label}: error {error:.9g} > {atol}')
    return error


class Asset:
    def __init__(self, doc, binary, path=None, sha=None):
        self.doc, self.binary = doc, bytes(binary)
        self.path, self.sha = path, sha

    @classmethod
    def load(cls, path):
        data = Path(path).read_bytes()
        require(len(data) >= 20, 'Truncated GLB')
        magic, version, total = struct.unpack_from('<4sII', data)
        require((magic, version, total) == (b'glTF', 2, len(data)), 'Invalid GLB header')
        offset, document, binary = 12, None, None
        while offset < total:
            require(offset + 8 <= total, 'Truncated GLB chunk')
            length, kind = struct.unpack_from('<II', data, offset)
            offset += 8
            require(offset + length <= total and length % 4 == 0, 'Invalid GLB chunk size')
            payload = data[offset:offset + length]
            if kind == 0x4E4F534A:
                require(document is None, 'Duplicate JSON chunk')
                document = json.loads(payload)
            elif kind == 0x004E4942:
                require(binary is None, 'Duplicate BIN chunk')
                binary = payload
            offset += length
        require(document is not None and binary is not None, 'Missing GLB JSON/BIN')
        require(len(document['buffers']) == 1 and 'uri' not in document['buffers'][0], 'Embedded buffer required')
        require(document['buffers'][0]['byteLength'] <= len(binary), 'Truncated declared buffer')
        return cls(document, binary, str(Path(path).resolve()), hashlib.sha256(data).hexdigest())

    def accessor(self, index, normalize=True):
        a = self.doc['accessors'][index]
        require('sparse' not in a, 'Sparse accessor is outside this audit contract')
        require(a['type'] in WIDTHS and a['componentType'] in TYPES, 'Unsupported accessor encoding')
        v = self.doc['bufferViews'][a['bufferView']]
        require(v.get('buffer', 0) == 0, 'External accessor buffer')
        dtype = np.dtype(TYPES[a['componentType']])
        width, count = WIDTHS[a['type']], a['count']
        stride = v.get('byteStride', width * dtype.itemsize)
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        end = start + (count - 1) * stride + width * dtype.itemsize if count else start
        require(count >= 0 and stride >= width * dtype.itemsize, 'Invalid accessor layout')
        require(end <= v.get('byteOffset', 0) + v['byteLength'] and end <= len(self.binary), 'Accessor outside bufferView')
        out = np.ndarray((count, width), dtype=dtype, buffer=self.binary, offset=start,
                         strides=(stride, dtype.itemsize)).copy()
        if normalize and a.get('normalized', False):
            require(a['componentType'] in (5120, 5121, 5122, 5123), 'Invalid normalized accessor')
            info = np.iinfo(dtype)
            out = out.astype(float) / info.max
            if info.min < 0:
                out = np.maximum(out, -1.0)
        return out

    def payload(self, index):
        return self.accessor(index, False).tobytes()

    def image_payloads(self):
        result = []
        for image in self.doc.get('images', []):
            require('bufferView' in image and 'uri' not in image, 'Embedded image required')
            view = self.doc['bufferViews'][image['bufferView']]
            begin = view.get('byteOffset', 0)
            result.append(self.binary[begin:begin + view['byteLength']])
        return result


def quat_matrix(q):
    q = np.asarray(q, dtype=float)
    length = np.linalg.norm(q)
    require(np.isfinite(length) and length > 1e-12, 'Invalid quaternion')
    x, y, z, w = q / length
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def local_matrix(node):
    if 'matrix' in node:
        require(not {'translation', 'rotation', 'scale'}.intersection(node), 'Matrix node also declares TRS')
        return np.asarray(node['matrix'], dtype=float).reshape(4, 4).T
    out = np.eye(4)
    out[:3, :3] = quat_matrix(node.get('rotation', (0, 0, 0, 1))) @ np.diag(node.get('scale', (1, 1, 1)))
    out[:3, 3] = node.get('translation', (0, 0, 0))
    return out


def slerp(a, b, alpha):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    dot = float(np.dot(a, b))
    if dot < 0:
        b, dot = -b, -dot
    if dot > .9995:
        out = a + alpha * (b - a)
        return out / np.linalg.norm(out)
    angle = math.acos(np.clip(dot, -1, 1))
    return (math.sin((1-alpha)*angle)*a + math.sin(alpha*angle)*b) / math.sin(angle)


def pose_world(asset, time):
    nodes = copy.deepcopy(asset.doc['nodes'])
    clips = asset.doc.get('animations', [])
    require(len(clips) == 1 and clips[0].get('name') == 'grip', 'One grip clip required')
    clip = clips[0]
    channels = set()
    for channel in clip['channels']:
        target, sampler = channel['target'], clip['samplers'][channel['sampler']]
        key = target['node'], target['path']
        require(key not in channels and target['path'] in ('translation', 'rotation', 'scale'), 'Invalid/duplicate TRS channel')
        channels.add(key)
        require('matrix' not in nodes[target['node']], 'Animated node must use TRS')
        ts = asset.accessor(sampler['input']).ravel().astype(float)
        values = asset.accessor(sampler['output']).astype(float)
        require(len(ts) >= 2 and np.isfinite(ts).all() and (np.diff(ts) > 0).all(), 'Invalid grip key times')
        require(ts[0] == 0 and ts[-1] == 1 and len(values) == len(ts), 'Grip must cover 0..1')
        interpolation = sampler.get('interpolation', 'LINEAR')
        require(interpolation in ('LINEAR', 'STEP'), 'Only LINEAR/STEP channels supported')
        after = int(np.searchsorted(ts, time, side='right'))
        if after == 0:
            value = values[0]
        elif after >= len(ts):
            value = values[-1]
        else:
            before = after - 1
            alpha = (time - ts[before]) / (ts[after] - ts[before])
            if interpolation == 'STEP':
                value = values[before]
            elif target['path'] == 'rotation':
                value = slerp(values[before], values[after], alpha)
            else:
                value = values[before]*(1-alpha) + values[after]*alpha
        nodes[target['node']][target['path']] = value
    parents = {}
    for parent, node in enumerate(nodes):
        for child in node.get('children', []):
            require(0 <= child < len(nodes) and child not in parents, 'Invalid or multiply-parented node')
            parents[child] = parent
    world, visiting = {}, set()
    def visit(index):
        if index not in world:
            require(index not in visiting, 'Cyclic node hierarchy')
            visiting.add(index)
            matrix = local_matrix(nodes[index])
            world[index] = visit(parents[index]) @ matrix if index in parents else matrix
            visiting.remove(index)
        return world[index]
    return np.array([visit(i) for i in range(len(nodes))])


def swap_side(name):
    if name.startswith('R_'):
        return 'L_' + name[2:]
    if name.startswith('L_'):
        return 'R_' + name[2:]
    return name


def unit(vectors):
    lengths = np.linalg.norm(vectors, axis=1)
    require((lengths > 1e-12).all(), 'Zero transformed normal/tangent')
    return vectors / lengths[:, None]


def skin(asset, primitive, world, skin_index):
    p = asset.accessor(primitive['attributes']['POSITION']).astype(float)
    j = asset.accessor(primitive['attributes']['JOINTS_0'], False).astype(int)
    weights = asset.accessor(primitive['attributes']['WEIGHTS_0']).astype(float)
    palette = asset.doc['skins'][skin_index]['joints']
    require(np.isfinite(weights).all() and (weights >= 0).all(), 'Invalid skin weights')
    require(((j >= 0) & (j < len(palette))).all(), 'JOINTS_0 outside palette')
    require(np.max(np.abs(weights.sum(axis=1)-1)) < 1e-5, 'Weights must sum to one')
    bind = asset.accessor(asset.doc['skins'][skin_index]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
    require(len(bind) == len(palette), 'IBM/palette length mismatch')
    matrices = world[palette] @ bind
    blended = np.sum(matrices[j] * weights[:, :, None, None], axis=1)
    position = np.einsum('vij,vj->vi', blended, np.column_stack((p, np.ones(len(p)))))[:, :3]
    normal = asset.accessor(primitive['attributes']['NORMAL']).astype(float)
    try:
        normal_matrix = np.linalg.inv(blended[:, :3, :3]).transpose(0, 2, 1)
    except np.linalg.LinAlgError as exc:
        raise ReviewError('Singular blended skin matrix') from exc
    normal = unit(np.einsum('vij,vj->vi', normal_matrix, normal))
    tangent = None
    if 'TANGENT' in primitive['attributes']:
        raw = asset.accessor(primitive['attributes']['TANGENT']).astype(float)
        tangent = np.column_stack((unit(np.einsum('vij,vj->vi', blended[:, :3, :3], raw[:, :3])), raw[:, 3]))
    return position, normal, tangent


def handedness(asset, world, side):
    names = {node.get('name'): i for i, node in enumerate(asset.doc['nodes'])}
    needed = [side + x for x in ('Hand', 'Forearm', 'Thumb1', 'Index1', 'Pinky1')]
    require(all(x in names for x in needed), 'Missing anatomical hand joints')
    hand, forearm, thumb, index, pinky = (world[names[x], :3, 3] for x in needed)
    vectors = np.array([thumb-index, pinky-index, hand-forearm])
    divisor = np.prod(np.linalg.norm(vectors, axis=1))
    require(divisor > 1e-12, 'Degenerate anatomical landmarks')
    return float(np.linalg.det(vectors) / divisor)


def validate_bounds(asset, used):
    checked = 0
    for index in used:
        accessor = asset.doc['accessors'][index]
        values = asset.accessor(index, False)
        require(np.isfinite(values).all(), 'Nonfinite referenced accessor')
        if 'min' in accessor:
            close(np.asarray(accessor['min']), values.min(axis=0), f'accessor {index} min', 1e-6)
            checked += 1
        if 'max' in accessor:
            close(np.asarray(accessor['max']), values.max(axis=0), f'accessor {index} max', 1e-6)
            checked += 1
    return checked


def audit(right, left):
    rd, ld = right.doc, left.doc
    require(len(rd['nodes']) == len(ld['nodes']), 'Node count differs; hidden compensation frame is forbidden')
    require(len(rd['meshes']) == len(ld['meshes']) and len(rd['skins']) == len(ld['skins']) == 1, 'Mesh/skin count mismatch')
    require(len(rd['skins'][0]['joints']) == 78, 'Expected complete 78-joint source rig')
    require(rd['scene'] == ld['scene'], 'Scene index differs')
    require(rd['scenes'][rd['scene']]['nodes'] == ld['scenes'][ld['scene']]['nodes'], 'Scene roots differ')
    require(rd.get('materials') == ld.get('materials') and rd.get('textures') == ld.get('textures') and rd.get('samplers') == ld.get('samplers'), 'Materials/textures/samplers changed')
    require(rd.get('extensionsUsed') == ld.get('extensionsUsed') and rd.get('extensionsRequired') == ld.get('extensionsRequired'), 'Extensions changed')
    require([{k:v for k,v in image.items() if k != 'bufferView'} for image in rd.get('images',[])] ==
            [{k:v for k,v in image.items() if k != 'bufferView'} for image in ld.get('images',[])], 'Image metadata changed')
    require(right.image_payloads() == left.image_payloads(), 'Image payloads changed')
    for side, doc in [('right', rd), ('left', ld)]:
        names = [n.get('name') for n in doc['nodes'] if n.get('name')]
        require(len(names) == len(set(names)), side + ' duplicate node names')
        for root in doc['scenes'][doc['scene']]['nodes']:
            close(local_matrix(doc['nodes'][root]), np.eye(4), side + ' outer root must be identity', 1e-7)
        for i, node in enumerate(doc['nodes']):
            require('weights' not in node, side + ' morph weights are outside the source contract')
            require(all(v > 0 for v in node.get('scale', (1, 1, 1))), side + ' negative/zero scale')
            determinant = np.linalg.det(local_matrix(node)[:3, :3])
            require(np.isfinite(determinant) and determinant > 1e-12, side + f' improper node {i}')
    maximum_local_error = 0.0
    for i, (rn, ln) in enumerate(zip(rd['nodes'], ld['nodes'])):
        require(all(rn.get(k) == ln.get(k) for k in ('children', 'mesh', 'skin')), f'Node {i} topology/mesh/skin changed')
        maximum_local_error = max(maximum_local_error, close(local_matrix(ln), S @ local_matrix(rn) @ S, f'Node {i} conjugation', 1e-6))
    rs, ls = rd['skins'][0], ld['skins'][0]
    require(rs['joints'] == ls['joints'] and rs.get('skeleton') == ls.get('skeleton'), 'Joint palette/topology changed')
    for i in rs['joints']:
        require(ld['nodes'][i].get('name') == swap_side(rd['nodes'][i].get('name', '')), f'Joint {i} side swap incorrect')
    rbind = right.accessor(rs['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0,2,1)
    lbind = left.accessor(ls['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0,2,1)
    maximum_ibm_error = close(lbind, S @ rbind @ S, 'IBM conjugation', 1e-6)
    rc, lc = rd['animations'], ld['animations']
    require(len(rc) == len(lc) == 1 and rc[0]['name'] == lc[0]['name'] == 'grip', 'grip clip changed')
    require(rc[0]['channels'] == lc[0]['channels'], 'Animation channel/node mapping changed')
    require(len(rc[0]['samplers']) == len(lc[0]['samplers']), 'Sampler count changed')
    used_r, used_l = {rs['inverseBindMatrices']}, {ls['inverseBindMatrices']}
    times = set(TIMES)
    for channel in rc[0]['channels']:
        index, path = channel['sampler'], channel['target']['path']
        ra, la = rc[0]['samplers'][index], lc[0]['samplers'][index]
        require(ra.get('interpolation','LINEAR') == la.get('interpolation','LINEAR'), 'Animation interpolation changed')
        require(right.payload(ra['input']) == left.payload(la['input']), 'Animation key grid changed')
        times.update(float(t) for t in right.accessor(ra['input']).ravel())
        values, actual = right.accessor(ra['output']).astype(float), left.accessor(la['output']).astype(float)
        expected = values.copy()
        if path == 'rotation':
            expected[:, 1:3] *= -1
        elif path == 'translation':
            expected[:, 0] *= -1
        else:
            require(path == 'scale', 'Unsupported animation path')
        close(actual, expected, 'Animation ' + path, 1e-6)
        used_r.update((ra['input'], ra['output'])); used_l.update((la['input'], la['output']))
    primitives, total_vertices, total_triangles, tangents_present = [], 0, 0, 0
    for mi, (rm, lm) in enumerate(zip(rd['meshes'], ld['meshes'])):
        require('weights' not in rm and 'weights' not in lm, 'Mesh morph weights are outside the source contract')
        require(len(rm['primitives']) == len(lm['primitives']), 'Primitive count changed')
        for pi, (rp, lp) in enumerate(zip(rm['primitives'], lm['primitives'])):
            label = f'mesh {mi} primitive {pi}'
            require('targets' not in rp and 'targets' not in lp, label + ' morph targets are outside the source contract')
            require(rp.get('mode',4) == lp.get('mode',4) == 4, 'Triangle primitives required')
            require(rp.get('material') == lp.get('material') and rp.get('extras') == lp.get('extras'), label + ' material/extras changed')
            require(set(rp['attributes']) == set(lp['attributes']), label + ' attributes changed')
            for name, rindex in rp['attributes'].items():
                lindex = lp['attributes'][name]
                ra, la = rd['accessors'][rindex], ld['accessors'][lindex]
                require(all(ra.get(k) == la.get(k) for k in ('componentType','type','count','normalized')), label + ' accessor layout changed')
                actual = left.accessor(lindex,False).astype(float)
                expected = right.accessor(rindex,False).astype(float)
                if name in ('POSITION','NORMAL','TANGENT'):
                    expected[:,0] *= -1
                    if name == 'TANGENT':
                        expected[:,3] *= -1
                        tangents_present += 1
                    close(actual, expected, label + ' ' + name, 1e-6)
                else:
                    require(right.payload(rindex) == left.payload(lindex), label + ' ' + name + ' bytes changed')
                used_r.add(rindex); used_l.add(lindex)
            rf = right.accessor(rp['indices'],False).ravel().reshape(-1,3).astype(int)
            lf = left.accessor(lp['indices'],False).ravel().reshape(-1,3).astype(int)
            require(np.array_equal(lf, rf[:,[0,2,1]]), label + ' triangle winding not reversed')
            count = rd['accessors'][rp['attributes']['POSITION']]['count']
            require(((rf >= 0) & (rf < count)).all(), label + ' indices outside mesh')
            total_vertices += count; total_triangles += len(rf)
            used_r.add(rp['indices']); used_l.add(lp['indices'])
            # A skin must be attached to the same mesh node(s) in both scenes.
            nodes = [n for n in rd['nodes'] if n.get('mesh') == mi]
            require(nodes and all(n.get('skin') == 0 for n in nodes), label + ' unskinned/unexpected mesh node')
            primitives.append((mi, pi, rp, lp, rf, lf))
    bounds_checked = validate_bounds(right, used_r) + validate_bounds(left, used_l)
    samples = []
    for time in sorted(times):
        rw, lw = pose_world(right,time), pose_world(left,time)
        row = {'grip_time':time, 'world_matrix_error':close(lw,S@rw@S,'Posed world matrices',2e-6), 'primitives':[]}
        chirality_r, chirality_l = handedness(right,rw,'R_'), handedness(left,lw,'L_')
        require(abs(chirality_r) > 1e-5 and chirality_r * chirality_l < 0 and abs(chirality_r+chirality_l) < 1e-6, 'Hand chirality did not reverse')
        row['source_right_chirality'], row['candidate_left_chirality'] = chirality_r, chirality_l
        for mi, pi, rp, lp, rf, lf in primitives:
            rpos,rnormal,rtangent = skin(right,rp,rw,0)
            lpos,lnormal,ltangent = skin(left,lp,lw,0)
            position_error = close(lpos,rpos@S3,'Actual LBS reflected position',2e-6)
            normal_error = close(lnormal,rnormal@S3,'Actual inverse-transpose normal',2e-6)
            rarea=np.cross(rpos[rf[:,1]]-rpos[rf[:,0]],rpos[rf[:,2]]-rpos[rf[:,0]])
            larea=np.cross(lpos[lf[:,1]]-lpos[lf[:,0]],lpos[lf[:,2]]-lpos[lf[:,0]])
            area_error=close(larea,rarea@S3,'Actual posed face orientation',1e-9)
            tangent_error=None
            if rtangent is not None:
                tangent_error=close(ltangent,np.column_stack((rtangent[:,:3]@S3,-rtangent[:,3])),'Actual tangent basis',2e-6)
            row['primitives'].append({'mesh':mi,'primitive':pi,'position_error_m':position_error,'normal_error':normal_error,'oriented_area_error_m2':area_error,'tangent_error':tangent_error})
        samples.append(row)
    return {'status':'PASS_COMMON_GRIP_REFLECTION_MATH','source':{'path':right.path,'sha256':right.sha},
            'candidate':{'path':left.path,'sha256':left.sha},'nodes':len(rd['nodes']),
            'joint_palette_count':78,'vertices':total_vertices,'triangles':total_triangles,
            'local_matrix_error':maximum_local_error,'inverse_bind_error':maximum_ibm_error,
            'accessor_min_max_fields_checked':bounds_checked,'image_payloads_equal':True,
            'tangent_scope':'present and checked' if tangents_present else 'absent in both real assets; synthetic tangent handedness regression covers the audit branch',
            'sampling':samples,'proof':'S*M*S hierarchy and IBM plus S*v imply LBS_L=S*LBS_R; reversed winding and tangent.w retain oriented faces/TBN.',
            'limits':['Mathematical audit of this exact pair; not anatomical/art approval.',
                      'Does not test the actual asymmetric dao/hilt or mesh self-intersections.',
                      'Does not prove PICO SDK import/skinning, controller conventions, runtime performance or physical hand comfort.',
                      'The existing Kotlin left-wrist offset must be removed in the same integration as this common-Grip asset.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--right',type=Path,required=True)
    parser.add_argument('--left',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        right,left=Asset.load(args.right),Asset.load(args.left)
        require(right.sha==RIGHT_SHA,'Right source is not the reviewed 3a1be1dd asset')
        report=audit(right,left)
        require(Asset.load(args.right).sha==right.sha and Asset.load(args.left).sha==left.sha,'Input changed during audit')
        code=0
    except (ReviewError,KeyError,ValueError,IndexError) as error:
        report={'status':'FAIL_COMMON_GRIP_REFLECTION_MATH','error':str(error)}
        code=1
    report['reviewer_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='sampling'},ensure_ascii=False))
    return code


if __name__=='__main__':
    raise SystemExit(main())
