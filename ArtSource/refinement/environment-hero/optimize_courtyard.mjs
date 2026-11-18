import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

// Offline only: npm install --prefix <tool-dir> meshoptimizer@1.1.1
// node optimize_courtyard.mjs <tool-dir>/node_modules/meshoptimizer <composition/courtyard_lantern_surface_ktx.glb> <output.glb>
const [moduleDir, source, destination] = process.argv.slice(2);
assert(moduleDir && source && destination && resolve(source) !== resolve(destination));
const pkg = JSON.parse(readFileSync(resolve(moduleDir, 'package.json')));
assert.equal(pkg.name + '@' + pkg.version, 'meshoptimizer@1.1.1');
const { MeshoptSimplifier } = await import(pathToFileURL(resolve(moduleDir, pkg.main)));
await MeshoptSimplifier.ready;
const sourceBytes = readFileSync(source);
assert.equal(createHash('sha256').update(sourceBytes).digest('hex'), 'c7f2e2b2833cdd84fbc73918fdcd2f9036dee582a46c29d8db67df806e77fc78');
const jsonEnd = 20 + sourceBytes.readUInt32LE(12);
const doc = JSON.parse(sourceBytes.toString('utf8', 20, jsonEnd));
const bin = sourceBytes.subarray(jsonEnd + 8);
const rawViews = doc.bufferViews.map(view => bin.subarray(view.byteOffset || 0, (view.byteOffset || 0) + view.byteLength));
const dimensions = { VEC2: 2, VEC3: 3, VEC4: 4, SCALAR: 1 };
const arrays = { 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };
const original = structuredClone(doc);
const outputAccessors = [], outputViews = [], outputChunks = [];
let written = 0;
function appendView(bytes, target) {
    const pad = (4 - written % 4) % 4;
    outputChunks.push(Buffer.alloc(pad), bytes);
    written += pad;
    const view = {buffer: 0, byteOffset: written, byteLength: bytes.length};
    if (target !== undefined) view.target = target;
    written += bytes.length;
    return outputViews.push(view) - 1;
}
function values(index) {
    const acc = original.accessors[index], bytes = rawViews[acc.bufferView];
    const ArrayType = arrays[acc.componentType];
    assert(!acc.sparse && !acc.byteOffset && !original.bufferViews[acc.bufferView].byteStride);
    assert.equal(acc.count * dimensions[acc.type] * ArrayType.BYTES_PER_ELEMENT, bytes.length);
    return new ArrayType(bytes.buffer, bytes.byteOffset, acc.count * dimensions[acc.type]);
}
function storeAccessor(index, data) {
    const acc = structuredClone(original.accessors[index]);
    const bytes = Buffer.from(data.buffer, data.byteOffset, data.byteLength);
    const width = dimensions[acc.type];
    acc.count = data.length / width;
    for (const bound of ['min','max']) {
        if (!(bound in acc)) continue;
        const reduce = Math[bound];
        const limit = bound === 'min' ? Infinity : -Infinity;
        acc[bound] = Array(width).fill(limit);
        for (let i = 0; i < data.length; ++i) acc[bound][i % width] = reduce(acc[bound][i % width], data[i]);
    }
    acc.bufferView = appendView(bytes, original.bufferViews[acc.bufferView].target);
    return outputAccessors.push(acc) - 1;
}
const copied = new Map();
function copy(index) {
    if (!copied.has(index)) copied.set(index, storeAccessor(index, values(index)));
    return copied.get(index);
}
const distant = /^(EH_(EastRoof|WestRoof|TavernMainRoof|TavernPorchRoof|TownLowerEave|TownRoof|SideGalleryWindows)|Facade_(SharedGroundWindowCore|UpperWindowCore|BatchedTileEnds))/;
let outTriangles = 0, inTriangles = 0, worst = 0;
for (const [mi, mesh] of doc.meshes.entries()) {
    const instances = doc.nodes.filter(node => node.mesh === mi).length;
    for (const prim of mesh.primitives) {
        const attrs = prim.attributes, verts = values(attrs.POSITION);
        const inputIndices = values(prim.indices);
        const sourceCount = inputIndices.length;
        inTriangles += instances * sourceCount / 3;
        let indices;
        if (distant.test(mesh.name) && sourceCount >= 450) {
            const norm = values(attrs.NORMAL), uv = values(attrs.TEXCOORD_0);
            const attributes = new Float32Array(verts.length / 3 * 5);
            for (let i = 0; i < verts.length / 3; ++i) {
                attributes.set(norm.subarray(3*i, 3*i+3), 5*i);
                attributes.set(uv.subarray(2*i, 2*i+2), 5*i+3);
            }
            const limit = mesh.name.startsWith('Facade_') ? .003 : .007;
            const [candidate, error] = MeshoptSimplifier.simplifyWithAttributes(
                Uint32Array.from(inputIndices), verts, 3, attributes, 5, [.025,.025,.025,.03,.03],
                null, 3*Math.max(1, Math.floor(sourceCount*.45/3)), limit, ['ErrorAbsolute','Permissive']);
            if (candidate.length < sourceCount && candidate.length >= 3) {
                indices = candidate; worst = Math.max(worst,error);
            }
        }
        if (!indices) {
            prim.indices = copy(prim.indices);
            for (const name in attrs) attrs[name] = copy(attrs[name]);
            outTriangles += instances * sourceCount / 3;
            continue;
        }
        outTriangles += instances * indices.length / 3;
        const [remap, vertexCount] = MeshoptSimplifier.compactMesh(indices);
        prim.indices = storeAccessor(prim.indices, new inputIndices.constructor(indices));
        for (const [name, index] of Object.entries(attrs)) {
            const old = values(index), width = dimensions[original.accessors[index].type];
            const packed = new old.constructor(vertexCount * width);
            for (let i = 0; i < remap.length; ++i) {
                if (remap[i] < vertexCount) packed.set(old.subarray(i*width,(i+1)*width),remap[i]*width);
            }
            attrs[name] = storeAccessor(index, packed);
        }
    }
}
for (const image of doc.images) image.bufferView = appendView(rawViews[image.bufferView]);
doc.accessors = outputAccessors;
doc.bufferViews = outputViews;
doc.buffers = [{byteLength: written}];
const json = Buffer.from(JSON.stringify(doc)), jsonPad = (4 - json.length % 4) % 4;
const binPad = (4 - written % 4) % 4, binSize = written + binPad;
const header = Buffer.alloc(20), binHeader = Buffer.alloc(8);
header.write('glTF'); header.writeUInt32LE(2,4);
header.writeUInt32LE(28 + json.length + jsonPad + binSize,8);
header.writeUInt32LE(json.length + jsonPad,12); header.write('JSON',16);
binHeader.writeUInt32LE(binSize); binHeader.write('BIN\0',4);
writeFileSync(destination, Buffer.concat([header,json,Buffer.alloc(jsonPad,0x20),binHeader,...outputChunks,Buffer.alloc(binPad)]));
console.log(JSON.stringify({inTriangles,outTriangles,sourceBytes:sourceBytes.length,outputBytes:header.readUInt32LE(8),maxSimplificationError:worst}));
