import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import cp from "node:child_process";
import crypto from "node:crypto";
import assert from "node:assert/strict";
import {fileURLToPath} from "node:url";
import {runScenarios} from "./scenarios.mjs";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
const bin="C:/Program Files/PostgreSQL/18/bin",port=55992;
const work=fs.mkdtempSync(path.join(os.tmpdir(),"fmz6e10-local-"));
const report={scope:"local PostgreSQL; Auth stubs, not hosted JWT proof",cluster:work,checks:[],errors:[]};
let server;
const exec=(name,args,input)=>{
 const r=cp.spawnSync(path.join(bin,name+".exe"),args,{input,encoding:"utf8",windowsHide:true,maxBuffer:5000000,timeout:60000});
 if(r.status!==0)throw Error(r.stderr||"local_process_failed");return r.stdout;
};
const sql=q=>exec("psql",["-h","127.0.0.1","-p",String(port),"-U","postgres","-d","postgres","-v","ON_ERROR_STOP=1","-At"],q);
const uuid=n=>"61000000-0000-4000-8000-"+String(n).padStart(12,"0");
const ids={member:uuid(1),trainer:uuid(2),b:uuid(3),plain:uuid(4),foreign:uuid(5)};
const lit=x=>"'"+String(x).replaceAll("'","''")+"'";
const j=x=>lit(JSON.stringify(x))+"::jsonb";
const value=s=>JSON.parse(s.trim().split(/\r?\n/).filter(x=>/^[\[{]/.test(x)||x==="null").at(-1));
const actor=(who,q,proof=true)=>"begin;set local role authenticated;select set_config('request.jwt.claims',"+j({sub:ids[who],session_id:uuid(Object.values(ids).indexOf(ids[who])+101)})+"::text,true);select set_config('request.headers',"+j(proof?{"x-fmz6e10-proof":"synthetic-only-local-proof"}:{})+"::text,true);"+q+";commit;";
const raw=async(who,body,proof=true)=>{
 try{return {status:200,data:value(sql(actor(who,"select public.fmz6e10_call("+j(body)+")",proof)))};}
 catch(e){return {status:/stale|conflict/.test(e.message)?409:403,data:{error:e.message}};}
};
try{
 exec("initdb",["-D",path.join(work,"data"),"-A","trust","-U","postgres"]);
 server=cp.spawn(path.join(bin,"postgres.exe"),["-D",path.join(work,"data"),"-p",String(port),"-h","127.0.0.1"],{windowsHide:true,stdio:"ignore"});
 for(let i=0;i<100;i++){try{sql("select 1");break;}catch{await new Promise(r=>setTimeout(r,100));}}
 sql("create role anon;create role authenticated;create role service_role;create schema auth;create table auth.users(id uuid primary key,email text);create table auth.sessions(id uuid primary key,user_id uuid,not_after timestamptz);create function auth.uid() returns uuid language sql stable as $$select (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid$$;grant usage on schema auth to authenticated;grant execute on function auth.uid() to authenticated;create table public.profiles(id uuid primary key,role text,email text,trainer_id uuid,updated_at timestamptz not null default now());");
 sql(fs.readFileSync(path.join(root,"supabase/migrations/20260915104711_phase6e10_sources_managed_windows.sql"),"utf8"));
 sql(fs.readFileSync(path.join(root,"supabase/migrations/20260916071416_phase6e10_source_reference_indexes.sql"),"utf8"));
 sql(fs.readFileSync(path.join(root,"supabase/migrations/20260916072203_phase6e10_strict_command_versions.sql"),"utf8"));
 sql(fs.readFileSync(path.join(root,"supabase/migrations/20260916073923_phase6e10_api_conflict_sqlstate.sql"),"utf8"));
 const aliases=["zorgeyouri+6e9-a-lid@gmail.com","zorgeyouri+6e9-a-trainer@gmail.com","zorgeyouri+6e9-b-lid@gmail.com","ordinary@example.invalid","foreign-trainer@example.invalid"];
 for(let i=0;i<5;i++){
  sql("insert into auth.users values("+lit(uuid(i+1))+","+lit(aliases[i])+");insert into auth.sessions(id,user_id) values("+lit(uuid(i+101))+","+lit(uuid(i+1))+");insert into public.profiles(id,role,email,trainer_id) values("+lit(uuid(i+1))+","+lit([1,4].includes(i)?"trainer":"client")+","+lit(aliases[i])+","+(i===0?lit(uuid(2)):"null")+")");
 }
 sql("insert into fmz6e10_private.identities(user_id,role,provenance_sha) values("+lit(ids.member)+",'a_member',repeat('a',64)),("+lit(ids.trainer)+",'a_trainer',repeat('a',64)),("+lit(ids.b)+",'b_member',repeat('a',64));insert into fmz6e10_private.operators values("+lit(ids.trainer)+",true);update fmz6e10_private.config set enabled=true,proof_hash=encode(sha256(convert_to('synthetic-only-local-proof','UTF8')),'hex')");
 const api={ids,raw,sql:async q=>sql(q),json:async q=>value(sql(q)),lit,j,
 fixture:async unit=>value(sql("select fmz6e10_private.fixture("+lit(unit)+")")),
 calculate:async(b,p,logs,v)=>value(sql("select fmz6e10_private.calculate("+[j(b),j(p),j(logs),v].join(",")+")")),
 concurrent:async(who,bodies)=>Promise.all(bodies.map(body=>new Promise(resolve=>{
  const p=cp.spawn(path.join(bin,"psql.exe"),["-h","127.0.0.1","-p",String(port),"-U","postgres","-d","postgres","-v","ON_ERROR_STOP=1","-At"],{windowsHide:true});
  let out="",err="";p.stdout.on("data",b=>out+=b);p.stderr.on("data",b=>err+=b);p.on("close",code=>resolve(code===0?{status:200,data:value(out)}:{status:409,data:{error:err}}));
  p.stdin.end(actor(who,"select public.fmz6e10_call("+j(body)+")"));
 }))),
 anonymous:async()=>{assert.throws(()=>sql("set role anon;select public.fmz6e10_call('{\"op\":\"home\"}')"),/permission/);},
 direct:async()=>{assert.throws(()=>sql("set role authenticated;select * from fmz6e10_private.source_versions"),/permission/);},
 };
 await runScenarios(api,report);
 report.pass=true;
}catch(e){report.errors.push(e.message);console.error(e.message);process.exitCode=1;}
finally{
 if(server){try{exec("pg_ctl",["-D",path.join(work,"data"),"-m","fast","-w","stop"]);}catch{server.kill();}}
 fs.mkdirSync(path.join(root,"supabase/.temp"),{recursive:true});fs.writeFileSync(path.join(root,"supabase/.temp/phase6e10-local.json"),JSON.stringify(report,null,2)+"\n");
}
console.log(JSON.stringify({pass:report.pass||false,checks:report.checks.length,cluster:work,deleted_files:0}));
