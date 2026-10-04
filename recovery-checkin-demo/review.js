(function(root){"use strict";const M=typeof module==='object'?require('./model.js'):root.FMZ19Model,F=typeof module==='object'?require('./fixtures.js'):root.FMZ19Fixtures;
const rows=[
['arrival',['Nieuwe registratie','New record','Neuer Eintrag'],'record_change','member_pending',1],
['trainer',['Met trainer','With trainer','Mit Trainer'],'applied','applied',2],
['duplicate',['Geen dubbele melding','No duplicate notice','Keine doppelte Meldung'],'record_change','member_pending',1],
['correction',['Registratie gecorrigeerd','Corrected record','Korrigierter Eintrag'],'record_change','member_pending',1],
['unchanged',['Geen verandering','No change','Keine Aenderung'],'unchanged','facts',1],
['missing',['Slaap ontbreekt','Sleep missing','Schlaf fehlt'],'missing','blocked',1],
['incomparable',['Andere eenheid','Different unit','Andere Einheit'],'incomparable','blocked',1],
['rule',['Regel ontbreekt','Missing rule','Regel fehlt'],'rule_missing','facts',1],
['no_trainer',['Trainerbevoegdheid ontbreekt','Trainer authority missing','Trainerbefugnis fehlt'],'trainer','facts',1],
['health',['Klacht voorbij gemeld','Reported recovery','Genesung gemeldet'],'safety','blocked',1],
['consent',['Toestemming ingetrokken','Consent withdrawn','Einwilligung widerrufen'],'consent','blocked',1],
['expired',['Bron verlopen','Source expired','Quelle abgelaufen'],'expired','blocked',1],
['complete',['Check-in afronden','Complete check-in','Check-in abschliessen'],'checkin_complete','member_pending',1],
['edit',['Check-intijd aanpassen','Change check-in time','Check-in-Zeit aendern'],'applied','applied',2],
['atomic',['Onderbreking','Interruption','Unterbrechung'],'record_change','confirmed',1],
['restore',['Vorige check-inversie','Previous check-in version','Vorherige Check-in-Version'],'applied','applied',4]];
const scenarios=rows.map(([id,title,reason,status,version])=>({id,title,reason,status,version}));
function run(id){
 const spec=scenarios.find(x=>x.id===id),f=F.copy(F.cases[id]);if(!spec)throw Error('scenario');if(id==='expired')f.sources.expires=f.clock+86400000;
 const model=M.create(f),events=[];const send=(action,data={},actor='member',opt={})=>{const e=model.event(action,data,actor),r=model.command(e,opt);events.push({action,actor,ok:r.ok,reason:r.reason});return e;};
 if(id==='unchanged')send('refresh');
 else{const first=send('record',{id:'syn19-recovery-5',version:1,value:6});
 if(id==='trainer'){send('accept');send('approve');send('approve',{},'trainer');send('apply');}
 if(id==='duplicate'){const r=model.command(first);events.push({action:'replay',ok:r.ok,reason:r.reason});send('record',{id:'syn19-recovery-5',version:2,value:6});}
 if(id==='correction'){send('accept');send('record',{id:'syn19-recovery-5',version:2,value:8});}
 if(id==='health')send('context',{health:'reported_resolved'});
 if(id==='consent'){send('accept');send('revoke');send('apply');}
 if(id==='expired'){send('accept');send('expire');send('apply');}
 if(id==='complete'){send('complete');send('complete');}
 if(id==='edit'){send('accept');send('edit',{at:'20:00'});send('accept');send('apply');}
 if(id==='atomic'){send('accept');send('apply',{},'member',{fault_before_commit:true});}
 if(id==='restore'){send('accept');send('apply');send('restore',{version:1});send('edit',{at:'20:00'});send('accept');send('apply');send('restore',{version:2});send('accept');send('apply');}
 }
 return {spec,model,events};
}
function assess(r,s=r.model.view()){
 let pass=!!r.events.length&&s.reason===r.spec.reason&&s.status===r.spec.status&&s.active.version===r.spec.version&&s.history.length===s.active.version;
 const original=F.cases[r.spec.id].plan;pass=pass&&M.same(s.input.plan,original);
 if(r.spec.id==='duplicate')pass=pass&&s.cards.length===1&&s.recordsHistory.length===2;
 if(r.spec.id==='correction')pass=pass&&s.cards.length===2&&s.cards[0].state==='superseded'&&!s.member&&s.recordsHistory.length===3;
 if(r.spec.id==='complete')pass=pass&&s.completion?.id==='syn19-checkin-1';
 if(r.spec.id==='atomic')pass=pass&&r.events.at(-1).reason==='atomic_fault'&&s.audit.every(x=>x.action!=='apply');
 if(r.spec.id==='trainer')pass=pass&&r.events.some(x=>x.reason==='actor')&&s.active.trainer===true;
 if(r.spec.id==='restore')pass=pass&&s.history[0].option==='after_workout'&&s.history[1].option==='daily'&&s.history[2].at==='20:00'&&s.active.option==='daily'&&s.active.at==='08:00'&&s.active.restores===2&&r.events.some(x=>x.reason==='restore');
 return {pass:!!pass};
}
const api={scenarios,run,assess};if(typeof module==='object')module.exports=api;else root.FMZ19Review=api;})(globalThis);
