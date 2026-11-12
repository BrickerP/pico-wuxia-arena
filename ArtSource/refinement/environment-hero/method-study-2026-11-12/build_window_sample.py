"""One bounded modelling-method specimen. Never writes frozen scene inputs.

Blender local (X, depth, height); glTF local (X, height, -depth).
Install origin in Stage: (-2.5, 0, -5.51), identity, metres.
The original posts/beams are read-only comparison context, not replacement parts.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import traceback

import bpy
from mathutils import Matrix,Vector

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[2]
SOURCE=BASE/'stage2/courtyard_materials_stage2.glb'
EXPECTED='8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b'
ORIGIN=Vector((-2.5,5.51,0))
OWN_LO=(-.985,0,.515);OWN_HI=(.985,.28,2.765)
CONTEXT_LO=(-1.22,-1.16,0);CONTEXT_HI=(1.22,.39,3.23)
AFTER=[];BEFORE=[];CONTEXT=[];OPEN=[];PARTS=[]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def empty(name):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);return o
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def apply(o,name):activate(o);bpy.ops.object.modifier_apply(modifier=name)
def cube(name,center,size,mat=None,group=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    if group is not None:group.append(o)
    return o
def box_bounds(name,lo,hi):
    return cube(name,tuple((a+b)/2 for a,b in zip(lo,hi)),tuple(b-a for a,b in zip(lo,hi)))
def boolean(o,cutter,operation):
    mod=o.modifiers.new('Exact construction '+operation,'BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=cutter
    apply(o,mod.name)
def bevel(o,width,segments=2,vertex_group=None):
    mod=o.modifiers.new('Physical edge radius','BEVEL');mod.width=width;mod.segments=segments
    mod.limit_method='VGROUP' if vertex_group else 'ANGLE';mod.use_clamp_overlap=True
    if vertex_group:mod.vertex_group=vertex_group
    apply(o,mod.name)
    for p in o.data.polygons:p.use_smooth=True
    mod=o.modifiers.new('Weighted broad faces','WEIGHTED_NORMAL');mod.keep_sharp=True;apply(o,mod.name)
def solid(name,color,rough=.7):
    m=bpy.data.materials.new(name);m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough
    return m
def textured(prefix,name):
    m=solid(name,(.25,.16,.08));b=m.node_tree.nodes['Principled BSDF'];nodes=m.node_tree.nodes;links=m.node_tree.links
    for suffix in ['basecolor','normal','mr']:
        image=bpy.data.images.load(str(HERE/'materials'/f'{prefix}_{suffix}.png'),check_existing=True)
        if suffix!='basecolor':image.colorspace_settings.name='Non-Color'
        image.pack();t=nodes.new('ShaderNodeTexImage');t.image=image
        if suffix=='basecolor':links.new(t.outputs['Color'],b.inputs['Base Color'])
        elif suffix=='normal':
            n=nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.55
            links.new(t.outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],b.inputs['Normal'])
        else:
            split=nodes.new('ShaderNodeSeparateColor');links.new(t.outputs['Color'],split.inputs['Color'])
            links.new(split.outputs['Green'],b.inputs['Roughness']);links.new(split.outputs['Blue'],b.inputs['Metallic'])
    return m

def metric_uv(o,axis,wood=True):
    mesh=o.data
    uv=mesh.uv_layers.get('UVMap') or mesh.uv_layers.new(name='UVMap')
    if wood:
        mesh.materials.clear();mesh.materials.append(WOOD);mesh.materials.append(END)
    seed=int(hashlib.sha256(o.name.encode()).hexdigest()[:8],16)
    shift=((seed%997)/997,((seed//997)%991)/991)
    grain=Vector(axis)
    for p in mesh.polygons:
        n=p.normal.normalized();end=wood and abs(n.dot(grain))>.95
        v=grain-n*n.dot(grain)
        if v.length<1e-6:
            guess=Vector((0,0,1)) if abs(n.z)<.9 else Vector((1,0,0));v=guess-n*n.dot(guess)
        v.normalize();u=v.cross(n).normalized()
        tile=.25 if end else .8
        p.material_index=1 if end else 0
        for li in p.loop_indices:
            q=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(q.dot(u)/tile+shift[0],q.dot(v)/tile+shift[1])

def finish(o,axis=(0,0,1),radius=.002):
    if radius:bevel(o,radius)
    metric_uv(o,axis);PARTS.append({'name':o.name,'grain_axis_blender':list(axis),'edge_radius_m':radius})
    AFTER.append(o);return o

def extrusion(name,profile,a,b,mat=None):
    # profile is (front-outward depth, vertical height), extruded across X.
    pts=[(x,-d,z) for x in (a,b) for d,z in profile];n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(pts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);o.data.materials.append(mat or WOOD)
    # Fix closed convex/concave profile orientation without touching UV data.
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    return o

def profile_frame(name,cx,cz,hw,hh,profile,depth=0,parent=None):
    # Four separately capped, mitred extrusions with an actual corner seam.
    result=[];gap=.0015
    for side in range(4):
        rings=[]
        for r,d in profile:
            corners=[(-hw-r,-hh-r),(hw+r,-hh-r),(hw+r,hh+r),(-hw-r,hh+r)]
            a=Vector(corners[side]);b=Vector(corners[(side+1)%4]);direction=(b-a).normalized()
            a+=direction*gap/2;b-=direction*gap/2
            rings.append([(cx+a.x,depth-d,cz+a.y),(cx+b.x,depth-d,cz+b.y)])
        pts=[p for ring in rings for p in ring];n=len(rings)
        faces=[(2*i,2*i+1,2*((i+1)%n)+1,2*((i+1)%n)) for i in range(n)]
        faces += [tuple(2*i for i in reversed(range(n))),tuple(2*i+1 for i in range(n))]
        mesh=bpy.data.meshes.new(f'{name}_{side}_Mesh');mesh.from_pydata(pts,[],faces);mesh.update()
        import bmesh
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
        o=bpy.data.objects.new(f'{name}_{side}',mesh);bpy.context.scene.collection.objects.link(o)
        finish(o,(1,0,0) if side%2==0 else (0,0,1),.0015)
        if parent:o.parent=parent
        result.append(o)
    return result

def paper(name,cx,depth,cz,width,height,parent):
    nu,nv=8,12;pts=[];faces=[];uvs=[]
    for back in [0,1]:
        for j in range(nv+1):
            for i in range(nu+1):
                u=i/nu;v=j/nv
                sag=.0007*math.sin(math.pi*u)*math.sin(math.pi*v)*math.sin(u*10+v*7)
                pts.append((cx+(u-.5)*width,depth+sag+back*.0015,cz+(v-.5)*height));uvs.append((u,v))
    stride=nu+1;count=(nu+1)*(nv+1)
    for j in range(nv):
        for i in range(nu):
            a=j*stride+i;q=(a,a+1,a+1+stride,a+stride)
            faces.append(q);faces.append(tuple(t+count for t in reversed(q)))
    edges=[(i,i+1) for i in range(nu)] + [(nv*stride+i+1,nv*stride+i) for i in range(nu)]
    edges += [(j*stride,(j+1)*stride) for j in range(nv)]+[((j+1)*stride+nu,j*stride+nu) for j in range(nv)]
    for a,b in edges:faces.append((a,a+count,b+count,b))
    mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(pts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);o.parent=parent;mesh.materials.append(PAPER)
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        for li in p.loop_indices:
            u,v=uvs[mesh.loops[li].vertex_index]
            uv.data[li].uv=(.00415039+u*.49169922,.50415039+v*.49169922)
    AFTER.append(o);return o

def leaf(name,cx,hinge_x,angle):
    root=empty(name+'_Hinge');root.location=(hinge_x,.11,1.7)
    profile=[(0,.010),(.012,.010),(.012,.019),(.045,.019),(.045,-.024),(.032,-.024),(.032,-.014),(0,-.014)]
    members=profile_frame(name+'_Frame',cx,1.7,.255,.62,profile,.11)
    verticals=[]
    for x in (cx-.088,cx+.088):
        o=cube(name+'_Vertical',(x,.105,1.7),(.022,.026,1.25),WOOD)
        for z in (1.39,1.7,2.01):
            cut=cube('half_lap_back',(x,.12,z),(.028,.030,.028));boolean(o,cut,'DIFFERENCE');bpy.data.objects.remove(cut,do_unlink=True)
        finish(o,(0,0,1),.0008);verticals.append(o);members.append(o)
    for z in (1.39,1.7,2.01):
        o=cube(name+'_Horizontal',(cx,.105,z),(.52,.026,.026),WOOD)
        for x in (cx-.088,cx+.088):
            cut=cube('half_lap_front',(x,.09,z),(.024,.030,.030));boolean(o,cut,'DIFFERENCE');bpy.data.objects.remove(cut,do_unlink=True)
        finish(o,(1,0,0),.0008);members.append(o)
    sheet=paper(name+'_Paper',cx,.127,1.7,.53,1.24,None);members.append(sheet)
    for o in members:
        matrix=o.matrix_world.copy();o.parent=root;o.matrix_world=matrix
    root.rotation_euler.z=math.radians(angle)
    for z in (1.18,2.22):
        # Hinge barrel and strap are fixed to the case, outside the paper plane.
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.0075,depth=.072,location=(hinge_x,.105,z))
        o=bpy.context.object;o.name=name+'_HingeBarrel';o.data.materials.append(IRON);AFTER.append(o)
    return root

def make_candidate():
    wall=box_bounds('OpeningWall',OWN_LO,OWN_HI);wall.data.materials.append(PLASTER)
    cut=cube('RealWindowOpening',(.03,.14,1.7),(1.44,1.0,1.62));boolean(wall,cut,'DIFFERENCE');bpy.data.objects.remove(cut,do_unlink=True)
    aperture=wall.vertex_groups.new(name='Aperture edges only')
    for v in wall.data.vertices:
        q=v.co+wall.location
        if abs(q.x-.03)<=.72001 and abs(q.z-1.7)<=.81001:
            aperture.add([v.index],1.,'REPLACE')
    # The infill boundary is a replacement cut through a continuous wall, not
    # an exposed prefab-panel edge. Bevel the actual aperture, not that cut.
    bevel(wall,.002,2,aperture.name)
    uv=wall.data.uv_layers.get('UVMap') or wall.data.uv_layers.new(name='UVMap')
    for p in wall.data.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=((1,2),(0,2),(0,1))[axis]
        for li in p.loop_indices:
            v=wall.data.vertices[wall.data.loops[li].vertex_index].co+wall.location
            uv.data[li].uv=((v[axes[0]]-2.5)/2.5,v[axes[1]]/5.5)
    AFTER.append(wall)
    case=[(0,-.025),(.025,-.025),(.025,.010),(.080,.010),(.080,.026),(.135,.026),
          (.135,-.018),(.107,-.018),(.107,-.235),(0,-.235),(0,-.175),(.030,-.175),(.030,-.070),(0,-.070)]
    profile_frame('RebatedCase',.03,1.7,.605,.67,case)
    sill=extrusion('SlopedSill',[( -.235,.925),(.145,.890),(.145,.815),(.104,.815),(.104,.826),(.085,.826),(.085,.815),(-.235,.815)],-.82,.88)
    finish(sill,(1,0,0),.003)
    leaf('LeftSash',-.2725,-.5725,0)
    leaf('RightSash',.3325,.6325,0)
    # A shallow, real inner lining makes the open leaf reveal wall depth.
    for center,size in [((.03,.37,2.47),(1.45,.20,.035)),((.03,.37,.93),(1.45,.20,.035)),
                        ((-.685,.37,1.7),(.035,.20,1.54)),((.745,.37,1.7),(.035,.20,1.54))]:
        o=cube('InnerRevealLining',center,size,WOOD);finish(o,(1,0,0) if size[0]>1 else (0,0,1),.002)

def crop(o,lo,hi,operation='INTERSECT'):
    # The old merged architecture contains overlapping loose solids. Boolean
    # intersection can invent a cutter-box skin on that input. Clip each source
    # triangle analytically instead; this neither classifies by centroid nor
    # removes unrelated parts of the shared wall.
    bpy.context.view_layer.update()
    mesh=o.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active
    normal_matrix=o.matrix_world.to_3x3().inverted().transposed()
    planes=[]
    for axis in range(3):planes.extend([(axis,float(lo[axis]),1),(axis,float(hi[axis]),-1)])
    def half(poly,axis,bound,sign):
        if not poly:return []
        out=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da=(a[0][axis]-bound)*sign;db=(b[0][axis]-bound)*sign
            ina,inb=da>=-1e-9,db>=-1e-9
            if ina:out.append(a)
            if ina!=inb:
                t=da/(da-db)
                out.append(tuple(x.lerp(y,t) for x,y in zip(a,b)))
        return out
    points=[];normals=[];uvs=[];faces=[];materials=[]
    def emit(poly,material):
        if len(poly)<3:return
        for j in range(1,len(poly)-1):
            tri=[poly[0],poly[j],poly[j+1]]
            if (tri[1][0]-tri[0][0]).cross(tri[2][0]-tri[0][0]).length<1e-12:continue
            start=len(points);faces.append((start,start+1,start+2));materials.append(material)
            for p,n,u in tri:points.append(tuple(p));normals.append(tuple(n.normalized()));uvs.append(tuple(u))
    for tri in mesh.loop_triangles:
        poly=[]
        for li in tri.loops:
            vi=mesh.loops[li].vertex_index
            poly.append((o.matrix_world@mesh.vertices[vi].co,
                         normal_matrix@mesh.corner_normals[li].vector,
                         uv.data[li].uv.copy() if uv else Vector((0,0))))
        material=mesh.polygons[tri.polygon_index].material_index
        for axis,bound,sign in planes:
            if operation=='DIFFERENCE':emit(half(poly,axis,bound,-sign),material)
            poly=half(poly,axis,bound,sign)
            if not poly:break
        if operation=='INTERSECT':emit(poly,material)
    new=bpy.data.meshes.new(o.name+'_ExactClip');new.from_pydata(points,[],faces);new.update()
    for m in mesh.materials:new.materials.append(m)
    target=new.uv_layers.new(name='UVMap')
    for p,material in zip(new.polygons,materials):
        p.material_index=material;p.use_smooth=True
        for li in p.loop_indices:target.data[li].uv=uvs[new.loops[li].vertex_index]
    new.normals_split_custom_set(normals)
    o.data=new;o.matrix_world=Matrix.Identity(4)
def duplicate(o,name):
    c=o.copy();c.data=o.data.copy();bpy.context.scene.collection.objects.link(c)
    c.parent=None;c.matrix_world=o.matrix_world.copy();c.name=name;return c
def baseline():
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    imported=list(bpy.context.selected_objects)
    originals={o.name:o for o in imported if o.type=='MESH'}
    needed=['EH_EntryDoorsWindows','EH_TavernWalls','EH_TavernTimber','EH_S2_TimberJointFaces']
    for name in needed:
        o=duplicate(originals[name],'Before_'+name);o.location-=ORIGIN;crop(o,CONTEXT_LO,CONTEXT_HI)
        if not o.data.polygons:bpy.data.objects.remove(o,do_unlink=True);continue
        BEFORE.append(o)
        if name=='EH_EntryDoorsWindows':continue
        c=duplicate(o,'Context_'+name)
        if name=='EH_TavernWalls':crop(c,(-.985,-1.16,.515),(.985,.39,2.765),'DIFFERENCE')
        CONTEXT.append(c)
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)

def export(name,objects):
    if not objects or not any(len(o.data.polygons) for o in objects):
        raise ValueError('Cannot export an empty comparison asset: '+name)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(HERE/name),export_format='GLB',use_selection=True,
      export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)

def static_batch(objects):
    copies=[duplicate(o,'Export_'+o.name) for o in objects]
    bpy.ops.object.select_all(action='DESELECT')
    for o in copies:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join()
    batch=bpy.context.object;batch.name='WindowInfill_Geometry'
    return batch

def studio():
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('Fixed method-review world');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.11,.13,.15,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
    for p,energy,size,color in [((-3,-3,5),650,4,(1,.94,.86)),((3,-2,3),300,3,(.82,.90,1))]:
        d=bpy.data.lights.new('Same area key/fill','AREA');d.energy=energy;d.size=size;d.color=color
        o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('Same sample eye');d.sensor_width=36;d.clip_start=.03
    camera=bpy.data.objects.new(d.name,d);scene.collection.objects.link(camera);scene.camera=camera
    return scene,camera

VIEWS={'overview':((1.0,-2.7,1.6),(0,0,1.60),25),
       '1p5m':((.55,-1.5,1.6),(.03,.08,1.65),18),
       '0p8m':((.28,-.8,1.6),(.03,.08,1.65),18)}
def render():
    scene,cam=studio();clay=solid('Same neutral clay',(.48,.48,.48),.73)
    wire=solid('Topology lines',(.012,.016,.020),.9)
    outputs={}
    for phase,visible in [('before',BEFORE),('after',CONTEXT+AFTER),('open14',OPEN)]:
        for o in BEFORE+CONTEXT+AFTER+OPEN:o.hide_render=o not in visible
        for mode in ['pbr','clay','wire']:
            if phase=='open14' and mode=='wire':continue
            records=[];wire_objects=[]
            for o in visible:
                if mode!='pbr':
                    records.append((o,list(o.data.materials),[p.material_index for p in o.data.polygons]));o.data.materials.clear();o.data.materials.append(clay)
                if mode=='wire':
                    w=duplicate(o,'Review_wire');w.data.materials.clear();w.data.materials.append(wire)
                    mod=w.modifiers.new('Actual editable topology','WIREFRAME');mod.thickness=.00065;mod.use_replace=True
                    wire_objects.append(w)
            views=VIEWS if mode!='wire' and phase!='open14' else {'1p5m':VIEWS['1p5m']}
            for name,(p,t,lens) in views.items():
                cam.location=p;cam.rotation_euler=(Vector(t)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.dof.use_dof=False
                path=HERE/'review'/f'{phase}_{mode}_{name}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);outputs[path.name]=sha(path)
            for o,mats,indices in records:
                o.data.materials.clear()
                for m in mats:o.data.materials.append(m)
                for p,index in zip(o.data.polygons,indices):p.material_index=index
            for o in wire_objects:bpy.data.objects.remove(o,do_unlink=True)
    (HERE/'review/render_evidence.json').write_text(json.dumps({'kind':'offline modelling specimen, not native PICO',
       'frozen_source_sha256':EXPECTED,'candidate_sha256':sha(HERE/'window_infill_candidate.glb'),
       'same_lighting':True,'depth_of_field':False,'views_blender_m':VIEWS,
       'distance_definition':'perpendicular distance from eye to wall front plane; eye height1.6m',
       'modes':['GLB roundtrip PBR','same clay','actual GLB triangle wire overlay'],'images':outputs},indent=2)+'\n')

def main():
    global WOOD,END,PLASTER,PAPER,IRON
    if sha(SOURCE)!=EXPECTED:raise ValueError('Frozen input changed')
    (HERE/'review').mkdir(exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    baseline()
    PLASTER=bpy.data.materials['EH Wall | rain stained lime'];PAPER=bpy.data.materials['EH S2 Windows | layered paper emission']
    WOOD=textured('wood_long','Method | CC0 directional wood .8m');END=textured('wood_end','Method | original endgrain .25m');IRON=solid('Method | dark iron',(.055,.045,.035),.55)
    make_candidate();bpy.context.view_layer.update()
    # Closed/closed is the primary A/B. A separate 14-degree pose is supplemental.
    for o in AFTER:
        if o.parent:
            frame=o.matrix_world.copy();o.parent=None;o.matrix_world=frame
    export('window_infill_construction.glb',AFTER)
    export('before_bay_with_context.glb',BEFORE)
    for o in BEFORE:o.hide_render=True;o.hide_set(True)
    for o in CONTEXT+AFTER:o.hide_render=False
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'window_method_sample.blend'))
    batch=static_batch(AFTER)
    export('window_infill_candidate.glb',[batch])
    export('after_bay_with_context.glb',CONTEXT+[batch])
    hinge=Vector((.6325,.11,1.7))
    turn=Matrix.Translation(hinge)@Matrix.Rotation(math.radians(-14),4,'Z')@Matrix.Translation(-hinge)
    for o in AFTER:
        if o.name.startswith('RightSash_') and 'HingeBarrel' not in o.name:o.matrix_world=turn@o.matrix_world
    bpy.context.view_layer.update()
    open_batch=static_batch(AFTER)
    export('window_infill_open14.glb',[open_batch]);export('open14_bay_with_context.glb',CONTEXT+[open_batch])
    info={'status':'asset_complete_review_pending','source_glb':str(SOURCE.relative_to(ROOT)),'source_sha256':EXPECTED,
      'producer_sha256':sha(Path(__file__)),'candidate':'window_infill_candidate.glb','candidate_sha256':sha(HERE/'window_infill_candidate.glb'),
      'placement_stage_m':[-2.5,0,-5.51],'rotation':'identity','scale':[1,1,1],
      'replacement_inner_bounds_stage_m':{'min':[-3.485,.515,-5.79],'max':[-1.515,2.765,-5.51]},
      'source_window_bounds_stage_m':{'min':[-3.20,.89,-5.44],'max':[-1.74,2.51,-5.31]},
      'source_nodes':['EH_EntryDoorsWindows','EH_TavernWalls'],'context_only':['EH_TavernTimber','EH_S2_TimberJointFaces'],
      'construction':['true aperture through .28m wall','separate profiled mitred case and sash members','rebate and thin .0015m paper',
                      'half-lap lattice intersections','primary closed-sash comparison; separate open14 pose only supplemental','sloping sill with actual underside drip groove'],
      'wood_uv':{'side_m_per_tile':.8,'end_m_per_tile':.25,'density_method':'orthonormal face basis aligned to projected component grain'},
      'parts':PARTS,'limitations':['not a full courtyard candidate or runtime overlay','not a historical reconstruction certification',
        'no high-poly architectural source exists; this sample rebuilds medium structure, not fake normal-map depth',
        'native response and closed-sash use remain Root review gates']}
    (HERE/'sample_manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    # Review exported resources, not only Blender's authoring shader graph.
    for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
    BEFORE.clear();AFTER.clear();CONTEXT.clear()
    bpy.ops.import_scene.gltf(filepath=str(HERE/'before_bay_with_context.glb'))
    BEFORE.extend(o for o in bpy.context.selected_objects if o.type=='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(HERE/'after_bay_with_context.glb'))
    AFTER.extend(o for o in bpy.context.selected_objects if o.type=='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(HERE/'open14_bay_with_context.glb'))
    OPEN.extend(o for o in bpy.context.selected_objects if o.type=='MESH')
    render()
    if sha(SOURCE)!=EXPECTED:raise AssertionError('Source mutated')
    print('WINDOW_METHOD_COMPLETE',info['candidate_sha256'])

if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.exit(1)
