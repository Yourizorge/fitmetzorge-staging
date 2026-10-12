import test from 'node:test';
import assert from 'node:assert/strict';
import {existingIdentityGuard,LOCK_IDENTITY} from './auth_guard.mjs';
import {EMAILS,SyntheticAuth} from './auth.mjs';
const expected={id:'65000000-0000-4000-8000-000000000002',role:'b_member',trainer_id:null};
const identity={id:expected.id,email:EMAILS.b_member,registered_role:'b_member',profile_role:'client',trainer_id:null,enabled:true,operator:false,alias_key_locked:true};
function rig({rows=[identity],fail,check=()=>{}}={}){
 const events=[];let actions=0;
 const query=async(sql,args)=>{events.push({sql,args});if(sql===fail)throw Error('not-exportable');return sql===LOCK_IDENTITY?rows:[];};
 const guard=existingIdentityGuard({query,check});
 return {guard,events,action:async()=>{actions++;return {status:'synthetic'};},get actions(){return actions;}};
}
test('exact existing identity locked before issuance and released afterwards',async()=>{
 const r=rig();assert.deepEqual(await r.guard(expected,r.action),{status:'synthetic'});
 assert.deepEqual(r.events.map(x=>x.sql),['BEGIN',"SET LOCAL lock_timeout='1s'","SET LOCAL statement_timeout='2s'",LOCK_IDENTITY,'ROLLBACK']);
 assert.deepEqual(r.events[3].args,[expected.id,EMAILS.b_member]);assert.equal(r.actions,1);
});
for(const changed of [{id:'other'},{email:'other'},{enabled:false},{profile_role:'trainer'},{registered_role:'a_trainer'},{trainer_id:expected.id},{operator:true}])
test('stale or changed '+Object.keys(changed)[0]+' prevents Auth write',async()=>{
 const r=rig({rows:[{...identity,...changed}]});await assert.rejects(r.guard(expected,r.action),/identity_not_allowlisted/);
 assert.equal(r.actions,0);assert.equal(r.events.at(-1).sql,'ROLLBACK');
});
test('deleted identity never invokes generate_link',async()=>{
 const r=rig({rows:[]});await assert.rejects(r.guard(expected,r.action),/identity_not_allowlisted/);assert.equal(r.actions,0);
});
for(const value of [false,null,undefined])test('unproven alias stability '+value+' performs no Auth call',async()=>{
 const r=rig({rows:[{...identity,alias_key_locked:value}]});
 await assert.rejects(r.guard(expected,r.action),/alias_stability_unproven/);assert.equal(r.actions,0);
 assert.equal(r.events.at(-1).sql,'ROLLBACK');
});
test('failure in Auth service still releases database lock, not called again',async()=>{
 const r=rig();await assert.rejects(r.guard(expected,async()=>{throw Error('upstream');}),/upstream/);
 assert.equal(r.events.at(-1).sql,'ROLLBACK');assert.equal(r.events.filter(x=>x.sql==='BEGIN').length,1);
});
test('failure to release lock is explicit and fail closed',async()=>{
 const r=rig({fail:'ROLLBACK'});await assert.rejects(r.guard(expected,r.action),/identity_unlock_unconfirmed/);
});
test('expiry after lock prevents Auth call',async()=>{
 let n=0;const r=rig({check:()=>{if(++n===2)throw Error('expired');}});
 await assert.rejects(r.guard(expected,r.action),/expired/);assert.equal(r.actions,0);assert.equal(r.events.at(-1).sql,'ROLLBACK');
});
test('parallel operation cannot reuse locked connection',async()=>{
 const r=rig();let release;const first=r.guard(expected,()=>new Promise(resolve=>release=resolve));
 while(!release)await new Promise(r=>setTimeout(r,1));
 await assert.rejects(r.guard(expected,r.action),/identity_guard_scope/);release();await first;
});
test('Auth helper fails before HTTP when guard is missing',async()=>{
 let calls=0;const a=new SyntheticAuth({expected,identity,key:'synthetic',admin:'synthetic',fetcher:()=>{calls++;}});
 await assert.rejects(a.issue(),/identity_guard_absent/);assert.equal(calls,0);
});
