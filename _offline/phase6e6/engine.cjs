"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,clone,freeze,hash,ref,locales}=require("../phase6e5/common.cjs");
const old=require("../phase6e5/engine.cjs"),{resolve}=require("./rules.cjs"),{collect}=require("./facts.cjs");
const {view}=require("../phase6e4/context.cjs"),copy=freeze(require("./copy.json")),issued=new WeakMap();
const fill=old.fill,reference=r=>r.id+"@"+r.revision,numeric=(x,l)=>String(x).replace(".",l==="en"?".":",");
function propose(request,ctx,authority){
 const locale=locales.includes(request?.base?.locale)?request.base.locale:"en",c=copy[locale];
 const out={version:"6e6-offline-v1",status:"invalid_input",mode:"candidate_only",rows:[],facts:{observations:[],omitted:[]},plan_option:null,messages:[],
  automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false,provider_calls:0,storage_enabled:false,
  owner_accepted:false,frozen:false,trainer_sharing:false,source_trust:"synthetic_declared_only_not_live_authority"};
 const fail=(reason,status="facts_only")=>freeze({...out,status,reason,messages:[c.scope,...(out.context_feedback||[]),fill(c.none,{reason:c.issues[reason]||c.issues.invalid}),
  ...out.facts.observations.map(x=>fill(c.fact,{session:reference(x.session_ref),exercise:reference(x.exercise_ref),set:x.set_index,
   reps:x.recorded.reps===null?c.missing:x.recorded.reps,load:x.recorded.load.value===null?c.missing:numeric(x.recorded.load.value,locale),unit:x.recorded.load.unit,
   rir:x.recorded.rir===null?c.missing:x.recorded.rir,rpe:x.recorded.rpe===null?c.missing:x.recorded.rpe,plan:reference(x.plan_ref)})),c.separate]});
 if(!exact(request,["synthetic_only","base","expected_rulebook","rulebook"])||request.synthetic_only!==true)return fail("invalid","invalid_input");
 let context;try{context=view(ctx,request.base.binding,authority,locale);}catch{return fail("invalid","invalid_input");}
 if(!context.valid)return fail("invalid","invalid_input");
 out.access=clone(context.gate.access);out.warnings=clone(context.gate.warnings||[]);out.nonclinical_options=clone(context.options||[]);
 out.context_feedback=clone(context.feedback||[]);
 if(!out.access.new_analysis)return fail("invalid","access_unavailable");
 out.facts=collect(request.base,ctx,authority);
 let resolved;try{resolved=resolve(request,ctx.evaluated_at_ms);}catch{return fail("invalid","invalid_input");}
 if(!resolved.valid)return fail(resolved.reason);
 const result=old.propose(resolved.projected,ctx,authority);
 let option=null;
 if(result.plan_option){
  const oldOption=result.plan_option,data=old.proposalDetails(oldOption),basis=hash({projected_basis:oldOption.basis_hash,rulebook:request.rulebook});
  const payload={...clone(oldOption),basis_hash:basis,rulebook_ref:ref(request.rulebook),rulebook_hash:hash(request.rulebook),
   source_refs:{...clone(oldOption.source_refs),rulebook:ref(request.rulebook)},provenance:clone(resolved.provenance)};
  delete payload.id;option=freeze({...payload,id:"syn-proposal6-"+hash(payload).slice(0,40)});
  issued.set(option,freeze({base_plan:clone(data.base_plan),locale,basis_hash:basis}));
 }
 const rules=resolved.provenance.map(x=>fill(c.rule,{rule:reference(x.rule_ref),kind:c.kinds[x.selector.kind],
  sets:x.parameters.set_count,min:x.parameters.reps_min,max:x.parameters.reps_max,reps:x.parameters.reps_step,weight:numeric(x.parameters.weight_step,locale),unit:x.parameters.unit}));
 return freeze({...out,...result,version:out.version,mode:out.mode,facts:out.facts,plan_option:option,rule_provenance:resolved.provenance,
  rows:result.rows.map(r=>({...clone(r),approval_status:option?"member_and_trainer_pending":"no_applicable_change"})),
  messages:[...result.messages,...rules,...(result.status==="proposal"?[option?c.pending:c.maintain]:[]),c.separate]});
}
module.exports={propose,details:x=>issued.get(x)||null,copy,fill,prepare:old.prepare,assess:old.assess};
