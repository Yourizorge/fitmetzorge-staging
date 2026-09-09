"use strict";
const test=require("node:test"), assert=require("node:assert/strict"),fs=require("node:fs"),
 path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm");
const root=path.resolve(__dirname,"../../.."),directory=path.resolve(__dirname,"..");
const base="e356a4cb951fc3d614035fa0bf547e669b4d045a";
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:30000000}).trim();
test("6E2 scope: only new offline package and docs; no runtime/Edge/DB/workflow changes",()=>{
 assert.equal(git("remote","get-url","origin"),"https://github.com/Yourizorge/fitmetzorge-staging.git");
 assert.equal(git("branch","--show-current"),"main");
 assert.equal(git("diff",base,"--name-only","--",".",":(exclude)docs/**",":(exclude)_offline/phase6e2/**"),"");
 assert(git("ls-files","--others","--exclude-standard").split("\n").filter(Boolean).every(f=>f.startsWith("docs/")||f.startsWith("_offline/phase6e2/")));
});
test("6E2 all 45 frozen 6E0/6E1 sources retain Git identities AND working bytes",()=>{
 const e0=require("../../../docs/PHASE6E0_FREEZE_EVIDENCE.json"),e1=require("../../../docs/PHASE6E1_FREEZE_EVIDENCE.json");
 assert.equal(e0.offline_sources.length+e1.offline_sources.length,45);
 for(const [dir,evidence] of [["phase6e0",e0],["phase6e1",e1]]){
  assert.equal(git("rev-parse","HEAD:_offline/"+dir),evidence.offline_tree);
  for(const f of evidence.offline_sources){
   assert.equal(git("rev-parse","HEAD:"+f.file),f.git_blob);
   const bytes=fs.readFileSync(path.join(root,f.file));
   assert.equal(crypto.createHash("sha256").update(bytes).digest("hex"),f.working_sha256||f.sha256,f.file);
  }
 }
});
test("6E2 D1-D12, O1-O5, prior freeze receipts and historical evidence unchanged",()=>{
 for(const file of ["PHASE6E0_OWNER_DECISIONS.md","PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md",
  "PHASE6E0_FREEZE_RECEIPT.md","PHASE6E0_FREEZE_EVIDENCE.json","PHASE6E1_FREEZE_RECEIPT.md","PHASE6E1_FREEZE_EVIDENCE.json",
  "PHASE6E1_OWNER_OVERVIEW.md","PHASE6E1_CONTRACTS.md","PHASE6E1_EVIDENCE.json"])
  assert.equal(git("diff",base,"--","docs/"+file),"",file);
});
test("6E2 no runtime imports or embedded offline packages",()=>{
 const files=git("ls-tree","-r","--name-only",base).split("\n").filter(f=>
  !["docs/","_offline/","_tests/"].some(p=>f.startsWith(p))&&/\.(html|js|cjs|ts|tsx|json|ya?ml)$/.test(f));
 assert(files.length>50);
 for(const f of files)assert.doesNotMatch(fs.readFileSync(path.join(root,f),"utf8"),/_offline|phase6e[012]\./,f);
});
test("6E2 core is Node-only, no provider/IO/clock/env/random/storage import",()=>{
 const source=fs.readFileSync(path.join(directory,"engine.cjs"),"utf8");
 assert.throws(()=>vm.runInNewContext(source,{window:{},require(){throw Error("import");}}),/offline_node_only/);
 assert.doesNotMatch(source,/\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|setTimeout|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
 for(const m of source.matchAll(/require\("([^"]+)"\)/g))
  assert.match(m[1],/^(?:\.\.\/phase6e1\/(?:common|flow|analysis|retention)\.cjs|\.\/(?:contract|copy)\.json)$/);
 const pkg=require("../package.json");assert.equal(pkg.private,true);
 assert.deepEqual(pkg.dependencies||{},{});assert.deepEqual(pkg.devDependencies||{},{});
});
test("6E2 complete examples run without network, storage, clock or environment",()=>{
 const sandbox=vm.createContext({process:{versions:{node:"synthetic"}}});
 vm.runInContext("globalThis.Date=undefined; Math.random=()=>{throw Error('random_forbidden')}",sandbox);
 const paths=["engine.cjs","contract.json","copy.json","preregistered-cases.json","test/fixtures.cjs","test/examples.cjs",
  "../phase6e1/common.cjs","../phase6e1/flow.cjs","../phase6e1/analysis.cjs","../phase6e1/context.cjs","../phase6e1/retention.cjs",
  "../phase6e1/contract.json","../phase6e1/content-contract.json","../phase6e1/test/helpers.cjs",
  "../phase6e0/rules.json","../phase6e0/context-hints.json","../phase6e0/copy.json","../phase6e0/warning-recovery-proposal.json"];
 const allowed=new Set(paths.map(f=>path.resolve(directory,f))),cache=new Map();
 function load(file){
  assert(allowed.has(file),file);if(cache.has(file))return cache.get(file);
  const src=fs.readFileSync(file,"utf8");
  if(file.endsWith(".json")){const value=vm.runInContext("("+src+")",sandbox);cache.set(file,value);return value;}
  const module={exports:{}},require=name=>{assert(name.startsWith("."));return load(path.resolve(path.dirname(file),name));};
  vm.runInContext("(function(require,module,exports){"+src+"\n})",sandbox)(require,module,module.exports);
  cache.set(file,module.exports);return module.exports;
 }
 sandbox.examples=load(path.join(directory,"test/examples.cjs"));
 const outputs=JSON.parse(vm.runInContext("JSON.stringify({normal:examples.examples(),flow:examples.transitions()})",sandbox,{timeout:5000}));
 assert.equal(outputs.normal.length,9);assert.equal(outputs.flow.length,16);
 assert(outputs.normal.every(e=>e.output.recommendations.length===1&&e.output.medical_clearance===false));
 assert(outputs.flow.every(e=>e.results.every(r=>r.output.actions.length===0)));
});
test("6E2 preregistration predates implementation; original 122 cases and nine exact replies unchanged",()=>{
 const file="_offline/phase6e2/preregistered-cases.json",first=git("log","--diff-filter=A","--format=%H","--",file).split("\n")[0];
 assert(first.startsWith("d233cec"));
 assert.equal(git("ls-tree","-r","--name-only",first,"--","_offline/phase6e2"),file);
 assert.equal(git("diff",first,"--",file,"docs/PHASE6E2_PREREGISTRATION.md"),"");
 const data=require("../preregistered-cases.json");assert.equal(data.cases.length,122);
 assert.equal(data.cases.filter(c=>c.exact_recommendation).length,9);
});
