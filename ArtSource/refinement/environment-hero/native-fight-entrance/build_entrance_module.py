"""Bespoke central entrance, using only materials already present in 64da.
No old door is loaded into this module; the full-scene builder removes it.
"""
from pathlib import Path
import hashlib
import json
import math
import sys
import traceback

import bpy
from mathutils import Matrix,Vector

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
SOURCE=BASE/'facade-polish/courtyard_facade_polish.glb'
sys.path.insert(0,str(BASE/'method-study-2026-11-12'));import build_window_sample as w
PARTS=[]
def p(v):return (v[0],-v[2],v[1])
def box(name,c,size,grain=(0,0,1),radius=.003,material=None):
    o=w.cube(name,p(c),(size[0],size[2],size[1]),material or WOOD)
    if material is None:w.finish(o,grain,radius)
    else:w.bevel(o,radius,2)
    PARTS.append(o);return o
def mesh(name,vertices,faces,mat,grain=None,bevel=0):
    data=bpy.data.meshes.new(name+'_Mesh');data.from_pydata([p(v) for v in vertices],[],faces);data.update()
    import bmesh
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    o=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(o);data.materials.append(mat)
    if bevel:w.bevel(o,bevel,2)
    if grain:w.metric_uv(o,grain)
    else:
        uv=data.uv_layers.get('UVMap') or data.uv_layers.new(name='UVMap')
        for poly in data.polygons:
            axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=((1,2),(0,2),(0,1))[axis]
            for li in poly.loop_indices:
                q=data.vertices[data.loops[li].vertex_index].co
                uv.data[li].uv=(q[axes[0]]/.65,q[axes[1]]/.65)
    PARTS.append(o);return o
def profile(name,center,shape,length,vertical=False):
    # shape=(cross-width offset, front-outward depth). Real closed stepped section.
    vertices=[]
    for t in [-length/2,length/2]:
        for a,d in shape:
            vertices.append((center[0]+(a if vertical else t),center[1]+(t if vertical else a),center[2]+d))
    n=len(shape);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vertices,faces,WOOD,(0,0,1) if vertical else (1,0,0),.002)
def cylinder(name,c,r,length,mat,axis='Y',segments=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=r,depth=length,location=p(c))
    o=bpy.context.object;o.name=name
    if axis=='Z':o.rotation_euler.x=math.pi/2
    w.activate(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);w.bevel(o,.001,1);PARTS.append(o);return o
def leaf(side):
    cx=side*.63
    # Real stiles and rails; there is no full slab behind the upper paper.
    for dx in [-.5835,.5835]:
        if side>0 and dx<0:
            o=w.cube(f'Leaf{side}_RebatedMeetingStile',p((cx+dx,1.4075,-5.4775)),(.075,.075,2.675),WOOD)
            cutter=w.cube('MeetingStopRebate',p((.0225,1.395,-5.442)),(.029,.008,2.655))
            w.boolean(o,cutter,'DIFFERENCE');bpy.data.objects.remove(cutter,do_unlink=True)
            w.finish(o,(0,0,1),.002);PARTS.append(o)
        else:box(f'Leaf{side}_Stile',(cx+dx,1.4075,-5.4775),(.075,2.675,.075),radius=.004)
    for y,h in [(.145,.15),(1.22,.13),(2.69,.11)]:box(f'Leaf{side}_Rail',(cx,y,-5.4775),(1.092,h,.075),(1,0,0),.003)
    for i in range(5):
        x=cx-.546+(i+.5)*(.2184)
        box(f'Leaf{side}_LowerBoard{i}',(x,.6875,-5.487),(.2172,.935,.040),radius=.002)
    # Pressure strips seat the thin sheet behind the lattice.
    for dx in [-.537,.537]:box(f'Leaf{side}_PaperStop',(cx+dx,1.96,-5.486),(.018,1.354,.018),radius=.001)
    for y in [1.294,2.626]:box(f'Leaf{side}_PaperStop',(cx,y,-5.486),(1.092,.018,.018),(1,0,0),.001)
    for dx in [-.18,.18]:
        o=w.cube(f'Leaf{side}_LatticeVertical',p((cx+dx,1.96,-5.454)),(.022,.028,1.354),WOOD)
        for y in [1.735,2.185]:
            cutter=w.cube('LapRear',p((cx+dx,y,-5.470)),(.028,.032,.030));w.boolean(o,cutter,'DIFFERENCE');bpy.data.objects.remove(cutter,do_unlink=True)
        w.finish(o,(0,0,1),.001);PARTS.append(o)
    for y in [1.735,2.185]:
        o=w.cube(f'Leaf{side}_LatticeHorizontal',p((cx,y,-5.454)),(1.096,.028,.028),WOOD)
        for dx in [-.18,.18]:
            cutter=w.cube('LapFront',p((cx+dx,y,-5.438)),(.024,.032,.032));w.boolean(o,cutter,'DIFFERENCE');bpy.data.objects.remove(cutter,do_unlink=True)
        w.finish(o,(1,0,0),.001);PARTS.append(o)
    paper=w.paper(f'Leaf{side}_ThinPaper',cx,5.478,1.96,1.07,1.31,None);PARTS.append(paper)
    if side<0:
        # One lapped meeting stile, seated into the opposite rebate; no fake gap decal.
        profile('MeetingAstragal',(0,1.395,-5.44),[(-.036,-.002),(-.009,-.002),(-.009,-.006),(.036,-.006),(.036,.018),(-.036,.018)],2.65,True)
    x=side*.16
    box(f'Handle{side}_Escutcheon',(x,1.22,-5.435),(.075,.12,.012),material=BRONZE,radius=.004)
    cylinder(f'Handle{side}_Pin',(x,1.22,-5.415),.012,.035,BRONZE,'Z',12)
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,location=p((x,1.155,-5.401)),major_radius=.050,minor_radius=.007)
    o=bpy.context.object;o.name=f'Handle{side}_Ring';o.rotation_euler.x=math.pi/2
    w.activate(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(BRONZE);PARTS.append(o)
def foundation(side):
    cx=side*1.4;cz=-5.24;outline=[(-1,-.72),(-.72,-1),(.72,-1),(1,-.72),(1,.72),(.72,1),(-.72,1),(-1,.72)]
    rings=[]
    for y,sx,sz in [(0,.20,.215),(.055,.20,.215),(.067,.18,.195),(.225,.153,.168),(.24,.185,.20),(.32,.185,.20)]:
        rings.append([(cx+x*sx,y,cz+z*sz) for x,z in outline])
    vertices=[v for ring in rings for v in ring];faces=[tuple(reversed(range(8))),tuple(range(40,48))]
    for k in range(5):
        for i in range(8):j=(i+1)%8;faces.append((k*8+i,k*8+j,(k+1)*8+j,(k+1)*8+i))
    o=mesh(f'Pier{side}_TaperedSocketBase',vertices,faces,STONE)
    cutter=w.cube('PostSocket',p((cx,.325,cz)),(.242,.302,.080));w.boolean(o,cutter,'DIFFERENCE');bpy.data.objects.remove(cutter,do_unlink=True)
    w.bevel(o,.003,2)
    # Refresh metric granite UV after the genuine socket cut.
    uv=o.data.uv_layers.active
    for poly in o.data.polygons:
        axis=max(range(3),key=lambda i:abs(poly.normal[i]));axes=((1,2),(0,2),(0,1))[axis]
        for li in poly.loop_indices:
            q=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(q[axes[0]]/.65,q[axes[1]]/.65)
def bracket(side):
    x=side*1.4
    # A solid shouldered support meets the retained porch beam at Y=3.02.
    points=[(x-.105,2.87,-5.08),(x+.105,2.87,-5.08),(x+.105,2.87,-4.79),(x-.105,2.87,-4.79),
            (x-.105,3.02,-5.08),(x+.105,3.02,-5.08),(x+.105,3.02,-4.79),(x-.105,3.02,-4.79)]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh(f'Bracket{side}_BearingHead',points,faces,WOOD,(0,1,0),.004)
    a=Vector(p((x,2.50,-5.085)));b=Vector(p((x,2.91,-4.88)));length=(b-a).length
    o=w.cube(f'Bracket{side}_SolidBrace',(a+b)/2,(.115,.125,length),WOOD)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();w.activate(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    w.finish(o,tuple((b-a).normalized()),.004);PARTS.append(o)
    box(f'Bracket{side}_PostSeat',(x,2.51,-5.073),(.17,.15,.046),radius=.003)
def main():
    global WOOD,END,PAPER,STONE,BRONZE
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605'
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    WOOD=bpy.data.materials['Method | CC0 directional wood .8m'];END=bpy.data.materials['Method | original endgrain .25m']
    PAPER=bpy.data.materials['EH S2 Windows | layered paper emission'];STONE=bpy.data.materials['EH Stone | low damp granite'];BRONZE=bpy.data.materials['EH Fittings | aged bronze']
    w.WOOD=WOOD;w.END=END;w.PAPER=PAPER;w.AFTER=[];w.PARTS=[]
    leaf(-1);leaf(1)
    shape=[(-.060,-.006),(-.060,.012),(.045,.012),(.045,-.19),(-.045,-.19),(-.045,-.045),(-.025,-.045),(-.025,-.006)]
    for side in [-1,1]:
        profile(f'Jamb{side}_RebatedCase',(side*1.3075,1.4325,-5.435),[(a*side,d) for a,d in shape],2.625,True)
        foundation(side);bracket(side)
        box(f'Jamb{side}_BedStone',(side*1.3075,.06,-5.56),(.11,.12,.21),material=STONE,radius=.006)
    profile('Head_RebatedLintel',(0,2.79,-5.435),shape,2.705)
    # Keep the approach at existing Y=0; only a narrow threshold is raised.
    o=w.extrusion('Threshold_DrainedTop',[(-.12,.065),(.12,.047),(.12,0),(-.12,0)],-1.25,1.25,WOOD)
    # extrusion uses absolute Blender Y via depth; place at the actual doorway.
    o.location.y=5.48;w.finish(o,(1,0,0),.003);PARTS.append(o)
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.type=='MESH':o.hide_render=o not in PARTS
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'entrance_editable.blend'))
    copies=[w.duplicate(o,'Batch_'+o.name) for o in PARTS];bpy.ops.object.select_all(action='DESELECT')
    for o in copies:o.select_set(True)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();batch=bpy.context.object;batch.name='NativeEntrance_Geometry'
    bpy.ops.object.select_all(action='DESELECT');batch.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(HERE/'entrance_module.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
    (HERE/'module_parts.json').write_text(json.dumps({'parts':[o.name for o in PARTS],'count':len(PARTS),'source_materials_only':True},indent=2)+'\n')
    print('ENTRANCE_MODULE_COMPLETE',hashlib.sha256((HERE/'entrance_module.glb').read_bytes()).hexdigest())
if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.exit(1)
