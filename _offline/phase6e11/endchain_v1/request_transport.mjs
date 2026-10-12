// Dedicated native client: first SQL is BEGIN, no reserve(), no startup type query.
import {connectionOptions} from '../request_v4/connection_options.mjs';
import {Halt,UUID} from '../controller_v1/core.mjs';
import {deadline} from '../transport_v1/contract.mjs';
export const IDENTITY=`select current_database()='postgres' and current_user='postgres' and ssl as identity,
 current_setting('log_parameter_max_length_on_error')::int=0 and
 (current_setting('log_parameter_max_length')::int=0 or
 (current_setting('log_statement')='none' and current_setting('log_min_duration_statement')::int=-1
 and current_setting('log_min_duration_sample')::int=-1 and current_setting('log_transaction_sample_rate')::numeric=0))
 and coalesce(nullif(current_setting('pgaudit.log_parameter',true),''),'off') in ('off','false','0') as safe
 from pg_stat_ssl where pid=pg_backend_pid()`;
export function createTransport({postgres,connectionUrl,ca,sessionHost,onCommand=()=>{}}){
 let busy=false,closed=false;
 return async({input,claims,proof,requestId})=>{
  if(busy||closed)throw new Halt('admission','transport_closed_or_busy');
  if(!UUID.test(requestId||'')||!claims||!proof)throw new Halt('admission','request_context_missing');
  busy=true;let sql,phase='begin',committed=false,transaction=false;
  const query=async(text,args=[])=>{
   onCommand(phase);
   return deadline(()=>sql.unsafe(text,args),5000,()=>{closed=true;sql.end({timeout:0}).catch(()=>{});});
  };
  try{
   const options=connectionOptions(connectionUrl,ca,sessionHost);
   sql=postgres(options);
   transaction=true;await query('BEGIN');
   phase='identity';const rows=await query(IDENTITY);
   if(rows.length!==1||rows[0].identity!==true||rows[0].safe!==true)throw new Halt(phase,'request_database_guard');
   phase='binding';await query("select set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",
    [JSON.stringify(claims),JSON.stringify({'x-fmz6e11-proof':proof,'x-fmz6e11-request-id':requestId})]);
   phase='call';const response=await query('select fmz6e11_request_private.call($1::text::jsonb,$2::uuid) as value',
    [JSON.stringify(input),requestId]);
   if(response.length!==1||!response[0].value)throw new Halt(phase,'request_response_missing');
   phase='commit';await query('COMMIT');committed=true;transaction=false;
   // A standalone SQL statement is its own transaction. This seal is still
   // separate from the committed call; failure leaves the M42 receipt unsealed.
   phase='seal';await query('select fmz6e11_request_private.seal($1::uuid)',[requestId]);
   return response[0].value;
  }catch(error){
   closed=true;
   throw new Halt(phase,error instanceof Halt?error.code:committed?'committed_seal_unconfirmed':'request_transaction_unconfirmed');
  }finally{
   try{
    if(sql&&transaction){phase='rollback';try{await query('ROLLBACK');}catch{closed=true;throw new Halt(phase,'rollback_unconfirmed');}}
   }finally{
    try{
     if(sql)try{await deadline(()=>sql.end({timeout:2}),2000,()=>{closed=true;sql.end({timeout:0}).catch(()=>{});});}
     catch{closed=true;throw new Halt('close','connection_close_unconfirmed');}
    }finally{busy=false;}
   }
  }
 };
}
