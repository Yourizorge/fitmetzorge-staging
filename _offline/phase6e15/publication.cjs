"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),[out,phase]=process.argv.slice(2),git=(...args)=>cp.execFileSync(process.env.FMZ_GIT||"git",args,{cwd:root,maxBuffer:40000000});
if(!out||!["before","after"].includes(phase))throw Error("args");
const sha=x=>crypto.createHash("sha256").update(x).digest("hex"),head=git("rev-parse","HEAD").toString().trim(),base="https://yourizorge.github.io/fitmetzorge-staging/";
const read=f=>JSON.parse(fs.readFileSync(p.join(root,f)));
const old=read("docs/PHASE6E10_FREEZE_EVIDENCE.json").protected.filter(x=>!x.file.startsWith("_")&&!x.file.startsWith("supabase/")).map(x=>({file:x.file,hash:x.sha256}));
for(const [n,dir]of [["12","workout-reflection-demo/"],["13","proactive-signals-demo/"],["14","bounded-adjustments-demo/"]])for(const x of read("docs/PHASE6E"+n+"_FREEZE_EVIDENCE.json").sources.filter(x=>x.file.startsWith(dir)))old.push({file:x.file,hash:x.git_sha256});
a.equal(old.length,102);const result={phase,head,existing:[],added:[],private:[],hosted_supabase_calls:0};
async function get(f){const r=await fetch(base+f.split("/").map(encodeURIComponent).join("/")+"?p15="+head,{redirect:"error",signal:AbortSignal.timeout(20000)});return {status:r.status,sha256:sha(Buffer.from(await r.arrayBuffer()))};}
(async()=>{try{
 for(const row of old){a.equal(sha(git("show","HEAD:"+row.file)),row.hash,row.file+" Git");const r=await get(row.file);result.existing.push({file:row.file,expected:row.hash,...r});a.equal(r.status,200,row.file);a.equal(r.sha256,row.hash,row.file);}
 if(phase==="after")for(const f of fs.readdirSync(p.join(root,"independent-intake-demo"))){const file="independent-intake-demo/"+f,expected=sha(git("show","HEAD:"+file)),r=await get(file);result.added.push({file,expected,...r});a.equal(r.status,200,file);a.equal(r.sha256,expected,file);}
 const privatePaths=[];for(const dir of ["_offline/phase6e12","_offline/phase6e13","_offline/phase6e14","_offline/phase6e15"])for(const f of fs.readdirSync(p.join(root,dir),{recursive:true}).filter(f=>fs.statSync(p.join(root,dir,f)).isFile()))privatePaths.push(dir+"/"+f.replaceAll("\\","/"));
 privatePaths.push("_offline/phase6e11/request_v4/transport.mjs","supabase/migrations/20260924155822_phase6e11_rpc_bridge.sql","supabase/migrations/20260928120846_phase6e11_request_binding.sql");
 for(const file of privatePaths){const r=await get(file);result.private.push({file,status:r.status});a.equal(r.status,404,file);}result.status="PUBLICATION_PASS";
 }catch(e){result.status="PUBLICATION_NO_GO";result.reason=e.message;process.exitCode=1;}
 finally{fs.writeFileSync(p.join(out,"publication-"+phase+"-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,phase,existing:result.existing.length,added:result.added.length,private:result.private.length,reason:result.reason}));}
})();
