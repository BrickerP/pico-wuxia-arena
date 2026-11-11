'use strict';
// Update only the two identified bundles; never regenerate UI or model integration.
const fs=require('node:fs'),path=require('node:path'),target=path.join(__dirname,'../index.html');let html=fs.readFileSync(target,'utf8');
for(const [file,label]of [['motion-core.js','MOTION'],['battle-core.js','BATTLE'],['locomotion-core.js','LOCOMOTION']]){const pattern=new RegExp('// BEGIN '+label+' CORE BUNDLE[\\s\\S]*?// END '+label+' CORE BUNDLE');if(!pattern.test(html))throw Error(label+' bundle anchors missing');html=html.replace(pattern,'// BEGIN '+label+' CORE BUNDLE\n'+fs.readFileSync(path.join(__dirname,file),'utf8')+'// END '+label+' CORE BUNDLE');}
fs.writeFileSync(target,html);console.log('Updated independent motion and battle bundles only');
