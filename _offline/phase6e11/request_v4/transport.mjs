import {connectionOptions} from '../edge_bridge_v2/transport.mjs';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
export function createRequestTransport({postgres,connectionUrl,ca,sessionHost}) {
  let busy=false;
  return async ({input,claims,proof,requestId})=>{
    if(busy)throw Error('request_collector_busy');
    if(!UUID.test(requestId||'')||!claims||!proof)throw Error('request_context_missing');
    busy=true;let sql;
    try {
      const options=connectionOptions(connectionUrl,ca,sessionHost);
      options.connection.application_name='fmz6e11-request-v4';
      sql=postgres(options);
      const value=await sql.begin(async tx=>{
        const rows=await tx.unsafe(`select current_database()='postgres' and current_user='postgres' and ssl as identity,
         current_setting('log_parameter_max_length_on_error')::int=0 and
         (current_setting('log_parameter_max_length')::int=0 or
          (current_setting('log_statement')='none' and current_setting('log_min_duration_statement')::int=-1
           and current_setting('log_min_duration_sample')::int=-1 and current_setting('log_transaction_sample_rate')::numeric=0))
         and coalesce(nullif(current_setting('pgaudit.log_parameter',true),''),'off') in ('off','false','0') as safe
         from pg_stat_ssl where pid=pg_backend_pid()`);
        if(rows.length!==1||rows[0].identity!==true||rows[0].safe!==true)throw Error('request_database_guard');
        await tx.unsafe("select set_config('request.jwt.claims',$1,true),set_config('request.headers',$2,true)",[
          JSON.stringify(claims),JSON.stringify({'x-fmz6e11-proof':proof,'x-fmz6e11-request-id':requestId})]);
        const result=await tx.unsafe("select fmz6e11_request_private.call($1::text::jsonb,$2::uuid) as value",
          [JSON.stringify(input),requestId]);
        if(result.length!==1||!result[0].value)throw Error('request_response_missing');
        return result[0].value;
      });
      // The first transaction is committed; an interrupted seal blocks later mutations.
      await sql.begin(tx=>tx.unsafe("select fmz6e11_request_private.seal($1::uuid)",[requestId]));
      return value;
    } finally {try {if(sql)await sql.end({timeout:2});}finally {busy=false;}}
  };
}
