import postgres from 'https://deno.land/x/postgresjs@v3.4.7/mod.js';
import {runWorkflow} from './workflow_composition.mjs';
import {createSessionTransport} from './session_transport.mjs';
import {Halt} from '../controller_v1/core.mjs';
let text='';for await(const c of Deno.stdin.readable)text+=new TextDecoder().decode(c);
const p=JSON.parse(text);
if(!Number.isInteger(p.port)||p.port<56110||p.port>=56140)throw Error('local_only');
const ca=await Deno.readTextFile(p.ca),commands:any[]=[],events:any[]=[];
let injected=false;
function fault(when:string){
 if(p.fault&&!injected&&p.fault.command===commands.length&&p.fault.when===when){
  injected=true;throw new Halt('local_failure_injection','local_injected_receipt_loss');
 }
}
if(p.fault&&(!Number.isInteger(p.fault.command)||p.fault.command<1||p.fault.command>938||
 !['before','after'].includes(p.fault.when)))throw Error('local_fault_scope');
const options:any={host:'127.0.0.1',port:p.port,database:'postgres',username:'postgres',password:'',
 ssl:{caCerts:[ca],hostname:'127.0.0.1'},max:1,max_pipeline:1,fetch_types:false,prepare:false,connect_timeout:5,
 idle_timeout:0,max_lifetime:0,connection:{statement_timeout:5000,lock_timeout:1000},onnotice:()=>{}};
const writer=postgres(options),reader=postgres(options),started=performance.now();
async function trace(phase:string,q:string){
 if(commands.length>=1280)throw Error('local_command_budget');
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(q));
 commands.push({command:commands.length+1,phase,sql_sha256:[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join(''),at_ms:performance.now()-started});
 fault('before');
}
const t=createSessionTransport({postgres:(o:any)=>{
 const client=postgres({...o,...options});
 return {unsafe:async(q:string,args:any[]=[])=>{const rows=await client.unsafe(q,args);fault('after');return rows;},
  end:(o:any)=>client.end(o)};
},
 connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
 ca,sessionHost:'aws-0-eu-west-2.pooler.supabase.com',onCommand:trace});
const query=async(q:string,args:any[]=[])=>{
 await trace('controller_evidence',q);
 try{const rows=await writer.unsafe(q,args);fault('after');return rows;}
 catch(e){
  events.push({phase:'native_evidence_error',command:commands.length,
   sqlstate:/^[A-Z0-9]{5}$/.test((e as any).code)?(e as any).code:null,
   constraint:/^[a-z_0-9]{1,100}$/.test((e as any).constraint_name)?(e as any).constraint_name:null});
  throw e;
 }
};
const measureQuery=async(q:string,args:any[]=[])=>{await trace('measurement',q);const rows=await reader.unsafe(q,args);fault('after');return rows;};
const users:any={},tokens:any={};
for(const [i,role] of ['member','trainer','b'].entries()){
 const claims={sub:p.ids[role],session_id:p.sessions[role],iss:'https://mokxyyullfhkfalopbzd.supabase.co/auth/v1',
  aud:'authenticated',role:'authenticated',exp:Math.floor(Date.now()/1000)+300};
 const b64=(x:any)=>btoa(JSON.stringify(x)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
 tokens[role]=b64({alg:'HS256',typ:'JWT'})+'.'+b64(claims)+'.local_synthetic_signature';
 users[tokens[role]]={id:p.ids[role],email:['zorgeyouri+6e9-a-lid@gmail.com','zorgeyouri+6e9-a-trainer@gmail.com','zorgeyouri+6e9-b-lid@gmail.com'][i]};
}
let began=false,outcome:any;
const closeCollector=async()=>{if(began){await measureQuery('ROLLBACK');began=false;}};
try{
 await measureQuery('BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY');began=true;
 const guard=await measureQuery("select current_setting('transaction_read_only')='on' readonly,current_setting('transaction_isolation')='read committed' fresh,pg_backend_pid() backend");
 if(guard[0].readonly!==true||guard[0].fresh!==true)throw Error('local_collector_guard');
 const result=await runWorkflow({...p,query,measureQuery,transport:t,commandCount:()=>commands.length,collectorBackend:guard[0].backend,
  closeCollector,proof:'synthetic-only-local-proof',key:'local_only',persist:async(x:any)=>events.push(x),
  auth:{withToken:(role:string,callback:any)=>callback(tokens[role]),fetcher:async(url:string,o:any)=>{
   if(url!=='https://mokxyyullfhkfalopbzd.supabase.co/auth/v1/user')throw Error('local_auth_only');
   const user=users[o.headers.Authorization.slice(7)];return Response.json(user||{},{status:user?200:401});
  }}});
 outcome={...result,scope:'real PG controller/store/handler and scoped pairs; local Auth stubs; not full admission'};
}catch(e){
 outcome={status:'NO_GO',phase:(e as any).phase||'local_composition',
  code:/^[a-z0-9_]+$/.test((e as any).code)?(e as any).code:'local_composition_failed',
  transport_failure:(e as any).transportFailure||null};Deno.exitCode=2;
}finally{
 const failures=[];
 for(const [phase,close] of [['collector_rollback',closeCollector],['transport_close',()=>t.close()],
   ['reader_close',()=>reader.end({timeout:2})],['writer_close',()=>writer.end({timeout:2})]] as const){
  try{await close();}catch{failures.push(phase);}
 }
 if(failures.length){outcome={...outcome,status:'NO_GO',closure_failures:failures};Deno.exitCode=2;}
 // Emit only after every independently authorized safety close was attempted.
 console.log(JSON.stringify({...outcome,commands,events,injected,seconds:(performance.now()-started)/1000}));
}
