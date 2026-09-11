"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const c=require("../phase6e5/common.cjs");
const {exact,id,integer,number,reference,list,unique,same,clone,ref,hash}=c;
const fields=["set_count","unit","minimum_sessions","comparable_plan_refs","comparable_goal_refs","reps_step","reps_min","reps_max","reset_reps","weight_step","available_weights","rir","rpe","forbidden_effort_pairs","maintain_when"];
function decimal(n){
 if(!number(n)||!/^\d+(?:\.\d{1,6})?$/.test(String(n)))return null;
 const [a,b=""]=String(n).split(".");return BigInt(a)*1000000n+BigInt(b.padEnd(6,"0"));
}
function resolve(request,now){
 const b=request.rulebook,p=request.base?.policy,s=request.base?.base?.sources;
 const bad=(reason,exercise_id=null)=>({valid:false,reason,exercise_id});
 if(!s?.relationship)return bad("trainer_missing");
 if(b===null)return bad("rulebook_missing");
 if(!exact(b,["id","revision","subject_id","trainer_id","policy_ref","status","captured_at_ms","valid_from_ms","valid_until_ms","bindings","rules"])||
  !reference(ref(b))||!id(b.subject_id)||!id(b.trainer_id)||!reference(b.policy_ref)||
  !integer(b.captured_at_ms)||!integer(b.valid_from_ms)||(b.valid_until_ms!==null&&!integer(b.valid_until_ms))||
  !list(b.bindings,100,x=>exact(x,["exercise_ref","workout_id","variant_id","equipment_id","type_ref"])&&reference(x.exercise_ref)&&id(x.workout_id)&&id(x.variant_id)&&id(x.equipment_id)&&(x.type_ref===null||reference(x.type_ref)))||
  !list(b.rules,100,x=>exact(x,["id","revision","status","selector","parameters"])&&reference(ref(x))&&
   exact(x.selector,["kind","ref"])&&["exercise","type"].includes(x.selector.kind)&&reference(x.selector.ref)&&exact(x.parameters,fields))||
  !unique(b.rules.map(x=>x.id))||!unique(b.bindings.map(x=>x.exercise_ref.id)))return bad("rulebook_shape");
 if(!reference(request.expected_rulebook)||!same(request.expected_rulebook,ref(b)))return bad("rulebook_version");
 if(b.subject_id!==s.subject_id||b.trainer_id!==s.relationship.trainer_id)return bad("rulebook_identity");
 if(!p||!same(b.policy_ref,ref(p)))return bad("rulebook_policy");
 if(b.status!=="active"||b.captured_at_ms>now||b.valid_from_ms>now||b.valid_until_ms!==null&&(b.valid_until_ms<=now||b.valid_until_ms<=b.valid_from_ms))return bad("rulebook_not_current");
 if(!Array.isArray(p.rules)||p.rules.length!==0)return bad("dual_rule_authority");
 const selected=s.plan?.options?.find(x=>x.id===s.selection?.option_id);
 if(!selected)return bad("current_plan_missing");
 if(b.bindings.length!==selected.exercises.length)return bad("binding_coverage");
 const resolved=[],provenance=[];
 for(const exercise of selected.exercises){
  const binding=b.bindings.find(x=>same(x.exercise_ref,{id:exercise.exercise_id,revision:exercise.catalog_revision}));
  if(!binding||binding.workout_id!==selected.workout_id)return bad("exercise_binding",exercise.exercise_id);
  const matches=b.rules.filter(x=>same(x.selector.ref,x.selector.kind==="exercise"?binding.exercise_ref:binding.type_ref));
  if(matches.length!==1)return bad(matches.length?"ambiguous_rules":"missing_rule",exercise.exercise_id);
  const rule=matches[0],q=rule.parameters;
  if(rule.status!=="active")return bad("rule_not_current",exercise.exercise_id);
  if(!integer(q.reps_min)||q.reps_min<1||!integer(q.reps_max)||q.reps_min>q.reps_max||
    !integer(q.reset_reps)||q.reset_reps<q.reps_min||q.reset_reps>q.reps_max||
    !integer(q.reps_step)||q.reps_step<1||!integer(q.set_count)||q.set_count!==exercise.sets.length||
    !["kg","lb"].includes(q.unit)||decimal(q.weight_step)===null||q.weight_step===0||
    !list(q.available_weights,1000,x=>decimal(x)!==null)||q.available_weights.length===0)return bad("rule_parameters",exercise.exercise_id);
  if(q.available_weights.some((x,i,a)=>i>0&&decimal(x)-decimal(a[i-1])!==decimal(q.weight_step)))return bad("weight_step_conflict",exercise.exercise_id);
  if(exercise.sets.some(t=>t.reps.min<q.reps_min||t.reps.max>q.reps_max||t.load.unit!==q.unit))return bad("current_target_conflict",exercise.exercise_id);
  if(exercise.sets.some(t=>t.reps.min<q.reps_max&&t.reps.min+q.reps_step>q.reps_max))return bad("rep_step_conflict",exercise.exercise_id);
  const parameters=clone(q);delete parameters.reps_min;delete parameters.reps_max;delete parameters.weight_step;
  resolved.push({...parameters,id:"syn-resolved-"+hash({book:ref(b),rule:ref(rule),exercise:binding.exercise_ref}).slice(0,36),
   exercise_id:exercise.exercise_id,catalog_revision:exercise.catalog_revision,workout_id:binding.workout_id,
   variant_id:binding.variant_id,equipment_id:binding.equipment_id,reps_ceiling:q.reps_max});
  provenance.push({exercise_id:exercise.exercise_id,rulebook_ref:ref(b),rule_ref:ref(rule),selector:clone(rule.selector),
   binding:clone(binding),parameters:clone(q),authority_kind:"synthetic_declared_trainer_rule_not_live_attestation"});
 }
 const projected=clone(request.base);projected.policy.rules=resolved;
 return {valid:true,projected,provenance};
}
module.exports={resolve,decimal};
