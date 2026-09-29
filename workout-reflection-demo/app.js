"use strict";
(()=>{const $=id=>document.getElementById(id),names=Object.keys(FMZ6E12Data.profiles);
let locale="nl",scenario="normal",role="member",memory,draft,lastReason="",seq=0;
const c=()=>FMZ6E12Copy[locale],profile=()=>FMZ6E12Data.profiles[scenario][locale];
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const num=v=>v===null?c().missing:String(v).replace(".",locale==="en"?".":",");
const target=e=>e.sets.map(s=>num(s.reps.min)+(s.reps.min!==s.reps.max?"-"+num(s.reps.max):"")+" "+c().reps+" / "+num(s.load.value)+" "+s.load.unit).join(" · ");
function reset(){memory=FMZ6E12Memory.create(profile());draft=structuredClone(profile().draft.sets);lastReason="";seq=0;role="member";$("role").value=role;render();}
function labels(){
 const text={"scope":"scope","reset-note":"resetNote","language-label":"language","theme-label":"theme","reset":"reset","title":"title","demo-label":"demo","scenario-label":"scenario","role-label":"role","registration-title":"registrationTitle","register":"register","reflect":"reflect","review-title":"reviewTitle","registration-history-title":"regHistory","reason-title":"reasons","history-title":"history","audit-title":"audit","event-label":"event","inject":"inject","example-limit":"exampleLimit","footer":"footer"};
 for(const [id,key]of Object.entries(text))$(id).textContent=c()[key];
 $("role").options[0].text=c().member;$("role").options[1].text=c().trainer;
 $("scenario").replaceChildren(...names.map((n,i)=>{const o=new Option(c().scenarios[i],n);o.selected=n===scenario;return o;}));
 const event=$("source-event").value||"version_conflict";$("source-event").replaceChildren(...Object.entries(c().events).map(([k,v])=>new Option(v,k)));$("source-event").value=event;
 document.documentElement.lang=locale;
}
function form(){
 const p=profile();$("sets").replaceChildren();
 for(const e of p.snapshot.exercises){
  const box=el("div",undefined,"exercise"),label=p.pack.catalog.find(x=>x.id===e.exercise_id)?.labels[locale]||e.exercise_id;
  box.append(el("h3",label));const head=el("div",undefined,"set-head");for(const name of ["#",e.sets[0].load.unit.toUpperCase(),c().reps.toUpperCase(),"RIR","RPE"])head.append(el("span",name));box.append(head);
  for(const t of draft.filter(t=>t.exercise_id===e.exercise_id)){
   const row=el("div",undefined,"set");row.append(el("span",String(t.set_index)));
   for(const field of ["load","reps","rir","rpe"]){const input=document.createElement("input");input.type="number";input.inputMode="decimal";input.min=field==="rpe"?"1":"0";input.step=field==="load"||field==="rpe"?"0.5":"1";if(field==="rir"||field==="rpe")input.max="10";
    input.value=(field==="load"?t.load.value:t[field])??"";input.setAttribute("aria-label",label+" "+t.set_index+" "+(field==="load"?t.load.unit:field.toUpperCase()));input.dataset.field=field;input.dataset.set=t.id;
    input.oninput=()=>{const v=input.value===""?null:Number(input.value);if(field==="load")t.load.value=v;else t[field]=v;};row.append(input);
   }box.append(row);
  }$("sets").append(box);
 }
 $("snapshot").textContent=c().snapshot+": "+p.snapshot.id+" | "+p.snapshot.plan_ref.id+"@"+p.snapshot.plan_ref.revision+" | "+c().goal+": "+p.snapshot.goal_ref.id+"@"+p.snapshot.goal_ref.revision;
}
function actionButton(action,targetVersion=null){
 const b=el("button",action==="restore"?c().restore:c().actions[action],action==="apply"?"primary":"");b.dataset.action=action;
 b.onclick=()=>{const ev=memory.event(action,role,"cmd-ui-"+(++seq),targetVersion),r=memory.command(ev);lastReason=r.ok?"done":"failed";render(false);};return b;
}
function render(rebuildForm=true){
 labels();if(rebuildForm)form();const v=memory.view(),w=v.workflow,p=w?.proposal;
 $("reg-version").textContent="v"+v.records.length;$("plan-version").textContent=c().version+" "+(w?.active.revision||profile().pack.plan.revision);
 $("register").disabled=!!w?.history.length;$("reflect").disabled=!v.records.length||!!w?.history.length;
 $("feedback").textContent=c().feedback[lastReason]||c().events[lastReason]||(lastReason?c().feedback.blocked:"");
 $("registration-history").replaceChildren(...v.records.map(r=>el("div","v"+r.revision+" | "+r.sets.length+" "+c().sets+" | "+r.snapshot.plan_ref.id+"@"+r.snapshot.plan_ref.revision,"record")));
 const index=!v.records.length?0:!p?1:p.status==="member_pending"?2:p.status==="trainer_pending"?3:4;
 $("steps").replaceChildren(...c().steps.map((s,i)=>el("div",(i+1)+". "+s,"step"+(i<=index?" active":""))));
 $("empty").textContent=p?"":c().empty;$("empty").hidden=!!p;$("status").textContent=p?c().states[p.status]:"";$("status").className=p&&["blocked","rejected"].includes(p.status)?"warning":"";
 $("comparison").replaceChildren();$("actions").replaceChildren();$("reasons").replaceChildren();$("history").replaceChildren();$("audit").replaceChildren();
 $("reason-detail").hidden=!p;
 if(!p)return;
 for(const e of p.base.options[0].exercises){
  const label=profile().pack.catalog.find(x=>x.id===e.exercise_id)?.labels[locale]||e.exercise_id;
  const next=p.target.options[0].exercises.find(x=>x.exercise_id===e.exercise_id);
  const box=el("div",undefined,"comparison-row");box.append(el("h3",label));const grid=el("div",undefined,"compare-grid");
  for(const [caption,ex]of [[c().current,e],[c().next,next]]){const cell=el("div");cell.append(el("span",caption),el("strong",target(ex),JSON.stringify(e.sets)!==JSON.stringify(ex.sets)?"changed":""));grid.append(cell);}box.append(grid);
  const registered=v.records.at(-1).sets.filter(x=>x.exercise_id===e.exercise_id).map(t=>num(t.reps)+" "+c().reps+" / "+num(t.load.value)+" "+t.load.unit+" / RIR "+num(t.rir)+" / RPE "+num(t.rpe)).join(" · ");
  box.append(el("p",c().recorded+": "+(registered||c().missing),"reason"));
  box.append(el("p",p.kind==="restore"?c().restoreReason:p.status==="blocked"?c().feedback.blocked:profile().short_reasons[e.exercise_id]||"","reason"));$("comparison").append(box);
 }
 const allowed=role==="member"&&p.status==="member_pending"?["member_accept","member_reject"]:role==="trainer"&&p.status==="trainer_pending"?["trainer_approve","trainer_reject","trainer_block"]:role==="trainer"&&p.status==="approved"?["apply"]:[];
 for(const a of allowed)$("actions").append(actionButton(a));
 const known=JSON.stringify(v.records.at(-1).sets)===JSON.stringify(profile().draft.sets);
 const messages=v.gate?[c().events[v.gate],c().feedback.blocked]:p.kind==="restore"?[c().restoreReason]:known?profile().messages:[c().feedback.not_example];
 for(const m of messages)$("reasons").append(el("p",m));
 if(known&&profile().pack.w2.length){
  for(const row of profile().pack.w2)$("reasons").append(el("p",row.exercise+" | "+c().weightStep+": "+num(row.step)+" "+row.unit+" | "+c().weights+": "+row.available.map(num).join(", ")+" "+row.unit));
  $("reasons").append(el("p",c().w2Reason));
 }
 for(const h of w.history){const row=el("div",undefined,"version");row.append(el("span",c().version+" "+h.revision));if(p.status==="applied"&&!w.gate)row.append(actionButton("restore",h.revision));$("history").append(row);}
 for(const entry of w.audit)$("audit").append(el("li",entry.at+" | "+(c().actions[entry.action]||c().events[entry.reason]||entry.action)+" | "+(entry.actor==="trainer"?c().trainer:entry.actor==="member"?c().member:"system")+" | v"+entry.before_version+" → v"+entry.after_version,"audit-entry"));
}
$("language").onchange=e=>{locale=e.target.value;render();};
$("theme").onchange=e=>document.documentElement.dataset.theme=e.target.value;
$("scenario").onchange=e=>{scenario=e.target.value;reset();};
$("role").onchange=e=>{role=e.target.value;render(false);};
$("reset").onclick=reset;
$("register").onclick=()=>{const r=memory.register(draft);lastReason=r.reason;render(false);};
$("reflect").onclick=()=>{const r=memory.reflect();lastReason=r.reason;render(false);};
$("inject").onclick=()=>{const code=$("source-event").value;memory.inject(code);lastReason=code;render(false);};
reset();
})();
