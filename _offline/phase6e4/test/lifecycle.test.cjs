"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),{setup,clone,engine,flow,helpers,DAY}=require("./fixtures.cjs");
function requestAt(f,ctx){const r=clone(f.request);r.binding=clone(ctx.binding);r.sources.readset.read_at_ms=ctx.evaluated_at_ms;return r;}
const apply=(state,type,body,at)=>{const r=flow.apply(state,{...helpers.event(state,type,body),at_ms:at});assert.notEqual(r.state,state,r.status);return r;};
function send(state,text,at){return apply(state,"message",{expected_revision:state.revision,message_id:"syn-message-"+(state.revision+1),text,locale:"nl",availability:"available"},at).state;}
for(const scenario of ["current","self_reported","technical","unclear"])test("O5 exact first-registration expiry "+scenario,()=>{
  const f=setup({scenario}),first=f.context.safety_records[0].first_registered_at_ms;
  const before=engine.prepare(f.state,first+30*DAY-1,{},f.context);
  assert.equal(before.safety_records.length,1);
  const at=engine.prepare(f.state,first+30*DAY,{},before);assert.deepEqual(at.safety_records,[]);
  const after=engine.prepare(f.state,first+30*DAY+1,{},at);assert.deepEqual(after.safety_records,[]);
  const r=engine.suggest(requestAt(f,after),after,f.authority);
  assert.equal(r.candidate,null);assert.deepEqual(r.warnings,[]);assert.equal(r.physical_advice_authorized,false);
  assert(!r.messages.join(" ").includes("loodzwaar"));
});
test("earlier expiry stays omitted across refresh with no options, fresh context or retry",()=>{
  const f=setup({scenario:"technical"}),id=f.state.messages[0].id;
  const omitted=engine.prepare(f.state,f.clock+1,{unnecessary_message_ids:[id]},f.context);
  assert.deepEqual(omitted.safety_records,[]);
  const again=engine.prepare(f.state,f.clock+2,{},omitted);assert.deepEqual(again.safety_records,[]);
  const i=f.state.issues[0],start=apply(f.state,"begin",{expected_revision:f.state.revision,message_id:i.message_id,source_revision:i.source_revision,mode:"retry"},f.clock+3);
  const retry=apply(start.state,"retry",{binding:start.binding,availability:"available"},f.clock+4);
  const ctx=engine.prepare(retry.state,f.clock+4,{},again);assert.deepEqual(ctx.safety_records,[]);
  assert.equal(engine.suggest(requestAt(f,ctx),ctx,f.authority).candidate,null);
});
for(const mode of ["technical","unclear"])test("attempt/status transition cannot extend O5 "+mode,()=>{
  const f=setup({scenario:mode}),first=f.context.safety_records[0].first_registered_at_ms,i=f.state.issues[0],kind=mode==="technical"?"retry":"clarify";
  const begin=apply(f.state,"begin",{expected_revision:f.state.revision,message_id:i.message_id,source_revision:i.source_revision,mode:kind},first+29*DAY);
  const pending=engine.prepare(begin.state,first+29*DAY,{},f.context);
  assert.equal(pending.safety_records[0].first_registered_at_ms,first);assert.equal(pending.safety_records[0].status,"awaiting");
  const end=apply(begin.state,kind,kind==="retry"?{binding:begin.binding,availability:"available"}:
    {binding:begin.binding,text:"Ik bedoelde mijn borsttraining met gewichten",locale:"nl"},first+29*DAY+1);
  const settled=engine.prepare(end.state,first+29*DAY+1,{},pending);
  assert.equal(settled.safety_records[0].status,"settled");assert.equal(settled.safety_records[0].first_registered_at_ms,first);
  const expired=engine.prepare(end.state,first+30*DAY,{},settled);assert.deepEqual(expired.safety_records,[]);
});
test("missing source stays missing; no original warning/content is reconstructed",()=>{
  const f=setup({scenario:"current"}),id=f.state.messages[0].id;
  const missing=engine.prepare(f.state,f.clock+1,{missing_message_ids:[id]},f.context);
  const again=engine.prepare(f.state,f.clock+2,{},missing);
  assert.equal(again.safety_records[0].status,"context_missing");
  const r=engine.suggest(requestAt(f,again),again,f.authority);assert.deepEqual(r.warnings,[]);assert.equal(r.candidate,null);
  assert(!r.messages.join(" ").includes("borstpijn"));
});
test("new report after expiry gets only its own first-registration date",()=>{
  const f=setup({scenario:"current"}),at=f.clock+30*DAY;
  const expired=engine.prepare(f.state,at,{},f.context);
  const state=send(f.state,"Nu heb ik moeite met ademhalen",at+1);
  const ctx=engine.prepare(state,at+1,{},expired);
  assert.equal(ctx.safety_records.length,1);assert.equal(ctx.safety_records[0].first_registered_at_ms,at+1);
  assert.notEqual(ctx.safety_records[0].message_ref.message_id,f.state.messages[0].id);
  const r=engine.suggest(requestAt(f,ctx),ctx,f.authority);assert.equal(r.reason,"current_health_report");assert(r.warnings.length);
});
test("ordinary adapter view never erases the original issue or extends its O5 record",()=>{
  const f=setup({text:"Ik bekijk mijn trainingsregistratie"}),before=JSON.stringify(f.state);
  assert.equal(f.state.messages[0].assessment.category,"communication");assert.equal(f.context.safety_records.length,1);
  const result=engine.suggest(f.request,f.context,f.authority);assert.equal(result.status,"candidate_only");assert.equal(result.language_adapter_applied,true);
  assert.equal(JSON.stringify(f.state),before);
  const at=engine.prepare(f.state,f.clock+30*DAY,{},f.context);assert.deepEqual(at.safety_records,[]);
  assert.equal(engine.suggest(requestAt(f,at),at,f.authority).candidate,null);
});
test("technical retry of review phrase still retains exact original O5 anchor",()=>{
  const f=setup({scenario:"technical_retry",text:"Ik bekijk mijn trainingsregistratie"});
  const r=engine.suggest(f.request,f.context,f.authority);
  assert.equal(r.status,"candidate_only");assert.equal(f.context.safety_records.length,1);
  assert.equal(f.context.safety_records[0].first_registered_at_ms,f.state.messages[0].at_ms);
});
test("viewing and reevaluating cannot change retained source records",()=>{
  const f=setup({scenario:"current"}),snapshot=JSON.stringify(f.context.safety_records);
  for(let i=0;i<20;i++)assert.equal(engine.suggest(f.request,f.context,f.authority).candidate,null);
  assert.equal(JSON.stringify(f.context.safety_records),snapshot);
  assert.deepEqual(Object.keys(f.context.safety_records[0]).sort(),["first_registered_at_ms","message_ref","status"]);
});
test("old frozen facts and nonphysical reflection remain independently usable after self report",()=>{
  const old=require("../../phase6e3/test/fixtures.cjs"),f=old.setup({scenario:"self_reported"});
  const r=old.engine.reflect(f.request,f.context,f.authority);
  assert.equal(r.status,"recommendation");assert(r.observations.length);assert.equal(r.medical_clearance,false);
  assert.equal(engine.suggest(...(()=>{const n=setup({scenario:"self_reported"});return[n.request,n.context,n.authority];})()).candidate,null);
});
test("later current plan/goal changes do not mutate historical 6E3 reflection or snapshot",()=>{
  const old=require("../../phase6e3/test/fixtures.cjs"),f=old.setup(),original=JSON.stringify(old.engine.reflect(f.request,f.context,f.authority)),historical=JSON.stringify(f.request.sources);
  const current=setup();current.request.sources.goal.code="muscle_gain";
  const result=engine.suggest(current.request,current.context,current.authority);assert.equal(result.status,"candidate_only");
  assert.equal(result.candidate.goal_code,"muscle_gain");
  assert.equal(JSON.stringify(old.engine.reflect(f.request,f.context,f.authority)),original);assert.equal(JSON.stringify(f.request.sources),historical);
});
test("clock rollback, unrelated lineage and old attempt binding are rejected",()=>{
  const f=setup({scenario:"technical"});
  assert.throws(()=>engine.prepare(f.state,f.clock-1,{},f.context),/invalid_projection/);
  const other=flow.create("syn-other");assert.throws(()=>engine.prepare(other,f.clock+1,{},f.context),/context_lineage_mismatch/);
  const i=f.state.issues[0],start=helpers.begin(f.state,i);
  assert.equal(flow.apply(start.state,{...helpers.event(start.state,"retry",{binding:{...start.binding,attempt:0},availability:"available"})}).status,"stale_or_wrong_attempt");
});
