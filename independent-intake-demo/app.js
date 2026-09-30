"use strict";
const D=FMZ15Data,C=FMZ8Catalog,B=FMZ8Model,M=FMZ15Model,L=FMZ15Copy,$=id=>document.getElementById(id),clone=x=>JSON.parse(JSON.stringify(x));
let locale="nl",scenario="complete",model=M.create(D.fixtures[scenario],D.registry),last="",editError="",lastConfirm=null,lastActivate=null;
let ownerTest=null;
const R=FMZ15Review;
const ix=()=>["nl","en","de"].indexOf(locale),w=k=>L.words[k]?.[ix()]||k,v=k=>L.values[k]?.[ix()]||String(k),label=k=>L.labels[k]?.[ix()]||k;
const n=(tag,text,cls)=>{const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;};
const error=k=>L.words.errors[k]?.[ix()]||w("noPlan")+" ("+k+")";
function opts(select,values,current,unknown=false){select.replaceChildren();if(unknown){const o=n("option",w("unknown"));o.value="";select.append(o);}for(const [id,text]of values){const o=n("option",text);o.value=String(id);select.append(o);}select.value=current===null?"":String(current);}
const list={
 ...B.arrays,disliked:C.exercises.map(x=>x.id),machines:["cable"],dietLimits:["medical_diet"]
};
function textFor(key,value){if(["favorites","avoided","disliked"].includes(key))return C.exercises.find(x=>x.id===value).label[ix()];if(key==="excludedFoods")return C.foods.find(x=>x.id===value).label[ix()];return v(value);}
const enums={...B.enums,location:["home","gym"],locale:["nl","en","de"],health:M.health,consent:[true,false],rir:[true,false],rpe:[true,false]};
const groups={goals:["goal","secondary","experience","favorites","disliked","avoided"],practice:["days","minutes","location","machines","equipment","movement","unit","rir","rpe"],food:["diet","allergies","excludedFoods","dietLimits","meals","kitchen","budget","rhythm"],records:["sleep","recovery","activity","health","locale","consent"]};
function form(i){
 const holder=$("intake");holder.replaceChildren();
 for(const [group,keys]of Object.entries(groups)){
  const d=n("details",undefined,"group");d.open=group==="goals";d.append(n("summary",w(group)));const grid=n("div",undefined,"fields");
  for(const key of keys){
   if(list[key]){const f=n("fieldset",undefined,"multi");f.append(n("legend",label(key)));const known=n("label",undefined,"recorded"),k=n("input");k.type="checkbox";k.id="known-"+key;k.checked=Array.isArray(i[key]);known.append(k,document.createTextNode(w("known")));f.append(known);
    const choices=n("div",undefined,"choices");for(const value of list[key]){const l=n("label"),x=n("input");x.type="checkbox";x.name=key;x.value=value;x.checked=Array.isArray(i[key])&&i[key].includes(value);x.disabled=!k.checked;l.append(x,document.createTextNode(textFor(key,value)));choices.append(l);}
    k.onchange=()=>choices.querySelectorAll("input").forEach(x=>x.disabled=!k.checked);f.append(choices);grid.append(f);
   }else{const l=n("label",undefined,"field");l.append(n("span",label(key)));let input;
    if(key==="activity"){input=n("input");input.type="number";input.min=0;input.max=1440;input.step=1;input.value=i.records?.activity_minutes??"";}
    else{input=n("select");opts(input,enums[key].map(x=>[x,v(x)]),i[key],true);}
    input.id="f-"+key;l.append(input);grid.append(l);
   }
  }d.append(grid);holder.append(d);
 }
}
function readForm(){const i=clone(model.view().intake);
 for(const keys of Object.values(groups))for(const key of keys){if(list[key])i[key]=$("known-"+key).checked?[...document.querySelectorAll('input[name="'+key+'"]:checked')].map(x=>x.value):null;
 else{const raw=$("f-"+key).value;if(key==="activity")i.records.activity_minutes=raw===""?null:Number(raw);else if(raw==="")i[key]=null;else if(["consent","rir","rpe"].includes(key))i[key]=raw==="true";else if(["minutes","meals","sleep"].includes(key))i[key]=Number(raw);else i[key]=raw;}}
 i.records.sleep=i.sleep;i.records.recovery=i.recovery;i.records.revision++;return i;
}
function button(parent,id,text,fn,primary=false){const b=n("button",text,primary?"primary":"");b.type="button";b.id=id;b.onclick=fn;parent.append(b);}
function send(action,data={},e){ownerTest=null;const event=e||model.event(action,data),r=model.command(event);last=r.ok?r.reason==="idempotent"?w("idempotent"):"":error(r.reason);editError=action==="edit"&&!r.ok?w("unchanged")+" "+error(r.reason):"";
 if(action==="confirm"&&r.ok)lastConfirm=event;if(action==="activate"&&r.ok)lastActivate=event;render();return r;}
function renderPlan(el,p,i,editable){
 el.replaceChildren();if(!p){el.append(n("p",w("noPlan")));return;}
 el.append(n("p",w("proposalText")),n("p",w("setRule"),"notes"));
 for(const [si,session]of p.training.sessions.entries()){
  const section=n("div",undefined,"session");section.append(n("h3",v(session.day)+" | "+p.training.minutes+" "+w("minutes")));
  for(const [ei,ex]of session.exercises.entries()){
   const box=n("div",undefined,"exercise-editor"),name=n("strong",C.exercises.find(x=>x.id===ex.id).label[ix()]);name.dataset.reviewExercise=ex.id;box.append(name);
   box.append(n("p",ex.sets+" x "+ex.reps+" | "+w("rest")+": "+ex.rest+" | "+(ex.load??"-")+" "+ex.unit+" | RIR "+(ex.rir??"-")+" / RPE "+(ex.rpe??"-")));
   box.append(n("p",C.policy.catalog+" / "+ex.rule+" / sets."+i.experience,"notes"));
   if(editable){const row=n("div",undefined,"toolbar"),sel=n("select");sel.id="ex-"+si+"-"+ei;opts(sel,B.eligibleExercises(i).filter(x=>x.id===ex.id||!session.exercises.some(e=>e.id===x.id)).map(x=>[x.id,x.label[ix()]]),ex.id);
    const sets=n("input"),reps=n("input");for(const [input,value,max,id]of [[sets,ex.sets,3,"sets"],[reps,ex.reps,12,"reps"]]){input.type="number";input.min=1;input.max=max;input.step=1;input.value=value;input.id=id+"-"+si+"-"+ei;}
    for(const [key,x]of [["alternative",sel],["sets",sets],["reps",reps]]){const l=n("label");l.append(n("span",w(key)),x);row.append(l);}box.append(row);
    button(box,"edit-ex-"+si+"-"+ei,w("edit"),()=>send("edit",{kind:"exercise",session:si,index:ei,id:sel.value,sets:Number(sets.value),reps:Number(reps.value)}));
   }section.append(box);
  }el.append(section);
 }
 const food=n("div",undefined,"food-plan");food.append(n("h3",w("food")),n("p",w("nutritionText")));
 for(const [mi,meal]of p.nutrition.meals.entries()){
  const box=n("div",undefined,"meal-editor"),recipe=C.recipes.find(x=>x.id===meal.id);box.append(n("h4",(recipe?.label[ix()]||w("meal"))+" | "+meal.at+":00"));
  if(editable){const sel=n("select");sel.id="meal-"+mi;sel.setAttribute("aria-label",w("meal")+" "+(mi+1));opts(sel,B.eligibleMeals(i).map(x=>[x.id,x.label[ix()]]),meal.id);box.append(sel);button(box,"edit-meal-"+mi,w("edit"),()=>send("edit",{kind:"meal",index:mi,id:sel.value}));}
  for(const [fi,item]of meal.items.entries()){
   const row=n("div",undefined,"meal-item"),name=n("span",C.foods.find(x=>x.id===item.food).label[ix()]+" | "+item.g+" g");name.dataset.reviewFood=item.food;row.append(name);
   if(editable){const sel=n("select");sel.id="food-"+mi+"-"+fi;sel.setAttribute("aria-label",w("item")+" "+(mi+1)+"."+(fi+1));opts(sel,C.foods.filter(x=>B.foodAllowed(x.id,i)).map(x=>[x.id,x.label[ix()]]),item.food);row.append(sel);button(row,"edit-food-"+mi+"-"+fi,w("edit"),()=>send("edit",{kind:"food",meal:mi,index:fi,id:sel.value}));}box.append(row);
  }food.append(box);
 }food.append(n("p",p.nutrition.totals.kcal+" kcal | P "+p.nutrition.totals.protein+" g | C "+p.nutrition.totals.carbs+" g | F "+p.nutrition.totals.fat+" g", "notes"));el.append(food);
 el.append(n("h3",w("records")),n("p",w("recoveryText")),n("p",w("sleepTemplate")+": "+p.recovery.sleepGoal+" | "+w("checkins")+": "+v(p.recovery.checkins)),n("p",w("restDays")+": "+p.recovery.restDays.map(v).join(", ")));
}
function render(){
 const s=model.view();document.documentElement.lang=locale;document.querySelectorAll("[data-word]").forEach(x=>x.textContent=w(x.dataset.word));
 opts($("scenario"),Object.keys(D.fixtures).map(k=>[k,L.scenarios[k][ix()]]),scenario);opts($("theme"),[["light",w("light")],["dark",w("dark")]],document.body.dataset.theme||"light");
 $("status").textContent="Route B | "+L.words.statuses[s.status][ix()];
 const avail=model.availability();$("reason").textContent=last||(!avail.ok?error(avail.reason):s.status==="needs_review"?w("intakeChanged"):"");
 const safety=D.registry.safety[s.intake.health];if(!avail.ok&&avail.reason==="safety"&&safety)$("reason").textContent+=" "+(safety.messages[locale]||[]).join(" ");
 const acts=$("actions");acts.replaceChildren();button(acts,"build",w("build"),()=>send("build"),true);
 if(s.status==="member_pending")button(acts,"confirm",w("confirm"),()=>send("confirm"),true);
 if(["member_pending","confirmed"].includes(s.status))button(acts,"reject",w("reject"),()=>send("reject"));
 if(s.status==="confirmed"){button(acts,"activate",w("activate"),()=>send("activate"),true);button(acts,"double-confirm",w("doubleConfirm"),()=>send("confirm",{},lastConfirm));}
 if(s.status==="active"){button(acts,"double-activate",w("doubleActivate"),()=>send("activate",{},lastActivate));if(s.history.length>1)button(acts,"restore",w("restore"),()=>send("restore",{version:s.history.at(-2).version}));}
 form(s.intake);$("save").disabled=s.revoked||!s.intake.consent;
 renderPlan($("proposal"),s.draft?.plan,s.draft?.intake||s.intake,["member_pending","confirmed"].includes(s.status));$("edit-result").textContent=editError;
 $("proposal-warning").hidden=avail.ok||!s.draft;
 const activeIntake=s.active?s.intakeHistory.find(x=>x.revision===s.active.intakeRevision).intake:s.intake;renderPlan($("active"),s.active?.plan,activeIntake,false);
 $("sources").textContent=JSON.stringify({intake_revision:s.intakeRevision,records:s.intake.records,source:s.source,proposal:s.draft?.refs||null},null,2);
 $("versions").textContent="Intake: "+s.intakeHistory.map(x=>x.revision).join(" / ")+" | Plan: "+(s.history.map(x=>x.version).join(" / ")||"-");
 $("audit").replaceChildren(...s.audit.map(x=>n("li",new Date(x.at).toISOString()+" | "+x.action+" | "+x.status+" | v"+x.from+" -> v"+x.to+" | intake "+x.intake)));
 const sim=$("simulations");sim.replaceChildren();for(const action of ["stale","expire","revoke"])button(sim,action,w(action),()=>send(action));button(sim,"reset",w("reset"),reset);
 renderOwnerTest();
}
function reset(){ownerTest=null;model=M.create(D.fixtures[scenario],D.registry);last="";editError="";lastConfirm=null;lastActivate=null;render();}
function startOwnerTest(index){
 ownerTest=R.run(R.cases[index].id);model=ownerTest.model;scenario=ownerTest.spec.fixture;last="";editError="";
 lastConfirm=ownerTest.ledger.filter(x=>x.action==="confirm"&&x.ok).at(-1)?.event||null;
 lastActivate=ownerTest.ledger.filter(x=>x.action==="activate"&&x.ok).at(-1)?.event||null;
 render();$("review-summary").focus({preventScroll:true});$("review-summary").scrollIntoView({block:"start"});
}
function renderOwnerTest(){
 const index=ownerTest?R.cases.findIndex(x=>x.id===ownerTest.id):-1;
 $("test-buttons").replaceChildren();
 R.cases.forEach((c,i)=>{button($("test-buttons"),"test-"+c.id,(i+1)+". "+c.title,()=>startOwnerTest(i));$("test-"+c.id).setAttribute("aria-pressed",String(i===index));});
 $("review-prev").disabled=index<=0;$("review-next").disabled=index===R.cases.length-1;
 $("review-prev").onclick=()=>startOwnerTest(index-1);$("review-next").onclick=()=>startOwnerTest(index+1);
 $("review-step").textContent=index<0?"Kies een test":("Stap "+(index+1)+" van "+R.cases.length);
 $("review-finish").textContent=index===8?"Laatste stap. Meld welke uitkomst je ziet en of alles duidelijk is. Je akkoord wordt niet automatisch vastgelegd.":"";
 $("review-facts").replaceChildren();$("review-checks").replaceChildren();
 const badge=$("review-verdict");badge.className="";badge.removeAttribute("data-result");
 if(!ownerTest){$("review-title").textContent="Nog geen actuele test";badge.textContent="Kies een test. Na een handmatige wijziging moet je opnieuw testen.";return;}
 $("review-title").textContent=ownerTest.spec.title;
 for(const [title,key]of [["Gewijzigde gegevens","changed"],["Verwacht gedrag","expected"],["Mag er een voorstel komen?","permission"],["Waarom wel of niet?","reason"]])$("review-facts").append(n("dt",title),n("dd",ownerTest.spec[key]));
 const display={locale:ix(),foods:[...$("proposal").querySelectorAll("[data-review-food]")].map(e=>({id:e.dataset.reviewFood,text:e.textContent})),exercises:[...$("proposal").querySelectorAll("[data-review-exercise]")].map(e=>({id:e.dataset.reviewExercise,text:e.textContent})),versions:$("versions").textContent,confirm:!!$("confirm"),activate:!!$("activate"),blockedNotice:!$("proposal-warning").hidden};
 const result=R.assess(ownerTest,model.view(),display);badge.textContent=result.pass?"PASS - het zichtbare resultaat klopt.":"AFWIJKING - het resultaat wijkt af. Meld deze test; nog niet goedkeuren.";badge.className=result.pass?"review-pass":"review-fail";badge.dataset.result=result.pass?"pass":"fail";
 const words={build:"voorstel maken",edit:"product wijzigen",confirm:"bevestigen",activate:"activeren",intake:"intake wijzigen",stale:"bronconflict",revoke:"toestemming intrekken",restore:"terugzetvoorstel",success:"uitgevoerd",idempotent:"niets dubbel gewijzigd",excluded:"uitgesloten product geweigerd",incomplete:"verplicht gegeven ontbreekt",safety:"klacht blokkeert plan",machine_rule_missing:"apparaatregel ontbreekt",rule_source:"bronversie klopt niet",version_conflict:"verouderde of dubbele aanvraag geweigerd",consent:"geen toestemming",member_pending:"wacht op bevestiging"};
 const ul=n("ul");
 for(const c of result.checks){let title=c.label;if(title.startsWith("Uitkomst "))title="Testhandeling: "+(words[title.slice(9)]||title.slice(9));const li=n("li",(c.pass?"Klopt: ":"AFWIJKING: ")+title+" - "+(words[c.observed]||c.observed));li.className=c.pass?"check-ok":"check-fail";ul.append(li);}
 const details=n("details");details.append(n("summary","Bekijk de uitgevoerde controles"),ul);$("review-checks").append(details);
 const direct=result.checks.filter(c=>/in voedingsvoorstel|in training|in trainingsvoorstel|Aantal planversies|Versie [12] behouden|Nieuwe versie bevat/.test(c.label));
 for(const c of direct)$("review-checks").prepend(n("p",(c.pass?"Klopt: ":"AFWIJKING: ")+c.label+" - "+c.observed,c.pass?"check-ok":"check-fail"));
}
$("review-start").onclick=()=>startOwnerTest(0);
for(const event of ["input","change"])$("intake-form").addEventListener(event,()=>{if(ownerTest){ownerTest=null;renderOwnerTest();}});
for(const event of ["input","change"])$("proposal").addEventListener(event,()=>{if(ownerTest){ownerTest=null;renderOwnerTest();}});
$("language").onchange=e=>{locale=e.target.value;render();};$("theme").onchange=e=>{document.body.dataset.theme=e.target.value;};$("scenario").onchange=e=>{scenario=e.target.value;reset();};
$("intake-form").onsubmit=e=>{e.preventDefault();send("intake",readForm());};render();
