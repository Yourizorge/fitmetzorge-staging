(() => {
  if (window.FMZ_PHASE4_NUTRITION_SLICE2_LOADED) return;
  window.FMZ_PHASE4_NUTRITION_SLICE2_LOADED = true;

  const PHASE4_NUTRITION_SLICE2_VERSION = "20260818-phase4-nutrition-slice2-1";
  const PHASE4_LANGUAGES = ["nl", "en", "de"];
  const PHASE4_SEARCH_PAGE_SIZE = 25;
  const PHASE4_CUSTOM_PAGE_SIZE = 25;
  const PHASE4_CUSTOM_FOOD_FREE_LIMIT = 10;
  const PHASE4_UNITS = ["g", "ml", "serving", "piece"];

  const PHASE4_I18N = {
    nl: {
      nutrition: "Voeding",
      today: "Vandaag",
      dayTarget: "Dagdoel",
      noTarget: "Nog geen dagdoel ingesteld.",
      targetLoading: "Dagdoel laden...",
      targetLoadFailed: "Dagdoel kon niet worden geladen.",
      setTargets: "Doelen instellen",
      editTargets: "Doelen aanpassen",
      foods: "Voedingsmiddelen",
      foodsSummary: "Zoek in de catalogus of beheer je eigen voedingsmiddelen.",
      openFoods: "Voedingsmiddelen openen",
      noDailyEntry: "Nog geen voedingsinvoer voor vandaag.",
      energy: "Kcal",
      protein: "Eiwit",
      carbohydrate: "Koolhydraten",
      fat: "Vet",
      fiber: "Vezels",
      grams: "g",
      targetDialogTitle: "Dagdoel instellen",
      targetDialogIntro: "Vul je dagelijkse doelen handmatig in.",
      saveTarget: "Doelen opslaan",
      saving: "Opslaan...",
      saved: "Opgeslagen",
      close: "Sluiten",
      cancel: "Annuleren",
      retry: "Opnieuw proberen",
      required: "Dit veld is verplicht.",
      invalidTarget: "Controleer de doelwaarden.",
      positiveEnergy: "Kcal moet hoger dan 0 en maximaal 20000 zijn.",
      macroRange: "Macrodoelen moeten tussen 0 en 2000 gram liggen.",
      authNotReady: "Je Nutrition-profiel wordt nog geladen.",
      onlineRequired: "Nutrition is alleen beschikbaar met een actieve stagingverbinding.",
      searchFoods: "Voedingsmiddel zoeken",
      searchPlaceholder: "Zoek op naam, merk of barcode",
      search: "Zoeken",
      searchTab: "Zoeken",
      customTab: "Mijn producten",
      results: "Resultaten",
      searchLoading: "Voedingsmiddelen laden...",
      searchError: "Zoeken is niet gelukt.",
      emptyCatalog: "Geen voedingsmiddelen gevonden.",
      emptyCatalogDetail: "Maak een eigen voedingsmiddel als de catalogus nog geen passend resultaat bevat.",
      createCustom: "Eigen voedingsmiddel maken",
      loadMore: "Meer laden",
      reference: "Per {amount} {unit}",
      brand: "Merk",
      source: "Bron",
      canonicalFood: "Catalogus",
      customFood: "Eigen product",
      view: "Bekijken",
      customFoodsTitle: "Mijn voedingsmiddelen",
      customFoodsLoading: "Eigen voedingsmiddelen laden...",
      customFoodsError: "Eigen voedingsmiddelen konden niet worden geladen.",
      noCustomFoods: "Je hebt nog geen eigen voedingsmiddelen.",
      active: "Actief",
      archived: "Gearchiveerd",
      edit: "Bewerken",
      archive: "Archiveren",
      customLimit: "Free bevat maximaal 10 actieve eigen voedingsmiddelen.",
      customLimitReached: "Je hebt de Free-limiet van 10 actieve eigen voedingsmiddelen bereikt.",
      customDialogCreate: "Eigen voedingsmiddel maken",
      customDialogEdit: "Eigen voedingsmiddel bewerken",
      name: "Naam",
      optionalBrand: "Merk (optioneel)",
      referenceAmount: "Referentiehoeveelheid",
      referenceUnit: "Referentie-eenheid",
      unitServing: "Portie",
      unitPiece: "Stuk",
      conversionDetails: "Omrekening opgeven",
      conversionAmount: "Komt overeen met",
      conversionUnit: "Omrekenen naar",
      conversionRequired: "Voor een portie of stuk is een expliciete omzetting naar gram of milliliter nodig.",
      noDensityAssumption: "Gram en milliliter worden niet automatisch gelijkgesteld.",
      saveCustom: "Voedingsmiddel opslaan",
      customSaved: "Voedingsmiddel opgeslagen.",
      customArchived: "Voedingsmiddel gearchiveerd.",
      customValidation: "Controleer de productgegevens.",
      nameRequired: "Vul een naam in.",
      referenceInvalid: "De referentiehoeveelheid moet hoger dan 0 zijn.",
      nutrientsInvalid: "Voedingswaarden mogen niet negatief zijn.",
      staleFood: "Dit voedingsmiddel is intussen gewijzigd. Ververs de lijst en probeer opnieuw.",
      refreshList: "Lijst vernieuwen",
      archiveTitle: "Voedingsmiddel archiveren?",
      archiveBody: "Het product verdwijnt uit normale zoekresultaten. Bestaande historie blijft behouden.",
      confirmArchive: "Archiveren",
      details: "Details",
      updated: "Bijgewerkt",
      retrySameRequest: "Dezelfde veilige aanvraag kan opnieuw worden geprobeerd.",
      unexpectedError: "Er ging iets mis. Probeer opnieuw.",
      readOnlyArchived: "Gearchiveerde producten blijven alleen-lezen zichtbaar.",
      status: "Status"
    },
    en: {
      nutrition: "Nutrition",
      today: "Today",
      dayTarget: "Daily target",
      noTarget: "No daily target has been set.",
      targetLoading: "Loading daily target...",
      targetLoadFailed: "The daily target could not be loaded.",
      setTargets: "Set targets",
      editTargets: "Edit targets",
      foods: "Foods",
      foodsSummary: "Search the catalog or manage your own foods.",
      openFoods: "Open foods",
      noDailyEntry: "No nutrition entry for today yet.",
      energy: "Kcal",
      protein: "Protein",
      carbohydrate: "Carbohydrates",
      fat: "Fat",
      fiber: "Fiber",
      grams: "g",
      targetDialogTitle: "Set daily target",
      targetDialogIntro: "Enter your daily targets manually.",
      saveTarget: "Save targets",
      saving: "Saving...",
      saved: "Saved",
      close: "Close",
      cancel: "Cancel",
      retry: "Try again",
      required: "This field is required.",
      invalidTarget: "Check the target values.",
      positiveEnergy: "Kcal must be above 0 and no more than 20000.",
      macroRange: "Macro targets must be between 0 and 2000 grams.",
      authNotReady: "Your Nutrition profile is still loading.",
      onlineRequired: "Nutrition requires an active staging connection.",
      searchFoods: "Search foods",
      searchPlaceholder: "Search by name, brand, or barcode",
      search: "Search",
      searchTab: "Search",
      customTab: "My foods",
      results: "Results",
      searchLoading: "Loading foods...",
      searchError: "Search failed.",
      emptyCatalog: "No foods found.",
      emptyCatalogDetail: "Create your own food if the catalog has no suitable result yet.",
      createCustom: "Create custom food",
      loadMore: "Load more",
      reference: "Per {amount} {unit}",
      brand: "Brand",
      source: "Source",
      canonicalFood: "Catalog",
      customFood: "Custom food",
      view: "View",
      customFoodsTitle: "My foods",
      customFoodsLoading: "Loading custom foods...",
      customFoodsError: "Custom foods could not be loaded.",
      noCustomFoods: "You have no custom foods yet.",
      active: "Active",
      archived: "Archived",
      edit: "Edit",
      archive: "Archive",
      customLimit: "Free includes up to 10 active custom foods.",
      customLimitReached: "You have reached the Free limit of 10 active custom foods.",
      customDialogCreate: "Create custom food",
      customDialogEdit: "Edit custom food",
      name: "Name",
      optionalBrand: "Brand (optional)",
      referenceAmount: "Reference amount",
      referenceUnit: "Reference unit",
      unitServing: "Serving",
      unitPiece: "Piece",
      conversionDetails: "Add conversion",
      conversionAmount: "Equivalent amount",
      conversionUnit: "Convert to",
      conversionRequired: "A serving or piece needs an explicit conversion to grams or milliliters.",
      noDensityAssumption: "Grams and milliliters are never treated as equal automatically.",
      saveCustom: "Save food",
      customSaved: "Food saved.",
      customArchived: "Food archived.",
      customValidation: "Check the food details.",
      nameRequired: "Enter a name.",
      referenceInvalid: "The reference amount must be above 0.",
      nutrientsInvalid: "Nutrition values cannot be negative.",
      staleFood: "This food changed in the meantime. Refresh the list and try again.",
      refreshList: "Refresh list",
      archiveTitle: "Archive food?",
      archiveBody: "The food will leave normal search results. Existing history remains intact.",
      confirmArchive: "Archive",
      details: "Details",
      updated: "Updated",
      retrySameRequest: "The same safe request can be retried.",
      unexpectedError: "Something went wrong. Try again.",
      readOnlyArchived: "Archived foods remain visible as read-only items.",
      status: "Status"
    },
    de: {
      nutrition: "Ernaehrung",
      today: "Heute",
      dayTarget: "Tagesziel",
      noTarget: "Noch kein Tagesziel festgelegt.",
      targetLoading: "Tagesziel wird geladen...",
      targetLoadFailed: "Das Tagesziel konnte nicht geladen werden.",
      setTargets: "Ziele festlegen",
      editTargets: "Ziele anpassen",
      foods: "Lebensmittel",
      foodsSummary: "Durchsuche den Katalog oder verwalte eigene Lebensmittel.",
      openFoods: "Lebensmittel oeffnen",
      noDailyEntry: "Noch kein Ernaehrungseintrag fuer heute.",
      energy: "Kcal",
      protein: "Protein",
      carbohydrate: "Kohlenhydrate",
      fat: "Fett",
      fiber: "Ballaststoffe",
      grams: "g",
      targetDialogTitle: "Tagesziel festlegen",
      targetDialogIntro: "Trage deine Tagesziele manuell ein.",
      saveTarget: "Ziele speichern",
      saving: "Speichern...",
      saved: "Gespeichert",
      close: "Schliessen",
      cancel: "Abbrechen",
      retry: "Erneut versuchen",
      required: "Dieses Feld ist erforderlich.",
      invalidTarget: "Pruefe die Zielwerte.",
      positiveEnergy: "Kcal muss groesser als 0 und hoechstens 20000 sein.",
      macroRange: "Makroziele muessen zwischen 0 und 2000 Gramm liegen.",
      authNotReady: "Dein Ernaehrungsprofil wird noch geladen.",
      onlineRequired: "Ernaehrung benoetigt eine aktive Staging-Verbindung.",
      searchFoods: "Lebensmittel suchen",
      searchPlaceholder: "Nach Name, Marke oder Barcode suchen",
      search: "Suchen",
      searchTab: "Suchen",
      customTab: "Meine Lebensmittel",
      results: "Ergebnisse",
      searchLoading: "Lebensmittel werden geladen...",
      searchError: "Die Suche ist fehlgeschlagen.",
      emptyCatalog: "Keine Lebensmittel gefunden.",
      emptyCatalogDetail: "Erstelle ein eigenes Lebensmittel, wenn der Katalog noch kein passendes Ergebnis enthaelt.",
      createCustom: "Eigenes Lebensmittel erstellen",
      loadMore: "Mehr laden",
      reference: "Pro {amount} {unit}",
      brand: "Marke",
      source: "Quelle",
      canonicalFood: "Katalog",
      customFood: "Eigenes Lebensmittel",
      view: "Ansehen",
      customFoodsTitle: "Meine Lebensmittel",
      customFoodsLoading: "Eigene Lebensmittel werden geladen...",
      customFoodsError: "Eigene Lebensmittel konnten nicht geladen werden.",
      noCustomFoods: "Du hast noch keine eigenen Lebensmittel.",
      active: "Aktiv",
      archived: "Archiviert",
      edit: "Bearbeiten",
      archive: "Archivieren",
      customLimit: "Free enthaelt bis zu 10 aktive eigene Lebensmittel.",
      customLimitReached: "Du hast das Free-Limit von 10 aktiven eigenen Lebensmitteln erreicht.",
      customDialogCreate: "Eigenes Lebensmittel erstellen",
      customDialogEdit: "Eigenes Lebensmittel bearbeiten",
      name: "Name",
      optionalBrand: "Marke (optional)",
      referenceAmount: "Referenzmenge",
      referenceUnit: "Referenzeinheit",
      unitServing: "Portion",
      unitPiece: "Stueck",
      conversionDetails: "Umrechnung angeben",
      conversionAmount: "Entspricht",
      conversionUnit: "Umrechnen in",
      conversionRequired: "Eine Portion oder ein Stueck braucht eine ausdrueckliche Umrechnung in Gramm oder Milliliter.",
      noDensityAssumption: "Gramm und Milliliter werden nie automatisch gleichgesetzt.",
      saveCustom: "Lebensmittel speichern",
      customSaved: "Lebensmittel gespeichert.",
      customArchived: "Lebensmittel archiviert.",
      customValidation: "Pruefe die Lebensmitteldaten.",
      nameRequired: "Gib einen Namen ein.",
      referenceInvalid: "Die Referenzmenge muss groesser als 0 sein.",
      nutrientsInvalid: "Naehrwerte duerfen nicht negativ sein.",
      staleFood: "Dieses Lebensmittel wurde inzwischen geaendert. Aktualisiere die Liste und versuche es erneut.",
      refreshList: "Liste aktualisieren",
      archiveTitle: "Lebensmittel archivieren?",
      archiveBody: "Das Lebensmittel verschwindet aus normalen Suchergebnissen. Bestehender Verlauf bleibt erhalten.",
      confirmArchive: "Archivieren",
      details: "Details",
      updated: "Aktualisiert",
      retrySameRequest: "Dieselbe sichere Anfrage kann erneut versucht werden.",
      unexpectedError: "Etwas ist schiefgegangen. Versuche es erneut.",
      readOnlyArchived: "Archivierte Lebensmittel bleiben schreibgeschuetzt sichtbar.",
      status: "Status"
    }
  };

  const phase4State = {
    userId: "",
    notice: "",
    target: { status: "idle", value: null, error: "", requestToken: 0 },
    search: { status: "idle", query: "", items: [], afterName: null, afterId: null, hasMore: false, error: "", requestToken: 0 },
    customs: { status: "idle", items: [], offset: 0, hasMore: false, error: "", requestToken: 0 },
    portal: { type: "", tab: "search", food: null, opener: null, feedback: "", feedbackType: "" },
    targetDraft: { targetId: "", requestId: "", submittedFingerprint: "" },
    customDraft: { foodId: "", submittedFingerprint: "" }
  };

  const phase4LegacyRenderNutrition = renderNutrition;

  function phase4Language() {
    const language = state?.accountSettings?.language || "nl";
    return PHASE4_LANGUAGES.includes(language) ? language : "nl";
  }

  function phase4Text(key, replacements = {}) {
    let value = PHASE4_I18N[phase4Language()]?.[key] || PHASE4_I18N.nl[key] || key;
    Object.entries(replacements).forEach(([name, replacement]) => {
      value = value.split(`{${name}}`).join(String(replacement ?? ""));
    });
    return value;
  }

  function phase4FormatNumber(value, digits = 0) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return "-";
    const locale = { nl: "nl-NL", en: "en-US", de: "de-DE" }[phase4Language()] || "nl-NL";
    return parsed.toLocaleString(locale, { minimumFractionDigits: 0, maximumFractionDigits: digits });
  }

  function phase4Uuid() {
    if (!window.crypto?.randomUUID) throw new Error("Secure UUID support is unavailable.");
    return window.crypto.randomUUID();
  }

  function phase4NormalizedUserId() {
    if (!isLoggedIn() || state.ui.role !== "client" || !onlineReady || !onlineProfile?.id) return "";
    return String(onlineProfile.id);
  }

  function phase4ResetForUser(userId = "") {
    phase4State.userId = userId;
    phase4State.notice = "";
    phase4State.target = { status: "idle", value: null, error: "", requestToken: phase4State.target.requestToken + 1 };
    phase4State.search = { status: "idle", query: "", items: [], afterName: null, afterId: null, hasMore: false, error: "", requestToken: phase4State.search.requestToken + 1 };
    phase4State.customs = { status: "idle", items: [], offset: 0, hasMore: false, error: "", requestToken: phase4State.customs.requestToken + 1 };
    phase4State.targetDraft = { targetId: "", requestId: "", submittedFingerprint: "" };
    phase4State.customDraft = { foodId: "", submittedFingerprint: "" };
    phase4ClosePortal(false);
  }

  function phase4EnsureCurrentUser() {
    const userId = phase4NormalizedUserId();
    if (userId !== phase4State.userId) phase4ResetForUser(userId);
    return userId;
  }

  function phase4ErrorMessage(error, context = "") {
    const message = String(error?.message || error || "").toLowerCase();
    if (message.includes("maximum 10 active custom foods") || message.includes("free nutrition limit")) return phase4Text("customLimitReached");
    if (message.includes("changed; refresh") || message.includes("uuid already exists")) return phase4Text("staleFood");
    if (message.includes("authenticated user required")) return phase4Text("authNotReady");
    if (context === "target") return phase4Text("targetLoadFailed");
    if (context === "search") return phase4Text("searchError");
    if (context === "customs") return phase4Text("customFoodsError");
    return phase4Text("unexpectedError");
  }

  function phase4SetPortalFeedback(message = "", type = "") {
    phase4State.portal.feedback = message;
    phase4State.portal.feedbackType = type;
  }

  function phase4ShowPortalFeedback(message = "", type = "") {
    phase4SetPortalFeedback(message, type);
    const feedback = document.querySelector("#phase4NutritionPortal .phase4-feedback");
    if (!feedback) return;
    feedback.className = `phase4-feedback ${type === "error" ? "error" : type === "ok" ? "ok" : ""}`.trim();
    feedback.textContent = message;
  }

  function phase4FeedbackMarkup() {
    const message = phase4State.portal.feedback;
    if (!message) return '<p class="phase4-feedback" aria-live="polite"></p>';
    return `<p class="phase4-feedback ${phase4State.portal.feedbackType === "error" ? "error" : "ok"}" aria-live="polite">${escapeHTML(message)}</p>`;
  }

  function phase4UnitLabel(unit) {
    if (unit === "serving") return phase4Text("unitServing");
    if (unit === "piece") return phase4Text("unitPiece");
    return unit;
  }

  function phase4FoodReference(food) {
    return phase4Text("reference", {
      amount: phase4FormatNumber(food?.reference_amount, 3),
      unit: phase4UnitLabel(food?.reference_unit || "g")
    });
  }

  function phase4NutritionValues(food) {
    return [
      `${phase4FormatNumber(food?.energy_kcal, 1)} kcal`,
      `P ${phase4FormatNumber(food?.protein_grams, 1)}g`,
      `C ${phase4FormatNumber(food?.carbohydrate_grams, 1)}g`,
      `F ${phase4FormatNumber(food?.fat_grams, 1)}g`
    ].join(" | ");
  }

  function phase4InstallStyles() {
    if (document.getElementById("phase4-nutrition-slice2-styles")) return;
    const style = document.createElement("style");
    style.id = "phase4-nutrition-slice2-styles";
    style.textContent = `
      #nutrition.phase4-nutrition-active > :not(#phase4NutritionRoot) { display: none !important; }
      #phase4NutritionRoot { display: block; }
      .phase4-nutrition-shell { display: grid; gap: 18px; min-width: 0; }
      .phase4-page-head { display: grid; gap: 4px; }
      .phase4-page-head h1, .phase4-section-head h2, .phase4-dialog-head h2 { margin: 0; letter-spacing: 0; }
      .phase4-page-head h1 { font-size: 28px; line-height: 1.15; }
      .phase4-summary-band { display: grid; gap: 14px; padding: 16px 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
      .phase4-summary-title, .phase4-section-head, .phase4-dialog-head, .phase4-row, .phase4-card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
      .phase4-summary-title { align-items: flex-start; }
      .phase4-summary-title p, .phase4-section p, .phase4-food-card p, .phase4-dialog p { margin: 0; }
      .phase4-macro-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .phase4-macro { min-width: 0; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); display: grid; gap: 2px; }
      .phase4-macro span { color: var(--muted); font-size: 12px; font-weight: 800; }
      .phase4-macro strong { font-size: 20px; overflow-wrap: anywhere; }
      .phase4-section { display: grid; gap: 12px; padding: 4px 0 18px; border-bottom: 1px solid var(--line); }
      .phase4-section-head { align-items: flex-start; }
      .phase4-section-actions, .phase4-dialog-actions, .phase4-card-actions, .phase4-pagination { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
      .phase4-gold-action { min-height: 44px; background: #c89312; border-color: #c89312; color: #111; font-weight: 800; }
      .phase4-gold-action:hover { background: #d8a72a; border-color: #d8a72a; }
      .phase4-section button, .phase4-portal button, .phase4-portal input, .phase4-portal select { min-height: 44px; }
      .phase4-inline-state { min-height: 56px; display: grid; align-content: center; gap: 8px; color: var(--muted); }
      .phase4-inline-state.error { color: var(--text); }
      .phase4-portal { position: fixed; inset: 0; z-index: 78; display: grid; align-items: end; }
      .phase4-backdrop { position: absolute; inset: 0; border: 0; background: rgba(7, 11, 18, .72); cursor: pointer; }
      .phase4-sheet { position: relative; z-index: 1; width: 100%; max-height: 94dvh; overflow: auto; overscroll-behavior: contain; background: var(--bg); color: var(--text); border: 1px solid var(--line); border-radius: 8px 8px 0 0; padding: 16px 16px calc(22px + env(safe-area-inset-bottom)); box-shadow: var(--shadow); display: grid; gap: 16px; }
      body.phase4-nutrition-dialog-open { overflow: hidden; }
      .phase4-dialog-head { align-items: flex-start; position: sticky; top: -16px; z-index: 2; margin: -16px -16px 0; padding: 16px; background: var(--bg); border-bottom: 1px solid var(--line); }
      .phase4-dialog-head > div { min-width: 0; }
      .phase4-close { flex: none; min-width: 44px; padding-inline: 12px; }
      .phase4-form { display: grid; gap: 14px; }
      .phase4-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .phase4-form-grid .wide { grid-column: 1 / -1; }
      .phase4-form .field { min-width: 0; }
      .phase4-form input, .phase4-form select { width: 100%; }
      .phase4-segmented { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px; padding: 4px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-2); }
      .phase4-segmented button { border: 0; background: transparent; color: var(--text); border-radius: 6px; }
      .phase4-segmented button.active { background: var(--surface); box-shadow: var(--shadow); font-weight: 800; }
      .phase4-search-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; }
      .phase4-food-list { display: grid; gap: 10px; }
      .phase4-food-card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; display: grid; gap: 8px; min-width: 0; }
      .phase4-food-card.archived { opacity: .72; }
      .phase4-food-title { min-width: 0; display: grid; gap: 2px; }
      .phase4-food-title strong, .phase4-food-title small { overflow-wrap: anywhere; }
      .phase4-food-title small, .phase4-food-meta { color: var(--muted); }
      .phase4-food-meta { font-size: 13px; }
      .phase4-status { display: inline-flex; align-items: center; min-height: 28px; width: fit-content; padding: 3px 8px; border: 1px solid var(--line); border-radius: 999px; font-size: 12px; font-weight: 800; }
      .phase4-status.active { border-color: #2d8a67; color: #8bd8b8; }
      .phase4-feedback { min-height: 22px; color: var(--muted); }
      .phase4-feedback.error { color: #ffb0b0; }
      .phase4-feedback.ok { color: #8bd8b8; }
      .phase4-empty { display: grid; gap: 10px; padding: 22px 0; text-align: center; justify-items: center; }
      .phase4-conversion { border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
      .phase4-conversion[data-required="false"] { display: none; }
      .phase4-conversion summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; font-weight: 800; }
      .phase4-detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .phase4-detail-grid > div { display: grid; gap: 2px; min-width: 0; }
      .phase4-detail-grid span { color: var(--muted); font-size: 12px; font-weight: 800; }
      .phase4-detail-grid strong { overflow-wrap: anywhere; }
      @media (min-width: 720px) {
        .phase4-nutrition-shell { max-width: 920px; }
        .phase4-macro-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .phase4-portal { align-items: center; justify-items: center; padding: 24px; }
        .phase4-sheet { width: min(760px, calc(100vw - 48px)); max-height: 88dvh; border-radius: 8px; }
      }
      @media (max-width: 359px) {
        .phase4-form-grid, .phase4-detail-grid { grid-template-columns: 1fr; }
        .phase4-form-grid .wide { grid-column: auto; }
        .phase4-search-form { grid-template-columns: 1fr; }
        .phase4-summary-title, .phase4-section-head, .phase4-card-head { align-items: stretch; flex-direction: column; }
      }
    `;
    document.head.appendChild(style);
  }

  function phase4EnsureRoot() {
    const view = document.getElementById("nutrition");
    if (!view) return null;
    let root = document.getElementById("phase4NutritionRoot");
    if (!root) {
      root = document.createElement("div");
      root.id = "phase4NutritionRoot";
      view.appendChild(root);
    }
    return root;
  }

  function phase4TargetMetrics(target) {
    const metrics = [
      [phase4Text("energy"), target ? phase4FormatNumber(target.energy_kcal, 0) : "-", "kcal"],
      [phase4Text("protein"), target ? phase4FormatNumber(target.protein_grams, 1) : "-", phase4Text("grams")],
      [phase4Text("carbohydrate"), target ? phase4FormatNumber(target.carbohydrate_grams, 1) : "-", phase4Text("grams")],
      [phase4Text("fat"), target ? phase4FormatNumber(target.fat_grams, 1) : "-", phase4Text("grams")]
    ];
    return metrics.map(([label, value, unit]) => `
      <div class="phase4-macro">
        <span>${escapeHTML(label)}</span>
        <strong>${escapeHTML(`${value}${value === "-" ? "" : ` ${unit}`}`)}</strong>
      </div>
    `).join("");
  }

  function phase4TargetStateMarkup() {
    if (phase4State.target.status === "loading" || phase4State.target.status === "idle") {
      return `<div class="phase4-inline-state" aria-live="polite">${escapeHTML(phase4Text("targetLoading"))}</div>`;
    }
    if (phase4State.target.status === "error") {
      return `
        <div class="phase4-inline-state error" aria-live="polite">
          <span>${escapeHTML(phase4State.target.error || phase4Text("targetLoadFailed"))}</span>
          <button class="secondary-btn" data-phase4-retry-target type="button">${escapeHTML(phase4Text("retry"))}</button>
        </div>
      `;
    }
    const target = phase4State.target.value;
    return `
      <div class="phase4-macro-grid">${phase4TargetMetrics(target)}</div>
      ${target ? "" : `<p class="muted">${escapeHTML(phase4Text("noTarget"))}</p>`}
    `;
  }

  function phase4RenderOverview() {
    const root = phase4EnsureRoot();
    if (!root) return;
    phase4InstallStyles();
    const userId = phase4EnsureCurrentUser();
    const isOnline = isOnlineMode();
    const canHydrate = Boolean(userId);
    root.innerHTML = `
      <div class="phase4-nutrition-shell">
        <header class="phase4-page-head">
          <p class="eyebrow">${escapeHTML(phase4Text("nutrition"))}</p>
          <h1>${escapeHTML(phase4Text("nutrition"))}</h1>
        </header>
        ${!isOnline ? `
          <div class="phase4-inline-state error" aria-live="polite">${escapeHTML(phase4Text("onlineRequired"))}</div>
        ` : !canHydrate ? `
          <div class="phase4-inline-state" aria-live="polite">${escapeHTML(phase4Text("authNotReady"))}</div>
        ` : `
          <section class="phase4-summary-band" aria-labelledby="phase4-today-title">
            <div class="phase4-summary-title">
              <div>
                <p class="eyebrow">${escapeHTML(phase4Text("today"))}</p>
                <h2 id="phase4-today-title">${escapeHTML(phase4Text("dayTarget"))}</h2>
              </div>
              <span class="muted">${escapeHTML(phase4Text("noDailyEntry"))}</span>
            </div>
            ${phase4TargetStateMarkup()}
            ${phase4State.notice ? `<p class="phase4-feedback ok" aria-live="polite">${escapeHTML(phase4State.notice)}</p>` : ""}
          </section>
          <section class="phase4-section" aria-labelledby="phase4-target-section-title">
            <div class="phase4-section-head">
              <div>
                <p class="eyebrow">${escapeHTML(phase4Text("nutrition"))}</p>
                <h2 id="phase4-target-section-title">${escapeHTML(phase4Text("dayTarget"))}</h2>
              </div>
              <button class="phase4-gold-action" data-phase4-open-target type="button" aria-haspopup="dialog" aria-controls="phase4NutritionPortal">
                ${escapeHTML(phase4Text(phase4State.target.value ? "editTargets" : "setTargets"))}
              </button>
            </div>
          </section>
          <section class="phase4-section" aria-labelledby="phase4-foods-section-title">
            <div class="phase4-section-head">
              <div>
                <p class="eyebrow">${escapeHTML(phase4Text("nutrition"))}</p>
                <h2 id="phase4-foods-section-title">${escapeHTML(phase4Text("foods"))}</h2>
              </div>
            </div>
            <p class="muted">${escapeHTML(phase4Text("foodsSummary"))}</p>
            <div class="phase4-section-actions">
              <button class="phase4-gold-action" data-phase4-open-foods type="button" aria-haspopup="dialog" aria-controls="phase4NutritionPortal">${escapeHTML(phase4Text("openFoods"))}</button>
            </div>
          </section>
        `}
      </div>
    `;
    if (canHydrate && phase4State.target.status === "idle") phase4LoadTarget();
  }

  async function phase4LoadTarget(force = false) {
    const userId = phase4EnsureCurrentUser();
    if (!userId || !supabaseClient) return;
    if (!force && ["loading", "ready"].includes(phase4State.target.status)) return;
    const requestToken = phase4State.target.requestToken + 1;
    phase4State.target.requestToken = requestToken;
    phase4State.target.status = "loading";
    phase4State.target.error = "";
    phase4RenderOverview();
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_get_current_nutrition_target");
      if (error) throw error;
      if (phase4State.userId !== userId || phase4State.target.requestToken !== requestToken) return;
      phase4State.target.value = data || null;
      phase4State.target.status = "ready";
    } catch (error) {
      if (phase4State.userId !== userId || phase4State.target.requestToken !== requestToken) return;
      phase4State.target.status = "error";
      phase4State.target.error = phase4ErrorMessage(error, "target");
    }
    phase4RenderOverview();
  }

  function phase4OpenPortal(type, opener = document.activeElement, options = {}) {
    const previousPortal = phase4State.portal;
    phase4ClosePortal(false);
    phase4State.portal = {
      type,
      tab: options.tab || previousPortal.tab || "search",
      food: options.food || null,
      opener: opener || previousPortal.opener,
      feedback: options.feedback || "",
      feedbackType: options.feedbackType || ""
    };
    document.body.classList.add("phase4-nutrition-dialog-open");
    phase4RenderPortal();
  }

  function phase4ClosePortal(restoreFocus = true) {
    const opener = phase4State.portal?.opener;
    document.getElementById("phase4NutritionPortal")?.remove();
    document.body.classList.remove("phase4-nutrition-dialog-open");
    phase4State.portal = { type: "", tab: "search", food: null, opener: null, feedback: "", feedbackType: "" };
    if (restoreFocus) opener?.focus?.();
  }

  function phase4DialogFrame(title, body, options = {}) {
    return `
      <button class="phase4-backdrop" data-phase4-close type="button" aria-label="${escapeHTML(phase4Text("close"))}"></button>
      <section class="phase4-sheet" role="dialog" aria-modal="true" aria-labelledby="phase4-dialog-title">
        <div class="phase4-dialog-head">
          <div>
            <p class="eyebrow">${escapeHTML(options.eyebrow || phase4Text("nutrition"))}</p>
            <h2 id="phase4-dialog-title">${escapeHTML(title)}</h2>
          </div>
          <button class="secondary-btn phase4-close" data-phase4-close type="button">${escapeHTML(phase4Text("close"))}</button>
        </div>
        ${body}
      </section>
    `;
  }

  function phase4RenderPortal() {
    if (!phase4State.portal.type) return;
    let portal = document.getElementById("phase4NutritionPortal");
    const isNew = !portal;
    if (!portal) {
      portal = document.createElement("div");
      portal.id = "phase4NutritionPortal";
      portal.className = "phase4-portal";
      document.body.appendChild(portal);
    }
    if (phase4State.portal.type === "target") portal.innerHTML = phase4TargetDialog();
    if (phase4State.portal.type === "foods") portal.innerHTML = phase4FoodsDialog();
    if (phase4State.portal.type === "custom") portal.innerHTML = phase4CustomFoodDialog();
    if (phase4State.portal.type === "food-detail") portal.innerHTML = phase4FoodDetailDialog();
    if (phase4State.portal.type === "archive") portal.innerHTML = phase4ArchiveDialog();
    if (isNew) window.requestAnimationFrame(() => portal.querySelector("input, button, select")?.focus?.());
  }

  function phase4TargetDialog() {
    const target = phase4State.target.value || {};
    if (!phase4State.targetDraft.targetId) phase4State.targetDraft.targetId = phase4Uuid();
    if (!phase4State.targetDraft.requestId) phase4State.targetDraft.requestId = phase4Uuid();
    const body = `
      <form id="phase4TargetForm" class="phase4-form" novalidate>
        <p class="muted">${escapeHTML(phase4Text("targetDialogIntro"))}</p>
        <div class="phase4-form-grid">
          <label class="field">
            <span>${escapeHTML(phase4Text("energy"))}</span>
            <input name="energy" type="number" inputmode="decimal" min="0.01" max="20000" step="1" required value="${escapeHTML(target.energy_kcal ?? "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("protein"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="protein" type="number" inputmode="decimal" min="0" max="2000" step="0.1" required value="${escapeHTML(target.protein_grams ?? "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("carbohydrate"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="carbohydrate" type="number" inputmode="decimal" min="0" max="2000" step="0.1" required value="${escapeHTML(target.carbohydrate_grams ?? "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("fat"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="fat" type="number" inputmode="decimal" min="0" max="2000" step="0.1" required value="${escapeHTML(target.fat_grams ?? "")}" autocomplete="off" />
          </label>
        </div>
        ${phase4FeedbackMarkup()}
        <div class="phase4-dialog-actions">
          <button class="phase4-gold-action" type="submit">${escapeHTML(phase4Text("saveTarget"))}</button>
          <button class="secondary-btn" data-phase4-close type="button">${escapeHTML(phase4Text("cancel"))}</button>
        </div>
      </form>
    `;
    return phase4DialogFrame(phase4Text("targetDialogTitle"), body);
  }

  function phase4TargetPayload(form) {
    const data = new FormData(form);
    return {
      energy: Number(data.get("energy")),
      protein: Number(data.get("protein")),
      carbohydrate: Number(data.get("carbohydrate")),
      fat: Number(data.get("fat"))
    };
  }

  function phase4ValidateTarget(payload) {
    const errors = [];
    if (!Number.isFinite(payload.energy) || payload.energy <= 0 || payload.energy > 20000) errors.push(phase4Text("positiveEnergy"));
    if ([payload.protein, payload.carbohydrate, payload.fat].some((value) => !Number.isFinite(value) || value < 0 || value > 2000)) errors.push(phase4Text("macroRange"));
    return errors;
  }

  function phase4TargetFingerprint(payload) {
    return JSON.stringify([payload.energy, payload.protein, payload.carbohydrate, payload.fat, todayISO()]);
  }

  async function phase4SaveTarget(form) {
    const userId = phase4EnsureCurrentUser();
    if (!userId || !supabaseClient) {
      phase4ShowPortalFeedback(phase4Text("authNotReady"), "error");
      return;
    }
    const payload = phase4TargetPayload(form);
    const errors = phase4ValidateTarget(payload);
    if (errors.length) {
      phase4ShowPortalFeedback(errors.join(" "), "error");
      return;
    }
    const fingerprint = phase4TargetFingerprint(payload);
    if (phase4State.targetDraft.submittedFingerprint && phase4State.targetDraft.submittedFingerprint !== fingerprint) {
      phase4State.targetDraft.targetId = phase4Uuid();
      phase4State.targetDraft.requestId = phase4Uuid();
    }
    phase4State.targetDraft.submittedFingerprint = fingerprint;
    phase4ShowPortalFeedback(phase4Text("saving"));
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_save_member_target", {
        p_target_id: phase4State.targetDraft.targetId,
        p_request_id: phase4State.targetDraft.requestId,
        p_energy_kcal: payload.energy,
        p_protein_grams: payload.protein,
        p_carbohydrate_grams: payload.carbohydrate,
        p_fat_grams: payload.fat,
        p_fiber_grams: null,
        p_effective_from: todayISO()
      });
      if (error) throw error;
      if (phase4State.userId !== userId) return;
      phase4State.target = { status: "ready", value: data || null, error: "", requestToken: phase4State.target.requestToken + 1 };
      phase4State.targetDraft = { targetId: "", requestId: "", submittedFingerprint: "" };
      phase4State.notice = phase4Text("saved");
      phase4ClosePortal();
      phase4RenderOverview();
    } catch (error) {
      phase4ShowPortalFeedback(phase4ErrorMessage(error), "error");
    }
  }

  function phase4SearchForm() {
    return `
      <form id="phase4FoodSearchForm" class="phase4-search-form" role="search">
        <label class="field">
          <span class="sr-only">${escapeHTML(phase4Text("searchFoods"))}</span>
          <input name="query" type="search" value="${escapeHTML(phase4State.search.query)}" placeholder="${escapeHTML(phase4Text("searchPlaceholder"))}" autocomplete="off" />
        </label>
        <button class="phase4-gold-action" type="submit">${escapeHTML(phase4Text("search"))}</button>
      </form>
    `;
  }

  function phase4FoodCard(food, options = {}) {
    const isArchived = food.status === "archived";
    const isCustom = food.catalog_scope === "custom";
    const actionMarkup = options.management
      ? isArchived
        ? `<button class="secondary-btn" data-phase4-view-food="${escapeHTML(food.id)}" type="button">${escapeHTML(phase4Text("view"))}</button>`
        : `
            <button class="secondary-btn" data-phase4-edit-custom="${escapeHTML(food.id)}" type="button">${escapeHTML(phase4Text("edit"))}</button>
            <button class="secondary-btn" data-phase4-archive-custom="${escapeHTML(food.id)}" type="button">${escapeHTML(phase4Text("archive"))}</button>
          `
      : `<button class="secondary-btn" data-phase4-view-food="${escapeHTML(food.id)}" type="button">${escapeHTML(phase4Text("view"))}</button>`;
    return `
      <article class="phase4-food-card ${isArchived ? "archived" : ""}">
        <div class="phase4-card-head">
          <div class="phase4-food-title">
            <strong>${escapeHTML(food.name || "-")}</strong>
            ${food.brand ? `<small>${escapeHTML(food.brand)}</small>` : ""}
          </div>
          ${options.management ? `<span class="phase4-status ${isArchived ? "" : "active"}">${escapeHTML(phase4Text(isArchived ? "archived" : "active"))}</span>` : ""}
        </div>
        <p class="phase4-food-meta">${escapeHTML(phase4FoodReference(food))}</p>
        <p class="phase4-food-meta">${escapeHTML(phase4NutritionValues(food))}</p>
        <div class="phase4-card-actions">${actionMarkup}</div>
        ${isCustom && !options.management ? `<span class="muted">${escapeHTML(phase4Text("customFood"))}</span>` : ""}
      </article>
    `;
  }

  function phase4SearchResults() {
    const search = phase4State.search;
    if (search.status === "loading" && !search.items.length) {
      return `<div class="phase4-inline-state" aria-live="polite">${escapeHTML(phase4Text("searchLoading"))}</div>`;
    }
    if (search.status === "error" && !search.items.length) {
      return `
        <div class="phase4-inline-state error" aria-live="polite">
          <span>${escapeHTML(search.error || phase4Text("searchError"))}</span>
          <button class="secondary-btn" data-phase4-retry-search type="button">${escapeHTML(phase4Text("retry"))}</button>
        </div>
      `;
    }
    if (search.status === "ready" && !search.items.length) {
      return `
        <div class="phase4-empty" aria-live="polite">
          <strong>${escapeHTML(phase4Text("emptyCatalog"))}</strong>
          <p class="muted">${escapeHTML(phase4Text("emptyCatalogDetail"))}</p>
          <button class="phase4-gold-action" data-phase4-new-custom type="button">${escapeHTML(phase4Text("createCustom"))}</button>
        </div>
      `;
    }
    return `
      <div class="phase4-food-list" aria-live="polite">
        ${search.items.map((food) => phase4FoodCard(food)).join("")}
      </div>
      ${search.status === "error" ? `<p class="phase4-feedback error" aria-live="polite">${escapeHTML(search.error)}</p>` : ""}
      ${search.hasMore || search.status === "loading" ? `
        <div class="phase4-pagination">
          <button class="secondary-btn" data-phase4-load-more-search type="button" ${search.status === "loading" ? "disabled" : ""}>${escapeHTML(search.status === "loading" ? phase4Text("searchLoading") : phase4Text("loadMore"))}</button>
        </div>
      ` : ""}
    `;
  }

  function phase4CustomResults() {
    const custom = phase4State.customs;
    if (custom.status === "loading" && !custom.items.length) {
      return `<div class="phase4-inline-state" aria-live="polite">${escapeHTML(phase4Text("customFoodsLoading"))}</div>`;
    }
    if (custom.status === "error" && !custom.items.length) {
      return `
        <div class="phase4-inline-state error" aria-live="polite">
          <span>${escapeHTML(custom.error || phase4Text("customFoodsError"))}</span>
          <button class="secondary-btn" data-phase4-retry-customs type="button">${escapeHTML(phase4Text("retry"))}</button>
        </div>
      `;
    }
    if (custom.status === "ready" && !custom.items.length) {
      return `
        <div class="phase4-empty" aria-live="polite">
          <strong>${escapeHTML(phase4Text("noCustomFoods"))}</strong>
        </div>
      `;
    }
    return `
      <div class="phase4-food-list" aria-live="polite">
        ${custom.items.map((food) => phase4FoodCard(food, { management: true })).join("")}
      </div>
      ${custom.status === "error" ? `<p class="phase4-feedback error" aria-live="polite">${escapeHTML(custom.error)}</p>` : ""}
      ${custom.hasMore || custom.status === "loading" ? `
        <div class="phase4-pagination">
          <button class="secondary-btn" data-phase4-load-more-customs type="button" ${custom.status === "loading" ? "disabled" : ""}>${escapeHTML(custom.status === "loading" ? phase4Text("customFoodsLoading") : phase4Text("loadMore"))}</button>
        </div>
      ` : ""}
    `;
  }

  function phase4FoodsDialog() {
    const isSearch = phase4State.portal.tab !== "custom";
    const body = `
      <div class="phase4-segmented" role="tablist" aria-label="${escapeHTML(phase4Text("foods"))}">
        <button class="${isSearch ? "active" : ""}" data-phase4-food-tab="search" role="tab" aria-selected="${isSearch}" type="button">${escapeHTML(phase4Text("searchTab"))}</button>
        <button class="${!isSearch ? "active" : ""}" data-phase4-food-tab="custom" role="tab" aria-selected="${!isSearch}" type="button">${escapeHTML(phase4Text("customTab"))}</button>
      </div>
      ${phase4FeedbackMarkup()}
      ${isSearch ? `
        ${phase4SearchForm()}
        <div>
          <p class="eyebrow">${escapeHTML(phase4Text("results"))}</p>
          ${phase4SearchResults()}
        </div>
      ` : `
        <div class="phase4-row">
          <p class="muted">${escapeHTML(phase4Text("customLimit"))}</p>
          <button class="phase4-gold-action" data-phase4-new-custom type="button">${escapeHTML(phase4Text("createCustom"))}</button>
        </div>
        ${phase4CustomResults()}
      `}
    `;
    return phase4DialogFrame(isSearch ? phase4Text("searchFoods") : phase4Text("customFoodsTitle"), body, { eyebrow: phase4Text("foods") });
  }

  function phase4MergeUniqueFoods(existing, incoming) {
    const byId = new Map(existing.map((food) => [food.id, food]));
    incoming.forEach((food) => byId.set(food.id, food));
    return Array.from(byId.values());
  }

  async function phase4SearchFoods({ reset = true } = {}) {
    const userId = phase4EnsureCurrentUser();
    if (!userId || !supabaseClient) return;
    const search = phase4State.search;
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
    phase4RenderPortal();
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_search_foods", {
        p_query: search.query || null,
        p_page_size: PHASE4_SEARCH_PAGE_SIZE,
        p_after_name: reset ? null : search.afterName,
        p_after_id: reset ? null : search.afterId
      });
      if (error) throw error;
      if (phase4State.userId !== userId || search.requestToken !== requestToken) return;
      const rows = Array.isArray(data) ? data : [];
      search.items = reset ? rows : phase4MergeUniqueFoods(search.items, rows);
      const last = rows[rows.length - 1];
      search.afterName = last?.name || null;
      search.afterId = last?.id || null;
      search.hasMore = rows.length === PHASE4_SEARCH_PAGE_SIZE;
      search.status = "ready";
    } catch (error) {
      if (phase4State.userId !== userId || search.requestToken !== requestToken) return;
      search.status = "error";
      search.error = phase4ErrorMessage(error, "search");
    }
    phase4RenderPortal();
  }

  async function phase4LoadCustomFoods({ reset = true } = {}) {
    const userId = phase4EnsureCurrentUser();
    if (!userId || !supabaseClient) return;
    const custom = phase4State.customs;
    const requestToken = custom.requestToken + 1;
    custom.requestToken = requestToken;
    custom.status = "loading";
    custom.error = "";
    if (reset) {
      custom.items = [];
      custom.offset = 0;
      custom.hasMore = false;
    }
    phase4RenderPortal();
    const start = reset ? 0 : custom.offset;
    const end = start + PHASE4_CUSTOM_PAGE_SIZE - 1;
    try {
      const { data, error } = await supabaseClient
        .from("foods")
        .select("id,catalog_scope,name,brand,reference_amount,reference_unit,reference_mass_grams,reference_volume_ml,density_g_per_ml,energy_kcal,protein_grams,carbohydrate_grams,fat_grams,fiber_grams,status,source_provider,updated_at,archived_at")
        .eq("catalog_scope", "custom")
        .order("updated_at", { ascending: false })
        .range(start, end);
      if (error) throw error;
      if (phase4State.userId !== userId || custom.requestToken !== requestToken) return;
      const rows = Array.isArray(data) ? data : [];
      custom.items = reset ? rows : phase4MergeUniqueFoods(custom.items, rows);
      custom.offset = start + rows.length;
      custom.hasMore = rows.length === PHASE4_CUSTOM_PAGE_SIZE;
      custom.status = "ready";
    } catch (error) {
      if (phase4State.userId !== userId || custom.requestToken !== requestToken) return;
      custom.status = "error";
      custom.error = phase4ErrorMessage(error, "customs");
    }
    phase4RenderPortal();
  }

  function phase4FindFood(id) {
    return phase4State.customs.items.find((food) => food.id === id)
      || phase4State.search.items.find((food) => food.id === id)
      || null;
  }

  function phase4FoodDetailDialog() {
    const food = phase4State.portal.food || {};
    const source = food.catalog_scope === "custom" ? phase4Text("customFood") : (food.source_provider || phase4Text("canonicalFood"));
    const body = `
      <div class="phase4-detail-grid">
        <div class="wide"><span>${escapeHTML(phase4Text("name"))}</span><strong>${escapeHTML(food.name || "-")}</strong></div>
        ${food.brand ? `<div class="wide"><span>${escapeHTML(phase4Text("brand"))}</span><strong>${escapeHTML(food.brand)}</strong></div>` : ""}
        <div><span>${escapeHTML(phase4Text("referenceAmount"))}</span><strong>${escapeHTML(phase4FoodReference(food))}</strong></div>
        <div><span>${escapeHTML(phase4Text("source"))}</span><strong>${escapeHTML(source)}</strong></div>
        <div><span>${escapeHTML(phase4Text("energy"))}</span><strong>${escapeHTML(`${phase4FormatNumber(food.energy_kcal, 1)} kcal`)}</strong></div>
        <div><span>${escapeHTML(phase4Text("protein"))}</span><strong>${escapeHTML(`${phase4FormatNumber(food.protein_grams, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(phase4Text("carbohydrate"))}</span><strong>${escapeHTML(`${phase4FormatNumber(food.carbohydrate_grams, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(phase4Text("fat"))}</span><strong>${escapeHTML(`${phase4FormatNumber(food.fat_grams, 1)} g`)}</strong></div>
        ${food.fiber_grams === null || food.fiber_grams === undefined ? "" : `<div><span>${escapeHTML(phase4Text("fiber"))}</span><strong>${escapeHTML(`${phase4FormatNumber(food.fiber_grams, 1)} g`)}</strong></div>`}
        <div><span>${escapeHTML(phase4Text("status"))}</span><strong>${escapeHTML(phase4Text(food.status === "archived" ? "archived" : "active"))}</strong></div>
      </div>
      ${food.status === "archived" ? `<p class="muted">${escapeHTML(phase4Text("readOnlyArchived"))}</p>` : ""}
      <div class="phase4-dialog-actions">
        <button class="secondary-btn" data-phase4-back-foods type="button">${escapeHTML(phase4Text("close"))}</button>
      </div>
    `;
    return phase4DialogFrame(food.name || phase4Text("details"), body, { eyebrow: phase4Text("details") });
  }

  function phase4CustomFoodDialog() {
    const food = phase4State.portal.food;
    const editing = Boolean(food?.id);
    if (!phase4State.customDraft.foodId) phase4State.customDraft.foodId = food?.id || phase4Uuid();
    const unit = food?.reference_unit || "g";
    const conversionRequired = ["serving", "piece"].includes(unit);
    const conversionUnit = food?.reference_mass_grams ? "g" : "ml";
    const conversionAmount = food?.reference_mass_grams || food?.reference_volume_ml || "";
    const unitOptions = PHASE4_UNITS.map((value) => `<option value="${value}" ${unit === value ? "selected" : ""}>${escapeHTML(phase4UnitLabel(value))}</option>`).join("");
    const body = `
      <form id="phase4CustomFoodForm" class="phase4-form" novalidate data-phase4-editing="${editing}">
        <div class="phase4-form-grid">
          <label class="field wide">
            <span>${escapeHTML(phase4Text("name"))}</span>
            <input name="name" maxlength="240" required value="${escapeHTML(food?.name || "")}" autocomplete="off" />
          </label>
          <label class="field wide">
            <span>${escapeHTML(phase4Text("optionalBrand"))}</span>
            <input name="brand" maxlength="160" value="${escapeHTML(food?.brand || "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("referenceAmount"))}</span>
            <input name="referenceAmount" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" required value="${escapeHTML(food?.reference_amount ?? (unit === "g" || unit === "ml" ? 100 : 1))}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("referenceUnit"))}</span>
            <select name="referenceUnit">${unitOptions}</select>
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("energy"))}</span>
            <input name="energy" type="number" inputmode="decimal" min="0" max="1000000" step="0.1" required value="${escapeHTML(food?.energy_kcal ?? "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("protein"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="protein" type="number" inputmode="decimal" min="0" max="100000" step="0.1" required value="${escapeHTML(food?.protein_grams ?? "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("carbohydrate"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="carbohydrate" type="number" inputmode="decimal" min="0" max="100000" step="0.1" required value="${escapeHTML(food?.carbohydrate_grams ?? "")}" autocomplete="off" />
          </label>
          <label class="field">
            <span>${escapeHTML(phase4Text("fat"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="fat" type="number" inputmode="decimal" min="0" max="100000" step="0.1" required value="${escapeHTML(food?.fat_grams ?? "")}" autocomplete="off" />
          </label>
          <label class="field wide">
            <span>${escapeHTML(phase4Text("fiber"))} (${escapeHTML(phase4Text("grams"))})</span>
            <input name="fiber" type="number" inputmode="decimal" min="0" max="100000" step="0.1" value="${escapeHTML(food?.fiber_grams ?? "")}" autocomplete="off" />
          </label>
        </div>
        <details class="phase4-conversion" data-phase4-conversion data-required="${conversionRequired}" ${conversionRequired ? "open" : ""}>
          <summary>${escapeHTML(phase4Text("conversionDetails"))}</summary>
          <div class="phase4-form-grid">
            <label class="field">
              <span>${escapeHTML(phase4Text("conversionAmount"))}</span>
              <input name="conversionAmount" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" value="${escapeHTML(conversionAmount)}" autocomplete="off" />
            </label>
            <label class="field">
              <span>${escapeHTML(phase4Text("conversionUnit"))}</span>
              <select name="conversionUnit">
                <option value="g" ${conversionUnit === "g" ? "selected" : ""}>g</option>
                <option value="ml" ${conversionUnit === "ml" ? "selected" : ""}>ml</option>
              </select>
            </label>
            <p class="muted wide">${escapeHTML(phase4Text("noDensityAssumption"))}</p>
          </div>
        </details>
        ${phase4FeedbackMarkup()}
        <div class="phase4-dialog-actions">
          <button class="phase4-gold-action" type="submit">${escapeHTML(phase4Text("saveCustom"))}</button>
          <button class="secondary-btn" data-phase4-back-foods type="button">${escapeHTML(phase4Text("cancel"))}</button>
        </div>
      </form>
    `;
    return phase4DialogFrame(phase4Text(editing ? "customDialogEdit" : "customDialogCreate"), body, { eyebrow: phase4Text("customFood") });
  }

  function phase4CustomPayload(form) {
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
      referenceMassGrams: (unit === "g" || (needsConversion && conversionUnit === "g")) ? explicitAmount : null,
      referenceVolumeMl: (unit === "ml" || (needsConversion && conversionUnit === "ml")) ? explicitAmount : null,
      density: null,
      energy: Number(data.get("energy")),
      protein: Number(data.get("protein")),
      carbohydrate: Number(data.get("carbohydrate")),
      fat: Number(data.get("fat")),
      fiber: data.get("fiber") === "" ? null : Number(data.get("fiber")),
      needsConversion,
      conversionAmount
    };
  }

  function phase4ValidateCustom(payload) {
    const errors = [];
    if (!payload.name || payload.name.length > 240) errors.push(phase4Text("nameRequired"));
    if (payload.brand.length > 160) errors.push(phase4Text("customValidation"));
    if (!PHASE4_UNITS.includes(payload.referenceUnit) || !Number.isFinite(payload.referenceAmount) || payload.referenceAmount <= 0 || payload.referenceAmount > 100000) errors.push(phase4Text("referenceInvalid"));
    if (payload.needsConversion && (!Number.isFinite(payload.conversionAmount) || payload.conversionAmount <= 0 || payload.conversionAmount > 100000)) errors.push(phase4Text("conversionRequired"));
    const nutrients = [payload.energy, payload.protein, payload.carbohydrate, payload.fat];
    if (nutrients.some((value) => !Number.isFinite(value) || value < 0) || payload.energy > 1000000 || [payload.protein, payload.carbohydrate, payload.fat].some((value) => value > 100000) || (payload.fiber !== null && (!Number.isFinite(payload.fiber) || payload.fiber < 0 || payload.fiber > 100000))) errors.push(phase4Text("nutrientsInvalid"));
    return Array.from(new Set(errors));
  }

  function phase4CustomFingerprint(payload) {
    return JSON.stringify([
      payload.name, payload.brand, payload.referenceAmount, payload.referenceUnit,
      payload.referenceMassGrams, payload.referenceVolumeMl, payload.energy,
      payload.protein, payload.carbohydrate, payload.fat, payload.fiber
    ]);
  }

  async function phase4SaveCustomFood(form) {
    const userId = phase4EnsureCurrentUser();
    if (!userId || !supabaseClient) {
      phase4ShowPortalFeedback(phase4Text("authNotReady"), "error");
      return;
    }
    const food = phase4State.portal.food;
    const editing = Boolean(food?.id);
    const payload = phase4CustomPayload(form);
    const errors = phase4ValidateCustom(payload);
    if (errors.length) {
      phase4ShowPortalFeedback(errors.join(" "), "error");
      return;
    }
    const fingerprint = phase4CustomFingerprint(payload);
    if (!editing && phase4State.customDraft.submittedFingerprint && phase4State.customDraft.submittedFingerprint !== fingerprint) {
      phase4State.customDraft.foodId = phase4Uuid();
    }
    phase4State.customDraft.submittedFingerprint = fingerprint;
    phase4ShowPortalFeedback(phase4Text("saving"));
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_upsert_custom_food", {
        p_food_id: editing ? food.id : phase4State.customDraft.foodId,
        p_name: payload.name,
        p_brand: payload.brand || null,
        p_reference_amount: payload.referenceAmount,
        p_reference_unit: payload.referenceUnit,
        p_reference_mass_grams: payload.referenceMassGrams,
        p_reference_volume_ml: payload.referenceVolumeMl,
        p_density_g_per_ml: null,
        p_energy_kcal: payload.energy,
        p_protein_grams: payload.protein,
        p_carbohydrate_grams: payload.carbohydrate,
        p_fat_grams: payload.fat,
        p_fiber_grams: payload.fiber,
        p_expected_updated_at: editing ? food.updated_at : null
      });
      if (error) throw error;
      if (phase4State.userId !== userId) return;
      phase4State.customDraft = { foodId: "", submittedFingerprint: "" };
      phase4State.customs.status = "idle";
      phase4State.search.status = "idle";
      phase4OpenPortal("foods", phase4State.portal.opener, { tab: "custom", feedback: phase4Text("customSaved"), feedbackType: "ok" });
      await phase4LoadCustomFoods({ reset: true });
      if (!data) phase4SetPortalFeedback(phase4Text("unexpectedError"), "error");
    } catch (error) {
      phase4ShowPortalFeedback(phase4ErrorMessage(error, "customs"), "error");
    }
  }

  function phase4ArchiveDialog() {
    const food = phase4State.portal.food || {};
    const body = `
      <p>${escapeHTML(phase4Text("archiveBody"))}</p>
      <strong>${escapeHTML(food.name || "-")}</strong>
      ${phase4FeedbackMarkup()}
      <div class="phase4-dialog-actions">
        <button class="phase4-gold-action" data-phase4-confirm-archive type="button">${escapeHTML(phase4Text("confirmArchive"))}</button>
        <button class="secondary-btn" data-phase4-back-foods type="button">${escapeHTML(phase4Text("cancel"))}</button>
      </div>
    `;
    return phase4DialogFrame(phase4Text("archiveTitle"), body, { eyebrow: phase4Text("customFood") });
  }

  async function phase4ArchiveCustomFood() {
    const userId = phase4EnsureCurrentUser();
    const food = phase4State.portal.food;
    if (!userId || !food?.id || !supabaseClient) return;
    phase4ShowPortalFeedback(phase4Text("saving"));
    try {
      const { error } = await supabaseClient.rpc("fmz_phase4_archive_custom_food", {
        p_food_id: food.id,
        p_expected_updated_at: food.updated_at
      });
      if (error) throw error;
      if (phase4State.userId !== userId) return;
      phase4State.customs.status = "idle";
      phase4State.search.status = "idle";
      phase4OpenPortal("foods", phase4State.portal.opener, { tab: "custom", feedback: phase4Text("customArchived"), feedbackType: "ok" });
      await phase4LoadCustomFoods({ reset: true });
    } catch (error) {
      phase4ShowPortalFeedback(phase4ErrorMessage(error, "customs"), "error");
    }
  }

  function phase4ReturnToFoods(tab = "custom") {
    const opener = phase4State.portal.opener;
    phase4State.customDraft = { foodId: "", submittedFingerprint: "" };
    phase4OpenPortal("foods", opener, { tab });
    if (tab === "custom" && phase4State.customs.status === "idle") phase4LoadCustomFoods({ reset: true });
    if (tab === "search" && phase4State.search.status === "idle") phase4SearchFoods({ reset: true });
  }

  function phase4HandleClick(event) {
    const button = event.target?.closest?.("button");
    if (!button) return;
    if (button.dataset.phase4OpenTarget !== undefined) {
      phase4SetPortalFeedback();
      phase4OpenPortal("target", button);
      return;
    }
    if (button.dataset.phase4OpenFoods !== undefined) {
      phase4SetPortalFeedback();
      phase4OpenPortal("foods", button, { tab: "search" });
      if (phase4State.search.status === "idle") phase4SearchFoods({ reset: true });
      return;
    }
    if (button.dataset.phase4Close !== undefined) {
      phase4ClosePortal();
      return;
    }
    if (button.dataset.phase4RetryTarget !== undefined) {
      phase4LoadTarget(true);
      return;
    }
    if (button.dataset.phase4FoodTab) {
      phase4State.portal.tab = button.dataset.phase4FoodTab;
      phase4SetPortalFeedback();
      phase4RenderPortal();
      if (phase4State.portal.tab === "custom" && phase4State.customs.status === "idle") phase4LoadCustomFoods({ reset: true });
      if (phase4State.portal.tab === "search" && phase4State.search.status === "idle") phase4SearchFoods({ reset: true });
      return;
    }
    if (button.dataset.phase4RetrySearch !== undefined) {
      phase4SearchFoods({ reset: true });
      return;
    }
    if (button.dataset.phase4LoadMoreSearch !== undefined) {
      phase4SearchFoods({ reset: false });
      return;
    }
    if (button.dataset.phase4RetryCustoms !== undefined || button.dataset.phase4RefreshCustoms !== undefined) {
      phase4LoadCustomFoods({ reset: true });
      return;
    }
    if (button.dataset.phase4LoadMoreCustoms !== undefined) {
      phase4LoadCustomFoods({ reset: false });
      return;
    }
    if (button.dataset.phase4NewCustom !== undefined) {
      phase4State.customDraft = { foodId: phase4Uuid(), submittedFingerprint: "" };
      phase4OpenPortal("custom", phase4State.portal.opener || button, { food: null });
      return;
    }
    if (button.dataset.phase4EditCustom) {
      const food = phase4FindFood(button.dataset.phase4EditCustom);
      if (!food || food.status === "archived") return;
      phase4State.customDraft = { foodId: food.id, submittedFingerprint: "" };
      phase4OpenPortal("custom", phase4State.portal.opener || button, { food });
      return;
    }
    if (button.dataset.phase4ArchiveCustom) {
      const food = phase4FindFood(button.dataset.phase4ArchiveCustom);
      if (!food || food.status === "archived") return;
      phase4OpenPortal("archive", phase4State.portal.opener || button, { food });
      return;
    }
    if (button.dataset.phase4ConfirmArchive !== undefined) {
      phase4ArchiveCustomFood();
      return;
    }
    if (button.dataset.phase4ViewFood) {
      const food = phase4FindFood(button.dataset.phase4ViewFood);
      if (food) phase4OpenPortal("food-detail", phase4State.portal.opener || button, { food });
      return;
    }
    if (button.dataset.phase4BackFoods !== undefined) {
      phase4ReturnToFoods(phase4State.portal.tab || "custom");
    }
  }

  function phase4HandleSubmit(event) {
    if (event.target?.id === "phase4TargetForm") {
      event.preventDefault();
      phase4SaveTarget(event.target);
    }
    if (event.target?.id === "phase4FoodSearchForm") {
      event.preventDefault();
      const data = new FormData(event.target);
      phase4State.search.query = String(data.get("query") || "").trim();
      phase4SearchFoods({ reset: true });
    }
    if (event.target?.id === "phase4CustomFoodForm") {
      event.preventDefault();
      phase4SaveCustomFood(event.target);
    }
  }

  function phase4HandleChange(event) {
    if (!event.target?.matches?.('#phase4CustomFoodForm select[name="referenceUnit"]')) return;
    const requiresConversion = ["serving", "piece"].includes(event.target.value);
    const details = event.target.form?.querySelector("[data-phase4-conversion]");
    if (!details) return;
    details.dataset.required = String(requiresConversion);
    details.open = requiresConversion;
  }

  function phase4HandleKeydown(event) {
    if (event.key === "Escape" && phase4State.portal.type) {
      event.preventDefault();
      phase4ClosePortal();
    }
  }

  renderNutrition = function renderNutritionPhase4Slice2() {
    const view = document.getElementById("nutrition");
    if (!view) return;
    if (!isLoggedIn() || state.ui.role !== "client") {
      view.classList.remove("phase4-nutrition-active");
      const root = document.getElementById("phase4NutritionRoot");
      if (root) root.hidden = true;
      return phase4LegacyRenderNutrition();
    }
    view.classList.add("phase4-nutrition-active");
    const root = phase4EnsureRoot();
    if (root) root.hidden = false;
    phase4RenderOverview();
  };

  document.addEventListener("click", phase4HandleClick);
  document.addEventListener("submit", phase4HandleSubmit);
  document.addEventListener("change", phase4HandleChange);
  document.addEventListener("keydown", phase4HandleKeydown);

  window.FMZ_PHASE4_NUTRITION_SLICE2 = Object.freeze({
    version: PHASE4_NUTRITION_SLICE2_VERSION,
    searchPageSize: PHASE4_SEARCH_PAGE_SIZE,
    customPageSize: PHASE4_CUSTOM_PAGE_SIZE,
    freeCustomFoodLimit: PHASE4_CUSTOM_FOOD_FREE_LIMIT,
    validateTarget: (payload) => phase4ValidateTarget({ ...payload }),
    validateCustomFood: (payload) => phase4ValidateCustom({ ...payload }),
    state: () => ({
      userId: phase4State.userId,
      targetStatus: phase4State.target.status,
      searchStatus: phase4State.search.status,
      customStatus: phase4State.customs.status,
      portalType: phase4State.portal.type
    })
  });
})();
