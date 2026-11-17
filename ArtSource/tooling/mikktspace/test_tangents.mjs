import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { loadMikk,generatePrimitive,assemble,inspectCorners,repairDegenerateCorner,geometryFingerprint,assertGeometryContract,assertPreservation } from './build_tangents.mjs';
import { append,attributeBytes } from './glb_io.mjs';
const mikk=await loadMikk();
function fixture({mirror=false,unused=false}={}) {
  const doc={asset:{version:'2.0'},buffers:[{byteLength:0}],bufferViews:[],accessors:[],materials:[{name:'Body',normalTexture:{index:0}}],textures:[],images:[],nodes:[{mesh:0}],skins:[],scenes:[{nodes:[0]}],scene:0,animations:[]},chunks=[];
  let p=[0,0,0,1,0,0,0,1,0],uv=[0,0,1,0,0,1],indices=[0,1,2];
  if(mirror){p.push(-1,0,0,0,-1,0);uv.push(-1,0,0,1);indices.push(0,3,4);}
  if(unused){p.push(99,99,99);uv.push(0,0);}
  const n=Array.from({length:p.length/3},()=>[0,0,1]).flat(),j=Array.from({length:p.length/3},()=>[26,25,12,40]).flat(),w=Array.from({length:p.length/3},()=>[1,0,0,0]).flat();
  const attributes={POSITION:append(doc,chunks,new Float32Array(p),'VEC3',5126),NORMAL:append(doc,chunks,new Float32Array(n),'VEC3',5126),TEXCOORD_0:append(doc,chunks,new Float32Array(uv),'VEC2',5126),JOINTS_0:append(doc,chunks,new Uint16Array(j),'VEC4',5123),WEIGHTS_0:append(doc,chunks,new Float32Array(w),'VEC4',5126)};
  const primitive={attributes,indices:append(doc,chunks,new Uint32Array(indices),'SCALAR',5125,34963),material:0,mode:4};
  const ibm=append(doc,chunks,new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]),'MAT4',5126);doc.skins=[{joints:[0],inverseBindMatrices:ibm}];
  doc.meshes=[{primitives:Array.from({length:5},()=>structuredClone(primitive)),extras:{body_primitive_indices:[0,1,2,3,4]}}];
  return {doc,bin:Buffer.concat(chunks),primitive};
}
test('planar Mikk glTF frame is unit, orthogonal, and has the documented W conversion',()=>{
  const f=fixture(),g=generatePrimitive(f.doc,f.bin,f.primitive,mikk);assert.equal(g.audit.pass,true);assert.equal(g.splitCount,0);
  assert.deepEqual(Array.from(g.tangents.slice(0,4)),[1,0,0,-1]);
});
test('mirrored UV seam splits a shared source vertex rather than averaging opposite W',()=>{
  const f=fixture({mirror:true}),g=generatePrimitive(f.doc,f.bin,f.primitive,mikk);assert.equal(g.audit.pass,true);assert.equal(g.splitCount,1);assert.notEqual(g.remapped[0],g.remapped[3]);assert.equal(g.origin[g.remapped[0]],0);assert.equal(g.origin[g.remapped[3]],0);assert.equal(g.tangents[g.remapped[0]*4+3],-g.tangents[g.remapped[3]*4+3]);
});
test('orphan source rows never become rendered Mikk input or UV-degenerate faces',()=>{
  const f=fixture({unused:true}),g=generatePrimitive(f.doc,f.bin,f.primitive,mikk);assert.equal(g.audit.corners,3);assert.equal(g.audit.exact_zero_UV_faces,0);assert.equal(g.usedCount,3);assert.equal(g.sourceCount,4);
});
test('every split corner preserves all original P N UV JOINTS WEIGHTS bytes',()=>{
  const f=fixture({mirror:true}),made=assemble(f.doc,f.bin,mikk);assert.equal(made.pass,true);assert.deepEqual(made.bin.subarray(0,f.bin.length),f.bin);
  for(const row of made.mapping){const p=made.doc.meshes[0].primitives[row.primitive];for(const [key,id]of Object.entries(f.primitive.attributes)){const src=attributeBytes(f.doc,f.bin,id),out=attributeBytes(made.doc,made.bin,p.attributes[key]),size=src.length/f.doc.accessors[id].count;row.vertex_origin.forEach((old,i)=>assert.deepEqual(out.subarray(i*size,(i+1)*size),src.subarray(old*size,(old+1)*size)));}}
});
test('Steel outside the target domain stays byte-for-byte and JSON exact',()=>{
  const f=fixture();f.doc.materials.push({name:'Steel',normalTexture:{index:0}});f.doc.meshes[0].primitives.push({...structuredClone(f.primitive),material:1});const before=structuredClone(f.doc.meshes[0].primitives[5]);const made=assemble(f.doc,f.bin,mikk);assert.deepEqual(made.doc.meshes[0].primitives[5],before);
});
test('Steel accidentally selected as body is rejected',()=>{
  const f=fixture();f.doc.materials[0].name='Steel';assert.throws(()=>assemble(f.doc,f.bin,mikk),/Weapon primitive/);
});
test('bad tangent W, nonunit vectors and nonorthogonal vectors fail the frame gate',()=>{
  const p=new Float32Array([0,0,0,1,0,0,0,1,0]),n=new Float32Array([0,0,1,0,0,1,0,0,1]),uv=new Float32Array([0,0,1,0,0,1]);
  for(const row of [[1,0,0,0],[2,0,0,1],[0,0,1,1],[NaN,0,0,1]])assert.equal(inspectCorners(p,n,uv,new Float32Array([...row,...row,...row])).pass,false);
});
test('exact rank1 UV uses a stable +U edge projection and preserves Mikk W',()=>{
  const p=new Float32Array([0,0,0,1,1,0,2,2,0]),n=new Float32Array([0,0,1,0,0,1,Math.SQRT1_2,0,Math.SQRT1_2]),uv=new Float32Array([0,0,1,0,2,0]),t=new Float32Array([1,0,0,-1,1,0,0,-1,1,0,0,-1]);const r=repairDegenerateCorner(p,n,uv,t,2);assert.equal(r.UV_determinant,0);assert.equal(t[11],-1);assert.equal(r.handedness_unchanged,true);assert.ok(Math.abs(t[8]*n[6]+t[9]*n[7]+t[10]*n[8])<1e-6);
});
test('zero-U degenerate triangle is rejected, no arbitrary direction is invented',()=>{
  assert.throws(()=>repairDegenerateCorner(new Float32Array([0,0,0,1,1,0,2,2,0]),new Float32Array([0,0,1,0,0,1,0,0,1]),new Float32Array(6),new Float32Array([1,0,0,1,1,0,0,1,1,0,0,1]),0),/no nonzero/);
});
test('a +U edge nearly parallel to N is rejected',()=>{
  assert.throws(()=>repairDegenerateCorner(new Float32Array([0,0,0,1e-9,0,1,2e-9,0,2]),new Float32Array([0,0,1,0,0,1,0,0,1]),new Float32Array([0,0,1,0,2,0]),new Float32Array([1,0,0,1,1,0,0,1,1,0,0,1]),0),/nearly parallel/);
});
test('a nondegenerate UV corner cannot enter the special repair policy',()=>{
  assert.throws(()=>repairDegenerateCorner(new Float32Array([0,0,0,1,0,0,0,1,0]),new Float32Array([0,0,1,0,0,1,0,0,1]),new Float32Array([0,0,1,0,0,1]),new Float32Array([1,0,0,1,1,0,0,1,1,0,0,1]),0),/Only an exact/);
});
test('geometry/skin contract admits animation-only changes and rejects static-frame drift',()=>{
  const f=fixture(),baseline=geometryFingerprint(f.doc,f.bin).sha256,changed=structuredClone(f.doc);changed.animations=[{name:'future recipe3',channels:[],samplers:[]}];assert.equal(geometryFingerprint(changed,f.bin).sha256,baseline);changed.nodes[0].translation=[0,.01,0];assert.notEqual(geometryFingerprint(changed,f.bin).sha256,baseline);
});
test('local tangents are stored before the prepared +X to +Z frame, not rotated twice',()=>{
  const f=fixture(),g=generatePrimitive(f.doc,f.bin,f.primitive,mikk),t=Array.from(g.tangents.slice(0,3));assert.deepEqual(t,[1,0,0]);const A=[[0,0,-1],[0,1,0],[1,0,0]],world=A.map(row=>row.reduce((s,v,i)=>s+v*t[i],0));assert.deepEqual(world,[0,0,1]);
});
test('out-of-range indices and absent normals are rejected',()=>{
  const f=fixture();const broken=structuredClone(f.primitive);delete broken.attributes.NORMAL;assert.throws(()=>generatePrimitive(f.doc,f.bin,broken,mikk),/Missing NORMAL/);const bin=Buffer.from(f.bin),a=f.doc.accessors[f.primitive.indices],v=f.doc.bufferViews[a.bufferView];bin.writeUInt32LE(1000,v.byteOffset);assert.throws(()=>generatePrimitive(f.doc,bin,f.primitive,mikk),/Invalid source/);
});
test('a changed Mikk tool file fails the pinned identity gate',async()=>{
  const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'mikk-tool-negative-'));try{const file=path.join(tmp,'fake.mjs');fs.writeFileSync(file,'export const ready=Promise.resolve()');await assert.rejects(loadMikk(file),/identity changed/);}finally{fs.rmSync(tmp,{recursive:true,force:true});}
});

test('rendered-corner contract survives tangent seam splits and ignores added TANGENT', () => {
  const f = fixture({mirror:true}), before = geometryFingerprint(f.doc, f.bin);
  const made = assemble(f.doc, f.bin, mikk);
  assert.ok(made.mapping.some(row => row.vertex_origin.length > f.doc.accessors[f.primitive.attributes.POSITION].count));
  assert.equal(geometryFingerprint(made.doc, made.bin).sha256, before.sha256);
  assert.doesNotThrow(() => assertGeometryContract(made.doc, made.bin, before));
});
test('contract ignores unreferenced position rows while preserving referenced geometry checks', () => {
  const f = fixture({unused:true}), contract = geometryFingerprint(f.doc, f.bin), b = Buffer.from(f.bin);
  const position = f.doc.accessors[f.primitive.attributes.POSITION];
  const offset = f.doc.bufferViews[position.bufferView].byteOffset || 0;
  b.writeFloatLE(123456, offset + 3 * 12);
  assert.doesNotThrow(() => assertGeometryContract(f.doc, b, contract));
  b.writeFloatLE(.001, offset);
  assert.throws(() => assertGeometryContract(f.doc, b, contract), /Geometry\/skin/);
});
test('contract rejects changed joint weight, joint index, inverse bind matrix and corner order', () => {
  const f = fixture(), contract = geometryFingerprint(f.doc, f.bin);
  const offset = id => { const a = f.doc.accessors[id]; return (f.doc.bufferViews[a.bufferView].byteOffset || 0) + (a.byteOffset || 0); };
  for (const [id, size, value] of [
    [f.primitive.attributes.WEIGHTS_0, 4, .5],
    [f.primitive.attributes.JOINTS_0, 2, 1],
    [f.doc.skins[0].inverseBindMatrices, 4, 2],
    [f.primitive.indices, 4, 1],
  ]) {
    const b = Buffer.from(f.bin);
    if (id === f.primitive.indices) b.writeUInt32LE(value, offset(id));
    else if (size === 2) b.writeUInt16LE(value, offset(id));
    else b.writeFloatLE(value, offset(id));
    assert.throws(() => assertGeometryContract(f.doc, b, contract), /Geometry\/skin/);
  }
});
test('contract permits changed animation sampler bytes, not static nodes or skin topology', () => {
  const f = fixture(), contract = geometryFingerprint(f.doc, f.bin);
  const changed = structuredClone(f.doc), chunks = [Buffer.from(f.bin)];
  const time = append(changed, chunks, new Float32Array([0,1]), 'SCALAR', 5126);
  const value = append(changed, chunks, new Float32Array([0,0,0,1,0,1,0,0]), 'VEC4', 5126);
  changed.animations = [{name:'compact reaction recipe3', channels:[{sampler:0,target:{node:0,path:'rotation'}}], samplers:[{input:time,output:value}]}];
  const b = Buffer.concat(chunks);
  assert.doesNotThrow(() => assertGeometryContract(changed, b, contract));
  changed.skins[0].joints = [1];
  assert.throws(() => assertGeometryContract(changed, b, contract), /Geometry\/skin/);
});
test('unexpected degenerate bad corner cannot automatically use the approved source repair', () => {
  const f = fixture(), b = Buffer.from(f.bin), a = f.doc.accessors[f.primitive.attributes.NORMAL];
  const offset = f.doc.bufferViews[a.bufferView].byteOffset || 0;
  b.writeFloatLE(1, offset); b.writeFloatLE(0, offset + 8);
  assert.throws(() => generatePrimitive(f.doc, b, f.primitive, mikk), /Unapproved invalid tangent corner/);
});

test('publication gate checks strict corner and complete original JSON/BIN preservation', () => {
  const f = fixture({mirror:true}), made = assemble(f.doc, f.bin, mikk);
  const receipt = assertPreservation(f.doc, f.bin, made.doc, made.bin);
  assert.equal(receipt.pass, true); assert.equal(receipt.indexed_corner_attributes_exact, 25);
  const b = Buffer.from(made.bin); b[0] ^= 1;
  assert.throws(() => assertPreservation(f.doc, f.bin, made.doc, b), /original BIN prefix/);
  const changed = structuredClone(made.doc); changed.animations.push({name:'unexpected',channels:[],samplers:[]});
  assert.throws(() => assertPreservation(f.doc, f.bin, changed, made.bin), /animations/);
});
test('publication gate rejects added output-only vertices changing an indexed corner', () => {
  const f = fixture({mirror:true}), made = assemble(f.doc, f.bin, mikk);
  const p = made.doc.meshes[0].primitives[0], a = made.doc.accessors[p.attributes.POSITION];
  const offset = made.doc.bufferViews[a.bufferView].byteOffset || 0;
  const b = Buffer.from(made.bin); b.writeFloatLE(.01, offset);
  assert.throws(() => assertPreservation(f.doc, f.bin, made.doc, b), /indexed corner POSITION/);
});

test('short accessor views and illegal strides fail instead of silently zero-padding', () => {
  const f = fixture(), a = f.doc.accessors[f.primitive.attributes.POSITION];
  const changed = structuredClone(f.doc); changed.bufferViews[a.bufferView].byteLength -= 4;
  assert.throws(() => attributeBytes(changed, f.bin, f.primitive.attributes.POSITION), /exceeds declared/);
  changed.bufferViews[a.bufferView].byteLength += 4; changed.bufferViews[a.bufferView].byteStride = 4;
  assert.throws(() => attributeBytes(changed, f.bin, f.primitive.attributes.POSITION), /exceeds declared/);
});

test('approved JSON array witness matches exact float32 corner arrays without coercing values', () => {
  const doc={bufferViews:[],accessors:[],buffers:[{byteLength:0}]}, chunks=[];
  const p = new Float32Array([0,0,0,1,1,0,2,2,0]);
  const n = new Float32Array([0,0,1,0,0,1,Math.SQRT1_2,0,Math.SQRT1_2]);
  const uv = new Float32Array([0,0,1,0,2,0]);
  const primitive={attributes:{POSITION:append(doc,chunks,p,'VEC3',5126),NORMAL:append(doc,chunks,n,'VEC3',5126),TEXCOORD_0:append(doc,chunks,uv,'VEC2',5126)}};
  const fakeMikk={generateTangents:()=>new Float32Array([1,0,0,1,1,0,0,1,1,0,0,1])};
  const policy=[{corner:2,source_normal:Array.from(n.slice(6)),source_positions:[Array.from(p.slice(0,3)),Array.from(p.slice(3,6)),Array.from(p.slice(6))],source_uv:[[0,0],[1,0],[2,0]]}];
  const source=Buffer.concat(chunks), g=generatePrimitive(doc,source,primitive,fakeMikk,policy);
  assert.equal(g.audit.pass,true); assert.equal(g.audit.explicit_degenerate_corner_repairs.length,1);
  const changed=structuredClone(policy); changed[0].source_normal[0] += 1e-9;
  assert.throws(()=>generatePrimitive(doc,source,primitive,fakeMikk,changed),/source witness changed: source_normal/);
});
