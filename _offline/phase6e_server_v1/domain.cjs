'use strict';
const crypto=require('node:crypto');
const C=require('../../complete-recording-demo/model.js');
const T=require('../../training-rules-demo/model.js');
const N=require('../../nutrition-rules-demo/model.js');
const P=require('../../combined-plan-demo/model.js');
const R=require('../../recovery-checkin-demo/model.js');
const W=require('./windows.cjs');
const UI=require('./presentation.cjs');
const clone=structuredClone;
const fail=code=>{throw new Error(code);};
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&
 JSON.stringify(Object.keys(x).sort())===JSON.stringify([...keys].sort());
function canonical(x){return JSON.stringify(x===null||typeof x!=='object'?x:
 Array.isArray(x)?x.map(v=>JSON.parse(canonical(v))):
 Object.fromEntries(Object.keys(x).sort().map(k=>[k,JSON.parse(canonical(x[k]))])));}
const hash=x=>crypto.createHash('sha256').update(canonical(x)).digest('hex');
const equal=(a,b)=>hash(a)===hash(b);
const physical=p=>({training:p.training,nutrition:p.nutrition});
const allowed=new Set(['intake','build','record','finish_workout','finish_day','recovery',
 'complete','edit','confirm','approve','apply','reject','block','restore','health','revoke','compare_window','preferences']);

function initial(route){
 const source=C.base(route),s=C.create(source).view();
 return {...s,revision:0,initialSource:source,sourceHash:hash(source),
  intakeHistory:[clone(source.pair)],healthLatch:false,review:null,
  consentExpires:null,comparison:null,comparisonHistory:[],preferences:structuredClone(UI.defaults),server_candidate:true,synthetic_only:true};
}
function invalidate(s,external=true){
 s.sourceRevision++;s.review=null;s.proposal=null;s.member=false;s.trainer=false;
 s.comparison=null;
 if(external)s.sourceGeneration++;
 for(const n of s.notices)if(n.status==='current')n.status='superseded';
 s.sourceHash=hash({pair:s.pair,recovery:s.recovery,records:s.records,health:s.healthLatch});
}
function access(s){
 if(!s.consent)fail('consent');
 if(s.clock>=Math.min(s.pair.link.expires,s.pair.training.expires,s.pair.nutrition.expires,
 s.recovery.sources.expires))fail('expired_source');
}
function physicalGate(s){access(s);if(s.healthLatch)fail('safety');}
function validTarget(s,target){
 if(s.route==='B'){
  T.catalog(s.pair.training.fixture.catalog,s.clock);
  T.intake(s.pair.training.fixture.intake,s.pair.training.fixture.catalog,s.clock);
  T.validatePlan(target.training,s.pair.training.fixture.intake,s.pair.training.fixture.catalog);
  N.validatePlan(target.nutrition,s.pair.nutrition.fixture.intake,s.pair.nutrition.fixture.catalog,s.clock);
 }else if(!equal(physical(target),physical(s.history[0])))fail('trainer_scope');
}
function offer(s,target,kind,rule,restores=null){
 physicalGate(s);validTarget(s,target);
 s.review={target:clone(target),base:s.active.version,source:s.sourceHash,
  sourceRevision:s.sourceRevision,kind,rule:clone(rule),restores,member:false,trainer:false};
 s.status='pending';s.reason=kind;
}
function assess(s){
 s.facts=[];s.status='facts';s.reason='registration';
 const key=hash({source:s.sourceHash,revision:s.sourceRevision});
 if(!s.notices.some(n=>n.id===key))s.notices.push({id:key,sourceRevision:s.sourceRevision,
  status:'current',kind:'record_review',text_key:'records_changed'});
 try{
  access(s);s.facts=R.compare({...s.recovery,clock:s.clock});
  physicalGate(s);
  if(!equal(physical(s.active),physical(s.history[0])))fail('plan_binding');
  if(s.facts.every(f=>f.delta.numerator===0))return;
  const option=R.option({...s.recovery,clock:s.clock});
  if(s.active.cadence.option===option.option)return;
  offer(s,{...physical(s.active),cadence:{option:option.option,at:option.at}},'checkin',s.recovery.rule);
 }catch(e){s.reason=e.message;}
}
function validateActual(row,actual){
 if(row.kind==='training'){
  if(!exact(actual,['load','reps','rir','rpe']))fail('payload');
  if(actual.load!==null&&(!Number.isFinite(actual.load)||actual.load<0||actual.load>10000)||
   actual.reps!==null&&(!Number.isSafeInteger(actual.reps)||actual.reps<0||actual.reps>10000)||
   actual.rir!==null&&(!Number.isSafeInteger(actual.rir)||actual.rir<0||actual.rir>10)||
   actual.rpe!==null&&(!Number.isFinite(actual.rpe)||actual.rpe<1||actual.rpe>10||!Number.isInteger(actual.rpe*2)))fail('value');
 }else{
  if(!exact(actual,['state','grams'])||!['missing','eaten','not_eaten'].includes(actual.state))fail('payload');
  if(actual.state==='missing'&&actual.grams!==null||actual.state==='not_eaten'&&actual.grams!==0||
   actual.state==='eaten'&&(!Number.isSafeInteger(actual.grams)||!N.within(actual.grams,row.planned.bounds)))fail('portion');
  if(actual.state==='eaten')N.amount({nutrients:row.planned.per100},actual.grams);
 }
}
function transition(input,request,role){
 if(!input?.synthetic_only||!input.server_candidate)fail('synthetic_scope');
 if(!exact(request,['action','data'])||!allowed.has(request.action)||!request.data||
  typeof request.data!=='object'||Array.isArray(request.data))fail('payload');
 const {action,data}=request,s=clone(input),trainer=['approve','block'].includes(action);
 if(role!==(trainer?'trainer':'member')||trainer&&s.route!=='A')fail('actor');
 if(!['intake','record','finish_workout','recovery','edit','restore','health','compare_window','preferences'].includes(action)&&!exact(data,[]))fail('payload');
 access(s);
 if(s.revision>=250)fail('synthetic_capacity');
 if(action==='preferences'){
  const value=UI.preferences(data);
  if(equal(s.preferences||UI.defaults,value))return clone(input);
  s.preferences=value;
 }else if(action==='compare_window'){
  if(!exact(data,['bundle']))fail('payload');
  const compared=W.compare(s,data.bundle);
  if(s.comparison?.bundleHash===compared.bundleHash)return clone(input);
  if(s.comparisonHistory.length&&compared.revision<=s.comparisonHistory.at(-1).revision)fail('comparison_version');
  invalidate(s);s.comparison=compared;s.comparisonHistory.push(clone(compared));
  s.status='facts';s.reason='comparison';s.facts=compared.facts;
  const id=hash({window:compared.bundleHash});
  if(!s.notices.some(n=>n.id===id))s.notices.push({id,status:'current',kind:'record_review',sourceRevision:s.sourceRevision,text_key:'records_changed'});
 }else if(action==='revoke'){s.consent=false;invalidate(s);s.status='blocked';s.reason='consent';}
 else if(action==='health'){
  if(!exact(data,['value'])||!['current','reported_resolved','none'].includes(data.value))fail('payload');
  s.healthLatch=s.healthLatch||data.value!=='none';s.health=s.healthLatch;
  s.recovery.health=data.value;invalidate(s);assess(s);
 }else if(action==='intake'){
  if(s.route!=='B')fail('route');
  if(!exact(data,['training','nutrition'])||!data.training||!data.nutrition)fail('payload');
  // Inputs are recorded as supplied. Only the frozen validators can admit them.
  s.pair.training.fixture.intake=clone(data.training);
  s.pair.nutrition.fixture.intake=clone(data.nutrition);
  s.pair.revision++;s.pair.training.revision++;s.pair.nutrition.revision++;
  s.healthLatch=s.healthLatch||data.training.health!=='none'||
   data.nutrition.health?.status!=='known'||data.nutrition.health.value!=='none';
  if(data.training.consent!==true||data.nutrition.consent?.status!=='known'||
   data.nutrition.consent.value!==true)s.consent=false;
  s.intakeHistory.push(clone(s.pair));invalidate(s);s.status='reassess';s.reason=s.consent?'intake':'consent';
 }else if(action==='build'){
  physicalGate(s);
  if(s.route==='B'){
   const pair=P.inspect(s.pair,s.clock);
   offer(s,{training:pair.training,nutrition:pair.nutrition,cadence:clone(s.active.cadence)},
    'joint_plan',{training:pair.training.catalogId||s.pair.training.fixture.catalog.id,
     trainingVersion:s.pair.training.fixture.catalog.version,nutrition:pair.nutrition.ruleId,
     nutritionVersion:pair.nutrition.ruleVersion});
  }else{assess(s);if(!s.review)fail(s.reason);}
 }else if(action==='record'){
  if(!exact(data,['id','version','planVersion','unit','source','actual']))fail('payload');
  const row=s.records.find(x=>x.id===data.id);
  if(!row||row.revision!==data.version||row.planVersion!==data.planVersion)fail('record_binding');
  if(data.unit!==row.unit||!['kg','lb','g'].includes(data.unit))fail('unit');
  if(data.source!==hash({planned:row.planned,planVersion:row.planVersion,unit:row.unit}))fail('record_source');
  validateActual(row,data.actual);
  if(equal(row.actual,data.actual))return clone(input);
  row.actual=clone(data.actual);row.revision++;
  if(row.kind==='training')delete s.closed[row.workout];else s.dayClose=null;
  invalidate(s);s.recordHistory.push({revision:s.sourceRevision,plan:clone(s.active),rows:clone(s.records)});
  assess(s);
 }else if(action==='finish_workout'){
  if(!exact(data,['workout']))fail('payload');
  const summary=C.workoutSummary(s.records,data.workout);
  if(!summary.recorded)fail('missing');
  const binding=hash(summary.lines);
  if(s.closed[data.workout]?.binding===binding)return clone(input);
  const closure={id:'finish-'+(s.workoutClosures.length+1),binding,summary,
   sourceRevision:s.sourceRevision,plan:clone(s.active),at:s.clock};
  s.closed[data.workout]={id:closure.id,binding};s.workoutClosures.push(closure);
  invalidate(s);assess(s);
 }else if(action==='finish_day'){
  const summary=C.foodSummary(s.records,s.active.nutrition);
  if(!summary.recorded)fail('missing');
  const rows=s.records.filter(x=>x.kind==='nutrition'),binding=hash(rows);
  if(s.dayClose?.binding===binding)return clone(input);
  s.dayClose={id:'day-'+(s.dayHistory.length+1),binding};
  s.dayHistory.push({...s.dayClose,summary,plan:clone(s.active),rows:clone(rows)});
  invalidate(s);assess(s);
 }else if(action==='recovery'){
  if(!exact(data,['id','version','value']))fail('payload');
  const row=s.recovery.rows.find(x=>x.id===data.id);
  if(!row||row.version!==data.version)fail('record_binding');
  const min=row.metric==='sleep'?0:1,max=row.metric==='sleep'?1440:10;
  if(data.value!==null&&(!Number.isSafeInteger(data.value)||data.value<min||data.value>max))fail('value');
  if(row.value===data.value)return clone(input);
  row.value=data.value;row.version++;s.recoveryHistory.push(clone(s.recovery.rows));
  invalidate(s);assess(s);
 }else if(action==='complete'){
  const row=s.recovery.rows.at(-1);if(row.value===null)fail('missing');
  if(s.completion?.version===row.version)return clone(input);
  s.completion={id:s.recovery.agenda.checkin.id,record:row.id,version:row.version};
  invalidate(s);assess(s);
 }else if(action==='edit'){
  physicalGate(s);if(!exact(data,['domain','value']))fail('payload');
  const target=clone(s.review?.target||s.active);
  if(data.domain==='time'){
   R.compare({...s.recovery,clock:s.clock});const o=R.option({...s.recovery,clock:s.clock});
   if(!s.recovery.agenda.allowedTimes.includes(data.value))fail('time');
   target.cadence={option:o.option,at:data.value};
  }else if(s.route==='B'&&data.domain==='training_day')target.training.sessions[0].day=data.value;
  else if(s.route==='B'&&data.domain==='training_exercise'){
   const d=data.value;
   if(!exact(d,['session','index','exercise','sets','reps','rest','rir','rpe'])||
      !Number.isSafeInteger(d.session)||!Number.isSafeInteger(d.index))fail('payload');
   const catalog=s.pair.training.fixture.catalog,intake=s.pair.training.fixture.intake;
   const session=target.training.sessions[d.session],exercise=session?.exercises[d.index];
   if(!exercise)fail('plan_source');
   const rule=T.selectRule(catalog,intake,exercise.role);
   const option=T.eligible(catalog,intake,rule).find(e=>e.id===d.exercise);
   if(!option)fail('excluded');
   Object.assign(exercise,{exercise:d.exercise,type:option.type,sets:d.sets,reps:d.reps,
    rest:d.rest,rir:d.rir,rpe:d.rpe,history:T.historical(intake,d.exercise)});
   exercise.seconds=T.seconds(exercise,rule);
   session.seconds=catalog.overhead_seconds+session.exercises.reduce((n,e)=>n+e.seconds,0);
  }
  else if(s.route==='B'&&data.domain==='nutrition_portion'){
   const d=data.value;
   if(!exact(d,['meal','item','grams'])||!Number.isSafeInteger(d.meal)||!Number.isSafeInteger(d.item))fail('payload');
   const raw=N.raw(target.nutrition);
   if(!raw[d.meal]?.items?.[d.item])fail('plan_source');
   raw[d.meal].items[d.item].grams=d.grams;
   target.nutrition=N.calculate(raw,s.pair.nutrition.fixture.intake,s.pair.nutrition.fixture.catalog,s.clock);
  }
  else if(s.route==='B'&&data.domain==='nutrition_moment'){
   const raw=N.raw(target.nutrition);raw[0].moment=data.value;
   target.nutrition=N.calculate(raw,s.pair.nutrition.fixture.intake,s.pair.nutrition.fixture.catalog,s.clock);
  }else fail('edit_scope');
  invalidate(s,false);offer(s,target,data.domain,data.domain==='time'?s.recovery.rule:{
   training:s.pair.training.fixture.catalog.id,trainingVersion:s.pair.training.fixture.catalog.version,
   nutrition:s.pair.nutrition.fixture.catalog.id,nutritionVersion:s.pair.nutrition.fixture.catalog.version});
 }else if(action==='restore'){
  physicalGate(s);if(!exact(data,['version'])||!Number.isSafeInteger(data.version))fail('payload');
  const prior=s.history.find(x=>x.version===data.version);
  if(!prior||prior.version===s.active.version)fail('restore_version');
  if(prior.sourceGeneration!==s.sourceGeneration)fail('restore_source');
  validTarget(s,prior);
  if(!equal(prior.cadence,s.active.cadence)){
   const o=R.option({...s.recovery,clock:s.clock});
   if(prior.cadence.option!==o.option||!s.recovery.agenda.allowedTimes.includes(prior.cadence.at))fail('restore_rule');
  }
  if(prior.sources&&!equal(prior.sources.pair,s.pair))fail('restore_source');
  offer(s,prior,'restore',{restores:data.version},data.version);
 }else{
  physicalGate(s);const p=s.review;
  if(!p||p.base!==s.active.version||p.source!==s.sourceHash)fail('version_conflict');
  validTarget(s,p.target);
  if(action==='confirm'){
   if(p.member)return clone(input);
   p.member=true;s.status=s.route==='A'?'trainer_pending':'confirmed';
  }else if(action==='approve'){
   if(!p.member)fail('member_confirmation');
   if(p.trainer)return clone(input);
   p.trainer=true;s.status='approved';
  }else if(action==='reject'||action==='block'){
   s.review=null;s.status='rejected';s.reason=action;
  }else if(action==='apply'){
   if(!p.member||s.route==='A'&&!p.trainer)fail('approvals');
   const next={...clone(p.target),version:s.active.version+1};
   const changed=!equal(physical(next),physical(s.active));
   s.history.push({...clone(next),sources:{pair:clone(s.pair),recovery:clone(s.recovery)},
    sourceRevision:s.sourceRevision,sourceGeneration:s.sourceGeneration,sourceHash:s.sourceHash,kind:p.kind,restores:p.restores,
    approvals:{member:p.member,trainer:s.route==='A'?p.trainer:null}});
   s.active=next;
   if(changed){s.records=C.slots(next,next.version,s.route);s.closed={};s.dayClose=null;
    s.recordHistory.push({revision:s.sourceRevision,plan:clone(next),rows:clone(s.records)});}
   s.review=null;s.status='active';s.reason='applied';
  }
 }
 s.revision++;s.audit.push({revision:s.revision,action,role,source:s.sourceHash,plan:s.active.version});
 return s;
}
function view(s){
 return {...clone(s),preferences:clone(s.preferences||UI.defaults),editorOptions:UI.options(s),
  plannedNutrition:UI.nutrition(s.active.nutrition),progress:UI.progress(s),
  comparisonExample:W.example(s),foodSummary:C.foodSummary(s.records,s.active.nutrition),
  reflections:[...new Set(s.records.filter(x=>x.kind==='training').map(x=>x.workout))].map(w=>C.workoutSummary(s.records,w)),
  unresolvedComparisons:s.comparison?[]:[{metric:'training',reason:'complete_comparable_multi_day_window_missing'},
                        {metric:'nutrition',reason:'complete_comparable_multi_day_window_missing'}],
  records:s.records.map(row=>({...clone(row),source:hash({planned:row.planned,planVersion:row.planVersion,unit:row.unit})}))};
}
module.exports={initial,transition,view,hash,canonical,validateActual};
