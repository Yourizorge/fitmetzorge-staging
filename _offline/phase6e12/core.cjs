"use strict";
if(typeof window!=="undefined")throw Error("offline_node_only");
const f6=require("../phase6e6/test/fixtures.cjs"),adapter=require("../phase6e7/adapter.cjs");
const model=require("../../training-review-demo/model.js");
const {clone,freeze,hash,exact,same,number,rir,rpe}=require("../phase6e5/common.cjs");
const scenarios=["normal","lb","all_maintain","type_rule","rir_zero","optional_effort_missing","missing_set","missing_rule","ambiguous_rules","step_off_grid","no_trainer","current","self_reported","expired","missing","no_analysis_consent","book_expired","stale_request"];
function fixture(name="normal",locale="nl"){if(!scenarios.includes(name))throw Error("scenario");return f6.setup(name,locale);}
const sourceHash=f=>hash({request:f.request,context:f.context,authority:f.authority});
function create(f=fixture()){
 const source=sourceHash(f),request=clone(f.request),h=request.base.history;
 if(!h?.sessions?.length)throw Error("source_history_required");
 const original=clone(h.sessions.at(-1)),snapshot=clone(original.snapshot);
 const subject=request.base.base.sources.subject_id,workspace="syn-workout-workspace";
 let records=[],controller=null,issued=null;
 const draft=()=>({synthetic_only:true,subject_id:subject,workspace_id:workspace,id:"syn-registration",
  revision:records.length+1,session_id:original.id,snapshot_id:snapshot.id,source_hash:source,
  snapshot_hash:hash(snapshot),sets:clone(original.sets)});
 const view=()=>freeze({source_hash:source,snapshot:clone(snapshot),records:clone(records),workflow:controller?.view()||null});
 const invalid=reason=>freeze({ok:false,reason,view:view()});
 function register(input){
  if(sourceHash(f)!==source){if(controller)controller.inject("version_conflict");return invalid("source_changed");}
  if(controller?.view().history.length)return invalid("new_plan_source_required");
  if(!exact(input,Object.keys(draft()))||input.synthetic_only!==true||input.subject_id!==subject||
   input.workspace_id!==workspace||input.id!=="syn-registration"||input.revision!==records.length+1||
   input.session_id!==original.id||input.snapshot_id!==snapshot.id||input.source_hash!==source||input.snapshot_hash!==hash(snapshot))
   return invalid("registration_binding");
  if(!Array.isArray(input.sets)||input.sets.length>snapshot.exercises.reduce((n,e)=>n+e.sets.length,0))return invalid("sets_shape");
  const seen=new Set();
  for(const t of input.sets){
   const fields=["id","subject_id","session_id","snapshot_id","exercise_id","set_index","completed","reps","load","rir","rpe","quality"];
   const e=snapshot.exercises.find(e=>e.exercise_id===t?.exercise_id),planned=e?.sets.find(s=>s.index===t.set_index);
   const old=original.sets.find(s=>s.exercise_id===t?.exercise_id&&s.set_index===t.set_index);
   const key=t?.exercise_id+":"+t?.set_index;
   if(!exact(t,fields)||!planned||!old||seen.has(key)||t.id!==old.id||t.subject_id!==subject||t.session_id!==original.id||
    t.snapshot_id!==snapshot.id||typeof t.completed!=="boolean"||!["confirmed","disputed"].includes(t.quality))return invalid("set_binding");
   seen.add(key);
   if(t.reps!==null&&(!Number.isSafeInteger(t.reps)||t.reps<0||t.reps>1000000000)||
    !exact(t.load,["value","unit"])||t.load.value!==null&&!number(t.load.value)||
    t.load.unit!==planned.load.unit||!["kg","lb"].includes(t.load.unit)||
    t.rir!==null&&!rir(t.rir)||t.rpe!==null&&!rpe(t.rpe))return invalid("set_value");
  }
  const record=freeze({...clone(input),previous_hash:records.at(-1)?.hash||null});
  const next=freeze({...record,hash:hash(record)});
  if(controller)controller.inject("version_conflict");
  records=[...records,next];issued=null;
  return freeze({ok:true,reason:"registration_saved",registration:clone(next)});
 }
 function reflect(){
  if(sourceHash(f)!==source){if(controller)controller.inject("version_conflict");return invalid("source_changed");}
  if(!records.length)return invalid("registration_required");
  if(controller?.view().history.length)return invalid("new_plan_source_required");
  const current=records.at(-1);
  if(issued?.hash===current.hash)return issued.response;
  const fresh=clone(request);
  fresh.base.history.revision=h.revision+records.length;
  fresh.base.expected_progression.history_ref.revision=fresh.base.history.revision;
  const session=fresh.base.history.sessions.at(-1);
  session.revision=original.revision+records.length;session.sets=clone(current.sets);
  const derived={...f,request:fresh};
  const result=f6.engine.propose(fresh,f.context,f.authority);
  const pack=adapter.fromFixture(derived,"registration-"+current.revision);
  controller=model.create(pack);
  const response=freeze({ok:true,registration_ref:{id:current.id,revision:current.revision,hash:current.hash},
   source_hash:source,snapshot_hash:hash(snapshot),result,pack});
  issued={hash:current.hash,response};
  return response;
 }
 function command(event,options={}){
  if(!controller||!issued)return invalid("reflection_required");
  if(sourceHash(f)!==source){controller.inject("version_conflict");return invalid("source_changed");}
  if(issued.hash!==records.at(-1)?.hash)return invalid("registration_changed");
  return controller.command(event,options);
 }
 const event=(...args)=>{if(!controller)throw Error("reflection_required");return controller.event(...args);};
 return Object.freeze({draft,register,reflect,view,command,event});
}
module.exports={fixture,create,scenarios,sourceHash,clone,hash};
