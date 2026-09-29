"use strict";
const {copy,number}=FMZ13Copy,$=s=>document.querySelector(s),el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let locale="nl",name="changes",model,serial=0;
const catalog=()=>FMZ13Data.locales[locale][name];
function start(){model=FMZ13Model.create(FMZ13Data.locales.nl[name]);serial=0;act("source_arrival","v1");}
function act(type,source){const e=model.event(type,source,"syn-command-"+(++serial));model.command(e);render();}
function button(id,text,handler,disabled=false,cls=""){const b=el("button",text,cls);b.id=id;b.type="button";b.disabled=disabled;b.onclick=handler;return b;}
function render(){
 const c=copy[locale],s=model.view(),v=catalog().versions.find(v=>v.key===s.current),r=v.result,withdrawn=s.revoked||s.expired;
 document.documentElement.lang=locale;
 document.querySelectorAll("[data-copy]").forEach(n=>n.textContent=c[n.dataset.copy]);
 $("#title").textContent=c.title;$("#banner").textContent=c.banner;$("#scope").textContent=c.scope;$("#notice").textContent=c.notices;$("#boundary").textContent=c.readonly;
 $("#reset").textContent=c.reset;$("#theme option[value=light]").textContent=c.light;$("#theme option[value=dark]").textContent=c.dark;
 const scenario=$("#scenario");scenario.replaceChildren(...FMZ13Data.scenarios.map((key,i)=>{const o=el("option",c.cases[i]);o.value=key;return o;}));scenario.value=name;
 const card=s.cards.find(x=>x.key===s.current),pending=!withdrawn&&card?.state==="pending";
 $("#count").textContent=String(s.cards.filter(x=>x.state==="pending").length);
 $("#notification").textContent=pending?c.notification:"";
 $("#context").replaceChildren(...r.feedback.map(t=>el("p",t)));
 $("#summary").textContent=withdrawn?(s.revoked?c.access:c.expired):c[r.status==="unchanged"?"unchangedState":r.status];
 $("#facts").replaceChildren(...(withdrawn?[]:r.facts).map(f=>{
  const box=el("article",undefined,"metric");box.dataset.metric=f.metric;box.append(el("h3",c.metrics[f.metric]));
  const values=el("div",undefined,"values");
  for(const [k,label]of [["previous",c.before],["current",c.after]]){const side=el("div");side.append(el("span",label),el("strong",number(f[k].sum/f[k].divisor,locale)));values.append(side);}
  const delta=el("div",undefined,"delta");delta.append(el("span",c.delta),el("strong",(f.delta_numerator>0?"+":"")+number(f.delta_numerator/f.delta_divisor,locale)));
  box.append(values,el("div",c.units[f.metric],"unit"),delta);return box;
 }));
 $("#proposal").textContent=withdrawn?"":r.messages[0];
 $("#actions").replaceChildren();
 if(pending)$("#actions").append(button("review",c.review,()=>act("review"),false,"primary-action"),button("dismiss",c.dismiss,()=>act("dismiss")));
 $("#calculations").replaceChildren(...(withdrawn?[]:r.calculations).map(f=>{
  const d=el("div",undefined,"calculation");d.append(el("h3",c.metrics[f.metric]));
  for(const [key,label]of [["previous",c.before],["current",c.after]]){
   d.append(el("p",label+": ("+f[key].values.join(" + ")+") / "+f[key].divisor+" = "+number(f[key].sum/f[key].divisor,locale)),
    el("code",f[key].refs.map(x=>x.id+" @v"+x.revision).join("; ")));
  }
  d.append(el("p",c.delta+": ("+f.current.sum+" - "+f.previous.sum+") / "+f.delta_divisor+" = "+number(f.delta_numerator/f.delta_divisor,locale)));return d;
 }));
 $("#source").replaceChildren(el("p",v.source.route==="HUMAN_REQUIRED"?c.routeA:c.routeB),el("p",c.goal),
  el("p",v.source.goal_ref.id+" @v"+v.source.goal_ref.revision),el("p",v.source.snapshot_ref.id+" @v"+v.source.snapshot_ref.revision),
  el("p",v.source.id+" @v"+v.revision),el("code",v.source_hash),el("p",c.safety+": "+r.context_mode));
 $("#source-controls").replaceChildren(
  button("replay",c.replay,()=>act("source_arrival",s.current),withdrawn),
  button("correct",c.correct,()=>act("source_arrival","v2"),withdrawn||v.revision!==1),
  button("restore",c.restore,()=>act("source_arrival","v3"),withdrawn||v.revision!==2),
  button("expire",c.expire,()=>act("expire"),withdrawn),
  button("revoke",c.revoke,()=>act("revoke"),withdrawn));
 $("#access").replaceChildren();
 for(const [key,label]of [["chat",c.chat],["history",c.past],["new_analysis",c.analysis]])$("#access").append(el("dt",label),el("dd",r.access[key]&&!(s.revoked&&key==="new_analysis")?c.yes:c.no));
 $("#history").replaceChildren(...s.history.map(h=>el("li","v"+h.revision+" · "+(c[s.cards.find(x=>x.key===h.key)?.state]||c.blocked)+" · "+h.source_hash.slice(0,12))));
 $("#audit").replaceChildren(...s.audit.map(a=>el("li",a.sequence+" · "+a.type+" · "+a.source+" · "+new Date(a.synthetic_timestamp_ms).toISOString())));
}
$("#scenario").onchange=e=>{name=e.target.value;start();};$("#language").onchange=e=>{locale=e.target.value;render();};
$("#theme").onchange=e=>document.documentElement.dataset.theme=e.target.value;$("#reset").onclick=start;
start();
