"use strict";
const fs=require("node:fs"),p=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),a=require("node:assert/strict");
const root=p.resolve(__dirname,"../.."),[out,phase]=process.argv.slice(2);
if(!out||!["before","after"].includes(phase))throw Error("args");
const git=(...args)=>cp.execFileSync(process.env.FMZ_GIT||"git",args,{cwd:root,maxBuffer:30000000});
const sha=x=>crypto.createHash("sha256").update(x).digest("hex"),head=git("rev-parse","HEAD").toString().trim();
const base="https://yourizorge.github.io/fitmetzorge-staging/";
const old=JSON.parse(fs.readFileSync(p.join(root,"docs/PHASE6E10_FREEZE_EVIDENCE.json"))).protected.filter(x=>!x.file.startsWith("_")&&!x.file.startsWith("supabase/"));
const f12=JSON.parse(fs.readFileSync(p.join(root,"docs/PHASE6E12_FREEZE_EVIDENCE.json"))).sources.filter(x=>x.file.startsWith("workout-reflection-demo/"));
a.equal(old.length,84);a.equal(f12.length,6);
const result={phase,head,existing:[],frozen6e12:[],added:[],private:[],hosted_supabase_calls:0};
async function get(f){const r=await fetch(base+f.split("/").map(encodeURIComponent).join("/")+"?p13="+head,{redirect:"error",signal:AbortSignal.timeout(20000)});return {status:r.status,sha256:sha(Buffer.from(await r.arrayBuffer()))};}
(async()=>{try{
 for(const [rows,key,field]of [[old,"existing","sha256"],[f12,"frozen6e12","git_sha256"]])for(const row of rows){
  a.equal(sha(git("show","HEAD:"+row.file)),row[field],row.file+" Git");
  const r=await get(row.file);result[key].push({file:row.file,expected:row[field],...r});a.equal(r.status,200,row.file);a.equal(r.sha256,row[field],row.file);
 }
 if(phase==="after")for(const file of fs.readdirSync(p.join(root,"proactive-signals-demo")).map(f=>"proactive-signals-demo/"+f)){
  const expected=sha(git("show","HEAD:"+file)),r=await get(file);result.added.push({file,expected,...r});a.equal(r.status,200,file);a.equal(r.sha256,expected,file);
 }
 const privatePaths=[...fs.readdirSync(p.join(root,"_offline/phase6e13"),{recursive:true}).filter(f=>fs.statSync(p.join(root,"_offline/phase6e13",f)).isFile()).map(f=>"_offline/phase6e13/"+f.replaceAll("\\","/")),
  ...git("ls-files","_offline/phase6e12").toString().trim().split(/\r?\n/).filter(Boolean),"_offline/phase6e11/request_v4/transport.mjs",
  "supabase/migrations/20260924155822_phase6e11_rpc_bridge.sql","supabase/migrations/20260928120846_phase6e11_request_binding.sql"];
 for(const file of privatePaths){const r=await get(file);result.private.push({file,status:r.status});a.equal(r.status,404,file);}
 result.status="PUBLICATION_PASS";
 }catch(e){result.status="PUBLICATION_NO_GO";result.reason=e.message;process.exitCode=1;}
 finally{fs.writeFileSync(p.join(out,"publication-"+phase+"-"+Date.now()+".json"),JSON.stringify(result,null,2),{flag:"wx"});console.log(JSON.stringify({status:result.status,phase,existing:result.existing.length,frozen6e12:result.frozen6e12.length,added:result.added.length,private:result.private.length,reason:result.reason}));}
})();
