(() => {
  if (window.FMZ_MEMBER_UX_CONSISTENCY_LOADED) return;
  window.FMZ_MEMBER_UX_CONSISTENCY_LOADED = true;

  const MEMBER_UX_VERSION = "20260818-member-ux-final-owner1";
  const MEMBER_UX_LANGUAGES = ["nl", "en", "de"];
  const MEMBER_UX_LEGACY_TRACKER_VIEW_IDS = ["steps", "sleep", "wellbeing", "water", "progress"];

  const MEMBER_UX_I18N = {
    nl: {
      today: "Vandaag",
      greeting: "Goedemorgen, {name}",
      todayIntro: "Dit staat er vandaag voor je klaar.",
      dailyCheckin: "Dagelijkse check-in",
      checkinQuestion: "Hoe voel je je vandaag?",
      checkinComplete: "Check-in voltooid",
      viewCheckin: "Check-in bekijken",
      complete: "Vandaag compleet",
      partial: "Gedeeltelijk ingevuld",
      empty: "Nog invullen",
      profileIncomplete: "Maak je basisprofiel af",
      profileIntro: "Vul je ontbrekende gegevens in om je plan persoonlijk en veilig te houden.",
      completeProfile: "Profiel afronden",
      recovery: "Herstel",
      recoveryIntro: "Slaap, welzijn en je eigen herstelgevoel.",
      fillCheckin: "Check-in invullen",
      view: "Bekijken",
      training: "Training",
      trainingEntry: "Open Training om een workout te kiezen.",
      activeWorkout: "Actieve workout",
      pausedWorkout: "Workout gepauzeerd",
      readyToTrain: "Klaar om te trainen?",
      trainingToday: "Training vandaag",
      openTraining: "Training openen",
      activity: "Activiteit",
      steps: "Stappen",
      water: "Water",
      addWater: "+250 ml",
      openTrackers: "Trackers openen",
      sleep: "Slaap",
      sleepHours: "Slaapuren",
      sleepQuality: "Slaapkwaliteit",
      wellbeing: "Welzijn",
      progress: "Progress",
      weight: "Gewicht",
      noData: "Nog geen data",
      target: "Doel",
      trackers: "Trackers",
      trackersIntro: "Bekijk je dag en open alleen de tracker die je nodig hebt.",
      recoveryHistory: "Recovery week",
      recoveryHistoryIntro: "Compact overzicht van je herstel deze week.",
      daysComplete: "{count}/7 dagen compleet",
      previousWeek: "Vorige week",
      thisWeek: "Deze week",
      nextWeek: "Volgende week",
      close: "Sluiten",
      save: "Opslaan",
      saved: "Opgeslagen",
      currentDay: "Geselecteerde dag",
      hours: "Uren",
      quality: "Cijfer 1-10",
      bedtime: "Naar bed",
      wakeTime: "Wakker",
      energy: "Energie",
      stress: "Stress",
      motivation: "Motivatie",
      mood: "Stemming",
      moodGood: "Goed",
      moodNeutral: "Neutraal",
      moodLow: "Laag",
      recoveryFeeling: "Recovery feeling",
      recoveryHelp: "Eigen gevoel 1-10, geen medische score.",
      note: "Notitie",
      notePlaceholder: "Bijv. zware benen, goed geslapen, rustig aan vandaag...",
      saveRecovery: "Recovery opslaan",
      waist: "Taille",
      chest: "Borst",
      armLeft: "Arm links",
      armRight: "Arm rechts",
      legLeft: "Been links",
      legRight: "Been rechts",
      front: "Voorkant",
      side: "Zijkant",
      back: "Achterkant",
      extra: "Extra foto",
      choosePhoto: "Foto kiezen",
      reset: "Reset",
      connections: "Connecties",
      healthSync: "Health-sync",
      healthLocked: "Niet beschikbaar in Free",
      healthPlaceholder: "Nog niet actief",
      healthExplanation: "Je entitlement blijft bewaard. Een echte Health-koppeling is nog niet actief.",
      accountProfile: "Profiel en onboarding",
      open: "Openen",
      of: "van"
    },
    en: {
      today: "Today",
      greeting: "Good morning, {name}",
      todayIntro: "This is what is ready for you today.",
      dailyCheckin: "Daily check-in",
      checkinQuestion: "How do you feel today?",
      checkinComplete: "Check-in completed",
      viewCheckin: "View check-in",
      complete: "Today complete",
      partial: "Partly completed",
      empty: "Needs input",
      profileIncomplete: "Complete your basic profile",
      profileIntro: "Add the missing details to keep your plan personal and safe.",
      completeProfile: "Complete profile",
      recovery: "Recovery",
      recoveryIntro: "Sleep, wellbeing and your own recovery feeling.",
      fillCheckin: "Complete check-in",
      view: "View",
      training: "Training",
      trainingEntry: "Open Training to choose a workout.",
      activeWorkout: "Active workout",
      pausedWorkout: "Workout paused",
      readyToTrain: "Ready to train?",
      trainingToday: "Training today",
      openTraining: "Open Training",
      activity: "Activity",
      steps: "Steps",
      water: "Water",
      addWater: "+250 ml",
      openTrackers: "Open trackers",
      sleep: "Sleep",
      sleepHours: "Sleep hours",
      sleepQuality: "Sleep quality",
      wellbeing: "Wellbeing",
      progress: "Progress",
      weight: "Weight",
      noData: "No data yet",
      target: "Target",
      trackers: "Trackers",
      trackersIntro: "Review your day and open only the tracker you need.",
      recoveryHistory: "Recovery week",
      recoveryHistoryIntro: "Compact overview of this week's recovery.",
      daysComplete: "{count}/7 days complete",
      previousWeek: "Previous week",
      thisWeek: "This week",
      nextWeek: "Next week",
      close: "Close",
      save: "Save",
      saved: "Saved",
      currentDay: "Selected day",
      hours: "Hours",
      quality: "Score 1-10",
      bedtime: "Bedtime",
      wakeTime: "Wake time",
      energy: "Energy",
      stress: "Stress",
      motivation: "Motivation",
      mood: "Mood",
      moodGood: "Good",
      moodNeutral: "Neutral",
      moodLow: "Low",
      recoveryFeeling: "Recovery feeling",
      recoveryHelp: "Your own feeling 1-10, not a medical score.",
      note: "Note",
      notePlaceholder: "E.g. heavy legs, slept well, take it easy today...",
      saveRecovery: "Save recovery",
      waist: "Waist",
      chest: "Chest",
      armLeft: "Left arm",
      armRight: "Right arm",
      legLeft: "Left leg",
      legRight: "Right leg",
      front: "Front",
      side: "Side",
      back: "Back",
      extra: "Extra photo",
      choosePhoto: "Choose photo",
      reset: "Reset",
      connections: "Connections",
      healthSync: "Health sync",
      healthLocked: "Not available on Free",
      healthPlaceholder: "Not active yet",
      healthExplanation: "Your entitlement is preserved. A real Health connection is not active yet.",
      accountProfile: "Profile and onboarding",
      open: "Open",
      of: "of"
    },
    de: {
      today: "Heute",
      greeting: "Guten Morgen, {name}",
      todayIntro: "Das steht heute fuer dich bereit.",
      dailyCheckin: "Taeglicher Check-in",
      checkinQuestion: "Wie fuehlst du dich heute?",
      checkinComplete: "Check-in abgeschlossen",
      viewCheckin: "Check-in ansehen",
      complete: "Heute komplett",
      partial: "Teilweise ausgefuellt",
      empty: "Noch ausfuellen",
      profileIncomplete: "Basisprofil vervollstaendigen",
      profileIntro: "Ergaenze die fehlenden Angaben fuer einen persoenlichen und sicheren Plan.",
      completeProfile: "Profil vervollstaendigen",
      recovery: "Recovery",
      recoveryIntro: "Schlaf, Wohlbefinden und dein eigenes Erholungsgefuehl.",
      fillCheckin: "Check-in ausfuellen",
      view: "Ansehen",
      training: "Training",
      trainingEntry: "Oeffne Training, um ein Workout zu waehlen.",
      activeWorkout: "Aktives Workout",
      pausedWorkout: "Workout pausiert",
      readyToTrain: "Bereit fuer dein Training?",
      trainingToday: "Training heute",
      openTraining: "Training oeffnen",
      activity: "Aktivitaet",
      steps: "Schritte",
      water: "Wasser",
      addWater: "+250 ml",
      openTrackers: "Tracker oeffnen",
      sleep: "Schlaf",
      sleepHours: "Schlafstunden",
      sleepQuality: "Schlafqualitaet",
      wellbeing: "Wohlbefinden",
      progress: "Fortschritt",
      weight: "Gewicht",
      noData: "Noch keine Daten",
      target: "Ziel",
      trackers: "Tracker",
      trackersIntro: "Pruefe deinen Tag und oeffne nur den Tracker, den du brauchst.",
      recoveryHistory: "Recovery-Woche",
      recoveryHistoryIntro: "Kompakte Uebersicht deiner Erholung in dieser Woche.",
      daysComplete: "{count}/7 Tage komplett",
      previousWeek: "Vorherige Woche",
      thisWeek: "Diese Woche",
      nextWeek: "Naechste Woche",
      close: "Schliessen",
      save: "Speichern",
      saved: "Gespeichert",
      currentDay: "Ausgewaehlter Tag",
      hours: "Stunden",
      quality: "Bewertung 1-10",
      bedtime: "Schlafenszeit",
      wakeTime: "Aufwachzeit",
      energy: "Energie",
      stress: "Stress",
      motivation: "Motivation",
      mood: "Stimmung",
      moodGood: "Gut",
      moodNeutral: "Neutral",
      moodLow: "Niedrig",
      recoveryFeeling: "Recovery Feeling",
      recoveryHelp: "Eigenes Gefuehl 1-10, kein medizinischer Score.",
      note: "Notiz",
      notePlaceholder: "Z.B. schwere Beine, gut geschlafen, heute ruhiger...",
      saveRecovery: "Recovery speichern",
      waist: "Taille",
      chest: "Brust",
      armLeft: "Linker Arm",
      armRight: "Rechter Arm",
      legLeft: "Linkes Bein",
      legRight: "Rechtes Bein",
      front: "Vorne",
      side: "Seite",
      back: "Hinten",
      extra: "Extra Foto",
      choosePhoto: "Foto auswaehlen",
      reset: "Zuruecksetzen",
      connections: "Verbindungen",
      healthSync: "Health-Sync",
      healthLocked: "In Free nicht verfuegbar",
      healthPlaceholder: "Noch nicht aktiv",
      healthExplanation: "Deine Berechtigung bleibt erhalten. Eine echte Health-Verbindung ist noch nicht aktiv.",
      accountProfile: "Profil und Onboarding",
      open: "Oeffnen",
      of: "von"
    }
  };

  window.FMZ_MEMBER_UX_CONSISTENCY = {
    version: MEMBER_UX_VERSION,
    surfaces: ["client_today", "client_trackers", "tracker_detail", "settings_connections"],
    mobileFirst: true,
    overviewFirst: true,
    databaseChanges: false,
    phase3Frozen: true,
    noPolling: true,
    explicitRenderBoundaries: true
  };

  const memberUxLegacyRenderClientHome = renderClientHome;
  const memberUxOriginalRenderSettingsPage = renderSettingsPage;
  const memberUxOriginalShowView = showView;
  const memberUxOriginalRenderAll = renderAll;
  const memberUxOriginalRenderers = {
    steps: renderSteps,
    progress: renderProgress,
    wellbeing: renderWellbeing,
    sleep: renderSleep,
    water: renderWater,
    nutrition: renderNutrition,
    nutritionLog: renderNutritionLog
  };

  let memberUxDetail = { type: "", dayIndex: todayIndex(), opener: null, photoDraft: {} };

  function memberUxLanguage() {
    const language = state?.accountSettings?.language || "nl";
    return MEMBER_UX_LANGUAGES.includes(language) ? language : "nl";
  }

  function memberUxText(key) {
    const language = memberUxLanguage();
    return MEMBER_UX_I18N[language]?.[key] || MEMBER_UX_I18N.nl[key] || key;
  }

  function memberUxFormat(key, values = {}) {
    let value = memberUxText(key);
    Object.entries(values).forEach(([name, replacement]) => {
      value = value.split(`{${name}}`).join(String(replacement ?? ""));
    });
    return value;
  }

  function memberUxLocale() {
    return { nl: "nl-NL", en: "en-GB", de: "de-DE" }[memberUxLanguage()] || "nl-NL";
  }

  function memberUxDateLabel(dateValue, options = { weekday: "short", day: "numeric", month: "short" }) {
    const date = new Date(`${dateValue}T12:00:00`);
    return Number.isNaN(date.getTime()) ? String(dateValue || "") : date.toLocaleDateString(memberUxLocale(), options);
  }

  function memberUxValue(value, suffix = "") {
    return value === "" || value === null || value === undefined ? memberUxText("noData") : `${fmt(number(value), suffix ? 1 : 0)}${suffix}`;
  }

  function memberUxOnboardingComplete(selected) {
    return phase1OnboardingComplete(selected);
  }

  function memberUxSetLegacyTrackerViewsHidden(hidden) {
    MEMBER_UX_LEGACY_TRACKER_VIEW_IDS.forEach((id) => {
      const view = document.getElementById(id);
      if (!view) return;
      view.hidden = hidden;
      if (hidden) {
        view.classList.remove("active");
        view.setAttribute("aria-hidden", "true");
      } else {
        view.removeAttribute("aria-hidden");
      }
    });
  }

  function memberUxSelectedDayIndex() {
    return Math.max(0, Math.min(6, number(state.ui.trackerDayIndex, todayIndex())));
  }

  function memberUxLegacyRecoveryFeeling(selected, index) {
    return selected?.recoveryFeelingByWeek?.[activeWeekStart()]?.[index] || {};
  }

  function memberUxReadDay(selected, index = memberUxSelectedDayIndex(), { includeExtendedTrackers = true } = {}) {
    const dates = weekDates(activeWeekStart());
    const day = dates[index] || dates[0];
    const stored = state?.phase2Recovery?.logs?.[day.date] || {};
    const stepsEntry = weekArray(selected, "stepsByWeek", "value")[index] || {};
    const waterEntry = includeExtendedTrackers ? (weekWaterEntries(selected)[index] || {}) : {};
    const sleepEntry = weekArray(selected, "sleepByWeek", "hours", { quality: "", bed: "", wake: "" })[index] || {};
    const wellbeingEntry = weekArray(selected, "wellbeingByWeek", "energy", { stress: "", motivation: "", mood: "" })[index] || {};
    const progressEntry = includeExtendedTrackers ? (progressWeekEntries(selected)[index] || {}) : {};
    const feelingEntry = memberUxLegacyRecoveryFeeling(selected, index);
    return {
      index,
      date: day.date,
      day: day.day,
      steps: stored.steps ?? stepsEntry.value ?? "",
      water: waterEntry.value ?? "",
      sleepHours: stored.sleep_hours ?? sleepEntry.hours ?? "",
      sleepQuality: stored.sleep_quality ?? sleepEntry.quality ?? "",
      bedtime: sleepEntry.bed ?? "",
      wakeTime: sleepEntry.wake ?? "",
      energy: stored.wellbeing_energy ?? wellbeingEntry.energy ?? "",
      stress: stored.wellbeing_stress ?? wellbeingEntry.stress ?? "",
      motivation: stored.wellbeing_motivation ?? wellbeingEntry.motivation ?? "",
      mood: stored.wellbeing_mood ?? wellbeingEntry.mood ?? "",
      recoveryFeeling: stored.recovery_feeling ?? feelingEntry.feeling ?? "",
      recoveryNote: stored.recovery_note ?? feelingEntry.note ?? "",
      progress: progressEntry
    };
  }

  function memberUxRecoveryCompletion(day) {
    const checks = [
      day.steps !== "",
      day.sleepHours !== "",
      day.energy !== "" || day.stress !== "" || day.motivation !== "",
      day.recoveryFeeling !== ""
    ];
    const count = checks.filter(Boolean).length;
    return {
      count,
      complete: count === checks.length,
      label: memberUxText(count === checks.length ? "complete" : count ? "partial" : "empty")
    };
  }

  function memberUxTrainingSummary() {
    const profileId = onlineProfile?.role === "client" && onlineProfile?.id ? onlineProfile.id : "";
    const localId = `local-${String(state?.ui?.authEmail || client()?.id || "guest").toLowerCase()}`;
    try {
      const raw = localStorage.getItem(`fmz-phase3-training:${profileId || localId}`);
      const session = raw ? JSON.parse(raw)?.activeSession : null;
      if (session && ["active", "paused"].includes(session.status)) {
        return {
          active: true,
          title: session.planTitle || memberUxText("activeWorkout"),
          status: memberUxText(session.status === "paused" ? "pausedWorkout" : "activeWorkout")
        };
      }
    } catch {
      // A generic Training entry remains available if the local session snapshot is unavailable.
    }
    return { active: false, title: memberUxText("readyToTrain"), status: memberUxText("trainingEntry") };
  }

  function memberUxLatestWeight(selected) {
    const entries = progressWeekEntries(selected);
    for (let index = entries.length - 1; index >= 0; index -= 1) {
      if (entries[index]?.value !== "" && entries[index]?.value !== undefined) return entries[index].value;
    }
    return "";
  }

  function memberUxMoodLabel(value) {
    return { Goed: memberUxText("moodGood"), Neutraal: memberUxText("moodNeutral"), Laag: memberUxText("moodLow") }[value] || "";
  }

  function memberUxWellbeingSummary(day) {
    const parts = [];
    if (day.energy !== "") parts.push(`${memberUxText("energy")} ${escapeHTML(day.energy)}/10`);
    if (day.mood) parts.push(memberUxMoodLabel(day.mood));
    return parts.join(" | ") || memberUxText("noData");
  }

  function memberUxMetric(label, value, sub = "") {
    return `<div class="member-ux-metric"><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong>${sub ? `<small>${escapeHTML(sub)}</small>` : ""}</div>`;
  }

  function memberUxDialogButton(type, label, className = "secondary-btn") {
    return `<button class="${className}" data-member-open-detail="${escapeHTML(type)}" type="button" aria-haspopup="dialog" aria-controls="memberUxDetailPortal" aria-expanded="false">${escapeHTML(label)}</button>`;
  }

  function memberUxInstallStyles() {
    if (document.getElementById("member-ux-consistency-styles")) return;
    const style = document.createElement("style");
    style.id = "member-ux-consistency-styles";
    style.textContent = `
      .member-ux-shell { display: grid; gap: 12px; }
      .member-ux-hero,
      .member-ux-card,
      .member-ux-profile-cta,
      .member-ux-connection-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface);
        padding: 14px;
        min-width: 0;
      }
      .member-ux-hero { display: grid; gap: 10px; border-color: rgba(215,178,77,.45); }
      .member-ux-hero-row,
      .member-ux-card-head,
      .member-ux-card-actions,
      .member-ux-week-actions,
      .member-ux-detail-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }
      .member-ux-hero h1,
      .member-ux-card h2,
      .member-ux-detail-head h2 { margin: 0; letter-spacing: 0; }
      .member-ux-hero h1 { font-size: 28px; line-height: 1.1; }
      .member-ux-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .member-ux-card { display: grid; gap: 10px; align-content: start; }
      .member-ux-card-wide { grid-column: 1 / -1; }
      .member-ux-card p { margin: 0; }
      .member-ux-card-actions { justify-content: flex-start; flex-wrap: wrap; }
      .member-ux-primary-action {
        background: linear-gradient(135deg, var(--gold), #e2b848);
        border-color: transparent;
        color: #17120a;
      }
      .member-ux-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .member-ux-metric { display: grid; gap: 2px; min-width: 0; }
      .member-ux-metric span,
      .member-ux-metric small { color: var(--muted); font-size: 12px; font-weight: 800; }
      .member-ux-metric strong { font-size: 20px; line-height: 1.1; overflow-wrap: anywhere; }
      .member-ux-profile-cta { display: grid; gap: 8px; border-color: rgba(215,178,77,.55); }
      .member-ux-day-strip { display: flex; gap: 8px; overflow-x: auto; padding: 2px 0 4px; scrollbar-width: none; }
      .member-ux-day-strip::-webkit-scrollbar { display: none; }
      .member-ux-day {
        flex: 0 0 auto;
        min-width: 70px;
        min-height: 48px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: transparent;
        color: var(--text);
        padding: 8px;
        cursor: pointer;
      }
      .member-ux-day.active { border-color: var(--gold); background: rgba(215,178,77,.14); }
      .member-ux-day span { display: block; color: var(--muted); font-size: 11px; }
      .member-ux-progress { height: 6px; border-radius: 3px; background: rgba(255,255,255,.1); overflow: hidden; }
      .member-ux-progress > span { display: block; width: var(--member-progress, 0%); height: 100%; background: var(--gold); }
      .member-ux-portal { position: fixed; inset: 0; z-index: 90; display: grid; align-items: end; }
      .member-ux-backdrop { position: absolute; inset: 0; border: 0; background: rgba(0,0,0,.68); cursor: pointer; }
      .member-ux-sheet {
        position: relative;
        width: 100%;
        max-height: 94dvh;
        overflow-y: auto;
        border: 1px solid var(--line);
        border-radius: 8px 8px 0 0;
        background: var(--bg);
        padding: 16px 16px calc(24px + env(safe-area-inset-bottom));
        box-shadow: var(--shadow);
      }
      body.member-ux-detail-open { overflow: hidden; }
      .member-ux-close { width: 44px; height: 44px; padding: 0; flex: none; font-size: 22px; }
      .member-ux-detail-body { display: grid; gap: 14px; margin-top: 14px; }
      .member-ux-detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .member-ux-detail-grid .wide { grid-column: 1 / -1; }
      .member-ux-save-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
      .member-ux-history { display: grid; gap: 8px; }
      .member-ux-history-row { display: grid; grid-template-columns: 1fr repeat(3, minmax(0, .8fr)); gap: 8px; align-items: center; border-bottom: 1px solid var(--line); padding: 10px 0; }
      .member-ux-photo-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .member-ux-photo { display: grid; gap: 7px; }
      .member-ux-photo img { width: 100%; height: 120px; object-fit: cover; border-radius: 8px; }
      .member-ux-photo-empty { display: grid; place-items: center; height: 82px; border: 1px dashed var(--line); border-radius: 8px; color: var(--muted); }
      .member-ux-connection-card { display: grid; gap: 8px; }
      .member-ux-sheet button,
      .member-ux-card button,
      .member-ux-profile-cta button { min-height: 44px; }
      @media (min-width: 720px) {
        .member-ux-portal { align-items: center; justify-items: center; padding: 24px; }
        .member-ux-sheet { max-width: 760px; max-height: 88dvh; border-radius: 8px; }
        .member-ux-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .member-ux-card-wide { grid-column: span 2; }
      }
      @media (max-width: 359px) {
        .member-ux-grid,
        .member-ux-detail-grid,
        .member-ux-metrics,
        .member-ux-photo-grid { grid-template-columns: 1fr; }
        .member-ux-card-wide,
        .member-ux-detail-grid .wide { grid-column: auto; }
        .member-ux-hero-row,
        .member-ux-card-head,
        .member-ux-week-actions { align-items: stretch; flex-direction: column; }
      }
    `;
    document.head.appendChild(style);
  }

  function memberUxRenderDashboard() {
    if (currentView !== "client-home") return;
    memberUxInstallStyles();
    const target = document.getElementById("clientSummary");
    const selected = client();
    if (!target) return;
    if (!isLoggedIn() || state.ui.role !== "client" || !hasSelectedClient(selected)) {
      target.innerHTML = emptyTrackerState(memberUxText("noData"));
      return;
    }
    const day = memberUxReadDay(selected, todayIndex(), { includeExtendedTrackers: false });
    const recovery = memberUxRecoveryCompletion(day);
    const training = memberUxTrainingSummary();
    const onboardingComplete = memberUxOnboardingComplete(selected);
    const firstName = String(selected.name || state.ui.authName || "").split(" ")[0] || memberUxText("today");
    const checkinTitle = memberUxText(recovery.complete ? "checkinComplete" : "checkinQuestion");
    const checkinAction = memberUxText(recovery.complete ? "viewCheckin" : "fillCheckin");

    target.innerHTML = `
      <div class="member-ux-shell member-ux-today-simplified">
        <section class="member-ux-hero" aria-labelledby="member-ux-today-title">
          <div><p class="eyebrow">${escapeHTML(memberUxText("today"))}</p><h1 id="member-ux-today-title">${escapeHTML(memberUxFormat("greeting", { name: firstName }))}</h1></div>
          <p class="muted">${escapeHTML(memberUxText("todayIntro"))}</p>
        </section>

        ${onboardingComplete ? `
          <section class="member-ux-card member-ux-daily-checkin" aria-labelledby="member-ux-checkin-title">
            <div class="member-ux-card-head">
              <div><p class="eyebrow">${escapeHTML(memberUxText("dailyCheckin"))}</p><h2 id="member-ux-checkin-title">${escapeHTML(checkinTitle)}</h2></div>
              <span class="status ${recovery.complete ? "ok" : recovery.count ? "warn" : ""}">${escapeHTML(recovery.label)}</span>
            </div>
            ${recovery.complete ? `<p class="muted">${escapeHTML(memberUxText("recoveryFeeling"))}: ${escapeHTML(day.recoveryFeeling)}/10</p>` : ""}
            <div class="member-ux-card-actions">${memberUxDialogButton("recovery", checkinAction, "primary-btn")}</div>
          </section>

          <section class="member-ux-card member-ux-training-today" aria-labelledby="member-ux-training-title">
            <div class="member-ux-card-head">
              <div><p class="eyebrow">${escapeHTML(memberUxText(training.active ? "trainingToday" : "training"))}</p><h2 id="member-ux-training-title">${escapeHTML(training.title)}</h2></div>
              ${training.active ? '<span class="status ok">Live</span>' : ""}
            </div>
            <p class="muted">${escapeHTML(training.status)}</p>
            <div class="member-ux-card-actions"><button class="primary-btn" data-member-open-view="training" type="button">${escapeHTML(memberUxText("openTraining"))}</button></div>
          </section>
        ` : `
          <section class="member-ux-profile-cta" aria-labelledby="member-ux-profile-title">
            <div><p class="eyebrow">${escapeHTML(memberUxText("accountProfile"))}</p><h2 id="member-ux-profile-title">${escapeHTML(memberUxText("profileIncomplete"))}</h2></div>
            <p class="muted">${escapeHTML(memberUxText("profileIntro"))}</p>
            <div><button class="primary-btn" data-member-open-profile type="button">${escapeHTML(memberUxText("completeProfile"))}</button></div>
          </section>
        `}
      </div>
    `;
  }

  function memberUxTrackerCard(type, title, value, detail, actions = "", wide = false) {
    return `
      <section class="member-ux-card ${wide ? "member-ux-card-wide" : ""}">
        <div class="member-ux-card-head"><h2>${escapeHTML(title)}</h2><button class="primary-btn member-ux-primary-action" data-member-open-detail="${escapeHTML(type)}" type="button" aria-haspopup="dialog" aria-controls="memberUxDetailPortal" aria-expanded="false">${escapeHTML(memberUxText("open"))}</button></div>
        <strong>${escapeHTML(value)}</strong>
        ${detail ? `<p class="muted">${escapeHTML(detail)}</p>` : ""}
        ${actions ? `<div class="member-ux-card-actions">${actions}</div>` : ""}
      </section>
    `;
  }

  function memberUxRenderTrackers() {
    if (currentView !== "trackers") return;
    memberUxInstallStyles();
    const target = document.getElementById("trackerOverview");
    const selected = client();
    if (!target) return;
    if (!isLoggedIn() || state.ui.role !== "client" || !hasSelectedClient(selected)) {
      target.innerHTML = emptyTrackerState(memberUxText("noData"));
      return;
    }
    memberUxSetLegacyTrackerViewsHidden(true);
    const index = memberUxSelectedDayIndex();
    const day = memberUxReadDay(selected, index);
    const recovery = memberUxRecoveryCompletion(day);
    const dates = weekDates(activeWeekStart());
    const completedDays = dates.map((_, dayIndex) => memberUxRecoveryCompletion(memberUxReadDay(selected, dayIndex))).filter((item) => item.complete).length;
    const stepGoal = number(selected.goals?.steps, 10000) || 10000;
    const waterGoal = number(selected.goals?.water, 2.5) || 2.5;
    const latestWeight = memberUxLatestWeight(selected);

    target.innerHTML = `
      <div class="member-ux-shell">
        <header class="member-ux-hero">
          <div class="member-ux-hero-row"><div><p class="eyebrow">${escapeHTML(memberUxText("trackers"))}</p><h1>${escapeHTML(memberUxText("trackers"))}</h1></div><span class="status">${escapeHTML(memberUxDateLabel(day.date))}</span></div>
          <p class="muted">${escapeHTML(memberUxText("trackersIntro"))}</p>
          <div class="member-ux-week-actions">
            <button class="secondary-btn" data-member-week-nav="-1" type="button">${escapeHTML(memberUxText("previousWeek"))}</button>
            <button class="secondary-btn" data-member-week-nav="today" type="button">${escapeHTML(memberUxText("thisWeek"))}</button>
            <button class="secondary-btn" data-member-week-nav="1" type="button">${escapeHTML(memberUxText("nextWeek"))}</button>
          </div>
        </header>
        <div class="member-ux-day-strip" aria-label="${escapeHTML(memberUxText("currentDay"))}">
          ${dates.map((item, dayIndex) => `<button class="member-ux-day ${dayIndex === index ? "active" : ""}" data-member-tracker-day="${dayIndex}" type="button" aria-pressed="${dayIndex === index}"><strong>${escapeHTML(memberUxDateLabel(item.date, { weekday: "short" }))}</strong><span>${escapeHTML(memberUxDateLabel(item.date, { day: "numeric", month: "short" }))}</span></button>`).join("")}
        </div>
        <div class="member-ux-grid">
          ${memberUxTrackerCard("recovery-history", memberUxText("recoveryHistory"), memberUxFormat("daysComplete", { count: completedDays }), recovery.label, "", true)}
          ${memberUxTrackerCard("steps", memberUxText("steps"), day.steps === "" ? memberUxText("noData") : fmt(day.steps), `${memberUxText("target")} ${fmt(stepGoal)}`)}
          ${memberUxTrackerCard("water", memberUxText("water"), day.water === "" ? memberUxText("noData") : `${fmt(day.water, 2)}L`, `${memberUxText("target")} ${fmt(waterGoal, 1)}L`, `<button class="secondary-btn" data-member-water-adjust="0.25" data-member-water-index="${index}" type="button">${escapeHTML(memberUxText("addWater"))}</button><span class="save-feedback" data-save-feedback="water-${index}" role="status" aria-live="polite"></span>`)}
          ${memberUxTrackerCard("sleep", memberUxText("sleep"), day.sleepHours === "" ? memberUxText("noData") : `${fmt(day.sleepHours, 1)}u`, day.sleepQuality === "" ? "" : `${memberUxText("quality")}: ${day.sleepQuality}/10`)}
          ${memberUxTrackerCard("wellbeing", memberUxText("wellbeing"), memberUxWellbeingSummary(day), "")}
          ${memberUxTrackerCard("progress", memberUxText("progress"), latestWeight === "" ? memberUxText("noData") : `${fmt(latestWeight, 1)} kg`, memberUxText("weight"), "", true)}
        </div>
      </div>
    `;
  }

  function memberUxScoreOptions(value) {
    return ["", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
      .map((option) => `<option value="${option}" ${String(option) === String(value ?? "") ? "selected" : ""}>${option || "-"}</option>`)
      .join("");
  }

  function memberUxMoodOptions(value) {
    return [["", "-"], ["Goed", memberUxText("moodGood")], ["Neutraal", memberUxText("moodNeutral")], ["Laag", memberUxText("moodLow")]]
      .map(([key, label]) => `<option value="${escapeHTML(key)}" ${key === (value || "") ? "selected" : ""}>${escapeHTML(label)}</option>`)
      .join("");
  }

  function memberUxDaySelect(index) {
    return `
      <label class="field"><span>${escapeHTML(memberUxText("currentDay"))}</span>
        <select data-member-detail-day>
          ${weekDates(activeWeekStart()).map((item, dayIndex) => `<option value="${dayIndex}" ${dayIndex === index ? "selected" : ""}>${escapeHTML(memberUxDateLabel(item.date))}</option>`).join("")}
        </select>
      </label>
    `;
  }

  function memberUxRecoveryDetail(day) {
    return `
      ${memberUxDaySelect(day.index)}
      <div class="member-ux-detail-grid">
        <label class="field"><span>${escapeHTML(memberUxText("steps"))}</span><input data-phase2-steps="${day.index}" type="number" min="0" inputmode="numeric" value="${escapeHTML(day.steps || "")}" /></label>
        <label class="field"><span>${escapeHTML(memberUxText("sleepHours"))}</span><select data-phase2-sleep-hours="${day.index}">${trackerNumberOptions(day.sleepHours, 15, 0.5)}</select></label>
        <label class="field"><span>${escapeHTML(memberUxText("sleepQuality"))}</span><select data-phase2-sleep-quality="${day.index}">${memberUxScoreOptions(day.sleepQuality)}</select></label>
        <label class="field"><span>${escapeHTML(memberUxText("energy"))}</span><select data-phase2-wellbeing-energy="${day.index}">${memberUxScoreOptions(day.energy)}</select></label>
        <label class="field"><span>${escapeHTML(memberUxText("stress"))}</span><select data-phase2-wellbeing-stress="${day.index}">${memberUxScoreOptions(day.stress)}</select></label>
        <label class="field"><span>${escapeHTML(memberUxText("motivation"))}</span><select data-phase2-wellbeing-motivation="${day.index}">${memberUxScoreOptions(day.motivation)}</select></label>
        <label class="field"><span>${escapeHTML(memberUxText("mood"))}</span><select data-phase2-wellbeing-mood="${day.index}">${memberUxMoodOptions(day.mood)}</select></label>
        <label class="field"><span>${escapeHTML(memberUxText("recoveryFeeling"))}</span><select data-phase2-recovery-feeling="${day.index}">${memberUxScoreOptions(day.recoveryFeeling)}</select><small>${escapeHTML(memberUxText("recoveryHelp"))}</small></label>
        <label class="field wide"><span>${escapeHTML(memberUxText("note"))}</span><textarea data-phase2-recovery-note="${day.index}" rows="3" placeholder="${escapeHTML(memberUxText("notePlaceholder"))}">${escapeHTML(day.recoveryNote || "")}</textarea></label>
      </div>
      <div class="member-ux-save-row"><button class="primary-btn" data-phase2-save-recovery="${day.index}" type="button">${escapeHTML(memberUxText("saveRecovery"))}</button><span class="save-feedback" data-save-feedback="phase2-recovery-${day.index}" role="status" aria-live="polite"></span></div>
    `;
  }

  function memberUxSimpleDetail(type, day) {
    if (type === "steps") {
      return `${memberUxDaySelect(day.index)}<label class="field"><span>${escapeHTML(memberUxText("steps"))}</span><input data-member-field="steps" type="number" min="0" inputmode="numeric" value="${escapeHTML(day.steps || "")}" /></label>${memberUxSaveRow(type, day.index)}`;
    }
    if (type === "sleep") {
      return `${memberUxDaySelect(day.index)}<div class="member-ux-detail-grid"><label class="field"><span>${escapeHTML(memberUxText("hours"))}</span><select data-member-field="sleepHours">${trackerNumberOptions(day.sleepHours, 15, 0.5)}</select></label><label class="field"><span>${escapeHTML(memberUxText("quality"))}</span><select data-member-field="sleepQuality">${memberUxScoreOptions(day.sleepQuality)}</select></label><label class="field"><span>${escapeHTML(memberUxText("bedtime"))}</span><input data-member-field="bedtime" type="time" value="${escapeHTML(day.bedtime || "")}" /></label><label class="field"><span>${escapeHTML(memberUxText("wakeTime"))}</span><input data-member-field="wakeTime" type="time" value="${escapeHTML(day.wakeTime || "")}" /></label></div>${memberUxSaveRow(type, day.index)}`;
    }
    if (type === "wellbeing") {
      return `${memberUxDaySelect(day.index)}<div class="member-ux-detail-grid"><label class="field"><span>${escapeHTML(memberUxText("energy"))}</span><select data-member-field="energy">${memberUxScoreOptions(day.energy)}</select></label><label class="field"><span>${escapeHTML(memberUxText("stress"))}</span><select data-member-field="stress">${memberUxScoreOptions(day.stress)}</select></label><label class="field"><span>${escapeHTML(memberUxText("motivation"))}</span><select data-member-field="motivation">${memberUxScoreOptions(day.motivation)}</select></label><label class="field"><span>${escapeHTML(memberUxText("mood"))}</span><select data-member-field="mood">${memberUxMoodOptions(day.mood)}</select></label></div>${memberUxSaveRow(type, day.index)}`;
    }
    if (type === "water") {
      return `${memberUxDaySelect(day.index)}<div class="member-ux-metrics">${memberUxMetric(memberUxText("water"), day.water === "" ? memberUxText("noData") : `${fmt(day.water, 2)}L`, `${memberUxText("target")} ${fmt(client().goals?.water || 2.5, 1)}L`)}</div><div class="member-ux-card-actions"><button class="secondary-btn" data-member-water-adjust="-0.25" data-member-water-index="${day.index}" type="button">-250 ml</button><button class="primary-btn" data-member-water-adjust="0.25" data-member-water-index="${day.index}" type="button">+250 ml</button><button class="secondary-btn" data-member-water-adjust="0.5" data-member-water-index="${day.index}" type="button">+500 ml</button><button class="secondary-btn" data-member-water-adjust="reset" data-member-water-index="${day.index}" type="button">${escapeHTML(memberUxText("reset"))}</button></div><span class="save-feedback" data-save-feedback="water-${day.index}" role="status" aria-live="polite"></span>`;
    }
    return "";
  }

  function memberUxSaveRow(type, index) {
    return `<div class="member-ux-save-row"><button class="primary-btn" data-member-save-detail="${escapeHTML(type)}" data-member-save-index="${index}" type="button">${escapeHTML(memberUxText("save"))}</button><span class="save-feedback" data-save-feedback="${escapeHTML(type)}-${index}" role="status" aria-live="polite"></span></div>`;
  }

  function memberUxProgressDetail(day) {
    const progress = day.progress || {};
    const photoFields = [["photoFront", "front"], ["photoSide", "side"], ["photoBack", "back"], ["photoExtra", "extra"]];
    return `
      ${memberUxDaySelect(day.index)}
      <div class="member-ux-detail-grid">
        ${[["value", "weight"], ["waist", "waist"], ["chest", "chest"], ["armLeft", "armLeft"], ["armRight", "armRight"], ["legLeft", "legLeft"], ["legRight", "legRight"]].map(([key, label]) => `<label class="field"><span>${escapeHTML(memberUxText(label))}</span><input data-member-field="progress-${key}" type="number" min="0" step="0.1" inputmode="decimal" value="${escapeHTML(progress[key] || "")}" /></label>`).join("")}
        <label class="field wide"><span>${escapeHTML(memberUxText("note"))}</span><textarea data-member-field="progress-note" rows="3">${escapeHTML(progress.note || "")}</textarea></label>
      </div>
      <div class="member-ux-photo-grid">
        ${photoFields.map(([key, label]) => {
          const value = memberUxDetail.photoDraft[key] || progress[key] || "";
          return `<label class="member-ux-photo"><span>${escapeHTML(memberUxText(label))}</span>${value ? `<img data-member-photo-preview="${key}" src="${escapeHTML(value)}" alt="${escapeHTML(memberUxText(label))}" />` : `<span class="member-ux-photo-empty" data-member-photo-preview="${key}">${escapeHTML(memberUxText("noData"))}</span>`}<input data-member-progress-file="${key}" type="file" accept="image/*" aria-label="${escapeHTML(memberUxText("choosePhoto"))}: ${escapeHTML(memberUxText(label))}" /></label>`;
        }).join("")}
      </div>
      ${memberUxSaveRow("progress", day.index)}
    `;
  }

  function memberUxRecoveryHistory(selected) {
    const rows = weekDates(activeWeekStart()).map((date, index) => {
      const day = memberUxReadDay(selected, index);
      const completion = memberUxRecoveryCompletion(day);
      return `<div class="member-ux-history-row"><strong>${escapeHTML(memberUxDateLabel(date.date))}</strong><span>${day.sleepHours === "" ? "-" : `${fmt(day.sleepHours, 1)}u`}</span><span>${day.steps === "" ? "-" : fmt(day.steps)}</span><span class="status ${completion.complete ? "ok" : ""}">${escapeHTML(completion.label)}</span></div>`;
    }).join("");
    return `<p class="muted">${escapeHTML(memberUxText("recoveryHistoryIntro"))}</p><div class="member-ux-history">${rows}</div>`;
  }

  function memberUxDetailTitle(type) {
    return {
      recovery: memberUxText("recovery"),
      "recovery-history": memberUxText("recoveryHistory"),
      steps: memberUxText("steps"),
      water: memberUxText("water"),
      sleep: memberUxText("sleep"),
      wellbeing: memberUxText("wellbeing"),
      progress: memberUxText("progress")
    }[type] || memberUxText("trackers");
  }

  function memberUxDetailContent(type, day) {
    if (type === "recovery") return memberUxRecoveryDetail(day);
    if (type === "recovery-history") return memberUxRecoveryHistory(client());
    if (type === "progress") return memberUxProgressDetail(day);
    return memberUxSimpleDetail(type, day);
  }

  function memberUxRenderDetail() {
    if (!memberUxDetail.type || !isLoggedIn() || state.ui.role !== "client") return;
    const day = memberUxReadDay(client(), memberUxDetail.dayIndex);
    let portal = document.getElementById("memberUxDetailPortal");
    if (!portal) {
      portal = document.createElement("div");
      portal.id = "memberUxDetailPortal";
      portal.className = "member-ux-portal";
      document.body.appendChild(portal);
    }
    const titleId = "member-ux-detail-title";
    portal.innerHTML = `
      <button class="member-ux-backdrop" data-member-close-detail type="button" aria-label="${escapeHTML(memberUxText("close"))}"></button>
      <section class="member-ux-sheet" role="dialog" aria-modal="true" aria-labelledby="${titleId}">
        <header class="member-ux-detail-head"><div><p class="eyebrow">${escapeHTML(memberUxText("trackers"))}</p><h2 id="${titleId}">${escapeHTML(memberUxDetailTitle(memberUxDetail.type))}</h2></div><button class="secondary-btn member-ux-close" data-member-close-detail type="button" aria-label="${escapeHTML(memberUxText("close"))}">x</button></header>
        <div class="member-ux-detail-body">${memberUxDetailContent(memberUxDetail.type, day)}</div>
      </section>
    `;
    document.body.classList.add("member-ux-detail-open");
    portal.querySelector(".member-ux-close")?.focus();
  }

  function memberUxOpenDetail(type, opener) {
    memberUxDetail = { type, dayIndex: memberUxSelectedDayIndex(), opener: opener || document.activeElement, photoDraft: {} };
    memberUxDetail.opener?.setAttribute?.("aria-expanded", "true");
    memberUxRenderDetail();
  }

  function memberUxCloseDetail({ restoreFocus = true } = {}) {
    const opener = memberUxDetail.opener;
    opener?.setAttribute?.("aria-expanded", "false");
    document.getElementById("memberUxDetailPortal")?.remove();
    document.body.classList.remove("member-ux-detail-open");
    memberUxDetail = { type: "", dayIndex: memberUxSelectedDayIndex(), opener: null, photoDraft: {} };
    if (restoreFocus) opener?.focus?.();
  }

  function memberUxField(name) {
    return document.querySelector(`#memberUxDetailPortal [data-member-field="${name}"]`);
  }

  async function memberUxSaveDetail(type, index) {
    const selected = client();
    const dayIndex = Number(index);
    if (!hasSelectedClient(selected)) return;
    if (type === "steps") {
      weekArray(selected, "stepsByWeek", "value")[dayIndex].value = memberUxField("steps")?.value || "";
    }
    if (type === "sleep") {
      const entry = weekArray(selected, "sleepByWeek", "hours", { quality: "", bed: "", wake: "" })[dayIndex];
      entry.hours = memberUxField("sleepHours")?.value || "";
      entry.quality = memberUxField("sleepQuality")?.value || "";
      entry.bed = memberUxField("bedtime")?.value || "";
      entry.wake = memberUxField("wakeTime")?.value || "";
    }
    if (type === "wellbeing") {
      const entry = weekArray(selected, "wellbeingByWeek", "energy", { stress: "", motivation: "", mood: "" })[dayIndex];
      entry.energy = memberUxField("energy")?.value || "";
      entry.stress = memberUxField("stress")?.value || "";
      entry.motivation = memberUxField("motivation")?.value || "";
      entry.mood = memberUxField("mood")?.value || "";
    }
    if (type === "progress") {
      const entry = progressWeekEntries(selected)[dayIndex];
      ["value", "waist", "chest", "armLeft", "armRight", "legLeft", "legRight", "note"].forEach((key) => {
        entry[key] = memberUxField(`progress-${key}`)?.value || "";
      });
      Object.entries(memberUxDetail.photoDraft).forEach(([key, value]) => {
        entry[key] = value;
      });
      selected.dailyWeight = progressWeekEntries(selected);
    }
    await saveTrackerDay(type, dayIndex);
    if (currentView === "trackers") memberUxRenderTrackers();
    if (currentView === "client-home") memberUxRenderDashboard();
  }

  async function memberUxAdjustWater(index, amount) {
    const selected = client();
    if (!hasSelectedClient(selected)) return;
    if (amount === "reset") setWaterDay(selected, index, "");
    else addWaterDay(selected, index, amount);
    if (currentView === "trackers") memberUxRenderTrackers();
    if (currentView === "client-home") memberUxRenderDashboard();
    if (memberUxDetail.type === "water") memberUxRenderDetail();
    await saveTrackerDay("water", index);
  }

  function memberUxHealthSettings(selected) {
    const entitlement = state?.entitlements?.clients?.[selected?.id] || {};
    const allowed = Boolean(entitlement.pro || entitlement.ai || entitlement.personalCoaching);
    return `
      <section class="member-ux-connection-card" aria-labelledby="member-ux-health-title">
        <div class="member-ux-card-head"><div><p class="eyebrow">${escapeHTML(memberUxText("connections"))}</p><h2 id="member-ux-health-title">${escapeHTML(memberUxText("healthSync"))}</h2></div><span class="status ${allowed ? "ok" : ""}">${escapeHTML(memberUxText(allowed ? "healthPlaceholder" : "healthLocked"))}</span></div>
        <p class="muted">${escapeHTML(memberUxText("healthExplanation"))}</p>
      </section>
    `;
  }

  function memberUxRenderSettings() {
    if (currentView !== "settings") return;
    memberUxOriginalRenderSettingsPage();
    if (!isLoggedIn() || state.ui.role !== "client" || currentView !== "settings") return;
    const selected = client();
    const target = document.getElementById("settingsOverview");
    if (!target || !hasSelectedClient(selected)) return;

    memberUxLegacyRenderClientHome();
    const onboarding = document.querySelector("#clientSummary .phase1-onboarding-panel");
    const onboardingMarkup = onboarding?.outerHTML || "";
    memberUxRenderDashboard();

    const layout = target.querySelector(".settings-layout") || target;
    if (onboardingMarkup) layout.insertAdjacentHTML("beforeend", onboardingMarkup);
    layout.insertAdjacentHTML("beforeend", memberUxHealthSettings(selected));
  }

  renderClientHome = memberUxRenderDashboard;
  renderTrackersOverview = memberUxRenderTrackers;
  renderSettingsPage = memberUxRenderSettings;

  renderSteps = function renderStepsMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "steps") return;
    return memberUxOriginalRenderers.steps();
  };
  renderProgress = function renderProgressMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "progress") return;
    return memberUxOriginalRenderers.progress();
  };
  renderWellbeing = function renderWellbeingMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "wellbeing") return;
    return memberUxOriginalRenderers.wellbeing();
  };
  renderSleep = function renderSleepMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "sleep") return;
    return memberUxOriginalRenderers.sleep();
  };
  renderWater = function renderWaterMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "water") return;
    return memberUxOriginalRenderers.water();
  };
  renderNutrition = function renderNutritionMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "nutrition") return;
    return memberUxOriginalRenderers.nutrition();
  };
  renderNutritionLog = function renderNutritionLogMemberBoundary() {
    if (isLoggedIn() && state.ui.role === "client" && currentView !== "nutrition") return;
    return memberUxOriginalRenderers.nutritionLog();
  };

  showView = function showViewMemberBoundary(id) {
    if (isLoggedIn() && state.ui.role === "client" && MEMBER_UX_LEGACY_TRACKER_VIEW_IDS.includes(id)) {
      id = "trackers";
    }
    const selectiveMemberView = isLoggedIn()
      && state.ui.role === "client"
      && ["client-home", "trackers"].includes(id)
      && currentView !== "training";
    if (!selectiveMemberView) return memberUxOriginalShowView(id);
    memberUxCloseDetail({ restoreFocus: false });
    currentView = id;
    document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === id));
    renderNav();
    renderWeekLabels();
    if (id === "client-home") memberUxRenderDashboard();
    if (id === "trackers") memberUxRenderTrackers();
  };

  renderAll = function renderAllMemberBoundary() {
    const result = memberUxOriginalRenderAll();
    const clientMode = isLoggedIn() && state.ui.role === "client";
    memberUxSetLegacyTrackerViewsHidden(clientMode);
    if (!clientMode) memberUxCloseDetail({ restoreFocus: false });
    return result;
  };

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    if (button.dataset.memberOpenDetail) {
      event.preventDefault();
      event.stopImmediatePropagation();
      memberUxOpenDetail(button.dataset.memberOpenDetail, button);
      return;
    }
    if (button.dataset.memberCloseDetail !== undefined) {
      event.preventDefault();
      event.stopImmediatePropagation();
      memberUxCloseDetail();
      return;
    }
    if (button.dataset.memberOpenView) {
      event.preventDefault();
      event.stopImmediatePropagation();
      memberUxCloseDetail({ restoreFocus: false });
      showView(button.dataset.memberOpenView);
      return;
    }
    if (button.dataset.memberOpenProfile !== undefined) {
      event.preventDefault();
      event.stopImmediatePropagation();
      showView("settings");
      document.getElementById("phase1OnboardingForm")?.querySelector("input, select, textarea")?.focus();
      return;
    }
    if (button.dataset.memberWaterAdjust !== undefined) {
      event.preventDefault();
      event.stopImmediatePropagation();
      await memberUxAdjustWater(Number(button.dataset.memberWaterIndex), button.dataset.memberWaterAdjust);
      return;
    }
    if (button.dataset.memberTrackerDay !== undefined && currentView === "trackers") {
      event.preventDefault();
      event.stopImmediatePropagation();
      state.ui.trackerDayIndex = Math.max(0, Math.min(6, Number(button.dataset.memberTrackerDay)));
      memberUxRenderTrackers();
      return;
    }
    if (button.dataset.memberWeekNav !== undefined && currentView === "trackers") {
      event.preventDefault();
      event.stopImmediatePropagation();
      state.ui.trackingWeekStart = button.dataset.memberWeekNav === "today"
        ? startOfWeekISO()
        : addDaysISO(activeWeekStart(), Number(button.dataset.memberWeekNav) * 7);
      state.ui.trackerDayIndex = state.ui.trackingWeekStart === startOfWeekISO() ? todayIndex() : 0;
      memberUxRenderTrackers();
      return;
    }
    if (button.dataset.memberSaveDetail) {
      event.preventDefault();
      event.stopImmediatePropagation();
      await memberUxSaveDetail(button.dataset.memberSaveDetail, button.dataset.memberSaveIndex);
    }
  }, true);

  document.addEventListener("change", async (event) => {
    const target = event.target;
    if (target.dataset.memberDetailDay !== undefined) {
      event.preventDefault();
      event.stopImmediatePropagation();
      memberUxDetail.dayIndex = Math.max(0, Math.min(6, Number(target.value)));
      memberUxDetail.photoDraft = {};
      memberUxRenderDetail();
      return;
    }
    if (target.dataset.memberProgressFile) {
      event.preventDefault();
      event.stopImmediatePropagation();
      const file = target.files?.[0];
      if (!file) return;
      if (!file.type.startsWith("image/") || file.size > 12 * 1024 * 1024) {
        target.value = "";
        return;
      }
      memberUxDetail.photoDraft[target.dataset.memberProgressFile] = await readImageFileAsDataURL(file);
      memberUxRenderDetail();
    }
  }, true);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && memberUxDetail.type) {
      event.preventDefault();
      memberUxCloseDetail();
    }
  });
})();
