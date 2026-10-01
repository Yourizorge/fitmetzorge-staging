/* Owner scenarios call the same model as the manual editor. No live actions. */
(function(root){"use strict";
const M=typeof module==="object"?require("./model.js"):root.FMZ16Model,F=typeof module==="object"?require("./fixtures.js"):root.FMZ16Fixtures,copy=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const names=[
["beginner","Beginner: algemene fitness","Beginner: general fitness","Anfaenger: allgemeine Fitness"],
["muscle","Ervaren: spieropbouw","Experienced: muscle building","Erfahren: Muskelaufbau"],
["strength","Kracht: reps en rust","Strength: reps and rest","Kraft: Wiederholungen und Pausen"],
["short","Beperkte trainingsduur","Limited session time","Begrenzte Trainingszeit"],
["days","Twee en vier dagen","Two and four days","Zwei und vier Tage"],
["equipment","Beperkte apparatuur","Limited equipment","Begrenzte Ausruestung"],
["preferences","Favoriet en uitgesloten","Favorite and excluded","Favorit und ausgeschlossen"],
["valid_edit","Geldige bewerking","Allowed edit","Erlaubte Aenderung"],
["invalid_edit","Geweigerde bewerking","Refused edit","Abgelehnte Aenderung"],
["rules","Ontbrekende of conflicterende regel","Missing or conflicting rule","Fehlende oder widerspruechliche Regel"],
["rir","RIR aan, RPE uit","RIR on, RPE off","RIR an, RPE aus"],
["both","RIR en RPE aan","RIR and RPE on","RIR und RPE an"],
["units","Kg/lb zonder herinterpretatie","Kg/lb without reinterpretation","Kg/lb ohne Neuinterpretation"],
["source","Broncorrectie voor activering","Source correction before activation","Quellkorrektur vor Aktivierung"],
["restore","Dubbele activering en herstel","Duplicate activation and restore","Doppelte Aktivierung und Wiederherstellung"],
["safety","Klacht en ingetrokken toestemming","Complaint and withdrawn consent","Beschwerde und widerrufene Einwilligung"]];
const expectations=[
["Een concept met verschillende regels per oefenrol, nog niet actief.","A draft with different rules per role, not active.","Entwurf mit unterschiedlichen Rollenregeln, noch nicht aktiv."],
["Andere setbereiken dan bij een beginner, uit de spieropbouwregels.","Different set ranges from the muscle rules.","Andere Satzbereiche aus den Muskelaufbauregeln."],
["Krachtregels tonen andere reps en rust; geen verzonnen gewicht.","Strength rules show different reps/rest; no invented load.","Kraftregeln zeigen andere Wiederholungen/Pausen; kein erfundenes Gewicht."],
["De berekende planning blijft binnen tien minuten.","Calculated planning stays within ten minutes.","Berechnete Planung bleibt innerhalb von zehn Minuten."],
["Van twee naar vier dagen: nieuw concept, oude intake blijft bewaard.","Two to four days: new draft, old intake retained.","Zwei auf vier Tage: neuer Entwurf, alte Angaben bleiben erhalten."],
["Alleen oefeningen waarvoor de mat voldoende is.","Only exercises supported by a mat.","Nur Uebungen, fuer die eine Matte ausreicht."],
["Heupbrug gekozen; roeien en squat blijven uitgesloten.","Hip bridge chosen; row and squat stay excluded.","Hueftbruecke gewaehlt; Rudern und Kniebeuge bleiben ausgeschlossen."],
["Sets, reps, rust, oefening en dag wijzigen binnen de bronregels.","Sets, reps, rest, exercise and day change within source rules.","Saetze, Wiederholungen, Pause, Uebung und Tag innerhalb der Regeln aendern."],
["Te veel sets geweigerd; het vorige concept blijft exact gelijk.","Too many sets refused; previous draft stays identical.","Zu viele Saetze abgelehnt; vorheriger Entwurf bleibt identisch."],
["Beide fouten apart getest: geen regel en twee passende regels blokkeren.","Both tested separately: missing rule and two matching rules block.","Beides getrennt getestet: fehlende Regel und zwei passende Regeln blockieren."],
["RIR-doelen zichtbaar; RPE blijft leeg.","RIR targets visible; RPE stays empty.","RIR-Ziele sichtbar; RPE bleibt leer."],
["RIR en RPE zichtbaar en afzonderlijk instelbaar.","RIR and RPE visible and independently editable.","RIR und RPE sichtbar und getrennt aenderbar."],
["Bron blijft 20 kg en RIR 0. Nieuwe planunit lb; startgewicht blijft leeg.","Source stays 20 kg and RIR 0. New plan unit lb; initial load stays empty.","Quelle bleibt 20 kg und RIR 0. Neue Planeinheit lb; Startgewicht bleibt leer."],
["Nieuwe bronversie wist oude bevestiging; oude activering wordt geweigerd.","New source clears confirmation; stale activation is refused.","Neue Quelle loescht Bestaetigung; alte Aktivierung wird abgelehnt."],
["Twee oude versies blijven; herstel wordt versie 3 na aparte bevestiging en activering.","Two old versions remain; restore becomes version 3 after separate confirmation and activation.","Zwei alte Versionen bleiben; Wiederherstellung wird Version 3 nach getrennten Schritten."],
["Klacht en ingetrokken toestemming apart getest: geen nieuw fysiek plan.","Complaint and withdrawal tested separately: no new physical plan.","Beschwerde und Widerruf getrennt getestet: kein neuer physischer Plan."]];
const scenarios=names.map((x,i)=>({id:x[0],title:x.slice(1),expected:expectations[i]}));
function exerciseEdit(m,overrides={}){const s=m.view(),x=s.draft.plan.sessions[0].exercises[0];return {kind:"exercise",session:0,index:0,exercise:x.exercise,sets:x.sets,reps:x.reps,rest:x.rest,rir:x.rir,rpe:x.rpe,...overrides};}
function run(id,factory=M.create){
 const spec=scenarios.find(x=>x.id===id);if(!spec)throw Error("scenario");let model=factory(F.cases[id]);const checks=[],events=[];let before=null,failed=false;
 const add=(key,pass,actual)=>checks.push({key,pass:pass===true,actual:String(actual)});
 function act(action,data={},expected="success",e){
  const old=model.view(),event=e||model.event(action,data),r=model.command(event),after=model.view();
  events.push({action,expected,reason:r.reason,ok:r.ok,before:old,after});
  add("command",r.reason===expected&&r.ok===["success","idempotent"].includes(expected),action+": "+r.reason);
  if(!r.ok)add("unchanged",same(old,after),"unchanged");
  if(r.reason!==expected||r.ok!==["success","idempotent"].includes(expected))throw Error("unexpected");return event;
 }
 try{
  if(id==="rules"){
   const f=copy(F.base);f.catalog.rules=f.catalog.rules.filter(r=>!(r.goal==="fitness"&&r.experience==="beginner"&&r.role==="main"));model=factory(f);act("build",{},"rule_missing");
   const other=copy(F.base),r=copy(other.catalog.rules.find(r=>r.goal==="fitness"&&r.experience==="beginner"&&r.role==="main"));r.id+="-conflict";other.catalog.rules.push(r);model=factory(other);act("build",{},"rule_conflict");
  }else if(id==="safety"){
   const f=copy(F.base);f.intake.health="current";model=factory(f);act("build",{},"safety");model=factory(F.base);act("revoke");act("build",{},"consent");act("intake",copy(F.base.intake),"consent");
  }else{
   act("build");if(["days","valid_edit","invalid_edit","units","source","restore"].includes(id))before=copy(model.view().draft.plan);
   if(id==="days"){const i=model.view().intake;i.days=["mon","tue","thu","sat"];i.frequency=4;act("intake",i);add("reassess",model.view().draft===null,"2 -> 4");act("build");}
   if(id==="valid_edit"){
    act("edit",exerciseEdit(model,{exercise:"press",sets:3,reps:11,rest:75}));act("edit",{kind:"day",session:0,day:"fri"});
   }
   if(id==="invalid_edit"){act("edit",exerciseEdit(model,{sets:99}),"range");add("unchanged",same(before,model.view().draft.plan),"99 refused");}
   if(id==="units"){
    const i=model.view().intake,history=copy(i.history);i.unit="lb";act("intake",i);act("build");add("units",same(history,model.view().intake.history)&&model.view().draft.plan.sessions.every(s=>s.exercises.every(e=>e.load===null)),"20 kg / RIR 0 / lb / null");
   }
   if(id==="source"){
    act("confirm");const stale=model.event("activate"),c=model.view().catalog;c.version=2;for(const r of c.rules)r.version=2;act("source",c);act("activate",{},"version_conflict",stale);add("reassess",model.view().draft===null&&!model.view().confirmed,"v1 -> v2");
   }
   if(id==="restore"){
    act("confirm");const e=act("activate"),first=copy(model.view().history[0]);act("activate",{},"idempotent",e);act("activate",{},"version_conflict");
    act("build");act("edit",exerciseEdit(model,{reps:11}));act("confirm");act("activate");const second=copy(model.view().history[1]);
    act("restore",{version:1});act("activate",{},"version_conflict");act("confirm");act("activate");
    add("history",same(first,model.view().history[0])&&same(second,model.view().history[1])&&same(first.plan,model.view().active.plan),"1 / 2 / 3");
   }
  }
  const s=model.view(),p=s.draft?.plan;
  if(p){M.validatePlan(p,s.intake,s.catalog);add("budget",p.sessions.every(x=>x.seconds<=p.budget),p.sessions.map(x=>x.seconds).join(" / ")+" <= "+p.budget);}
  add("versions",s.version===(id==="restore"?3:0),s.version);
  add("no_auto",!s.automatic_actions_allowed&&!s.physical_advice_authorized&&!s.medical_clearance&&s.external_calls===0,"false");
  if(id==="beginner")add("different_sets",p.sessions[0].exercises[0].sets!==p.sessions[0].exercises[1].sets,"2 / 1");
  if(id==="equipment")add("equipment",p.sessions.every(s=>s.exercises.every(e=>synthExercise(model,e).equipment==="mat")),"mat");
  if(id==="preferences")add("preferences",p.sessions.every(s=>s.exercises[0].exercise==="bridge"&&s.exercises.every(e=>!["row","squat"].includes(e.exercise))),"bridge");
  if(id==="rir"||id==="both")add("effort",p.sessions.every(s=>s.exercises.every(e=>e.rir!==null&&(id==="both"?e.rpe!==null:e.rpe===null))),id);
 }catch(_){failed=true;add("complete",false,"stopped");}
 return {id,spec,model,before,checks,events,failed,expectedState:model.view()};
}
function synthExercise(m,e){return m.view().catalog.exercises.find(x=>x.id===e.exercise);}
const counts={beginner:1,muscle:1,strength:1,short:1,days:3,equipment:1,preferences:1,valid_edit:3,invalid_edit:2,rules:2,rir:1,both:1,units:3,source:4,restore:13,safety:4};
function assess(r,state,visible){
 const checks=copy(r.checks);checks.push({key:"complete",pass:!r.failed&&r.events.length===counts[r.id]&&r.checks.length>=r.events.length+2,actual:r.events.length});
 checks.push({key:"current",pass:same(state,r.expectedState),actual:"snapshot"});
 if(visible)checks.push({key:"visible",pass:same(visible,visibleFacts(state)),actual:"rendered"});
 return {pass:checks.every(x=>x.pass),checks};
}
function visibleFacts(s){return {rows:(s.draft?.plan.sessions||[]).flatMap(t=>t.exercises.map(e=>({day:t.day,exercise:e.exercise,sets:String(e.sets),reps:String(e.reps),rest:String(e.rest),rir:e.rir===null?"-":String(e.rir),rpe:e.rpe===null?"-":String(e.rpe)}))),times:(s.draft?.plan.sessions||[]).map(x=>String(x.seconds)),versions:s.history.map(h=>h.version).join(" / ")||"-",confirm:s.status==="pending",activate:s.status==="confirmed"};}
const api={scenarios,run,assess,visibleFacts,exerciseEdit};if(typeof module==="object")module.exports=api;else root.FMZ16Review=api;
})(globalThis);
