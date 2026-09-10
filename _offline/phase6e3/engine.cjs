"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, canonical, freeze, locales } = require("../phase6e1/common.cjs");
const { access } = require("../phase6e1/analysis.cjs");
const safety = require("../phase6e2/engine.cjs");
const safetyCopy = require("../phase6e2/copy.json");
const { validateSources, tuple } = require("./validate.cjs");
const contract = freeze(require("./contract.json")), copy = freeze(require("./copy.json"));
const clone = x => JSON.parse(JSON.stringify(x));
const reference = s => ({id:s.id,revision:s.revision});
const matches = (s,r) => s && canonical(reference(s)) === canonical(r);
const fill = (s, values) => s.replace(/\{([a-z_]+)\}/g, (_,k) => {
  if (!Object.hasOwn(values,k)) throw Error("missing_copy_value"); return values[k];
});
const numeric = (v,locale) => String(v).replace(".",locale==="en"?".":",");
const value = (v,locale,c) => v===null?c.missing:numeric(v,locale);
function dataView(s, locale) {
  const c=copy[locale], observations=[], unavailable=[];
  const add=(code,where={})=>unavailable.push({code,...where,text:c.issues[code]});
  const p=matches(s.snapshot,s.session.snapshot_ref)?s.snapshot:null;
  const r=matches(s.recording,s.session.recording_ref)?s.recording:null;
  if(!p) add("snapshot"); if(!r) add("recording");
  if(!p||!r) return {observations,unavailable,complete:false};
  const logs=new Map(r.sets.map(x=>[tuple(x),x]));
  let targetCount=0;
  for(const ex of p.exercises) {
    const catalog=s.catalog.find(e=>e.id===ex.exercise_id&&e.revision===ex.catalog_revision);
    if(!catalog) add("catalog",{exercise_id:ex.exercise_id});
    for(const planned of ex.sets) {
      targetCount++;
      const location={exercise_id:ex.exercise_id,index:planned.index};
      const recorded=logs.get(tuple(location));
      if(!recorded) {add("missing_set",location);continue;}
      if(!catalog) continue;
      const repComparable=planned.reps!==null&&recorded.reps!==null;
      const loadComparable=planned.load.value!==null&&recorded.load.value!==null&&
        planned.load.unit==="kg"&&recorded.load.unit==="kg";
      if(!repComparable) add("reps",location); if(!loadComparable) add("load",location);
      const relation=!repComparable?null:recorded.reps<planned.reps.min?"below":
        recorded.reps>planned.reps.max?"above":"within";
      const formatLoad=l=>l.value!==null&&l.unit==="kg"?numeric(l.value,locale)+" kg":c.unknown_load;
      const formatReps=n=>n===null?c.missing:typeof n==="number"?numeric(n,locale):
        n.min===n.max?numeric(n.min,locale):numeric(n.min,locale)+"-"+numeric(n.max,locale);
      let text=fill(c.row,{exercise:catalog.labels[locale],index:planned.index,
        planned:formatReps(planned.reps)+" "+c.reps+" "+c.with+" "+formatLoad(planned.load),
        recorded:formatReps(recorded.reps)+" "+c.reps+" "+c.with+" "+formatLoad(recorded.load)});
      if(relation) text+=" "+c[relation];
      text+=" "+fill(c.effort,{rir:value(recorded.rir,locale,c),rpe:value(recorded.rpe,locale,c)});
      if(planned.rir!==null||planned.rpe!==null) text+=" "+fill(c.target_effort,{rir:value(planned.rir,locale,c),rpe:value(planned.rpe,locale,c)});
      observations.push({...location,planned:clone(planned),recorded:clone(recorded),
        comparison:{reps:relation,load:loadComparable?(planned.load.value===recorded.load.value?"equal":"different"):null},
        effort_is_self_report:true,
        source_refs:{snapshot:reference(p),plan:clone(p.plan_ref),recording:reference(r),record_id:recorded.id,catalog:reference(catalog)},
        text});
    }
  }
  const partial=r.coverage!=="complete"||targetCount!==r.sets.length;
  if(partial) unavailable.push({code:"partial",text:c.partial});
  return {observations,unavailable,complete:!partial&&unavailable.length===0&&observations.length>0};
}
function goalView(s,locale) {
  const p=s.snapshot,g=s.goal,link=p?.goal_link,t=s.session.started_at_ms;
  if(!p||!link||!g||g.id!==link.id||g.revision!==link.revision||g.status_at_capture!=="active"||
      g.captured_at_ms>link.at_ms||g.valid_from_ms>t||(g.valid_until_ms!==null&&g.valid_until_ms<=t)||
      !Object.hasOwn(contract.goals,g.code)) return null;
  return {source_ref:reference(g),code:g.code,link:clone(link),historical_at_ms:t,
    text:fill(copy[locale].goal,{goal:contract.goals[g.code][locale]})};
}
function reflect(request, context, authority) {
  const locale=locales.includes(request?.locale)?request.locale:"en",c=copy[locale];
  const permission=access(authority,context?.binding?.subject_id);
  const base={version:contract.version,status:"invalid_input",access:permission,observations:[],unavailable:[],
    recommendations:[],warnings:[],nonclinical_options:[],messages:[],actions:[],automatic_actions_allowed:false,
    medical_clearance:false,training_suitability_assessed:false,trainer_sharing:false,trainer_limits_source:null,
    runtime_execution:false,storage_enabled:false,provider_calls:0,human_approval_service:false,
    permanent_health_access_block:false,owner_accepted:false,frozen:false,complete_health_resumption_flow:false,
    all_expert_reviews_open:true};
  const reject=(reason,detail)=>freeze({...base,reason,...(detail?{detail}:{}),messages:[c.invalid]});
  if(!exact(request,["synthetic_only","locale","binding","sources"])||request.synthetic_only!==true||
      !locales.includes(request.locale)||canonical(request.binding)!==canonical(context?.binding))
    return reject("invalid_request_or_binding");
  if(!permission.new_analysis) return freeze({...base,status:"access_unavailable",reason:"analysis_authority",messages:[c.access]});
  const valid=validateSources(request.sources,context.binding.subject_id,context.evaluated_at_ms);
  if(!valid.valid) return reject("invalid_sources",valid.reason);
  const s=request.sources;
  // The frozen 6E-2 engine owns the context/O5 decision. An empty, truthful
  // metric list is a probe only: 6E-3 validates its set sources separately.
  let gate;
  try {gate=safety.recommend({synthetic_only:true,type:"workout_reflection",binding:request.binding,
    analysis:{synthetic_only:true,subject_id:s.subject_id,kind:"post_workout",locale,time_basis:"synthetic_utc",
      window:{start_ms:s.session.started_at_ms,end_ms:s.session.ended_at_ms},facts:[]}},context,authority);
  } catch {return reject("invalid_context");}
  if(gate.status==="invalid_input") return reject(gate.reason);
  if(gate.reason!=="required_data_missing"||gate.messages.at(-1)!==safetyCopy[locale].scope||
      !["current_health","context_missing","clarification","self_reported","fresh_limited_context","ordinary_or_settled"].includes(gate.context_mode))
    return reject("unsupported_safety_contract");
  const data=dataView(s,locale),goal=goalView(s,locale);
  // In the pinned contract, feedback precedes the final data message and scope.
  const feedback=gate.messages.slice(0,-2);
  const result={...base,access:gate.access,binding:clone(gate.binding),context_mode:gate.context_mode,
    self_reported:gate.self_reported,expert_criteria:clone(gate.expert_criteria),warnings:clone(gate.warnings),
    nonclinical_options:clone(gate.nonclinical_options),observations:data.observations,unavailable:data.unavailable,
    goal:goal&&matches(s.snapshot,s.session.snapshot_ref)?goal:null};
  const finish=(status,reason,tail,recommendations=[])=>freeze({...result,status,reason,recommendations,
    messages:[...feedback,...(result.goal?[result.goal.text]:[]),...data.observations.map(o=>o.text),
      ...data.unavailable.map(u=>u.text),tail,safetyCopy[locale].scope]});
  if(gate.context_mode==="current_health") return finish("facts_only","current_health_report",safetyCopy[locale].current);
  if(["context_missing","clarification"].includes(gate.context_mode))
    return finish("clarification","context_unavailable",safetyCopy[locale][gate.context_mode]);
  if(!data.complete) return finish("facts_only","source_or_comparison_unavailable",c.data);
  if(!result.goal) return finish("facts_only","historical_goal_unavailable",c.goal_missing);
  return finish("recommendation","historical_goal_plan_reflection",c.reflect,[{
    type:contract.type,content_class:contract.content_class,text:c.reflect,goal_source:clone(goal),
    basis:data.observations.map(o=>({exercise_id:o.exercise_id,index:o.index,source_refs:clone(o.source_refs)})),
    bound_to:clone(context.binding),physical_prescription:false,trainer_limits_source:null}]);
}
module.exports={prepare:safety.prepare,reflect,validateSources,contract};
