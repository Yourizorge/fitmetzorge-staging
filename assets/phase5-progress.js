(() => {
  if (window.FMZ_PHASE5_PROGRESS_LOADED) return;
  window.FMZ_PHASE5_PROGRESS_LOADED = true;

  const PHASE5_VERSION = "20260831-phase5-progress1";
  const PHASE5_LANGUAGES = ["nl", "en", "de"];
  const KG_TO_LB = 2.2046226218;
  const CM_TO_IN = 1 / 2.54;
  const PHASE5_I18N = {
    nl: {
      nav: "Progressie", title: "Progressie", intro: "Je ontwikkeling in een rustig overzicht.",
      loading: "Progressie laden...", retry: "Opnieuw proberen", noData: "Nog geen gegevens",
      fullHistory: "Volledige historie", freeHistory: "Laatste 30 dagen", historyLocked: "Oudere historie is beschikbaar met Pro, AI of coaching.",
      goal: "Mijn doel", setGoal: "Doel instellen", editGoal: "Doel aanpassen", goalProgress: "Voortgang naar doel",
      goalFatLoss: "Vet verliezen", goalMuscle: "Spiermassa opbouwen", goalStrength: "Sterker worden",
      goalConditioning: "Conditie verbeteren", goalRunning: "Hardlopen verbeteren", goalHealth: "Gezonder leven", goalMaintenance: "Gewicht behouden",
      baselineWeight: "Startgewicht", targetWeight: "Doelgewicht", targetDate: "Streefdatum", notes: "Notitie",
      weight: "Gewicht", addWeight: "Gewicht invullen", editWeight: "Gewicht corrigeren", currentWeight: "Huidig gewicht",
      trend: "7-metingen trend", rawValue: "Ruwe meting", change: "Verschil", date: "Datum", save: "Opslaan", cancel: "Sluiten",
      measurements: "Lichaamsmetingen", addMeasurement: "Meting invullen", editMeasurement: "Meting corrigeren",
      waist: "Taille", chest: "Borst", hips: "Heupen", armLeft: "Bovenarm links", armRight: "Bovenarm rechts", thighLeft: "Bovenbeen links", thighRight: "Bovenbeen rechts",
      strength: "Krachtprogressie", estimatedOneRm: "Geschatte 1RM", maxWeight: "Max. gewicht", completedSets: "sets",
      consistency: "Trainingsritme", last7: "Laatste 7 dagen", last30: "Laatste 30 dagen", completedWorkouts: "voltooide trainingen",
      context: "Samenhang", recovery: "Herstel", nutrition: "Voeding", running: "Hardlopen en conditie",
      recoverySummary: "{days} dagen gelogd · gemiddeld {sleep} slaap · {steps} stappen",
      nutritionSummary: "{days} dagen gelogd · gemiddeld {kcal} kcal · {protein} eiwit",
      runningUnavailable: "Nog geen betrouwbare hardloop- of activiteitbron gekoppeld.",
      insufficientTrend: "Vul minimaal twee metingen in om een trend te zien.",
      bmiContext: "BMI als context", bmiDisclaimer: "BMI is een globale verhouding, geen lichaamssamenstelling of gezondheidsoordeel.",
      history: "Historie en ruwe waarden", archive: "Archiveren", archiveConfirm: "Deze invoer uit het actieve overzicht halen? De revisiehistorie blijft bewaard.",
      metric: "Metrisch", imperial: "Imperiaal", units: "Eenheden", kg: "kg", lb: "lb", cm: "cm", inch: "in",
      saved: "Opgeslagen", archived: "Gearchiveerd", stale: "Deze invoer is elders gewijzigd. De nieuwste versie is geladen.",
      validation: "Controleer de ingevulde waarden.", authRequired: "Log opnieuw in om Progressie te gebruiken.", onlineRequired: "Progressie heeft een beveiligde online verbinding nodig.",
      photos: "Progressiefoto's", photosGate: "Foto's volgen via een aparte private privacy- en opslagstap.",
      goalNeeded: "Stel je doel in om doelvoortgang te zien.", maintenanceDistance: "Afstand tot doelgewicht",
      current: "Nu", averageSleepUnknown: "slaap onbekend", stepsUnknown: "stappen onbekend", kcalUnknown: "kcal onbekend", proteinUnknown: "eiwit onbekend",
      previousPeriod: "Eerdere periode", newestPeriod: "Nieuwste periode", edit: "Bewerken", emptyMeasurements: "Nog geen lichaamsmetingen.", emptyStrength: "Voltooi sets met gewicht en herhalingen om krachtprogressie te zien.",
      updated: "Bijgewerkt", loadError: "Progressie kon niet worden geladen.", saveError: "Opslaan is niet gelukt.",
      goalOptionalWeight: "Gewichtsvelden zijn optioneel voor dit doel.", requiredMeasurement: "Vul minimaal een lichaamsmeting in."
    },
    en: {
      nav: "Progress", title: "Progress", intro: "Your development in a calm overview.",
      loading: "Loading progress...", retry: "Try again", noData: "No data yet",
      fullHistory: "Full history", freeHistory: "Last 30 days", historyLocked: "Older history is available with Pro, AI or coaching.",
      goal: "My goal", setGoal: "Set goal", editGoal: "Edit goal", goalProgress: "Goal progress",
      goalFatLoss: "Lose fat", goalMuscle: "Build muscle", goalStrength: "Get stronger", goalConditioning: "Improve conditioning", goalRunning: "Improve running", goalHealth: "Live healthier", goalMaintenance: "Maintain weight",
      baselineWeight: "Starting weight", targetWeight: "Target weight", targetDate: "Target date", notes: "Note",
      weight: "Weight", addWeight: "Add weight", editWeight: "Correct weight", currentWeight: "Current weight", trend: "7-entry trend", rawValue: "Raw entry", change: "Change", date: "Date", save: "Save", cancel: "Close",
      measurements: "Body measurements", addMeasurement: "Add measurement", editMeasurement: "Correct measurement", waist: "Waist", chest: "Chest", hips: "Hips", armLeft: "Left upper arm", armRight: "Right upper arm", thighLeft: "Left thigh", thighRight: "Right thigh",
      strength: "Strength progress", estimatedOneRm: "Estimated 1RM", maxWeight: "Max weight", completedSets: "sets",
      consistency: "Training consistency", last7: "Last 7 days", last30: "Last 30 days", completedWorkouts: "completed workouts",
      context: "Combined context", recovery: "Recovery", nutrition: "Nutrition", running: "Running and conditioning",
      recoverySummary: "{days} days logged · average {sleep} sleep · {steps} steps", nutritionSummary: "{days} days logged · average {kcal} kcal · {protein} protein", runningUnavailable: "No authoritative running or activity source is connected yet.",
      insufficientTrend: "Add at least two entries to see a trend.", bmiContext: "BMI as context", bmiDisclaimer: "BMI is a broad ratio, not body composition or a health judgement.",
      history: "History and raw values", archive: "Archive", archiveConfirm: "Remove this entry from the active overview? Revision history remains preserved.", metric: "Metric", imperial: "Imperial", units: "Units", kg: "kg", lb: "lb", cm: "cm", inch: "in",
      saved: "Saved", archived: "Archived", stale: "This entry changed elsewhere. The latest version is loaded.", validation: "Check the entered values.", authRequired: "Sign in again to use Progress.", onlineRequired: "Progress needs a secure online connection.",
      photos: "Progress photos", photosGate: "Photos follow through a separate private privacy and storage step.", goalNeeded: "Set your goal to see goal progress.", maintenanceDistance: "Distance to target weight",
      current: "Now", averageSleepUnknown: "sleep unknown", stepsUnknown: "steps unknown", kcalUnknown: "kcal unknown", proteinUnknown: "protein unknown", previousPeriod: "Earlier period", newestPeriod: "Newest period", edit: "Edit", emptyMeasurements: "No body measurements yet.", emptyStrength: "Complete weighted sets to see strength progress.",
      updated: "Updated", loadError: "Progress could not be loaded.", saveError: "Saving failed.", goalOptionalWeight: "Weight fields are optional for this goal.", requiredMeasurement: "Enter at least one body measurement."
    },
    de: {
      nav: "Fortschritt", title: "Fortschritt", intro: "Deine Entwicklung in einer ruhigen Uebersicht.",
      loading: "Fortschritt wird geladen...", retry: "Erneut versuchen", noData: "Noch keine Daten",
      fullHistory: "Gesamter Verlauf", freeHistory: "Letzte 30 Tage", historyLocked: "Aeltere Daten sind mit Pro, AI oder Coaching verfuegbar.",
      goal: "Mein Ziel", setGoal: "Ziel festlegen", editGoal: "Ziel anpassen", goalProgress: "Zielfortschritt",
      goalFatLoss: "Fett verlieren", goalMuscle: "Muskeln aufbauen", goalStrength: "Staerker werden", goalConditioning: "Kondition verbessern", goalRunning: "Laufleistung verbessern", goalHealth: "Gesuender leben", goalMaintenance: "Gewicht halten",
      baselineWeight: "Startgewicht", targetWeight: "Zielgewicht", targetDate: "Zieldatum", notes: "Notiz",
      weight: "Gewicht", addWeight: "Gewicht eintragen", editWeight: "Gewicht korrigieren", currentWeight: "Aktuelles Gewicht", trend: "Trend aus 7 Eintraegen", rawValue: "Rohwert", change: "Aenderung", date: "Datum", save: "Speichern", cancel: "Schliessen",
      measurements: "Koerpermasse", addMeasurement: "Messung eintragen", editMeasurement: "Messung korrigieren", waist: "Taille", chest: "Brust", hips: "Huefte", armLeft: "Oberarm links", armRight: "Oberarm rechts", thighLeft: "Oberschenkel links", thighRight: "Oberschenkel rechts",
      strength: "Kraftfortschritt", estimatedOneRm: "Geschaetztes 1RM", maxWeight: "Max. Gewicht", completedSets: "Saetze",
      consistency: "Trainingsrhythmus", last7: "Letzte 7 Tage", last30: "Letzte 30 Tage", completedWorkouts: "abgeschlossene Trainings",
      context: "Zusammenhang", recovery: "Erholung", nutrition: "Ernaehrung", running: "Laufen und Kondition", recoverySummary: "{days} Tage erfasst · im Mittel {sleep} Schlaf · {steps} Schritte", nutritionSummary: "{days} Tage erfasst · im Mittel {kcal} kcal · {protein} Protein", runningUnavailable: "Noch keine verlaessliche Lauf- oder Aktivitaetsquelle verbunden.",
      insufficientTrend: "Trage mindestens zwei Werte ein, um einen Trend zu sehen.", bmiContext: "BMI als Kontext", bmiDisclaimer: "BMI ist ein grobes Verhaeltnis, keine Koerperzusammensetzung oder Gesundheitsbewertung.",
      history: "Verlauf und Rohwerte", archive: "Archivieren", archiveConfirm: "Diesen Eintrag aus der aktiven Uebersicht entfernen? Der Revisionsverlauf bleibt erhalten.", metric: "Metrisch", imperial: "Imperial", units: "Einheiten", kg: "kg", lb: "lb", cm: "cm", inch: "in",
      saved: "Gespeichert", archived: "Archiviert", stale: "Dieser Eintrag wurde anderswo geaendert. Die neueste Version wurde geladen.", validation: "Pruefe die Eingaben.", authRequired: "Melde dich erneut an, um Fortschritt zu nutzen.", onlineRequired: "Fortschritt benoetigt eine sichere Online-Verbindung.",
      photos: "Fortschrittsfotos", photosGate: "Fotos folgen ueber einen separaten privaten Datenschutz- und Speicherschritt.", goalNeeded: "Lege dein Ziel fest, um Zielfortschritt zu sehen.", maintenanceDistance: "Abstand zum Zielgewicht",
      current: "Jetzt", averageSleepUnknown: "Schlaf unbekannt", stepsUnknown: "Schritte unbekannt", kcalUnknown: "kcal unbekannt", proteinUnknown: "Protein unbekannt", previousPeriod: "Frueherer Zeitraum", newestPeriod: "Neuester Zeitraum", edit: "Bearbeiten", emptyMeasurements: "Noch keine Koerpermasse.", emptyStrength: "Schliesse gewichtete Saetze ab, um Kraftfortschritt zu sehen.",
      updated: "Aktualisiert", loadError: "Fortschritt konnte nicht geladen werden.", saveError: "Speichern fehlgeschlagen.", goalOptionalWeight: "Gewichtsfelder sind fuer dieses Ziel optional.", requiredMeasurement: "Trage mindestens ein Koerpermass ein."
    }
  };

  const phase5State = {
    profileId: "", loaded: false, loading: false, error: "", data: null,
    beforeDate: null, modal: "", modalDate: "", opener: null,
    timezoneInitializedFor: "", notice: "", pending: false
  };

  function phase5Language() {
    const value = state?.accountSettings?.language || "nl";
    return PHASE5_LANGUAGES.includes(value) ? value : "nl";
  }

  function phase5Text(key) {
    const language = phase5Language();
    return PHASE5_I18N[language]?.[key] || PHASE5_I18N.nl[key] || key;
  }

  function phase5Format(key, values = {}) {
    let result = phase5Text(key);
    Object.entries(values).forEach(([name, value]) => {
      result = result.split(`{${name}}`).join(String(value ?? ""));
    });
    return result;
  }

  function phase5Locale() {
    return { nl: "nl-NL", en: "en-GB", de: "de-DE" }[phase5Language()] || "nl-NL";
  }

  function phase5Escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[character]);
  }

  function phase5Number(value, digits = 1) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "-";
    return new Intl.NumberFormat(phase5Locale(), { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(numeric);
  }

  function phase5Date(value, options = { day: "numeric", month: "short", year: "numeric" }) {
    const parsed = new Date(`${value}T12:00:00`);
    return Number.isNaN(parsed.getTime()) ? String(value || "") : parsed.toLocaleDateString(phase5Locale(), options);
  }

  function phase5Today() {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(new Date());
    const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${map.year}-${map.month}-${map.day}`;
  }

  function phase5Timezone() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  }

  function phase5OffsetMinutes(dateValue) {
    return -new Date(`${dateValue}T12:00:00`).getTimezoneOffset();
  }

  function phase5Uuid() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
      const random = Math.floor(Math.random() * 16);
      return (char === "x" ? random : (random & 3) | 8).toString(16);
    });
  }

  function phase5UnitSystem() {
    return phase5State.data?.unit_system === "imperial" ? "imperial" : "metric";
  }

  function phase5WeightValue(kg) {
    const value = Number(kg);
    if (!Number.isFinite(value)) return null;
    return phase5UnitSystem() === "imperial" ? value * KG_TO_LB : value;
  }

  function phase5WeightKg(displayValue) {
    const value = Number(displayValue);
    if (!Number.isFinite(value)) return null;
    return phase5UnitSystem() === "imperial" ? value / KG_TO_LB : value;
  }

  function phase5LengthValue(cm) {
    const value = Number(cm);
    if (!Number.isFinite(value)) return null;
    return phase5UnitSystem() === "imperial" ? value * CM_TO_IN : value;
  }

  function phase5LengthCm(displayValue) {
    const value = Number(displayValue);
    if (!Number.isFinite(value)) return null;
    return phase5UnitSystem() === "imperial" ? value / CM_TO_IN : value;
  }

  function phase5WeightLabel(kg, digits = 1) {
    const value = phase5WeightValue(kg);
    return value === null ? "-" : `${phase5Number(value, digits)} ${phase5Text(phase5UnitSystem() === "imperial" ? "lb" : "kg")}`;
  }

  function phase5LengthLabel(cm) {
    const value = phase5LengthValue(cm);
    return value === null ? "-" : `${phase5Number(value, 1)} ${phase5Text(phase5UnitSystem() === "imperial" ? "inch" : "cm")}`;
  }

  function phase5GoalLabel(code) {
    return ({
      fat_loss: "goalFatLoss", muscle_gain: "goalMuscle", strength: "goalStrength",
      conditioning: "goalConditioning", running: "goalRunning",
      healthier_living: "goalHealth", weight_maintenance: "goalMaintenance"
    })[code] ? phase5Text(({
      fat_loss: "goalFatLoss", muscle_gain: "goalMuscle", strength: "goalStrength",
      conditioning: "goalConditioning", running: "goalRunning",
      healthier_living: "goalHealth", weight_maintenance: "goalMaintenance"
    })[code]) : phase5Text("goal");
  }

  function phase5Latest(items = []) {
    return items.length ? items[items.length - 1] : null;
  }

  function phase5GoalProgress() {
    const goal = phase5State.data?.goal;
    const current = Number(phase5Latest(phase5State.data?.weights)?.weight_kg);
    const baseline = Number(goal?.baseline_weight_kg);
    const target = Number(goal?.target_weight_kg);
    if (!goal || !Number.isFinite(current) || !Number.isFinite(baseline) || !Number.isFinite(target) || baseline === target) return null;
    const raw = ((current - baseline) / (target - baseline)) * 100;
    return { raw, display: Math.max(0, Math.min(100, raw)), current, baseline, target };
  }

  function phase5ErrorMessage(error, fallback = "saveError") {
    const message = String(error?.message || "");
    if (/progress_stale_conflict/i.test(message)) return phase5Text("stale");
    if (/history_locked/i.test(message)) return phase5Text("historyLocked");
    if (/jwt|auth|session|42501/i.test(message)) return phase5Text("authRequired");
    if (/constraint|range|required|invalid|22023|23514/i.test(message)) return phase5Text("validation");
    return phase5Text(fallback);
  }

  function phase5InstallStyles() {
    if (document.getElementById("phase5-progress-styles")) return;
    const style = document.createElement("style");
    style.id = "phase5-progress-styles";
    style.textContent = `
      #progress.phase5-progress-active { display: none; }
      #progress.phase5-progress-active.active { display: block; }
      .phase5-shell { display: grid; gap: 14px; padding-bottom: calc(var(--member-bottom-nav-reserve, 96px) + env(safe-area-inset-bottom)); }
      .phase5-hero, .phase5-section { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); padding: 14px; min-width: 0; }
      .phase5-hero { display: grid; gap: 12px; border-color: rgba(215,178,77,.5); }
      .phase5-head, .phase5-section-head, .phase5-actions, .phase5-unit-toggle, .phase5-history-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
      .phase5-head h1, .phase5-section h2, .phase5-section h3 { margin: 0; letter-spacing: 0; }
      .phase5-head h1 { font-size: 28px; line-height: 1.15; }
      .phase5-section { display: grid; gap: 12px; }
      .phase5-grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
      .phase5-metrics { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; }
      .phase5-metric { display: grid; gap: 3px; min-width: 0; }
      .phase5-metric span, .phase5-metric small { color: var(--muted); font-size: 12px; font-weight: 750; }
      .phase5-metric strong { font-size: 20px; line-height: 1.15; overflow-wrap: anywhere; }
      .phase5-progress-track { height: 9px; border-radius: 5px; overflow: hidden; background: rgba(255,255,255,.1); }
      .phase5-progress-track span { display: block; width: var(--phase5-progress,0%); height: 100%; background: var(--gold); }
      .phase5-chart { width: 100%; aspect-ratio: 16 / 7; max-height: 230px; overflow: visible; }
      .phase5-chart .grid { stroke: rgba(255,255,255,.1); stroke-width: 1; }
      .phase5-chart .raw { fill: none; stroke: #d7b24d; stroke-width: 2.5; vector-effect: non-scaling-stroke; }
      .phase5-chart .trend { fill: none; stroke: #4fa7a1; stroke-width: 3; vector-effect: non-scaling-stroke; }
      .phase5-chart .dot { fill: #d7b24d; }
      .phase5-legend { display: flex; flex-wrap: wrap; gap: 12px; color: var(--muted); font-size: 12px; font-weight: 750; }
      .phase5-legend span::before { content: ""; display: inline-block; width: 16px; height: 3px; margin-right: 6px; vertical-align: middle; background: #d7b24d; }
      .phase5-legend .trend::before { background: #4fa7a1; }
      .phase5-list { display: grid; gap: 8px; }
      .phase5-list-row { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 10px; align-items: center; border-top: 1px solid var(--line); padding-top: 9px; }
      .phase5-list-row:first-child { border-top: 0; padding-top: 0; }
      .phase5-list-row p, .phase5-section p { margin: 0; }
      .phase5-context { display: grid; gap: 10px; }
      .phase5-context-item { border-left: 3px solid #4fa7a1; padding-left: 10px; }
      .phase5-context-item strong { display: block; margin-bottom: 3px; }
      .phase5-table-wrap { overflow-x: auto; }
      .phase5-table { width: 100%; border-collapse: collapse; min-width: 520px; }
      .phase5-table th, .phase5-table td { padding: 9px 8px; border-bottom: 1px solid var(--line); text-align: left; }
      .phase5-table th { color: var(--muted); font-size: 12px; }
      .phase5-details > summary { cursor: pointer; min-height: 44px; display: flex; align-items: center; font-weight: 800; }
      .phase5-actions { justify-content: flex-start; flex-wrap: wrap; }
      .phase5-actions button, .phase5-unit-toggle button { min-height: 44px; }
      .phase5-unit-toggle { justify-content: flex-start; }
      .phase5-unit-toggle button[aria-pressed="true"] { border-color: var(--gold); color: var(--gold); }
      .phase5-notice { border: 1px solid rgba(79,167,161,.55); border-radius: 8px; padding: 10px; }
      .phase5-error { border-color: rgba(220,80,80,.6); }
      .phase5-photo-gate { border-style: dashed; }
      .phase5-portal { position: fixed; inset: 0; z-index: 96; display: grid; align-items: end; }
      .phase5-backdrop { position: absolute; inset: 0; border: 0; background: rgba(0,0,0,.7); }
      .phase5-sheet { position: relative; width: 100%; max-height: 94dvh; overflow-y: auto; background: var(--bg); border: 1px solid var(--line); border-radius: 8px 8px 0 0; padding: 16px 16px calc(24px + env(safe-area-inset-bottom)); }
      .phase5-sheet-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
      .phase5-sheet-head h2 { margin: 0; font-size: 22px; }
      .phase5-form { display: grid; gap: 12px; }
      .phase5-form-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 10px; }
      .phase5-form-grid .wide { grid-column: 1 / -1; }
      .phase5-close { width: 44px; height: 44px; padding: 0; flex: none; font-size: 22px; }
      body.phase5-modal-open { overflow: hidden; }
      @media (min-width: 760px) {
        .phase5-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
        .phase5-wide { grid-column: 1 / -1; }
        .phase5-portal { align-items: center; justify-items: center; padding: 24px; }
        .phase5-sheet { max-width: 720px; max-height: 88dvh; border-radius: 8px; }
      }
      @media (max-width: 359px) {
        .phase5-head, .phase5-section-head, .phase5-history-row { align-items: stretch; flex-direction: column; }
        .phase5-form-grid, .phase5-metrics { grid-template-columns: 1fr; }
        .phase5-form-grid .wide { grid-column: auto; }
        .phase5-head h1 { font-size: 25px; }
      }
    `;
    document.head.appendChild(style);
  }

  function phase5EnsureNav() {
    if (!Array.isArray(NAV?.client)) return;
    const existing = NAV.client.find((item) => item[0] === "progress");
    if (existing) existing[1] = phase5Text("nav");
    else {
      const nutritionIndex = NAV.client.findIndex((item) => item[0] === "nutrition");
      NAV.client.splice(Math.max(0, nutritionIndex + 1), 0, ["progress", phase5Text("nav")]);
    }
  }

  function phase5LineChart(weights) {
    if (!Array.isArray(weights) || weights.length < 2) return `<p class="muted">${phase5Escape(phase5Text("insufficientTrend"))}</p>`;
    const rows = weights.slice(-30);
    const values = rows.flatMap((item) => [Number(item.weight_kg), Number(item.trend_kg)]).filter(Number.isFinite);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const spread = Math.max(1, max - min);
    const point = (value, index) => {
      const x = 16 + (index / Math.max(1, rows.length - 1)) * 288;
      const y = 132 - ((Number(value) - min) / spread) * 112;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    };
    const raw = rows.map((item, index) => point(item.weight_kg, index)).join(" ");
    const trend = rows.map((item, index) => point(item.trend_kg ?? item.weight_kg, index)).join(" ");
    const label = `${phase5Text("weight")}: ${rows.map((item) => `${phase5Date(item.log_date)} ${phase5WeightLabel(item.weight_kg)}`).join(", ")}`;
    return `
      <svg class="phase5-chart" viewBox="0 0 320 150" role="img" aria-label="${phase5Escape(label)}" preserveAspectRatio="none">
        <line class="grid" x1="16" y1="20" x2="304" y2="20"></line>
        <line class="grid" x1="16" y1="76" x2="304" y2="76"></line>
        <line class="grid" x1="16" y1="132" x2="304" y2="132"></line>
        <polyline class="raw" points="${raw}"></polyline>
        <polyline class="trend" points="${trend}"></polyline>
        ${rows.map((item, index) => `<circle class="dot" cx="${point(item.weight_kg, index).split(",")[0]}" cy="${point(item.weight_kg, index).split(",")[1]}" r="3"></circle>`).join("")}
      </svg>
      <div class="phase5-legend"><span>${phase5Escape(phase5Text("rawValue"))}</span><span class="trend">${phase5Escape(phase5Text("trend"))}</span></div>
    `;
  }

  function phase5GoalCard() {
    const goal = phase5State.data?.goal;
    const latest = phase5Latest(phase5State.data?.weights || []);
    const progress = phase5GoalProgress();
    if (!goal) return `
      <section class="phase5-section" aria-labelledby="phase5-goal-title">
        <div class="phase5-section-head"><h2 id="phase5-goal-title">${phase5Escape(phase5Text("goal"))}</h2></div>
        <p class="muted">${phase5Escape(phase5Text("goalNeeded"))}</p>
        <div class="phase5-actions"><button class="primary-btn" data-phase5-open="goal" type="button">${phase5Escape(phase5Text("setGoal"))}</button></div>
      </section>`;
    const maintenance = goal.goal_code === "weight_maintenance" && latest?.weight_kg && goal.target_weight_kg;
    const goalMetric = progress
      ? `<strong>${phase5Number(progress.raw, 0)}%</strong><div class="phase5-progress-track" aria-label="${phase5Escape(phase5Text("goalProgress"))}: ${phase5Number(progress.raw, 0)}%"><span style="--phase5-progress:${progress.display}%"></span></div>`
      : maintenance
        ? `<strong>${phase5WeightLabel(Math.abs(Number(latest.weight_kg) - Number(goal.target_weight_kg)))}</strong><small>${phase5Escape(phase5Text("maintenanceDistance"))}</small>`
        : `<strong>${phase5Escape(phase5Text("noData"))}</strong><small>${phase5Escape(phase5Text("goalOptionalWeight"))}</small>`;
    return `
      <section class="phase5-section" aria-labelledby="phase5-goal-title">
        <div class="phase5-section-head"><div><p class="eyebrow">${phase5Escape(phase5Text("goal"))}</p><h2 id="phase5-goal-title">${phase5Escape(phase5GoalLabel(goal.goal_code))}</h2></div><button class="secondary-btn" data-phase5-open="goal" type="button">${phase5Escape(phase5Text("edit"))}</button></div>
        <div class="phase5-metric">${goalMetric}</div>
        <div class="phase5-metrics">
          <div class="phase5-metric"><span>${phase5Escape(phase5Text("baselineWeight"))}</span><strong>${phase5WeightLabel(goal.baseline_weight_kg)}</strong></div>
          <div class="phase5-metric"><span>${phase5Escape(phase5Text("targetWeight"))}</span><strong>${phase5WeightLabel(goal.target_weight_kg)}</strong></div>
        </div>
      </section>`;
  }

  function phase5WeightCard() {
    const weights = phase5State.data?.weights || [];
    const latest = phase5Latest(weights);
    const previous = weights.length > 1 ? weights[weights.length - 2] : null;
    const delta = latest && previous ? Number(latest.weight_kg) - Number(previous.weight_kg) : null;
    return `
      <section class="phase5-section phase5-wide" aria-labelledby="phase5-weight-title">
        <div class="phase5-section-head"><div><p class="eyebrow">${phase5Escape(phase5Text("trend"))}</p><h2 id="phase5-weight-title">${phase5Escape(phase5Text("weight"))}</h2></div><button class="primary-btn" data-phase5-open="weight" type="button">${phase5Escape(phase5Text(latest?.log_date === phase5Today() ? "editWeight" : "addWeight"))}</button></div>
        <div class="phase5-metrics">
          <div class="phase5-metric"><span>${phase5Escape(phase5Text("currentWeight"))}</span><strong>${phase5WeightLabel(latest?.weight_kg)}</strong><small>${latest ? phase5Date(latest.log_date) : phase5Text("noData")}</small></div>
          <div class="phase5-metric"><span>${phase5Escape(phase5Text("change"))}</span><strong>${delta === null ? "-" : `${delta > 0 ? "+" : ""}${phase5WeightLabel(delta)}`}</strong><small>${phase5Escape(phase5Text("rawValue"))}</small></div>
        </div>
        ${phase5LineChart(weights)}
      </section>`;
  }

  function phase5MeasurementCard() {
    const rows = phase5State.data?.measurements || [];
    const latest = phase5Latest(rows);
    const metrics = [["waist_cm","waist"],["chest_cm","chest"],["hips_cm","hips"],["upper_arm_left_cm","armLeft"]];
    return `
      <section class="phase5-section" aria-labelledby="phase5-measure-title">
        <div class="phase5-section-head"><h2 id="phase5-measure-title">${phase5Escape(phase5Text("measurements"))}</h2><button class="primary-btn" data-phase5-open="measurement" type="button">${phase5Escape(phase5Text("addMeasurement"))}</button></div>
        ${latest ? `<div class="phase5-metrics">${metrics.map(([key,label]) => `<div class="phase5-metric"><span>${phase5Escape(phase5Text(label))}</span><strong>${phase5LengthLabel(latest[key])}</strong></div>`).join("")}</div><small class="muted">${phase5Escape(phase5Text("updated"))}: ${phase5Escape(phase5Date(latest.log_date))}</small>` : `<p class="muted">${phase5Escape(phase5Text("emptyMeasurements"))}</p>`}
      </section>`;
  }

  function phase5StrengthCard() {
    const rows = phase5State.data?.strength || [];
    return `
      <section class="phase5-section" aria-labelledby="phase5-strength-title">
        <div class="phase5-section-head"><h2 id="phase5-strength-title">${phase5Escape(phase5Text("strength"))}</h2></div>
        ${rows.length ? `<div class="phase5-list">${rows.slice(0,4).map((row) => `<div class="phase5-list-row"><div><strong>${phase5Escape(row.exercise_name)}</strong><p class="muted">${phase5Escape(phase5Text("maxWeight"))}: ${phase5WeightLabel(row.max_weight_kg)} · ${phase5Escape(String(row.completed_sets))} ${phase5Escape(phase5Text("completedSets"))}</p></div><div class="phase5-metric"><span>${phase5Escape(phase5Text("estimatedOneRm"))}</span><strong>${phase5WeightLabel(row.estimated_one_rep_max_kg)}</strong></div></div>`).join("")}</div>` : `<p class="muted">${phase5Escape(phase5Text("emptyStrength"))}</p>`}
      </section>`;
  }

  function phase5ConsistencyCard() {
    const value = phase5State.data?.consistency || {};
    return `
      <section class="phase5-section" aria-labelledby="phase5-consistency-title">
        <h2 id="phase5-consistency-title">${phase5Escape(phase5Text("consistency"))}</h2>
        <div class="phase5-metrics">
          <div class="phase5-metric"><span>${phase5Escape(phase5Text("last7"))}</span><strong>${phase5Number(value.last_7_days || 0,0)}</strong><small>${phase5Escape(phase5Text("completedWorkouts"))}</small></div>
          <div class="phase5-metric"><span>${phase5Escape(phase5Text("last30"))}</span><strong>${phase5Number(value.last_30_days || 0,0)}</strong><small>${phase5Escape(phase5Text("completedWorkouts"))}</small></div>
        </div>
      </section>`;
  }

  function phase5ContextCard() {
    const recovery = phase5State.data?.recovery_context || {};
    const nutrition = phase5State.data?.nutrition_context || {};
    const sleep = recovery.average_sleep_hours == null ? phase5Text("averageSleepUnknown") : `${phase5Number(recovery.average_sleep_hours,1)}u`;
    const steps = recovery.average_steps == null ? phase5Text("stepsUnknown") : phase5Number(recovery.average_steps,0);
    const kcal = nutrition.average_energy_kcal == null ? phase5Text("kcalUnknown") : phase5Number(nutrition.average_energy_kcal,0);
    const protein = nutrition.average_protein_grams == null ? phase5Text("proteinUnknown") : `${phase5Number(nutrition.average_protein_grams,1)}g`;
    return `
      <section class="phase5-section phase5-wide" aria-labelledby="phase5-context-title">
        <h2 id="phase5-context-title">${phase5Escape(phase5Text("context"))}</h2>
        <div class="phase5-context">
          <div class="phase5-context-item"><strong>${phase5Escape(phase5Text("recovery"))}</strong><p class="muted">${phase5Escape(phase5Format("recoverySummary", { days: recovery.days_logged || 0, sleep, steps }))}</p></div>
          <div class="phase5-context-item"><strong>${phase5Escape(phase5Text("nutrition"))}</strong><p class="muted">${phase5Escape(phase5Format("nutritionSummary", { days: nutrition.days_logged || 0, kcal, protein }))}</p></div>
          <div class="phase5-context-item"><strong>${phase5Escape(phase5Text("running"))}</strong><p class="muted">${phase5Escape(phase5Text("runningUnavailable"))}</p></div>
        </div>
      </section>`;
  }

  function phase5History() {
    const weights = [...(phase5State.data?.weights || [])].reverse();
    const measurements = [...(phase5State.data?.measurements || [])].reverse();
    return `
      <section class="phase5-section phase5-wide">
        <details class="phase5-details">
          <summary>${phase5Escape(phase5Text("history"))}</summary>
          <div class="phase5-table-wrap"><table class="phase5-table"><thead><tr><th>${phase5Escape(phase5Text("date"))}</th><th>${phase5Escape(phase5Text("weight"))}</th><th>${phase5Escape(phase5Text("trend"))}</th><th></th></tr></thead><tbody>
            ${weights.length ? weights.map((row) => `<tr><td>${phase5Escape(phase5Date(row.log_date))}</td><td>${phase5Escape(phase5WeightLabel(row.weight_kg))}</td><td>${phase5Escape(phase5WeightLabel(row.trend_kg))}</td><td><button class="secondary-btn" data-phase5-edit-weight="${phase5Escape(row.log_date)}" type="button">${phase5Escape(phase5Text("edit"))}</button> <button class="secondary-btn" data-phase5-archive-weight="${phase5Escape(row.id)}" data-updated-at="${phase5Escape(row.updated_at)}" type="button">${phase5Escape(phase5Text("archive"))}</button></td></tr>`).join("") : `<tr><td colspan="4">${phase5Escape(phase5Text("noData"))}</td></tr>`}
          </tbody></table></div>
          <div class="phase5-table-wrap"><table class="phase5-table"><thead><tr><th>${phase5Escape(phase5Text("date"))}</th><th>${phase5Escape(phase5Text("waist"))}</th><th>${phase5Escape(phase5Text("chest"))}</th><th>${phase5Escape(phase5Text("hips"))}</th><th></th></tr></thead><tbody>
            ${measurements.length ? measurements.map((row) => `<tr><td>${phase5Escape(phase5Date(row.log_date))}</td><td>${phase5Escape(phase5LengthLabel(row.waist_cm))}</td><td>${phase5Escape(phase5LengthLabel(row.chest_cm))}</td><td>${phase5Escape(phase5LengthLabel(row.hips_cm))}</td><td><button class="secondary-btn" data-phase5-edit-measurement="${phase5Escape(row.log_date)}" type="button">${phase5Escape(phase5Text("edit"))}</button> <button class="secondary-btn" data-phase5-archive-measurement="${phase5Escape(row.id)}" data-updated-at="${phase5Escape(row.updated_at)}" type="button">${phase5Escape(phase5Text("archive"))}</button></td></tr>`).join("") : `<tr><td colspan="5">${phase5Escape(phase5Text("emptyMeasurements"))}</td></tr>`}
          </tbody></table></div>
        </details>
      </section>`;
  }

  function phase5Render() {
    const target = document.getElementById("progress");
    if (!target) return;
    phase5InstallStyles();
    target.classList.add("phase5-progress-active");
    target.hidden = false;
    target.removeAttribute("aria-hidden");

    if (!isLoggedIn() || state.ui.role !== "client") return;
    if (!onlineProfile?.id || !isOnlineMode()) {
      target.innerHTML = `<div class="phase5-shell"><section class="phase5-hero phase5-error"><h1>${phase5Escape(phase5Text("title"))}</h1><p>${phase5Escape(phase5Text(!isOnlineMode() ? "onlineRequired" : "authRequired"))}</p></section></div>`;
      return;
    }
    if (phase5State.loading && !phase5State.loaded) {
      target.innerHTML = `<div class="phase5-shell"><section class="phase5-hero"><h1>${phase5Escape(phase5Text("title"))}</h1><p class="muted" role="status">${phase5Escape(phase5Text("loading"))}</p></section></div>`;
      return;
    }
    if (phase5State.error && !phase5State.loaded) {
      target.innerHTML = `<div class="phase5-shell"><section class="phase5-hero phase5-error"><h1>${phase5Escape(phase5Text("title"))}</h1><p>${phase5Escape(phase5State.error)}</p><div><button class="primary-btn" data-phase5-retry type="button">${phase5Escape(phase5Text("retry"))}</button></div></section></div>`;
      return;
    }
    if (!phase5State.loaded) {
      target.innerHTML = `<div class="phase5-shell"><section class="phase5-hero"><h1>${phase5Escape(phase5Text("title"))}</h1><p class="muted">${phase5Escape(phase5Text("loading"))}</p></section></div>`;
      phase5Hydrate();
      return;
    }

    const data = phase5State.data || {};
    target.innerHTML = `
      <div class="phase5-shell">
        <header class="phase5-hero">
          <div class="phase5-head"><div><p class="eyebrow">${phase5Escape(phase5Text("current"))}</p><h1>${phase5Escape(phase5Text("title"))}</h1></div><span class="status ${data.access === "full" ? "ok" : ""}">${phase5Escape(phase5Text(data.access === "full" ? "fullHistory" : "freeHistory"))}</span></div>
          <p class="muted">${phase5Escape(phase5Text("intro"))}</p>
          <div class="phase5-unit-toggle" role="group" aria-label="${phase5Escape(phase5Text("units"))}"><button class="secondary-btn" data-phase5-unit="metric" aria-pressed="${phase5UnitSystem() === "metric"}" type="button">${phase5Escape(phase5Text("metric"))}</button><button class="secondary-btn" data-phase5-unit="imperial" aria-pressed="${phase5UnitSystem() === "imperial"}" type="button">${phase5Escape(phase5Text("imperial"))}</button></div>
          ${phase5State.notice ? `<div class="phase5-notice" role="status">${phase5Escape(phase5State.notice)}</div>` : ""}
          ${data.history_locked ? `<div class="phase5-notice">${phase5Escape(phase5Text("historyLocked"))}</div>` : ""}
        </header>
        <div class="phase5-grid">
          ${phase5GoalCard()}
          <section class="phase5-section"><div class="phase5-section-head"><h2>${phase5Escape(phase5Text("bmiContext"))}</h2></div><div class="phase5-metric"><strong>${data.bmi_context == null ? "-" : phase5Number(data.bmi_context,1)}</strong><small>${phase5Escape(phase5Text("bmiDisclaimer"))}</small></div></section>
          ${phase5WeightCard()}
          ${phase5MeasurementCard()}
          ${phase5ConsistencyCard()}
          ${phase5StrengthCard()}
          ${phase5ContextCard()}
          ${phase5History()}
          <section class="phase5-section phase5-photo-gate phase5-wide"><div class="phase5-section-head"><h2>${phase5Escape(phase5Text("photos"))}</h2></div><p class="muted">${phase5Escape(phase5Text("photosGate"))}</p></section>
        </div>
      </div>`;
  }

  async function phase5Hydrate({ force = false } = {}) {
    if (!isLoggedIn() || state.ui.role !== "client" || !onlineProfile?.id || !supabaseClient) return;
    const profileId = onlineProfile.id;
    if (phase5State.loading || (!force && phase5State.loaded && phase5State.profileId === profileId)) return;
    if (phase5State.profileId && phase5State.profileId !== profileId) phase5Reset();
    phase5State.profileId = profileId;
    phase5State.loading = true;
    phase5State.error = "";
    if (currentView === "progress") phase5Render();
    try {
      const timezone = phase5Timezone();
      if (phase5State.timezoneInitializedFor !== profileId) {
        const timezoneResult = await supabaseClient.rpc("fmz_phase5_set_progress_timezone", { p_timezone_name: timezone });
        if (timezoneResult.error) throw timezoneResult.error;
        phase5State.timezoneInitializedFor = profileId;
      }
      const { data, error } = await supabaseClient.rpc("fmz_phase5_get_progress_dashboard", {
        p_before_date: phase5State.beforeDate,
        p_requested_days: 90
      });
      if (error) throw error;
      phase5State.data = data || {};
      phase5State.loaded = true;
      phase5State.error = "";
    } catch (error) {
      phase5State.error = phase5ErrorMessage(error, "loadError");
    } finally {
      phase5State.loading = false;
      if (currentView === "progress") phase5Render();
    }
  }

  function phase5Reset() {
    phase5CloseModal({ restoreFocus: false });
    phase5State.profileId = "";
    phase5State.loaded = false;
    phase5State.loading = false;
    phase5State.error = "";
    phase5State.data = null;
    phase5State.beforeDate = null;
    phase5State.timezoneInitializedFor = "";
    phase5State.notice = "";
    phase5State.pending = false;
  }

  function phase5GoalOptions(selected) {
    return [
      ["fat_loss","goalFatLoss"],["muscle_gain","goalMuscle"],["strength","goalStrength"],
      ["conditioning","goalConditioning"],["running","goalRunning"],
      ["healthier_living","goalHealth"],["weight_maintenance","goalMaintenance"]
    ].map(([value,key]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${phase5Escape(phase5Text(key))}</option>`).join("");
  }

  function phase5ModalMarkup() {
    const modal = phase5State.modal;
    if (!modal) return "";
    const data = phase5State.data || {};
    const date = phase5State.modalDate || phase5Today();
    const weight = (data.weights || []).find((item) => item.log_date === date) || null;
    const measurement = (data.measurements || []).find((item) => item.log_date === date) || null;
    const goal = data.goal || {};
    const weightUnit = phase5Text(phase5UnitSystem() === "imperial" ? "lb" : "kg");
    const lengthUnit = phase5Text(phase5UnitSystem() === "imperial" ? "inch" : "cm");
    let title = phase5Text("goal");
    let form = "";
    if (modal === "weight") {
      title = phase5Text(weight ? "editWeight" : "addWeight");
      form = `<form class="phase5-form" data-phase5-form="weight" data-expected-updated-at="${phase5Escape(weight?.updated_at || "")}"><div class="phase5-form-grid"><label class="field"><span>${phase5Escape(phase5Text("date"))}</span><input name="log_date" type="date" max="${phase5Today()}" value="${phase5Escape(date)}" required /></label><label class="field"><span>${phase5Escape(phase5Text("weight"))} (${weightUnit})</span><input name="weight" type="number" inputmode="decimal" step="0.1" min="${phase5UnitSystem() === "imperial" ? 55 : 25}" max="${phase5UnitSystem() === "imperial" ? 882 : 400}" value="${weight ? phase5Number(phase5WeightValue(weight.weight_kg),1).replace(/[^0-9,.-]/g,"").replace(",",".") : ""}" required /></label><label class="field wide"><span>${phase5Escape(phase5Text("notes"))}</span><textarea name="notes" rows="3" maxlength="500">${phase5Escape(weight?.notes || "")}</textarea></label></div><div class="phase5-actions"><button class="primary-btn" type="submit">${phase5Escape(phase5Text("save"))}</button><span class="save-feedback" data-phase5-form-feedback role="status" aria-live="polite"></span></div></form>`;
    } else if (modal === "measurement") {
      title = phase5Text(measurement ? "editMeasurement" : "addMeasurement");
      const field = (name,key) => `<label class="field"><span>${phase5Escape(phase5Text(key))} (${lengthUnit})</span><input name="${name}" type="number" inputmode="decimal" min="0" step="0.1" value="${measurement?.[name] == null ? "" : phase5Number(phase5LengthValue(measurement[name]),1).replace(/[^0-9,.-]/g,"").replace(",",".")}" /></label>`;
      form = `<form class="phase5-form" data-phase5-form="measurement" data-expected-updated-at="${phase5Escape(measurement?.updated_at || "")}"><div class="phase5-form-grid"><label class="field"><span>${phase5Escape(phase5Text("date"))}</span><input name="log_date" type="date" max="${phase5Today()}" value="${phase5Escape(date)}" required /></label><span></span>${field("waist_cm","waist")}${field("chest_cm","chest")}${field("hips_cm","hips")}${field("upper_arm_left_cm","armLeft")}${field("upper_arm_right_cm","armRight")}${field("thigh_left_cm","thighLeft")}${field("thigh_right_cm","thighRight")}<label class="field wide"><span>${phase5Escape(phase5Text("notes"))}</span><textarea name="notes" rows="3" maxlength="500">${phase5Escape(measurement?.notes || "")}</textarea></label></div><div class="phase5-actions"><button class="primary-btn" type="submit">${phase5Escape(phase5Text("save"))}</button><span class="save-feedback" data-phase5-form-feedback role="status" aria-live="polite"></span></div></form>`;
    } else {
      const latestWeight = phase5Latest(data.weights || [])?.weight_kg;
      const baseline = goal.baseline_weight_kg ?? latestWeight;
      form = `<form class="phase5-form" data-phase5-form="goal" data-expected-updated-at="${phase5Escape(goal.updated_at || "")}"><div class="phase5-form-grid"><label class="field wide"><span>${phase5Escape(phase5Text("goal"))}</span><select name="goal_code" required>${phase5GoalOptions(goal.goal_code || "fat_loss")}</select></label><label class="field"><span>${phase5Escape(phase5Text("baselineWeight"))} (${weightUnit})</span><input name="baseline_weight" type="number" inputmode="decimal" step="0.1" min="0" value="${baseline == null ? "" : phase5Number(phase5WeightValue(baseline),1).replace(/[^0-9,.-]/g,"").replace(",",".")}" /></label><label class="field"><span>${phase5Escape(phase5Text("targetWeight"))} (${weightUnit})</span><input name="target_weight" type="number" inputmode="decimal" step="0.1" min="0" value="${goal.target_weight_kg == null ? "" : phase5Number(phase5WeightValue(goal.target_weight_kg),1).replace(/[^0-9,.-]/g,"").replace(",",".")}" /></label><label class="field"><span>${phase5Escape(phase5Text("targetDate"))}</span><input name="target_date" type="date" value="${phase5Escape(goal.target_date || "")}" /></label><label class="field wide"><span>${phase5Escape(phase5Text("notes"))}</span><textarea name="notes" rows="3" maxlength="1000">${phase5Escape(goal.notes || "")}</textarea></label></div><p class="muted">${phase5Escape(phase5Text("goalOptionalWeight"))}</p><div class="phase5-actions"><button class="primary-btn" type="submit">${phase5Escape(phase5Text("save"))}</button><span class="save-feedback" data-phase5-form-feedback role="status" aria-live="polite"></span></div></form>`;
    }
    return `<button class="phase5-backdrop" data-phase5-close type="button" aria-label="${phase5Escape(phase5Text("cancel"))}"></button><section class="phase5-sheet" role="dialog" aria-modal="true" aria-labelledby="phase5-modal-title"><header class="phase5-sheet-head"><h2 id="phase5-modal-title">${phase5Escape(title)}</h2><button class="secondary-btn phase5-close" data-phase5-close type="button" aria-label="${phase5Escape(phase5Text("cancel"))}">x</button></header>${form}</section>`;
  }

  function phase5RenderModal() {
    let portal = document.getElementById("phase5ProgressPortal");
    if (!phase5State.modal) {
      portal?.remove();
      document.body.classList.remove("phase5-modal-open");
      return;
    }
    if (!portal) {
      portal = document.createElement("div");
      portal.id = "phase5ProgressPortal";
      portal.className = "phase5-portal";
      document.body.appendChild(portal);
    }
    portal.innerHTML = phase5ModalMarkup();
    document.body.classList.add("phase5-modal-open");
    portal.querySelector("input,select,textarea")?.focus();
  }

  function phase5OpenModal(type, date = "", opener = null) {
    phase5State.modal = type;
    phase5State.modalDate = date || phase5Today();
    phase5State.opener = opener || document.activeElement;
    phase5RenderModal();
  }

  function phase5CloseModal({ restoreFocus = true } = {}) {
    const opener = phase5State.opener;
    phase5State.modal = "";
    phase5State.modalDate = "";
    phase5State.opener = null;
    document.getElementById("phase5ProgressPortal")?.remove();
    document.body.classList.remove("phase5-modal-open");
    if (restoreFocus) opener?.focus?.();
  }

  function phase5FormNumber(data, name, converter) {
    const raw = String(data.get(name) || "").trim().replace(",", ".");
    if (!raw) return null;
    const value = converter(Number(raw));
    return Number.isFinite(value) ? Number(value.toFixed(2)) : null;
  }

  async function phase5Submit(form) {
    if (phase5State.pending) return;
    const type = form.dataset.phase5Form;
    const data = new FormData(form);
    const feedback = form.querySelector("[data-phase5-form-feedback]");
    const requestId = form.dataset.requestId || phase5Uuid();
    form.dataset.requestId = requestId;
    phase5State.pending = true;
    feedback.textContent = "";
    form.querySelectorAll("button,input,select,textarea").forEach((control) => { control.disabled = true; });
    try {
      let result;
      if (type === "weight") {
        result = await supabaseClient.rpc("fmz_phase5_save_weight_log", {
          p_log_date: data.get("log_date"), p_weight_kg: phase5FormNumber(data,"weight",phase5WeightKg),
          p_notes: data.get("notes") || null, p_timezone_name: phase5Timezone(),
          p_timezone_offset_minutes: phase5OffsetMinutes(data.get("log_date")),
          p_request_id: requestId, p_expected_updated_at: form.dataset.expectedUpdatedAt || null
        });
      } else if (type === "measurement") {
        const values = ["waist_cm","chest_cm","hips_cm","upper_arm_left_cm","upper_arm_right_cm","thigh_left_cm","thigh_right_cm"];
        const converted = Object.fromEntries(values.map((name) => [name, phase5FormNumber(data,name,phase5LengthCm)]));
        if (values.every((name) => converted[name] === null)) throw new Error("required measurement");
        result = await supabaseClient.rpc("fmz_phase5_save_body_measurement", {
          p_log_date: data.get("log_date"), p_waist_cm: converted.waist_cm,
          p_chest_cm: converted.chest_cm, p_hips_cm: converted.hips_cm,
          p_upper_arm_left_cm: converted.upper_arm_left_cm, p_upper_arm_right_cm: converted.upper_arm_right_cm,
          p_thigh_left_cm: converted.thigh_left_cm, p_thigh_right_cm: converted.thigh_right_cm,
          p_notes: data.get("notes") || null, p_timezone_name: phase5Timezone(),
          p_timezone_offset_minutes: phase5OffsetMinutes(data.get("log_date")), p_request_id: requestId,
          p_expected_updated_at: form.dataset.expectedUpdatedAt || null
        });
      } else {
        result = await supabaseClient.rpc("fmz_phase5_save_progress_goal", {
          p_goal_code: data.get("goal_code"), p_baseline_weight_kg: phase5FormNumber(data,"baseline_weight",phase5WeightKg),
          p_target_weight_kg: phase5FormNumber(data,"target_weight",phase5WeightKg), p_target_date: data.get("target_date") || null,
          p_notes: data.get("notes") || null, p_request_id: requestId,
          p_expected_updated_at: form.dataset.expectedUpdatedAt || null
        });
      }
      if (result.error) throw result.error;
      phase5State.notice = phase5Text("saved");
      phase5CloseModal({ restoreFocus: false });
      phase5State.loaded = false;
      await phase5Hydrate({ force: true });
    } catch (error) {
      const message = /required measurement/i.test(error?.message || "") ? phase5Text("requiredMeasurement") : phase5ErrorMessage(error);
      feedback.textContent = message;
      if (/progress_stale_conflict/i.test(error?.message || "")) {
        phase5State.loaded = false;
        await phase5Hydrate({ force: true });
      }
    } finally {
      phase5State.pending = false;
      if (document.body.contains(form)) form.querySelectorAll("button,input,select,textarea").forEach((control) => { control.disabled = false; });
    }
  }

  async function phase5Archive(kind, id, updatedAt) {
    if (phase5State.pending || !window.confirm(phase5Text("archiveConfirm"))) return;
    phase5State.pending = true;
    try {
      const rpc = kind === "weight" ? "fmz_phase5_archive_weight_log" : "fmz_phase5_archive_body_measurement";
      const args = kind === "weight"
        ? { p_weight_log_id: id, p_expected_updated_at: updatedAt }
        : { p_body_measurement_id: id, p_expected_updated_at: updatedAt };
      const result = await supabaseClient.rpc(rpc, args);
      if (result.error) throw result.error;
      phase5State.notice = phase5Text("archived");
      phase5State.loaded = false;
      await phase5Hydrate({ force: true });
    } catch (error) {
      phase5State.notice = phase5ErrorMessage(error);
      await phase5Hydrate({ force: true });
    } finally {
      phase5State.pending = false;
    }
  }

  async function phase5SetUnit(unitSystem) {
    if (phase5State.pending || !["metric","imperial"].includes(unitSystem) || unitSystem === phase5UnitSystem()) return;
    phase5State.pending = true;
    try {
      const result = await supabaseClient.rpc("fmz_phase5_set_unit_system", { p_unit_system: unitSystem });
      if (result.error) throw result.error;
      if (state?.accountSettings) state.accountSettings.unitSystem = unitSystem;
      phase5State.loaded = false;
      await phase5Hydrate({ force: true });
    } catch (error) {
      phase5State.notice = phase5ErrorMessage(error);
      phase5Render();
    } finally {
      phase5State.pending = false;
    }
  }

  const phase5OriginalRenderProgress = renderProgress;
  const phase5OriginalRenderAll = renderAll;
  const phase5OriginalRenderNav = renderNav;

  renderProgress = function renderProgressPhase5() {
    if (isLoggedIn() && state.ui.role === "client") return phase5Render();
    return phase5OriginalRenderProgress();
  };

  renderNav = function renderNavPhase5() {
    phase5EnsureNav();
    return phase5OriginalRenderNav();
  };

  renderAll = function renderAllPhase5() {
    if (!isLoggedIn() || state.ui.role !== "client") phase5Reset();
    const result = phase5OriginalRenderAll();
    if (isLoggedIn() && state.ui.role === "client" && currentView === "progress") phase5Render();
    return result;
  };

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.phase5Open) {
      event.preventDefault();
      phase5OpenModal(button.dataset.phase5Open, "", button);
      return;
    }
    if (button.dataset.phase5EditWeight) {
      event.preventDefault();
      phase5OpenModal("weight", button.dataset.phase5EditWeight, button);
      return;
    }
    if (button.dataset.phase5EditMeasurement) {
      event.preventDefault();
      phase5OpenModal("measurement", button.dataset.phase5EditMeasurement, button);
      return;
    }
    if (button.dataset.phase5Close !== undefined) {
      event.preventDefault();
      phase5CloseModal();
      return;
    }
    if (button.dataset.phase5Retry !== undefined) {
      event.preventDefault();
      await phase5Hydrate({ force: true });
      return;
    }
    if (button.dataset.phase5Unit) {
      event.preventDefault();
      await phase5SetUnit(button.dataset.phase5Unit);
      return;
    }
    if (button.dataset.phase5ArchiveWeight) {
      event.preventDefault();
      await phase5Archive("weight", button.dataset.phase5ArchiveWeight, button.dataset.updatedAt);
      return;
    }
    if (button.dataset.phase5ArchiveMeasurement) {
      event.preventDefault();
      await phase5Archive("measurement", button.dataset.phase5ArchiveMeasurement, button.dataset.updatedAt);
    }
  }, true);

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("[data-phase5-form]");
    if (!form) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    phase5Submit(form);
  }, true);

  document.addEventListener("input", (event) => {
    const form = event.target.closest("[data-phase5-form]");
    if (form) form.dataset.requestId = "";
  }, true);

  document.addEventListener("change", (event) => {
    const dateInput = event.target.closest('[data-phase5-form] input[name="log_date"]');
    if (!dateInput) return;
    const type = dateInput.closest("form")?.dataset.phase5Form;
    if (type) phase5OpenModal(type, dateInput.value, phase5State.opener);
  }, true);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && phase5State.modal) {
      event.preventDefault();
      phase5CloseModal();
    }
  });

  phase5EnsureNav();
  window.FMZ_PHASE5_PROGRESS = Object.freeze({
    version: PHASE5_VERSION,
    render: phase5Render,
    hydrate: phase5Hydrate,
    reset: phase5Reset,
    canonicalUnits: Object.freeze({ weight: "kg", length: "cm" }),
    freeHistoryDays: 30,
    photosEnabled: false,
    mobileFirst: true,
    noPolling: true
  });
})();
