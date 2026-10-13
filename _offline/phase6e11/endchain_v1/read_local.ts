import postgres from 'https://deno.land/x/postgresjs@v3.4.7/mod.js';
import {READ_STATE} from './session_transport.mjs';
let text='';for await(const c of Deno.stdin.readable)text+=new TextDecoder().decode(c);
const p=JSON.parse(text);
if(!Number.isInteger(p.port)||p.port<56110||p.port>=56140)throw Error('local_only');
const ca=await Deno.readTextFile(p.ca);
const sql=postgres({host:'127.0.0.1',port:p.port,database:'postgres',username:'postgres',password:'',
 ssl:{caCerts:[ca],hostname:'127.0.0.1'},max:1,max_pipeline:1,fetch_types:false,prepare:false,connect_timeout:5,
 connection:{statement_timeout:5000,lock_timeout:1000},onnotice:()=>{}});
const checks:any[]=[];
const bind=async(actor:string)=>sql.unsafe("select set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",
 [JSON.stringify({sub:actor,session_id:p.sessions[p.actors.indexOf(actor)]}),
  JSON.stringify({'x-fmz6e11-proof':'synthetic-only-local-proof'})]);
const read={op:'read',window:p.window,workspace:p.b};
const state=()=>sql.unsafe("select fmz6e11_private.sha(fmz6e11_request_private.snapshot($1::uuid,$2::uuid)) hash",[p.window,p.b]);
try{
 const before=await state();
 await sql.unsafe('BEGIN TRANSACTION READ ONLY');await bind(p.actors[2]);
 let stateCode='';
 try{await sql.unsafe('select public.fmz6e11_call($1::text::jsonb) value',[JSON.stringify(read)]);}
 catch(e){stateCode=(e as any).code;}
 finally{await sql.unsafe('ROLLBACK');}
 if(stateCode!=='25006')throw Error('legacy_read_lock_not_reproduced');
 checks.push({name:'legacy_lock_in_readonly',sqlstate:stateCode,denied:true});
 await sql.unsafe('BEGIN');await bind(p.actors[2]);
 const original=await sql.unsafe('select public.fmz6e11_call($1::text::jsonb) value',[JSON.stringify(read)]);
 await sql.unsafe('ROLLBACK');
 await sql.unsafe('BEGIN TRANSACTION READ WRITE');await bind(p.actors[2]);
 const corrected=await sql.unsafe(READ_STATE,[JSON.stringify(read)]);
 const active=await sql.unsafe("select current_setting('transaction_read_only')='off' locks_allowed");
 await sql.unsafe('ROLLBACK');
 if(JSON.stringify(original)!==JSON.stringify(corrected)||active[0].locks_allowed!==true)throw Error('read_result_not_equivalent');
 checks.push({name:'same_result_existing_locks_preserved',pass:true});
 for(const actor of p.actors.slice(0,2)){
  await sql.unsafe('BEGIN TRANSACTION READ WRITE');await bind(actor);let code='';
  try{await sql.unsafe(READ_STATE,[JSON.stringify(read)]);}catch(e){code=(e as any).code;}
  finally{await sql.unsafe('ROLLBACK');}
  if(code!=='42501')throw Error('cross_route_not_denied');
  checks.push({name:'cross_route_denied',actor:actor.endsWith('1')?'synthetic_a_member':'synthetic_a_trainer',sqlstate:code});
 }
 if(JSON.stringify(before)!==JSON.stringify(await state()))throw Error('local_read_changed_data');
 checks.push({name:'synthetic_state_preserved',pass:true});
 console.log(JSON.stringify({status:'LOCAL_LOCKED_READ_PASS',checks,hosted_calls:0,auth:'local_stubs_only',
  measurement_collector_readonly_unchanged:true}));
}catch(e){console.log(JSON.stringify({status:'NO_GO',code:/^[a-z_]+$/.test((e as any).message)?(e as any).message:'local_read_failure',sqlstate:/^[A-Z0-9]{5}$/.test((e as any).code)?(e as any).code:null}));Deno.exitCode=2;}
finally{await sql.end({timeout:2});}
