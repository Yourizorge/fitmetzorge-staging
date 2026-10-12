import test from 'node:test';
import assert from 'node:assert/strict';
import {Controller,Halt,metadata,PROJECT} from './core.mjs';
const id=n=>'65000000-0000-4000-8000-'+String(n).padStart(12,'0');
const now=1791801900000;
const contract={step:0,actor:id(2),action_id:id(3),request_id:id(4),workspace:null,kind:'auth',operation:'verify',writes:[]};
function rig({actionError,afterError,recordError,haltError}={}){
 const r={events:[],failure:null,actions:0};
 const store={claim:async()=>{},before:async()=>{},record:async(_r,_s,p)=>{r.events.push(p);if(recordError&&p==='action_confirmed')throw recordError;},
   halt:async(_r,_s,value)=>{if(haltError)throw haltError;r.failure=metadata(value);r.events.push('stopped');}};
 const controller=new Controller({grant:{project:PROJECT,id:id(1),sha:'a'.repeat(40),run:'123',manifest_sha:'b'.repeat(64),starts:now,expires:now+600000},store,now:()=>now});
 const adapter={measure:async phase=>{r.events.push('measure_'+phase);if(phase==='after'&&afterError)throw afterError;return {count:phase==='before'?0:1};},
   act:async()=>{r.actions++;if(actionError)throw actionError;return {status:'confirmed'};},
   validate:async()=>({pair_complete:true,protected_equal:true})};
 return {...r,controller,adapter,state:r};
}
for(const [phase,code] of [['transport','connection_deadline'],['authentication','session_revoked'],['transaction','transaction_rollback']])
test('unconfirmed '+phase+' retains distinct cause and forensic after-state',async()=>{
 const r=rig({actionError:new Halt(phase,code)});await r.controller.claim();
 await assert.rejects(r.controller.execute(contract,r.adapter),new RegExp(code));
 assert.deepEqual(r.state.failure.actual,{phase,code});assert.deepEqual(r.state.failure.before,{count:0});
 assert.deepEqual(r.state.failure.after,{count:1});assert.equal(r.state.failure.pair_complete,false);
 assert.ok(!r.state.events.includes('action_confirmed'));assert.equal(r.controller.step,0);
 await assert.rejects(r.controller.execute(contract,r.adapter),/controller_closed/);assert.equal(r.state.actions,1);
});
test('failed confirmed-receipt persistence still captures after-state without retry',async()=>{
 const r=rig({recordError:Error('do-not-log')});await r.controller.claim();
 await assert.rejects(r.controller.execute(contract,r.adapter),/operation_failed/);
 assert.equal(r.state.failure.phase,'action_confirmed');assert.deepEqual(r.state.failure.after,{count:1});
 assert.equal(r.state.actions,1);assert.ok(!JSON.stringify(r.state.failure).includes('do-not-log'));
});
test('missing forensic after-state is retained as missing, never a complete pair',async()=>{
 const r=rig({actionError:new Halt('transport','connection_deadline'),afterError:Error('private')});await r.controller.claim();
 await assert.rejects(r.controller.execute(contract,r.adapter),/connection_deadline/);
 assert.deepEqual(r.state.failure.after,{status:'missing',phase:'after_saved',code:'operation_failed'});
 assert.equal(r.state.events.filter(x=>x==='measure_after').length,1);assert.equal(r.state.failure.pair_complete,false);
});
test('normal failed after-measurement is not repeated',async()=>{
 const r=rig({afterError:Error('private')});await r.controller.claim();
 await assert.rejects(r.controller.execute(contract,r.adapter),/operation_failed/);
 assert.equal(r.state.events.filter(x=>x==='measure_after').length,1);assert.equal(r.controller.step,0);
});
test('failure to persist halt is explicit',async()=>{
 const r=rig({actionError:Error('private'),haltError:Error('private')});await r.controller.claim();
 await assert.rejects(r.controller.execute(contract,r.adapter),e=>e.code==='failure_record_missing'&&e.phase==='evidence');
 assert.equal(r.controller.stopped,true);
});
test('forensic measurement cannot raise the query budget',async()=>{
 const r=rig({actionError:new Halt('transport','connection_deadline')});await r.controller.claim();
 const measure=r.adapter.measure;r.adapter.measure=async p=>{if(p==='after')for(let i=0;i<129;i++)r.controller.command();return measure(p);};
 await assert.rejects(r.controller.execute(contract,r.adapter),/connection_deadline/);
 assert.equal(r.state.failure.after.code,'command_budget');assert.equal(r.controller.step,0);
});
