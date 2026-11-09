"""Produce the arena's side-court props with the existing tavern PBR materials.

Model coordinates passed to helpers are Stage metres, +Y up, -Z forward.
The Blender source uses (Stage X, -Stage Z, Stage Y), and GLB export restores
Stage coordinates. The courtyard's centre remains open for close combat.
"""

import json
import math
import random
import shutil
from array import array
from pathlib import Path

import bpy
from mathutils import Vector


OUT = Path(__file__).resolve().parent
RUNTIME = OUT.parents[1] / "app/src/main/assets/models"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
asset = bpy.data.collections.new("COURTYARD_DETAIL_ASSET")
scene.collection.children.link(asset)


def blender_point(point):
    return (point[0], -point[2], point[1])


def root(name, position=(0, 0, 0), parent=None, yaw=0.0):
    obj = bpy.data.objects.new(name, None)
    asset.objects.link(obj)
    obj.parent = parent
    obj.location = blender_point(position)
    obj.rotation_euler.z = yaw
    obj.empty_display_size = 0.08
    return obj


root_asset = root("CourtyardDetails_Root")
root_asset["units"] = "metres"
root_asset["stage_origin"] = "load at 0,0,0; +Y up; -Z forward"
root_asset["combat_clearance"] = "X -1.35..1.35; Z -3.0..0.8"

with bpy.data.libraries.load(str(OUT / "tavern_slice.blend"), link=False) as (source, loaded):
    loaded.materials = [name for name in source.materials if name.startswith((
        "Wood |", "Timber |", "Stone |", "Iron |", "Brass |", "Lantern |", "Paving |"))]
    loaded.objects = ["Lantern"]

materials = {material.name: material for material in loaded.materials}
wood = materials["Wood | aged scanned grain"]
dark_wood = materials["Timber | darkened edges"]
stone = materials["Stone | grey scanned granite"]
iron = materials["Iron | aged hardware"]
brass = materials["Brass | dulled fittings"]
grout = materials["Paving | dark joints"]
source_lantern = next(obj for obj in loaded.objects if obj is not None)


def solid(name, color, roughness, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*color, 1)
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


def textured_surface(name, base, roughness, seed, cloth=False):
    """Bake colour variation and physical roughness into portable image maps."""
    material = solid(name, base, roughness)
    shader = material.node_tree.nodes.get("Principled BSDF")
    rng = random.Random(seed)
    colors, rough = array("f"), array("f")
    size = 512
    for row in range(size):
        v = row / size
        for column in range(size):
            u = column / size
            noise = rng.uniform(-0.018, 0.018)
            if cloth:
                detail = 0.035 * math.sin(column * math.pi / 2) * math.sin(row * math.pi / 2)
                variation = 0.88 + detail + noise + 0.07 * math.sin(u * 28 + v * 13)
                surface = roughness + noise
            else:
                drip = math.sin(u * 93 + math.sin(u * 21) * 2.7)
                variation = 0.88 + 0.09 * math.sin(v * 12) + 0.065 * drip * (0.4 + v) + noise
                surface = roughness + 0.065 * math.sin(u * 33 + v * 4) + noise
            colors.extend((*[max(0.001, min(1.0, c * variation)) for c in base], 1))
            value = max(0.08, min(0.95, surface))
            rough.extend((value, value, value, 1))
    for suffix, pixels, target in (("color", colors, "Base Color"), ("rough", rough, "Roughness")):
        image = bpy.data.images.new(f"{name}_{suffix}", width=size, height=size)
        if suffix == "rough":
            image.colorspace_settings.name = "Non-Color"
        image.pixels.foreach_set(pixels)
        image.filepath_raw = str(OUT / f"courtyard_{name.split('|')[0].strip().lower()}_{suffix}.png")
        image.file_format = "PNG"
        image.save()
        image.pack()
        node = material.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = image
        material.node_tree.links.new(node.outputs["Color"], shader.inputs[target])
    return material


brown_glaze = textured_surface("Pottery | iron brown glaze", (0.145, 0.055, 0.024), 0.27, 83)
celadon = textured_surface("Celadon | mineral green glaze", (0.16, 0.245, 0.18), 0.22, 92)
seal_cloth = textured_surface("Cloth | faded wine seal", (0.28, 0.022, 0.011), 0.88, 123, cloth=True)
unglazed = solid("Clay | exposed foot and rim", (0.19, 0.125, 0.075), 0.9)
rope = solid("Rope | twisted hemp", (0.19, 0.13, 0.065), 0.96)
water = solid("Water | dark courtyard basin", (0.018, 0.042, 0.033), 0.13, 0.18)
leaf_mat = solid("Lotus | muted leaf", (0.045, 0.11, 0.041), 0.64)
vein_mat = solid("Lotus | leaf veins", (0.1, 0.16, 0.061), 0.8)


def mesh_object(name, vertices, faces, material, parent, uvs=None, smooth=False):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata([blender_point(vertex) for vertex in vertices], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    asset.objects.link(obj)
    obj.parent = parent
    mesh.materials.append(material)
    layer = mesh.uv_layers.new(name="SurfaceUV")
    for face_index, polygon in enumerate(mesh.polygons):
        polygon.use_smooth = smooth
        if uvs is not None:
            face_uvs = uvs[face_index]
        else:
            a, b, c = (Vector(vertices[index]) for index in faces[face_index][:3])
            normal = (b - a).cross(c - a)
            axis = max(range(3), key=lambda value: abs(normal[value]))
            axes = ((1, 2), (0, 2), (0, 1))[axis]
            face_uvs = [(vertices[index][axes[0]] / 0.6, vertices[index][axes[1]] / 0.6)
                        for index in faces[face_index]]
        for loop_index, uv in zip(polygon.loop_indices, face_uvs):
            layer.data[loop_index].uv = uv
    return obj


def box(name, center, size, material, parent, bevel=0.008):
    x, y, z = center
    dx, dy, dz = (length / 2 for length in size)
    vertices = [(x-dx,y-dy,z-dz), (x+dx,y-dy,z-dz), (x+dx,y+dy,z-dz), (x-dx,y+dy,z-dz),
                (x-dx,y-dy,z+dz), (x+dx,y-dy,z+dz), (x+dx,y+dy,z+dz), (x-dx,y+dy,z+dz)]
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]
    obj = mesh_object(name, vertices, faces, material, parent)
    if bevel:
        modifier = obj.modifiers.new("Worn edge arris", "BEVEL")
        modifier.width = min(bevel, min(size) * 0.22)
        modifier.segments = 2
        modifier.affect = "EDGES"
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.select_set(False)
    return obj


def lathe(name, profile, material, parent, center=(0,0,0), segments=40, irregular=0.0):
    vertices = []
    for height, radius in profile:
        for index in range(segments):
            angle = math.tau * index / segments
            wobble = 1 + irregular * (math.sin(angle * 3 + height * 7) + 0.4 * math.sin(angle * 7))
            r = radius * wobble
            vertices.append((center[0]+r*math.cos(angle), center[1]+height,
                             center[2]+r*math.sin(angle)))
    faces, uvs = [], []
    for ring in range(len(profile)-1):
        for index in range(segments):
            next_index = (index + 1) % segments
            faces.append((ring*segments+index, (ring+1)*segments+index,
                          (ring+1)*segments+next_index, ring*segments+next_index))
            v0, v1 = profile[ring][0] / profile[-1][0], profile[ring+1][0] / profile[-1][0]
            u0, u1 = index/segments, (index+1)/segments
            uvs.append(((u0,v0), (u0,v1), (u1,v1), (u1,v0)))
    return mesh_object(name, vertices, faces, material, parent, uvs, smooth=True)


def tube(name, points, radius, material, parent, sides=6):
    vertices = []
    for index, point in enumerate(points):
        direction = Vector(points[min(index+1,len(points)-1)]) - Vector(points[max(0,index-1)])
        tangent = direction.normalized()
        side = tangent.cross(Vector((0,1,0)))
        if side.length < 0.01:
            side = tangent.cross(Vector((0,0,1)))
        side.normalize()
        up = tangent.cross(side).normalized()
        for step in range(sides):
            angle = math.tau * step / sides
            offset = side * (math.cos(angle)*radius) + up * (math.sin(angle)*radius)
            vertices.append(tuple(Vector(point)+offset))
    faces = []
    for index in range(len(points)-1):
        for step in range(sides):
            following = (step+1)%sides
            faces.append((index*sides+step, index*sides+following,
                          (index+1)*sides+following, (index+1)*sides+step))
    return mesh_object(name, vertices, faces, material, parent, smooth=True)


def ring(name, center, radius, thickness, material, parent, turns=1, rise=0.0):
    points = []
    for index in range(48*turns+1):
        angle = math.tau * index / 48
        points.append((center[0]+radius*math.cos(angle), center[1]+rise*index/48,
                       center[2]+radius*math.sin(angle)))
    return tube(name, points, thickness, material, parent)


def wine_jar(name, parent, position, scale=1.0, covered=True):
    module = root(name, position, parent, yaw=0.18)
    profile = [(0,0.001),(.012,.16),(.025,.20),(.05,.215),(.10,.255),(.18,.29),
               (.27,.305),(.36,.30),(.45,.27),(.51,.225),(.55,.16),(.575,.135),
               (.60,.135),(.615,.153),(.635,.153),(.642,.135),(.625,.118),(.585,.118)]
    profile = [(height*scale,radius*scale) for height,radius in profile]
    lathe(name+"_ThrownBody", profile, brown_glaze, module, irregular=0.009)
    lathe(name+"_UnglazedFoot", [(0,.17*scale),(.018*scale,.205*scale),(.038*scale,.21*scale)],
          unglazed, module, segments=40)
    ring(name+"_Rim",(0,.63*scale,0),.142*scale,.009*scale,unglazed,module)
    if covered:
        vertices = [(0,.653*scale,0)]
        segments = 40
        for index in range(segments):
            angle = math.tau*index/segments
            r = (.177+.012*math.sin(angle*7))*scale
            vertices.append((r*math.cos(angle),(.613+.016*math.sin(angle*5))*scale,r*math.sin(angle)))
        faces = [(0,(index+1)%segments+1,index+1) for index in range(segments)]
        mesh_object(name+"_PleatedWineSeal",vertices,faces,seal_cloth,module)
        ring(name+"_NeckLashing",(0,.592*scale,0),.144*scale,.005*scale,rope,module,turns=3,rise=.008*scale)
        tie = [(0,.60*scale,.15*scale),(.025*scale,.57*scale,.17*scale),
               (.005*scale,.53*scale,.20*scale),(-.025*scale,.56*scale,.17*scale),
               (0,.60*scale,.15*scale),(.02*scale,.49*scale,.24*scale),(.05*scale,.43*scale,.25*scale)]
        tube(name+"_HandTiedCord",tie,.006*scale,rope,module)
    else:
        lathe(name+"_DarkInnerBowl",[(.13*scale,0.001),(.14*scale,.13*scale),
              (.42*scale,.20*scale),(.56*scale,.12*scale)],grout,module)
    return module


def cup(name, parent, center, size=1.0):
    profile = [(0,.001),(.004,.035),(.014,.044),(.046,.055),(.07,.063),
               (.074,.060),(.067,.056),(.02,.039),(.016,.001)]
    return lathe(name,[(h*size,r*size) for h,r in profile],celadon,parent,center,segments=32)


table = root("TeaTable_Root",(-2.04,.028,-3.15),root_asset,yaw=-0.08)
for index in range(3):
    box(f"Table_TopPlank_{index}",(0,.705,(index-1)*.19),(1.12,.045,.184),wood,table)
for x in (-.46,.46):
    for z in (-.20,.20):
        box("Table_TaperedLeg",(x,.34,z),(.07,.66,.07),wood,table,bevel=.006)
        box("Table_LegFoot",(x,.067,z),(.085,.055,.085),dark_wood,table,bevel=.004)
    box("Table_SideApron",(x,.62,0),(.055,.12,.45),wood,table)
    box("Table_LowStretcher",(x,.24,0),(.045,.045,.43),dark_wood,table)
for z in (-.215,.215):
    box("Table_LongApron",(0,.62,z),(.96,.12,.045),wood,table)
    box("Table_ApronMoulding",(0,.55,z),(.98,.025,.057),dark_wood,table,bevel=.003)
box("Table_Tray",(.10,.744,-.03),(.48,.035,.29),dark_wood,table,bevel=.008)
for x in (-.132,.332):
    box("Tray_RaisedEnd",(x,.77,-.03),(.02,.04,.29),wood,table,bevel=.003)
cup("CeladonWineCup_A",table,(-.02,.765,-.06))
cup("CeladonWineCup_B",table,(.22,.765,.045),.94)
wine_jar("Table_PourJar",table,(-.34,.73,.035),scale=.42,covered=False)

stool = root("Stool_Root",(-2.02,.028,-2.42),root_asset,yaw=.12)
box("Stool_Seat",(0,.43,0),(.58,.055,.32),wood,stool)
for x in (-.21,.21):
    for z in (-.10,.10):
        box("Stool_Leg",(x,.215,z),(.055,.41,.055),wood,stool)
    box("Stool_Stretcher",(x,.15,0),(.042,.038,.23),dark_wood,stool)
box("Stool_LongBrace",(0,.12,0),(.43,.035,.035),wood,stool)

jars = root("WineJars_Root",(2.03,.028,-3.10),root_asset)
wine_jar("SealedWineJar_Large",jars,(.18,0,-.11),1.0)
wine_jar("SealedWineJar_Small",jars,(-.23,0,.30),.72)
wine_jar("OpenWineJar",jars,(.48,0,.32),.60,covered=False)
box("JarWoodenPlinth",(.11,.01,.11),(1.03,.025,.91),dark_wood,jars)

fences = root("SideRailings_Root",(0,.028,0),root_asset)
for side in (-1,1):
    x = side*2.72
    for z in (-2.18,-.65):
        box("Fence_GraniteShoe",(x,.12,z),(.25,.24,.25),stone,fences,bevel=.018)
        box("Fence_Post",(x,.72,z),(.12,1.19,.12),wood,fences)
        box("Fence_PostShoulder",(x,1.29,z),(.16,.06,.16),dark_wood,fences)
        box("Fence_PostCap",(x,1.34,z),(.19,.055,.19),wood,fences)
    for height in (.35,1.02):
        box("Fence_Rail",(x,height,-1.415),(.075,.07,1.53),wood,fences)
    for index in range(5):
        z = -2.05+index*.30
        box("Fence_LatticeUpright",(x,.685,z),(.035,.61,.035),dark_wood,fences,bevel=.003)
        box("Fence_BrassPeg",(x-side*.020,.77,z),(.008,.018,.018),brass,fences,bevel=.002)
    lantern_post = root("LanternPost_Left" if side<0 else "LanternPost_Right",(x,0,-2.18),fences)
    box("LanternPost_Upright",(0,1.12,0),(.10,2.14,.10),wood,lantern_post)
    box("LanternPost_Arm",(-side*.16,2.13,.025),(.42,.07,.09),wood,lantern_post)
    box("LanternPost_Finial",(0,2.20,0),(.15,.08,.15),dark_wood,lantern_post)
    lamp = bpy.data.objects.new("HangingPaperLantern",source_lantern.data)
    asset.objects.link(lamp)
    lamp.parent = lantern_post
    lamp.location = blender_point((-side*.32,2.15,.025))
    lamp.scale = (.82,.82,.82)

basin = root("StoneLotusBasin_Root",(2.23,.028,-.30),root_asset)
box("Basin_Base",(0,.055,0),(.88,.11,1.02),grout,basin,bevel=.02)
for x in (-.39,.39):
    box("Basin_LongDressedStone",(x,.17,0),(.13,.24,1.02),stone,basin,bevel=.018)
    box("Basin_LongCap",(x,.305,0),(.16,.055,1.07),stone,basin,bevel=.014)
for z in (-.445,.445):
    box("Basin_EndStone",(0,.17,z),(.68,.24,.13),stone,basin,bevel=.018)
    box("Basin_EndCap",(0,.305,z),(.68,.055,.16),stone,basin,bevel=.014)
box("Basin_Water",(0,.205,0),(.65,.008,.75),water,basin,bevel=0)
for leaf_index,(x,z,radius) in enumerate(((-.12,.12,.13),(.13,-.16,.10))):
    vertices = [(x,.221,z)]
    segments=32
    for index in range(segments):
        angle=.18+index/(segments-1)*(math.tau-.36)
        rim=radius*(1+.035*math.sin(angle*6))
        vertices.append((x+rim*math.cos(angle),.214+.005*math.sin(angle*4),z+rim*math.sin(angle)))
    mesh_object(f"Lotus_Leaf_{leaf_index}",vertices,[(0,index+2,index+1) for index in range(segments-1)],leaf_mat,basin)
    for index in range(7):
        angle=.28+index*.84
        tube("Lotus_LeafVein",[(x,.224,z),(x+radius*.88*math.cos(angle),.218,z+radius*.88*math.sin(angle))],
             .0008,vein_mat,basin,sides=4)

ground = root("SidePaving_Root",parent=root_asset)
for side in (-1,1):
    box("SidePaving_Mortar",(side*2.55,-.05,-1.93),(1.0,.10,4.60),grout,ground,bevel=0)
    for column in range(2):
        for row in range(9):
            x=side*(2.35+column*.44)
            z=-4.02+row*.51
            box("SidePaving_DressedSlab",(x,-.007,z),(.425,.065,.492),stone,ground,bevel=.012)

# One mesh per module preserves editable assemblies with bounded material batches.
for module in (table,stool,jars,fences,basin,ground):
    objects = [obj for obj in module.children_recursive if obj.type=="MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    joined.name = module.name.replace("_Root","_Geometry")
    world_transform = joined.matrix_world.copy()
    joined.parent = module
    joined.matrix_world = world_transform
    bpy.ops.object.select_all(action="DESELECT")

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"courtyard_details.blend"))
for obj in asset.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root_asset
output = OUT/"courtyard_details.glb"
bpy.ops.export_scene.gltf(filepath=str(output),export_format="GLB",use_selection=True,
                          export_extras=True,export_yup=True,export_animations=False)
RUNTIME.mkdir(parents=True,exist_ok=True)
shutil.copy2(output,RUNTIME/output.name)

# This offline production image shows the new pieces in the existing entrance.
# The camera and lighting are excluded from the exported runtime GLB.
bpy.ops.object.select_all(action="DESELECT")
for source_name in ("tavern_slice.glb","forecourt.glb"):
    bpy.ops.import_scene.gltf(filepath=str(OUT/source_name))
    imported=[obj for obj in bpy.context.selected_objects if obj.parent is None]
    for obj in imported:
        obj.location += Vector(blender_point((0,0,-4)))
world=bpy.data.worlds.new("Courtyard production studio")
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.11,.15,.22,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.28
scene.world=world
for name,position,target,power,size,color in (
        ("MoonFill",(0,5.3,-.3),(0,.6,-2.3),550,5,(.59,.72,1)),
        ("EntranceWarmth",(-1.6,2.2,-3.4),(-.7,.8,-2.8),90,1.1,(1,.46,.21)),
        ("SideLanternWarmth",(2.4,1.7,-1.9),(1.9,.6,-1),55,.8,(1,.48,.20)),
        ("FrontSoftFill",(-2.5,3,2),(-.3,.6,-2),160,4,(.74,.79,.91))):
    data=bpy.data.lights.new(name,"AREA")
    data.energy=power
    data.shape="DISK"
    data.size=size
    data.color=color
    lamp=bpy.data.objects.new(name,data)
    scene.collection.objects.link(lamp)
    lamp.location=blender_point(position)
    lamp.rotation_euler=(Vector(blender_point(target))-lamp.location).to_track_quat("-Z","Y").to_euler()
camera_data=bpy.data.cameras.new("CourtyardProductionCamera")
camera=bpy.data.objects.new("CourtyardProductionCamera",camera_data)
scene.collection.objects.link(camera)
camera.location=blender_point((4.6,3.7,4.9))
camera.rotation_euler=(Vector(blender_point((0,1.05,-2.15)))-camera.location).to_track_quat("-Z","Y").to_euler()
camera_data.lens=40
scene.camera=camera
scene.render.engine="CYCLES"
scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.resolution_x=1400
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.filepath=str(OUT/"courtyard_details_preview.png")
bpy.ops.render.render(write_still=True)
print(json.dumps({"asset":str(output),"load_at_stage_meters":[0,0,0],
                  "modules":["TeaTable","Stool","WineJars","SideRailings","StoneLotusBasin","SidePaving"],
                  "preview":"offline production image; device acceptance pending"},ensure_ascii=False))
