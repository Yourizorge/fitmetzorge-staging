"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),folder=process.argv[2],phase=process.argv[3];
if(!folder||!["before","after"].includes(phase))throw Error("args");
const git=(...args)=>cp.execFileSync(process.env.FMZ_GIT||"git",args,{cwd:root,maxBuffer:20000000});
const hash=x=>crypto.createHash("sha256").update(x).digest("hex"),head=git("rev-parse","HEAD").toString().trim();
const base="https://yourizorge.github.io/fitmetzorge-staging/";
const frozen=JSON.parse(fs.readFileSync(path.join(root,"docs/PHASE6E10_FREEZE_EVIDENCE.json"))).protected.filter(x=>!x.file.startsWith("_")&&!x.file.startsWith("supabase/"));
a.equal(frozen.length,84);
const config=git("show","HEAD:_config.yml").toString();a(config.includes("- _offline")&&config.includes("- supabase"));
const report={phase,head,existing:[],added:[],private:[],hosted_supabase_calls:0};
async function get(file){const r=await fetch(base+file.split("/").map(encodeURIComponent).join("/")+"?p12="+head,{redirect:"error",signal:AbortSignal.timeout(20000)});return {status:r.status,sha256:hash(Buffer.from(await r.arrayBuffer()))};}
(async()=>{try{
 for(const old of frozen){const expected=hash(git("show","HEAD:"+old.file));a.equal(expected,old.sha256,old.file+" frozen Git identity");
  const observed=await get(old.file);report.existing.push({file:old.file,expected,...observed});a.equal(observed.status,200);a.equal(observed.sha256,expected,old.file);}
 if(phase==="after")for(const file of fs.readdirSync(path.join(root,"workout-reflection-demo")).map(x=>"workout-reflection-demo/"+x)){
  const expected=hash(git("show","HEAD:"+file)),r=await get(file);report.added.push({file,expected,...r});a.equal(r.status,200,file);a.equal(r.sha256,expected,file);
 }
 const hidden=git("ls-files","_offline/phase6e12").toString().trim().split(/\r?\n/).filter(Boolean);
 for(const f of [...hidden,"_offline/phase6e11/request_v4/transport.mjs","supabase/migrations/20260928120846_phase6e11_request_binding.sql"]){const r=await get(f);report.private.push({file:f,status:r.status});a.equal(r.status,404,f);}
 report.status="PUBLICATION_IDENTITY_PASS";
}catch(e){report.status="PUBLICATION_NO_GO";report.reason=e.message;process.exitCode=1;}
finally{fs.writeFileSync(path.join(folder,"publication-"+phase+"-"+Date.now()+".json"),JSON.stringify(report,null,2),{flag:"wx"});console.log(JSON.stringify({phase,status:report.status,existing:report.existing.length,added:report.added.length,private:report.private.length,reason:report.reason}));}})();
