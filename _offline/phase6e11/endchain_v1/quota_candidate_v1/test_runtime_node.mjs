// Unit fake driver only. No database, GoTrue, hosted access or real fault evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,cpSync,mkdtempSync,appendFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {BoundController,BoundNativeStore,grantFor,validateBinding,validateQuota,resumeWorkflow,
 validateRegister,closeStatement} from './runtime_node.mjs';
import {Controller,Halt,canonical} from '../../controller_v1/core.mjs';

const original=JSON.parse(readFileSync(process.env.QUOTA_UNIT_CONFIG,'utf8'));
const hash=value=>createHash('sha256').update(canonical(value)).digest('hex');
// Schema-only private handoff fixtures, never authoritative source/DAG evidence.
function currentFixture(){
 const q=structuredClone(original),r=q.register;
 const source='_offline/phase6e11/endchain_v1/';
 const phases={...r.phase_budgets,io:r.phase_budgets.io+2};
 const normal=Object.values(phases).reduce((a,n)=>a+n,0);
 q.current_dag={format:'admission-current-dispatch-dag-v1',release_format:'admission-actual-execution-release-v1',
  plan_sha256:'a'.repeat(64),meter_requirements:{required_limit:normal+1},
  source_hashes:{[source+'quota_candidate_v1/runtime_adapter.py']:q.manifest.sources[source+'quota_candidate_v1/runtime_adapter.py']},
  register_source_hashes:{'runtime_budget.py':q.manifest.sources[source+'runtime_budget.py']}};
 q.release_model={format:q.current_dag.release_format,dag_sha256:hash(q.current_dag),
  plan_sha256:q.current_dag.plan_sha256,bound_complete:true,fits:true,missing_costs:[],approved_limit:2349,
  minimal_cap:normal+1,normal_capacity:normal,phase_capacities:phases,case_fault_count:12,
  bootstrap_fault_count:2,meter_required_limit:normal+1};
 Object.assign(r,{plan_path:null,plan_sha256:hash(q.current_dag),dag_sha256:hash(q.current_dag),
  semantic_plan_sha256:q.current_dag.plan_sha256,release_format:q.release_model.format,
  release_sha256:hash(q.release_model),phase_budgets:phases,normal_capacity:normal,
  worst_including_safety:normal+1});
 return q;
}
function fixture(){
 const quota=structuredClone(original),calls=[];
 const store=new BoundNativeStore(async(sql,args)=>{calls.push({sql,args});return [{id:quota.binding.run_id,phase:'pair_validated'}];},quota);
 const controller=new BoundController({quota,grant:grantFor(quota),store});
 return {quota,calls,store,controller};
}
function contract(step){return {step,actor:crypto.randomUUID(),action_id:crypto.randomUUID(),
 request_id:crypto.randomUUID(),workspace:null,kind:'auth',operation:'verify',writes:[]};}
const good=()=>({measure:async()=>({sha256:'1'.repeat(64),count:0}),
 act:async()=>({http_status:200}),validate:async()=>({pair_complete:true,protected_equal:true,count:0})});

test('scope denies legacy, hosted, parent-as-case, expired and excessive-cap bindings',()=>{
 for(const change of [{run_id:'6f8c8909-9b79-4011-a9d1-db5e23c6b6c1'},
  {run_id:original.binding.parent_id},{environment:'staging'},{hosted_permission:true},
  {execution_admitted:true},{cap:2350},{cap:true},{expiry:'2000-01-01T00:00:00Z'}])
  assert.throws(()=>validateBinding({...original.binding,...change}));
});
test('missing register rejected before any fake SQL dispatch',()=>{
 const q=structuredClone(original);delete q.register;let calls=0;
 const store=new BoundNativeStore(async()=>{calls++;return [];},q);
 assert.throws(()=>new BoundController({quota:q,grant:{},store}),/quota_full_register_missing/);
 assert.equal(calls,0);
});
test('source and register tampering rejected before claim',()=>{
 for(const alter of [q=>q.register.approved_limit++,q=>q.register.phase_budgets.auth++,
  q=>q.register.plan_sha256='f'.repeat(64),q=>q.manifest.candidate_sha256='e'.repeat(64)]){
  const q=structuredClone(original);alter(q);assert.throws(()=>validateQuota(q));
 }
});

test('mixed checkout and candidate roots reject before install or claim',()=>{
 const temp=mkdtempSync(join(tmpdir(),'quota-two-roots-'));
 try{
  const worker=join(temp,'worker'),candidate=join(temp,'candidate');
  cpSync(original.root,worker,{recursive:true});cpSync(original.root,candidate,{recursive:true});
  appendFileSync(join(worker,'_offline/phase6e11/controller_v1/core.mjs'),'\n// unit-only altered loaded dependency\n');
  const q=structuredClone(original);q.root=candidate;
  const url=pathToFileURL(join(worker,'_offline/phase6e11/endchain_v1/quota_candidate_v1/runtime_node.mjs')).href;
  const script=`import assert from 'node:assert/strict';import {BoundController,BoundNativeStore,grantFor} from ${JSON.stringify(url)};
   const q=${JSON.stringify(q)};let calls=0;const store=new BoundNativeStore(async()=>{calls++;return [];},q);
   assert.throws(()=>new BoundController({quota:q,grant:grantFor(q),store}),/quota_loaded_source_root/);
   assert.equal(calls,0);`;
  const result=spawnSync(process.execPath,['--input-type=module','--eval',script],{encoding:'utf8',timeout:30000});
  assert.equal(result.status,0,result.stderr);
  const cleanUrl=pathToFileURL(join(candidate,'_offline/phase6e11/endchain_v1/quota_candidate_v1/runtime_node.mjs')).href;
  const changed=join(candidate,'_offline/phase6e11/endchain_v1/quota_candidate_v1/runtime_workflow.mjs');
  const fresh=`import assert from 'node:assert/strict';import {appendFileSync} from 'node:fs';
   import {validateQuota} from ${JSON.stringify(cleanUrl)};
   const q=${JSON.stringify(q)};validateQuota(structuredClone(q));
   appendFileSync(${JSON.stringify(changed)},'\\n// unit-only change between validations\\n');
   assert.throws(()=>validateQuota(structuredClone(q)),/quota_runtime_source/);`;
  const second=spawnSync(process.execPath,['--input-type=module','--eval',fresh],{encoding:'utf8',timeout:30000});
  assert.equal(second.status,0,second.stderr);
 }finally{rmSync(temp,{recursive:true,force:true});}
});
test('same original controller execute and claim implementations are used',()=>{
 assert.match(BoundController.prototype.execute.toString(),/Controller.prototype.execute.call/);
 assert.match(BoundController.prototype.claim.toString(),/Controller.prototype.claim.call/);
 assert.equal(typeof Controller.prototype.execute,'function');
});
test('normal prefix really dispatches claim and 12 full store pairs before handoff',async()=>{
 const {controller,calls,quota}=fixture();await controller.claim();
 for(let i=0;i<12;i++)await controller.execute(contract(i),good());
 assert.equal(controller.step,12);
 assert.equal(calls.filter(x=>x.sql.includes('insert into fmz6e11_controller_private.runs')).length,1);
 assert.equal(calls.filter(x=>x.args[2]==='pair_validated').length,12);
 const handoff=controller.handoff();assert.equal(handoff.journal.length,12);
 const resumed=resumeWorkflow(handoff,async()=>[{phase:'pair_validated'}]);
 assert.equal(resumed.controller.step,12);assert.equal(resumed.grant.id,quota.binding.run_id);
 await resumed.controller.execute(contract(12),good());assert.equal(resumed.controller.step,13);
 assert.equal(resumed.controller.claimed,true);
});
test('inventing step 12 without persisted pairs cannot produce a handoff',async()=>{
 const {controller}=fixture();await controller.claim();controller.step=12;
 assert.throws(()=>controller.handoff(),/quota_auth_prefix_unconfirmed/);
});
test('wrong or partial private handoff cannot resume',async()=>{
 const {controller}=fixture();await controller.claim();
 for(let i=0;i<12;i++)await controller.execute(contract(i),good());
 const a=structuredClone(controller.handoff());a.step=11;
 assert.throws(()=>resumeWorkflow(a,async()=>[]));
 const b=structuredClone(controller.handoff());b.journal.pop();
 assert.throws(()=>resumeWorkflow(b,async()=>[]));
 const c=structuredClone(controller.handoff());c.grant.id=crypto.randomUUID();
 assert.throws(()=>resumeWorkflow(c,async()=>[]));
});
for(const where of ['before_call','after_commit','after_snapshot']){
 test('unit fault '+where+' stops durable pair without retry or complete claim',async()=>{
  const {controller,calls,store}=fixture();await controller.claim();
  let attempts=0,afterReads=0,committed=false;
  const adapter=good();
  adapter.act=async()=>{attempts++;if(where==='before_call')throw new Halt('call','unit_before_call');
   committed=true;if(where==='after_commit')throw new Halt('commit','unit_lost_reply');return {http_status:200};};
  adapter.measure=async side=>{if(side==='after'){afterReads++;if(where==='after_snapshot')throw new Halt('measurement','unit_after_snapshot');}
   return {sha256:'1'.repeat(64),count:0};};
  await assert.rejects(controller.execute(contract(0),adapter));
  assert.equal(attempts,1);assert.equal(afterReads,1);assert.equal(controller.stopped,true);
  assert.equal(controller.step,0);assert.equal(store.journal.length,0);
  assert.equal(committed,where!=='before_call');
  assert.equal(calls.filter(x=>x.sql.includes("set state='stopped'")).length,1);
  assert.equal(calls.filter(x=>x.args[1]==='complete').length,0);
  await assert.rejects(controller.execute(contract(0),good()));assert.equal(attempts,1);
 });
}
test('bound close preserves existing SQL and refuses over-cap without dispatch',async()=>{
 const {controller,store,calls,quota}=fixture();await controller.claim();
 const before=calls.length;
 await assert.rejects(store.close(quota.binding.run_id,false,quota.binding.cap+1));assert.equal(calls.length,before);
 await store.close(quota.binding.run_id,false,quota.binding.cap);
 assert.equal(calls.at(-1).args[1],'closed');assert.match(calls.at(-1).sql,/not exists\(select 1/);
 assert.equal(calls.at(-1).sql.split('/* fmz6e11:controller_v1:evidence */ ').length-1,1);
});
test('accepted binding is immutable, no post-admission cap reset',()=>{
 const {quota}=fixture();assert.throws(()=>{quota.binding.cap=9999;},TypeError);
});

test('current DAG handoff permits exact dynamic phases without old 2338 substitution',()=>{
 const q=currentFixture();assert.equal(q.register.normal_capacity,2340);
 assert.equal(validateRegister(q),q.register);
});

test('actual incomplete or over-cap current model remains denied even with recomputed hashes',()=>{
 for(const mutate of [m=>m.bound_complete=false,m=>m.fits=false,m=>m.missing_costs=['unjoined_finally'],
  m=>m.meter_required_limit=2352,m=>m.case_fault_count=3,m=>m.bootstrap_fault_count=0]){
  const q=currentFixture();mutate(q.release_model);q.register.release_sha256=hash(q.release_model);
  assert.throws(()=>validateRegister(q),/quota_current_release_incomplete/);
 }
});

test('current DAG source, semantic, and private model hashes cannot be substituted',()=>{
 for(const mutate of [q=>q.current_dag.plan_sha256='f'.repeat(64),
  q=>q.register.semantic_plan_sha256='f'.repeat(64),q=>q.register.release_sha256='f'.repeat(64),
  q=>q.register.plan_sha256='f'.repeat(64),q=>{delete q.release_model;}]){
  const q=currentFixture();mutate(q);assert.throws(()=>validateRegister(q));
 }
 const q=currentFixture();q.current_dag.register_source_hashes['runtime_budget.py']='f'.repeat(64);
 q.register.plan_sha256=q.register.dag_sha256=hash(q.current_dag);
 q.release_model.dag_sha256=q.register.dag_sha256;q.register.release_sha256=hash(q.release_model);
 assert.throws(()=>validateRegister(q),/quota_current_source_changed/);
});

test('current phase ledger rejects aliases, noninteger counts and incorrect sum',()=>{
 for(const mutate of [p=>p.extra=1,p=>p.io=true,p=>p.io++]){
  const q=currentFixture();mutate(q.register.phase_budgets);
  q.release_model.phase_capacities=q.register.phase_budgets;q.register.release_sha256=hash(q.release_model);
  assert.throws(()=>validateRegister(q),/quota_current_phase_budget/);
 }
});

test('source close builder cannot authorize an unadmitted store or dispatch SQL',async()=>{
 const q=currentFixture(),calls=[];
 assert.match(closeStatement(q.binding.run_id,false,0).sql,/closed_at=clock_timestamp/);
 const store=new BoundNativeStore(async(...args)=>{calls.push(args);return [];},q);
 validateRegister(q);
 await assert.rejects(store.close(q.binding.run_id,false,0),/quota_close_budget/);
 assert.equal(calls.length,0);
});
