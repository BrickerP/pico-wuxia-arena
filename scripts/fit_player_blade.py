"""Deterministic offline Steel-only capsule fitting for the displayed dao asset."""
import argparse
import hashlib
import heapq
import json
import math
from pathlib import Path
import struct

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / 'app/src/main/assets/models/dao_grip.glb'
ASSET_SHA256 = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'
KOTLIN = ROOT / 'app/src/main/java/com/example/wuxiaarena/core/combat/PlayerBladeShape.kt'
RADIUS = .006


def load_steel(path=ASSET):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ASSET_SHA256:
        raise ValueError('Displayed dao changed; review and regenerate the capsule fit')
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546C67 or version != 2 or length != len(raw):
        raise ValueError('Expected a complete GLB2')
    offset = 12
    chunks = {}
    while offset < length:
        size, kind = struct.unpack_from('<II', raw, offset)
        chunks[kind] = raw[offset+8:offset+8+size]
        offset += 8+size
    document = json.loads(chunks[0x4E4F534A])
    binary = chunks[0x004E4942]

    def positions(index):
        accessor = document['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != 'VEC3' or 'sparse' in accessor:
            raise ValueError('Expected dense float32 Steel positions')
        view = document['bufferViews'][accessor['bufferView']]
        stride = view.get('byteStride', 12)
        start = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
        if stride < 12 or start+stride*(accessor['count']-1)+12 > view.get('byteOffset', 0)+view['byteLength']:
            raise ValueError('Steel accessor exceeds its view')
        return np.ndarray((accessor['count'], 3), dtype='<f4', buffer=binary,
                          offset=start, strides=(stride, 4)).astype(np.float64)

    def local(node):
        if 'matrix' in node:
            return np.array(node['matrix'], dtype=np.float64).reshape((4, 4), order='F')
        x, y, z, w = node.get('rotation', [0., 0., 0., 1.])
        matrix = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), 0.],
                           [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), 0.],
                           [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), 0.],
                           [0., 0., 0., 1.]])
        matrix[:3, :3] *= np.array(node.get('scale', [1., 1., 1.]))
        matrix[:3, 3] = node.get('translation', [0., 0., 0.])
        return matrix

    worlds = {}
    def visit(index, parent):
        if index in worlds:
            raise ValueError('Default scene node has multiple parents')
        node = document['nodes'][index]
        worlds[index] = parent @ local(node)
        for child in node.get('children', []):
            visit(child, worlds[index])
    for index in document['scenes'][document.get('scene', 0)]['nodes']:
        visit(index, np.eye(4))
    grips = [i for i in worlds if document['nodes'][i].get('name') == 'Grip']
    if len(grips) != 1:
        raise ValueError('Expected the one displayed default-scene Grip')
    inverse = np.linalg.inv(worlds[grips[0]])
    steel = []
    for index, world in worlds.items():
        node = document['nodes'][index]
        if 'mesh' not in node:
            continue
        for primitive in document['meshes'][node['mesh']]['primitives']:
            material = document['materials'][primitive['material']]['name']
            if not material.startswith('Steel | '):
                continue
            p = positions(primitive['attributes']['POSITION'])
            matrix = inverse @ world
            steel.append(p @ matrix[:3, :3].T + matrix[:3, 3])
    points = np.concatenate(steel)
    if len(points) != 5533 or not np.isfinite(points).all():
        raise ValueError('Steel-only default-scene denominator changed')
    return points


def axis_distances(points, bases, tips):
    axes = tips-bases
    amounts = np.clip(np.sum((points[:, None]-bases)*axes, axis=2)/np.sum(axes*axes, axis=1), 0., 1.)
    delta = points[:, None]-(bases+amounts[:, :, None]*axes)
    return np.sqrt(np.sum(delta*delta, axis=2))


def fit(points):
    """Side-by-side strips, trimmed to the real Steel rows assigned to each strip.

    A spacing no greater than the diameter avoids isolated centre-line beads.
    Steel thickness is included in the final three-dimensional distance test.
    No random seed, optimization package or mesh other than the displayed dao is used.
    """
    left = float(points[:, 0].min())+RADIUS
    right = float(points[:, 0].max())-RADIUS
    count = math.ceil((right-left)/(2*RADIUS))+1
    if count > 16:
        raise ValueError('Steel width needs more than the permitted16 strips')
    centers = np.linspace(left, right, count)
    assignment = np.argmin(np.abs(points[:, 0, None]-centers), axis=1)
    bases, tips = [], []
    y = float((points[:, 1].min()+points[:, 1].max())*.5)
    for index, x in enumerate(centers):
        band = points[assignment == index]
        if not len(band):
            raise ValueError('Empty Steel strip')
        bases.append([float(x), y, float(band[:, 2].max())])
        tips.append([float(x), y, float(band[:, 2].min())])
    bases, tips = np.array(bases), np.array(tips)
    radii = np.full(count, RADIUS)
    outside = np.maximum(0., (axis_distances(points, bases, tips)-radii).min(axis=1))
    if outside.max() > .002:
        raise ValueError(f'Fit misses2mm limit by {(outside.max()-.002)*1000:.9f}mm')
    return bases, tips, radii


def kotlin_source(bases, tips, radii):
    def vector(p):
        return 'Vector3('+', '.join(format(float(v), '.17g') if v != 0 else '0.0' for v in p)+')'
    rows = ['        BladeSegment('+vector(a)+', '+vector(b)+', '+format(float(r), '.17g')+'),' for a,b,r in zip(bases,tips,radii)]
    return '\n'.join([
        'package com.example.wuxiaarena.core.combat', '',
        'import com.example.wuxiaarena.core.math.Vector3', '',
        '/** Grip-local Steel coverage generated by scripts/fit_player_blade.py.',
        ' * Source: asset://models/dao_grip.glb; SHA256 '+ASSET_SHA256+'.',
        ' * Seven thin strips span the blade face; runtime only transforms this table.',
        ' */',
        'internal object PlayerBladeShape {',
        '    val capsules: List<BladeSegment> = listOf(', *rows,
        '    )',
        '    val gripRadius: Double = capsules.maxOf { maxOf(it.base.length(), it.tip.length()) }',
        '}', '',
    ])


def surface_distance_interval(points, bases, tips, radii, tolerance=.00005):
    """Bracket max distance from the exposed union surface to a Steel vertex.

    The nearest-vertex distance and each capsule signed distance are1-Lipschitz.
    A side/cap parameter patch is bounded by a Euclidean radius around its centre.
    We discard a patch only if that whole ball is inside another capsule. Exposed
    centres give a lower bound; all remaining patch upper bounds enclose the
    continuous maximum. The return value is not labelled an exact sampled maximum.
    """
    axes = tips-bases
    lengths = np.sqrt(np.sum(axes*axes, axis=1))
    directions = axes/lengths[:, None]
    e1, e2 = [], []
    for direction in directions:
        reference = np.array([1.,0.,0.]) if abs(direction[0]) < .9 else np.array([0.,1.,0.])
        u = np.cross(direction,reference)
        u /= math.sqrt(float(np.sum(u*u)))
        e1.append(u)
        e2.append(np.cross(direction,u))
    e1,e2=np.array(e1),np.array(e2)
    lower = 0.
    witness = None
    heap = []
    serial = 0
    evaluations = 0

    def add(index,kind,a,b,c,d):
        nonlocal lower,witness,serial,evaluations
        s,t=(a+b)*.5,(c+d)*.5
        r=float(radii[index])
        radial=e1[index]*math.cos(t)+e2[index]*math.sin(t)
        if kind == 0:
            p=bases[index]+directions[index]*s+r*radial
            bound=math.sqrt(((b-a)*.5)**2+(2*r*math.sin((d-c)*.25))**2)
        else:
            center=bases[index] if kind == -1 else tips[index]
            p=center+directions[index]*(kind*r*math.cos(s))+r*math.sin(s)*radial
            bound=r*((b-a)+(d-c))*.5
        # Roundoff allowance is only for this offline surface certificate.
        bound=math.nextafter(bound+1e-12,math.inf)
        gaps=axis_distances(p[None],bases,tips)[0]-radii
        other=np.delete(gaps,index)
        if float(other.min())+bound < -1e-12:
            return
        distance=math.sqrt(float(np.min(np.sum((points-p)**2,axis=1))))
        evaluations += 1
        if float(other.min()) >= -1e-12 and distance > lower:
            lower=distance
            witness=p.tolist()
        upper=math.nextafter(distance+bound,math.inf)
        heapq.heappush(heap,(-upper,serial,index,kind,a,b,c,d))
        serial+=1

    for index,length in enumerate(lengths):
        sections=math.ceil(float(length)/.004)
        for section in range(sections):
            for angle in range(12):
                add(index,0,float(length)*section/sections,float(length)*(section+1)/sections,
                    math.tau*angle/12,math.tau*(angle+1)/12)
        for kind in [-1,1]:
            for latitude in range(3):
                for angle in range(12):
                    add(index,kind,math.pi*.5*latitude/3,math.pi*.5*(latitude+1)/3,
                        math.tau*angle/12,math.tau*(angle+1)/12)
    while heap and -heap[0][0] > lower+tolerance:
        if evaluations > 200_000:
            raise ValueError('Surface certificate budget exhausted; no maximum claim')
        neg_upper,unused,index,kind,a,b,c,d=heapq.heappop(heap)
        s_weight=1. if kind == 0 else float(radii[index])
        if s_weight*(b-a) >= float(radii[index])*(d-c):
            middle=(a+b)*.5
            add(index,kind,a,middle,c,d)
            add(index,kind,middle,b,c,d)
        else:
            middle=(c+d)*.5
            add(index,kind,a,b,c,middle)
            add(index,kind,a,b,middle,d)
    upper=max(lower,-heap[0][0]) if heap else lower
    return dict(lower=lower,upper=upper,tolerance=tolerance,evaluations=evaluations,witness=witness)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Write the one Kotlin coefficient table')
    parser.add_argument('--check',action='store_true',help='Require checked-in table to reproduce exactly')
    options=parser.parse_args()
    points=load_steel()
    bases,tips,radii=fit(points)
    source=kotlin_source(bases,tips,radii)
    if options.write:
        KOTLIN.write_text(source)
    if options.check and KOTLIN.read_text()!=source:
        raise SystemExit('PlayerBladeShape.kt differs from the displayed-asset fit')
    old=axis_distances(points,np.array([[.022,0.,-.129]]),np.array([[.0532,0.,-.849]]))[:,0]
    outside=np.maximum(0.,(axis_distances(points,bases,tips)-radii).min(axis=1))
    print(f'Steel vertices={len(points)} capsules={len(radii)} radii_mm={[float(r)*1000 for r in radii]}')
    print(f'Before max_axis_mm={old.max()*1000:.9f} max_outside_mm={max(0.,old.max()-.012)*1000:.9f}')
    print(f'After all_vertices={len(outside)} max_outside_mm={outside.max()*1000:.9f}')
    surface=surface_distance_interval(points,bases,tips,radii)
    print(f'Union surface -> nearest Steel vertex maximum_mm=[{surface["lower"]*1000:.9f},{surface["upper"]*1000:.9f}] continuous_interval_width_mm={(surface["upper"]-surface["lower"])*1000:.9f} evaluations={surface["evaluations"]}')


if __name__ == '__main__':
    main()
