// Protocol commands, not helper invocations. No transport or hosted admission.
import {sha,Halt} from '../controller_v1/core.mjs';
import {limitFor} from './budget.mjs';
const LABEL=/^[a-z][a-z0-9_]{1,63}$/;
const HASH=/^[0-9a-f]{64}$/;
const PHASES=['baseline','fixtures','guard','observer','auth','controller','route_a',
 'route_b','restore','measurements','io','cleanup','final','closure'];
const TYPES=['sql','http','local'];
export const MAX_SQL=128;
const problem=code=>{throw new Halt('command_register',code);};
function freeze(value){if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;}
function integer(n){return Number.isSafeInteger(n)&&n>=0;}
function command(c){
 if(!c||!LABEL.test(c.id)||!PHASES.includes(c.phase)||!TYPES.includes(c.type)||
    !HASH.test(c.source_sha)||!HASH.test(c.template_sha)||!LABEL.test(c.adapter)||
    typeof c.mutates!=='boolean'||!integer(c.deadline_ms)||c.deadline_ms<1||
    c.type==='sql'&&c.deadline_ms>5000)problem('command_shape');
 if(c.mutates&&(!HASH.test(c.writeset_sha)||!LABEL.test(c.pair)))problem('mutation_unbound');
 if(c.type==='sql'&&c.protocol_commands!==1)problem('hidden_protocol_commands');
 if(c.type!=='sql'&&c.protocol_commands!==0)problem('non_sql_misclassified');
 return structuredClone(c);
}
export function compileRegister({steps,failures,sourceHashes,complete,missing=[],run=null}){
 const limit=limitFor(run);
 if(!Array.isArray(steps)||!steps.length||steps.length>4096||!Array.isArray(failures)||
    !sourceHashes||Object.values(sourceHashes).some(v=>!HASH.test(v))||
    typeof complete!=='boolean'||!Array.isArray(missing)||missing.some(v=>!LABEL.test(v)))problem('register_shape');
 const commands=steps.map(command),ids=new Set(commands.map(c=>c.id));
 if(ids.size!==commands.length)problem('duplicate_command_id');
 if(commands.some(c=>sourceHashes[c.adapter]!==c.source_sha))problem('source_binding');
 // Each prefix is separately audited. A failure path is a suffix, never a
 // replay of the original action. Prefix 0 includes setup failing before SQL.
 const paths=new Map();
 for(const f of failures){
  if(!integer(f.after)||f.after>commands.length||paths.has(f.after)||!Array.isArray(f.commands))problem('failure_path_shape');
  const suffix=f.commands.map(command);
  if(new Set(suffix.map(c=>c.id)).size!==suffix.length)problem('duplicate_cleanup_command');
  if(suffix.some(c=>sourceHashes[c.adapter]!==c.source_sha))problem('cleanup_source_binding');
  if(suffix.some(c=>c.mutates&&!['cleanup','guard','observer','auth','closure'].includes(c.phase)))problem('failure_new_mutation');
  if(suffix.some(c=>!c.safety))problem('failure_not_safety');
  const seen=new Set();
  for(const c of suffix){
   if(!Array.isArray(c.depends_on)||c.depends_on.some(id=>!seen.has(id)))problem('safety_dependency');
   seen.add(c.id);
  }
  paths.set(f.after,suffix);
 }
 const absent=Array.from({length:commands.length+1},(_,i)=>i).filter(i=>!paths.has(i));
 const absentPhases=PHASES.filter(p=>!commands.some(c=>c.phase===p));
 if(complete&&(missing.length||absent.length||absentPhases.length))problem('incomplete_register_claim');
 const count=x=>x.filter(c=>c.type==='sql').length;
 const phaseCounts=Object.fromEntries(PHASES.map(p=>[p,count(commands.filter(c=>c.phase===p))]));
 let used=0,worst=count(commands);const reserves=[];
 for(let i=0;i<=commands.length;i++){
  if(i)used+=commands[i-1].protocol_commands;
  const suffix=paths.get(i),reserve=suffix?count(suffix):null;
  const total=reserve===null?null:used+reserve;
  if(total!==null)worst=Math.max(worst,total);
  reserves.push({after:i,used,reserved_sql:reserve,total,within_limit:total!==null&&total<=limit});
 }
 return {version:1,complete,missing,commands,failures:[...paths].map(([after,commands])=>({after,commands})),
  sourceHashes,phase_counts:phaseCounts,normal_sql:count(commands),minimum_registered_limit:worst,
  extra_sql:Math.max(0,worst-limit),limit,run:structuredClone(run),reserves,uncovered_prefixes:absent,uncovered_phases:absentPhases,
  budget_fits:complete&&!missing.length&&!absent.length&&worst<=limit,
  // A register/trace alone cannot grant database or hosted execution.
  hosted_admitted:false};
}

export class RegisteredExecutor{
 constructor({register,adapters,persist,now=()=>performance.now(),expiresAt,safetyExpiresAt=expiresAt,localOnly=false}){
  if(typeof localOnly!=='boolean'||typeof persist!=='function'||!Number.isFinite(expiresAt))problem('executor_shape');
  if(!localOnly)problem('hosted_executor_not_admitted');
  const rebuilt=compileRegister({steps:register.commands,failures:register.failures,
   sourceHashes:register.sourceHashes,complete:register.complete,missing:register.missing,run:register.run});
  if(JSON.stringify(register)!==JSON.stringify(rebuilt))problem('register_modified');
  if(!register.budget_fits)problem('register_not_admitted');
  for(const [name,source] of Object.entries(register.sourceHashes))
   if(adapters[name]?.source_sha!==source||typeof adapters[name]?.execute!=='function')problem('adapter_unbound');
  if(!Number.isFinite(safetyExpiresAt)||safetyExpiresAt<expiresAt||safetyExpiresAt-now()>600000)
   problem('safety_deadline');
  // Admission cannot be changed through references retained by the caller.
  const boundAdapters=Object.freeze(Object.fromEntries(Object.entries(adapters).map(([name,a])=>
   [name,Object.freeze({source_sha:a.source_sha,execute:a.execute})])));
  Object.assign(this,{register:freeze(structuredClone(register)),adapters:boundAdapters,persist,now,
   expiresAt,safetyExpiresAt,localOnly,used:0,index:0,stopped:false,busy:false});
  this.started=now();this.events=[];this.failure=null;this.inSafety=false;this.safetyIndex=0;
 }
 async one(c){
  const ordinal=this.used+c.protocol_commands;
  if(ordinal>this.register.limit||this.now()>=(this.inSafety?this.safetyExpiresAt:this.expiresAt))problem('hard_limit');
  const entry={id:c.id,phase:c.phase,type:c.type,command:ordinal,source_sha:c.source_sha,
   template_sha:c.template_sha,started_ms:this.now()-this.started,status:'started',safety:this.inSafety};
  // A durable intent precedes ALL protocol commands, including safety removal.
  await this.persist({...entry});this.used=ordinal;
  let value;
  try{
   value=await this.adapters[c.adapter].execute(c);
   entry.duration_ms=this.now()-this.started-entry.started_ms;
   if(entry.duration_ms<0||entry.duration_ms>c.deadline_ms)problem('command_deadline');
   if(c.type==='sql'&&(!HASH.test(value?.receipt_sha)||value?.validated!==true))problem('sql_receipt_missing');
   if(c.phase==='io'&&(!HASH.test(value?.io_pair_sha)||value?.validated!==true))problem('io_receipt_missing');
  }
  catch(error){
   entry.status='failed';entry.code=error instanceof Halt&&LABEL.test(error.code)?error.code:'adapter_failed';
   entry.duration_ms=this.now()-this.started-entry.started_ms;
   await this.persist({...entry});this.events.push(entry);throw error;
  }
  entry.status='confirmed';entry.receipt_sha=value?.receipt_sha||null;
  entry.io_pair_sha=value?.io_pair_sha||null;
  await this.persist({...entry});this.events.push(entry);return value;
 }
 async next(){
  if(this.busy||this.stopped||this.inSafety||this.index>=this.register.commands.length)problem('executor_closed');
  const current=this.register.commands[this.index];
  const prefix=this.register.reserves[this.index+1];
  if(!prefix.within_limit||this.used+current.protocol_commands+prefix.reserved_sql>this.register.limit)problem('cleanup_escrow');
  this.busy=true;
  try{const value=await this.one(current);this.index++;return value;}
  catch(error){this.stopped=true;this.failure={after:this.index+1,phase:current.phase,command:this.used,
   code:error instanceof Halt&&LABEL.test(error.code)?error.code:'adapter_failed'};throw error;}
  finally{this.busy=false;}
 }
 async safety(){
  if(this.busy||this.inSafety)problem('safety_replayed');
  this.inSafety=true;this.stopped=true;
  const after=this.failure?.after??this.index;
  const path=this.register.failures.find(x=>x.after===after);
  if(!path)problem('safety_path_missing');
  // Every safe action has an identity-bound adapter. No generic bypass flag.
  const completed=new Set(),failures=[];
  for(const c of path.commands){
   if(c.depends_on.some(id=>!completed.has(id))){
    failures.push({id:c.id,code:'safety_dependency_failed'});continue;
   }
   try{await this.one(c);this.safetyIndex++;completed.add(c.id);}
   catch(error){failures.push({id:c.id,code:error instanceof Halt&&LABEL.test(error.code)?error.code:'safety_failed'});}
  }
  return {sql_commands:this.used,safety_commands:this.safetyIndex,complete:failures.length===0,failures};
 }
 async evidence(){return {sql_commands:this.used,stopped:this.stopped,failure:this.failure,
  receipt_sha:await sha(this.events),hosted_admitted:false,local_only:this.localOnly};}
}
