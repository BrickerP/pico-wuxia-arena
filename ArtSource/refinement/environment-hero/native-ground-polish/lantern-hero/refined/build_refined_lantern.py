"""A rounded, continuous-curvature lantern module for Root composition only."""
from pathlib import Path
import hashlib,json,math,sys,traceback
import bpy,bmesh
from mathutils import Vector

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
SOURCE=ROOT/'app/src/main/assets/models/courtyard_hero.glb';EXPECTED='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667'
PNG_EQUIVALENT=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';PNG_EXPECTED='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392';PARTS={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def p(v):return (v[0],-v[2],v[1])
def activate(o):bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def part(name,verts,faces,mat,group):
    data=bpy.data.meshes.new(name+'_Mesh');data.from_pydata([p(v) for v in verts],[],faces);data.update();bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);data.materials.append(mat);uv=data.uv_layers.new(name='UVMap')
    for face in data.polygons:
        for loop in face.loop_indices:
            q=data.vertices[data.loops[loop].vertex_index].co;uv.data[loop].uv=(q.x/.65,q.z/.65)
    PARTS.setdefault(group,[]).append(o);return o
def torus(name,c,major,minor,mat,vertical=False,group='wood'):
    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=4,major_radius=major,minor_radius=minor,location=p(c));o=bpy.context.object;o.name=name
    if vertical:o.rotation_euler.x=math.pi/2
    activate(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.data.materials.append(mat);PARTS.setdefault(group,[]).append(o)
def cylinder(name,a,b,r,mat,vertices=12,group='wood'):
    a,b=Vector(p(a)),Vector(p(b));d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();activate(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.data.materials.append(mat);PARTS.setdefault(group,[]).append(o)
def paper_shell(paper,rings,sides=48):
    verts=[]
    for y,r in rings:
        for k in range(sides):
            a=2*math.pi*k/sides;verts.append((r*math.cos(a),y,r*math.sin(a)))
    faces=[]
    for j in range(len(rings)-1):
        for k in range(sides):faces.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    return part('LanternRefined_PaperShell',verts,faces,paper,'paper')
def rib(name,phi,rings,wood):
    # A single swept octagonal tube follows the complete paper profile, so ribs meet collars continuously.
    centers=[]
    for y,r in rings:centers.append(Vector((r*1.018*math.cos(phi),y,r*1.018*math.sin(phi))))
    radial=Vector((math.cos(phi),0,math.sin(phi)));verts=[];sides=6
    for j,c in enumerate(centers):
        tangent=(centers[min(j+1,len(centers)-1)]-centers[max(j-1,0)]).normalized();binormal=tangent.cross(radial).normalized()
        for k in range(sides):
            a=2*math.pi*k/sides;verts.append(tuple(c+radial*math.cos(a)*.0055+binormal*math.sin(a)*.0055))
    faces=[tuple(reversed(range(sides))),tuple(range((len(centers)-1)*sides,len(centers)*sides))]
    for j in range(len(centers)-1):
        for k in range(sides):faces.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    return part(name,verts,faces,wood,'wood')
def join(name,items):
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:o.select_set(True)
    bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o
def main():
    if sha(SOURCE)!=EXPECTED or sha(PNG_EQUIVALENT)!=PNG_EXPECTED:raise ValueError('formal or PNG-equivalent source SHA changed')
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.import_scene.gltf(filepath=str(PNG_EQUIVALENT));mats={m.name:m for m in bpy.data.materials}
    paper=mats['EH S2 Lantern | graded paper emission'];wood=mats['EH Timber | aged grain'];bronze=mats['EH Fittings | aged bronze'];rope=mats['Rope | twisted hemp']
    for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
    root=bpy.data.objects.new('LanternHero_Root',None);bpy.context.collection.objects.link(root)
    rings=[(-.32,.073),(-.286,.165),(-.23,.215),(-.12,.241),(0,.245),(.12,.241),(.23,.215),(.286,.165),(.32,.073)]
    paper_shell(paper,rings)
    for k in range(12):rib(f'LanternRefined_Rib_{k:02}',2*math.pi*k/12,rings,wood)
    # Paired collar rings contact the rib endpoints and hide the paper edge without a flat decal.
    for name,y,r,w in [('BottomNeck',-.321,.079,.012),('BottomShoulder',-.282,.171,.010),('TopShoulder',.282,.171,.010),('TopNeck',.321,.079,.012)]:torus('LanternRefined_'+name,(0,y,0),r,w,wood)
    cylinder('LanternRefined_TopCap',(0,.320,0),(0,.365,0),.072,bronze,16,'bronze');cylinder('LanternRefined_BottomCap',(0,-.366,0),(0,-.33,0),.071,bronze,16,'bronze')
    torus('LanternRefined_HangingEye',(0,.694,0),.040,.0065,bronze,True,'bronze');cylinder('LanternRefined_SuspensionCord',(0,.365,0),(0,.655,0),.0075,rope,10,'rope')
    cylinder('LanternRefined_TasselCord',(0,-.365,0),(0,-.548,0),.008,rope,10,'rope')
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.027,location=p((0,-.548,0)));o=bpy.context.object;o.name='LanternRefined_TasselKnot';o.data.materials.append(bronze);PARTS.setdefault('bronze',[]).append(o)
    for k in range(5):
        a=2*math.pi*k/5;c=.021;cylinder(f'LanternRefined_Tassel_{k}',(0,-.55,0),(c*math.cos(a),-.625,c*math.sin(a)),.0038,rope,8,'rope')
    groups=[join('LanternRefined_'+name.capitalize(),items) for name,items in PARTS.items()]
    for o in groups:
        o.parent=root;activate(o);tri=o.modifiers.new('Export triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name);o.data.calc_tangents(uvmap='UVMap')
    bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'lantern_refined_editable.blend'));bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
    for o in groups:o.select_set(True)
    bpy.context.view_layer.objects.active=root;out=HERE/'lantern_refined_module.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_tangents=True)
    bounds=[o.matrix_world@Vector(c) for o in groups for c in o.bound_box];box={'min':[min(q.x for q in bounds),min(q.z for q in bounds),-max(q.y for q in bounds)],'max':[max(q.x for q in bounds),max(q.z for q in bounds),-min(q.y for q in bounds)]}
    instances=[{'name':'front_left','translation_stage_m':[-2.15,2.70,-4.78],'rotation':[0,0,0,1],'scale':[1,1,1]},{'name':'front_right','translation_stage_m':[2.15,2.70,-4.78],'rotation':[0,0,0,1],'scale':[1,1,1]}]
    manifest={'status':'reusable_refined_module_for_root_composition','formal_source_sha256':EXPECTED,'blender_png_equivalent_sha256':PNG_EXPECTED,'module':out.name,'module_sha256':sha(out),'editable':'lantern_refined_editable.blend','coordinates':'module local metres, +Y up, -Z forward; root identity','module_bounds_stage_local_m':box,'instances':instances,'source_materials':{'paper':10,'wood':0,'bronze':7,'rope':24},'paper_segments':48,'ribs':12,'ribs_are_continuous':True,'source_light_anchors_preserved':['EH_Light_Lantern_01','EH_Light_Lantern_02'],'no_runtime_light_change':True,'preview_note':'Blender importer cannot load formal KHR_texture_basisu; only the verified PNG-equivalent scene supplied existing material bindings for authoring, while formal bd5d remains unchanged.','replaces':'same two front-lantern component envelopes as frozen old module 178d1bfc'}
    (HERE/'module_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.exit(1)
