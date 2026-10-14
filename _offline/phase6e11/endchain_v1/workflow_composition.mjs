// Full original 45-step product scenario through actual controller/store,
// existing HTTP handler, counted native request transport and scoped PG pairs.
// Setup, real Auth, global IO and final window closure remain admission gates.
import {Controller,sha,Halt,canonical} from '../controller_v1/core.mjs';
import {NativeStore} from './native_store.mjs';
import {validateWorkflow} from '../controller_v1/workflow_evidence.mjs';
import {createComposedHandler} from './composed_handler.mjs';
import {ENDCHAIN_RUN_ID,PURPOSE,limitFor} from './budget.mjs';
import {verifiedClaims,BASE} from '../edge_bridge_v2/handler.mjs';

export const CLEANUP_LAYOUT=[['inbox_state','B',1],['inbox_state','A',1],
 ['events','B',8],['events','B',8],['events','B',6],['events','A',8],['events','A',8],['events','A',7],
 ['proposals','A',5],['source_heads','A',1],['source_versions','A',1],['plans','A',3],
 ['b_versions','B',3],['b_states','B',1],['audit','A',8],['audit','A',8],['audit','A',4],
 ['requests','A',8],['requests','A',8],['requests','A',8],['requests','A',8],['requests','A',5],
 ['participants','A',3],['workspaces','B',1],['workspaces','A',1]];
const cleanupTables=[...new Set(CLEANUP_LAYOUT.map(x=>x[0]))];
const cleanupKeys=cleanupTables.map(t=>`(select fmz6e11_audit_private.project_key(t,r.pk_columns) k
 from fmz6e11_private.${t} t cross join fmz6e11_audit_private.relations r
 where r.table_name='fmz6e11_private.${t}' and $10::text='${t}' and
 t.${['audit','requests','participants'].includes(t)?'window_id=$1':'workspaces'===t?'id=$2':'workspace_id=$2'}::uuid
 order by t.ctid limit 8)`).join(' union all ');

export const MEASURE=`/* fmz6e11:endchain_v1:scoped_workflow_pair */
with r as (select * from fmz6e11_request_private.receipts where request_id=$3::uuid),
 p as (select fmz6e11_request_private.snapshot($1::uuid,$2::uuid) state),
 o as (select r.table_name,t.tgenabled,t.tgfoid::regprocedure::text function_name,
 t.oid is not null and t.tgenabled='O' and t.tgfoid='fmz6e11_audit_private.observe()'::regprocedure present
 from fmz6e11_audit_private.relations r left join pg_trigger t on t.tgrelid=r.rel and t.tgname='fmz6e11_tx_observer')
select jsonb_build_object('sha256',fmz6e11_private.sha(p.state),
 'versions',coalesce(fmz6e11_workflow_audit.versions($1::uuid),'{}'),
 'observer_sha',(select fmz6e11_private.sha(jsonb_agg(to_jsonb(o) order by table_name)) from o),
 'observers_complete',(select bool_and(present) from o),
 'protected_rows',jsonb_build_object(
 'profiles',(select fmz6e11_private.sha(coalesce(jsonb_agg(to_jsonb(t) order by id),'[]')) from public.profiles t where id in (select jsonb_array_elements_text($5::text::jsonb)::uuid)),
 'users',(select fmz6e11_private.sha(coalesce(jsonb_agg(to_jsonb(t) order by id),'[]')) from auth.users t where id in (select jsonb_array_elements_text($5::text::jsonb)::uuid)),
 'sessions',(select fmz6e11_private.sha(coalesce(jsonb_agg(to_jsonb(t) order by id),'[]')) from auth.sessions t where user_id in (select jsonb_array_elements_text($5::text::jsonb)::uuid))),
 'receipt',(select to_jsonb(r) from r),
 'writes',coalesce((select jsonb_agg(to_jsonb(w) order by ordinal) from fmz6e11_audit_private.writes w join r on r.action_id=w.action_id),'[]'),
 'expected',coalesce((select jsonb_agg(fmz6e11_request_private.entry(r.run_id,e->>0,e->>1,e->2)->0) from r cross join jsonb_array_elements($4::text::jsonb) e),'[]'),
 'proposal_ids',coalesce((select jsonb_object_agg(version,id) from fmz6e11_private.proposals where workspace_id=$6::uuid),'{}'),
 'window',(select jsonb_build_object('starts',starts_at,'ends',ends_at,'scenario',scenario,'revision',revision) from fmz6e11_private.windows where id=$1::uuid),
 'template',(select fmz6e11_private.fixture(scenario)->'source_template' from fmz6e11_private.windows where id=$1::uuid),
 'b_proposal_version',(select proposal_version from fmz6e11_private.b_states where workspace_id=$7::uuid),
 'payload_sha',fmz6e11_private.sha($8::text::jsonb),
 'cleanup_keys',coalesce((select jsonb_agg(k) from (${cleanupKeys}) keys),'[]')) value from p`;
export const BOUND_MEASURE=`select current_setting('transaction_read_only')='on' readonly,
 current_setting('transaction_isolation')='read committed' fresh,pg_backend_pid() backend,
 case when current_setting('transaction_read_only')='on' and pg_backend_pid()=$9::integer
 then (${MEASURE}) else null end value`;

export async function runWorkflow({scenario,ids,sessions,window,a,b,initialRevision,query,transport,
 auth,proof,key,sourceSha,persist,commandCount,collectorBackend,includeCleanup=false,measureQuery=query,now=Date.now,
 closeCollector=async()=>{},controllerContext=null}){
 if(!Array.isArray(scenario)||scenario.length!==45)throw new Halt('admission','scenario_incomplete');
 const grant=controllerContext?.grant||{project:'mokxyyullfhkfalopbzd',id:ENDCHAIN_RUN_ID,budget_ref:PURPOSE,run:'1',sha:sourceSha,
  manifest_sha:await sha(scenario),starts:now(),expires:now()+120000};
 const controller=new Controller({grant,store:new NativeStore(query),now,maxCommands:limitFor(grant)});
 if(controllerContext){
  if(!Number.isSafeInteger(controllerContext.step)||controllerContext.step!==12)throw new Halt('admission','auth_prefix_incomplete');
  controller.claimed=true;controller.step=controllerContext.step;
 }else await controller.claim();
 const placeholder={};
 const old=n=>'68000000-0000-4000-8000-'+String(n).padStart(12,'0');
 for(const [n,value] of [[1,ids.member],[2,ids.trainer],[3,ids.b],[10,window],[11,a],[12,b]])placeholder[old(n)]=value;
 if(!Number.isInteger(collectorBackend)||collectorBackend<1)throw new Halt('admission','collector_backend_missing');
 const requestKeys=new Map(),proofs=[];
 const steps=[...scenario];
 if(includeCleanup){
  steps.push({step:45,role:'trainer',route:'A',lifecycle:true,request:{action:'revoke'},writes:[],expected_http:200,expected_outcome:'committed'});
  for(const [i,[table,route,rows]] of CLEANUP_LAYOUT.entries())
   steps.push({step:46+i,role:'trainer',route,lifecycle:true,table,rows,request:{action:'cleanup_batch'},writes:[],expected_http:200,expected_outcome:'committed'});
 }
 let lastFailure=null,phase='workflow';
 function resolve(v,context){
  if(Array.isArray(v))return v.map(x=>resolve(x,context));
  if(v&&typeof v==='object'){
   if(v.$trusted_source_template)return context.template;
   return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,resolve(x,context)]));
  }
  if(v==='$window_starts_at')return context.window.starts;
  if(v==='$window_ends_at')return context.window.ends;
  if(v==='$current_b_proposal_version')return context.b_proposal_version;
  if(typeof v==='string'){
   if(placeholder[v])return placeholder[v];
   if(v.startsWith('68000000-0000-4000-8001-')){
    if(!requestKeys.has(v))requestKeys.set(v,crypto.randomUUID());return requestKeys.get(v);
   }
   if(v.startsWith('68000000-0000-4000-8000-0000000001')){
    const found=context.proposal_ids[Number(v.slice(-3))-100];
    if(!found)throw new Halt('contract','proposal_not_in_prestate');return found;
   }
  }
  return v;
 }
 try{
  for(const step of steps){
   phase='workflow_'+step.step;const role=step.role,workspace=step.route==='A'?a:b,rid=crypto.randomUUID();
   const read=async expected=>{
    const rows=await measureQuery(BOUND_MEASURE,[window,workspace,rid,JSON.stringify(expected),JSON.stringify(Object.values(ids)),a,b,JSON.stringify(wireInput||{}),collectorBackend,step.table||'']);
    if(rows.length!==1||!rows[0].value||rows[0].readonly!==true||rows[0].fresh!==true||rows[0].backend!==collectorBackend)
     throw new Halt('measurement','scoped_response_missing');return rows[0].value;
   };
   let before,after,q,effects,contract,requestReceipt,wireInput;
   const c={step:controller.step,actor:ids[role],workspace,action_id:crypto.randomUUID(),request_id:rid,
    kind:'workflow',operation:step.request.action,writes:step.writes};
   const expectedAfter=v=>{
    if(step.table==='b_states')return {};
    const result=structuredClone(v);
    if(Number.isInteger(result.revision))result.revision+=step.request.action==='revoke'?1:
      effects.filter(x=>x[0]==='windows'&&x[1]==='UPDATE').length;
    for(const [table,op,k] of effects)if(op==='INSERT'&&table==='plans')result.a_version=k[1];
     else if(op==='INSERT'&&table==='b_versions')result.b_version=k[1];
    return result;
   };
   await controller.execute(c,{
    measure:async side=>{
     if(side==='before'){
      before=await read([]);
      if(step.lifecycle){
       q={op:'command',window,workspace,key:crypto.randomUUID(),expected:before.window.revision,
        action:step.request.action,data:step.table?{table:step.table}:{}};
       if(step.table){
        if(before.cleanup_keys.length!==step.rows)throw new Halt('contract','cleanup_preregistered_count');
        effects=before.cleanup_keys.map(k=>[step.table,'DELETE',k]);
       }else effects=[['windows','UPDATE',[window]],['windows','UPDATE',[window]],
         ['audit','INSERT',[window,ids.trainer,'revoke']],['requests','INSERT',[ids.trainer,q.key]]];
      }else{
       q=resolve(step.request,before);effects=resolve(step.writes,before);q.expected+=initialRevision-1;
      }
      c.writes=effects;
      const vb=before.versions;
      if(!step.lifecycle&&vb.revision!==step.before_revision+initialRevision-1)throw new Halt('contract','preregistered_revision_mismatch');
      contract={request_id:rid,actor:ids[role],session_id:sessions[role],workspace,window,key:q.key,
       payload_sha:null,route:step.route,operation:q.action,outcome:step.expected_outcome,
       versions_before:vb,versions_after:expectedAfter(vb)};
      // Raw pre-state/keys stay only in the synthetic runner. Persist the
      // independently preregistered hash before the mutation, never actual writes.
      await persist({step:step.step,phase:'contract',request_id:rid,contract_sha:await sha({q,effects,contract})});
      return {sha256:before.sha256,version:before.window.revision,protected_equal:true};
     }
     after=await read(effects);
     return {sha256:after.sha256,version:after.window.revision,protected_equal:canonical(before.protected_rows)===canonical(after.protected_rows)};
    },
    act:async()=>{
     if(step.lifecycle){
      wireInput=structuredClone(q);
      await persist({step:step.step,phase:'request_bound',request_id:rid,payload_sha:await sha(wireInput)});
      requestReceipt=await auth.withToken(role,async token=>{
       const response=await auth.fetcher(BASE+'/auth/v1/user',{headers:{Authorization:'Bearer '+token,apikey:key},signal:AbortSignal.timeout(5000)});
       if(!response.ok)throw new Halt('auth','cleanup_auth_denied');
       const claims=verifiedClaims('Bearer '+token,await response.json(),now());
       if(claims.sub!==ids.trainer||claims.session_id!==sessions.trainer)throw new Halt('auth','cleanup_actor_mismatch');
       return transport.invoke({input:wireInput,claims,proof,requestId:rid});
      });
      if(requestReceipt.http_status&&requestReceipt.http_status!==200)throw new Halt('cleanup','cleanup_not_confirmed');
      if(step.table&&requestReceipt.deleted!==step.rows)throw new Halt('cleanup','cleanup_count_mismatch');
      return {http_status:200,request_id:rid};
     }
     const handler=createComposedHandler({key,proof,transport:{read:args=>transport.read(args),invoke:async args=>{
      wireInput=structuredClone(args.input);
      await persist({step:step.step,phase:'request_bound',request_id:rid,payload_sha:await sha(wireInput)});
      requestReceipt=await transport.invoke(args);return requestReceipt;}},fetcher:auth.fetcher,
      now,onFailure:value=>{lastFailure=value;}});
     const response=await auth.withToken(role,token=>handler(new Request('https://synthetic.invalid',{method:'POST',
      headers:{Authorization:'Bearer '+token,'Content-Type':'application/json','x-fmz6e11-request-id':rid},body:JSON.stringify(q)})));
     if(response.status!==step.expected_http||!requestReceipt)throw new Halt(lastFailure?.phase||'workflow',lastFailure?.code||'workflow_response_mismatch');
     return {http_status:response.status,request_id:rid};
    },
    validate:async()=>{
     contract.expected=after.expected;
     // M42 hashes the incoming JSONB request; this independent comparison is
     // calculated by the collector from the preregistered request, not receipt.
     contract.payload_sha=after.payload_sha;
     const validated=await validateWorkflow(contract,before,after.receipt,after.writes,after);
     proofs.push(validated);return validated;
    }
   });
   await persist({step:step.step,phase:'pair_validated',...proofs.at(-1)});
  }
  if(typeof commandCount!=='function'||!Number.isInteger(commandCount())||commandCount()<1)
   throw new Halt('closure','command_count_missing');
  // The reader's final ROLLBACK is part of the run, not an uncounted epilogue.
  await closeCollector();
  if(!controllerContext)await controller.store.close(grant.id,true,commandCount()+1);
  return {status:includeCleanup?'LOCAL_COMPOSED_71_PASS':'LOCAL_COMPOSED_45_PASS',pairs:proofs.length,writes:proofs.reduce((n,p)=>n+p.count,0),
   deletes:proofs.reduce((n,p)=>n+p.changes.find(x=>x.operation==='DELETE').count,0),
   proofs,next_step:controller.step,hosted_admitted:false,missing:['fixture_lifecycle_evidence','full_protocol_register']};
 }catch(error){
  await persist({status:'NO_GO',phase,code:error instanceof Halt?error.code:'workflow_unconfirmed',
   transport_failure:lastFailure});
  if(lastFailure)error.transportFailure=lastFailure;
  throw error;
 }
}
