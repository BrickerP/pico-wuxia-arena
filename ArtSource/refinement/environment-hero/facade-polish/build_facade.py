"""One courtyard, a family of shared window cores, and one batched eave edge.

Reads the accepted 9b scene and 2fb named construction; writes facade-polish
only. No image/material is added. Upper members change length around protected
joinery bands; cross-sections, rebates and lap widths do not get globally scaled.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import sys

import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
SOURCE=BASE/'single-window-integration-2026-11-12/courtyard_one_window.glb'
CONSTRUCTION=BASE/'method-study-2026-11-12/window_infill_construction.glb'
MODULE=BASE/'method-study-2026-11-12/window_infill_candidate.glb'
EXPECTED='9b259812a46f07e95dab6b4e4c414521c05118366ed09fca9632bebc51c27dd5'
sys.path.insert(0,str(BASE));from verify_environment import read,rows,active_nodes,world_primitives
sys.path.insert(0,str(BASE/'single-window-integration-2026-11-12'));from build_courtyard import Output,clip_wall
sys.path.insert(0,str(BASE/'stage2'));from create_candidate import encode,components,tangents
GROUND=[(-4.62,-5.535,-3.715),(2.47,1.515,3.485),(4.62,3.715,5.535)]
UPPER=[(-4.55,-5.535,-3.715),(-2.30,-3.485,-1.515),(0,-1.285,1.285),(2.30,1.515,3.485),(4.55,3.715,5.535)]
DX=.045;DY=.185

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def append_node(d,node,parent=None):
    d['nodes'].append(node);i=len(d['nodes'])-1
    if parent is not None:d['nodes'][parent].setdefault('children',[]).append(i)
    return i
def remove_old_windows(doc,blob,out):
    targets=[]
    for x,_,_ in GROUND:targets.append((x,1.7,1.34,1.5,-5.44,-5.31))
    for x,_,_ in UPPER:targets.append((x,3.97,1.45,1.12,-5.46,-5.33))
    reports=[]
    for pi,p in enumerate(doc['meshes'][4]['primitives']):
        v=rows(doc,blob,p['attributes']['POSITION']);ix=rows(doc,blob,p['indices']).reshape(-1,3)
        chosen=set();counts=[0]*8
        for group in components(v,ix):
            a,b=v[group].min(axis=0),v[group].max(axis=0)
            for j,(x,y,w,h,z0,z1) in enumerate(targets):
                lo=np.array([x-w/2-.06,y-h/2-.06,z0]);hi=np.array([x+w/2+.06,y+h/2+.06,z1])
                if np.all(a>=lo-2e-5) and np.all(b<=hi+2e-5):
                    # Unreferenced vertices of the already removed first window
                    # are outside these eight boxes; use only actual triangles.
                    if np.isin(ix,group).any():chosen.update(group.tolist());counts[j]+=1
        keep=np.array([not any(int(i) in chosen for i in t) for t in ix])
        out.doc['meshes'][4]['primitives'][pi]['indices']=out.accessor(ix[keep].reshape(-1,1),'SCALAR',True)
        expected=[4,9,1,0][pi]
        if counts!=[expected]*8:raise ValueError('Window component selection mismatch: '+str((pi,counts)))
        reports.append({'primitive':pi,'parts_per_window':counts,'removed_triangles':int((~keep).sum())})
    return reports

def shift_bands(values,bands):
    knots=[]
    for center,width,delta in bands:knots.extend([(center-width,delta),(center+width,delta)])
    knots=sorted(knots);return np.interp(values,[k[0] for k in knots],[k[1] for k in knots])
def upper_positions(name,p,n):
    q=p.copy();normal=n.copy();cx=.03
    if name.startswith('RebatedCase') or name.startswith('InnerReveal'):
        q[:,0]+=np.where(p[:,0]<cx,-DX,DX);q[:,1]+=np.where(p[:,1]<1.7,DY,-DY)
    elif name=='SlopedSill':
        q[:,0]+=np.where(p[:,0]<cx,.065,-.065);q[:,1]+=DY
    elif name.startswith(('LeftSash','RightSash')):
        left=name.startswith('Left');leafcx=-.2725 if left else .3325
        if 'HingeBarrel' in name:
            q[:,0]+= -DX if left else DX;q[:,1]+=np.where(p[:,1]<1.7,DY,-DY)
        elif 'Paper' in name:
            lo,hi=p[:,0].min(),p[:,0].max();u=(p[:,0]-lo)/(hi-lo)
            q[:,0]+= -DX*(1-u) if left else DX*u
            sy=(1.24-2*DY)/1.24;sx=(.53+DX)/.53;q[:,1]=1.7+(p[:,1]-1.7)*sy
            normal[:,0]/=sx;normal[:,1]/=sy;normal/=np.linalg.norm(normal,axis=1,keepdims=True)
        else:
            outer=leafcx+(-.2775 if left else .2775);inner=leafcx+(.2775 if left else -.2775)
            bars=[leafcx-.088,leafcx+.088];low=leafcx-.3
            def delta(x):
                t=(x-low)/.6;return -DX*(1-t) if left else DX*t
            xb=[(outer,.04,-DX if left else DX),(inner,.04,0)]+[(x,.02,delta(x)) for x in bars]
            yb=[(1.0575,.04,DY),(1.39,.02,DY*.5),(1.7,.02,0),(2.01,.02,-DY*.5),(2.3425,.04,-DY)]
            q[:,0]+=shift_bands(p[:,0],xb);q[:,1]+=shift_bands(p[:,1],yb)
    else:raise ValueError('Unexpected core part '+name)
    return q,normal

class MeshBuilder:
    def __init__(self):self.groups={}
    def triangle(self,points,normals,uv,mat):
        g=self.groups.setdefault(mat,{'p':[],'n':[],'uv':[],'ix':[],'lookup':{}});indices=[]
        for p,n,u in zip(points,normals,uv):
            key=tuple(np.round(np.r_[p,n,u],8))
            if key not in g['lookup']:
                g['lookup'][key]=len(g['p']);g['p'].append(p);g['n'].append(n);g['uv'].append(u)
            indices.append(g['lookup'][key])
        g['ix'].append(indices)
    def face(self,points,mat):
        points=np.asarray(points,dtype=float);n=np.cross(points[1]-points[0],points[2]-points[0]);n/=np.linalg.norm(n)
        tex=np.zeros((len(points),2))
        if mat==5:
            axis=int(np.argmax(np.abs(n)))
            if axis==2:tex=np.column_stack((points[:,0]/.6,1-points[:,1]/.6))
            elif axis==0:tex=np.column_stack((-points[:,2]/.6,1-points[:,1]/.6))
            else:tex=np.column_stack((points[:,0]/.6,1+points[:,2]/.6))
        for j in range(1,len(points)-1):
            tri=points[[0,j,j+1]];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
            self.triangle(tri,[normal,normal,normal],tex[[0,j,j+1]],mat)
    def write(self,out,name):
        primitives=[];dropped=0
        for mat,g in self.groups.items():
            p=np.asarray(g['p'],dtype=np.float32);n=np.array(g['n']);uv=np.array(g['uv']);ix=np.array(g['ix'])
            triangles=p[ix].astype(float)
            area2=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)
            keep=area2>1e-14;dropped+=int((~keep).sum());ix=ix[keep]
            used=np.unique(ix);remap=np.full(len(p),-1,dtype=int);remap[used]=np.arange(len(used));ix=remap[ix]
            p=p[used];n=n[used];uv=uv[used];n/=np.linalg.norm(n,axis=1,keepdims=True)
            attr={'POSITION':out.accessor(p,'VEC3'),'NORMAL':out.accessor(n,'VEC3'),'TEXCOORD_0':out.accessor(uv,'VEC2')}
            if 'normalTexture' in out.doc['materials'][mat]:
                fallback=np.tile([1.,0,0,1],(len(p),1));fallback[np.abs(n[:,0])>.95,:3]=[0,0,1]
                attr['TANGENT']=out.accessor(tangents(p,n,uv,ix,fallback),'VEC4')
            primitives.append({'attributes':attr,'indices':out.accessor(ix.reshape(-1,1),'SCALAR',True),'material':mat,'mode':4})
        out.doc['meshes'].append({'name':name,'primitives':primitives,
          'extras':{'removed_float32_degenerate_triangles':dropped}});return len(out.doc['meshes'])-1

def upper_core(out):
    d,b=read(CONSTRUCTION);builder=MeshBuilder();parts=[]
    for name,primitive,p,ix in world_primitives(d,b):
        if name=='OpeningWall':continue
        # The construction mesh nodes have translation only; normals are already
        # in the same local Stage orientation as their world positions.
        n=rows(d,b,primitive['attributes']['NORMAL']);uv=rows(d,b,primitive['attributes']['TEXCOORD_0'])
        material=d['materials'][primitive['material']]['name']
        mat={'Method | CC0 directional wood .8m':29,'Method | original endgrain .25m':30,
             'EH S2 Windows | layered paper emission':4,'Method | dark iron':31}[material]
        q,nn=upper_positions(name,p,n)
        horizontal=('Horizontal' in name or name=='SlopedSill' or ('Frame_' in name and name.split('_')[-1] in ['0','2'])
                    or ('RebatedCase_' in name and name[-1] in ['0','2'])
                    or (name.startswith('InnerReveal') and np.ptp(p[:,0])>np.ptp(p[:,1])))
        grain=np.array([1.,0,0]) if horizontal else np.array([0,1.,0])
        seed=int(hashlib.sha256(name.encode()).hexdigest()[:8],16);shift=np.array([(seed%997)/997,((seed//997)%991)/991])
        for tri in ix:
            tex=uv[tri]
            if mat in [29,30]:
                normal=np.cross(q[tri[1]]-q[tri[0]],q[tri[2]]-q[tri[0]])
                if np.linalg.norm(normal)<1e-14:continue
                normal/=np.linalg.norm(normal)
                v=grain-normal*np.dot(normal,grain)
                if np.linalg.norm(v)<1e-6:
                    v=np.eye(3)[int(np.argmin(np.abs(normal)))];v-=normal*np.dot(normal,v)
                v/=np.linalg.norm(v);u=np.cross(v,normal);tile=.25 if mat==30 else .8
                tex=np.column_stack((q[tri]@u/tile+shift[0],1-q[tri]@v/tile+shift[1]))
            builder.triangle(q[tri],nn[tri],tex,mat)
        parts.append({'name':name,'source_bounds':[p.min(axis=0).tolist(),p.max(axis=0).tolist()],
                      'upper_bounds':[q.min(axis=0).tolist(),q.max(axis=0).tolist()]})
    return builder.write(out,'Facade_UpperWindowCore'),parts

def wall_patches(out):
    d,b=read(MODULE);name,pr,p,ix=next(world_primitives(d,b));assert pr['material']==0
    n=rows(d,b,pr['attributes']['NORMAL']);builder=MeshBuilder();specs=[]
    for upper,items in [(False,GROUND),(True,UPPER)]:
        for center,lo,hi in items:
            anchor=center-.03;offset=2.27 if upper else 0;bottom,top=(3.235,4.715) if upper else (.515,2.765)
            q=p.copy()
            left=np.isclose(p[:,0],-.985,atol=1e-5);right=np.isclose(p[:,0],.985,atol=1e-5)
            if upper:
                q[:,0]+=np.where(p[:,0]<.03,-DX,DX);q[:,1]+=np.where(p[:,1]<1.7,DY,-DY)
            q[left,0]=lo-anchor;q[right,0]=hi-anchor
            q[np.isclose(p[:,1],.515,atol=1e-5),1]=bottom-offset
            q[np.isclose(p[:,1],2.765,atol=1e-5),1]=top-offset
            q+=np.array([anchor,offset,-5.51])
            for tri in ix:
                normal=np.cross(q[tri[1]]-q[tri[0]],q[tri[2]]-q[tri[0]]);axis=int(np.argmax(np.abs(normal)))
                if axis==2:tex=np.column_stack((q[tri,0]/2.5,1-q[tri,1]/5.5))
                elif axis==0:tex=np.column_stack((-q[tri,2]/2.5,1-q[tri,1]/5.5))
                else:tex=np.column_stack((q[tri,0]/2.5,1+q[tri,2]/5.5))
                builder.triangle(q[tri],n[tri],tex,25)
            specs.append({'center_x':center,'upper':upper,'wall_bounds':{'min':[lo,bottom,-5.79],'max':[hi,top,-5.51]}})
    return builder.write(out,'Facade_RebuiltWallInfills'),specs

def eave_edge(doc,blob,out):
    p=doc['meshes'][20]['primitives'][1];v=rows(doc,blob,p['attributes']['POSITION']);ix=rows(doc,blob,p['indices']).reshape(-1,3)
    chosen=set();groups=0
    for group in components(v,ix):
        a,b=v[group].min(axis=0),v[group].max(axis=0)
        if a[2]>=-4.18255 and b[2]<=-4.09745 and b[2]>-4.11:
            if np.isin(ix,group).any():chosen.update(group.tolist());groups+=1
    keep=np.array([not any(int(i) in chosen for i in t) for t in ix]);removed=int((~keep).sum())
    if removed!=190:raise ValueError('Porch edge selection mismatch '+str((removed,groups)))
    out.doc['meshes'][20]['primitives'][1]['indices']=out.accessor(ix[keep].reshape(-1,1),'SCALAR',True)
    builder=MeshBuilder();segments=12;units=59
    cover_triangles=v[ix[keep]]
    pan=doc['meshes'][20]['primitives'][0]
    pv=rows(doc,blob,pan['attributes']['POSITION']);pi=rows(doc,blob,pan['indices']).reshape(-1,3)
    pan_triangles=pv[pi]
    def surface_y(triangles,x,z):
        a=triangles[:,0];e1=triangles[:,1]-a;e2=triangles[:,2]-a
        det=e1[:,0]*e2[:,2]-e1[:,2]*e2[:,0];valid=np.abs(det)>1e-12
        inverse=np.divide(1.,det,out=np.zeros_like(det),where=valid)
        sx=x-a[:,0];sz=z-a[:,2]
        u=(sx*e2[:,2]-sz*e2[:,0])*inverse;w=(e1[:,0]*sz-e1[:,2]*sx)*inverse
        good=valid&(u>=-2e-5)&(w>=-2e-5)&(u+w<=1+2e-5)
        if not good.any():raise ValueError('No frozen roof surface at '+str((x,z)))
        return float(np.max((a[:,1]+u*e1[:,1]+w*e2[:,1])[good]))
    for k in range(units):
        x=-6.10+.21*k
        # The accepted roof's rolled caps have a five-segment half-profile;
        # recover its actual base instead of guessing a new constant elevation.
        crown=.035*math.sin(2*math.pi/5)
        cy_back=surface_y(cover_triangles,x,-4.18)-crown
        cy_front=surface_y(cover_triangles,x,-4.145)-crown
        # An open half-tube follows the existing cover tile, rather than a large
        # solid coin. Four rings make its ceramic wall a closed thin volume.
        rings=[[(x+rx*math.cos(i*math.pi/segments),cy+ry*math.sin(i*math.pi/segments),z)
                for i in range(segments+1)] for rx,ry,z in
               [(.046,.036,-4.18),(.046,.036,-4.115),(.036,.027,-4.115),(.036,.027,-4.18)]
               for cy in [cy_back if z< -4.15 else cy_front]]
        for a,b in zip(rings,rings[1:]+rings[:1]):
            for i in range(segments):
                j=i+1;builder.face([a[i],a[j],b[j],b[i]],5)
        builder.face([ring[0] for ring in rings],5)
        builder.face([ring[-1] for ring in reversed(rings)],5)
        if k==units-1:continue
        # Drip tongues belong between the cover tiles; the final narrow pan is
        # deliberately omitted rather than extending beyond the existing roof.
        px=x+.105
        outline=[(-.061,.005),(-.053,-.045),(0,-.070),(.053,-.045),(.061,.005)]
        front=[(px+a,surface_y(pan_triangles,px+a,-4.145)+b,-4.13) for a,b in outline]
        back=[(px+a,surface_y(pan_triangles,px+a,-4.18)+b,-4.18) for a,b in outline]
        builder.face(front,5);builder.face(list(reversed(back)),5)
        for i in range(5):
            j=(i+1)%5;builder.face([front[i],back[i],back[j],front[j]],5)
    return builder.write(out,'Facade_BatchedTileEnds'),{'removed_front_edge_triangles':removed,'units':units,
          'drip_tongues':58,'material':5,'image_delta':0,'construction':'thin half-tube rims with drip tongues in the intervening pans',
          'node_strategy':'one batched row; no per-tile draw/node explosion'}

def budget(d,b):
    frames=active_nodes(d);used_meshes={d['nodes'][i]['mesh'] for i in frames if 'mesh' in d['nodes'][i]}
    attrs=set();indices=set();position=set();unique_tris=0
    for mi in used_meshes:
        for p in d['meshes'][mi]['primitives']:
            position.add(p['attributes']['POSITION']);unique_tris+=d['accessors'][p['indices']]['count']//3
            attrs.update(d['accessors'][a]['bufferView'] for a in p['attributes'].values());indices.add(d['accessors'][p['indices']]['bufferView'])
    expanded=sum(sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][d['nodes'][i]['mesh']]['primitives']) for i in frames if 'mesh' in d['nodes'][i])
    draws=sum(len(d['meshes'][d['nodes'][i]['mesh']]['primitives']) for i in frames if 'mesh' in d['nodes'][i])
    return {'node_expanded_triangles':expanded,'unique_mesh_triangles':unique_tris,'active_unique_meshes':len(used_meshes),
      'unique_position_stream_vertices':sum(d['accessors'][i]['count'] for i in position),
      'unique_attribute_buffer_bytes':sum(d['bufferViews'][i]['byteLength'] for i in attrs),
      'unique_index_buffer_bytes':sum(d['bufferViews'][i]['byteLength'] for i in indices),
      'primitive_node_submission_upper_estimate':draws,'materials':len(d['materials']),'images':len(d['images'])}

def main():
    if sha(SOURCE)!=EXPECTED:raise ValueError('Formal source9b changed')
    doc,blob=read(SOURCE);out=Output(copy.deepcopy(doc),blob);root=doc['scenes'][doc.get('scene',0)]['nodes'][0]
    removed=remove_old_windows(doc,blob,out)
    specs=[{'min':[lo,.515,-5.79],'max':[hi,2.765,-5.51]} for x,lo,hi in GROUND]
    specs += [{'min':[lo,3.235,-5.79],'max':[hi,4.715,-5.51]} for x,lo,hi in UPPER]
    clips=[clip_wall(out.doc,out.blob,out,s) for s in specs]
    # Separate the accepted first wall from its original four material core
    # primitives; all four ground windows reference exactly those same streams.
    core=copy.deepcopy(out.doc['meshes'][31]);core['name']='Facade_SharedGroundWindowCore';core['primitives']=core['primitives'][1:]
    out.doc['meshes'][31]['primitives']=out.doc['meshes'][31]['primitives'][:1]
    out.doc['meshes'].append(core);ground_mesh=len(out.doc['meshes'])-1
    first=copy.deepcopy(doc['nodes'][39]);first['name']='Facade_GroundWindow_Existing';first['mesh']=ground_mesh
    lower_nodes=[append_node(out.doc,first,40)]
    for x,_,_ in GROUND:
        lower_nodes.append(append_node(out.doc,{'name':f'Facade_GroundWindow_{x}','mesh':ground_mesh,
          'translation':[x-.03,1.6399999856948853,-5.650000000596047]},root))
    upper_mesh,part_report=upper_core(out);upper_nodes=[]
    for x,_,_ in UPPER:
        upper_nodes.append(append_node(out.doc,{'name':f'Facade_UpperWindow_{x}','mesh':upper_mesh,'translation':[x-.03,2.27,-5.51]},root))
    wall_mesh,wall_report=wall_patches(out);append_node(out.doc,{'name':'Facade_WallInfills','mesh':wall_mesh},root)
    roof_mesh,roof_report=eave_edge(doc,blob,out);append_node(out.doc,{'name':'Facade_TileEndRow','mesh':roof_mesh},root)
    assert out.doc['materials']==doc['materials'] and out.doc['images']==doc['images'] and out.doc['textures']==doc['textures']
    target=HERE/'courtyard_facade_polish.glb';target.write_bytes(encode(out.doc,out.blob))
    manifest={'status':'constructed_for_visual_review','candidate':target.name,'sha256':sha(target),'source_sha256':EXPECTED,
       'construction_sha256':sha(CONSTRUCTION),'module_sha256':sha(MODULE),'producer_sha256':sha(Path(__file__)),
       'placement_stage_m':[0,0,0],'rotation':'identity','scale':[1,1,1],'removed_windows':removed,'wall_clips':clips,
       'ground_core':{'mesh':ground_mesh,'nodes':lower_nodes,'instance_count':4,'source_vertex_streams_reused':True},
       'upper_core':{'mesh':upper_mesh,'nodes':upper_nodes,'instance_count':5,'cross_sections_unchanged':True,
          'width_length_delta_m':.09,'height_length_delta_m':-.37,'sill_width_m':1.57,'parts':part_report},
       'wall_infills':wall_report,'eave':roof_report,'source_budget':budget(doc,blob),'candidate_budget':budget(out.doc,out.blob),
       'source_bytes':SOURCE.stat().st_size,'candidate_bytes':target.stat().st_size,'added_images':0,'added_materials':0,
       'draw_caveat':'node-shared mesh guarantees shared geometry storage only; estimated submissions are not measured drawcalls or a hardware instancing guarantee',
       'kept':['one courtyard/scene','origin','ground receivers','light anchors','door opening and door meshes','post/beam structure','combat clearance','formal app/source files']}
    (HERE/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'sha256':manifest['sha256'],'bytes':manifest['candidate_bytes'],'source':manifest['source_budget'],
                      'candidate':manifest['candidate_budget'],'images_added':0,'materials_added':0},indent=2))
if __name__=='__main__':main()
