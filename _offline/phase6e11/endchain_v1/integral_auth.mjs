// Local CI only. Ephemeral credentials travel exclusively over private pipes.
import readline from 'node:readline';
import assert from 'node:assert/strict';
import {SyntheticAuth,EMAILS} from '../controller_v1/auth.mjs';
import {guardedIssuance} from '../controller_guard_v1/issuance.mjs';
import {metadata,Controller,sha} from '../controller_v1/core.mjs';
import {NativeStore} from './native_store.mjs';
import {ENDCHAIN_RUN_ID,PURPOSE} from './budget.mjs';
import {bindSession} from '../auth_metadata_v1/hashes.mjs';
const lines=readline.createInterface({input:process.stdin,terminal:false})[Symbol.asyncIterator]();
const read=async()=>JSON.parse((await lines.next()).value);
const send=async value=>{process.stdout.write(JSON.stringify(value)+'\n');const reply=await read();if(reply.error)throw Error(reply.error);return reply.value;};
const config=await read(),origin='https://mokxyyullfhkfalopbzd.supabase.co';
if(config.mode!=='disposable_ci'||config.url!=='http://127.0.0.1:59999')throw Error('ci_boundary');
const localFetch=(url,options)=>{
 const p=new URL(url);
 if(p.origin!==origin||!p.pathname.startsWith('/auth/v1/'))throw Error('network_boundary');
 return fetch(config.url+p.pathname.slice('/auth/v1'.length)+p.search,options);
};
let guard,receipt,controller,protocolCount=0;
const auths={},ids={},proof=[],tokens={};
const query=async(sql,args)=>{
 const result=await send({op:'evidence_query',sql,args});protocolCount=result.commandCount;return result.rows;
};
async function action(role,operation){
 let before,after,result;
 const c={step:controller.step,actor:ids[role],action_id:crypto.randomUUID(),request_id:crypto.randomUUID(),
  workspace:null,kind:'auth',operation:operation==='getUser'?'get_user':operation,
  writes:config.authContracts[operation]};
 await controller.execute(c,{
 measure:async side=>{
  if(side==='before'){
   before=await send({op:'before',role,operation,action:c.action_id});
   return {sha256:await sha(before),count:0};
  }
  after=await send({op:'after',role,operation,before,result});
  return {sha256:await sha(after),count:after.events.length};
 },act:async()=>{
 if(operation==='revoked_denial'){
  const response=await localFetch(origin+'/auth/v1/user',{method:'GET',redirect:'error',signal:AbortSignal.timeout(5000),
   headers:{Authorization:'Bearer '+tokens[role],apikey:config.anon}});
  assert.equal(response.status,403);await response.arrayBuffer();result={http_status:response.status};tokens[role]=null;
 }else{
  result=metadata(await auths[role][operation]());
  if(operation!=='issue')result=await bindSession(auths[role],result);
  if(operation==='refresh')await auths[role].withToken(token=>{tokens[role]=token;});
 }
 return result;
 },validate:async()=>{
  if(after.pair_complete!==true||after.exact_contract!==true)throw Error('ci_auth_exact_pair');
  return {pair_complete:true,protected_equal:true,count:after.events.length};
 }});
 proof.push({role,operation,result,after});
}
try{
 for(const role of Object.keys(EMAILS)){
  const response=await localFetch(origin+'/auth/v1/admin/users',{method:'POST',redirect:'error',signal:AbortSignal.timeout(5000),
   headers:{Authorization:'Bearer '+config.admin,'Content-Type':'application/json'},body:JSON.stringify({email:EMAILS[role],email_confirm:true})});
  if(!response.ok)throw Error('ci_auth_seed');ids[role]=(await response.json()).id;
 }
 receipt=await send({op:'install',ids});
 const grant={project:'mokxyyullfhkfalopbzd',id:ENDCHAIN_RUN_ID,budget_ref:PURPOSE,run:'1',sha:config.sourceSha,
  manifest_sha:await sha(config.authContracts),starts:Date.now(),expires:Date.parse(receipt.expires_at)};
 controller=new Controller({grant,store:new NativeStore(query),maxCommands:1280});await controller.claim();
 guard=guardedIssuance({receipt,query:(sql,args=[])=>send({op:'query',sql,args}),check:()=>{}});
 for(const role of Object.keys(EMAILS)){
  const expected={id:ids[role],role,trainer_id:role==='a_member'?ids.a_trainer:null};
  const identity={...expected,email:EMAILS[role],registered_role:role,profile_role:role==='a_trainer'?'trainer':'client',enabled:true,operator:role==='a_trainer'};
  auths[role]=new SyntheticAuth({expected,identity,key:config.anon,admin:config.admin,fetcher:localFetch,guard});
  for(const operation of ['issue','verify','getUser','refresh'])await action(role,operation);
 }
 // The receiving CI adapter is loopback-only. These are never artifact fields.
 const workflow=await send({op:'workflow',tokens,anon:config.anon,ids,controllerContext:{grant,step:controller.step}});
 if(workflow.next_step!==83)throw Error('ci_workflow_step_chain');controller.step=workflow.next_step;
 for(const role of Object.keys(EMAILS))for(const operation of ['logout','revoked_denial'])await action(role,operation);
 guard.close();const removed=await send({op:'remove',receipt});receipt=null;
 if(removed.removed!==true)throw Error('ci_guard_removal');protocolCount=removed.commandCount;
 if(controller.step!==89)throw Error('ci_durable_sequence');
 // Local capacity study: do not falsify the M44 command count to close a run
 // larger than the owner-approved cap. Its budget rejection is retained.
 let closure='not_confirmed';
 try{await controller.store.close(grant.id,true,protocolCount+1);closure='confirmed';}
 catch(e){if(e.phase!=='evidence'||e.code!=='close_budget')throw e;closure='approved_budget_rejected';}
 process.stdout.write(JSON.stringify({op:'complete',result:{status:'INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS',
  checks:proof.length,proof,workflow,durable_steps:controller.step,closure,protocolCount,
  hosted_requests:0,emails_sent:0}})+'\n');
}catch(error){
 if(guard)guard.close();
 if(receipt){try{await send({op:'remove',receipt});}catch{}}
 process.stdout.write(JSON.stringify({op:'failed',code:/^[a-z_]+[0-9]*$/.test(error.message)?error.message:'integral_auth_failed'})+'\n');process.exitCode=2;
}finally{
 for(const role of Object.keys(auths)){auths[role].clear();tokens[role]=null;}
 config.admin=null;config.anon=null;process.stdin.destroy();
}
