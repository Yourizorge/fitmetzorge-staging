// Opt-in local binding boundary. No legacy constants or module globals are changed.
import {readFileSync,realpathSync,lstatSync} from 'node:fs';
import {resolve,relative,isAbsolute,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Controller,validateGrant,canonical,Halt,metadata,sha} from '../../controller_v1/core.mjs';
import {NativeStore} from '../native_store.mjs';
import {LIMITS} from '../budget.mjs';

const HERE=dirname(fileURLToPath(import.meta.url));
const PREFIX='_offline/phase6e11/endchain_v1/quota_candidate_v1/';
const PARENT='11a909f4-7113-424a-aa4b-ce9964720a3e';
const PURPOSE='6e11_disposable_quota_candidate_v1';
const LEGACY=new Set([PARENT,'6f8c8909-9b79-4011-a9d1-db5e23c6b6c1',
 '1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d','4b0bb35f-02b5-4a9d-92d7-c29995691460',
 '32321f17-07f1-4f3d-aa4b-3218bc7368a4','acd473d0-5a81-4aca-928a-3907b2bda3a3',
 'debe3298-9772-40b1-a9f4-8e3d99c8fd20']);
const hash=data=>createHash('sha256').update(data).digest('hex');
const equal=(a,b)=>canonical(a)===canonical(b);
const require=(value,code)=>{if(!value)throw new Halt('quota_admission',code);};
const accepted=new WeakSet();
const DAG_FORMAT='admission-current-dispatch-dag-v1';
const RELEASE_FORMAT='admission-actual-execution-release-v1';
const ENDCHAIN='_offline/phase6e11/endchain_v1/';
const freeze=value=>{if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.freeze(value);for(const item of Object.values(value))freeze(item);}return value;};

function readSource(root,name){
 require(typeof name==='string'&&!name.includes('\\')&&!name.includes(':')&&!name.split('/').some(x=>x==='..'||x==='.'||!x),'quota_source_path');
 const file=resolve(root,name),rel=relative(root,realpathSync(file));
 require(!isAbsolute(rel)&&rel!=='..'&&!rel.startsWith('../')&&!rel.startsWith('..\\')&&!lstatSync(file).isSymbolicLink(),'quota_source_path');
 return readFileSync(file);
}

export function validateBinding(binding,now=Date.now()){
 require(binding&&binding.parent_id===PARENT&&binding.purpose===PURPOSE&&
  binding.environment==='disposable_ci'&&binding.execution_admitted===false&&binding.hosted_permission===false,'quota_binding_scope');
 require(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(binding.run_id)&&!LEGACY.has(binding.run_id),'quota_case_identity');
 require(Number.isSafeInteger(binding.cap)&&binding.cap>=1&&binding.cap<=2349,'quota_case_cap');
 require(/^[a-f0-9]{40}$/.test(binding.source_commit)&&/^[a-f0-9]{64}$/.test(binding.candidate_sha)&&/^[a-f0-9]{64}$/.test(binding.binding_sha),'quota_case_source');
 require(/^[1-9][0-9]{0,18}$/.test(binding.ci_run)&&BigInt(binding.ci_run)<=9223372036854775807n,'quota_ci_run');
 require(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(binding.expiry)&&Number.isFinite(Date.parse(binding.expiry))&&now<Date.parse(binding.expiry),'quota_expired');
 return binding;
}

export function validateQuota(q,now=Date.now()){
 require(q&&typeof q==='object','quota_context_required');
 const b=validateBinding(q.binding,now),m=q.manifest,r=q.register;
 require(m&&hash(canonical(m))===b.binding_sha&&m.parent_run===b.parent_id&&m.purpose===b.purpose&&
  m.source_commit===b.source_commit&&m.candidate_sha256===b.candidate_sha&&m.github_run===b.ci_run&&
  m.expires_at===b.expiry&&m.hosted_permission===false&&m.runtime_integrated===false&&
  m.clean47_baseline===false&&m.maximum_sql===2349,'quota_manifest_binding');
 require(Date.parse(m.created_at)<=now&&Date.parse(m.expires_at)-Date.parse(m.created_at)<=600000,'quota_manifest_expiry');
 require(m.cases?.filter(c=>c.id===b.run_id&&c.cap===b.cap).length===1,'quota_case_not_registered');
 const env=process.env;
 require(env.GITHUB_ACTIONS==='true'&&env.GITHUB_REPOSITORY==='Yourizorge/fitmetzorge-staging'&&
  env.GITHUB_REF==='refs/heads/main'&&env.GITHUB_SHA===b.source_commit&&env.GITHUB_RUN_ID===b.ci_run,'quota_ci_context');
 require(isAbsolute(q.root)&&realpathSync(q.root)===q.root,'quota_source_root');
 // Relative imports and the verified source tree must be the same tree.
 require(realpathSync(resolve(HERE,'../../../..'))===q.root,'quota_loaded_source_root');
 const refs=JSON.parse(readFileSync(resolve(HERE,'runtime_refs.json'),'utf8'));
 // One fresh snapshot per validation; never cache across calls or admissions.
 const sourceHashes=new Map();
 const sourceHash=name=>{
  if(!sourceHashes.has(name))sourceHashes.set(name,hash(readSource(q.root,name)));
  return sourceHashes.get(name);
 };
 for(const [name,expected] of Object.entries(refs.references)){
  require(m.sources[name]===expected&&sourceHash(name)===expected,'quota_reference_changed');
 }
 for(const name of refs.runtime_files){
  const relativeName=PREFIX+name;
  require(resolve(HERE,name)===resolve(q.root,relativeName)&&
   sourceHash(relativeName)===m.sources[relativeName],'quota_runtime_source');
 }
 for(const [name,expected] of Object.entries(m.sources))require(sourceHash(name)===expected,'quota_source_changed');
 validateRegister(q);
 require(q.isolation&&q.isolation.run_id===b.run_id&&q.isolation.ci_run===b.ci_run&&
  q.isolation.source_commit===b.source_commit&&q.isolation.environment==='disposable_ci'&&
  q.isolation.auth_database_bound===true&&q.isolation.reused===false,'quota_case_isolation');
 freeze(q);accepted.add(q);return q;
}

// This checks the private Python handoff, not an independent graph compiler or CI proof.
export function validateRegister(q){
 const b=q.binding,m=q.manifest,r=q.register;
 require(r&&r.format==='fmz6e11-disposable-runtime-register-v1'&&r.run_id===b.run_id&&
  r.purpose===b.purpose&&r.binding_sha===b.binding_sha&&r.source_commit===b.source_commit&&
  r.candidate_sha===b.candidate_sha&&r.approved_limit===b.cap&&r.complete_register===true&&
  r.fits===true&&Number.isSafeInteger(r.normal_capacity)&&r.normal_capacity>0&&
  Number.isSafeInteger(r.worst_including_safety)&&r.worst_including_safety>=r.normal_capacity&&
  r.worst_including_safety<=b.cap&&r.hosted_permission===false,'quota_full_register_missing');
 if(q.current_dag!=null){
  const dag=q.current_dag,model=q.release_model;
  require(dag.format===DAG_FORMAT&&dag.release_format===RELEASE_FORMAT&&
   /^[a-f0-9]{64}$/.test(r.dag_sha256)&&hash(canonical(dag))===r.dag_sha256&&
   /^[a-f0-9]{64}$/.test(r.semantic_plan_sha256)&&dag.plan_sha256===r.semantic_plan_sha256,
   'quota_current_dag_binding');
  if(r.plan_path===null)require(r.plan_sha256===r.dag_sha256,'quota_current_plan_binding');
  else require(m.sources[r.plan_path]===r.plan_sha256&&
   hash(readSource(q.root,r.plan_path))===r.plan_sha256&&
   equal(JSON.parse(readSource(q.root,r.plan_path)),dag),'quota_current_plan_binding');
  require(model&&model.format===RELEASE_FORMAT&&r.release_format===RELEASE_FORMAT&&
   hash(canonical(model))===r.release_sha256&&model.dag_sha256===r.dag_sha256&&
   model.plan_sha256===r.semantic_plan_sha256&&model.bound_complete===true&&model.fits===true&&
   Array.isArray(model.missing_costs)&&model.missing_costs.length===0&&
   model.approved_limit===2349&&model.minimal_cap===r.worst_including_safety&&
   model.normal_capacity===r.normal_capacity&&equal(model.phase_capacities,r.phase_budgets)&&
   model.case_fault_count===12&&model.bootstrap_fault_count===2&&
   Number.isSafeInteger(model.meter_required_limit)&&model.meter_required_limit>=r.normal_capacity&&
   model.meter_required_limit<=b.cap&&dag.meter_requirements?.required_limit===model.meter_required_limit,
   'quota_current_release_incomplete');
  require(equal(Object.keys(r.phase_budgets).sort(),Object.keys(LIMITS).sort())&&
   Object.values(r.phase_budgets).every(n=>Number.isSafeInteger(n)&&n>0)&&
   Object.values(r.phase_budgets).reduce((a,n)=>a+n,0)===r.normal_capacity,
   'quota_current_phase_budget');
  for(const field of ['source_hashes','register_source_hashes']){
   require(dag[field]&&typeof dag[field]==='object'&&!Array.isArray(dag[field])&&
    Object.keys(dag[field]).length>0,'quota_current_sources_missing');
   for(const [name,digest] of Object.entries(dag[field])){
    const full=Object.hasOwn(m.sources,name)?name:ENDCHAIN+name;
    require(/^[a-f0-9]{64}$/.test(digest)&&m.sources[full]===digest,'quota_current_source_changed');
   }
  }
  require(Object.hasOwn(m.sources,ENDCHAIN+'admission_budget_current_release.py'),
   'quota_current_compiler_missing');
 }else{
  require(q.release_model==null&&r.normal_capacity===2338&&equal(r.phase_budgets,LIMITS),
   'quota_full_register_missing');
  require(m.sources[r.plan_path]===r.plan_sha256&&hash(readSource(q.root,r.plan_path))===r.plan_sha256,
   'quota_register_source');
 }
 return r;
}

export function grantFor(q,now=Date.now(),receipt=null){
 validateQuota(q,now);
 const b=q.binding,expires=Date.parse(b.expiry);
 if(receipt)require(expires<=Date.parse(receipt.expires_at),'quota_guard_expiry');
 return {project:'mokxyyullfhkfalopbzd',id:b.run_id,budget_ref:b.purpose,run:b.ci_run,
  sha:b.source_commit,manifest_sha:b.binding_sha,starts:Date.parse(q.manifest.created_at),expires};
}

export class BoundNativeStore extends NativeStore{
 constructor(query,quota){super(query);this.quota=quota;this.journal=[];this.claimedGrant=null;}
 async claim(grant){
  require(accepted.has(this.quota)&&equal(grant,grantFor(this.quota)),'quota_unadmitted_claim');
  const result=await super.claim(grant);this.claimedGrant=structuredClone(grant);return result;
 }
 async record(run,step,phase,data){
  const result=await super.record(run,step,phase,data);
  if(phase==='pair_validated'){
   require(data.pair_complete===true&&data.protected_equal===true,'quota_handoff_pair');
   this.journal.push({step,sha256:await sha(metadata(data))});
  }
  return result;
 }
 async close(run,complete,count){
  const b=this.quota.binding;
  require(accepted.has(this.quota)&&run===b.run_id&&typeof complete==='boolean'&&Number.isSafeInteger(count)&&count>=0&&count<=b.cap,'quota_close_budget');
  // Identical Store.close SQL; only the old hardcoded allowance lookup is replaced.
  const command=closeStatement(run,complete,count);
  return this.one(command.sql,command.args);
 }
}

// Pure builder shared with offline source probes; admission remains in close().
export function closeStatement(run,complete,count){
 require(typeof run==='string'&&typeof complete==='boolean'&&Number.isSafeInteger(count)&&
  count>=0&&count<=2349,'quota_close_template');
 return {sql:`update fmz6e11_controller_private.runs set state=$2,command_count=$3,closed_at=clock_timestamp()
      where id=$1::uuid and state in ('running','stopped') and ($2<>'complete' or
        (state='running' and next_step>0 and next_step=(select count(*) from fmz6e11_controller_private.steps where run_id=$1::uuid)
         and not exists(select 1 from fmz6e11_controller_private.steps where run_id=$1::uuid and state<>'pair_validated')))
      returning state`,args:[run,complete?'complete':'closed',count]};
}

export class BoundController{
 constructor({quota,grant,store,now=Date.now}){
  validateQuota(quota,now());validateGrant(grant,now());
  require(equal(grant,grantFor(quota,now()))&&store instanceof BoundNativeStore&&store.quota===quota,'quota_controller_binding');
  Object.assign(this,{quota,grant:Object.freeze(structuredClone(grant)),store,now,
   maxCommands:quota.binding.cap,commands:0,step:0,claimed:false,stopped:false,busy:false});
 }
 check(){return Controller.prototype.check.call(this);}
 command(){return Controller.prototype.command.call(this);}
 claim(){return Controller.prototype.claim.call(this);}
 execute(contract,adapter){return Controller.prototype.execute.call(this,contract,adapter);}
 handoff(){
  require(this.claimed&&!this.stopped&&!this.busy&&this.step===12&&
   equal(this.store.claimedGrant,this.grant)&&this.store.journal.length===12&&
   this.store.journal.every((e,i)=>e.step===i),'quota_auth_prefix_unconfirmed');
  const journal=structuredClone(this.store.journal),grant=structuredClone(this.grant);
  return {quota:this.quota,grant,step:12,journal,sha256:hash(canonical({grant,step:12,journal}))};
 }
}

export function resumeWorkflow(context,query,now=Date.now){
 require(context&&context.step===12&&Array.isArray(context.journal)&&context.journal.length===12&&
  context.journal.every((e,i)=>e.step===i&&/^[a-f0-9]{64}$/.test(e.sha256))&&
  context.sha256===hash(canonical({grant:context.grant,step:12,journal:context.journal})),
  'quota_auth_handoff_required');
 const quota=validateQuota(context.quota,now()),grant=context.grant;
 const controller=new BoundController({quota,grant,store:new BoundNativeStore(query,quota),now});
 // Private IPC handoff only, emitted after the actual claim and 12 confirmed pairs.
 // RegisteredLifecycle independently rejects workflow until all three Auth contracts reach step 4.
 controller.claimed=true;controller.step=12;
 return {grant,controller};
}
