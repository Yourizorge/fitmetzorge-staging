"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const {exact,id,integer,canonical}=require("../phase6e1/common.cjs");
const goals=require("../phase6e3/contract.json").goals;
const meta=["id","revision","subject_id","status","captured_at_ms","valid_from_ms","valid_until_ms"];
const names=["goal","plan","relationship","authority","limits","selection"];
const ref=x=>exact(x,["id","revision"])&&id(x.id)&&integer(x.revision);
const reference=x=>({id:x.id,revision:x.revision});
const same=(a,b)=>canonical(a)===canonical(b);
const nullable=(x,test)=>x===null||test(x);
const number=x=>typeof x==="number"&&Number.isFinite(x)&&x>=0&&x<=1000000000;
const range=x=>exact(x,["min","max"])&&number(x.min)&&number(x.max)&&x.min<=x.max;
const reps=x=>range(x)&&integer(x.min)&&integer(x.max);
const rir=x=>integer(x)&&x<=10;
const rpe=x=>number(x)&&x>=1&&x<=10&&Number.isInteger(x*2);
const unit=x=>x===null||typeof x==="string"&&/^[a-z_]{1,16}$/.test(x);
const labels=x=>exact(x,["nl","en","de"])&&Object.values(x).every(v=>typeof v==="string"&&v.trim()===v&&v.length>0&&v.length<=120&&!/[\u0000-\u001f<>]/.test(v));
const list=(x,max,test)=>Array.isArray(x)&&x.length<=max&&x.every(test);
const unique=x=>new Set(x).size===x.length;
const load=x=>exact(x,["value","unit"])&&nullable(x.value,number)&&unit(x.unit);
const set=x=>exact(x,["index","reps","load","rir","rpe"])&&integer(x.index)&&x.index>0&&nullable(x.reps,reps)&&load(x.load)&&nullable(x.rir,rir)&&nullable(x.rpe,rpe);
const exercise=x=>exact(x,["exercise_id","catalog_revision","sets"])&&id(x.exercise_id)&&integer(x.catalog_revision)&&list(x.sets,100,set)&&x.sets.length>0&&x.sets.every((s,i)=>s.index===i+1);
const option=x=>exact(x,["id","workout_id","labels","exercises"])&&id(x.id)&&id(x.workout_id)&&labels(x.labels)&&list(x.exercises,100,exercise)&&x.exercises.length>0&&unique(x.exercises.map(e=>e.exercise_id));
const rule=x=>exact(x,["id","workout_id","exercise_id","set_index","reps","load","allowed"])&&id(x.id)&&id(x.workout_id)&&id(x.exercise_id)&&integer(x.set_index)&&x.set_index>0&&
  nullable(x.reps,reps)&&exact(x.load,["min","max","unit"])&&nullable(x.load.min,number)&&nullable(x.load.max,number)&&
  (x.load.min===null||x.load.max===null||x.load.min<=x.load.max)&&unit(x.load.unit)&&typeof x.allowed==="boolean";
const tuple=x=>x.workout_id+":"+x.exercise_id+":"+x.set_index;
function versioned(x,extra){
  return exact(x,[...meta,...extra])&&id(x.id)&&integer(x.revision)&&id(x.subject_id)&&
    ["active","inactive","revoked"].includes(x.status)&&integer(x.captured_at_ms)&&integer(x.valid_from_ms)&&
    nullable(x.valid_until_ms,integer)&&(x.valid_until_ms===null||x.valid_until_ms>x.valid_from_ms);
}
function validate(s,subject,now,expected){
  const bad=(reason,path="sources",status="invalid_input")=>({valid:false,status,reason,path});
  const absent=(reason,path)=>bad(reason,path,"unavailable");
  if(!exact(s,["synthetic_only","subject_id","readset",...names,"catalog"])||s.synthetic_only!==true||!id(subject)||s.subject_id!==subject||!integer(now))return bad("identity_or_source_envelope");
  if(!exact(s.readset,["id","revision","subject_id","read_at_ms","current_refs"])||!ref(reference(s.readset))||s.readset.subject_id!==subject||
    !integer(s.readset.read_at_ms)||!exact(s.readset.current_refs,names)||!Object.values(s.readset.current_refs).every(ref)||!ref(expected))return bad("readset_shape");
  if(s.readset.read_at_ms>now)return bad("future_readset");
  if(s.readset.read_at_ms!==now||!same(reference(s.readset),expected))return absent("stale_readset","readset");
  const checks={
    goal:x=>versioned(x,["code"])&&typeof x.code==="string"&&/^[a-z_]{1,40}$/.test(x.code),
    plan:x=>versioned(x,["trainer_id","authority_ref","goal_link","options"])&&id(x.trainer_id)&&ref(x.authority_ref)&&
      (x.goal_link===null||exact(x.goal_link,["goal_ref","basis","at_ms"])&&ref(x.goal_link.goal_ref)&&typeof x.goal_link.basis==="string"&&integer(x.goal_link.at_ms))&&
      list(x.options,20,option)&&unique(x.options.map(o=>o.id))&&unique(x.options.map(o=>o.workout_id)),
    relationship:x=>versioned(x,["trainer_id","role"])&&id(x.trainer_id)&&typeof x.role==="string",
    authority:x=>versioned(x,["trainer_id","relationship_ref","plan_ref","goal_ref","workout_ids","permission","member_source_consent","attestation"])&&
      id(x.trainer_id)&&ref(x.relationship_ref)&&ref(x.plan_ref)&&ref(x.goal_ref)&&list(x.workout_ids,20,id)&&unique(x.workout_ids)&&
      typeof x.permission==="string"&&typeof x.member_source_consent==="boolean"&&x.attestation==="synthetic_declared_only",
    limits:x=>versioned(x,["trainer_id","authority_ref","plan_ref","goal_ref","coverage","rules"])&&id(x.trainer_id)&&
      ref(x.authority_ref)&&ref(x.plan_ref)&&ref(x.goal_ref)&&["complete","partial"].includes(x.coverage)&&list(x.rules,2000,rule)&&unique(x.rules.map(r=>r.id))&&unique(x.rules.map(tuple)),
    selection:x=>versioned(x,["trainer_id","authority_ref","plan_ref","goal_ref","option_id","basis"])&&id(x.trainer_id)&&
      ref(x.authority_ref)&&ref(x.plan_ref)&&ref(x.goal_ref)&&nullable(x.option_id,id)&&typeof x.basis==="string"
  };
  for(const name of names)if(s[name]!==null){
    if(!checks[name](s[name]))return bad("source_shape",name);
    if(s[name].subject_id!==subject)return bad("identity_mismatch",name);
    if(s[name].captured_at_ms>now)return bad("future_source",name);
  }
  if(!list(s.catalog,2000,x=>exact(x,["id","revision","labels"])&&ref(reference(x))&&labels(x.labels))||!unique(s.catalog.map(x=>x.id+":"+x.revision)))return bad("catalog_shape","catalog");
  for(const name of names)if(s[name]===null)return absent("missing_"+name,name);
  const {goal:g,plan:p,relationship:r,authority:a,limits:l,selection:n}=s;
  if([p,r,l,n].some(x=>x.trainer_id!==a.trainer_id))return bad("trainer_identity_mismatch");
  for(const name of names){
    const x=s[name];
    if(!same(reference(x),s.readset.current_refs[name]))return absent("stale_sources",name);
    if(x.status!=="active")return absent("source_"+x.status,name);
    if(x.valid_from_ms>now||x.valid_until_ms!==null&&x.valid_until_ms<=now)return absent("source_not_current",name);
  }
  if(r.role!=="trainer"||a.permission!=="propose_existing_next_option"||!a.member_source_consent)return absent("trainer_authority_unavailable","authority");
  const bindings=[[p.authority_ref,a],[a.relationship_ref,r],[a.plan_ref,p],[a.goal_ref,g],[l.authority_ref,a],[l.plan_ref,p],[l.goal_ref,g],[n.authority_ref,a],[n.plan_ref,p],[n.goal_ref,g]];
  if(bindings.some(([x,y])=>!same(x,reference(y))))return absent("source_binding_conflict","current_refs");
  if(!Object.hasOwn(goals,g.code))return absent("goal_unavailable","goal");
  if(!p.goal_link||p.goal_link.basis!=="explicit_current_workout_goal"||!same(p.goal_link.goal_ref,reference(g))||
    p.goal_link.at_ms>p.captured_at_ms||p.goal_link.at_ms<g.captured_at_ms||
    p.goal_link.at_ms<g.valid_from_ms)return absent("goal_link_unavailable","plan.goal_link");
  if(n.option_id===null)return absent("next_option_missing","selection");
  const chosen=p.options.find(o=>o.id===n.option_id);
  if(!chosen)return bad("option_binding","selection.option_id");
  if(n.basis!=="trainer_explicit_next_option"||!a.workout_ids.includes(chosen.workout_id))return absent("next_option_not_authorized","selection");
  const allKeys=new Set(p.options.flatMap(o=>o.exercises.flatMap(e=>e.sets.map(t=>tuple({workout_id:o.workout_id,exercise_id:e.exercise_id,set_index:t.index})))));
  if(l.rules.some(rule=>!allKeys.has(tuple(rule))))return bad("set_binding","limits.rules");
  if(l.coverage!=="complete")return absent("incomplete_limits","limits");
  const rows=[];
  for(const e of chosen.exercises){
    const catalog=s.catalog.find(c=>c.id===e.exercise_id&&c.revision===e.catalog_revision);
    if(!catalog)return absent("catalog_unavailable","catalog");
    for(const target of e.sets){
      const key=tuple({workout_id:chosen.workout_id,exercise_id:e.exercise_id,set_index:target.index}),boundary=l.rules.find(r=>tuple(r)===key);
      if(!boundary)return absent("missing_set_limit",key);
      if(!boundary.allowed)return absent("trainer_forbids",key);
      if(target.reps===null||target.load.value===null||boundary.reps===null||boundary.load.min===null||boundary.load.max===null)return absent("missing_set_data",key);
      if(!["kg","lb"].includes(target.load.unit)||!["kg","lb"].includes(boundary.load.unit))return absent("unknown_unit",key);
      if(target.load.unit!==boundary.load.unit)return absent("mixed_units",key);
      if(target.reps.min<boundary.reps.min||target.reps.max>boundary.reps.max||target.load.value<boundary.load.min||target.load.value>boundary.load.max)return absent("outside_trainer_limits",key);
      rows.push({exercise_id:e.exercise_id,catalog_ref:reference(catalog),labels:catalog.labels,target,boundary});
    }
  }
  if(!rows.length)return absent("missing_set_data","plan.options");
  if(new Set(rows.map(r=>r.target.load.unit)).size>1)return absent("mixed_units","selected_option_units");
  return {valid:true,chosen,rows,goal:g,source_refs:Object.fromEntries(names.map(k=>[k,reference(s[k])])),readset_ref:reference(s.readset)};
}
module.exports={validate,reference,tuple};
