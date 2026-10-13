// Local CI only. Ephemeral credentials travel exclusively over private pipes.
import readline from 'node:readline';
import assert from 'node:assert/strict';
import {SyntheticAuth,EMAILS} from '../controller_v1/auth.mjs';
import {guardedIssuance} from '../controller_guard_v1/issuance.mjs';
import {metadata} from '../controller_v1/core.mjs';
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
let guard,receipt;
const auths={},ids={},proof=[],tokens={};
async function action(role,operation){
 const before=await send({op:'before',role,operation});
 let result;
 if(operation==='revoked_denial'){
  const response=await localFetch(origin+'/auth/v1/user',{method:'GET',redirect:'error',signal:AbortSignal.timeout(5000),
   headers:{Authorization:'Bearer '+tokens[role],apikey:config.anon}});
  assert.equal(response.status,403);await response.arrayBuffer();result={http_status:response.status};tokens[role]=null;
 }else{
  result=metadata(await auths[role][operation]());
  if(operation!=='issue')result=await bindSession(auths[role],result);
  if(operation==='refresh')await auths[role].withToken(token=>{tokens[role]=token;});
 }
 const after=await send({op:'after',role,operation,before,result});proof.push({role,operation,result,after});
}
try{
 for(const role of Object.keys(EMAILS)){
  const response=await localFetch(origin+'/auth/v1/admin/users',{method:'POST',redirect:'error',signal:AbortSignal.timeout(5000),
   headers:{Authorization:'Bearer '+config.admin,'Content-Type':'application/json'},body:JSON.stringify({email:EMAILS[role],email_confirm:true})});
  if(!response.ok)throw Error('ci_auth_seed');ids[role]=(await response.json()).id;
 }
 receipt=await send({op:'install',ids});
 guard=guardedIssuance({receipt,query:(sql,args=[])=>send({op:'query',sql,args}),check:()=>{}});
 for(const role of Object.keys(EMAILS)){
  const expected={id:ids[role],role,trainer_id:role==='a_member'?ids.a_trainer:null};
  const identity={...expected,email:EMAILS[role],registered_role:role,profile_role:role==='a_trainer'?'trainer':'client',enabled:true,operator:role==='a_trainer'};
  auths[role]=new SyntheticAuth({expected,identity,key:config.anon,admin:config.admin,fetcher:localFetch,guard});
  for(const operation of ['issue','verify','getUser','refresh'])await action(role,operation);
 }
 // The receiving CI adapter is loopback-only. These are never artifact fields.
 const workflow=await send({op:'workflow',tokens,anon:config.anon,ids});
 for(const role of Object.keys(EMAILS))for(const operation of ['logout','revoked_denial'])await action(role,operation);
 guard.close();await send({op:'remove',receipt});receipt=null;
 process.stdout.write(JSON.stringify({op:'complete',result:{status:'INTEGRAL_REAL_AUTH_WORKFLOW_CI_PASS',
  checks:proof.length,proof,workflow,hosted_requests:0,emails_sent:0}})+'\n');
}catch(error){
 if(guard)guard.close();
 if(receipt){try{await send({op:'remove',receipt});}catch{}}
 process.stdout.write(JSON.stringify({op:'failed',code:/^[a-z_]+[0-9]*$/.test(error.message)?error.message:'integral_auth_failed'})+'\n');process.exitCode=2;
}finally{
 for(const role of Object.keys(auths)){auths[role].clear();tokens[role]=null;}
 config.admin=null;config.anon=null;process.stdin.destroy();
}
