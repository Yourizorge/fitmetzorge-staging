// Generated presentation adapter from frozen 6E-8; no local command execution.
window.FMZ9Render=function(ctx){
const {lang,tab,form,pendingIntake,scenario}=ctx;const M=FMZ8Model,C=FMZ8Catalog,clone=x=>JSON.parse(JSON.stringify(x));const view=clone(ctx.state.view);view.audit=ctx.state.audit.map(x=>({...x,base:x.source_version,version:x.target_version}));view.notifications=[];const a={view:()=>view},b={view:()=>view};
const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ix=()=>["nl","en","de"].indexOf(lang),t=k=>FMZ8Copy[lang][k]||FMZDemoCopy[lang][k]||k,ta=k=>FMZDemoCopy[lang][k]||t(k),label=x=>x.label[ix()];
const option=(v,text,current)=>'<option value="'+esc(v)+'"'+(same(v,current)?" selected":"")+'>'+esc(text)+'</option>';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const btn=(text,action,data={},style="",disabled=false)=>'<button type="button" class="'+style+'" data-action="'+action+'" data-value="'+esc(JSON.stringify(data))+'"'+(disabled?" disabled":"")+'>'+esc(text)+'</button>';
const icon=(name,title,action,data={})=>'<button type="button" class="icon" title="'+esc(title)+'" aria-label="'+esc(title)+'" data-action="'+action+'" data-value="'+esc(JSON.stringify(data))+'"><img src="../assets/vendor/lucide-'+name+'.svg" alt=""></button>';
const pre=x=>'<pre>'+esc(JSON.stringify(x,null,2))+'</pre>';
const details=(title,body)=>'<details><summary>'+esc(title)+'</summary>'+body+'</details>';
function field(k,i){
 const choices=M.enums[k];return '<label>'+esc(t(k))+'<select name="'+k+'">'+choices.map(v=>option(v,t(String(v)),i[k])).join("")+'</select></label>';
}
function checks(k,i){
 return '<fieldset><legend>'+esc(t(k))+'</legend><div class="checks">'+M.arrays[k].map(v=>{
  const obj=(["favorites","avoided"].includes(k)?C.exercises:k==="excludedFoods"?C.foods:[]).find(x=>x.id===v);
  return '<label><input type="checkbox" name="'+k+'" value="'+esc(v)+'"'+(i[k].includes(v)?" checked":"")+'>'+esc(obj?label(obj):t(v))+'</label>';
 }).join("")+'</div></fieldset>';
}
function intake(){
 const i=pendingIntake||b.view().intake;
 return '<section><h2>'+t("intake")+'</h2><form id="intake" novalidate><div class="intake-grid">'+
 ["goal","secondary","experience","days","minutes","equipment","favorites","avoided","movement","rir","rpe","diet","allergies","excludedFoods","meals","kitchen","budget","rhythm","sleep","recovery","unit"].map(k=>M.enums[k]?field(k,i):M.arrays[k]?checks(k,i):'<label class="checks"><span><input type="checkbox" name="'+k+'"'+(i[k]?" checked":"")+'>'+t(k)+'</span></label>').join("")+
 '</div><div class="actions">'+btn(t("build"),"build",{},"primary")+'</div></form></section>';
}
function exerciseEditor(e,n,session,i,all){
 const alternatives=M.eligibleExercises(i).filter(x=>!all.some(y=>y.id===x.id)||x.id===e.id);
 const selection='<select aria-label="'+esc(t("replace"))+'" data-replace="'+session+':'+n+'">'+alternatives.map(x=>option(x.id,label(x),e.id)).join("")+'</select>';
 const effects=alternatives.filter(x=>x.id!==e.id).map(x=>{const ef=M.effect(e.id,x.id,i);return '<p class="effect">'+esc(label(x)+": "+ef.muscle.map(t).join(" → ")+" / "+ef.equipment.map(t).join(" → ")+" / "+t(ef.goal)+": "+t(ef.goalMatch?"yes":"no"))+'</p>';}).join("");
 return '<div class="row">'+selection+btn(t("replace"),"replace",{session,index:n})+icon("arrow-up",t("move"),"edit",{kind:"move",session,index:n,to:Math.max(n-1,0)})+icon("trash-2",t("remove"),"edit",{kind:"remove",session,index:n})+'</div>'+details(t("effect"),effects);
}
function training(p,i,editable){
 return '<p>'+esc(t(p.goal)+" / "+p.days.map(t).join(", ")+" / "+p.minutes+" min")+'</p>'+
 (p.sessionStart?'<p>'+t("time")+': '+esc(p.sessionStart)+'</p>':"")+
 p.sessions.map((s,session)=>'<h3>'+t(s.day)+'</h3>'+s.exercises.map((e,n)=>{
 const x=C.exercises.find(x=>x.id===e.id);
 return '<article class="exercise-row"><strong>'+(n+1)+'. '+esc(label(x))+'</strong><p class="measure">'+e.sets+' '+t("sets")+' × '+e.reps+' '+t("reps")+' / '+t("rest")+' '+e.rest+' s</p><p class="small">'+(e.rir===null?"":"RIR "+e.rir+" ") +(e.rpe===null?"":"RPE "+e.rpe)+' / '+t("loadMissing")+' ('+esc(e.unit)+')</p>'+
 (editable?exerciseEditor(e,n,session,i,s.exercises):"")+'</article>';
 }).join("")+(editable?'<div class="row"><select aria-label="'+esc(t("add"))+'" data-add="'+session+'">'+M.eligibleExercises(i).filter(x=>!s.exercises.some(e=>e.id===x.id)).map(x=>option(x.id,label(x),"")).join("")+'</select>'+icon("plus",t("add"),"add",{session})+'</div>':"")).join("")+
 '<p class="small">'+t("start_principle")+'</p><p class="small">'+t("progressRule")+'</p><p class="small">'+t("effort")+'</p>'+
 (p.temporary?'<p class="notice">'+esc(t("replace")+": "+p.temporary.weeks+" "+(lang==="nl"?"weken":lang==="de"?"Wochen":"weeks")+" / "+p.temporary.reason)+'</p>':"");
}
function nutrition(p,i,editable){
 const tt=p.totals;
 return '<p class="measure"><strong>'+tt.kcal+' kcal</strong> / '+t("protein")+' '+tt.protein+' g / '+t("carbs")+' '+tt.carbs+' g / '+t("fat")+' '+tt.fat+' g</p><p class="small">'+t("portions")+' / EUR '+tt.cost.toFixed(2)+' / '+t("budget")+': EUR '+p.budgetCap+'</p>'+
 p.meals.map((m,n)=>{
 const meal=C.recipes.find(x=>x.id===m.id);
 return '<article class="meal-row"><h3>'+m.at+':00 / '+esc(meal?label(meal):t("foodAlt"))+'</h3>'+
 m.items.map((x,j)=>'<div><p>'+esc(label(C.foods.find(f=>f.id===x.food)))+' '+x.g+' g</p>'+
 (editable?'<div class="row"><select aria-label="'+esc(t("foodAlt"))+'" data-food="'+n+':'+j+'">'+C.foods.filter(f=>M.foodAllowed(f.id,i)).map(f=>option(f.id,label(f),x.food)).join("")+'</select>'+btn(t("replace"),"food",{meal:n,index:j})+'</div>':"")+'</div>').join("")+
 (editable?'<div class="row"><select aria-label="'+esc(t("mealAlt"))+'" data-meal="'+n+'">'+M.eligibleMeals(i).map(x=>option(x.id,label(x),m.id)).join("")+'</select>'+btn(t("mealAlt"),"meal",{index:n})+'</div>':"")+'</article>';
 }).join("");
}
function recovery(p,i,editable){
 return '<p>'+t("sleepGoal")+': <strong>'+p.sleepGoal+' h</strong> / '+t("sleep")+': '+p.baselineSleep+' h</p>'+
 (editable?'<div class="row"><select id="sleep-edit" aria-label="'+esc(t("sleepGoal"))+'">'+[7,8,9].map(x=>option(x,x+" h",p.sleepGoal)).join("")+'</select>'+btn(t("replace"),"sleep")+'</div>':"")+
 '<p>'+t("restDays")+': '+p.restDays.map(t).join(", ")+'</p><p>'+t("days")+': '+p.schedule.map(t).join(", ")+'</p><p>'+t("checkins")+': '+t(p.checkins)+'</p><p>'+t("secondary")+': '+p.secondary.map(t).join(", ")+'</p><p class="small">'+t("secondaryNote")+'</p>'+
 '<p>'+t("lightWeek")+': '+t(p.lightWeek.active?"yes":"no")+'</p>'+
 (editable?btn(t("lightWeek"),"edit",{kind:"light_week"}):"")+
 (p.windDown?'<p>'+t("time")+': '+p.windDown+'</p>':"");
}
function component(plan,i,editable){
 if(!plan)return '<p class="empty">'+t("noActive")+'</p>';
 return tab==="training"?training(plan.training,i,editable):tab==="nutrition"?nutrition(plan.nutrition,i,editable):recovery(plan.recovery,i,editable);
}
function warningMessages(s){
 const keys=[];
 if(s.contextFixtures.some(x=>["current","serious","recurring","unclassified"].includes(x)))keys.push("warning_health");
 if(s.contextFixtures.includes("self_reported"))keys.push("warning_recovered");
 if(s.contextFixtures.some(x=>["misunderstanding","missing","expired_context"].includes(x)))keys.push("warning_unclear");
 if(s.contextFixtures.includes("technical"))keys.push("warning_technical");
 return keys.map(k=>'<p class="notice" data-warning="'+k+'">'+t(k)+'</p>').join("");
}
function diffTable(before,after){
 const rows=M.differences(before,after);
 return '<table class="diff"><thead><tr><th>'+t("changes")+'</th><th>'+t("currentPlan")+'</th><th>'+t("proposalPlan")+'</th></tr></thead><tbody>'+rows.map(x=>'<tr><td><code>'+esc(x.path)+'</code></td><td>'+esc(typeof x.before==="object"?JSON.stringify(x.before):x.before)+'</td><td>'+esc(typeof x.after==="object"?JSON.stringify(x.after):x.after)+'</td></tr>').join("")+'</tbody></table>';
}
function independent(){
 const s=b.view(),editable=!!s.draft&&["member_pending","confirmed"].includes(s.status),p=s.draft?.plan;
 return '<h1>'+t("routeB")+'</h1><p class="status" id="status">'+t(s.status==="intake"?"intakeStep":s.status)+'</p>'+
 '<ol class="timeline">'+["intakeStep","reviewStep","confirmStep","applyStep"].map((k,n)=>'<li class="'+((s.status==="intake"?0:s.status==="member_pending"?1:s.status==="confirmed"?2:3)===n?"active":"")+'">'+(n+1)+'. '+t(k)+'</li>').join("")+'</ol>'+
 (form?intake():btn(t("editIntake"),"intake-form"))+
 ((p||s.active)?'<section><div class="tabs">'+["training","nutrition","recovery"].map(x=>'<button type="button" data-tab="'+x+'" aria-pressed="'+(tab===x)+'">'+t(x==="recovery"?"recoveryPlan":x)+'</button>').join("")+'</div><div class="pair"><div class="old"><h2>'+t("currentPlan")+' '+s.revision+'</h2>'+component(s.active?.plan,s.active?.intake,false)+'</div><div><h2>'+t(s.status==="applied"?"reviewedPlan":"proposalPlan")+'</h2>'+component(p,s.intake,editable)+'</div></div>'+
 (p?details(t("changes"),diffTable(s.active?.plan[tab]??null,p[tab])):"")+
 '<div class="actions">'+btn(t("confirm"),"confirm",{},"primary",s.status!=="member_pending")+btn(t("apply"),"apply",{},"primary",s.status!=="confirmed")+btn(t("reject"),"reject",{},"",!editable)+btn(t("reopen"),"reopen",{},"",!["rejected","applied"].includes(s.status))+'</div>'+
 details(t("sourceTrace"),pre({intake:s.draft?.intake||s.intake,intakeVersion:s.intakeVersion,refs:s.draft?.refs,policy:C.policy}))+ '</section>':"")+
 '<section><h2>'+t("proactive")+'</h2><div class="row"><select id="signal-select" aria-label="'+esc(t("signal"))+'">'+Object.keys(C.signals).map(x=>option(x,t("signal_"+x),s.signal?.id||"sleep")).join("")+'</select>'+btn(t("simulate"),"signal",{},"",!s.active)+'</div>'+
 (s.signal?.id&&C.signals[s.signal.id]?'<dl class="signal-data"><dt>'+t("signal")+'</dt><dd>'+t("signal_"+s.signal.id)+'</dd><dt>'+t("window")+'</dt><dd>'+esc(s.signal.window)+'</dd><dt>'+t("data")+'</dt><dd>'+esc(JSON.stringify(s.signal.values))+'</dd><dt>'+t("proposalPlan")+'</dt><dd>'+t("why_"+s.signal.id)+'</dd><dt>'+t("unchanged")+'</dt><dd>'+s.signal.unchanged.map(x=>t(x==="recovery"?"recoveryPlan":x)).join(", ")+'</dd><dt>'+t("confirmStep")+'</dt><dd>'+t(s.signal.confirmation==="none"?"facts":"confirm")+(s.signal.confirmation==="none"?"":" + "+t("apply"))+'</dd></dl>':"")+'</section>'+
 '<section><h2>'+t("photo")+'</h2><img class="photo-pair" src="../coach-review-demo/photo-concept.svg" alt="'+esc(t("before")+" / "+t("after"))+'"><div class="photos"><p>A / '+t("before")+'</p><p>B / '+t("after")+'</p></div><p>'+t("photoNote")+'</p>'+btn(t("photoAction"),"photo",{corroborated:true},"",!s.active)+
 (s.signal?.id==="photo"?pre(s.signal):"")+'</section>'+
 '<section><h2>'+t("safety")+'</h2><div class="row"><select id="safety-select" aria-label="'+esc(t("safety"))+'">'+["current","serious","recurring","unclassified","self_reported","missing","expired_context","misunderstanding","technical","consent_revoked","version_conflict","expired"].map(x=>option(x,t(x),"current")).join("")+'</select>'+btn(t("simulate"),"safety")+'</div>'+warningMessages(s)+'<p>'+t("safetyNote")+'</p><p>'+s.contextFixtures.map(t).join(", ")+'</p>'+(s.contextFixtures.some(x=>["misunderstanding","technical"].includes(x))?'<p>'+t("optionalClarify")+'</p>'+btn(t("clarify"),"clarify",{source:"syn-new-clear-context@1"}):"")+'</section>'+
 '<section><h2>'+t("history")+'</h2>'+s.history.map(v=>'<div class="history-row"><strong>v'+v.version+'</strong><span>'+esc(JSON.stringify(v.componentVersions))+'</span>'+btn(t("restore"),"restore",{version:v.version},"",v.version===s.revision)+'</div>'+details(t("saved")+" v"+v.version,pre(v))).join("")+'</section>'+
 '<section><h2>'+t("inbox")+'</h2>'+s.notifications.map(n=>'<p>'+t(({proposal:"proposal",confirmed:"confirmed_notice",applied:"applied_notice",restore:"restore_notice",rejected:"rejected_notice"})[n.key])+'</p>').join("")+'</section>'+
 '<section><h2>'+t("audit")+'</h2>'+s.audit.map(x=>'<div class="audit-row"><time>'+new Date(x.at).toISOString()+'</time><div>'+esc(x.action)+' / '+t(x.status)+' / v'+x.base+' → v'+x.version+'</div>'+details(t("sourceTrace"),pre(x))+'</div>').join("")+'</section>';
}
function human(){
 const s=a.view(),p=s.proposal;
 const setTable=es=>'<table><thead><tr><th>'+ta("set")+'</th><th>'+ta("weight")+'</th><th>'+ta("reps")+'</th><th>RIR / RPE</th></tr></thead><tbody>'+es.map(x=>'<tr><td>'+x.index+'</td><td>'+x.load.value+' '+x.load.unit+'</td><td>'+x.reps.min+' - '+x.reps.max+'</td><td>'+esc(x.rir??"—")+' / '+esc(x.rpe??"—")+'</td></tr>').join("")+'</tbody></table>';
 const renderPlan=plan=>plan.options.map(o=>o.exercises.map(e=>'<h3>'+esc(FMZDemoData.seeds[scenario].catalog.find(x=>x.id===e.exercise_id)?.labels[lang]||e.exercise_id)+'</h3>'+setTable(e.sets)).join("")).join("");
 return '<h1>'+t("routeA")+'</h1><p>'+ta("fiction")+'</p><label>'+ta("scenario")+'<select id="scenario">'+Object.keys(FMZDemoData.seeds).map(x=>option(x,ta(x),scenario)).join("")+'</select></label><p id="status" class="status">'+ta(p.status)+'</p>'+
 '<ol class="timeline">'+["review","member","approval","application"].map(k=>'<li>'+ta(k)+'</li>').join("")+'</ol>'+
 '<section><div class="pair"><div><h2>'+ta("plan")+' v'+s.active.revision+'</h2>'+renderPlan(s.active)+'</div><div><h2>'+ta("proposed")+'</h2>'+renderPlan(p.target)+'</div></div>'+details(t("changes"),diffTable(s.active,p.target))+
 '<div class="actions">'+btn(ta("accept"),"a",{action:"member_accept",role:"member"},"primary",p.status!=="member_pending")+btn(ta("reject")+" / "+ta("member"),"a",{action:"member_reject",role:"member"},"",p.status!=="member_pending")+
 btn(ta("approve")+" / "+ta("trainer"),"a",{action:"trainer_approve",role:"trainer"},"primary",p.status!=="trainer_pending")+btn(ta("reject")+" / "+ta("trainer"),"a",{action:"trainer_reject",role:"trainer"},"",p.status!=="trainer_pending")+btn(ta("block")+" / "+ta("trainer"),"a",{action:"trainer_block",role:"trainer"},"",p.status!=="trainer_pending")+btn(ta("apply"),"a",{action:"apply",role:"trainer"},"primary",p.status!=="approved")+'</div>'+
 '<p>'+ta("reason")+': '+ta(p.reason)+'</p>'+details(ta("actual"),pre(p.rows))+
 (FMZDemoData.seeds[scenario].w2.length?'<h3>W2</h3><p>'+ta("weight_step_conflict")+'</p>'+pre(FMZDemoData.seeds[scenario].w2):"")+
 details(ta("sources"),pre(p.refs))+'</section>'+
 '<section><h2>'+ta("simulate")+'</h2><select id="a-inject">'+["version_conflict","expired","no_trainer","consent_revoked","relation_revoked","incomplete","unavailable"].map(x=>option(x,ta(x),"version_conflict")).join("")+'</select>'+btn(ta("trigger"),"a-inject")+'</section>'+
 '<section><h2>'+ta("history")+'</h2>'+s.history.map(v=>'<div class="history-row"><strong>v'+v.revision+'</strong>'+btn(ta("restore"),"a",{action:"restore",role:"member",version:v.revision},"",p.status!=="applied"||v.revision===s.active.revision)+'</div>').join("")+'<p>'+ta("restoreWarning")+'</p></section>'+
 '<section><h2>'+ta("inbox")+'</h2>'+s.notifications.map(n=>'<p>'+ta(n.key)+' '+(n.reason?ta(n.reason):"")+'</p>').join("")+'</section>'+
 '<section><h2>'+ta("audit")+'</h2>'+s.audit.map(x=>'<div class="audit-row"><time>'+new Date(x.at).toISOString()+'</time><p>'+ta(x.action)+' / '+ta(x.status)+'</p>'+details(ta("sources"),pre(x))+'</div>').join("")+'</section>';
}

return ctx.state.route==="A"?human():independent();
};
