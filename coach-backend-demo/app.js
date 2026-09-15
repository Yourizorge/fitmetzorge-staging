(function(){"use strict";
const cfg=window.FMZ_CONFIG,base="https://mokxyyullfhkfalopbzd.supabase.co",root=document.getElementById("root"),STORE="fmz6e9.synthetic.session.v1";
if(cfg?.SUPABASE_URL!==base)throw Error("staging_only");
const params=new URLSearchParams(location.search),media=matchMedia("(prefers-color-scheme: dark)");
let lang=["nl","en","de"].includes(params.get("lang"))?params.get("lang"):"nl",theme=["light","dark","system"].includes(params.get("theme"))?params.get("theme"):"system";
let auth=null,state=null,busy=false,feedback="",pending=null,pendingIntake=null,form=true,tab="training",homes=[];
const text={
nl:{title:"Youri Coach | Backenddemo",demo:"Synthetische stagingdemo. Geen echte ledengegevens. Alleen tijdelijke testaccounts; testplannen blijven bij verversen behouden.",email:"Testaccount",password:"Wachtwoord",login:"Inloggen",logout:"Uitloggen",language:"Taal",theme:"Thema",light:"Licht",dark:"Donker",system:"Systeem",loading:"Bezig...",error:"De handeling is niet verwerkt. Controleer de verbinding of laad de actuele versie.",denied:"Geen toegang of de synthetische testomgeving staat uit.",conflict:"De bron of versie is gewijzigd. Laad de actuele versie; eerdere goedkeuringen worden niet overgenomen.",retry:"Opnieuw proberen",refresh:"Actuele versie laden",open:"Voorstel bekijken",member:"Lid",trainer:"Trainer",saved:"Verwerkt door de synthetische backend.",audit:"Serveraudit",notices:"Meldingen",source:"Bronversies",guard:"Context",new:"Youri heeft een voorstel voor je volgende training.",member_pending:"Youri heeft een voorstel voor je volgende training.",trainer_pending:"Er wacht een trainingsvoorstel op jouw beoordeling.",approved:"Het voorstel is goedgekeurd en wacht op toepassing.",ready:"Het voorstel is goedgekeurd en wacht op toepassing.",applied:"Je trainingsschema heeft een nieuwe versie.",restore:"Er is een voorstel gemaakt om een eerdere schemaversie te herstellen.",rejected:"Het voorstel is afgewezen.",blocked:"Het voorstel is geblokkeerd."},
en:{title:"Youri Coach | Backend demo",demo:"Synthetic staging demo. No real member data. Temporary test accounts only; test plans survive refresh.",email:"Test account",password:"Password",login:"Sign in",logout:"Sign out",language:"Language",theme:"Theme",light:"Light",dark:"Dark",system:"System",loading:"Working...",error:"The action was not processed. Check your connection or load the current version.",denied:"Access denied or the synthetic environment is disabled.",conflict:"The source or version changed. Load the current version; previous approvals are not reused.",retry:"Retry",refresh:"Load current version",open:"View proposal",member:"Member",trainer:"Trainer",saved:"Processed by the synthetic backend.",audit:"Server audit",notices:"Notifications",source:"Source versions",guard:"Context",new:"Youri has a proposal for your next workout.",member_pending:"Youri has a proposal for your next workout.",trainer_pending:"A training proposal is waiting for your review.",approved:"The proposal is approved and awaiting application.",ready:"The proposal is approved and awaiting application.",applied:"Your training plan has a new version.",restore:"A proposal to restore an earlier plan version has been created.",rejected:"The proposal was rejected.",blocked:"The proposal was blocked."},
de:{title:"Youri Coach | Backend-Demo",demo:"Synthetische Staging-Demo. Keine echten Mitgliedsdaten. Nur temporaere Testkonten; Testplaene bleiben beim Neuladen erhalten.",email:"Testkonto",password:"Passwort",login:"Anmelden",logout:"Abmelden",language:"Sprache",theme:"Darstellung",light:"Hell",dark:"Dunkel",system:"System",loading:"Wird verarbeitet...",error:"Die Aktion wurde nicht verarbeitet. Verbindung pruefen oder aktuelle Version laden.",denied:"Kein Zugriff oder die synthetische Testumgebung ist deaktiviert.",conflict:"Quelle oder Version geaendert. Aktuelle Version laden; alte Freigaben werden nicht uebernommen.",retry:"Erneut versuchen",refresh:"Aktuelle Version laden",open:"Vorschlag ansehen",member:"Mitglied",trainer:"Trainer",saved:"Vom synthetischen Backend verarbeitet.",audit:"Serverprotokoll",notices:"Mitteilungen",source:"Quellversionen",guard:"Kontext",new:"Youri hat einen Vorschlag fuer dein naechstes Training.",member_pending:"Youri hat einen Vorschlag fuer dein naechstes Training.",trainer_pending:"Ein Trainingsvorschlag wartet auf deine Pruefung.",approved:"Der Vorschlag ist genehmigt und wartet auf die Anwendung.",ready:"Der Vorschlag ist genehmigt und wartet auf die Anwendung.",applied:"Dein Trainingsplan hat eine neue Version.",restore:"Ein Vorschlag zur Wiederherstellung einer frueheren Planversion wurde erstellt.",rejected:"Der Vorschlag wurde abgelehnt.",blocked:"Der Vorschlag wurde blockiert."}
};
const t=k=>text[lang][k]||k,esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const btn=(k,action)=>'<button type="button" data-command="'+action+'">'+esc(t(k))+'</button>';
const select=(id,values,value)=>'<select id="'+id+'">'+values.map(v=>'<option value="'+v+'"'+(value===v?' selected':'')+'>'+esc(id==="lang"?v.toUpperCase():t(v))+'</option>').join("")+'</select>';
function render(){
 document.documentElement.lang=lang;document.documentElement.dataset.theme=theme==="system"?(media.matches?"dark":"light"):theme;
 root.innerHTML='<header class="backend-bar"><img src="../training-review-demo/brand.png" alt="FitMetZorge"><strong>'+t("title")+'</strong><label>'+t("language")+select("lang",["nl","en","de"],lang)+'</label><label>'+t("theme")+select("theme",["light","dark","system"],theme)+'</label>'+(auth?btn("logout","logout"):"")+'</header><div class="banner">'+t("demo")+'</div><main><p id="feedback" role="status" aria-live="polite">'+esc(busy?t("loading"):feedback)+'</p>'+
 (!auth?'<form id="login" class="login"><h1>'+t("login")+'</h1><label>'+t("email")+'<input name="email" type="email" autocomplete="username" required></label><label>'+t("password")+'<input name="password" type="password" autocomplete="current-password" required></label><button type="submit">'+t("login")+'</button></form>':
 '<div class="actions">'+btn("refresh","refresh")+(pending?btn("retry","retry"):"")+'</div>'+
 (state?'<div class="backend-state"><strong>Route '+state.route+' / '+t(state.actor_role)+'</strong><span>v'+state.version+' / r'+state.revision+'</span></div>'+
 (state.route==="A"&&state.revision===0&&state.actor_role==="member"?btn("open","open"):"")+
 '<div id="route-content">'+FMZ9Render({lang,tab,form,pendingIntake,scenario:state.seed||"normal",state})+'</div>'+
 '<section><h2>'+t("guard")+'</h2><p>'+esc(state.guard)+'</p>'+warning()+'</section>'+
 '<section><h2>'+t("notices")+'</h2><ul class="notice-list">'+state.notices.map(n=>'<li>'+esc(t(n.code))+'</li>').join("")+'</ul></section>'+
 '<details><summary>'+t("source")+'</summary><pre>'+esc(JSON.stringify(state.basis,null,2))+'</pre></details>':""))+'</main>';
 for(const id of ["scenario","a-inject","safety-select"]){const node=root.querySelector("#"+id);if(node){const target=id==="scenario"?node.closest("label"):node.closest("section");target?.remove();}}
 for(const title of ["inbox"]){const label=FMZ8Copy[lang][title]||FMZDemoCopy[lang][title];for(const h of root.querySelectorAll("#route-content h2"))if(h.textContent===label)h.closest("section")?.remove();}
 for(const b of root.querySelectorAll('[data-action="a"]')){const d=JSON.parse(b.dataset.value);if(d.role!==state?.actor_role||state.revision===0)b.disabled=true;}
 for(const b of root.querySelectorAll("button"))if(busy)b.disabled=true;
}
function warning(){if(!state||state.guard==="clear")return "";const key=["current","serious","recurring","unclassified"].includes(state.guard)?"warning_health":state.guard==="self_reported"?"warning_recovered":"warning_unclear";return '<p class="notice">'+esc(FMZ8Copy[lang][key])+'</p>';}
async function request(body){
 if(!navigator.onLine)throw Error("offline");
 const r=await fetch(base+"/functions/v1/fmz6e9-synthetic",{method:"POST",headers:{Authorization:"Bearer "+auth.access_token,"Content-Type":"application/json"},body:JSON.stringify(body),signal:AbortSignal.timeout(20000)});
 const d=await r.json();if(!r.ok){const e=Error(d.error||"request_failed");e.status=r.status;throw e;}return d;
}
function error(e){feedback=e.status===409?t("conflict"):e.status===401||e.status===403||e.status===503?t("denied"):t("error");if(e.status===409||e.status===400||e.status===403)pending=null;if(e.status===401){auth=null;state=null;sessionStorage.removeItem(STORE);}}
async function load(){
 homes=(await request({op:"home"})).workspaces;
 if(!homes.length)throw Error("no_workspace");
 state=await request({op:"read",workspace:homes[0].workspace});
 form=state.route==="B"&&!state.view.active&&!state.view.draft;pendingIntake=null;
}
async function perform(action,data={}){
 pending={op:"command",workspace:state.workspace,expected:state.revision,key:crypto.randomUUID(),command:{action,data}};
 state=await request(pending);pending=null;feedback=t("saved");if(action==="build"){form=false;pendingIntake=null;}
}
function intakeData(){const form=root.querySelector("#intake"),i=JSON.parse(JSON.stringify(FMZ8Catalog.defaults));
 for(const k of Object.keys(FMZ8Model.enums)){const v=form.elements.namedItem(k).value;i[k]=typeof i[k]==="number"?Number(v):v;}
 for(const k of Object.keys(FMZ8Model.arrays))i[k]=[...form.querySelectorAll('input[name="'+k+'"]:checked')].map(x=>x.value);
 i.rir=form.elements.namedItem("rir").checked;i.rpe=form.elements.namedItem("rpe").checked;return i;
}
async function task(fn){if(busy)return;busy=true;render();try{await fn();}catch(e){error(e);}finally{busy=false;render();}}
root.addEventListener("submit",e=>{e.preventDefault();if(e.target.id!=="login")return;
 const email=e.target.elements.email.value.trim(),password=e.target.elements.password.value;
 if(!/^6e9-[a-z0-9-]+@example\.invalid$/.test(email)){feedback=t("denied");render();return;}
 task(async()=>{const r=await fetch(base+"/auth/v1/token?grant_type=password",{method:"POST",headers:{apikey:cfg.SUPABASE_ANON_KEY,"Content-Type":"application/json"},body:JSON.stringify({email,password})});const d=await r.json();if(!r.ok){const x=Error("login");x.status=401;throw x;}
 auth={access_token:d.access_token,refresh_token:d.refresh_token};sessionStorage.setItem(STORE,JSON.stringify(auth));await load();feedback="";});
});
root.addEventListener("change",e=>{if(e.target.closest("#intake"))pendingIntake=intakeData();if(e.target.id==="lang"){lang=e.target.value;render();}if(e.target.id==="theme"){theme=e.target.value;render();}});
root.addEventListener("click",e=>{
 const b=e.target.closest("button");if(!b||b.disabled)return;
 if(b.dataset.tab){tab=b.dataset.tab;render();return;}
 if(b.dataset.command==="logout"){const old=auth;auth=null;state=null;pending=null;pendingIntake=null;sessionStorage.removeItem(STORE);render();if(old)fetch(base+"/auth/v1/logout?scope=local",{method:"POST",headers:{apikey:cfg.SUPABASE_ANON_KEY,Authorization:"Bearer "+old.access_token}}).catch(()=>{});return;}
 if(b.dataset.command==="refresh"){task(load);return;}
 if(b.dataset.command==="retry"){const retry=pending;task(async()=>{state=await request(retry);pending=null;feedback=t("saved");});return;}
 if(b.dataset.command==="open"){task(()=>perform("open"));return;}
 const action=b.dataset.action,d=JSON.parse(b.dataset.value||"{}");
 if(action==="intake-form"){form=true;render();return;}
 if(action==="build"){const i=intakeData();task(()=>perform("build",{intake:i}));return;}
 if(action==="a"){task(()=>perform(d.action,d.action==="restore"?{version:d.version}:{}));return;}
 let next=action;
 if(action==="replace"){next="edit";d.kind="replace";d.id=root.querySelector('[data-replace="'+d.session+':'+d.index+'"]').value;}
 if(action==="add"){next="edit";d.kind="add";d.id=root.querySelector('[data-add="'+d.session+'"]').value;}
 if(action==="meal"){next="edit";d.kind="meal";d.id=root.querySelector('[data-meal="'+d.index+'"]').value;}
 if(action==="food"){next="edit";d.kind="food";d.id=root.querySelector('[data-food="'+d.meal+':'+d.index+'"]').value;}
 if(action==="sleep"){next="edit";d.kind="sleep";d.hours=Number(root.querySelector("#sleep-edit").value);}
 if(action==="signal")d.id=root.querySelector("#signal-select").value;
 if(next)task(()=>perform(next,d));
});
media.addEventListener("change",()=>{if(theme==="system")render();});
try{auth=JSON.parse(sessionStorage.getItem(STORE)||"null");}catch{sessionStorage.removeItem(STORE);}
render();
if(auth)task(async()=>{const r=await fetch(base+"/auth/v1/token?grant_type=refresh_token",{method:"POST",headers:{apikey:cfg.SUPABASE_ANON_KEY,"Content-Type":"application/json"},body:JSON.stringify({refresh_token:auth.refresh_token})});const d=await r.json();if(!r.ok){const e=Error("expired");e.status=401;throw e;}auth={access_token:d.access_token,refresh_token:d.refresh_token};sessionStorage.setItem(STORE,JSON.stringify(auth));await load();});
})();
