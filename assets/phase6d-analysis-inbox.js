(() => {
  "use strict";
  if(window.FMZ_ANALYSIS_INBOX)return;
  const AI=window.FMZ_PHASE6C_PRIVATE_CHAT,Settings=window.FMZ_OWNER_SETTINGS;
  const words={
    ready:["Klaar voor jou","Ready for you","Fuer dich bereit"],all:["Alle analyses","All analyses","Alle Analysen"],
    history:["Analysegeschiedenis","Analysis history","Analyseverlauf"],view:["Bekijk analyse","View analysis","Analyse ansehen"],
    now:["Nu bekijken","View now","Jetzt ansehen"],later:["Later bekijken","View later","Spaeter ansehen"],
    daily:["Dagelijkse analyse","Daily analysis","Taegliche Analyse"],weekly:["Weekanalyse","Weekly analysis","Wochenanalyse"],
    post_workout:["Trainingsanalyse","Workout analysis","Trainingsanalyse"],
    dailyReady:["Je dagelijkse analyse staat klaar.","Your daily analysis is ready.","Deine Tagesanalyse ist bereit."],
    weeklyReady:["Je wekelijkse analyse staat klaar.","Your weekly analysis is ready.","Deine Wochenanalyse ist bereit."],
    post_workoutReady:["Je nieuwe trainingsanalyse staat klaar.","Your new workout analysis is ready.","Deine neue Trainingsanalyse ist bereit."],
    new:["Nieuw","New","Neu"],laterState:["Bewaard voor later","Saved for later","Fuer spaeter gespeichert"],
    close:["Sluiten","Close","Schliessen"],loading:["Laden...","Loading...","Wird geladen..."],
    retry:["Opnieuw laden","Reload","Neu laden"],error:["Laden of opslaan is niet gelukt. Probeer opnieuw.","Could not load or save. Please try again.","Laden oder Speichern fehlgeschlagen. Bitte erneut versuchen."],
    unavailable:["Deze analyse is niet beschikbaar.","This analysis is not available.","Diese Analyse ist nicht verfuegbar."],
    empty:["Nog geen analyses.","No analyses yet.","Noch keine Analysen."],more:["Meer laden","Load more","Mehr laden"],
    export:["Exporteren","Export","Exportieren"],delete:["Verwijderen","Delete","Loeschen"],archive:["Archiveren","Archive","Archivieren"],
    confirm:["Deze analyse definitief verwijderen?","Permanently delete this analysis?","Diese Analyse endgueltig loeschen?"],
    period:["Geanalyseerde periode","Analysis period","Analysezeitraum"],quality:["Datakwaliteit","Data quality","Datenqualitaet"],
    sufficient:["Voldoende","Sufficient","Ausreichend"],partial:["Gedeeltelijk","Partial","Teilweise"],
    insufficient:["Onvoldoende data","Insufficient data","Unzureichende Daten"],insufficient_data:["Onvoldoende data","Insufficient data","Unzureichende Daten"],
    pending:["Wordt verwerkt","Processing","In Bearbeitung"],failed:["Niet afgerond","Not completed","Nicht abgeschlossen"],
    completed:["Gereed","Ready","Fertig"],insights:["Kerninzichten","Key observations","Beobachtungen"],
    caveats:["Aandachtspunten","Caveats","Hinweise"],reflection:["Veilige aanbeveling","Safe reflection","Sichere Empfehlung"],
    mock:["Mock / stagingtest - externe AI uit","Mock / staging test - external AI off","Mock / Staging-Test - externe KI aus"],
    first:["Dit is de eerste geschikte vergelijking; er is geen betrouwbare vorige training.","This is the first suitable comparison; no reliable previous workout is available.","Dies ist der erste passende Vergleich; kein verlaessliches vorheriges Training liegt vor."],
    compare:["Trainingsvergelijking","Workout comparison","Trainingsvergleich"],current:["Deze training","This workout","Dieses Training"],
    previous:["Vorige training","Previous workout","Vorheriges Training"],noValue:["Niet vastgelegd","Not recorded","Nicht erfasst"],
    duration:["Verstreken minuten, inclusief pauzes","Elapsed minutes, including pauses","Vergangene Minuten, einschliesslich Pausen"],
    noActiveDuration:["Actieve trainingsduur is niet vastgelegd.","Active training duration was not recorded.","Die aktive Trainingsdauer wurde nicht erfasst."],
    same_program_day:["Dezelfde programmadag","Same program day","Gleicher Programmtag"],
    same_exercise_set:["Dezelfde oefeningenset","Same exercise set","Gleiche Uebungsauswahl"],
    sets:["Sets","Sets","Saetze"],reps:["Herhalingen totaal","Total repetitions","Wiederholungen gesamt"],
    max_weight_kg:["Hoogste gewicht (kg)","Highest weight (kg)","Hoechstes Gewicht (kg)"],
    volume_kg:["Volume (kg x herhalingen)","Volume (kg x repetitions)","Volumen (kg x Wiederholungen)"],
    rpe:["Gemiddelde RPE","Average RPE","Mittlere RPE"],rir:["Gemiddelde RIR","Average RIR","Mittlere RIR"],
    higher:["Hoger gemeten volume","Higher measured volume","Hoeheres gemessenes Volumen"],
    lower:["Lager gemeten volume","Lower measured volume","Geringeres gemessenes Volumen"],
    equal:["Gelijk gemeten volume","Equal measured volume","Gleiches gemessenes Volumen"],
    observationsOnly:["Een verschil is een meetpunt, geen diagnose van vooruitgang of vermoeidheid.","A difference is an observation, not a diagnosis of progress or fatigue.","Ein Unterschied ist eine Beobachtung, keine Diagnose von Fortschritt oder Ermuedung."],
    training:["Training","Training","Training"],nutrition:["Voeding","Nutrition","Ernaehrung"],recovery:["Herstel","Recovery","Erholung"],progress:["Voortgang","Progress","Fortschritt"],
    missing:["Ontbrekende bronnen","Missing sources","Fehlende Quellen"],
    days_logged:["Geregistreerde dagen","Logged days","Erfasste Tage"],items_logged:["Voedingsitems","Food items","Lebensmitteleintraege"],
    completed_workouts:["Voltooide trainingen","Completed workouts","Abgeschlossene Trainings"],set_count:["Sets","Sets","Saetze"],
    avg_sets_per_workout:["Gemiddeld aantal sets per training","Average sets per workout","Mittlere Saetze pro Training"],
    avg_sleep_hours:["Gemiddelde slaap (uur)","Average sleep (hours)","Mittlerer Schlaf (Stunden)"],
    avg_sleep_quality:["Gemiddelde slaapkwaliteit","Average sleep quality","Mittlere Schlafqualitaet"],
    avg_steps:["Gemiddelde stappen","Average steps","Mittlere Schritte"],avg_energy:["Gemiddelde energie","Average energy","Mittlere Energie"],
    avg_stress:["Gemiddelde stress","Average stress","Mittlerer Stress"],avg_motivation:["Gemiddelde motivatie","Average motivation","Mittlere Motivation"],
    avg_recovery_feeling:["Gemiddeld herstelgevoel","Average recovery feeling","Mittleres Erholungsgefuehl"],
    avg_energy_kcal:["Gemiddelde energie (kcal)","Average energy (kcal)","Mittlere Energie (kcal)"],
    avg_protein_grams:["Gemiddeld eiwit (g)","Average protein (g)","Mittleres Eiweiss (g)"],
    avg_carbohydrate_grams:["Gemiddelde koolhydraten (g)","Average carbohydrates (g)","Mittlere Kohlenhydrate (g)"],
    avg_fat_grams:["Gemiddeld vet (g)","Average fat (g)","Mittleres Fett (g)"],
    avg_fiber_grams:["Gemiddelde vezels (g)","Average fibre (g)","Mittlere Ballaststoffe (g)"],
    weight_logs:["Gewichtsmetingen","Weight observations","Gewichtsmessungen"],body_measurement_logs:["Lichaamsmetingen","Body measurements","Koerpermessungen"],
    latest_weight_kg:["Laatste gewicht (kg)","Latest weight (kg)","Letztes Gewicht (kg)"],first_weight_kg:["Eerste gewicht (kg)","First weight (kg)","Erstes Gewicht (kg)"],
    insufficient_reliable_data:["Nog onvoldoende betrouwbare meetpunten.","Not enough reliable observations yet.","Noch nicht genug verlaessliche Beobachtungen."],
    noInsights:["Er is geen conclusie beschikbaar.","No conclusion is available.","Es liegt keine Schlussfolgerung vor."]
  };
  const lang=()=>["nl","en","de"].includes(state.accountSettings?.language)?state.accountSettings.language:"nl";
  const t=key=>words[key]?.[["nl","en","de"].indexOf(lang())]||words[key]?.[0]||key;
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const uid=()=>isLoggedIn()&&onlineProfile?.role==="client"?onlineProfile.id:"";
  const icon=name=>'<img src="assets/vendor/lucide-'+name+'.svg" width="22" height="22" alt="">';
  const command=(name,key,attrs)=>'<button type="button" class="fmz-icon" '+attrs+' title="'+esc(t(key))+'" aria-label="'+esc(t(key))+'">'+icon(name)+'</button>';
  const when=value=>value?Settings.formatDate(value)+" "+Settings.formatTime(value):t("noValue");
  const number=value=>typeof value==="number"&&Number.isFinite(value)?value.toLocaleString(lang(),{maximumFractionDigits:1}):t("noValue");
  const dateOnly=value=>/^\d{4}-\d{2}-\d{2}$/.test(value||"")?new Date(value+"T12:00:00Z").toLocaleDateString(lang(),{timeZone:"UTC"}):t("noValue");
  const validId=id=>/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id||"");
  let owner="",generation=0,inFlight=null,inboxVersion=0,inbox={items:[],recent:[],unread_count:0},dialog=null,result=null,detailId="",detailError="",detailBusy=false,detailOpener=null,readSequence=0;
  let archiveBusy=false;
  let toast=null,toastBusy=false,inboxError="",timer=null,routed="",oldHash="",historyExtra=[],historyEnd=false,historyBusy=false;
  async function rpc(name,args={}) {
    const user=uid(),epoch=generation;
    if(!user)throw new Error("auth_required");
    const response=await supabaseClient.rpc(name,args);
    if(uid()!==user||generation!==epoch)throw new Error("identity_changed");
    if(response.error)throw response.error;
    return response.data;
  }
  function reset(){
    generation++;owner="";inFlight=null;inboxVersion++;archiveBusy=false;inbox={items:[],recent:[],unread_count:0};inboxError="";historyExtra=[];historyEnd=false;historyBusy=false;routed="";
    clearTimeout(timer);timer=null;toastBusy=false;closeDetail(false);toast?.remove();toast=null;
    document.getElementById("fmz-analysis-inbox")?.remove();updateBadge();
  }
  function ensureOwner(){const user=uid();if(owner!==user){reset();owner=user;}return Boolean(user);}
  function updateBadge(){
    const badge=document.querySelector(".fmz-avatar-unread");if(!badge)return;
    badge.hidden=!uid()||!inbox.unread_count;badge.textContent=inbox.unread_count>9?"9+":String(inbox.unread_count||"");
    badge.title=t("ready")+": "+Number(inbox.unread_count||0);
  }
  function schedulePoll(){
    clearTimeout(timer);timer=null;
    if(uid()&&!document.hidden&&navigator.onLine)timer=setTimeout(()=>hydrate(),45000);
  }
  async function hydrate({force=false}={}){
    if(!ensureOwner())return;
    if(inFlight){if(!force)return inFlight;await inFlight;return hydrate();}
    const epoch=generation,version=inboxVersion;
    inFlight=(async()=>{
      try{
        const next=await rpc("fmz_phase6d_get_inbox");
        if(!Array.isArray(next?.items)||!Array.isArray(next?.recent))throw new Error("inbox_invalid");
        if(version!==inboxVersion)return;
        inbox=next;inboxError="";
      }catch{if(epoch===generation)inboxError=t("error");}
      finally{if(epoch===generation){inFlight=null;renderDashboard();renderToast();updateBadge();route();schedulePoll();}}
    })();
    return inFlight;
  }
  function renderDashboard(){
    if(!uid())return;
    const home=document.getElementById("client-home");if(!home)return;
    const shell=home.querySelector("#clientSummary > .member-ux-today-simplified");
    const anchor=shell?.querySelector(":scope > .member-ux-training-today")||shell?.querySelector(":scope > .member-ux-profile-cta");
    if(!anchor){document.getElementById("fmz-analysis-inbox")?.remove();return;}
    let node=document.getElementById("fmz-analysis-inbox");
    if(!node){node=document.createElement("section");node.id="fmz-analysis-inbox";node.setAttribute("aria-labelledby","fmz-inbox-title");}
    if(anchor.nextElementSibling!==node)anchor.after(node);
    node.innerHTML='<header><h2 id="fmz-inbox-title">'+esc(t("ready"))+'</h2></header>'+
      (inboxError?'<p role="status">'+esc(inboxError)+'</p><button type="button" class="secondary-btn" data-fmz-inbox-retry>'+esc(t("retry"))+'</button>':"")+
      '<div class="fmz-inbox-items">'+inbox.recent.slice(0,3).map(item=>'<article class="member-ux-card fmz-inbox-item"><div class="fmz-inbox-meta"><p class="eyebrow">'+esc(t(item.analysis_kind))+'</p><span class="fmz-inbox-marker">'+
        (["new","later"].includes(item.state)?'<span class="fmz-inbox-state">'+esc(t("new"))+'</span>':"")+'</span></div>'+
        '<h3 title="'+esc(item.title||t(item.analysis_kind))+'">'+esc(item.title||t(item.analysis_kind))+'</h3><time class="muted">'+esc(when(item.completed_at||item.created_at))+'</time><div class="member-ux-card-actions fmz-inbox-actions"><button type="button" class="primary-btn" data-fmz-analysis-open="'+esc(item.analysis_id)+'">'+esc(t("view"))+'</button>'+
        command("archive","archive",'data-fmz-analysis-archive="'+esc(item.analysis_id)+'" '+(archiveBusy?'disabled':""))+'</div></article>').join("")+'</div><footer class="fmz-inbox-actions"><button type="button" class="fmz-inbox-history-link" data-fmz-all-analyses>'+esc(t("all"))+'</button></footer>';
    node.hidden=!inbox.recent.length&&!inboxError;
  }
  function renderToast(){
    const hidden=document.hidden||!uid()||Settings.unsafeSurface()||Boolean(document.querySelector("dialog[open],[aria-modal=true]"))||document.activeElement?.matches("input,textarea,[contenteditable=true]");
    const item=inbox.items.find(n=>n.state==="new");
    if(!item||hidden){toast?.remove();toast=null;return;}
    if(toast?.dataset.analysisId===item.analysis_id)return;
    toast?.remove();toast=document.createElement("section");toast.className="fmz-analysis-toast";toast.setAttribute("role","status");toast.setAttribute("aria-live","polite");toast.dataset.analysisId=item.analysis_id;
    toast.innerHTML='<p>'+esc(t(item.analysis_kind+"Ready"))+'</p><div class="fmz-actions"><button type="button" class="primary-btn" data-fmz-analysis-open="'+esc(item.analysis_id)+'">'+esc(t("now"))+'</button><button type="button" class="secondary-btn" data-fmz-analysis-later="'+esc(item.analysis_id)+'">'+esc(t("later"))+'</button></div><p class="fmz-notification-error"></p>';
    document.body.appendChild(toast);
  }
  async function mark(id,action){
    await rpc("fmz_phase6d_mark_notification",{p_analysis_id:id,p_action:action});
    inboxVersion++;await hydrate({force:true});
  }
  async function archive(id){
    if(archiveBusy)return;archiveBusy=true;renderDashboard();
    try{await mark(id,"archived");document.querySelector("[data-fmz-all-analyses]")?.focus({preventScroll:true});}
    catch{inboxError=t("error");}
    finally{archiveBusy=false;renderDashboard();}
  }
  async function defer(id){
    if(toastBusy)return;toastBusy=true;
    toast?.querySelectorAll("button").forEach(b=>b.disabled=true);
    try{await mark(id,"later");}catch{const target=toast?.querySelector(".fmz-notification-error");if(target)target.textContent=t("error");}
    finally{toastBusy=false;toast?.querySelectorAll("button").forEach(b=>b.disabled=false);}
  }
  function closeDetail(restore=true){
    readSequence++;dialog?.close();dialog?.remove();dialog=null;result=null;detailId="";detailError="";detailBusy=false;
    document.body.classList.remove("fmz-analysis-open");
    if(restore&&location.hash.startsWith("#analysis="))history.replaceState(history.state,"",location.pathname+location.search+oldHash);
    if(restore&&detailOpener?.isConnected)detailOpener.focus({preventScroll:true});
  }
  async function openDetail(id,{deep=false}={}){
    if(!ensureOwner()||!validId(id))return;
    const sequence=++readSequence,epoch=generation;
    if(!dialog){
      detailOpener=document.activeElement;oldHash=deep?"":location.hash;
      dialog=document.createElement("dialog");dialog.id="fmz-analysis-detail";dialog.className="fmz-dialog fmz-analysis-dialog";dialog.setAttribute("aria-label",t("view"));document.body.appendChild(dialog);
      dialog.addEventListener("cancel",event=>{event.preventDefault();closeDetail();});
    }
    detailId=id;result=null;detailError="";detailBusy=true;renderDetail();
    if(!dialog.open)dialog.showModal();
    document.body.classList.add("fmz-analysis-open");renderToast();
    if(!deep)history.replaceState(history.state,"",location.pathname+location.search+"#analysis="+id);
    routed=uid()+":"+id;
    try{
      const data=await rpc("fmz_phase6d_read_analysis",{p_result_id:id});
      if(sequence!==readSequence||epoch!==generation)return;
      if(data?.result?.id!==id)throw new Error("result_identity_invalid");
      result=data.result;detailBusy=false;renderDetail();
      try{await mark(id,"opened");}catch{if(sequence===readSequence){detailError=t("error");renderDetail();}}
    }catch{
      if(sequence===readSequence&&epoch===generation){detailBusy=false;detailError=t("unavailable");renderDetail();}
    }
  }
  const row=(key,value)=>'<div class="fmz-value-row"><dt>'+esc(t(key))+'</dt><dd>'+esc(value)+'</dd></div>';
  function workoutComparison(comparison){
    if(!comparison)return "";
    const current=comparison.current,previous=comparison.previous;
    const session=(key,item)=>'<div class="fmz-workout-reference"><h3>'+esc(t(key))+'</h3>'+(item?'<time>'+esc(when(item.completed_at))+'</time><code>'+esc(item.id)+'</code><p>'+esc(t("duration"))+': '+number(typeof item.elapsed_seconds==="number"?item.elapsed_seconds/60:null)+'</p>':'<p>'+esc(t("noValue"))+'</p>')+'</div>';
    return '<section class="fmz-comparison"><h2>'+esc(t("compare"))+'</h2><p>'+esc(t(comparison.available?comparison.reason:"first"))+'</p><div class="fmz-workout-pair">'+session("current",current)+session("previous",previous)+'</div><p>'+esc(t("noActiveDuration"))+'</p>'+
      (comparison.exercises||[]).map(ex=>'<section class="fmz-exercise-comparison"><h3>'+esc((ex.label||"").replace(/[-_]/g," "))+'</h3><table><thead><tr><th scope="col"></th><th scope="col">'+esc(t("current"))+'</th><th scope="col">'+esc(t("previous"))+'</th></tr></thead><tbody>'+
      ["sets","reps","max_weight_kg","volume_kg","rpe","rir"].map(key=>'<tr><th scope="row">'+esc(t(key))+'</th><td data-label="'+esc(t("current"))+'">'+esc(number(ex.current?.[key]))+'</td><td data-label="'+esc(t("previous"))+'">'+esc(number(ex.previous?.[key]))+'</td></tr>').join("")+'</tbody></table>'+
      (ex.volume_change?'<p class="fmz-observed-change '+esc(ex.volume_change)+'">'+esc(t(ex.volume_change))+'</p>':"")+'</section>').join("")+'<p>'+esc(t("observationsOnly"))+'</p></section>';
  }
  function resultBody(item){
    const payload=item.result_payload||{},quality=item.quality||payload.data_quality||{},isPending=item.status==="pending",isFailed=item.status==="failed";
    const observations=Array.isArray(payload.observations)?payload.observations:[],suggestions=Array.isArray(payload.suggestions)?payload.suggestions:[];
    return '<p class="fmz-mock-label">'+esc(t("mock"))+(item.model_tier?' / '+esc(item.model_tier):"")+'</p><time>'+esc(when(item.completed_at||item.created_at))+'</time>'+
      '<dl>'+row("period",dateOnly(item.period_start_local||payload.period?.start_local)+" - "+dateOnly(item.period_end_local||payload.period?.end_local)+" / "+(item.timezone_name||payload.period?.timezone_name||""))+
      row("quality",t(quality.level||"insufficient"))+'</dl>'+
      '<section><h2>'+esc(t(isPending?"pending":isFailed?"failed":"insights"))+'</h2><p>'+esc(isPending?t("pending"):isFailed?t("failed"):item.summary_text||item.summary||payload.summary||t("noInsights"))+'</p>'+
      observations.map(ob=>'<div class="fmz-observation">'+(ob.text?'<p>'+esc(ob.text)+'</p>':"")+
        (ob.metrics?'<h3>'+esc(t(ob.source))+'</h3><dl>'+Object.entries(ob.metrics).filter(([key,value])=>words[key]&&typeof value==="number").map(([key,value])=>row(key,number(value))).join("")+'</dl>':"")+'</div>').join("")+'</section>'+
      workoutComparison(payload.comparison)+
      '<section><h2>'+esc(t("caveats"))+'</h2><p>'+esc(t("missing"))+': '+((quality.missing_sources||[]).map(key=>esc(t(key))).join(", ")||esc(t("noValue")))+'</p>'+
      (payload.uncertainties||[]).filter(key=>words[key]&&!(quality.missing_sources||[]).includes(key)).map(key=>'<p>'+esc(t(key))+'</p>').join("")+'</section>'+
      (suggestions.length?'<section><h2>'+esc(t("reflection"))+'</h2>'+suggestions.map(value=>'<p>'+esc(value.text||"")+'</p>').join("")+'</section>':"");
  }
  function renderDetail(){
    if(!dialog)return;
    dialog.innerHTML='<header class="fmz-dialog-head"><h2>'+esc(t(result?.analysis_kind||"view"))+'</h2><div class="fmz-detail-actions">'+
      (result?command("download","export","data-fmz-detail-export")+command("trash-2","delete","data-fmz-detail-delete"):"")+command("x","close","data-fmz-detail-close")+'</div></header>'+
      '<main class="fmz-settings-content">'+(detailError?'<p class="error" role="status">'+esc(detailError)+'</p><button type="button" class="secondary-btn" data-fmz-detail-retry>'+esc(t("retry"))+'</button>':"")+
      (result?resultBody(result):detailBusy?'<p role="status">'+esc(t("loading"))+'</p>':"")+'</main>';
    dialog.querySelectorAll("[data-fmz-detail-export],[data-fmz-detail-delete]").forEach(node=>node.disabled=detailBusy);
  }
  async function deleteResult(){
    if(!result||detailBusy||!window.confirm(t("confirm")))return;
    const id=result.id,revision=result.revision;detailBusy=true;renderDetail();
    try{
      await rpc("fmz_phase6d_delete_analysis",{p_result_id:id,p_expected_revision:revision,p_request_id:crypto.randomUUID()});
      historyExtra=historyExtra.filter(item=>item.id!==id);closeDetail();await AI.hydrate({force:true});await hydrate();
    }catch{detailBusy=false;detailError=t("error");renderDetail();}
  }
  function exportResult(){
    if(!result)return;
    const link=document.createElement("a"),url=URL.createObjectURL(new Blob([JSON.stringify({schema_version:"phase6d.detail.v1",result},null,2)],{type:"application/json"}));
    link.href=url;link.download="fitmetzorge-analysis-"+result.id+".json";link.click();setTimeout(()=>URL.revokeObjectURL(url),0);
  }
  function historyItems(items){
    return [...new Map([...historyExtra,...items].map(item=>[item.id,item])).values()].sort((a,b)=>b.created_at.localeCompare(a.created_at)||b.id.localeCompare(a.id));
  }
  function renderHistory(items=[],status){
    const visible=historyItems(items).filter(item=>item.status!=="deleted"&&(!item.result_expires_at||new Date(item.result_expires_at)>new Date()));
    return '<div class="fmz-analysis-history">'+(Settings.safetyPanel(status?.recovery)||"")+
      '<header><h2>'+esc(t("history"))+'</h2>'+command("download","export","data-p6d-export")+'</header>'+
      (visible.length?visible.map(item=>'<button type="button" class="fmz-history-row" data-fmz-analysis-open="'+esc(item.id)+'"><span><strong>'+esc(t(item.analysis_kind))+'</strong><time>'+esc(when(item.created_at))+'</time><small>'+esc(t(["ready","partial"].includes(item.status)?"completed":item.status))+'</small></span>'+icon("chevron-right")+'</button>').join(""):'<p>'+esc(t("empty"))+'</p>')+
      (!historyEnd&&items.length+historyExtra.length>=20?'<button type="button" class="secondary-btn" data-fmz-history-more '+(historyBusy?"disabled":"")+'>'+esc(t(historyBusy?"loading":"more"))+'</button>':"")+
      (inboxError?'<p role="status">'+esc(inboxError)+'</p>':"")+'</div>';
  }
  async function moreHistory(){
    if(historyBusy)return;historyBusy=true;AI.render();
    const items=historyItems(AI.snapshot().analyses||[]),last=items.at(-1);
    try{
      const next=await rpc("fmz_phase6d_list_analyses",{p_limit:20,p_before_created_at:last?.created_at||null,p_before_id:last?.id||null});
      historyExtra=historyItems([...(next.results||[]),...historyExtra]);historyEnd=(next.results||[]).length<20;
    }catch{inboxError=t("error");}finally{historyBusy=false;AI.render();}
  }
  async function openHistory(){await Settings.openChat();AI.selectTab("analyses");}
  function route(){
    if(!uid())return;
    const hash=location.hash.match(/^#analysis=([0-9a-f-]+)$/i),id=hash?.[1]||new URL(location.href).searchParams.get("analysis");
    if(validId(id)&&routed!==uid()+":"+id)openDetail(id,{deep:true});
  }
  document.addEventListener("click",event=>{
    const button=event.target.closest("button");if(!button)return;
    if(button.dataset.fmzAnalysisOpen)openDetail(button.dataset.fmzAnalysisOpen);
    if(button.dataset.fmzAnalysisLater)defer(button.dataset.fmzAnalysisLater);
    if(button.dataset.fmzAnalysisArchive)archive(button.dataset.fmzAnalysisArchive);
    if(button.hasAttribute("data-fmz-all-analyses"))openHistory();
    if(button.hasAttribute("data-fmz-detail-close"))closeDetail();
    if(button.hasAttribute("data-fmz-detail-retry"))openDetail(detailId,{deep:true});
    if(button.hasAttribute("data-fmz-detail-export"))exportResult();
    if(button.hasAttribute("data-fmz-detail-delete"))deleteResult();
    if(button.hasAttribute("data-fmz-history-more"))moreHistory();
    if(button.hasAttribute("data-fmz-inbox-retry"))hydrate();
    queueMicrotask(renderToast);
  });
  window.addEventListener("hashchange",()=>{routed="";route();});
  document.addEventListener("visibilitychange",()=>{if(document.hidden){clearTimeout(timer);timer=null;}else hydrate();});
  window.addEventListener("online",hydrate);
  window.addEventListener("focus",()=>{Settings.syncDeviceTimezone();hydrate();});
  window.addEventListener("fmz:ai-state",()=>{renderDashboard();updateBadge();hydrate();});
  window.addEventListener("fmz:surface-change",renderToast);
  // Hook renders, not DOM mutations: existing dashboard modules keep ownership of their content.
  const previousRender=renderAll,previousView=showView,previousHome=renderClientHome;
  renderClientHome=function(){const value=previousHome();if(ensureOwner())renderDashboard();return value;};
  renderAll=function(){const value=previousRender();if(ensureOwner()){renderDashboard();updateBadge();if(!inFlight&&!timer)queueMicrotask(hydrate);}return value;};
  showView=function(id){const value=previousView(id);if(uid()){renderDashboard();renderToast();if(id==="client-home")hydrate();}return value;};
  supabaseClient?.auth.onAuthStateChange?.(event=>{if(event==="SIGNED_OUT")reset();});
  window.FMZ_ANALYSIS_INBOX=Object.freeze({hydrate,open:openDetail,openHistory,renderHistory,reset,snapshot:()=>({inbox,owner}),mockOnly:true});
  if(uid())hydrate();
})();
