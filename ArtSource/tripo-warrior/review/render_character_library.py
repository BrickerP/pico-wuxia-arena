"""Offline production display of the actual three Tripo GLB character assets.

Selects imported NLA tracks by their original GLB clip names. No runtime assets
are modified, and the studio, labels and lights are only display content.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE=Path(__file__).resolve().parent
LIBRARY=HERE.parent/"library"
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=30
scene.unit_settings.system="METRIC"


def material(name,color,roughness=0.7,emission=False):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Roughness"].default_value=roughness
    if emission:
        shader.inputs["Emission Color"].default_value=(*color,1)
        shader.inputs["Emission Strength"].default_value=0.7
    return mat


actors=[]
for index,key in enumerate(("base","indigo","veteran")):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(LIBRARY/f"{key}.glb"))
    imported=list(bpy.context.selected_objects)
    placement=bpy.data.objects.new(f"Display_{key}",None)
    scene.collection.objects.link(placement)
    for obj in imported:
        if obj.parent is None:
            obj.parent=placement
    placement.location.x=(index-1)*2.40
    placement.rotation_euler.z=(index-1)*-0.07
    armatures=[obj for obj in imported if obj.type=="ARMATURE"]
    actors.append((key,armatures))


def pose(armatures,clip,seconds):
    for armature in armatures:
        data=armature.animation_data
        if data is None:
            raise RuntimeError(f"Missing animation data in {armature.name}")
        data.action=None
        found=False
        for track in data.nla_tracks:
            selected=track.name==clip
            track.mute=not selected
            if selected:
                found=True
                strip=track.strips[0]
                # All displays are rendered at scene frame 63. Moving the strip
                # aligns its original 30 fps source time with this common frame.
                strip.frame_start=64-seconds*scene.render.fps
                strip.influence=1.0
        if not found:
            raise RuntimeError(f"Clip {clip} is absent from {armature.name}")
        print(f"Display {armature.name}: original NLA {clip}, source {seconds:.3f}s")


floor=material("Studio | charcoal stone",(.035,.041,.048),.72)
bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,-.035))
bpy.context.object.data.materials.append(floor)

world=bpy.data.worlds.new("Offline studio")
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.07,.09,.12,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.42
scene.world=world
for name,position,target,power,size,color in (
        ("KeyWarm",(-3.0,-4.5,5.5),(0,0,1),900,5,(1,.84,.69)),
        ("FillCool",(4.2,-2.0,3.5),(0,0,1.2),650,4,(.62,.76,1)),
        ("Edge",(1.2,3.0,4.0),(0,0,1.2),1100,3,(.88,.94,1))):
    data=bpy.data.lights.new(name,"AREA")
    data.energy=power
    data.shape="DISK"
    data.size=size
    data.color=color
    light=bpy.data.objects.new(name,data)
    scene.collection.objects.link(light)
    light.location=position
    light.rotation_euler=(Vector(target)-light.location).to_track_quat("-Z","Y").to_euler()

camera_data=bpy.data.cameras.new("LibraryDisplayCamera")
camera_data.type="ORTHO"
camera_data.ortho_scale=8.1
camera=bpy.data.objects.new("LibraryDisplayCamera",camera_data)
scene.collection.objects.link(camera)
camera.location=(.1,-11,3.7)
camera.rotation_euler=(Vector((0,0,1.12))-camera.location).to_track_quat("-Z","Y").to_euler()
scene.camera=camera
font=bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
label_material=material("Studio | ivory captions",(.8,.78,.69),emission=True)


def label(name,text,position,size):
    curve=bpy.data.curves.new(name,"FONT")
    curve.body=text
    curve.font=font
    curve.align_x="CENTER"
    curve.size=size
    curve.space_character=1.06
    obj=bpy.data.objects.new(name,curve)
    scene.collection.objects.link(obj)
    obj.location=position
    obj.rotation_euler=camera.rotation_euler
    curve.materials.append(label_material)
    return curve


title=label("Title","酒馆试炼 · 三套实际角色资产",(0,.6,2.85),.23)
labels=[]
for index,name in enumerate(("试刀客","青衫护院","玄甲守擂")):
    labels.append(label(f"Name_{index}",name,((index-1)*2.4,-.8,.12),.20))
label("OfflineCaption","离线资产展示 · 实际 GLB 骨架与动作 · 游戏画面待运行验收",(0,-1.55,.05),.12)
scene.render.engine="CYCLES"
scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1800
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
def render_stills():
    for key,armatures in actors:
        pose(armatures,"slash",2.10)
    scene.frame_set(63)
    scene.render.filepath=str(HERE/"character_library_preview.png")
    bpy.ops.render.render(write_still=True)

    title.body="酒馆试炼 · 实际动作资源时刻"
    for (key,armatures),curve,(clip,seconds,text) in zip(actors,labels,(
            ("idle",1.0,"试刀客 · idle 1.00s"),
            ("walk",.60,"青衫护院 · walk 0.60s"),
            ("hit_body",.35,"玄甲守擂 · hit_body 0.35s"))):
        pose(armatures,clip,seconds)
        curve.body=text
    scene.frame_set(63)
    scene.render.filepath=str(HERE/"character_motion_preview.png")
    bpy.ops.render.render(write_still=True)
    print("Produced character_library_preview.png and character_motion_preview.png")


if __name__ == "__main__":
    render_stills()
