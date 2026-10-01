(function(root){"use strict";
const M=typeof module==='object'?require('./model.js'):root.FMZ18Model,F=typeof module==='object'?require('./fixtures.js'):root.FMZ18Fixtures;
const rows=[
 ['valid',['Twee geldige plannen','Two valid plans','Zwei gueltige Plaene'],['Zelfde fictieve lid, expliciete doelen en tweemaal training.','Same fictional member, explicit goals and two workouts.','Gleiches fiktives Mitglied, explizite Ziele und zwei Trainings.'],'success','pending',0],
 ['missing',['Verplicht gegeven ontbreekt','Required data missing','Pflichtangabe fehlt'],['Leeftijd ontbreekt in de voedingsintake.','Age is missing in the nutrition intake.','Alter fehlt in der Ernaehrungsanamnese.'],'nutrition:missing:age','intake',0],
 ['identity',['Ander bronaccount','Different source account','Anderes Quellkonto'],['Voedingsbron hoort bij een andere fictieve identiteit.','Nutrition source belongs to another fictional identity.','Ernaehrungsquelle gehoert zu einer anderen fiktiven Identitaet.'],'identity','intake',0],
 ['frequency',['Frequenties spreken elkaar tegen','Conflicting frequencies','Widerspruechliche Haeufigkeiten'],['Training zegt 2; voedingsintake zegt 3 trainingen.','Training says 2; nutrition intake says 3 workouts.','Training nennt 2; Ernaehrungsanamnese nennt 3 Trainings.'],'frequency','intake',0],
 ['goal',['Doelkoppeling klopt niet','Goal link mismatch','Zielverknuepfung stimmt nicht'],['Gekoppeld voedingsdoel wijkt af van het bestaande doel.','Linked nutrition goal differs from the existing goal.','Verknuepftes Ernaehrungsziel weicht vom bestehenden Ziel ab.'],'goal','intake',0],
 ['expired',['Bron is verlopen','Expired source','Abgelaufene Quelle'],['De geldigheidsduur van de voedingsbron is verstreken.','Nutrition source validity has elapsed.','Gueltigkeit der Ernaehrungsquelle ist abgelaufen.'],'expired','intake',0],
 ['health',['Actuele klacht','Current complaint','Aktuelle Beschwerde'],['Een klacht staat in de trainingsbron.','A complaint is recorded in the training source.','Eine Beschwerde steht in der Trainingsquelle.'],'safety','intake',0],
 ['recovery',['Klacht voorbij gemeld','Reported recovery','Gemeldete Genesung'],['Na een klacht wordt herstel gemeld; dit is geen medische vrijgave.','Recovery after a complaint is reported; this is not medical clearance.','Nach einer Beschwerde wird Genesung gemeldet; keine medizinische Freigabe.'],'safety','reassess',0],
 ['consent',['Toestemming ingetrokken','Consent withdrawn','Einwilligung widerrufen'],['Intrekken na bevestiging; activatie mag niet doorgaan.','Withdraw after confirmation; activation must stop.','Widerruf nach Bestaetigung; Aktivierung muss stoppen.'],'consent','blocked',0],
 ['changed',['Nieuwe intakeversie','New intake version','Neue Anamneseversion'],['Trainingsvoorkeur verandert; de oude bevestiging vervalt.','Training preference changes; prior confirmation expires.','Trainingsvorliebe aendert sich; bisherige Bestaetigung verfaellt.'],'version_conflict','reassess',0],
 ['atomic',['Onderbroken toepassing','Interrupted activation','Unterbrochene Aktivierung'],['Fout na voorbereiding training; beide delen blijven ongewijzigd.','Failure after training preparation; both parts stay unchanged.','Fehler nach Trainingsvorbereitung; beide Teile bleiben unveraendert.'],'atomic_fault','confirmed',0],
 ['duplicate',['Dubbel activeren','Duplicate activation','Doppelte Aktivierung'],['Dezelfde activatie wordt tweemaal verstuurd.','The same activation is sent twice.','Dieselbe Aktivierung wird zweimal gesendet.'],'idempotent','active',1],
 ['stale',['Verouderde bevestiging','Stale confirmation','Veraltete Bestaetigung'],['Bevestiging is afkomstig van voor een nieuwe beoordeling.','Confirmation predates a new review.','Bestaetigung stammt aus der Zeit vor einer neuen Pruefung.'],'version_conflict','pending',0],
 ['restore',['Vorige versie terugzetten','Restore previous version','Vorherige Version wiederherstellen'],['Versie 1 terugzetten maakt na nieuw akkoord versie 3.','Restoring version 1 creates version 3 after new approval.','Version 1 wird nach neuer Zustimmung als Version 3 wiederhergestellt.'],'success','active',3],
 ['allergy',['Allergie versus voorkeur','Allergy versus preference','Allergie gegen Vorliebe'],['Pinda is tegelijk allergie en favoriete keuze; geen plan.','Peanut is both an allergy and a favorite; no plan.','Erdnuss ist zugleich Allergie und Favorit; kein Plan.'],'nutrition:preference_conflict','intake',0],
 ['units',['Eenheden en RIR nul','Units and RIR zero','Einheiten und RIR null'],['Historisch 20 kg, RIR 0 en RPE leeg blijven apart; voorkeur lb wordt niet omgerekend.','Historical 20 kg, RIR 0 and absent RPE stay separate; lb preference is not converted.','Historische 20 kg, RIR 0 und fehlender RPE bleiben getrennt; lb-Vorliebe wird nicht umgerechnet.'],'success','pending',0]
];
const scenarios=rows.map(([id,title,changed,reason,status,version])=>({id,title,changed,reason,status,version}));
function run(id){
 const spec=scenarios.find(x=>x.id===id);if(!spec)throw Error('scenario');
 const f=F.copy(F.cases[id]),model=M.create(f),events=[];
 const send=(action,data={},options={})=>{const event=model.event(action,data),r=model.command(event,options);events.push({action,ok:r.ok,reason:r.reason});return event;};
 if(id==='recovery'){
  let src=F.copy(f);src.revision++;src.training.revision++;src.training.fixture.intake.health='current';send('sources',src);
  src=F.copy(src);src.revision++;src.training.revision++;src.training.fixture.intake.health='none';send('sources',src);send('build');
 }else if(id==='consent'){send('build');send('confirm');send('revoke');send('activate');}
 else if(id==='changed'){send('build');send('confirm');const e=model.event('activate'),src=F.copy(f);src.revision++;src.training.revision++;src.training.fixture.intake.minutes=45;send('sources',src);const r=model.command(e);events.push({action:e.action,ok:r.ok,reason:r.reason});}
 else if(id==='atomic'){send('build');send('confirm');send('activate',{}, {fault:'after_training'});}
 else if(id==='duplicate'){send('build');send('confirm');const e=send('activate'),r=model.command(e);events.push({action:e.action,ok:r.ok,reason:r.reason});}
 else if(id==='stale'){send('build');const e=model.event('confirm');send('build');const r=model.command(e);events.push({action:e.action,ok:r.ok,reason:r.reason});}
 else if(id==='restore'){for(let j=0;j<2;j++){send('build');if(j)send('edit',{domain:'training_day',value:'fri'});send('confirm');send('activate');}send('restore',{version:1});send('confirm');send('activate');}
 else send('build');
 return {spec,model,events};
}
function assess(r,s=r.model.view()){
 const last=r.events.at(-1),spec=r.spec;let pass=!!last&&last.reason===spec.reason&&s.status===spec.status&&s.version===spec.version&&s.history.length===spec.version;
 if(s.active)pass=pass&&s.active.version===s.version&&s.active.training?.sessions.length===2&&!!s.active.nutrition?.meals.length;
 if(s.draft)try{const check=M.inspect(s.sources,s.clock);if(s.selection){check.training=s.selection.training;check.nutrition=s.selection.nutrition;}pass=pass&&M.same(s.draft,check);}catch{pass=false;}
 if(spec.id==='units'){const e=s.draft?.training.sessions.flatMap(x=>x.exercises).find(x=>x.history);pass=pass&&e?.history.rir===0&&e.history.rpe===null&&e.history.weight.unit==='kg'&&s.draft.nutrition.bodyWeight.unit==='lb';}
 return {pass:!!pass,proposal:!!s.draft,reason:last?.reason||'missing_evidence'};
}
const api={scenarios,run,assess};if(typeof module==='object')module.exports=api;else root.FMZ18Review=api;
})(globalThis);
