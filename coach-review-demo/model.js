/* In-memory, deterministic independent-route contract. Never a live authority. */
(function(root){"use strict";
const C=typeof module==="object"&&module.exports?require("./catalog.js"):root.FMZ8Catalog;
const clone=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const days=["mon","tue","wed","thu","fri","sat","sun"],rank={none:0,microwave:1,full:2};
const enums={goal:["strength","muscle","consistency"],experience:["beginner","regular"],minutes:[20,30,45,60],diet:["plant","omnivore"],meals:[3,4],kitchen:Object.keys(rank),budget:["low","medium"],rhythm:["early","late"],sleep:[6,7,8],recovery:["low","okay"],unit:["kg","lb"]};
const arrays={secondary:["mobility","endurance"],days,equipment:["mat","dumbbell","band"],favorites:C.exercises.map(x=>x.id),avoided:C.exercises.map(x=>x.id),movement:["deep_knee","overhead"],allergies:["nuts","dairy","soy","gluten"],excludedFoods:C.foods.map(x=>x.id)};
function fail(code){throw new Error(code);}
function validateIntake(i){
 if(!i||!same(Object.keys(i).sort(),Object.keys(C.defaults).sort()))fail("incomplete");
 for(const [k,v]of Object.entries(enums))if(!v.includes(i[k]))fail("incomplete");
 for(const [k,v]of Object.entries(arrays))if(!Array.isArray(i[k])||new Set(i[k]).size!==i[k].length||i[k].some(x=>!v.includes(x)))fail("incomplete");
 if(i.days.length<2||i.days.length>4||!i.equipment.length||typeof i.rir!=="boolean"||typeof i.rpe!=="boolean")fail("incomplete");
 if(i.favorites.some(x=>i.avoided.includes(x)))fail("conflicting_preferences");
 return true;
}
function eligibleExercises(i){return C.exercises.filter(e=>i.equipment.includes(e.equipment)&&!i.avoided.includes(e.id)&&!e.constraints.some(x=>i.movement.includes(x)));}
function foodAllowed(id,i){const f=C.foods.find(x=>x.id===id);return !!f&&!i.excludedFoods.includes(id)&&!(i.diet==="plant"&&!f.plant)&&!f.allergens.some(a=>i.allergies.includes(a))&&rank[f.kitchen]<=rank[i.kitchen];}
function eligibleMeals(i){return C.recipes.filter(r=>r.items.every(x=>foodAllowed(x.food,i)));}
function totals(meals){const n=[0,0,0,0];let cost=0;for(const m of meals)for(const x of m.items){const f=C.foods.find(f=>f.id===x.food);if(!f||!Number.isFinite(x.g)||x.g<=0)fail("incomplete");f.nutrients.forEach((v,j)=>n[j]+=v*x.g/100);cost+=f.cost*x.g/100;}return {kcal:Math.round(n[0]),protein:Math.round(n[1]),carbs:Math.round(n[2]),fat:Math.round(n[3]),cost:Math.round(cost*100)/100};}
function exercise(id,i){const e=eligibleExercises(i).find(e=>e.id===id);if(!e)fail("excluded");return {id,sets:C.policy.sets[i.experience],reps:C.policy.reps[i.goal],load:null,unit:i.unit,rest:C.policy.rest[i.goal],rir:i.rir?2:null,rpe:i.rpe?7:null,rule:C.policy.progression};}
function validatePlan(p,i){
 validateIntake(i);
 if(!p||!p.training||!p.nutrition||!p.recovery)fail("incomplete");
 if(!same(p.training.days,i.days)||p.training.sessions.length!==i.days.length)fail("incomplete");
 for(const [n,s]of p.training.sessions.entries()){
  if(s.day!==i.days[n]||!s.exercises.length||s.exercises.length>Math.floor(i.minutes/10)+1||new Set(s.exercises.map(x=>x.id)).size!==s.exercises.length)fail("incomplete");
  for(const e of s.exercises){if(!eligibleExercises(i).some(x=>x.id===e.id)||e.unit!==i.unit||e.load!==null||e.sets!==C.policy.sets[i.experience]||!Number.isInteger(e.reps)||e.reps<1||e.reps>C.policy.repMax||e.rule!==C.policy.progression||e.rest!==C.policy.rest[i.goal])fail("excluded");
   if(!(e.rir===null||(Number.isInteger(e.rir)&&e.rir>=0&&e.rir<=10))||!(e.rpe===null||(Number.isFinite(e.rpe)&&e.rpe>=0&&e.rpe<=10)))fail("incomplete");
  }
 }
 if(p.nutrition.meals.length!==i.meals||p.nutrition.meals.some(m=>!m.items.length||m.items.some(x=>!foodAllowed(x.food,i))))fail("excluded");
 const t=totals(p.nutrition.meals);if(t.cost>C.policy.budget[i.budget]||!same(t,p.nutrition.totals))fail("budget");
 if(!same(p.recovery.restDays,days.filter(d=>!i.days.includes(d))))fail("incomplete");
 return true;
}
function build(i){
 validateIntake(i);
 const es=eligibleExercises(i).sort((a,b)=>Number(i.favorites.includes(b.id))-Number(i.favorites.includes(a.id))||Number(b.goals.includes(i.goal))-Number(a.goals.includes(i.goal)));
 const count=Math.min(Math.floor(i.minutes/10),4);
 if(es.length<count)fail("catalog_gap");
 const ms=eligibleMeals(i).sort((a,b)=>totals([a]).cost-totals([b]).cost);
 if(ms.length<3)fail("catalog_gap");
 const meals=Array.from({length:i.meals},(_,n)=>({id:ms[n%ms.length].id,at:(i.rhythm==="early"?7:10)+n*(i.meals===3?5:4),items:clone(ms[n%ms.length].items)}));
 const plan={
  training:{days:clone(i.days),minutes:i.minutes,goal:i.goal,secondary:clone(i.secondary),sessions:i.days.map(day=>({day,exercises:es.slice(0,count).map(e=>exercise(e.id,i))})),start:"start_principle",progression:C.policy.progression},
  nutrition:{meals,totals:totals(meals),source:C.policy.nutrition,budgetCap:C.policy.budget[i.budget]},
  recovery:{sleepGoal:Math.max(i.sleep,C.policy.sleepGoal),baselineSleep:i.sleep,restDays:days.filter(d=>!i.days.includes(d)),checkins:i.recovery==="low"?"daily":"after_workout",lightWeek:{week:4,optional:true,active:false},secondary:clone(i.secondary),schedule:clone(i.days),source:C.policy.sleep}
 };
 validatePlan(plan,i);return plan;
}
function differences(before,after,path=""){
 if(same(before,after))return [];
 if(before&&after&&typeof before==="object"&&typeof after==="object"){
  return [...new Set([...Object.keys(before),...Object.keys(after)])].flatMap(k=>differences(before[k]??null,after[k]??null,path?path+"."+k:k));
 }return [{path,before:before??null,after:after??null}];
}
function effect(oldId,newId,i){
 const a=C.exercises.find(x=>x.id===oldId),b=eligibleExercises(i).find(x=>x.id===newId);
 if(!a||!b)fail("excluded");
 return {from:a.id,to:b.id,muscle:[a.muscle,b.muscle],equipment:[a.equipment,b.equipment],goal:i.goal,goalMatch:b.goals.includes(i.goal),medical_claim:false};
}
function create(){
 let s={synthetic_only:true,route:"independent",subject:"syn-ai-member",revision:0,epoch:0,clock:1789293600000,intake:clone(C.defaults),intakeVersion:1,active:null,draft:null,history:[],status:"intake",confirmed:null,audit:[],notifications:[],signal:null,signalBindings:{},safety:"clear",contextFixtures:[],consent:true,source:C.policy.id,sourceExpires:C.policy.expires,automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false};
 const done=new Map();let counter=0;
 const view=()=>clone(s);
 function basis(){return JSON.stringify([s.revision,s.epoch,s.intakeVersion,s.source,s.draft]);}
 function event(action,data={}){return {id:"cmd-b-"+(++counter),route:"independent",subject:"syn-ai-member",action,data:clone(data),basis:basis()};}
 function gate(){if(!s.consent)fail("consent_revoked");if(s.source!==C.policy.id)fail("version_conflict");if(s.clock>=s.sourceExpires)fail("expired");if(s.safety!=="clear")fail("safety_"+s.safety);}
 function draft(plan,reason){
  validatePlan(plan,s.intake);s.draft={plan:clone(plan),intake:clone(s.intake),intakeVersion:s.intakeVersion,refs:{catalog:C.policy.catalog,policy:C.policy.id,nutrition:C.policy.nutrition,sleep:C.policy.sleep,progression:C.policy.progression},base:s.revision,reason};
  s.status="member_pending";s.confirmed=null;
 }
 function command(e,options={}){
  const before=clone(s);
  try{
   if(!e||!/^cmd-b-[a-zA-Z0-9-]{1,60}$/.test(e.id)||e.route!=="independent"||e.subject!=="syn-ai-member"||!e.data)fail("wrong_route");
   const fingerprint=JSON.stringify(e);
   if(done.has(e.id)){if(done.get(e.id)!==fingerprint)fail("duplicate_conflict");return {ok:true,reason:"idempotent",state:view()};}
   if(e.basis!==basis())fail("version_conflict");
   const d=e.data;
   if(e.action==="intake"){validateIntake(d);s.intake=clone(d);s.intakeVersion++;s.draft=null;s.confirmed=null;s.status="intake";}
   else if(e.action==="build"){gate();draft(build(s.intake),"intake");}
   else if(e.action==="edit"){
    gate();if(!s.draft||!["member_pending","confirmed"].includes(s.status))fail("wrong_status");
    const p=clone(s.draft.plan);
    if(["replace","add","remove","move"].includes(d.kind)){
     const session=p.training.sessions[d.session];if(!session)fail("incomplete");
     if(d.kind==="add")session.exercises.push(exercise(d.id,s.intake));
     else{
      if(!Number.isInteger(d.index)||!session.exercises[d.index])fail("incomplete");
      if(d.kind==="replace"){s.signal={effect:effect(session.exercises[d.index].id,d.id,s.intake)};session.exercises[d.index]=exercise(d.id,s.intake);}
      if(d.kind==="remove")session.exercises.splice(d.index,1);
      if(d.kind==="move"){if(!Number.isInteger(d.to)||d.to<0||d.to>=session.exercises.length)fail("incomplete");session.exercises.splice(d.to,0,session.exercises.splice(d.index,1)[0]);}
     }
    }else if(d.kind==="meal"){
     const r=eligibleMeals(s.intake).find(x=>x.id===d.id);if(!r||!p.nutrition.meals[d.index])fail("excluded");
     p.nutrition.meals[d.index]={id:r.id,at:p.nutrition.meals[d.index].at,items:clone(r.items)};p.nutrition.totals=totals(p.nutrition.meals);
    }else if(d.kind==="food"){
     const m=p.nutrition.meals[d.meal],x=m?.items[d.index];if(!x||!foodAllowed(d.id,s.intake))fail("excluded");
     x.food=d.id;m.id="custom";p.nutrition.totals=totals(p.nutrition.meals);
    }else if(d.kind==="sleep"){if(![7,8,9].includes(d.hours))fail("incomplete");p.recovery.sleepGoal=d.hours;}
    else if(d.kind==="light_week")p.recovery.lightWeek.active=!p.recovery.lightWeek.active;
    else fail("invalid_action");
    draft(p,"member_edit");
   }else if(e.action==="clarify"){
    if(d.source!=="syn-new-clear-context@1")fail("incomplete");
    s.contextFixtures=s.contextFixtures.filter(x=>!["misunderstanding","technical"].includes(x));
    s.safety=s.contextFixtures[0]||"clear";s.epoch++;s.confirmed=null;
    if(s.status==="confirmed")s.status="member_pending";
   }else if(e.action==="confirm"){
    gate();if(s.status!=="member_pending"||!s.draft)fail("wrong_status");validatePlan(s.draft.plan,s.draft.intake);s.status="confirmed";s.confirmed=basis();
   }else if(e.action==="apply"){
    gate();if(s.status!=="confirmed"||s.confirmed!==basis()||s.draft.base!==s.revision)fail("wrong_status");
    validatePlan(s.draft.plan,s.draft.intake);
    const active={version:s.revision+1,plan:clone(s.draft.plan),intake:clone(s.draft.intake),intakeVersion:s.draft.intakeVersion,refs:clone(s.draft.refs),reason:s.draft.reason,at:s.clock,componentVersions:{}};
    for(const k of ["training","nutrition","recovery"])active.componentVersions[k]=(s.active?.componentVersions[k]||0)+(same(s.active?.plan[k]??null,active.plan[k])?0:1);
    if(options.fault_before_commit)fail("atomic_fault");
    s.active=active;s.history.push(clone(active));s.revision++;s.status="applied";s.confirmed=null;
   }else if(e.action==="reject"){if(!s.draft||!["member_pending","confirmed"].includes(s.status))fail("wrong_status");s.status="rejected";s.confirmed=null;}
   else if(e.action==="reopen"){gate();if(!s.draft||!["rejected","applied"].includes(s.status))fail("wrong_status");draft(s.draft.plan,"reopened");}
   else if(e.action==="restore"){
    gate();const old=s.history.find(x=>x.version===d.version);if(!old||d.version===s.revision)fail("wrong_status");
    // Restore under current exclusions/consent, never resurrect incompatible intake.
    draft(old.plan,"restore_v"+old.version);
   }else if(e.action==="signal"){
    gate();if(!s.active)fail("wrong_status");const signal=C.signals[d.id];if(!signal)fail("incomplete");
    if(s.signalBindings[d.id]!==undefined&&s.signalBindings[d.id]!==s.revision)fail("version_conflict");
    s.signalBindings[d.id]=s.revision;
    s.signal={id:d.id,...clone(signal),source:"syn-signal-"+d.id+"@1",base:s.revision,confirmation:"member_then_apply"};
    const p=clone(s.active.plan);
    if(signal.kind==="facts"){s.signal.confirmation="none";s.draft=null;s.confirmed=null;s.status="facts";}
    else{
     if(signal.kind==="sleep")p.recovery.sleepGoal=Math.max(p.recovery.sleepGoal,8);
     if(signal.kind==="checkin")p.recovery.checkins="daily";
     if(signal.kind==="schedule"){p.training.sessionStart=s.intake.rhythm==="early"?"18:00":"11:00";}
     if(signal.kind==="swap"){
      const old=p.training.sessions[0].exercises[0],alt=eligibleExercises(s.intake).find(x=>x.id!==old.id&&x.muscle===C.exercises.find(x=>x.id===old.id).muscle&&!p.training.sessions[0].exercises.some(y=>y.id===x.id));
      if(!alt)fail("catalog_gap");p.training.sessions[0].exercises[0]=exercise(alt.id,s.intake);p.training.temporary={weeks:2,reason:"syn-plateau@1",original:old.id};
     }
     if(signal.kind==="reps"){const x=p.training.sessions[0].exercises[0];if(x.reps+C.policy.repStep>C.policy.repMax)fail("rule_limit");x.reps+=C.policy.repStep;}
     if(signal.kind==="sleep")p.recovery.windDown=s.intake.rhythm==="early"?"21:30":"23:30";
     draft(p,"signal_"+d.id);s.draft.refs.evidence=s.signal.source;
    }
   }else if(e.action==="photo"){
    gate();if(!s.active||d.corroborated!==true)fail("incomplete");
    if(s.signalBindings.photo!==undefined&&s.signalBindings.photo!==s.revision)fail("version_conflict");
    s.signalBindings.photo=s.revision;
    const p=clone(s.active.plan),session=p.training.sessions[0],old=session.exercises.find(x=>C.exercises.find(z=>z.id===x.id).muscle==="shoulders");
    const alt=old&&eligibleExercises(s.intake).find(x=>x.muscle==="shoulders"&&!session.exercises.some(y=>y.id===x.id));
    if(!old||!alt)fail("catalog_gap");
    session.exercises[session.exercises.indexOf(old)]=exercise(alt.id,s.intake);
    p.training.temporary={weeks:2,reason:"syn-photo-context@1",original:old.id};
    s.signal={id:"photo",source:"syn-photo-context@1",window:"4 weeks",values:["fixture illustration pair","synthetic shoulder measure: 30 / 30 cm","synthetic workout log: 4 sessions"],effect:effect(old.id,alt.id,s.intake),confirmation:"member_then_apply"};
    draft(p,"photo_concept");s.draft.refs.evidence="syn-photo-context@1";
   }else fail("invalid_action");
   s.clock+=1000;
   s.audit.push({id:e.id,at:s.clock,action:e.action,reason:s.draft?.reason||e.action,status:s.status,base:before.revision,version:s.revision,refs:s.draft?.refs||{policy:s.source},intakeVersion:s.intakeVersion});
   const notice={build:"proposal",confirm:"confirmed",apply:"applied",restore:"restore",reject:"rejected"}[e.action];
   if(notice)s.notifications.push({id:e.id,at:s.clock,key:notice,recipient:"syn-ai-member"});
   done.set(e.id,fingerprint);return {ok:true,reason:"success",state:view()};
  }catch(err){s=before;return {ok:false,reason:err.message,state:view()};}
 }
 function inject(code){
  const allowed=["current","serious","recurring","unclassified","self_reported","missing","expired_context","misunderstanding","technical","consent_revoked","version_conflict","expired"];
  if(!allowed.includes(code))return {ok:false,reason:"invalid_action"};
  s.epoch++;s.confirmed=null;
  if(code==="consent_revoked")s.consent=false;
  else if(code==="version_conflict")s.source="syn-coach-policy@2";
  else if(code==="expired")s.clock=s.sourceExpires;
  else {if(!s.contextFixtures.includes(code))s.contextFixtures.push(code);s.safety=s.contextFixtures[0];}
  s.audit.push({id:"source-"+s.epoch,at:s.clock,action:"source_event",reason:code,status:"blocked",base:s.revision,version:s.revision,refs:{policy:s.source},intakeVersion:s.intakeVersion});
  return {ok:true,state:view()};
 }
 return Object.freeze({view,event,command,inject});
}
const api={create,build,validateIntake,validatePlan,eligibleExercises,eligibleMeals,foodAllowed,totals,effect,differences,enums,arrays};
if(typeof module==="object"&&module.exports)module.exports=api;else root.FMZ8Model=api;
})(globalThis);
