"""Build one smooth paper-surface lantern module without changing formal assets."""
from pathlib import Path
import hashlib,json,math,sys,traceback
import bpy,bmesh
from mathutils import Vector
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[6]
FORMAL=ROOT/'app/src/main/assets/models/courtyard_hero.glb';FORMAL_SHA='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667';PNG=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';PNG_SHA='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392';FIBER=HERE/'textures/paper_fiber_1024x512.png';PARTS={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def p(v):return(v[0],-v[2],v[1])
def active(o):bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def part(name,verts,faces,mat,group,smooth=False):
 d=bpy.data.meshes.new(name+'_Mesh');d.from_pydata([p(v) for v in verts],[],faces);d.update();bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);uv=d.uv_layers.new(name='UVMap')
 for f in d.polygons:
  f.use_smooth=smooth
  for li in f.loop_indices:
   q=d.vertices[d.loops[li].vertex_index].co;uv.data[li].uv=(q.x/.49+.5,q.z/.64+.5)
 PARTS.setdefault(group,[]).append(o);return o
def torus(name,c,major,minor,mat,group='wood'):
 bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=4,major_radius=major,minor_radius=minor,location=p(c));o=bpy.context.object;o.name=name;o.data.materials.append(mat);PARTS.setdefault(group,[]).append(o)
def cylinder(name,a,b,r,mat,vertices=12,group='wood'):
 a,b=Vector(p(a)),Vector(p(b));d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();active(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.data.materials.append(mat);PARTS.setdefault(group,[]).append(o)
def join(name,items):
 bpy.ops.object.select_all(action='DESELECT')
 for o in items:o.select_set(True)
 bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();o=bpy.context.object;o.name=name;return o
def clone_paper(source):
 material=source.copy();material.name='EH S2 Lantern | graded paper emission | surface finish preview';fiber=bpy.data.images.load(str(FIBER),check_existing=True)
 for node in material.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and node.image.colorspace_settings.name!='Non-Color':node.image=fiber
 return material
def paper(rings,paper):
 sides=48;verts=[]
 for y,r in rings:
  for k in range(sides):
   a=2*math.pi*k/sides;verts.append((r*math.cos(a),y,r*math.sin(a)))
 faces=[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(len(rings)-1) for k in range(sides)];part('LanternSurface_Paper',verts,faces,paper,'paper',True)
def rib(name,phi,rings,wood):
 centers=[Vector((r*1.018*math.cos(phi),y,r*1.018*math.sin(phi))) for y,r in rings];radial=Vector((math.cos(phi),0,math.sin(phi)));sides=6;verts=[]
 for j,c in enumerate(centers):
  tangent=(centers[min(j+1,len(centers)-1)]-centers[max(j-1,0)]).normalized();binormal=tangent.cross(radial).normalized()
  for k in range(sides):
   a=2*math.pi*k/sides;verts.append(tuple(c+radial*math.cos(a)*.0052+binormal*math.sin(a)*.0052))
 faces=[tuple(reversed(range(sides))),tuple(range((len(centers)-1)*sides,len(centers)*sides))]+[(j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k) for j in range(len(centers)-1) for k in range(sides)];part(name,verts,faces,wood,'wood',False)
def main():
 if sha(FORMAL)!=FORMAL_SHA or sha(PNG)!=PNG_SHA or not FIBER.exists():raise ValueError('formal/PNG/fiber identity missing')
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.import_scene.gltf(filepath=str(PNG));mats={m.name:m for m in bpy.data.materials};paper_mat=clone_paper(mats['EH S2 Lantern | graded paper emission']);wood=mats['EH Timber | aged grain'];bronze=mats['EH Fittings | aged bronze'];rope=mats['Rope | twisted hemp']
 for o in list(bpy.context.scene.objects):bpy.data.objects.remove(o,do_unlink=True)
 root=bpy.data.objects.new('LanternHero_Root',None);bpy.context.collection.objects.link(root);rings=[]
 for j in range(17):
  t=j/16;y=-.32+.64*t;r=.073+.172*(math.sin(math.pi*t)**.72);rings.append((y,r))
 paper(rings,paper_mat)
 for k in range(12):rib(f'LanternSurface_Rib_{k:02}',2*math.pi*k/12,rings,wood)
 for name,y,r,w in [('BottomNeck',-.321,.079,.012),('BottomShoulder',-.282,.171,.010),('TopShoulder',.282,.171,.010),('TopNeck',.321,.079,.012)]:torus('LanternSurface_'+name,(0,y,0),r,w,wood)
 cylinder('LanternSurface_TopCap',(0,.32,0),(0,.365,0),.072,bronze,16,'bronze');cylinder('LanternSurface_BottomCap',(0,-.366,0),(0,-.33,0),.071,bronze,16,'bronze');bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=4,major_radius=.04,minor_radius=.0065,location=p((0,.694,0)));o=bpy.context.object;o.rotation_euler.x=math.pi/2;active(o);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);o.data.materials.append(bronze);PARTS.setdefault('bronze',[]).append(o)
 cylinder('LanternSurface_Cord',(0,.365,0),(0,.655,0),.0075,rope,10,'rope');cylinder('LanternSurface_TasselCord',(0,-.365,0),(0,-.548,0),.008,rope,10,'rope');bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.027,location=p((0,-.548,0)));o=bpy.context.object;o.data.materials.append(bronze);PARTS.setdefault('bronze',[]).append(o)
 for k in range(5):
  a=2*math.pi*k/5;c=.021;cylinder(f'LanternSurface_Tassel_{k}',(0,-.55,0),(c*math.cos(a),-.625,c*math.sin(a)),.0038,rope,8,'rope')
 groups=[join('LanternSurface_'+name.capitalize(),items) for name,items in PARTS.items()]
 for o in groups:o.parent=root;active(o);tri=o.modifiers.new('Export triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name);o.data.calc_tangents(uvmap='UVMap')
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'lantern_surface_editable.blend'));bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
 for o in groups:o.select_set(True)
 bpy.context.view_layer.objects.active=root;out=HERE/'lantern_surface_module.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_cameras=False,export_lights=False,export_tangents=True)
 bounds=[o.matrix_world@Vector(c) for o in groups for c in o.bound_box];box={'min':[min(q.x for q in bounds),min(q.z for q in bounds),-max(q.y for q in bounds)],'max':[max(q.x for q in bounds),max(q.z for q in bounds),-min(q.y for q in bounds)]};instances=[{'name':'front_left','translation_stage_m':[-2.15,2.70,-4.78],'rotation':[0,0,0,1],'scale':[1,1,1]},{'name':'front_right','translation_stage_m':[2.15,2.70,-4.78],'rotation':[0,0,0,1],'scale':[1,1,1]}]
 manifest={'status':'surface_finish_module_for_root_composition','formal_source_sha256':FORMAL_SHA,'blender_png_equivalent_sha256':PNG_SHA,'module':out.name,'module_sha256':sha(out),'editable':'lantern_surface_editable.blend','instances':instances,'module_bounds_stage_local_m':box,'paper_segments':48,'longitudinal_rings':17,'paper_smooth_normals':True,'ribs':12,'ribs_are_continuous':True,'source_materials':{'paper_target_material':10,'wood':0,'bronze':7,'rope':24},'one_new_image':{'path':'textures/paper_fiber_1024x512.png','bind_to':'material10 baseColorTexture and emissiveTexture; retain existing MR/normal','source_image_to_replace':41},'no_runtime_light_change':True,'no_global_emission_change':True}
 (HERE/'module_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':
 try:main()
 except BaseException:traceback.print_exc();sys.exit(1)
