// Disposable CI orchestration: real GoTrue HTTP and real PostgreSQL sessions.
// SQL travels over private local IPC; no hosted network or credential support.
import readline from 'node:readline';
import {runWorkflow} from './workflow_composition.mjs';
import {createSessionTransport} from './session_transport.mjs';
const lines=readline.createInterface({input:process.stdin,terminal:false})[Symbol.asyncIterator]();
const read=async()=>JSON.parse((await lines.next()).value);
const p=await read();
if(p.mode!=='disposable_ci'||p.authUrl!=='http://127.0.0.1:59999')throw Error('ci_boundary');
let count=p.commandCount,open=false,result;
const events=[];
const sql=async(channel,phase,q,args=[])=>{
 process.stdout.write(JSON.stringify({op:'sql',channel,phase,q,args})+'\n');
 const r=await read();count=r.commandCount;if(r.error)throw Error(r.error);return r.rows;
};
let phase='identity';
const transport=createSessionTransport({postgres:()=>({
 unsafe:(q,args=[])=>sql('workflow',phase,q,args),end:async()=>{}}),
 connectionUrl:'postgres://postgres:synthetic@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres?sslmode=verify-full',
 ca:p.ca,
 sessionHost:'aws-0-eu-west-2.pooler.supabase.com',onCommand:async name=>{phase=name;}});
const query=(q,args=[])=>sql('writer','controller_evidence',q,args);
const measureQuery=(q,args=[])=>sql('reader','measurement',q,args);
const closeCollector=async()=>{if(open){await measureQuery('ROLLBACK');open=false;}};
const roleMap={member:'a_member',trainer:'a_trainer',b:'b_member'};
const sessions={};
for(const [role,key] of Object.entries(roleMap)){
 const token=p.tokens[key];
 const claims=JSON.parse(Buffer.from(token.split('.')[1],'base64url').toString());
 if(claims.sub!==p.ids[role]||typeof claims.session_id!=='string')throw Error('ci_identity_mismatch');
 sessions[role]=claims.session_id;
}
try{
 await measureQuery('BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY');open=true;
 const rows=await measureQuery("select current_setting('transaction_read_only')='on' readonly,current_setting('transaction_isolation')='read committed' fresh,pg_backend_pid() backend");
 if(rows[0]?.readonly!==true||rows[0]?.fresh!==true)throw Error('ci_collector_guard');
 result=await runWorkflow({...p,sessions,query,measureQuery,transport,collectorBackend:rows[0].backend,
  closeCollector,commandCount:()=>count,includeCleanup:true,persist:async e=>{
   events.push(e);process.stdout.write(JSON.stringify({op:'persist',event:e})+'\n');
   const r=await read();if(r.error)throw Error(r.error);
  },auth:{withToken:(role,callback)=>callback(p.tokens[roleMap[role]]),fetcher:(url,options)=>{
   const u=new URL(url);
   if(u.origin!=='https://mokxyyullfhkfalopbzd.supabase.co'||u.pathname!=='/auth/v1/user')throw Error('ci_auth_route');
   return fetch(p.authUrl+'/user',options);
  }}});
}catch(e){
 result={status:'NO_GO',phase:/^[a-z0-9_]+$/.test(e.phase)?e.phase:'integral_workflow',
  code:/^[a-z0-9_]+$/.test(e.code||e.message)?e.code||e.message:'ci_workflow_failed'};
 process.exitCode=2;
}finally{
 try{await closeCollector();}catch{result={...result,status:'NO_GO',close_failed:true};process.exitCode=2;}
 await transport.close();
 for(const key of Object.keys(p.tokens))p.tokens[key]=null;
 process.stdout.write(JSON.stringify({op:'complete',result:{...result,real_local_auth:true,commandCount:count}})+'\n');
 process.stdin.destroy();
}
