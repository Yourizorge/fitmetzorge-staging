(function phase2HomeRecovery() {
  if (window.FMZ_PHASE2_HOME_RECOVERY_LOADED) return;
  window.FMZ_PHASE2_HOME_RECOVERY_LOADED = true;

  const PHASE2_VERSION = "20260816-phase2-step1";
  const PHASE2_LANGUAGES = ["nl", "en", "de"];
  const PHASE2_RECOVERY_SYNC_TYPES = ["steps", "sleep", "wellbeing", "training"];
  const PHASE2_NO_NATIVE_HEALTH_SYNC = true;

  const PHASE2_I18N = {
    nl: {
      navToday: "Vandaag",
      todayEyebrow: "Vandaag",
      todayTitle: "Goedemorgen {name}.",
      todayIntro: "Kijk kort naar je herstel, plan je belangrijkste acties en vul je recovery in.",
      nextActions: "Acties voor vandaag",
      startTraining: "Training bekijken",
      fillNutrition: "Voeding invullen",
      openTrackers: "Trackers openen",
      recoveryStatus: "Recovery status",
      recoveryComplete: "Vandaag compleet",
      recoveryPartial: "Gedeeltelijk ingevuld",
      recoveryEmpty: "Nog invullen",
      recoveryTitle: "Recovery check-in",
      recoveryIntro: "Handmatige input blijft beschikbaar zonder wearable of Health-koppeling.",
      recoveryWeekTitle: "Recovery weekoverzicht",
      recoveryWeekIntro: "Slaap, stappen, welzijn en recovery feeling worden genormaliseerd opgeslagen zodra de Phase 2 migration actief is.",
      saveRecovery: "Recovery opslaan",
      saving: "Opslaan...",
      saved: "Recovery opgeslagen",
      saveFailed: "Recovery opslaan mislukt: {message}",
      onlineRequired: "Online Supabase-opslag is nodig voor Phase 2 recovery persistence.",
      migrationNeeded: "Phase 2 recovery_logs migration is nog niet uitgevoerd.",
      steps: "Stappen",
      stepsToday: "Stappen vandaag",
      sleep: "Slaap",
      sleepHours: "Slaapuren",
      sleepQuality: "Slaapkwaliteit",
      wellbeing: "Welzijn",
      energy: "Energie",
      stress: "Stress",
      motivation: "Motivatie",
      mood: "Stemming",
      moodGood: "Goed",
      moodNeutral: "Neutraal",
      moodLow: "Laag",
      recoveryFeeling: "Recovery feeling",
      recoveryFeelingHelp: "Eigen gevoel 1-10, geen medische score.",
      recoveryNote: "Recovery notitie",
      recoveryNotePlaceholder: "Bijv. zware benen, goed geslapen, rustig aan vandaag...",
      trainingLoadTitle: "Training-load placeholder",
      trainingLoadIntro: "Gebaseerd op bestaande trainingsaanwezigheid. Dit is geen medische of gevalideerde herstelberekening.",
      trainingLoadUnknown: "Onvoldoende data",
      trainingLoadRest: "Rust / niet getraind",
      trainingLoadLight: "Training gepland",
      trainingLoadModerate: "Training gedaan",
      trainingLoadHeavy: "Zwaar nog niet bepaald",
      healthTitle: "Health-sync",
      healthFreeTitle: "Health-sync is Pro/AI",
      healthFreeIntro: "Free kan alles handmatig blijven invullen. Automatische Apple Health of Health Connect sync is hier nog niet actief.",
      healthProTitle: "Health-sync entry point",
      healthProIntro: "Je entitlement staat een Health-koppeling toe, maar native sync is in Phase 2 alleen een gecontroleerde placeholder.",
      healthLocked: "Locked",
      healthPlaceholder: "Placeholder",
      healthButtonLocked: "Upgrade nodig",
      healthButtonPlaceholder: "Nog niet actief",
      noNativeHealth: "Geen echte native Health-sync in Phase 2.",
      entitlementSource: "Entitlement via Phase 1 foundation",
      target: "Doel",
      filled: "Ingevuld",
      missing: "Mist nog",
      noData: "Geen data",
      of: "van",
      scoreScale: "Schaal 1-10",
      date: "Datum",
      trainingLoadLegacySource: "Bestaande trainingsdata",
      trainingLoadPlaceholderSource: "Placeholder",
      legacySaveFailed: "Legacy workspace opslag mislukt.",
      daySavedToSupabase: "Deze dag wordt opgeslagen in Supabase recovery_logs.",
      legacyBridge: "Legacy trackerdata blijft intact en wordt tijdelijk naast normalized recovery-data gebruikt."
    },
    en: {
      navToday: "Today",
      todayEyebrow: "Today",
      todayTitle: "Good morning {name}.",
      todayIntro: "Check your recovery, plan the key actions and fill in today's recovery.",
      nextActions: "Today's actions",
      startTraining: "View training",
      fillNutrition: "Fill nutrition",
      openTrackers: "Open trackers",
      recoveryStatus: "Recovery status",
      recoveryComplete: "Today complete",
      recoveryPartial: "Partly filled",
      recoveryEmpty: "Needs input",
      recoveryTitle: "Recovery check-in",
      recoveryIntro: "Manual input stays available without a wearable or Health connection.",
      recoveryWeekTitle: "Recovery week overview",
      recoveryWeekIntro: "Sleep, steps, wellbeing and recovery feeling are stored in normalized form once the Phase 2 migration is active.",
      saveRecovery: "Save recovery",
      saving: "Saving...",
      saved: "Recovery saved",
      saveFailed: "Recovery save failed: {message}",
      onlineRequired: "Online Supabase storage is required for Phase 2 recovery persistence.",
      migrationNeeded: "The Phase 2 recovery_logs migration has not been executed yet.",
      steps: "Steps",
      stepsToday: "Steps today",
      sleep: "Sleep",
      sleepHours: "Sleep hours",
      sleepQuality: "Sleep quality",
      wellbeing: "Wellbeing",
      energy: "Energy",
      stress: "Stress",
      motivation: "Motivation",
      mood: "Mood",
      moodGood: "Good",
      moodNeutral: "Neutral",
      moodLow: "Low",
      recoveryFeeling: "Recovery feeling",
      recoveryFeelingHelp: "Own feeling 1-10, not a medical score.",
      recoveryNote: "Recovery note",
      recoveryNotePlaceholder: "E.g. heavy legs, slept well, take it easy today...",
      trainingLoadTitle: "Training-load placeholder",
      trainingLoadIntro: "Based on existing training attendance. This is not a medical or validated recovery calculation.",
      trainingLoadUnknown: "Insufficient data",
      trainingLoadRest: "Rest / not trained",
      trainingLoadLight: "Training planned",
      trainingLoadModerate: "Training done",
      trainingLoadHeavy: "Heavy not determined",
      healthTitle: "Health sync",
      healthFreeTitle: "Health sync is Pro/AI",
      healthFreeIntro: "Free can keep using manual input. Automatic Apple Health or Health Connect sync is not active here yet.",
      healthProTitle: "Health sync entry point",
      healthProIntro: "Your entitlement allows a Health connection, but native sync is only a controlled placeholder in Phase 2.",
      healthLocked: "Locked",
      healthPlaceholder: "Placeholder",
      healthButtonLocked: "Upgrade needed",
      healthButtonPlaceholder: "Not active yet",
      noNativeHealth: "No real native Health sync in Phase 2.",
      entitlementSource: "Entitlement through Phase 1 foundation",
      target: "Target",
      filled: "Filled",
      missing: "Missing",
      noData: "No data",
      of: "of",
      scoreScale: "Scale 1-10",
      date: "Date",
      trainingLoadLegacySource: "Existing training data",
      trainingLoadPlaceholderSource: "Placeholder",
      legacySaveFailed: "Legacy workspace save failed.",
      daySavedToSupabase: "This day is stored in Supabase recovery_logs.",
      legacyBridge: "Legacy tracker data stays intact and temporarily exists next to normalized recovery data."
    },
    de: {
      navToday: "Heute",
      todayEyebrow: "Heute",
      todayTitle: "Guten Morgen {name}.",
      todayIntro: "Pruefe kurz deine Erholung, plane die wichtigsten Aktionen und fuelle deine Recovery aus.",
      nextActions: "Aktionen fuer heute",
      startTraining: "Training ansehen",
      fillNutrition: "Ernaehrung eintragen",
      openTrackers: "Tracker oeffnen",
      recoveryStatus: "Recovery-Status",
      recoveryComplete: "Heute komplett",
      recoveryPartial: "Teilweise ausgefuellt",
      recoveryEmpty: "Noch ausfuellen",
      recoveryTitle: "Recovery Check-in",
      recoveryIntro: "Manuelle Eingabe bleibt ohne Wearable oder Health-Verbindung verfuegbar.",
      recoveryWeekTitle: "Recovery Wochenuebersicht",
      recoveryWeekIntro: "Schlaf, Schritte, Wohlbefinden und Recovery Feeling werden normalisiert gespeichert, sobald die Phase 2 Migration aktiv ist.",
      saveRecovery: "Recovery speichern",
      saving: "Speichern...",
      saved: "Recovery gespeichert",
      saveFailed: "Recovery speichern fehlgeschlagen: {message}",
      onlineRequired: "Online-Supabase-Speicherung ist fuer Phase 2 Recovery Persistence erforderlich.",
      migrationNeeded: "Die Phase 2 recovery_logs Migration wurde noch nicht ausgefuehrt.",
      steps: "Schritte",
      stepsToday: "Schritte heute",
      sleep: "Schlaf",
      sleepHours: "Schlafstunden",
      sleepQuality: "Schlafqualitaet",
      wellbeing: "Wohlbefinden",
      energy: "Energie",
      stress: "Stress",
      motivation: "Motivation",
      mood: "Stimmung",
      moodGood: "Gut",
      moodNeutral: "Neutral",
      moodLow: "Niedrig",
      recoveryFeeling: "Recovery Feeling",
      recoveryFeelingHelp: "Eigenes Gefuehl 1-10, kein medizinischer Score.",
      recoveryNote: "Recovery Notiz",
      recoveryNotePlaceholder: "Z.B. schwere Beine, gut geschlafen, heute ruhiger...",
      trainingLoadTitle: "Training-Load Platzhalter",
      trainingLoadIntro: "Basierend auf bestehender Trainingsanwesenheit. Das ist keine medizinische oder validierte Erholungsberechnung.",
      trainingLoadUnknown: "Zu wenig Daten",
      trainingLoadRest: "Ruhe / nicht trainiert",
      trainingLoadLight: "Training geplant",
      trainingLoadModerate: "Training erledigt",
      trainingLoadHeavy: "Schwer noch nicht bestimmt",
      healthTitle: "Health-Sync",
      healthFreeTitle: "Health-Sync ist Pro/AI",
      healthFreeIntro: "Free kann alles weiter manuell eintragen. Automatische Apple Health oder Health Connect Sync ist hier noch nicht aktiv.",
      healthProTitle: "Health-Sync Einstieg",
      healthProIntro: "Deine Entitlement erlaubt eine Health-Verbindung, aber native Sync ist in Phase 2 nur ein kontrollierter Platzhalter.",
      healthLocked: "Gesperrt",
      healthPlaceholder: "Platzhalter",
      healthButtonLocked: "Upgrade noetig",
      healthButtonPlaceholder: "Noch nicht aktiv",
      noNativeHealth: "Kein echter nativer Health-Sync in Phase 2.",
      entitlementSource: "Entitlement ueber Phase 1 Foundation",
      target: "Ziel",
      filled: "Ausgefuellt",
      missing: "Fehlt noch",
      noData: "Keine Daten",
      of: "von",
      scoreScale: "Skala 1-10",
      date: "Datum",
      trainingLoadLegacySource: "Bestehende Trainingsdaten",
      trainingLoadPlaceholderSource: "Platzhalter",
      legacySaveFailed: "Legacy-Workspace-Speicherung fehlgeschlagen.",
      daySavedToSupabase: "Dieser Tag wird in Supabase recovery_logs gespeichert.",
      legacyBridge: "Legacy-Trackerdata bleibt intakt und wird temporaer neben normalisierten Recovery-Daten genutzt."
    }
  };

  window.FMZ_PHASE2_HOME_RECOVERY = {
    version: PHASE2_VERSION,
    surfaces: ["client_today", "manual_recovery", "health_placeholder"],
    recoveryTable: "recovery_logs",
    noNativeHealthSync: PHASE2_NO_NATIVE_HEALTH_SYNC
  };

  function phase2NormalizeLanguage(language) {
    return PHASE2_LANGUAGES.includes(language) ? language : "nl";
  }

  function phase2Language() {
    return phase2NormalizeLanguage(state?.accountSettings?.language || "nl");
  }

  function phase2Text(key) {
    const language = phase2Language();
    return PHASE2_I18N[language]?.[key] || PHASE2_I18N.nl[key] || key;
  }

  function phase2Format(key, values = {}) {
    let text = phase2Text(key);
    Object.entries(values).forEach(([name, value]) => {
      text = text.split(`{${name}}`).join(String(value ?? ""));
    });
    return text;
  }

  function phase2EnsureState() {
    state.phase2Recovery = state.phase2Recovery && typeof state.phase2Recovery === "object"
      ? state.phase2Recovery
      : {};
    state.phase2Recovery.logs = state.phase2Recovery.logs && typeof state.phase2Recovery.logs === "object"
      ? state.phase2Recovery.logs
      : {};
    return state.phase2Recovery;
  }

  function phase2RecoveryFeelingWeek(selected) {
    selected.recoveryFeelingByWeek = selected.recoveryFeelingByWeek && typeof selected.recoveryFeelingByWeek === "object"
      ? selected.recoveryFeelingByWeek
      : {};
    selected.recoveryFeelingByWeek[activeWeekStart()] = normalizeWeek(
      selected.recoveryFeelingByWeek[activeWeekStart()],
      "feeling",
      { note: "" }
    );
    return selected.recoveryFeelingByWeek[activeWeekStart()];
  }

  function phase2NumberOrNull(value, min, max, integer = false) {
    if (value === "" || value === null || value === undefined) return null;
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return null;
    const bounded = Math.max(min, Math.min(max, parsed));
    return integer ? Math.round(bounded) : bounded;
  }

  function phase2ScoreOptions(value) {
    return ["", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
      .map((option) => `<option value="${option}" ${String(option) === String(value || "") ? "selected" : ""}>${option || "-"}</option>`)
      .join("");
  }

  function phase2MoodOptions(value) {
    return [
      ["", "-"],
      ["Goed", phase2Text("moodGood")],
      ["Neutraal", phase2Text("moodNeutral")],
      ["Laag", phase2Text("moodLow")]
    ]
      .map(([option, label]) => `<option value="${escapeHTML(option)}" ${option === (value || "") ? "selected" : ""}>${escapeHTML(label)}</option>`)
      .join("");
  }

  function phase2ReadDay(selected, index) {
    const dates = weekDates(activeWeekStart());
    const day = dates[index] || dates[todayIndex()];
    const logs = phase2EnsureState().logs;
    const stored = logs[day.date] || {};
    const stepsEntry = weekArray(selected, "stepsByWeek", "value")[index] || {};
    const sleepEntry = weekArray(selected, "sleepByWeek", "hours", { quality: "", bed: "", wake: "" })[index] || {};
    const wellbeingEntry = weekArray(selected, "wellbeingByWeek", "energy", { stress: "", motivation: "", mood: "" })[index] || {};
    const feelingEntry = phase2RecoveryFeelingWeek(selected)[index] || {};
    const trainingLoad = phase2TrainingLoad(selected, index);
    return {
      index,
      day,
      logDate: day.date,
      steps: stored.steps ?? stepsEntry.value ?? "",
      sleepHours: stored.sleep_hours ?? sleepEntry.hours ?? "",
      sleepQuality: stored.sleep_quality ?? sleepEntry.quality ?? "",
      wellbeingEnergy: stored.wellbeing_energy ?? wellbeingEntry.energy ?? "",
      wellbeingStress: stored.wellbeing_stress ?? wellbeingEntry.stress ?? "",
      wellbeingMotivation: stored.wellbeing_motivation ?? wellbeingEntry.motivation ?? "",
      wellbeingMood: stored.wellbeing_mood ?? wellbeingEntry.mood ?? "",
      recoveryFeeling: stored.recovery_feeling ?? feelingEntry.feeling ?? "",
      recoveryNote: stored.recovery_note ?? feelingEntry.note ?? "",
      trainingLoadStatus: stored.training_load_status || trainingLoad.status,
      trainingLoadSource: stored.training_load_source || trainingLoad.source,
      trainingLoadLabel: phase2TrainingLoadLabel(stored.training_load_status || trainingLoad.status)
    };
  }

  function phase2LocalDayFromLegacy(selected, index) {
    const dates = weekDates(activeWeekStart());
    const day = dates[index] || dates[todayIndex()];
    const stepsEntry = weekArray(selected, "stepsByWeek", "value")[index] || {};
    const sleepEntry = weekArray(selected, "sleepByWeek", "hours", { quality: "", bed: "", wake: "" })[index] || {};
    const wellbeingEntry = weekArray(selected, "wellbeingByWeek", "energy", { stress: "", motivation: "", mood: "" })[index] || {};
    const feelingEntry = phase2RecoveryFeelingWeek(selected)[index] || {};
    const trainingLoad = phase2TrainingLoad(selected, index);
    return {
      index,
      day,
      logDate: day.date,
      steps: stepsEntry.value ?? "",
      sleepHours: sleepEntry.hours ?? "",
      sleepQuality: sleepEntry.quality ?? "",
      wellbeingEnergy: wellbeingEntry.energy ?? "",
      wellbeingStress: wellbeingEntry.stress ?? "",
      wellbeingMotivation: wellbeingEntry.motivation ?? "",
      wellbeingMood: wellbeingEntry.mood ?? "",
      recoveryFeeling: feelingEntry.feeling ?? "",
      recoveryNote: feelingEntry.note ?? "",
      trainingLoadStatus: trainingLoad.status,
      trainingLoadSource: trainingLoad.source
    };
  }

  function phase2ApplyDayToLegacy(selected, log) {
    if (!selected || !log?.log_date) return;
    const dates = weekDates(activeWeekStart());
    const index = dates.findIndex((item) => item.date === log.log_date);
    if (index < 0) return;
    if (log.steps !== null && log.steps !== undefined) {
      weekArray(selected, "stepsByWeek", "value")[index].value = log.steps;
    }
    const sleep = weekArray(selected, "sleepByWeek", "hours", { quality: "", bed: "", wake: "" })[index];
    if (log.sleep_hours !== null && log.sleep_hours !== undefined) sleep.hours = log.sleep_hours;
    if (log.sleep_quality !== null && log.sleep_quality !== undefined) sleep.quality = log.sleep_quality;
    const wellbeing = weekArray(selected, "wellbeingByWeek", "energy", { stress: "", motivation: "", mood: "" })[index];
    if (log.wellbeing_energy !== null && log.wellbeing_energy !== undefined) wellbeing.energy = log.wellbeing_energy;
    if (log.wellbeing_stress !== null && log.wellbeing_stress !== undefined) wellbeing.stress = log.wellbeing_stress;
    if (log.wellbeing_motivation !== null && log.wellbeing_motivation !== undefined) wellbeing.motivation = log.wellbeing_motivation;
    if (log.wellbeing_mood !== null && log.wellbeing_mood !== undefined) wellbeing.mood = log.wellbeing_mood;
    const feeling = phase2RecoveryFeelingWeek(selected)[index];
    if (log.recovery_feeling !== null && log.recovery_feeling !== undefined) feeling.feeling = log.recovery_feeling;
    if (log.recovery_note !== null && log.recovery_note !== undefined) feeling.note = log.recovery_note;
  }

  function phase2TrainingLoad(selected, index) {
    const attendance = trainingAttendanceWeek(selected)[index]?.status || "";
    if (attendance === "Geweest") {
      return { status: "moderate", source: "legacy_attendance" };
    }
    if (attendance === "Niet geweest") {
      return { status: "rest", source: "legacy_attendance" };
    }
    const day = DAYS[index] || "";
    const planned = (selected.trainingPlan || []).filter((item) => item.day === day && item.published !== false);
    if (planned.length) {
      return { status: "light", source: "phase2_placeholder" };
    }
    return { status: "unknown", source: "phase2_placeholder" };
  }

  function phase2TrainingLoadLabel(status) {
    const labels = {
      unknown: "trainingLoadUnknown",
      rest: "trainingLoadRest",
      light: "trainingLoadLight",
      moderate: "trainingLoadModerate",
      heavy: "trainingLoadHeavy"
    };
    return phase2Text(labels[status] || "trainingLoadUnknown");
  }

  function phase2RecoveryCompletion(log) {
    const checks = [
      log.steps !== "",
      log.sleepHours !== "",
      log.wellbeingEnergy !== "" || log.wellbeingStress !== "" || log.wellbeingMotivation !== "",
      log.recoveryFeeling !== ""
    ];
    const filled = checks.filter(Boolean).length;
    if (filled === checks.length) return { key: "recoveryComplete", className: "ok", filled };
    if (filled > 0) return { key: "recoveryPartial", className: "warn", filled };
    return { key: "recoveryEmpty", className: "", filled };
  }

  function phase2HealthAccess(selected) {
    const entitlement = state.entitlements?.clients?.[selected.id] || {};
    return Boolean(entitlement.pro || entitlement.ai || entitlement.personalCoaching);
  }

  function phase2HealthCard(selected) {
    const allowed = phase2HealthAccess(selected);
    return `
      <section class="phase2-card phase2-health-card">
        <div class="phase2-card-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase2Text("healthTitle"))}</p>
            <h2>${escapeHTML(phase2Text(allowed ? "healthProTitle" : "healthFreeTitle"))}</h2>
          </div>
          <span class="status ${allowed ? "ok" : ""}">${escapeHTML(phase2Text(allowed ? "healthPlaceholder" : "healthLocked"))}</span>
        </div>
        <p class="muted">${escapeHTML(phase2Text(allowed ? "healthProIntro" : "healthFreeIntro"))}</p>
        <p class="muted">${escapeHTML(phase2Text("noNativeHealth"))}</p>
        <button class="${allowed ? "secondary-btn" : "danger-btn"}" data-phase2-health-placeholder="true" type="button" disabled>${escapeHTML(phase2Text(allowed ? "healthButtonPlaceholder" : "healthButtonLocked"))}</button>
        <small class="muted">${escapeHTML(phase2Text("entitlementSource"))}</small>
      </section>
    `;
  }

  function phase2TrainingLoadCard(log) {
    return `
      <section class="phase2-card">
        <div class="phase2-card-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase2Text("trainingLoadTitle"))}</p>
            <h2>${escapeHTML(log.trainingLoadLabel)}</h2>
          </div>
          <span class="status">${escapeHTML(phase2Text(log.trainingLoadSource === "legacy_attendance" ? "trainingLoadLegacySource" : "trainingLoadPlaceholderSource"))}</span>
        </div>
        <p class="muted">${escapeHTML(phase2Text("trainingLoadIntro"))}</p>
      </section>
    `;
  }

  function phase2MetricCard(label, value, sub = "") {
    return `
      <section class="phase2-metric">
        <span>${escapeHTML(label)}</span>
        <strong>${escapeHTML(value === "" || value === null || value === undefined ? "-" : value)}</strong>
        <small>${escapeHTML(sub)}</small>
      </section>
    `;
  }

  function phase2InstallStyles() {
    if (document.getElementById("phase2-home-recovery-styles")) return;
    const style = document.createElement("style");
    style.id = "phase2-home-recovery-styles";
    style.textContent = `
      .phase2-today-shell { gap: 14px; }
      .phase2-hero,
      .phase2-card,
      .phase2-metric {
        border: 1px solid var(--line);
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(255,255,255,.08), rgba(255,255,255,.035));
        box-shadow: var(--shadow);
        padding: 18px;
      }
      .phase2-hero {
        display: grid;
        gap: 14px;
        border-color: rgba(215,178,77,.28);
        background: linear-gradient(145deg, rgba(215,178,77,.16), rgba(255,255,255,.055));
      }
      .phase2-hero h1 {
        max-width: 760px;
        margin: 0;
        font-size: clamp(34px, 7vw, 56px);
        line-height: .98;
        letter-spacing: 0;
      }
      .phase2-card-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
        margin-bottom: 10px;
      }
      .phase2-grid-two,
      .phase2-metric-grid {
        display: grid;
        gap: 14px;
      }
      .phase2-grid-two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .phase2-metric-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .phase2-metric {
        display: grid;
        gap: 6px;
        align-content: start;
      }
      .phase2-metric span,
      .phase2-metric small { color: var(--muted); font-weight: 800; }
      .phase2-metric strong {
        color: var(--text);
        font-size: 28px;
        line-height: 1;
      }
      .phase2-recovery-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .phase2-recovery-grid .wide { grid-column: 1 / -1; }
      .phase2-save-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
        margin-top: 12px;
      }
      .phase2-week-grid {
        display: grid;
        gap: 8px;
        overflow-x: auto;
      }
      .phase2-week-row {
        display: grid;
        grid-template-columns: 1.1fr .85fr .75fr .75fr .9fr 1.1fr;
        gap: 8px;
        align-items: center;
        min-width: 680px;
        padding: 10px;
        border-radius: 12px;
        background: rgba(255,255,255,.055);
      }
      .phase2-week-head {
        color: var(--muted);
        font-weight: 800;
      }
      body.light .phase2-hero,
      body.light .phase2-card,
      body.light .phase2-metric {
        background: #fff;
      }
      @media (max-width: 820px) {
        .phase2-grid-two,
        .phase2-metric-grid,
        .phase2-recovery-grid { grid-template-columns: 1fr; }
        .phase2-hero h1 { font-size: 38px; }
      }
    `;
    document.head.appendChild(style);
  }

  function phase2RecoveryForm(log) {
    return `
      <section class="phase2-card phase2-recovery-form-card">
        <div class="phase2-card-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase2Text("recoveryStatus"))}</p>
            <h2>${escapeHTML(phase2Text("recoveryTitle"))}</h2>
          </div>
          <span class="status">${escapeHTML(formatShortDate(log.logDate))}</span>
        </div>
        <p class="muted">${escapeHTML(phase2Text("recoveryIntro"))}</p>
        <div class="phase2-recovery-grid">
          <label class="field"><span>${escapeHTML(phase2Text("stepsToday"))}</span><input data-phase2-steps="${log.index}" type="number" min="0" value="${escapeHTML(log.steps || "")}" placeholder="10000" /></label>
          <label class="field"><span>${escapeHTML(phase2Text("sleepHours"))}</span><select data-phase2-sleep-hours="${log.index}">${trackerNumberOptions(log.sleepHours, 15, 0.5)}</select></label>
          <label class="field"><span>${escapeHTML(phase2Text("sleepQuality"))}</span><select data-phase2-sleep-quality="${log.index}">${phase2ScoreOptions(log.sleepQuality)}</select></label>
          <label class="field"><span>${escapeHTML(phase2Text("energy"))}</span><select data-phase2-wellbeing-energy="${log.index}">${phase2ScoreOptions(log.wellbeingEnergy)}</select></label>
          <label class="field"><span>${escapeHTML(phase2Text("stress"))}</span><select data-phase2-wellbeing-stress="${log.index}">${phase2ScoreOptions(log.wellbeingStress)}</select></label>
          <label class="field"><span>${escapeHTML(phase2Text("motivation"))}</span><select data-phase2-wellbeing-motivation="${log.index}">${phase2ScoreOptions(log.wellbeingMotivation)}</select></label>
          <label class="field"><span>${escapeHTML(phase2Text("mood"))}</span><select data-phase2-wellbeing-mood="${log.index}">${phase2MoodOptions(log.wellbeingMood)}</select></label>
          <label class="field"><span>${escapeHTML(phase2Text("recoveryFeeling"))}</span><select data-phase2-recovery-feeling="${log.index}">${phase2ScoreOptions(log.recoveryFeeling)}</select><small>${escapeHTML(phase2Text("recoveryFeelingHelp"))}</small></label>
          <label class="field wide"><span>${escapeHTML(phase2Text("recoveryNote"))}</span><textarea data-phase2-recovery-note="${log.index}" rows="3" placeholder="${escapeHTML(phase2Text("recoveryNotePlaceholder"))}">${escapeHTML(log.recoveryNote || "")}</textarea></label>
        </div>
        <div class="phase2-save-row">
          <button class="primary-btn" data-phase2-save-recovery="${log.index}" type="button">${escapeHTML(phase2Text("saveRecovery"))}</button>
          <span class="save-feedback" data-save-feedback="phase2-recovery-${log.index}"></span>
        </div>
        <small class="muted">${escapeHTML(phase2Text("daySavedToSupabase"))}</small>
      </section>
    `;
  }

  function phase2RenderTodayHub(selected) {
    const name = selected.name.split(" ")[0] || selected.name || phase2Text("navToday");
    const log = phase2ReadDay(selected, todayIndex());
    const completion = phase2RecoveryCompletion(log);
    const stepGoal = number(selected.goals?.steps, 10000) || 10000;
    const sleepGoal = number(selected.goals?.sleep, 8) || 8;
    const wellbeingGoal = number(selected.goals?.wellbeing, 8) || 8;
    return `
      <div class="phase2-today-shell client-preview-shell">
        <section class="phase2-hero">
          <div>
            <p class="eyebrow">${escapeHTML(phase2Text("todayEyebrow"))}</p>
            <h1>${escapeHTML(phase2Format("todayTitle", { name }))}</h1>
            <p class="muted">${escapeHTML(phase2Text("todayIntro"))}</p>
          </div>
          <span class="status ${completion.className}">${escapeHTML(phase2Text(completion.key))}</span>
          <div class="client-preview-actions">
            <button class="primary-btn" data-action="open-view" data-target="training" type="button">${escapeHTML(phase2Text("startTraining"))}</button>
            <button class="secondary-btn" data-action="open-view" data-target="nutrition" type="button">${escapeHTML(phase2Text("fillNutrition"))}</button>
            <button class="secondary-btn" data-action="open-view" data-target="trackers" type="button">${escapeHTML(phase2Text("openTrackers"))}</button>
          </div>
        </section>

        <div class="phase2-metric-grid">
          ${phase2MetricCard(phase2Text("steps"), fmt(log.steps), `${phase2Text("target")} ${fmt(stepGoal)}`)}
          ${phase2MetricCard(phase2Text("sleep"), log.sleepHours ? `${fmt(log.sleepHours, 1)}u` : "", `${phase2Text("target")} ${fmt(sleepGoal, 1)}u`)}
          ${phase2MetricCard(phase2Text("wellbeing"), log.wellbeingEnergy ? `${fmt(log.wellbeingEnergy)}/10` : "", `${phase2Text("target")} ${fmt(wellbeingGoal)}/10`)}
          ${phase2MetricCard(phase2Text("recoveryFeeling"), log.recoveryFeeling ? `${fmt(log.recoveryFeeling)}/10` : "", phase2Text("scoreScale"))}
        </div>

        ${phase2RecoveryForm(log)}

        <div class="phase2-grid-two">
          ${phase2TrainingLoadCard(log)}
          ${phase2HealthCard(selected)}
        </div>
      </div>
    `;
  }

  function phase2RenderRecoveryWeekPanel(selected) {
    const rows = weekDates(activeWeekStart()).map((day, index) => {
      const log = phase2ReadDay(selected, index);
      const completion = phase2RecoveryCompletion(log);
      return `
        <div class="phase2-week-row">
          <strong>${escapeHTML(day.day)}</strong>
          <span>${escapeHTML(formatShortDate(day.date))}</span>
          <span>${escapeHTML(log.sleepHours ? `${fmt(log.sleepHours, 1)}u` : "-")}</span>
          <span>${escapeHTML(log.steps ? fmt(log.steps) : "-")}</span>
          <span>${escapeHTML(log.recoveryFeeling ? `${fmt(log.recoveryFeeling)}/10` : "-")}</span>
          <span class="status ${completion.className}">${escapeHTML(phase2Text(completion.key))}</span>
        </div>
      `;
    }).join("");
    return `
      <section class="phase2-card phase2-week-card">
        <div class="phase2-card-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase2Text("recoveryStatus"))}</p>
            <h2>${escapeHTML(phase2Text("recoveryWeekTitle"))}</h2>
          </div>
          <span class="status">Phase 2</span>
        </div>
        <p class="muted">${escapeHTML(phase2Text("recoveryWeekIntro"))}</p>
        <div class="phase2-week-grid">
          <div class="phase2-week-row phase2-week-head">
            <strong>${escapeHTML(phase2Text("navToday"))}</strong>
            <span>${escapeHTML(phase2Text("date"))}</span>
            <span>${escapeHTML(phase2Text("sleep"))}</span>
            <span>${escapeHTML(phase2Text("steps"))}</span>
            <span>${escapeHTML(phase2Text("recoveryFeeling"))}</span>
            <span>${escapeHTML(phase2Text("recoveryStatus"))}</span>
          </div>
          ${rows}
        </div>
        <small class="muted">${escapeHTML(phase2Text("legacyBridge"))}</small>
      </section>
    `;
  }

  function phase2CollectRecoveryInputs(selected, index) {
    const steps = document.querySelector(`[data-phase2-steps="${index}"]`);
    const sleepHours = document.querySelector(`[data-phase2-sleep-hours="${index}"]`);
    const sleepQuality = document.querySelector(`[data-phase2-sleep-quality="${index}"]`);
    const wellbeingEnergy = document.querySelector(`[data-phase2-wellbeing-energy="${index}"]`);
    const wellbeingStress = document.querySelector(`[data-phase2-wellbeing-stress="${index}"]`);
    const wellbeingMotivation = document.querySelector(`[data-phase2-wellbeing-motivation="${index}"]`);
    const wellbeingMood = document.querySelector(`[data-phase2-wellbeing-mood="${index}"]`);
    const recoveryFeeling = document.querySelector(`[data-phase2-recovery-feeling="${index}"]`);
    const recoveryNote = document.querySelector(`[data-phase2-recovery-note="${index}"]`);
    const stepEntry = weekArray(selected, "stepsByWeek", "value")[index];
    const sleepEntry = weekArray(selected, "sleepByWeek", "hours", { quality: "", bed: "", wake: "" })[index];
    const wellbeingEntry = weekArray(selected, "wellbeingByWeek", "energy", { stress: "", motivation: "", mood: "" })[index];
    const feelingEntry = phase2RecoveryFeelingWeek(selected)[index];
    if (steps) stepEntry.value = steps.value;
    if (sleepHours) sleepEntry.hours = sleepHours.value;
    if (sleepQuality) sleepEntry.quality = sleepQuality.value;
    if (wellbeingEnergy) wellbeingEntry.energy = wellbeingEnergy.value;
    if (wellbeingStress) wellbeingEntry.stress = wellbeingStress.value;
    if (wellbeingMotivation) wellbeingEntry.motivation = wellbeingMotivation.value;
    if (wellbeingMood) wellbeingEntry.mood = wellbeingMood.value;
    if (recoveryFeeling) feelingEntry.feeling = recoveryFeeling.value;
    if (recoveryNote) feelingEntry.note = recoveryNote.value.trim();
  }

  function phase2BuildRecoveryPayload(selected, index) {
    const log = phase2LocalDayFromLegacy(selected, index);
    const trainingLoad = phase2TrainingLoad(selected, index);
    return {
      user_id: onlineProfile.id,
      log_date: log.logDate,
      sleep_hours: phase2NumberOrNull(log.sleepHours, 0, 24),
      sleep_quality: phase2NumberOrNull(log.sleepQuality, 1, 10, true),
      steps: phase2NumberOrNull(log.steps, 0, 200000, true),
      wellbeing_energy: phase2NumberOrNull(log.wellbeingEnergy, 1, 10, true),
      wellbeing_stress: phase2NumberOrNull(log.wellbeingStress, 1, 10, true),
      wellbeing_motivation: phase2NumberOrNull(log.wellbeingMotivation, 1, 10, true),
      wellbeing_mood: log.wellbeingMood || null,
      recovery_feeling: phase2NumberOrNull(log.recoveryFeeling, 1, 10, true),
      recovery_note: log.recoveryNote || null,
      training_load_status: trainingLoad.status,
      training_load_source: trainingLoad.source,
      source: "manual_phase2",
      metadata: {
        phase: "phase2",
        no_native_health_sync: PHASE2_NO_NATIVE_HEALTH_SYNC
      },
      updated_at: new Date().toISOString()
    };
  }

  async function phase2PersistRecoveryLog(selected, index) {
    if (!isOnlineMode() || !supabaseClient || !onlineProfile || onlineProfile.role !== "client") {
      return { ok: false, skipped: true, error: new Error(phase2Text("onlineRequired")) };
    }
    const payload = phase2BuildRecoveryPayload(selected, index);
    const { error } = await supabaseClient
      .from("recovery_logs")
      .upsert(payload, { onConflict: "user_id,log_date" });
    if (error) {
      const message = /recovery_logs|schema cache|not find|does not exist|relation/i.test(error.message || "")
        ? phase2Text("migrationNeeded")
        : error.message;
      return { ok: false, error: new Error(message) };
    }
    phase2EnsureState().logs[payload.log_date] = payload;
    return { ok: true, payload };
  }

  async function phase2SaveRecoveryDay(index) {
    const selected = client();
    const feedbackKey = `phase2-recovery-${index}`;
    if (!hasSelectedClient(selected)) {
      setSaveFeedback(feedbackKey, phase2Text("noData"), true);
      return;
    }
    setSaveFeedback(feedbackKey, phase2Text("saving"));
    try {
      phase2CollectRecoveryInputs(selected, index);
      saveState();
      if (!isOnlineMode() || !onlineReady || !onlineProfile) {
        throw new Error(phase2Text("onlineRequired"));
      }
      const result = await phase2PersistRecoveryLog(selected, index);
      if (!result.ok) throw result.error || new Error(phase2Text("onlineRequired"));
      if (onlineProfile.trainer_id) {
        const legacySave = await saveStateToCloud();
        if (!legacySave?.ok) throw legacySave?.error || new Error(phase2Text("legacySaveFailed"));
      }
      renderAll();
      setSaveFeedback(feedbackKey, phase2Text("saved"));
    } catch (error) {
      renderAll();
      setSaveFeedback(feedbackKey, phase2Format("saveFailed", { message: error.message }), true);
    }
  }

  async function phase2HydrateRecoveryLogs(profile) {
    if (!isOnlineMode() || !supabaseClient || !profile?.id || profile.role !== "client") return false;
    const selected = client();
    if (!hasSelectedClient(selected)) return false;
    const fromDate = addDaysISO(startOfWeekISO(), -28);
    const toDate = addDaysISO(startOfWeekISO(), 13);
    try {
      const { data, error } = await supabaseClient
        .from("recovery_logs")
        .select("user_id,log_date,sleep_hours,sleep_quality,steps,wellbeing_energy,wellbeing_stress,wellbeing_motivation,wellbeing_mood,recovery_feeling,recovery_note,training_load_status,training_load_source,source,updated_at")
        .eq("user_id", profile.id)
        .gte("log_date", fromDate)
        .lte("log_date", toDate)
        .order("log_date", { ascending: true });
      if (error) throw error;
      const phase2State = phase2EnsureState();
      (data || []).forEach((log) => {
        phase2State.logs[log.log_date] = log;
        phase2ApplyDayToLegacy(selected, log);
      });
      return true;
    } catch (error) {
      console.warn("Phase 2 recovery logs laden mislukt", error);
      return false;
    }
  }

  const phase2OriginalRenderNav = renderNav;
  renderNav = function renderNavPhase2() {
    const result = phase2OriginalRenderNav();
    const label = phase2Text("navToday");
    const home = NAV.client.find(([id]) => id === "client-home");
    if (home) home[1] = label;
    const buttonLabel = document.querySelector('.nav-btn[data-view="client-home"] span');
    const buttonIcon = document.querySelector('.nav-btn[data-view="client-home"] i');
    const currentLabel = document.querySelector(".nav-current span");
    if (buttonLabel) buttonLabel.textContent = label;
    if (buttonIcon) buttonIcon.textContent = label.slice(0, 1);
    if (currentView === "client-home" && currentLabel) currentLabel.textContent = label;
    return result;
  };

  const phase2OriginalRenderClientHome = renderClientHome;
  renderClientHome = function renderClientHomePhase2() {
    phase2InstallStyles();
    phase2OriginalRenderClientHome();
    const selected = client();
    if (!isLoggedIn() || state.ui.role !== "client" || !hasSelectedClient(selected)) return;
    const target = document.getElementById("clientSummary");
    if (!target) return;
    const oldShell = target.querySelector(".client-preview-shell");
    if (oldShell) oldShell.outerHTML = phase2RenderTodayHub(selected);
    else target.insertAdjacentHTML("beforeend", phase2RenderTodayHub(selected));
  };

  const phase2OriginalRenderTrackersOverview = renderTrackersOverview;
  renderTrackersOverview = function renderTrackersOverviewPhase2() {
    phase2InstallStyles();
    phase2OriginalRenderTrackersOverview();
    if (!isLoggedIn() || state.ui.role !== "client") return;
    const selected = client();
    const target = document.getElementById("trackerOverview");
    if (!target || !hasSelectedClient(selected)) return;
    target.insertAdjacentHTML("afterbegin", phase2RenderRecoveryWeekPanel(selected));
  };

  const phase2OriginalLoadOnlineWorkspace = loadOnlineWorkspace;
  loadOnlineWorkspace = async function loadOnlineWorkspacePhase2(profile) {
    await phase2OriginalLoadOnlineWorkspace(profile);
    const hydrated = await phase2HydrateRecoveryLogs(profile);
    if (hydrated) {
      const previousHydrating = hydratingFromCloud;
      hydratingFromCloud = true;
      try {
        renderAll();
        showView(currentView);
      } finally {
        hydratingFromCloud = previousHydrating;
      }
    }
  };

  const phase2OriginalSaveTrackerDay = saveTrackerDay;
  saveTrackerDay = async function saveTrackerDayPhase2(type, index) {
    await phase2OriginalSaveTrackerDay(type, index);
    if (!PHASE2_RECOVERY_SYNC_TYPES.includes(type)) return;
    if (!isLoggedIn() || state.ui.role !== "client") return;
    const selected = client();
    if (!hasSelectedClient(selected)) return;
    const result = await phase2PersistRecoveryLog(selected, Number(index));
    if (!result.ok && !result.skipped) {
      setSaveFeedback(`${type}-${index}`, phase2Format("saveFailed", { message: result.error.message }), true);
    }
  };

  document.addEventListener("click", (event) => {
    const saveButton = event.target.closest("[data-phase2-save-recovery]");
    if (!saveButton) return;
    event.preventDefault();
    phase2SaveRecoveryDay(Number(saveButton.dataset.phase2SaveRecovery));
  });
})();
