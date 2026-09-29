"use strict";
const $=id=>document.getElementById(id),D=globalThis.FMZ14Data,M=globalThis.FMZ14Model,C=globalThis.FMZ8Catalog,B=globalThis.FMZ8Model;
let locale="nl",name="a_progression",model=M.create(D[name][locale]),last="",lastApply=null;
const names={
a_progression:["A | Traineroptie kg","A | Trainer option kg","A | Traineroption kg"],a_maintain:["A | Doel behouden","A | Keep target","A | Ziel beibehalten"],a_lb:["A | Traineroptie lb","A | Trainer option lb","A | Traineroption lb"],b_schedule:["B | Gemiste training / planning","B | Missed workout / schedule","B | Ausgelassene Einheit / Planung"],
nutrition_partial:["Voedingsregistratie controleren","Check food log","Ernaehrungsprotokoll pruefen"],recovery_reflection:["Slaap / herstel / planning","Sleep / recovery / planning","Schlaf / Erholung / Planung"],calorie_rule_missing:["Geen voedingsregel","No nutrition rule","Keine Ernaehrungsregel"],
missing_rule:["A | Geen trainerregel","A | Missing trainer rule","A | Fehlende Trainerregel"],ambiguous_rule:["A | Twee regels","A | Two rules","A | Zwei Regeln"],no_trainer:["A | Trainer ontbreekt","A | Missing trainer","A | Trainer fehlt"],invalid_option:["Onjuiste optie","Invalid option","Ungueltige Option"],missing_value:["Ontbrekende waarde","Missing value","Fehlender Wert"],expired:["Verlopen bron","Expired source","Abgelaufene Quelle"],conflict:["Versieconflict","Version conflict","Versionskonflikt"],revoked:["Geen toestemming","No consent","Keine Einwilligung"],current:["Actuele klacht","Current symptom","Aktuelle Beschwerde"],self_reported:["Zelf gemeld herstel","Self-reported recovery","Selbst gemeldete Erholung"],recurring:["Terugkerende klacht","Recurring symptom","Wiederkehrende Beschwerde"],unclassified:["Oningedeelde klacht","Unclassified symptom","Nicht eingeordnete Beschwerde"],expired_context:["Verlopen context / O5","Expired context / O5","Abgelaufener Kontext / O5"],technical:["Technisch misverstand","Technical misunderstanding","Technisches Missverstaendnis"],b_current:["B | Actuele klacht","B | Current symptom","B | Aktuelle Beschwerde"],b_partial:["B | Onvolledige voeding","B | Incomplete food log","B | Unvollstaendiges Protokoll"],b_no_rule:["B | Geen catalogusoptie","B | No catalog option","B | Keine Katalogoption"]};
const text=(id,t)=>{$(id).textContent=t;},node=(tag,t,cls)=>{const n=document.createElement(tag);n.textContent=t??"";if(cls)n.className=cls;return n;};
const idx=()=>["nl","en","de"].indexOf(locale),c=()=>FMZ14Copy.copy[locale],state=()=>model.view();
function options(el,values,value){el.replaceChildren(...values.map(([v,t])=>{const o=node("option",t);o.value=v;return o;}));el.value=value;}
function send(action,data={},event){
 const e=event||model.event(action,data,$("actor").value||"member"),r=model.command(e);last=r.ok?"":c()[r.reason]||c().blocked+" ("+r.reason+")";
 if(r.reason==="idempotent")last=["Al verwerkt. Er is geen tweede schemaversie gemaakt.","Already processed. No second plan version was created.","Bereits verarbeitet. Keine zweite Planversion erstellt."][idx()];
 if(action==="apply"&&r.ok)lastApply=e;render();return r;
}
function button(parent,id,label,action,primary=false){const b=node("button",label,primary?"primary":"");b.id=id;b.type="button";b.onclick=action;parent.append(b);}
function plan(el,v,compare){
 el.replaceChildren();if(!v){el.append(node("p",c().noTarget));return;}
 if(v.training){
  for(const ex of v.training.exercises){const block=node("div",null,"exercise");block.append(node("h3",ex.labels[locale]));const table=node("table"),thead=node("tr");
   for(const h of ["Set","REPS",ex.sets[0].load.unit,"RIR","RPE"])thead.append(node("th",h));table.append(thead);
   ex.sets.forEach((s,i)=>{const row=node("tr"),old=compare?.training.exercises.find(e=>e.exercise_id===ex.exercise_id)?.sets[i];
    [s.index,s.reps.min+(s.reps.min!==s.reps.max?"-"+s.reps.max:""),s.load.value,s.rir??"-",s.rpe??"-"].forEach((x,j)=>row.append(node("td",x,old&&(j===1&&JSON.stringify(old.reps)!==JSON.stringify(s.reps)||j===2&&old.load.value!==s.load.value)?"changed":"")));table.append(row);});block.append(table);el.append(block);
  }
 }else{
  const p=v.plan,when=p.training.sessionStart||c().unrecorded;
  el.append(node("p",when,compare?.plan.training.sessionStart!==p.training.sessionStart?"changed":""));
  for(const session of p.training.sessions){const wrap=node("div",null,"exercise");wrap.append(node("h3",dayLabel(session.day)));for(const e of session.exercises){const label=C.exercises.find(x=>x.id===e.id)?.label[idx()]||e.id;wrap.append(node("p",label+" | "+e.sets+" x "+e.reps+" | "+(e.load??"-")+" "+e.unit+" | RIR "+(e.rir??"-")+" / RPE "+(e.rpe??"-")));}el.append(wrap);}
  el.append(node("p",["Voeding en slaapdoel ongewijzigd.","Food plan and sleep target unchanged.","Ernaehrung und Schlafziel unveraendert."][idx()],"label"));
 }
}
function dayLabel(d){return {mon:["ma","Mon","Mo"],tue:["di","Tue","Di"],wed:["wo","Wed","Mi"],thu:["do","Thu","Do"],fri:["vr","Fri","Fr"],sat:["za","Sat","Sa"],sun:["zo","Sun","So"]}[d][idx()];}
function render(){
 const s=state(),out=D[name][locale][s.source===D[name][locale].corrected.source_hash?"corrected":"initial"],t=c();
 document.documentElement.lang=locale;
 document.querySelectorAll("[data-copy]").forEach(e=>e.textContent=t[e.dataset.copy]);
 for(const id of ["title","demo","access","scope","rollback"])text(id,t[id]);text("result",last);
 options($("scenario"),Object.keys(names).map(k=>[k,names[k][idx()]]),name);
 options($("theme"),[["light",t.light],["dark",t.dark]],document.body.dataset.theme||"light");
 const actor=$("actor").value||"member";options($("actor"),s.route==="A"?[["member",t.member],["trainer",t.trainer]]:[["member",t.member]],actor);$("actor-label").hidden=s.route==="B";
 text("status","Route "+s.route+" | "+(t.statuses[s.status]||s.status));
 $("steps").replaceChildren(...(s.route==="A"?[[t.member,s.member],[t.trainer,s.trainer],[t.apply,s.status==="applied"]]:[[t.confirm,s.member],[t.activate,s.status==="applied"]]).map(([x,yes])=>node("li",x,yes?"done":"")));
 $("message").replaceChildren(...out.messages.map(x=>node("p",x)));
 for(const r of out.rationale||[])$("message").append(node("p",r));
 if(s.status==="needs_review")$("message").append(node("p",t.newSource));
 if(s.status==="stale_source")$("message").append(node("p",t.currentSource));
 if(!s.consent)$("message").append(node("p",t.consent));
 if(s.expired)$("message").append(node("p",t.expired));
 if(s.health)$("message").append(node("p",t.safety));
 if(s.conflict)$("message").append(node("p",t.conflict));
 if(s.checked)$("message").append(node("p",t.checked));
 text("feedback",(out.feedback||[]).map(x=>typeof x==="string"?x:JSON.stringify(x)).join(" "));
 $("facts").replaceChildren(...out.facts.map(f=>{const n=node("article",null,"fact"),label={sleep:["Slaap","Sleep","Schlaf"],recovery:["Herstel","Recovery","Erholung"],nutrition:["Voeding","Food log","Ernaehrung"],training:["Training","Training","Training"]}[f.metric][idx()];n.append(node("strong",label),node("p",f.text||JSON.stringify(f)));return n;}));
 if(!s.consent)$("facts").replaceChildren();
 const acts=$("actions");acts.replaceChildren();
 if(s.status==="member_pending"&&actor==="member")button(acts,"accept",s.route==="A"?t.accept:t.confirm,()=>send(s.route==="A"?"accept":"confirm"),true);
 if(s.status==="trainer_pending"&&actor==="trainer"){button(acts,"approve",t.approve,()=>send("approve"),true);button(acts,"block",t.block,()=>send("block"));}
 if(["member_pending","confirmed"].includes(s.status)&&actor==="member"||s.status==="trainer_pending"&&actor==="trainer")button(acts,"reject",t.reject,()=>send("reject"));
 if(["approved","confirmed"].includes(s.status)&&actor==="member")button(acts,"apply",s.route==="A"?t.apply:t.activate,()=>send("apply"),true);
 if(s.status==="applied"){
  button(acts,"restore",t.restore,()=>send("restore",{version:s.history.at(-2).version}));
  if(lastApply&&actor==="member")button(acts,"double",["Dubbel toepassen testen","Test duplicate apply","Doppelte Anwendung testen"][idx()],()=>send("apply",{},lastApply));
 }
 if(s.status==="confirmation")button(acts,"check",t.registrationCheck,()=>send("check"));
 if(s.status==="needs_review")button(acts,"reassess",t.reassess,()=>send("reassess"),true);
 plan($("before"),s.active);plan($("after"),s.target,s.active);
 $("edit-section").hidden=s.route!=="B"||!["member_pending","confirmed"].includes(s.status);
 if(!$("edit-section").hidden){
  const i=s.target.intake;
  $("days").replaceChildren(...B.arrays.days.map(d=>{const l=node("label",null),input=node("input");input.type="checkbox";input.value=d;input.checked=i.days.includes(d);l.append(input,document.createTextNode(dayLabel(d)));return l;}));
  const ex=C.exercises.map(x=>[x.id,x.label[idx()]]);
  options($("favorite"),[["",t.none],...ex],i.favorites[0]||"");options($("avoid"),[["",t.none],...ex],i.avoided[0]||"");
  options($("exercise"),[["",t.none],...ex],s.target.plan.training.sessions[0].exercises[0].id);
 }
 $("changes").replaceChildren(...M.differences(s.active,s.target||s.active).map(d=>node("div",d.path+": "+JSON.stringify(d.before)+" -> "+JSON.stringify(d.after),"delta")));
 text("sources",JSON.stringify({binding:out.binding,calculations:out.facts,provenance:D[name][locale].provenance},null,2));
 text("versions",s.history.map(h=>t.version+" "+h.version+" ("+h.kind+")").join(" | "));
 $("audit").replaceChildren(...s.audit.map(a=>node("li",new Date(a.at).toISOString()+" | "+a.actor+" | "+a.action+" | "+a.status+" | v"+a.base+" -> v"+a.version+" | source "+a.source.slice(0,12))));
 const sim=$("simulations");sim.replaceChildren();
 for(const [a,label] of [["correct",t.correct],["stale",t.stale],["revoke",t.revoke],["expire",["Bronverloop simuleren","Simulate expiry","Quellenablauf simulieren"][idx()]],["health",names.current[idx()]]])button(sim,a,label,()=>{$("actor").value="member";send(a);});
 button(sim,"reset",t.reset,reset);
}
function reset(){model=M.create(D[name][locale]);last="";lastApply=null;$("actor").value="member";render();}
$("scenario").onchange=e=>{name=e.target.value;reset();};
$("language").onchange=e=>{locale=e.target.value;render();};
$("theme").onchange=e=>{document.body.dataset.theme=e.target.value;};
$("actor").onchange=render;
$("edit-form").onsubmit=e=>{e.preventDefault();send("edit",{days:[...$("days").querySelectorAll("input:checked")].map(i=>i.value),favorite:$("favorite").value,avoid:$("avoid").value,exercise:$("exercise").value});};
render();
