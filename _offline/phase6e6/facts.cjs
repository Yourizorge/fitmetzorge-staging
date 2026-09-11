"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,id,integer,number,reference,ref,nullable,rir,rpe,reps,clone,freeze,same}=require("../phase6e5/common.cjs");
const {view}=require("../phase6e4/context.cjs");
function collect(base,ctx,authority){
 const none={observations:[],omitted:[],meaning:"historical_records_only_not_current_prescription"};
 let v;try{v=view(ctx,base?.binding,authority,base?.locale);}catch{return freeze(none);}
 if(!v.valid||!v.gate.access.new_analysis||!v.gate.access.history)return freeze(none);
 const h=base?.history,subject=ctx.binding.subject_id,now=ctx.evaluated_at_ms;
 if(!h||h.subject_id!==subject||!reference(ref(h))||h.read_at_ms!==now||!same(base.expected_progression?.history_ref,ref(h))||
   !Array.isArray(h.sessions)||h.sessions.length>100)return freeze(none);
 const out={...none,history_ref:ref(h)},seen=new Set(),snapshots=new Set(),logIds=new Set();
 const counts=values=>{const m=new Map();for(const value of values)m.set(value,(m.get(value)||0)+1);return m;};
 const sessionCounts=counts(h.sessions.map(x=>x?.id)),snapshotCounts=counts(h.sessions.map(x=>x?.snapshot?.id));
 const allLogs=h.sessions.flatMap(x=>Array.isArray(x?.sets)?x.sets.slice(0,10000):[]);
 const logCounts=counts(allLogs.map(x=>x?.id));
 for(const x of h.sessions){
  const sn=x?.snapshot;
  if(!id(x?.id)||sessionCounts.get(x.id)!==1||seen.has(x.id)||!reference(ref(x))||x.subject_id!==subject||!sn||snapshotCounts.get(sn.id)!==1||snapshots.has(sn.id)||!id(sn.id)||sn.subject_id!==subject||sn.session_id!==x.id||
   !id(x.workout_id)||sn.workout_id!==x.workout_id||!reference(sn.plan_ref)||!reference(sn.goal_ref)||
   !integer(x.started_at_ms)||!integer(x.completed_at_ms)||!integer(sn.captured_at_ms)||
   sn.captured_at_ms>x.started_at_ms||x.started_at_ms>x.completed_at_ms||x.completed_at_ms>now||
   !Array.isArray(sn.exercises)||sn.exercises.length>100||!Array.isArray(x.sets)||x.sets.length>10000){
    out.omitted.push("unreliable_session");continue;
  }
  seen.add(x.id);snapshots.add(sn.id);
  for(const t of x.sets){
   const es=sn.exercises.filter(e=>e?.exercise_id===t?.exercise_id),e=es[0],targets=Array.isArray(e?.sets)?e.sets.filter(p=>p?.index===t?.set_index):[],p=targets[0];
   const duplicate=x.sets.filter(y=>y?.id===t?.id||y?.exercise_id===t?.exercise_id&&y?.set_index===t?.set_index).length!==1;
   if(!exact(t,["id","subject_id","session_id","snapshot_id","exercise_id","set_index","completed","reps","load","rir","rpe","quality"])||
    !id(t.id)||duplicate||logCounts.get(t.id)!==1||logIds.has(t.id)||t.subject_id!==subject||t.session_id!==x.id||t.snapshot_id!==sn.id||
    !id(t.exercise_id)||!integer(t.set_index)||t.set_index<1||t.quality!=="confirmed"||t.completed!==true||
    es.length!==1||!integer(e.catalog_revision)||!id(e.variant_id)||!id(e.equipment_id)||targets.length!==1||
    !reps(p.reps)||!exact(p.load,["value","unit"])||!number(p.load.value)||!["kg","lb"].includes(p.load.unit)||
    !nullable(t.reps,n=>integer(n)&&n<=1000000000)||!exact(t.load,["value","unit"])||!nullable(t.load.value,number)||!["kg","lb"].includes(t.load.unit)||
    !nullable(t.rir,rir)||!nullable(t.rpe,rpe)){out.omitted.push("unreliable_set");continue;}
   logIds.add(t.id);
   out.observations.push({session_ref:ref(x),snapshot_id:sn.id,plan_ref:clone(sn.plan_ref),goal_ref:clone(sn.goal_ref),
    exercise_ref:{id:e.exercise_id,revision:e.catalog_revision},set_id:t.id,set_index:t.set_index,
    historical_target:{reps:clone(p.reps),load:clone(p.load)},recorded:{reps:t.reps,load:clone(t.load),rir:t.rir,rpe:t.rpe},
    complete:t.reps!==null&&t.load.value!==null,effort_is_self_report:true});
  }
 }
 return freeze(out);
}
module.exports={collect};
