"""Create a rig-compatible wuxia opponent study and attach the real dao.

This is an editable Blender/GLB candidate, not an accepted final character or
PICO runtime integration. Quaternius mannequin/animations and the scanned
linen are CC0; see README for sources and limitations.
"""

import math
from array import array
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


HERE = Path(__file__).resolve().parent
ART = HERE.parent
TEX = HERE / "textures"
bpy.ops.wm.open_mainfile(filepath=str(ART / "graybox" / "graybox_candidate.blend"), load_ui=False)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.render.fps = 30
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH" and
            any(m.type == "ARMATURE" and m.object == rig for m in o.modifiers))
asset = bpy.data.collections["GRAYBOX_ASSET"]
asset.name = "WARRIOR_ASSET"
studio = bpy.data.collections["REVIEW_STUDIO"]
pointer = bpy.data.objects.get("Review-only blade pointer")
if pointer:
    bpy.data.objects.remove(pointer, do_unlink=True)


def material(name, color, roughness=.8, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color,1)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color,1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


undersuit = material("Warrior | dark undercloth", (.035,.043,.046), .9)
skin = material("Warrior | exposed skin", (.30,.19,.12), .7)
hair = material("Warrior | hair and face wrap", (.020,.016,.013), .92)
belt = material("Warrior | worn brown sash", (.13,.052,.029), .88)
wrap = material("Warrior | dark bindings", (.07,.052,.040), .92)
cloth = material("Warrior | indigo linen", (.11,.15,.16), .85)

# Derive a restrained indigo colour map from the CC0 linen scan. The original
# colour, roughness and normal files remain available in textures/.
source = bpy.data.images.load(str(TEX / "rough_linen_diff_1k.jpg"), check_existing=True)
width,height = source.size
source_pixels = array("f", [0.0]) * (width*height*4)
source.pixels.foreach_get(source_pixels)
output = array("f")
for i in range(0,len(source_pixels),4):
    lum = .30*source_pixels[i] + .59*source_pixels[i+1] + .11*source_pixels[i+2]
    value = max(.10,min(.42,.14 + lum*.26))
    output.extend((value*.72,value*.90,value,1.0))
image = bpy.data.images.new("Warrior | indigo linen", width=width, height=height)
image.pixels.foreach_set(output)
image.filepath_raw = str(HERE / "warrior_linen_indigo.png")
image.file_format = "PNG"
image.save()
image.pack()
nodes = cloth.node_tree.nodes
links = cloth.node_tree.links
shader = nodes.get("Principled BSDF")
node = nodes.new("ShaderNodeTexImage")
node.image = image
links.new(node.outputs["Color"],shader.inputs["Base Color"])
rough = bpy.data.images.load(str(TEX / "rough_linen_rough_1k.jpg"), check_existing=True)
rough.colorspace_settings.name = "Non-Color"
rough.pack()
node = nodes.new("ShaderNodeTexImage")
node.image = rough
links.new(node.outputs["Color"],shader.inputs["Roughness"])
normal_image = bpy.data.images.load(str(TEX / "rough_linen_nor_gl_1k.jpg"), check_existing=True)
normal_image.colorspace_settings.name = "Non-Color"
normal_image.pack()
node = nodes.new("ShaderNodeTexImage")
node.image = normal_image
normal = nodes.new("ShaderNodeNormalMap")
normal.inputs["Strength"].default_value = .35
links.new(node.outputs["Color"],normal.inputs["Color"])
links.new(normal.outputs["Normal"],shader.inputs["Normal"])

# Paint the crossed lapel into the jacket's own colour map. It follows the
# weighted garment surface through animation rather than floating above it.
jacket_pixels=array("f",output)
for py in range(height):
    z=.78+.71*py/(height-1)
    for px in range(width):
        x=-.25+.5*px/(width-1)
        left=-.15+(1.45-z)*(.25/.37)
        right=.14-(1.45-z)*(.165/.28)
        in_left=1.08 <= z <= 1.45 and abs(x-left)<.019
        in_right=1.17 <= z <= 1.45 and abs(x-right)<.018
        if in_left or in_right:
            index=4*(py*width+px)
            weave=jacket_pixels[index+2]
            jacket_pixels[index:index+3]=array("f",(.28+weave*.20,.23+weave*.17,.17+weave*.12))
jacket_image=bpy.data.images.new("Warrior | crossed jacket",width=width,height=height)
jacket_image.pixels.foreach_set(jacket_pixels)
jacket_image.filepath_raw=str(HERE / "warrior_jacket_color.png")
jacket_image.file_format="PNG"
jacket_image.save()
jacket_image.pack()
jacket_material=material("Warrior | crossed jacket",(.12,.15,.16),.85)
jacket_nodes=jacket_material.node_tree.nodes
jacket_links=jacket_material.node_tree.links
jacket_shader=jacket_nodes.get("Principled BSDF")
node=jacket_nodes.new("ShaderNodeTexImage")
node.image=jacket_image
jacket_links.new(node.outputs["Color"],jacket_shader.inputs["Base Color"])
node=jacket_nodes.new("ShaderNodeTexImage")
node.image=rough
jacket_links.new(node.outputs["Color"],jacket_shader.inputs["Roughness"])
node=jacket_nodes.new("ShaderNodeTexImage")
node.image=normal_image
normal=jacket_nodes.new("ShaderNodeNormalMap")
normal.inputs["Strength"].default_value=.35
jacket_links.new(node.outputs["Color"],normal.inputs["Color"])
jacket_links.new(normal.outputs["Normal"],jacket_shader.inputs["Normal"])

# Keep the original mannequin mesh and weights, but replace yellow/purple
# placeholders and expose skin only on head and hands.
skin_groups = {g.index for g in body.vertex_groups if g.name in {"Head","hand_l","hand_r"}
               or g.name.startswith(("index_","middle_","ring_","pinky_","thumb_"))}
body.data.materials.clear()
body.data.materials.append(undersuit)
body.data.materials.append(skin)
for face in body.data.polygons:
    score = sum(sum(g.weight for g in body.data.vertices[i].groups if g.group in skin_groups)
                for i in face.vertices) / len(face.vertices)
    face.material_index = 1 if score > .55 else 0


def upper_weights(z):
    centres = [(.90,"pelvis"),(1.08,"spine_01"),(1.23,"spine_02"),(1.40,"spine_03")]
    if z <= centres[0][0]:return {centres[0][1]:1.0}
    if z >= centres[-1][0]:return {centres[-1][1]:1.0}
    for (a,na),(b,nb) in zip(centres,centres[1:]):
        if a <= z <= b:
            t=(z-a)/(b-a)
            return {na:1-t,nb:t}
    raise ValueError("unable to weight torso")


def skinned(name, vertices, faces, mat, weights, smooth=False):
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    asset.objects.link(obj)
    obj.parent=rig
    mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name="ClothUV")
    for polygon in mesh.polygons:
        polygon.use_smooth=smooth and len(polygon.vertices)==4
        for loop in polygon.loop_indices:
            v=mesh.vertices[mesh.loops[loop].vertex_index].co
            # A plain weave tolerates planar projection; seam quality is still
            # a visual review item, especially around the elbows.
            uv.data[loop].uv=(v.x/.3,v.z/.3)
    for index,group_weights in enumerate(weights):
        for name_,weight in group_weights.items():
            if weight <= 1e-6:continue
            group=obj.vertex_groups.get(name_) or obj.vertex_groups.new(name=name_)
            group.add([index],weight,"REPLACE")
    modifier=obj.modifiers.new("Skin to shared rig","ARMATURE")
    modifier.object=rig
    return obj


def torso_shell(name, rings, mat, segments=28):
    vertices=[]
    for z,rx,ry in rings:
        for j in range(segments):
            angle=2*math.pi*j/segments
            hem=.010*math.sin(j*2.7) if z==rings[0][0] else 0
            vertices.append((rx*math.cos(angle),ry*math.sin(angle),z+hem))
    faces=[]
    for i in range(len(rings)-1):
        for j in range(segments):
            k=(j+1)%segments
            faces.append((i*segments+j,i*segments+k,(i+1)*segments+k,(i+1)*segments+j))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple((len(rings)-1)*segments+j for j in range(segments)))
    return skinned(name,vertices,faces,mat,[upper_weights(v[2]) for v in vertices],True)


def tube(name, start, end, radius0, radius1, bone, mat, segments=16):
    a,b=Vector(start),Vector(end)
    axis=(b-a).normalized()
    ref=Vector((0,0,1)) if abs(axis.z)<.9 else Vector((0,1,0))
    u=axis.cross(ref).normalized()
    v=axis.cross(u).normalized()
    vertices=[]
    for t in (0,.48,1):
        centre=a.lerp(b,t)
        radius=radius0*(1-t)+radius1*t
        for j in range(segments):
            angle=2*math.pi*j/segments
            p=centre+radius*(u*math.cos(angle)+v*math.sin(angle))
            vertices.append(tuple(p))
    faces=[]
    for i in range(2):
        for j in range(segments):
            k=(j+1)%segments
            faces.append((i*segments+j,i*segments+k,(i+1)*segments+k,(i+1)*segments+j))
    faces.extend((tuple(reversed(range(segments))),tuple(2*segments+j for j in range(segments))))
    return skinned(name,vertices,faces,mat,[{bone:1.0} for _ in vertices],True)


def strip(name,a,b,width,y,mat,weight_fn):
    a,b=Vector(a),Vector(b)
    direction=(b-a).normalized()
    side=Vector((-direction.y,direction.x))*width/2
    points=[a-side,b-side,b+side,a+side]
    vertices=[(p.x,y,p.y) for p in points]
    return skinned(name,vertices,[(0,1,2,3)],mat,[weight_fn(v[2]) for v in vertices])


def sphere(name, centre, scale, weights, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=centre)
    obj=bpy.context.object
    obj.name=name
    obj.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for coll in list(obj.users_collection):coll.objects.unlink(obj)
    asset.objects.link(obj)
    obj.data.materials.append(mat)
    for bone,weight in weights.items():
        group=obj.vertex_groups.new(name=bone)
        group.add(list(range(len(obj.data.vertices))),weight,"REPLACE")
    mod=obj.modifiers.new("Skin to shared rig","ARMATURE")
    mod.object=rig
    obj.parent=rig
    for poly in obj.data.polygons:poly.use_smooth=True
    return obj


# Short crossed jacket and layered, uneven hem, chosen for a readable opponent
# silhouette rather than a replica of a specific historic costume.
jacket_rings=[(.78,.225,.155),(.90,.205,.15),(1.05,.17,.14),
              (1.23,.205,.16),(1.43,.23,.17),(1.49,.19,.155)]
jacket=torso_shell("Jacket | outer linen",jacket_rings,cloth)
jacket.data.materials.append(jacket_material)
for polygon in jacket.data.polygons:
    if polygon.normal.y < -.05:polygon.material_index=1
    for loop in polygon.loop_indices:
        vertex=jacket.data.vertices[jacket.data.loops[loop].vertex_index].co
        jacket.data.uv_layers.active.data[loop].uv=((vertex.x+.25)/.5,(vertex.z-.78)/.71)
torso_shell("Sash | belt",[(.945,.192,.153),(1.015,.19,.15)],belt)
strip("Sash | hanging end",(-.08,1.0),(-.115,.70),.060,-.164,belt,upper_weights)

for side in (-1,1):
    suffix="r" if side<0 else "l"
    tube("Sleeve | upper "+suffix,(side*.19,.065,1.44),(side*.47,.07,1.44),
         .102,.090,"upperarm_"+suffix,cloth)
    tube("Sleeve | forearm "+suffix,(side*.47,.07,1.44),(side*.71,.065,1.44),
         .073,.062,"lowerarm_"+suffix,cloth)
    tube("Wrap | wrist "+suffix,(side*.67,.065,1.44),(side*.735,.065,1.44),
         .065,.055,"lowerarm_"+suffix,wrap)
    tube("Trousers | upper "+suffix,(side*.089,0,.93),(side*.089,0,.53),
         .125,.110,"thigh_"+suffix,cloth)
    tube("Trousers | lower "+suffix,(side*.089,0,.53),(side*.089,.036,.115),
         .102,.075,"calf_"+suffix,cloth)
    tube("Wrap | ankle "+suffix,(side*.089,.028,.25),(side*.089,.036,.11),
         .066,.058,"calf_"+suffix,wrap)
    sphere("Sleeve | elbow "+suffix,(side*.466,.07,1.441),(.090,.090,.090),
           {"upperarm_"+suffix:.5,"lowerarm_"+suffix:.5},cloth)
    sphere("Trousers | knee "+suffix,(side*.089,.001,.532),(.105,.105,.105),
           {"thigh_"+suffix:.5,"calf_"+suffix:.5},cloth)

# Dark hair cap, topknot and a cloth face wrap avoid implying a finished face.
sphere("Hair | cap",(0,.005,1.78),(.092,.108,.070),{"Head":1.0},hair)
sphere("Hair | topknot",(0,.018,1.86),(.046,.046,.044),{"Head":1.0},hair)

# Curved cloth wraps around the lower face with an even edge. It is rigidly
# weighted to the head and does not depend on a captured image or font.
mask_vertices=[]
mask_segments=20
for z,rx,ry in ((1.575,.078,.092),(1.625,.087,.116),(1.680,.088,.119)):
    for i in range(mask_segments+1):
        angle=math.pi*i/mask_segments
        mask_vertices.append((rx*math.cos(angle),-ry*math.sin(angle)-.002,z))
mask_faces=[]
for row in range(2):
    for i in range(mask_segments):
        a=row*(mask_segments+1)+i
        b=a+mask_segments+1
        mask_faces.append((a,b,b+1,a+1))
skinned("Face | close-fitting wrap",mask_vertices,mask_faces,hair,
        [{"Head":1.0} for _ in mask_vertices],True)
for side in (-1,1):
    strip("Face | eye slit "+str(side),(side*.018,1.715),(side*.052,1.711),
          .008,-.112,hair,lambda _: {"Head":1.0})


def join_meshes(objects, name):
    """Merge rigidly related pieces while keeping materials and skin groups."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    result=bpy.context.object
    result.name=name
    # Blender join can leave duplicate slots that reference the same material.
    old=list(result.data.materials)
    unique=[]
    lookup={}
    for index,mat in enumerate(old):
        if mat not in unique:unique.append(mat)
        lookup[index]=unique.index(mat)
    face_indices=[lookup[face.material_index] for face in result.data.polygons]
    result.data.materials.clear()
    for mat in unique:result.data.materials.append(mat)
    for face,index in zip(result.data.polygons,face_indices):face.material_index=index
    return result


garments=join_meshes([o for o in asset.objects if o.type=="MESH" and o!=body],
                     "Warrior garments")

# Import the actual previously authored dao, not the greybox pointer.
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ART / "dao" / "dao_study.glb"))
new_objects=[o for o in bpy.data.objects if o not in before]
for obj in new_objects:
    for coll in list(obj.users_collection):coll.objects.unlink(obj)
    asset.objects.link(obj)
dao=bpy.data.objects["DAO_Root"]
grip=bpy.data.objects["Grip"]
join_meshes([o for o in new_objects if o.type=="MESH" and o.name!="Blade"],
            "Dao fittings and wear")
guard=bpy.data.actions["Graybox_Guard_Hold"]
rig.animation_data.action=guard
rig.animation_data.action_slot=guard.slots[0]
scene.frame_set(1)
bpy.context.view_layer.update()
dao.parent=rig
dao.parent_type="BONE"
dao.parent_bone="hand_r"
dao.location=(0,0,0)
dao.rotation_mode="QUATERNION"
dao.rotation_quaternion=(1,0,0,0)
bpy.context.view_layer.update()
world_direction=Vector((.65,-.06,.55)).normalized()
local_direction=dao.matrix_world.to_quaternion().inverted()@world_direction
rotation=Vector((0,0,1)).rotation_difference(local_direction)
dao.rotation_quaternion=rotation
dao.location=-(rotation@Vector((0,0,-.114)))
bpy.context.view_layer.update()

scene.camera.data.ortho_scale=2.7
scene.render.resolution_x=900
scene.render.resolution_y=1050
scene.render.resolution_percentage=100
scene.cycles.samples=32
scene.cycles.use_denoising=True
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "warrior_candidate.blend"))
bpy.ops.object.select_all(action="DESELECT")
for obj in asset.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(HERE / "warrior_candidate.glb"),export_format="GLB",
                          use_selection=True,export_yup=True,export_animations=True,
                          export_animation_mode="BROADCAST",export_extras=True)
for name,frame,scale,filename in (
    ("Graybox_Guard_Hold",1,2.7,"warrior_review_guard.png"),
    ("Sword_A_InPlace",7,3.1,"warrior_review_attack_a.png"),
    ("Sword_B_InPlace",8,3.4,"warrior_review_attack_b.png"),
    ("Overhead_Chop_Candidate",0,3.2,"warrior_review_overhead.png"),
):
    action=bpy.data.actions[name]
    rig.animation_data.action=action
    rig.animation_data.action_slot=action.slots[0]
    scene.frame_set(frame)
    scene.camera.data.ortho_scale=scale
    scene.render.filepath=str(HERE / filename)
    bpy.ops.render.render(write_still=True)
