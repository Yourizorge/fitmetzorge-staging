/* Synthetic memory-only simulator. Not an authentication or server authority layer. */
(function(root,factory){const api=factory(typeof module==="object"?require("../training-review-demo/model.js"):root.FMZDemoModel);
if(typeof module==="object")module.exports=api;else root.FMZ6E12Memory=api;})(globalThis,function(model){
"use strict";const clone=model.clone,same=model.same;
function create(profile){
 const baseline=clone(profile),records=[];let workflow=null,reflected=0,gate=null;
 const view=()=>clone({records,workflow:workflow?.view()||null,gate,snapshot:baseline.snapshot,source_hash:baseline.source_hash});
 function register(sets){
  if(workflow?.view().history.length)return {ok:false,reason:"new_plan_source_required"};
  if(!Array.isArray(sets)||sets.length>baseline.draft.sets.length)return {ok:false,reason:"registration_binding"};
  const ids=new Set();
  for(const t of sets){
   const original=baseline.draft.sets.find(x=>x.id===t.id);
   if(!original||ids.has(t.id)||Object.keys(t).sort().join()!==Object.keys(original).sort().join())return {ok:false,reason:"registration_binding"};
   ids.add(t.id);
   for(const key of ["id","subject_id","session_id","snapshot_id","exercise_id","set_index","completed","quality"])
    if(t[key]!==original[key])return {ok:false,reason:"registration_binding"};
   if(t.reps!==null&&(!Number.isSafeInteger(t.reps)||t.reps<0)||!t.load||Object.keys(t.load).sort().join()!=="unit,value"||
    t.load.unit!==original.load.unit||t.load.value!==null&&(!Number.isFinite(t.load.value)||t.load.value<0)||
    t.rir!==null&&(!Number.isInteger(t.rir)||t.rir<0||t.rir>10)||
    t.rpe!==null&&(!Number.isFinite(t.rpe)||t.rpe<1||t.rpe>10||!Number.isInteger(t.rpe*2)))return {ok:false,reason:"set_value"};
  }
  if(workflow)workflow.inject("version_conflict");
  records.push({revision:records.length+1,source_hash:baseline.source_hash,snapshot:clone(baseline.snapshot),sets:clone(sets)});
  reflected=0;return {ok:true,reason:"registration_saved"};
 }
 function reflect(){
  if(!records.length)return {ok:false,reason:"registration_required"};
  if(workflow?.view().history.length)return {ok:false,reason:"new_plan_source_required"};
  if(reflected===records.length)return {ok:true,reason:"existing_reflection"};
  const p=clone(baseline.pack),known=same(records.at(-1).sets,baseline.draft.sets);
  if(!known||gate){p.gate=gate||"incomplete";p.changes=[];p.target=clone(p.plan);p.rows=[];}
  p.basis+=":registration:"+records.length;workflow=model.create(p);reflected=records.length;
  return {ok:true,reason:gate||(!known?"not_example":p.gate||"reflection_ready"),known};
 }
 const command=(e,opts)=>!workflow||reflected!==records.length?{ok:false,reason:"reflection_required"}:workflow.command(e,opts);
 const event=(...args)=>workflow.event(...args);
 const inject=code=>{gate=code;if(workflow)workflow.inject(code);};
 return Object.freeze({view,register,reflect,command,event,inject});
}
return Object.freeze({create});
});
