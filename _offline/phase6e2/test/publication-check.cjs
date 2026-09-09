"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),baseline="e356a4cb951fc3d614035fa0bf547e669b4d045a";
const base="https://yourizorge.github.io/fitmetzorge-staging/",phase=process.argv[2];
assert(["before","after-source","after-docs"].includes(phase));
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,windowsHide:true,maxBuffer:30000000});
const list=(...a)=>git(...a).toString().trim().split("\n").filter(Boolean),hash=b=>crypto.createHash("sha256").update(b).digest("hex");
assert.equal(git("remote","get-url","origin").toString().trim(),"https://github.com/Yourizorge/fitmetzorge-staging.git");
assert.equal(git("branch","--show-current").toString().trim(),"main");
const head=git("rev-parse","HEAD").toString().trim();
assert(list("diff","--name-only",baseline).every(f=>f.startsWith("docs/")||f.startsWith("_offline/phase6e2/")));
const runtime=f=>(!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||
 (f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f));
const files=list("ls-tree","-r","--name-only",baseline).filter(runtime);
assert.equal(files.length,60);assert.deepEqual(list("ls-tree","-r","--name-only","HEAD").filter(runtime),files);
(async()=>{
 const assets=[];
 for(const file of files){
  const expected=git("cat-file","blob",baseline+":"+file),local=fs.readFileSync(path.join(root,file));
  assert(git("cat-file","blob","HEAD:"+file).equals(expected),"Git runtime "+file);
  assert.equal(git("hash-object","--path="+file,file).toString().trim(),git("rev-parse",baseline+":"+file).toString().trim(),"working runtime "+file);
  const r=await fetch(base+file+"?6e2="+head+"-"+phase,{signal:AbortSignal.timeout(30000)});
  assert.equal(r.status,200,file);assert(Buffer.from(await r.arrayBuffer()).equals(expected),"published bytes "+file);
  if(/\.(js|html)$/.test(file))assert.doesNotMatch(expected.toString(),/_offline|phase6e[012]\./);
  assets.push({file,bytes:expected.length,sha256:hash(expected),working_sha256:hash(local)});
 }
 const probes=[],privateFiles=[...new Set([...list("ls-files","_offline","_tests"),
  ...list("ls-files","--others","--exclude-standard","_offline","_tests")])].sort();
 for(const file of privateFiles){
  const r=await fetch(base+file+"?6e2="+head+"-"+phase,{signal:AbortSignal.timeout(30000)});await r.arrayBuffer();
  assert.equal(r.status,404,"private source "+file);probes.push({file,status:404});
 }
 if(phase!=="before"){
  const before=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/phase6e2-publication-before.json"),"utf8"));
  assert.deepEqual(assets,before.assets,"raw working/published bytes before and after");
  assert.deepEqual(probes,before.private_source_probes,"same private source coverage");
 }
 const result={phase,checked_at:new Date().toISOString(),head,runtime_baseline:baseline,target:base,assets,
  private_source_probes:probes,runtime_byte_identical:true,offline_isolated:true,production_touched:false};
 fs.writeFileSync(path.join(root,"supabase/.temp/phase6e2-publication-"+phase+".json"),JSON.stringify(result,null,2)+"\n");
 console.log(JSON.stringify({phase,head,runtime:assets.length,private404:probes.length,pass:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
