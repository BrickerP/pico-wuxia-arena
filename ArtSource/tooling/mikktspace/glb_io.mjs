import fs from 'node:fs';
import crypto from 'node:crypto';

export const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const widths = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
const sizes = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 };
export function readGLB(path) {
  const file = fs.readFileSync(path);
  if (file.length < 28) throw Error('Truncated GLB');
  if (file.readUInt32LE(0) !== 0x46546c67 || file.readUInt32LE(4) !== 2 || file.readUInt32LE(8) !== file.length) throw Error('Invalid GLB');
  const n = file.readUInt32LE(12);
  if (n % 4 || 28 + n > file.length) throw Error('Invalid GLB JSON length');
  if (file.readUInt32LE(16) !== 0x4e4f534a || file.readUInt32LE(24 + n) !== 0x004e4942) throw Error('Expected embedded JSON/BIN');
  const doc = JSON.parse(file.subarray(20, 20 + n));
  if (doc.buffers.length !== 1 || doc.buffers[0].uri) throw Error('One embedded buffer required');
  const binaryLength = file.readUInt32LE(20 + n), declaredLength = doc.buffers[0].byteLength;
  if (binaryLength % 4 || 28 + n + binaryLength !== file.length || !Number.isSafeInteger(declaredLength)
      || declaredLength < 0 || declaredLength > binaryLength || binaryLength - declaredLength > 3) throw Error('Invalid GLB BIN length');
  return { doc, bin: file.subarray(28 + n), file };
}
export function attributeBytes(doc, bin, id) {
  const a = doc.accessors[id];
  if (!a || !Number.isSafeInteger(a.count) || a.count <= 0 || !widths[a.type] || !sizes[a.componentType]) throw Error('Invalid accessor metadata');
  const v = doc.bufferViews[a.bufferView];
  if (!v || v.buffer !== 0 || !Number.isSafeInteger(v.byteLength) || v.byteLength < 0) throw Error('Invalid accessor buffer view');
  if (a.sparse) throw Error('Sparse input requires an explicit preservation implementation');
  const rowSize = widths[a.type] * sizes[a.componentType], output = Buffer.alloc(a.count * rowSize);
  const viewOffset = v.byteOffset || 0, relativeOffset = a.byteOffset || 0;
  const offset = viewOffset + relativeOffset, stride = v.byteStride || rowSize;
  if (![viewOffset, relativeOffset, stride].every(Number.isSafeInteger) || viewOffset < 0 || relativeOffset < 0 || stride < rowSize
      || viewOffset + v.byteLength > bin.length || relativeOffset + (a.count - 1) * stride + rowSize > v.byteLength) throw Error('Accessor exceeds declared buffer view');
  for (let i = 0; i < a.count; i++) bin.copy(output, i * rowSize, offset + i * stride, offset + i * stride + rowSize);
  return output;
}
export function values(doc, bin, id) {
  const a = doc.accessors[id], b = attributeBytes(doc, bin, id), count = a.count * widths[a.type], out = [];
  const readers = { 5121: ['readUInt8', 1], 5123: ['readUInt16LE', 2], 5125: ['readUInt32LE', 4], 5126: ['readFloatLE', 4] };
  if (!readers[a.componentType] || a.normalized) throw Error('Unexpected normalized/packed source accessor');
  const [read, size] = readers[a.componentType];
  for (let i = 0; i < count; i++) out.push(b[read](i * size));
  return out;
}
export function append(doc, chunks, array, type, componentType, target = 34962) {
  let length = chunks.reduce((n, b) => n + b.length, 0);
  const pad = (-length) & 3;
  if (pad) { chunks.push(Buffer.alloc(pad)); length += pad; }
  const bytes = Buffer.isBuffer(array) ? array : Buffer.from(array.buffer, array.byteOffset, array.byteLength);
  const view = doc.bufferViews.length;
  doc.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: bytes.length, target });
  chunks.push(bytes);
  const accessor = { bufferView: view, componentType, type, count: bytes.length / (widths[type] * sizes[componentType]) };
  const id = doc.accessors.length; doc.accessors.push(accessor);
  return id;
}
export function encodeGLB(doc, bin) {
  doc.buffers[0].byteLength = bin.length;
  let json = Buffer.from(JSON.stringify(doc));
  json = Buffer.concat([json, Buffer.alloc((-json.length) & 3, 0x20)]);
  const padded = Buffer.concat([bin, Buffer.alloc((-bin.length) & 3)]), header = Buffer.alloc(20), chunk = Buffer.alloc(8);
  header.writeUInt32LE(0x46546c67, 0); header.writeUInt32LE(2, 4); header.writeUInt32LE(28 + json.length + padded.length, 8);
  header.writeUInt32LE(json.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
  chunk.writeUInt32LE(padded.length, 0); chunk.writeUInt32LE(0x004e4942, 4);
  return Buffer.concat([header, json, chunk, padded]);
}
export function expanded(source, indices, width) {
  const out = new Float32Array(indices.length * width);
  for (let i = 0; i < indices.length; i++) for (let j = 0; j < width; j++) out[i * width + j] = source[indices[i] * width + j];
  return out;
}
