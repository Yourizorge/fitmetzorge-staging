"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,clone,freeze,same,ref,hash,locales}=require("./common.cjs");
const frozen=require("../phase6e4/engine.cjs"),goals=require("../phase6e3/contract.json").goals;
const {validate,calculate}=require("./validate.cjs"),copy=freeze(require("./copy.json")),contract=freeze(require("./contract.json"));
const issued=new WeakMap();
const fill=(text,values)=>text.replace(/\{([a-z_]+)\}/g,(_,k)=>{if(!Object.hasOwn(values,k))throw Error("missing_copy_value:"+k);return values[k];});
const numeric=(x,locale)=>String(x).replace(".",locale==="en"?".":",");
const referenceText=r=>r.id+"@"+r.revision;
function basis(request){
 const b=clone(request);delete b.locale;delete b.base.locale;
 delete b.base.sources.readset.read_at_ms;if(b.history)delete b.history.read_at_ms;
 return hash(b);
}
function propose(request,context,authority){
 const locale=locales.includes(request?.locale)?request.locale:"en",c=copy[locale];
 const out={version:contract.version,status:"invalid_input",mode:"synthetic_progression_candidate_only",rows:[],plan_option:null,
  warnings:[],messages:[],nonclinical_options:[],automatic_actions_allowed:false,physical_advice_authorized:false,
  medical_clearance:false,training_suitability_assessed:false,provider_calls:0,storage_enabled:false,trainer_sharing:false,
  owner_accepted:false,frozen:false,live_requirements:["validated_real_coaching_rules","medical_content_and_resumption","trusted_live_sources_and_authorization","privacy_legal_language_review","separate_live_GO"]};
 const fail=(reason,status="invalid_input",extra={})=>freeze({...out,status,reason,...extra,messages:[c.scope,fill(c.none,{reason:c.issues[reason]||c.issues.invalid_request}),c.separate]});
 if(!exact(request,["synthetic_only","locale","binding","base","expected_progression","policy","history"])||
  request.synthetic_only!==true||!locales.includes(request.locale)||!same(request.binding,request.base?.binding)||
  request.base?.locale!==locale)return fail("invalid_request");
 let gate;try{gate=frozen.suggest(request.base,context,authority);}catch{return fail("invalid_request");}
 out.access=clone(gate.access);out.warnings=clone(gate.warnings);out.nonclinical_options=clone(gate.nonclinical_options);
 if(gate.status!=="candidate_only"){
  const reason=gate.reason==="missing_relationship"?"fmz_policy_missing":gate.reason;
  return freeze({...out,status:gate.status,reason,context_mode:gate.context_mode,
   messages:[c.scope,...(reason==="fmz_policy_missing"?[fill(c.none,{reason:c.issues.fmz_policy_missing})]:gate.messages),c.issues.safety,c.separate]});
 }
 const data=validate(request,context.evaluated_at_ms,gate);
 if(!data.valid)return fail(data.reason,data.status,{access:out.access});
 const p=data.policy,s=request.base.sources,rows=[];
 for(const exercise of s.plan.options.find(o=>o.id===s.selection.option_id).exercises){
  const targets=gate.candidate.rows.filter(r=>r.exercise_id===exercise.exercise_id);
  const rule=p.rules.find(r=>r.exercise_id===exercise.exercise_id),row=calculate(rule,targets,data.history);
  rows.push({...row,exercise_id:exercise.exercise_id,labels:clone(targets[0].labels)});
 }
 const messages=[c.scope,fill(c.intro,{goal:goals[s.goal.code][locale]})];
 for(const row of rows){
  if(row.status!=="available"){
   messages.push(fill(c.missing,{exercise:row.labels[locale],reason:c.issues[row.reason]}));
   if(row.detail&&c.details[row.detail])messages.push(c.details[row.detail]);
   continue;
  }
  const current=row.current_plan,next=row.next_week;
  messages.push(fill(c.plan,{exercise:row.labels[locale],sets:current.sets,reps:current.reps,load:numeric(current.load.value,locale)+" "+current.load.unit}));
  for(const x of row.observations)messages.push(fill(c.observed,{session:referenceText(x.session_ref),index:x.set_index,
   reps:x.reps,load:numeric(x.load.value,locale)+" "+x.load.unit,rir:x.rir===null?c.null:numeric(x.rir,locale),rpe:x.rpe===null?c.null:numeric(x.rpe,locale)}));
  messages.push(fill(c.next,{sets:next.sets,reps:next.reps,load:numeric(next.load.value,locale)+" "+next.load.unit,kind:c.kinds[row.kind]}));
  messages.push(fill(c.rule,{reason:c.reasons[row.reason],rule:row.rule.id,sessions:row.rule.minimum_sessions,step:row.rule.reps_step,
   ceiling:row.rule.reps_ceiling,reset:row.rule.reset_reps,weights:row.rule.available_weights.map(v=>numeric(v,locale)+" "+row.rule.unit).join(", ")}));
 }
 const refs={goal:ref(s.goal),plan:ref(s.plan),relationship:ref(s.relationship),authority:ref(s.authority),limits:ref(s.limits),
  selection:ref(s.selection),policy:ref(p),history:ref(data.history)};
 messages.push(fill(c.refs,Object.fromEntries(Object.entries(refs).map(([k,v])=>[k,referenceText(v)]))),c.separate);
 const complete=rows.every(r=>r.status==="available"),changed=rows.some(r=>r.status==="available"&&r.kind!=="maintain");
 let option=null;
 if(complete&&changed){
  const changes=rows.filter(r=>r.kind!=="maintain").flatMap(row=>gate.candidate.rows.filter(r=>r.exercise_id===row.exercise_id).map(r=>({
   workout_id:gate.candidate.workout_id,exercise_id:row.exercise_id,set_index:r.target.index,before:clone(r.target),
   after:{...clone(r.target),reps:{min:row.next_week.reps,max:row.next_week.reps},load:clone(row.next_week.load)},
   rule_id:row.rule.id,reason:row.reason})));
  const payload={version:1,subject_id:s.subject_id,trainer_id:p.trainer_id,base_plan_ref:ref(s.plan),base_plan_hash:hash(s.plan),
   policy_ref:ref(p),relationship_ref:ref(s.relationship),source_refs:refs,bound_to:clone(request.binding),
   basis_hash:basis(request),next_week:clone(p.next_week),required_approvals:clone(p.required_approvals),changes,
   medical_clearance:false,physical_advice_authorized:false,automatic_actions_allowed:false};
  option=freeze({id:"syn-proposal-"+hash(payload).slice(0,40),...payload});
  issued.set(option,freeze({base_plan:clone(s.plan),basis_hash:payload.basis_hash,locale,policy_ref:ref(p)}));
  messages.push(c.review);
 }
 return freeze({...out,status:complete?"proposal":"partial",reason:complete?"source_rule_calculated":"incomplete_exercise_evidence",
  rows,plan_option:option,source_refs:refs,bound_to:clone(request.binding),target_week:clone(p.next_week),messages});
}
const proposalDetails=p=>issued.get(p)||null;
module.exports={propose,prepare:frozen.prepare,assess:frozen.assess,proposalDetails,basis,fill,copy,contract};
