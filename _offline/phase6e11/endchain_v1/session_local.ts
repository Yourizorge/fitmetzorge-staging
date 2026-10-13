import postgres from 'https://deno.land/x/postgresjs@v3.4.7/mod.js';
import {createSessionTransport} from './session_transport.mjs';
let text='';for await(const chunk of Deno.stdin.readable)text+=new TextDecoder().decode(chunk);
const p=JSON.parse(text);
if(!Number.isInteger(p.port)||p.port<56110||p.port>=56140)throw Error('local_only');
const ca=await Deno.readTextFile(p.ca),commands:string[]=[];
const options:any={host:'127.0.0.1',port:p.port,database:'postgres',username:'postgres',password:'',
 ssl:{caCerts:[ca],hostname:'127.0.0.1'},max:1,max_pipeline:1,fetch_types:false,prepare:false,
 connect_timeout:5,idle_timeout:0,max_lifetime:0,onnotice:()=>{}};
const t=createSessionTransport({postgres:(o:any)=>postgres({...o,...options}),
 connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
 ca,sessionHost:'aws-0-eu-west-2.pooler.supabase.com',onCommand:(phase:string)=>commands.push(phase)});
const verifier=postgres(options),ids:string[]=[];
const started=performance.now();let phase='requests';
try{
 for(let i=0;i<71;i++){
  const id=crypto.randomUUID();ids.push(id);
  const input={op:'command',window:p.window,workspace:p.workspace,key:id,expected:p.revision,action:'propose',data:{}};
  const receipt=await t.invoke({input,claims:p.claims,proof:'synthetic-only-local-proof',requestId:id});
  if(receipt.http_status!==403)throw Error('source_absence_not_denied');
 }
 phase='independent_receipt_check';
 const rows=await verifier.unsafe(`select count(*)::int n,count(distinct backend)::int backends,
 count(distinct xid)::int transactions,bool_and(state='pair_validated' and selected_branch='denied') valid,
 bool_and(after_sha<>before_sha) retained_event,min(backend)::int backend
 from fmz6e11_request_private.receipts where request_id in
 (select jsonb_array_elements_text($1::text::jsonb)::uuid)`,[JSON.stringify(ids)]);
 const row=rows[0];
 if(commands.length!==356||row.n!==71||row.backends!==1||row.transactions!==71||!row.valid||!row.retained_event)
  throw Error('session_proof_incomplete');
 phase='lost_connection_denial';
 const stopped=await verifier.unsafe('select pg_terminate_backend($1::integer) stopped',[row.backend]);
 if(stopped[0].stopped!==true)throw Error('owned_local_session_not_stopped');
 await new Promise(resolve=>setTimeout(resolve,50));
 let denied=false;
 try{await t.invoke({input:{},claims:p.claims,proof:'synthetic-only-local-proof',requestId:crypto.randomUUID()});}
 catch(e){denied=(e as {code?:string}).code==='transport_closed_or_busy';}
 if(!denied||commands.length!==356)throw Error('lost_session_reconnected');
 await t.close();
 console.log(JSON.stringify({status:'LOCAL_NATIVE_SESSION_PASS',pairs:71,request_commands:356,
 independent_verification_commands:2,backend_count:row.backends,transactions:row.transactions,
 owned_local_backend_termination:true,reconnect_denied:denied,
 separate_seals:true,seconds:(performance.now()-started)/1000,hosted_calls:0,
 scope:'transport and M42 denial receipts with local Auth stubs; not full Auth/workflow admission'}));
}catch(e){
 console.log(JSON.stringify({status:'NO_GO',phase,code:(e as {code?:string}).code||'local_session_failed',commands:commands.length}));
 Deno.exitCode=2;
}finally{await t.close();await verifier.end({timeout:2});}
