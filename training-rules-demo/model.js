/* Deterministic synthetic contract; no network, persistence or real authorization. */
(function(root){"use strict";
const C=typeof module==="object"?require("./catalog.js").data:root.FMZ16Catalog.data;
if(typeof module==="object")require("../independent-intake-demo/data.js");
const G=root.FMZ15Data.registry.safety,copy=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=x=>{throw Error(x);};
const days=["mon","tue","wed","thu","fri","sat","sun"],goals=["fitness","muscle","strength"],experiences=["beginner","experienced"],health=Object.keys(G);
const exact=(x,keys)=>x&&typeof x==="object"&&!Array.isArray(x)&&same(Object.keys(x).sort(),keys.slice().sort());
const unique=(v,allowed)=>Array.isArray(v)&&new Set(v).size===v.length&&v.every(x=>allowed.includes(x));
const int=x=>Number.isSafeInteger(x),range=(v,r)=>int(v)&&v>=r.min&&v<=r.max&&(v-r.min)%r.step===0;
const fields=["goal","experience","days","frequency","minutes","equipment","favorites","excluded","rir","rpe","unit","health","consent","history"];
function catalog(c,clock){
 if(!c||c.id!=="syn16-training-rules"||!int(c.version)||c.version<1||c.review!=="unreviewed"||c.source!=="synthetic-platform-catalog"||
 !int(c.effective)||!int(c.expires)||c.effective>clock||c.expires<=clock||!int(c.overhead_seconds)||c.overhead_seconds<0)fail("source");
 if(!Array.isArray(c.exercises)||!Array.isArray(c.rules)||!Array.isArray(c.layouts)||!c.exercises.length)fail("source");
 const ids=new Set();for(const e of c.exercises){if(!e.id||ids.has(e.id)||!C.exercises.some(x=>same(x,e)))fail("exercise_source");ids.add(e.id);}
 const ruleIDs=new Set();for(const r of c.rules){
  if(!r.id||ruleIDs.has(r.id)||!int(r.version)||r.version<1||!goals.includes(r.goal)||!experiences.includes(r.experience)||!["main","support"].includes(r.role)||r.type!==(r.role==="main"?"compound":"accessory"))fail("rule");
  ruleIDs.add(r.id);
  for(const key of ["sets","reps","rest","rir","rpe"]){const q=r[key];if(!exact(q,["min","max","default","step"])||![q.min,q.max,q.default,q.step].every(int)||q.step<1||q.min<(key==="rir"?0:1)||q.max<q.min||!range(q.default,q))fail("rule");}
  if(r.rir.max>4||r.rpe.max>10||!unique(r.frequencies,[2,4])||!r.frequencies.length||!unique(r.minutes,[10,15,30,45,60])||!r.minutes.length||!unique(r.alternatives,[...ids])||!r.alternatives.length)fail("rule");
  if(!r.alternatives.every(id=>c.exercises.find(e=>e.id===id).type===r.type&&c.exercises.find(e=>e.id===id).role===r.role))fail("rule");
  if(!exact(r.timing,["rep_seconds","setup_seconds"])||!int(r.timing.rep_seconds)||r.timing.rep_seconds<=0||!int(r.timing.setup_seconds)||r.timing.setup_seconds<0)fail("rule");
  if(!exact(r.progression,["kind","step","ceiling","automatic"])||r.progression.kind!=="reps"||!int(r.progression.step)||r.progression.step<1||r.progression.ceiling!==r.reps.max||r.progression.automatic!==false||!Array.isArray(r.reason)||r.reason.length!==3||!r.reason.every(x=>typeof x==="string"&&x.length))fail("rule");
 }
 const layoutIDs=new Set();for(const l of c.layouts){if(!l.id||layoutIDs.has(l.id)||!int(l.version)||l.version<1||![2,4].includes(l.frequency)||!same(l.roles,["main","support"]))fail("layout");layoutIDs.add(l.id);}
 return true;
}
function intake(i,c,clock){
 if(!exact(i,fields)||!goals.includes(i.goal)||!experiences.includes(i.experience)||!unique(i.days,days)||![2,4].includes(i.frequency)||i.days.length<i.frequency||![10,15,30,45,60].includes(i.minutes)||
 !unique(i.equipment,["mat","dumbbell","band"])||!i.equipment.length||!unique(i.favorites,c.exercises.map(x=>x.id))||!unique(i.excluded,c.exercises.map(x=>x.id))||i.favorites.some(x=>i.excluded.includes(x))||
 typeof i.rir!=="boolean"||typeof i.rpe!=="boolean"||typeof i.consent!=="boolean"||!["kg","lb"].includes(i.unit)||!health.includes(i.health))fail("intake");
 if(i.history!==null){
  if(!Array.isArray(i.history))fail("history");
  const ids=new Set(),slots=new Set();
  for(const h of i.history){
   if(!exact(h,["id","person","exercise","session","version","at","expires","weight","reps","rir","rpe"])||!/^syn16-history-/.test(h.id)||ids.has(h.id)||h.person!=="syn16-member"||!c.exercises.some(e=>e.id===h.exercise)||!/^syn16-session-/.test(h.session)||!int(h.version)||h.version<1||
   !int(h.at)||!int(h.expires)||h.at>clock||h.expires<=clock||h.expires>h.at+86400000||!exact(h.weight,["value","unit"])||!["kg","lb"].includes(h.weight.unit)||
   !(h.weight.value===null||typeof h.weight.value==="number"&&Number.isFinite(h.weight.value)&&h.weight.value>=0)||!int(h.reps)||h.reps<1||
   !(h.rir===null||int(h.rir)&&h.rir>=0&&h.rir<=4)||!(h.rpe===null||int(h.rpe)&&h.rpe>=1&&h.rpe<=10))fail("history");
   const slot=h.exercise+"@"+h.at;if(slots.has(slot))fail("history_conflict");slots.add(slot);ids.add(h.id);
  }
 }
}
function selectRule(c,i,role){
 const matches=c.rules.filter(r=>r.goal===i.goal&&r.experience===i.experience&&r.role===role&&r.frequencies.includes(i.frequency)&&r.minutes.includes(i.minutes));
 if(matches.length!==1)fail(matches.length?"rule_conflict":"rule_missing");return matches[0];
}
function eligible(c,i,r){return c.exercises.filter(e=>r.alternatives.includes(e.id)&&e.role===r.role&&e.type===r.type&&i.equipment.includes(e.equipment)&&!i.excluded.includes(e.id)).sort((a,b)=>Number(i.favorites.includes(b.id))-Number(i.favorites.includes(a.id)));}
function historical(i,id){return copy((i.history||[]).filter(h=>h.exercise===id).sort((a,b)=>b.at-a.at)[0]||null);}
function seconds(e,r){return r.timing.setup_seconds+e.sets*e.reps*r.timing.rep_seconds+(e.sets-1)*e.rest;}
function row(c,i,r,e){return {exercise:e.id,role:r.role,type:e.type,rule:r.id,ruleVersion:r.version,sets:r.sets.default,reps:r.reps.default,rest:r.rest.default,
 rir:i.rir?r.rir.default:null,rpe:i.rpe?r.rpe.default:null,load:null,requestedUnit:i.unit,history:historical(i,e.id),seconds:0};}
function validatePlan(p,i,c){
 if(!p||p.catalogId!==c.id||p.catalogVersion!==c.version||p.source!==JSON.stringify(c)||p.goal!==i.goal||p.experience!==i.experience||p.budget!==i.minutes*60||p.requestedUnit!==i.unit||p.sessions.length!==i.frequency)fail("plan_source");
 const layouts=c.layouts.filter(l=>l.frequency===i.frequency);if(layouts.length!==1)fail("layout");const l=layouts[0];
 if(p.layout!==l.id||p.layoutVersion!==l.version||!unique(p.sessions.map(s=>s.day),i.days))fail("day");
 for(const s of p.sessions){
  if(s.exercises.length!==l.roles.length||!same(s.exercises.map(e=>e.role),l.roles))fail("plan_source");
  let total=c.overhead_seconds;
  for(const e of s.exercises){
   const r=selectRule(c,i,e.role),match=eligible(c,i,r).find(x=>x.id===e.exercise);
   if(!match||e.type!==r.type||e.rule!==r.id||e.ruleVersion!==r.version)fail("excluded");
   for(const k of ["sets","reps","rest"])if(!range(e[k],r[k]))fail("range");
   for(const k of ["rir","rpe"])if(i[k]?!range(e[k],r[k]):e[k]!==null)fail("effort");
   if(e.load!==null||e.requestedUnit!==i.unit||!same(e.history,historical(i,e.exercise)))fail("history");
   if(e.seconds!==seconds(e,r))fail("time_binding");total+=e.seconds;
  }
  if(s.seconds!==total)fail("time_binding");if(total>p.budget)fail("time_budget");
 }
 return true;
}
function build(i,c,clock){
 catalog(c,clock);intake(i,c,clock);const layouts=c.layouts.filter(l=>l.frequency===i.frequency);if(layouts.length!==1)fail("layout");const l=layouts[0];
 const p={catalogId:c.id,catalogVersion:c.version,source:JSON.stringify(c),goal:i.goal,experience:i.experience,budget:i.minutes*60,requestedUnit:i.unit,layout:l.id,layoutVersion:l.version,sessions:[]};
 for(const day of i.days.slice(0,i.frequency)){
  const s={day,exercises:[],seconds:c.overhead_seconds};
  for(const role of l.roles){const r=selectRule(c,i,role),e=eligible(c,i,r)[0];if(!e)fail("equipment");const x=row(c,i,r,e);x.seconds=seconds(x,r);s.exercises.push(x);s.seconds+=x.seconds;}p.sessions.push(s);
 }validatePlan(p,i,c);return p;
}
function create(f){
 const input=copy(f);let seq=0;
 let s={synthetic_only:true,route:"B",person:"syn16-member",clock:input.clock,intake:copy(input.intake),catalog:copy(input.catalog),intakeRevision:1,intakeHistory:[copy(input.intake)],draft:null,confirmed:false,status:"intake",version:0,history:[],active:null,audit:[],epoch:0,revoked:false,healthLatch:input.intake.health!=="none",automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false,external_calls:0};
 const completed=new Map(),view=()=>copy(s),binding=()=>JSON.stringify([s.version,s.intakeRevision,s.epoch,s.catalog]);
 function gate(){
  if(!input.synthetic_only||input.route!=="B"||input.person!=="syn16-member"||!int(s.clock))fail("binding");
  if(s.revoked||s.intake.consent!==true)fail("consent");
  if(s.healthLatch||!G[s.intake.health]?.plan_allowed)fail("safety");
  catalog(s.catalog,s.clock);intake(s.intake,s.catalog,s.clock);
 }
 function event(action,data={}){return {id:"syn16-request-"+(++seq),person:s.person,route:"B",action,data:copy(data),binding:binding()};}
 function pending(p){validatePlan(p,s.intake,s.catalog);s.draft={plan:copy(p),intake:copy(s.intake),catalog:copy(s.catalog),base:s.version,intakeRevision:s.intakeRevision};s.confirmed=false;s.status="pending";}
 function command(e,opt={}){
  const old=copy(s);try{
   if(!exact(e,["id","person","route","action","data","binding"])||!/^syn16-request-[a-zA-Z0-9-]+$/.test(e.id)||e.person!==s.person||e.route!=="B"||!e.data||typeof e.data!=="object")fail("binding");
   const fingerprint=JSON.stringify(e);
   if(completed.has(e.id)){if(completed.get(e.id)!==fingerprint)fail("duplicate_conflict");return {ok:true,reason:"idempotent",state:view()};}
   if(e.binding!==binding())fail("version_conflict");
   if(!["intake","edit","source","restore"].includes(e.action)&&!exact(e.data,[]))fail("payload");
   if(e.action==="revoke"){s.revoked=true;s.confirmed=false;s.status="blocked";s.epoch++;}
   else if(e.action==="intake"){
    if(s.revoked||!s.intake.consent)fail("consent");if(!exact(e.data,fields))fail("intake");
    s.intake=copy(e.data);s.intakeRevision++;s.intakeHistory.push(copy(e.data));s.healthLatch=s.healthLatch||s.intake.health!=="none";s.draft=null;s.confirmed=false;s.status="reassess";s.epoch++;
   }else if(e.action==="source"){
    if(s.revoked||!s.intake.consent)fail("consent");catalog(e.data,s.clock);s.catalog=copy(e.data);s.draft=null;s.confirmed=false;s.status="reassess";s.epoch++;
   }else if(e.action==="reject"){if(!s.draft||!["pending","confirmed"].includes(s.status))fail("status");s.status="rejected";s.confirmed=false;s.epoch++;}
   else{
    gate();
    if(e.action==="build")pending(build(s.intake,s.catalog,s.clock));
    else if(e.action==="edit"){
     if(!["pending","confirmed"].includes(s.status)||!s.draft)fail("status");const p=copy(s.draft.plan),d=e.data;
     if(d.kind==="day"&&exact(d,["kind","session","day"])){
      if(!int(d.session)||!p.sessions[d.session]||!s.intake.days.includes(d.day))fail("day");p.sessions[d.session].day=d.day;
     }else if(d.kind==="exercise"&&exact(d,["kind","session","index","exercise","sets","reps","rest","rir","rpe"])){
      if(!int(d.session)||!int(d.index))fail("payload");const x=p.sessions[d.session]?.exercises[d.index];if(!x)fail("payload");
      const r=selectRule(s.catalog,s.intake,x.role),candidate=eligible(s.catalog,s.intake,r).find(e=>e.id===d.exercise);if(!candidate)fail("excluded");
      Object.assign(x,{exercise:d.exercise,type:candidate.type,sets:d.sets,reps:d.reps,rest:d.rest,rir:d.rir,rpe:d.rpe,history:historical(s.intake,d.exercise)});
      x.seconds=seconds(x,r);p.sessions[d.session].seconds=s.catalog.overhead_seconds+p.sessions[d.session].exercises.reduce((sum,e)=>sum+e.seconds,0);
     }else fail("payload");
     pending(p);
    }else if(e.action==="confirm"){
     if(s.status==="confirmed")return {ok:true,reason:"idempotent",state:view()};if(s.status!=="pending"||!s.draft)fail("status");validatePlan(s.draft.plan,s.intake,s.catalog);s.status="confirmed";s.confirmed=true;
    }else if(e.action==="activate"){
     if(s.status!=="confirmed"||!s.confirmed||!s.draft||s.draft.base!==s.version||s.draft.intakeRevision!==s.intakeRevision||!same(s.draft.catalog,s.catalog))fail("version_conflict");
     validatePlan(s.draft.plan,s.intake,s.catalog);s.version++;s.active={version:s.version,plan:copy(s.draft.plan),intake:copy(s.intake),catalog:copy(s.catalog),at:s.clock};s.history.push(copy(s.active));s.status="active";s.confirmed=false;
    }else if(e.action==="restore"){
     if(!exact(e.data,["version"])||!s.active)fail("status");const h=s.history.find(h=>h.version===e.data.version);if(!h||h.version===s.version)fail("version_conflict");pending(h.plan);
    }else fail("action");
    s.epoch++;
   }
   if(opt.fault_before_commit)fail("atomic_fault");
   s.clock+=1000;s.audit.push({request:e.id,action:e.action,from:old.version,to:s.version,intake:s.intakeRevision,catalog:s.catalog.version,status:s.status,at:s.clock});
   completed.set(e.id,fingerprint);return {ok:true,reason:"success",state:view()};
  }catch(error){s=old;return {ok:false,reason:error.message,state:view()};}
 }
 return Object.freeze({view,event,command,availability:()=>{try{gate();return {ok:true};}catch(e){return {ok:false,reason:e.message};}}});
}
const api={create,build,validatePlan,catalog,intake,selectRule,eligible,historical,seconds,fields,days,goals,experiences,health};
if(typeof module==="object")module.exports=api;else root.FMZ16Model=api;
})(globalThis);
