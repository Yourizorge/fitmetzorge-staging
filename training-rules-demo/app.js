"use strict";
const M=FMZ16Model,C=FMZ16Catalog,F=FMZ16Fixtures,R=FMZ16Review,L=FMZ16Copy,$=id=>document.getElementById(id),clone=x=>JSON.parse(JSON.stringify(x));
let locale="nl",model=M.create(F.base),review=null,message="",previousPlan=null,lastActivate=null;
const ix=()=>["nl","en","de"].indexOf(locale),w=k=>L.w[k]?.[ix()]||k,v=k=>L.values[k]?.[ix()]||String(k),label=k=>L.labels[k]?.[ix()]||k;
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;},err=k=>L.errors[k]?.[ix()]||w("fail")+" ("+k+")";
function button(parent,id,text,fn,primary=false){const b=el("button",text,primary?"primary":"");b.id=id;b.type="button";b.onclick=fn;parent.append(b);return b;}
function options(select,choices,current){select.replaceChildren();for(const [id,text]of choices){const o=el("option",text);o.value=String(id);select.append(o);}select.value=String(current);}
function form(i,c){
 const box=$("intake");box.replaceChildren();box.className="fields";
 const enums={goal:M.goals,experience:M.experiences,frequency:[2,4],minutes:[10,15,30,45,60],unit:["kg","lb"],rir:[true,false],rpe:[true,false],health:M.health,consent:[true,false]};
 for(const [key,values]of Object.entries(enums)){const l=el("label",undefined,"field"),s=el("select");s.id="f-"+key;l.append(el("span",key==="rir"||key==="rpe"?key.toUpperCase():label(key)));options(s,values.map(x=>[x,v(x)]),i[key]);l.append(s);box.append(l);}
 for(const [key,values]of Object.entries({days:M.days,equipment:["mat","dumbbell","band"],favorites:c.exercises.map(x=>x.id),excluded:c.exercises.map(x=>x.id)})){
  const f=el("fieldset"),choices=el("div",undefined,"choices");f.append(el("legend",label(key)));
  for(const id of values){const l=el("label"),x=el("input");x.type="checkbox";x.name=key;x.value=id;x.checked=i[key].includes(id);l.append(x,document.createTextNode(["favorites","excluded"].includes(key)?c.exercises.find(e=>e.id===id).label[ix()]:v(id)));choices.append(l);}f.append(choices);box.append(f);
 }
}
function readForm(){const i=model.view().intake;for(const key of ["goal","experience","frequency","minutes","unit","rir","rpe","health","consent"]){const x=$("f-"+key).value;i[key]=["frequency","minutes"].includes(key)?Number(x):["rir","rpe","consent"].includes(key)?x==="true":x;}for(const k of ["days","equipment","favorites","excluded"])i[k]=[...$("intake").querySelectorAll('input[name="'+k+'"]:checked')].map(e=>e.value);return i;}
function send(action,data={},event){review=null;previousPlan=clone(model.view().draft?.plan||null);const e=event||model.event(action,data),r=model.command(e);message=r.ok?(r.reason==="idempotent"?err("idempotent"):""):(action==="edit"?w("unchanged")+" ":"")+err(r.reason);if(action==="activate"&&r.ok)lastActivate=e;render();return r;}
function renderPlan(holder,p,editable=false){
 holder.replaceChildren();if(!p){holder.append(el("p",w("empty")));return;}
 const c=JSON.parse(p.source),i=model.view().intake;
 holder.append(el("p",w("option")+": "+v(p.goal)+" / "+v(p.experience)+" / "+p.sessions.length+" "+w("day")),el("p",w("catalog")+": "+p.catalogId+"@"+p.catalogVersion+" | "+p.layout+"@"+p.layoutVersion,"source-line"));
 for(const [si,s]of p.sessions.entries()){
  const section=el("div",undefined,"session"),day=el("select");day.className="session-day";day.dataset.day="";day.setAttribute("aria-label",w("day"));options(day,(editable?i.days:[s.day]).map(d=>[d,v(d)]),s.day);day.disabled=!editable;section.append(day);
  if(editable)button(section,"edit-day-"+si,w("edit"),()=>send("edit",{kind:"day",session:si,day:day.value}));
  const total=el("strong",String(s.seconds),"time-value");section.append(el("p",w("budget")+": "+p.budget+" sec"),total,el("span"," / "+p.budget+" sec"),el("p",w("estimate"),"notes"));
  for(const [ei,e]of s.exercises.entries()){
   const r=c.rules.find(x=>x.id===e.rule),ex=c.exercises.find(x=>x.id===e.exercise),box=el("div",undefined,"exercise");box.dataset.day=s.day;
   box.append(el("h4",ex.label[ix()]),el("p",w("role")+": "+v(e.role)+" / "+v(e.type)),el("p",w("reason")+": "+r.reason[ix()]),el("p",w("rule")+": "+r.id+"@"+e.ruleVersion,"source-line"));
   const prefix=holder.id==="proposal"?"":holder.id+"-",sel=el("select");sel.className="exercise-choice";sel.id=prefix+"ex-"+si+"-"+ei;sel.setAttribute("aria-label",w("alternatives"));
   options(sel,(editable?M.eligible(c,i,r):[ex]).map(x=>[x.id,x.label[ix()]]),e.exercise);sel.disabled=!editable;box.append(sel);
   const grid=el("div",undefined,"edit-grid"),inputs={};
   for(const key of ["sets","reps","rest","rir","rpe"]){
    const l=el("label");l.append(el("span",["rir","rpe"].includes(key)?key.toUpperCase():w(key)));
    let input;if(e[key]===null){input=el("span","-","effort-empty");}else{input=el("input");input.type="number";input.value=e[key];input.min=r[key].min;input.max=r[key].max;input.step=r[key].step;input.disabled=!editable;}
    input.dataset.field=key;input.id=prefix+key+"-"+si+"-"+ei;inputs[key]=input;l.append(input,el("span",r[key].min+" - "+r[key].max+" / "+r[key].step,"range"));grid.append(l);
   }box.append(grid);
   if(editable)button(box,"edit-ex-"+si+"-"+ei,w("edit"),()=>send("edit",{kind:"exercise",session:si,index:ei,exercise:sel.value,...Object.fromEntries(Object.entries(inputs).map(([k,e])=>[k,e.tagName==="INPUT"?(e.value===""?null:Number(e.value)):null]))}));
   box.append(el("p",w("load")+" ("+e.requestedUnit+")"),el("p",w("progression")+": +"+r.progression.step+" / max "+r.progression.ceiling,"notes"));
   if(e.history){const h=e.history;box.append(el("p",w("history")+": "+h.id+" / "+h.session+"@"+h.version,"source-line"),el("p",(h.weight.value??"-")+" "+h.weight.unit+" | "+h.reps+" reps | RIR "+(h.rir??"-")+" / RPE "+(h.rpe??"-"),"history-value"));}
   else box.append(el("p",w("missingHistory"),"notes"));
   box.append(el("p",w("unitsNote"),"notes"),el("p",w("selfReport"),"notes"),el("p",r.timing.setup_seconds+" + ("+e.sets+" x "+e.reps+" x "+r.timing.rep_seconds+") + ("+(e.sets-1)+" x "+e.rest+") = "+e.seconds+" sec","formula"));
   section.append(box);
  }
  section.append(el("p",w("formula")+": "+c.overhead_seconds+" + "+s.exercises.map(e=>e.seconds).join(" + ")+" = "+s.seconds+" sec","formula"));holder.append(section);
 }
}
function actualDisplay(){
 return {rows:[...$("proposal").querySelectorAll(".session")].flatMap(s=>[...s.querySelectorAll(".exercise")].map(e=>({day:s.querySelector(".session-day").value,exercise:e.querySelector(".exercise-choice").value,...Object.fromEntries(["sets","reps","rest","rir","rpe"].map(k=>{const x=e.querySelector('[data-field="'+k+'"]');return [k,x.tagName==="INPUT"?x.value:x.textContent];}))}))),times:[...$("proposal").querySelectorAll(".time-value")].map(e=>e.textContent),versions:$("versions").textContent,confirm:!!$("confirm"),activate:!!$("activate")};
}
function renderReview(){
 const index=review?R.scenarios.findIndex(x=>x.id===review.id):-1;
 $("scenario-buttons").replaceChildren();R.scenarios.forEach((c,i)=>{const b=button($("scenario-buttons"),"test-"+c.id,(i+1)+". "+c.title[ix()],()=>start(i));b.setAttribute("aria-pressed",String(i===index));});
 $("previous").disabled=index<=0;$("next").disabled=index===15;$("previous").onclick=()=>start(index-1);$("next").onclick=()=>start(index+1);
 $("step").textContent=index<0?w("choose"):w("steps")+" "+(index+1)+" "+w("of")+" 16";
 $("scenario-title").textContent=review?review.spec.title[ix()]:w("choose");$("expectation").textContent=review?review.spec.expected[ix()]:"";
 $("verdict").className="";$("verdict").removeAttribute("data-result");$("checks").replaceChildren();
 const s=model.view();$("used").textContent=label("goal")+": "+v(s.intake.goal)+" | "+label("experience")+": "+v(s.intake.experience)+" | "+s.intake.days.map(v).join(", ")+" | "+s.intake.minutes+" min | "+s.intake.equipment.map(v).join(", ")+" | "+w("catalog")+": "+s.catalog.id+"@"+s.catalog.version;
 if(!review){$("verdict").textContent=w("manual");return;}
 const result=R.assess(review,s,actualDisplay());$("verdict").textContent=result.pass?w("pass"):w("fail");$("verdict").className=result.pass?"pass":"fail";$("verdict").dataset.result=result.pass?"pass":"fail";
 $("checks").append(...result.checks.map(c=>el("li",(c.pass?"PASS: ":w("fail")+": ")+c.key+" | "+c.actual,c.pass?"":"check-fail")));
}
function render(){
 const s=model.view(),available=model.availability();document.documentElement.lang=locale;document.querySelectorAll("[data-word]").forEach(e=>e.textContent=w(e.dataset.word));
 $("catalog-line").textContent=w("catalog")+": "+s.catalog.id+"@"+s.catalog.version+" | "+s.catalog.review;
 $("feedback").textContent=message||(!available.ok?err(available.reason):s.status==="reassess"?w("review"):"");
 if(!available.ok&&available.reason==="safety")$("feedback").textContent+=" "+(FMZ15Data.registry.safety[s.intake.health]?.messages[locale]||[]).join(" ");
 form(s.intake,s.catalog);$("save").disabled=s.revoked||!s.intake.consent;
 $("actions").replaceChildren();button($("actions"),"build",w("build"),()=>send("build"),true);
 if(s.status==="pending")button($("actions"),"confirm",w("confirm"),()=>send("confirm"),true);
 if(s.status==="confirmed")button($("actions"),"activate",w("activate"),()=>send("activate"),true);
 if(["pending","confirmed"].includes(s.status))button($("actions"),"reject",w("reject"),()=>send("reject"));
 if(s.status==="active"){button($("actions"),"duplicate",w("duplicate"),()=>send("activate",{},lastActivate));if(s.history.length>1)button($("actions"),"restore",w("restore"),()=>send("restore",{version:s.history.at(-2).version}));}
 $("blocked").hidden=available.ok||!s.draft;
 renderPlan($("proposal"),s.draft?.plan,["pending","confirmed"].includes(s.status));renderPlan($("before"),review?.before||previousPlan);renderPlan($("active"),s.active?.plan);
 $("versions").textContent=s.history.map(h=>h.version).join(" / ")||"-";$("audit").replaceChildren(...s.audit.map(x=>el("li",x.request+" | "+x.action+" | "+x.from+" -> "+x.to+" | "+w("catalog")+" "+x.catalog+" | "+new Date(x.at).toISOString())));
 $("simulations").replaceChildren();button($("simulations"),"source",w("source"),()=>{const c=model.view().catalog;c.version++;for(const r of c.rules)r.version++;send("source",c);});button($("simulations"),"revoke",w("revoke"),()=>send("revoke"));button($("simulations"),"reset",w("reset"),reset);
 renderReview();
}
function start(index){review=R.run(R.scenarios[index].id);model=review.model;previousPlan=null;message="";lastActivate=null;render();$("review-result").focus({preventScroll:true});$("review-result").scrollIntoView({block:"start"});}
function reset(){model=M.create(F.base);review=null;previousPlan=null;message="";lastActivate=null;render();}
$("start").onclick=()=>start(0);$("language").onchange=e=>{locale=e.target.value;render();};$("theme").onchange=e=>document.body.dataset.theme=e.target.value;
$("intake-form").onsubmit=e=>{e.preventDefault();send("intake",readForm());};
for(const id of ["intake","proposal"])for(const event of ["input","change"])$(id).addEventListener(event,()=>{if(review){review=null;renderReview();}});
render();
