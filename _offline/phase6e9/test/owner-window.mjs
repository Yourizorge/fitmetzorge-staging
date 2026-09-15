import fs from "node:fs";
import path from "node:path";
import cp from "node:child_process";
import crypto from "node:crypto";
import readline from "node:readline";
import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {browserTest} from "./browser.mjs";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
const url="https://mokxyyullfhkfalopbzd.supabase.co",pub="sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT";
const target=path.join(root,"supabase/.temp/phase6e9-owner-window.json");
const python="C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const report={scope:"6E9 owner retest; exactly three new synthetic identities",at:new Date().toISOString(),checks:[],accounts:[],emails:[],active:false};
if(fs.existsSync(target))throw Error("existing_window_receipt_requires_inspection");
const proc=cp.spawn(python,[path.join(root,"_offline/phase6e9/test/admin.py"),"--owner-window"],{windowsHide:true,stdio:["pipe","pipe","pipe"]});
const queue=[];proc.stderr.on("data",()=>{});
readline.createInterface({input:proc.stdout}).on("line",line=>{
 const item=queue.shift();if(!item)return;
 try{const d=JSON.parse(line);d.ok?item.resolve(d.result):item.reject(Error(d.error+" "+(d.status||"")));}catch{item.reject(Error("broker_response_invalid"));}
});
proc.on("exit",()=>{for(const q of queue)q.reject(Error("broker_exited"));});
const broker=d=>new Promise((resolve,reject)=>{queue.push({resolve,reject});proc.stdin.write(JSON.stringify(d)+"\n");});
const query=sql=>broker({op:"query",sql});
const lit=x=>"'"+String(x).replaceAll("'","''")+"'";
const save=()=>fs.writeFileSync(target,JSON.stringify(report,null,2)+"\n");
const accounts={};
async function check(name,fn){await fn();report.checks.push(name);save();console.log("PASS",name);}
async function request(a,route,body,method="POST",headers={}){
 const r=await fetch(url+route,{method,headers:{apikey:pub,...(a?.token?{Authorization:"Bearer "+a.token}:{}),"Content-Type":"application/json",...headers},...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(30000)});
 let data;try{data=await r.json();}catch{data={};}return {status:r.status,data};
}
const edge=(a,body)=>request(a,"/functions/v1/fmz6e9-synthetic",body);
const denied=r=>assert([400,401,403,409].includes(r.status),"denial expected, status "+r.status);
async function login(a){
 const r=await request(null,"/auth/v1/token?grant_type=password",{email:a.email,password:a.password});
 assert.equal(r.status,200,"synthetic_login_status");a.token=r.data.access_token;
}
async function read(a,w=a.workspace){const r=await edge(a,{op:"read",workspace:w});assert.equal(r.status,200,"synthetic_read_status");return r.data;}
async function cmd(a,action,data={},opts={}){
 const s=opts.state||await read(a);
 return edge(a,{op:"command",workspace:s.workspace,expected:s.revision,key:opts.key||crypto.randomUUID(),command:{action,data}});
}
async function ok(a,action,data={},opts={}){const r=await cmd(a,action,data,opts);assert.equal(r.status,200,"command "+action+" status "+r.status);return r.data;}
async function capture(){
 const names=await query("select n.nspname as schema,c.relname as name from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','ai_private','legacy_auth_private') and c.relkind='r' order by 1,2");
 const ids=report.accounts.map(a=>lit(a.id)).join(",")||"null";
 const workspaces=report.accounts.filter(a=>a.workspace).map(a=>lit(a.workspace)).join(",")||"null";
 const pieces=names.map(t=>{
  assert(/^[a-z0-9_]+$/.test(t.schema)&&/^[a-z0-9_]+$/.test(t.name));
  let filter="";
  if(report.accounts.length&&t.schema==="public"&&t.name==="profiles")filter=" where id not in ("+ids+")";
  if(report.accounts.length&&t.schema==="public"&&["fmz6e9_audit","fmz6e9_notices"].includes(t.name))filter=" where workspace not in ("+workspaces+")";
  return "select "+lit(t.schema+"."+t.name)+" as name,count(*)::int as rows,encode(sha256(convert_to(coalesce(string_agg(h,',' order by h),''),'UTF8')),'hex') as sha256 from (select encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h from "+t.schema+"."+t.name+" t"+filter+") hashes";
 });
 return query(pieces.join(" union all ")+" /* fmz6e9 unchanged existing cohort */");
}
async function create(name,email,role,trainer=null){
 const a={email,password:crypto.randomBytes(32).toString("base64url")+"aA1!",workspace:role==="trainer"?null:crypto.randomUUID()};
 a.id=(await broker({op:"create",email,password:a.password})).id;
 report.accounts.push({name,id:a.id,workspace:a.workspace});accounts[name]=a;save();
 await query("insert into public.profiles(id,role,name,email,trainer_id) values("+[lit(a.id),lit(role),lit("Synthetic 6E9 owner "+name),lit(email),trainer?lit(trainer.id):"null"].join(",")+") /* fmz6e9 newly created exact identity */");
 await login(a);return a;
}
async function subject(a,route,trainer=null){
 await query("insert into fmz6e9_private.subjects(workspace,member_id,route,trainer_id,expires_at,active_version) values("+[lit(a.workspace),lit(a.id),lit(route),trainer?lit(trainer.id):"null",lit(report.expires_at),route==="A"?3:0].join(",")+")");
}
try{
 const state=(await query("select (select enabled from fmz6e9_private.config where id) enabled,(select proof_hash is null from fmz6e9_private.config where id) proof_absent,(select count(*)::int from fmz6e9_private.subjects) subjects,(select count(*)::int from auth.users where lower(email) in ('zorgeyouri+6e9-a-lid@gmail.com','zorgeyouri+6e9-a-trainer@gmail.com','zorgeyouri+6e9-b-lid@gmail.com')) aliases"))[0];
 assert.deepEqual(state,{enabled:false,proof_absent:true,subjects:0,aliases:0});
 report.auth_config=await broker({op:"auth_config"});assert(report.auth_config.staging_site&&report.auth_config.staging_redirect);
 report.before=await capture();save();
 report.migrations_before=await query("select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sha256 from supabase_migrations.schema_migrations order by version /* fmz6e9 */");
 assert.equal(report.migrations_before.length,34);
 report.expires_at=(await query("select clock_timestamp()+interval '23 hours 59 minutes' as expires_at /* fmz6e9 */"))[0].expires_at;
 save();
 const trainer=await create("trainerA","zorgeyouri+6e9-a-trainer@gmail.com","trainer");
 const a=await create("memberA","zorgeyouri+6e9-a-lid@gmail.com","client",trainer);
 const b=await create("memberB","zorgeyouri+6e9-b-lid@gmail.com","client");
 trainer.workspace=a.workspace;await subject(a,"A",trainer);
 await check("disabled window denies the new valid login",async()=>assert.equal((await edge(a,{op:"read",workspace:a.workspace})).status,503));
 await broker({op:"proof"});
 let ready=false;
 for(let i=0;i<18;i++){const r=await edge(a,{op:"read",workspace:a.workspace});if(r.status===200){ready=true;break;}await new Promise(r=>setTimeout(r,5000));}
 assert(ready,"edge_proof_not_ready");
 await check("ordinary authenticated principal without fixture denied (same new B identity before enrollment)",async()=>denied(await edge(b,{op:"home"})));
 await subject(b,"B");
 await check("anonymous Edge and RPC denied",async()=>{denied(await edge(null,{op:"home"}));denied(await request(null,"/rest/v1/rpc/fmz6e9_home",{}));});
 await check("exactly three actors; homes and cross-route reads isolated",async()=>{
  for(const [who,route,role] of [[a,"A","member"],[trainer,"A","trainer"],[b,"B","member"]]){
   const r=await edge(who,{op:"home"});assert.equal(r.status,200);assert.deepEqual(r.data.workspaces,[{workspace:who.workspace,route,actor_role:role}]);
  }
  denied(await edge(b,{op:"read",workspace:a.workspace}));denied(await edge(a,{op:"read",workspace:b.workspace}));denied(await edge(trainer,{op:"read",workspace:b.workspace}));
  const rows=await query("select trainer_id is null as no_trainer from public.profiles where id="+lit(b.id)+" /* fmz6e9 */");assert(rows[0].no_trainer);
 });
 await check("member cannot approve as trainer or forge role, route or proposal data",async()=>{
  denied(await cmd(a,"trainer_approve"));denied(await edge(a,{op:"home",role:"trainer"}));
  denied(await cmd(a,"open",{proposal_version:999}));
  denied(await request(a,"/rest/v1/rpc/fmz6e9_read",{p_workspace:a.workspace}));
 });
 await check("published mobile workflow, separate approvals, restore, lost-response retry and relogin",async()=>{
  const r=await browserTest({root,accounts:{memberA:a,trainerA:trainer,memberB:b},label:"owner-window",published:true});
  report.browser={checks:r.checks.length,layouts:r.layouts,errors:r.errors,physical_phone:false};
 });
 for(const who of [a,trainer,b])await login(who);
 await check("old apply cannot produce a second version or partial write",async()=>{
  for(const who of [trainer,b]){const before=await read(who);denied(await cmd(who,"apply"));const after=await read(who);assert.deepEqual(after.versions,before.versions);assert.equal(after.revision,before.revision);}
 });
 await check("stale revision and same-key altered proposal rejected; same apply retry is idempotent",async()=>{
  await ok(a,"restore",{version:4});const old=await read(a);await ok(a,"member_accept");
  denied(await cmd(trainer,"trainer_approve",{}, {state:old}));denied(await cmd(trainer,"apply"));
  await ok(trainer,"trainer_approve");const s=await read(trainer),key=crypto.randomUUID();
  const first=await ok(trainer,"apply",{},{state:s,key});const repeat=await ok(trainer,"apply",{},{state:s,key});
  assert.equal(first.version,6);assert.equal(repeat.receipt.replay,true);
  denied(await cmd(trainer,"trainer_reject",{},{state:s,key}));denied(await cmd(trainer,"apply"));
 });
 await check("B has no trainer approval; rejection and edit invalidate activation",async()=>{
  await ok(b,"reopen");denied(await cmd(b,"trainer_approve"));await ok(b,"confirm");await ok(b,"edit",{kind:"sleep",hours:8});
  denied(await cmd(b,"apply"));await ok(b,"reject");denied(await cmd(b,"apply"));
 });
 await check("expired server window denies existing sessions and direct table reads",async()=>{
  await query("update fmz6e9_private.subjects set expires_at=clock_timestamp()-interval '1 second' where workspace in ("+[a.workspace,b.workspace].map(lit).join(",")+")");
  try{
   for(const who of [a,trainer,b]){denied(await edge(who,{op:"home"}));denied(await edge(who,{op:"read",workspace:who.workspace}));}
   const r=await request(a,"/rest/v1/fmz6e9_audit?select=id",undefined,"GET");assert(r.status!==200||r.data.length===0);
  }finally{await query("update fmz6e9_private.subjects set expires_at="+lit(report.expires_at)+" where workspace in ("+[a.workspace,b.workspace].map(lit).join(",")+")");}
 });
 await check("audit RLS and direct writes cannot cross identity boundaries",async()=>{
  const r=await request(b,"/rest/v1/fmz6e9_audit?workspace=eq."+a.workspace,undefined,"GET");assert.equal(r.status,200);assert.deepEqual(r.data,[]);
  const n=await request(trainer,"/rest/v1/fmz6e9_notices?recipient=eq."+a.id,undefined,"GET");assert.deepEqual(n.data,[]);
  denied(await request(a,"/rest/v1/fmz6e9_audit",{workspace:a.workspace}));
 });
 // Leave the tested audit history intact and a fresh pending proposal for owner review.
 await ok(a,"restore",{version:3});await ok(b,"reopen");
 await check("owner start state retained with no automatic approval or application",async()=>{
  report.start={};
  for(const [key,who] of [["A",a],["B",b]]){const s=await read(who);report.start[key]={version:s.version,revision:s.revision,status:s.status,versions:s.versions.map(v=>v.version)};}
  assert.equal(report.start.A.version,6);assert.equal(report.start.B.version,3);
 });
 report.after=await capture();
 await check("all preexisting business rows unchanged excluding only three new profiles and two fixture workspaces",async()=>assert.deepEqual(report.after,report.before));
 report.migrations_after=await query("select version,name,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') sha256 from supabase_migrations.schema_migrations order by version /* fmz6e9 */");
 await check("all 34 migration records unchanged",async()=>assert.deepEqual(report.migrations_after,report.migrations_before));
 report.window=await query("select s.route,s.workspace,s.expires_at,s.expires_at<=s.created_at+interval '24 hours' within_24h,s.trainer_id is null no_trainer from fmz6e9_private.subjects s order by route");
 assert.equal(report.window.length,2);assert(report.window.every(w=>w.within_24h));
 // Remove only our temporary test sessions; passwords remain unknown to the owner until recovery.
 for(const who of [a,trainer,b])await request(who,"/auth/v1/logout?scope=global",{});
 for(const who of [a,trainer,b]){
  report.emails.push({identity:report.accounts.find(x=>x.id===who.id).name,attempted_at:new Date().toISOString(),accepted:false});save();
  const sent=await broker({op:"recover",email:who.email});report.emails.at(-1).accepted=sent.accepted;save();
 }
 await broker({op:"retain"});report.active=true;save();
 console.log(JSON.stringify({active:true,expires_at:report.expires_at,checks:report.checks.length,browser:report.browser,start:report.start,mail_requests:report.emails.length}));
}catch(e){
 report.failure={message:e instanceof assert.AssertionError?"assertion_failed: "+e.message.split("\n")[0]:e.message};save();
 console.error("OWNER_WINDOW_FAILED",report.failure.message);process.exitCode=1;
}finally{
 proc.stdin.end();await new Promise(resolve=>proc.once("exit",resolve));
 for(const who of Object.values(accounts)){who.password=null;who.token=null;}
}
