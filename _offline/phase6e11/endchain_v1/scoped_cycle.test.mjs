import test from 'node:test';import assert from 'node:assert/strict';
import {ScopedCycle,GUARD} from './scoped_cycle.mjs';
const fixture=()=>{
 const calls=[];let next={readonly:true,fresh:true,backend:123,bound:true,instance:'test',value:{count:0}},closes=0;
 const c=new ScopedCycle({instance:'test',queries:{rows:"select '{}'::jsonb"},close:async()=>closes++,
  query:async q=>{calls.push(q);if(q==='ROLLBACK')return [];return [{...next}];}});
 return {c,calls,get next(){return next;},set next(v){next=v;},get closes(){return closes;}};
};
test('two fresh scoped snapshots use five commands in one explicit transaction',async()=>{
 const r=fixture();await r.c.begin();assert.deepEqual(await r.c.read('rows'),{count:0});
 r.next={...r.next,value:{count:1}};assert.deepEqual(await r.c.read('rows'),{count:1});
 await r.c.end();assert.equal(r.calls.length,5);assert.equal(r.calls[1],GUARD);assert.equal(r.closes,1);
});
for(const field of ['readonly','fresh','bound','instance','backend'])test('bad initial guard '+field,async()=>{
 const r=fixture();r.next={...r.next,[field]:field==='backend'?0:false};
 await assert.rejects(r.c.begin(),/readonly_unconfirmed/);assert.equal(r.calls.at(-1),'ROLLBACK');
 assert.equal(r.closes,1);await assert.rejects(r.c.begin(),/cycle_reuse/);
});
for(const [field,value] of [['readonly',false],['fresh',false],['backend',124]])
test('changed read connection '+field,async()=>{
 const r=fixture();await r.c.begin();r.next={...r.next,[field]:value};
 await assert.rejects(r.c.read('rows'),/scoped_connection_changed/);
 await assert.rejects(r.c.read('rows'),/scoped_query_denied/);await r.c.end();assert.equal(r.closes,1);
});
test('unregistered SQL and data content are not accepted',async()=>{
 const r=fixture();await r.c.begin();await assert.rejects(r.c.read('select private'),/scoped_query_denied/);
 r.next={...r.next,value:{password:'not-loggable'}};
 await assert.rejects(r.c.read('rows'),/metadata_field_denied/);await r.c.end();
});

for(const stage of ['begin','read'])test('sanitized '+stage+' failure survives rollback and close faults',async()=>{
 let broken=false,closed=0;
 const c=new ScopedCycle({instance:'test',queries:{rows:"select '{}'::jsonb"},
  query:async q=>{
   if(q==='ROLLBACK'||stage==='begin'||broken)throw Error('postgres://secret');
   return [{readonly:true,fresh:true,backend:123,bound:true,instance:'test'}];
  },close:async()=>{closed++;throw Error('Bearer secret');}});
 if(stage==='read'){await c.begin();broken=true;}
 let original;
 try{stage==='begin'?await c.begin():await c.read('rows');}catch(e){original=e;}
 if(stage==='read')await assert.rejects(c.end(),e=>e===original);
 assert.equal(original.code,stage==='begin'?'readonly_begin_unconfirmed':'scoped_read_unconfirmed');
 assert.deepEqual(original.cleanupFailures,[{phase:'rollback',code:'rollback_unconfirmed'},
  {phase:'close',code:'connection_close_unconfirmed'}]);
 assert.ok(!JSON.stringify(original).includes('secret'));assert.equal(closed,1);
 await c.end();assert.equal(closed,1);
});
