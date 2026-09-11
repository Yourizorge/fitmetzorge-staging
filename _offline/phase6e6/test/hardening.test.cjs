"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),f=require("./fixtures.cjs");
test("review-before: duplicate sessions expose neither ambiguous copy",()=>{
 const x=f.setup("rulebook_missing");x.request.base.history.sessions.push(f.clone(x.request.base.history.sessions[0]));
 const out=f.run(x);assert.equal(out.facts.observations.length,6);assert(out.facts.observations.every(t=>t.session_ref.id==="syn-session-2"));
});
test("review-before: duplicate snapshot IDs expose neither ambiguous copy",()=>{
 const x=f.setup("rulebook_missing");x.request.base.history.sessions[1].snapshot.id=x.request.base.history.sessions[0].snapshot.id;
 assert.equal(f.run(x).facts.observations.length,0);
});
test("review-before: duplicate global log IDs expose neither copy",()=>{
 const x=f.setup("rulebook_missing");x.request.base.history.sessions[1].sets[0].id=x.request.base.history.sessions[0].sets[0].id;
 const out=f.run(x);assert.equal(out.facts.observations.length,10);
});
test("review-before: malformed exercise cannot crash facts fallback",()=>{
 const x=f.setup("rulebook_missing");x.request.base.history.sessions[0].snapshot.exercises[0]=null;
 assert.doesNotThrow(()=>f.run(x));assert.equal(f.run(x).plan_option,null);
});
test("review-before: missing rules do not hide a current-health warning",()=>{
 const x=f.setup("current");x.request.rulebook=null;const o=f.run(x);
 const v=require("../../phase6e4/context.cjs").view(x.context,x.request.base.binding,x.authority,"nl");
 assert(v.feedback.length>0);for(const text of v.feedback)assert(o.messages.includes(text),text);assert.equal(o.plan_option,null);
});
test("review-before: reject requires issued context for audit timestamp",()=>{
 const x=f.start(),ctx=f.clone(x.f.context),r=f.review.act(x.state,f.event(x.f,x.state,"member","reject"),x.f.request,ctx,x.f.authority);
 assert.equal(r.status,"invalid_action");assert.strictEqual(r.state,x.state);
});
test("explicit type rule can serve two exercises without implicit classification",()=>{
 const x=f.setup(),a=x.book.rules[0],b=x.book.rules[2],common={id:"syn-compound",revision:1};
 a.selector={kind:"type",ref:common};a.parameters.available_weights=[20,22.5,25];x.book.rules.splice(2,1);
 for(const i of [0,2])x.book.bindings[i].type_ref=f.clone(common);
 const o=f.run(x);assert.equal(o.status,"proposal");assert.equal(o.rule_provenance[0].rule_ref.id,o.rule_provenance[2].rule_ref.id);
});
test("null vs RIR0, invalid RPE0 and no inverse conversion",()=>{
 const x=f.setup("rir_zero");assert.equal(f.run(x).rows[0].observations.find(t=>t.rir===0).rpe,8);
 x.request.base.history.sessions[0].sets[0].rpe=0;assert.equal(f.run(x).plan_option,null);
});
test("weight step decimal precision is explicit, never rounded",()=>{
 const x=f.setup();x.book.rules[0].parameters.weight_step=0.0000001;assert.equal(f.run(x).plan_option,null);
});
test("two competing rule authorities are refused",()=>{
 const x=f.setup();x.request.base.policy.rules=[f.clone(f.old.setup().policy.rules[0])];assert.equal(f.run(x).reason,"dual_rule_authority");
});
test("historical snapshots are unchanged by new type mapping and simulation",()=>{
 const x=f.approved(f.setup("type_rule")),before=f.clone(x.f.request.base.history);
 f.act(x.f,x.state,"trainer","apply");assert.deepEqual(x.f.request.base.history,before);
});
test("a cloned context never permits facts or a proposal",()=>{
 const x=f.setup();x.context=f.clone(x.context);const o=f.run(x);assert.equal(o.status,"invalid_input");assert.equal(o.facts.observations.length,0);
});
