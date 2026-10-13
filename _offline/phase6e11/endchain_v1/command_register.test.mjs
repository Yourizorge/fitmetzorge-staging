import test from 'node:test';
import assert from 'node:assert/strict';
import {compileRegister,RegisteredExecutor} from './command_register.mjs';
const hash='a'.repeat(64);
const phases=['baseline','fixtures','guard','observer','auth','controller','route_a',
 'route_b','restore','measurements','io','cleanup','final','closure'];
const cmd=(id,phase='cleanup',extra={})=>({id,phase,type:'sql',source_sha:hash,template_sha:hash,
 adapter:'test_adapter',mutates:false,deadline_ms:5000,protocol_commands:1,depends_on:[],...extra});
function input(){
 const steps=phases.map((p,i)=>cmd('command_'+i,p));
 return {steps,sourceHashes:{test_adapter:hash},complete:true,
 failures:Array.from({length:steps.length+1},(_,after)=>({after,
 commands:[cmd('rollback','closure',{safety:true}),cmd('close','closure',{safety:true})]}))};
}
function exec(register,action=async()=>({receipt_sha:hash,io_pair_sha:hash,validated:true}),persist=async()=>{}){
 return new RegisteredExecutor({register,localOnly:true,adapters:{test_adapter:{source_sha:hash,execute:action}},
  persist,now:()=>0,expiresAt:600000});
}
test('all fourteen phases and every stop prefix are registered',()=>{
 const r=compileRegister(input());assert.equal(r.normal_sql,14);assert.equal(r.minimum_registered_limit,16);
 assert.equal(r.reserves.length,15);assert.equal(r.budget_fits,true);assert.equal(r.hosted_admitted,false);
 assert.equal(Object.values(r.phase_counts).reduce((a,b)=>a+b),14);
});
test('missing category prevents complete admission',()=>{
 const p=input();p.steps[2].phase='baseline';assert.throws(()=>compileRegister(p),/incomplete_register_claim/);
});
test('a missing stop suffix is not silently costed at zero',()=>{
 const p=input();p.failures.splice(3,1);assert.throws(()=>compileRegister(p),/incomplete_register_claim/);
 p.complete=false;const r=compileRegister(p);assert.deepEqual(r.uncovered_prefixes,[3]);assert.equal(r.budget_fits,false);
});
test('uncompiled lifecycle is explicit and never admits execution',()=>{
 const p=input();p.complete=false;p.missing=['fixture_lifecycle'];const r=compileRegister(p);
 assert.equal(r.budget_fits,false);assert.throws(()=>exec(r),/register_not_admitted/);
});
test('one helper cannot hide BEGIN/COMMIT or cursor commands',()=>{
 const p=input();p.steps[0].protocol_commands=4;assert.throws(()=>compileRegister(p),/hidden_protocol_commands/);
});
test('SQL is never relabelled as HTTP to escape its counter',()=>{
 const p=input();p.steps[0].type='http';assert.throws(()=>compileRegister(p),/non_sql_misclassified/);
});
test('cleanup is reserved after every prefix, not only at entry',()=>{
 const p=input();p.failures[8].commands=Array.from({length:1273},(_,i)=>cmd('cleanup_'+i,'cleanup',{safety:true}));
 const r=compileRegister(p);assert.equal(r.minimum_registered_limit,1281);assert.equal(r.extra_sql,1);
 assert.equal(r.reserves[8].total,1281);assert.equal(r.budget_fits,false);
});
for(const kind of ['normal','cleanup'])test('source edits invalidate '+kind+' commands',()=>{
 const p=input(),c=kind==='normal'?p.steps[0]:p.failures[0].commands[0];c.source_sha='b'.repeat(64);
 assert.throws(()=>compileRegister(p),/source_binding/);
});
test('unbound or new business mutation cannot enter a safety route',()=>{
 const p=input();p.failures[0].commands[0].mutates=true;
 assert.throws(()=>compileRegister(p),/mutation_unbound/);
 Object.assign(p.failures[0].commands[0],{writeset_sha:hash,pair:'cleanup_pair',phase:'route_a'});
 assert.throws(()=>compileRegister(p),/failure_new_mutation/);
});
test('duplicate commands or cleanup identities are rejected',()=>{
 const p=input();p.steps[1].id=p.steps[0].id;assert.throws(()=>compileRegister(p),/duplicate_command_id/);
 const q=input();q.failures[0].commands[1].id=q.failures[0].commands[0].id;
 assert.throws(()=>compileRegister(q),/duplicate_cleanup_command/);
});
test('register does not authorize hosted execution',()=>{
 assert.throws(()=>new RegisteredExecutor({register:compileRegister(input()),persist:async()=>{},expiresAt:1}),/hosted_executor_not_admitted/);
});
test('normal execution charges every protocol command and persists both sides',async()=>{
 const saved=[],r=compileRegister(input()),e=exec(r,undefined,async v=>saved.push(v));
 for(const _ of r.commands)await e.next();
 assert.equal(e.used,14);assert.equal(saved.length,28);
 assert.deepEqual(saved.map(x=>x.status),Array(14).fill(['started','confirmed']).flat());
 assert.equal((await e.evidence()).hosted_admitted,false);
});
test('SQL failures retain first error and permit only the registered safety suffix',async()=>{
 for(let position=0;position<14;position++){
  let n=0;const r=compileRegister(input()),e=exec(r,async c=>{
   if(n++===position)throw Error('postgres://secret');
   return {receipt_sha:hash,io_pair_sha:hash,validated:true};
  });
  for(let i=0;i<position;i++)await e.next();await assert.rejects(()=>e.next());
  assert.equal(e.failure.command,position+1);await assert.rejects(()=>e.next(),/executor_closed/);
  await e.safety();assert.equal(e.used,position+3);assert.ok(!JSON.stringify(await e.evidence()).includes('secret'));
  await assert.rejects(()=>e.safety(),/safety_replayed/);
 }
});
test('missing SQL or IO evidence is not replaced by zero measurements',async()=>{
 const e=exec(compileRegister(input()),async()=>({}));
 await assert.rejects(()=>e.next(),/sql_receipt_missing/);
 const f=exec(compileRegister(input()),async()=>({receipt_sha:hash,validated:true}));
 for(let i=0;i<10;i++)await f.next();await assert.rejects(()=>f.next(),/io_receipt_missing/);
});
test('no command is sent if durable intent fails',async()=>{
 let calls=0;const e=exec(compileRegister(input()),async()=>{calls++;},async()=>{throw Error('disk');});
 await assert.rejects(()=>e.next());assert.equal(calls,0);assert.equal(e.used,0);
});
test('failed cleanup does not skip independent guard/access closure',async()=>{
 const p=input();p.failures[0].commands=[cmd('guard_inspect','guard',{safety:true}),
  cmd('guard_remove','guard',{safety:true,depends_on:['guard_inspect']}),
  cmd('jit_revoke','closure',{safety:true,type:'http',protocol_commands:0})];
 const calls=[],e=exec(compileRegister(p),async c=>{
  calls.push(c.id);if(c.id==='guard_inspect')throw Error('network');
  return {receipt_sha:hash,validated:true};
 });
 const result=await e.safety();assert.equal(result.complete,false);
 assert.deepEqual(calls,['guard_inspect','jit_revoke']);assert.equal(e.used,1);
 assert.equal(result.failures[1].code,'safety_dependency_failed');
});
test('cleanup cannot depend on an unknown or future command',()=>{
 const p=input();p.failures[0].commands[0].depends_on=['unknown'];
 assert.throws(()=>compileRegister(p),/safety_dependency/);
});

test('caller mutation cannot change the admitted commands or reserves',async()=>{
 const r=compileRegister(input()),calls=[],e=exec(r,async c=>{
  calls.push(c.id);return {receipt_sha:hash,validated:true};
 });
 r.commands[0].id='injected';r.reserves[1].reserved_sql=0;r.failures[0].commands=[];
 await e.next();assert.deepEqual(calls,['command_0']);assert.equal(e.register.reserves[1].reserved_sql,2);
 assert.throws(()=>{e.register.commands[0].phase='auth';},TypeError);
});

test('expired normal work does not disable separately bounded safety closure',async()=>{
 let now=0;const calls=[],e=new RegisteredExecutor({register:compileRegister(input()),localOnly:true,
  adapters:{test_adapter:{source_sha:hash,execute:async c=>{calls.push(c.id);return {receipt_sha:hash,validated:true};}}},
  persist:async()=>{},now:()=>now,expiresAt:120000,safetyExpiresAt:180000});
 now=120001;await assert.rejects(()=>e.next(),/hard_limit/);
 const result=await e.safety();assert.equal(result.complete,true);assert.deepEqual(calls,['rollback','close']);
});

test('a separate safety deadline cannot extend the ten-minute authorization',()=>{
 assert.throws(()=>new RegisteredExecutor({register:compileRegister(input()),localOnly:true,
  adapters:{test_adapter:{source_sha:hash,execute:async()=>{}}},persist:async()=>{},now:()=>0,
  expiresAt:120000,safetyExpiresAt:600001}),/safety_deadline/);
});
