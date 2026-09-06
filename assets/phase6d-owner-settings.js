(() => {
  "use strict";
  if (window.FMZ_OWNER_SETTINGS) return;
  const AI = window.FMZ_PHASE6C_PRIVATE_CHAT;
  const avatarSource = "assets/youri-ai-avatar-3d-v3-256.webp";
  const copy = {
    settings:["Instellingen","Settings","Einstellungen"], account:["Account","Account","Konto"],
    privacy:["Privacy en gegevens","Privacy and data","Datenschutz und Daten"], time:["Tijd en datum","Time and date","Zeit und Datum"],
    language:["Taal","Language","Sprache"], ai:["AI","AI","KI"], subscription:["Abonnement","Subscription","Abonnement"],
    legal:["Juridisch","Legal","Rechtliches"], close:["Sluiten","Close","Schliessen"], save:["Opslaan","Save","Speichern"],
    saved:["Opgeslagen","Saved","Gespeichert"], loading:["Laden...","Loading...","Wird geladen..."],
    error:["Opslaan of laden is niet gelukt. Probeer opnieuw.","Could not save or load. Please try again.","Speichern oder Laden fehlgeschlagen. Bitte erneut versuchen."],
    stale:["Dit is elders gewijzigd. De actuele waarden zijn geladen; controleer ze opnieuw.","Changed elsewhere. Current values have been loaded; please review them.","Andernorts geaendert. Aktuelle Werte wurden geladen; bitte erneut pruefen."],
    retry:["Opnieuw laden","Reload","Neu laden"], name:["Naam","Name","Name"], country:["Land","Country","Land"],
    email:["E-mailadres","Email address","E-Mail-Adresse"], logout:["Uitloggen","Sign out","Abmelden"],
    password:["Wachtwoord wijzigen","Change password","Passwort aendern"], currentPassword:["Huidig wachtwoord","Current password","Aktuelles Passwort"],
    newPassword:["Nieuw wachtwoord","New password","Neues Passwort"], repeatPassword:["Herhaal nieuw wachtwoord","Repeat new password","Neues Passwort wiederholen"],
    passwordMismatch:["Gebruik minimaal 12 tekens en twee gelijke nieuwe wachtwoorden.","Use at least 12 characters and two matching new passwords.","Mindestens 12 Zeichen und zwei gleiche neue Passwoerter verwenden."],
    passwordFailed:["Wachtwoord niet gewijzigd. Controleer je huidige wachtwoord.","Password unchanged. Check your current password.","Passwort unveraendert. Aktuelles Passwort pruefen."],
    nonce:["Bevestigingscode","Confirmation code","Bestaetigungscode"], sendCode:["Bevestigingscode aanvragen","Request confirmation code","Bestaetigungscode anfordern"],
    codeSent:["Controleer je e-mail voor de beveiligingscode.","Check your email for the security code.","Pruefe deine E-Mail auf den Sicherheitscode."],
    passwordSaved:["Wachtwoord gewijzigd. Log opnieuw in.","Password changed. Sign in again.","Passwort geaendert. Erneut anmelden."],
    passwordSessionFailed:["Wachtwoord gewijzigd, maar niet alle sessies konden worden afgemeld. Probeer opnieuw uit te loggen.","Password changed, but not all sessions could be signed out. Try signing out again.","Passwort geaendert, aber nicht alle Sitzungen konnten abgemeldet werden. Erneut abmelden."],
    dateFormat:["Datumweergave","Date format","Datumsformat"], localDate:["Volgens taal","Language default","Nach Sprache"],
    dayFirst:["Dag-maand-jaar","Day-month-year","Tag-Monat-Jahr"], hourCycle:["Tijdweergave","Time format","Zeitformat"],
    hours12:["12 uur","12 hours","12 Stunden"], hours24:["24 uur","24 hours","24 Stunden"],
    timezone:["Tijdzone","Timezone","Zeitzone"], daily:["Dagelijkse analyse","Daily analysis","Taegliche Analyse"],
    post:["Analyse na training","Post-workout analysis","Analyse nach Training"], weekly:["Weekanalyse","Weekly analysis","Wochenanalyse"],
    dailyTime:["Dagelijks tijdstip","Daily time","Taegliche Zeit"], weeklyDay:["Wekelijkse dag","Weekly day","Wochentag"],
    weeklyTime:["Wekelijks tijdstip","Weekly time","Woechentliche Zeit"], change:["Wijzigen","Change","Aendern"],
    schedule:["Analyseplanning","Analysis schedule","Analyseplanung"], active:["Actief","Active","Aktiv"],
    inactive:["Inactief","Inactive","Inaktiv"], expired:["Verlopen","Expired","Abgelaufen"],
    missing:["Nog niet gegeven","Not yet given","Noch nicht erteilt"], withdrawn:["Ingetrokken","Withdrawn","Widerrufen"],
    granted:["Gegeven","Granted","Erteilt"], version:["Versie","Version","Version"], date:["Datum","Date","Datum"],
    ai_processing:["FitMetZorge AI Coach-toestemming","FitMetZorge AI Coach consent","FitMetZorge AI Coach-Einwilligung"],
    private_chat:["Prive-AI-chattoestemming","Private AI chat consent","Einwilligung fuer privaten KI-Chat"],
    ai_analysis:["Automatische AI-analysetoestemming","Automatic AI analysis consent","Einwilligung fuer automatische KI-Analysen"],
    trainer_summary_sharing:["Trainer-summary-toestemming","Trainer summary consent","Einwilligung fuer Trainerzusammenfassungen"],
    consentConfirm:["Ik geef expliciet toestemming voor het bovenstaande doel.","I explicitly consent to the purpose above.","Ich willige ausdruecklich in den oben genannten Zweck ein."],
    giveConsent:["Toestemming geven","Give consent","Einwilligen"], withdraw:["Toestemming intrekken","Withdraw consent","Einwilligung widerrufen"],
    withdrawConfirm:["Deze toestemming intrekken?","Withdraw this consent?","Diese Einwilligung widerrufen?"],
    chatData:["AI-chatgegevens","AI chat data","KI-Chatdaten"], history:["Analysegeschiedenis","Analysis history","Analyseverlauf"],
    exportChat:["AI-chat exporteren","Export AI chat","KI-Chat exportieren"], exportAnalysis:["Analyses exporteren","Export analyses","Analysen exportieren"],
    deleteChat:["Gesprek verwijderen","Delete conversation","Gespraech loeschen"], deleteAnalysis:["Analyse verwijderen","Delete analysis","Analyse loeschen"],
    deleteConfirm:["Deze inhoud definitief verwijderen?","Permanently delete this content?","Diesen Inhalt endgueltig loeschen?"],
    empty:["Nog geen gegevens.","No data yet.","Noch keine Daten."], retention:["Bewaartermijnen","Retention","Aufbewahrung"],
    retentionCopy:["Analyseresultaten worden maximaal 90 dagen bewaard; geminimaliseerde analyse-auditmetadata maximaal 180 dagen. Chat heeft na verlopen AI-toegang een leesperiode van 90 dagen. Actieve safety-auditmetadata blijft voor de veiligheidscontrole beschikbaar.",
      "Analysis results are retained for up to 90 days; minimized analysis audit metadata for up to 180 days. After AI access expires, chat has a 90-day reading period. Active safety audit metadata remains available for safety checks.",
      "Analyseergebnisse werden bis zu 90 Tage gespeichert; minimierte Analyse-Auditdaten bis zu 180 Tage. Nach Ablauf des KI-Zugangs bleibt der Chat 90 Tage lesbar. Aktive Safety-Auditdaten bleiben fuer Sicherheitspruefungen verfuegbar."],
    deleteAccount:["Account verwijderen","Delete account","Konto loeschen"],
    deletionGate:["Accountverwijdering is nog niet beschikbaar. De beveiligde controle van identiteit, sessies en bewaarplichten moet eerst zijn afgerond.",
      "Account deletion is not available yet. Secure identity checks, session revocation and retention requirements must be completed first.",
      "Kontoloeschung ist noch nicht verfuegbar. Sichere Identitaetspruefung, Sitzungswiderruf und Aufbewahrungspflichten muessen zuerst geklaert sein."],
    showAvatar:["Zwevende Youri AI-avatar tonen","Show floating Youri AI avatar","Schwebenden Youri AI-Avatar anzeigen"],
    resetAvatar:["Avatarpositie herstellen","Reset avatar position","Avatarposition zuruecksetzen"], openAI:["Open Youri AI","Open Youri AI","Youri AI oeffnen"],
    plan:["Huidig plan","Current plan","Aktueller Tarif"], status:["Status","Status","Status"], start:["Begindatum","Start date","Startdatum"],
    end:["Eind- / verlengdatum","End / renewal date","End- / Verlaengerungsdatum"], unknown:["Niet vastgelegd","Not recorded","Nicht erfasst"],
    trial:["Trialstatus","Trial status","Teststatus"], trialActive:["Proefperiode","Trial","Testphase"],
    billingGate:["Abonnement wijzigen, opzeggen, maand/jaar kiezen, betaalgegevens en facturen komen beschikbaar in abonnementsbeheer. Hier wordt nog geen betaling of wijziging uitgevoerd.",
      "Plan changes, cancellation, monthly/annual billing, payment details and invoices will be available in subscription management. No payment or plan change is performed here.",
      "Tarifwechsel, Kuendigung, Monats-/Jahresabrechnung, Zahlungsdaten und Rechnungen werden in der Aboverwaltung verfuegbar. Hier erfolgt noch keine Zahlung oder Tarifaenderung."],
    terms:["Algemene voorwaarden","Terms and conditions","Allgemeine Geschaeftsbedingungen"],
    privacyDoc:["Privacyverklaring","Privacy notice","Datenschutzerklaerung"], aiTerms:["AI-voorwaarden en toestemming","AI terms and consent","KI-Bedingungen und Einwilligung"],
    draft:["Concept - niet juridisch goedgekeurd","Draft - not legally approved","Entwurf - nicht rechtlich freigegeben"],
    draftCopy:["Een goedgekeurde algemene tekst is nog niet vastgesteld. Versie: staging-draft-20260906. Dit concept geldt niet als juridische goedkeuring of als vervanging van je gegeven toestemmingen.",
      "An approved general document has not yet been established. Version: staging-draft-20260906. This draft is not legal approval and does not replace your recorded consents.",
      "Ein freigegebenes allgemeines Dokument liegt noch nicht vor. Version: staging-draft-20260906. Dieser Entwurf ist keine rechtliche Freigabe und ersetzt keine erteilten Einwilligungen."],
    stop:["Analyse tijdelijk gestopt","Analysis temporarily paused","Analyse voruebergehend gestoppt"],
    stopWhy:["Een eerder ernstig of onduidelijk gezondheidssignaal vraagt om een controle van je actuele status.",
      "An earlier serious or unclear health signal requires a check of your current status.",
      "Ein frueheres ernstes oder unklares Gesundheitssignal erfordert eine Pruefung deines aktuellen Zustands."],
    medical:["FitMetZorge stelt geen diagnose. Stop bij actuele of terugkerende ernstige klachten en zoek professionele beoordeling. Schakel bij acuut gevaar spoedhulp in.",
      "FitMetZorge does not diagnose. Stop and seek professional assessment for current or recurring serious symptoms. In an emergency, seek urgent help.",
      "FitMetZorge stellt keine Diagnose. Bei aktuellen oder wiederkehrenden ernsten Beschwerden stoppen und medizinische Hilfe suchen. Im Notfall sofort Hilfe holen."],
    checkStatus:["Controleer mijn status","Check my status","Meinen Status pruefen"],
    symptomsResolved:["Mijn klachten zijn voorbij","My symptoms have resolved","Meine Beschwerden sind vorbei"],
    misunderstood:["Dit werd verkeerd begrepen","This was misunderstood","Dies wurde missverstanden"],
    checkOne:["Ik heb de genoemde klachten nu niet meer.","I no longer have the symptoms mentioned.","Ich habe die genannten Beschwerden jetzt nicht mehr."],
    checkTwo:["Ik ervaar momenteel geen pijn op/in de borst, ernstige duizeligheid, benauwdheid, flauwvallen of ander ernstig signaal.",
      "I currently have no chest pain, severe dizziness, shortness of breath, fainting or other serious warning sign.",
      "Ich habe aktuell keine Brustschmerzen, starken Schwindel, Atemnot, Ohnmacht oder andere ernste Warnzeichen."],
    checkThree:["Ik begrijp dat ik bij terugkerende of ernstige klachten moet stoppen en professionele of acute hulp moet inschakelen.",
      "I understand that I must stop and seek professional or urgent help for recurring or serious symptoms.",
      "Ich verstehe, dass ich bei wiederkehrenden oder ernsten Beschwerden stoppen und professionelle oder akute Hilfe suchen muss."],
    confirmRecovery:["Bevestigen en status controleren","Confirm and check status","Bestaetigen und Status pruefen"],
    recovered:["Je actuele status is opgeslagen. Nieuwe analyses zijn weer beschikbaar zodra de overige voorwaarden zijn vervuld.",
      "Your current status is saved. New analyses are available when the other requirements are met.",
      "Dein aktueller Status ist gespeichert. Neue Analysen sind verfuegbar, sobald die weiteren Voraussetzungen erfuellt sind."],
    recoveryNotNeeded:["Er is geen tijdelijke analyseblokkade.","There is no temporary analysis block.","Es besteht keine voruebergehende Analysesperre."],
    remainBlocked:["Bevestig alle drie alleen wanneer ze voor jou kloppen. Anders blijft de analyse gestopt.",
      "Confirm all three only if they are true for you. Otherwise the analysis stays paused.",
      "Bestaetige alle drei Aussagen nur, wenn sie fuer dich zutreffen. Sonst bleibt die Analyse gestoppt."],
    entitlement:["Youri AI is beschikbaar met een actief AI- of personal-coachingplan. Bekijk je huidige abonnement in Instellingen.",
      "Youri AI is available with an active AI or personal coaching plan. View your current plan in Settings.",
      "Youri AI ist mit einem aktiven KI- oder Personal-Coaching-Tarif verfuegbar. Deinen Tarif findest du in den Einstellungen."]
  };
  const sections = ["account","privacy","time","language","ai","subscription","legal"];
  const languages = ["nl","en","de"];
  const languageNames = ["Nederlands","English","Deutsch"];
  let ownerId = "", data = null, loading = null, epoch = 0, section = "account";
  let message = "", error = "", busy = false, dirty = false, settingsDialog = null, chatDialog = null, recoveryDialog = null;
  let chatMarker = null, chatOrigin = null, settingsOpener = null, chatOpener = null, recoveryRevision = null, recoveryReason = "reassessment", routedUser = "";
  let drag = null, avatarDraft = null, ignoreClickUntil = 0, positionQueue = Promise.resolve(), languageOpen = false;
  const esc = value => String(value == null ? "" : value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const lang = () => languages.includes(state.accountSettings?.language) ? state.accountSettings.language : "nl";
  const t = key => copy[key]?.[languages.indexOf(lang())] || copy[key]?.[0] || key;
  const uid = () => isLoggedIn() ? onlineProfile?.id || "" : "";
  const member = () => onlineProfile?.role === "client";
  const uuid = () => crypto.randomUUID();
  const locale = () => ({nl:"nl-NL",en:"en-GB",de:"de-DE"})[lang()];
  const formatDate = value => {
    if (!value) return t("unknown");
    const date = new Date(value);
    if (data?.display?.date_format === "iso") return date.toISOString().slice(0,10);
    return date.toLocaleDateString(data?.display?.date_format === "day_first" ? "en-GB" : locale());
  };
  const icon = name => '<img src="assets/vendor/lucide-' + name + '.svg" alt="" width="22" height="22">';
  const button = (label,attrs,style="secondary-btn") => '<button type="button" class="' + style + '" ' + attrs + '>' + esc(label) + '</button>';
  const field = (label,html) => '<label class="fmz-field"><span>' + esc(label) + '</span>' + html + '</label>';
  const input = (name,value,attrs="") => '<input name="' + name + '" value="' + esc(value) + '" ' + attrs + '>';
  const options = (list,value) => list.map(([id,label]) => '<option value="' + esc(id) + '"' + (String(value)===String(id)?' selected':'') + '>' + esc(label) + '</option>').join("");
  const select = (name,list,value) => '<select name="' + name + '">' + options(list,value) + '</select>';
  const row = (label,value) => '<div class="fmz-value-row"><dt>' + esc(label) + '</dt><dd>' + esc(value) + '</dd></div>';
  async function rpc(name,args={}) {
    const result = await supabaseClient.rpc(name,args);
    if (result.error) throw result.error;
    return result.data;
  }
  function applySettings(next) {
    if(!next?.profile||!next?.avatar||!next?.display||!languages.includes(next.language))throw new Error("settings_response_invalid");
    data = next;
    state.accountSettings = {...state.accountSettings,language:next.language,country:next.country,unitSystem:next.unit_system};
    document.documentElement.lang = next.language;
    syncTools();
  }
  async function hydrate(force=false) {
    const user = uid();
    if (!user) return;
    if (ownerId!==user) { ownerId=user; data=null; loading=null; epoch++; }
    if (loading) return loading;
    if (data&&!force) return data;
    const generation=epoch;
    loading=(async()=>{
      try {
        const next=await rpc("fmz_phase6d_get_member_settings");
        if (uid()!==user||epoch!==generation) return;
        const languageChanged=lang()!==next.language;
        applySettings(next);
        if(languageChanged){renderNav();renderAll();}
        if (settingsDialog&&!dirty) renderSettings();
        route();
        return next;
      } catch(e) {
        if (uid()===user) { error=t("error"); renderSettings(); }
      } finally { if(epoch===generation)loading=null; }
    })();
    return loading;
  }
  async function savePatch(patch) {
    const user=uid(),generation=epoch;
    if (!data||!user) throw new Error("settings_unavailable");
    try {
      const result=await rpc("fmz_phase6d_update_member_settings",{p_patch:patch,p_expected_revision:data.revision});
      if(uid()!==user||epoch!==generation) return;
      applySettings(result);
      return result;
    } catch(e) {
      if(/stale_conflict/.test(e.message||"")) { await hydrate(true); throw new Error("settings_stale_conflict"); }
      throw e;
    }
  }
  function notice() {
    return '<p class="fmz-feedback' + (error?' error':'') + '" role="status" aria-live="polite">' + esc(error||message) + '</p>';
  }
  function makeDialog(id,label) {
    const element=document.createElement("dialog");
    element.id=id; element.className="fmz-dialog"; element.setAttribute("aria-label",label);
    document.body.appendChild(element);
    element.addEventListener("cancel",event=>{event.preventDefault();closeTop();});
    return element;
  }
  function modalState() {
    document.body.classList.toggle("fmz-modal-open",Boolean(settingsDialog||chatDialog||recoveryDialog));
    syncTools();
  }
  function closeSettings() {
    if(!settingsDialog)return;
    settingsDialog.close();settingsDialog.remove();settingsDialog=null;dirty=false;
    modalState();
    (settingsOpener?.isConnected?settingsOpener:chatDialog?.querySelector('[data-fmz-settings]')||document.querySelector('#fmz-top-tools [data-fmz-settings]'))?.focus();
  }
  function closeChat() {
    if(!chatDialog)return;
    const target=document.getElementById("ai-coach");
    if(chatMarker?.parentNode)chatMarker.replaceWith(target);
    else if(chatOrigin)chatOrigin.appendChild(target);
    target.classList.toggle("active",currentView==="ai-coach");
    chatDialog.close();chatDialog.remove();chatDialog=null;chatMarker=null;
    modalState();(chatOpener?.isConnected?chatOpener:document.getElementById("fmz-avatar"))?.focus();
  }
  function closeRecovery() {
    if(!recoveryDialog)return;
    recoveryDialog.close();recoveryDialog.remove();recoveryDialog=null;modalState();
    (settingsDialog||chatDialog)?.querySelector("button")?.focus();
  }
  function closeTop() {
    if(recoveryDialog)closeRecovery();else if(settingsDialog)closeSettings();else closeChat();
  }
  async function openSettings(next="account") {
    if(!uid())return;
    if(!settingsDialog)settingsOpener=document.activeElement;
    section=sections.includes(next)?next:"account";message="";error="";dirty=false;
    if(!settingsDialog)settingsDialog=makeDialog("fmz-settings",t("settings"));
    renderSettings();if(!settingsDialog.open)settingsDialog.showModal();modalState();
    await hydrate();
    if(member())await AI.hydrate({force:true});
    renderSettings();
    settingsDialog?.querySelector('[data-fmz-section="'+section+'"]')?.focus();
  }
  async function openChat() {
    if(!uid()||!member())return;
    if(chatDialog){chatDialog.focus();return;}
    chatOpener=document.activeElement;
    const target=document.getElementById("ai-coach");
    if(!target)return;
    chatOrigin=target.parentNode;chatMarker=document.createComment("youri-ai-route");target.before(chatMarker);
    chatDialog=makeDialog("fmz-youri-chat","Youri AI");
    chatDialog.classList.add("fmz-chat-dialog");
    chatDialog.innerHTML='<div class="fmz-chat-close"><button type="button" class="fmz-icon" data-fmz-settings="ai" aria-label="'+esc(t("settings"))+'" title="'+esc(t("settings"))+'">'+icon("settings")+'</button>'+
      '<button type="button" class="fmz-icon" data-fmz-close aria-label="'+esc(t("close"))+'" title="'+esc(t("close"))+'">'+icon("x")+'</button></div>';
    chatDialog.appendChild(target);target.classList.add("active");
    chatDialog.showModal();modalState();
    await AI.hydrate({force:true});
    if(!chatDialog||!uid())return;
    AI.selectTab("chat");
    if(AI.snapshot().status?.chat_write_allowed&&!AI.snapshot().thread)await AI.newThread();
    (chatDialog.querySelector("#p6cMessage")||chatDialog.querySelector("button"))?.focus();
  }
  function languageControl(name="language") {
    return select(name,languages.map((id,i)=>[id,languageNames[i]]),data?.language||lang());
  }
  function accountSection() {
    return '<form data-fmz-form="account" class="fmz-form">'+
      field(t("name"),input("name",data.profile.name,'maxlength="120" required autocomplete="name"'))+
      field(t("email"),input("email",data.profile.email,'type="email" readonly autocomplete="email"'))+
      field(t("country"),input("country",data.country,'maxlength="80" required autocomplete="country-name"'))+
      '<button class="primary-btn" type="submit">'+esc(t("save"))+'</button></form>'+
      '<details class="fmz-disclosure"><summary>'+esc(t("password"))+'</summary><form data-fmz-form="password" class="fmz-form">'+
      field(t("currentPassword"),input("current_password","","type=\"password\" required autocomplete=\"current-password\""))+
      field(t("newPassword"),input("password","","type=\"password\" minlength=\"12\" required autocomplete=\"new-password\""))+
      field(t("repeatPassword"),input("repeat","","type=\"password\" minlength=\"12\" required autocomplete=\"new-password\""))+
      field(t("nonce"),input("nonce","","autocomplete=\"one-time-code\""))+
      button(t("sendCode"),"data-fmz-code")+'<button type="submit" class="primary-btn">'+esc(t("password"))+'</button></form></details>'+
      button(t("logout"),"data-fmz-logout");
  }
  function weekdays() {
    const monday=new Date("2026-09-07T12:00:00Z");
    return Array.from({length:7},(_,i)=>[i+1,new Date(monday.getTime()+i*86400000).toLocaleDateString(locale(),{weekday:"long",timeZone:"UTC"})]);
  }
  function analysisPreferences() {return AI.snapshot().analysisStatus?.preferences||data?.analysis_preferences;}
  function scheduleForm() {
    const pref=analysisPreferences();
    if(!pref)return '<p>'+esc(t("loading"))+'</p>';
    const zones=[...new Set([pref.timezone_name,"Europe/Amsterdam","Europe/Berlin","Europe/London","UTC",...(Intl.supportedValuesOf?.("timeZone")||[])])];
    return '<form data-fmz-form="schedule" class="fmz-form"><div class="fmz-field-grid">'+
      field(t("timezone"),select("timezone_name",zones.map(z=>[z,z]),pref.timezone_name))+
      field(t("dailyTime"),input("daily_time",pref.daily_time,'type="time" step="60" required'))+
      field(t("weeklyDay"),select("weekly_day",weekdays(),pref.weekly_day))+
      field(t("weeklyTime"),input("weekly_time",pref.weekly_time,'type="time" step="60" required'))+'</div>'+
      [["daily_enabled","daily"],["post_workout_enabled","post"],["weekly_enabled","weekly"]].map(([name,label])=>
        '<label class="fmz-check"><input type="checkbox" name="'+name+'" '+(pref[name]?'checked':'')+'>'+esc(t(label))+'</label>').join("")+
      '<button type="submit" class="primary-btn">'+esc(t("save"))+'</button></form>';
  }
  function timeSection() {
    return '<form data-fmz-form="display" class="fmz-form"><div class="fmz-field-grid">'+
      field(t("dateFormat"),select("date_format",[["locale",t("localDate")],["day_first",t("dayFirst")],["iso","ISO 8601"]],data.display.date_format))+
      field(t("hourCycle"),select("hour_cycle",[["24",t("hours24")],["12",t("hours12")]],data.display.hour_cycle))+
      '</div><button type="submit" class="primary-btn">'+esc(t("save"))+'</button></form>'+
      (member()?'<h3>'+esc(t("schedule"))+'</h3>'+scheduleForm():"");
  }
  function consentSections() {
    const snapshot=AI.snapshot(),contracts=[...(snapshot.consent?.contracts||[]),...(snapshot.analysisConsent?.contracts||[])];
    const current={...snapshot.consent?.current,...snapshot.analysisConsent?.current};
    const kinds=["ai_processing","private_chat","ai_analysis"];
    if(data.profile.trainer_linked)kinds.push("trainer_summary_sharing");
    return kinds.map(kind=>{
      const doc=contracts.find(d=>d.consent_kind===kind),status=current[kind]||{consent_state:"missing"};
      return '<details class="fmz-disclosure" data-fmz-consent-block="'+kind+'"><summary><span>'+esc(t(kind))+'</span><small>'+esc(t(status.consent_state))+'</small></summary>'+
        '<dl>'+row(t("version"),status.document_version||doc?.document_version||t("unknown"))+row(t("date"),formatDate(status.consented_at))+'</dl>'+
        '<p class="fmz-consent-text">'+esc(doc?.content_text||t("loading"))+'</p>'+
        (doc?status.consent_state==="granted"?button(t("withdraw"),'data-fmz-consent="'+kind+'" data-action="withdrawn"'):
          '<label class="fmz-check"><input type="checkbox" data-fmz-consent-check="'+kind+'">'+esc(t("consentConfirm"))+'</label>'+
          '<button type="button" class="primary-btn" data-fmz-consent="'+kind+'" data-action="granted" disabled>'+esc(t("giveConsent"))+'</button>':"")+'</details>';
    }).join("");
  }
  function chatData() {
    const threads=AI.snapshot().threads||[];
    return '<h3>'+esc(t("chatData"))+'</h3>'+button(t("exportChat"),"data-fmz-export=\"chat\"")+
      '<ul class="fmz-data-list">'+(threads.length?threads.map(item=>'<li><span>'+esc(formatDate(item.created_at))+'</span>'+
        button(t("deleteChat"),'data-fmz-delete-thread="'+esc(item.id)+'" data-revision="'+item.revision+'"')+'</li>').join(""):'<li>'+esc(t("empty"))+'</li>')+'</ul>';
  }
  function analysisData() {
    const results=(AI.snapshot().analyses||[]).filter(item=>item.status!=="deleted");
    return '<h3>'+esc(t("history"))+'</h3>'+button(t("exportAnalysis"),'data-fmz-export="analyses"')+
      '<ul class="fmz-data-list">'+(results.length?results.map(item=>'<li><span>'+esc(t(item.analysis_kind==="post_workout"?"post":item.analysis_kind))+
        ' - '+esc(formatDate(item.created_at))+'</span>'+button(t("deleteAnalysis"),'data-fmz-delete-analysis="'+esc(item.id)+'" data-revision="'+item.revision+'"')+'</li>').join(""):'<li>'+esc(t("empty"))+'</li>')+'</ul>';
  }
  function avatarSettings() {
    return '<h3>Youri AI</h3><label class="fmz-check"><input type="checkbox" data-fmz-avatar-visible '+(data.avatar.visible?'checked':'')+'>'+esc(t("showAvatar"))+'</label>'+
      button(t("resetAvatar"),"data-fmz-avatar-reset");
  }
  function privacySection() {
    return (member()?consentSections()+chatData()+analysisData():"")+
      '<h3>'+esc(t("retention"))+'</h3><p>'+esc(t("retentionCopy"))+'</p><h3>'+esc(t("deleteAccount"))+'</h3><p>'+esc(t("deletionGate"))+'</p>';
  }
  function subscriptionSection() {
    const plan=data.subscription;
    return '<dl>'+row(t("plan"),plan.plan)+row(t("status"),t(plan.status))+row(t("trial"),plan.trial_status==="trial"?t("trialActive"):t("unknown"))+
      row(t("start"),formatDate(plan.starts_at))+row(t("end"),formatDate(plan.ends_at))+'</dl><p>'+esc(t("billingGate"))+'</p>';
  }
  function legalSection() {
    return ["terms","privacyDoc"].map(key=>'<details class="fmz-disclosure"><summary>'+esc(t(key))+'</summary><p><strong>'+esc(t("draft"))+'</strong></p><p>'+esc(t("draftCopy"))+'</p><p>2026-09-06</p></details>').join("")+
      (member()?'<h3>'+esc(t("aiTerms"))+'</h3>'+consentSections():"");
  }
  function renderSettings() {
    if(!settingsDialog)return;
    const activeId=document.activeElement?.getAttribute("data-fmz-section");
    let body='<p>'+esc(t("loading"))+'</p>';
    if(data){
      if(section==="account")body=accountSection();
      if(section==="privacy")body=privacySection();
      if(section==="time")body=timeSection();
      if(section==="language")body=field(t("language"),languageControl());
      if(section==="ai")body=member()?consentSections()+safetyPanel(AI.snapshot().analysisStatus?.recovery)+
        '<h3>'+esc(t("schedule"))+'</h3>'+scheduleForm()+avatarSettings()+chatData()+analysisData():'<p>'+esc(t("entitlement"))+'</p>';
      if(section==="subscription")body=subscriptionSection();
      if(section==="legal")body=legalSection();
    }
    settingsDialog.innerHTML='<header class="fmz-dialog-head"><h2>'+esc(t("settings"))+'</h2><button type="button" class="fmz-icon" data-fmz-close aria-label="'+esc(t("close"))+'">'+icon("x")+'</button></header>'+
      '<nav class="fmz-settings-nav" aria-label="'+esc(t("settings"))+'">'+sections.map(key=>'<button type="button" data-fmz-section="'+key+'" aria-current="'+(key===section?"page":"false")+'">'+esc(t(key))+'</button>').join("")+
      '</nav><main class="fmz-settings-content"><h2>'+esc(t(section))+'</h2>'+notice()+body+
      (error?button(t("retry"),"data-fmz-reload"):"")+'</main>';
    if(busy)settingsDialog.querySelectorAll("input,select,button").forEach(el=>{if(!el.matches("[data-fmz-close]"))el.disabled=true;});
    if(activeId)settingsDialog.querySelector('[data-fmz-section="'+activeId+'"]')?.focus();
  }
  function safetyPanel(recovery) {
    if(!recovery?.analysis_blocked)return "";
    return '<section class="fmz-safety p6d-panel wide" role="status"><h2>'+esc(t("stop"))+'</h2><p>'+esc(t("stopWhy"))+'</p><p>'+esc(t("medical"))+
      '</p><div class="fmz-actions">'+button(t("checkStatus"),'data-fmz-recovery="reassessment"',"primary-btn")+
      button(t("symptomsResolved"),'data-fmz-recovery="symptoms_resolved"')+
      button(t("misunderstood"),'data-fmz-recovery="misunderstood"')+'</div></section>';
  }
  function analysisSummary(status) {
    const pref=status?.preferences;if(!pref)return "";
    return '<section class="p6d-panel wide"><h2>'+esc(t("schedule"))+'</h2><p>'+esc(pref.timezone_name)+' / '+esc(pref.daily_time)+' / '+
      esc(weekdays().find(([day])=>Number(day)===Number(pref.weekly_day))?.[1])+' '+esc(pref.weekly_time)+'</p>'+
      button(t("change"),'data-fmz-settings="ai"')+'</section>';
  }
  async function openRecovery(reason="reassessment") {
    if(!uid()||!member())return;
    await AI.hydrate({force:true});
    const recovery=AI.snapshot().analysisStatus?.recovery;
    if(!recovery?.analysis_blocked){message=t("recoveryNotNeeded");renderSettings();return;}
    recoveryRevision=recovery.safety_revision;recoveryReason=["symptoms_resolved","misunderstood","reassessment"].includes(reason)?reason:"reassessment";
    if(!recoveryDialog)recoveryDialog=makeDialog("fmz-safety-recovery",t("checkStatus"));
    recoveryDialog.classList.add("fmz-recovery-dialog");
    recoveryDialog.innerHTML='<header class="fmz-dialog-head"><h2>'+esc(t("checkStatus"))+'</h2><button type="button" class="fmz-icon" data-fmz-close aria-label="'+esc(t("close"))+'">'+icon("x")+'</button></header>'+
      '<div class="fmz-settings-content"><p>'+esc(t("medical"))+'</p><p>'+esc(t("remainBlocked"))+'</p><form data-fmz-form="recovery" class="fmz-form">'+
      ["checkOne","checkTwo","checkThree"].map((key,i)=>'<label class="fmz-check"><input type="checkbox" name="confirm'+i+'" required>'+esc(t(key))+'</label>').join("")+
      '<button type="submit" class="primary-btn" disabled>'+esc(t("confirmRecovery"))+'</button><p class="fmz-feedback" role="status"></p></form></div>';
    if(!recoveryDialog.open)recoveryDialog.showModal();modalState();recoveryDialog.querySelector("input")?.focus();
  }
  function unsafeSurface() {
    return !uid()||document.fullscreenElement||[...document.querySelectorAll('dialog[open]:not(.fmz-dialog),[aria-modal="true"]:not(.fmz-dialog),.phase4-s3-camera,.phase3-focus-overlay')].some(node=>node.getClientRects().length&&!node.hidden)||
      [...document.body.classList].some(c=>/^(phase3-(picker|focus|history)-open|phase4.*dialog-open|member-ux-detail-open)$/.test(c));
  }
  function avatarBounds() {
    const viewport=window.visualViewport;
    const topbar=document.querySelector(".topbar")?.getBoundingClientRect();
    const css=getComputedStyle(document.documentElement),safe=name=>parseFloat(css.getPropertyValue("--fmz-safe-"+name))||0;
    const left=(viewport?.offsetLeft||0)+12+safe("left"),top=Math.max((viewport?.offsetTop||0)+76+safe("top"),(topbar?.bottom||0)+8);
    const width=viewport?.width||innerWidth,height=viewport?.height||innerHeight;
    const nav=document.querySelector(".sidebar")?.getBoundingClientRect();
    const bottom=Math.min((viewport?.offsetTop||0)+height-76-safe("bottom"),nav&&nav.top>top?nav.top-74:Infinity);
    return {left,right:Math.max(left,(viewport?.offsetLeft||0)+width-72-safe("right")),top,bottom:Math.max(top,bottom)};
  }
  function placeAvatar() {
    const node=document.getElementById("fmz-avatar");if(!node||drag)return;
    const bounds=avatarBounds(),pref=avatarDraft||data?.avatar||{side:"right",y:.72};
    const y=Number.isFinite(Number(pref.y))?Math.min(1,Math.max(0,Number(pref.y))):.72;
    node.style.left=(pref.side==="left"?bounds.left:bounds.right)+"px";
    node.style.top=(bounds.top+(bounds.bottom-bounds.top)*y)+"px";
  }
  function syncTools() {
    const allowed=Boolean(uid());
    let tools=document.getElementById("fmz-top-tools");
    if(!tools){
      const host=document.querySelector(".topbar-controls");if(!host)return;
      tools=document.createElement("div");tools.id="fmz-top-tools";host.appendChild(tools);
    }
    tools.hidden=!allowed;
    tools.innerHTML='<button type="button" class="fmz-icon" data-fmz-settings="account" aria-label="'+esc(t("settings"))+'" title="'+esc(t("settings"))+'">'+icon("settings")+'</button>'+
      '<div class="fmz-language-wrap"><button type="button" class="fmz-icon fmz-language-button" data-fmz-language-toggle aria-label="'+esc(t("language"))+'" aria-expanded="'+languageOpen+'" title="'+esc(t("language"))+'">'+icon("globe")+'<span>'+lang().toUpperCase()+'</span></button>'+
      (languageOpen?'<div class="fmz-language-menu">'+languages.map((id,i)=>'<button type="button" data-fmz-language="'+id+'" aria-pressed="'+(lang()===id)+'">'+languageNames[i]+'</button>').join("")+'</div>':"")+'</div>';
    let avatar=document.getElementById("fmz-avatar");
    if(!avatar){
      avatar=document.createElement("button");avatar.id="fmz-avatar";avatar.type="button";
      avatar.innerHTML='<img src="'+avatarSource+'" alt="" width="256" height="256" draggable="false">';
      document.body.appendChild(avatar);
      avatar.addEventListener("pointerdown",startDrag);
      avatar.addEventListener("pointermove",moveDrag);
      avatar.addEventListener("pointerup",endDrag);
      avatar.addEventListener("pointercancel",cancelDrag);
      avatar.addEventListener("click",()=>{if(performance.now()>=ignoreClickUntil)openChat();});
      avatar.addEventListener("keydown",event=>{
        if(!data||!["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(event.key))return;
        event.preventDefault();
        const pref=avatarDraft||data.avatar;
        queueAvatar({avatar_side:event.key==="ArrowLeft"?"left":event.key==="ArrowRight"?"right":pref.side,
          avatar_y:Math.min(1,Math.max(0,Number(pref.y)+(event.key==="ArrowUp"?-.08:event.key==="ArrowDown"?.08:0)))});
      });
    }
    avatar.setAttribute("aria-label",t("openAI"));avatar.title=t("openAI");
    avatar.hidden=!allowed||!member()||!data||data.avatar.visible===false||Boolean(settingsDialog||chatDialog||recoveryDialog)||Boolean(unsafeSurface());
    document.querySelectorAll('#nav [data-view="ai-coach"]').forEach(node=>node.remove());
    placeAvatar();
  }
  function startDrag(event) {
    if(event.button!==0||!event.isPrimary)return;
    const rect=event.currentTarget.getBoundingClientRect();
    drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:rect.left,top:rect.top,moved:false,user:uid()};
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function moveDrag(event) {
    if(!drag||drag.id!==event.pointerId)return;
    const dx=event.clientX-drag.x,dy=event.clientY-drag.y;
    if(Math.hypot(dx,dy)>7)drag.moved=true;
    if(!drag.moved)return;
    const bounds=avatarBounds();
    event.currentTarget.style.left=Math.min(bounds.right,Math.max(bounds.left,drag.left+dx))+"px";
    event.currentTarget.style.top=Math.min(bounds.bottom,Math.max(bounds.top,drag.top+dy))+"px";
  }
  function endDrag(event) {
    if(!drag||drag.id!==event.pointerId)return;
    const moved=drag.moved,user=drag.user;drag=null;
    if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);
    if(!moved)return;
    ignoreClickUntil=performance.now()+500;
    const bounds=avatarBounds(),rect=event.currentTarget.getBoundingClientRect();
    const patch={avatar_side:rect.left<(bounds.left+bounds.right)/2?"left":"right",avatar_y:Math.max(0,Math.min(1,(rect.top-bounds.top)/Math.max(1,bounds.bottom-bounds.top)))};
    if(uid()===user)queueAvatar(patch);
  }
  function queueAvatar(patch) {
    const user=uid(),generation=epoch,draft={...data.avatar,side:patch.avatar_side,y:patch.avatar_y};
    avatarDraft=draft;placeAvatar();
    positionQueue=positionQueue.catch(()=>{}).then(async()=>{
      if(uid()===user&&epoch===generation)await savePatch(patch);
    }).catch(()=>{error=t("error");}).finally(()=>{
      if(avatarDraft===draft){avatarDraft=null;placeAvatar();}
    });
  }
  function cancelDrag(){drag=null;ignoreClickUntil=performance.now()+500;placeAvatar();}
  async function mutate(action) {
    if(busy)return;busy=true;message="";error="";
    try {await action();if(!message)message=t("saved");dirty=false;}
    catch(e){
      const stale=/stale_conflict/.test(e.message||"");
      if(stale){dirty=false;await hydrate(true);if(member())await AI.hydrate({force:true});}
      error=stale?t("stale"):t("error");
    }
    finally{busy=false;renderSettings();syncTools();}
  }
  async function setLanguage(language) {
    if(!languages.includes(language))return;
    languageOpen=false;
    await mutate(async()=>{
      await savePatch({language});
      renderNav();renderAll();
      if(member())await AI.hydrate({force:true});
    });
  }
  async function saveSchedule(form) {
    const values=new FormData(form),pref=analysisPreferences();
    const args={p_timezone_name:values.get("timezone_name"),p_daily_time:values.get("daily_time"),
      p_weekly_day:Number(values.get("weekly_day")),p_weekly_time:values.get("weekly_time"),
      p_daily_enabled:values.has("daily_enabled"),p_post_workout_enabled:values.has("post_workout_enabled"),
      p_weekly_enabled:values.has("weekly_enabled"),p_expected_revision:Number(pref.revision),p_request_id:uuid()};
    await mutate(async()=>{
      const saved=await rpc("fmz_phase6d_update_preferences",args);
      if(data)data.analysis_preferences=saved;
      if(AI.snapshot().analysisStatus)AI.snapshot().analysisStatus.preferences=saved;
      await AI.hydrate({force:true});
    });
  }
  async function changePassword(form) {
    const values=new FormData(form),password=String(values.get("password")||"");
    if(password.length<12||password!==values.get("repeat")){error=t("passwordMismatch");renderSettings();return;}
    if(busy)return;busy=true;let passwordChanged=false;
    try {
      const verifier=window.supabase.createClient(FMZ_CONFIG.SUPABASE_URL,FMZ_CONFIG.SUPABASE_ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false}});
      const verification=await verifier.auth.signInWithPassword({email:data.profile.email,password:String(values.get("current_password")||"")});
      if(verification.error)throw verification.error;
      const revokeVerification=await verifier.auth.signOut({scope:"local"});
      if(revokeVerification.error)throw revokeVerification.error;
      const result=await supabaseClient.auth.updateUser({password,current_password:String(values.get("current_password")||""),...(values.get("nonce")?{nonce:String(values.get("nonce"))}:{})});
      if(result.error)throw result.error;
      passwordChanged=true;
      form.reset();
      const signedOut=await supabaseClient.auth.signOut({scope:"global"});
      if(signedOut.error)throw signedOut.error;
      logout();reset();showAuthPanel("login");
      const target=document.getElementById("loginMessage");if(target)target.textContent=t("passwordSaved");
    } catch {error=t(passwordChanged?"passwordSessionFailed":"passwordFailed");}
    finally {busy=false;renderSettings();}
  }
  async function recover(form) {
    if(busy)return;
    const checks=[0,1,2].map(i=>Boolean(form.elements["confirm"+i]?.checked));
    if(checks.some(value=>!value))return;
    busy=true;form.querySelector("button[type=submit]").disabled=true;
    try {
      await rpc("fmz_phase6d_recover_analysis_safety",{p_expected_safety_revision:recoveryRevision,p_reason_code:recoveryReason,
        p_no_previous_symptoms:checks[0],p_no_current_serious_symptoms:checks[1],p_understands_support:checks[2],p_request_id:uuid()});
      message=t("recovered");closeRecovery();await AI.hydrate({force:true});renderSettings();
    } catch(e) {
      form.querySelector(".fmz-feedback").textContent=/stale_conflict/.test(e.message||"")?t("stale"):t("error");
      if(/stale_conflict/.test(e.message||"")){await AI.hydrate({force:true});}
    } finally {busy=false;}
  }
  function reset() {
    epoch++;ownerId="";data=null;loading=null;message="";error="";busy=false;languageOpen=false;drag=null;avatarDraft=null;routedUser="";
    closeRecovery();closeSettings();closeChat();AI.reset();syncTools();
  }
  document.addEventListener("click",async event=>{
    const target=event.target.closest("button");if(!target)return;
    if(target.matches("[data-fmz-close]")){event.preventDefault();event.stopImmediatePropagation();closeTop();return;}
    if(target.dataset.fmzSettings){event.stopImmediatePropagation();await openSettings(target.dataset.fmzSettings);return;}
    if(target.dataset.fmzSection){dirty=false;section=target.dataset.fmzSection;message="";error="";renderSettings();return;}
    if(target.hasAttribute("data-fmz-language-toggle")){languageOpen=!languageOpen;syncTools();document.querySelector(".fmz-language-menu button")?.focus();return;}
    if(target.dataset.fmzLanguage){await setLanguage(target.dataset.fmzLanguage);return;}
    if(target.hasAttribute("data-fmz-reload")){error="";await hydrate(true);if(member())await AI.hydrate({force:true});renderSettings();return;}
    if(target.dataset.fmzRecovery){await openRecovery(target.dataset.fmzRecovery);return;}
    if(target.hasAttribute("data-fmz-avatar-reset")){await mutate(()=>savePatch({avatar_side:"right",avatar_y:.72}));return;}
    if(target.hasAttribute("data-fmz-logout")){
      await mutate(async()=>{const result=await supabaseClient.auth.signOut({scope:"local"});if(result.error)throw result.error;logout();reset();});return;
    }
    if(target.hasAttribute("data-fmz-code")){
      await mutate(async()=>{const result=await supabaseClient.auth.reauthenticate();if(result.error)throw result.error;message=t("codeSent");});return;
    }
    if(target.dataset.fmzConsent){
      const kind=target.dataset.fmzConsent,action=target.dataset.action;
      if(action==="withdrawn"&&!window.confirm(t("withdrawConfirm")))return;
      if(action==="granted"&&!target.closest("[data-fmz-consent-block]")?.querySelector("input:checked"))return;
      const snapshot=AI.snapshot(),doc=[...(snapshot.consent?.contracts||[]),...(snapshot.analysisConsent?.contracts||[])].find(item=>item.consent_kind===kind);
      if(!doc)return;
      await mutate(async()=>{const args={p_action:action,p_document_version:doc.document_version,p_locale:lang(),p_explicit_confirmation:true,p_request_id:uuid()};
        await rpc(kind==="ai_analysis"?"fmz_phase6d_record_analysis_consent":"fmz_phase6a_record_consent",kind==="ai_analysis"?args:{...args,p_consent_kind:kind});
        await AI.hydrate({force:true});
      });return;
    }
    if(target.dataset.fmzExport){
      await mutate(async()=>{const result=await rpc(target.dataset.fmzExport==="chat"?"fmz_phase6c_export_chat":"fmz_phase6d_export_analyses",{p_request_id:uuid()});
        const link=document.createElement("a");link.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:"application/json"}));
        link.download="fitmetzorge-"+target.dataset.fmzExport+".json";link.click();setTimeout(()=>URL.revokeObjectURL(link.href),0);
      });return;
    }
    if(target.dataset.fmzDeleteThread||target.dataset.fmzDeleteAnalysis){
      if(!window.confirm(t("deleteConfirm")))return;
      await mutate(async()=>{const chat=Boolean(target.dataset.fmzDeleteThread);
        await rpc(chat?"fmz_phase6c_delete_thread":"fmz_phase6d_delete_analysis",{[chat?"p_thread_id":"p_result_id"]:target.dataset.fmzDeleteThread||target.dataset.fmzDeleteAnalysis,
          p_expected_revision:Number(target.dataset.revision),p_request_id:uuid()});
        await AI.hydrate({force:true});
      });
    }
  },true);
  document.addEventListener("submit",event=>{
    const form=event.target;if(!form.matches("[data-fmz-form]"))return;
    event.preventDefault();event.stopImmediatePropagation();
    const values=new FormData(form),kind=form.dataset.fmzForm;
    if(kind==="schedule")saveSchedule(form);
    if(kind==="account")mutate(()=>savePatch({name:String(values.get("name")),country:String(values.get("country"))}));
    if(kind==="display")mutate(()=>savePatch({date_format:values.get("date_format"),hour_cycle:values.get("hour_cycle")}));
    if(kind==="password")changePassword(form);
    if(kind==="recovery")recover(form);
  },true);
  document.addEventListener("change",event=>{
    const target=event.target;
    if(target.closest("#fmz-settings"))dirty=true;
    if(target.matches('#fmz-settings [name="language"]'))setLanguage(target.value);
    if(target.matches("[data-fmz-avatar-visible]"))mutate(()=>savePatch({avatar_visible:target.checked}));
    if(target.dataset.fmzConsentCheck){
      const block=target.closest("[data-fmz-consent-block]");block.querySelector('[data-action="granted"]').disabled=!target.checked;
    }
    if(target.closest('[data-fmz-form="recovery"]')){
      const form=target.form;form.querySelector("button[type=submit]").disabled=![0,1,2].every(i=>form.elements["confirm"+i].checked);
    }
  },true);
  document.addEventListener("input",event=>{if(event.target.closest("#fmz-settings"))dirty=true;},true);
  document.addEventListener("keydown",event=>{
    if(event.key==="Escape"&&languageOpen){languageOpen=false;syncTools();document.querySelector("[data-fmz-language-toggle]")?.focus();}
  });
  window.addEventListener("fmz:ai-state",()=>{if(settingsDialog&&!dirty&&!busy)renderSettings();});
  window.addEventListener("resize",placeAvatar);
  window.visualViewport?.addEventListener("resize",placeAvatar);
  window.visualViewport?.addEventListener("scroll",placeAvatar);
  // Only class changes on the body are observed, to hide the avatar in existing fullscreen flows.
  new MutationObserver(()=>{const avatar=document.getElementById("fmz-avatar");if(avatar)avatar.hidden=Boolean(unsafeSurface()||settingsDialog||chatDialog||recoveryDialog||!data?.avatar.visible||!member());}).observe(document.body,{attributes:true,attributeFilter:["class"]});
  const oldRender=renderAll,oldNav=renderNav,oldView=showView;
  renderNav=function(){const result=oldNav();syncTools();return result;};
  renderAll=function(){
    if(!uid()){if(ownerId)reset();const result=oldRender();syncTools();return result;}
    const result=oldRender();syncTools();if(!data||ownerId!==uid())queueMicrotask(()=>hydrate());
    if(chatDialog)document.getElementById("ai-coach")?.classList.add("active");
    return result;
  };
  showView=function(id){
    if(id==="settings"&&uid()){openSettings("account");return;}
    return oldView(id);
  };
  const route=(force=false)=>{
    if(uid()&&data&&member()&&(force||routedUser!==uid())&&(location.hash==="#ai-coach"||new URL(location.href).searchParams.get("view")==="ai-coach")){
      routedUser=uid();openChat();
    }
  };
  window.addEventListener("hashchange",()=>route(true));
  window.FMZ_OWNER_SETTINGS=Object.freeze({open:openSettings,openChat,openRecovery,hydrate,safetyPanel,analysisSummary,reset,
    snapshot:()=>data,formatDate,formatTime:value=>new Date(value).toLocaleTimeString(locale(),{hour:"2-digit",minute:"2-digit",hour12:data?.display?.hour_cycle==="12",timeZone:analysisPreferences()?.timezone_name||"Europe/Amsterdam"})});
  window.addEventListener("fmz:ai-state",syncTools);
  supabaseClient?.auth.onAuthStateChange?.(event=>{if(event==="SIGNED_OUT")reset();});
  hydrate();
})();
