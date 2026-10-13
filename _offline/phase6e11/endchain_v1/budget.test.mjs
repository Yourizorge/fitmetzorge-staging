import test from 'node:test';
import assert from 'node:assert/strict';
import {SqlBudget,ENDCHAIN_RUN_ID,PURPOSE,LIMITS,limitFor} from './budget.mjs';
const zero={temp_written:0,own_wal_bytes:0,background_wal_bytes:0,background_temp_bytes:0};
const make=()=>new SqlBudget({runId:ENDCHAIN_RUN_ID,now:()=>1});
const use=(b,phase,safety=false)=>{const e=b.charge(phase,safety?'safety_check':'metadata_read',{safety});b.finish(e,zero);};
test('exact single run and purpose only; old cap unchanged',()=>{
 assert.equal(limitFor({id:ENDCHAIN_RUN_ID,budget_ref:PURPOSE}),1280);
 for(const g of [{},{id:ENDCHAIN_RUN_ID},{id:'other',budget_ref:PURPOSE}])assert.equal(limitFor(g),128);
 assert.throws(()=>new SqlBudget({runId:'other'}),/run_not_registered/);
});
test('phase allocations sum exactly 1280',()=>assert.equal(Object.values(LIMITS).reduce((a,b)=>a+b),1280));
test('truthy strings cannot enter safety reserve',()=>assert.throws(()=>make().charge('cleanup','safety_check',{safety:'true'}),/safety_flag_invalid/));
test('query completing beyond deadline stops before a next action',()=>{
 let clock=0;const b=new SqlBudget({runId:ENDCHAIN_RUN_ID,now:()=>clock});
 const e=b.charge('auth','auth_before');clock=540001;
 assert.throws(()=>b.finish(e,zero),e=>e.code==='run_deadline'&&e.command===1);
});
test('clock moving backwards is not accepted',()=>{
 let clock=10;const b=new SqlBudget({runId:ENDCHAIN_RUN_ID,now:()=>clock});
 const e=b.charge('auth','auth_before');clock=9;
 assert.throws(()=>b.finish(e,zero),/clock_invalid/);
});
for(const phase of Object.keys(LIMITS))test('no borrowing from other phase: '+phase,()=>{
 const b=make(),safety=['cleanup','final'].includes(phase);
 for(let i=0;i<LIMITS[phase];i++)use(b,phase,safety);
 assert.throws(()=>use(b,phase,safety),e=>e.code==='phase_query_budget'&&e.command===LIMITS[phase]+1);
 assert.equal(b.total,LIMITS[phase]);
});
test('normal failure retains exact query number; only reserved safety remains',()=>{
 const b=make(),e=b.charge('auth','auth_before');b.fail(e,'auth_binding');
 assert.deepEqual(b.failure,{phase:'auth',command:1,code:'auth_binding'});
 assert.throws(()=>use(b,'route_a'),/run_stopped/);
 use(b,'cleanup',true);assert.equal(b.total,2);
 assert.equal(b.failure.command,1);
});
test('unrecognized safety operation and wrong safety phase denied',()=>{
 assert.throws(()=>make().charge('cleanup','new_token',{safety:true}),/safety_scope/);
 assert.throws(()=>make().charge('auth','guard_remove',{safety:true}),/safety_scope/);
});
test('all 338 ordinary cleanup commands fit before the 48-command safety reserve',()=>{
 const b=make();
 for(let i=0;i<338;i++)use(b,'cleanup');
 assert.throws(()=>use(b,'cleanup'),/phase_query_budget/);
 for(let i=0;i<48;i++)use(b,'cleanup',true);
 assert.equal(b.used.cleanup,386);
});
test('one active query only',()=>{
 const b=make();b.charge('baseline','metadata_read');
 assert.throws(()=>b.charge('baseline','metadata_read'),/parallel_query/);
 assert.equal(b.total,1);
});
test('own temp write stops at executed command, not next command',()=>{
 const b=make(),e=b.charge('route_a','workflow_call');
 assert.throws(()=>b.finish(e,{...zero,temp_written:1}),e=>e.command===1&&e.code==='own_temp_write');
});
test('ambient WAL and temp are recorded separately, not relabelled as own',()=>{
 const b=make(),e=b.charge('baseline','metadata_read');
 const v=b.finish(e,{...zero,background_temp_bytes:17,background_wal_bytes:999});
 assert.equal(v.temp_written,0);assert.equal(v.own_wal_bytes,0);assert.equal(b.stopped,false);
});
test('unexplained ambient load must be explicitly stopped by IO validator',()=>{
 const b=make();use(b,'baseline');
 assert.throws(()=>b.stop('baseline','unattributed_temp_write'),/unattributed_temp_write/);
 assert.throws(()=>use(b,'auth'),/run_stopped/);
});
for(const field of Object.keys(zero))test('missing metric denied: '+field,()=>{
 const b=make(),e=b.charge('baseline','metadata_read'),m={...zero};delete m[field];
 assert.throws(()=>b.finish(e,m),e=>e.code==='query_metric_missing'&&e.command===1);
});
test('wall-clock reserve and hard safety deadline',()=>{
 let clock=0;const b=new SqlBudget({runId:ENDCHAIN_RUN_ID,now:()=>clock});
 clock=540000;assert.throws(()=>use(b,'auth'),/run_deadline/);
 use(b,'cleanup',true);clock=600000;
 assert.throws(()=>use(b,'cleanup',true),/run_deadline/);
});
test('receipt from another query rejected',()=>{
 const b=make();b.charge('baseline','metadata_read');
 assert.throws(()=>b.finish({command:1},zero),/query_receipt_binding/);
});
test('no secrets enter generic error receipt',()=>{
 const b=make(),e=b.charge('auth','auth_call');b.fail(e,'postgres://user:secret@host');
 assert.equal(b.failure.code,'query_failed');
 assert.ok(!JSON.stringify(b.snapshot()).includes('secret'));
});
