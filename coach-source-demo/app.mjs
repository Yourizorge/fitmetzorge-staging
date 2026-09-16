import {copy} from "./strings.mjs";
const BASE="https://mokxyyullfhkfalopbzd.supabase.co",KEY="sb_publishable_6OiMLMl946arkI71-ylqkQ_EQWL6kKT";
const STORE="fmz6e10-session",aliases=["zorgeyouri+6e9-a-lid@gmail.com","zorgeyouri+6e9-a-trainer@gmail.com","zorgeyouri+6e9-b-lid@gmail.com"];
const root=document.querySelector("#root"),params=new URLSearchParams(location.search);
let lang=copy[params.get("lang")]?params.get("lang"):"nl",theme=["light","dark","system"].includes(params.get("theme"))?params.get("theme"):"system";
let session=null,home=null,view=null,selected=null,busy=false,feedback="",pending=null,draft=null,draftOpen=false,management=false,validity=null;
try{session=JSON.parse(sessionStorage.getItem(STORE));}catch{}
const t=k=>copy[lang][k]||k,esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const $=s=>document.querySelector(s),clone=x=>structuredClone(x);
const options=(arr,v)=>arr.map(x=>'<option value="'+esc(x)+'" '+(x===v?"selected":"")+'>'+esc(t(x))+'</option>').join("");
const dt=x=>new Date(x).toLocaleString(lang==="nl"?"nl-NL":lang==="de"?"de-DE":"en-GB",{timeZone:"Europe/Amsterdam",dateStyle:"medium",timeStyle:"short"})+" (Europe/Amsterdam)";
const local=x=>{const d=new Date(x);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,19);};
const button=(action,label,disabled=false,extra="")=>'<button type="button" data-action="'+action+'" '+extra+' '+(disabled||busy?"disabled":"")+'>'+esc(t(label))+'</button>';
const state=s=>'<span class="status '+esc(s)+'">'+esc(t(s))+'</span>';
function save(){if(session)sessionStorage.setItem(STORE,JSON.stringify(session));else sessionStorage.removeItem(STORE);}
async function auth(path,data,token){
 const r=await fetch(BASE+"/auth/v1/"+path,{method:"POST",headers:{apikey:KEY,"Content-Type":"application/json",...(token?{Authorization:"Bearer "+token}:{})},body:JSON.stringify(data),signal:AbortSignal.timeout(15000)});
 if(!r.ok)throw Error("authentication_required");return r.status===204?null:r.json();
}
async function token(){
 if(!session)throw Error("authentication_required");
 if(session.expires_at*1000<Date.now()+30000){session=await auth("token?grant_type=refresh_token",{refresh_token:session.refresh_token});save();}
 return session.access_token;
}
async function rpc(p){
 const a=await token();
 let r;
 try{r=await fetch(BASE+"/functions/v1/fmz6e10-synthetic",{method:"POST",headers:{Authorization:"Bearer "+a,"Content-Type":"application/json"},body:JSON.stringify(p),signal:AbortSignal.timeout(45000)});}
 catch{throw Error("network");}
 let d;
 try{d=await r.json();}catch{throw Error("network");}
 if(!r.ok){
  if(r.status>=500||r.status===429)throw Error("network");
  const e=Error(d.error||"synthetic_operation_denied");e.denied=true;throw e;
 }return d;
}
async function reload(){
 const previous=view?.workspace;
 home=await rpc({op:"home"});
 const ws=home.workspaces.find(w=>w.window===selected)||home.workspaces[0];
 selected=ws?.window||selected;
 view=ws?await rpc({op:"read",window:ws.window,workspace:ws.workspace}):null;
 if(previous!==view?.workspace){draftOpen=false;resetDraft();}
 else if(view&&!draft)resetDraft();
}
function resetDraft(){
 const source=view?.sources.at(-1);
 draft=view?.role==="a_trainer"?clone(source?.body||view.source_template):null;
 validity=view?{from:local(view.window.starts_at),until:local(view.window.ends_at)}:null;
 if(draft)draft.note=draft.note||"";
}
async function run(fn){
 if(busy)return;busy=true;feedback=t("busy");render();
 try{await fn();feedback=t("success");}catch(e){
  if(e.message==="authentication_required"){session=null;home=view=null;save();feedback=t("signin");}
  else feedback=e.message==="network"?t("network"):t("error")+" ["+e.message+"]";
 }finally{busy=false;render();}
}
async function command(action,data={},workspace=view?.workspace,window=selected,expected=null){
 if(pending)throw Error("pending_request_retry_required");
 const w=home?.windows.find(w=>w.id===window);
 const p={op:"command",window:window||null,workspace:workspace||null,key:crypto.randomUUID(),expected:expected??w?.revision??0,action,data};
 pending=p;await sendPending();
}
async function sendPending(){
 try{
  const sent=pending,receipt=await rpc(sent);pending=null;
  if(sent.workspace&&view?.workspace===sent.workspace){
   view=await rpc({op:"read",window:sent.window,workspace:sent.workspace});
   const w=home.windows.find(w=>w.id===sent.window);if(w)w.revision=view.window.revision;
  }else await reload();
 }
 catch(e){if(e.denied)pending=null;throw e;}
}
function setList(sets,unit,changed=null){
 if(!sets)return t("blocked");
 return '<ol class="sets">'+sets.map((s,i)=>'<li><span>'+s.index+'</span> <strong class="'+(changed&&JSON.stringify(s)!==JSON.stringify(changed[i])?"changed":"")+'">'+esc(s.load)+" "+esc(unit)+" × "+esc(s.reps)+'</strong><small>RIR '+(s.rir??"—")+' · RPE '+(s.rpe??"—")+'</small></li>').join("")+'</ol>';
}
function rowReason(row){
 if(row.reason?.startsWith("W2"))return t("W2")+" "+t("step")+": "+row.weight_step+" "+row.unit+". "+t("attempt")+": "+row.attempted_load+" "+row.unit+". "+t("available")+": "+row.available_weights.join(", ")+". "+t("nochange");
 if(row.reason?.startsWith("W1"))return t("W1");
 return t(["reps","weight","hold"].includes(row.kind)?row.kind:"missing");
}
function sourceMarkup(s){
 return '<article class="source"><div class="heading"><h3>'+t("source")+" v"+s.version+'</h3>'+state(s.status)+'</div><p class="hash">'+esc(s.hash)+'</p><p>'+esc(s.body.note)+'</p><small>'+dt(s.valid_from)+" — "+dt(s.valid_until)+'</small><details><summary>'+t("rules")+'</summary>'+
 s.body.rules.map(r=>'<p><strong>'+esc(r.selector.id)+'</strong> · '+r.reps_min+"–"+r.reps_max+" reps · "+t("step")+" "+r.weight_step+" "+r.unit+" · "+r.sets_min+"–"+r.sets_max+" sets"+'<br><small>RIR '+t(r.rir.required?"required":"optional")+": "+r.rir.min+"–"+r.rir.max+" · RPE "+t(r.rpe.required?"required":"optional")+": "+r.rpe.min+"–"+r.rpe.max+'</small></p>').join("")+'</details>'+
 '<details><summary>'+t("binding")+'</summary><dl class="bindings"><dt>'+t("source")+' ID</dt><dd>'+esc(s.source_id)+'</dd><dt>Trainer</dt><dd>'+esc(s.trainer_id)+'</dd><dt>Workspace</dt><dd>'+esc(s.workspace_id)+'</dd><dt>'+t("goal")+'</dt><dd>'+esc(s.body.goal_ref)+'</dd></dl></details></article>';
}
function proposalMarkup(p){
 const member=view.role==="a_member",trainer=view.role==="a_trainer";
 const attrs='data-id="'+p.id+'" data-version="'+p.version+'"';
 const allowed= !p.stale;
 const rows=(p.reflection.rows||[]).map(r=>{
 const observed=view.observations?.at(-1)?.exercises.find(e=>e.id===r.exercise)?.sets;
 return '<article class="exercise"><h4>'+esc(r.exercise)+'</h4><div class="comparison"><div><h5>'+t("base")+'</h5>'+setList(r.current,r.unit)+'</div><div><h5>'+t("observed")+'</h5>'+setList(observed,r.unit)+'</div><div><h5>'+t("next")+'</h5>'+setList(r.next,r.unit,r.current)+'</div></div><p>'+esc(rowReason(r))+'</p></article>';
 }).join("");
 return '<article class="proposal"><div class="heading"><h3>'+t("version")+" "+p.version+' · '+t("source")+" v"+p.source_version+'</h3>'+state(p.status)+'</div>'+
 (p.stale&&p.status!=="applied"?'<p class="warning">'+t("stale")+'</p>':"")+
 '<p class="hash">'+esc(p.source_hash)+'</p>'+
 (p.restored_from?'<p>'+t("restored")+" "+p.restored_from.plan_version+" · "+t("original")+": "+esc(p.restored_from.original_source_ref?.version??t("noSource"))+'</p>':"")+
 (rows||'<p>'+t(p.reflection.allowed?"consent":"missing")+'</p>')+
 '<div class="actions">'+(member?button("member_accept","member_accept",!allowed||p.status!=="member_pending",attrs)+button("member_reject","member_reject",p.status!=="member_pending",attrs):"")+
 (trainer?button("trainer_approve","trainer_approve",!allowed||p.status!=="member_accepted",attrs)+button("trainer_reject","trainer_reject",p.status!=="member_accepted",attrs)+button("trainer_block","trainer_block",p.status!=="member_accepted",attrs)+button("apply","apply",!allowed||p.status!=="approved",attrs):"")+
 '</div></article>';
}
function numeric(label,field,value,index,min,max,step="1"){
 return '<label>'+esc(t(label))+'<input data-rule="'+index+'" data-field="'+field+'" type="number" value="'+esc(value)+'" min="'+min+'" max="'+max+'" step="'+step+'" '+(field==="priority"?"":"required")+'></label>';
}
function editor(){
 if(!draft||!draftOpen)return "";
 return '<form id="source-form"><div class="heading"><h3>'+t("newsource")+'</h3>'+button("close-editor","close")+'</div><div class="form-grid">'+
 '<label>'+t("note")+'<input name="note" maxlength="160" value="'+esc(draft.note)+'" required></label>'+
 '<label>'+t("minSessions")+'<input name="minimum_sessions" type="number" min="1" max="10" value="'+draft.minimum_sessions+'" required></label>'+
 '<label>'+t("comparable")+'<input name="comparable_plan_versions" value="'+esc(draft.comparable_plan_versions.join(", "))+'" required></label>'+
 '<label>'+t("validfrom")+'<input name="valid_from" type="datetime-local" step="1" value="'+esc(validity.from)+'" required></label>'+
 '<label>'+t("validuntil")+'<input name="valid_until" type="datetime-local" step="1" value="'+esc(validity.until)+'" required></label></div>'+
 draft.rules.map((r,i)=>'<fieldset><legend>'+esc(r.id)+'</legend><div class="form-grid">'+
 '<label>'+t("selector")+'<select data-rule="'+i+'" data-field="selector.kind">'+options(["exercise","type"],r.selector.kind)+'</select></label>'+
 '<label>'+t("exercise")+'<select data-rule="'+i+'" data-field="selector.id">'+options(r.selector.kind==="exercise"?["syn-squat","syn-press","syn-row"]:["syn-lower","syn-push","syn-pull"],r.selector.id)+'</select></label>'+
 '<label>'+t("unit")+'<select data-rule="'+i+'" data-field="unit">'+options(["kg","lb"],r.unit)+'</select></label>'+
 numeric("minreps","reps_min",r.reps_min,i,1,50)+numeric("maxreps","reps_max",r.reps_max,i,1,50)+numeric("repstep","reps_step",r.reps_step,i,1,10)+numeric("resetreps","reset_reps",r.reset_reps,i,1,50)+numeric("weightstep","weight_step",r.weight_step,i,0.000001,1000,"any")+
 '<label>'+t("weights")+'<input data-rule="'+i+'" data-field="available_weights" value="'+esc(r.available_weights.join(", "))+'" required></label>'+
 numeric("minsets","sets_min",r.sets_min,i,1,10)+numeric("maxsets","sets_max",r.sets_max,i,1,10)+numeric("priority","priority",r.priority,i,0,1000)+
 ["rir","rpe"].map(f=>'<div class="effort"><label class="check"><input type="checkbox" data-rule="'+i+'" data-field="'+f+'.required" '+(r[f].required?"checked":"")+'> '+f.toUpperCase()+" "+t("required")+'</label>'+numeric("min",f+".min",r[f].min,i,f==="rpe"?1:0,10,"any")+numeric("max",f+".max",r[f].max,i,f==="rpe"?1:0,10,"any")+'</div>').join("")+'</div></fieldset>').join("")+
 '<p>'+t("sourceHelp")+'</p><div class="actions">'+button("add-rule","addRule",draft.rules.length>=12)+'<button type="submit" '+(busy?"disabled":"")+'>'+t("append")+'</button></div></form>';
}
function windowMarkup(){
 if(!home?.operator)return "";
 return '<details id="management" '+(management?"open":"")+'><summary>'+t("manage")+'</summary><form id="prepare"><div class="form-grid"><label>'+t("scenario")+'<select name="scenario"><option>kg</option><option>lb</option></select></label><label>'+t("hours")+'<input name="hours" type="number" min="1" max="24" value="24" required></label></div><button type="submit" '+(busy?"disabled":"")+'>'+t("prepare")+'</button></form>'+
 home.windows.map(w=>'<article class="window"><div class="heading"><strong>'+esc(w.scenario)+" · "+esc(w.id.slice(0,8))+'</strong>'+state(w.status)+'</div><small>'+dt(w.starts_at)+" — "+dt(w.ends_at)+'</small><div class="actions">'+
 button("activate","activate",w.status!=="prepared",'data-window="'+w.id+'"')+
 button("revoke","revoke",["revoked","cleaned"].includes(w.status),'data-window="'+w.id+'"')+
 button("cleanup","cleanup",w.status==="active"||w.status==="cleaned",'data-window="'+w.id+'"')+
 '</div>'+(w.cleanup?'<small>Cleanup: '+w.cleanup.workspaces+' workspaces · '+w.cleanup.audit_count+' audit · '+w.cleanup.accounts_deleted+' accounts</small>':"")+'</article>').join("")+'</details>';
}
function render(){
 document.documentElement.lang=lang;
 document.documentElement.dataset.theme=theme==="system"?(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"):theme;
 const banner='<header><div class="brand"><img src="../assets/fit-met-zorge-logo-cropped.png" alt="FitMetZorge"><div><strong>FitMetZorge</strong><p>'+t("badge")+'</p></div></div><div class="preferences"><label>'+t("language")+'<select id="language">'+options(["nl","en","de"],lang)+'</select></label><label>'+t("theme")+'<select id="theme">'+options(["light","dark","system"],theme)+'</select></label></div></header><main><div class="heading"><h1>'+t("title")+'</h1>'+
 (session?'<div class="actions"><button type="button" data-action="refresh" title="'+t("refresh")+'" aria-label="'+t("refresh")+'" '+(busy?"disabled":"")+'><img class="refresh-icon" src="../assets/vendor/lucide-rotate-cw.svg" alt=""></button>'+button("logout","logout")+'</div>':"")+'</div><p class="notice">'+t("limit")+'</p><div id="feedback" role="status">'+esc(feedback)+(pending?button("retry","retry"):"")+'</div>';
 if(!session){root.innerHTML=banner+'<form id="login"><h2>'+t("login")+'</h2><p>'+t("signin")+'</p><label>'+t("email")+'<select name="email" autocomplete="username">'+aliases.map(x=>'<option>'+x+'</option>').join("")+'</select></label><label>'+t("password")+'<input type="password" name="password" autocomplete="current-password" required></label><button type="submit" '+(busy?"disabled":"")+'>'+t("login")+'</button></form></main>';bind();return;}
 let content=home?'<p id="identity">'+t(home.role)+'</p>'+windowMarkup():"";
 if(view){
  content+='<section class="window-band"><strong>'+t("window")+" "+view.window.id.slice(0,8)+'</strong><span>'+t("ends")+": "+dt(view.window.ends_at)+'</span></section>';
  if(view.route==="B")content+='<section id="route-content"><h2>Route B</h2><p>'+t("b")+'</p></section>';
  else content+='<div id="route-content"><section><div class="heading"><h2>'+t("sources")+'</h2>'+(view.role==="a_trainer"?'<div class="actions">'+button("new-source","newsource")+button("withdraw","withdraw",!["active","not_yet_valid","expired"].includes(view.sources.at(-1)?.status))+'</div>':"")+'</div>'+
   (view.sources.length?'<div class="sources">'+view.sources.map(sourceMarkup).join("")+'</div>':'<p>'+t("emptySource")+'</p>')+editor()+'</section>'+
   '<section><div class="heading"><h2>'+t("proposals")+'</h2>'+button("propose","propose")+'</div><p>'+t("consent")+'</p>'+
   (view.proposals.length?[...view.proposals].reverse().map(proposalMarkup).join(""):'<p>'+t("nothing")+'</p>')+'</section>'+
   '<section><h2>'+t("history")+' · v'+view.active_version+'</h2>'+[...view.plans].reverse().map(p=>'<details class="plan"><summary>v'+p.version+' · '+(p.source_ref?t("source")+" v"+p.source_ref.version:t("noSource"))+'</summary><p class="hash">'+esc(p.hash)+'</p>'+
   p.content.exercises.map(e=>'<h4>'+esc(e.id)+'</h4>'+setList(e.sets,e.unit)).join("")+
   (p.restored_from?'<p>'+t("original")+": v"+p.restored_from.plan_version+'</p>':"")+
   (view.role==="a_member"?button("restore","restore",p.version===view.active_version,'data-plan="'+p.version+'"'):"")+'</details>').join("")+'</section>'+
   '<section><h2>'+t("audit")+'</h2><ol class="audit">'+[...view.audit].reverse().map(a=>'<li><time>'+dt(a.at)+'</time><strong>'+esc(t(a.action))+'</strong><small>'+t("source")+" "+(a.receipt.source_version??"—")+" · r"+a.receipt.revision+'</small></li>').join("")+'</ol></section></div>';
 }else content+='<p class="notice">'+t("inactive")+'</p>';
 root.innerHTML=banner+content+'</main>';bind();
}
function capture(){
 const form=$("#source-form");if(!form||!draft)return;
 draft.note=form.elements.note.value;draft.minimum_sessions=Number(form.elements.minimum_sessions.value);
 draft.comparable_plan_versions=form.elements.comparable_plan_versions.value.split(",").map(x=>Number(x.trim()));
 validity={from:form.elements.valid_from.value,until:form.elements.valid_until.value};
}
function bind(){
 $("#language").onchange=e=>{capture();lang=e.target.value;render();};
 $("#theme").onchange=e=>{capture();theme=e.target.value;render();};
 const mg=$("#management");if(mg)mg.ontoggle=()=>management=mg.open;
 $("#login")?.addEventListener("submit",e=>{
 e.preventDefault();const email=e.target.elements.email.value,password=e.target.elements.password.value;
 if(!aliases.includes(email))return;
 run(async()=>{session=await auth("token?grant_type=password",{email,password});save();await reload();});
 });
 $("#prepare")?.addEventListener("submit",e=>{
 e.preventDefault();const scenario=e.target.elements.scenario.value,hours=Number(e.target.elements.hours.value),now=Date.now();
 run(()=>command("prepare",{scenario,starts_at:new Date(now).toISOString(),ends_at:new Date(now+hours*3600000-5000).toISOString()},null,null,0));
 });
 $("#source-form")?.addEventListener("submit",e=>{
 e.preventDefault();capture();
 const data={body:clone(draft),valid_from:new Date(e.target.elements.valid_from.value).toISOString(),valid_until:new Date(e.target.elements.valid_until.value).toISOString()};
 run(async()=>{await command("source_append",data);draftOpen=false;resetDraft();});
 });
 document.querySelectorAll("[data-rule]").forEach(input=>input.addEventListener("change",()=>{
 const r=draft.rules[Number(input.dataset.rule)],keys=input.dataset.field.split("."),k=keys.at(-1),target=keys.length>1?r[keys[0]]:r;
 target[k]=input.type==="checkbox"?input.checked:input.type==="number"?(input.value===""?null:Number(input.value)):k==="available_weights"?input.value.split(",").map(x=>Number(x.trim())):input.value;
 if(input.dataset.field==="selector.kind"){r.selector.id=input.value==="exercise"?"syn-squat":"syn-lower";capture();render();}
 }));
 document.querySelectorAll("[data-action]").forEach(b=>b.onclick=()=>{
 const a=b.dataset.action;capture();
 if(a==="new-source"){resetDraft();draftOpen=true;render();return;}
 if(a==="close-editor"){draftOpen=false;render();return;}
 if(a==="add-rule"){const r=clone(draft.rules[0]);r.id="syn-type-"+(draft.rules.length+1);r.selector={kind:"type",id:"syn-lower"};draft.rules.push(r);render();return;}
 run(async()=>{
 if(a==="logout"){try{await auth("logout?scope=local",{},session.access_token);}finally{session=home=view=draft=null;pending=null;selected=null;save();}return;}
 if(a==="refresh"){await reload();return;}
 if(a==="retry"){await sendPending();return;}
 if(["activate","revoke","cleanup"].includes(a)){await command(a,{},null,b.dataset.window);return;}
 if(a==="withdraw"){await command("source_withdraw",{source_version:view.sources.at(-1).version});return;}
 if(a==="propose"){await command("propose");return;}
 if(a==="restore"){await command("restore",{plan_version:Number(b.dataset.plan)});return;}
 await command(a,{proposal:b.dataset.id,proposal_version:Number(b.dataset.version)});
 });
 });
}
render();
if(session)run(reload);
setInterval(()=>{
 if(view&&Date.now()>=new Date(view.window.ends_at).getTime()){view=null;feedback=t("inactive");render();}
},1000);
document.addEventListener("visibilitychange",()=>{if(!document.hidden&&session&&!busy&&!draftOpen)run(reload);});
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",()=>{if(theme==="system"){capture();render();}});
