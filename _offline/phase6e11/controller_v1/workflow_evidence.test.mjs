import test from 'node:test';
import assert from 'node:assert/strict';
import {validateWorkflow} from './workflow_evidence.mjs';
const id=n=>'65000000-0000-4000-8000-'+String(n).padStart(12,'0');
const hash=n=>String(n).repeat(64);
function fixture(){
 const expected=['INSERT','UPDATE','DELETE'].map(op=>({table:'fmz6e11_private.proposals',op,old:op==='INSERT'?null:hash(1),new:op==='DELETE'?null:hash(1)}));
 const contract={request_id:id(1),actor:id(2),session_id:id(3),workspace:id(4),window:id(5),key:id(6),payload_sha:hash(2),
  route:'A',operation:'apply',outcome:'committed',expected,versions_before:{revision:1,a_version:1},versions_after:{revision:2,a_version:2}};
 const before={versions:contract.versions_before,sha256:hash(3),observers_complete:true,observer_sha:hash(4),protected_rows:[{key:hash(5),value:hash(6)}]};
 const after={...structuredClone(before),versions:contract.versions_after,sha256:hash(7)};
 const receipt={request_id:id(1),actor:id(2),session_id:id(3),workspace_id:id(4),window_id:id(5),idempotency_key:id(6),payload_sha:hash(2),
  route:'A',action:'apply',selected_branch:'committed',state:'pair_validated',action_id:id(7),run_id:id(8),xid:'1001',backend:123,
  versions_before:contract.versions_before,versions_after:contract.versions_after,before_sha:before.sha256,after_sha:after.sha256};
 const writes=expected.map((e,i)=>({action_id:id(7),run_id:id(8),xid:'1001',backend:123,actor:id(2),workspace:id(4),ordinal:i+1,
  table_name:e.table,operation:e.op,old_key_sha:e.old,new_key_sha:e.new}));
 return {contract,before,receipt,writes,after};
}
const run=x=>validateWorkflow(x.contract,x.before,x.receipt,x.writes,x.after);
test('separate insert update delete including retained tombstone',async()=>{
 const result=await run(fixture());assert.equal(result.count,3);assert.deepEqual(result.changes.map(x=>x.count),[1,1,1]);
});
test('order does not matter but multiplicity does',async()=>{const x=fixture();x.writes.reverse();assert.equal((await run(x)).pair_complete,true);});
for(const key of ['request_id','actor','session_id','workspace_id','window_id','idempotency_key','payload_sha','route','action','selected_branch'])
test('reject wrong receipt '+key,async()=>{const x=fixture();x.receipt[key]='wrong';await assert.rejects(run(x),/receipt_binding/);});
for(const key of ['action_id','run_id','xid','backend','actor','workspace'])
test('reject foreign transaction '+key,async()=>{const x=fixture();x.writes[0][key]='wrong';await assert.rejects(run(x),/transaction_binding/);});
for(const [name,mutate] of [
 ['missing write',x=>x.writes.pop()],['extra write',x=>x.writes.push({...x.writes[0],ordinal:4})],
 ['duplicate ordinal',x=>x.writes[1].ordinal=1],['wrong row',x=>x.writes[0].new_key_sha=hash(8)],
 ['public table',x=>x.writes[0].table_name='public.profiles'],['missing tombstone',x=>x.writes[2].old_key_sha=null],
 ['incomplete pair',x=>x.receipt.state='confirmed'],['before hash',x=>x.before.sha256=hash(8)],
 ['after hash',x=>x.after.sha256=hash(8)],['wrong version',x=>x.after.versions={revision:9}],
 ['missing observer',x=>x.after.observers_complete=false],['changed observer',x=>x.after.observer_sha=hash(8)],
 ['protected data',x=>x.after.protected_rows=[]],['unplanned table',x=>x.contract.expected[0].table='public.profiles']])
test('reject '+name,async()=>{const x=fixture();mutate(x);await assert.rejects(run(x));});
