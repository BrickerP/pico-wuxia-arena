import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { sha, readGLB, attributeBytes, values, append, encodeGLB, expanded } from './glb_io.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
// The pinned self-contained WASM module and original licenses ship with this tool.
export const MIKK_PATH = path.join(HERE, 'mikktspace.mjs');
export const CONTRACT_PATH = path.join(HERE, 'geometry_contract.json');
export const POLICY_PATH = path.join(HERE, 'degenerate_policy.json');
export const MIKK_SHA = 'f415ebd2f7bbe4ac06439be40d2ca4a11bb17123009bb33582176b1b21a14dac';
export async function loadMikk(modulePath = MIKK_PATH) {
  if (sha(fs.readFileSync(modulePath)) !== MIKK_SHA) throw Error('Existing Mikk module identity changed');
  const mikk = await import(pathToFileURL(modulePath));
  await mikk.ready;
  if (!mikk.isReady) throw Error('Mikk WASM is not ready');
  return mikk;
}
function vector(a, i, width = 3) { return a.slice(i * width, i * width + width); }
function dot(a, b) { return a.reduce((sum, v, i) => sum + v * b[i], 0); }
function cross(a, b) { return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }
function unit(a) { const length = Math.hypot(...a); if (!(length > 1e-20)) throw Error('Undefined direction'); return a.map(v => v / length); }
function unusedBasis(n) {
  const axis = [0,0,0]; axis[n.map(Math.abs).indexOf(Math.min(...n.map(Math.abs)))] = 1;
  return [...unit(cross(axis, n)), 1];
}
export function inspectCorners(positions, normals, uvs, tangents) {
  if (positions.length % 9 || normals.length !== positions.length || uvs.length * 3 !== positions.length * 2 || tangents.length * 3 !== positions.length * 4) throw Error('Malformed corner attributes');
  let unitError = 0, normalError = 0, orthogonalError = 0, uvDegenerate = 0, geometricDegenerate = 0, mirrored = 0;
  const bad = [], degenerateFaces = [];
  for (let i = 0; i < positions.length / 3; i++) {
    const n = vector(normals, i), t = vector(tangents, i, 4), length = Math.hypot(...t.slice(0,3)), nd = Math.abs(dot(n, t));
    unitError = Math.max(unitError, Math.abs(length - 1)); normalError = Math.max(normalError, Math.abs(Math.hypot(...n) - 1)); orthogonalError = Math.max(orthogonalError, nd);
    if (![...n,...t].every(Number.isFinite) || Math.abs(length - 1) > 2e-5 || nd > 2e-5 || Math.abs(t[3]) !== 1) bad.push(i);
  }
  for (let face = 0; face < positions.length / 9; face++) {
    const p = [0,1,2].map(i => vector(positions, face*3+i)), uv = [0,1,2].map(i => vector(uvs, face*3+i,2));
    const d = (uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0]);
    const edge = i => p[i].map((v,k) => v-p[0][k]);
    if (d === 0) { uvDegenerate++; degenerateFaces.push(face); }
    if (Math.hypot(...cross(edge(1),edge(2))) === 0) geometricDegenerate++;
    if (d < 0) mirrored++;
  }
  return { corners: positions.length/3, maximum_unit_error: unitError, maximum_source_normal_error: normalError, maximum_abs_normal_dot_tangent: orthogonalError,
    exact_zero_UV_faces: uvDegenerate, exact_zero_geometric_faces: geometricDegenerate, mirrored_UV_faces: mirrored,
    degenerate_UV_face_ids: degenerateFaces, bad_corner_count: bad.length, first_bad_corners: bad.slice(0,30), pass: bad.length === 0 && normalError <= 2e-5 };
}
export function repairDegenerateCorner(positions,normals,uvs,tangents,corner) {
  const face=Math.floor(corner/3), p=[0,1,2].map(i=>vector(positions,face*3+i)), uv=[0,1,2].map(i=>vector(uvs,face*3+i,2)), n=vector(normals,corner);
  const determinant=(uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[1][1]-uv[0][1])*(uv[2][0]-uv[0][0]);
  if (determinant!==0) throw Error('Only an exact degenerate-UV corner may be repaired');
  const edges=[];
  for (const [a,b] of [[0,1],[1,2],[2,0]]) {
    const du=uv[b][0]-uv[a][0];if(du===0)continue;
    const derivative=p[b].map((v,k)=>(v-p[a][k])/du), projected=derivative.map((v,k)=>v-dot(derivative,n)*n[k]);
    if (!(Math.hypot(...projected)>1e-6*Math.hypot(...derivative))) throw Error('Degenerate +U edge is nearly parallel to source N');
    edges.push({corners:[a,b],delta_u:du,positive_u_derivative:derivative,projected_unit:unit(projected)});
  }
  if (!edges.length) throw Error('Degenerate UV has no nonzero +U edge');
  edges.sort((a,b)=>Math.abs(b.delta_u)-Math.abs(a.delta_u));
  const direction=edges[0].projected_unit;
  if(edges.some(edge=>dot(direction,edge.projected_unit)<1-1e-6)) throw Error('Degenerate +U edges do not define one stable direction');
  const previous=Array.from(tangents.slice(corner*4,corner*4+4));
  for(let k=0;k<3;k++)tangents[corner*4+k]=direction[k];
  return {corner,face,source_normal:n,source_positions:p,source_uv:uv,UV_determinant:determinant,old_glTF_mikk_tangent:previous,new_tangent:Array.from(tangents.slice(corner*4,corner*4+4)),chosen_edge:edges[0],all_projected_U_edges:edges,handedness_unchanged:tangents[corner*4+3]===previous[3],policy:'Root-approved exact-zero-UV corner only; maximum-|dU| source edge projected to original N, no averaging'};
}
export function generatePrimitive(doc, bin, primitive, mikk, approvedRepairs = []) {
  if (primitive.mode !== undefined && primitive.mode !== 4) throw Error('Only triangle primitives are admitted');
  if (primitive.targets?.length || primitive.attributes.TANGENT !== undefined) throw Error('Morph/existing tangent requires a separate explicit contract');
  for (const key of ['POSITION','NORMAL','TEXCOORD_0']) if (primitive.attributes[key] === undefined) throw Error('Missing '+key);
  const p = values(doc,bin,primitive.attributes.POSITION), n = values(doc,bin,primitive.attributes.NORMAL), uv = values(doc,bin,primitive.attributes.TEXCOORD_0);
  const count = p.length/3, indices = primitive.indices === undefined ? Array.from({length:count},(_,i)=>i) : values(doc,bin,primitive.indices);
  if (indices.length % 3 || indices.some(i=>!Number.isInteger(i)||i<0||i>=count)) throw Error('Invalid source triangle indices');
  if (![...p,...n,...uv].every(Number.isFinite) || n.length!==p.length || uv.length!==count*2) throw Error('Malformed/nonfinite source attributes');
  const cp=expanded(p,indices,3), cn=expanded(n,indices,3), cuv=expanded(uv,indices,2);
  const tangents = mikk.generateTangents(cp,cn,cuv);
  for (let i=3;i<tangents.length;i+=4) tangents[i]*=-1; // Official glTF convention, not a mesh/world rotation.
  const pureAudit=inspectCorners(cp,cn,cuv,tangents),repairs=[];
  if (pureAudit.bad_corner_count !== pureAudit.first_bad_corners.length) throw Error('Too many invalid tangent corners');
  for (const corner of pureAudit.first_bad_corners) {
    const approved = approvedRepairs.find(row => row.corner === corner);
    if (!approved) throw Error('Unapproved invalid tangent corner ' + corner);
    const face = Math.floor(corner / 3);
    const actual = {
      source_normal: Array.from(vector(cn, corner)),
      source_positions: [0,1,2].map(i => Array.from(vector(cp, face * 3 + i))),
      source_uv: [0,1,2].map(i => Array.from(vector(cuv, face * 3 + i, 2))),
    };
    for (const key of Object.keys(actual)) {
      if (JSON.stringify(actual[key]) !== JSON.stringify(approved[key])) throw Error('Approved degenerate source witness changed: ' + key);
    }
    repairs.push({...repairDegenerateCorner(cp,cn,cuv,tangents,corner),source_vertex:indices[corner]});
  }
  const audit={...inspectCorners(cp,cn,cuv,tangents),pure_mikk_bad_corner_count:pureAudit.bad_corner_count,explicit_degenerate_corner_repairs:repairs}, groups = Array.from({length:count},()=>new Map()), origin=Array.from({length:count},(_,i)=>i), remapped=[];
  const rows=Array.from({length:count},(_,i)=>unusedBasis(vector(n,i)));
  let used=0;
  for (let corner=0;corner<indices.length;corner++) {
    const old=indices[corner], t=tangents.slice(corner*4,corner*4+4), key=Buffer.from(t.buffer,t.byteOffset,16).toString('hex'), group=groups[old];
    if (!group.has(key)) {
      const index=group.size ? origin.length : old;
      if (!group.size) used++;
      if (index===origin.length) { origin.push(old); rows.push([...t]); } else rows[index]=[...t];
      group.set(key,index);
    }
    remapped.push(group.get(key));
  }
  const stored=new Float32Array(rows.flat());
  for (let corner=0;corner<indices.length;corner++) for(let k=0;k<4;k++) if (!Object.is(stored[remapped[corner]*4+k],tangents[corner*4+k])) throw Error('Mikk corner result changed while indexing');
  return { audit, indices, remapped, origin, tangents:stored, sourceCount:count, usedCount:used, splitCount:origin.length-count };
}
// Hash the rendered corner stream, not storage row/index identities. Tangent seam
// splits and unused source rows cannot change this static geometry/skin contract.
export function geometryFingerprint(doc, bin) {
  const body = doc.meshes?.[0]?.extras?.body_primitive_indices;
  if (JSON.stringify(body) !== '[0,1,2,3,4]') throw Error('Frozen five-body primitive interface changed');
  const record = {
    schema: 'pico-indexed-corner-static-contract-v1',
    nodes: doc.nodes,
    skins: doc.skins.map(skin => {
      const { inverseBindMatrices, ...rest } = skin;
      return { ...rest, IBM: inverseBindMatrices === undefined ? null : sha(attributeBytes(doc, bin, inverseBindMatrices)) };
    }),
    scenes: doc.scenes, scene: doc.scene,
    materials: doc.materials, textures: doc.textures, samplers: doc.samplers,
    images: doc.images.map(image => {
      if (image.uri || image.bufferView === undefined) throw Error('Embedded images required');
      const view = doc.bufferViews[image.bufferView], offset = view.byteOffset || 0;
      if (offset < 0 || offset + view.byteLength > bin.length) throw Error('Invalid image view');
      const { bufferView, ...description } = image;
      return { ...description, sha256: sha(bin.subarray(offset, offset + view.byteLength)) };
    }),
    meshes: doc.meshes.map(mesh => {
      const { primitives, ...description } = mesh;
      return { ...description, primitives: primitives.map(primitive => {
        const position = doc.accessors[primitive.attributes.POSITION];
        const indices = primitive.indices === undefined
          ? Array.from({length: position.count}, (_, i) => i)
          : values(doc, bin, primitive.indices);
        if ((primitive.mode ?? 4) !== 4 || indices.length % 3 || indices.some(i => !Number.isInteger(i) || i < 0 || i >= position.count)) throw Error('Invalid triangle contract');
        if (primitive.targets?.length) throw Error('Morphs require an explicit contract');
        const { attributes, indices: ignoredIndex, ...metadata } = primitive;
        return {
          ...metadata, mode: primitive.mode ?? 4,
          corners: indices.length,
          attributes: Object.fromEntries(Object.keys(attributes).filter(key => key !== 'TANGENT').sort().map(key => {
            const id = attributes[key], accessor = doc.accessors[id], bytes = attributeBytes(doc, bin, id);
            if (accessor.count !== position.count) throw Error('Contract vertex counts differ');
            const size = bytes.length / accessor.count, corners = Buffer.alloc(indices.length * size);
            indices.forEach((index, corner) => bytes.copy(corners, corner * size, index * size, (index + 1) * size));
            return [key, { type: accessor.type, componentType: accessor.componentType,
              normalized: accessor.normalized ?? false, sha256: sha(corners) }];
          })),
        };
      }) };
    }),
  };
  return { sha256: sha(JSON.stringify(record)), record };
}
export function assertGeometryContract(doc, bin, contract) {
  const actual = geometryFingerprint(doc, bin);
  if (contract.record?.schema !== 'pico-indexed-corner-static-contract-v1' || contract.sha256 !== actual.sha256) throw Error('Geometry/skin/material/static-frame interface changed');
  return actual;
}
export function assemble(doc,bin,mikk,repairPolicy = []) {
  const result=structuredClone(doc), chunks=[bin], mapping=[], reports=[];
  for (const index of doc.meshes[0].extras.body_primitive_indices) {
    const before=doc.meshes[0].primitives[index], material=doc.materials[before.material];
    if (!material.normalTexture || (material.normalTexture.texCoord||0)!==0 || material.normalTexture.extensions) throw Error('Normal-map UV0 contract changed');
    if (/Steel|DAO|Blade/i.test(material.name||'')) throw Error('Weapon primitive entered target domain');
    const generated=generatePrimitive(doc,bin,before,mikk,repairPolicy.filter(row => row.primitive === index)), after=result.meshes[0].primitives[index];
    reports.push({primitive:index,material:material.name,...generated.audit,original_vertices:generated.sourceCount,referenced_vertices:generated.usedCount,unreferenced_vertices_preserved:generated.sourceCount-generated.usedCount,split_vertices:generated.splitCount});
    mapping.push({primitive:index,vertex_origin:generated.origin});
    if (generated.splitCount) {
      for (const [key,id] of Object.entries(before.attributes)) {
        const a=doc.accessors[id], original=attributeBytes(doc,bin,id), rowSize=original.length/a.count;
        if (a.count!==generated.sourceCount) throw Error('Attribute vertex counts differ');
        const rows=Buffer.alloc(generated.origin.length*rowSize);
        generated.origin.forEach((old,i)=>original.copy(rows,i*rowSize,old*rowSize,(old+1)*rowSize));
        const next=append(result,chunks,rows,a.type,a.componentType);
        result.accessors[next]={...structuredClone(a),bufferView:result.accessors[next].bufferView,byteOffset:0,count:generated.origin.length};
        after.attributes[key]=next;
      }
      after.indices=append(result,chunks,new Uint32Array(generated.remapped),'SCALAR',5125,34963);
    }
    after.attributes.TANGENT=append(result,chunks,generated.tangents,'VEC4',5126);
  }
  return {doc:result,bin:Buffer.concat(chunks),mapping,reports,pass:reports.every(r=>r.pass)};
}
// Publication gate independent of source hash pinning: the operation may add
// storage rows/TANGENT only, never change an existing rendered corner or clip.
export function assertPreservation(beforeDoc, beforeBin, afterDoc, afterBin) {
  const sameJSON = (a, b, label) => {
    if (JSON.stringify(a) !== JSON.stringify(b)) throw Error('Preservation failed: ' + label);
  };
  if (!afterBin.subarray(0, beforeBin.length).equals(beforeBin)) throw Error('Preservation failed: original BIN prefix');
  sameJSON(Object.keys(beforeDoc).sort(), Object.keys(afterDoc).sort(), 'root property set');
  for (const key of Object.keys(beforeDoc)) {
    if (!['buffers', 'bufferViews', 'accessors', 'meshes'].includes(key)) sameJSON(beforeDoc[key], afterDoc[key], key);
  }
  sameJSON(beforeDoc.accessors, afterDoc.accessors.slice(0, beforeDoc.accessors.length), 'original accessors');
  sameJSON(beforeDoc.bufferViews, afterDoc.bufferViews.slice(0, beforeDoc.bufferViews.length), 'original bufferViews');
  if (beforeDoc.meshes.length !== afterDoc.meshes.length) throw Error('Preservation failed: mesh count');
  let cornerAttributes = 0, cornerRows = 0, animationAccessors = 0;
  const indexedBytes = (doc, bin, primitive, key) => {
    const count = doc.accessors[primitive.attributes.POSITION].count;
    const indices = primitive.indices === undefined ? Array.from({length:count}, (_, i) => i) : values(doc, bin, primitive.indices);
    const id = primitive.attributes[key], source = attributeBytes(doc, bin, id);
    const size = source.length / doc.accessors[id].count, bytes = Buffer.alloc(indices.length * size);
    indices.forEach((index, corner) => source.copy(bytes, corner * size, index * size, (index + 1) * size));
    return { bytes, rows: indices.length };
  };
  beforeDoc.meshes.forEach((mesh, meshIndex) => {
    const afterMesh = afterDoc.meshes[meshIndex], {primitives, ...description} = mesh;
    const {primitives: afterPrimitives, ...afterDescription} = afterMesh;
    sameJSON(description, afterDescription, 'mesh metadata');
    if (primitives.length !== afterPrimitives.length) throw Error('Preservation failed: primitive count');
    primitives.forEach((primitive, index) => {
      const next = afterPrimitives[index];
      const {attributes, indices, ...metadata} = primitive;
      const {attributes: nextAttributes, indices: nextIndices, ...nextMetadata} = next;
      sameJSON(metadata, nextMetadata, 'primitive metadata');
      const targeted = meshIndex === 0 && mesh.extras.body_primitive_indices.includes(index);
      if (!targeted) sameJSON(primitive, next, 'untargeted primitive');
      const expectedKeys = Object.keys(attributes).concat(targeted ? ['TANGENT'] : []).sort();
      sameJSON(expectedKeys, Object.keys(nextAttributes).sort(), 'attribute set');
      for (const key of Object.keys(attributes)) {
        const a = indexedBytes(beforeDoc, beforeBin, primitive, key);
        const b = indexedBytes(afterDoc, afterBin, next, key);
        if (!a.bytes.equals(b.bytes)) throw Error('Preservation failed: indexed corner ' + key);
        cornerAttributes++; cornerRows += a.rows;
      }
    });
  });
  for (const animation of beforeDoc.animations || []) {
    for (const sampler of animation.samplers) {
      for (const id of [sampler.input, sampler.output]) {
        if (!attributeBytes(beforeDoc, beforeBin, id).equals(attributeBytes(afterDoc, afterBin, id))) throw Error('Preservation failed: animation sampler bytes');
        animationAccessors++;
      }
    }
  }
  if (geometryFingerprint(beforeDoc, beforeBin).sha256 !== geometryFingerprint(afterDoc, afterBin).sha256) throw Error('Preservation failed: static contract');
  return { pass: true, original_BIN_prefix_exact: true, root_JSON_except_appended_storage_exact: true,
    original_accessors_and_views_exact: true, mesh_and_primitive_metadata_exact: true,
    indexed_corner_attributes_exact: cornerAttributes, indexed_attribute_corner_rows_checked: cornerRows,
    nodes_skins_animations_images_materials_JSON_exact: true,
    animation_sampler_accessors_exact: animationAccessors,
    static_indexed_corner_contract_exact: true };
}
async function main() {
  if (process.argv.length !== 5) throw Error('Usage: node build_tangents.mjs INPUT.glb OUTPUT.glb REPORT_DIRECTORY');
  const input = path.resolve(process.argv[2]), output = path.resolve(process.argv[3]);
  const reportDirectory = path.resolve(process.argv[4]);
  if (input === output) throw Error('Input and output must differ');
  const source = readGLB(input);
  const contract = JSON.parse(fs.readFileSync(CONTRACT_PATH, 'utf8'));
  const fingerprint = assertGeometryContract(source.doc, source.bin, contract);
  const policy = JSON.parse(fs.readFileSync(POLICY_PATH, 'utf8'));
  if (policy.schema !== 'pico-explicit-degenerate-uv-corners-v1') throw Error('Unknown degenerate policy');
  const mikk = await loadMikk(), made = assemble(source.doc, source.bin, mikk, policy.repairs);
  const preservation = assertPreservation(source.doc, source.bin, made.doc, made.bin);
  const repairCount = made.reports.reduce((sum, row) => sum + row.explicit_degenerate_corner_repairs.length, 0);
  const report = {
    status: made.pass ? 'PASS' : 'FAILED_TANGENT_FRAME_GATE',
    input: { file: input, sha256: sha(source.file) },
    geometry_contract_sha256: fingerprint.sha256,
    algorithm: `MikkTSpace + ${repairCount} explicit source-validated degenerate UV corner`,
    generator: { name: 'Three0.185.1 bundled MikkTSpace WASM', module_sha256: MIKK_SHA,
      glTF_w_conversion: 'negate Mikk W exactly, per official API',
      space: 'mesh-local P/N/UV of prepared PNG; scene normalization retained' },
    primitives: made.reports,
    preservation,
  };
  fs.mkdirSync(reportDirectory, { recursive: true });
  const json = value => JSON.stringify(value, (_, v) => ArrayBuffer.isView(v) ? Array.from(v) : v, 2) + '\n';
  const save = () => fs.writeFileSync(path.join(reportDirectory, 'generation.json'), json(report));
  save();
  if (!made.pass) throw Error('Mikk output contains invalid frames; diagnostic saved, no GLB published');
  if (geometryFingerprint(made.doc, made.bin).sha256 !== fingerprint.sha256) throw Error('Tangent assembly changed static corner contract');
  const data = encodeGLB(made.doc, made.bin);
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, data);
  fs.writeFileSync(path.join(reportDirectory, 'vertex_origin.json'), JSON.stringify(made.mapping) + '\n');
  report.output = { file: output, sha256: sha(data), bytes: data.length };
  save();
  console.log(JSON.stringify({ status: report.status, output: report.output,
    geometry_contract_sha256: fingerprint.sha256,
    primitives: made.reports.map(({primitive,split_vertices,bad_corner_count}) => ({primitive,split_vertices,bad_corner_count})) }, null, 2));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
