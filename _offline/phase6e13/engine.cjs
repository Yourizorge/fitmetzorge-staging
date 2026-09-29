"use strict";
if(typeof window!=="undefined")throw Error("offline_only");
const {hash,clone,freeze,exact}=require("../phase6e5/common.cjs"),safety=require("./safety.cjs");
const {copy,format}=require("../../proactive-signals-demo/copy.js");
const METRICS={
 sleep:{unit:"min",method:"declared_sleep_minutes_v1",min:0,max:1440,aggregation:"mean"},
 recovery:{unit:"score_1_10",method:"self_report_1_10_v1",min:1,max:10,aggregation:"mean"},
 nutrition:{unit:"kcal_logged",method:"complete_food_log_sum_v1",min:0,max:100000,aggregation:"mean"},
 training:{unit:"sets",method:"completed_sets_v1",min:0,max:10000,aggregation:"sum"}
};
const POLICY=freeze({id:"syn-observation-policy",revision:1,window_days:3,signal:"exact_nonzero_record_difference",max_cards:20});
const id=x=>typeof x==="string"&&/^syn-[a-z0-9-]{1,70}$/.test(x),int=x=>Number.isSafeInteger(x),ref=x=>exact(x,["id","revision"])&&id(x.id)&&int(x.revision)&&x.revision>0;
const bundleKeys=["synthetic_only","subject_id","id","revision","previous_hash","route","trainer_ref","goal_ref","snapshot_ref","policy","issued_at_ms","valid_until_ms","window_end_ms","source_manifest","rows"];
function evaluate(b,gate,locale="nl"){
 if(!copy[locale])throw Error("locale");
 const c=copy[locale],base={synthetic_only:true,status:"blocked",reason:"invalid_contract",facts:[],proposal:null,
  automatic_actions_allowed:false,physical_advice_authorized:false,trainer_sharing:false,medical_clearance:false,
  source_hash:hash(b),access:{chat:false,history:false,new_analysis:false},feedback:[],messages:[c.invalid],calculations:[],provider_calls:0};
 const finish=(reason,text,extra={})=>freeze({...base,reason,messages:[text,c.scope],...extra});
 if(!safety.isIssued(gate))return finish("unissued_safety",c.context);
 base.access=gate.access;base.safety_binding=clone(gate.binding);base.context_mode=gate.mode;base.feedback=clone(gate.feedback);base.expert_criteria=gate.expert_criteria;
 if(!gate.access.new_analysis)return finish("access_unavailable",c.access);
 if(!exact(b,bundleKeys)||b.synthetic_only!==true||b.subject_id!==gate.subject_id||!id(b.id)||!int(b.revision)||b.revision<1||
  !(b.previous_hash===null||/^[a-f0-9]{64}$/.test(b.previous_hash))||!["HUMAN_REQUIRED","INDEPENDENT"].includes(b.route)||
  !ref(b.goal_ref)||!ref(b.snapshot_ref)||hash(b.policy)!==hash(POLICY))return finish("binding_or_policy",c.binding);
 if(b.route==="HUMAN_REQUIRED"&&!ref(b.trainer_ref)||b.route==="INDEPENDENT"&&b.trainer_ref!==null)return finish("route_authority",c.trainer);
 if(![b.issued_at_ms,b.valid_until_ms,b.window_end_ms].every(int)||b.issued_at_ms>gate.now_ms||b.valid_until_ms<=gate.now_ms||
  b.valid_until_ms<=b.issued_at_ms||b.valid_until_ms-b.issued_at_ms>safety.DAY||b.window_end_ms>gate.now_ms||
  b.window_end_ms%safety.DAY!==0||gate.now_ms-b.window_end_ms>safety.DAY)return finish("stale_or_future_source",c.expired);
 base.binding={subject_id:b.subject_id,bundle_id:b.id,revision:b.revision,goal_ref:clone(b.goal_ref),snapshot_ref:clone(b.snapshot_ref),
  trainer_ref:clone(b.trainer_ref),policy:clone(POLICY),route:b.route,valid_until_ms:b.valid_until_ms};
 if(!Array.isArray(b.rows)||b.rows.length!==24||!Array.isArray(b.source_manifest)||b.source_manifest.length!==24)return finish("incomplete_bundle",c.missing);
 const seen=new Set(),dates=new Set(),manifest=new Map();
 for(const m of b.source_manifest){if(!exact(m,["id","revision","sha256"])||!ref({id:m.id,revision:m.revision})||manifest.has(m.id)||! /^[a-f0-9]{64}$/.test(m.sha256))return finish("manifest_conflict",c.binding);manifest.set(m.id,m);}
 const groups=Object.fromEntries(Object.keys(METRICS).map(k=>[k,[[],[]]]));
 for(const r of b.rows){
  if(!exact(r,["id","revision","subject_id","metric","day_ms","value","unit","method","coverage","quality","goal_ref","snapshot_ref"])||!id(r.id)||!int(r.revision)||r.revision<1||r.subject_id!==b.subject_id||
   !Object.hasOwn(METRICS,r.metric)||seen.has(r.id)||!int(r.day_ms)||r.day_ms%safety.DAY!==0||r.day_ms<b.window_end_ms-6*safety.DAY||r.day_ms>=b.window_end_ms)return finish("row_binding",c.binding);
  seen.add(r.id);const key=r.metric+":"+r.day_ms;if(dates.has(key))return finish("duplicate_day",c.binding);dates.add(key);
  const m=METRICS[r.metric],entry=manifest.get(r.id);
  if(!entry||entry.revision!==r.revision||entry.sha256!==hash(r))return finish("source_hash_conflict",c.binding);
  if(r.coverage!=="complete"||r.quality!=="confirmed"||r.value===null)return finish("incomplete_or_disputed",c.missing);
  if(!int(r.value)||r.value<m.min||r.value>m.max||r.unit!==m.unit||r.method!==m.method||
   hash(r.goal_ref)!==hash(b.goal_ref)||hash(r.snapshot_ref)!==hash(b.snapshot_ref))return finish("not_comparable",c.comparable);
  groups[r.metric][r.day_ms<b.window_end_ms-3*safety.DAY?0:1].push(r);
 }
 for(const [metric,windows]of Object.entries(groups)){
  if(windows.some(w=>w.length!==3))return finish("incomplete_window",c.missing);
  for(const w of windows)w.sort((a,b)=>a.day_ms-b.day_ms);
  const sums=windows.map(w=>w.reduce((n,r)=>n+r.value,0)),denominator=METRICS[metric].aggregation==="sum"?1:3;
  const calculation={metric,unit:METRICS[metric].unit,aggregation:METRICS[metric].aggregation,
   previous:{values:windows[0].map(r=>r.value),sum:sums[0],divisor:denominator,refs:windows[0].map(r=>({id:r.id,revision:r.revision}))},
   current:{values:windows[1].map(r=>r.value),sum:sums[1],divisor:denominator,refs:windows[1].map(r=>({id:r.id,revision:r.revision}))},
   delta_numerator:sums[1]-sums[0],delta_divisor:denominator};
  base.calculations.push(calculation);
  base.facts.push({...calculation,text:format(locale,metric,calculation)});
 }
 const changes=base.facts.filter(f=>f.delta_numerator!==0).map(f=>f.metric);
 if(!gate.access.chat||["current_health","context_missing","clarification"].includes(gate.mode))
  return finish("safety_or_context",c.context,{status:"facts_only",changes});
 if(!changes.length)return finish("no_change",c.unchanged,{status:"unchanged",changes});
 const text=c.proposal+(b.route==="HUMAN_REQUIRED"?" "+c.withTrainer:" "+c.independent);
 return finish("bounded_record_review",text,{status:"candidate_only",changes,proposal:{type:"nonphysical_record_review",text,
  goal_ref:clone(b.goal_ref),snapshot_ref:clone(b.snapshot_ref),source_hash:base.source_hash,requires_plan_approvals_if_later_changed:true}});
}
module.exports={evaluate,METRICS,POLICY,hash,clone,freeze};
