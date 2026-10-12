/* Full-plan records over the accepted 20 coordinator; frozen validators are read-only. */
(function(root){'use strict';
const node=typeof module==='object',P=node?require('../combined-plan-demo/model.js'):root.FMZ18Model,F=node?require('../combined-plan-demo/fixtures.js'):root.FMZ18Fixtures,
R=node?require('../recovery-checkin-demo/model.js'):root.FMZ19Model,H=node?require('../recovery-checkin-demo/fixtures.js'):root.FMZ19Fixtures,
T=node?require('../training-rules-demo/model.js'):root.FMZ16Model,N=node?require('../nutrition-rules-demo/model.js'):root.FMZ17Model;
const copy=x=>structuredClone(x),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),int=Number.isSafeInteger,fail=x=>{throw Error(x);},
exact=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&same(Object.keys(x).sort(),k.slice().sort());
function base(route='B'){
 if(!['A','B'].includes(route))fail('binding');const recovery=H.base(route),pair=copy(F.base),b=P.inspect(pair);
 return {synthetic_only:true,person:'syn21-member',route,clock:pair.clock,link:{id:'syn21-link',version:1,aliases:['syn16-member','syn17-member','syn18-member','syn19-member','syn-owner'],training:recovery.plan.id,nutrition:b.nutrition.catalogId,recovery:recovery.subject},pair,recovery};
}
function slots(plan,version,route){
 const workouts=route==='B'?plan.training.sessions.map((x,i)=>({id:'workout-'+(i+1),day:x.day,exercises:x.exercises.map(e=>({id:e.exercise,label:JSON.parse(plan.training.source).exercises.find(z=>z.id===e.exercise)?.label||[e.exercise,e.exercise,e.exercise],sets:Array.from({length:e.sets},(_,j)=>({index:j+1,reps:{min:e.reps,max:e.reps},load:e.load,unit:e.requestedUnit,rir:e.rir,rpe:e.rpe,rule:e.rule,ruleVersion:e.ruleVersion}))}))})):
 [{id:plan.training.workout_id,day:'mon',exercises:plan.training.exercises.map(e=>({id:e.exercise_id,label:e.labels?['nl','en','de'].map(l=>e.labels[l]):[e.exercise_id,e.exercise_id,e.exercise_id],sets:e.sets.map(z=>({...copy(z),unit:z.load?.unit}))}))}];
 const rows=workouts.flatMap(w=>w.exercises.flatMap(e=>e.sets.map(z=>({id:w.id+':'+e.id+':'+z.index,kind:'training',workout:w.id,day:w.day,exercise:e.id,label:e.label,index:z.index,planned:copy(z),unit:z.unit,actual:{load:null,reps:null,rir:null,rpe:null}}))));
 for(const [i,m]of plan.nutrition.meals.entries())for(const x of m.items)rows.push({id:'meal-'+(i+1)+':'+x.food,kind:'nutrition',meal:'meal-'+(i+1),moment:m.moment,recipe:m.recipe,recipeVersion:m.recipeVersion,label:copy(x.name),planned:copy(x),unit:'g',actual:{state:'missing',grams:null}});
 return rows.map(x=>({...x,planVersion:version,revision:1}));
}
function workoutSummary(rows,workout){
 const sets=rows.filter(x=>x.kind==='training'&&x.workout===workout);if(!sets.length)fail('record_binding');
 const lines=sets.map(x=>{const actual=copy(x.actual),range=x.planned.reps,weight=x.planned.load;
  return {id:x.id,exercise:x.exercise,index:x.index,label:copy(x.label),planVersion:x.planVersion,recordVersion:x.revision,planned:copy(x.planned),actual,unit:x.unit,
   repsRelation:actual.reps===null?'missing':actual.reps<range.min?'below':actual.reps>range.max?'above':'within',
   loadDelta:actual.load===null||weight==null||typeof weight==='object'&&weight.value==null?null:actual.load-(typeof weight==='number'?weight:weight.value)};});
 const recorded=sets.filter(x=>x.actual.reps!==null).length,weights=sets.filter(x=>x.actual.load!==null).length;
 return {workout,total:sets.length,recorded,weights,complete:recorded===sets.length&&sets.every(x=>x.planned.load==null||x.actual.load!==null),lines,physical_advice_authorized:false};
}
function foodSummary(rows,plan){
 const foods=rows.filter(x=>x.kind==='nutrition'),resolved=foods.filter(x=>x.actual.state!=='missing'),zero=Object.fromEntries(N.keys.map(k=>[k,0]));
 const totals=resolved.length?N.sum(resolved.map(x=>x.actual.state==='not_eaten'?zero:N.amount({nutrients:x.planned.per100},x.actual.grams))):null;
 const goal=copy(plan.target),delta=totals?Object.fromEntries(N.keys.map(k=>[k,totals[k]-goal.totals[k]])):null;
 return {total:foods.length,recorded:resolved.length,notEaten:foods.filter(x=>x.actual.state==='not_eaten').length,completePlan:resolved.length===foods.length,fullDayIntake:false,totals,goal,delta,units:'millikcal_and_milligrams',source:{catalog:plan.catalogId,version:plan.catalogVersion,rule:plan.ruleId,ruleVersion:plan.ruleVersion}};
}
function sourceKey(row){return JSON.stringify({id:row.id,planVersion:row.planVersion,unit:row.unit,recipe:row.recipe??null,recipeVersion:row.recipeVersion??null,planned:row.planned});}
function create(input=base()){
 if(!same(input,base(input.route)))fail('binding');
 let serial=0;const initial=copy(input),initialPlan={training:copy(input.recovery.plan.training),nutrition:copy(input.recovery.plan.nutrition),cadence:copy(input.recovery.cadence)};
 let s={person:input.person,route:input.route,link:copy(input.link),sourceRevision:1,sourceGeneration:1,epoch:0,clock:input.clock,consent:true,health:false,ruleAvailable:true,conflict:false,
 pair:copy(input.pair),recovery:copy(input.recovery),active:{version:1,...copy(initialPlan)},proposal:null,member:false,trainer:false,status:'missing',reason:'missing',
 history:[],records:[],closed:{},workoutClosures:[],dayClose:null,dayHistory:[],recordHistory:[],recoveryHistory:[copy(input.recovery.rows)],notices:[],facts:[],completion:null,audit:[],external_calls:0,automatic_actions_allowed:false,physical_advice_authorized:false};
 s.history=[{...copy(s.active),sourceRevision:1,sourceGeneration:1,source:copy(input),kind:'original'}];s.records=slots(s.active,1,s.route);s.recordHistory=[{revision:1,plan:copy(s.active),rows:copy(s.records)}];
 const done=new Map(),view=()=>copy(s),basis=()=>JSON.stringify([s.epoch,s.sourceRevision,s.active.version,s.link]),event=(action,data={},actor='member')=>({id:'syn21-request-'+(++serial),action,data:copy(data),actor,person:s.person,route:s.route,basis:basis()});
 function access(){if(!s.consent)fail('consent');if(s.clock>=Math.min(s.pair.link.expires,s.pair.training.expires,s.pair.nutrition.expires,s.recovery.sources.expires))fail('expired');if(s.conflict)fail('source_conflict');}
 function gate(){access();if(s.health)fail('safety');}
 function retire(){s.proposal=null;s.member=false;s.trainer=false;for(const x of s.notices)if(x.status==='current')x.status='superseded';}
 function notice(kind){const id='syn21-notice-'+s.sourceRevision;if(!s.notices.some(x=>x.id===id))s.notices.push({id,sourceRevision:s.sourceRevision,kind,status:'current'});}
 function physical(p){return {training:p.training,nutrition:p.nutrition};}
 function validPlan(p){
  if(s.route==='B'){T.validatePlan(p.training,s.pair.training.fixture.intake,s.pair.training.fixture.catalog,s.clock);N.validatePlan(p.nutrition,s.pair.nutrition.fixture.intake,s.pair.nutrition.fixture.catalog,s.clock);}
  else if(!same(physical(p),physical(initialPlan)))fail('trainer_scope');
 }
 function pending(target,kind,rule,restores=null){s.proposal={target:copy(target),sourceRevision:s.sourceRevision,base:s.active.version,link:copy(s.link),rule:copy(rule),kind,restores};s.member=false;s.trainer=false;s.status='pending';s.reason=kind;notice(kind);}
 function assess(){
  retire();s.facts=[];try{
   access();if(s.sourceRevision>1)notice('record_change');try{s.facts=R.compare({...s.recovery,clock:s.clock});}catch(e){if(s.health)fail('safety');throw e;}gate();
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
   if(!exact(e,['id','action','data','actor','person','route','basis'])||!/^syn21-request-[a-zA-Z0-9-]+$/.test(e.id)||e.person!==s.person||e.route!==s.route||!exact(e.data,Object.keys(e.data||{})))fail('binding');
   const trainer=['approve','block'].includes(e.action);if(e.actor!==(trainer?'trainer':'member')||trainer&&s.route!=='A')fail('actor');
   const fp=JSON.stringify(e);if(done.has(e.id)){if(done.get(e.id)!==fp)fail('duplicate_conflict');if(e.action!=='revoke')access();return {ok:true,reason:'idempotent',state:view()};}
   if(e.basis!==basis())fail('version_conflict');
   if(!['record','finish_workout','recovery','edit','restore','health'].includes(e.action)&&!exact(e.data,[]))fail('payload');
   if(e.action==='revoke'){s.consent=false;sourceChanged();s.status='blocked';s.reason='consent';}
   else{
    access();
    if(e.action==='recovery'){
     const d=e.data;if(!exact(d,['id','version','value']))fail('payload');const row=s.recovery.rows.find(x=>x.id===d.id);if(!row||row.version!==d.version)fail('record_version');
     const max=row.metric==='sleep'?1440:10,min=row.metric==='sleep'?0:1;if(d.value!==null&&(!int(d.value)||d.value<min||d.value>max))fail('value');
     if(row.value===d.value){done.set(e.id,fp);return {ok:true,reason:'unchanged',state:view()};}
     row.value=d.value;row.version++;s.recoveryHistory.push(copy(s.recovery.rows));sourceChanged();assess();
    }else if(e.action==='record'){
     const d=e.data;if(!exact(d,['id','version','planVersion','group','unit','sourceVersion','actual']))fail('payload');
     const row=s.records.find(x=>x.id===d.id);if(!row||row.revision!==d.version||row.planVersion!==d.planVersion||d.group!==(row.workout||row.meal))fail('record_binding');
     if(d.unit!==row.unit||!['kg','lb','g'].includes(d.unit))fail('unit');
     if(d.sourceVersion!==sourceKey(row))fail('record_source');
     const v=d.actual;
     if(row.kind==='training'){
      if(!exact(v,['load','reps','rir','rpe']))fail('payload');
      if(v.load!==null&&(!Number.isFinite(v.load)||v.load<0||v.load>10000)||v.reps!==null&&(!int(v.reps)||v.reps<0||v.reps>10000)||v.rir!==null&&(!int(v.rir)||v.rir<0||v.rir>10)||v.rpe!==null&&(!Number.isFinite(v.rpe)||v.rpe<1||v.rpe>10||!int(v.rpe*2)))fail('value');
     }else{
      if(!exact(v,['state','grams'])||!['missing','eaten','not_eaten'].includes(v.state))fail('payload');
      if(v.state==='missing'&&v.grams!==null||v.state==='not_eaten'&&v.grams!==0||v.state==='eaten'&&(!int(v.grams)||!N.within(v.grams,row.planned.bounds)))fail('portion');
      if(v.state==='eaten')N.amount({nutrients:row.planned.per100},v.grams);
     }
     if(same(v,row.actual)){done.set(e.id,fp);return {ok:true,reason:'unchanged',state:view()};}
     row.actual=copy(v);row.revision++;
     if(row.kind==='training')delete s.closed[row.workout];else s.dayClose=null;
     sourceChanged();s.recordHistory.push({revision:s.sourceRevision,plan:copy(s.active),rows:copy(s.records)});assess();
    }else if(e.action==='finish_workout'){
     if(!exact(e.data,['workout']))fail('payload');
     const summary=workoutSummary(s.records,e.data.workout);if(!summary.recorded)fail('missing');
     const binding=JSON.stringify(summary.lines.map(x=>[x.id,x.planVersion,x.recordVersion]));
     if(s.closed[e.data.workout]?.binding===binding){done.set(e.id,fp);return {ok:true,reason:'idempotent',state:view()};}
     const closure={id:'syn21-finish-'+(s.workoutClosures.length+1),at:s.clock,sourceRevision:s.sourceRevision,plan:copy(s.active),summary,binding};
     s.workoutClosures.push(closure);s.closed[e.data.workout]={id:closure.id,binding};sourceChanged();assess();
    }else if(e.action==='finish_day'){
     const summary=foodSummary(s.records,s.active.nutrition);if(!summary.recorded)fail('missing');
     const binding=JSON.stringify(s.records.filter(x=>x.kind==='nutrition').map(x=>[x.id,x.planVersion,x.revision]));
     if(s.dayClose?.binding===binding){done.set(e.id,fp);return {ok:true,reason:'idempotent',state:view()};}
     const closure={id:'syn21-day-'+(s.dayHistory.length+1),at:s.clock,summary,plan:copy(s.active),rows:copy(s.records.filter(x=>x.kind==='nutrition')),binding};
     s.dayHistory.push(closure);s.dayClose={id:closure.id,binding};sourceChanged();assess();
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
       if(planChanged){s.closed={};s.dayClose=null;s.records=slots(next,next.version,s.route);s.recordHistory.push({revision:s.sourceRevision,plan:copy(next),rows:copy(s.records)});}
       for(const n of s.notices)if(n.status==='current')n.status='applied';
       s.status='applied';s.reason='applied';s.proposal=null;s.member=false;s.trainer=false;
      }else fail('action');
     }
    }
   }
   if(opt.fault==='before_commit')fail('atomic_fault');
   if(s.audit.length>=250||s.recordHistory.length>80||s.recoveryHistory.length>30)fail('memory_limit');
   s.epoch++;s.audit.push({id:e.id,action:e.action,actor:e.actor,source:s.sourceRevision,version:s.active.version,at:s.clock,status:s.status});done.set(e.id,fp);
   return {ok:true,reason:'success',state:view()};
  }catch(err){s=old;return {ok:false,reason:err.message,state:view()};}
 }
 assess();
 return Object.freeze({event,command,view});
}
const api={base,create,copy,same,slots,workoutSummary,foodSummary,sourceKey};if(node)module.exports=api;else root.FMZ21Model=api;
})(globalThis);
