/* Synthetic memory-only state machine. Not browser authorization for a real app. */
(function(root){"use strict";
const B=typeof module==="object"?require("../coach-review-demo/model.js"):root.FMZ8Model;
const clone=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const exact=(x,keys)=>x&&same(Object.keys(x).sort(),keys.slice().sort());
function create(packet){
 const packs=clone(packet),initial=packs.initial,route=packs.route,clock=packs.now_ms;
 if(!["A","B"].includes(route)||!initial.synthetic_only||initial.automatic_actions_allowed!==false)throw Error("invalid_packet");
 let count=0,epoch=0,current=initial;
 let s={route,subject:"syn-owner",revision:initial.binding?.plan.revision||packs.baseRevision,
  active:clone(packs.before),target:clone(initial.target),status:initial.status==="candidate_only"?"member_pending":initial.status,
  proposal:1,source:initial.source_hash,member:false,trainer:false,consent:true,expired:false,health:false,
  sourceChanged:false,conflict:false,checked:false,clock,history:[],audit:[],automatic_actions_allowed:false,physical_advice_authorized:false,medical_clearance:false};
 s.history.push({version:s.revision,plan:clone(s.active),source:s.source,at:clock,kind:"original"});
 const done=new Map(),view=()=>clone(s),basis=()=>JSON.stringify([s.revision,s.proposal,s.source,epoch]);
 const fail=c=>{throw Error(c);};
 function gate(){if(!s.consent)fail("consent");if(s.expired||s.clock>=current.binding?.valid_until_ms)fail("expired");if(s.health)fail("safety");if(s.conflict)fail("conflict");
  if(current.status!=="candidate_only"||!s.target||s.sourceChanged)fail("no_target");}
 function pending(target,kind){s.target=clone(target);s.proposal++;s.status="member_pending";s.member=false;s.trainer=false;s.kind=kind;}
 function event(action,data={},actor="member"){return {id:"request-"+(++count),action,data:clone(data),actor,route,subject:"syn-owner",basis:basis()};}
 function command(e,opt={}){
  const old=clone(s),oldCurrent=current,oldEpoch=epoch;
  try{
   if(!exact(e,["id","action","data","actor","route","subject","basis"])||!/^request-[a-zA-Z0-9-]{1,80}$/.test(e.id)||e.route!==route||e.subject!=="syn-owner"||!["member","trainer"].includes(e.actor)||!e.data||typeof e.data!=="object")fail("binding");
   if(e.actor==="trainer"&&route!=="A")fail("actor");
   const fp=JSON.stringify(e);
   if(done.has(e.id)){if(done.get(e.id)!==fp)fail("duplicate_conflict");return {ok:true,reason:"idempotent",state:view()};}
   if(e.basis!==basis())fail("conflict");
   if(!["edit","restore"].includes(e.action)&&!exact(e.data,[]))fail("payload");
   const trainer=["approve","block"].includes(e.action)||e.action==="reject"&&s.status==="trainer_pending"||e.action==="restore"&&route==="A"&&e.actor==="trainer";
   if(e.actor!==(trainer?"trainer":"member"))fail("actor");
   if(e.action==="check"){
    if(s.status!=="confirmation")fail("status");s.checked=true;
   }else if(e.action==="correct"){
    if(s.sourceChanged||current.source_hash===packs.corrected.source_hash)fail("already_corrected");
    if(packs.correctedPrevious!==s.source)fail("source_chain");
    current=packs.corrected;s.source=current.source_hash;s.sourceChanged=true;s.status="needs_review";s.member=false;s.trainer=false;epoch++;
   }else if(e.action==="reassess"){
    if(!s.sourceChanged)fail("status");
    s.sourceChanged=false;
    if(s.revision!==packs.baseRevision){s.target=null;s.status="stale_source";}
    else if(current.status!=="candidate_only"){s.target=null;s.status=current.status;}
    else if(!s.consent||s.expired||s.health||s.conflict){s.target=null;s.status="blocked";}
    else pending(current.target,"source_review");
   }else if(["revoke","expire","health","stale"].includes(e.action)){
    if(e.action==="revoke")s.consent=false;if(e.action==="expire")s.expired=true;if(e.action==="health")s.health=true;if(e.action==="stale")s.conflict=true;
    s.status="blocked";s.member=false;s.trainer=false;epoch++;
   }else{
    gate();
    if(e.action==="accept"||e.action==="confirm"){
     if(e.action!==(route==="A"?"accept":"confirm")||s.status!=="member_pending")fail("status");
     s.member=true;s.status=route==="A"?"trainer_pending":"confirmed";
    }else if(e.action==="approve"){
     if(route!=="A"||s.status!=="trainer_pending"||!s.member)fail("status");s.trainer=true;s.status="approved";
    }else if(e.action==="reject"||e.action==="block"){
     if(!["member_pending","trainer_pending","confirmed","approved"].includes(s.status)||e.action==="block"&&s.status!=="trainer_pending")fail("status");
     s.status=e.action==="block"?"blocked":"rejected";s.member=false;s.trainer=false;
    }else if(e.action==="apply"){
     if(s.status!==(route==="A"?"approved":"confirmed")||!s.member||route==="A"&&!s.trainer)fail("status");
     if(route==="B")B.validatePlan(s.target.plan,s.target.intake);
     s.revision++;s.active=clone(s.target);s.history.push({version:s.revision,plan:clone(s.active),source:s.source,at:s.clock,kind:s.kind||"proposal",member:true,trainer:route==="A"?true:null});s.status="applied";
    }else if(e.action==="restore"){
     if(s.status!=="applied"||!exact(e.data,["version"]))fail("status");
     const h=s.history.find(x=>x.version===e.data.version);if(!h||h.version===s.revision)fail("conflict");
     const target=clone(h.plan);
     if(route==="B"){B.validatePlan(target.plan,s.active.intake);target.intake=clone(s.active.intake);}
     pending(target,"restore_v"+h.version);
    }else if(e.action==="edit"){
     if(route!=="B"||!["member_pending","confirmed"].includes(s.status)||!exact(e.data,["days","favorite","avoid","exercise"]))fail("status");
     const i=clone(s.target.intake);i.days=clone(e.data.days);i.favorites=e.data.favorite?[e.data.favorite]:[];i.avoided=e.data.avoid?[e.data.avoid]:[];
     B.validateIntake(i);const plan=B.build(i);plan.training.sessionStart=s.target.plan.training.sessionStart;
     if(e.data.exercise){
      if(!B.eligibleExercises(i).some(x=>x.id===e.data.exercise))fail("excluded");
      plan.training.sessions[0].exercises[0].id=e.data.exercise;
     }
     B.validatePlan(plan,i);
     if(!same(plan.nutrition,s.active.plan.nutrition)||plan.recovery.sleepGoal!==s.active.plan.recovery.sleepGoal)fail("out_of_scope");
     pending({plan,intake:i},"member_edit");
    }else fail("action");
   }
   if(opt.fault_before_commit)fail("atomic_fault");
   s.clock+=1000;
   s.audit.push({id:e.id,actor:e.actor,action:e.action,status:s.status,at:s.clock,source:s.source,base:old.revision,version:s.revision,proposal:s.proposal,reason:s.kind||e.action});
   done.set(e.id,fp);return {ok:true,reason:"success",state:view()};
  }catch(err){s=old;current=oldCurrent;epoch=oldEpoch;return {ok:false,reason:err.message,state:view()};}
 }
 return Object.freeze({view,event,command,result:()=>clone(current)});
}
const api={create,differences:B.differences};if(typeof module==="object")module.exports=api;else root.FMZ14Model=api;
})(globalThis);
