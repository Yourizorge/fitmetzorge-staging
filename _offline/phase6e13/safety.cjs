"use strict";
const f=require("../phase6e2/test/fixtures.cjs"),flow=require("../phase6e1/flow.cjs"),engine=require("../phase6e2/engine.cjs");
const {freeze}=require("../phase6e1/common.cjs");
const issued=new WeakSet(),DAY=86400000,NOW=Date.UTC(2026,8,29);
function create(scenario="ordinary",locale="nl"){
 let s=flow.create("syn-owner"),clock=NOW-1000,prior=null,options={};
 const event=(type,body)=>{const r=flow.apply(s,{type,subject_id:s.subject_id,event_id:"syn-e-"+(s.revision+1),at_ms:++clock,...body});if(r.state===s)throw Error(r.status);s=r.state;return r;};
 const send=(text,availability="available")=>event("message",{expected_revision:s.revision,message_id:"syn-m-"+(s.revision+1),text,locale,availability});
 if(["current","self_reported","recurring","expired_context","missing_context"].includes(scenario))send("Ik heb borstpijn");
 else if(scenario==="unclassified")send("Mijn borst voelt loodzwaar");
 else if(scenario==="unclear")send("flurbel");
 else send(scenario==="german_observation"?"Ich sehe meine erfassten Saetze und Wiederholungen an.":require("../phase6e2/preregistered-cases.json").normal_messages[locale],scenario==="technical"?"unavailable":"available");
 if(["self_reported","recurring"].includes(scenario)){
  event("self_report",{expected_revision:s.revision,targets:s.issues.map(i=>({message_id:i.message_id,source_revision:i.source_revision})),method:"chat",confirmed:false,text:"Mijn klachten zijn voorbij",locale:"nl"});
  if(scenario==="recurring")send("Ik heb borstpijn");
 }
 if(["expired_context","missing_context"].includes(scenario)){
  prior=engine.prepare(s,clock);
  if(scenario==="expired_context")clock+=30*DAY;
  else options={missing_message_ids:[s.messages[0].id]};
 }
 clock++;
 const context=engine.prepare(s,clock,options,prior),authority=f.clone(f.legacy.authority);
 if(scenario==="consent_revoked")authority.ai_analysis_consent=false;
 if(scenario==="entitlement_revoked")authority.ai_entitlement=false;
 if(scenario==="chat_revoked")authority.private_chat_consent=false;
 const request={synthetic_only:true,type:"training_load",binding:f.clone(context.binding),analysis:{
  synthetic_only:true,subject_id:s.subject_id,kind:"weekly",locale,time_basis:"synthetic_utc",window:{start_ms:clock-7*DAY,end_ms:clock},facts:[]}};
 const gate=engine.recommend(request,context,authority);
 if(gate.status==="invalid_input")throw Error("frozen_safety_contract");
 const receipt=freeze({subject_id:s.subject_id,binding:context.binding,now_ms:clock,mode:gate.context_mode||"context_missing",access:gate.access,
  feedback:gate.messages?.slice(0,-2)||[],warnings:gate.warnings||[],expert_criteria:gate.expert_criteria||[],
  medical_clearance:false,context_version:context.version});
 issued.add(receipt);return receipt;
}
module.exports={create,isIssued:x=>issued.has(x),DAY};
