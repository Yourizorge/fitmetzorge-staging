'use strict';
const {test}=require('node:test'),a=require('node:assert/strict'),R=require('./registration12.cjs');
test('frozen12 registration keeps immutable snapshot, kg/lb, null and zero',()=>{
 for(const scenario of ['normal','lb']){
  let s=R.initial(scenario),v=R.view(s),original=structuredClone(s.original);
  v.draft.sets[0].rir=0;v.draft.sets[0].rpe=null;v.draft.sets[0].reps=0;
  s=R.transition(s,{action:'register12',data:{input:v.draft}});
  const first=structuredClone(s.records);v=R.view(s);v.draft.sets[0].reps=8;
  s=R.transition(s,{action:'register12',data:{input:v.draft}});
  a.deepEqual(s.original,original);a.deepEqual(s.records[0],first[0]);
  a.equal(R.view(s).registrations[0].sets[0].rir,0);a.equal(R.view(s).registrations[0].sets[0].rpe,null);
  a.equal(R.view(s).reflection.physical_advice_authorized,false);
 }
});
test('registration binding, foreign sets, source changes and duplicate version reject',()=>{
 const s=R.initial(),d=R.view(s).draft;
 for(const mutate of [d=>d.subject_id='other',d=>d.source_hash='0'.repeat(64),d=>d.sets.push(structuredClone(d.sets[0])),
  d=>d.sets[0].load.unit='lb',d=>d.revision=2]){
  const input=structuredClone(d);mutate(input);a.throws(()=>R.transition(s,{action:'register12',data:{input}}));
 }
 const next=R.transition(s,{action:'register12',data:{input:d}});
 a.throws(()=>R.transition(next,{action:'register12',data:{input:d}}));
 next.original.exercises[0].exercise_id='changed';a.throws(()=>R.view(next));
});
test('revocation retains records and cannot activate other packages',()=>{
 const s=R.initial(),saved=R.transition(s,{action:'register12',data:{input:R.view(s).draft}});
 const revoked=R.transition(saved,{action:'revoke',data:{}});
 a.equal(R.view(revoked).registrations.length,1);
 for(const action of ['register12','apply','approve','record'])a.throws(()=>R.transition(revoked,{action,data:{}}));
});
