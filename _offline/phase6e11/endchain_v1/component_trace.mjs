// Offline command trace of the existing adapters. No network or SQL execution.
import assert from 'node:assert/strict';
import {Store} from '../controller_v1/store.mjs';
import {createRequestTransport} from '../request_v4/transport.mjs';
import {guardedIssuance} from '../controller_guard_v1/issuance.mjs';
import {EMAILS} from '../controller_v1/auth.mjs';
import {LOCK_IDENTITY} from '../controller_v1/auth_guard.mjs';
const id=n=>'69000000-0000-4000-8000-'+String(n).padStart(12,'0');
const events=[];
const record=(label,query)=>{events.push({component:label,ordinal:events.filter(e=>e.component===label).length+1});
 return query;};
const store=new Store(async(q)=>{record('evidence',q);return [{phase:'pair_validated'}];});
await store.before(id(1),{step:0,action_id:id(2),request_id:id(3),actor:id(4),
 workspace:id(5),kind:'workflow',operation:'apply'}, {count:0},'a'.repeat(64));
for(const p of ['action_started','action_confirmed','after_saved','pair_validated'])
 await store.record(id(1),0,p,{count:0});

const fakePostgres=options=>{
 assert.equal(options.fetch_types,false);assert.equal(options.max,1);
 const tx={unsafe:async(q)=>{
  record('workflow',q);
  if(q.includes('as identity'))return [{identity:true,safe:true}];
  if(q.includes('.call('))return [{value:{status:'confirmed'}}];
  return [];
 }};
 return {begin:async action=>{
  record('workflow','BEGIN');
  const value=await action(tx);record('workflow','COMMIT');return value;
 },end:async()=>{}};
};
const transport=createRequestTransport({postgres:fakePostgres,
 connectionUrl:'postgres://postgres:synthetic-not-a-credential@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
 ca:'-----BEGIN CERTIFICATE----- synthetic-only',sessionHost:'aws-0-eu-west-2.pooler.supabase.com'});
await transport({requestId:id(3),input:{op:'synthetic'},claims:{sub:id(4)},proof:'synthetic-only'});
const schema='fmz6e11_guard_'+id(1).replaceAll('-','');
const trigger_shas=Object.fromEntries(['_d','_i','_u'].map(n=>[schema+n,'b'.repeat(64)]));
const expected={id:id(4),role:'a_member',trainer_id:id(6)};
const guard=guardedIssuance({receipt:{run:id(1),schema,function_sha:'a'.repeat(64),trigger_shas,
 expires_at:new Date(600000).toISOString()},now:()=>0,check:()=>{},query:async(q)=>{
 record('issuance_guard',q);
 if(q===LOCK_IDENTITY)return [{id:id(4),email:EMAILS.a_member,registered_role:'a_member',
   profile_role:'client',trainer_id:id(6),enabled:true,operator:false}];
 if(q.includes('function_sha'))return [{function_sha:'a'.repeat(64),unexpired:true,definer:false,
   acl:'{postgres=X/postgres}',search_path:['search_path=pg_catalog, pg_temp'],trigger_shas}];
 return [];
}});
await guard(expected,async()=>({status:'synthetic'}));guard.close();
const counts=Object.fromEntries(['evidence','workflow','issuance_guard'].map(c=>[c,events.filter(e=>e.component===c).length]));
assert.deepEqual(counts,{evidence:5,workflow:8,issuance_guard:6});
console.log(JSON.stringify({status:'OFFLINE_ADAPTER_TRACE_PASS',counts,events,
 hosted_calls:0,sql_executed:0,limitation:'Command shape only; this does not prove hosted execution or IO.'}));
