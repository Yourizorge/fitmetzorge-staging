/* Memory-only source-bound check-ins. No server authority, medical rule or plan writes. */
(function(root){"use strict";const D=typeof module==='object'?require('./data.js'):root.FMZ19Data,copy=x=>structuredClone(x),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),int=Number.isSafeInteger,fail=c=>{throw Error(c);};
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&same(Object.keys(x).sort(),keys.slice().sort());
function validate(f){
 if(!exact(f,['synthetic_only','route','subject','clock','plan','rows','reportedRecovery','consent','health','rule','sources','agenda','cadence'])||f.synthetic_only!==true||f.subject!=='syn19-member'||!['A','B'].includes(f.route)||!int(f.clock))fail('binding');
 if(!same(f.plan,D.plans[f.route])||!Array.isArray(f.rows)||f.rows.length!==12)fail('plan_binding');
 if(!exact(f.sources,['version','issued','expires'])||!int(f.sources.version)||f.sources.version<1||!int(f.sources.issued)||!int(f.sources.expires)||f.sources.expires<=f.sources.issued||f.sources.expires-f.sources.issued>D.DAY)fail('source');
 const ids=new Set(),slots=new Set();
 for(const x of f.rows){
  if(!exact(x,['id','version','subject','metric','day','value','unit','method','coverage','quality','plan','planVersion'])||!D.metrics[x.metric]||!/^syn19-(sleep|recovery)-[0-5]$/.test(x.id)||ids.has(x.id)||!int(x.version)||x.version<1||x.subject!==f.subject||x.plan!==f.plan.id||x.planVersion!==f.plan.version||!int(x.day)||x.day%D.DAY||slots.has(x.metric+':'+x.day))fail('record_binding');
  if(!x.id.startsWith('syn19-'+x.metric+'-')||x.day!==Math.floor(D.clock/D.DAY)*D.DAY-(6-Number(x.id.at(-1)))*D.DAY)fail('record_binding');
  ids.add(x.id);slots.add(x.metric+':'+x.day);
 }
 if(!f.agenda||f.agenda.plan!==f.plan.id||f.agenda.planVersion!==f.plan.version||!same(f.agenda.allowedTimes,['08:00','20:00'])||f.agenda.nextTraining?.date!=='2026-10-05'||f.agenda.nextTraining.day!=='mon'||f.agenda.nextTraining.at!=='18:00'||f.agenda.checkin?.id!=='syn19-checkin-1'||f.agenda.checkin.date!=='2026-09-30'||f.agenda.checkin.at!=='19:00')fail('agenda');
 if(!same(f.cadence,{version:1,option:'after_workout',at:'19:00'})||!['low','okay',null].includes(f.reportedRecovery)||typeof f.consent!=='boolean'||!['none','current','reported_resolved','unclassified','missing_context'].includes(f.health))fail('context');
 return true;
}
function compare(f){
 validate(f);if(f.sources.issued>f.clock||f.sources.expires<=f.clock)fail('expired');
 const end=Math.floor(D.clock/D.DAY)*D.DAY,calculations=[];if(end>f.clock||f.clock-end>D.DAY)fail('window');
 for(const metric of ['sleep','recovery']){
  const m=D.metrics[metric],rows=f.rows.filter(x=>x.metric===metric).sort((a,b)=>a.day-b.day);
  if(rows.length!==6||rows.some((x,i)=>x.day!==end-(6-i)*D.DAY))fail('window');
  if(rows.some(x=>x.value===null||x.coverage!=='complete'||x.quality!=='confirmed'))fail('missing');
  if(rows.some(x=>!int(x.value)||x.value<m.min||x.value>m.max||x.unit!==m.unit||x.method!==m.method))fail('incomparable');
  const sums=[rows.slice(0,3),rows.slice(3)].map(xs=>xs.reduce((n,x)=>n+x.value,0));
  calculations.push({metric,unit:m.unit,previous:{sum:sums[0],divisor:3},current:{sum:sums[1],divisor:3},delta:{numerator:sums[1]-sums[0],divisor:3},refs:rows.map(x=>({id:x.id,version:x.version,day:x.day}))});
 }
 return calculations;
}
function option(f){
 const q=f.rule,expected=D.options.find(x=>x.id==='daily');
 if(!q)fail('rule_missing');
 if(!exact(q,['id','version','origin','option','optionVersion','allowedRestore','plan','planVersion','status','at','expires','trainer'])||q.id!=='syn19-'+f.route+'-checkin'||q.version!==1||q.origin!==expected.source||q.option!=='daily'||q.optionVersion!==1||!same(q.allowedRestore,['after_workout','daily'])||q.plan!==f.plan.id||q.planVersion!==f.plan.version||q.status!=='active')fail('rule_conflict');
 if(!int(q.at)||!int(q.expires)||q.at>f.clock||q.expires<=f.clock)fail('rule_expired');
 if(f.route==='A'&&!same(q.trainer,{id:'syn19-trainer',relationshipVersion:1,status:'active'})||f.route==='B'&&q.trainer!==null)fail('trainer');
 if(f.reportedRecovery!==expected.requiresReportedRecovery)fail('classification_missing');
 return {option:'daily',optionVersion:1,at:f.agenda.allowedTimes[0],origin:expected.origin,rule:q.id,ruleVersion:q.version,changesTraining:false,changesNutrition:false};
}
function nextCheckin(s){
 const cadence=s.active;if(!['daily','after_workout'].includes(cadence.option)||!/^\d{2}:\d{2}$/.test(cadence.at))fail('agenda');
 const day=cadence.option==='after_workout'?Date.parse(s.input.agenda.nextTraining.date+'T00:00:00Z'):Math.floor(s.clock/D.DAY)*D.DAY;
 const [h,m]=cadence.at.split(':').map(Number);if(h>23||m>59)fail('agenda');
 let at=day+(h*60+m)*60000;if(cadence.option==='daily'&&at<=s.clock)at+=D.DAY;
 return {date:new Date(at).toISOString().slice(0,10),at:cadence.at,zone:'UTC',cadenceVersion:cadence.version};
}
function create(input){
 input=copy(input);
 let s={input:copy(input),clock:input.clock,epoch:0,revision:0,status:'missing',facts:[],reason:'missing',cards:[],currentCard:null,proposal:null,member:false,trainer:false,active:copy(input.cadence),history:[copy(input.cadence)],recordsHistory:[copy(input.rows)],audit:[],completion:null,revoked:false,healthLatch:input.health!=='none',planStale:false,external_calls:0,automatic_actions_allowed:false,physical_advice_authorized:false};
 const done=new Map();let serial=0;const view=()=>copy(s),basis=()=>JSON.stringify([s.epoch,s.revision,s.input,s.active]),event=(action,data={},actor='member')=>({id:'syn19-request-'+(++serial),action,data:copy(data),actor,subject:'syn19-member',route:input.route,basis:basis()});
 function access(){if(s.revoked||!s.input.consent)fail('consent');if(s.clock>=s.input.sources.expires)fail('expired');}
 function gate(){access();if(s.healthLatch)fail('safety');if(s.planStale)fail('plan_changed');}
 function retire(){for(const c of s.cards)if(c.state!=='superseded')c.state='superseded';s.currentCard=null;s.proposal=null;s.member=false;s.trainer=false;}
 function assess(){
  retire();s.facts=[];s.input.clock=s.clock;
  try{
   access();s.facts=compare(s.input);gate();
   if(s.facts.every(x=>x.delta.numerator===0)){s.status='facts';s.reason='unchanged';return;}
   const key='syn19-observation-'+s.revision;
   const card={id:key,sourceRevision:s.revision,state:'pending',kind:'record_review',reason:'record_change'};
   s.cards.push(card);s.currentCard=key;
   try{const choice=option(s.input);if(s.active.option===choice.option){s.status='facts';s.reason='already_planned';return;}s.proposal={...choice,sourceRevision:s.revision,base:s.active.version,restores:null};s.status='member_pending';s.reason='record_change';}
   catch(e){s.status='facts';s.reason=e.message;card.reason=e.message;}
  }catch(e){s.status='blocked';s.reason=e.message;}
 }
 function command(e,opt={}){
  const old=copy(s);try{
   validate(input);
   if(!exact(e,['id','action','data','actor','subject','route','basis'])||!/^syn19-request-[a-zA-Z0-9-]+$/.test(e.id)||e.subject!=='syn19-member'||e.route!==input.route||!['member','trainer'].includes(e.actor)||!e.data||Array.isArray(e.data))fail('binding');
   const fp=JSON.stringify(e);if(done.has(e.id)){if(done.get(e.id)!==fp)fail('duplicate_conflict');if(e.action!=='revoke'&&(s.revoked||!s.input.consent))fail('consent');return {ok:true,reason:'idempotent',state:view()};}
   if(e.basis!==basis())fail('version_conflict');
   const trainerAction=e.action==='approve'||e.action==='block';
   if((trainerAction?'trainer':'member')!==e.actor||e.actor==='trainer'&&input.route!=='A')fail('actor');
   if(!['record','edit','restore','context'].includes(e.action)&&!exact(e.data,[]))fail('payload');
   if(e.action==='revoke'){s.revoked=true;retire();s.status='blocked';s.reason='consent';}
   else{
    if(s.revoked||!s.input.consent)fail('consent');
    if(e.action==='record'){
     access();const d=e.data;if(!exact(d,['id','version','value']))fail('payload');const x=s.input.rows.find(x=>x.id===d.id);if(!x||d.version!==x.version)fail('record_version');const m=D.metrics[x.metric];
     if(!(d.value===null||int(d.value)&&d.value>=m.min&&d.value<=m.max))fail('value');
     if(d.value===x.value){done.set(e.id,fp);return {ok:true,reason:'unchanged_record',state:view()};}
     if(s.recordsHistory.length>=20)fail('memory_limit');
     x.value=d.value;x.version++;s.revision++;s.recordsHistory.push(copy(s.input.rows));assess();
    }else if(e.action==='refresh'){access();if(!s.revision){s.revision++;assess();}else{done.set(e.id,fp);return {ok:true,reason:'already_assessed',state:view()};}}
    else if(e.action==='context'){
     if(!exact(e.data,['health'])||!['none','current','reported_resolved','unclassified','missing_context'].includes(e.data.health))fail('context');
     s.input.health=e.data.health;s.healthLatch=s.healthLatch||e.data.health!=='none';s.revision++;assess();
    }else if(e.action==='expire'){s.clock=s.input.sources.expires;s.revision++;assess();}
    else if(e.action==='plan_changed'){s.planStale=true;s.revision++;assess();}
    else if(e.action==='rule_revoked'){if(s.input.rule)s.input.rule.status='revoked';s.revision++;assess();}
    else if(e.action==='complete'){
     access();if(s.completion){done.set(e.id,fp);return {ok:true,reason:'idempotent',state:view()};}
     const row=s.input.rows.find(x=>x.id==='syn19-recovery-5');if(row.value===null)fail('missing');
     s.completion={id:s.input.agenda.checkin.id,record:{id:row.id,version:row.version},at:s.clock};s.reason='checkin_complete';
    }else{
     gate();compare({...s.input,clock:s.clock});option({...s.input,clock:s.clock});
     if(e.action==='edit'){
      if(!exact(e.data,['at'])||!s.input.agenda.allowedTimes.includes(e.data.at)||!s.proposal||!['member_pending','trainer_pending','approved','confirmed'].includes(s.status))fail('time_option');
      s.proposal.at=e.data.at;s.member=false;s.trainer=false;s.status='member_pending';
     }else if(e.action==='accept'){
      if(s.status!=='member_pending'||!s.proposal)fail('status');s.member=true;s.status=input.route==='A'?'trainer_pending':'confirmed';
     }else if(e.action==='approve'){
      if(s.status!=='trainer_pending'||!s.member)fail('status');s.trainer=true;s.status='approved';
     }else if(['reject','block'].includes(e.action)){
      if(!s.proposal||!['member_pending','trainer_pending','approved','confirmed'].includes(s.status)||e.action==='block'&&s.status!=='trainer_pending')fail('status');retire();s.status=e.action==='block'?'blocked':'rejected';s.reason=e.action;
     }else if(e.action==='apply'){
      if(s.status!==(input.route==='A'?'approved':'confirmed')||!s.member||input.route==='A'&&!s.trainer||s.proposal.base!==s.active.version||s.proposal.sourceRevision!==s.revision)fail('version_conflict');
      s.active={version:s.active.version+1,option:s.proposal.option,at:s.proposal.at,sourceRevision:s.revision,restores:s.proposal.restores,member:true,trainer:input.route==='A'?true:null,binding:{plan:s.input.plan.id,planVersion:s.input.plan.version,rule:copy(s.input.rule),sources:copy(s.input.sources),records:s.input.rows.map(x=>({id:x.id,version:x.version})),agenda:copy(s.input.agenda)}};
      s.history.push(copy(s.active));s.status='applied';s.member=false;s.trainer=false;s.cards.find(c=>c.id===s.currentCard).state='reviewed';s.reason='applied';
     }else if(e.action==='restore'){
      if(!exact(e.data,['version'])||s.status!=='applied'||e.data.version===s.active.version)fail('status');const h=s.history.find(x=>x.version===e.data.version);
      if(!h||!D.options.some(x=>x.id===h.option)||!s.input.rule.allowedRestore.includes(h.option))fail('restore');
      s.proposal={option:h.option,optionVersion:1,at:h.at,sourceRevision:s.revision,base:s.active.version,restores:h.version,changesTraining:false,changesNutrition:false};s.member=false;s.trainer=false;s.status='member_pending';s.reason='restore';
     }else fail('action');
    }
   }
   if(opt.fault_before_commit)fail('atomic_fault');
   s.epoch++;s.clock+=1;s.audit.push({id:e.id,actor:e.actor,action:e.action,sourceRevision:s.revision,from:old.active.version,to:s.active.version,at:s.clock,status:s.status});done.set(e.id,fp);return {ok:true,reason:'success',state:view()};
  }catch(e){s=old;return {ok:false,reason:e.message,state:view()};}
 }
 return Object.freeze({event,command,view});
}
const api={create,compare,option,validate,nextCheckin,copy,same};if(typeof module==='object')module.exports=api;else root.FMZ19Model=api;})(globalThis);
