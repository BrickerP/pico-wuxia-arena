"""Same-pose PBR/albedo/clay/shading-normal/mesh-normal neck evidence."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def diagnostic(mat,mode,original):
    tree=mat.node_tree;nodes=tree.nodes;links=tree.links
    output,source=original
    for link in list(output.inputs['Surface'].links):links.remove(link)
    if mode=='pbr':links.new(source,output.inputs['Surface']);return
    bsdf=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not bsdf:links.new(source,output.inputs['Surface']);return
    emission=nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=1
    if mode=='albedo':
        color=bsdf.inputs['Base Color']
        if color.is_linked:links.new(color.links[0].from_socket,emission.inputs['Color'])
        else:emission.inputs['Color'].default_value=color.default_value
    else:
        geometry=nodes.new('ShaderNodeNewGeometry')
        normal=bsdf.inputs['Normal']
        source_normal=normal.links[0].from_socket if mode=='normal' and normal.is_linked else geometry.outputs['Normal']
        multiply=nodes.new('ShaderNodeVectorMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=(.5,.5,.5)
        add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5)
        links.new(source_normal,multiply.inputs[0]);links.new(multiply.outputs['Vector'],add.inputs[0]);links.new(add.outputs['Vector'],emission.inputs['Color'])
    transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
    alpha=bsdf.inputs['Alpha']
    if alpha.is_linked:links.new(alpha.links[0].from_socket,mix.inputs[0])
    else:mix.inputs[0].default_value=alpha.default_value
    links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE/'prepared/base.glb')
    parser.add_argument('--output',type=Path,default=HERE/'diagnostics-initial')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    source=args.source.resolve();digest=hashlib.sha256(source.read_bytes()).hexdigest()
    args.output.mkdir(parents=True,exist_ok=True)
    studio=module('neck_diag_studio',ROOT/'ArtSource/refinement/grip/render_grip_candidates.py')
    poses=module('neck_diag_poses',ROOT/'ArtSource/refinement/hand-poses/render_hand_poses.py')
    root_review=ROOT/'ArtSource/tripo-warrior/review/hero-face-integrated/review/render_manifest.json'
    camera_record=next(row for row in json.loads(root_review.read_text())['images']
                       if row['label']=='after' and row['clip']=='idle' and row['view']=='oblique')
    scene,camera=studio.setup_scene(768,8);scene.render.threads_mode='FIXED';scene.render.threads=2
    for light in bpy.data.lights:light.color=(1,1,1)
    bpy.ops.mesh.primitive_plane_add(size=10,location=(0,0,-.029))
    bpy.ops.import_scene.gltf(filepath=str(source))
    poses.select_pose(scene,'idle',1.)
    camera.location=camera_record['camera_location'];target=Vector(camera_record['camera_target'])
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=camera_record['camera_ortho_scale']
    originals={}
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        output=next((n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
        if output and output.inputs['Surface'].is_linked:originals[mat]=(output,output.inputs['Surface'].links[0].from_socket)
    clay=bpy.data.materials.new('Diagnostic uniform clay');clay.use_nodes=True
    clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.35,.35,.35,1)
    clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.75
    record={'source':str(source.relative_to(ROOT)),'source_sha256':digest,'clip':'idle','seconds':1.,
            'camera':camera_record,'modes':[],'images_are_diagnostic_not_final_materials':True}
    for mode in ('pbr','albedo','clay','normal','mesh-normal'):
        scene.view_layers[0].material_override=clay if mode=='clay' else None
        if mode!='clay':
            for mat,original in originals.items():diagnostic(mat,mode,original)
        scene.render.filepath=str((args.output/f'idle_oblique_{mode}.png').resolve())
        bpy.ops.render.render(write_still=True);record['modes'].append(mode)
        (args.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise ValueError('Source changed during diagnostic')


if __name__=='__main__':main()
