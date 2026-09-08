const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),base="https://yourizorge.github.io/fitmetzorge-staging/";
const git=(...args)=>cp.execFileSync("git",args,{cwd:root,windowsHide:true,maxBuffer:30000000});
const head=git("rev-parse","HEAD").toString().trim(),frozen="bc6308fbf0f914b04c7faa711219d9ae46e9cbe3";
const allowed=["app.js","index.html","assets/phase3-training-engine.js","assets/phase6d-owner-settings.js","assets/training-workout-model.js","assets/training-workout-ui.js","assets/training-workout.css"];
const files=git("ls-tree","-r","--name-only","HEAD").toString().trim().split("\n").filter(f=>
 (!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||(f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f)));
const hash=bytes=>crypto.createHash("sha256").update(bytes).digest("hex");
(async()=>{
 const assets=[];
 for(const file of files){
  const expected=git("cat-file","blob","HEAD:"+file),url=base+file+"?training="+head;
  const response=await fetch(url);assert.equal(response.status,200,file);
  const actual=Buffer.from(await response.arrayBuffer());assert(actual.equals(expected),"published bytes "+file);
  if(!allowed.includes(file))assert(expected.equals(git("cat-file","blob",frozen+":"+file)),"unrelated frozen runtime "+file);
  if(/\.(js|html)$/.test(file))assert.doesNotMatch(actual.toString(),/_offline|phase6e[01]\./,file);
  assets.push({file,bytes:actual.length,sha256:hash(actual),authorized_training_change:allowed.includes(file)});
 }
 const privateFiles=git("ls-files","_offline","_tests").toString().trim().split("\n").filter(Boolean),probes=[];
 for(const file of privateFiles){
  const response=await fetch(base+file+"?training="+head);await response.arrayBuffer();
  assert.equal(response.status,404,"private source must not be published: "+file);probes.push({file,status:404});
 }
 const result={checked_at:new Date().toISOString(),head,target:base,assets,private_source_probes:probes,
  runtime_matches_commit:true,unrelated_runtime_frozen:true,offline_isolated:true,production_touched:false};
 fs.writeFileSync(path.join(root,"supabase/.temp/training-publication.json"),JSON.stringify(result,null,2));
 console.log(JSON.stringify({head,assets:assets.length,unchanged:assets.filter(a=>!a.authorized_training_change).length,private_404:probes.length,pass:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
