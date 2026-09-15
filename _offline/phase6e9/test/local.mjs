import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import cp from "node:child_process";
import crypto from "node:crypto";
import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {next,C,present} from "../edge/core.mjs";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
const bin="C:/Program Files/PostgreSQL/18/bin",port=55991;
const work=fs.mkdtempSync(path.join(os.tmpdir(),"fmz6e9-local-"));
const report={scope:"synthetic local PostgreSQL authorization/transitions; not hosted Auth/REST",at:new Date().toISOString(),checks:[],cluster:work,deleted_files:0};
let server;
const run=(name,args,input)=>{const r=cp.spawnSync(path.join(bin,name+".exe"),args,{input,encoding:"utf8",windowsHide:true,maxBuffer:2000000,timeout:60000});if(r.status!==0)throw Error(r.stderr||r.stdout||"local_process_failed");return r.stdout;};
const sql=q=>run("psql",["-h","127.0.0.1","-p",String(port),"-U","postgres","-d","postgres","-v","ON_ERROR_STOP=1","-At"],q);
const concurrent=q=>new Promise((resolve,reject)=>{
 const p=cp.spawn(path.join(bin,"psql.exe"),["-h","127.0.0.1","-p",String(port),"-U","postgres","-d","postgres","-v","ON_ERROR_STOP=1","-At"],{windowsHide:true});
 let out="",err="";p.stdout.on("data",b=>out+=b);p.stderr.on("data",b=>err+=b);
 p.on("error",reject);p.on("close",code=>code===0?resolve(value(out)):reject(Error(err)));p.stdin.end(q);
});
const uuid=n=>"69000000-0000-4000-8000-"+String(n).padStart(12,"0");
const lit=x=>"'"+String(x).replaceAll("'","''")+"'";
const j=x=>lit(JSON.stringify(x))+"::jsonb";
const actor=(n,q,proof=true)=>"begin;set local role authenticated;select set_config('request.jwt.claims',"+j({sub:uuid(n),session_id:uuid(n+100)})+"::text,true);select set_config('request.headers',"+j(proof?{"x-fmz6e9-proof":"test-only-proof"}:{})+"::text,true);"+q+";commit;";
function value(out){return JSON.parse(out.trim().split(/\r?\n/).filter(x=>x.startsWith("{")||x.startsWith("[")||x==="null").at(-1));}
const read=(n,w)=>value(sql(actor(n,"select public.fmz6e9_read("+lit(uuid(w))+"::uuid)")));
const qcommit=(n,w,key,rev,command,row,result)=>actor(n,"select public.fmz6e9_commit("+[lit(uuid(w)),lit(uuid(key)),rev,lit(command.action),j(command.data),j(row.basis),j({event:result.event,status:result.status,version:result.version,content:result.content,candidate_hash:result.candidate_hash})].join(",")+")");
async function command(n,w,action,data={},key=crypto.randomInt(10000,999999)){
 const row=read(n,w),c={action,data},r=await next(row,c);
 return value(sql(qcommit(n,w,key,row.revision,c,row,r)));
}
function seed(w,member,trainer=null,seed="normal"){
 sql("insert into fmz6e9_private.subjects(workspace,member_id,route,trainer_id,seed,expires_at,active_version) values("+[lit(uuid(w)),lit(uuid(member)),lit(trainer?"A":"B"),trainer?lit(uuid(trainer)):"null",lit(seed),"clock_timestamp()+interval '6 hours'",trainer?3:0].join(",")+")");
}
async function check(name,fn){try{await fn();report.checks.push({name,pass:true});console.log("PASS",name);}catch(e){report.checks.push({name,pass:false,error:e.message});throw e;}}
const deny=(n,q,match=/denied|permission|conflict|required|order|invalid|block/)=>assert.throws(()=>sql(actor(n,q)),match);
try{
 run("initdb",["-D",path.join(work,"data"),"-A","trust","-U","postgres"]);
 server=cp.spawn(path.join(bin,"postgres.exe"),["-D",path.join(work,"data"),"-p",String(port),"-h","127.0.0.1"],{windowsHide:true,stdio:"ignore"});
 let ready=false;for(let i=0;i<100;i++){try{sql("select 1");ready=true;break;}catch{await new Promise(r=>setTimeout(r,100));}}
 assert(ready);
 sql("create role anon;create role authenticated;create role service_role;create schema auth;create table auth.users(id uuid primary key);create table auth.sessions(id uuid primary key,user_id uuid);create function auth.uid() returns uuid language sql stable as $$select (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid$$;grant usage on schema auth to authenticated;grant execute on function auth.uid() to authenticated;create table public.profiles(id uuid primary key,role text,trainer_id uuid,updated_at timestamptz not null default now());");
 sql("alter table auth.sessions add column not_after timestamptz");
 sql(fs.readFileSync(path.join(root,"supabase/migrations/20260915072202_phase6e9_synthetic_authorization.sql"),"utf8"));
 for(let n=1;n<=16;n++)sql("insert into auth.users values("+lit(uuid(n))+");insert into auth.sessions(id,user_id) values("+lit(uuid(n+100))+","+lit(uuid(n))+");insert into public.profiles(id,role,trainer_id) values("+lit(uuid(n))+","+lit([3,4].includes(n)?"trainer":"client")+","+(n===1?lit(uuid(3)):"null")+")");
 await check("standard-off gate denies even valid fixture JWT",()=>assert.throws(()=>read(1,501),/denied/));
 sql("update fmz6e9_private.config set enabled=true,proof_hash=encode(sha256(convert_to('test-only-proof','UTF8')),'hex')");
 seed(501,1,3);seed(502,2);
 await check("anonymous RPC EXECUTE denied",()=>assert.throws(()=>sql("set role anon;select public.fmz6e9_read("+lit(uuid(501))+")"),/permission/));
 await check("authenticated direct RPC without server proof denied",()=>assert.throws(()=>sql(actor(1,"select public.fmz6e9_read("+lit(uuid(501))+")",false)),/denied/));
 await check("other member denied",()=>assert.throws(()=>read(2,501),/denied/));
 await check("unrelated trainer denied",()=>assert.throws(()=>read(4,501),/denied/));
 await check("ordinary non-fixture user denied",()=>assert.throws(()=>read(16,501),/denied/));
 await check("client cannot update private state",()=>deny(1,"update fmz6e9_private.subjects set route='B'"));
 await check("client cannot insert audit or notices",()=>deny(1,"insert into public.fmz6e9_notices(workspace,recipient,code,request_id) values("+[lit(uuid(501)),lit(uuid(1)),"'applied'",lit(uuid(999))].join(",")+")"));
 await check("A member opens checked candidate",()=>command(1,501,"open"));
 await check("A cannot apply before approvals",()=>assert.rejects(()=>command(3,501,"apply")));
 await check("member cannot impersonate trainer",()=>assert.rejects(()=>command(1,501,"trainer_approve"),/actor/));
 await check("A member accepts",()=>command(1,501,"member_accept"));
 await check("A still cannot apply without trainer",()=>assert.rejects(()=>command(3,501,"apply")));
 await check("A trainer approves exact candidate",()=>command(3,501,"trainer_approve"));
 await check("A separate apply increments to version 4",async()=>assert.equal((await command(3,501,"apply")).version,4));
 await check("A duplicate fresh-key apply denied",()=>assert.rejects(()=>command(3,501,"apply")));
 await check("A restore is a new unapproved proposal",async()=>{assert.equal((await command(1,501,"restore",{version:3})).status,"member_pending");await assert.rejects(()=>command(3,501,"apply"));});
 await check("A restore requires both approvals and makes version 5",async()=>{await command(1,501,"member_accept");await command(3,501,"trainer_approve");assert.equal((await command(3,501,"apply")).version,5);});
 await check("B complete intake/build",()=>command(2,502,"build",{intake:C.defaults}));
 await check("B no trainer action",()=>assert.rejects(()=>command(2,502,"trainer_approve")));
 await check("B edit keeps complete bundle",()=>command(2,502,"edit",{kind:"sleep",hours:9}));
 await check("B member confirms",()=>command(2,502,"confirm"));
 await check("B edit invalidates confirmation",async()=>{await command(2,502,"edit",{kind:"sleep",hours:8});await assert.rejects(()=>command(2,502,"apply"));});
 await command(2,502,"confirm");
 let saved;
 await check("B apply commits all components at once",async()=>{const row=read(2,502),c={action:"apply",data:{}},r=await next(row,c);saved=qcommit(2,502,123456,row.revision,c,row,r);assert.equal(value(sql(saved)).version,1);});
 await check("same-key retry returns replay, one version only",()=>{assert.equal(value(sql(saved)).replay,true);assert.equal(sql("select count(*) from fmz6e9_private.versions where workspace="+lit(uuid(502))).trim(),"1");});
 await check("same-key different payload rejected",()=>assert.throws(()=>sql(saved.replace("'apply'","'reject'")),/idempotency_conflict/));
 await check("audit RLS hides unrelated workspace",()=>{const out=sql(actor(2,"select jsonb_build_object('n',count(*)) from public.fmz6e9_audit where workspace="+lit(uuid(501))));assert.equal(value(out).n,0);});
 await check("notice RLS only recipient",()=>{const out=sql(actor(3,"select jsonb_build_object('n',count(*)) from public.fmz6e9_notices where recipient="+lit(uuid(1))));assert.equal(value(out).n,0);});
 await check("linked trainer can inspect training audit",()=>assert(value(sql(actor(3,"select jsonb_build_object('n',count(*)) from public.fmz6e9_audit where workspace="+lit(uuid(501))))).n>0));
 await check("revoked session denied including direct RLS",()=>{sql("delete from auth.sessions where user_id="+lit(uuid(3)));assert.throws(()=>read(3,501),/session_required/);assert.equal(value(sql(actor(3,"select jsonb_build_object('n',count(*)) from public.fmz6e9_audit"))).n,0);sql("insert into auth.sessions(id,user_id) values("+lit(uuid(103))+","+lit(uuid(3))+")");});
 await check("trainer link loss blocks A without fallback",()=>{sql("update public.profiles set trainer_id=null where id="+lit(uuid(1)));assert.throws(()=>read(1,501),/authority_conflict/);sql("update public.profiles set trainer_id="+lit(uuid(3))+" where id="+lit(uuid(1)));});
 await check("B linked trainer conflicts, not converted to A",()=>{sql("update public.profiles set trainer_id="+lit(uuid(3))+" where id="+lit(uuid(2)));assert.throws(()=>read(2,502),/authority_conflict/);sql("update public.profiles set trainer_id=null where id="+lit(uuid(2)));});
 await check("revoked consent retains reads but blocks mutation",async()=>{sql("update fmz6e9_private.subjects set consent=false,consent_revision=consent_revision+1 where workspace="+lit(uuid(502)));assert.equal(read(2,502).consent,false);await assert.rejects(()=>command(2,502,"reopen"),/consent/);sql("update fmz6e9_private.subjects set consent=true where workspace="+lit(uuid(502)));});
 await check("expired O5 record removed and missing context persists",async()=>{sql("insert into fmz6e9_private.safety values("+lit(uuid(502))+",clock_timestamp()-interval '30 days',"+lit(uuid(700))+",'self_reported',true)");assert.equal(read(2,502).guard,"missing");assert.equal(read(2,502).guard,"missing");assert.equal(sql("select count(*) from fmz6e9_private.safety").trim(),"0");await assert.rejects(()=>command(2,502,"reopen"),/safety/);});
 await check("source and source-version bound data remain unchanged after denials",()=>assert.equal(read(2,502).versions.length,1));
 seed(505,5);
 await command(5,505,"build",{intake:C.defaults});await command(5,505,"confirm");
 await check("concurrent different-key application commits exactly once",async()=>{
 const row=read(5,505),c={action:"apply",data:{}},result=await next(row,c);
 const outcomes=await Promise.allSettled([81001,81002].map(k=>concurrent(qcommit(5,505,k,row.revision,c,row,result))));
 assert.equal(outcomes.filter(x=>x.status==="fulfilled").length,1);
 assert.equal(read(5,505).versions.length,1);
 });
 seed(506,6);await command(6,506,"build",{intake:C.defaults});await command(6,506,"confirm");
 await check("concurrent same-key application returns one result plus replay",async()=>{
 const row=read(6,506),c={action:"apply",data:{}},result=await next(row,c),q=qcommit(6,506,81003,row.revision,c,row,result);
 const outcomes=await Promise.all([concurrent(q),concurrent(q)]);
 assert.equal(outcomes.filter(x=>x.replay).length,1);assert.equal(read(6,506).versions.length,1);
 });
 seed(507,7);await command(7,507,"build",{intake:C.defaults});await command(7,507,"confirm");
 await check("concurrent apply and edit cannot partially merge",async()=>{
 const row=read(7,507),c={action:"apply",data:{}},e={action:"edit",data:{kind:"sleep",hours:9}};
 const results=await Promise.allSettled([
 concurrent(qcommit(7,507,81004,row.revision,c,row,await next(row,c))),
 concurrent(qcommit(7,507,81005,row.revision,e,row,await next(row,e)))]);
 assert.equal(results.filter(x=>x.status==="fulfilled").length,1);
 const after=read(7,507);assert.equal(after.revision,row.revision+1);
 assert.equal(after.versions.length,after.status==="applied"?1:0);
 });
 seed(508,8);await command(8,508,"build",{intake:C.defaults});await command(8,508,"confirm");
 await check("fault after version/audit/notice insert rolls back entire transaction",async()=>{
 sql("create function fmz6e9_private.test_fault() returns trigger language plpgsql as $$begin raise exception 'forced_fault';end$$;create trigger test_fault before insert on fmz6e9_private.requests for each row execute function fmz6e9_private.test_fault()");
 const before=read(8,508);
 await assert.rejects(()=>command(8,508,"apply"),/forced_fault/);
 const after=read(8,508);assert.deepEqual(after,before);
 assert.equal(value(sql("select jsonb_build_object('n',count(*)) from public.fmz6e9_audit where workspace="+lit(uuid(508)))).n,2);
 sql("drop trigger test_fault on fmz6e9_private.requests;drop function fmz6e9_private.test_fault()");
 assert.equal((await command(8,508,"apply")).version,1);
 });
 seed(509,9);await command(9,509,"build",{intake:C.defaults});
 await check("changed source revision invalidates prior proposal approval",async()=>{
 sql("update fmz6e9_private.config set source_revision=source_revision+1");
 await assert.rejects(()=>command(9,509,"confirm"),/source_conflict/);
 });
 seed(510,10);await command(10,510,"build",{intake:C.defaults});await command(10,510,"reject");
 await check("rejected proposal cannot activate",()=>assert.rejects(()=>command(10,510,"apply")));
 await check("unknown free text/private health/photo fields never enter command log",async()=>{
 for(const forbidden of ["user","role","trainer","route","chat","health","photo_url"]){
 const row=read(10,510),c={action:"reopen",data:{[forbidden]:"private content"}};
 await assert.rejects(()=>next(row,c),/payload_invalid/);
 }
 });
 await check("unnecessary O5 record removed before maximum without clearance",()=>{
 sql("insert into fmz6e9_private.safety values("+lit(uuid(510))+",clock_timestamp(),"+lit(uuid(701))+",'current',false)");
 assert.equal(read(10,510).guard,"missing");
 assert.equal(sql("select count(*) from fmz6e9_private.safety where workspace="+lit(uuid(510))).trim(),"0");
 });
 await check("subject expiry denies all access",()=>{
 sql("update fmz6e9_private.subjects set expires_at=clock_timestamp()-interval '1 second' where workspace="+lit(uuid(509)));
 assert.throws(()=>read(9,509),/denied/);
 });
 await check("all private tables RLS enabled and no authenticated writes",()=>{
 assert.equal(value(sql("select jsonb_build_object('n',count(*)) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='fmz6e9_private' and c.relkind='r' and (not c.relrowsecurity or has_table_privilege('authenticated',c.oid,'INSERT,UPDATE,DELETE'))")).n,0);
 });
 seed(511,11);await command(11,511,"build",{intake:C.defaults});await command(11,511,"confirm");
 await check("consent revocation winning lock prevents concurrent application",async()=>{
 const row=read(11,511),c={action:"apply",data:{}},r=await next(row,c);
 const revoke=concurrent("begin;update fmz6e9_private.subjects set consent=false,consent_revision=consent_revision+1 where workspace="+lit(uuid(511))+";select pg_sleep(0.4);select '{}'::jsonb;commit;");
 await new Promise(resolve=>setTimeout(resolve,100));
 const results=await Promise.allSettled([revoke,concurrent(qcommit(11,511,81101,row.revision,c,row,r))]);
 assert.equal(results[0].status,"fulfilled");assert.equal(results[1].status,"rejected");assert.equal(read(11,511).versions.length,0);
 });
 seed(515,15);await command(15,515,"build",{intake:C.defaults});
 await check("clarification removes communication only, never another health report",async()=>{
 sql("insert into fmz6e9_private.safety values("+lit(uuid(515))+",clock_timestamp(),"+lit(uuid(715))+",'technical',true),("+lit(uuid(515))+",clock_timestamp(),"+lit(uuid(716))+",'current',true)");
 assert.equal(read(15,515).guard,"current");
 await command(15,515,"clarify",{source:"syn-new-clear-context@1"});
 assert.equal(read(15,515).guard,"current");
 assert.equal(sql("select count(*) from fmz6e9_private.safety where workspace="+lit(uuid(515))).trim(),"1");
 await assert.rejects(()=>command(15,515,"confirm"),/safety/);
 });
 await check("O5 status changes and retries cannot renew first registration",()=>{
 sql("update fmz6e9_private.safety set first_registered_at=clock_timestamp()-interval '29 days 23 hours',status='self_reported' where workspace="+lit(uuid(515)));
 const first=sql("select first_registered_at from fmz6e9_private.safety where workspace="+lit(uuid(515)));
 read(15,515);read(15,515);
 assert.equal(sql("select first_registered_at from fmz6e9_private.safety where workspace="+lit(uuid(515))),first);
 sql("update fmz6e9_private.safety set first_registered_at=clock_timestamp()-interval '30 days' where workspace="+lit(uuid(515)));
 assert.equal(read(15,515).guard,"missing");
 assert.equal(sql("select count(*) from fmz6e9_private.safety where workspace="+lit(uuid(515))).trim(),"0");
 });
 if(process.argv.includes("--browser")){
 const {createHandler}=await import("../edge/handler.mjs"),{browserTest}=await import("./browser.mjs");
 sql("update public.profiles set role='trainer' where id="+lit(uuid(13))+";update public.profiles set trainer_id="+lit(uuid(13))+" where id="+lit(uuid(12)));
 seed(512,12,13);seed(514,14);
 const accounts={memberA:{email:"6e9-local-a@example.invalid",password:"SyntheticOnly-123456!",n:12},trainerA:{email:"6e9-local-t@example.invalid",password:"SyntheticOnly-123456!",n:13},memberB:{email:"6e9-local-b@example.invalid",password:"SyntheticOnly-123456!",n:14}};
 async function upstream(url,options={}){
 const req=url instanceof Request?url:new Request(url,options),u=new URL(req.url),origin=req.headers.get("origin")||"http://127.0.0.1:5189";
 const headers={"Content-Type":"application/json","Access-Control-Allow-Origin":origin,"Access-Control-Allow-Headers":"apikey,authorization,content-type","Access-Control-Allow-Methods":"POST,GET,OPTIONS"};
 const res=(status,data)=>new Response(status===204?null:JSON.stringify(data),{status,headers});
 if(req.method==="OPTIONS")return res(204,null);
 const bearer=req.headers.get("authorization")||"",n=Number(bearer.replace("Bearer test-token-",""));
 if(u.pathname==="/auth/v1/token"){
 const d=await req.json(),account=Object.values(accounts).find(a=>a.email===d.email&&a.password===d.password);
 const id=account?.n||Number(String(d.refresh_token).replace("test-refresh-",""));
 if(![12,13,14].includes(id))return res(401,{error:"invalid"});
 sql("insert into auth.sessions(id,user_id) values("+lit(uuid(id+100))+","+lit(uuid(id))+") on conflict(id) do nothing");
 return res(200,{access_token:"test-token-"+id,refresh_token:"test-refresh-"+id});
 }
 if(![12,13,14].includes(n))return res(401,{error:"invalid"});
 if(u.pathname==="/auth/v1/user")return res(200,{id:uuid(n)});
 if(u.pathname==="/auth/v1/logout"){sql("delete from auth.sessions where user_id="+lit(uuid(n)));return res(204,null);}
 try{
 let q;
 if(u.pathname.includes("/rpc/")){
 const name=u.pathname.split("/").at(-1),d=await req.json();
 const shape={fmz6e9_home:[],fmz6e9_read:["p_workspace"],fmz6e9_replay:["p_workspace","p_key","p_expected","p_action","p_payload"],fmz6e9_commit:["p_workspace","p_key","p_expected","p_action","p_payload","p_basis","p_next"]}[name];
 if(!shape)return res(404,{message:"denied"});
 q="select coalesce(public."+name+"("+shape.map(k=>typeof d[k]==="object"?j(d[k]):typeof d[k]==="number"?d[k]:lit(d[k])).join(",")+")::text,'null')";
 }else{
 const table=u.pathname.split("/").at(-1);
 if(!["fmz6e9_audit","fmz6e9_notices"].includes(table))return res(404,{message:"denied"});
 const workspace=u.searchParams.get("workspace")?.replace("eq.","");
 if(!/^[0-9a-f-]{36}$/.test(workspace))return res(400,{message:"denied"});
 q="select coalesce(jsonb_agg(to_jsonb(x) order by x.id),'[]') from public."+table+" x where workspace="+lit(workspace);
 }
 return res(200,value(sql(actor(n,q,req.headers.get("x-fmz6e9-proof")==="test-only-proof"))));
 }catch(e){console.log("LOCAL_TRANSPORT_FAILURE",e.message.slice(0,500));return res(403,{message:/synthetic_[a-z_]+/.exec(e.message)?.[0]||"synthetic_operation_denied"});}
 }
 const handler=createHandler({url:"https://mokxyyullfhkfalopbzd.supabase.co",key:"test-publishable",proof:"test-only-proof",fetcher:upstream});
 const transport=req=>new URL(req.url).pathname.includes("/functions/v1/")?handler(req):upstream(req);
 const browserResult=await browserTest({root,transport,accounts});
 report.browser={checks:browserResult.checks.length,layouts:browserResult.layouts,errors:browserResult.errors};
 console.log(JSON.stringify(report.browser));
 }
 console.log(JSON.stringify({pass:report.checks.length,fail:0,cluster:work,deleted_files:0}));
}finally{
 if(server){try{run("pg_ctl",["-D",path.join(work,"data"),"-m","fast","-w","stop"]);}finally{server.kill();}}
 fs.mkdirSync(path.join(root,"supabase/.temp"),{recursive:true});
 fs.writeFileSync(path.join(root,"supabase/.temp/phase6e9-local.json"),JSON.stringify(report,null,2)+"\n");
}
