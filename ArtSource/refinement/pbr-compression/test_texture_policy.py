"""Size policy failures plus a real pinned KTX encode of 4K PBR inputs."""
from pathlib import Path
import copy,io,json,struct,tempfile,unittest,os,sys,ast
from unittest import mock
sys.dont_write_bytecode=True
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
PUBLIC_PRODUCER=REPO/'ArtSource/tripo-warrior'
sys.path.insert(0,str(PUBLIC_PRODUCER))
sys.path.insert(0,str(HERE))
import compress_pbr as p
import production_contract
from production_contract import production_binding,canonical_hash
ENCODER=REPO/'ArtSource/refinement/pbr-compression/tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx'

def fixture(size=4):
    payload=bytearray();views=[]
    def add(data):
        payload.extend(b'\0'*(-len(payload)%4));index=len(views);views.append(dict(buffer=0,byteOffset=len(payload),byteLength=len(data)));payload.extend(data);return index
    geometry=struct.pack('<9f',0,0,0,1,0,0,0,1,0);geometry_view=add(geometry)
    times=add(struct.pack('<f',0));translation=add(struct.pack('<3f',.1,.2,.3));ibm=add(struct.pack('<16f',*[1 if i%5==0 else 0 for i in range(16)]))
    images=[]
    for name,colour in [('body',(110,120,130)),('head_base',(167,132,111)),('head_normal',(128,128,255)),('head_mr',(255,128,0))]:
        image=Image.new('RGB',(size,size),colour);stream=io.BytesIO();image.save(stream,format='PNG');images.append(dict(name=name,mimeType='image/png',bufferView=add(stream.getvalue())))
    return p.write_glb(dict(asset=dict(version='2.0'),buffers=[dict(byteLength=len(payload))],bufferViews=views,
        accessors=[dict(bufferView=geometry_view,componentType=5126,type='VEC3',count=3),dict(bufferView=times,componentType=5126,type='SCALAR',count=1),dict(bufferView=translation,componentType=5126,type='VEC3',count=1),dict(bufferView=ibm,componentType=5126,type='MAT4',count=1)],
        images=images,textures=[dict(source=i)for i in range(4)],
        materials=[dict(name='Body',pbrMetallicRoughness=dict(baseColorTexture=dict(index=0))),dict(name='HeroHead_test',pbrMetallicRoughness=dict(baseColorTexture=dict(index=1),metallicRoughnessTexture=dict(index=3)),normalTexture=dict(index=2))],
        meshes=[dict(primitives=[dict(attributes=dict(POSITION=0),material=0),dict(attributes=dict(POSITION=0),material=1)])],
        nodes=[dict(mesh=0,skin=0)],skins=[dict(joints=[0],inverseBindMatrices=3)],scene=0,scenes=[dict(nodes=[0])],
        animations=[dict(name='proof',samplers=[dict(input=1,output=2,interpolation='STEP')],channels=[dict(sampler=0,target=dict(node=0,path='translation'))])]),bytes(payload))

class PolicyTests(unittest.TestCase):
    def setUp(self):self.doc,self.binary=p.load_glb(fixture())
    def test_actual_material_slots_assign_three_head_images(self):
        self.assertEqual(p.image_resize_limits(self.doc,{'HeroHead_':2048}),[1024,2048,2048,2048])
    def test_no_override_means_one_explicit_1024_policy(self):
        self.assertEqual(p.image_resize_limits(self.doc),[1024]*4)
    def test_missing_head_material_rejected(self):
        with self.assertRaisesRegex(ValueError,'did not match'):p.image_resize_limits(self.doc,{'HeroHeed_':2048})
    def test_orphaned_material_cannot_satisfy_head_match(self):
        self.doc['meshes'][0]['primitives'].pop()
        with self.assertRaisesRegex(ValueError,'rendered material'):p.image_resize_limits(self.doc,{'HeroHead_':2048})
    def test_shared_image_cannot_be_silently_upgraded(self):
        self.doc['materials'][1]['pbrMetallicRoughness']['baseColorTexture']['index']=0
        with self.assertRaisesRegex(ValueError,'conflicting'):p.image_resize_limits(self.doc,{'HeroHead_':2048})
    def test_invalid_override_fails(self):
        for override in ({'':2048},{'HeroHead_':True},{'HeroHead_':4096},[]):
            with self.subTest(override=override),self.assertRaisesRegex(ValueError,'2048 maximum'):p.image_resize_limits(self.doc,override)
    def test_wrong_prefix_fails_before_any_encoder_execution(self):
        with tempfile.TemporaryDirectory()as tmp:
            source=Path(tmp)/'input.glb';source.write_bytes(fixture());output=Path(tmp)/'output.glb'
            with self.assertRaisesRegex(ValueError,'did not match'):p.build(source,p.sha(source.read_bytes()),output,Path('missing-encoder'),Path(tmp)/'cache',{'WrongHead_':2048})
            self.assertFalse(output.exists());self.assertFalse((Path(tmp)/'cache').exists())
    def test_resize_never_upscales_and_retains_blocks(self):
        self.assertEqual(p.runtime_size((4096,2048),1024),(1024,512));self.assertEqual(p.runtime_size((512,256),1024),(512,256));self.assertEqual(p.runtime_size((4096,4096),2048),(2048,2048))
    def test_resize_filters_srgb_in_linear_light_and_alpha_linearly(self):
        image=Image.new('RGBA',(8,8));image.putdata([(255 if x%2 else 0,)*3+(200 if x%2 else 100,) for y in range(8)for x in range(8)])
        colour=p.resize_for_runtime(image,dict(domain='srgb',wrap_s='wrap',wrap_t='wrap'),4)
        data=p.resize_for_runtime(image,dict(domain='linear',wrap_s='wrap',wrap_t='wrap'),4)
        self.assertEqual(set(colour.getdata()),{(188,188,188,150)});self.assertEqual(set(data.getdata()),{(128,128,128,150)})
    def test_material_budget_is_part_of_shared_production_binding(self):
        manifest=json.loads((PUBLIC_PRODUCER/'motion_library.json').read_text())
        baseline=copy.deepcopy(manifest)
        next(c for c in baseline['characters']if c['id']=='veteran').pop('runtime_texture_material_overrides',None)
        before=canonical_hash(production_binding(baseline))
        with_head_budget=copy.deepcopy(baseline)
        next(c for c in with_head_budget['characters']if c['id']=='veteran')['runtime_texture_material_overrides']={'HeroHead_':2048}
        self.assertNotEqual(before,canonical_hash(production_binding(with_head_budget)))
    def test_producer_and_encoder_have_one_identical_settings_contract(self):
        self.assertEqual(Path(p.__file__).resolve(),HERE/'compress_pbr.py')
        self.assertEqual(Path(production_contract.__file__).resolve(),PUBLIC_PRODUCER/'production_contract.py')
        # The producer imports Blender-only mathutils. Read its real public
        # literal contract in host tests instead of stubbing Blender APIs.
        tree=ast.parse((PUBLIC_PRODUCER/'prepare_character_library.py').read_text());settings=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='TEXTURE_SETTINGS'for t in n.targets));self.assertEqual(settings,p.SETTINGS)

@unittest.skipUnless(os.environ.get('RUN_REAL_KTX_TEST')=='1','set RUN_REAL_KTX_TEST=1 for actual KTX encode')
class ActualEncoderTests(unittest.TestCase):
    def test_encoder_symlink_reuses_cache_and_preserves_canonical_report(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);source=root/'source.glb';raw=fixture(64)
            doc,binary=p.load_glb(raw)
            doc['samplers']=[dict(wrapS=10497,wrapT=33071)]
            doc['textures'][0]['sampler']=0
            raw=p.write_glb(doc,binary);source.write_bytes(raw)
            real=ENCODER.resolve();alias=root/'ktx-alias';alias.symlink_to(real)
            cache=root/'cache';first=root/'real/output.glb';second=root/'alias/output.glb'
            original=p.build(source,p.sha(raw),first,real,cache,{'HeroHead_':2048})
            cached={path.name:path.read_bytes()for path in cache.iterdir()if path.is_file()}
            real_run=p.run
            def cached_tool_run(args):
                self.assertNotEqual(str(args[1]),'create','The alias must reuse the already validated cache')
                return real_run(args)
            with mock.patch.object(p,'run',side_effect=cached_tool_run):
                linked=p.build(source,p.sha(raw),second,alias,cache,{'HeroHead_':2048})
            self.assertEqual(first.read_bytes(),second.read_bytes())
            self.assertEqual(cached,{path.name:path.read_bytes()for path in cache.iterdir()if path.is_file()})
            self.assertEqual(original['images'],linked['images'])
            self.assertEqual(original['encoder'],linked['encoder'])
            self.assertEqual(linked['encoder']['sha256'],p.ENCODER_SHA)
            self.assertEqual(linked['encoder']['libktx_sha256'],p.LIBKTX_SHA)
            self.assertEqual(linked['images'][0]['mip_provenance']['generator_sha256'],p.sha(Path(p.__file__).read_bytes()))
            for report in [original,linked]:
                for role in ['input','output']:report[role]['path']=Path(report[role]['path']).name
            self.assertEqual(original,linked)

    def test_4k_source_becomes_real_2k_head_and_1k_body_without_geometry_change(self):
        with tempfile.TemporaryDirectory()as tmp:
            out=Path(tmp);source=out/'pbr_4k_fixture.glb';raw=fixture(4096);source.write_bytes(raw);output=out/'pbr_runtime_fixture.glb'
            output.unlink(missing_ok=True);report=p.build(source,p.sha(raw),output,ENCODER,out/'cache',{'HeroHead_':2048})
            sd,sb=p.load_glb(raw);d,b=p.load_glb(output.read_bytes());self.assertEqual(p.sha(source.read_bytes()),p.sha(raw))
            self.assertEqual([r['source_width']for r in report['images']],[4096]*4)
            expected=[1024,2048,2048,2048];actual=[]
            for im in d['images']:
                blob=p.view_bytes(d,b,im['bufferView']);width,height=struct.unpack_from('<II',blob,20);self.assertEqual(width,height);actual.append(width)
            self.assertEqual(actual,expected)
            for field in ['nodes','skins','meshes','accessors','animations','materials','samplers','scene','scenes']:self.assertEqual(sd.get(field),d.get(field))
            image_views={im['bufferView']for im in sd['images']}
            for i in range(len(sd['bufferViews'])):
                if i not in image_views:self.assertEqual(p.view_bytes(sd,sb,i),p.view_bytes(d,b,i))
            tampered=copy.deepcopy(d);tampered['nodes'][0]['translation']=[9,9,9]
            with self.assertRaisesRegex(ValueError,'semantics changed'):p.verify_preserved(raw,p.write_glb(tampered,b),{'HeroHead_':2048})
if __name__=='__main__':unittest.main(verbosity=2)
