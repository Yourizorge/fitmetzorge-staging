/* Visible owner tests. Every scenario calls the unchanged, memory-only model. */
(function(root) {
"use strict";
const M=typeof module==="object"?require("./model.js"):root.FMZ15Model;
const C=typeof module==="object"?require("../coach-review-demo/catalog.js"):root.FMZ8Catalog;
if(typeof module==="object")require("./data.js");
const D=root.FMZ15Data,copy=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const cases=[
 {id:"valid",fixture:"complete",title:"Volledige geldige intake",changed:"Alle verplichte antwoorden zijn ingevuld met fictieve gegevens.",expected:"Er verschijnt een voorstel. Er wordt nog niets geactiveerd.",permission:"Ja, een conceptvoorstel is toegestaan. Activeren blijft een aparte stap.",reason:"Geen blokkade: de ingevulde gegevens passen bij de bestaande catalogus."},
 {id:"missing",fixture:"incomplete",title:"Ontbrekende verplichte gegevens",changed:"Het hoofddoel is leeg gemaakt.",expected:"Geen voorstel zolang het hoofddoel ontbreekt.",permission:"Nee, eerst het ontbrekende hoofddoel invullen.",reason:"Youri mag een ontbrekend doel niet zelf verzinnen."},
 {id:"allergy",fixture:"allergy",title:"Allergieconflict",changed:"Allergie voor noten en zuivel; tofu is uitgesloten. De oefening Goblet squat is ook uitgesloten. De test probeert daarna toch noten en yoghurt toe te voegen.",expected:"Een passend voorstel zonder deze producten of oefening. Toevoegen van noten of yoghurt wordt geweigerd; het goede voorstel blijft ongewijzigd.",permission:"Alleen een voorstel zonder uitgesloten producten en oefeningen is toegestaan.",reason:"De conflicterende toevoeging is geblokkeerd. Niet het hele veilige alternatief."},
 {id:"health",fixture:"complaint",title:"Gezondheidsklacht of beperking",changed:"Een actuele gezondheidsklacht is gemeld in de fictieve intake.",expected:"Geen fysiek trainings- of voedingsplan. De veiligheidsmelding staat ook bij het voorstel.",permission:"Nee, fysieke planvorming is geblokkeerd.",reason:"Er is een actuele klacht. Deze test geeft geen diagnose of medische vrijgave."},
 {id:"rule",fixture:"unsupported_machine",title:"Niet-ondersteunde catalogusregel",changed:"Een kabelmachine is geselecteerd, maar de gebruikte catalogus heeft daarvoor geen regel.",expected:"Geen voorstel; geen oefening of regel verzinnen.",permission:"Nee, een passende bronregel ontbreekt.",reason:"De kabelmachine is niet ondersteund door deze catalogusversie."},
 {id:"source",fixture:"complete",title:"Bronconflict of gewijzigde intake",changed:"Na bevestigen zijn maandag/woensdag/vrijdag vervangen door dinsdag/donderdag. Daarna is een afwijkende catalogusversie gesimuleerd.",expected:"De oude bevestiging vervalt. De oude aanvraag kan niet activeren. Het bronconflict blokkeert een nieuw voorstel.",permission:"Nu niet. Een gewijzigde intake moet opnieuw beoordeeld worden met geldige, overeenkomende bronnen.",reason:"Oude bevestiging en huidige gegevens passen niet bij elkaar; de catalogusversie wijkt ook af."},
 {id:"consent",fixture:"complete",title:"Toestemming ingetrokken",changed:"Na het maken van een concept is de toestemming ingetrokken. De test probeert een nieuwe intake, een nieuw voorstel en activering.",expected:"Alle drie worden geweigerd. Het eerdere concept is alleen nog zichtbaar als geblokkeerd concept.",permission:"Nee, geen verdere verwerking of nieuwe voorstellen.",reason:"Toestemming is ingetrokken. Het eerdere concept mag niet worden geactiveerd."},
 {id:"duplicate",fixture:"complete",title:"Dubbele bevestiging / activering",changed:"Deze test simuleert bevestigen en afzonderlijk activeren, en herhaalt daarna beide aanvragen.",expected:"Precies een actieve versie, zonder dubbele wijzigingen.",permission:"Ja, de ene bevestigde versie mag actief zijn. Een herhaling mag geen extra versie maken.",reason:"Herhaalde aanvragen veranderen niets; een nieuwe dubbele activering wordt geweigerd."},
 {id:"restore",fixture:"complete",title:"Vorige versie terugzetten",changed:"De test simuleert versie 1 (8 reps), versie 2 (9 reps) en een herstelvoorstel voor versie 1. Lidbevestiging en aparte activering worden alleen in deze demo nagebootst; er is geen trainerstap.",expected:"Zonder nieuwe bevestiging geen herstel. Na bevestigen en apart activeren ontstaat versie 3 met 8 reps. Versies 1 en 2 blijven staan.",permission:"Ja, maar alleen als nieuw bevestigd voorstel, gevolgd door aparte activering.",reason:"Terugzetten overschrijft geen oude versie en slaat bevestiging niet over."}
];
function run(id,factory=M.create) {
 const spec=cases.find(x=>x.id===id);if(!spec)throw Error("unknown_review_case");
 const f=copy(D.fixtures[spec.fixture]);if(id==="allergy")f.intake.avoided=["squat"];
 const model=factory(f,D.registry),checks=[],ledger=[];
 const add=(label,pass,observed)=>checks.push({label,pass:pass===true,observed:String(observed)});
 function act(action,data={},expected="success",saved) {
  const before=model.view(),event=saved||model.event(action,data),result=model.command(event),after=model.view();
  ledger.push({action,expected,event:copy(event),ok:result.ok,reason:result.reason,before,after});
  const ok=expected==="success"||expected==="idempotent";
  add("Uitkomst "+action,result.ok===ok&&result.reason===expected,result.reason);
  if(!ok)add("Geweigerde stap verandert niets",same(before,after),same(before,after)?"ongewijzigd":"onverwachte wijziging");
  if(result.ok!==ok||result.reason!==expected)throw Error("unexpected_result");
  return event;
 }
 try {
  if(id==="valid")act("build");
  if(id==="missing")act("build",{},"incomplete");
  if(id==="health")act("build",{},"safety");
  if(id==="rule")act("build",{},"machine_rule_missing");
  if(id==="allergy") {
   act("build");act("edit",{kind:"food",meal:0,index:0,id:"nuts"},"excluded");
   act("edit",{kind:"food",meal:0,index:0,id:"yogurt"},"excluded");
   const p=model.view().draft.plan,foods=p.nutrition.meals.flatMap(x=>x.items.map(x=>x.food)),exercises=p.training.sessions.flatMap(x=>x.exercises.map(x=>x.id));
   for(const food of ["nuts","yogurt","tofu"])add(C.foods.find(x=>x.id===food).label[0]+" in voedingsvoorstel",!foods.includes(food),foods.filter(x=>x===food).length+" keer");
   add("Voedingsproducten in trainingsvoorstel",exercises.every(x=>C.exercises.some(e=>e.id===x)),exercises.filter(x=>C.foods.some(f=>f.id===x)).length+" keer");
   add("Uitgesloten Goblet squat in training",!exercises.includes("squat"),exercises.filter(x=>x==="squat").length+" keer");
  }
  if(id==="source") {
   act("build");act("confirm");const stale=model.event("activate"),i=model.view().intake;i.days=["tue","thu"];
   act("intake",i);add("Oude bevestiging en concept vervallen",!model.view().confirmed&&model.view().draft===null,"nieuwe intake");
   act("activate",{},"version_conflict",stale);act("stale");act("build",{},"rule_source");
  }
  if(id==="consent") {
   act("build");act("revoke");act("intake",copy(D.fixtures.complete.intake), "consent");act("build",{},"consent");act("activate",{},"consent");
  }
  if(id==="duplicate") {
   act("build");const c=act("confirm");act("confirm",{},"idempotent",c);act("confirm",{},"idempotent");
   const e=act("activate");act("activate",{},"idempotent",e);act("activate",{},"version_conflict");
  }
  if(id==="restore") {
   act("build");act("confirm");act("activate");const first=copy(model.view().history[0]);
   act("build");const e=model.view().draft.plan.training.sessions[0].exercises[0];
   act("edit",{kind:"exercise",session:0,index:0,id:e.id,sets:e.sets,reps:9});act("confirm");act("activate");const second=copy(model.view().history[1]);
   act("restore",{version:1});add("Herstel wacht op bevestigen",!model.view().confirmed&&model.view().version===2,model.view().status);
   act("activate",{},"version_conflict");act("confirm");act("activate");
   const s=model.view();add("Versie 1 behouden",same(s.history[0],first),"8 herhalingen");add("Versie 2 behouden",same(s.history[1],second),"9 herhalingen");
   add("Nieuwe versie bevat oude plan",same(s.active.plan,first.plan),"versie "+s.version+", 8 herhalingen");
  }
  const s=model.view(),expectedVersion=id==="restore"?3:id==="duplicate"?1:0;
  add("Aantal planversies",s.version===expectedVersion&&s.history.length===expectedVersion,s.history.length);
  add("Geen automatische of medische vrijgave",s.automatic_actions_allowed===false&&s.physical_advice_authorized===false&&s.medical_clearance===false&&s.external_calls===0,"geen vrijgave");
  const allowed=["valid","allergy","duplicate","restore"].includes(id);
  add("Voorsteltoegang",model.availability().ok===allowed,model.availability().ok?"toegestaan":"geblokkeerd");
  add("Concept aanwezig zoals verwacht",Boolean(s.draft)===["valid","allergy","consent","duplicate","restore"].includes(id),s.draft?"aanwezig":"geen concept");
 } catch(_) {add("Test volledig uitgevoerd",false,"Onverwachte uitkomst; test gestopt.");}
 return {id,spec,model,checks,ledger,expectedState:model.view()};
}
function assess(result,state,display) {
 const checks=copy(result.checks),add=(label,pass,observed)=>checks.push({label,pass:pass===true,observed:String(observed)});
 const counts={valid:1,missing:1,allergy:3,health:1,rule:1,source:6,consent:5,duplicate:7,restore:11};
 add("Alle testhandelingen vastgelegd",result.ledger.length===counts[result.id]&&result.checks.length>=counts[result.id]+4,result.ledger.length+" stappen");
 add("Testresultaat hoort bij huidige gegevens",same(state,result.expectedState),"huidige momentopname");
 if(display) {
  const p=state.draft?.plan,items=p?.nutrition.meals.flatMap(x=>x.items)||[],ex=p?.training.sessions.flatMap(x=>x.exercises)||[];
  add("Zichtbaar voedingsvoorstel klopt",same(display.foods,items.map(x=>({id:x.food,text:C.foods.find(f=>f.id===x.food).label[display.locale]+" | "+x.g+" g"}))),display.foods.length+" producten");
  add("Zichtbaar trainingsvoorstel klopt",same(display.exercises,ex.map(x=>({id:x.id,text:C.exercises.find(e=>e.id===x.id).label[display.locale]}))),display.exercises.length+" oefeningen");
  add("Zichtbare versiegeschiedenis klopt",display.versions==="Intake: "+state.intakeHistory.map(x=>x.revision).join(" / ")+" | Plan: "+(state.history.map(x=>x.version).join(" / ")||"-"),display.versions);
  const blocked=!result.model.availability().ok;
  add("Geen bevestigen of activeren bij blokkade",!blocked||(!display.confirm&&!display.activate),"bediening gecontroleerd");
  add("Geblokkeerd oud concept herkenbaar",!blocked||!state.draft||display.blockedNotice,"conceptstatus gecontroleerd");
 }
 return {pass:checks.length>0&&checks.every(x=>x.pass),checks};
}
const api={cases,run,assess};if(typeof module==="object")module.exports=api;else root.FMZ15Review=api;
})(globalThis);
