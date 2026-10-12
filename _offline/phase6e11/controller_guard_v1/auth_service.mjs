// CI-only real GoTrue integration. No hosted URL can reach the network here.
import readline from 'node:readline';
import assert from 'node:assert/strict';
import {SyntheticAuth,EMAILS} from '../controller_v1/auth.mjs';
import {guardedIssuance} from './issuance.mjs';
import {metadata} from '../controller_v1/core.mjs';
import {bindSession} from '../auth_metadata_v1/hashes.mjs';
const lines=readline.createInterface({input:process.stdin,terminal:false})[Symbol.asyncIterator]();
const read=async()=>JSON.parse((await lines.next()).value);
const send=async(value)=>{process.stdout.write(JSON.stringify(value)+'\n');const reply=await read();if(reply.error)throw Error(reply.error);return reply.value;};
const config=await read();
if(config.mode!=='disposable_ci' || config.url!=='http://127.0.0.1:59999')throw Error('ci_boundary');
const localFetch=async(url,options)=>{
 const parsed=new URL(url);
 if(parsed.origin!=='https://mokxyyullfhkfalopbzd.supabase.co'||!parsed.pathname.startsWith('/auth/v1/'))throw Error('network_boundary');
 return fetch(config.url+parsed.pathname.slice('/auth/v1'.length)+parsed.search,options);
};
const raw=async(path,body,token=config.admin)=>{
 const response=await localFetch('https://mokxyyullfhkfalopbzd.supabase.co/auth/v1'+path,{method:'POST',redirect:'error',
   signal:AbortSignal.timeout(5000),headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(!response.ok)throw Error('ci_auth_setup_'+response.status);
 return response.json();
};
let guard,receipt;
try{
 const ids={};
 for(const role of Object.keys(EMAILS)){
  const user=await raw('/admin/users',{email:EMAILS[role],email_confirm:true});ids[role]=user.id;
 }
 receipt=await send({op:'install',ids});
 const query=(sql,args=[])=>send({op:'query',sql,args});
 guard=guardedIssuance({receipt,query,check:()=>{}});
 const proof=[];
 for(const role of Object.keys(EMAILS)){
  const expected={id:ids[role],role,trainer_id:role==='a_member'?ids.a_trainer:null};
  const identity={...expected,email:EMAILS[role],registered_role:role,profile_role:role==='a_trainer'?'trainer':'client',enabled:true,operator:role==='a_trainer'};
  const auth=new SyntheticAuth({expected,identity,key:config.anon,admin:config.admin,fetcher:localFetch,guard});
  let access=null;
  for(const operation of ['issue','verify','getUser','refresh','logout']){
   const before=await send({op:'before',role,operation});
   let result=metadata(await auth[operation]());
   if(operation!=='issue')result=await bindSession(auth,result);
   if(operation==='refresh')await auth.withToken(token=>{access=token;});
   const after=await send({op:'after',role,operation,before,result});
   proof.push({role,operation,result,after});
  }
  // A real server request using the old JWT, not the helper's local closed flag.
  const before=await send({op:'before',role,operation:'revoked_denial'});
  const response=await localFetch('https://mokxyyullfhkfalopbzd.supabase.co/auth/v1/user',{
   method:'GET',redirect:'error',signal:AbortSignal.timeout(5000),headers:{Authorization:'Bearer '+access,apikey:config.anon}});
  assert.equal(response.status,403);
  await response.arrayBuffer();access=null;
  const after=await send({op:'after',role,operation:'revoked_denial',before,result:{http_status:response.status}});
  proof.push({role,operation:'revoked_denial',result:{http_status:response.status},after});auth.clear();
 }
 guard.close();await send({op:'remove',receipt});receipt=null;
 const result={status:'REAL_AUTH_CI_PASS',checks:proof.length,proof,hosted_requests:0,emails_sent:0};
 process.stdout.write(JSON.stringify({op:'complete',result})+'\n');
}catch(error){
 if(guard)guard.close();
 if(receipt){try{await send({op:'remove',receipt});}catch{}}
 process.stdout.write(JSON.stringify({op:'failed',code:/^[a-z_]+[0-9]*$/.test(error.message)?error.message:'auth_composition_failed'})+'\n');
 process.exitCode=2;
}finally{config.admin=null;config.anon=null;process.stdin.destroy();}
