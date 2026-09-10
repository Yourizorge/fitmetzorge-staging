"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),
 cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm");
const root=path.resolve(__dirname,"../../.."),dir=path.resolve(__dirname,".."),baseline="9406ab5a0869564a6a5498ec2d7a679589a38bc0";
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,encoding:"utf8",windowsHide:true,maxBuffer:30000000}).trim();
const read=f=>fs.readFileSync(path.join(root,f),"utf8"),changed=["app.js","index.html","assets/training-workout.css"];
test("scope: only alignment/cache, new 6E3, its tests and documentation",()=>{
 assert.equal(git("remote","get-url","origin"),"https://github.com/Yourizorge/fitmetzorge-staging.git");
 assert.equal(git("branch","--show-current"),"main");
 const files=[...git("diff","--name-only",baseline).split("\n"),...git("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
 assert(files.every(f=>changed.includes(f)||f.startsWith("_offline/phase6e3/")||f.startsWith("_tests/training/alignment-")||f.startsWith("docs/")),files.join("\n"));
 assert.equal(git("diff",baseline,"--","supabase","AGENTS.md",".codex",".github"),"");
});
test("all 57 frozen 6E0/6E1/6E2 source Git and checkout identities preserved",()=>{
 const trees=["27ed4679b59fc5909712d4fa927138e5f9f03689","03cef72c409b7125488a3f5fa854fcf1247546c0","93ad63e84861c166f53ba5530d7496222461b4f8"];
 let count=0;
 for(const [i,tree] of trees.entries()) {
  assert.equal(git("rev-parse","HEAD:_offline/phase6e"+i),tree);
  const files=git("ls-tree","-r","--name-only",baseline,"_offline/phase6e"+i).split("\n");
  for(const f of files){assert.equal(git("hash-object",f),git("rev-parse",baseline+":"+f),f);count++;}
 }
 assert.equal(count,57);
 for(const i of [0,1])for(const f of JSON.parse(read("docs/PHASE6E"+i+"_FREEZE_EVIDENCE.json")).offline_sources)
  assert.equal(crypto.createHash("sha256").update(fs.readFileSync(path.join(root,f.file))).digest("hex"),f.working_sha256||f.sha256);
});
test("accepted D1-D12/O1-O5 and original frozen receipts/evidence retained",()=>{
 for(const f of ["PHASE6E0_OWNER_DECISIONS.md","PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md",
  "PHASE6E0_FREEZE_RECEIPT.md","PHASE6E0_FREEZE_EVIDENCE.json","PHASE6E1_FREEZE_RECEIPT.md",
  "PHASE6E1_FREEZE_EVIDENCE.json","PHASE6E1_OWNER_OVERVIEW.md","PHASE6E1_CONTRACTS.md","PHASE6E1_EVIDENCE.json",
  "PHASE6E2_PREREGISTRATION.md","PHASE6E2_EVIDENCE.json"])
  assert.equal(git("diff",baseline,"--","docs/"+f),"",f);
});
test("57 other runtime assets exact; app and HTML only alignment cache edits",()=>{
 const files=git("ls-tree","-r","--name-only",baseline).split("\n").filter(f=>
  (!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||(f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f)));
 assert.equal(files.length,60);
 const unchanged=files.filter(f=>!changed.includes(f));assert.equal(unchanged.length,57);
 for(const f of unchanged)assert.equal(git("hash-object",f),git("rev-parse",baseline+":"+f),f);
 for(const f of ["app.js","index.html"])assert.equal(read(f).replace(/\r\n/g,"\n").trim().replaceAll("20260910-effort-align1","20260909-training-correction2"),git("cat-file","blob",baseline+":"+f));
});
test("CSS diff limited to effort-row placement and shared columns; approved timer untouched",()=>{
 const prefixes=[".tw-set-effort,.tw-target-effort {",".tw-set-effort {",".tw-focus .tw-set-effort label {",
  ".tw-set-effort label:has(",".tw-target-effort {",".tw-live-set,.tw-set-headings {"];
 const strip=s=>s.split(/\r?\n/).filter(line=>!prefixes.some(p=>line.startsWith(p))).join("\n").trim();
 assert.equal(strip(read("assets/training-workout.css")),strip(git("cat-file","blob",baseline+":assets/training-workout.css")));
});
test("no runtime imports/embedding and new core is Node-only with no IO or clock",()=>{
 for(const f of git("ls-tree","-r","--name-only",baseline).split("\n").filter(f=>
   !["docs/","_offline/","_tests/"].some(p=>f.startsWith(p))&&/\.(html|js|cjs|ts|json|ya?ml)$/.test(f)))
  assert.doesNotMatch(read(f),/_offline|phase6e[0123]\./,f);
 for(const f of ["engine.cjs","validate.cjs"]) {
  const src=read("_offline/phase6e3/"+f);
  assert.throws(()=>vm.runInNewContext(src,{window:{},require(){throw Error("import");}}),/offline_node_only/);
  assert.doesNotMatch(src,/\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|setTimeout|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
  for(const m of src.matchAll(/require\("([^"]+)"\)/g))
   assert.match(m[1],/^(?:\.\.\/phase6e1\/(?:common|analysis)\.cjs|\.\.\/phase6e2\/(?:engine\.cjs|copy\.json)|\.\/(?:validate\.cjs|contract\.json|copy\.json))$/);
 }
 const pkg=JSON.parse(read("_offline/phase6e3/package.json"));assert.equal(pkg.private,true);
 assert.deepEqual(pkg.dependencies||{},{});assert.deepEqual(pkg.devDependencies||{},{});
});
test("complete examples execute inside a VM without networking, storage, clock or environment",()=>{
 const box=vm.createContext({process:{versions:{node:"synthetic"}}});
 vm.runInContext("globalThis.Date=undefined;Math.random=()=>{throw Error('random_forbidden')}",box);
 const cache=new Map(),offline=path.join(root,"_offline")+path.sep;
 function load(file) {
  assert(file.startsWith(offline));assert(/\.(cjs|json)$/.test(file));
  if(cache.has(file))return cache.get(file);
  const src=fs.readFileSync(file,"utf8");
  if(file.endsWith(".json")){const v=vm.runInContext("("+src+")",box);cache.set(file,v);return v;}
  const module={exports:{}},require=name=>{assert(name.startsWith("."));return load(path.resolve(path.dirname(file),name));};
  vm.runInContext("(function(require,module,exports){"+src+"\n})",box)(require,module,module.exports);
  cache.set(file,module.exports);return module.exports;
 }
 box.examples=load(path.join(dir,"test/examples.cjs"));
 const data=JSON.parse(vm.runInContext("JSON.stringify({normal:examples.examples(),boundary:examples.boundaries()})",box,{timeout:5000}));
 assert.equal(data.normal.length,3);assert.equal(data.boundary.length,8);
 assert(data.normal.every(x=>x.output.status==="recommendation"));
 assert(data.boundary.every(x=>!x.output.automatic_actions_allowed));
});
test("76 preregistered cases and three exact excerpts predate the new engine",()=>{
 const file="_offline/phase6e3/preregistered-cases.json";
 const first=git("log","--diff-filter=A","--format=%H","--",file).split("\n")[0];assert(first.startsWith("e635fe5"));
 assert.equal(git("ls-tree","-r","--name-only",first,"_offline/phase6e3"),file);
 assert.equal(git("diff",first,"--",file,"docs/PHASE6E3_PREREGISTRATION.md"),"");
 const data=JSON.parse(read(file));assert.equal(data.cases.length,76);assert.equal(data.cases.filter(c=>c.exact_excerpt).length,3);
});
