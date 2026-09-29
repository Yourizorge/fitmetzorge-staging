"use strict";
const F=require("../phase6e13/fixtures.cjs"),S=require("../phase6e13/safety.cjs"),{catalogs,clone,hash}=require("./catalog.cjs");
const scenarios=["a_progression","a_maintain","a_lb","b_schedule","nutrition_partial","recovery_reflection","calorie_rule_missing","missing_rule","ambiguous_rule","no_trainer","invalid_option","missing_value","expired","conflict","revoked","current","self_reported","recurring","unclassified","expired_context","technical","b_current","b_partial","b_no_rule"];
const safetyMap={current:"current",b_current:"current",self_reported:"self_reported",recurring:"recurring",unclassified:"unclassified",expired_context:"expired_context",technical:"technical",revoked:"consent_revoked"};
function fixture(name="a_progression",locale="nl"){
 if(!scenarios.includes(name))throw Error("scenario");
 const b=name.startsWith("b_"),template=b?"b_schedule":["a_maintain","a_lb"].includes(name)?name:"a_progression",cat=catalogs[template];
 const f=F.fixture(safetyMap[name]||"changes",locale),bundle=f.bundle,gate=f.gate;
 const goal={id:b?"syn-independent-strength":"syn-trainer-strength",revision:1},planRef={id:b?"syn-independent-plan":"syn-trainer-plan",revision:b?1:3};
 bundle.route=b?"INDEPENDENT":"HUMAN_REQUIRED";bundle.trainer_ref=b?null:{id:"syn-trainer",revision:1};bundle.goal_ref=goal;bundle.snapshot_ref=planRef;
 const end=bundle.window_end_ms,days=[];
 for(let i=7;i>0;i--){const at=end-i*S.DAY,weekday=["sun","mon","tue","wed","thu","fri","sat"][new Date(at).getUTCDay()];if(b&&cat.before.intake.days.includes(weekday))days.push({id:"syn-week-session-"+i,day_ms:at,planned:true,completed_sets:6,planned_sets:6,complete:true});}
 if(b)days.at(-1).completed_sets=0;
 else {
  const offset=gate.now_ms-cat.source_clock;
  for(const h of cat.history.sessions)days.push({id:h.id,day_ms:Math.floor((h.completed_at_ms+offset)/S.DAY)*S.DAY,planned:true,
   completed_sets:h.sets.filter(x=>x.completed).length,planned_sets:6,complete:true});
 }
 for(const r of bundle.rows){
  r.goal_ref=clone(goal);r.snapshot_ref=clone(planRef);
  if(r.metric==="training")r.value=days.filter(s=>s.day_ms===r.day_ms).reduce((n,s)=>n+s.completed_sets,0);
 }
 if(name==="nutrition_partial"||name==="b_partial")bundle.rows.find(r=>r.metric==="nutrition").coverage="partial";
 if(name==="missing_value")bundle.rows[0].value=null;
 const source={synthetic_only:true,subject_id:"syn-owner",route:b?"B":"A",id:"syn-adjustment-source",revision:1,previous_hash:null,
  issued_at_ms:gate.now_ms,valid_until_ms:gate.now_ms+S.DAY,goal_ref:goal,plan_ref:planRef,template,
  trainer_ref:b?null:{id:"syn-trainer",revision:1},catalog_ref:{id:cat.id,revision:cat.revision,sha256:cat.source_sha256},
  plan:clone(cat.before),option:clone(cat.after),kind:name==="nutrition_partial"||name==="b_partial"?"registration":name==="recovery_reflection"?"reflection":name==="calorie_rule_missing"?"nutrition_change":"plan",
  rules:[{id:b?"syn-missed-catalog-binding":"syn-explicit-trainer-binding",revision:1,status:"active",signal:"training",option:cat.id}],
  sessions:days,signal: F.seal(bundle)};
 if(name==="missing_rule"||name==="b_no_rule"||name==="calorie_rule_missing")source.rules=[];
 if(name==="ambiguous_rule")source.rules.push({...clone(source.rules[0]),id:"syn-conflicting-rule"});
 if(name==="no_trainer")source.trainer_ref=null;
 if(name==="invalid_option")source.option.training.exercises[0].sets[0].reps.min=999;
 if(name==="expired")source.valid_until_ms=gate.now_ms;
 if(name==="conflict")source.plan_ref.revision++;
 return {source,gate};
}
function corrected(f){
 const source=clone(f.source);source.previous_hash=hash(f.source);source.revision++;
 source.signal=F.corrected({bundle:source.signal,gate:f.gate}).bundle;
 // A timing correction supplies no missing measurement.
 for(let i=0;i<source.signal.rows.length;i++)if(f.source.signal.rows[i].value===null)source.signal.rows[i].value=null;
 source.signal=F.seal(source.signal);
 return {source,gate:f.gate};
}
module.exports={scenarios,fixture,corrected};
