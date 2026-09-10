"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),F=require("./fixtures.cjs");
const {canonical}=require("../common.cjs");
const special=new Set(["all_three","original_lb","exact_step","zero_preserved","null_preserved","maintain","inclusive_start","boundary_inclusive","safety","optional_clarification","optional_retry","observation_not_recognition_success","access","historical_sources_unchanged"]);
for(const c of F.prereg.cases)test("preregistered: "+c.id,()=>{
 const f=F.setup(c.id),before=canonical(f.request),state=canonical(f.state),r=F.engine.propose(f.request,f.context,f.authority);
 assert.equal(r.status,c.expected.status);assert.equal(canonical(f.request),before);assert.equal(canonical(f.state),state);
 assert.equal(r.physical_advice_authorized,false);assert.equal(r.automatic_actions_allowed,false);assert.equal(r.medical_clearance,false);
 assert.equal(r.provider_calls,0);assert.equal(r.storage_enabled,false);
 if(!special.has(c.expected.check))assert([r.reason,...r.rows.map(r=>r.reason)].includes(c.expected.check),c.expected.check);
 if(r.status!=="proposal")assert.equal(r.plan_option,null);
 if(c.id==="normal")for(const [i,m]of F.prereg.fixture_contract.exercises.entries()){
  assert.equal(r.rows[i].kind,m.expected.kind);assert.deepEqual(r.rows[i].next_week,{sets:m.expected.sets,reps:m.expected.reps,load:{value:m.expected.weight,unit:"kg"}});
 }
 if(c.id==="lb")assert.deepEqual(r.rows.map(r=>r.next_week.load),[{value:55,unit:"lb"},{value:32.5,unit:"lb"},{value:20,unit:"lb"}]);
 if(c.id==="fractional_step")assert.equal(r.rows[1].next_week.load.value,32.125);
 if(c.id==="rir_zero")assert(r.rows[0].observations.some(x=>x.rir===0));
 if(c.id==="optional_effort_missing")assert(r.rows.every(r=>r.observations.every(o=>o.rir===null&&o.rpe===null)));
 if(c.id==="effort_rule_not_met")assert.equal(r.rows[0].kind,"maintain");
 if(c.id==="known_language_miss"){assert.equal(r.rows.length,0);assert(r.nonclinical_options.length>0);}
 if(c.expected.check==="safety"){assert(!r.plan_option);assert.equal(r.rows.length,0);}
 assert(!r.messages.some(s=>/undefined|NaN/.test(s)));
});
test("exact changes preserve planned RIR and RPE independently",()=>{
 const f=F.setup();f.request.base.sources.plan.options[0].exercises[0].sets[0].rir=0;f.request.base.sources.plan.options[0].exercises[0].sets[0].rpe=9;
 const r=F.engine.propose(f.request,f.context,f.authority),change=r.plan_option.changes[0];
 assert.equal(change.after.rir,0);assert.equal(change.after.rpe,9);assert.equal(change.after.reps.min,9);
});
test("no automatic RIR/RPE inverse inference without explicit pair rule",()=>{
 const f=F.setup();f.history.sessions[0].sets[0].rir=0;f.history.sessions[0].sets[0].rpe=1;
 assert.equal(F.engine.propose(f.request,f.context,f.authority).rows[0].status,"available");
 f.policy.rules[0].forbidden_effort_pairs=[{rir:0,rpe:1}];
 assert.equal(F.engine.propose(f.request,f.context,f.authority).rows[0].reason,"conflicting_effort");
});
test("source order is preserved; latest required sessions determine calculation",()=>{
 const f=F.setup(),original=canonical(f.history);f.history.sessions.reverse();
 const r=F.engine.propose(f.request,f.context,f.authority);
 assert.equal(r.rows[0].observations[0].session_ref.id,"syn-session-2");
 f.history.sessions.reverse();assert.equal(canonical(f.history),original);
});
test("missing step never rounds or clamps to trainer maximum",()=>{
 const f=F.setup();f.policy.rules[0].reps_step=3;
 assert.equal(F.engine.propose(f.request,f.context,f.authority).rows[0].reason,"rep_step_unavailable");
});
test("all maintain gives concrete values without needless schema option",()=>{
 const f=F.setup();for(const s of f.history.sessions)for(const t of s.sets)t.reps=6;
 const r=F.engine.propose(f.request,f.context,f.authority);assert.equal(r.status,"proposal");assert(r.rows.every(x=>x.kind==="maintain"));assert.equal(r.plan_option,null);
});
test("request locale and binding cannot disagree with frozen source request",()=>{
 const f=F.setup();f.request.locale="en";assert.equal(F.engine.propose(f.request,f.context,f.authority).status,"invalid_input");
});
test("new plan version never rewrites older snapshots or source objects",()=>{
 const f=F.setup(),before=canonical(f.history);F.changedPlan(f);const r=F.engine.propose(f.request,f.context,f.authority);
 assert.equal(r.source_refs.plan.revision,4);assert.equal(r.rows[0].observations[0].plan_ref.revision,2);assert.equal(canonical(f.history),before);
});
test("proposal is immutable and every change is inside exact set boundaries",()=>{
 const r=F.run();assert(Object.isFrozen(r));assert(Object.isFrozen(r.plan_option));
 for(const c of r.plan_option.changes){const b=r.rows.find(r=>r.exercise_id===c.exercise_id).boundaries.find(b=>b.set_index===c.set_index);
  assert(c.after.reps.min>=b.reps.min&&c.after.reps.max<=b.reps.max);assert(c.after.load.value>=b.load.min&&c.after.load.value<=b.load.max);
 }
});
test("O5 adapter still exposes no extended or reconstructed safety record",()=>{
 for(const name of ["expired","expired_fresh","unnecessary_fresh"]){const f=F.setup(name);assert.equal(f.context.safety_records.length,0);assert.equal(F.engine.propose(f.request,f.context,f.authority).plan_option,null);}
});
