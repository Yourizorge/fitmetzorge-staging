import test from 'node:test';
import assert from 'node:assert/strict';
import {Controller,createEndpoint,Halt,metadata,sha,validateGrant,PROJECT} from './core.mjs';
const now=1791801900000;
const id=n=>'65000000-0000-4000-8000-'+String(n).padStart(12,'0');
const grant=()=>({project:PROJECT,id:id(1),sha:'a'.repeat(40),run:'123',manifest_sha:'b'.repeat(64),starts:now,expires:now+600000});
const contract=()=>({step:0,actor:id(2),action_id:id(3),request_id:id(4),workspace:null,kind:'auth',operation:'verify',writes:[]});
function rig(fail){
 const events=[],claims=new Set();let writes=0;
 const emit=async phase=>{events.push(phase);if(phase===fail)throw Error('postgres://secret@host');};
 const store={claim:async g=>{if(claims.has(g.id))throw new Halt('admission','run_replayed');claims.add(g.id);await emit('claim');},
   before:async()=>emit('before_saved'),record:async(r,s,p)=>emit(p),halt:async()=>emit('halt')};
 const adapter={measure:async p=>{await emit('measure_'+p);return {rows:[],count:0};},
   act:async()=>{writes++;await emit('write');return {status:'expected'};},
   validate:async()=>{await emit('validate');return {pair_complete:true,protected_equal:true};}};
 return {events,store,adapter,get writes(){return writes;},controller:new Controller({grant:grant(),store,now:()=>now})};
}
test('durable phase sequence precedes the next action',async()=>{
 const r=rig();await r.controller.claim();await r.controller.execute(contract(),r.adapter);
 assert.deepEqual(r.events,['claim','measure_before','before_saved','action_started','write','action_confirmed','measure_after','after_saved','validate','pair_validated']);
 assert.equal(r.controller.step,1);
});
for(const phase of ['measure_before','before_saved','action_started','write','action_confirmed','measure_after','after_saved','validate','pair_validated'])
test('failure '+phase+' is closed without retry or cleanup',async()=>{
 const r=rig(phase);await r.controller.claim();
 await assert.rejects(r.controller.execute(contract(),r.adapter),e=>e instanceof Halt&&!e.message.includes('secret'));
 await assert.rejects(r.controller.execute(contract(),r.adapter),/controller_closed/);
 assert.equal(r.writes,['measure_before','before_saved','action_started'].includes(phase)?0:1);
 assert.equal(r.controller.step,0);assert.equal(r.events.at(-1),'halt');
});
test('restart cannot consume the same durable run',async()=>{
 const r=rig();await r.controller.claim();
 const restarted=new Controller({grant:grant(),store:r.store,now:()=>now});
 await assert.rejects(restarted.claim(),/run_replayed/);assert.equal(r.writes,0);
});
test('concurrent action blocked before second measurement',async()=>{
 const r=rig();await r.controller.claim();let release;
 const original=r.adapter.act;r.adapter.act=async()=>{await new Promise(x=>release=x);return original();};
 const pending=r.controller.execute(contract(),r.adapter);
 while(!release)await new Promise(x=>setTimeout(x,1));
 await assert.rejects(r.controller.execute(contract(),r.adapter),/controller_busy/);
 release();await pending;assert.equal(r.writes,1);
});
for(const change of [{project:'other'}, {expires:now}, {starts:now+1},{expires:now+600001},{run:'bad'}, {sha:'x'}, {manifest_sha:'x'}, {id:'x'}])
test('grant rejects '+JSON.stringify(change),()=>assert.throws(()=>validateGrant({...grant(),...change},now),/grant_invalid/));
test('expiry between durable intent and side effect blocks write',async()=>{
 const r=rig();let t=now;r.controller.now=()=>t;
 r.store.record=async()=>{t=now+600000;};await r.controller.claim();
 await assert.rejects(r.controller.execute(contract(),r.adapter),/controller_closed/);assert.equal(r.writes,0);
});
test('query cap cannot be silently raised',()=>{
 const r=rig();for(let i=0;i<128;i++)r.controller.command();assert.throws(()=>r.controller.command(),/command_budget/);
 assert.throws(()=>new Controller({grant:grant(),store:r.store,now:()=>now,maxCommands:129}),/budget_invalid/);
});
for(const value of [{password:'redacted'},{token:'redacted'},{status:'postgres://secret@host'}, {code:'Bearer_secret'}, {rows:[{session:'bad'}]}, {before:{value_sha:'bad'}}, {count:NaN}])
test('metadata rejects '+Object.keys(value),()=>assert.throws(()=>metadata(value)));
test('exact technical hashes, counters and dates allowed',()=>assert.deepEqual(metadata({count:2,value_sha:'a'.repeat(64),started_at:'2026-10-12T12:00:00.000Z'}),{count:2,value_sha:'a'.repeat(64),started_at:'2026-10-12T12:00:00.000Z'}));
test('canonical hashing is stable but preserves duplicates and null',async()=>{
 assert.equal(await sha({a:1,b:null}),await sha({b:null,a:1}));
 assert.notEqual(await sha([null,0]),await sha([null,null,0]));
});
for(const [name,method,headers,body] of [
 ['GET','GET',{},undefined],['browser','POST',{origin:'https://yourizorge.github.io'},'{}'],
 ['missing auth','POST',{},'{}'],['forged','POST',{authorization:'Bearer wrong'},'{}'],
 ['payload','POST',{authorization:'Bearer valid'},'{"actor":"other"}'],['empty','POST',{authorization:'Bearer valid'},''],
 ['role','POST',{authorization:'Bearer valid'},'{"role":"trainer"}']])
test('endpoint denies '+name+' before side effects',async()=>{
 let calls=0;const h=createEndpoint({grant:grant(),now:()=>now,verify:async x=>{if(x!=='Bearer valid')throw Error('private-token');},execute:async()=>{calls++;return {status:'PASS'};}});
 const response=await h(new Request('https://example.invalid',{method,headers,body}));
 assert.ok(response.status>=400);assert.equal(calls,0);assert.ok(!(await response.text()).includes('private-token'));
});
test('endpoint accepts only verified, empty fixed command',async()=>{
 const h=createEndpoint({grant:grant(),now:()=>now,verify:async()=>{},execute:async()=>({status:'LOCAL_PASS'})});
 assert.equal((await h(new Request('https://example.invalid',{method:'POST',body:'{}'}))).status,200);
});
test('negative preservation validation stops, never promotes a partial PASS',async()=>{
 const r=rig();await r.controller.claim();r.adapter.validate=async()=>({pair_complete:true,protected_equal:false});
 await assert.rejects(r.controller.execute(contract(),r.adapter),/pair_invalid/);assert.equal(r.controller.step,0);
});
