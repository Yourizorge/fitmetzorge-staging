'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),S=require('./sync_contract.cjs'),A=require('./access_policy.cjs');
const actor='10000000-0000-4000-8000-000000000001',workspace='20000000-0000-4000-8000-000000000001',request_id='30000000-0000-4000-8000-000000000001';
function base(){return {actor,workspace,request_id,version:4,source:'a'.repeat(64),request:{action:'recovery',data:{id:'synthetic-recovery',version:1,value:0}}};}
test('offline request keeps identity, source, original version and idempotency; never automatic',()=>{
 const d=S.draft(base()),current={authenticated:true,actor,workspace,version:4,source:d.source,consent:true};
 const ready=S.reconcile(d,current);assert.equal(ready.submit,false);assert.equal(ready.payload.request_id,request_id);
 assert.equal(S.reconcile(d,{...current,version:5}).status,'conflict_review_required');
 assert.equal(S.reconcile(d,{...current,source:'b'.repeat(64)}).status,'conflict_review_required');
 for(const patch of [{actor:workspace},{workspace:actor},{authenticated:false},{consent:false}])assert.throws(()=>S.reconcile(d,{...current,...patch}));
 const receipt={request_id,payload_hash:S.digest({expected:4,request:d.request}),version:5};assert.equal(S.reconcile(d,{...current,version:5},receipt).status,'already_saved');
 assert.throws(()=>S.reconcile(d,current,{...receipt,payload_hash:'b'.repeat(64)}));
 assert.throws(()=>S.reconcile({...d,request:{action:'apply',data:{}}},current));
});
test('offline draft excludes approval/application and secrets',()=>{
 for(const action of ['confirm','approve','apply','restore','activate','revoke','record','finish_day'])assert.throws(()=>S.draft({...base(),request:{action,data:{}}}));
 for(const key of ['password','token','service_role','refresh_token','role'])assert.throws(()=>S.draft({...base(),request:{action:'recovery',data:{[key]:'not-a-real-secret'}}}));
});
const source=()=>({id:'synthetic-access',version:1,synthetic_only:true,verified:true,grants:[{id:'trial-1',kind:'trial',tier:'ai',start:0,end:30*A.DAY,revoked:false}]});
test('accepted thirty-day trial boundaries and fallback retain history, never renew',()=>{
 const s=source();assert.equal(A.view(s,0).tier,'ai');assert.equal(A.view(s,30*A.DAY-1).tier,'ai');assert.equal(A.view(s,30*A.DAY).tier,'free');
 s.grants.push({id:'existing-pro',kind:'paid',tier:'pro',start:0,end:60*A.DAY,revoked:false});assert.equal(A.view(s,30*A.DAY).tier,'pro');
 const end=A.view(s,60*A.DAY);assert.equal(end.tier,'free');assert.equal(end.retained_history,true);assert.equal(end.automatic_renewal,false);assert.equal(end.external_ai_enabled,false);
});
test('trial reminder identities are stable; malformed or repeated trials cannot grant access',()=>{
 const s=source();assert.equal(A.view(s,23*A.DAY-1).notices.length,0);assert.equal(A.view(s,23*A.DAY).notices.length,1);assert.equal(A.view(s,29*A.DAY).notices.length,2);assert.equal(A.view(s,30*A.DAY).notices.length,3);
 assert.deepEqual(A.view(s,30*A.DAY).notices,A.view(s,31*A.DAY).notices);
 s.grants[0].revoked=true;assert.equal(A.view(s,5*A.DAY).tier,'free');assert.equal(A.view(s,30*A.DAY).notices.length,0);
 assert.throws(()=>A.view({...s,verified:false},0));s.grants[0].end=7*A.DAY;assert.throws(()=>A.view(s,0));
 const duplicate=source();duplicate.grants.push({...duplicate.grants[0],id:'second'});assert.throws(()=>A.view(duplicate,0));
});
