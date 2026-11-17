import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../../../..');
const require=createRequire(import.meta.url);
const validator=require(path.join(root,'ArtSource/refinement/pbr-compression/tooling/gltf-validator/node_modules/gltf-validator'));
const rows=[],warningSets={};
const inputs=[
  ['baseline_png',path.join(root,'ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_png.glb')],
  ['baseline_ktx',path.join(root,'ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_ktx.glb')],
  ['png',path.join(here,'courtyard_entry_finish_png.glb')],
  ['ktx',path.join(here,'courtyard_entry_finish_ktx.glb')],
];
for(const [label,file] of inputs) {
  const report=await validator.validateBytes(new Uint8Array(fs.readFileSync(file)),{uri:path.basename(file),maxIssues:0,writeTimestamp:false});
  fs.writeFileSync(path.join(here,'review',`${label}_gltf_validator.json`),JSON.stringify(report,null,2)+'\n');
  const missing=report.issues.messages.filter(m=>m.code==='MESH_PRIMITIVE_GENERATED_TANGENT_SPACE'&&m.pointer.startsWith('/meshes/41/'));
  const codes={};for(const issue of report.issues.messages)codes[issue.code]=(codes[issue.code]??0)+1;
  warningSets[label]=JSON.stringify(report.issues.messages.filter(m=>m.severity===1).map(m=>[m.code,m.pointer,m.message]).sort());
  rows.push({label,errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos,new_timber_missing_TBN:missing.length,codes});
}
const inheritedWarningsExact=warningSets.png===warningSets.baseline_png&&warningSets.ktx===warningSets.baseline_ktx;
const summary={validator_version:validator.version(),models:rows,baseline_warning_fingerprints_exact:inheritedWarningsExact};
fs.writeFileSync(path.join(here,'review/gltf_summary.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary));
if(rows.some(r=>r.errors||r.new_timber_missing_TBN)||!inheritedWarningsExact)process.exitCode=1;
