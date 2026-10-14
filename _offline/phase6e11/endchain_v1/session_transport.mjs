// One source-bound controller session. Never reconnect or replay a lost action.
import {connectionOptions} from '../request_v4/connection_options.mjs';
import {deadline} from '../transport_v1/contract.mjs';
import {Halt,UUID} from '../controller_v1/core.mjs';
import {IDENTITY} from './request_transport.mjs';

// Product reads take the existing authorization/row locks. They are NOT the
// read-only measurement collector. Preserve those guards and always rollback.
export const READ_STATE='select public.fmz6e11_call($1::text::jsonb) as value';

export function createSessionTransport({postgres,connectionUrl,ca,sessionHost,onCommand=()=>{},now=()=>performance.now()}){
 const options=connectionOptions(connectionUrl,ca,sessionHost);
 // Explicit owner closes this dedicated session, including failure. This is
 // not an increased connect/query timeout. The worker limit below is 120s.
 options.idle_timeout=0;options.max_lifetime=0;
 let lost=()=>{};
 options.onclose=()=>lost();
 const sql=postgres(options);
 return createProtocolSessionTransport({sql,onCommand,now,onLost:callback=>{lost=callback;}});
}

// Private IPC only: the native owner verifies TLS before supplying this handle.
// No invented connection URL or second credential copy is needed by the child.
export function createProtocolSessionTransport({sql,onCommand=()=>{},now=()=>performance.now(),onLost=()=>{}}){
 if(typeof sql?.unsafe!=='function'||typeof sql?.end!=='function')throw new Halt('admission','private_session_missing');
 let busy=false,closed=false,lost=false,attested=false,teardown=false;
 const started=now();
 onLost(()=>{if(!teardown){lost=true;closed=true;}});
 const lifetime=setTimeout(()=>{
  lost=true;closed=true;sql.end({timeout:0}).catch(()=>{});
 },120000);
 async function query(phase,text,args=[]){
  if(lost)throw new Halt(phase,'connection_lost_no_reconnect');
  if(phase!=='rollback'&&(now()<started||now()-started>=120000))throw new Halt(phase,'session_lifetime');
  await onCommand(phase,text,args);
  return deadline(()=>sql.unsafe(text,args),5000,()=>{
   lost=true;closed=true;sql.end({timeout:0}).catch(()=>{});
  });
 }
 async function close(){
  if(teardown)return;
  clearTimeout(lifetime);
  teardown=true;closed=true;
  try{await deadline(()=>sql.end({timeout:2}),2000,()=>sql.end({timeout:0}).catch(()=>{}));}
  catch{throw new Halt('close','connection_close_unconfirmed');}
 }
 async function invoke({input,claims,proof,requestId}){
  if(busy||closed)throw new Halt('admission','transport_closed_or_busy');
  if(!UUID.test(requestId||'')||!claims||!proof)throw new Halt('admission','request_context_missing');
  busy=true;let phase='begin',transaction=false,committed=false,failure=null,result;
  try{
   transaction=true;await query(phase,'BEGIN');
   if(!attested){
    phase='identity';const rows=await query(phase,IDENTITY);
    if(rows.length!==1||rows[0].identity!==true||rows[0].safe!==true)
     throw new Halt(phase,'request_database_guard');
    attested=true;
   }
   phase='binding';await query(phase,"select set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",
    [JSON.stringify(claims),JSON.stringify({'x-fmz6e11-proof':proof,'x-fmz6e11-request-id':requestId})]);
   phase='call';const rows=await query(phase,'select fmz6e11_request_private.call($1::text::jsonb,$2::uuid) as value',
    [JSON.stringify(input),requestId]);
   if(rows.length!==1||!rows[0].value)throw new Halt(phase,'request_response_missing');
   result=rows[0].value;phase='commit';await query(phase,'COMMIT');
   transaction=false;committed=true;
   phase='seal';await query(phase,'select fmz6e11_request_private.seal($1::uuid)',[requestId]);
  }catch(error){
   closed=true;
   failure=new Halt(phase,error instanceof Halt?error.code:committed?'committed_seal_unconfirmed':'request_transaction_unconfirmed');
  }finally{
   if(failure){
    if(transaction&&!lost){
     try{await query('rollback','ROLLBACK');}
     catch{(failure.cleanupFailures??=[]).push({phase:'rollback',code:'rollback_unconfirmed'});}
    }else if(transaction){
     (failure.cleanupFailures??=[]).push({phase:'rollback',code:'rollback_transport_unavailable'});
    }
    try{await close();}catch{(failure.cleanupFailures??=[]).push({phase:'close',code:'connection_close_unconfirmed'});}
   }
   busy=false;
  }
  if(failure)throw failure;
  return result;
 }
 async function read({input,claims,proof,requestId}){
  if(busy||closed)throw new Halt('admission','transport_closed_or_busy');
  if(input?.op!=='read'||Object.keys(input).sort().join()!=='op,window,workspace'||
     !UUID.test(input.window)||!UUID.test(input.workspace)||!UUID.test(requestId||'')||!claims||!proof)
   throw new Halt('admission','read_context_missing');
  busy=true;let phase='read_begin',began=false,result,failure;
  try{
   began=true;await query(phase,'BEGIN TRANSACTION READ WRITE');
   if(!attested){
    phase='identity';const rows=await query(phase,IDENTITY);
    if(rows.length!==1||rows[0].identity!==true||rows[0].safe!==true)
     throw new Halt(phase,'request_database_guard');
    attested=true;
   }
   phase='read_binding';const bound=await query(phase,
    "select current_setting('transaction_read_only')='off' as locks_allowed,set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",
    [JSON.stringify(claims),JSON.stringify({'x-fmz6e11-proof':proof,'x-fmz6e11-request-id':requestId})]);
   if(bound.length!==1||bound[0].locks_allowed!==true)throw new Halt(phase,'locked_read_unconfirmed');
   phase='read_call';const rows=await query(phase,READ_STATE,[JSON.stringify(input)]);
   if(rows.length!==1||!rows[0].value)throw new Halt(phase,'read_response_missing');
   result=rows[0].value;
  }catch(error){
   closed=true;failure=new Halt(phase,error instanceof Halt?error.code:'read_transaction_unconfirmed');
  }finally{
   if(began){
    try{await query('rollback','ROLLBACK');}
    catch{
     closed=true;
     if(failure)(failure.cleanupFailures??=[]).push({phase:'rollback',code:'rollback_unconfirmed'});
     else failure=new Halt('rollback','rollback_unconfirmed');
    }
   }
   if(failure)try{await close();}catch{(failure.cleanupFailures??=[]).push({phase:'close',code:'connection_close_unconfirmed'});}
   busy=false;
  }
  if(failure)throw failure;
  return result;
 }
 return {invoke,read,close};
}
