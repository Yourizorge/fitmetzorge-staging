"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,canonical,freeze,normalized,locales}=require("../phase6e1/common.cjs");
const original=require("../phase6e1/context.cjs");
const safety=require("../phase6e2/engine.cjs");
const safetyCopy=require("../phase6e2/copy.json");
const issued=new WeakMap(),superseded=new WeakSet();
const patterns={
  nl:/^(?:ik bekijk (?:nu )?mijn trainingsregistratie(?: van gisteren)?|nu bekijk ik mijn trainingsregistratie|ik wil mijn trainingsregistratie bekijken|kan ik mijn trainingsregistratie bekijken|ik kijk mijn trainingsregistratie na)[.!?]?$/,
  en:/^(?:i am reviewing my workout log|i review my training records|i want to review my training records|can i review my training records)[.!?]?$/,
  de:/^(?:ich sehe mir mein trainingsprotokoll an|ich m(?:oe|o)chte mein trainingsprotokoll ansehen|kann ich mein trainingsprotokoll ansehen|ich pr(?:ue|u)fe meine trainingsaufzeichnungen)[.!?]?$/
};
const reviewMarker=/\b(?:trainingsregistratie|workout log|training records|trainingsprotokoll|trainingsaufzeichnungen)\b/;
function assess(input){
  const frozen=original.assess(input);
  // Only a completely consumed review phrase may explain unresolved meaning.
  // Existing signals, noncurrent traces, symbols, errors or residue always win.
  const text=typeof input?.text==="string"?normalized(input.text).value.trim().replace(/\s+/g," "):"";
  const complete=patterns[input?.locale]?.test(text);
  const adapted=frozen.category==="communication"&&frozen.trace.length===0&&frozen.conflicts.length===0&&
    canonical(frozen.uncertainty)===canonical(["unresolved_meaning"])&&complete;
  const residue=frozen.category==="ordinary"&&reviewMarker.test(text)&&!complete;
  return freeze({original:frozen,category:residue?"communication":adapted?"ordinary":frozen.category,adapted:Boolean(adapted||residue),
    review_residue_unresolved:residue,adapter_rule:residue?"unconsumed_review_context_v1":adapted?"complete_record_review_phrase_v1":null,
    level:residue?null:adapted?"R0":frozen.level,
    medical_clearance:false,training_suitability_assessed:false});
}
function prepare(state,now,options={},previous=null){
  const prior=previous===null?null:issued.get(previous);
  if(previous!==null&&(!prior||superseded.has(previous)))throw Error("current_issued_context_required");
  const inner=safety.prepare(state,now,options,prior?.inner||null);
  const result=freeze({version:"6e4-context-v1",binding:inner.binding,evaluated_at_ms:now,
    safety_records:inner.safety_records,storage_enabled:false,medical_clearance:false});
  issued.set(result,{state,inner});if(previous)superseded.add(previous);
  return result;
}
function view(context,binding,authority,locale){
  const data=issued.get(context);
  if(!data||superseded.has(context)||!exact(binding,["subject_id","revision","message_id","source_revision"])||
    canonical(binding)!==canonical(context.binding)||!locales.includes(locale))return {valid:false,reason:"stale_or_wrong_context"};
  const {state,inner}=data,now=context.evaluated_at_ms;
  if(now<1)return {valid:false,reason:"missing_evaluation_window"};
  const gate=safety.recommend({synthetic_only:true,type:"workout_reflection",binding:inner.binding,
    analysis:{synthetic_only:true,subject_id:state.subject_id,kind:"post_workout",locale,time_basis:"synthetic_utc",
      window:{start_ms:now-1,end_ms:now},facts:[]}},inner,authority);
  if(gate.status==="access_unavailable")return {valid:true,gate,mode:"access_unavailable",feedback:[],adapted:false};
  if(gate.status==="invalid_input"||gate.reason!=="required_data_missing"||gate.messages.at(-1)!==safetyCopy[locale].scope)return {valid:false,reason:"unsupported_safety_contract"};
  let mode=gate.context_mode,feedback=gate.messages.slice(0,-2),options=gate.nonclinical_options,adapted=false;
  if(!gate.access.chat)return {valid:true,gate,mode:"context_missing",feedback:[],options:[],adapted:false};
  const latest=state.messages.at(-1),records=context.safety_records;
  const retained=i=>records.some(r=>r.status!=="context_missing"&&r.message_ref.message_id===i.retention_origin.message_id&&r.message_ref.source_revision===i.retention_origin.source_revision);
  const available=state.issues.filter(retained);
  // The view may reinterpret a retained communication issue, never alter its
  // event, status, original assessment or O5 deadline in the frozen simulator.
  if(mode==="clarification"){
    const pending=available.filter(i=>i.kind!=="health_report"&&i.status!=="settled");
    const allReview=pending.length>0&&pending.every(i=>{
      const m=state.messages.find(m=>m.id===i.message_id&&m.source_revision===i.source_revision);
      return i.kind==="communication"&&m&&assess({synthetic_only:true,text:m.text,locale:m.locale,availability:"available"}).adapted;
    });
    const latestReview=latest&&assess({synthetic_only:true,text:latest.text,locale:latest.locale,availability:"available"});
    if(allReview&&available.length===state.issues.length&&latestReview.category==="ordinary"&&
      !available.some(i=>i.kind==="health_report")&&!latest.assessment.recovery){
      mode="ordinary_or_settled";feedback=[];options=[];adapted=true;
    }
  }
  if(mode!=="current_health"&&(gate.self_reported||latest?.assessment.recovery))mode="self_reported";
  if(mode==="ordinary_or_settled"&&latest?.assessment.category==="noncurrent")mode="noncurrent_context";
  if(mode==="ordinary_or_settled"&&latest&&assess({synthetic_only:true,text:latest.text,locale:latest.locale,availability:"available"}).review_residue_unresolved){
    mode="clarification";feedback=[];adapted=true;
    options=[{kind:"new_message",binding:context.binding,choices:["reformulate_as_new_message","continue_chat"]}];
  }
  return {valid:true,gate,mode,feedback,options:options||[],adapted};
}
module.exports={assess,prepare,view};
