"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),{setup,run,clone,engine,prereg}=require("./fixtures.cjs");
for(const c of prereg.cases)test("preregistered "+c.id,()=>{
  const output=run(c);
  assert.equal(output.status,c.expected.status,JSON.stringify({reason:output.reason,issues:output.source_issues}));
  if(c.expected.reason)assert.equal(output.reason,c.expected.reason);
  assert.equal(output.automatic_actions_allowed,false);assert.equal(output.physical_advice_authorized,false);
  assert(output.messages.every(x=>typeof x==="string"&&x.length>0));
  assert.equal(Boolean(output.candidate),output.status==="candidate_only");
});
test("candidate retains precise source values, null and independent scores",()=>{
  const f=setup();f.request.sources.plan.options[0].exercises[0].sets[0].load.value=55.12345;
  const before=JSON.stringify(f.request),output=engine.suggest(f.request,f.context,f.authority);
  assert.equal(output.status,"candidate_only");assert.equal(output.candidate.rows[0].target.load.value,55.12345);
  assert.equal(output.candidate.rows[0].target.rir,0);assert.equal(output.candidate.rows[0].target.rpe,8.5);
  assert(output.messages.some(m=>m.includes("55,12345 kg")));assert.equal(JSON.stringify(f.request),before);
  assert(Object.isFrozen(output.candidate.rows[0].target));assert(!Object.isFrozen(f.request.sources));
});
test("wrong request person, stale context and forged context never expose candidate",()=>{
  const f=setup();f.request.binding.subject_id="syn-other";
  assert.equal(engine.suggest(f.request,f.context,f.authority).status,"invalid_input");
  assert.equal(engine.suggest({...f.request,binding:clone(f.context.binding)},clone(f.context),f.authority).status,"invalid_input");
  const current=engine.prepare(f.state,f.clock+1,{},f.context);
  assert.equal(engine.suggest({...f.request,binding:clone(f.context.binding)},f.context,f.authority).status,"invalid_input");
  assert.throws(()=>engine.prepare(f.state,f.clock+2,{},f.context),/current_issued_context/);
  assert(Object.isFrozen(current));
});
test("request for old readset cannot take silently newer versions",()=>{
  const f=setup();f.request.expected_readset.revision=0;
  assert.equal(engine.suggest(f.request,f.context,f.authority).reason,"stale_readset");
});
test("other authority cannot read member source content or private warning",()=>{
  const f=setup({scenario:"current"});f.authority.subject_id="syn-other";
  const r=engine.suggest(f.request,f.context,f.authority);
  assert.equal(r.status,"access_unavailable");assert.deepEqual(r.warnings,[]);assert.equal(r.candidate,null);
  assert(!r.messages.join(" ").includes("Squat"));
});
test("new health report takes priority over earlier self report",()=>{
  for(const scenario of ["recurring","new_after_recovery"]){
    const r=run({scenario});assert.equal(r.context_mode,"current_health");assert.equal(r.reason,"current_health_report");
    assert(r.warnings.length>0);assert.equal(r.candidate,null);
  }
});
test("historical report is not reclassified as current health or a medical clearance",()=>{
  const r=run({scenario:"historical"});assert.equal(r.candidate,null);assert.equal(r.warnings.length,0);
  assert.equal(r.reason,"noncurrent_not_current_context");
});
test("ordinary correction cannot suppress another available health report",()=>{
  const f=setup({scenario:"current"});
  const event={...require("../../phase6e1/test/helpers.cjs").event(f.state,"message",{expected_revision:f.state.revision,
    message_id:"syn-review",text:"Ik bekijk mijn trainingsregistratie",locale:"nl",availability:"available"}),at_ms:f.clock+1};
  const state=require("../../phase6e1/flow.cjs").apply(f.state,event).state;
  const ctx=engine.prepare(state,f.clock+1,{},f.context);
  f.request.binding=clone(ctx.binding);f.request.sources.readset.read_at_ms=f.clock+1;
  const r=engine.suggest(f.request,ctx,f.authority);assert.equal(r.reason,"current_health_report");assert(r.warnings.length);
});
