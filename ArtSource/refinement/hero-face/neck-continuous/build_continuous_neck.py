"""Build one continuous source-weighted neck; no affine cap/skin-cover path.

Source body streams/rest remain immutable. The audit supplies the exact body
edge contour, the head is clipped by Y+.6X=.8223, and a weighted atlas-baked loft
closes the two contours. Run with the unextended static ocular head component.
"""
import argparse
import copy
from io import BytesIO
import json
import math
from pathlib import Path
import struct
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import graft_head as g

CUT_C = .8223
PLANE_SLOPE = .6

def field(p):
    return p[1]+PLANE_SLOPE*p[0]

def plane_coordinates(p):
    return ((p[0]-PLANE_SLOPE*p[1])/math.sqrt(1+PLANE_SLOPE**2),p[2])
SAMPLES = 128


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def key(p):
    return struct.pack('<3f', *p)


def unit(v):
    size = math.sqrt(sum(x*x for x in v))
    if size < 1e-15 or not math.isfinite(size):
        raise ValueError('Invalid continuous-neck normal')
    return tuple(x/size for x in v)


def mix(a, b, t):
    return tuple((1-t)*x+t*y for x,y in zip(a,b))


def decode(data):
    size = struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size]), data[28+size:]


def append_rows(doc, binary, rows, kind, component=5126):
    code = g.COMPONENTS[component][0]
    width = g.WIDTHS[kind]
    index = g.append_accessor(doc,binary,b''.join(struct.pack('<'+code*width,*row) for row in rows),component,kind,len(rows),34962)
    if kind=='VEC3':
        doc['accessors'][index]['min']=[min(row[i] for row in rows) for i in range(3)]
        doc['accessors'][index]['max']=[max(row[i] for row in rows) for i in range(3)]
    return index


def append_indices(doc,binary,faces):
    values=[x for face in faces for x in face]
    if not values:
        raise ValueError('Empty output index stream')
    component,code=(5123,'H') if max(values)<65536 else (5125,'I')
    return g.append_accessor(doc,binary,struct.pack('<'+code*len(values),*values),component,'SCALAR',len(values),34963)


def clip_head(head, source, cut_c=CUT_C):
    """Exact Sutherland-Hodgman clip; retain source arrays and interpolate edges."""
    meshes=g.static_head_meshes(head)
    if len(meshes)!=1:
        raise ValueError('Expected one static ocular head mesh')
    mesh=meshes[0]
    primitives=head['meshes'][mesh]['primitives']
    skin=[i for i,p in enumerate(primitives) if 'rig_joint' not in p.get('extras',{})]
    # The first untagged surface is the skin/hair; later untagged surfaces are
    # preserved socket rims, so only this primary surface is clipped.
    if not skin:
        raise ValueError('Head has no main skin primitive')
    pi=skin[0]
    primitive=primitives[pi]
    points,faces=g.triangles(head,source,primitive)
    rows={name:list(g.accessor_rows(head,source,index)) for name,index in primitive['attributes'].items()}
    if any(len(v)!=len(points) for v in rows.values()):
        raise ValueError('Head attribute counts differ')
    if any(name.startswith(('JOINTS_','WEIGHTS_')) for name in rows):
        raise ValueError('Use an unskinned unextended head')
    result,binary=copy.deepcopy(head),bytearray(source)
    edge_cache,position_cache={},{}
    output_faces,retained,generated,new_vertices=[],[],[],[]
    source_face_ids=[];vertex_refs={}
    def crossing(a,b):
        edge=tuple(sorted((a,b)))
        if edge in edge_cache:
            return edge_cache[edge]
        pa,pb=points[a],points[b]
        t=(cut_c-field(pa))/(field(pb)-field(pa))
        geom=tuple(sorted((key(pa),key(pb))))
        if geom not in position_cache:
            position_cache[geom]=tuple(f32(v) for v in mix(pa,pb,t))
        index=len(rows['POSITION'])
        for name,values in rows.items():
            value=mix(values[a],values[b],t)
            if name=='POSITION':value=position_cache[geom]
            elif name in ('NORMAL','TANGENT'):
                direction=unit(value[:3]);value=direction+((1 if value[3]>=0 else -1,) if name=='TANGENT' else ())
            values.append(tuple(f32(v) for v in value))
        edge_cache[edge]=index
        vertex_refs[index]=(a,b,t)
        new_vertices.append({'output_vertex':index,'source_edge_vertex_ids':[a,b],'source_edge_barycentric':[1-t,t]})
        return index
    for fi,face in enumerate(faces):
        poly=[]
        for a,b in zip(face,face[1:]+face[:1]):
            inside_a,inside_b=field(points[a])>=cut_c,field(points[b])>=cut_c
            if inside_a:poly.append(a)
            if inside_a!=inside_b:poly.append(crossing(a,b))
        if len(poly)<3:continue
        tris=[(poly[0],poly[i],poly[i+1]) for i in range(1,len(poly)-1)]
        output_faces.extend(tris)
        source_face_ids.extend([fi]*len(tris))
        if len(poly)==3 and set(poly)==set(face):retained.append(fi)
        else:generated.append({'source_face':fi,'source_vertex_ids':face,'output_triangles':tris})
    updated=result['meshes'][mesh]['primitives'][pi]
    for name,values in rows.items():
        width=len(values[0]);updated['attributes'][name]=append_rows(result,binary,values,'VEC'+str(width))
    updated['indices']=append_indices(result,binary,output_faces)
    # Geometric edge welding respects UV splits while identifying the true cut.
    geometric={};position_ids={}
    for i,row in enumerate(rows['POSITION']):
        position_ids.setdefault(key(row),i)
    edge_faces={}
    for output_index,face in enumerate(output_faces):
        for a,b in zip(face,face[1:]+face[:1]):
            ka,kb=key(rows['POSITION'][a]),key(rows['POSITION'][b]);edge=tuple(sorted((ka,kb)))
            edge_faces.setdefault(edge,[]).append((a,b,output_index))
    directed={};uv_samples={}
    for refs in edge_faces.values():
        if len(refs)==1:
            a,b,output_index=refs[0]
            if abs(field(rows['POSITION'][a])-cut_c)<1e-6 and abs(field(rows['POSITION'][b])-cut_c)<1e-6:
                ka,kb=key(rows['POSITION'][a]),key(rows['POSITION'][b])
                if ka in directed:raise ValueError('Branched clipped neck boundary')
                directed[ka]=kb
                source_face=source_face_ids[output_index]
                for vertex in (a,b):
                    bary=[0.,0.,0.]
                    if vertex in vertex_refs:
                        sa,sb,t=vertex_refs[vertex];bary[faces[source_face].index(sa)]=1-t;bary[faces[source_face].index(sb)]=t
                    else:bary[faces[source_face].index(vertex)]=1.
                    uv_samples.setdefault(key(rows['POSITION'][vertex]),[]).append({'head_source_face':source_face,'barycentric':bary,'uv':list(rows['TEXCOORD_0'][vertex])})
    if len(directed)<3:raise ValueError('No clipped head neck boundary')
    seed=min(directed);at=seed;ring=[]
    while at not in ring:
        if at not in directed:raise ValueError('Open clipped head neck boundary')
        ring.append(at);at=directed[at]
    if at!=seed or len(ring)!=len(directed):raise ValueError('Multiple clipped neck rings')
    ids=[position_ids[x] for x in ring]
    report={'cut_field':'Y+.6*X','cut_c':cut_c,'mesh':mesh,'primitive':pi,'original_triangles':len(faces),'retained_original_triangle_ids':retained,
            'clipped_source_faces':generated,'edge_interpolations':new_vertices,'neck_ring_vertex_ids':ids,
            'neck_ring_positions':[list(rows['POSITION'][i]) for i in ids],
            'neck_ring_normals':[list(rows['NORMAL'][i]) for i in ids],
            'neck_ring_uv_samples':[uv_samples[x] for x in ring],
            'minimum_retained_head_field':min(field(rows['POSITION'][v])for face in output_faces for v in face)}
    result['buffers'][0]['byteLength']=len(binary)
    return result,bytes(binary),report


def perimeter(points):
    projected=[plane_coordinates(p) for p in points]
    distances=[math.dist(projected[i],projected[(i+1)%len(points)]) for i in range(len(points))]
    total=sum(distances)
    if total<=0 or any(x<=0 for x in distances):raise ValueError('Degenerate source ring')
    cumulative=[0.]
    for value in distances:cumulative.append(cumulative[-1]+value/total)
    cumulative[-1]=1.
    return cumulative


def sample(values, parameters, t):
    if t>=1:return values[0],0,0.
    for i in range(len(values)):
        if parameters[i]<=t<parameters[i+1]:
            fraction=(t-parameters[i])/(parameters[i+1]-parameters[i]);return mix(values[i],values[(i+1)%len(values)],fraction),i,fraction
    raise ValueError('Invalid perimeter sample')


def stitch_rings(bottom_indices,top_indices,bottom_t,top_t):
    faces=[];i=j=0
    while i<len(bottom_indices)-1 or j<len(top_indices)-1:
        a,b=bottom_indices[i],top_indices[j]
        lower=bottom_t[i+1] if i+1<len(bottom_t) else math.inf
        upper=top_t[j+1] if j+1<len(top_t) else math.inf
        if abs(lower-upper)<1e-10:
            faces.extend(((a,bottom_indices[i+1],top_indices[j+1]),(a,top_indices[j+1],b)));i+=1;j+=1
        elif lower<upper:faces.append((a,bottom_indices[i+1],b));i+=1
        else:faces.append((a,top_indices[j+1],b));j+=1
    return faces


def atlas(doc,binary,primitive):
    mat=doc['materials'][primitive['material']];pbr=mat.get('pbrMetallicRoughness',{})
    def image(info):
        if not info:return None
        if info.get('texCoord',0)!=0 or info.get('extensions'):raise ValueError('Unsupported atlas coordinates')
        item=doc['images'][doc['textures'][info['index']]['source']];view=doc['bufferViews'][item['bufferView']];start=view.get('byteOffset',0)
        return Image.open(BytesIO(binary[start:start+view['byteLength']])).convert('RGB')
    color=image(pbr.get('baseColorTexture'));mr=image(pbr.get('metallicRoughnessTexture'))
    if color is None:raise ValueError('Missing source skin color atlas')
    return color,mr,pbr.get('roughnessFactor',1.)


def pixel(image,uv):
    u,v=uv;u=u-math.floor(u);v=v-math.floor(v)
    return image.getpixel((min(image.width-1,int(u*image.width)),min(image.height-1,int(v*image.height))))


def skin_rgb(rgb):
    r,g,b=rgb;return r>g*1.12 and g>b*1.05 and r>70


def linear(x):
    x=x/255;return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4


def srgb(x):
    x=max(0,min(1,x));return round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055))


def append_image(doc,binary,image,name):
    stream=BytesIO();image.save(stream,format='PNG');data=stream.getvalue();binary.extend(b'\0'*(-len(binary)%4))
    view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary.extend(data)
    index=len(doc.setdefault('images',[]));doc['images'].append({'bufferView':view,'mimeType':'image/png','name':name});return index



def geometry_safety(points,faces,coords):
    """Finite triangle intersection proof, including coplanar overlap pairs."""
    from collections import defaultdict
    def sub(a,b):return tuple(x-y for x,y in zip(a,b))
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    triangles=[[points[i]for i in face]for face in faces]
    keys=[set(key(p)for p in tri)for tri in triangles]
    boxes=[([min(p[a]for p in tri)for a in range(3)],[max(p[a]for p in tri)for a in range(3)])for tri in triangles]
    buckets=defaultdict(list);pairs=set();cell=.004
    for i,(low,high)in enumerate(boxes):
        for x in range(math.floor(low[0]/cell),math.floor(high[0]/cell)+1):
            for y in range(math.floor(low[1]/cell),math.floor(high[1]/cell)+1):
                for z in range(math.floor(low[2]/cell),math.floor(high[2]/cell)+1):
                    bucket=buckets[(x,y,z)]
                    for j in bucket:
                        if keys[i].isdisjoint(keys[j]) and all(low[a]<=boxes[j][1][a]+1e-10 and high[a]>=boxes[j][0][a]-1e-10 for a in range(3)):pairs.add((j,i))
                    bucket.append(i)
    def segment_triangle(p,q,tri):
        a,b,c=tri;direction=sub(q,p);e1,e2=sub(b,a),sub(c,a);h=cross(direction,e2);det=dot(e1,h)
        if abs(det)<1e-15:return False
        inv=1/det;s=sub(p,a);u=dot(s,h)*inv
        if u< -1e-8 or u>1+1e-8:return False
        t=cross(s,e1);v=dot(direction,t)*inv
        if v< -1e-8 or u+v>1+1e-8:return False
        fraction=dot(e2,t)*inv
        return -1e-8<=fraction<=1+1e-8
    def coplanar_overlap(one,two):
        normal=cross(sub(one[1],one[0]),sub(one[2],one[0]));length=math.sqrt(dot(normal,normal))
        if length<1e-15 or any(abs(dot(normal,sub(p,one[0])))>length*1e-8for p in two):return False
        drop=max(range(3),key=lambda a:abs(normal[a]));axes=[i for i in range(3)if i!=drop]
        first=[tuple(p[i]for i in axes)for p in one];second=[tuple(p[i]for i in axes)for p in two]
        def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        for a,b in zip(first,first[1:]+first[:1]):
            for c,d in zip(second,second[1:]+second[:1]):
                if orient(a,b,c)*orient(a,b,d)<-1e-28 and orient(c,d,a)*orient(c,d,b)<-1e-28:return True
        def interior(p,tri):
            values=[orient(a,b,p)for a,b in zip(tri,tri[1:]+tri[:1])]
            return min(values)>1e-14 or max(values)<-1e-14
        return any(interior(p,second)for p in first)or any(interior(p,first)for p in second)
    intersections=[]
    for a,b in pairs:
        one,two=triangles[a],triangles[b]
        if any(segment_triangle(p,q,two)for p,q in zip(one,one[1:]+one[:1])) or any(segment_triangle(p,q,one)for p,q in zip(two,two[1:]+two[:1])) or coplanar_overlap(one,two):intersections.append([a,b])
    if intersections:raise ValueError('Continuous loft self-intersects: '+str(intersections[:5]))
    if any(field(p)>=CUT_C-1e-7 for p,uv in zip(points,coords)if uv[1]<1):raise ValueError('Loft interior crosses retained head halfspace')
    radial={}
    for frame,project in (('raw_Y_axis',lambda p:(p[0],p[2])),('tilted_axis',plane_coordinates)):
        rings=[]
        for value in (0.,1.):
            ring=[project(p)for p,uv in zip(points,coords)if uv[1]==value and uv[0]<1];rings.append(tuple(sum(p[a]for p in ring)/len(ring)for a in range(2)))
        values=[]
        for face in faces:
            p,q,r=[points[i]for i in face];normal=cross(sub(q,p),sub(r,p));nr=(normal[0],normal[2])if frame=='raw_Y_axis'else((normal[0]-.6*normal[1])/math.sqrt(1.36),normal[2]);t=sum(coords[i][1]for i in face)/3;center=mix(rings[0],rings[1],t);at=tuple(sum(project(points[i])[a]for i in face)/3 for a in range(2));values.append(dot(nr,sub(at,center)))
        radial[frame]={'minimum_centroid_radial_dot':min(values),'nonpositive_faces':sum(value<=0for value in values)}
    return {'tested_nonadjacent_triangle_pairs':len(pairs),'self_intersections':0,'coplanar_overlap_checked':True,
            'all_loft_interior_below_cut_field':True,'radial_diagnostics':radial,
            'radial_note':'Concave source collar/V boundary need not face away from its centroid. Directed winding plus nonintersection establishes orientation; radial signs alone do not.'}


def build(body,body_binary,head,head_binary,audit,body_sha,head_sha):
    if not body_sha or audit.get('source_sha256')!=body_sha:raise ValueError('Audit source SHA mismatch')
    proposal=audit.get('source_edge_loop52_proposal',{})
    if not proposal.get('all13_protected03faces_in_body_side'):raise ValueError('Protected collar mask not verified')
    bp=body['meshes'][0]['primitives'][0];points,faces=g.triangles(body,body_binary,bp)
    source_j=g.accessor_rows(body,body_binary,bp['attributes']['JOINTS_0']);source_w=g.accessor_rows(body,body_binary,bp['attributes']['WEIGHTS_0'])
    normals=g.accessor_rows(body,body_binary,bp['attributes']['NORMAL']) if 'NORMAL' in bp['attributes'] else [(1.,0.,0.)]*len(points)
    uv=g.accessor_rows(body,body_binary,bp['attributes']['TEXCOORD_0'])
    deleted=proposal.get('head_side_original_face_ids',[]);body_side=proposal.get('body_side_original_face_ids',[])
    if not deleted or any(type(i)!=int or i<0 or i>=len(faces) for i in deleted+body_side) or len(set(deleted))!=len(deleted) or set(deleted)&set(body_side):raise ValueError('Invalid source face mask')
    protected=[row['source_face'] for row in audit.get('protected_03_lapel_path_faces',[])]
    if any(i in deleted for i in protected):raise ValueError('Protected collar face deleted')
    deleted_set=set(deleted)
    kept=[i for i in range(len(faces)) if i not in deleted_set]
    ring_rows=proposal.get('directed_vertices',[]);base_ids=[row['representative_source_vertex_id'] for row in ring_rows]
    if len(base_ids)<3 or len(set(key(points[i]) for i in base_ids))!=len(base_ids):raise ValueError('Invalid source ring')
    base=[points[i] for i in base_ids]
    if any(list(points[i])!=row['position_raw_gltf'] for i,row in zip(base_ids,ring_rows)):raise ValueError('Source ring coordinates drifted')
    edge_faces={}
    for fi,face in enumerate(faces):
        for a,b in zip(face,face[1:]+face[:1]):edge_faces.setdefault(tuple(sorted((key(points[a]),key(points[b])))),[]).append((fi,a,b))
    expected_edges={tuple(sorted((key(a),key(b)))) for a,b in zip(base,base[1:]+base[:1])}
    actual_edges={edge for edge,refs in edge_faces.items() if sum(fi in deleted_set for fi,a,b in refs)==1}
    if actual_edges!=expected_edges:raise ValueError('Source mask has an extra or missing boundary')
    for i,(a,b) in enumerate(zip(base,base[1:]+base[:1])):
        refs=edge_faces.get(tuple(sorted((key(a),key(b)))),[])
        if len(refs)!=2 or sum(fi in set(deleted) for fi,_,_ in refs)!=1:raise ValueError('Source ring does not match exact mask boundary')
        retain=next((fi,x,y) for fi,x,y in refs if fi not in deleted_set)
        if key(points[retain[1]])!=key(b) or key(points[retain[2]])!=key(a):raise ValueError('Source ring winding must oppose retained body')
    clipped,clip_binary,clip=clip_head(head,head_binary)
    top=[tuple(p) for p in clip['neck_ring_positions']];top_norm=[tuple(p) for p in clip['neck_ring_normals']];top_samples=clip['neck_ring_uv_samples']
    if max(field(p)for p in base)>=CUT_C:raise ValueError('Original collar ring crosses the anatomical clip plane')
    if clip['minimum_retained_head_field']<CUT_C-1e-7:raise ValueError('Retained head lies below anatomical plane')
    def area(r):
        v=[plane_coordinates(p)for p in r];return sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(v,v[1:]+v[:1]))
    if area(base)*area(top)<=0:raise ValueError('Body/head neck winding mismatch')
    base_plane=[plane_coordinates(p)for p in base];top_plane=[plane_coordinates(p)for p in top]
    bx=sum(p[0]for p in base_plane)/len(base);bz=sum(p[1]for p in base_plane)/len(base);tx=sum(p[0]for p in top_plane)/len(top);tz=sum(p[1]for p in top_plane)/len(top)
    target=math.atan2(base_plane[0][1]-bz,base_plane[0][0]-bx)
    offset=min(range(len(top)),key=lambda i:abs(math.atan2(math.sin(math.atan2(top_plane[i][1]-tz,top_plane[i][0]-tx)-target),math.cos(math.atan2(top_plane[i][1]-tz,top_plane[i][0]-tx)-target))))
    top=top[offset:]+top[:offset];top_norm=top_norm[offset:]+top_norm[:offset];top_samples=top_samples[offset:]+top_samples[:offset]
    low_t,high_t=perimeter(base),perimeter(top)
    combined,graft=g.graft(body,body_binary,clipped,clip_binary,.81);result,binary=decode(combined);binary=bytearray(binary)
    mesh=result['nodes'][graft['body_mesh_node']]['mesh'];primitives=result['meshes'][mesh]['primitives']
    primitives[0]['indices']=append_indices(result,binary,[faces[i] for i in kept])
    skin=body['skins'][body['nodes'][graft['body_mesh_node']]['skin']];head_joint=next(i for i,node in enumerate(skin['joints']) if body['nodes'][node].get('name')=='Head')
    base_dict=[{j:w for j,w in zip(source_j[i],source_w[i]) if w>0} for i in base_ids]
    positions,uvs,joints,weights,endpoint_normals=[],[],[],[],[];rings=[];parameters=[]
    for ri,t in enumerate((0.,.25,.5,.75,1.)):
        ts=low_t if ri==0 else high_t if ri==4 else [i/SAMPLES for i in range(SAMPLES+1)]
        current=[]
        for s in ts:
            lower,li,lf=sample(base,low_t,s);upper,ui,uf=sample(top,high_t,s)
            current.append(len(positions));positions.append(tuple(f32(v) for v in mix(lower,upper,t)));uvs.append((s,t))
            if ri==0:
                vid=base_ids[li if s<1 else 0];positions[-1]=points[vid];joint=tuple(source_j[vid]);weight=tuple(source_w[vid]);normal=normals[vid]
            elif ri==4:
                normal=top_norm[ui if s<1 else 0];joint=(head_joint,0,0,0);weight=(1.,0.,0.,0.);positions[-1]=top[ui if s<1 else 0]
            else:
                lo={j:(1-lf)*base_dict[li].get(j,0)+lf*base_dict[(li+1)%len(base)].get(j,0) for j in set(base_dict[li])|set(base_dict[(li+1)%len(base)])};lo={j:w*(1-t) for j,w in lo.items()};lo[head_joint]=lo.get(head_joint,0)+t
                ordered=sorted(lo.items(),key=lambda item:-item[1])[:4];total=sum(w for j,w in ordered);joint=tuple(j for j,w in ordered)+(0,)*(4-len(ordered));weight=tuple(w/total for j,w in ordered)+(0.,)*(4-len(ordered));normal=unit(mix(unit(mix(normals[base_ids[li]],normals[base_ids[(li+1)%len(base)]],lf)),unit(mix(top_norm[ui],top_norm[(ui+1)%len(top)],uf)),t))
            joints.append(joint);weights.append(weight);endpoint_normals.append(normal)
        rings.append(current);parameters.append(ts)
    loft=[]
    for i in range(4):loft.extend(stitch_rings(rings[i],rings[i+1],parameters[i],parameters[i+1]))
    sums=[[0.,0.,0.]for p in positions]
    zero=0
    for a,b,c in loft:
        u=[positions[b][i]-positions[a][i]for i in range(3)];v=[positions[c][i]-positions[a][i]for i in range(3)];n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);zero+=sum(x*x for x in n)<1e-24
        for vertex in (a,b,c):sums[vertex]=[x+y for x,y in zip(sums[vertex],n)]
    if zero:raise ValueError('Degenerate continuous loft faces')
    safety=geometry_safety(positions,loft,uvs)
    geometric_sums={}
    for position,normal in zip(positions,sums):
        k=key(position);geometric_sums[k]=[a+b for a,b in zip(geometric_sums.get(k,(0.,0.,0.)),normal)]
    loft_norm=[unit(geometric_sums[key(position)]) for position in positions]
    for ring in (rings[0],rings[-1]):
        for i in ring:loft_norm[i]=endpoint_normals[i]
    # Sample inside each original chart first. Only linear-light COLORS and
    # roughness are then interpolated around the geometric rings, never UVs.
    from statistics import median
    body_color,body_mr,body_rough=atlas(body,body_binary,bp)
    head_primitive=clipped['meshes'][clip['mesh']]['primitives'][clip['primitive']]
    head_color,head_mr,head_rough=atlas(clipped,clip_binary,head_primitive)
    incident={};verified=[]
    for fi in deleted:
        center=tuple(sum(points[i][a]for i in faces[fi])/3 for a in range(3))
        if not (.73<center[1]<.86 and abs(center[2])<.07):continue
        coord=tuple(sum(uv[i][a]for i in faces[fi])/3 for a in range(2));rgb=pixel(body_color,coord)
        ref={'source_face':fi,'barycentric':[1/3]*3,'uv':list(coord),'rgb':list(rgb)}
        if skin_rgb(rgb):verified.append((center,ref))
        for i in faces[fi]:incident.setdefault(key(points[i]),[]).append((fi,i))
    if not verified:raise ValueError('No verified removed original neck-skin atlas samples')
    bottom_colors=[];bottom_rough=[];top_colors=[];top_rough=[];sample_refs=[]
    def rough(image,coord,factor):return (pixel(image,coord)[1]/255 if image else 1)*factor
    for index,position in enumerate(base):
        refs=[]
        for fi,vid in incident.get(key(position),[]):
            bary=[.07,.07,.07];bary[faces[fi].index(vid)]=.86
            coord=tuple(sum(uv[v][a]*w for v,w in zip(faces[fi],bary))for a in range(2));rgb=pixel(body_color,coord)
            if skin_rgb(rgb):refs.append({'source_face':fi,'barycentric':bary,'uv':list(coord),'rgb':list(rgb)})
        adjacent=bool(refs)
        if not refs:
            nearest=sorted(verified,key=lambda row:math.dist(position,row[0]))
            limit=math.dist(position,nearest[0][0])+.004
            refs=[row[1]for row in nearest[:5]if math.dist(position,row[0])<=limit]
        color=tuple(median([linear(ref['rgb'][channel])for ref in refs])for channel in range(3))
        value=median([rough(body_mr,ref['uv'],body_rough)for ref in refs])
        bottom_colors.append(color);bottom_rough.append((value,))
        sample_refs.append({'side':'body','u':low_t[index],'source_vertex_id':base_ids[index],'position_raw_gltf':list(position),
                            'samples':refs,'adjacent_removed_skin':adjacent,'linear_rgb':list(color),'roughness':value})
    for index,refs in enumerate(top_samples):
        actual=[]
        for ref in refs:
            rgb=pixel(head_color,ref['uv']);actual.append({**ref,'rgb':list(rgb)})
        color=tuple(sum(linear(ref['rgb'][channel])for ref in actual)/len(actual)for channel in range(3))
        value=sum(rough(head_mr,ref['uv'],head_rough)for ref in actual)/len(actual)
        top_colors.append(color);top_rough.append((value,))
        sample_refs.append({'side':'head','u':high_t[index],'position_raw_gltf':list(top[index]),'samples':actual,'linear_rgb':list(color),'roughness':value})
    color_image=Image.new('RGB',(1024,256));mr_image=Image.new('RGB',(1024,256));color_px=color_image.load();mr_px=mr_image.load()
    for x in range(1024):
        coordinate=x/1023;lower,_,_=sample(bottom_colors,low_t,coordinate);upper,_,_=sample(top_colors,high_t,coordinate)
        lower_r,_,_=sample(bottom_rough,low_t,coordinate);upper_r,_,_=sample(top_rough,high_t,coordinate)
        for y in range(256):
            t=y/255;color_px[x,y]=tuple(srgb(value)for value in mix(lower,upper,t))
            mr_px[x,y]=(255,round(255*((1-t)*lower_r[0]+t*upper_r[0])),0)
    atlas_jump=max(abs(color_px[x,y][channel]-color_px[(x+1)%1024,y][channel])for y in range(256)for x in range(1024)for channel in range(3))
    front_columns=[x for x in range(1023)if sample(top,high_t,x/1023)[0][0]>0]
    front_jump=max([abs(color_px[x,y][channel]-color_px[x+1,y][channel])for x in front_columns for y in range(256)for channel in range(3)]or[0])
    if front_jump>8:raise ValueError('Front neck skin atlas has an adjacent color jump above eight')
    dark_controls=[row for row in sample_refs if row['side']=='head' and srgb(row['linear_rgb'][0])<70]
    image_color=append_image(result,binary,color_image,'tripo_neck_continuous_basecolor');image_mr=append_image(result,binary,mr_image,'tripo_neck_continuous_mr')
    sampler=len(result.setdefault('samplers',[]));result['samplers'].append({'wrapS':10497,'wrapT':33071})
    texture_color=len(result.setdefault('textures',[]));result['textures'].extend([{'source':image_color,'sampler':sampler},{'source':image_mr,'sampler':sampler}])
    material=len(result['materials']);result['materials'].append({'name':'tripo_neck_continuous','doubleSided':False,'pbrMetallicRoughness':{'baseColorTexture':{'index':texture_color},'metallicRoughnessTexture':{'index':texture_color+1},'metallicFactor':0,'roughnessFactor':1}})
    attributes={'POSITION':append_rows(result,binary,positions,'VEC3'),'NORMAL':append_rows(result,binary,loft_norm,'VEC3'),'TEXCOORD_0':append_rows(result,binary,uvs,'VEC2'),'JOINTS_0':append_rows(result,binary,joints,'VEC4',5123),'WEIGHTS_0':append_rows(result,binary,weights,'VEC4')}
    loft_primitive=len(primitives);primitives.append({'attributes':attributes,'indices':append_indices(result,binary,loft),'material':material})
    output=g.encode_glb(result,binary)
    report={'body_source_sha256':body_sha,'head_source_sha256':head_sha,'output_sha256':g.sha(output),'body_mesh':mesh,'body_keep_original_face_ids':kept,'body_delete_original_face_ids':deleted,'all_protected_collar_faces_retained':not any(i in deleted for i in protected),'original_body_binary_prefix_equal':bytes(binary[:len(body_binary)])==body_binary,'original_nodes_rest_equal':result['nodes']==body['nodes'],'original_skins_equal':result['skins']==body['skins'],'clip':clip,'loft':{'primitive':loft_primitive,'vertices':len(positions),'triangles':len(loft),'rings':[len(r)-1 for r in rings],'base_source_vertex_ids':base_ids,'lower_exact_source_weights':True,'upper_Head_weight':1,'intermediate_ring_fractions':[.25,.5,.75],'atlas_size':[1024,256],'atlas_source_samples':sample_refs,'atlas_maximum_adjacent_u_rgb_jump':atlas_jump,'atlas_front_neck_maximum_adjacent_u_rgb_jump':front_jump,'actual_dark_head_controls':dark_controls,'atlas_color_interpolation':'linear-light colors after actual per-chart endpoint sampling; no UV interpolation','zero_area_faces':zero,'geometry_safety':safety,'maximum_lower_field':max(field(p)for p in base),'minimum_upper_field':min(field(p)for p in top),'clip_field':'Y+.6*X','clip_c':CUT_C},'limitations':['Anatomical oblique clip separates all original anchors from retained head; actual-pose visual review remains required.','Actual dark posterior nape chart samples are preserved with exact positions/UV references; global atlas jump can exceed front-skin bounds at that source transition.','No native rendering, dynamic comfort or runtime shading is proven by this authoring report.']}
    encoded,encoded_binary=decode(output)
    head_runtime=next(row['output_primitive'] for row in graft['head_primitive_mapping'] if row['head_primitive']==clip['primitive'])
    report['interface_verification']=verify_interfaces(encoded,encoded_binary,0,head_runtime,loft_primitive)
    return output,report



def verify_interfaces(document,binary,body_index,head_index,loft_index):
    from collections import Counter
    primitives=document['meshes'][0]['primitives']
    edges=Counter();directed=Counter();weighted={};maximum_difference=0.
    for index in (body_index,head_index,loft_index):
        primitive=primitives[index];positions,faces=g.triangles(document,binary,primitive)
        joints=g.accessor_rows(document,binary,primitive['attributes']['JOINTS_0'])
        weights=g.accessor_rows(document,binary,primitive['attributes']['WEIGHTS_0'])
        for face in faces:
            for a,b in zip(face,face[1:]+face[:1]):
                ka,kb=key(positions[a]),key(positions[b]);edges[tuple(sorted((ka,kb)))]+=1;directed[(ka,kb)]+=1
        for vertex in set(v for face in faces for v in face):
            position=key(positions[vertex]);row={}
            for joint,weight in zip(joints[vertex],weights[vertex]):
                if weight>0:row[joint]=row.get(joint,0)+weight
            if position in weighted:
                old=weighted[position]
                maximum_difference=max(maximum_difference,max([abs(old.get(j,0)-row.get(j,0)) for j in set(old)|set(row)]or[0]))
            else:weighted[position]=row
    primitive=primitives[loft_index];positions,faces=g.triangles(document,binary,primitive)
    coords=g.accessor_rows(document,binary,primitive['attributes']['TEXCOORD_0'])
    counts={}
    for value,name in ((0.,'lower'),(1.,'upper')):
        ids=[i for i,uv in enumerate(coords)if uv[1]==value]
        values=Counter(edges[tuple(sorted((key(positions[a]),key(positions[b]))))] for a,b in zip(ids[:-1],ids[1:]))
        if set(values)!={2}:raise ValueError('Continuous-neck interface is not watertight')
        for a,b in zip(ids[:-1],ids[1:]):
            ka,kb=key(positions[a]),key(positions[b])
            if directed[(ka,kb)]!=1 or directed[(kb,ka)]!=1:raise ValueError('Continuous-neck interface directed edge winding differs')
        counts[name+'_edge_incidence']=dict(values)
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):
            ka,kb=key(positions[a]),key(positions[b])
            if directed[(ka,kb)]!=1 or directed[(kb,ka)]!=1:raise ValueError('Continuous loft directed edge winding differs')
    counts['all_loft_edges_opposed']=True
    if maximum_difference!=0:raise ValueError('Coincident interface bone weights differ')
    counts['opposing_directed_edge_incidence_verified']=True
    counts['maximum_coincident_weight_component_difference']=maximum_difference
    counts['zero_LBS_seam_for_arbitrary_bone_transforms']=True
    return counts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('body','head','audit','output','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if len({p.resolve()for p in (args.body,args.head,args.audit,args.output,args.report)})!=5:parser.error('All paths must differ')
    body,bb=g.read_glb(args.body);head,hb=g.read_glb(args.head);audit=json.loads(args.audit.read_text())
    output,report=build(body,bb,head,hb,audit,g.sha(args.body.read_bytes()),g.sha(args.head.read_bytes()))
    args.output.parent.mkdir(exist_ok=True,parents=True);args.report.parent.mkdir(exist_ok=True,parents=True);args.output.write_bytes(output);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'body_faces':len(report['body_keep_original_face_ids']),'loft':{k:v for k,v in report['loft'].items()if k in ('vertices','triangles','rings')},'sha256':report['output_sha256']}))


if __name__=='__main__':main()
