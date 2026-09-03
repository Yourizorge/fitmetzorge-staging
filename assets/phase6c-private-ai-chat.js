(() => {
  if (window.FMZ_PHASE6C_PRIVATE_CHAT_LOADED) return;
  window.FMZ_PHASE6C_PRIVATE_CHAT_LOADED = true;

  const VERSION = "20260903-phase6c-private-chat1";
  const LANGUAGES = ["nl", "en", "de"];
  const I18N = {
    nl: {
      nav:"AI Coach",title:"FitMetZorge AI Coach",intro:"Een privegesprek voor heldere, haalbare volgende stappen.",mock:"Testmodus: antwoorden komen van een vaste simulatie, niet van een live AI-model.",
      loading:"Gesprekken laden...",retry:"Opnieuw proberen",newChat:"Nieuw gesprek",conversations:"Gesprekken",empty:"Nog geen gesprekken.",emptyMessages:"Begin met een vraag of vertel waar je tegenaan loopt.",
      placeholder:"Schrijf je bericht...",send:"Versturen",sending:"Bezig met antwoorden...",failed:"Antwoord mislukt.",offline:"Je bent offline. Je bericht blijft hier staan en wordt niet verstuurd.",
      consentTitle:"Toestemming voor AI-verwerking",consentAgree:"Ik geef expliciet toestemming voor de beschreven AI-verwerking.",activate:"Toestemming geven",withdraw:"Toestemming intrekken",withdrawConfirm:"AI-toestemming intrekken? Nieuwe verwerking stopt direct.",
      entitlement:"AI Coach is beschikbaar met AI of personal coaching.",age:"AI Coach is alleen beschikbaar vanaf 18 jaar.",safety:"AI Coach is geblokkeerd vanwege een serieus of onduidelijk gezondheidssignaal. Zoek passende professionele hulp.",
      grace:"Je AI-toegang is afgelopen. Je kunt gesprekken nog lezen, exporteren en verwijderen tot {date}.",export:"Exporteren",delete:"Gesprek verwijderen",deleteConfirm:"Dit gesprek definitief verwijderen? De ruwe inhoud wordt onherstelbaar gewist.",
      close:"Sluiten",back:"Terug",older:"Oudere berichten",today:"Vandaag",you:"Jij",coach:"AI Coach test",deleted:"Gesprek verwijderd.",exported:"Export gereed.",stale:"Dit gesprek is elders gewijzigd. De nieuwste versie is geladen.",
      limit:"De veilige gebruikslimiet is bereikt. Probeer later opnieuw.",error:"AI Coach kon niet worden geladen.",consentSaved:"Toestemming opgeslagen.",consentWithdrawn:"Toestemming ingetrokken.",testOnly:"Alleen staging testmodus"
    },
    en: {
      nav:"AI Coach",title:"FitMetZorge AI Coach",intro:"A private conversation for clear, realistic next steps.",mock:"Test mode: replies come from a fixed simulation, not a live AI model.",
      loading:"Loading conversations...",retry:"Try again",newChat:"New conversation",conversations:"Conversations",empty:"No conversations yet.",emptyMessages:"Start with a question or explain what is getting in your way.",placeholder:"Write your message...",send:"Send",sending:"Preparing a reply...",failed:"Reply failed.",offline:"You are offline. Your message stays here and is not sent.",
      consentTitle:"Consent for AI processing",consentAgree:"I explicitly consent to the described AI processing.",activate:"Give consent",withdraw:"Withdraw consent",withdrawConfirm:"Withdraw AI consent? New processing stops immediately.",entitlement:"AI Coach is available with AI or personal coaching.",age:"AI Coach is available from age 18.",safety:"AI Coach is blocked due to a serious or unclear health signal. Seek appropriate professional support.",
      grace:"Your AI access ended. You can still read, export and delete conversations until {date}.",export:"Export",delete:"Delete conversation",deleteConfirm:"Delete this conversation permanently? Raw content will be irrecoverably erased.",close:"Close",back:"Back",older:"Older messages",today:"Today",you:"You",coach:"AI Coach test",deleted:"Conversation deleted.",exported:"Export ready.",stale:"This conversation changed elsewhere. The latest version was loaded.",limit:"The safe usage limit has been reached. Try again later.",error:"AI Coach could not be loaded.",consentSaved:"Consent saved.",consentWithdrawn:"Consent withdrawn.",testOnly:"Staging test mode only"
    },
    de: {
      nav:"AI Coach",title:"FitMetZorge AI Coach",intro:"Ein privates Gespraech fuer klare, realistische naechste Schritte.",mock:"Testmodus: Antworten kommen aus einer festen Simulation, nicht von einem Live-KI-Modell.",loading:"Gespraeche werden geladen...",retry:"Erneut versuchen",newChat:"Neues Gespraech",conversations:"Gespraeche",empty:"Noch keine Gespraeche.",emptyMessages:"Beginne mit einer Frage oder erzaehle, was dich gerade hindert.",placeholder:"Nachricht schreiben...",send:"Senden",sending:"Antwort wird vorbereitet...",failed:"Antwort fehlgeschlagen.",offline:"Du bist offline. Deine Nachricht bleibt hier und wird nicht gesendet.",
      consentTitle:"Einwilligung zur KI-Verarbeitung",consentAgree:"Ich willige ausdruecklich in die beschriebene KI-Verarbeitung ein.",activate:"Einwilligen",withdraw:"Einwilligung widerrufen",withdrawConfirm:"KI-Einwilligung widerrufen? Neue Verarbeitung stoppt sofort.",entitlement:"AI Coach ist mit AI oder Personal Coaching verfuegbar.",age:"AI Coach ist ab 18 Jahren verfuegbar.",safety:"AI Coach ist wegen eines ernsten oder unklaren Gesundheitssignals gesperrt. Hole passende professionelle Hilfe.",grace:"Dein AI-Zugang ist beendet. Du kannst Gespraeche bis {date} lesen, exportieren und loeschen.",export:"Exportieren",delete:"Gespraech loeschen",deleteConfirm:"Dieses Gespraech endgueltig loeschen? Der Rohinhalt wird unwiederbringlich entfernt.",close:"Schliessen",back:"Zurueck",older:"Aeltere Nachrichten",today:"Heute",you:"Du",coach:"AI Coach Test",deleted:"Gespraech geloescht.",exported:"Export bereit.",stale:"Dieses Gespraech wurde anderswo geaendert. Die neueste Version wurde geladen.",limit:"Das sichere Nutzungslimit ist erreicht. Versuche es spaeter erneut.",error:"AI Coach konnte nicht geladen werden.",consentSaved:"Einwilligung gespeichert.",consentWithdrawn:"Einwilligung widerrufen.",testOnly:"Nur Staging-Testmodus"
    }
  };

  const chat = { profileId:"",loaded:false,loading:false,status:null,consent:null,threads:[],thread:null,messages:[],error:"",notice:"",pending:false,draft:"",retry:null,opener:null };
  const lang=()=>{const value=state?.accountSettings?.language||"nl";return LANGUAGES.includes(value)?value:"nl";};
  const text=(key)=>I18N[lang()]?.[key]||I18N.nl[key]||key;
  const format=(key,values={})=>Object.entries(values).reduce((result,[name,value])=>result.split(`{${name}}`).join(String(value??"")),text(key));
  const esc=(value)=>String(value??"").replace(/[&<>"']/g,(char)=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
  const uuid=()=>window.crypto?.randomUUID?.()||"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,(char)=>{const value=Math.random()*16|0;return(char==="x"?value:(value&3)|8).toString(16);});
  const locale=()=>({nl:"nl-NL",en:"en-GB",de:"de-DE"})[lang()]||"nl-NL";
  const date=(value)=>value?new Date(value).toLocaleDateString(locale(),{day:"numeric",month:"short",year:"numeric"}):"";
  const time=(value)=>value?new Date(value).toLocaleTimeString(locale(),{hour:"2-digit",minute:"2-digit"}):"";
  const activeProfile=()=>onlineProfile?.role==="client"?onlineProfile.id:"";

  function errorText(error){
    const value=String(error?.message||error||"");
    if(/stale_conflict/.test(value))return text("stale");
    if(/limit_reached|rate_limit/.test(value))return text("limit");
    if(/entitlement/.test(value))return text("entitlement");
    if(/age_required/.test(value))return text("age");
    if(/safety_hard_stop/.test(value))return text("safety");
    return text("error");
  }

  function installStyles(){
    if(document.getElementById("phase6c-private-chat-styles"))return;
    const style=document.createElement("style");style.id="phase6c-private-chat-styles";style.textContent=`
      #ai-coach.phase6c-active{display:none}#ai-coach.phase6c-active.active{display:block}
      .p6c-shell{display:grid;gap:12px;padding-bottom:calc(var(--member-bottom-nav-reserve,96px) + env(safe-area-inset-bottom));min-width:0}
      .p6c-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.p6c-head h1{font-size:26px;line-height:1.15;margin:0;letter-spacing:0}.p6c-head p{margin:5px 0 0}
      .p6c-mode{border:1px solid rgba(215,178,77,.55);background:rgba(215,178,77,.1);padding:10px 12px;border-radius:8px;font-size:13px}
      .p6c-toolbar{display:flex;gap:8px;flex-wrap:wrap}.p6c-toolbar button{min-height:44px}.p6c-gold{background:#d7b24d!important;color:#15120a!important;border-color:#d7b24d!important;font-weight:700}
      .p6c-layout{display:grid;gap:12px}.p6c-list,.p6c-chat,.p6c-gate{border:1px solid var(--line);background:var(--surface);border-radius:8px;padding:12px;min-width:0}
      .p6c-list h2,.p6c-gate h2{font-size:18px;margin:0 0 10px}.p6c-thread-list{display:grid;gap:7px}.p6c-thread{width:100%;min-height:54px;text-align:left;display:grid;gap:3px;padding:9px 10px;border-radius:7px}.p6c-thread.active{border-color:#d7b24d}.p6c-thread span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.p6c-thread small{color:var(--muted)}
      .p6c-chat{display:grid;grid-template-rows:auto minmax(220px,1fr) auto;gap:10px;min-height:calc(100dvh - 250px)}.p6c-chat-head{display:flex;align-items:center;justify-content:space-between;gap:8px}.p6c-chat-head h2{font-size:18px;margin:0}
      .p6c-messages{display:flex;flex-direction:column;gap:9px;overflow:auto;overscroll-behavior:contain;padding:4px;min-height:220px;max-height:58dvh}.p6c-message{max-width:88%;padding:10px 11px;border-radius:8px;background:var(--panel);border:1px solid var(--line);overflow-wrap:anywhere}.p6c-message.user{align-self:flex-end;background:rgba(215,178,77,.12);border-color:rgba(215,178,77,.4)}.p6c-message.assistant{align-self:flex-start}.p6c-message strong{display:block;font-size:12px;margin-bottom:4px}.p6c-message p{margin:0;white-space:pre-wrap}.p6c-message time{display:block;color:var(--muted);font-size:11px;margin-top:5px;text-align:right}
      .p6c-composer{display:grid;gap:8px}.p6c-composer textarea{width:100%;min-height:82px;max-height:160px;resize:vertical}.p6c-composer-row{display:flex;justify-content:flex-end;gap:8px}.p6c-feedback{min-height:20px;font-size:13px}.p6c-feedback.error{color:#d86f6f}.p6c-empty{padding:22px 10px;text-align:center;color:var(--muted)}
      .p6c-consent{display:grid;gap:12px}.p6c-consent-copy{max-height:240px;overflow:auto;border-left:3px solid #d7b24d;padding:0 12px;white-space:pre-wrap}.p6c-check{display:grid;grid-template-columns:24px 1fr;align-items:start;gap:9px}.p6c-check input{width:22px;height:22px;margin:1px 0}.p6c-retention{border-left:3px solid #d7b24d;padding:10px 12px;background:rgba(215,178,77,.08)}
      @media(min-width:760px){.p6c-layout{grid-template-columns:minmax(220px,300px) minmax(0,1fr)}.p6c-chat{min-height:620px}.p6c-messages{max-height:520px}}
      @media(max-width:359px){.p6c-head{display:grid}.p6c-toolbar{display:grid;grid-template-columns:1fr 1fr}.p6c-toolbar button{padding-inline:8px}.p6c-message{max-width:94%}}
    `;document.head.appendChild(style);
  }

  function ensureNav(){
    const existing=NAV.client.find((item)=>item[0]==="ai-coach");
    if(existing){existing[1]=text("nav");return;}
    const settingsIndex=NAV.client.findIndex((item)=>item[0]==="settings");
    NAV.client.splice(settingsIndex>=0?settingsIndex:NAV.client.length,0,["ai-coach",text("nav")]);
  }

  async function rpc(name,args={}){if(!supabaseClient)throw new Error("auth_required");const result=await supabaseClient.rpc(name,args);if(result.error)throw result.error;return result.data;}

  function reset(){Object.assign(chat,{profileId:"",loaded:false,loading:false,status:null,consent:null,threads:[],thread:null,messages:[],error:"",notice:"",pending:false,draft:"",retry:null,opener:null});}

  async function hydrate({force=false,threadId=""}={}){
    const profileId=activeProfile();
    if(!profileId)return reset();
    if(chat.profileId!==profileId)reset();chat.profileId=profileId;
    if(chat.loading||(!force&&chat.loaded))return;
    chat.loading=true;chat.error="";render();
    try{
      const [status,consent,threads]=await Promise.all([
        rpc("fmz_phase6c_get_chat_status"),rpc("fmz_phase6a_read_consent_contract",{p_locale:lang()}),rpc("fmz_phase6c_list_threads",{p_limit:20,p_before_updated_at:null,p_before_id:null})
      ]);
      chat.status=status;chat.consent=consent;chat.threads=threads?.threads||[];
      const wanted=threadId||chat.thread?.id||chat.threads[0]?.id||"";
      if(wanted&&chat.threads.some((item)=>item.id===wanted))await loadThread(wanted,{renderNow:false});else{chat.thread=null;chat.messages=[];}
      chat.loaded=true;
    }catch(error){chat.error=errorText(error);}finally{chat.loading=false;render();}
  }

  async function loadThread(threadId,{renderNow=true}={}){
    const data=await rpc("fmz_phase6c_read_thread",{p_thread_id:threadId,p_limit:50,p_before_sequence:null});
    chat.thread=data.thread;chat.messages=data.messages||[];chat.retry=null;
    if(renderNow)render();
  }

  function currentConsent(){return chat.consent?.current?.ai_processing||{};}
  function consentDocument(){return (chat.consent?.contracts||[]).find((item)=>item.consent_kind==="ai_processing");}
  function denyCopy(){const reason=chat.status?.deny_reason;if(reason==="ai_entitlement_required")return text("entitlement");if(reason==="ai_age_required")return text("age");if(reason==="safety_hard_stop")return text("safety");return "";}

  function renderGate(){
    const consent=currentConsent(),doc=consentDocument(),denied=denyCopy();
    if(denied)return `<section class="p6c-gate"><h2>${esc(text("title"))}</h2><p>${esc(denied)}</p></section>`;
    if(consent.consent_state!=="granted")return `<section class="p6c-gate p6c-consent"><h2>${esc(text("consentTitle"))}</h2><div class="p6c-consent-copy">${esc(doc?.content_text||"")}</div><label class="p6c-check"><input type="checkbox" data-p6c-consent-check><span>${esc(text("consentAgree"))}</span></label><button class="primary-btn p6c-gold" type="button" data-p6c-consent="grant" disabled>${esc(text("activate"))}</button><div class="p6c-feedback" aria-live="polite">${esc(chat.notice)}</div></section>`;
    return "";
  }

  function renderThreads(){return `<aside class="p6c-list"><h2>${esc(text("conversations"))}</h2><div class="p6c-thread-list">${chat.threads.length?chat.threads.map((item)=>`<button type="button" class="secondary-btn p6c-thread ${chat.thread?.id===item.id?"active":""}" data-p6c-thread="${esc(item.id)}"><span>${esc(item.last_message||text("newChat"))}</span><small>${esc(date(item.updated_at))}${item.processing_status==="failed"?` · ${esc(text("failed"))}`:""}</small></button>`).join(""):`<p class="p6c-empty">${esc(text("empty"))}</p>`}</div></aside>`;}
  function renderMessages(){return chat.messages.length?chat.messages.map((item)=>`<article class="p6c-message ${item.message_role==='user'?'user':'assistant'}"><strong>${esc(item.message_role==='user'?text("you"):text("coach"))}</strong><p>${esc(item.content_text)}</p><time>${esc(time(item.created_at))}</time></article>`).join(""):`<p class="p6c-empty">${esc(text("emptyMessages"))}</p>`;}
  function renderChat(){
    if(!chat.thread)return `<section class="p6c-chat"><div class="p6c-empty">${esc(text("emptyMessages"))}</div></section>`;
    const canWrite=Boolean(chat.status?.chat_write_allowed);
    return `<section class="p6c-chat"><header class="p6c-chat-head"><h2>${esc(date(chat.thread.created_at)||text("today"))}</h2><button class="secondary-btn" type="button" data-p6c-delete>${esc(text("delete"))}</button></header><div class="p6c-messages" data-p6c-messages>${renderMessages()}</div>${canWrite?`<form class="p6c-composer" data-p6c-form><label class="sr-only" for="p6cMessage">${esc(text("placeholder"))}</label><textarea id="p6cMessage" maxlength="4000" enterkeyhint="send" autocomplete="off" placeholder="${esc(text("placeholder"))}" ${chat.pending?"disabled":""}>${esc(chat.draft)}</textarea><div class="p6c-composer-row"><button class="primary-btn p6c-gold" type="submit" ${chat.pending?"disabled":""}>${esc(chat.pending?text("sending"):chat.retry?text("retry"):text("send"))}</button></div><div class="p6c-feedback ${chat.error?"error":""}" aria-live="polite">${esc(chat.pending?text("sending"):chat.error||chat.notice)}</div></form>`:""}</section>`;
  }

  function render(){
    installStyles();ensureNav();const target=document.getElementById("ai-coach");if(!target)return;target.classList.add("phase6c-active");
    if(!isLoggedIn()||state.ui.role!=="client"){target.innerHTML="";return;}
    const gate=renderGate();
    const layout=`<div class="p6c-layout">${renderThreads()}${renderChat()}</div>`;
    target.innerHTML=`<div class="p6c-shell"><header class="p6c-head"><div><h1>${esc(text("title"))}</h1><p class="muted">${esc(text("intro"))}</p></div><span class="status">${esc(text("testOnly"))}</span></header><div class="p6c-mode">${esc(text("mock"))}</div>${chat.status?.grace_deadline?`<div class="p6c-retention">${esc(format("grace",{date:date(chat.status.grace_deadline)}))}</div>`:""}<div class="p6c-toolbar"><button class="primary-btn p6c-gold" type="button" data-p6c-new ${!chat.status?.chat_write_allowed||chat.pending?"disabled":""}>${esc(text("newChat"))}</button><button class="secondary-btn" type="button" data-p6c-export>${esc(text("export"))}</button>${currentConsent().consent_state==="granted"?`<button class="secondary-btn" type="button" data-p6c-consent="withdraw">${esc(text("withdraw"))}</button>`:""}</div>${chat.loading?`<p class="p6c-empty" aria-live="polite">${esc(text("loading"))}</p>`:chat.error&&!chat.loaded?`<section class="p6c-gate"><p>${esc(chat.error)}</p><button class="secondary-btn" data-p6c-retry>${esc(text("retry"))}</button></section>`:gate?`${gate}${chat.threads.length?layout:""}`:layout}</div>`;
    requestAnimationFrame(()=>{const timeline=target.querySelector("[data-p6c-messages]");if(timeline)timeline.scrollTop=timeline.scrollHeight;});
  }

  async function recordConsent(action){
    if(chat.pending)return;const doc=consentDocument();if(!doc)return;chat.pending=true;chat.error="";render();
    try{await rpc("fmz_phase6a_record_consent",{p_consent_kind:"ai_processing",p_action:action,p_document_version:doc.document_version,p_locale:lang(),p_explicit_confirmation:true,p_request_id:uuid()});chat.notice=text(action==="granted"?"consentSaved":"consentWithdrawn");chat.loaded=false;await hydrate({force:true});}catch(error){chat.error=errorText(error);}finally{chat.pending=false;render();}
  }
  async function newThread(){
    if(chat.pending)return;chat.pending=true;chat.error="";render();const threadId=uuid();
    try{await rpc("fmz_phase6c_create_thread",{p_thread_id:threadId,p_locale:lang(),p_request_id:uuid()});chat.loaded=false;await hydrate({force:true,threadId});setTimeout(()=>document.getElementById("p6cMessage")?.focus(),0);}catch(error){chat.error=errorText(error);}finally{chat.pending=false;render();}
  }
  async function send(){
    if(chat.pending||!chat.thread)return;if(!navigator.onLine){chat.error=text("offline");render();return;}const content=chat.draft.trim();if(!content)return;
    const retry=chat.retry||{requestId:uuid(),attemptId:uuid(),content};chat.retry=retry;chat.pending=true;chat.error="";render();let gotResponse=false;
    try{const session=(await supabaseClient.auth.getSession()).data?.session;if(!session?.access_token)throw new Error("auth_required");const response=await fetch(`${FMZ_CONFIG.SUPABASE_URL}/functions/v1/youri-ai/phase6c/chat`,{method:"POST",headers:{Authorization:`Bearer ${session.access_token}`,apikey:FMZ_CONFIG.SUPABASE_ANON_KEY,"Content-Type":"application/json"},body:JSON.stringify({request_id:retry.requestId,attempt_id:retry.attemptId,thread_id:chat.thread.id,expected_revision:chat.thread.revision,locale:lang(),content:retry.content})});gotResponse=true;const payload=await response.json().catch(()=>({error:"chat_unexpected_error"}));if(!response.ok)throw new Error(payload.error||"chat_unexpected_error");chat.draft="";chat.retry=null;chat.loaded=false;await hydrate({force:true,threadId:chat.thread.id});}catch(error){if(gotResponse&& !/stale_conflict/.test(String(error?.message||"")))chat.retry={...retry,attemptId:uuid()};chat.error=errorText(error);if(/stale_conflict/.test(String(error?.message||"")))await hydrate({force:true,threadId:chat.thread.id});}finally{chat.pending=false;render();}
  }
  async function exportChat(){
    if(chat.pending)return;chat.pending=true;render();try{const data=await rpc("fmz_phase6c_export_chat",{p_request_id:uuid()});const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=`fitmetzorge-ai-chat-${new Date().toISOString().slice(0,10)}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(link.href),0);chat.notice=text("exported");}catch(error){chat.error=errorText(error);}finally{chat.pending=false;render();}
  }
  async function deleteThread(){
    if(!chat.thread||chat.pending||!window.confirm(text("deleteConfirm")))return;chat.pending=true;render();try{await rpc("fmz_phase6c_delete_thread",{p_thread_id:chat.thread.id,p_expected_revision:chat.thread.revision,p_request_id:uuid()});chat.notice=text("deleted");chat.thread=null;chat.messages=[];chat.loaded=false;await hydrate({force:true});}catch(error){chat.error=errorText(error);if(/stale/.test(chat.error))await hydrate({force:true,threadId:chat.thread?.id||""});}finally{chat.pending=false;render();}
  }

  const originalRenderAll=renderAll,originalRenderNav=renderNav;
  renderNav=function renderNavPhase6c(){ensureNav();return originalRenderNav();};
  renderAll=function renderAllPhase6c(){if(!isLoggedIn()||state.ui.role!=="client")reset();const result=originalRenderAll();if(isLoggedIn()&&state.ui.role==="client"&&currentView==="ai-coach"){render();queueMicrotask(()=>hydrate());}return result;};

  document.addEventListener("click",async(event)=>{const button=event.target.closest("button");if(!button)return;
    if(button.dataset.view==="ai-coach")queueMicrotask(()=>hydrate());
    if(button.dataset.p6cRetry!==undefined){chat.loaded=false;await hydrate({force:true});}
    if(button.dataset.p6cNew!==undefined)await newThread();
    if(button.dataset.p6cThread)await loadThread(button.dataset.p6cThread);
    if(button.dataset.p6cConsent==="grant")await recordConsent("granted");
    if(button.dataset.p6cConsent==="withdraw"&&window.confirm(text("withdrawConfirm")))await recordConsent("withdrawn");
    if(button.dataset.p6cExport!==undefined)await exportChat();
    if(button.dataset.p6cDelete!==undefined)await deleteThread();
  },true);
  document.addEventListener("change",(event)=>{if(event.target.matches("[data-p6c-consent-check]")){const button=document.querySelector('[data-p6c-consent="grant"]');if(button)button.disabled=!event.target.checked;}},true);
  document.addEventListener("input",(event)=>{if(event.target.id==="p6cMessage"){chat.draft=event.target.value;if(chat.retry?.content!==chat.draft.trim())chat.retry=null;}},true);
  document.addEventListener("submit",(event)=>{if(!event.target.matches("[data-p6c-form]"))return;event.preventDefault();event.stopImmediatePropagation();send();},true);
  window.addEventListener("online",()=>{if(currentView==="ai-coach"){chat.error="";render();}});
  window.addEventListener("offline",()=>{if(currentView==="ai-coach"){chat.error=text("offline");render();}});

  ensureNav();
  window.FMZ_PHASE6C_PRIVATE_CHAT=Object.freeze({version:VERSION,hydrate,render,reset,mockOnly:true,externalAiCalls:0,externalAiCostEur:0,mobileFirst:true,noPolling:true});
})();
