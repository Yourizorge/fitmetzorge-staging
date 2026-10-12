(function(root){'use strict';const M=typeof module==='object'?require('./model.js'):root.FMZ21Model;
const copy=M.copy,same=M.same,act=(m,a,d={},actor='member',opt)=>m.command(m.event(a,d,actor),opt);
function data(row,actual){return {id:row.id,version:row.revision,planVersion:row.planVersion,group:row.workout||row.meal,unit:row.unit,sourceVersion:M.sourceKey(row),actual};}
function register(m,id,actual){const row=m.view().records.find(x=>x.id===id);return act(m,'record',data(row,actual));}
function training(m,workout){let last;for(const r of m.view().records.filter(x=>x.kind==='training'&&(!workout||x.workout===workout)))last=register(m,r.id,{load:r.planned.load?.value??10,reps:r.planned.reps.min,rir:0,rpe:7.5});return last;}
function food(m,meal){let last;for(const r of m.view().records.filter(x=>x.kind==='nutrition'&&(!meal||x.meal===meal)))last=register(m,r.id,{state:'eaten',grams:r.planned.grams});return last;}
function arrive(m,v=6){const r=m.view().recovery.rows.at(-1);return act(m,'recovery',{id:r.id,version:r.version,value:v});}
function approvals(m){act(m,'accept');if(m.view().route==='A')act(m,'approve',{},'trainer');}
const specs=[
 ['full','Alle workouts registreren','Record every workout','Alle Workouts erfassen','full'],
 ['partial','Gedeeltelijk afronden','Finish a partial workout','Teilweise abschliessen','partial'],
 ['zero','Nul en zelfrapportage','Zero and self-report','Nullwert und Selbstauskunft','zero'],
 ['food','Alle maaltijden registreren','Record every meal','Alle Mahlzeiten erfassen','food'],
 ['missing','Ontbrekende maaltijd','Missing meal','Fehlende Mahlzeit','missing_food'],
 ['uneaten','Bewust niet gegeten','Explicitly not eaten','Bewusst nicht gegessen','uneaten'],
 ['portion','Portie buiten catalogus','Portion outside catalogue','Portion ausserhalb des Katalogs','portion'],
 ['unit','Verkeerde gewichtseenheid','Incorrect weight unit','Falsche Gewichtseinheit','unit'],
 ['source','Verkeerde productversie','Incorrect product version','Falsche Produktversion','record_source'],
 ['duplicate','Dubbele registratie en afronding','Duplicate recording and completion','Doppelte Erfassung und Abschluss','duplicate'],
 ['correct','Correctie na goedkeuring','Correction after approval','Korrektur nach Freigabe','correct'],
 ['reopen','Correctie na afronden','Correction after completion','Korrektur nach Abschluss','reopen'],
 ['trainer','Route A: aparte trainerstap','Route A: separate trainer step','Route A: separater Trainerschritt','trainerFlow'],
 ['atomic','Onderbroken toepassing','Interrupted application','Abgebrochene Anwendung','atomic_fault'],
 ['restore','Herstel als nieuwe versie','Restore as a new version','Wiederherstellung als neue Version','restore'],
 ['snapshot','Nieuw plan, oude registratie','New plan, original record','Neuer Plan, alter Eintrag','snapshot'],
 ['health','Actuele klacht','Current complaint','Aktuelle Beschwerde','safety'],
 ['resolved','Zelf gemeld herstel','Self-reported recovery','Selbst gemeldete Erholung','safety'],
 ['consent','Toestemming intrekken','Withdraw consent','Einwilligung widerrufen','consent'],
 ['expired','Verlopen bron','Expired source','Abgelaufene Quelle','expired']
];
const scenarios=specs.map(([id,nl,en,de,reason])=>({id,title:[nl,en,de],reason}));
function run(id){
 if(!scenarios.some(x=>x.id===id))throw Error('scenario');
 const model=M.create(M.base(id==='trainer'?'A':'B')),m=model;let last=null,before=null,proof={};
 const first=()=>m.view().records.find(x=>x.kind==='training'),meal=()=>m.view().records.find(x=>x.kind==='nutrition');
 if(id==='full'){training(m);for(const w of [...new Set(m.view().records.filter(x=>x.kind==='training').map(x=>x.workout))])last=act(m,'finish_workout',{workout:w});}
 if(id==='partial'){const r=first();last=register(m,r.id,{load:null,reps:8,rir:null,rpe:null});last=act(m,'finish_workout',{workout:r.workout});}
 if(id==='zero'){last=register(m,first().id,{load:0,reps:0,rir:0,rpe:7.5});}
 if(id==='food'){food(m);last=act(m,'finish_day');}
 if(id==='missing'){last=food(m,'meal-1');}
 if(id==='uneaten'){last=register(m,meal().id,{state:'not_eaten',grams:0});}
 if(id==='portion'){before=m.view();last=register(m,meal().id,{state:'eaten',grams:1});}
 if(id==='unit'||id==='source'){const row=id==='unit'?first():meal(),d=data(row,id==='unit'?{load:10,reps:10,rir:0,rpe:7.5}:{state:'eaten',grams:200});if(id==='unit')d.unit='lb';else d.sourceVersion+='x';before=m.view();last=act(m,'record',d);}
 if(id==='duplicate'){training(m,'workout-1');const r=first(),e=m.event('record',data(r,r.actual));act(m,'finish_workout',{workout:r.workout});const f=m.event('finish_workout',{workout:r.workout});last=m.command(f);before=m.view();last=m.command(f);proof.finish=same(before,m.view());const current=first(),record=m.event('record',data(current,current.actual));m.command(record);before=m.view();last=m.command(record);}
 if(id==='correct'){arrive(m);approvals(m);proof.approved=m.view().member;last=register(m,first().id,{load:0,reps:0,rir:0,rpe:null});}
 if(id==='reopen'){training(m,'workout-1');act(m,'finish_workout',{workout:'workout-1'});before=copy(m.view().workoutClosures[0]);last=register(m,first().id,{load:12,reps:9,rir:null,rpe:null});}
 if(id==='trainer'){training(m);last=act(m,'finish_workout',{workout:first().workout});arrive(m);act(m,'accept');before=m.view();proof.early=act(m,'apply').ok===false;act(m,'approve',{},'trainer');last=act(m,'apply');}
 if(id==='atomic'){arrive(m);approvals(m);before=m.view();last=act(m,'apply',{},'member',{fault:'after_nutrition'});}
 if(id==='restore'){arrive(m);approvals(m);act(m,'apply');act(m,'edit',{domain:'time',value:'20:00'});approvals(m);act(m,'apply');act(m,'restore',{version:2});approvals(m);last=act(m,'apply');}
 if(id==='snapshot'){training(m);before=copy(m.view().recordHistory);act(m,'edit',{domain:'training_day',value:'fri'});approvals(m);last=act(m,'apply');}
 if(id==='health'||id==='resolved'){training(m,'workout-1');act(m,'finish_workout',{workout:'workout-1'});arrive(m);last=act(m,'health',{value:'current'});if(id==='resolved')last=act(m,'health',{value:'reported_resolved'});}
 if(id==='consent'){food(m,'meal-1');act(m,'revoke');before=m.view();last=register(m,first().id,{load:1,reps:1,rir:null,rpe:null});}
 if(id==='expired'){act(m,'expire');before=m.view();last=food(m,'meal-1');}
 return {id,model,last,before,proof};
}
function assess(r){
 const s=r.model.view(),f=M.foodSummary(s.records,s.active.nutrition),first=s.records.find(x=>x.kind==='training');
 const checks={
 full:()=>Object.keys(s.closed).length===2&&s.workoutClosures.every(x=>x.summary.complete)&&s.workoutClosures.reduce((n,x)=>n+x.summary.recorded,0)===6,
 partial:()=>Object.keys(s.closed).length===1&&!s.workoutClosures[0].summary.complete&&s.workoutClosures[0].summary.recorded===1,
 zero:()=>same(first.actual,{load:0,reps:0,rir:0,rpe:7.5})&&!Object.keys(s.closed).length,
 food:()=>f.recorded===12&&f.totals.energy===1725000&&f.delta.energy===-75000&&f.completePlan&&!f.fullDayIntake&&s.dayClose!==null,
 missing:()=>f.recorded===4&&!f.completePlan&&f.totals.energy===575000&&!f.fullDayIntake,
 uneaten:()=>f.recorded===1&&f.notEaten===1&&f.totals.energy===0&&s.records.filter(x=>x.kind==='nutrition'&&x.actual.state==='missing').length===11,
 portion:()=>!r.last.ok&&r.last.reason==='portion'&&same(s,r.before),
 unit:()=>!r.last.ok&&r.last.reason==='unit'&&same(s,r.before),
 source:()=>!r.last.ok&&r.last.reason==='record_source'&&same(s,r.before),
 duplicate:()=>r.last.ok&&r.last.reason==='idempotent'&&r.proof.finish&&same(s,r.before),
 correct:()=>r.proof.approved&&!s.member&&!s.trainer&&s.status==='pending'&&s.notices.filter(x=>x.status==='current').length===1,
 reopen:()=>!s.closed['workout-1']&&same(s.workoutClosures[0],r.before)&&s.workoutClosures[0].summary.lines[0].actual.reps===10&&first.actual.reps===9,
 trainer:()=>r.proof.early&&s.active.version===2&&s.history[1].trainer===true&&s.workoutClosures[0].summary.recorded===6,
 atomic:()=>!r.last.ok&&r.last.reason==='atomic_fault'&&same(s,r.before),
 restore:()=>s.active.version===4&&s.history.length===4&&s.history[3].restores===2&&s.active.cadence.at==='08:00',
 snapshot:()=>s.active.version===2&&s.active.training.sessions[0].day==='fri'&&s.records.filter(x=>x.kind==='training').every(x=>x.actual.reps===null)&&r.before.every((x,i)=>same(x,s.recordHistory[i]))&&s.recordHistory.at(-2).rows[0].actual.reps===10,
 health:()=>s.health&&!s.proposal&&s.workoutClosures.length===1&&s.reason==='safety',
 resolved:()=>s.health&&!s.proposal&&s.workoutClosures.length===1&&s.reason==='safety',
 consent:()=>!r.last.ok&&r.last.reason==='consent'&&same(s,r.before)&&f.recorded===4,
 expired:()=>!r.last.ok&&r.last.reason==='expired'&&same(s,r.before)
 };
 return {pass:!!checks[r.id](),status:s.status,version:s.active.version,registered:s.records.filter(x=>x.kind==='training'?x.actual.reps!==null:x.actual.state!=='missing').length,finished:Object.keys(s.closed).length,food:f.recorded};
}
const api={scenarios,run,assess,data,register,training,food,arrive,approvals,act};if(typeof module==='object')module.exports=api;else root.FMZ21Review=api;
})(globalThis);
