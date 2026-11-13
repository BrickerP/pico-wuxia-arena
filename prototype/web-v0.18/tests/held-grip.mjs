import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
const begin = html.indexOf('function renderFreeHand(');
const end = html.indexOf('\nwindow.wuxiaFirstPerson', begin);
assert(begin >= 0 && end > begin);
const source = html.slice(begin, end).trim();
assert(source.endsWith('}'));
const response = await fetch('https://raw.githubusercontent.com/mrdoob/three.js/r147/build/three.module.js', {
  signal: AbortSignal.timeout(15000),
});
assert(response.ok);
const THREE = await import('data:text/javascript;base64,' + Buffer.from(await response.text()).toString('base64'));
assert.equal(THREE.REVISION, '147');
const V = (...args) => new THREE.Vector3(...args);
const Q = () => new THREE.Quaternion();

function render(equipped, weaponHand, grips, error = null) {
  const calls = [];
  const hands = { update: (side, matrix, closed, anchor) => calls.push({ side, closed, anchor }), audit: () => ({}) };
  const visuals = { hands, error };
  const visual = { root: new THREE.Group() };
  for (const key of ['gripMarker', 'baseMarker', 'tipMarker']) {
    visual[key] = new THREE.Object3D();
    visual.root.add(visual[key]);
  }
  visual.root.userData.bladeParts = 5;
  const camera = new THREE.PerspectiveCamera();
  camera.position.y = 1.6;
  const pose = { base: V(.1, 1.4, -.4), tip: V(.1, 1.4, -1.24) };
  const run = new Function('firstPersonVisuals', 'daoTemplate', 'actor', 'scene',
    'ensureFirstPersonWeapon', 'goalQ', 'camera', 'Q', 'V', 'equipped', 'weaponHand',
    'weaponId', 'mouse', 'grips', 'currentP', 'window', 'THREE', 'ASSET_SHA',
    'failFirstPersonPresentation', 'clamp', source + ';return renderFreeHand(currentP);');
  const before = { ...grips };
  const result = run(visuals, {}, {}, new THREE.Scene(), () => visual, Q, camera, Q, V,
    equipped, weaponHand, 'dao', { x: 0, y: 0 }, grips, pose, {}, THREE, { dao: 'source' },
    failure => { throw failure; }, (value, lo, hi) => Math.max(lo, Math.min(hi, value)));
  assert.deepEqual(grips, before, 'Presentation must not change guard input');
  return { calls, result };
}

for (const side of ['R', 'L']) {
  const { calls, result } = render(true, side, { R: false, L: false });
  assert.equal(result, true);
  assert.equal(calls.find(call => call.side === side).closed, true, 'Equipped hand holds its weapon without K');
  assert.equal(calls.find(call => call.side !== side).closed, false, 'Unoccupied hand remains relaxed');
  assert.equal(calls.find(call => call.side === side).anchor, 'grip');
}
assert(render(false, 'R', { R: false, L: false }).calls.every(call => !call.closed));
assert.equal(render(false, 'R', { R: true, L: false }).calls.find(call => call.side === 'R').closed, true);
assert.equal(render(true, 'R', { R: false, L: false }, new Error('locked')).result, false);
assert.equal(render(true, 'R', { R: false, L: false }, new Error('locked')).calls.length, 0);
console.log('Held hand, both sides, unarmed and fault boundaries passed; guard input unchanged.');
