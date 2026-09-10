"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm"),test=require("node:test"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),baseline="314730b6e25b908673e164696b11d25dae38c600";
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,windowsHide:true,encoding:"utf8",maxBuffer:60000000}).trim();
const read=f=>fs.readFileSync(path.join(root,f),"utf8"),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(path.join(root,f))).digest("hex");
const evidence=JSON.parse(read("docs/PHASE6E4_FREEZE_EVIDENCE.json"));
test("only staging main and new 6E5/docs change",()=>{
 assert.equal(git("remote","get-url","origin"),"https://github.com/Yourizorge/fitmetzorge-staging.git");assert.equal(git("branch","--show-current"),"main");
 assert.equal(git("diff",baseline,"--",".",":(exclude)docs",":(exclude)_offline/phase6e5"),"");
 const files=git("ls-files","--others","--exclude-standard").split("\n").filter(Boolean);assert(files.every(f=>f.startsWith("_offline/phase6e5/")||f.startsWith("docs/")));
});
test("all 89 frozen sources and 60 runtime assets keep Git and checkout hashes",()=>{
 const all=[...evidence.offline_sources,...evidence.prior_frozen_sources,...evidence.runtime_assets];assert.equal(all.length,149);
 for(const f of all){assert.equal(sha(f.file),f.working_sha256,f.file);assert.equal(git("rev-parse","HEAD:"+f.file),f.git_blob,f.file);}
 assert.equal(git("rev-parse","HEAD:_offline/phase6e4"),evidence.offline_tree);
 for(const t of evidence.prior_frozen_trees)assert.equal(git("rev-parse","HEAD:_offline/phase"+t.phase.toLowerCase().replace("-","")),t.tree);
});
test("original evidence and preregistration preserved before implementation",()=>{
 assert.equal(sha(evidence.original_evidence.file),evidence.original_evidence.sha256);
 assert.equal(git("diff","b428924","--","_offline/phase6e5/preregistered-cases.json"),"");
 assert.equal(git("ls-tree","-r","--name-only","b428924","_offline/phase6e5/engine.cjs"),"");
 const old=cp.execFileSync("git",["cat-file","blob",baseline+":docs/DECISIONS.md"],{cwd:root,windowsHide:true,encoding:"utf8"}).replace(/\r\n/g,"\n");
 assert(read("docs/DECISIONS.md").replace(/\r\n/g,"\n").startsWith(old));
});
test("core imports only explicit frozen/static dependencies and hash primitive",()=>{
 for(const file of ["common.cjs","validate.cjs","engine.cjs","review.cjs"]){
  const src=read("_offline/phase6e5/"+file);
  assert.doesNotMatch(src,/\b(?:fetch|XMLHttpRequest|WebSocket|setTimeout|setInterval|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
  for(const m of src.matchAll(/require\("([^"]+)"\)/g))assert.match(m[1],/^(?:node:crypto|\.\/(?:common\.cjs|validate\.cjs|engine\.cjs|copy\.json|contract\.json)|\.\.\/phase6e1\/(?:common|analysis)\.cjs|\.\.\/phase6e3\/contract\.json|\.\.\/phase6e4\/engine\.cjs)$/);
  assert.throws(()=>vm.runInNewContext(src,{window:{}}),/offline_node_only/);
 }
 for(const f of evidence.runtime_assets.filter(f=>/\.(?:js|html|css)$/.test(f.file)))assert.doesNotMatch(read(f.file),/_offline|phase6e[0-5]\./);
 const p=JSON.parse(read("_offline/phase6e5/package.json"));assert.equal(p.private,true);assert(!p.dependencies);
});
test("all concept examples run without clock network IO storage or randomness",()=>{
 const box=vm.createContext({process:{versions:{node:"synthetic"}}}),cache=new Map(),prefix=path.join(root,"_offline")+path.sep;
 vm.runInContext("globalThis.Date=undefined;Math.random=()=>{throw Error('random_forbidden')}",box);
 function load(file){
  assert(file.startsWith(prefix));assert(/\.(cjs|json)$/.test(file));if(cache.has(file))return cache.get(file);
  const src=fs.readFileSync(file,"utf8");if(file.endsWith(".json")){const value=vm.runInContext("("+src+")",box);cache.set(file,value);return value;}
  const module={exports:{}},require=name=>name==="node:crypto"?Object.freeze({createHash:crypto.createHash}):(assert(name.startsWith(".")),load(path.resolve(path.dirname(file),name)));
  vm.runInContext("(function(require,module,exports){"+src+"\n})",box)(require,module,module.exports);cache.set(file,module.exports);return module.exports;
 }
 box.examples=load(path.join(__dirname,"examples.cjs"));
 const results=JSON.parse(vm.runInContext("JSON.stringify(examples.generate())",box,{timeout:10000}));
 assert.equal(results.length,30);assert(results.every(x=>(x.output||x.initial).physical_advice_authorized===false));
});
