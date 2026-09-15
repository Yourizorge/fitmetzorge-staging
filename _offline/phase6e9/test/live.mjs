import fs from "node:fs";
import path from "node:path";
import cp from "node:child_process";
import crypto from "node:crypto";
import readline from "node:readline";
import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {C} from "../edge/core.mjs";
import {browserTest} from "./browser.mjs";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
const url="https://mokxyyullfhkfalopbzd.supabase.co";
const pub="sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT";
const python="C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const proc=cp.spawn(python,[path.join(root,"_offline/phase6e9/test/admin.py")],{windowsHide:true,stdio:["pipe","pipe","pipe"]});
const queue=[];let stderr="";proc.stderr.on("data",b=>stderr+=b);
readline.createInterface({input:proc.stdout}).on("line",line=>{
 const item=queue.shift();if(!item)return;
 const d=JSON.parse(line);d.ok?item.resolve(d.result):item.reject(Error(d.error+" "+(d.status||"")));
});
proc.on("exit",()=>{for(const q of queue)q.reject(Error("broker_exited"));});
function broker(d){return new Promise((resolve,reject)=>{queue.push({resolve,reject});proc.stdin.write(JSON.stringify(d)+"\n");});}
const query=sql=>broker({op:"query",sql});
const lit=x=>"'"+String(x).replaceAll("'","''")+"'";
const report={scope:"real staging Auth + Edge + REST/RLS; synthetic accounts only",at:new Date().toISOString(),checks:[],account_ids:[],cleanup:null};
const run=Date.now().toString(36),accounts={};
async function check(name,fn){try{await fn();report.checks.push({name,pass:true});console.log("PASS",name);}catch(e){report.checks.push({name,pass:false,error:e.message});throw e;}}
async function request(a,route,body,method="POST",headers={}){
 const r=await fetch(url+route,{method,headers:{apikey:pub,...(a?.token?{Authorization:"Bearer "+a.token}:{}),"Content-Type":"application/json",...headers},...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(30000)});
 const text=await r.text();let data;try{data=JSON.parse(text);}catch{data={error:"non_json_response"};}
 return {status:r.status,data};
}
const edge=(a,body)=>request(a,"/functions/v1/fmz6e9-synthetic",body);
async function read(a,w=a.workspace){const r=await edge(a,{op:"read",workspace:w});assert.equal(r.status,200,JSON.stringify(r.data));return r.data;}
async function cmd(a,action,data={},opts={}){
 const state=opts.state||await read(a,opts.workspace||a.workspace);
 return edge(a,{op:"command",workspace:state.workspace,expected:state.revision,key:opts.key||crypto.randomUUID(),command:{action,data}});
}
async function ok(a,action,data={},opts={}){const r=await cmd(a,action,data,opts);assert.equal(r.status,200,JSON.stringify(r.data));return r.data;}
const denied=r=>assert([400,401,403,409].includes(r.status),"expected denial, got "+r.status);
async function seed(name,route="B",trainer=null,fixture=true){
 const a={email:"6e9-"+run+"-"+name+"@example.invalid",password:crypto.randomBytes(24).toString("base64url")+"aA1!",workspace:crypto.randomUUID()};
 a.id=(await broker({op:"create",email:a.email,password:a.password})).id;report.account_ids.push(a.id);accounts[name]=a;
 await query("insert into public.profiles(id,role,name,email,trainer_id) values("+[lit(a.id),lit(route==="trainer"?"trainer":"client"),lit("Synthetic 6E9 "+name),lit(a.email),trainer?lit(trainer.id):"null"].join(",")+") /* fmz6e9 new IDs only */");
 if(fixture)await query("insert into fmz6e9_private.subjects(workspace,member_id,route,trainer_id,expires_at,active_version) values("+[lit(a.workspace),lit(a.id),lit(route),trainer?lit(trainer.id):"null","clock_timestamp()+interval '2 hours'",route==="A"?3:0].join(",")+")");
 const login=await request(null,"/auth/v1/token?grant_type=password",{email:a.email,password:a.password});assert.equal(login.status,200,"synthetic_login_failed "+login.status);
 a.token=login.data.access_token;return a;
}
try{
 const trainer=await seed("trainer","trainer",null,false),otherTrainer=await seed("other-trainer","trainer",null,false);
 const a=await seed("member-a","A",trainer),b=await seed("member-b");
 trainer.workspace=a.workspace;
 const plain=await seed("no-fixture","B",null,false);
 await check("standard-off feature flag blocks valid new account",async()=>{const r=await edge(a,{op:"read",workspace:a.workspace});assert.equal(r.status,503);assert.equal(r.data.error,"synthetic_disabled");});
 await broker({op:"proof"});
 await check("real Auth/Edge session accepted and route derived by server",async()=>{
 let r;for(let i=0;i<12;i++){r=await edge(a,{op:"read",workspace:a.workspace});if(r.status===200)break;await new Promise(f=>setTimeout(f,5000));}
 assert.equal(r.status,200,JSON.stringify(r.data));assert.equal(r.data.route,"A");assert.equal(r.data.actor_role,"member");
 });
 if(!process.argv.includes("--browser-only")){
 await check("unauthenticated Edge and REST RPC denied",async()=>{
 denied(await edge(null,{op:"home"}));denied(await request(null,"/rest/v1/rpc/fmz6e9_home",{}));
 });
 await check("member B cannot read member A; unrelated trainer cannot read A",async()=>{
 denied(await edge(b,{op:"read",workspace:a.workspace}));denied(await edge(otherTrainer,{op:"read",workspace:a.workspace}));
 });
 await check("non-fixture principal denied without using any real member",async()=>denied(await edge(plain,{op:"home"})));
 await check("direct authenticated RPC requires server proof; private schema not exposed",async()=>{
 denied(await request(a,"/rest/v1/rpc/fmz6e9_read",{p_workspace:a.workspace}));
 const r=await request(a,"/rest/v1/subjects?select=* ",undefined,"GET",{"Accept-Profile":"fmz6e9_private"});assert.notEqual(r.status,200);
 });
 await check("client role/user/trainer/route/private payload tampering denied",async()=>{
 for(const key of ["role","user","trainer","route","chat","health","photo_url"]){
 const r=await edge(a,{op:"command",workspace:a.workspace,expected:0,key:crypto.randomUUID(),command:{action:"open",data:{[key]:"forged"}}});denied(r);}
 denied(await edge(a,{op:"home",role:"trainer"}));
 });
 await check("editable user metadata cannot grant trainer authority",async()=>{
 const r=await request(a,"/auth/v1/user",{data:{role:"trainer",trainer_id:trainer.id,route:"B"}},"PUT");assert.equal(r.status,200);
 denied(await cmd(a,"trainer_approve"));
 });
 await ok(a,"open");
 await check("A apply denied before both approvals",async()=>{denied(await cmd(trainer,"apply"));await ok(a,"member_accept");denied(await cmd(trainer,"apply"));});
 await check("duplicate acceptance/approval with fresh keys cannot advance twice",async()=>{
 denied(await cmd(a,"member_accept"));await ok(trainer,"trainer_approve");denied(await cmd(trainer,"trainer_approve"));
 });
 await check("A separate apply and idempotent retry create exactly one version",async()=>{
 const state=await read(trainer),key=crypto.randomUUID();const first=await ok(trainer,"apply",{},{state,key});
 const retry=await ok(trainer,"apply",{},{state,key});assert.equal(first.version,4);assert.equal(retry.receipt.replay,true);assert.equal(retry.versions.length,2);
 denied(await cmd(trainer,"apply"));denied(await cmd(trainer,"trainer_reject",{},{state,key}));
 });
 await check("A restore requires new approvals and immutable new version",async()=>{
 await ok(a,"restore",{version:3});denied(await cmd(trainer,"apply"));await ok(a,"member_accept");denied(await cmd(trainer,"apply"));
 await ok(trainer,"trainer_approve");assert.equal((await ok(trainer,"apply")).version,5);
 });
 await check("B intake plus edits invalidates prior confirmation",async()=>{
 await ok(b,"build",{intake:C.defaults});await ok(b,"confirm");await ok(b,"edit",{kind:"sleep",hours:9});denied(await cmd(b,"apply"));
 });
 await check("concurrent real Edge apply is atomic and expected-version protected",async()=>{
 await ok(b,"confirm");const state=await read(b);
 const r=await Promise.all([cmd(b,"apply",{},{state}),cmd(b,"apply",{},{state})]);
 assert.equal(r.filter(x=>x.status===200).length,1);assert.equal((await read(b)).version,1);
 });
 await check("REST audit/notices respect ownership and direct writes are denied",async()=>{
 const other=await request(b,"/rest/v1/fmz6e9_audit?workspace=eq."+a.workspace,undefined,"GET");assert.equal(other.status,200);assert.deepEqual(other.data,[]);
 const notice=await request(trainer,"/rest/v1/fmz6e9_notices?recipient=eq."+a.id,undefined,"GET");assert.deepEqual(notice.data,[]);
 denied(await request(a,"/rest/v1/fmz6e9_audit",{workspace:a.workspace},"POST"));
 denied(await request(a,"/rest/v1/rpc/fmz6e9_commit",{p_workspace:a.workspace,p_key:crypto.randomUUID(),p_expected:0,p_action:"apply",p_payload:{},p_basis:{},p_next:{}}));
 });
 await check("trainer unlink blocks A; linked trainer blocks B without route fallback",async()=>{
 await query("update public.profiles set trainer_id=null where id="+lit(a.id)+" /* fmz6e9 */");denied(await edge(a,{op:"read",workspace:a.workspace}));
 await query("update public.profiles set trainer_id="+lit(trainer.id)+" where id="+lit(a.id)+" /* fmz6e9 */");
 await query("update public.profiles set trainer_id="+lit(trainer.id)+" where id="+lit(b.id)+" /* fmz6e9 */");denied(await edge(b,{op:"read",workspace:b.workspace}));
 await query("update public.profiles set trainer_id=null where id="+lit(b.id)+" /* fmz6e9 */");
 });
 await check("changed source basis invalidates old approval",async()=>{
 await ok(b,"reopen");await ok(b,"confirm");
 await query("update fmz6e9_private.subjects set eligibility_revision=eligibility_revision+1 where workspace="+lit(b.workspace));
 denied(await cmd(b,"apply"));
 });
 await check("revoked consent blocks mutating request but retains read access",async()=>{
 await query("update fmz6e9_private.subjects set consent=false,consent_revision=consent_revision+1 where workspace="+lit(b.workspace));
 assert.equal((await read(b)).consent,false);denied(await cmd(b,"apply"));
 await query("update fmz6e9_private.subjects set consent=true,consent_revision=consent_revision+1 where workspace="+lit(b.workspace));
 });
 await check("forced transaction fault leaves version, audit, notices and requests unchanged",async()=>{
 await ok(b,"edit",{kind:"sleep",hours:8});await ok(b,"confirm");
 const count=()=>query("select (select count(*) from fmz6e9_private.versions) v,(select count(*) from public.fmz6e9_audit) a,(select count(*) from public.fmz6e9_notices) n,(select count(*) from fmz6e9_private.requests) r");
 const before=await count();
 await query("create function fmz6e9_private.test_fault() returns trigger language plpgsql as $$begin if NEW.workspace="+lit(b.workspace)+"::uuid then raise exception 'forced_6e9_fault';end if;return NEW;end$$;revoke all on function fmz6e9_private.test_fault() from public,anon,authenticated,service_role;create trigger test_fault before insert on fmz6e9_private.requests for each row execute function fmz6e9_private.test_fault()");
 try{denied(await cmd(b,"apply"));assert.deepEqual(await count(),before);}
 finally{await query("drop trigger test_fault on fmz6e9_private.requests;drop function fmz6e9_private.test_fault()");}
 assert.equal((await ok(b,"apply")).version,2);
 });
 await check("rejection prevents activation",async()=>{await ok(b,"reopen");await ok(b,"reject");denied(await cmd(b,"apply"));});
 await check("multiple safety references survive clarification and O5 expiry gives no clearance",async()=>{
 await query("insert into fmz6e9_private.safety values("+lit(b.workspace)+",clock_timestamp(),"+lit(crypto.randomUUID())+",'technical',true),("+lit(b.workspace)+",clock_timestamp(),"+lit(crypto.randomUUID())+",'current',true)");
 await ok(b,"clarify",{source:"syn-new-clear-context@1"});assert.equal((await read(b)).guard,"current");denied(await cmd(b,"reopen"));
 await query("update fmz6e9_private.safety set first_registered_at=clock_timestamp()-interval '30 days',status='self_reported' where workspace="+lit(b.workspace));
 assert.equal((await read(b)).guard,"missing");assert.equal((await read(b)).guard,"missing");
 assert.equal((await query("select count(*)::int n from fmz6e9_private.safety where workspace="+lit(b.workspace)))[0].n,0);
 });
 await check("no sensitive fields accepted/stored in minimal audits and notices",async()=>{
 const rows=await query("select row_to_json(a) d from public.fmz6e9_audit a limit 1");
 assert.deepEqual(Object.keys(rows[0].d).sort(),["id","workspace","actor","actor_role","action","proposal_hash","source_version","target_version","status","request_id","at"].sort());
 });
 await check("logged-out access token cannot reuse session for RPC/RLS",async()=>{
 const r=await request(a,"/auth/v1/logout?scope=local",{});assert.equal(r.status,204);
 denied(await edge(a,{op:"read",workspace:a.workspace}));
 const audit=await request(a,"/rest/v1/fmz6e9_audit?select=id",undefined,"GET");assert(audit.status!==200||audit.data.length===0);
 });
 }
 const bt=await seed("browser-trainer","trainer",null,false);
 const ba=await seed("browser-a","A",bt),bb=await seed("browser-b");
 const browser=await browserTest({root,accounts:{memberA:ba,trainerA:bt,memberB:bb},label:process.argv.includes("--published")?"published":"hosted",published:process.argv.includes("--published")});
 report.browser={checks:browser.checks.length,layouts:browser.layouts,errors:browser.errors};
 console.log(JSON.stringify(report.browser));
}finally{
 try{report.cleanup=await broker({op:"cleanup"});}
 finally{
 proc.stdin.end();await new Promise(resolve=>proc.once("exit",resolve));
 fs.writeFileSync(path.join(root,"supabase/.temp/phase6e9-live"+(process.argv.includes("--browser-only")?"-browser":"")+".json"),JSON.stringify(report,null,2)+"\n");
 }
}
console.log(JSON.stringify({checks:report.checks.length,cleanup:report.cleanup}));
