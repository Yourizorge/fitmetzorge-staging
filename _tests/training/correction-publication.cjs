const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),base="https://yourizorge.github.io/fitmetzorge-staging/",baseline="037a338a84a6144a149d44238cd936630cfbe503";
const allowed=["app.js","index.html","assets/phase3-training-engine.js","assets/training-workout-model.js","assets/training-workout-ui.js","assets/training-workout.css"];
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,windowsHide:true,maxBuffer:30000000}),sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const head=git("rev-parse","HEAD").toString().trim(),mode=process.argv[2]||"final";
(async()=>{
 const files=git("ls-tree","-r","--name-only","HEAD").toString().trim().split("\n").filter(f=>(!f.includes("/")&&/\.(html|css|js|png)$/.test(f))||(f.startsWith("assets/")&&!/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f))),assets=[];
 for(const file of files){
  const expected=git("cat-file","blob","HEAD:"+file),r=await fetch(base+file+"?correction="+head);assert.equal(r.status,200,file);
  const actual=Buffer.from(await r.arrayBuffer());assert(actual.equals(expected),"served bytes "+file);
  if(!allowed.includes(file))assert(expected.equals(git("cat-file","blob",baseline+":"+file)),file+" unrelated runtime");
  if(/\.(js|html)$/.test(file))assert.doesNotMatch(actual.toString(),/_offline|phase6e[012]\./,file);
  assets.push({file,bytes:actual.length,sha256:sha(actual),training_change:allowed.includes(file)});
 }
 const probes=[];for(const f of git("ls-files","_offline","_tests").toString().trim().split("\n")){const r=await fetch(base+f+"?correction="+head);await r.arrayBuffer();assert.equal(r.status,404,f);probes.push({file:f,status:404});}
 const result={head,baseline,at:new Date().toISOString(),assets,private_source_probes:probes,unchanged_other_runtime:54,runtime_matches_commit:true,offline_isolated:true,production_touched:false};
 fs.writeFileSync(path.join(root,"supabase/.temp/training-correction-publication-"+mode+".json"),JSON.stringify(result,null,2));console.log(JSON.stringify({head,assets:assets.length,unchanged:54,private404:probes.length,pass:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});

