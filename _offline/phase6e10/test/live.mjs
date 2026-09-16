import fs from "node:fs";
import path from "node:path";
import cp from "node:child_process";
import readline from "node:readline";
import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {runScenarios} from "./scenarios.mjs";
import * as followup from "../ops/followup-audit.mjs";
export const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
export const BASE="https://mokxyyullfhkfalopbzd.supabase.co",PUB="sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT";
export function broker(){
 const p=cp.spawn("C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",[path.join(root,"_offline/phase6e10/ops/broker.py")],{cwd:root,windowsHide:true,stdio:["pipe","pipe","pipe"]});
 const queue=[];let unexpected=false;
 readline.createInterface({input:p.stdout}).on("line",line=>{
  const q=queue.shift();if(!q){unexpected=true;return;}
  try{const r=JSON.parse(line);if(r.ok)q.resolve(r.result);else q.reject(Error(r.error));}catch{q.reject(Error("broker_protocol_error"));}
 });
 p.stderr.on("data",()=>{unexpected=true;});
 p.on("exit",()=>{while(queue.length)queue.shift().reject(Error("broker_exited"));});
 return {call:async d=>{const event=followup.brokerBefore(d);const result=await new Promise((resolve,reject)=>{queue.push({resolve,reject});p.stdin.write(JSON.stringify(d)+"\n");});followup.brokerAfter(d,result,event);return result;},
 close:()=>new Promise(resolve=>{p.once("exit",()=>resolve());p.stdin.end();}),assertQuiet:()=>assert(!unexpected)};
}
export async function makeApi(b){
 const ids=await b.call({op:"identities"}),sessions={};
 for(const role of Object.keys(ids))sessions[role]=await b.call({op:"session",role});
 const lit=x=>"'"+String(x).replaceAll("'","''")+"'",j=x=>lit(JSON.stringify(x))+"::jsonb";
 const sql=q=>b.call({op:"query",sql:q});
 const json=async q=>Object.values((await sql(q))[0])[0];
 async function raw(who,body,proof=true){
  const event=followup.request(who,body);
  const r=await fetch(BASE+(proof?"/functions/v1/fmz6e10-synthetic":"/rest/v1/rpc/fmz6e10_call"),{
   method:"POST",headers:{Authorization:"Bearer "+sessions[who].access_token,apikey:PUB,"Content-Type":"application/json"},
   body:JSON.stringify(proof?body:{p:body}),signal:AbortSignal.timeout(35000)});
  followup.response(event,r.status);return {status:r.status,data:await r.json()};
 }
 return {ids,sessions,raw,sql,json,lit,j,
  fixture:unit=>json("select fmz6e10_private.fixture("+lit(unit)+")"),
  calculate:(body,p,logs,v)=>json("select fmz6e10_private.calculate("+[j(body),j(p),j(logs),v].join(",")+")"),
  concurrent:(who,bodies)=>Promise.all(bodies.map(body=>raw(who,body))),
  anonymous:async()=>{
   const r=await fetch(BASE+"/functions/v1/fmz6e10-synthetic",{method:"POST",headers:{"Content-Type":"application/json"},body:'{"op":"home"}'});await r.text();assert([401,403].includes(r.status));
  },
  direct:async()=>{
   const token=sessions.member.access_token;
   for(const resource of ["source_versions","identities","operators"]){
    const r=await fetch(BASE+"/rest/v1/"+resource+"?select=*",{headers:{Authorization:"Bearer "+token,apikey:PUB,"Accept-Profile":"fmz6e10_private"}});
    await r.text();assert.notEqual(r.status,200);
   }
   const r=await fetch(BASE+"/rest/v1/rpc/fmz6e10_call",{method:"POST",headers:{Authorization:"Bearer "+token,apikey:PUB,"Content-Type":"application/json"},body:'{"p":{"op":"home"}}'});await r.text();assert.notEqual(r.status,200);
  }
 };
}
async function main(){
 if(fs.existsSync(path.join(root,"supabase/.temp/phase6e10-owner-window.json")))throw Error("owner_window_receipt_requires_explicit_owner_followup");
 const b=broker(),report={scope:"hosted Auth JWT + Edge + PostgreSQL; synthetic identities only",checks:[],errors:[]};
 let api;
 try{
  if(!fs.existsSync(path.join(root,"supabase/.temp/phase6e10-controls.json"))||JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/phase6e10-controls.json"))).plain===undefined)await b.call({op:"controls"});
  api=await makeApi(b);
  await runScenarios(api,report);
  report.pass=true;
 }catch(e){report.errors.push(e.message);console.error(e.message);process.exitCode=1;}
 finally{
  try{
   if(api){
    const r=await api.raw("trainer",{op:"home"});
    for(const w of (r.data.windows||[]).filter(w=>(report.windows||[]).includes(w.id))){
     if(w.status==="active"){
      const q={op:"command",window:w.id,workspace:null,key:crypto.randomUUID(),expected:w.revision,action:"revoke",data:{}};
      await api.raw("trainer",q);
     }
     const h=await api.raw("trainer",{op:"home"}),current=h.data.windows.find(x=>x.id===w.id);
     if(current.status!=="cleaned")await api.raw("trainer",{op:"command",window:w.id,workspace:null,key:crypto.randomUUID(),expected:current.revision,action:"cleanup",data:{}});
    }
   }
   await b.call({op:"cleanup_controls"});
  }catch(e){report.errors.push("cleanup:"+e.message);report.pass=false;process.exitCode=1;}
  b.assertQuiet();await b.close();
  fs.writeFileSync(path.join(root,"supabase/.temp/phase6e10-live.json"),JSON.stringify(report,null,2)+"\n");
 }
 console.log(JSON.stringify({pass:report.pass,checks:report.checks.length,errors:report.errors}));
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
