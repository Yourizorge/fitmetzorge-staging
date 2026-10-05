(function(r){'use strict';const M=typeof module==='object'?require('./model.js'):r.FMZ20Model;
const scenarios=[
['today',['Vandaag: plan en registratie','Today: plan and records','Heute: Plan und Eintraege'],'missing'],
['arrive',['Nieuwe herstelregistratie','New recovery record','Neuer Erholungseintrag'],'checkin'],
['routeA',['Route A: drie aparte stappen','Route A: three separate steps','Route A: drei getrennte Schritte'],'applied'],
['routeB',['Route B: zonder trainer','Route B: without trainer','Route B: ohne Trainer'],'applied'],
['correct',['Correctie na bevestiging','Correction after confirmation','Korrektur nach Bestaetigung'],'checkin'],
['record',['Training en voeding geregistreerd','Training and nutrition recorded','Training und Ernaehrung erfasst'],'checkin'],
['edit',['Handmatig plan bewerken','Edit plan manually','Plan manuell bearbeiten'],'manual'],
['complete',['Check-in apart afronden','Complete check-in separately','Check-in separat abschliessen'],'checkin'],
['duplicate',['Geen dubbele verwerking','No duplicate processing','Keine doppelte Verarbeitung'],'unchanged'],
['missing',['Ontbrekende gegevens','Missing data','Fehlende Daten'],'missing'],
['rule',['Ontbrekende gekoppelde regel','Missing linked rule','Fehlende verknuepfte Regel'],'rule_missing'],
['conflict',['Bronconflict','Source conflict','Quellkonflikt'],'source_conflict'],
['expiry',['Bron verlopen','Expired source','Abgelaufene Quelle'],'expired'],
['health',['Klacht voorbij is geen vrijgave','Resolved complaint is not clearance','Beschwerde vorbei ist keine Freigabe'],'safety'],
['consent',['Toestemming ingetrokken','Consent withdrawn','Einwilligung widerrufen'],'consent'],
['atomic',['Fout tijdens toepassing','Failure during application','Fehler bei Anwendung'],'atomic_fault'],
['restore',['Terugzetten als nieuwe versie','Restore as new version','Wiederherstellen als neue Version'],'applied'],
['stale',['Oude bevestiging geweigerd','Old confirmation rejected','Alte Bestaetigung abgelehnt'],'version_conflict']
].map(([id,title,reason])=>({id,title,reason}));
function arrive(m,value=6){const row=m.view().recovery.rows.at(-1);return m.command(m.event('recovery',{id:row.id,version:row.version,value}));}
function approve(m){let v=m.command(m.event('accept'));if(!v.ok)throw Error(v.reason);if(m.view().route==='A'){v=m.command(m.event('approve',{},'trainer'));if(!v.ok)throw Error(v.reason);}}
function apply(m,opt){approve(m);return m.command(m.event('apply'),opt);}
function record(m,kind,value){const row=m.view().records.find(x=>x.kind===kind);return m.command(m.event('record',{id:row.id,version:row.revision,planVersion:row.planVersion,value,rir:kind==='training'?0:null,rpe:kind==='training'?7:null,unit:row.unit}));}
function run(id){
 if(!scenarios.some(x=>x.id===id))throw Error('scenario');const m=M.create(M.base(id==='routeA'?'A':'B')),results=[];
 const call=(a,d={},actor='member',opt)=>{const x=m.command(m.event(a,d,actor),opt);results.push(x);return x;};
 let before=null,last=null;
 if(id!=='today')arrive(m);
 if(['routeA','routeB'].includes(id))last=apply(m);
 if(id==='correct'){approve(m);arrive(m,8);}
 if(id==='record'){approve(m);record(m,'training',0);record(m,'nutrition',175);}
 if(id==='edit'){approve(m);call('edit',{domain:'training_day',value:'fri'});call('edit',{domain:'nutrition_moment',value:'20:00'});}
 if(id==='complete')call('complete');
 if(id==='duplicate'){const e=m.event('accept');m.command(e);before=m.view();last=m.command(e);}
 if(id==='missing'){const row=m.view().recovery.rows[0];call('recovery',{id:row.id,version:row.version,value:null});}
 if(id==='rule')call('missing_rule');if(id==='conflict')call('conflict');if(id==='expiry')call('expire');
 if(id==='health'){call('health',{value:'current'});call('health',{value:'reported_resolved'});}
 if(id==='consent'){call('revoke');before=m.view();last=arrive(m,8);}
 if(id==='atomic'){approve(m);before=m.view();last=call('apply',{},'member',{fault:'after_nutrition'});}
 if(id==='restore'){apply(m);call('edit',{domain:'time',value:'20:00'});apply(m);call('restore',{version:2});last=apply(m);}
 if(id==='stale'){const e=m.event('accept');arrive(m,8);before=m.view();last=m.command(e);}
 return {id,model:m,before,last,results};
}
function assess(x){
 const s=x.model.view(),id=x.id;let pass=false;
 if(id==='today')pass=s.active.version===1&&s.records.every(x=>x.value===null)&&s.proposal===null;
 if(id==='arrive')pass=s.status==='pending'&&s.facts[0].delta.numerator===-270&&s.proposal.target.cadence.option==='daily';
 if(['routeA','routeB'].includes(id))pass=s.active.version===2&&s.history.length===2&&s.history[1].trainer===(id==='routeA'?true:null);
 if(id==='correct')pass=!s.member&&s.status==='pending'&&s.recoveryHistory.length===3&&s.facts[1].current.sum===20;
 if(id==='record')pass=!s.member&&s.records.find(x=>x.kind==='training').value===0&&s.records.find(x=>x.kind==='training').actualRir===0&&s.records.find(x=>x.kind==='nutrition').value===175;
 if(id==='edit')pass=!s.member&&s.proposal.target.training.sessions[0].day==='fri'&&s.proposal.target.nutrition.meals[0].moment==='20:00'&&s.active.training.sessions[0].day==='mon';
 if(id==='complete')pass=s.completion.version===2&&s.active.version===1&&s.records.every(x=>x.value===null);
 if(id==='duplicate')pass=x.last.reason==='idempotent'&&M.same(s,x.before);
 if(id==='missing')pass=!s.proposal&&s.facts.length===0&&s.reason==='missing';
 if(id==='rule')pass=!s.proposal&&s.facts.length===2&&s.reason==='rule_missing';
 if(['conflict','expiry','health'].includes(id))pass=!s.proposal&&s.reason===({conflict:'source_conflict',expiry:'expired',health:'safety'})[id];
 if(id==='consent')pass=!s.proposal&&!x.last.ok&&x.last.reason==='consent'&&M.same(s,x.before);
 if(['atomic','stale'].includes(id))pass=!x.last.ok&&x.last.reason===(id==='atomic'?'atomic_fault':'version_conflict')&&M.same(s,x.before);
 if(id==='restore')pass=s.active.version===4&&s.active.cadence.at==='08:00'&&s.history[3].restores===2&&s.history[0].cadence.option==='after_workout';
 return {pass,status:s.status,version:s.active.version,reason:s.reason,sourceRevision:s.sourceRevision};
}
const api={scenarios,run,assess,arrive,approve,apply,record};if(typeof module==='object')module.exports=api;else r.FMZ20Review=api;
})(globalThis);
