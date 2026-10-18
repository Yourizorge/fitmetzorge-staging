import test from 'node:test';import assert from 'node:assert/strict';
import {validateManifest} from '../controller_v1/manifest.mjs';
import {ENDCHAIN_RUN_ID,PURPOSE} from './budget.mjs';
const id=n=>'69000000-0000-4000-8000-'+String(n).padStart(12,'0');
function fixture(){return {version:2,run_id:ENDCHAIN_RUN_ID,budget_ref:PURPOSE,max_commands:2349,
 identities:[{id:id(1),role:'a_member',trainer_id:id(2)},{id:id(2),role:'a_trainer',trainer_id:null},{id:id(3),role:'b_member',trainer_id:null}],
 workspaces:[{id:id(4),window:id(6),route:'A',member:id(1),trainer:id(2)},{id:id(5),window:id(6),route:'B',member:id(3),trainer:null}],
 cleanup:{operator_id:id(2),requires_revoked_window:true},
 actions:[{step:0,action_id:id(7),request_id:id(8),actor:id(2),workspace:id(5),kind:'workflow',operation:'cleanup_batch',
 writes:[{table:'fmz6e11_private.b_versions',operation:'DELETE',key:[id(5),1]}]}]};}
test('exact one-run operator cleanup can reach its synthetic B workspace only',()=>{
 assert.doesNotThrow(()=>validateManifest(fixture()));
});
test('A cleanup also requires the one-run explicit operator and revoke gate',()=>{
 const m=fixture();m.actions[0].workspace=id(4);m.actions[0].writes[0].key=[id(4),1];
 assert.doesNotThrow(()=>validateManifest(m));m.cleanup.requires_revoked_window=false;
 assert.throws(()=>validateManifest(m),/cleanup_scope/);
});
for(const [name,mutate] of [
 ['old manifest',m=>{m.version=1;m.max_commands=128;}],
 ['wrong run',m=>m.run_id=id(90)],['ordinary member',m=>m.actions[0].actor=id(1)],
 ['B member',m=>m.actions[0].actor=id(3)],['unregistered operator',m=>m.cleanup.operator_id=id(90)],
 ['no revoke condition',m=>m.cleanup.requires_revoked_window=false],
 ['business B action',m=>m.actions[0].operation='b_apply'],
 ['extra workspace',m=>m.actions[0].workspace=id(90)],
 ['nondelete',m=>m.actions[0].writes[0].operation='UPDATE'],
 ['empty',m=>m.actions[0].writes=[]],
 ['oversize',m=>m.actions[0].writes=Array.from({length:9},()=>m.actions[0].writes[0])]])
test('operator exception denies '+name,()=>{const m=fixture();mutate(m);assert.throws(()=>validateManifest(m));});
