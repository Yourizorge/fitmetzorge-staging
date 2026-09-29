"use strict";
const signals=require("../phase6e13/engine.cjs"),safety=require("../phase6e13/safety.cjs"),{catalogs,hash,clone,freeze}=require("./catalog.cjs");
const {exact}=require("../phase6e5/common.cjs"),{copy}=require("../../bounded-adjustments-demo/copy.js");
const fields=["synthetic_only","subject_id","route","id","revision","previous_hash","issued_at_ms","valid_until_ms","goal_ref","plan_ref","template","trainer_ref","catalog_ref","plan","option","kind","rules","sessions","signal"];
function evaluate(source,gate,locale="nl",expected=hash(source)){
 const c=copy[locale];if(!c)throw Error("locale");
 const base={synthetic_only:true,mode:"candidate_only",status:"blocked",reason:"invalid",source_hash:hash(source),facts:[],messages:[],feedback:[],
  before:null,target:null,access:{chat:false,history:false,new_analysis:false},binding:null,
  automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false,trainer_sharing:false,provider_calls:0};
 const end=(status,reason,text,extra={})=>freeze({...base,status,reason,messages:[text,c.boundary],...extra});
 if(!exact(source,fields)||!source.plan_ref||!source.goal_ref||!source.signal||!Array.isArray(source.rules)||source.synthetic_only!==true||!safety.isIssued(gate)||source.subject_id!==gate.subject_id||
  source.id!=="syn-adjustment-source"||!Number.isInteger(source.revision)||source.revision<1||hash(source)!==expected||!["A","B"].includes(source.route)||
  !Object.hasOwn(catalogs,source.template))return end("blocked","binding",c.blocked);
 const cat=catalogs[source.template],b=source.route==="B";
 base.access=gate.access;
 if(!gate.access.new_analysis)return end("blocked","consent",c.consent);
 if(b!==(source.template==="b_schedule")||hash(source.catalog_ref)!==hash({id:cat.id,revision:cat.revision,sha256:cat.source_sha256})||
  hash(source.plan)!==hash(cat.before)||hash(source.option)!==hash(cat.after)||source.plan_ref.id!==(b?"syn-independent-plan":"syn-trainer-plan")||
  source.plan_ref.revision!==(b?1:3)||source.goal_ref.id!==(b?"syn-independent-strength":"syn-trainer-strength")||source.goal_ref.revision!==1)
  return end("blocked","catalog_or_plan_conflict",c.conflict);
 if(!Number.isSafeInteger(source.issued_at_ms)||!Number.isSafeInteger(source.valid_until_ms)||source.issued_at_ms>gate.now_ms||
  source.valid_until_ms<=gate.now_ms||source.valid_until_ms>gate.now_ms+safety.DAY)return end("blocked","expired",c.expired);
 if(!b&&hash(source.trainer_ref)!==hash({id:"syn-trainer",revision:1})||b&&source.trainer_ref!==null)return end("blocked","trainer",c.noTrainer);
 if(hash(source.signal.goal_ref)!==hash(source.goal_ref)||hash(source.signal.snapshot_ref)!==hash(source.plan_ref)||
  source.signal.subject_id!==source.subject_id||source.signal.route!==(b?"INDEPENDENT":"HUMAN_REQUIRED"))return end("blocked","signal_binding",c.conflict);
 const out=signals.evaluate(source.signal,gate,locale);
 base.access=out.access;base.feedback=out.feedback;base.facts=out.facts;
 base.binding={source:{id:source.id,revision:source.revision},signal:{id:source.signal.id,revision:source.signal.revision,sha256:out.source_hash},
  plan:clone(source.plan_ref),goal:clone(source.goal_ref),catalog:clone(source.catalog_ref),rule:clone(source.rules),safety:clone(gate.binding),valid_until_ms:source.valid_until_ms};
 base.before=clone(source.plan);
 if(source.kind==="registration"&&out.reason==="incomplete_or_disputed")return end("confirmation","registration_incomplete",c.registration);
 if(out.status==="blocked")return end("blocked",out.reason,c.incomplete);
 if(["current_health","context_missing","clarification"].includes(out.context_mode))return end("facts_only","safety",c.safety);
 if(source.kind==="nutrition_change")return end("facts_only","nutrition_rule_missing",c.nutrition);
 if(source.kind==="reflection")return end("reflection","nonphysical_planning",c.reflection);
 if(source.kind!=="plan")return end("blocked","kind",c.blocked);
 if(out.context_mode!=="ordinary_or_settled"||!out.access.chat)return end("facts_only","physical_resume_not_authorized",c.safety);
 if(!Array.isArray(source.rules)||source.rules.length!==1)return end("facts_only",source.rules.length?"ambiguous_rules":"missing_rule",source.rules.length?c.ambiguous:c.noRule);
 const rule=source.rules[0],expectedRule={id:b?"syn-missed-catalog-binding":"syn-explicit-trainer-binding",revision:1,status:"active",signal:"training",option:cat.id};
 if(hash(rule)!==hash(expectedRule))return end("facts_only","rule_invalid",c.noRule);
 if(!out.changes?.includes("training"))return end("facts_only","no_matching_signal",c.noMatch);
 if(!Array.isArray(source.sessions)||!source.sessions.length||source.sessions.some(x=>!x||typeof x!=="object")||new Set(source.sessions.map(x=>x.id)).size!==source.sessions.length)
  return end("blocked","sessions",c.incomplete);
 for(const s of source.sessions)if(!exact(s,["id","day_ms","planned","completed_sets","planned_sets","complete"])||typeof s.id!=="string"||!s.id.startsWith("syn-")||
  !Number.isSafeInteger(s.day_ms)||s.day_ms%safety.DAY||s.day_ms>=source.signal.window_end_ms||s.planned!==true||s.complete!==true||
  !Number.isSafeInteger(s.completed_sets)||s.completed_sets<0||s.completed_sets>s.planned_sets||s.planned_sets!==6)return end("blocked","sessions",c.incomplete);
 for(const row of source.signal.rows.filter(r=>r.metric==="training"))if(row.value!==source.sessions.filter(s=>s.day_ms===row.day_ms).reduce((n,s)=>n+s.completed_sets,0))
  return end("blocked","session_totals",c.incomplete);
 if(b){
  const priorWeek=source.sessions.filter(s=>s.day_ms>=source.signal.window_end_ms-7*safety.DAY).sort((a,b)=>a.day_ms-b.day_ms);
  if(priorWeek.length!==3||hash(priorWeek.map(s=>s.completed_sets===0))!==hash(cat.signal.values)||
   hash(priorWeek.map(s=>["sun","mon","tue","wed","thu","fri","sat"][new Date(s.day_ms).getUTCDay()]))!==hash(cat.before.intake.days))
   return end("blocked","catalog_evidence_mismatch",c.incomplete);
 }else{
  const offset=gate.now_ms-cat.source_clock,expectedSessions=cat.history.sessions.map(h=>({id:h.id,day_ms:Math.floor((h.completed_at_ms+offset)/safety.DAY)*safety.DAY,planned:true,
   completed_sets:h.sets.filter(s=>s.completed).length,planned_sets:6,complete:true}));
  if(hash(source.sessions)!==hash(expectedSessions))return end("blocked","trainer_history_binding",c.incomplete);
  if(cat.gate)return end("facts_only","trainer_gate",c.noRule);
 }
 if(hash(source.plan)===hash(source.option))return end("maintain","existing_maintain_rule",c.maintain);
 const list=b?"":cat.after.training.exercises.map(e=>e.labels[locale]+": "+e.sets.length+" x "+e.sets[0].reps.min+" / "+e.sets[0].load.value+" "+e.sets[0].load.unit).join("; ");
 const intro={nl:"Bestaande traineroptie",en:"Existing trainer option",de:"Bestehende Traineroption"}[locale];
 const next={nl:"Beoordeel, laat de trainer afzonderlijk goedkeuren en pas daarna apart toe.",en:"Review, obtain separate trainer approval, then apply separately.",de:"Pruefen, getrennte Trainerfreigabe einholen, dann separat anwenden."}[locale];
 const reasons={
  nl:{increase_reps:"De geregistreerde sets halen het doel onder de repgrens; de trainerregel geeft +1 herhaling.",increase_weight:"De geregistreerde sets halen de repgrens; de trainerregel geeft de volledige gewichtsstap en resetreps.",maintain:"Het geregistreerde doel is niet gehaald; de trainerregel houdt het doel gelijk."},
  en:{increase_reps:"Recorded sets meet the target below the rep ceiling; the trainer rule adds one rep.",increase_weight:"Recorded sets meet the rep ceiling; the trainer rule specifies the full weight step and reset reps.",maintain:"The recorded target was not met; the trainer rule keeps the target."},
  de:{increase_reps:"Erfasste Saetze erreichen das Ziel unter der Wiederholungsgrenze; die Trainerregel erhoeht um eine Wiederholung.",increase_weight:"Erfasste Saetze erreichen die Wiederholungsgrenze; die Trainerregel legt den vollen Gewichtsschritt und die Startwiederholungen fest.",maintain:"Das erfasste Ziel wurde nicht erreicht; die Trainerregel behaelt das Ziel bei."}
 };
 const rationale=b?[]:cat.observations.map(r=>r.labels[locale]+": "+reasons[locale][r.kind]);
 return end("candidate_only","explicit_existing_option",b?c.bProposal:intro+": "+list+". "+next,{target:clone(source.option),rationale});
}
module.exports={evaluate};
