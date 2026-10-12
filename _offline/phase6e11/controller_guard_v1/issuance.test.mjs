import test from 'node:test';import a from 'node:assert/strict';
import {guardedIssuance,withSafetyRemoval} from './issuance.mjs';
import {EMAILS} from '../controller_v1/auth.mjs';
const run='68000000-0000-4000-8000-000000000080',schema='fmz6e11_guard_'+run.replaceAll('-','');
const id='68000000-0000-4000-8000-000000000001';
const receipt={run,schema,function_sha:'a'.repeat(64),expires_at:new Date(600000).toISOString(),trigger_shas:Object.fromEntries(['_i','_u','_d'].map(x=>[schema+x,'b'.repeat(64)]))};
const expected={id,role:'a_member',trainer_id:'68000000-0000-4000-8000-000000000002'};
const identity={id,email:EMAILS.a_member,registered_role:'a_member',profile_role:'client',trainer_id:expected.trainer_id,enabled:true,operator:false,alias_key_locked:false};
const attest={function_sha:receipt.function_sha,unexpired:true,definer:false,search_path:['search_path=pg_catalog, pg_temp'],acl:'{postgres=X/postgres}',trigger_shas:receipt.trigger_shas};
function setup(edit={}){
 let time=0;const calls=[];
 const query=async(q)=>{calls.push(q);if(q.includes('identity_lock'))return edit.identity??[identity];if(q.includes(':attest'))return edit.attest??[attest];if(q==='ROLLBACK'&&edit.rollbackFail)throw Error('secret not to be logged');return [];};
 return {calls,setTime:t=>time=t,guard:guardedIssuance({receipt:edit.receipt??receipt,query,check:edit.check??(()=>{}),now:()=>time})};
}
test('partial-index identity is admitted only with exact independent live guard',async()=>{
 const s=setup();a.equal(await s.guard(expected,async()=>42),42);a.equal(s.calls.at(-1),'ROLLBACK');a.equal(s.calls.length,6);
});
for(const [name,change] of Object.entries({missing:[],wrong_source:[{...attest,function_sha:'c'.repeat(64)}],expired:[{...attest,unexpired:false}],definer:[{...attest,definer:true}],public_execute:[{...attest,acl:'{=X/postgres}'}],wrong_path:[{...attest,search_path:[]}],missing_trigger:[{...attest,trigger_shas:{}}]}))
 test('guard denies '+name+' before Auth call',async()=>{const s=setup({attest:change});let called=false;await a.rejects(s.guard(expected,async()=>{called=true;}),/guard_attestation_failed/);a.equal(called,false);a.equal(s.calls.at(-1),'ROLLBACK');});
test('missing registered account cannot reach generate_link',async()=>{const s=setup({identity:[]});let called=false;await a.rejects(s.guard(expected,async()=>{called=true;}),/identity_not_allowlisted/);a.equal(called,false);});
test('wrong UUID and address denied',async()=>{const s=setup({identity:[{...identity,id:expected.trainer_id}]});await a.rejects(s.guard(expected,async()=>a.fail()),/identity_not_allowlisted/);});
test('last sixty seconds cannot begin issuance',async()=>{const s=setup();s.setTime(540000);await a.rejects(s.guard(expected,async()=>a.fail()),/guard_expired_or_closing/);a.equal(s.calls.length,0);});
test('expiry during issuance discards result and closes future issuance',async()=>{const s=setup();await a.rejects(s.guard(expected,async()=>{s.setTime(600000);return 'discard';}),/guard_expired_or_closing/);a.equal(s.calls.at(-1),'ROLLBACK');s.setTime(0);await a.rejects(s.guard(expected,async()=>a.fail()),/guard_expired_or_closing/);});
test('aborted issuance is not retried and rolls back the lock only',async()=>{const s=setup();let calls=0;await a.rejects(s.guard(expected,async()=>{calls++;throw Error('test_abort');}),/test_abort/);a.equal(calls,1);a.equal(s.calls.at(-1),'ROLLBACK');await a.rejects(s.guard(expected,async()=>a.fail()),/guard_expired_or_closing/);});
test('rollback failure is an explicit no-go',async()=>{const s=setup({rollbackFail:true});await a.rejects(s.guard(expected,async()=>1),/identity_unlock_unconfirmed/);});
test('no concurrent issuance',async()=>{const s=setup();let release;const started=new Promise(r=>release=r);let ready;const entered=new Promise(r=>ready=r);const first=s.guard(expected,async()=>{ready();await started;});await entered;await a.rejects(s.guard(expected,async()=>a.fail()),/guard_action_invalid/);release();await first;});
for(const failed of [false,true])test('safety removal independent of run NO-GO '+failed,async()=>{
 const events=[];const action=withSafetyRemoval({run:async()=>{events.push('run');if(failed)throw Error('no_go');return 1;},closeIssuance:()=>events.push('closed'),remove:async()=>events.push('removed'),verifyRemoved:async()=>{events.push('verified');return true;}});
 if(failed)await a.rejects(action,/no_go/);else a.equal(await action,1);a.deepEqual(events,['run','closed','removed','verified']);
});
test('unconfirmed removal overrides successful result',async()=>{await a.rejects(withSafetyRemoval({run:async()=>1,closeIssuance:()=>{},remove:async()=>{},verifyRemoved:async()=>false}),/guard_removal_unconfirmed/);});
