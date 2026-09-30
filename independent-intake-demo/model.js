/* Memory-only synthetic Route B. No server authorization or real plan writes. */
(function(root){"use strict";
const B=typeof module==="object"?require("../coach-review-demo/model.js"):root.FMZ8Model,C=typeof module==="object"?require("../coach-review-demo/catalog.js"):root.FMZ8Catalog;
const clone=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=c=>{throw Error(c);};
const exact=(x,keys)=>x&&typeof x==="object"&&same(Object.keys(x).sort(),keys.slice().sort());
const extras=["location","machines","disliked","dietLimits","locale","health","consent","records"];
const fields=[...Object.keys(C.defaults),...extras],health=["none","current","recurring","unclassified","self_reported","expired_context","technical"];
const unique=(x,allowed)=>Array.isArray(x)&&new Set(x).size===x.length&&x.every(v=>allowed.includes(v));
function base(i){return Object.fromEntries(Object.keys(C.defaults).map(k=>[k,clone(i[k])]));}
function validate(i,clock){
 if(!exact(i,fields)||fields.some(k=>i[k]===null||i[k]===undefined))fail("incomplete");
 B.validateIntake(base(i));
 if(!["home","gym"].includes(i.location)||!["nl","en","de"].includes(i.locale)||!health.includes(i.health)||typeof i.consent!=="boolean")fail("incomplete");
 if(!unique(i.machines,["cable"])||!unique(i.disliked,B.arrays.favorites)||!unique(i.dietLimits,["medical_diet"]))fail("incomplete");
 if(i.machines.length)fail("machine_rule_missing");
 if(i.dietLimits.length)fail("diet_rule_missing");
 if(i.disliked.some(x=>i.favorites.includes(x)||i.avoided.includes(x)))fail("conflicting_preferences");
 const r=i.records;
 if(!exact(r,["id","revision","subject","at","expires","coverage","sleep","recovery","activity_minutes"])||r.id!=="syn-records"||r.subject!=="syn-intake-member"||!Number.isSafeInteger(r.revision)||r.revision<1||
  !Number.isSafeInteger(r.at)||!Number.isSafeInteger(r.expires)||r.at>clock||r.expires<=clock||r.expires>r.at+86400000||r.coverage!=="complete")fail("record_source");
 if(r.sleep!==i.sleep||r.recovery!==i.recovery)fail("conflicting_records");
 if(!Number.isInteger(r.activity_minutes)||r.activity_minutes<0||r.activity_minutes>1440)fail("incomplete");
 return true;
}
function plan(i,clock){
 validate(i,clock);const p=B.build(base(i));
 // Preferences change only ordering, never catalog quantities or exclusions.
 const es=B.eligibleExercises(i).sort((a,b)=>Number(i.favorites.includes(b.id))-Number(i.favorites.includes(a.id))||
  Number(i.disliked.includes(a.id))-Number(i.disliked.includes(b.id))||Number(b.goals.includes(i.goal))-Number(a.goals.includes(i.goal)));
 for(const session of p.training.sessions)for(let n=0;n<session.exercises.length;n++)session.exercises[n].id=es[n].id;
 validatePlan(p,i);return p;
}
function validatePlan(p,i){
 B.validatePlan(p,base(i));
 if(!same(p.training.secondary,i.secondary)||p.training.goal!==i.goal||p.training.minutes!==i.minutes)fail("plan_intake_conflict");
 if(p.recovery.sleepGoal!==Math.max(i.sleep,C.policy.sleepGoal)||p.recovery.baselineSleep!==i.sleep||p.recovery.checkins!==(i.recovery==="low"?"daily":"after_workout"))fail("recovery_rule");
 for(const session of p.training.sessions)for(const e of session.exercises)if(e.sets!==C.policy.sets[i.experience])fail("sets_rule");
 return true;
}
function references(p,i,source){
 return {catalog:source,training:p.training.sessions.flatMap(s=>s.exercises.map(e=>({day:s.day,exercise:e.id,rule:C.policy.progression,sets_rule:"sets."+i.experience,sets:e.sets,reps:e.reps,rep_range:[1,C.policy.repMax],rest:e.rest,unit:e.unit,load:e.load,
  equipment:C.exercises.find(x=>x.id===e.id).equipment,favorite:i.favorites.includes(e.id),less_liked:i.disliked.includes(e.id)}))),
 nutrition:{rule:C.policy.nutrition,meals:p.nutrition.meals,portion_totals:p.nutrition.totals,energy_requirement_calculated:false,macro_target_calculated:false,portions_unit:"g"},
 recovery:{rule:C.policy.sleep,sleep_record:i.records.sleep,recovery_record:i.records.recovery,activity_minutes_record:i.records.activity_minutes,activity_causes_no_adjustment:true,template:p.recovery}};
}
function create(f,registry){
 const input=clone(f);let counter=0;
 let s={synthetic_only:true,route:"B",subject:"syn-intake-member",clock:input.clock,intake:clone(input.intake),intakeRevision:1,intakeHistory:[{revision:1,intake:clone(input.intake)}],
 source:clone(input.source),status:"intake",draft:null,draftRevision:0,confirmed:false,active:null,version:0,history:[],audit:[],revoked:false,
 healthLatch:health.includes(input.intake.health)&&input.intake.health!=="none",epoch:0,automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false,external_calls:0};
 const view=()=>clone(s),done=new Map();
 function binding(){return JSON.stringify([s.version,s.intakeRevision,s.draftRevision,s.source,s.epoch]);}
 function gate(){
  if(input.subject!=="syn-intake-member"||input.route!=="B"||!input.synthetic_only||!Number.isSafeInteger(s.clock))fail("binding");
  if(!s.intake.consent||s.revoked)fail("consent");
  if(!same(s.source,registry.source)||s.source.policy!==C.policy.id||s.source.catalog!==C.policy.catalog||s.source.nutrition!==C.policy.nutrition||s.source.recovery!==C.policy.sleep||s.source.progression!==C.policy.progression||s.clock>=C.policy.expires)fail("rule_source");
  validate(s.intake,s.clock);
  const g=registry.safety[s.intake.health];if(!g||!g.plan_allowed||s.healthLatch)fail("safety");
 }
 function event(action,data={}){return {id:"syn-command-"+(++counter),route:"B",subject:s.subject,action,data:clone(data),binding:binding()};}
 function pending(p,reason){validatePlan(p,s.intake);s.draft={plan:clone(p),intake:clone(s.intake),intakeRevision:s.intakeRevision,source:clone(s.source),base:s.version,reason,refs:references(p,s.intake,s.source)};s.draftRevision++;s.status="member_pending";s.confirmed=false;}
 function command(e,opt={}){
  const old=clone(s);try{
   if(!exact(e,["id","route","subject","action","data","binding"])||!/^syn-command-[a-zA-Z0-9-]{1,80}$/.test(e.id)||e.subject!==s.subject||e.route!=="B"||!e.data||typeof e.data!=="object")fail("binding");
   const fingerprint=JSON.stringify(e);
   if(done.has(e.id)){if(done.get(e.id)!==fingerprint)fail("duplicate_conflict");return {ok:true,reason:"idempotent",state:view()};}
   if(e.binding!==binding())fail("version_conflict");
   if(!["intake","edit","restore"].includes(e.action)&&!exact(e.data,[]))fail("payload");
   if(e.action==="revoke"){s.revoked=true;s.status="blocked";s.confirmed=false;s.epoch++;}
   else if(e.action==="expire"){s.clock=C.policy.expires;s.status="blocked";s.confirmed=false;s.epoch++;}
   else if(e.action==="stale"){s.source.policy="syn-coach-policy@2";s.status="blocked";s.confirmed=false;s.epoch++;}
   else if(e.action==="intake"){
    if(s.revoked||!s.intake.consent)fail("consent");
    if(!exact(e.data,fields))fail("incomplete");
    s.intake=clone(e.data);s.intakeRevision++;s.intakeHistory.push({revision:s.intakeRevision,intake:clone(s.intake)});s.draft=null;s.confirmed=false;s.status="needs_review";s.epoch++;
    if(health.includes(s.intake.health)&&s.intake.health!=="none")s.healthLatch=true;
   }else if(e.action==="reject"){
    if(!s.draft||!["member_pending","confirmed"].includes(s.status))fail("status");s.status="rejected";s.confirmed=false;
   }else{
    gate();
    if(e.action==="build")pending(plan(s.intake,s.clock),"intake");
    else if(e.action==="edit"){
     if(!s.draft||!["member_pending","confirmed"].includes(s.status))fail("status");
     const d=e.data,p=clone(s.draft.plan);
     if(d.kind==="exercise"&&exact(d,["kind","session","index","id","sets","reps"])){
      if(!Number.isInteger(d.session)||!Number.isInteger(d.index))fail("payload");
      const ex=p.training.sessions[d.session]?.exercises[d.index];if(!ex||!B.eligibleExercises(s.intake).some(x=>x.id===d.id))fail("excluded");
      if(d.sets!==C.policy.sets[s.intake.experience])fail("sets_rule");
      if(!Number.isInteger(d.reps)||d.reps<1||d.reps>C.policy.repMax)fail("reps_rule");
      ex.id=d.id;ex.sets=d.sets;ex.reps=d.reps;
     }else if(d.kind==="meal"&&exact(d,["kind","index","id"])){
      if(!Number.isInteger(d.index))fail("payload");
      const recipe=B.eligibleMeals(s.intake).find(x=>x.id===d.id);if(!recipe||!p.nutrition.meals[d.index])fail("excluded");
      p.nutrition.meals[d.index]={id:recipe.id,at:p.nutrition.meals[d.index].at,items:clone(recipe.items)};p.nutrition.totals=B.totals(p.nutrition.meals);
     }else if(d.kind==="food"&&exact(d,["kind","meal","index","id"])){
      if(!Number.isInteger(d.meal)||!Number.isInteger(d.index))fail("payload");
      const m=p.nutrition.meals[d.meal],item=m?.items[d.index];if(!item||!B.foodAllowed(d.id,s.intake))fail("excluded");
      item.food=d.id;m.id="custom";p.nutrition.totals=B.totals(p.nutrition.meals);
     }else fail("payload");
     pending(p,"member_edit");
    }else if(e.action==="confirm"){
     if(s.status==="confirmed")return {ok:true,reason:"idempotent",state:view()};
     if(s.status!=="member_pending"||!s.draft)fail("status");validatePlan(s.draft.plan,s.intake);s.confirmed=true;s.status="confirmed";
    }else if(e.action==="activate"){
     if(s.status!=="confirmed"||!s.confirmed||!s.draft||s.draft.base!==s.version||s.draft.intakeRevision!==s.intakeRevision||!same(s.draft.source,s.source))fail("version_conflict");
     validatePlan(s.draft.plan,s.intake);s.version++;s.active={version:s.version,plan:clone(s.draft.plan),intakeRevision:s.intakeRevision,refs:clone(s.draft.refs),at:s.clock,reason:s.draft.reason};
     s.history.push(clone(s.active));s.status="active";s.confirmed=false;
    }else if(e.action==="restore"){
     if(!exact(e.data,["version"])||!s.active)fail("status");const h=s.history.find(x=>x.version===e.data.version);if(!h||h.version===s.version)fail("version_conflict");
     pending(h.plan,"restore_v"+h.version);
    }else fail("action");
   }
   if(opt.fault_before_commit)fail("atomic_fault");
   s.clock+=1000;s.audit.push({request:e.id,action:e.action,at:s.clock,from:old.version,to:s.version,intake:s.intakeRevision,draft:s.draftRevision,status:s.status,source:clone(s.source),reason:s.draft?.reason||e.action});
   done.set(e.id,fingerprint);return {ok:true,reason:"success",state:view()};
  }catch(error){s=old;return {ok:false,reason:error.message,state:view()};}
 }
 return Object.freeze({view,event,command,availability:()=>{try{gate();return {ok:true};}catch(e){return {ok:false,reason:e.message};}}});
}
const api={create,validate,validatePlan,plan,references,fields,extras,health};if(typeof module==="object")module.exports=api;else root.FMZ15Model=api;
})(globalThis);
