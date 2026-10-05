/* Shared memory-only coordinator. Frozen validators remain read-only. */
(function(root){'use strict';
const node=typeof module==='object',P=node?require('../combined-plan-demo/model.js'):root.FMZ18Model,F=node?require('../combined-plan-demo/fixtures.js'):root.FMZ18Fixtures,
R=node?require('../recovery-checkin-demo/model.js'):root.FMZ19Model,H=node?require('../recovery-checkin-demo/fixtures.js'):root.FMZ19Fixtures,
T=node?require('../training-rules-demo/model.js'):root.FMZ16Model,N=node?require('../nutrition-rules-demo/model.js'):root.FMZ17Model;
const copy=x=>structuredClone(x),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),int=Number.isSafeInteger,fail=x=>{throw Error(x);},
exact=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&same(Object.keys(x).sort(),k.slice().sort());
function base(route='B'){
 if(!['A','B'].includes(route))fail('binding');const recovery=H.base(route),pair=copy(F.base),b=P.inspect(pair);
 return {synthetic_only:true,person:'syn20-member',route,clock:pair.clock,link:{id:'syn20-link',version:1,aliases:['syn16-member','syn17-member','syn18-member','syn19-member','syn-owner'],training:recovery.plan.id,nutrition:b.nutrition.catalogId,recovery:recovery.subject},pair,recovery};
}
function slots(plan,version,route){
 const t=route==='B'?plan.training.sessions[0].exercises.flatMap(x=>Array.from({length:x.sets},(_,i)=>({id:'training:'+x.exercise+':'+(i+1),kind:'training',label:x.exercise+' #'+(i+1),planned:x.reps,unit:'reps',rir:x.rir,rpe:x.rpe}))):
 plan.training.exercises.flatMap(x=>x.sets.map(y=>({id:'training:'+x.exercise_id+':'+y.index,kind:'training',label:x.exercise_id+' #'+y.index,planned:y.reps.min,unit:'reps',rir:y.rir,rpe:y.rpe})));
 return t.concat(plan.nutrition.meals[0].items.map(x=>({id:'nutrition:'+x.food,kind:'nutrition',label:x.food,planned:x.grams,unit:'g',rir:null,rpe:null}))).map(x=>({...x,planVersion:version,value:null,actualRir:null,actualRpe:null,revision:1}));
}
function create(input=base()){
 if(!same(input,base(input.route)))fail('binding');
 let serial=0;const initial=copy(input),initialPlan={training:copy(input.recovery.plan.training),nutrition:copy(input.recovery.plan.nutrition),cadence:copy(input.recovery.cadence)};
 let s={person:input.person,route:input.route,link:copy(input.link),sourceRevision:1,sourceGeneration:1,epoch:0,clock:input.clock,consent:true,health:false,ruleAvailable:true,conflict:false,
 pair:copy(input.pair),recovery:copy(input.recovery),active:{version:1,...copy(initialPlan)},proposal:null,member:false,trainer:false,status:'missing',reason:'missing',
 history:[],records:[],recordHistory:[],recoveryHistory:[copy(input.recovery.rows)],notices:[],facts:[],completion:null,audit:[],external_calls:0,automatic_actions_allowed:false,physical_advice_authorized:false};
 s.history=[{...copy(s.active),sourceRevision:1,sourceGeneration:1,source:copy(input),kind:'original'}];s.records=slots(s.active,1,s.route);s.recordHistory=[{revision:1,plan:copy(s.active),rows:copy(s.records)}];
 const done=new Map(),view=()=>copy(s),basis=()=>JSON.stringify([s.epoch,s.sourceRevision,s.active.version,s.link]),event=(action,data={},actor='member')=>({id:'syn20-request-'+(++serial),action,data:copy(data),actor,person:s.person,route:s.route,basis:basis()});
 function access(){if(!s.consent)fail('consent');if(s.clock>=Math.min(s.pair.link.expires,s.pair.training.expires,s.pair.nutrition.expires,s.recovery.sources.expires))fail('expired');if(s.conflict)fail('source_conflict');}
 function gate(){access();if(s.health)fail('safety');}
 function retire(){s.proposal=null;s.member=false;s.trainer=false;for(const x of s.notices)if(x.status==='current')x.status='superseded';}
 function notice(kind){const id='syn20-notice-'+s.sourceRevision;if(!s.notices.some(x=>x.id===id))s.notices.push({id,sourceRevision:s.sourceRevision,kind,status:'current'});}
 function physical(p){return {training:p.training,nutrition:p.nutrition};}
 function validPlan(p){
  if(s.route==='B'){T.validatePlan(p.training,s.pair.training.fixture.intake,s.pair.training.fixture.catalog,s.clock);N.validatePlan(p.nutrition,s.pair.nutrition.fixture.intake,s.pair.nutrition.fixture.catalog,s.clock);}
  else if(!same(physical(p),physical(initialPlan)))fail('trainer_scope');
 }
 function pending(target,kind,rule,restores=null){s.proposal={target:copy(target),sourceRevision:s.sourceRevision,base:s.active.version,link:copy(s.link),rule:copy(rule),kind,restores};s.member=false;s.trainer=false;s.status='pending';s.reason=kind;notice(kind);}
 function assess(){
  retire();s.facts=[];try{
   access();if(s.sourceRevision>1)notice('record_change');s.facts=R.compare({...s.recovery,clock:s.clock});gate();
   if(!s.ruleAvailable)fail('rule_missing');
   if(!same(physical(s.active),physical(initialPlan)))fail('plan_binding');
   if(s.facts.every(x=>x.delta.numerator===0)){s.status='facts';s.reason='unchanged';return;}
   const o=R.option({...s.recovery,clock:s.clock});
   if(s.active.cadence.option===o.option){s.status='facts';s.reason='already_planned';return;}
   pending({...physical(s.active),cadence:{option:o.option,at:o.at}},'checkin',s.recovery.rule);
  }catch(e){s.reason=e.message;s.status=s.facts.length?'facts':'blocked';}
 }
 function sourceChanged(external=true){s.sourceRevision++;if(external)s.sourceGeneration++;retire();}
 function validateProposal(){
  gate();const p=s.proposal;if(!p||p.sourceRevision!==s.sourceRevision||p.base!==s.active.version||!same(p.link,s.link))fail('version_conflict');
  validPlan(p.target);
  if(p.kind==='checkin'||p.kind==='time'||p.kind==='restore'&&!same(p.target.cadence,s.active.cadence)){
   if(!s.ruleAvailable)fail('rule_missing');R.compare({...s.recovery,clock:s.clock});const o=R.option({...s.recovery,clock:s.clock});
   if(p.target.cadence.option!==o.option||!s.recovery.agenda.allowedTimes.includes(p.target.cadence.at))fail('restore_rule');
   if(!same(physical(p.target),physical(initialPlan)))fail('plan_binding');
  }
  if(s.route==='A'&&!same(s.recovery.rule?.trainer,initial.recovery.rule.trainer))fail('trainer');
 }
 function command(e,opt={}){
  const old=copy(s);try{
   if(!exact(e,['id','action','data','actor','person','route','basis'])||!/^syn20-request-[a-zA-Z0-9-]+$/.test(e.id)||e.person!==s.person||e.route!==s.route||!exact(e.data,Object.keys(e.data||{})))fail('binding');
   const trainer=['approve','block'].includes(e.action);if(e.actor!==(trainer?'trainer':'member')||trainer&&s.route!=='A')fail('actor');
   const fp=JSON.stringify(e);if(done.has(e.id)){if(done.get(e.id)!==fp)fail('duplicate_conflict');if(e.action!=='revoke')access();return {ok:true,reason:'idempotent',state:view()};}
   if(e.basis!==basis())fail('version_conflict');
   if(!['record','recovery','edit','restore','health'].includes(e.action)&&!exact(e.data,[]))fail('payload');
   if(e.action==='revoke'){s.consent=false;sourceChanged();s.status='blocked';s.reason='consent';}
   else{
    access();
    if(e.action==='recovery'){
     const d=e.data;if(!exact(d,['id','version','value']))fail('payload');const row=s.recovery.rows.find(x=>x.id===d.id);if(!row||row.version!==d.version)fail('record_version');
     const max=row.metric==='sleep'?1440:10,min=row.metric==='sleep'?0:1;if(d.value!==null&&(!int(d.value)||d.value<min||d.value>max))fail('value');
     if(row.value===d.value){done.set(e.id,fp);return {ok:true,reason:'unchanged',state:view()};}
     row.value=d.value;row.version++;s.recoveryHistory.push(copy(s.recovery.rows));sourceChanged();assess();
    }else if(e.action==='record'){
     const d=e.data;if(!exact(d,['id','version','planVersion','value','rir','rpe','unit']))fail('payload');
     const row=s.records.find(x=>x.id===d.id);if(!row||row.revision!==d.version||row.planVersion!==d.planVersion)fail('record_version');
     if(d.unit!==row.unit||d.value!==null&&(!int(d.value)||d.value<0||d.value>10000)||d.rir!==null&&(!int(d.rir)||d.rir<0||d.rir>10)||d.rpe!==null&&(!int(d.rpe)||d.rpe<1||d.rpe>10)||row.kind==='nutrition'&&(d.rir!==null||d.rpe!==null))fail('value');
     if(row.value===d.value&&row.actualRir===d.rir&&row.actualRpe===d.rpe){done.set(e.id,fp);return {ok:true,reason:'unchanged',state:view()};}
     row.value=d.value;row.actualRir=d.rir;row.actualRpe=d.rpe;row.revision++;sourceChanged();s.recordHistory.push({revision:s.sourceRevision,plan:copy(s.active),rows:copy(s.records)});assess();
    }else if(e.action==='refresh'){done.set(e.id,fp);return {ok:true,reason:'idempotent',state:view()};}
    else if(e.action==='complete'){
     const row=s.recovery.rows.at(-1);if(row.value===null)fail('missing');
     if(s.completion?.version===row.version){done.set(e.id,fp);return {ok:true,reason:'idempotent',state:view()};}
     s.completion={id:s.recovery.agenda.checkin.id,record:row.id,version:row.version,at:s.clock};sourceChanged();assess();
    }else if(e.action==='health'){
     if(!exact(e.data,['value'])||!['current','reported_resolved','none'].includes(e.data.value))fail('payload');
     s.health=s.health||e.data.value!=='none';s.recovery.health=e.data.value;sourceChanged();assess();
    }else if(['expire','conflict','missing_rule','no_trainer'].includes(e.action)){
     if(e.action==='expire')s.clock=s.pair.link.expires;
     if(e.action==='conflict')s.conflict=true;
     if(e.action==='missing_rule')s.ruleAvailable=false;
     if(e.action==='no_trainer')s.recovery.rule.trainer=null;
     sourceChanged();assess();
    }else{
     gate();
     if(e.action==='edit'){
      if(!exact(e.data,['domain','value']))fail('payload');
      const target=copy(s.proposal?.target||s.active),d=e.data;
      if(d.domain==='time'){
       if(!s.recovery.agenda.allowedTimes.includes(d.value))fail('time_option');
       R.compare({...s.recovery,clock:s.clock});R.option({...s.recovery,clock:s.clock});if(!s.ruleAvailable)fail('rule_missing');
       target.cadence={option:'daily',at:d.value};sourceChanged(false);pending(target,'time',s.recovery.rule);validateProposal();
      }else{
       if(s.route!=='B')fail('trainer_scope');
       if(d.domain==='training_day')target.training.sessions[0].day=d.value;
       else if(d.domain==='nutrition_moment'){const raw=N.raw(target.nutrition);raw[0].moment=d.value;target.nutrition=N.calculate(raw,s.pair.nutrition.fixture.intake,s.pair.nutrition.fixture.catalog,s.clock);}
       else fail('payload');
       validPlan(target);target.cadence=copy(s.active.cadence);sourceChanged(false);pending(target,'manual',{training:target.training.catalogId,trainingVersion:target.training.catalogVersion,nutrition:target.nutrition.ruleId,nutritionVersion:target.nutrition.ruleVersion});
      }
     }else if(e.action==='restore'){
      if(!exact(e.data,['version'])||!int(e.data.version)||e.data.version===s.active.version)fail('version_conflict');
      const h=s.history.find(x=>x.version===e.data.version);if(!h)fail('version_conflict');
      if(h.sourceGeneration!==s.sourceGeneration)fail('restore_source');
      const target=copy(physical(h));target.cadence=copy(h.cadence);pending(target,'restore',s.recovery.rule,h.version);validateProposal();
     }else{
      validateProposal();
      if(e.action==='accept'){if(s.status!=='pending')fail('status');s.member=true;s.status=s.route==='A'?'trainer_pending':'confirmed';}
      else if(e.action==='approve'){if(s.status!=='trainer_pending'||!s.member)fail('status');s.trainer=true;s.status='approved';}
      else if(e.action==='reject'||e.action==='block'){
       if(!['pending','trainer_pending','approved','confirmed'].includes(s.status)||e.action==='block'&&s.status!=='trainer_pending')fail('status');retire();s.status=e.action==='block'?'blocked':'rejected';s.reason=e.action;
      }else if(e.action==='apply'){
       if(s.status!==(s.route==='A'?'approved':'confirmed')||!s.member||s.route==='A'&&!s.trainer)fail('status');
       const p=s.proposal,training=copy(p.target.training);if(opt.fault==='after_training')fail('atomic_fault');
       const nutrition=copy(p.target.nutrition);if(opt.fault==='after_nutrition')fail('atomic_fault');
       const next={version:s.active.version+1,training,nutrition,cadence:copy(p.target.cadence)};
       const planChanged=!same(physical(next),physical(s.active));
       s.history.push({...copy(next),sourceRevision:s.sourceRevision,sourceGeneration:s.sourceGeneration,source:{link:copy(s.link),pair:copy(s.pair),recovery:copy(s.recovery),records:copy(s.records)},rule:copy(p.rule),kind:p.kind,restores:p.restores,member:true,trainer:s.route==='A'?true:null});
       s.active=next;
       if(planChanged){s.records=slots(next,next.version,s.route);s.recordHistory.push({revision:s.sourceRevision,plan:copy(next),rows:copy(s.records)});}
       for(const n of s.notices)if(n.status==='current')n.status='applied';
       s.status='applied';s.reason='applied';s.proposal=null;s.member=false;s.trainer=false;
      }else fail('action');
     }
    }
   }
   if(opt.fault==='before_commit')fail('atomic_fault');
   if(s.audit.length>=100||s.recordHistory.length>30||s.recoveryHistory.length>30)fail('memory_limit');
   s.epoch++;s.audit.push({id:e.id,action:e.action,actor:e.actor,source:s.sourceRevision,version:s.active.version,at:s.clock,status:s.status});done.set(e.id,fp);
   return {ok:true,reason:'success',state:view()};
  }catch(err){s=old;return {ok:false,reason:err.message,state:view()};}
 }
 assess();
 return Object.freeze({event,command,view});
}
const api={base,create,copy,same,slots};if(node)module.exports=api;else root.FMZ20Model=api;
})(globalThis);
