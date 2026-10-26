import test from 'node:test';
import assert from 'node:assert/strict';
import {safetyAuthlogout} from './safety_auth.mjs';
import {sha} from '../controller_v1/core.mjs';

const roles=['a_member','a_trainer','b_member'];
const session='69000000-0000-4000-8000-000000000001';

for(const fault of ['before_call','after_commit','after_snapshot']){
 test('stopped '+fault+' uses only logout and safety messages',async()=>{
  const calls=[],logout=[];
  const auths=Object.fromEntries(roles.map(role=>[role,{
   logout:async()=>{logout.push(role);return {http_status:204,session_sha:await sha(session)};},session:()=>session
  }]));
  const send=async request=>{
   calls.push(structuredClone(request));
   if(request.stage==='start')return {roles};
   if(request.stage==='finish')return {status:'NO_GO',revocation_confirmed:true};
   return {};
  };
  assert.equal((await safetyAuthlogout({send,auths,receipt:{bound:true}})).status,'NO_GO');
  assert.deepEqual(logout,roles);
  assert.deepEqual(calls.map(x=>x.stage),['start','before','after','before','after','before','after','finish']);
  assert.ok(calls.every(x=>x.op==='safetyAuthlogout'));
  assert.ok(calls.filter(x=>x.stage==='after').every(x=>/^[a-f0-9]{64}$/.test(x.result.key_sha)));
  assert.ok(!JSON.stringify(calls).includes('access_token'));
 });
}

test('lost logout HTTP result falls back once without retry or invented after',async()=>{
 const calls=[];let requests=0;
 const send=async q=>{calls.push(q);return q.stage==='start'?{roles}:{status:'NO_GO'};};
 const auths={a_member:{logout:async()=>{requests++;throw Error('lost_http');}}};
 assert.equal((await safetyAuthlogout({send,auths,receipt:{}})).status,'NO_GO');
 assert.equal(requests,1);assert.deepEqual(calls.map(x=>x.stage),['start','before','finish']);
});

test('unknown verify does not need tokens and never calls HTTP',async()=>{
 const calls=[];const send=async q=>{calls.push(q);return q.stage==='start'?{roles:[]}:{status:'NO_GO'};};
 await safetyAuthlogout({send,auths:{},receipt:{}});
 assert.deepEqual(calls.map(x=>x.stage),['start','finish']);
});

test('denied managed reservation cannot dispatch HTTP',async()=>{
 let requests=0;const stages=[];
 const send=async q=>{stages.push(q.stage);if(q.stage==='start')return {roles};if(q.stage==='before')throw Error('budget');return {status:'NO_GO'};};
 await safetyAuthlogout({send,auths:{a_member:{logout:()=>{requests++;}}},receipt:{}});
 assert.equal(requests,0);assert.deepEqual(stages,['start','before','finish']);
});
