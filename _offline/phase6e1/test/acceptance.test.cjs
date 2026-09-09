"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const retention=require("../retention.cjs"),flow=require("../flow.cjs");
const {subject,message,begin,recover,event,DAY}=require("./helpers.cjs");
const health=()=>message(flow.create(subject),"Mijn borst voelt loodzwaar").state;
const project=(s,at,options,previous)=>retention.projectSafety(s,at,options,previous);
for(const delta of [-1,0,1])test("O5 exact first-registration +30 days boundary "+delta,()=>{
 const s=health(),first=s.issues[0].created_at_ms,r=project(s,first+30*DAY+delta);
 assert.equal(r.records.length,delta<0?1:0);assert.equal(r.medical_clearance,false);assert.equal(r.storage_enabled,false);
 if(delta<0)assert.deepEqual(Object.keys(r.records[0]).sort(),["first_registered_at_ms","message_ref","status"]);
});
test("O5 inspect/reprocess never extends first registration or recreates expired records",()=>{
 const s=health(),first=s.issues[0].created_at_ms;
 let p=project(s,first);p=project(s,first+29*DAY,{},p);
 assert.equal(p.records[0].first_registered_at_ms,first);
 p=project(s,first+30*DAY,{},p);assert.equal(p.records.length,0);
 p=project(s,first+30000*DAY,{},p);assert.equal(p.records.length,0);
 assert(!JSON.stringify(p).includes(s.messages[0].id));assert(!JSON.stringify(p).includes(s.messages[0].text));
});
test("O5 earlier unnecessary removal is not revived by later status/self-report/reprocessing",()=>{
 const s=health(),id=s.messages[0].id;
 let p=project(s,10);p=project(s,11,{unnecessary_message_ids:[id]},p);
 assert.equal(p.records.length,0);
 const self=recover(s).state;p=project(self,12,{},p);assert.equal(p.records.length,0);
});
for(const kind of ["open","awaiting","settled","self_reported"])test("O5 status cannot escape 30-day safety cap: "+kind,()=>{
 let s=kind==="open"||kind==="self_reported"?health():message(flow.create(subject),"flurbel").state;
 const first=s.issues[0].created_at_ms;let p=project(s,first);
 if(kind==="self_reported")s=recover(s).state;
 if(kind==="awaiting"||kind==="settled"){
  const started=begin(s);s=started.state;
  if(kind==="settled")s=flow.apply(s,event(s,"clarify",{binding:started.binding,text:"Ik bedoelde mijn borsttraining",locale:"nl"})).state;
 }
 p=project(s,first+29*DAY,{},p);assert.equal(p.records[0].status,kind);
 p=project(s,first+30*DAY,{},p);assert.equal(p.records.length,0);
 p=project(s,first+200*DAY,{},p);assert.equal(p.records.length,0);
});
test("O5 delayed technical retry inherits source registration, not retry event time",()=>{
 let s=message(flow.create(subject),"Ik heb borstpijn","nl","unavailable").state;
 const origin=s.messages[0],started=begin(s);let p=project(started.state,30*DAY+1);
 s=flow.apply(started.state,{...event(started.state,"retry",{binding:started.binding,availability:"available"}),at_ms:31*DAY}).state;
 assert.equal(flow.view(s).current_reports,1);
 p=project(s,31*DAY,{},p);assert.equal(p.records.length,0);
 assert.equal(project(s,31*DAY).records.length,0);
 assert.equal(s.issues[1].retention_origin.message_id,origin.id);
 assert.equal(s.issues[1].retention_origin.first_registered_at_ms,origin.at_ms);
});
test("O5 missing source keeps only reference/status, no text reconstruction or fresh anchor",()=>{
 const s=health(),id=s.messages[0].id,original=JSON.stringify(s);
 let p=project(s,DAY,{missing_message_ids:[id]});
 assert.equal(p.records[0].status,"context_missing");assert.equal(p.records[0].message_ref.message_id,id);
 assert(!JSON.stringify(p).includes(s.messages[0].text));assert.equal(p.medical_clearance,false);
 p=project(s,30*DAY+1,{missing_message_ids:[id]},p);assert.equal(p.records.length,0);
 assert.equal(JSON.stringify(s),original);
});
test("O5 genuine new report gets its own first registration; old record stays gone",()=>{
 let s=health(),p=project(s,30*DAY+1);
 s=flow.apply(s,{...event(s,"message",{expected_revision:s.revision,message_id:"syn-new-complaint",text:"Ik heb borstpijn",locale:"nl",availability:"available"}),at_ms:31*DAY}).state;
 p=project(s,31*DAY,{},p);assert.equal(p.records.length,1);
 assert.equal(p.records[0].message_ref.message_id,"syn-new-complaint");
 assert.equal(p.records[0].first_registered_at_ms,31*DAY);
 assert.equal(project(s,61*DAY,{},p).records.length,0);
});
test("O5 raw forged lifecycle, wrong subject, backward clock and extra fields rejected",()=>{
 const s=health(),p=project(s,DAY);
 assert.throws(()=>project(JSON.parse(JSON.stringify(s)),DAY),/issued_synthetic_state/);
 assert.throws(()=>project(s,DAY,{},JSON.parse(JSON.stringify(p))),/issued_safety_projection/);
 assert.throws(()=>project(flow.create("syn-other"),DAY,{},p),/invalid_projection/);
 assert.throws(()=>project(s,1,{},p),/invalid_projection/);
 assert.throws(()=>project(s,DAY,{closed_details:true}),/invalid_projection/);
});
test("O2 failed clarification exposes reformulate and continue chat without clearing health",()=>{
 let s=message(flow.create(subject),"flurbel").state;
 s=message(s,"Ik heb borstpijn").state;
 const b=begin(s),failed=flow.apply(b.state,event(b.state,"clarify",{binding:b.binding,text:"flurbel",locale:"nl"}));
 const v=flow.view(failed.state);
 assert.deepEqual(v.nonclinical_options[0].choices,["reformulate","continue_chat"]);
 assert.equal(v.clarification_required,false);
 const continued=message(failed.state,"Ik train mijn benen").state;
 assert.equal(flow.view(continued).current_reports,1);assert.equal(flow.view(continued).unresolved_nonclinical.length,1);
 assert.deepEqual(flow.view(continued).warnings,v.warnings);
});
test("O2 technical retry is optional and never an enforced loop",()=>{
 const s=message(flow.create(subject),"Ik train benen","nl","unavailable").state;
 assert.deepEqual(flow.view(s).nonclinical_options[0].choices,["retry","continue_chat"]);
 assert.equal(flow.view(message(s,"Ik train armen").state).unresolved_nonclinical.length,1);
});
test("O5 successful retry before expiry folds into the same minimal source record",()=>{
 const initial=message(flow.create(subject),"Ik heb borstpijn","nl","unavailable").state;
 let p=project(initial,DAY);const b=begin(initial);
 const next=flow.apply(b.state,{...event(b.state,"retry",{binding:b.binding,availability:"available"}),at_ms:29*DAY}).state;
 p=project(next,29*DAY,{},p);assert.equal(p.records.length,1);
 assert.equal(p.records[0].first_registered_at_ms,initial.messages[0].at_ms);
 assert.equal(p.records[0].message_ref.message_id,initial.messages[0].id);
 assert.equal(p.records[0].status,"open");
 assert.equal(project(next,30*DAY+1,{},p).records.length,0);
});
test("O5 only the unnecessary source is removed; a missing source never resets its cap",()=>{
 let s=health();s=message(s,"flurbel").state;
 const ids=s.messages.map(m=>m.id);let p=project(s,DAY);
 p=project(s,2*DAY,{unnecessary_message_ids:[ids[0]],missing_message_ids:[ids[1]]},p);
 assert.equal(p.records.length,1);assert.equal(p.records[0].status,"context_missing");
 const anchor=p.records[0].first_registered_at_ms;
 p=project(s,3*DAY,{},p);assert.equal(p.records.length,1);assert.equal(p.records[0].first_registered_at_ms,anchor);
 p=project(s,30*DAY+anchor,{},p);assert.equal(p.records.length,0);
});
test("O5 invalid lists and overflowing timestamps are rejected",()=>{
 const s=health();
 for(const options of [{unnecessary_message_ids:null},{missing_message_ids:["syn-unknown"]},
   {missing_message_ids:[s.messages[0].id,s.messages[0].id]},[]])
  assert.throws(()=>project(s,DAY,options),/invalid_projection/);
 const r={id:"syn-record",class:"unresolved_signal",created_at_ms:Number.MAX_SAFE_INTEGER,
  closed_at_ms:null,necessary:true,details_present:true};
 assert.equal(retention.plan([r],Number.MAX_SAFE_INTEGER).status,"invalid_input");
});
