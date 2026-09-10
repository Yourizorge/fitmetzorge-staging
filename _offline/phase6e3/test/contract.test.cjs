"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {setup,run,clone,legacy,engine,prereg}=require("./fixtures.cjs");
for(const c of prereg.cases) test("preregistered: "+c.id,()=>{
  const f=setup(c),before=JSON.stringify(f.request),out=engine.reflect(f.request,f.context,f.authority);
  assert.equal(out.status,c.expected_status,JSON.stringify(out));assert.equal(out.reason,c.expected_reason);
  assert.equal(JSON.stringify(f.request),before);assert.equal(Object.isFrozen(f.request.sources),false);
  assert.equal(out.medical_clearance,false);assert.equal(out.training_suitability_assessed,false);
  assert.equal(out.automatic_actions_allowed,false);assert.deepEqual(out.actions,[]);assert.equal(out.provider_calls,0);
  if(c.exact_excerpt)assert.deepEqual([out.goal.text,out.observations[0].text,out.recommendations[0].text],c.exact_excerpt);
  if(out.status==="invalid_input")assert.deepEqual(out.observations,[]);
});
test("comparison is computed from unseen exact sets, not fixture lookup",()=>{
  for(const [min,max,actual,weight] of [[3,5,2,12.75],[3,5,4,0],[3,5,8,89.25],[0,0,0,0]]) {
    const f=setup(),p=f.request.sources.snapshot.exercises[0].sets[0],r=f.request.sources.recording.sets[0];
    p.reps={min,max};r.reps=actual;p.load.value=weight;r.load.value=weight+.25;
    const o=engine.reflect(f.request,f.context,f.authority);
    assert.equal(o.status,"recommendation");
    assert.equal(o.observations[0].comparison.reps,actual<min?"below":actual>max?"above":"within");
    assert.equal(o.observations[0].comparison.load,"different");
    assert.match(o.observations[0].text,new RegExp(String(weight).replace(".","[,]")));
    assert.equal(o.recommendations[0].physical_prescription,false);
  }
});
test("exact identity wins over reordered catalog/records, preserving every target",()=>{
  const f=setup(),s=f.request.sources,p=clone(s.snapshot.exercises[0]),r=clone(s.recording.sets[0]);
  p.exercise_id="syn-row";p.sets[0].reps={min:5,max:5};s.snapshot.exercises.push(p);
  r.id="syn-second-log";r.exercise_id="syn-row";r.reps=5;s.recording.sets.unshift(r);
  s.catalog.unshift({id:"syn-row",revision:1,labels:{nl:"Roeien",en:"Row",de:"Rudern"}});
  const o=engine.reflect(f.request,f.context,f.authority);
  assert.equal(o.status,"recommendation");
  assert.deepEqual(o.observations.map(x=>[x.exercise_id,x.recorded.reps]),[["syn-squat",9],["syn-row",5]]);
  assert.deepEqual(o.recommendations[0].basis.map(x=>x.source_refs.record_id),["syn-log","syn-second-log"]);
});
for(const kind of ["log-id","set-tuple","exercise-id","catalog-version"])test("duplicate identity rejected: "+kind,()=>{
  const f=setup(),s=f.request.sources;
  if(kind==="log-id"||kind==="set-tuple"){const r=clone(s.recording.sets[0]);if(kind==="set-tuple")r.id="syn-other-log";s.recording.sets.push(r);}
  if(kind==="exercise-id")s.snapshot.exercises.push(clone(s.snapshot.exercises[0]));
  if(kind==="catalog-version")s.catalog.push(clone(s.catalog[0]));
  assert.equal(engine.reflect(f.request,f.context,f.authority).status,"invalid_input");
});
for(const pair of [[null,null],[0,null],[null,9.5],[0,9.5]])test("independent RIR/RPE, including null and zero: "+pair,()=>{
  const f=setup(),r=f.request.sources.recording.sets[0];[r.rir,r.rpe]=pair;
  const o=engine.reflect(f.request,f.context,f.authority);
  assert.deepEqual([o.observations[0].recorded.rir,o.observations[0].recorded.rpe],pair);
  assert.equal(o.observations[0].effort_is_self_report,true);
  assert.equal(o.observations[0].planned.rir,null);assert.equal(o.observations[0].planned.rpe,null);
});
test("missing set remains missing even with claimed complete coverage",()=>{
  const f=setup(),p=clone(f.request.sources.snapshot.exercises[0].sets[0]);p.index=2;
  f.request.sources.snapshot.exercises[0].sets.push(p);
  const o=engine.reflect(f.request,f.context,f.authority);
  assert.equal(o.status,"facts_only");assert.equal(o.observations.length,1);
  assert(o.unavailable.some(x=>x.code==="missing_set"&&x.index===2));assert(o.unavailable.some(x=>x.code==="partial"));
});
test("an old but exact historical workout is not stale merely due to age",()=>{
  const f=setup(),context=engine.prepare(f.state,f.clock+400*legacy.DAY,{},f.context);
  f.request.binding=clone(context.binding);
  assert.equal(engine.reflect(f.request,context,f.authority).status,"recommendation");
});
test("later schema revision is not substituted into the historical snapshot",()=>{
  const f=setup(),before=engine.reflect(f.request,f.context,f.authority);
  const later=clone(f.request);later.sources.snapshot.revision++;later.sources.snapshot.plan_ref.revision++;
  later.sources.snapshot.exercises[0].sets[0].load.value=80;
  const o=engine.reflect(later,f.context,f.authority);
  assert.equal(o.status,"facts_only");assert.equal(o.observations.length,0);assert.equal(o.goal,null);
  assert.equal(before.observations[0].planned.load.value,55);
  assert.equal(engine.reflect(f.request,f.context,f.authority).observations[0].planned.load.value,55);
});
test("a goal version captured after the claimed historical link cannot support reflection",()=>{
  const f=setup(),s=f.request.sources;
  s.snapshot.captured_at_ms=s.session.started_at_ms-2000;
  s.snapshot.goal_link.at_ms=s.snapshot.captured_at_ms;
  const o=engine.reflect(f.request,f.context,f.authority);
  assert.equal(o.status,"facts_only");assert.equal(o.reason,"historical_goal_unavailable");
  assert.equal(o.goal,null);
});
test("later changed goal is not treated as the goal at workout start",()=>{
  const f=setup(),later=clone(f.request);later.sources.goal.revision=2;later.sources.goal.code="fat_loss";
  const o=engine.reflect(later,f.context,f.authority);
  assert.equal(o.status,"facts_only");assert.equal(o.goal,null);assert.equal(o.observations.length,1);
  assert(!o.messages.some(s=>s.includes("vet verliezen")));
});
for(const name of ["current_plan","trainer_limits","medical_clearance","approved","nutrition_target"])test("no invented extra source: "+name,()=>{
  const f=setup();f.request.sources[name]={value:100};
  assert.equal(engine.reflect(f.request,f.context,f.authority).status,"invalid_input");
});
for(const key of ["subject_id","message_id","source_revision","revision"])test("context binding rejects altered "+key,()=>{
  const f=setup();f.request.binding[key]=typeof f.request.binding[key]==="number"?999:"syn-other";
  assert.equal(engine.reflect(f.request,f.context,f.authority).status,"invalid_input");
});
test("a superseded context cannot hide a new complaint",()=>{
  const f=setup(),next=legacy.flow.apply(f.state,{...legacy.legacy.event(f.state,"message",{
    expected_revision:f.state.revision,message_id:"syn-new-health",text:"Ik heb borstpijn",locale:"nl",availability:"available"}),at_ms:f.clock+1}).state;
  const ctx=engine.prepare(next,f.clock+1,{},f.context);
  assert.equal(engine.reflect(f.request,f.context,f.authority).reason,"stale_context");
  f.request.binding=clone(ctx.binding);const o=engine.reflect(f.request,ctx,f.authority);
  assert.equal(o.reason,"current_health_report");assert.equal(o.warnings[0].binding.message_id,"syn-new-health");
  assert.equal(o.messages[0],o.warnings[0].text);
});
test("forged context cannot grant a reflection",()=>{
  const f=setup();const ctx=clone(f.context);
  assert.equal(engine.reflect(f.request,ctx,f.authority).reason,"invalid_context");
});
test("O5 exact cap, repeat handling, missing source and new ordinary context",()=>{
  const f=setup({scenario:"unclassified"}),origin=f.context.safety_records[0].first_registered_at_ms;
  // The frozen record contract names its first date first_registered_at_ms.
  assert.equal(typeof origin,"number");
  let ctx=engine.prepare(f.state,origin+30*legacy.DAY-1,{},f.context);f.request.binding=clone(ctx.binding);
  assert.equal(engine.reflect(f.request,ctx,f.authority).reason,"current_health_report");
  ctx=engine.prepare(f.state,origin+30*legacy.DAY,{},ctx);f.request.binding=clone(ctx.binding);
  assert.equal(ctx.safety_records.length,0);assert.equal(engine.reflect(f.request,ctx,f.authority).status,"clarification");
  ctx=engine.prepare(f.state,origin+30*legacy.DAY+1,{},ctx);assert.equal(ctx.safety_records.length,0);
  const state=legacy.flow.apply(f.state,{...legacy.legacy.event(f.state,"message",{
    expected_revision:f.state.revision,message_id:"syn-fresh-context",text:"Ik train mijn benen",locale:"nl",availability:"available"}),at_ms:origin+30*legacy.DAY+2}).state;
  ctx=engine.prepare(state,origin+30*legacy.DAY+2,{},ctx);f.request.binding=clone(ctx.binding);
  const o=engine.reflect(f.request,ctx,f.authority);assert.equal(o.status,"recommendation");
  assert.equal(o.medical_clearance,false);assert.equal(o.warnings.length,0);
});
test("limitation observation, not recognition success: trainingsregistratie remains unclear",()=>{
  const f=setup(),state=legacy.flow.apply(f.state,{...legacy.legacy.event(f.state,"message",{
    expected_revision:f.state.revision,message_id:"syn-unrecognized-compound",text:"Ik bekijk mijn trainingsregistratie",locale:"nl",availability:"available"}),at_ms:f.clock+1}).state;
  const ctx=engine.prepare(state,f.clock+1,{},f.context);f.request.binding=clone(ctx.binding);
  const o=engine.reflect(f.request,ctx,f.authority);
  assert.equal(o.status,"clarification");assert.deepEqual(o.warnings,[]);
  assert(o.nonclinical_options[0].choices.includes("continue_chat"));
});
test("nonphysical self-report never closes expert criteria or other reports",()=>{
  const f=setup({scenario:"serious_recovered"}),o=engine.reflect(f.request,f.context,f.authority);
  assert.equal(o.status,"recommendation");assert(o.expert_criteria.includes("serious_recovery"));
  assert(o.messages.some(s=>s.includes("geen medische vrijgave")));
  assert.equal(run({scenario:"new_after_recovery"}).status,"facts_only");
});
for(const flag of ["authenticated","adult","ai_entitlement","ai_analysis_consent"])test("analysis authority remains separate: "+flag,()=>{
  const f=setup();f.authority[flag]=false;const o=engine.reflect(f.request,f.context,f.authority);
  assert.equal(o.status,"access_unavailable");assert.deepEqual(o.observations,[]);assert.equal(o.access.entitlements_modified,false);
});
test("without chat consent no health context leaks into otherwise available facts",()=>{
  const f=setup({scenario:"current"});f.authority.private_chat_consent=false;
  const o=engine.reflect(f.request,f.context,f.authority);
  assert.equal(o.access.history,true);assert.equal(o.access.new_analysis,true);assert.equal(o.access.chat,false);
  assert.equal(o.observations.length,1);assert.equal(o.status,"clarification");assert.deepEqual(o.warnings,[]);
  assert(!JSON.stringify(o).includes("borstpijn"));
});
test("all supported goals require the same explicit historical link, never causal claims",()=>{
  for(const code of Object.keys(engine.contract.goals)) {
    const f=setup();f.request.sources.goal.code=code;
    const o=engine.reflect(f.request,f.context,f.authority);
    assert.equal(o.goal.code,code);assert.equal(o.recommendations[0].physical_prescription,false);
    assert.equal(o.recommendations[0].trainer_limits_source,null);
  }
});
