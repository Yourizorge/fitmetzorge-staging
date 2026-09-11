"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm"),test=require("node:test"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),baseline="8b994e1c355e1c3a6145a91546936d42123b20b0";
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,windowsHide:true,encoding:"utf8",maxBuffer:60000000}).trim();
const read=f=>fs.readFileSync(path.join(root,f),"utf8"),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(path.join(root,f))).digest("hex");
const evidence=JSON.parse(read("docs/PHASE6E5_FREEZE_EVIDENCE.json"));
test("scope is only new 6E6 and docs in staging main",()=>{
 assert.equal(git("remote","get-url","origin"),"https://github.com/Yourizorge/fitmetzorge-staging.git");assert.equal(git("branch","--show-current"),"main");
 assert.equal(git("diff",baseline,"--",".",":(exclude)docs",":(exclude)_offline/phase6e6"),"");
 assert(git("ls-files","--others","--exclude-standard").split("\n").filter(Boolean).every(f=>f.startsWith("docs/")||f.startsWith("_offline/phase6e6/")));
});
test("all 106 frozen sources and ALL 60 runtime assets retain raw and checkout bytes",()=>{
 const all=[...evidence.offline_sources,...evidence.prior_frozen_sources,...evidence.runtime_assets];assert.equal(all.length,166);
 for(const f of all){assert.equal(sha(f.file),f.working_sha256,f.file);assert.equal(git("rev-parse","HEAD:"+f.file),f.git_blob,f.file);}
 assert.equal(git("rev-parse","HEAD:_offline/phase6e5"),evidence.offline_tree);
 for(const t of evidence.prior_frozen_trees)assert.equal(git("rev-parse","HEAD:_offline/phase"+t.phase.toLowerCase().replace("-","")),t.tree);
});
test("original test evidence, preregistration and prior decisions are retained",()=>{
 assert.equal(sha(evidence.original_evidence.file),evidence.original_evidence.sha256);
 assert.equal(git("diff","6d11595","--","_offline/phase6e6/preregistered-cases.json"),"");
 assert.equal(git("ls-tree","-r","--name-only","6d11595","_offline/phase6e6/engine.cjs"),"");
 const old=cp.execFileSync("git",["cat-file","blob",baseline+":docs/DECISIONS.md"],{cwd:root,windowsHide:true,encoding:"utf8"}).replace(/\r\n/g,"\n");
 assert(read("docs/DECISIONS.md").replace(/\r\n/g,"\n").startsWith(old));
});
test("core has only explicit frozen/static imports; no runtime imports or dependencies",()=>{
 for(const file of ["rules.cjs","facts.cjs","engine.cjs","review.cjs"]){
  const src=read("_offline/phase6e6/"+file);
  assert.doesNotMatch(src,/\b(?:fetch|XMLHttpRequest|WebSocket|setTimeout|setInterval|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
  for(const m of src.matchAll(/require\("([^"]+)"\)/g))assert.match(m[1],/^(?:\.\/(?:rules|facts|engine)\.cjs|\.\/copy\.json|\.\.\/phase6e5\/(?:common|engine)\.cjs|\.\.\/phase6e4\/context\.cjs|\.\.\/phase6e1\/analysis\.cjs)$/);
  assert.throws(()=>vm.runInNewContext(src,{window:{}}),/offline_node_only/);
 }
 for(const f of evidence.runtime_assets.filter(f=>/\.(?:js|html|css)$/.test(f.file)))assert.doesNotMatch(read(f.file),/_offline|phase6e[0-6]\./);
 const p=JSON.parse(read("_offline/phase6e6/package.json"));assert.equal(p.private,true);assert(!p.dependencies);
});
test("all 30 examples execute without clock/random/network/IO/storage",()=>{
 const box=vm.createContext({process:{versions:{node:"synthetic"}}}),cache=new Map(),prefix=path.join(root,"_offline")+path.sep;
 vm.runInContext("globalThis.Date=undefined;Math.random=()=>{throw Error('random_forbidden')}",box);
 function load(file){
  assert(file.startsWith(prefix));assert(/\.(cjs|json)$/.test(file));if(cache.has(file))return cache.get(file);
  const src=fs.readFileSync(file,"utf8");if(file.endsWith(".json")){const value=vm.runInContext("("+src+")",box);cache.set(file,value);return value;}
  const module={exports:{}},require=name=>name==="node:crypto"?Object.freeze({createHash:crypto.createHash}):(assert(name.startsWith(".")),load(path.resolve(path.dirname(file),name)));
  vm.runInContext("(function(require,module,exports){"+src+"\n})",box)(require,module,module.exports);cache.set(file,module.exports);return module.exports;
 }
 box.examples=load(path.join(__dirname,"examples.cjs"));
 const results=JSON.parse(vm.runInContext("JSON.stringify(examples.generate())",box,{timeout:20000}));
 assert.equal(results.length,30);assert(results.every(x=>x.output.physical_advice_authorized===false));
});
