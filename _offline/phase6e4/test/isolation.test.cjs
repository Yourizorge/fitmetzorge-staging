"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),vm=require("node:vm"),test=require("node:test"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),baseline="adfff180e30093abc2febe601a3dead123afe36b",read=f=>fs.readFileSync(path.join(root,f),"utf8");
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,windowsHide:true,maxBuffer:60000000,encoding:"utf8"}).trim(),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(path.join(root,f))).digest("hex");
const proof=JSON.parse(read("docs/PHASE6E3_FREEZE_EVIDENCE.json"));
test("scope only new offline 6E4 and documentation; current main staging",()=>{
  assert.equal(git("remote","get-url","origin"),"https://github.com/Yourizorge/fitmetzorge-staging.git");assert.equal(git("branch","--show-current"),"main");
  const files=[...git("diff","--name-only",baseline).split("\n"),...git("ls-files","--others","--exclude-standard").split("\n")].filter(Boolean);
  assert(files.every(f=>f.startsWith("_offline/phase6e4/")||f.startsWith("docs/")),files.join("\n"));
  assert.equal(git("diff",baseline,"--",".",":(exclude)docs",":(exclude)_offline/phase6e4"),"");
});
test("all 69 frozen source and all 60 runtime identities unchanged without exceptions",()=>{
  for(const t of proof.frozen_trees)assert.equal(git("rev-parse","HEAD:_offline/phase"+t.phase.toLowerCase().replace("-","")),t.tree);
  let count=0;for(const key of ["offline_sources","other_frozen_sources","runtime_assets"]){
    for(const f of proof[key]){assert.equal(sha(f.file),f.working_sha256,f.file);count++;}
  }assert.equal(count,129);
});
test("earlier decisions, freeze receipts and evidence retained",()=>{
  const files=git("ls-tree","-r","--name-only",baseline,"docs").split("\n").filter(f=>/PHASE6E[0123].*(?:FREEZE|EVIDENCE|OWNER_DECISIONS)|PACKAGE6D_CORRECTED_FREEZE/.test(f));
  assert.equal(git("diff",baseline,"--",...files),"");
  const prior=cp.execFileSync("git",["cat-file","blob",baseline+":docs/DECISIONS.md"],{cwd:root,windowsHide:true,encoding:"utf8"}).replace(/\r\n/g,"\n");
  assert(read("docs/DECISIONS.md").replace(/\r\n/g,"\n").startsWith(prior));
});
test("preregistered cases precede implementation; only documented fixture time changed before core",()=>{
  const first=git("log","--diff-filter=A","--format=%H","--","_offline/phase6e4/preregistered-cases.json").split("\n").at(-1);
  assert(first.startsWith("e5d53ab"));
  assert.equal(git("ls-tree","-r","--name-only",first,"_offline/phase6e4/engine.cjs"),"");
  assert.equal(git("diff","0c37163","--","_offline/phase6e4/preregistered-cases.json","_offline/phase6e4/language-cases.json"),"");
  assert.equal(JSON.parse(read("_offline/phase6e4/preregistered-cases.json")).cases.length,129);
  assert.equal(JSON.parse(read("_offline/phase6e4/language-cases.json")).cases.length,41);
});
test("core has only frozen/static imports and no IO clock provider or runtime entry",()=>{
  for(const file of ["engine.cjs","context.cjs","validate.cjs"]){
    const text=read("_offline/phase6e4/"+file);
    assert.doesNotMatch(text,/\b(?:fetch|XMLHttpRequest|WebSocket|setTimeout|setInterval|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
    for(const m of text.matchAll(/require\("([^"]+)"\)/g))assert.match(m[1],/^(?:\.\/(?:context\.cjs|validate\.cjs|copy\.json|contract\.json)|\.\.\/phase6e1\/(?:common|analysis|context)\.cjs|\.\.\/phase6e2\/(?:engine\.cjs|copy\.json)|\.\.\/phase6e3\/contract\.json)$/);
    assert.throws(()=>vm.runInNewContext(text,{window:{}}),/offline_node_only/);
  }
  for(const file of proof.runtime_assets.filter(f=>/\.(?:js|html|css)$/.test(f.file)))assert.doesNotMatch(read(file.file),/_offline|phase6e[0-4]\./);
  const pkg=JSON.parse(read("_offline/phase6e4/package.json"));assert.equal(pkg.private,true);assert(!pkg.dependencies);
});
test("full allowed and refused examples execute in VM without IO storage clock environment",()=>{
  const box=vm.createContext({process:{versions:{node:"synthetic"}}}),cache=new Map(),prefix=path.join(root,"_offline")+path.sep;
  vm.runInContext("globalThis.Date=undefined;Math.random=()=>{throw Error('random_forbidden')}",box);
  function load(file){
    assert(file.startsWith(prefix));assert(/\.(cjs|json)$/.test(file));if(cache.has(file))return cache.get(file);
    const src=fs.readFileSync(file,"utf8");
    if(file.endsWith(".json")){const x=vm.runInContext("("+src+")",box);cache.set(file,x);return x;}
    const module={exports:{}},require=name=>{assert(name.startsWith("."));return load(path.resolve(path.dirname(file),name));};
    vm.runInContext("(function(require,module,exports){"+src+"\n})",box)(require,module,module.exports);cache.set(file,module.exports);return module.exports;
  }
  box.examples=load(path.join(__dirname,"examples.cjs"));
  const result=JSON.parse(vm.runInContext("JSON.stringify(examples.examples())",box,{timeout:5000}));
  assert.equal(result.length,6);assert.equal(result.filter(x=>x.output.status==="candidate_only").length,3);
  assert(result.every(x=>!x.output.automatic_actions_allowed&&!x.output.physical_advice_authorized));
});
