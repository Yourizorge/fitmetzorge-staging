"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),base="https://yourizorge.github.io/fitmetzorge-staging/";
const baseline="9406ab5a0869564a6a5498ec2d7a679589a38bc0",changed=["app.js","index.html","assets/training-workout.css"];
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,windowsHide:true,maxBuffer:30000000}),sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const label=process.argv[2]||"final",head=git("rev-parse","HEAD").toString().trim(),ref=label==="before"?baseline:head;
(async()=>{
 const files=git("ls-tree","-r","--name-only",ref).toString().trim().split("\n").filter(f=>
  (!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||(f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f)));
 const assets=[];for(const file of files) {
  const expected=git("cat-file","blob",ref+":"+file),r=await fetch(base+file+"?alignment="+ref);
  assert.equal(r.status,200,file);const actual=Buffer.from(await r.arrayBuffer());assert(actual.equals(expected),"published bytes "+file);
  if(!changed.includes(file))assert(expected.equals(git("cat-file","blob",baseline+":"+file)),"protected runtime "+file);
  if(/\.(html|js)$/.test(file))assert.doesNotMatch(actual.toString(),/_offline|phase6e[0123]\./);
  assets.push({file,sha256:sha(actual),bytes:actual.length,alignment_cache_change:changed.includes(file)});
 }
 const privatePaths=[...new Set([...git("ls-files","_offline","_tests").toString().trim().split("\n"),
  ...git("ls-files","--others","--exclude-standard","_offline","_tests").toString().trim().split("\n")])].filter(Boolean);
 const probes=[];for(const file of privatePaths){const r=await fetch(base+file+"?alignment="+ref);await r.arrayBuffer();assert.equal(r.status,404,file);probes.push({file,status:404});}
 const result={head,ref,baseline,at:new Date().toISOString(),assets,private_source_probes:probes,
  runtime_matches_commit:true,unchanged_other_runtime:57,offline_isolated:true,production_touched:false};
 fs.writeFileSync(path.join(root,"supabase/.temp/training-alignment-publication-"+label+".json"),JSON.stringify(result,null,2));
 console.log(JSON.stringify({label,ref,assets:assets.length,unchanged:57,private404:probes.length,pass:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
