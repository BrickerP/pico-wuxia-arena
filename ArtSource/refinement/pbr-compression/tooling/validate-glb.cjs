#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const validator = require('./gltf-validator/node_modules/gltf-validator');

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output || process.argv.length !== 4) {
    throw new Error('Usage: node tooling/validate-glb.cjs input.glb report.json');
  }
  if (path.resolve(input) === path.resolve(output)) {
    throw new Error('Report must not overwrite its input');
  }
  const bytes = fs.readFileSync(input);
  const report = await validator.validateBytes(new Uint8Array(bytes), {
    uri: path.basename(input),
    format: 'glb',
    maxIssues: 0,
    writeTimestamp: false,
    externalResourceFunction: async (uri) => {
      throw new Error(`External resource is forbidden for embedded candidates: ${uri}`);
    },
  });
  report.candidateValidation = {
    inputSha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    validatorVersion: validator.version(),
    supportsKHRTextureBasisu: validator.supportedExtensions().includes('KHR_texture_basisu'),
    limitation: 'This official validator does not validate KHR_texture_basisu or KTX2 image data. Run ktx validate --gltf-basisu independently.',
  };
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  const {numErrors, numWarnings, numInfos, numHints} = report.issues;
  console.log(JSON.stringify({input, output, inputSha256: report.candidateValidation.inputSha256, numErrors, numWarnings, numInfos, numHints}));
  if (report.issues.numErrors > 0) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 2;
});
