"""Build one image-only wet-stone material candidate from the formal 96c554 scene.

The two authored maps are derived from material8's embedded Granite Tile CC0 maps.
No lighting, node, material count, geometry or layout is changed.
"""
from pathlib import Path
from io import BytesIO
import copy
import argparse
import hashlib
import json
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ENV=HERE.parents[1];ROOT=HERE.parents[4]
SOURCE=ROOT/'ArtSource/refinement/environment-hero/native-fight-entrance/courtyard_native_entrance.glb'
EXPECTED='96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d'
ENCODER=ROOT/'ArtSource/refinement/pbr-compression/tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx'
sys.path[:0]=[str(ENV),str(ROOT/'ArtSource/refinement/pbr-compression')]
from verify_environment import read
import compress_pbr as ktx

BASE_IMAGE=10;MR_IMAGE=11;BASE_TEXTURE=10;MR_TEXTURE=11;MATERIAL=8

def sha(value):
    if isinstance(value,Path):value=value.read_bytes()
    return hashlib.sha256(value).hexdigest()

def view_bytes(doc,blob,index):
    v=doc['bufferViews'][index];start=v.get('byteOffset',0)
    return bytes(blob[start:start+v['byteLength']])

def source_image(doc,blob,index):
    image=doc['images'][index];return view_bytes(doc,blob,image['bufferView'])

def periodic_noise(size,grid,seed):
    rng=np.random.default_rng(seed)
    # A tiled low-frequency field: no location-specific light direction or reflection.
    tile=rng.random((grid,grid),dtype=np.float32)
    tiled=np.tile(tile,(2,2))
    crop=Image.fromarray(np.uint8(tiled*255)).resize((size*2,size*2),Image.Resampling.BICUBIC)
    return np.asarray(crop,dtype=np.float32)[:size,:size]/255.

def wet_mask(size):
    a=periodic_noise(size,13,20261116)
    b=periodic_noise(size,31,20261117)
    c=periodic_noise(size,5,20261118)
    field=.56*a+.29*b+.15*c
    field=(field-field.min())/(field.max()-field.min())
    # Broad moisture varies continuously over the 0.65m repeat; fine pores stay subtle.
    return np.clip((field-.25)/.67,0,1).astype(np.float32)

def author_maps(doc,blob):
    base=Image.open(BytesIO(source_image(doc,blob,BASE_IMAGE))).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    mr=Image.open(BytesIO(source_image(doc,blob,MR_IMAGE))).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    color=np.asarray(base,dtype=np.float32)/255.;metal=np.asarray(mr,dtype=np.uint8).copy();mask=wet_mask(1024)
    # Wet granite darkens most in pores while retaining neutral stone hue and scan grain.
    shade=.985-.145*mask
    neutral=color.mean(axis=2,keepdims=True)
    color=(color*.92+neutral*.08)*shade[:,:,None]
    # Only G roughness changes. R and B preserve existing occlusion/metal channels.
    rough=metal[:,:,1].astype(np.float32)/255.
    rough=np.clip(rough*(.90-.38*mask)+.018*(1-mask),.18,.88)
    metal[:,:,1]=np.uint8(np.floor(rough*255+.5))
    outputs={'wet_stone_basecolor_1024.png':Image.fromarray(np.uint8(np.floor(np.clip(color,0,1)*255+.5)),'RGB'),
             'wet_stone_metallic_roughness_1024.png':Image.fromarray(metal,'RGB')}
    return outputs,{'mask_min':float(mask.min()),'mask_max':float(mask.max()),'mask_mean':float(mask.mean()),
                    'base_darkening_min':float(shade.min()),'base_darkening_max':float(shade.max()),
                    'roughness_source_mean':float(np.asarray(mr,dtype=np.float32)[:,:,1].mean()/255.),
                    'roughness_wet_mean':float(rough.mean()),'fixed_light_baked':False,'new_normal_map':False}

def replace_views(doc,blob,replacements):
    result=copy.deepcopy(doc);packed=bytearray()
    for index,view in enumerate(result['bufferViews']):
        packed.extend(b'\0'*(-len(packed)%4));data=replacements.get(index,view_bytes(doc,blob,index))
        view['byteOffset']=len(packed);view['byteLength']=len(data);packed.extend(data)
    return result,bytes(packed)

def write_glb(doc,blob,path):
    path.write_bytes(ktx.write_glb(doc,blob))

def ktx_contract(domain):
    return {'roles':['baseColor' if domain=='srgb' else 'metallicRoughness'],'domain':domain,'wrap_s':'wrap','wrap_t':'wrap'}

def main(output_dir=HERE):
    output_dir=Path(output_dir).resolve();output_dir.mkdir(parents=True,exist_ok=True)
    if sha(SOURCE)!=EXPECTED:raise ValueError('immutable authoring 96c554 source SHA changed')
    doc,blob=read(SOURCE)
    material=doc['materials'][MATERIAL]
    assert material['name']=='EH Stone | walked granite'
    assert material['pbrMetallicRoughness']['baseColorTexture']['index']==BASE_TEXTURE
    assert material['pbrMetallicRoughness']['metallicRoughnessTexture']['index']==MR_TEXTURE
    assert material['normalTexture']['index']==9
    outputs,metrics=author_maps(doc,blob);texture_dir=output_dir/'textures';texture_dir.mkdir(parents=True,exist_ok=True)
    for name,image in outputs.items():image.save(texture_dir/name,format='PNG',optimize=True)
    raw={name:(texture_dir/name).read_bytes() for name in outputs}
    # Stage PNG GLB is the exact full-scene render source; KTX2 below is the private runtime candidate.
    png_replacements={doc['images'][BASE_IMAGE]['bufferView']:raw['wet_stone_basecolor_1024.png'],
                      doc['images'][MR_IMAGE]['bufferView']:raw['wet_stone_metallic_roughness_1024.png']}
    png_doc,png_blob=replace_views(doc,blob,png_replacements)
    png_doc['images'][BASE_IMAGE]['mimeType']=png_doc['images'][MR_IMAGE]['mimeType']='image/png'
    png_path=output_dir/'courtyard_wet_stone_png.glb';write_glb(png_doc,png_blob,png_path)
    identity=ktx.encoder_identity(ENCODER);cache=output_dir/'ktx-cache';cache.mkdir(exist_ok=True)
    color_ktx,color_record=ktx.encode_image(raw['wet_stone_basecolor_1024.png'],ktx_contract('srgb'),ENCODER,identity,cache)
    mr_ktx,mr_record=ktx.encode_image(raw['wet_stone_metallic_roughness_1024.png'],ktx_contract('linear'),ENCODER,identity,cache)
    ktx_doc,ktx_blob=replace_views(doc,blob,{doc['images'][BASE_IMAGE]['bufferView']:color_ktx,doc['images'][MR_IMAGE]['bufferView']:mr_ktx})
    for image in (BASE_IMAGE,MR_IMAGE):ktx_doc['images'][image]['mimeType']='image/ktx2'
    for texture in (BASE_TEXTURE,MR_TEXTURE):
        source=ktx_doc['textures'][texture].pop('source');ktx_doc['textures'][texture]['extensions']={'KHR_texture_basisu':{'source':source}}
    ktx_doc['extensionsUsed']=['KHR_texture_basisu'];ktx_doc['extensionsRequired']=['KHR_texture_basisu']
    ktx_path=output_dir/'courtyard_wet_stone_ktx.glb';write_glb(ktx_doc,ktx_blob,ktx_path)
    provenance={'status':'constructed_for_visual_gate','input':{'path':str(SOURCE.relative_to(ROOT)),'sha256':EXPECTED},
      'png_scene':{'path':png_path.name,'sha256':sha(png_path),'bytes':png_path.stat().st_size},
      'ktx_scene':{'path':ktx_path.name,'sha256':sha(ktx_path),'bytes':ktx_path.stat().st_size},
      'material':{'index':MATERIAL,'name':material['name'],'replaced_images':[BASE_IMAGE,MR_IMAGE],'unchanged_normal_image':9,'unchanged_texture_count':len(doc['textures']),'unchanged_material_count':len(doc['materials'])},
      'build_execution':{'script':str(Path(__file__).resolve().relative_to(ROOT)),'script_sha256':sha(Path(__file__)),
        'input_policy':'One immutable authoring asset; downstream runtime GLB is not read.'},
      'generated_images':[{'path':str((texture_dir/name).relative_to(output_dir)),'sha256':sha(data),'bytes':len(data),'size':[1024,1024]} for name,data in raw.items()],
      'source_images':{'baseColor_image10_sha256':sha(source_image(doc,blob,BASE_IMAGE)),'mr_image11_sha256':sha(source_image(doc,blob,MR_IMAGE)),'normal_image9_sha256':sha(source_image(doc,blob,9))},
      'authoring':metrics,'license':{'derived_from':'existing embedded material8 maps; no external download','original_source':'Poly Haven Granite Tile by Charlotte Baglioni','license':'CC0','repo_evidence':'ArtSource/tavern/README.md lines 22-25','modification':'procedural neutral darkening and roughness partition; no fixed light/reflection baked into albedo'},
      'compression':{'encoder':identity,'settings':ktx.SETTINGS,
        'baseColor':{'image':BASE_IMAGE,**color_record},'metallicRoughness':{'image':MR_IMAGE,**mr_record}}}
    (output_dir/'texture_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'png':provenance['png_scene'],'ktx':provenance['ktx_scene'],'images':provenance['generated_images'],'metrics':metrics},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=HERE,help='Private rebuild destination; authoring input remains fixed')
    main(parser.parse_args().output_dir)
