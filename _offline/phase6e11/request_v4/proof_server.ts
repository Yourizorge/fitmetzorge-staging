import postgres from 'npm:postgres@3.4.7';
import {verifyCI} from './oidc.mjs';
import {CA,SESSION_HOST} from '../edge_bridge_v2/ca.mjs';
import {expected} from './proof_binding.mjs';
let busy=false;
Deno.serve(async req=>{
  if(req.method!=='POST')return Response.json({error:'method_denied'},{status:405});
  try {await verifyCI(req.headers.get('authorization'),expected);}catch{return Response.json({error:'unauthorized'},{status:401});}
  if(busy)return Response.json({error:'busy'},{status:409});
  busy=true;let sql:ReturnType<typeof postgres>|undefined;
  try {
    if((await req.text())!=='{}')throw Error('payload_invalid');
    if(Deno.env.get('SUPABASE_URL')!=='https://mokxyyullfhkfalopbzd.supabase.co')throw Error('project_invalid');
    const u=new URL(Deno.env.get('SUPABASE_DB_URL')||'');
    const direct=u.hostname==='db.mokxyyullfhkfalopbzd.supabase.co';
    if(!['postgres:','postgresql:'].includes(u.protocol))throw Error('database_protocol_invalid');
    if(!direct&&u.hostname!==SESSION_HOST)throw Error('database_host_not_allowlisted');
    if((u.port||'5432')!=='5432')throw Error('database_port_not_session');
    if(u.pathname!=='/postgres')throw Error('database_name_invalid');
    if(!u.password)throw Error('database_password_absent');
    if(decodeURIComponent(u.username)!==(direct?'postgres':'postgres.mokxyyullfhkfalopbzd'))throw Error('database_role_not_postgres');
    if([...u.searchParams.keys()].some(k=>k!=='sslmode'))throw Error('database_options_unexpected');
    if(u.searchParams.has('sslmode')&&u.searchParams.get('sslmode')!=='verify-full')throw Error('database_sslmode_not_verify_full');
    sql=postgres({host:u.hostname,port:5432,database:'postgres',username:decodeURIComponent(u.username),
      password:decodeURIComponent(u.password),ssl:{ca:CA,rejectUnauthorized:true},max:1,prepare:false,
      fetch_types:false,debug:false,connect_timeout:5,idle_timeout:2,max_lifetime:15,onnotice:()=>{},
      connection:{application_name:'fmz6e11-server-admission',statement_timeout:3000,lock_timeout:1000}});
    const result=await sql.begin('read only',async tx=>{
      const rows=await tx.unsafe(`select current_database()='postgres' and current_user='postgres' and ssl as bound,
        current_setting('transaction_read_only')='on' as readonly,
        (select count(*)::int from supabase_migrations.schema_migrations) as migrations,
        (select count(*)::int from fmz6e11_private.identities where enabled) as synthetic_identities,
        (select enabled from fmz6e11_request_private.control where id) as bridge_enabled
        from pg_stat_ssl where pid=pg_backend_pid()`);
      if(rows.length!==1||rows[0].bound!==true||rows[0].readonly!==true||rows[0].migrations!==42)throw Error('identity_invalid');
      return rows[0];
    });
    return Response.json({status:'EDGE_READONLY_CONNECTION_PASS',...result,
      proof_present:Boolean(Deno.env.get('FMZ6E11_PROOF')),
      auth_admin_present:Boolean(Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')),
      application_writes:0,auth_calls:0,secrets_returned:false});
  }catch(error){
    const e=error as {message?:string;code?:string};
    const allowed=new Set(['database_configuration_invalid','payload_invalid','project_invalid','identity_invalid',
      'database_protocol_invalid','database_host_not_allowlisted','database_port_not_session','database_name_invalid',
      'database_password_absent','database_role_not_postgres','database_options_unexpected','database_sslmode_not_verify_full']);
    return Response.json({status:'NO_GO',error:allowed.has(e.message||'')?e.message:'server_connection_failed',
      sqlstate:/^[0-9A-Z]{5}$/.test(e.code||'')?e.code:null},{status:503});
  }finally{try{if(sql)await sql.end({timeout:2});}finally{busy=false;}}
});
