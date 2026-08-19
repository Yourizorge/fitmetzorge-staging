(() => {
  if (window.FMZ_PHASE4_NUTRITION_SLICE3_LOADED) return;
  window.FMZ_PHASE4_NUTRITION_SLICE3_LOADED = true;

  const PHASE4_SLICE3_VERSION = "20260819-phase4-nutrition-slice3-1";
  const PHASE4_SLICE3_SEARCH_PAGE_SIZE = 25;
  const PHASE4_SLICE3_FREE_HISTORY_DAYS = 7;
  const PHASE4_SLICE3_MEALS = ["breakfast", "lunch", "dinner", "snacks"];
  const PHASE4_SLICE3_UNITS = ["g", "ml", "serving", "piece"];

  const COPY = {
    nl: {
      nutrition: "Voeding",
      today: "Vandaag",
      previousDay: "Vorige dag",
      nextDay: "Volgende dag",
      backToToday: "Terug naar vandaag",
      loadingDay: "Voedingsdag laden...",
      loadDayFailed: "Deze voedingsdag kon niet worden geladen.",
      retry: "Opnieuw proberen",
      onlineRequired: "Voeding is alleen beschikbaar met een actieve stagingverbinding.",
      authLoading: "Je voedingsprofiel wordt nog geladen.",
      timezoneLoading: "Lokale daggrens voorbereiden...",
      timezoneFailed: "Je lokale tijdzone kon niet veilig worden ingesteld.",
      consumed: "Gegeten",
      remaining: "{value} over",
      above: "{value} boven doel",
      noTarget: "Nog geen dagdoel. Je invoer wordt wel veilig bijgehouden.",
      setTarget: "Dagdoel instellen",
      editTarget: "Dagdoel aanpassen",
      kcal: "Kcal",
      protein: "Eiwit",
      carbohydrate: "Koolhydraten",
      fat: "Vet",
      breakfast: "Ontbijt",
      lunch: "Lunch",
      dinner: "Diner",
      snacks: "Snacks",
      emptyMeal: "Nog niets toegevoegd.",
      emptyDay: "Nog geen voeding gelogd op deze dag.",
      addFood: "Voeding toevoegen",
      manageFoods: "Voedingsmiddelen beheren",
      searchFood: "Voedingsmiddel zoeken",
      searchPlaceholder: "Zoek op naam, merk of barcode",
      search: "Zoeken",
      results: "Resultaten",
      searchLoading: "Voedingsmiddelen laden...",
      searchFailed: "Zoeken is niet gelukt.",
      noFoods: "Geen passende voedingsmiddelen gevonden.",
      createCustom: "Eigen voedingsmiddel maken",
      loadMore: "Meer laden",
      select: "Kiezen",
      reference: "Per {amount} {unit}",
      entryTitle: "Hoeveel heb je gegeten?",
      editEntryTitle: "Gelogde voeding bewerken",
      changeFood: "Ander voedingsmiddel",
      meal: "Maaltijd",
      amount: "Hoeveelheid",
      unitOrPortion: "Eenheid of portie",
      directUnit: "{unit}",
      portion: "{label} ({amount} {unit})",
      portionsLoading: "Porties laden...",
      notes: "Notities (optioneel)",
      saveEntry: "Toevoegen",
      saveEdit: "Wijziging opslaan",
      saving: "Opslaan...",
      saved: "Voeding toegevoegd.",
      edited: "Voeding bijgewerkt.",
      validation: "Controleer maaltijd, hoeveelheid en eenheid.",
      quantityRange: "De hoeveelheid moet hoger dan 0 en maximaal 100000 zijn.",
      notesRange: "Notities mogen maximaal 1000 tekens bevatten.",
      details: "Details",
      edit: "Bewerken",
      remove: "Verwijderen",
      removeTitle: "Gelogde voeding verwijderen?",
      removeBody: "De invoer verdwijnt uit je actieve dagtotaal. Historie blijft veilig bewaard.",
      confirmRemove: "Verwijderen",
      removed: "Voeding verwijderd.",
      close: "Sluiten",
      cancel: "Annuleren",
      back: "Terug",
      stale: "Deze invoer is intussen gewijzigd. De dag is vernieuwd; open de invoer opnieuw.",
      conflict: "De veilige aanvraagidentiteit is al gebruikt. Probeer opnieuw met de huidige gegevens.",
      freeHistory: "Free geeft toegang tot vandaag en de zes vorige lokale kalenderdagen.",
      futureDay: "Een toekomstige voedingsdag is niet beschikbaar.",
      networkRetry: "Verbinding onderbroken. Je kunt dezelfde veilige aanvraag opnieuw proberen.",
      unexpected: "Er ging iets mis. Probeer opnieuw.",
      customTitle: "Eigen voedingsmiddel maken",
      customIntro: "Maak een priveproduct en gebruik het direct in deze maaltijd.",
      name: "Naam",
      brand: "Merk (optioneel)",
      referenceAmount: "Referentiehoeveelheid",
      referenceUnit: "Referentie-eenheid",
      conversionAmount: "Komt overeen met",
      conversionUnit: "Omrekenen naar",
      conversionRequired: "Voor een portie of stuk is een expliciete omzetting naar gram of milliliter nodig.",
      energy: "Kcal per referentie",
      fiber: "Vezels",
      saveCustom: "Maken en gebruiken",
      customLimit: "Free bevat maximaal 10 actieve eigen voedingsmiddelen.",
      customLimitReached: "Je hebt de Free-limiet van 10 actieve eigen voedingsmiddelen bereikt.",
      customValidation: "Controleer de product- en voedingswaarden.",
      sourceSnapshot: "Bronsnapshot",
      serverCalculated: "Totaal wordt na opslaan door de server berekend.",
      unitServing: "Portie",
      unitPiece: "Stuk"
    },
    en: {
      nutrition: "Nutrition",
      today: "Today",
      previousDay: "Previous day",
      nextDay: "Next day",
      backToToday: "Back to today",
      loadingDay: "Loading nutrition day...",
      loadDayFailed: "This nutrition day could not be loaded.",
      retry: "Try again",
      onlineRequired: "Nutrition requires an active staging connection.",
      authLoading: "Your Nutrition profile is still loading.",
      timezoneLoading: "Preparing your local day boundary...",
      timezoneFailed: "Your local timezone could not be set safely.",
      consumed: "Consumed",
      remaining: "{value} remaining",
      above: "{value} above target",
      noTarget: "No daily target yet. Your intake is still tracked safely.",
      setTarget: "Set daily target",
      editTarget: "Edit daily target",
      kcal: "Kcal",
      protein: "Protein",
      carbohydrate: "Carbohydrates",
      fat: "Fat",
      breakfast: "Breakfast",
      lunch: "Lunch",
      dinner: "Dinner",
      snacks: "Snacks",
      emptyMeal: "Nothing added yet.",
      emptyDay: "No food has been logged for this day.",
      addFood: "Add food",
      manageFoods: "Manage foods",
      searchFood: "Search food",
      searchPlaceholder: "Search by name, brand, or barcode",
      search: "Search",
      results: "Results",
      searchLoading: "Loading foods...",
      searchFailed: "Search failed.",
      noFoods: "No matching foods found.",
      createCustom: "Create custom food",
      loadMore: "Load more",
      select: "Select",
      reference: "Per {amount} {unit}",
      entryTitle: "How much did you eat?",
      editEntryTitle: "Edit logged food",
      changeFood: "Choose another food",
      meal: "Meal",
      amount: "Amount",
      unitOrPortion: "Unit or portion",
      directUnit: "{unit}",
      portion: "{label} ({amount} {unit})",
      portionsLoading: "Loading portions...",
      notes: "Notes (optional)",
      saveEntry: "Add",
      saveEdit: "Save changes",
      saving: "Saving...",
      saved: "Food added.",
      edited: "Food updated.",
      validation: "Check the meal, amount, and unit.",
      quantityRange: "The amount must be above 0 and no more than 100000.",
      notesRange: "Notes may contain at most 1000 characters.",
      details: "Details",
      edit: "Edit",
      remove: "Remove",
      removeTitle: "Remove logged food?",
      removeBody: "The entry leaves your active daily total. History remains preserved.",
      confirmRemove: "Remove",
      removed: "Food removed.",
      close: "Close",
      cancel: "Cancel",
      back: "Back",
      stale: "This entry changed in the meantime. The day was refreshed; open the entry again.",
      conflict: "The safe request identity was already used. Retry with the current details.",
      freeHistory: "Free includes today and the previous six local calendar days.",
      futureDay: "A future nutrition day is unavailable.",
      networkRetry: "Connection interrupted. You can retry the same safe request.",
      unexpected: "Something went wrong. Try again.",
      customTitle: "Create custom food",
      customIntro: "Create a private food and use it in this meal immediately.",
      name: "Name",
      brand: "Brand (optional)",
      referenceAmount: "Reference amount",
      referenceUnit: "Reference unit",
      conversionAmount: "Equivalent amount",
      conversionUnit: "Convert to",
      conversionRequired: "A serving or piece needs an explicit conversion to grams or milliliters.",
      energy: "Kcal per reference",
      fiber: "Fiber",
      saveCustom: "Create and use",
      customLimit: "Free includes up to 10 active custom foods.",
      customLimitReached: "You have reached the Free limit of 10 active custom foods.",
      customValidation: "Check the food and nutrition values.",
      sourceSnapshot: "Source snapshot",
      serverCalculated: "The server calculates totals after saving.",
      unitServing: "Serving",
      unitPiece: "Piece"
    },
    de: {
      nutrition: "Ernaehrung",
      today: "Heute",
      previousDay: "Vorheriger Tag",
      nextDay: "Naechster Tag",
      backToToday: "Zurueck zu heute",
      loadingDay: "Ernaehrungstag wird geladen...",
      loadDayFailed: "Dieser Ernaehrungstag konnte nicht geladen werden.",
      retry: "Erneut versuchen",
      onlineRequired: "Ernaehrung benoetigt eine aktive Staging-Verbindung.",
      authLoading: "Dein Ernaehrungsprofil wird noch geladen.",
      timezoneLoading: "Lokale Tagesgrenze wird vorbereitet...",
      timezoneFailed: "Deine lokale Zeitzone konnte nicht sicher eingestellt werden.",
      consumed: "Verzehrt",
      remaining: "{value} uebrig",
      above: "{value} ueber Ziel",
      noTarget: "Noch kein Tagesziel. Deine Eingaben werden trotzdem sicher erfasst.",
      setTarget: "Tagesziel festlegen",
      editTarget: "Tagesziel anpassen",
      kcal: "Kcal",
      protein: "Protein",
      carbohydrate: "Kohlenhydrate",
      fat: "Fett",
      breakfast: "Fruehstueck",
      lunch: "Mittagessen",
      dinner: "Abendessen",
      snacks: "Snacks",
      emptyMeal: "Noch nichts hinzugefuegt.",
      emptyDay: "Fuer diesen Tag wurde noch nichts protokolliert.",
      addFood: "Lebensmittel hinzufuegen",
      manageFoods: "Lebensmittel verwalten",
      searchFood: "Lebensmittel suchen",
      searchPlaceholder: "Nach Name, Marke oder Barcode suchen",
      search: "Suchen",
      results: "Ergebnisse",
      searchLoading: "Lebensmittel werden geladen...",
      searchFailed: "Die Suche ist fehlgeschlagen.",
      noFoods: "Keine passenden Lebensmittel gefunden.",
      createCustom: "Eigenes Lebensmittel erstellen",
      loadMore: "Mehr laden",
      select: "Auswaehlen",
      reference: "Pro {amount} {unit}",
      entryTitle: "Wie viel hast du gegessen?",
      editEntryTitle: "Protokolliertes Lebensmittel bearbeiten",
      changeFood: "Anderes Lebensmittel",
      meal: "Mahlzeit",
      amount: "Menge",
      unitOrPortion: "Einheit oder Portion",
      directUnit: "{unit}",
      portion: "{label} ({amount} {unit})",
      portionsLoading: "Portionen werden geladen...",
      notes: "Notizen (optional)",
      saveEntry: "Hinzufuegen",
      saveEdit: "Aenderung speichern",
      saving: "Speichern...",
      saved: "Lebensmittel hinzugefuegt.",
      edited: "Lebensmittel aktualisiert.",
      validation: "Pruefe Mahlzeit, Menge und Einheit.",
      quantityRange: "Die Menge muss groesser als 0 und hoechstens 100000 sein.",
      notesRange: "Notizen duerfen hoechstens 1000 Zeichen enthalten.",
      details: "Details",
      edit: "Bearbeiten",
      remove: "Entfernen",
      removeTitle: "Protokolliertes Lebensmittel entfernen?",
      removeBody: "Der Eintrag verschwindet aus dem aktiven Tagestotal. Der Verlauf bleibt erhalten.",
      confirmRemove: "Entfernen",
      removed: "Lebensmittel entfernt.",
      close: "Schliessen",
      cancel: "Abbrechen",
      back: "Zurueck",
      stale: "Dieser Eintrag wurde inzwischen geaendert. Der Tag wurde aktualisiert; oeffne den Eintrag erneut.",
      conflict: "Die sichere Anfragekennung wurde bereits verwendet. Versuche es mit den aktuellen Daten erneut.",
      freeHistory: "Free umfasst heute und die sechs vorherigen lokalen Kalendertage.",
      futureDay: "Ein zukuenftiger Ernaehrungstag ist nicht verfuegbar.",
      networkRetry: "Verbindung unterbrochen. Du kannst dieselbe sichere Anfrage erneut versuchen.",
      unexpected: "Etwas ist schiefgegangen. Versuche es erneut.",
      customTitle: "Eigenes Lebensmittel erstellen",
      customIntro: "Erstelle ein privates Lebensmittel und verwende es direkt in dieser Mahlzeit.",
      name: "Name",
      brand: "Marke (optional)",
      referenceAmount: "Referenzmenge",
      referenceUnit: "Referenzeinheit",
      conversionAmount: "Entspricht",
      conversionUnit: "Umrechnen in",
      conversionRequired: "Eine Portion oder ein Stueck braucht eine ausdrueckliche Umrechnung in Gramm oder Milliliter.",
      energy: "Kcal pro Referenz",
      fiber: "Ballaststoffe",
      saveCustom: "Erstellen und verwenden",
      customLimit: "Free enthaelt bis zu 10 aktive eigene Lebensmittel.",
      customLimitReached: "Du hast das Free-Limit von 10 aktiven eigenen Lebensmitteln erreicht.",
      customValidation: "Pruefe die Lebensmittel- und Naehrwerte.",
      sourceSnapshot: "Quellensnapshot",
      serverCalculated: "Der Server berechnet die Summen nach dem Speichern.",
      unitServing: "Portion",
      unitPiece: "Stueck"
    }
  };

  const slice3State = {
    userId: "",
    context: null,
    selectedDate: "",
    todayDate: "",
    timezoneName: "UTC",
    timezone: { status: "idle", error: "", requestToken: 0 },
    day: { status: "idle", value: null, error: "", requestToken: 0 },
    notice: "",
    portal: { type: "", opener: null, meal: "breakfast", food: null, item: null, feedback: "", feedbackType: "" },
    search: { status: "idle", query: "", items: [], afterName: null, afterId: null, hasMore: false, error: "", requestToken: 0 },
    portions: { status: "idle", items: [], error: "", requestToken: 0 },
    submission: { kind: "", itemId: "", requestId: "", submittedFingerprint: "" },
    customDraft: { foodId: "", submittedFingerprint: "" }
  };

  function language() {
    const current = state?.accountSettings?.language || "nl";
    return COPY[current] ? current : "nl";
  }

  function text(key, replacements = {}) {
    let value = COPY[language()]?.[key] || COPY.nl[key] || key;
    Object.entries(replacements).forEach(([name, replacement]) => {
      value = value.split(`{${name}}`).join(String(replacement ?? ""));
    });
    return value;
  }

  function formatNumber(value, digits = 1) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return "0";
    const locale = { nl: "nl-NL", en: "en-US", de: "de-DE" }[language()] || "nl-NL";
    return parsed.toLocaleString(locale, { minimumFractionDigits: 0, maximumFractionDigits: digits });
  }

  function uuid() {
    if (!window.crypto?.randomUUID) throw new Error("Secure UUID support is unavailable.");
    return window.crypto.randomUUID();
  }

  function localTodayISO() {
    const now = new Date();
    return [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("-");
  }

  function parseISODate(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ""));
    if (!match) return null;
    return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
  }

  function shiftDate(value, amount) {
    const parts = parseISODate(value);
    if (!parts) return localTodayISO();
    const date = new Date(Date.UTC(parts.year, parts.month - 1, parts.day + amount, 12));
    return [date.getUTCFullYear(), String(date.getUTCMonth() + 1).padStart(2, "0"), String(date.getUTCDate()).padStart(2, "0")].join("-");
  }

  function localNoon(value) {
    const parts = parseISODate(value);
    if (!parts) return new Date();
    return new Date(parts.year, parts.month - 1, parts.day, 12, 0, 0, 0);
  }

  function timezoneOffsetMinutes(value) {
    return -localNoon(value).getTimezoneOffset();
  }

  function localConsumedAt(value) {
    return localNoon(value).toISOString();
  }

  function resolvedTimezone() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  }

  function formatDate(value) {
    const parts = parseISODate(value);
    if (!parts) return value;
    const date = new Date(Date.UTC(parts.year, parts.month - 1, parts.day, 12));
    const locale = { nl: "nl-NL", en: "en-US", de: "de-DE" }[language()] || "nl-NL";
    return date.toLocaleDateString(locale, { weekday: "short", day: "numeric", month: "short" });
  }

  function resetForUser(userId) {
    closePortal(false);
    slice3State.userId = userId;
    slice3State.todayDate = localTodayISO();
    slice3State.selectedDate = slice3State.todayDate;
    slice3State.timezoneName = resolvedTimezone();
    slice3State.timezone = { status: "idle", error: "", requestToken: slice3State.timezone.requestToken + 1 };
    slice3State.day = { status: "idle", value: null, error: "", requestToken: slice3State.day.requestToken + 1 };
    slice3State.notice = "";
    slice3State.search = { status: "idle", query: "", items: [], afterName: null, afterId: null, hasMore: false, error: "", requestToken: slice3State.search.requestToken + 1 };
    slice3State.portions = { status: "idle", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    slice3State.submission = { kind: "", itemId: "", requestId: "", submittedFingerprint: "" };
    slice3State.customDraft = { foodId: "", submittedFingerprint: "" };
  }

  function installStyles() {
    if (document.getElementById("phase4-nutrition-slice3-styles")) return;
    const style = document.createElement("style");
    style.id = "phase4-nutrition-slice3-styles";
    style.textContent = `
      .phase4-s3-shell { display:grid; gap:18px; min-width:0; }
      .phase4-s3-head, .phase4-s3-date-nav, .phase4-s3-summary-head, .phase4-s3-meal-head, .phase4-s3-item-row, .phase4-s3-dialog-head { display:flex; align-items:center; justify-content:space-between; gap:10px; }
      .phase4-s3-head h1, .phase4-s3-summary-head h2, .phase4-s3-meal-head h2, .phase4-s3-dialog-head h2 { margin:0; letter-spacing:0; }
      .phase4-s3-head h1 { font-size:28px; line-height:1.15; }
      .phase4-s3-date-nav { min-height:52px; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:6px 0; }
      .phase4-s3-date-nav strong { text-align:center; overflow-wrap:anywhere; }
      .phase4-s3-icon { min-width:44px; min-height:44px; padding:8px 12px; font-size:20px; }
      .phase4-s3-summary { display:grid; gap:12px; padding-bottom:18px; border-bottom:1px solid var(--line); }
      .phase4-s3-progress-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
      .phase4-s3-progress { min-width:0; display:grid; gap:6px; padding:10px; border:1px solid var(--line); border-radius:8px; background:var(--surface); }
      .phase4-s3-progress-top { display:flex; align-items:flex-start; justify-content:space-between; gap:8px; }
      .phase4-s3-progress span, .phase4-s3-progress small, .phase4-s3-item-meta, .phase4-s3-muted { color:var(--muted); }
      .phase4-s3-progress strong { font-size:19px; overflow-wrap:anywhere; }
      .phase4-s3-track { height:7px; border-radius:4px; background:var(--surface-2); overflow:hidden; }
      .phase4-s3-track > span { display:block; height:100%; background:#c89312; }
      .phase4-s3-track.over > span { background:#c85a4a; }
      .phase4-s3-actions, .phase4-s3-dialog-actions { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
      .phase4-s3-gold { min-height:44px; background:#c89312; border-color:#c89312; color:#111; font-weight:800; }
      .phase4-s3-gold:hover { background:#d8a72a; border-color:#d8a72a; }
      .phase4-s3-meals { display:grid; gap:0; }
      .phase4-s3-meal { display:grid; gap:10px; padding:16px 0; border-bottom:1px solid var(--line); }
      .phase4-s3-meal-head { align-items:flex-start; }
      .phase4-s3-meal-head h2 { font-size:18px; }
      .phase4-s3-item-list { display:grid; gap:6px; }
      .phase4-s3-item-row { width:100%; min-height:56px; text-align:left; padding:10px; border:1px solid var(--line); border-radius:8px; background:var(--surface); color:var(--text); }
      .phase4-s3-item-main { min-width:0; display:grid; gap:3px; }
      .phase4-s3-item-main strong, .phase4-s3-item-main small { overflow-wrap:anywhere; }
      .phase4-s3-item-kcal { flex:none; font-weight:800; }
      .phase4-s3-state { min-height:72px; display:grid; place-content:center; gap:10px; text-align:center; color:var(--muted); }
      .phase4-s3-state.error { color:var(--text); }
      .phase4-s3-portal { position:fixed; inset:0; z-index:79; display:grid; align-items:end; }
      .phase4-s3-backdrop { position:absolute; inset:0; border:0; background:rgba(7,11,18,.72); }
      .phase4-s3-sheet { position:relative; z-index:1; width:100%; max-height:94dvh; overflow:auto; overscroll-behavior:contain; padding:16px 16px calc(22px + env(safe-area-inset-bottom)); border:1px solid var(--line); border-radius:8px 8px 0 0; background:var(--bg); color:var(--text); box-shadow:var(--shadow); display:grid; gap:14px; }
      body.phase4-s3-dialog-open { overflow:hidden; }
      .phase4-s3-dialog-head { position:sticky; top:-16px; z-index:2; margin:-16px -16px 0; padding:16px; align-items:flex-start; background:var(--bg); border-bottom:1px solid var(--line); }
      .phase4-s3-dialog-head > div { min-width:0; }
      .phase4-s3-close { min-width:44px; min-height:44px; flex:none; }
      .phase4-s3-form { display:grid; gap:12px; }
      .phase4-s3-form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
      .phase4-s3-form-grid .wide { grid-column:1 / -1; }
      .phase4-s3-form .field { min-width:0; }
      .phase4-s3-form input, .phase4-s3-form select, .phase4-s3-form textarea { width:100%; min-height:44px; }
      .phase4-s3-search-form { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; }
      .phase4-s3-search-list { display:grid; gap:8px; }
      .phase4-s3-search-row { display:grid; gap:6px; padding:11px 0; border-bottom:1px solid var(--line); }
      .phase4-s3-search-row strong, .phase4-s3-search-row small { overflow-wrap:anywhere; }
      .phase4-s3-search-head { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
      .phase4-s3-feedback { min-height:22px; margin:0; color:var(--muted); }
      .phase4-s3-feedback.error { color:#ffb0b0; }
      .phase4-s3-feedback.ok { color:#8bd8b8; }
      .phase4-s3-detail-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
      .phase4-s3-detail-grid > div { min-width:0; display:grid; gap:2px; }
      .phase4-s3-detail-grid span { color:var(--muted); font-size:12px; font-weight:800; }
      .phase4-s3-detail-grid strong { overflow-wrap:anywhere; }
      @media (min-width:720px) {
        .phase4-s3-shell { max-width:920px; }
        .phase4-s3-progress-grid { grid-template-columns:repeat(4,minmax(0,1fr)); }
        .phase4-s3-portal { align-items:center; justify-items:center; padding:24px; }
        .phase4-s3-sheet { width:min(760px,calc(100vw - 48px)); max-height:88dvh; border-radius:8px; }
      }
      @media (max-width:359px) {
        .phase4-s3-progress-grid, .phase4-s3-form-grid, .phase4-s3-detail-grid { grid-template-columns:1fr; }
        .phase4-s3-form-grid .wide { grid-column:auto; }
        .phase4-s3-search-form { grid-template-columns:1fr; }
        .phase4-s3-summary-head, .phase4-s3-meal-head { align-items:stretch; flex-direction:column; }
      }
    `;
    document.head.appendChild(style);
  }

  function feedbackMarkup() {
    const portal = slice3State.portal;
    const className = portal.feedbackType === "error" ? "error" : portal.feedbackType === "ok" ? "ok" : "";
    return `<p class="phase4-s3-feedback ${className}" aria-live="polite">${escapeHTML(portal.feedback || "")}</p>`;
  }

  function showFeedback(message, type = "") {
    slice3State.portal.feedback = message;
    slice3State.portal.feedbackType = type;
    const target = document.querySelector("#phase4Slice3Portal .phase4-s3-feedback");
    if (!target) return;
    target.className = `phase4-s3-feedback ${type === "error" ? "error" : type === "ok" ? "ok" : ""}`.trim();
    target.textContent = message;
  }

  function currentTarget() {
    const day = slice3State.day.value;
    if (day?.target) return day.target;
    if (!day?.log && slice3State.context?.target) return slice3State.context.target;
    return null;
  }

  function metricDefinition() {
    return [
      { key: "energy_kcal", label: text("kcal"), unit: "kcal", digits: 0 },
      { key: "protein_grams", label: text("protein"), unit: "g", digits: 1 },
      { key: "carbohydrate_grams", label: text("carbohydrate"), unit: "g", digits: 1 },
      { key: "fat_grams", label: text("fat"), unit: "g", digits: 1 }
    ];
  }

  function progressMarkup() {
    const totals = slice3State.day.value?.totals || {};
    const target = currentTarget();
    return metricDefinition().map((metric) => {
      const consumed = Number(totals[metric.key]) || 0;
      const targetValue = Number(target?.[metric.key]);
      const hasTarget = Number.isFinite(targetValue) && targetValue > 0;
      const difference = hasTarget ? targetValue - consumed : null;
      const percentage = hasTarget ? Math.max(0, consumed / targetValue * 100) : 0;
      const status = !hasTarget
        ? text("consumed")
        : difference >= 0
          ? text("remaining", { value: `${formatNumber(difference, metric.digits)} ${metric.unit}` })
          : text("above", { value: `${formatNumber(Math.abs(difference), metric.digits)} ${metric.unit}` });
      return `
        <div class="phase4-s3-progress">
          <div class="phase4-s3-progress-top">
            <div><span>${escapeHTML(metric.label)}</span><br><strong>${escapeHTML(`${formatNumber(consumed, metric.digits)} ${metric.unit}`)}</strong></div>
            ${hasTarget ? `<small>${escapeHTML(`${formatNumber(targetValue, metric.digits)} ${metric.unit}`)}</small>` : ""}
          </div>
          ${hasTarget ? `<div class="phase4-s3-track ${difference < 0 ? "over" : ""}" role="progressbar" aria-label="${escapeHTML(metric.label)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.min(100, Math.round(percentage))}"><span style="width:${Math.min(100, percentage)}%"></span></div>` : ""}
          <small>${escapeHTML(status)}</small>
        </div>
      `;
    }).join("");
  }

  function mealItems(meal) {
    return (slice3State.day.value?.items || []).filter((item) => item.meal_moment === meal && item.status === "active");
  }

  function mealMarkup(meal) {
    const items = mealItems(meal);
    return `
      <section class="phase4-s3-meal" aria-labelledby="phase4-s3-${meal}-title">
        <div class="phase4-s3-meal-head">
          <div>
            <h2 id="phase4-s3-${meal}-title">${escapeHTML(text(meal))}</h2>
            <small class="phase4-s3-muted">${escapeHTML(items.length ? `${items.length}` : text("emptyMeal"))}</small>
          </div>
          <button class="phase4-s3-gold" data-phase4-s3-add="${escapeHTML(meal)}" type="button" aria-haspopup="dialog">${escapeHTML(text("addFood"))}</button>
        </div>
        ${items.length ? `<div class="phase4-s3-item-list">${items.map(itemRowMarkup).join("")}</div>` : ""}
      </section>
    `;
  }

  function itemRowMarkup(item) {
    return `
      <button class="phase4-s3-item-row" data-phase4-s3-item="${escapeHTML(item.id)}" type="button" aria-haspopup="dialog">
        <span class="phase4-s3-item-main">
          <strong>${escapeHTML(item.food_name_snapshot || "-")}</strong>
          <small>${escapeHTML(`${formatNumber(item.consumed_quantity, 3)} ${unitLabel(item.consumed_unit)} | P ${formatNumber(item.protein_grams_snapshot, 1)}g | C ${formatNumber(item.carbohydrate_grams_snapshot, 1)}g | F ${formatNumber(item.fat_grams_snapshot, 1)}g`)}</small>
        </span>
        <span class="phase4-s3-item-kcal">${escapeHTML(`${formatNumber(item.energy_kcal_snapshot, 0)} kcal`)}</span>
      </button>
    `;
  }

  function renderRoot() {
    const root = slice3State.context?.root;
    if (!root) return;
    const context = slice3State.context;
    const isToday = slice3State.selectedDate === slice3State.todayDate;
    let content = "";
    if (!context.isOnline) {
      content = `<div class="phase4-s3-state error" aria-live="polite">${escapeHTML(text("onlineRequired"))}</div>`;
    } else if (!context.canHydrate) {
      content = `<div class="phase4-s3-state" aria-live="polite">${escapeHTML(text("authLoading"))}</div>`;
    } else if (["idle", "loading"].includes(slice3State.timezone.status)) {
      content = `<div class="phase4-s3-state" aria-live="polite">${escapeHTML(text("timezoneLoading"))}</div>`;
    } else if (slice3State.timezone.status === "error") {
      content = `<div class="phase4-s3-state error" aria-live="polite"><span>${escapeHTML(slice3State.timezone.error || text("timezoneFailed"))}</span><button class="secondary-btn" data-phase4-s3-retry-timezone type="button">${escapeHTML(text("retry"))}</button></div>`;
    } else if (["idle", "loading"].includes(slice3State.day.status)) {
      content = `<div class="phase4-s3-state" aria-live="polite">${escapeHTML(text("loadingDay"))}</div>`;
    } else if (slice3State.day.status === "error") {
      content = `<div class="phase4-s3-state error" aria-live="polite"><span>${escapeHTML(slice3State.day.error || text("loadDayFailed"))}</span><div class="phase4-s3-actions"><button class="secondary-btn" data-phase4-s3-retry-day type="button">${escapeHTML(text("retry"))}</button>${!isToday ? `<button class="phase4-s3-gold" data-phase4-s3-today type="button">${escapeHTML(text("backToToday"))}</button>` : ""}</div></div>`;
    } else {
      const hasTarget = Boolean(currentTarget() && Number(currentTarget().energy_kcal) > 0);
      const itemCount = (slice3State.day.value?.items || []).length;
      content = `
        <section class="phase4-s3-summary" aria-labelledby="phase4-s3-summary-title">
          <div class="phase4-s3-summary-head">
            <div><p class="eyebrow">${escapeHTML(text("consumed"))}</p><h2 id="phase4-s3-summary-title">${escapeHTML(formatDate(slice3State.selectedDate))}</h2></div>
            <button class="secondary-btn" data-phase4-open-target type="button" aria-haspopup="dialog">${escapeHTML(text(hasTarget ? "editTarget" : "setTarget"))}</button>
          </div>
          <div class="phase4-s3-progress-grid">${progressMarkup()}</div>
          ${hasTarget ? "" : `<p class="phase4-s3-muted">${escapeHTML(text("noTarget"))}</p>`}
          ${slice3State.notice ? `<p class="phase4-s3-feedback ok" aria-live="polite">${escapeHTML(slice3State.notice)}</p>` : ""}
          ${itemCount ? "" : `<p class="phase4-s3-muted">${escapeHTML(text("emptyDay"))}</p>`}
        </section>
        <div class="phase4-s3-meals">${PHASE4_SLICE3_MEALS.map(mealMarkup).join("")}</div>
        <div class="phase4-s3-actions"><button class="secondary-btn" data-phase4-open-foods type="button" aria-haspopup="dialog">${escapeHTML(text("manageFoods"))}</button></div>
      `;
    }
    root.innerHTML = `
      <div class="phase4-s3-shell">
        <header class="phase4-s3-head"><div><p class="eyebrow">${escapeHTML(text("nutrition"))}</p><h1>${escapeHTML(text("nutrition"))}</h1></div></header>
        ${context.canHydrate ? `<nav class="phase4-s3-date-nav" aria-label="${escapeHTML(text("nutrition"))}"><button class="secondary-btn phase4-s3-icon" data-phase4-s3-date="previous" type="button" title="${escapeHTML(text("previousDay"))}" aria-label="${escapeHTML(text("previousDay"))}">&larr;</button><strong>${escapeHTML(isToday ? text("today") : formatDate(slice3State.selectedDate))}</strong><button class="secondary-btn phase4-s3-icon" data-phase4-s3-date="next" type="button" title="${escapeHTML(text("nextDay"))}" aria-label="${escapeHTML(text("nextDay"))}" ${isToday ? "disabled" : ""}>&rarr;</button></nav>` : ""}
        ${content}
      </div>
    `;
  }

  function applyTargetContext() {
    if (slice3State.day.status !== "ready" || slice3State.day.value?.log || !slice3State.context?.target) return;
    slice3State.day.value = { ...slice3State.day.value, target: slice3State.context.target };
  }

  function renderOverview(context) {
    installStyles();
    slice3State.context = context;
    if (context.userId !== slice3State.userId) resetForUser(context.userId || "");
    slice3State.context = context;
    applyTargetContext();
    renderRoot();
    if (context.isOnline && context.canHydrate) {
      if (slice3State.timezone.status === "idle") ensureTimezone();
      else if (slice3State.timezone.status === "ready" && slice3State.day.status === "idle") loadDay();
    }
    return true;
  }

  async function ensureTimezone(force = false) {
    if (!slice3State.userId || !supabaseClient) return;
    if (!force && ["loading", "ready"].includes(slice3State.timezone.status)) return;
    const userId = slice3State.userId;
    const requestToken = slice3State.timezone.requestToken + 1;
    slice3State.timezone.requestToken = requestToken;
    slice3State.timezone.status = "loading";
    slice3State.timezone.error = "";
    slice3State.timezoneName = resolvedTimezone();
    renderRoot();
    try {
      const { error } = await supabaseClient.rpc("fmz_phase4_set_nutrition_timezone", { p_timezone_name: slice3State.timezoneName });
      if (error) throw error;
      if (slice3State.userId !== userId || slice3State.timezone.requestToken !== requestToken) return;
      slice3State.timezone.status = "ready";
      slice3State.day.status = "idle";
      renderRoot();
      loadDay();
    } catch (error) {
      if (slice3State.userId !== userId || slice3State.timezone.requestToken !== requestToken) return;
      slice3State.timezone.status = "error";
      slice3State.timezone.error = errorMessage(error, "timezone");
      renderRoot();
    }
  }

  async function loadDay(force = false) {
    if (!slice3State.userId || !supabaseClient || slice3State.timezone.status !== "ready") return;
    if (!force && ["loading", "ready"].includes(slice3State.day.status)) return;
    const userId = slice3State.userId;
    const selectedDate = slice3State.selectedDate;
    const requestToken = slice3State.day.requestToken + 1;
    slice3State.day.requestToken = requestToken;
    slice3State.day.status = "loading";
    slice3State.day.error = "";
    slice3State.notice = "";
    renderRoot();
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_get_nutrition_day", { p_log_date: selectedDate });
      if (error) throw error;
      if (slice3State.userId !== userId || slice3State.selectedDate !== selectedDate || slice3State.day.requestToken !== requestToken) return;
      if (!data || data.log_date !== selectedDate || !Array.isArray(data.items) || !data.totals) throw new Error("authoritative Nutrition day payload unavailable");
      slice3State.day.value = data;
      slice3State.day.status = "ready";
      applyTargetContext();
    } catch (error) {
      if (slice3State.userId !== userId || slice3State.selectedDate !== selectedDate || slice3State.day.requestToken !== requestToken) return;
      slice3State.day.status = "error";
      slice3State.day.error = errorMessage(error, "day");
    }
    renderRoot();
  }

  function errorMessage(error, context = "") {
    const code = String(error?.code || "");
    const message = String(error?.message || error || "").toLowerCase();
    if (code === "40001" || message.includes("changed; refresh") || message.includes("no longer active")) return text("stale");
    if (code === "23505" || message.includes("already used with a different payload") || message.includes("uuid is unavailable")) return text("conflict");
    if (message.includes("seven local calendar days")) return text("freeHistory");
    if (message.includes("future nutrition")) return text("futureDay");
    if (message.includes("maximum 10 active custom foods") || message.includes("free nutrition limit")) return text("customLimitReached");
    if (message.includes("network") || message.includes("fetch") || message.includes("connection")) return text("networkRetry");
    if (context === "search") return text("searchFailed");
    if (context === "timezone") return text("timezoneFailed");
    if (context === "day") return text("loadDayFailed");
    return text("unexpected");
  }

  function changeDate(direction) {
    const next = direction === "previous" ? shiftDate(slice3State.selectedDate, -1) : shiftDate(slice3State.selectedDate, 1);
    if (next > slice3State.todayDate) return;
    closePortal(false);
    slice3State.selectedDate = next;
    slice3State.day = { status: "idle", value: null, error: "", requestToken: slice3State.day.requestToken + 1 };
    renderRoot();
    loadDay();
  }

  function goToday() {
    slice3State.selectedDate = slice3State.todayDate;
    slice3State.day = { status: "idle", value: null, error: "", requestToken: slice3State.day.requestToken + 1 };
    renderRoot();
    loadDay();
  }

  function dialogFrame(title, body, eyebrow = text("nutrition")) {
    return `
      <button class="phase4-s3-backdrop" data-phase4-s3-close type="button" aria-label="${escapeHTML(text("close"))}"></button>
      <section class="phase4-s3-sheet" role="dialog" aria-modal="true" aria-labelledby="phase4-s3-dialog-title">
        <header class="phase4-s3-dialog-head"><div><p class="eyebrow">${escapeHTML(eyebrow)}</p><h2 id="phase4-s3-dialog-title">${escapeHTML(title)}</h2></div><button class="secondary-btn phase4-s3-close" data-phase4-s3-close type="button">${escapeHTML(text("close"))}</button></header>
        ${body}
      </section>
    `;
  }

  function openPortal(type, opener = document.activeElement, options = {}) {
    const previous = slice3State.portal;
    closePortal(false);
    slice3State.portal = {
      type,
      opener: opener || previous.opener,
      meal: options.meal || previous.meal || "breakfast",
      food: options.food || null,
      item: options.item || null,
      feedback: options.feedback || "",
      feedbackType: options.feedbackType || ""
    };
    document.body.classList.add("phase4-s3-dialog-open");
    renderPortal();
  }

  function closePortal(restoreFocus = true) {
    const opener = slice3State.portal?.opener;
    document.getElementById("phase4Slice3Portal")?.remove();
    document.body.classList.remove("phase4-s3-dialog-open");
    slice3State.portal = { type: "", opener: null, meal: "breakfast", food: null, item: null, feedback: "", feedbackType: "" };
    if (restoreFocus) opener?.focus?.();
  }

  function renderPortal() {
    if (!slice3State.portal.type) return;
    let portal = document.getElementById("phase4Slice3Portal");
    const isNew = !portal;
    if (!portal) {
      portal = document.createElement("div");
      portal.id = "phase4Slice3Portal";
      portal.className = "phase4-s3-portal";
      document.body.appendChild(portal);
    }
    if (slice3State.portal.type === "search") portal.innerHTML = searchDialog();
    if (slice3State.portal.type === "entry") portal.innerHTML = entryDialog();
    if (slice3State.portal.type === "item") portal.innerHTML = itemDialog();
    if (slice3State.portal.type === "remove") portal.innerHTML = removeDialog();
    if (slice3State.portal.type === "custom") portal.innerHTML = customDialog();
    if (isNew) window.requestAnimationFrame(() => portal.querySelector("input, button, select")?.focus?.());
  }

  function openSearch(meal, opener, item = null) {
    slice3State.search = { status: "idle", query: "", items: [], afterName: null, afterId: null, hasMore: false, error: "", requestToken: slice3State.search.requestToken + 1 };
    openPortal("search", opener, { meal, item });
    searchFoods({ reset: true });
  }

  function searchDialog() {
    const search = slice3State.search;
    let results = "";
    if (search.status === "loading" && !search.items.length) results = `<div class="phase4-s3-state" aria-live="polite">${escapeHTML(text("searchLoading"))}</div>`;
    else if (search.status === "error" && !search.items.length) results = `<div class="phase4-s3-state error" aria-live="polite"><span>${escapeHTML(search.error)}</span><button class="secondary-btn" data-phase4-s3-retry-search type="button">${escapeHTML(text("retry"))}</button></div>`;
    else if (search.status === "ready" && !search.items.length) results = `<div class="phase4-s3-state" aria-live="polite"><strong>${escapeHTML(text("noFoods"))}</strong><button class="phase4-s3-gold" data-phase4-s3-custom type="button">${escapeHTML(text("createCustom"))}</button></div>`;
    else results = `
      <div class="phase4-s3-search-list" aria-live="polite">${search.items.map(searchRow).join("")}</div>
      ${search.status === "error" ? `<p class="phase4-s3-feedback error">${escapeHTML(search.error)}</p>` : ""}
      ${search.hasMore || search.status === "loading" ? `<button class="secondary-btn" data-phase4-s3-more-search type="button" ${search.status === "loading" ? "disabled" : ""}>${escapeHTML(search.status === "loading" ? text("searchLoading") : text("loadMore"))}</button>` : ""}
    `;
    const body = `
      <form id="phase4Slice3SearchForm" class="phase4-s3-search-form" role="search"><label class="field"><span class="sr-only">${escapeHTML(text("searchFood"))}</span><input name="query" type="search" value="${escapeHTML(search.query)}" placeholder="${escapeHTML(text("searchPlaceholder"))}" autocomplete="off"></label><button class="phase4-s3-gold" type="submit">${escapeHTML(text("search"))}</button></form>
      ${feedbackMarkup()}
      <div><p class="eyebrow">${escapeHTML(text("results"))}</p>${results}</div>
      <div class="phase4-s3-dialog-actions"><button class="secondary-btn" data-phase4-s3-custom type="button">${escapeHTML(text("createCustom"))}</button></div>
    `;
    return dialogFrame(text("searchFood"), body, text(slice3State.portal.meal));
  }

  function searchRow(food) {
    return `
      <article class="phase4-s3-search-row">
        <div class="phase4-s3-search-head"><div><strong>${escapeHTML(food.name || "-")}</strong>${food.brand ? `<br><small>${escapeHTML(food.brand)}</small>` : ""}</div><button class="phase4-s3-gold" data-phase4-s3-select-food="${escapeHTML(food.id)}" type="button">${escapeHTML(text("select"))}</button></div>
        <small>${escapeHTML(text("reference", { amount: formatNumber(food.reference_amount, 3), unit: unitLabel(food.reference_unit) }))}</small>
        <small>${escapeHTML(`${formatNumber(food.energy_kcal, 1)} kcal | P ${formatNumber(food.protein_grams, 1)}g | C ${formatNumber(food.carbohydrate_grams, 1)}g | F ${formatNumber(food.fat_grams, 1)}g`)}</small>
      </article>
    `;
  }

  async function searchFoods({ reset = true } = {}) {
    if (!slice3State.userId || !supabaseClient) return;
    const search = slice3State.search;
    const requestToken = search.requestToken + 1;
    search.requestToken = requestToken;
    search.status = "loading";
    search.error = "";
    if (reset) {
      search.items = [];
      search.afterName = null;
      search.afterId = null;
      search.hasMore = false;
    }
    renderPortal();
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_search_foods", {
        p_query: search.query || null,
        p_page_size: PHASE4_SLICE3_SEARCH_PAGE_SIZE,
        p_after_name: reset ? null : search.afterName,
        p_after_id: reset ? null : search.afterId
      });
      if (error) throw error;
      if (search.requestToken !== requestToken || slice3State.portal.type !== "search") return;
      const rows = Array.isArray(data) ? data : [];
      const map = new Map((reset ? [] : search.items).map((food) => [food.id, food]));
      rows.forEach((food) => map.set(food.id, food));
      search.items = Array.from(map.values());
      const last = rows[rows.length - 1];
      search.afterName = last?.name || null;
      search.afterId = last?.id || null;
      search.hasMore = rows.length === PHASE4_SLICE3_SEARCH_PAGE_SIZE;
      search.status = "ready";
    } catch (error) {
      if (search.requestToken !== requestToken || slice3State.portal.type !== "search") return;
      search.status = "error";
      search.error = errorMessage(error, "search");
    }
    renderPortal();
  }

  function selectSearchFood(foodId) {
    const food = slice3State.search.items.find((entry) => entry.id === foodId);
    if (!food) return;
    openEntry(food, slice3State.portal.meal, slice3State.portal.opener, slice3State.portal.item);
  }

  function unitLabel(unit) {
    if (unit === "serving") return text("unitServing");
    if (unit === "piece") return text("unitPiece");
    return unit || "";
  }

  function directUnits(food) {
    const result = [food?.reference_unit].filter((unit) => PHASE4_SLICE3_UNITS.includes(unit));
    if (food?.density_g_per_ml && food.reference_unit === "g") result.push("ml");
    if (food?.density_g_per_ml && food.reference_unit === "ml") result.push("g");
    return Array.from(new Set(result));
  }

  function resetSubmission(kind) {
    slice3State.submission = { kind, itemId: uuid(), requestId: uuid(), submittedFingerprint: "" };
  }

  function openEntry(food, meal, opener, item = null) {
    resetSubmission(item ? "edit" : "new");
    slice3State.portions = { status: "idle", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    openPortal("entry", opener, { food, meal, item });
    loadPortions(food.id);
  }

  async function loadPortions(foodId) {
    if (!supabaseClient || !foodId) return;
    const requestToken = slice3State.portions.requestToken + 1;
    slice3State.portions.requestToken = requestToken;
    slice3State.portions.status = "loading";
    slice3State.portions.error = "";
    renderPortal();
    try {
      const { data, error } = await supabaseClient.from("food_portions").select("id,food_id,label,amount,unit,equivalent_amount,equivalent_unit,status").eq("food_id", foodId).eq("status", "active").order("label", { ascending: true });
      if (error) throw error;
      if (slice3State.portions.requestToken !== requestToken || slice3State.portal.type !== "entry" || slice3State.portal.food?.id !== foodId) return;
      slice3State.portions.items = Array.isArray(data) ? data : [];
      slice3State.portions.status = "ready";
    } catch (error) {
      if (slice3State.portions.requestToken !== requestToken || slice3State.portal.type !== "entry") return;
      slice3State.portions.status = "error";
      slice3State.portions.error = errorMessage(error);
    }
    renderPortal();
  }

  function entrySelection(food, item) {
    if (item?.food_portion_id && slice3State.portions.items.some((portion) => portion.id === item.food_portion_id)) return `portion:${item.food_portion_id}`;
    const units = directUnits(food);
    if (item?.consumed_unit && units.includes(item.consumed_unit)) return `direct:${item.consumed_unit}`;
    return `direct:${units[0] || food.reference_unit || "g"}`;
  }

  function entryDialog() {
    const food = slice3State.portal.food || {};
    const item = slice3State.portal.item;
    const selection = entrySelection(food, item);
    const unitOptions = directUnits(food).map((unit) => `<option value="direct:${escapeHTML(unit)}" ${selection === `direct:${unit}` ? "selected" : ""}>${escapeHTML(text("directUnit", { unit: unitLabel(unit) }))}</option>`).join("");
    const portionOptions = slice3State.portions.items.map((portion) => `<option value="portion:${escapeHTML(portion.id)}" ${selection === `portion:${portion.id}` ? "selected" : ""}>${escapeHTML(text("portion", { label: portion.label, amount: formatNumber(portion.amount, 3), unit: unitLabel(portion.unit) }))}</option>`).join("");
    const body = `
      <div><strong>${escapeHTML(food.name || item?.food_name_snapshot || "-")}</strong>${food.brand ? `<br><small class="phase4-s3-muted">${escapeHTML(food.brand)}</small>` : ""}</div>
      <form id="phase4Slice3EntryForm" class="phase4-s3-form" novalidate>
        <div class="phase4-s3-form-grid">
          <label class="field"><span>${escapeHTML(text("meal"))}</span><select name="meal">${PHASE4_SLICE3_MEALS.map((meal) => `<option value="${meal}" ${meal === (item?.meal_moment || slice3State.portal.meal) ? "selected" : ""}>${escapeHTML(text(meal))}</option>`).join("")}</select></label>
          <label class="field"><span>${escapeHTML(text("amount"))}</span><input name="quantity" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" required value="${escapeHTML(item?.consumed_quantity ?? (food.reference_amount || 1))}" autocomplete="off"></label>
          <label class="field wide"><span>${escapeHTML(text("unitOrPortion"))}</span><select name="selection">${unitOptions}${portionOptions}</select></label>
          <label class="field wide"><span>${escapeHTML(text("notes"))}</span><textarea name="notes" maxlength="1000" rows="3">${escapeHTML(item?.notes || "")}</textarea></label>
        </div>
        ${slice3State.portions.status === "loading" ? `<p class="phase4-s3-muted">${escapeHTML(text("portionsLoading"))}</p>` : ""}
        ${slice3State.portions.status === "error" ? `<p class="phase4-s3-feedback error">${escapeHTML(slice3State.portions.error)}</p>` : ""}
        <p class="phase4-s3-muted">${escapeHTML(text("serverCalculated"))}</p>
        ${feedbackMarkup()}
        <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" type="submit">${escapeHTML(text(item ? "saveEdit" : "saveEntry"))}</button><button class="secondary-btn" data-phase4-s3-change-food type="button">${escapeHTML(text("changeFood"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("cancel"))}</button></div>
      </form>
    `;
    return dialogFrame(text(item ? "editEntryTitle" : "entryTitle"), body, text(item?.meal_moment || slice3State.portal.meal));
  }

  function entryPayload(form) {
    const data = new FormData(form);
    const selection = String(data.get("selection") || "");
    const portionId = selection.startsWith("portion:") ? selection.slice(8) : null;
    const portion = portionId ? slice3State.portions.items.find((entry) => entry.id === portionId) : null;
    const consumedUnit = portion ? portion.unit : selection.startsWith("direct:") ? selection.slice(7) : "";
    return {
      meal: String(data.get("meal") || ""),
      quantity: Number(data.get("quantity")),
      consumedUnit,
      portionId,
      notes: String(data.get("notes") || "").trim()
    };
  }

  function validateEntry(payload) {
    const errors = [];
    if (!PHASE4_SLICE3_MEALS.includes(payload.meal) || !PHASE4_SLICE3_UNITS.includes(payload.consumedUnit)) errors.push(text("validation"));
    if (!Number.isFinite(payload.quantity) || payload.quantity <= 0 || payload.quantity > 100000) errors.push(text("quantityRange"));
    if (payload.notes.length > 1000) errors.push(text("notesRange"));
    return Array.from(new Set(errors));
  }

  function entryFingerprint(payload, foodId, originalId = null) {
    return JSON.stringify([originalId, foodId, payload.portionId, payload.meal, payload.quantity, payload.consumedUnit, payload.notes || null]);
  }

  function prepareSubmission(kind, fingerprint) {
    if (slice3State.submission.kind !== kind || !slice3State.submission.itemId || !slice3State.submission.requestId) resetSubmission(kind);
    if (slice3State.submission.submittedFingerprint && slice3State.submission.submittedFingerprint !== fingerprint) resetSubmission(kind);
    slice3State.submission.submittedFingerprint = fingerprint;
  }

  async function saveEntry(form) {
    const food = slice3State.portal.food;
    const original = slice3State.portal.item;
    if (!food?.id || !supabaseClient) return;
    const payload = entryPayload(form);
    const errors = validateEntry(payload);
    if (errors.length) {
      showFeedback(errors.join(" "), "error");
      return;
    }
    const kind = original ? "edit" : "new";
    const fingerprint = entryFingerprint(payload, food.id, original?.id || null);
    prepareSubmission(kind, fingerprint);
    showFeedback(text("saving"));
    try {
      const response = original
        ? await supabaseClient.rpc("fmz_phase4_replace_food_log_item", {
            p_original_item_id: original.id,
            p_replacement_item_id: slice3State.submission.itemId,
            p_replacement_request_id: slice3State.submission.requestId,
            p_expected_original_updated_at: original.updated_at,
            p_meal_moment: payload.meal,
            p_food_id: food.id,
            p_food_portion_id: payload.portionId,
            p_consumed_quantity: payload.quantity,
            p_consumed_unit: payload.consumedUnit,
            p_notes: payload.notes || null
          })
        : await supabaseClient.rpc("fmz_phase4_log_food_item", {
            p_item_id: slice3State.submission.itemId,
            p_request_id: slice3State.submission.requestId,
            p_log_date: slice3State.selectedDate,
            p_timezone_name: slice3State.timezoneName,
            p_timezone_offset_minutes: timezoneOffsetMinutes(slice3State.selectedDate),
            p_meal_moment: payload.meal,
            p_food_id: food.id,
            p_food_portion_id: payload.portionId,
            p_consumed_quantity: payload.quantity,
            p_consumed_unit: payload.consumedUnit,
            p_notes: payload.notes || null,
            p_consumed_at: localConsumedAt(slice3State.selectedDate)
          });
      if (response.error) throw response.error;
      if (!response.data?.day || response.data.day.log_date !== slice3State.selectedDate) throw new Error("authoritative Nutrition day payload unavailable");
      slice3State.day = { status: "ready", value: response.data.day, error: "", requestToken: slice3State.day.requestToken + 1 };
      slice3State.notice = text(original ? "edited" : "saved");
      slice3State.submission = { kind: "", itemId: "", requestId: "", submittedFingerprint: "" };
      closePortal();
      renderRoot();
    } catch (error) {
      const code = String(error?.code || "");
      const message = errorMessage(error);
      if (code === "23505") slice3State.submission = { kind, itemId: uuid(), requestId: uuid(), submittedFingerprint: "" };
      showFeedback(message, "error");
      if (code === "40001") loadDay(true);
    }
  }

  function findItem(itemId) {
    return (slice3State.day.value?.items || []).find((item) => item.id === itemId) || null;
  }

  function itemDialog() {
    const item = slice3State.portal.item || {};
    const body = `
      <div class="phase4-s3-detail-grid">
        <div class="wide"><span>${escapeHTML(text("name"))}</span><strong>${escapeHTML(item.food_name_snapshot || "-")}</strong></div>
        ${item.brand_snapshot ? `<div class="wide"><span>${escapeHTML(text("brand"))}</span><strong>${escapeHTML(item.brand_snapshot)}</strong></div>` : ""}
        <div><span>${escapeHTML(text("meal"))}</span><strong>${escapeHTML(text(item.meal_moment))}</strong></div>
        <div><span>${escapeHTML(text("amount"))}</span><strong>${escapeHTML(`${formatNumber(item.consumed_quantity, 3)} ${unitLabel(item.consumed_unit)}`)}</strong></div>
        <div><span>${escapeHTML(text("kcal"))}</span><strong>${escapeHTML(`${formatNumber(item.energy_kcal_snapshot, 1)} kcal`)}</strong></div>
        <div><span>${escapeHTML(text("protein"))}</span><strong>${escapeHTML(`${formatNumber(item.protein_grams_snapshot, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(text("carbohydrate"))}</span><strong>${escapeHTML(`${formatNumber(item.carbohydrate_grams_snapshot, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(text("fat"))}</span><strong>${escapeHTML(`${formatNumber(item.fat_grams_snapshot, 1)} g`)}</strong></div>
        ${item.notes ? `<div class="wide"><span>${escapeHTML(text("notes"))}</span><strong>${escapeHTML(item.notes)}</strong></div>` : ""}
        <div class="wide"><span>${escapeHTML(text("sourceSnapshot"))}</span><strong>${escapeHTML(item.source_provider_snapshot || "-")}</strong></div>
      </div>
      ${feedbackMarkup()}
      <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" data-phase4-s3-edit-item type="button">${escapeHTML(text("edit"))}</button><button class="secondary-btn" data-phase4-s3-remove-item type="button">${escapeHTML(text("remove"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("close"))}</button></div>
    `;
    return dialogFrame(item.food_name_snapshot || text("details"), body, text("details"));
  }

  function removeDialog() {
    const item = slice3State.portal.item || {};
    const body = `<p>${escapeHTML(text("removeBody"))}</p><strong>${escapeHTML(item.food_name_snapshot || "-")}</strong>${feedbackMarkup()}<div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" data-phase4-s3-confirm-remove type="button">${escapeHTML(text("confirmRemove"))}</button><button class="secondary-btn" data-phase4-s3-back-item type="button">${escapeHTML(text("cancel"))}</button></div>`;
    return dialogFrame(text("removeTitle"), body, text("nutrition"));
  }

  async function archiveItem() {
    const item = slice3State.portal.item;
    if (!item?.id || !supabaseClient) return;
    showFeedback(text("saving"));
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_archive_food_log_item", { p_item_id: item.id, p_expected_updated_at: item.updated_at });
      if (error) throw error;
      if (!data?.day || data.day.log_date !== slice3State.selectedDate) throw new Error("authoritative Nutrition day payload unavailable");
      slice3State.day = { status: "ready", value: data.day, error: "", requestToken: slice3State.day.requestToken + 1 };
      slice3State.notice = text("removed");
      closePortal();
      renderRoot();
    } catch (error) {
      showFeedback(errorMessage(error), "error");
      if (String(error?.code || "") === "40001") loadDay(true);
    }
  }

  async function loadFoodForEdit(item, opener) {
    if (!item?.food_id || !supabaseClient) return;
    showFeedback(text("searchLoading"));
    try {
      const query = supabaseClient.from("foods").select("id,catalog_scope,name,brand,reference_amount,reference_unit,reference_mass_grams,reference_volume_ml,density_g_per_ml,energy_kcal,protein_grams,carbohydrate_grams,fat_grams,fiber_grams,status,source_provider,updated_at").eq("id", item.food_id).eq("status", "active");
      const { data, error } = typeof query.maybeSingle === "function" ? await query.maybeSingle() : await query.single();
      if (error) throw error;
      if (!data) throw new Error("active visible food not found");
      openEntry(data, item.meal_moment, opener, item);
    } catch (error) {
      showFeedback(errorMessage(error), "error");
    }
  }

  function customDialog() {
    const unitOptions = PHASE4_SLICE3_UNITS.map((unit) => `<option value="${unit}">${escapeHTML(unitLabel(unit))}</option>`).join("");
    const body = `
      <form id="phase4Slice3CustomForm" class="phase4-s3-form" novalidate>
        <p class="phase4-s3-muted">${escapeHTML(text("customIntro"))}</p>
        <div class="phase4-s3-form-grid">
          <label class="field wide"><span>${escapeHTML(text("name"))}</span><input name="name" maxlength="240" required autocomplete="off"></label>
          <label class="field wide"><span>${escapeHTML(text("brand"))}</span><input name="brand" maxlength="160" autocomplete="off"></label>
          <label class="field"><span>${escapeHTML(text("referenceAmount"))}</span><input name="referenceAmount" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" value="100" required autocomplete="off"></label>
          <label class="field"><span>${escapeHTML(text("referenceUnit"))}</span><select name="referenceUnit">${unitOptions}</select></label>
          <label class="field" data-phase4-s3-conversion hidden><span>${escapeHTML(text("conversionAmount"))}</span><input name="conversionAmount" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" autocomplete="off"></label>
          <label class="field" data-phase4-s3-conversion hidden><span>${escapeHTML(text("conversionUnit"))}</span><select name="conversionUnit"><option value="g">g</option><option value="ml">ml</option></select></label>
          <label class="field"><span>${escapeHTML(text("energy"))}</span><input name="energy" type="number" inputmode="decimal" min="0" max="1000000" step="0.1" required autocomplete="off"></label>
          <label class="field"><span>${escapeHTML(text("protein"))} (g)</span><input name="protein" type="number" inputmode="decimal" min="0" max="100000" step="0.1" required autocomplete="off"></label>
          <label class="field"><span>${escapeHTML(text("carbohydrate"))} (g)</span><input name="carbohydrate" type="number" inputmode="decimal" min="0" max="100000" step="0.1" required autocomplete="off"></label>
          <label class="field"><span>${escapeHTML(text("fat"))} (g)</span><input name="fat" type="number" inputmode="decimal" min="0" max="100000" step="0.1" required autocomplete="off"></label>
          <label class="field wide"><span>${escapeHTML(text("fiber"))} (g)</span><input name="fiber" type="number" inputmode="decimal" min="0" max="100000" step="0.1" autocomplete="off"></label>
        </div>
        <p class="phase4-s3-muted">${escapeHTML(text("customLimit"))}</p>
        ${feedbackMarkup()}
        <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" type="submit">${escapeHTML(text("saveCustom"))}</button><button class="secondary-btn" data-phase4-s3-back-search type="button">${escapeHTML(text("back"))}</button></div>
      </form>
    `;
    return dialogFrame(text("customTitle"), body, text(slice3State.portal.meal));
  }

  function customPayload(form) {
    const data = new FormData(form);
    const unit = String(data.get("referenceUnit") || "g");
    const referenceAmount = Number(data.get("referenceAmount"));
    const conversionAmount = Number(data.get("conversionAmount"));
    const conversionUnit = String(data.get("conversionUnit") || "g");
    const needsConversion = ["serving", "piece"].includes(unit);
    const explicitAmount = needsConversion ? conversionAmount : referenceAmount;
    return {
      name: String(data.get("name") || "").trim(),
      brand: String(data.get("brand") || "").trim(),
      referenceAmount,
      referenceUnit: unit,
      referenceMass: unit === "g" || (needsConversion && conversionUnit === "g") ? explicitAmount : null,
      referenceVolume: unit === "ml" || (needsConversion && conversionUnit === "ml") ? explicitAmount : null,
      energy: Number(data.get("energy")),
      protein: Number(data.get("protein")),
      carbohydrate: Number(data.get("carbohydrate")),
      fat: Number(data.get("fat")),
      fiber: data.get("fiber") === "" ? null : Number(data.get("fiber")),
      needsConversion,
      conversionAmount
    };
  }

  function validateCustom(payload) {
    const nutrients = [payload.energy, payload.protein, payload.carbohydrate, payload.fat];
    return Boolean(
      payload.name && payload.name.length <= 240 && payload.brand.length <= 160
      && PHASE4_SLICE3_UNITS.includes(payload.referenceUnit)
      && Number.isFinite(payload.referenceAmount) && payload.referenceAmount > 0 && payload.referenceAmount <= 100000
      && (!payload.needsConversion || (Number.isFinite(payload.conversionAmount) && payload.conversionAmount > 0 && payload.conversionAmount <= 100000))
      && nutrients.every((value) => Number.isFinite(value) && value >= 0)
      && payload.energy <= 1000000
      && [payload.protein, payload.carbohydrate, payload.fat].every((value) => value <= 100000)
      && (payload.fiber === null || (Number.isFinite(payload.fiber) && payload.fiber >= 0 && payload.fiber <= 100000))
    );
  }

  function customFingerprint(payload) {
    return JSON.stringify([payload.name, payload.brand, payload.referenceAmount, payload.referenceUnit, payload.referenceMass, payload.referenceVolume, payload.energy, payload.protein, payload.carbohydrate, payload.fat, payload.fiber]);
  }

  async function saveCustom(form) {
    const payload = customPayload(form);
    if (!validateCustom(payload)) {
      showFeedback(payload.needsConversion && !payload.conversionAmount ? text("conversionRequired") : text("customValidation"), "error");
      return;
    }
    const fingerprint = customFingerprint(payload);
    if (!slice3State.customDraft.foodId) slice3State.customDraft.foodId = uuid();
    if (slice3State.customDraft.submittedFingerprint && slice3State.customDraft.submittedFingerprint !== fingerprint) slice3State.customDraft.foodId = uuid();
    slice3State.customDraft.submittedFingerprint = fingerprint;
    showFeedback(text("saving"));
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_upsert_custom_food", {
        p_food_id: slice3State.customDraft.foodId,
        p_name: payload.name,
        p_brand: payload.brand || null,
        p_reference_amount: payload.referenceAmount,
        p_reference_unit: payload.referenceUnit,
        p_reference_mass_grams: payload.referenceMass,
        p_reference_volume_ml: payload.referenceVolume,
        p_density_g_per_ml: null,
        p_energy_kcal: payload.energy,
        p_protein_grams: payload.protein,
        p_carbohydrate_grams: payload.carbohydrate,
        p_fat_grams: payload.fat,
        p_fiber_grams: payload.fiber,
        p_expected_updated_at: null
      });
      if (error) throw error;
      if (!data?.id) throw new Error("custom food result unavailable");
      slice3State.customDraft = { foodId: "", submittedFingerprint: "" };
      openEntry(data, slice3State.portal.meal, slice3State.portal.opener, slice3State.portal.item);
    } catch (error) {
      showFeedback(errorMessage(error), "error");
    }
  }

  function handleClick(event) {
    const button = event.target?.closest?.("button");
    if (!button) return;
    if (button.dataset.phase4S3Date) return changeDate(button.dataset.phase4S3Date);
    if (button.dataset.phase4S3Today !== undefined) return goToday();
    if (button.dataset.phase4S3RetryTimezone !== undefined) return ensureTimezone(true);
    if (button.dataset.phase4S3RetryDay !== undefined) return loadDay(true);
    if (button.dataset.phase4S3Add) return openSearch(button.dataset.phase4S3Add, button);
    if (button.dataset.phase4S3Item) {
      const item = findItem(button.dataset.phase4S3Item);
      if (item) openPortal("item", button, { item, meal: item.meal_moment });
      return;
    }
    if (button.dataset.phase4S3Close !== undefined) return closePortal();
    if (button.dataset.phase4S3RetrySearch !== undefined) return searchFoods({ reset: true });
    if (button.dataset.phase4S3MoreSearch !== undefined) return searchFoods({ reset: false });
    if (button.dataset.phase4S3SelectFood) return selectSearchFood(button.dataset.phase4S3SelectFood);
    if (button.dataset.phase4S3Custom !== undefined) {
      slice3State.customDraft = { foodId: uuid(), submittedFingerprint: "" };
      return openPortal("custom", slice3State.portal.opener || button, { meal: slice3State.portal.meal, item: slice3State.portal.item });
    }
    if (button.dataset.phase4S3BackSearch !== undefined || button.dataset.phase4S3ChangeFood !== undefined) return openSearch(slice3State.portal.meal, slice3State.portal.opener || button, slice3State.portal.item);
    if (button.dataset.phase4S3EditItem !== undefined) return loadFoodForEdit(slice3State.portal.item, slice3State.portal.opener || button);
    if (button.dataset.phase4S3RemoveItem !== undefined) return openPortal("remove", slice3State.portal.opener || button, { item: slice3State.portal.item, meal: slice3State.portal.meal });
    if (button.dataset.phase4S3BackItem !== undefined) return openPortal("item", slice3State.portal.opener || button, { item: slice3State.portal.item, meal: slice3State.portal.meal });
    if (button.dataset.phase4S3ConfirmRemove !== undefined) return archiveItem();
  }

  function handleSubmit(event) {
    if (event.target?.id === "phase4Slice3SearchForm") {
      event.preventDefault();
      slice3State.search.query = String(new FormData(event.target).get("query") || "").trim();
      searchFoods({ reset: true });
    }
    if (event.target?.id === "phase4Slice3EntryForm") {
      event.preventDefault();
      saveEntry(event.target);
    }
    if (event.target?.id === "phase4Slice3CustomForm") {
      event.preventDefault();
      saveCustom(event.target);
    }
  }

  function handleChange(event) {
    if (!event.target?.matches?.('#phase4Slice3CustomForm select[name="referenceUnit"]')) return;
    const visible = ["serving", "piece"].includes(event.target.value);
    event.target.form?.querySelectorAll("[data-phase4-s3-conversion]").forEach((field) => { field.hidden = !visible; });
  }

  function handleKeydown(event) {
    if (event.key === "Escape" && slice3State.portal.type) {
      event.preventDefault();
      closePortal();
    }
  }

  document.addEventListener("click", handleClick);
  document.addEventListener("submit", handleSubmit);
  document.addEventListener("change", handleChange);
  document.addEventListener("keydown", handleKeydown);

  window.FMZ_PHASE4_NUTRITION_SLICE3 = Object.freeze({
    version: PHASE4_SLICE3_VERSION,
    freeHistoryDays: PHASE4_SLICE3_FREE_HISTORY_DAYS,
    searchPageSize: PHASE4_SLICE3_SEARCH_PAGE_SIZE,
    renderOverview,
    validateEntry: (payload) => validateEntry({ ...payload }),
    state: () => ({
      userId: slice3State.userId,
      selectedDate: slice3State.selectedDate,
      todayDate: slice3State.todayDate,
      timezoneStatus: slice3State.timezone.status,
      dayStatus: slice3State.day.status,
      portalType: slice3State.portal.type,
      activeItemCount: (slice3State.day.value?.items || []).length
    })
  });
})();
