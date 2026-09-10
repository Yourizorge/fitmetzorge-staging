"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),answers=require("../review-answers.json");
const {setup,run,clone,engine,flow,helpers}=require("./fixtures.cjs");
for(const answer of answers)test("exact complete owner answer "+answer.locale+" "+answer.situation,()=>{
  const r=run({locale:answer.locale,...(answer.status==="unavailable"?{changes:[{path:["authority"],value:null}]}:{})});
  assert.equal(r.status,answer.status);assert.deepEqual(r.messages,answer.messages);
});
test("unclear review residue can be reformulated as a new message without mandatory loop",()=>{
  const f=setup({locale:"en",text:"I am reviewing my workout log and flurbel"});
  const initial=engine.suggest(f.request,f.context,f.authority);
  assert.equal(initial.status,"clarification");assert(initial.nonclinical_options.some(o=>o.kind==="new_message"&&o.choices.includes("continue_chat")));
  const event={...helpers.event(f.state,"message",{expected_revision:f.state.revision,message_id:"syn-clear-review",text:"I am reviewing my workout log",locale:"en",availability:"available"}),at_ms:f.clock+1};
  const state=flow.apply(f.state,event).state,ctx=engine.prepare(state,f.clock+1,{},f.context),request=clone(f.request);
  request.binding=clone(ctx.binding);request.sources.readset.read_at_ms=f.clock+1;
  assert.equal(engine.suggest(request,ctx,f.authority).status,"candidate_only");
  assert.equal(state.messages.length,2);assert.equal(f.state.messages.length,1);
});
test("clarification of one issue cannot erase another health report",()=>{
  const r=run({scenario:"clarification_other_health"});assert.equal(r.reason,"current_health_report");assert(r.warnings.length);
});
