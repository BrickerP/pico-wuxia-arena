"""Canonical full blade-grip sampling and whole-shape interval certification.

A focused geometry helper for attack_profiles.py, not a second publication path.
Profiles remain in their canonical JSON and typed-generator formats. No file,
private-artifact import or SDK access occurs here.
"""
import copy
import math
import numpy as np
from production_contract import BLADE_GRIP_PROFILE_POLICY

NUMERIC_PAD = BLADE_GRIP_PROFILE_POLICY['offline_numeric_allowance_m']
C = np.eye(4)


def finite(a, name='geometry'):
    a = np.asarray(a, dtype=float)
    if not np.isfinite(a).all():
        raise ValueError(name + ' must be finite')
    return a

def quat_matrix(value):
    q = finite(value, 'quaternion'); n = np.linalg.norm(q)
    if q.shape != (4,) or n < 1e-15:
        raise ValueError('invalid quaternion')
    x, y, z, w = q / n
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def local_matrix(node):
    if 'matrix' in node:
        return finite(node['matrix']).reshape(4,4).T.copy()
    m = np.eye(4); m[:3,:3] = quat_matrix(node.get('rotation',[0,0,0,1])) @ np.diag(finite(node.get('scale',[1,1,1])))
    m[:3,3] = finite(node.get('translation',[0,0,0])); return m

def transform(matrix, points):
    p = finite(points); return np.c_[p, np.ones(len(p))] @ matrix.T[:, :3]

C[:3,:3] = quat_matrix([-math.sqrt(.5),0,0,math.sqrt(.5)])

def matrix_quaternion(r):
    trace=float(np.trace(r))
    if trace>0:
        s=math.sqrt(trace+1)*2;q=[(r[2,1]-r[1,2])/s,(r[0,2]-r[2,0])/s,(r[1,0]-r[0,1])/s,s/4]
    else:
        i=int(np.argmax(np.diag(r)));j=(i+1)%3;k=(i+2)%3;s=math.sqrt(max(0,1+r[i,i]-r[j,j]-r[k,k]))*2
        if s<1e-15:raise ValueError('invalid proper rotation')
        q=[0.,0.,0.,0.];q[i]=s/4;q[j]=(r[j,i]+r[i,j])/s;q[k]=(r[k,i]+r[i,k])/s;q[3]=(r[k,j]-r[j,k])/s
    q=np.array(q);q/=np.linalg.norm(q)
    if q[3]<0:q=-q
    return q.tolist()

def extract_rigid(matrix):
    m=finite(matrix,'grip matrix')
    if m.shape!=(4,4) or np.max(abs(m[3]-[0,0,0,1]))>1e-12:raise ValueError('expected affine 4x4 grip matrix')
    if np.linalg.det(m[:3,:3])<=0:raise ValueError('grip reflection/negative scale forbidden')
    u,s,v=np.linalg.svd(m[:3,:3]);r=u@v
    if np.max(abs(s-1))>2e-5 or np.linalg.det(r)<0:raise ValueError('grip materially non-unit scale')
    return {'position_m':m[:3,3].tolist(),'rotation_xyzw':matrix_quaternion(r)}

def grip_matrix(grip):
    p=finite(grip['position_m']);q=finite(grip['rotation_xyzw'])
    if p.shape!=(3,) or q.shape!=(4,) or np.linalg.norm(q)<1e-15:raise ValueError('invalid required grip')
    if abs(np.linalg.norm(q)-1)>2e-6:raise ValueError('grip quaternion must be normalized')
    m=np.eye(4);m[:3,:3]=quat_matrix(q);m[:3,3]=p;return m

def quaternion_angle(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    if a@b<0:b=-b
    return 4*math.atan2(float(np.linalg.norm(b-a)),float(np.linalg.norm(b+a)))

def slerp(a,b,f):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    if a@b<0:b=-b
    angle=quaternion_angle(a,b)/2
    q=(1-f)*a+f*b if angle<1e-15 else (math.sin((1-f)*angle)*a+math.sin(f*angle)*b)/math.sin(angle)
    return q/np.linalg.norm(q)

def interpolate_grip(a,b,f):
    if not math.isfinite(f) or not 0<=f<=1:raise ValueError('fraction outside unit interval')
    grip_matrix(a);grip_matrix(b)
    return {'position_m':((1-f)*np.array(a['position_m'])+f*np.array(b['position_m'])).tolist(),'rotation_xyzw':slerp(a['rotation_xyzw'],b['rotation_xyzw'],f).tolist()}

def point_reconstruction_error(actual,grip,source):
    a=finite(actual);p=finite(source)
    if a.shape!=p.shape or p.ndim!=2 or p.shape[1]!=3 or not len(p):raise ValueError('corresponding Nx3 steel points required')
    return float(np.linalg.norm(a-transform(grip_matrix(grip),p),axis=1).max())

class PreparedDocument:
    """Active-scene view using the existing producer's accessor decoder."""
    def __init__(self, document, binary):
        self.doc=document;self.binary=binary;self.nodes=document['nodes'];self.parents={};self.reachable_nodes=[];self.cache={};self.by_name={};self.animation_tracks_cache={}
        self.default_scene=document.get('scene',0)
        if type(self.default_scene) is not int or not 0<=self.default_scene<len(document.get('scenes',[])):raise ValueError('invalid active scene')
        def visit(i,ancestors):
            if type(i) is not int or not 0<=i<len(self.nodes) or i in ancestors or i in self.reachable_nodes:raise ValueError('invalid active hierarchy')
            self.reachable_nodes.append(i);self.by_name.setdefault(self.nodes[i].get('name',''),[]).append(i)
            for child in self.nodes[i].get('children',[]):
                if child in self.parents:raise ValueError('multiple active parents')
                self.parents[child]=i;visit(child,ancestors|{i})
        for root in document['scenes'][self.default_scene]['nodes']:visit(root,set())

    def accessor(self,index):
        from attack_profiles import skin_attribute
        if index not in self.cache:self.cache[index]=skin_attribute(self.doc,self.binary,index)
        return self.cache[index]

    def node(self,name):
            ids=self.by_name.get(name,[])
            if len(ids)!=1: raise ValueError('expected one active node '+name)
            return ids[0]

    def tracks(self,clip):
        if clip in self.animation_tracks_cache:return self.animation_tracks_cache[clip]
        from attack_profiles import animation_tracks
        matches=[a for a in self.doc.get('animations',[]) if a.get('name')==clip]
        if len(matches)!=1:raise ValueError('missing or duplicate source clip '+clip)
        tracks,_=animation_tracks(self.doc,self.binary,matches[0],require_attack_range=False)
        decoded=[(i,path,np.asarray(t,dtype=np.float32),np.asarray(v,dtype=np.float32),kind)
                 for (i,path),(t,v,kind) in tracks.items()]
        self.animation_tracks_cache[clip]=decoded
        return decoded

    def world(self,clip=None,time=0.):
            if not math.isfinite(time):raise ValueError('nonfinite sample time')
            edits={}
            for i,path,t,v,interpolation in (self.tracks(clip) if clip else []):
                j=int(np.searchsorted(t,time,side='right')); a=max(0,j-1); b=min(j,len(t)-1)
                f=0. if a==b or interpolation=='STEP' else float((np.asarray(time,dtype=t.dtype)[()]-t[a])/(t[b]-t[a]))
                if path=='rotation':
                    va=v[a].astype(float);vb=v[b].astype(float);va/=np.linalg.norm(va);vb/=np.linalg.norm(vb)
                    dot=float(va@vb)
                    if dot<0:vb=-vb;dot=-dot
                    angle=math.acos(min(1.,dot));value=(1-f)*va+f*vb if angle<1e-8 else (math.sin((1-f)*angle)*va+math.sin(f*angle)*vb)/math.sin(angle)
                else:value=np.float32(1-f)*v[a]+np.float32(f)*v[b]
                edits.setdefault(i,{})[path]=value
            world={}
            for i in self.reachable_nodes:
                node=dict(self.nodes[i])
                if i in edits:
                    if 'matrix' in node:raise ValueError('animation on matrix node')
                    node.update(edits[i])
                m=local_matrix(node);world[i]=world[self.parents[i]]@m if i in self.parents else m
            return world

    def steel(self,world):
            verts=[];tris=[];sources=[];rigid=[]
            for node_index in self.reachable_nodes:
                node=self.nodes[node_index]
                if 'mesh' not in node:continue
                for pi,primitive in enumerate(self.doc['meshes'][node['mesh']]['primitives']):
                    material=self.doc['materials'][primitive['material']].get('name','')
                    if not material.startswith('Steel |'):continue
                    if primitive.get('mode',4)!=4:raise ValueError('steel must be triangles')
                    p=self.accessor(primitive['attributes']['POSITION'])
                    if 'skin' in node:
                        skin=self.doc['skins'][node['skin']];j=self.accessor(primitive['attributes']['JOINTS_0']).astype(int);w=self.accessor(primitive['attributes']['WEIGHTS_0']).astype(float)
                        if j.shape!=w.shape or np.any(w<0) or np.max(abs(w.sum(axis=1)-1))>1e-6:raise ValueError('invalid skin weights')
                        if j.min()<0 or j.max()>=len(skin['joints']):raise ValueError('skin joint index')
                        ibm=self.accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
                        palette=np.array([world[k] for k in skin['joints']])@ibm
                        matrices=(palette[j]*w[:,:,None,None]).sum(axis=1)
                        out=np.einsum('nij,nj->ni',matrices,np.c_[p,np.ones(len(p))])[:,:3]
                        active=set(j[w>1e-9].tolist()); rigid.append({'node':node_index,'primitive':pi,'joint_names':[self.nodes[skin['joints'][k]].get('name') for k in sorted(active)],'single_joint_weight_one':bool(np.all((w>1e-9).sum(axis=1)==1))})
                    else:out=transform(world[node_index],p)
                    ids=self.accessor(primitive['indices']).astype(int).ravel() if 'indices' in primitive else np.arange(len(p))
                    if len(ids)%3 or ids.min()<0 or ids.max()>=len(p):raise ValueError('invalid triangle indices')
                    tris.extend(out[ids.reshape(-1,3)]);verts.extend(out)
                    sources.append({'node_index':node_index,'node_name':node.get('name'),'primitive':pi,'material':material,'vertices':len(p),'triangles':len(ids)//3})
            if not tris:raise ValueError('no rendered steel in default scene')
            return np.array(verts),np.array(tris),sources,rigid


class PreparedGrip:
    def __init__(self,asset,player_points,support_radius_m):
        self.asset=asset;self.hand=asset.node('R_Hand');self.grip=asset.node('Grip');chain=[];i=self.grip
        while True:
            chain.append(i)
            if i not in asset.parents:break
            i=asset.parents[i]
        self.chain=list(reversed(chain));self.hand_chain=self.chain[:self.chain.index(self.hand)+1]
        self.tracks={};self.cache={}
        for animation in asset.doc['animations']:
            tracks={}
            for i,path,t,v,k in asset.tracks(animation['name']):
                if i in self.chain:
                    if k not in ['LINEAR','STEP']:raise ValueError('unsupported interpolation')
                    if k=='STEP' and np.any(v!=v[0]):raise ValueError('discontinuous grip ancestor track')
                    if path=='scale' and np.any(v!=v[0]):raise ValueError('nonconstant grip ancestor scale')
                    if i in self.chain[self.chain.index(self.hand)+1:]:raise ValueError('animated rigid grip descendant')
                    tracks[(i,path)]=(t,v,k)
            self.tracks[animation['name']]=tracks
        w=self.world('idle',0.);self.K=np.linalg.inv(w[self.hand])@w[self.grip]@np.linalg.inv(C)
        verts,_,_,rigid=asset.steel(asset.world('idle',0.))
        if not all(r['single_joint_weight_one'] and r['joint_names']==['R_Hand'] for r in rigid):raise ValueError('expected weight-one R_Hand steel')
        skin=next(asset.doc['skins'][asset.nodes[i]['skin']] for i in asset.reachable_nodes if 'skin'in asset.nodes[i]);palette=skin['joints'].index(self.hand)
        self.ibm=asset.accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)[palette]
        self.baked=np.concatenate([asset.accessor(p['attributes']['POSITION']) for i in asset.reachable_nodes if 'mesh'in asset.nodes[i] for p in asset.doc['meshes'][asset.nodes[i]['mesh']]['primitives'] if asset.doc['materials'][p['material']].get('name','').startswith('Steel |')])
        self.canonical=transform(np.linalg.inv(w[self.grip]@np.linalg.inv(C)),verts)
        if self.canonical.shape!=player_points.shape:raise ValueError('player/NPC Steel topology mismatch')
        self.mesh_error=float(np.linalg.norm(self.canonical-player_points,axis=1).max())
        if self.mesh_error>2e-6:raise ValueError('NPC shape differs from shared common Grip by more than 2um')
        self.player_points=player_points
        if not math.isfinite(support_radius_m) or support_radius_m<float(np.linalg.norm(player_points,axis=1).max()):raise ValueError('full blade support radius does not contain its actual Steel')
        self.support_radius=float(support_radius_m)
        self.local_hand_radius=float(np.linalg.norm(self.K[:3,3])+np.linalg.norm(self.K[:3,:3],2)*self.support_radius)
        for clip in self.tracks:
            full=asset.world(clip,.413);fast=self.world(clip,.413)
            if max(abs(full[i]-fast[i]).max() for i in self.chain)>2e-6:raise ValueError('independent FK disagrees with active-scene evaluator')

    def value(self,track,time,rotation=False):
        # Explicit source float32 arithmetic reproduces the bound data across
        # NumPy1 and2 promotion rules; full FK matrices remain float64.
        t,v,k=track;v=v.astype(float);j=int(np.searchsorted(t,time,side='right'));a=max(0,j-1);b=min(j,len(t)-1)
        f=0. if a==b or k=='STEP' else float((np.asarray(time,dtype=t.dtype)[()]-t[a])/(t[b]-t[a]))
        return slerp(v[a],v[b],f) if rotation else (1-f)*v[a]+f*v[b]

    def world(self,clip,time):
        key=(clip,float(time))
        if key in self.cache:return self.cache[key]
        tracks=self.tracks.get(clip,{}) if hasattr(self,'tracks') else {};w={}
        for i in self.chain:
            node=dict(self.asset.nodes[i])
            for path in ['translation','rotation','scale']:
                if (i,path) in tracks:node[path]=self.value(tracks[(i,path)],time,path=='rotation')
            m=local_matrix(node);w[i]=w[self.asset.parents[i]]@m if i in self.asset.parents else m
        self.cache[key]=w;return w

    def true_matrix(self,clip,time):return self.world(clip,time)[self.grip]@np.linalg.inv(C)
    def actual_points(self,clip,time):return transform(self.world(clip,time)[self.hand]@self.ibm,self.baked)

    def speed_acceleration_bounds(self,clip,start,end):
        """One source-key-free span. Constant local scales; local SLERP has alpha=0."""
        mid=(start+end)/2;rows=[]
        for i in self.hand_chain:
            node=self.asset.nodes[i];tracks=self.tracks[clip]
            if 'matrix'in node:
                m=local_matrix(node);scale=float(np.linalg.norm(m[:3,:3],2));translation=float(np.linalg.norm(m[:3,3]));v=omega=0.
            else:
                sc=self.value(tracks[(i,'scale')],mid) if (i,'scale')in tracks else node.get('scale',[1,1,1]);scale=float(max(abs(np.asarray(sc))))
                tr=tracks.get((i,'translation'));translation=max(float(np.linalg.norm(self.value(tr,start))),float(np.linalg.norm(self.value(tr,end)))) if tr else float(np.linalg.norm(node.get('translation',[0,0,0])))
                v=omega=0.
                for path in ['translation','rotation']:
                    track=tracks.get((i,path))
                    if track is None:continue
                    t,values,k=track;j=int(np.searchsorted(t,mid,side='right'))
                    if j==0 or j>=len(t) or k=='STEP':continue
                    dt=float(t[j]-t[j-1])
                    if path=='translation':v=float(np.linalg.norm(values[j].astype(float)-values[j-1].astype(float))/dt)
                    else:omega=quaternion_angle(values[j-1],values[j])/dt
            rows.append((scale,translation,v,omega))
        radius=self.local_hand_radius;velocity=acceleration=0.
        for scale,translation,v,omega in reversed(rows):
            acceleration=scale*(acceleration+2*omega*velocity+omega*omega*radius)
            velocity=v+scale*(velocity+omega*radius)
            radius=translation+scale*radius
        return velocity,acceleration

    def matrix_error_bound(self,actual,predicted):
        return float(np.linalg.norm(actual[:3,:3]-predicted[:3,:3],2)*self.support_radius+np.linalg.norm(actual[:3,3]-predicted[:3,3])+np.linalg.norm(actual[:3,:3],2)*self.mesh_error+NUMERIC_PAD)

    def interval_bound(self,clip,start,end,a,b):
        dt=end-start
        if dt<=0:raise ValueError('interval must increase')
        point_speed=float(np.linalg.norm(np.array(b['position_m'])-a['position_m'])/dt);omega=quaternion_angle(a['rotation_xyzw'],b['rotation_xyzw'])/dt
        interp_speed=point_speed+omega*self.support_radius;interp_accel=omega*omega*self.support_radius
        source_cuts=sorted({start,end,*[float(t) for track in self.tracks[clip].values() for t in track[0] if start<t<end]})
        cuts=sorted({float(t) for a0,b0 in zip(source_cuts[:-1],source_cuts[1:]) for t in np.linspace(a0,b0,BLADE_GRIP_PROFILE_POLICY['proof_subdivisions_per_source_span']+1)})
        pieces=[]
        for x,y in zip(cuts[:-1],cuts[1:]):
            speed,accel=self.speed_acceleration_bounds(clip,x,y)
            ea=self.matrix_error_bound(self.true_matrix(clip,x),grip_matrix(interpolate_grip(a,b,(x-start)/dt)))
            eb=self.matrix_error_bound(self.true_matrix(clip,y),grip_matrix(interpolate_grip(a,b,(y-start)/dt)))
            # For curves with matched endpoint linear interpolants, each curve's
            # deviation is <= M*h²/8. Source-key splitting isolates all angular-
            # velocity jumps; exact subspan endpoint error accounts for joins.
            h=y-x;second=max(ea,eb)+(accel+interp_accel)*h*h/8
            first=max(ea,eb)+(speed+interp_speed)*h/2
            pieces.append({'source_start_s':x,'source_end_s':y,'true_fk_speed_bound_m_s':speed,'true_fk_acceleration_bound_m_s2':accel,'interpolated_speed_bound_m_s':interp_speed,'interpolated_acceleration_bound_m_s2':interp_accel,'endpoint_error_bound_m':max(ea,eb),'acceleration_error_bound_m':second,'lipschitz_error_bound_m':first,'error_bound_m':min(first,second)})
        return max(p['error_bound_m'] for p in pieces),pieces

def clip_items(profile):
    for group in ['attacks','locomotion','reactions']:
        for name,clip in profile[group].items():yield group,name,clip

def source_sample(asset,profile,clip,time):
    """Existing attack_profiles.profile_sample fields evaluated at an added time."""
    world=asset.world(clip,time);node=lambda name:world[asset.node(name)]
    offsets=profile['proxy_calibration']['bone_local_offsets']
    row={'time_seconds':time,'source_seconds':time}
    for field,name in [('head','Head'),('spine02','Spine02'),('hip','Hip'),('blade_base','Blade_Base'),('blade_tip','Blade_Tip')]:row[field]=node(name)[:3,3].tolist()
    row['head_origin']=list(row['head'])
    for field,name in [('head','Head'),('body_bottom','Hip'),('body_top','Spine02')]:row[field]=transform(node(name),np.array([offsets[field]]))[0].tolist()
    row['bone_rotation_xyzw']={}
    for name in ['Head','Spine02','Hip']:
        u,_,v=np.linalg.svd(node(name)[:3,:3]);row['bone_rotation_xyzw'][name]=matrix_quaternion(u@v)
    row['torso_lower']=list(row['hip']);row['torso_upper']=list(row['spine02']);return row

def refine_blade_grip_profiles(document,binary,profile,player_points,support_radius_m):
    asset=PreparedDocument(document,binary)
    if profile['schema_version']!=3:raise ValueError('canonical seed profile must use schema3 before Grip enrichment')
    prepared=PreparedGrip(asset,player_points,support_radius_m);candidate=copy.deepcopy(profile);candidate['schema_version']=4;reports=[]
    budget=BLADE_GRIP_PROFILE_POLICY['maximum_interval_error_m']
    for group,name,clip in clip_items(candidate):
        original_rows=clip['samples'];original_count=len(original_rows);keys=[];mids=[];intervals=[];max_depth=0
        def populate(row):
            if 'blade_grip' not in row:
                row['blade_grip']=extract_rigid(prepared.true_matrix(clip['clip'],row['source_seconds']))
                row['blade_grip']['interpolation_error_to_next_m']=0.
            return row
        for row in original_rows:populate(row)
        def refine(before,after,depth):
            nonlocal max_depth
            start=before['source_seconds'];end=after['source_seconds']
            bound,_=prepared.interval_bound(clip['clip'],start,end,before['blade_grip'],after['blade_grip'])
            if bound<=budget:
                before['blade_grip']['interpolation_error_to_next_m']=bound;return [before]
            if depth>=18:raise ValueError('adaptive pose proof exceeded 18 deterministic bisections')
            mid=float(np.float32((start+end)/2))
            if not start<mid<end:raise ValueError('float32 source-time subdivision exhausted')
            middle=populate(source_sample(asset,profile,clip['clip'],mid));max_depth=max(max_depth,depth+1)
            return refine(before,middle,depth+1)+refine(middle,after,depth+1)
        rows=[]
        for before,after in zip(original_rows[:-1],original_rows[1:]):rows.extend(refine(before,after,0))
        rows.append(original_rows[-1]);clip['samples']=rows
        if len(rows)>20000:raise ValueError('adaptive pose rows exceed bounded publication size')
        for row in rows:
            time=row['source_seconds'];g=row['blade_grip'];error=point_reconstruction_error(prepared.actual_points(clip['clip'],time),g,player_points)
            keys.append({'source_seconds':time,'full_steel_max_reconstruction_error_m':error})
        for before,after in zip(rows[:-1],rows[1:]):
            start=before['source_seconds'];end=after['source_seconds'];mid=(start+end)/2
            actual=prepared.actual_points(clip['clip'],mid);true_grip=extract_rigid(prepared.true_matrix(clip['clip'],mid));interp=interpolate_grip(before['blade_grip'],after['blade_grip'],.5)
            rigid=point_reconstruction_error(actual,true_grip,player_points);observed=point_reconstruction_error(actual,interp,player_points)
            bound,spans=prepared.interval_bound(clip['clip'],start,end,before['blade_grip'],after['blade_grip'])
            if observed>bound+1e-9 or bound>budget:raise ValueError(f'pose interval failed actual all-Steel/analytic envelope: {clip["clip"]} {start}..{end} {observed}>{bound}')
            before['blade_grip']['interpolation_error_to_next_m']=bound
            mids.append({'source_seconds':mid,'full_steel_rigid_reconstruction_error_m':rigid,'full_steel_interpolated_reconstruction_error_m':observed})
            intervals.append({'source_start_s':start,'source_end_s':end,'observed_midpoint_error_m':observed,'error_bound_m':bound,'source_key_free_spans':spans})
        source_original=profile[group][name]['samples'];by_time={row['source_seconds']:row for row in rows}
        for row in source_original:
            restored=dict(by_time[row['source_seconds']]);restored.pop('blade_grip')
            if restored!=row:raise ValueError('original sample/phase/anchor data changed')
        report={'group':group,'name':name,'clip':clip['clip'],'original_sample_count':original_count,'sample_count':len(rows),'added_sample_count':len(rows)-original_count,'maximum_bisection_depth':max_depth,'continuous_error_budget_m':budget,'steel_points_per_pose':len(player_points),'key_max_rigid_reconstruction_error_m':max(r['full_steel_max_reconstruction_error_m'] for r in keys),'midpoint_max_true_rigid_reconstruction_error_m':max(r['full_steel_rigid_reconstruction_error_m'] for r in mids),'midpoint_max_interpolated_error_m':max(r['full_steel_interpolated_reconstruction_error_m'] for r in mids),'continuous_interval_bound_max_m':max(r['error_bound_m'] for r in intervals),'continuous_intervals_above_2mm':sum(r['error_bound_m']>.002 for r in intervals),'keys':keys,'midpoints':mids,'intervals':intervals};reports.append(report)
    old=copy.deepcopy(candidate);old['schema_version']=3
    for group,name,clip in clip_items(old):
        source_times={r['source_seconds'] for r in profile[group][name]['samples']}
        clip['samples']=[r for r in clip['samples'] if r['source_seconds'] in source_times]
        for row in clip['samples']:del row['blade_grip']
    if old!=profile:raise ValueError('existing source profile data changed')
    return candidate,{'asset':'current prepared actor','source_profile_schema':3,'candidate_profile_schema':4,'shared_common_grip_geometry_error_m':prepared.mesh_error,'common_grip_support_radius_m':prepared.support_radius,'shared_shape_validated':True,'all_old_values_and_time_grids_preserved':True,'adaptive_error_budget_m':budget,'numeric_allowance_m':NUMERIC_PAD,'clips':reports,'interval_proof':'Each source-key-free span has constant local translation velocity, constant SLERP angular velocity and constant local scale. Recursively bound descendant radius r, velocity v and acceleration a by: a_parent=s*(a+2*omega*v+omega²*r); v_parent=translation_speed+s*(v+omega*r); r_parent=max_translation+s*r. Bound interpolated grip acceleration by omegaGrip²*supportRadius. Twice-differentiable curve deviation from its endpoint chord <= maxAcceleration*h²/8; combine true/predicted curves and exact endpoint affine-operator errors. Split all source keys to isolate derivative jumps, then deterministically split each span into eight for tighter certification. If outgoing interval still exceeds 1mm, recursively insert true-FK float32 source-time midpoint rows; preserve every original row. Also compute first-derivative Lipschitz bound and take minimum. Add 2um numeric allowance as explicit offline engineering margin, not a formal IEEE roundoff proof or measured SDK bound.','sdk_scope':'Actual SDK interpolation, float32 CPU/GPU evaluation and sampled-pose publication must be measured/verified by native owner. No SDK continuous-zero-error claim.'}

def common_grip_steel_points(document,binary):
    asset=PreparedDocument(document,binary);world=asset.world();grip=world[asset.node('Grip')]
    if np.max(abs(grip-np.eye(4)))>1e-12:raise ValueError('player common Grip must be identity')
    vertices=asset.steel(world)[0]
    return transform(np.linalg.inv(grip),vertices)
