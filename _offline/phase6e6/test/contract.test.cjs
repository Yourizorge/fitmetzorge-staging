"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),f=require("./fixtures.cjs"),cases=require("../preregistered-cases.json");
for(const c of cases.progression)test("preregistered progression: "+c.id,()=>{
 const x=f.setup(c.id),before=f.clone(x.request),out=f.run(x);
 const expected=c.id==="mixed_unit"?"unavailable":c.expected_status;
 assert.equal(out.status,expected,JSON.stringify({reason:out.reason,rows:out.rows.map(r=>r.reason)}));
 assert.deepEqual(x.request,before);assert.equal(out.automatic_actions_allowed,false);assert.equal(out.physical_advice_authorized,false);
 if(!["normal","type_rule","lb","rir_zero","optional_effort_missing","weight_step_exact","effort_hold","clarified","all_maintain"].includes(c.id))assert.equal(out.plan_option,null);
 if(c.id==="normal"){assert.deepEqual(out.rows.map(r=>r.kind),["increase_reps","increase_weight","maintain"]);assert.equal(out.rows[0].next_week.reps,9);assert.equal(out.rows[1].next_week.load.value,32.5);assert.equal(out.rows[2].next_week.reps,8);assert(out.rows[2].observations.every(t=>t.reps===7));}
 if(c.id==="all_maintain")assert.equal(out.plan_option,null);
 if(c.id==="rir_zero")assert(out.rows[0].observations.some(t=>t.rir===0));
 if(c.id==="optional_effort_missing")assert(out.rows.every(r=>r.observations.every(t=>t.rir===null&&t.rpe===null)));
 if(c.id==="weight_step_exact")assert.equal(out.rows[1].next_week.load.value,30.125);
 if(c.id==="type_rule")assert.equal(out.rule_provenance[0].selector.kind,"type");
 if(c.id==="lb")assert(out.rows.every(r=>r.current_plan.load.unit==="lb"&&r.next_week.load.unit==="lb"));
 if(c.id==="effort_hold")assert.equal(out.rows[0].kind,"maintain");
});
const factsCases={
 missing_trainer_reliable_facts(){const x=f.run(f.setup("no_trainer"));assert.equal(x.plan_option,null);assert.equal(x.facts.observations.length,12);},
 missing_rule_reliable_facts(){assert.equal(f.run(f.setup("rulebook_missing")).facts.observations.length,12);},
 wrong_owner_never_shown(){const x=f.setup("rulebook_missing");x.request.base.history.subject_id="syn-other";assert.equal(f.run(x).facts.observations.length,0);},
 bad_set_binding_omitted(){const x=f.setup("rulebook_missing");x.request.base.history.sessions[0].sets[0].subject_id="syn-other";const out=f.run(x);assert.equal(out.facts.observations.length,11);assert(out.facts.omitted.includes("unreliable_set"));},
 missing_values_not_invented(){const o=f.run(f.setup("partial_facts"));assert.equal(o.facts.observations[0].recorded.reps,null);assert.equal(o.facts.observations[0].complete,false);},
 zero_retained(){const x=f.setup("rulebook_missing");x.request.base.history.sessions[0].sets[0].rir=0;assert.equal(f.run(x).facts.observations[0].recorded.rir,0);},
 no_access_no_facts(){const x=f.setup("no_analysis_consent");assert.equal(f.run(x).facts.observations.length,0);}
};
for(const id of cases.facts)test("preregistered facts: "+id,factsCases[id]);
