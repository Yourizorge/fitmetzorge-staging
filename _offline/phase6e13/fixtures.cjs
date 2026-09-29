"use strict";
const {METRICS,POLICY,hash,clone}=require("./engine.cjs"),safety=require("./safety.cjs");
const scenarios=["changes","sleep_only","recovery_only","nutrition_only","training_only","unchanged","zero","independent","missing","partial","conflict","expired_source","no_trainer","current","unclassified","self_reported","recurring","expired_context","missing_context","technical","unclear","consent_revoked","entitlement_revoked"];
const safetyNames=new Set(["current","unclassified","self_reported","recurring","expired_context","missing_context","technical","unclear","consent_revoked","entitlement_revoked"]);
function seal(b){b.source_manifest=b.rows.map(r=>({id:r.id,revision:r.revision,sha256:hash(r)}));return b;}
function fixture(name="changes",locale="nl"){
 if(!scenarios.includes(name))throw Error("fixture");
 const gate=safety.create(safetyNames.has(name)?name:"ordinary",locale),end=Math.floor(gate.now_ms/safety.DAY)*safety.DAY;
 const b={synthetic_only:true,subject_id:"syn-owner",id:"syn-observations",revision:1,previous_hash:null,route:name==="independent"?"INDEPENDENT":"HUMAN_REQUIRED",
  trainer_ref:name==="independent"?null:{id:"syn-trainer",revision:2},goal_ref:{id:"syn-consistent-recording-goal",revision:2},snapshot_ref:{id:"syn-workout-plan",revision:3},
  policy:clone(POLICY),issued_at_ms:gate.now_ms,valid_until_ms:gate.now_ms+safety.DAY,window_end_ms:end,source_manifest:[],rows:[]};
 const values={sleep:[450,450,450,360,360,360],recovery:[8,8,8,6,6,6],nutrition:[2200,2200,2200,1900,1900,1900],training:[6,6,6,4,4,4]};
 for(const [metric,m]of Object.entries(METRICS))for(let day=0;day<6;day++){
  const value=name==="unchanged"||name.endsWith("_only")&&metric!==name.replace("_only","")?values[metric][day%3]:values[metric][day];
  b.rows.push({id:"syn-"+metric+"-"+day,revision:1,subject_id:b.subject_id,metric,day_ms:end-(6-day)*safety.DAY,value,
   unit:m.unit,method:m.method,coverage:"complete",quality:"confirmed",goal_ref:clone(b.goal_ref),snapshot_ref:clone(b.snapshot_ref)});
 }
 if(name==="zero")for(const r of b.rows)if(r.metric==="sleep"||r.metric==="training")r.value=0;
 if(name==="missing")b.rows[0].value=null;
 if(name==="partial")b.rows[14].coverage="partial";
 if(name==="conflict")b.rows[23].snapshot_ref.revision++;
 if(name==="expired_source")b.valid_until_ms=gate.now_ms;
 if(name==="no_trainer")b.trainer_ref=null;
 return {bundle:seal(b),gate};
}
function corrected(f){const b=clone(f.bundle);b.revision++;b.previous_hash=hash(f.bundle);b.rows=b.rows.map(r=>({...r,revision:r.revision+1,value:r.metric==="sleep"?420:r.value}));return {...f,bundle:seal(b)};}
function restore(current,original){const b=clone(original.bundle);b.revision=current.bundle.revision+1;b.previous_hash=hash(current.bundle);
 b.rows=b.rows.map(r=>({...r,revision:current.bundle.rows.find(q=>q.id===r.id).revision+1}));return {...current,bundle:seal(b)};}
module.exports={scenarios,fixture,corrected,restore,seal};
