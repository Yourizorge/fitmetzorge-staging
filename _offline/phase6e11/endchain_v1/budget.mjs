// One owner-authorized end-run. Every other run retains the 128-command cap.
export const ENDCHAIN_RUN_ID='4b0bb35f-02b5-4a9d-92d7-c29995691460';
export const PURPOSE='6e11_recovery_endchain_20261018';
// The complete register additionally reserves the exact safety suffix before
// every mutation. These phase ceilings alone never grant hosted admission.
export const LIMITS=Object.freeze({preflight:4,migration:92,baseline:61,setup:33,guard:13,
 auth:318,controller:286,route_a:191,route_b:286,restore:54,measurements:136,io:97,
 cleanup:633,final:133,closure:1});
const NORMAL=Object.values(LIMITS).reduce((a,b)=>a+b,0);
const RESERVE=Object.freeze({cleanup:18,final:18,closure:18});
const SAFETY=new Set(['guard_remove','observer_remove','jit_revoke','proven_fixture_delete','safety_check','record_stop']);
const LABEL=/^[a-z][a-z0-9_]{1,63}$/;
export const limitFor=g=>g?.id===ENDCHAIN_RUN_ID&&g?.budget_ref===PURPOSE?2349:128;
export class BudgetStop extends Error{
 constructor(phase,attempt,code){super(code);this.phase=phase;this.command=attempt;this.code=code;}
}
export class SqlBudget{
 constructor({runId,now=()=>performance.now()}){
  if(runId!==ENDCHAIN_RUN_ID)throw new BudgetStop('admission',0,'run_not_registered');
  this.runId=runId;this.now=now;this.started=now();this.total=0;this.busy=false;
  this.stopped=false;this.failure=null;this.events=[];
  this.used=Object.fromEntries(Object.keys(LIMITS).map(k=>[k,0]));
 }
 stop(phase,code,command=this.total+1){this.stopped=true;this.failure??={phase,command,code};throw new BudgetStop(phase,command,code);}
 charge(phase,signature,{safety=false}={}){
  if(typeof safety!=='boolean')return this.stop('admission','safety_flag_invalid');
  if(!Object.hasOwn(LIMITS,phase)||!LABEL.test(signature))return this.stop('admission','query_not_registered');
  if(safety&&(!Object.hasOwn(RESERVE,phase)||!SAFETY.has(signature)))return this.stop(phase,'safety_scope');
  if(this.busy)return this.stop(phase,'parallel_query');
  const elapsed=this.now()-this.started;
  if(elapsed<0||elapsed>=(safety?600000:540000))return this.stop(phase,'run_deadline');
  if(this.stopped&&!safety)throw new BudgetStop(phase,this.total+1,'run_stopped');
  const approved=limitFor({id:this.runId,budget_ref:PURPOSE});
  if(this.total>=approved||!safety&&this.total>=NORMAL)return this.stop(phase,'global_query_budget');
  if(!safety&&this.used[phase]>=LIMITS[phase])return this.stop(phase,'phase_query_budget');
  this.total++;this.used[phase]++;this.busy=true;
  const entry={command:this.total,phase,signature,safety,started_ms:elapsed};
  this.events.push(entry);return entry;
 }
 finish(entry,{temp_written,own_wal_bytes,background_wal_bytes,background_temp_bytes}){
  if(!this.busy||this.events.at(-1)!==entry)return this.stop('evidence','query_receipt_binding');
  this.busy=false;
  const duration=this.now()-this.started-entry.started_ms;
  if(!Number.isFinite(duration)||duration<0)return this.stop(entry.phase,'clock_invalid',entry.command);
  for(const value of [temp_written,own_wal_bytes,background_wal_bytes,background_temp_bytes])
   if(!Number.isSafeInteger(value)||value<0)return this.stop(entry.phase,'query_metric_missing',entry.command);
  Object.assign(entry,{duration_ms:duration,temp_written,
   own_wal_bytes,background_wal_bytes,background_temp_bytes});
  if(temp_written!==0)return this.stop(entry.phase,'own_temp_write',entry.command);
  if(this.now()-this.started>=(entry.safety?600000:540000))return this.stop(entry.phase,'run_deadline',entry.command);
  return structuredClone(entry);
 }
 fail(entry,code){
  if(!this.busy||this.events.at(-1)!==entry)return this.stop('evidence','query_receipt_binding');
  this.busy=false;entry.duration_ms=this.now()-this.started-entry.started_ms;
  entry.code=typeof code==='string'&&LABEL.test(code)?code:'query_failed';
  this.stopped=true;this.failure??={phase:entry.phase,command:entry.command,code:entry.code};
 }
 snapshot(){return structuredClone({run_id:this.runId,limits:LIMITS,reserve:RESERVE,total:this.total,
  used:this.used,elapsed_ms:this.now()-this.started,stopped:this.stopped,failure:this.failure,events:this.events});}
}
