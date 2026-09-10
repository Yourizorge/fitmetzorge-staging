"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,canonical,freeze,locales}=require("../phase6e1/common.cjs");
const {access}=require("../phase6e1/analysis.cjs");
const goals=require("../phase6e3/contract.json").goals;
const context=require("./context.cjs"),{validate}=require("./validate.cjs");
const copy=freeze(require("./copy.json")),contract=freeze(require("./contract.json"));
const clone=x=>JSON.parse(JSON.stringify(x));
const fill=(s,v)=>s.replace(/\{([a-z_]+)\}/g,(_,k)=>{if(!Object.hasOwn(v,k))throw Error("missing_copy_value");return v[k];});
const numeric=(v,locale)=>String(v).replace(".",locale==="en"?".":",");
const range=(r,locale)=>r.min===r.max?numeric(r.min,locale):numeric(r.min,locale)+"-"+numeric(r.max,locale);
const ref=r=>r.id+"@"+r.revision;
function suggest(request,ctx,authority){
  const locale=locales.includes(request?.locale)?request.locale:"en",c=copy[locale],permission=access(authority,ctx?.binding?.subject_id);
  const base={version:contract.version,status:"invalid_input",mode:"candidate_only",access:permission,candidate:null,
    warnings:[],nonclinical_options:[],source_issues:[],messages:[],actions:[],automatic_actions_allowed:false,
    physical_advice_authorized:false,medical_clearance:false,training_suitability_assessed:false,
    provider_calls:0,storage_enabled:false,trainer_sharing:false,human_approval_service:false,
    permanent_health_access_block:false,clarification_required:false,owner_accepted:false,frozen:false,
    existing_nonphysical_reflection:"frozen_6e3_policy_unchanged",source_trust:"synthetic_declared_only_not_live_authority"};
  const invalid=reason=>freeze({...base,reason,messages:[c.none,c.invalid,c.separate,c.scope]});
  if(!exact(request,["synthetic_only","locale","binding","expected_readset","sources"])||request.synthetic_only!==true||!locales.includes(request.locale))return invalid("invalid_request");
  const v=context.view(ctx,request.binding,authority,locale);
  if(!v.valid)return invalid(v.reason);
  const result={...base,binding:clone(ctx.binding),context_mode:v.mode,language_adapter_applied:v.adapted,
    access:v.gate.access,warnings:clone(v.gate.warnings||[]),nonclinical_options:clone(v.options||[]),expert_criteria:clone(v.gate.expert_criteria||[])};
  const finish=(status,reason,tail,extra={})=>freeze({...result,status,reason,...extra,
    messages:[...v.feedback,...tail,c.separate,c.scope]});
  if(!permission.new_analysis)return finish("access_unavailable","analysis_authority",[c.none,c.access]);
  const data=validate(request.sources,ctx.binding.subject_id,ctx.evaluated_at_ms,request.expected_readset);
  if(!data.valid)return finish(data.status,data.reason,[c.none,data.status==="invalid_input"?c.invalid:c.issues[data.reason],
    ...(data.status==="invalid_input"?[]:[fill(c.source,{source:c.source_labels[data.path]||c.source_labels.set})])],
    {source_issues:[{code:data.reason,path:data.path}]});
  if(v.mode==="current_health")return finish("unavailable","current_health_report",[c.none,c.current]);
  if(v.mode==="self_reported")return finish("unavailable","self_report_not_clearance",[c.none,c.recovered]);
  if(v.mode==="clarification")return finish("clarification","optional_clarification_or_retry",[c.none,c.clarify]);
  if(v.mode==="noncurrent_context")return finish("unavailable","noncurrent_not_current_context",[c.none,c.noncurrent]);
  if(v.mode!=="ordinary_or_settled")return finish("unavailable","current_context_unavailable",[c.none,c.context]);
  const rows=data.rows.map(row=>{
    const t=row.target,b=row.boundary;
    return {...clone(row),text:fill(c.row,{exercise:row.labels[locale],index:t.index,reps:range(t.reps,locale),
      load:numeric(t.load.value,locale)+" "+t.load.unit,rir:t.rir===null?c.missing:numeric(t.rir,locale),rpe:t.rpe===null?c.missing:numeric(t.rpe,locale)}),
      limit_text:fill(c.limit,{reps:range(b.reps,locale),min:numeric(b.load.min,locale),max:numeric(b.load.max,locale),unit:b.load.unit,rule:b.id})};
  });
  const refs=Object.fromEntries(Object.entries(data.source_refs).map(([k,r])=>[k,ref(r)]));
  const candidate={type:"existing_explicit_next_trainer_option",option_id:data.chosen.id,workout_id:data.chosen.workout_id,
    goal_code:data.goal.code,source_refs:clone(data.source_refs),readset_ref:clone(data.readset_ref),rows,
    bound_to:clone(ctx.binding),evaluated_at_ms:ctx.evaluated_at_ms,physical_advice_authorized:false,automatic_actions_allowed:false};
  return finish("candidate_only","explicit_source_bounded_option",
    [fill(c.intro,{workout:data.chosen.labels[locale],goal:goals[data.goal.code][locale]}),
      ...rows.flatMap(r=>[r.text,r.limit_text]),c.within,fill(c.refs,refs)],{candidate});
}
module.exports={suggest,prepare:context.prepare,assess:context.assess,validateSources:validate,contract};
