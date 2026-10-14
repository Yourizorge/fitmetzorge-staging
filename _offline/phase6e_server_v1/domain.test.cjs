'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const D=require('./domain.cjs');
const go=(s,action,data={},role='member')=>D.transition(s,{action,data},role);
const record=(s,row,actual)=>go(s,'record',{id:row.id,version:row.revision,
 planVersion:row.planVersion,unit:row.unit,source:row.source,actual});
function arrive(s){const row=s.recovery.rows.at(-1);return go(s,'recovery',{id:row.id,version:row.version,value:6});}
function apply(s){s=go(s,'confirm');if(s.route==='A')s=go(s,'approve',{},'trainer');return go(s,'apply');}
for(const route of ['A','B']){
 test(route+' durable-transition candidate keeps approvals separate',()=>{
  const initial=D.initial(route);let s=arrive(initial);assert.ok(s.review);
  assert.throws(()=>go(s,'apply'),/approvals/);
  s=go(s,'confirm');
  if(route==='A'){assert.throws(()=>go(s,'apply'),/approvals/);assert.throws(()=>go(s,'approve'),/actor/);s=go(s,'approve',{},'trainer');}
  else assert.throws(()=>go(s,'approve',{},'trainer'),/actor/);
  const previous=structuredClone(s.history);s=go(s,'apply');
  assert.equal(s.active.version,2);assert.deepEqual(s.history.slice(0,-1),previous);
  assert.throws(()=>go(s,'apply'),/version_conflict/);assert.equal(initial.active.version,1);
 });
 test(route+' source correction invalidates both approvals',()=>{
  let s=go(arrive(D.initial(route)),'confirm');
  if(route==='A')s=go(s,'approve',{},'trainer');
  const row=D.view(s).records.find(x=>x.kind==='training');
  s=record(s,row,{load:0,reps:0,rir:0,rpe:null});
  assert.equal(s.review?.member,false);assert.equal(s.review?.trainer,false);
  assert.throws(()=>go(s,'apply'),/approvals|version_conflict/);
  assert.equal(s.records[0].actual.rir,0);assert.equal(s.records[0].actual.rpe,null);
 });
 test(route+' restore is a new approved version and does not delete history',()=>{
  let s=apply(arrive(D.initial(route)));
  s=apply(go(s,'edit',{domain:'time',value:'20:00'}));
  s=go(s,'restore',{version:2});assert.equal(s.active.version,3);
  s=apply(s);assert.equal(s.active.version,4);assert.equal(s.history.length,4);
  assert.equal(s.history.at(-1).restores,2);
 });
 test(route+' current or reported resolved health never grants physical approval',()=>{
  let s=arrive(D.initial(route));s=go(s,'health',{value:'current'});
  s=go(s,'health',{value:'reported_resolved'});assert.equal(s.healthLatch,true);
  assert.throws(()=>go(s,'build'),/safety/);
  const row=D.view(s).records[0];s=record(s,row,{load:null,reps:0,rir:null,rpe:5});
  assert.equal(s.records[0].actual.reps,0);assert.equal(s.review,null);
 });
}
test('B intake uses original training/nutrition validators and immutable history',()=>{
 let s=D.initial('B');const old=structuredClone(s.history);
 const data={training:structuredClone(s.pair.training.fixture.intake),nutrition:structuredClone(s.pair.nutrition.fixture.intake)};
 s=go(s,'intake',data);s=go(s,'build');assert.ok(s.review.target.nutrition.ruleId);
 s=apply(s);assert.deepEqual(s.history.slice(0,1),old);
 assert.equal(s.active.version,2);
});
test('incomplete intake remains missing and cannot produce a plan',()=>{
 let s=D.initial('B');
 const data={training:structuredClone(s.pair.training.fixture.intake),nutrition:structuredClone(s.pair.nutrition.fixture.intake)};
 data.nutrition.target={status:'missing',value:null};
 s=go(s,'intake',data);assert.throws(()=>go(s,'build'));
 assert.equal(s.review,null);assert.equal(s.pair.nutrition.fixture.intake.target.value,null);
});
test('A intake cannot create new physical trainer authority',()=>assert.throws(()=>go(D.initial('A'),'intake',{training:{},nutrition:{}}),/route/));
test('all planned sets can be recorded; completion is explicit',()=>{
 let s=D.initial('B');const original=structuredClone(s.active);
 for(const row of D.view(s).records.filter(x=>x.kind==='training'))s=record(s,row,{load:null,reps:row.planned.reps.min,rir:0,rpe:7.5});
 assert.deepEqual(s.closed,{});
 for(const workout of [...new Set(s.records.filter(x=>x.kind==='training').map(x=>x.workout))])s=go(s,'finish_workout',{workout});
 assert.equal(s.workoutClosures.length,2);assert.deepEqual(s.active,original);
});
test('partial food is not full day; all explicit uneaten produces zero not null',()=>{
 let s=D.initial('B');assert.equal(D.view(s).foodSummary.totals,null);
 const row=D.view(s).records.find(x=>x.kind==='nutrition');
 s=record(s,row,{state:'not_eaten',grams:0});s=go(s,'finish_day');
 assert.equal(s.dayHistory[0].summary.completePlan,false);
 for(const row of D.view(s).records.filter(x=>x.kind==='nutrition'))s=record(s,row,{state:'not_eaten',grams:0});
 assert.equal(D.view(s).foodSummary.totals.energy,0);
 assert.equal(D.view(s).foodSummary.fullDayIntake,false);
});
test('exact full food totals follow product versions, not a new formula',()=>{
 let s=D.initial('B');
 for(const row of D.view(s).records.filter(x=>x.kind==='nutrition'))s=record(s,row,{state:'eaten',grams:row.planned.grams});
 const summary=D.view(s).foodSummary;
 assert.deepEqual(summary.totals,s.active.nutrition.total);assert.equal(summary.completePlan,true);
 assert.equal(summary.fullDayIntake,false);assert.equal(s.dayClose,null);
});
test('row, unit and original snapshot binding reject bad records',()=>{
 const s=D.initial('B'),row=D.view(s).records[0],v={load:0,reps:0,rir:0,rpe:null};
 for(const change of [{unit:'lb'},{planVersion:999},{source:'x'},{revision:999}])
  assert.throws(()=>record(s,{...row,...change},v));
 assert.equal(s.revision,0);
});
test('source correction preserves old closure and reopens only that workout',()=>{
 let s=D.initial('B'),row=D.view(s).records[0];
 s=record(s,row,{load:null,reps:10,rir:0,rpe:null});s=go(s,'finish_workout',{workout:row.workout});
 const old=structuredClone(s.workoutClosures[0]);row=D.view(s).records[0];
 s=record(s,row,{load:null,reps:9,rir:1,rpe:6});
 assert.deepEqual(s.workoutClosures[0],old);assert.equal(s.closed[row.workout],undefined);
});
test('withdrawn consent blocks later processing but preserves history',()=>{
 let s=apply(arrive(D.initial('B')));const history=structuredClone(s.history);
 s=go(s,'revoke');assert.throws(()=>go(s,'build'),/consent/);
 assert.deepEqual(s.history,history);assert.equal(D.view(s).active.version,2);
});
test('unavailable or expired source cannot silently acquire a rule',()=>{
 const s=D.initial('B');s.pair.training.fixture.catalog.rules=[];
 assert.throws(()=>go(s,'build'));
 const expired=D.initial('B');expired.clock=expired.pair.link.expires;
 assert.throws(()=>go(expired,'build'),/expired_source/);
});
test('an unchanged registration does not duplicate source or notification',()=>{
 let s=D.initial('B'),row=D.view(s).records[0];
 const v={load:0,reps:0,rir:0,rpe:null};s=record(s,row,v);
 assert.deepEqual(record(s,D.view(s).records[0],v),s);
});
