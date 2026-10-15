'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),W=require('./workout12.cjs'),R=require('./registration12.cjs');
const go=(s,action,data={})=>W.transition(s,{action,data});
test('historical start, partial recording, explicit finish, correction and immutable facts',()=>{
 let s=R.initial('normal'),original=structuredClone(s.original);
 assert.throws(()=>go(s,'register12',{input:R.view(s).draft}),/not_started/);
 s=go(s,'start12');assert.throws(()=>go(s,'finish12'),/missing/);
 let input=R.view(s).draft;input.sets.forEach(x=>x.completed=false);input.sets[0].load.value=0;input.sets[0].reps=0;input.sets[0].rir=0;input.sets[0].rpe=null;input.sets[0].completed=true;
 s=go(s,'register12',{input});assert.equal(W.view(s).session12.status,'started');
 s=go(s,'finish12');assert.equal(W.view(s).session12.closures[0].completed,1);
 assert.equal(W.view(s).session12.closures[0].physical_advice_authorized,false);assert.throws(()=>go(s,'finish12'));
 s=go(s,'start12');assert.throws(()=>go(s,'finish12'),/already_finished/);
 input=R.view(s).draft;input.sets[0].completed=true;input.sets[0].reps=1;s=go(s,'register12',{input});s=go(s,'finish12');
 assert.equal(W.view(s).session12.closures.length,2);assert.deepEqual(s.original,original);
});
test('historical lifecycle does not enable full-day, application or consent bypass',()=>{
 let s=go(R.initial('no_trainer'),'start12');
 for(const action of ['apply','approve','finish_day','record'])assert.throws(()=>go(s,action));
 assert.throws(()=>go(s,'finish12',{role:'trainer'}));s=go(s,'revoke');assert.throws(()=>go(s,'start12'),/consent/);
 assert.equal(W.view(s).full_day21,false);
});
