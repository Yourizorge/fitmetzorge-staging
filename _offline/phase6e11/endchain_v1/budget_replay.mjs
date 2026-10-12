// Offline lower-bound replay. ZERO metrics below are simulator inputs, not IO evidence.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {SqlBudget,ENDCHAIN_RUN_ID,LIMITS} from './budget.mjs';
const root=path.resolve(import.meta.dirname,'../../..');
const [rawSequence,rawCleanup,rawOut]=process.argv.slice(2);
const sequence=path.resolve(rawSequence),cleanup=path.resolve(rawCleanup),out=path.resolve(rawOut);
for(const p of [sequence,cleanup,out])assert.equal(path.dirname(p),path.join(root,'supabase','.temp'));
assert.ok(path.basename(sequence).startsWith('phase6e11-endchain-'));
assert.ok(path.basename(cleanup).startsWith('phase6e11-workflow-local-'));
assert.ok(path.basename(out).startsWith('phase6e11-endchain-'));
const read=p=>JSON.parse(fs.readFileSync(p));
const s=read(path.join(sequence,'sequence.json')),c=read(path.join(cleanup,'endchain-cleanup-result.json'));
assert.equal(s.actions.length,63);assert.equal(c.status,'LOCAL_EXISTING_CLEANUP_PASS');
assert.equal(c.product_pairs,45);assert.equal(c.revoke_pairs,1);assert.equal(c.delete_batch_pairs,c.batches.length);
assert.equal(c.request_commands,(46+c.batches.length)*6);
assert.ok(c.batches.every(x=>Number.isSafeInteger(x.rows)&&x.rows>0&&x.rows<=8));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
for(const [p,h] of Object.entries(read(path.join(cleanup,'cleanup-sources.json'))))assert.equal(sha(p),h,p);
const actions=[];
for(const a of s.actions){
 if(a.step===57){
  actions.push({phase:'cleanup',name:'revoke',commands:13});
  for(const [i,b] of c.batches.entries())actions.push({phase:'cleanup',name:'delete_'+b.table,batch:i+1,commands:13});
 }
 if(a.kind==='auth')actions.push({phase:'auth',name:a.operation,commands:9+(['issue','verify','refresh'].includes(a.operation)?6:0)});
 else{
  const step=a.scenario_step;
  const restore=step>=8&&step<=19||step>=29&&step<=40;
  actions.push({phase:restore?'restore':a.scenario_contract.route==='A'?'route_a':'route_b',
   name:a.operation,commands:13});
 }
}
const budget=new SqlBudget({runId:ENDCHAIN_RUN_ID,now:()=>0});let stop=null;
for(const a of actions){
 try{
  for(let i=0;i<a.commands;i++){
   const e=budget.charge(a.phase,'offline_simulation');
   budget.finish(e,{temp_written:0,own_wal_bytes:0,background_wal_bytes:0,background_temp_bytes:0});
  }
 }catch(e){stop={phase:e.phase,command:e.command,code:e.code,action:a.name,batch:a.batch??null};break;}
}
const total=actions.reduce((n,a)=>n+a.commands,0);
const result={status:stop?'OFFLINE_PHASE_BUDGET_NO_GO':'INCOMPLETE_LIFECYCLE_LEDGER',
 hosted_attempts:0,hosted_sql_commands:0,real_io_measured:false,simulation_only:true,stop,
 known_action_commands:total,workflow_auth_core_commands:801,
 revoke_and_batch_cleanup_commands:(c.batches.length+1)*13,
 safety_reserved:64,remaining_ordinary_commands_before_1280:1280-64-total,
 omitted:['project/source admission','fixture prepare and activate','window lifecycle delete',
 'controller claim/close','reader cycle envelopes','guard/observer install and removal',
 'native query-level IO binding','final preservation and migration checks'],
 phase_limits:LIMITS,actions,source_hashes:{
  budget:sha(path.join(root,'_offline/phase6e11/endchain_v1/budget.mjs')),
  cleanup_receipt:sha(path.join(cleanup,'endchain-cleanup-result.json')),
  sequence:sha(path.join(sequence,'sequence.json'))}};
fs.mkdirSync(out);
fs.writeFileSync(path.join(out,'budget-replay.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({...result,actions:undefined,source_hashes:undefined,evidence:out}));

