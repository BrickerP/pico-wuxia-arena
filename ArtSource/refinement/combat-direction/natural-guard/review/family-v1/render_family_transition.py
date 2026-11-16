"""One four-time formal/private-family overhead contact board, no movie or producer writes."""
import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
NATURAL = HERE.parents[1]
REPO = NATURAL.parents[3]
OLD = NATURAL.parent / 'native-weighted-overhead'
TIMES = (0., .2, 1.5, 1.75)
CLIP = 'attack_overhead'
CAMERA = {'projection': 'perspective', 'eye_height_metres': 1.62, 'aim_height_metres': 1.62,
          'horizontal_standoff_metres': 2.75, 'azimuth_degrees': 25., 'vertical_fov_degrees': 70.,
          'aim_gltf': [0., 1.62, 0.], 'location_gltf': [2.75*math.sin(math.radians(25)),1.62,2.75*math.cos(math.radians(25))],
          'scope': 'One fixed normal horizontal eye-height camera for all eight actual source stills; no actor or material change'}


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


HELPERS=load('family_transition_helpers',OLD/'render_weighted_overhead.py')
BASE,EYE=HELPERS.BASE,HELPERS.EYE


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')


def render(args):
    import bpy
    from mathutils import Vector

    assets={'before':args.before,'after':args.after}
    expected={'before':args.before_sha,'after':args.after_sha}
    for stage,path in assets.items():
        if BASE.identity(path)['sha256']!=expected[stage]:raise ValueError('Explicit actual '+stage+' SHA differs')
    pins={name:BASE.identity(path) for name,path in [('formal_before',args.before),('private_family',args.after),('family_authoring',args.authoring),('surface_verification',args.surface_proof),('renderer',Path(__file__)),('helpers',OLD/'render_weighted_overhead.py'),('surface_helpers',OLD/'integration/review_candidate.py')]}
    reviewer=load('family_static_semantics',OLD/'integration/review_candidate.py')
    before=reviewer.static_signature(*reviewer.library.read_glb(args.before));after=reviewer.static_signature(*reviewer.library.read_glb(args.after))
    checks={key:before[key]==after[key] for key in before}
    if not all(checks.values()):raise ValueError('Actual static body/material semantics differ: '+str(checks))
    floor_path=NATURAL/'review/v1/floor_reference.json';floor=json.loads(floor_path.read_text())
    if floor['actual_before']!=BASE.identity(args.before):raise ValueError('Current actual before does not match frozen floor baseline')
    pins['floor_reference']=BASE.identity(floor_path)
    studio=load('family_transition_studio',REPO/'ArtSource/refinement/grip/render_grip_candidates.py')
    common=load('family_transition_geometry',REPO/'ArtSource/refinement/hand-poses/attack-keyposes/render_attack_keyposes.py')
    direct=load('family_transition_direct',REPO/'ArtSource/refinement/hand-poses/attack-keyposes/stage8/render_hit_reactions.py')
    record={'completion':'rendering','inputs':pins,'clip':CLIP,'source_times_seconds':list(TIMES),'size':args.size,'samples':args.samples,'camera':CAMERA,'static_same_actual_formal_checks':checks,'source_evaluation':'Direct imported Action+action_slot, NLA disabled, source0/.2/1.5/1.75, no epsilon, actor/head/grip transform or carrier','stages':{}}
    destination=args.output/'render_manifest.json';save(destination,record)
    for stage,path in assets.items():
        scene,camera=studio.setup_scene(args.size,args.samples)
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()));imported=list(bpy.context.selected_objects)
        arms=[o for o in imported if o.type=='ARMATURE']
        if len(arms)!=1:raise ValueError('Expected one actual source armature')
        armature=arms[0];direct.select_action(scene,CLIP,0.)
        camera.data.type,camera.data.sensor_fit='PERSP','VERTICAL';camera.data.angle_y=math.radians(CAMERA['vertical_fov_degrees'])
        camera.location=common.to_blender(CAMERA['location_gltf']);aim=Vector(common.to_blender(CAMERA['aim_gltf']))
        camera.rotation_euler=(aim-camera.location).to_track_quat('-Z','Y').to_euler()
        material=common.material('Family transition floor',(.075,.09,.11));grid=common.material('Family transition grid',(.20,.25,.28));floor_z=floor['floor_blender_z']
        bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,floor_z-.006));bpy.context.object.data.materials.append(material)
        for index in range(-7,8):
            value=index*.25
            common.line('Grid X',[(-1.75,floor_z+.002,value),(1.75,floor_z+.002,value)],grid,.001)
            common.line('Grid Z',[(value,floor_z+.002,-1.75),(value,floor_z+.002,1.75)],grid,.001)
        bpy.context.view_layer.update()
        stage_record={'actor_world_matrix_blender':[list(row) for row in armature.matrix_world],'camera_world_matrix_blender':[list(row) for row in camera.matrix_world],'actual_vertical_fov_degrees':math.degrees(camera.data.angle_y),'frames':[]}
        record['stages'][stage]=stage_record;directory=args.output/stage;directory.mkdir(parents=True,exist_ok=True)
        for index,seconds in enumerate(TIMES):
            evaluation=direct.select_action(scene,CLIP,seconds);points,meshes=EYE.geometry_points(imported)
            projection=EYE.projection(points,camera,CAMERA['vertical_fov_degrees'])
            if projection['outside_vertex_count']:raise ValueError(f'Actual {stage} geometry outside fixed camera at source{seconds}: {projection}')
            row={'index':index,'source_seconds':seconds,'action_evaluation':evaluation,'anchors_gltf_metres':BASE.bone_points(armature,imported),'actual_geometry_projection':projection,'actual_geometry_meshes':meshes}
            image=directory/f'frame_{index:03d}.png';scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
            row['image']=BASE.identity(image);stage_record['frames'].append(row);save(destination,record)
            print('FAMILY_TRANSITION',stage,index,seconds,flush=True)
    if record['stages']['before']['actor_world_matrix_blender']!=record['stages']['after']['actor_world_matrix_blender']:raise ValueError('Actor transforms differ')
    if record['stages']['before']['camera_world_matrix_blender']!=record['stages']['after']['camera_world_matrix_blender']:raise ValueError('Camera transforms differ')
    for pin in pins.values():
        if BASE.identity(pin['path'])!=pin:raise ValueError('Input changed during still rendering: '+pin['path'])
    record['completion']='complete';save(destination,record)


def assemble(args):
    from PIL import Image,ImageDraw,ImageFont
    record=json.loads((args.output/'render_manifest.json').read_text())
    if record['completion']!='complete':raise ValueError('Eight-still pass incomplete')
    for pin in record['inputs'].values():
        if BASE.identity(pin['path'])!=pin:raise ValueError('Rendered input identity changed: '+pin['path'])
    size=record['size'];header,footer=72,56
    fontfile='/System/Library/Fonts/Supplemental/Arial Unicode.ttf';font=ImageFont.truetype(fontfile,21);small=ImageFont.truetype(fontfile,16)
    board=Image.new('RGB',(size*4,(size+header+footer)*2),(24,29,35))
    for r,stage in enumerate(('before','after')):
        for row in record['stages'][stage]['frames']:
            image=Path(row['image']['path'])
            if BASE.identity(image)!=row['image']:raise ValueError('Source image changed')
            panel=Image.new('RGB',(size,size+header+footer),(24,29,35));panel.paste(Image.open(image).convert('RGB'),(0,header));draw=ImageDraw.Draw(panel)
            label='CURRENT FORMAL' if stage=='before' else 'PRIVATE FAMILY'
            identity=record['inputs']['formal_before' if stage=='before' else 'private_family']
            draw.text((9,6),f'{label} / attack_overhead',font=font,fill='white')
            draw.text((9,36),f'source {row["source_seconds"]:.6f}s / SHA {identity["sha256"][:16]}',font=small,fill=(205,218,230))
            draw.text((9,size+header+6),'eye=aim1.62m / standoff2.75m / +X25deg / VFOV70',font=small,fill=(205,218,230))
            draw.text((9,size+header+29),'Actual body + blade / same camera, actor and materials',font=small,fill=(205,218,230))
            panel.save(args.output/stage/f'panel_{row["index"]:03d}.png');board.paste(panel,(row['index']*size,r*panel.height))
    board.save(args.output/'overhead_four_times_formal_vs_family.png')
    print('FAMILY_TRANSITION_BOARD',args.output/'overhead_four_times_formal_vs_family.png',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('before','after','authoring','surface-proof','output'):parser.add_argument('--'+flag,type=Path,required=True)
    for flag in ('before-sha','after-sha'):parser.add_argument('--'+flag,required=True)
    parser.add_argument('--size',type=int,default=640);parser.add_argument('--samples',type=int,default=4);parser.add_argument('--assemble-only',action='store_true')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:];args=parser.parse_args(argv)
    if args.size<128 or args.size%2 or args.samples<1:parser.error('Expected even size>=128 and positive samples')
    if args.assemble_only:assemble(args)
    else:render(args)


if __name__=='__main__':main()
