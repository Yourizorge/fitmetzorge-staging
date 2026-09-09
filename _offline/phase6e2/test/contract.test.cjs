"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { setup, sample, clone, types, DAY, CLOCK, legacy, flow, engine } = require("./fixtures.cjs");
const prereg = require("../preregistered-cases.json");
for (const c of prereg.cases) test("preregistered: " + c.id, () => {
  const f = setup(c), before = JSON.stringify({ state: f.state, request: f.request, authority: f.authority, context: f.context });
  const r = engine.recommend(f.request, f.context, f.authority);
  assert.equal(r.status, c.expected_status);
  if (c.expected_reason) assert.equal(r.reason, c.expected_reason);
  if (c.exact_recommendation) assert.equal(r.recommendations[0].text, c.exact_recommendation);
  assert.equal(r.recommendations.length, r.status === "recommendation" ? 1 : 0);
  assert.equal(r.medical_clearance, false); assert.equal(r.training_suitability_assessed, false);
  assert.deepEqual(r.actions, []); assert.equal(r.automatic_actions_allowed, false);
  assert.equal(r.provider_calls, 0); assert.equal(r.trainer_sharing, false); assert.equal(r.storage_enabled, false);
  assert.equal(r.clarification_required, false); assert.equal(r.human_approval_service, false);
  assert.equal(r.access.chat, true); assert.equal(r.access.history, true); assert.equal(r.access.new_analysis, true);
  assert.equal(JSON.stringify({ state: f.state, request: f.request, authority: f.authority, context: f.context }), before);
  assert(Object.isFrozen(r));
  assert(!r.messages.some(t => /undefined|NaN|\{[a-z_]+\}/.test(t)));
  if (r.recommendations.length) {
    assert.deepEqual(r.recommendations[0].bound_to, f.context.binding);
    assert.equal(r.recommendations[0].goal_source, null); assert.equal(r.recommendations[0].trainer_limits_source, null);
  }
});
test("existing facts are preserved, and recommendations add an optional concrete step", () => {
  const f = setup({kind:"post_workout"}), old = require("../../phase6e1/analysis.cjs").analyze(f.request.analysis,f.state,f.authority);
  const r=engine.recommend(f.request,f.context,f.authority);
  assert.deepEqual(r.observations,old.observations); assert.equal(old.recommendations.length,0);
  assert.equal(r.recommendations.length,1); assert.match(r.recommendations[0].text,/Kies zelf een set/);
});
for (const [field,changes] of [
  ["authentication",{authenticated:false}],["adult",{adult:false}],["entitlement",{ai_entitlement:false}],
  ["analysis-consent",{ai_analysis_consent:false}],["wrong-owner",{subject_id:"syn-other"}],
  ["forged-authority",{approved:true}]
]) test("authority denies without leaking context or facts: "+field,()=>{
 const f=setup({scenario:"current"});Object.assign(f.authority,changes);
 const r=engine.recommend(f.request,f.context,f.authority);
 assert.equal(r.status,"access_unavailable");assert.deepEqual(r.observations,[]);assert.deepEqual(r.warnings,[]);
});
test("chat/history/facts permissions are independent; no private context leaks without chat consent",()=>{
 const f=setup({scenario:"current",kind:"post_workout"}); f.authority.private_chat_consent=false;
 const r=engine.recommend(f.request,f.context,f.authority);
 assert.equal(r.access.chat,false);assert.equal(r.access.history,true);assert.equal(r.access.new_analysis,true);
 assert(r.observations.length);assert.deepEqual(r.warnings,[]);assert.deepEqual(r.expert_criteria,[]);
 assert.equal(r.status,"clarification");assert(!JSON.stringify(r).includes("borstpijn"));
});
for(const field of ["goals","trainer_limits","medical_clearance","approved","context","expected","actions"])
 test("no extra or invented authority field: "+field,()=>{
 const f=setup();f.request[field]=true;
 assert.equal(engine.recommend(f.request,f.context,f.authority).status,"invalid_input");
});
for(const [field,value] of [["subject_id","syn-other"],["revision",999],["message_id","syn-other"],["source_revision",999]])
 test("exact context binding: "+field,()=>{
 const f=setup();f.request.binding[field]=value;
 const r=engine.recommend(f.request,f.context,f.authority);assert.equal(r.status,"invalid_input");assert.deepEqual(r.observations,[]);
});
test("forged snapshots and raw states cannot enter the engine",()=>{
 const f=setup();
 assert.throws(()=>engine.recommend(f.request,clone(f.context),f.authority),/issued_context/);
 assert.throws(()=>engine.prepare(clone(f.state),f.clock),/issued_synthetic_state/);
});
test("superseded context cannot issue stale recommendations after a new complaint",()=>{
 const f=setup({kind:"weekly"});
 const next=flow.apply(f.state,{...legacy.event(f.state,"message",{expected_revision:f.state.revision,message_id:"syn-next",text:"Ik heb borstpijn",locale:"nl",availability:"available"}),at_ms:f.clock+1}).state;
 const c=engine.prepare(next,f.clock+1,{},f.context);
 assert.equal(engine.recommend(f.request,f.context,f.authority).reason,"stale_context");
 assert.throws(()=>engine.prepare(next,f.clock+1,{},f.context),/current_issued_context/);
 assert.equal(engine.recommend({...f.request,binding:clone(c.binding)},c,f.authority).status,"facts_only");
});
test("same revision on a different branch is not trusted lineage",()=>{
 const f=setup(), branch=legacy.message(flow.create(legacy.subject),"Ik heb borstpijn").state;
 assert.throws(()=>engine.prepare(branch,f.clock,{},f.context),/lineage/);
});
test("O5 exact boundary, repeat processing and early removal preserve the original cap",()=>{
 const f=setup({scenario:"current"}), first=f.context.safety_records[0].first_registered_at_ms;
 let c=engine.prepare(f.state,first+30*DAY-1,{},f.context);assert.equal(c.safety_records.length,1);
 c=engine.prepare(f.state,first+30*DAY,{},c);assert.deepEqual(c.safety_records,[]);
 c=engine.prepare(f.state,first+300*DAY,{},c);assert.deepEqual(c.safety_records,[]);
 const early=setup({scenario:"unnecessary"});assert.deepEqual(early.context.safety_records,[]);
 const again=engine.prepare(early.state,early.clock+1,{},early.context);assert.deepEqual(again.safety_records,[]);
});
test("new report after O5 expiry gets only its own anchor and warning; no expiry clearance",()=>{
 const f=setup({scenario:"expired",kind:"weekly"});
 const s=flow.apply(f.state,{...legacy.event(f.state,"message",{expected_revision:f.state.revision,message_id:"syn-new-health",text:"Ik heb borstpijn",locale:"nl",availability:"available"}),at_ms:f.clock+1}).state;
 const c=engine.prepare(s,f.clock+1,{},f.context),r=engine.recommend({...f.request,binding:clone(c.binding)},c,f.authority);
 assert.equal(c.safety_records.length,1);assert.equal(c.safety_records[0].first_registered_at_ms,f.clock+1);
 assert.equal(r.status,"facts_only");assert.equal(r.warnings.length,1);assert.equal(r.warnings[0].binding.message_id,"syn-new-health");
});
test("deleted/missing context is not reconstructed from raw synthetic history",()=>{
 const f=setup({scenario:"missing",kind:"weekly"}),r=engine.recommend(f.request,f.context,f.authority);
 assert.equal(r.status,"clarification");assert.deepEqual(r.warnings,[]);assert.deepEqual(r.expert_criteria,[]);
 assert(!JSON.stringify(r).includes("loodzwaar"));assert(!JSON.stringify(r).includes("current_unclassified"));
 assert.equal(f.context.safety_records[0].status,"context_missing");
});
test("continue chatting never settles the other nonclinical issue",()=>{
 const f=setup({scenario:"continue_chat",kind:"weekly"}),r=engine.recommend(f.request,f.context,f.authority);
 assert.equal(r.status,"recommendation");assert.equal(r.nonclinical_options.length,1);
 assert.deepEqual(r.nonclinical_options[0].choices,["reformulate","continue_chat"]);
 assert.equal(flow.view(f.state).unresolved_nonclinical.length,1);
});
test("self-report permits only nonphysical reflection and keeps expert recovery criteria open",()=>{
 const f=setup({scenario:"serious_recovered",kind:"post_workout"}),r=engine.recommend(f.request,f.context,f.authority);
 assert.equal(r.status,"recommendation");assert(r.expert_criteria.includes("serious_recovery"));
 assert(r.messages.some(m=>m.includes("geen medische vrijgave")));
 const denied=engine.recommend({...f.request,type:"recovery_return"},f.context,f.authority);
 assert.equal(denied.status,"content_boundary");assert.equal(denied.medical_clearance,false);
});
for(const kind of ["daily","post_workout","weekly"])test("unseen numeric examples are computed, not selected from fixtures: "+kind,()=>{
 const f=setup({kind});
 for(const fact of f.request.analysis.facts){if(fact.unit==="min")fact.value=42; if(fact.code==="steps")fact.value=4321;}
 const r=engine.recommend(f.request,f.context,f.authority);
 assert.equal(r.status,"recommendation");assert(r.recommendations[0].text.includes("42"));
 if(kind==="weekly")assert(r.recommendations[0].text.includes("-48"));
});
test("wrong kind, duplicate metric, foreign source and injected goal fail closed",()=>{
 for(const change of [
  r=>r.type="workout_reflection",
  r=>r.analysis.facts.push(clone(r.analysis.facts[0])),
  r=>r.analysis.facts[0].source.subject_id="syn-other",
  r=>r.analysis.goal={target:10000}
 ]){const f=setup();change(f.request);assert.equal(engine.recommend(f.request,f.context,f.authority).status,"invalid_input");}
});

test("daily sleep value has its own source in recommendation evidence",()=>{
 const f=setup({variant:"sleep_present"}),r=engine.recommend(f.request,f.context,f.authority);
 assert(r.recommendations[0].basis.some(b=>b.metric==="sleep_hours"&&b.value===8&&b.source.id==="syn-current"));
});
test("different comparison bundles and absent source retain facts but never generate a paired claim",()=>{
 const f=setup({kind:"weekly"});f.request.analysis.facts[0].previous.source.id="syn-separate";
 assert.equal(engine.recommend(f.request,f.context,f.authority).reason,"incoherent_comparison_bundle");
 const g=setup({kind:"post_workout"});g.request.analysis.facts[1].source=null;
 assert.equal(engine.recommend(g.request,g.context,g.authority).status,"facts_only");
});
test("current health warning and binding remain exact, even alongside daily record checks",()=>{
 const f=setup({scenario:"current"}),r=engine.recommend(f.request,f.context,f.authority),issue=f.state.issues[0];
 assert.equal(r.messages[0],issue.feedback.text);assert.equal(r.warnings[0].text,issue.feedback.text);
 assert.equal(r.warnings[0].binding.issue_revision,issue.issue_revision);
 assert.equal(r.warnings[0].binding.source_revision,issue.source_revision);
 assert.equal(r.recommendations[0].physical_prescription,false);
});
test("partially available sleep is never silently treated as zero or as an exact value",()=>{
 const f=setup({variant:"sleep_present"});f.request.analysis.facts.at(-1).source.coverage="partial";
 const r=engine.recommend(f.request,f.context,f.authority);
 assert(r.recommendations[0].text.includes("niet volledig bruikbaar"));assert(!r.recommendations[0].text.includes("8 uur"));
});

test("missing declaration survives reprocessing without reconstructing the source or extending O5",()=>{
 const f=setup({scenario:"missing",kind:"weekly"});
 let c=engine.prepare(f.state,f.clock+1,{},f.context);
 assert.equal(c.safety_records[0].status,"context_missing");
 let r=engine.recommend({...f.request,binding:clone(c.binding)},c,f.authority);
 assert.deepEqual(r.warnings,[]);assert.equal(r.status,"clarification");
 c=engine.prepare(f.state,CLOCK+30*DAY,{},c);assert.deepEqual(c.safety_records,[]);
 r=engine.recommend({...f.request,binding:clone(c.binding)},c,f.authority);
 assert.deepEqual(r.warnings,[]);assert(!JSON.stringify(r).includes("loodzwaar"));
});
test("invalid clock/options cannot supersede a valid context",()=>{
 const f=setup();
 for(const [now,options] of [[f.clock-1,{}],[f.clock,{missing_message_ids:null}],[f.clock,{approved:true}],[f.clock,[]]])
  assert.throws(()=>engine.prepare(f.state,now,options,f.context),/invalid_projection/);
 assert.equal(engine.recommend(f.request,f.context,f.authority).status,"recommendation");
});
