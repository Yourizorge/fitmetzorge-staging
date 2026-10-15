'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),Q=require('./draft_queue.js');
const R=require('./registration12.cjs');
const actor='00000000-0000-4000-8000-000000000001',workspace='00000000-0000-4000-8000-000000000002',request_id='00000000-0000-4000-8000-000000000003';
const view=()=>({actor,workspace,version:1,role:'member',state:{consent:true,snapshot:{source:1}},capabilities:{registration12:true}});
const payload=()=>{const input=R.view(R.initial()).draft;input.sets[0].rir=0;input.sets[0].rpe=null;return {workspace,request_id,version:1,request:{action:'register12',data:{input}}};};
test('exact account/source/version, zero and null preserved',async()=>{const e=await Q.create(view(),payload());assert.equal(await Q.inspect(e,view()),'pending');assert.equal(e.payload.request.data.input.sets[0].rir,0);assert.equal(e.payload.request.data.input.sets[0].rpe,null);assert.equal(await Q.inspect(e,{...view(),version:2}),'changed');assert.equal(await Q.inspect(e,{...view(),state:{consent:false}}),'consent');});
test('different actor/role, changed hash and physical actions cannot enter queue',async()=>{const e=await Q.create(view(),payload());await assert.rejects(Q.inspect(e,{...view(),actor:workspace}));await assert.rejects(Q.inspect(e,{...view(),role:'trainer'}));await assert.rejects(Q.checked({...e,payload:{...payload(),version:2}}));for(const action of ['apply','approve','confirm','start12','finish12','record'])await assert.rejects(Q.create(view(),{...payload(),request:{action,data:{}}}));});
test('no secret fields, invalid ids, wrong sources or out-of-bound payload',async()=>{for(const key of ['password','token','role','csrf','refresh_token'])await assert.rejects(Q.create(view(),{...payload(),request:{action:'register12',data:{[key]:'forbidden'}}}));await assert.rejects(Q.create({...view(),actor:'bad'},payload()));await assert.rejects(Q.create(view(),{...payload(),version:2}));await assert.rejects(Q.create(view(),{...payload(),request:{action:'recovery',data:{}}}));await assert.rejects(Q.create(view(),{...payload(),request:{action:'register12',data:{oversized:'x'.repeat(131072)}}}));});
test('only exact registration and recovery data shapes enter durable storage',async()=>{
 for(const change of [p=>p.request.data.input.email='private@example.test',p=>p.request.data.input.sets[0].accessToken='secret',p=>p.request.data.input.sets[0].load.key='secret',p=>p.request.data.input.sets[0].reps=NaN,p=>p.request.data.input.sets[0].rir=Infinity,p=>p.request.data.input.subject_id='Bearer secret.token']){const p=payload();change(p);await assert.rejects(Q.create(view(),p));}
 const v={...view(),state:{consent:true,sourceHash:'source'},capabilities:{registration12:false}};
 for(const value of [0,null,420]){const p={...payload(),request:{action:'recovery',data:{id:'sleep-1',version:0,value}}};const e=await Q.create(v,p);assert.equal(e.payload.request.data.value,value);assert.equal(await Q.inspect(e,v),'pending');}
});
test('missing source or workspace capability mismatch fails closed',async()=>{
 await assert.rejects(Q.create({...view(),state:{consent:true}},payload()),/draft_source/);
 const e=await Q.create(view(),payload());await assert.rejects(Q.inspect(e,{...view(),capabilities:{registration12:false}}),/draft_scope/);
 assert.equal(await Q.inspect(e,{...view(),state:{consent:true,snapshot:{source:2}}}),'changed');
});
test('payload mutation during async hashing cannot change the saved request',async()=>{
 const p=payload(),promise=Q.create(view(),p);p.request.data.input.sets[0].rir=9;
 const e=await promise;assert.equal(e.payload.request.data.input.sets[0].rir,0);
 const checked=Q.checked(e);e.payload.request.data.input.sets[0].rir=8;assert.equal((await checked).payload.request.data.input.sets[0].rir,0);
});
