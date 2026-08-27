(() => {
  if (window.FMZ_PHASE4_NUTRITION_SLICE3_LOADED) return;
  window.FMZ_PHASE4_NUTRITION_SLICE3_LOADED = true;

  const PHASE4_SLICE3_VERSION = "20260827-phase4fd-barcode1";
  const PHASE4_SLICE3_SEARCH_PAGE_SIZE = 25;
  const PHASE4_SLICE3_FREE_HISTORY_DAYS = 7;
  const PHASE4_SLICE3_MEALS = ["breakfast", "lunch", "dinner", "snacks"];
  const PHASE4_SLICE3_UNITS = ["g", "ml", "serving", "piece"];
  const PHASE4_PROVIDER_FUNCTION = "nutrition-provider";
  const PHASE4_PROVIDER_SEARCH_PAGE_SIZE = 5;
  const PHASE4_PROVIDER_MAX_PAGES = 3;

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
      scanBarcode: "Barcode scannen",
      scanBarcodeTitle: "Barcode zoeken",
      scanBarcodeIntro: "Scan de barcode of voer hem handmatig in. Er wordt nooit automatisch voeding gelogd.",
      startCamera: "Camera starten",
      stopCamera: "Camera stoppen",
      cameraLoading: "Camera starten...",
      cameraReady: "Houd de barcode rustig en volledig in beeld.",
      cameraDenied: "Cameratoegang is geweigerd. Gebruik de handmatige barcode-invoer.",
      cameraUnsupported: "Deze browser ondersteunt geen veilige camerascan. Gebruik de handmatige barcode-invoer.",
      manualBarcode: "Barcode handmatig invoeren",
      barcodePlaceholder: "EAN, UPC of GTIN",
      lookupBarcode: "Product zoeken",
      barcodeLookingUp: "Barcode controleren...",
      barcodeInvalid: "Voer een geldige EAN-8, UPC-A, EAN-13 of GTIN-14 in.",
      barcodeNotFound: "Geen bruikbaar product gevonden. Je kunt een eigen voedingsmiddel met deze barcode maken.",
      barcodeUnavailable: "Barcode zoeken is tijdelijk niet beschikbaar. Probeer het opnieuw of maak een eigen voedingsmiddel.",
      createCustomWithBarcode: "Eigen product met barcode maken",
      barcodeLabel: "Barcode",
      scanAgain: "Opnieuw scannen",
      manageFoods: "Voedingsmiddelen beheren",
      searchFood: "Voedingsmiddel zoeken",
      searchPlaceholder: "Zoek op naam, merk of barcode",
      search: "Zoeken",
      results: "Resultaten",
      myFoodsResults: "Mijn voedingsmiddelen",
      productResults: "Producten",
      catalogResults: "Voedingsmiddelen",
      searchLoading: "Voedingsmiddelen laden...",
      searchFailed: "Zoeken is niet gelukt.",
      noFoods: "Geen passende voedingsmiddelen gevonden.",
      providerSearch: "Meer voedingsmiddelen zoeken",
      providerResults: "Meer resultaten",
      providerSearchLoading: "Meer voedingsmiddelen zoeken...",
      providerSearchEmpty: "Geen aanvullende voedingsmiddelen gevonden.",
      providerLookupLoading: "Voedingsmiddel controleren...",
      providerSource: "USDA FoodData Central",
      providerAttribution: "Bron: USDA FoodData Central (CC0)",
      offSource: "Open Food Facts",
      offAttribution: "Productgegevens: Open Food Facts-bijdragers (ODbL)",
      offInspect: "Kiezen",
      offInspectTitle: "Product bekijken",
      offUseProduct: "Product toevoegen",
      offUnitOnly: "Dit product wordt uitsluitend in {unit} gelogd. Gram en milliliter worden nooit onderling gelijkgesteld.",
      offHistorical: "Opgeslagen Open Food Facts-waarden blijven de historische bron voor deze invoer.",
      offUnavailable: "Dit Open Food Facts-product is niet meer actief of logbaar. Kies het product opnieuw.",
      unexpectedResult: "Een onveilig of onvolledig zoekresultaat is niet getoond.",
      per100g: "Voedingswaarden per 100 g",
      per100ml: "Voedingswaarden per 100 ml",
      providerGramsOnly: "Dit voedingsmiddel wordt in gram gelogd.",
      providerAuthRequired: "Je sessie is verlopen. Log opnieuw in en probeer het daarna nog eens.",
      providerRateLimited: "De aanvullende zoekdienst is tijdelijk druk. Probeer het later opnieuw.",
      providerUnavailable: "Meer voedingsmiddelen zoeken is tijdelijk niet beschikbaar. Lokale en eigen voedingsmiddelen blijven bruikbaar.",
      providerCandidateInvalid: "Dit zoekresultaat is verlopen. Zoek het voedingsmiddel opnieuw.",
      providerStale: "Deze invoer is intussen gewijzigd. De dag is vernieuwd; open de invoer opnieuw.",
      providerHistorical: "Opgeslagen voedingswaarden; voor weergave is geen nieuwe zoekopdracht nodig.",
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
      scanBarcode: "Scan barcode",
      scanBarcodeTitle: "Find by barcode",
      scanBarcodeIntro: "Scan the barcode or enter it manually. Food is never logged automatically.",
      startCamera: "Start camera",
      stopCamera: "Stop camera",
      cameraLoading: "Starting camera...",
      cameraReady: "Hold the complete barcode steady inside the camera view.",
      cameraDenied: "Camera access was denied. Use manual barcode entry.",
      cameraUnsupported: "This browser does not support safe camera scanning. Use manual barcode entry.",
      manualBarcode: "Enter barcode manually",
      barcodePlaceholder: "EAN, UPC, or GTIN",
      lookupBarcode: "Find product",
      barcodeLookingUp: "Checking barcode...",
      barcodeInvalid: "Enter a valid EAN-8, UPC-A, EAN-13, or GTIN-14.",
      barcodeNotFound: "No usable product was found. You can create a custom food with this barcode.",
      barcodeUnavailable: "Barcode lookup is temporarily unavailable. Retry or create a custom food.",
      createCustomWithBarcode: "Create custom food with barcode",
      barcodeLabel: "Barcode",
      scanAgain: "Scan again",
      manageFoods: "Manage foods",
      searchFood: "Search food",
      searchPlaceholder: "Search by name, brand, or barcode",
      search: "Search",
      results: "Results",
      myFoodsResults: "My foods",
      productResults: "Products",
      catalogResults: "Foods",
      searchLoading: "Loading foods...",
      searchFailed: "Search failed.",
      noFoods: "No matching foods found.",
      providerSearch: "Search more foods",
      providerResults: "More results",
      providerSearchLoading: "Searching more foods...",
      providerSearchEmpty: "No additional foods found.",
      providerLookupLoading: "Checking food...",
      providerSource: "USDA FoodData Central",
      providerAttribution: "Source: USDA FoodData Central (CC0)",
      offSource: "Open Food Facts",
      offAttribution: "Product data: Open Food Facts contributors (ODbL)",
      offInspect: "Select",
      offInspectTitle: "View product",
      offUseProduct: "Add product",
      offUnitOnly: "This product is logged only in {unit}. Grams and millilitres are never treated as equal.",
      offHistorical: "Saved Open Food Facts values remain the historical source for this entry.",
      offUnavailable: "This Open Food Facts product is no longer active or loggable. Select the product again.",
      unexpectedResult: "An unsafe or incomplete search result was not shown.",
      per100g: "Nutrition per 100 g",
      per100ml: "Nutrition per 100 ml",
      providerGramsOnly: "This food is logged in grams.",
      providerAuthRequired: "Your session has expired. Sign in again and then retry.",
      providerRateLimited: "The additional food search is temporarily busy. Try again later.",
      providerUnavailable: "Searching more foods is temporarily unavailable. Local and custom foods remain available.",
      providerCandidateInvalid: "This search result has expired. Search for the food again.",
      providerStale: "This entry changed in the meantime. The day was refreshed; open the entry again.",
      providerHistorical: "Saved nutrition values; displaying this entry does not require another search.",
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
      scanBarcode: "Barcode scannen",
      scanBarcodeTitle: "Per Barcode suchen",
      scanBarcodeIntro: "Scanne den Barcode oder gib ihn manuell ein. Lebensmittel werden nie automatisch protokolliert.",
      startCamera: "Kamera starten",
      stopCamera: "Kamera stoppen",
      cameraLoading: "Kamera wird gestartet...",
      cameraReady: "Halte den vollstaendigen Barcode ruhig im Kamerabild.",
      cameraDenied: "Der Kamerazugriff wurde verweigert. Nutze die manuelle Barcode-Eingabe.",
      cameraUnsupported: "Dieser Browser unterstuetzt keinen sicheren Kamerascan. Nutze die manuelle Barcode-Eingabe.",
      manualBarcode: "Barcode manuell eingeben",
      barcodePlaceholder: "EAN, UPC oder GTIN",
      lookupBarcode: "Produkt suchen",
      barcodeLookingUp: "Barcode wird geprueft...",
      barcodeInvalid: "Gib eine gueltige EAN-8, UPC-A, EAN-13 oder GTIN-14 ein.",
      barcodeNotFound: "Kein nutzbares Produkt gefunden. Du kannst ein eigenes Lebensmittel mit diesem Barcode erstellen.",
      barcodeUnavailable: "Die Barcode-Suche ist voruebergehend nicht verfuegbar. Versuche es erneut oder erstelle ein eigenes Lebensmittel.",
      createCustomWithBarcode: "Eigenes Produkt mit Barcode erstellen",
      barcodeLabel: "Barcode",
      scanAgain: "Erneut scannen",
      manageFoods: "Lebensmittel verwalten",
      searchFood: "Lebensmittel suchen",
      searchPlaceholder: "Nach Name, Marke oder Barcode suchen",
      search: "Suchen",
      results: "Ergebnisse",
      myFoodsResults: "Meine Lebensmittel",
      productResults: "Produkte",
      catalogResults: "Lebensmittel",
      searchLoading: "Lebensmittel werden geladen...",
      searchFailed: "Die Suche ist fehlgeschlagen.",
      noFoods: "Keine passenden Lebensmittel gefunden.",
      providerSearch: "Weitere Lebensmittel suchen",
      providerResults: "Weitere Ergebnisse",
      providerSearchLoading: "Weitere Lebensmittel werden gesucht...",
      providerSearchEmpty: "Keine weiteren Lebensmittel gefunden.",
      providerLookupLoading: "Lebensmittel wird geprueft...",
      providerSource: "USDA FoodData Central",
      providerAttribution: "Quelle: USDA FoodData Central (CC0)",
      offSource: "Open Food Facts",
      offAttribution: "Produktdaten: Open Food Facts-Mitwirkende (ODbL)",
      offInspect: "Auswaehlen",
      offInspectTitle: "Produkt ansehen",
      offUseProduct: "Produkt hinzufuegen",
      offUnitOnly: "Dieses Produkt wird nur in {unit} protokolliert. Gramm und Milliliter werden niemals gleichgesetzt.",
      offHistorical: "Gespeicherte Open-Food-Facts-Werte bleiben die historische Quelle fuer diesen Eintrag.",
      offUnavailable: "Dieses Open-Food-Facts-Produkt ist nicht mehr aktiv oder protokollierbar. Waehle das Produkt erneut aus.",
      unexpectedResult: "Ein unsicheres oder unvollstaendiges Suchergebnis wurde nicht angezeigt.",
      per100g: "Naehrwerte pro 100 g",
      per100ml: "Naehrwerte pro 100 ml",
      providerGramsOnly: "Dieses Lebensmittel wird in Gramm protokolliert.",
      providerAuthRequired: "Deine Sitzung ist abgelaufen. Melde dich erneut an und versuche es danach noch einmal.",
      providerRateLimited: "Die zusaetzliche Lebensmittelsuche ist voruebergehend ausgelastet. Versuche es spaeter erneut.",
      providerUnavailable: "Die Suche nach weiteren Lebensmitteln ist voruebergehend nicht verfuegbar. Lokale und eigene Lebensmittel bleiben nutzbar.",
      providerCandidateInvalid: "Dieses Suchergebnis ist abgelaufen. Suche das Lebensmittel erneut.",
      providerStale: "Dieser Eintrag wurde inzwischen geaendert. Der Tag wurde aktualisiert; oeffne den Eintrag erneut.",
      providerHistorical: "Gespeicherte Naehrwerte; fuer die Anzeige ist keine neue Suche erforderlich.",
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
    portal: { type: "", opener: null, meal: "breakfast", food: null, item: null, offProduct: false, transientOff: false, providerCandidate: null, candidateToken: "", feedback: "", feedbackType: "" },
    search: { status: "idle", query: "", items: [], afterRank: null, afterScore: null, afterName: null, afterSource: null, afterId: null, hasMore: false, error: "", rejectedCount: 0, requestToken: 0 },
    providerSearch: { status: "idle", query: "", items: [], page: 1, hasMore: false, error: "", requestToken: 0, requestId: "", submittedFingerprint: "", lookupStatus: "idle", lookupCandidateId: "", lookupRequestId: "" },
    portions: { status: "idle", items: [], error: "", requestToken: 0 },
    submission: { kind: "", itemId: "", requestId: "", submittedFingerprint: "", inFlight: false },
    customDraft: { foodId: "", submittedFingerprint: "", barcode: "" },
    scanner: { status: "idle", error: "", barcode: "", lastDecoded: "", requestId: "", submittedBarcode: "", allowCustom: false },
    dutchDisplayLabels: new Map(),
    dutchDisplayLabelsLoading: new Set(),
    displayLabelsRequestToken: 0
  };
  const PHASE4_LOCAL_SEARCH_DEBOUNCE_MS = 240;
  const PHASE4_LOCAL_RESULTS_BEFORE_PROVIDER = 5;
  const PHASE4_PROVIDER_SEARCH_DEBOUNCE_MS = 400;
  let localSearchDebounceTimer = null;
  let providerSearchDebounceTimer = null;
  let barcodeScannerStream = null;
  let barcodeScannerControls = null;
  let barcodeScannerFrame = 0;
  let barcodeScannerLocked = false;

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

  function displayFoodName(food, fallback = "-") {
    const mappedLabel = food?.food_id ? slice3State.dutchDisplayLabels.get(food.food_id) : "";
    const offDutchLabel = food?.source_provider_snapshot === "open_food_facts"
      ? String(food?.metadata?.display_name_nl || "").trim()
      : "";
    const displayFood = mappedLabel
      ? { ...food, name: food?.name || food?.food_name_snapshot, metadata: { ...(food?.metadata || {}), dutch_display_label: mappedLabel } }
      : offDutchLabel
        ? { ...food, name: food?.name || food?.food_name_snapshot, metadata: { ...(food?.metadata || {}), dutch_display_label: offDutchLabel } }
        : food;
    const displayHelper = window.FMZ_PHASE4_NUTRITION_SLICE2?.displayFoodName;
    if (typeof displayHelper === "function") return displayHelper(displayFood, fallback, language());
    const canonicalName = String(displayFood?.name || displayFood?.food_name_snapshot || "").trim();
    const dutchLabel = String(displayFood?.metadata?.dutch_display_label || "").trim();
    return language() === "nl" && dutchLabel ? dutchLabel : (canonicalName || fallback);
  }

  async function hydrateDutchDisplayLabels(day) {
    if (language() !== "nl" || !supabaseClient || !slice3State.userId) return;
    const foodIds = Array.from(new Set(
      (day?.items || [])
        .filter((item) => item?.status === "active" && item?.food_id)
        .map((item) => item.food_id)
    )).filter((foodId) => !slice3State.dutchDisplayLabels.has(foodId) && !slice3State.dutchDisplayLabelsLoading.has(foodId)).slice(0, 200);
    if (!foodIds.length) return;
    foodIds.forEach((foodId) => slice3State.dutchDisplayLabelsLoading.add(foodId));
    const userId = slice3State.userId;
    const requestToken = slice3State.displayLabelsRequestToken + 1;
    slice3State.displayLabelsRequestToken = requestToken;
    try {
      const { data, error } = await supabaseClient
        .from("foods")
        .select("id,name,metadata")
        .in("id", foodIds);
      if (error) throw error;
      if (slice3State.userId !== userId || slice3State.displayLabelsRequestToken !== requestToken) return;
      const labelsById = new Map((Array.isArray(data) ? data : []).map((food) => [food.id, String(food?.metadata?.dutch_display_label || "").trim()]));
      foodIds.forEach((foodId) => slice3State.dutchDisplayLabels.set(foodId, labelsById.get(foodId) || ""));
      renderRoot();
    } catch (_error) {
      if (slice3State.userId !== userId || slice3State.displayLabelsRequestToken !== requestToken) return;
      foodIds.forEach((foodId) => slice3State.dutchDisplayLabels.set(foodId, ""));
    } finally {
      foodIds.forEach((foodId) => slice3State.dutchDisplayLabelsLoading.delete(foodId));
    }
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
    cancelLocalSearchDebounce();
    cancelProviderSearchDebounce();
    closePortal(false);
    slice3State.userId = userId;
    slice3State.todayDate = localTodayISO();
    slice3State.selectedDate = slice3State.todayDate;
    slice3State.timezoneName = resolvedTimezone();
    slice3State.timezone = { status: "idle", error: "", requestToken: slice3State.timezone.requestToken + 1 };
    slice3State.day = { status: "idle", value: null, error: "", requestToken: slice3State.day.requestToken + 1 };
    slice3State.notice = "";
    slice3State.search = { status: "idle", query: "", items: [], afterRank: null, afterScore: null, afterName: null, afterSource: null, afterId: null, hasMore: false, error: "", rejectedCount: 0, requestToken: slice3State.search.requestToken + 1 };
    slice3State.providerSearch = { status: "idle", query: "", items: [], page: 1, hasMore: false, error: "", requestToken: slice3State.providerSearch.requestToken + 1, requestId: "", submittedFingerprint: "", lookupStatus: "idle", lookupCandidateId: "", lookupRequestId: "" };
    slice3State.portions = { status: "idle", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    slice3State.submission = { kind: "", itemId: "", requestId: "", submittedFingerprint: "", inFlight: false };
    slice3State.customDraft = { foodId: "", submittedFingerprint: "", barcode: "" };
    slice3State.scanner = { status: "idle", error: "", barcode: "", lastDecoded: "", requestId: "", submittedBarcode: "", allowCustom: false };
    slice3State.dutchDisplayLabels = new Map();
    slice3State.dutchDisplayLabelsLoading = new Set();
    slice3State.displayLabelsRequestToken += 1;
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
      .phase4-s3-search-fixed { display:grid; gap:8px; min-width:0; }
      .phase4-s3-search-results { min-width:0; display:grid; gap:14px; overflow-anchor:none; }
      .phase4-s3-search-group { display:grid; gap:8px; min-width:0; }
      .phase4-s3-search-group + .phase4-s3-search-group { margin-top:14px; }
      .phase4-s3-search-list { display:grid; gap:8px; }
      .phase4-s3-search-row { display:grid; gap:6px; padding:11px 0; border-bottom:1px solid var(--line); }
      .phase4-s3-search-row strong, .phase4-s3-search-row small { overflow-wrap:anywhere; }
      .phase4-s3-search-head { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
      .phase4-s3-search-meta { display:flex; flex-wrap:wrap; gap:5px 12px; color:var(--muted); }
      .phase4-s3-source-label { color:var(--muted); font-size:12px; font-weight:800; }
      .phase4-s3-off-note { padding:10px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); color:var(--muted); }
      .phase4-s3-provider { display:grid; gap:10px; padding-top:12px; border-top:1px solid var(--line); }
      .phase4-s3-provider-head { display:flex; align-items:center; justify-content:space-between; gap:10px; }
      .phase4-s3-provider-source { color:var(--muted); font-size:12px; font-weight:700; }
      .phase4-s3-scan-sheet { grid-template-rows:auto minmax(0,1fr); }
      .phase4-s3-scanner { display:grid; gap:14px; min-width:0; }
      .phase4-s3-camera { position:relative; width:100%; aspect-ratio:4 / 3; max-height:44dvh; overflow:hidden; border:1px solid var(--line); border-radius:8px; background:#05070a; }
      .phase4-s3-camera[hidden] { display:none; }
      .phase4-s3-camera video { width:100%; height:100%; object-fit:cover; display:block; }
      .phase4-s3-camera-guide { pointer-events:none; position:absolute; inset:20%; border:2px solid #c89312; border-radius:8px; box-shadow:0 0 0 999px rgba(0,0,0,.28); }
      .phase4-s3-camera-actions { display:flex; flex-wrap:wrap; gap:8px; }
      .phase4-s3-manual { display:grid; gap:10px; padding-top:12px; border-top:1px solid var(--line); }
      .phase4-s3-manual-row { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; }
      .phase4-s3-manual-row input { min-width:0; min-height:44px; }
      .phase4-s3-feedback { min-height:22px; margin:0; color:var(--muted); }
      .phase4-s3-feedback.error { color:#ffb0b0; }
      .phase4-s3-feedback.ok { color:#8bd8b8; }
      .phase4-s3-detail-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
      .phase4-s3-detail-grid > div { min-width:0; display:grid; gap:2px; }
      .phase4-s3-detail-grid span { color:var(--muted); font-size:12px; font-weight:800; }
      .phase4-s3-detail-grid strong { overflow-wrap:anywhere; }
      @media (max-width:719px) {
        .phase4-s3-search-sheet { height:94dvh; max-height:94dvh; overflow:hidden; grid-template-rows:auto auto minmax(0,1fr) auto; }
        .phase4-s3-search-results { min-height:0; overflow-y:auto; overscroll-behavior:contain; }
        .phase4-s3-scan-sheet { height:94dvh; max-height:94dvh; overflow:auto; }
      }
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
        .phase4-s3-manual-row { grid-template-columns:1fr; }
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
    const providerSource = isProviderSnapshot(item) ? `<small class="phase4-s3-provider-source">${escapeHTML(text("providerSource"))}</small>` : "";
    return `
      <button class="phase4-s3-item-row" data-phase4-s3-item="${escapeHTML(item.id)}" type="button" aria-haspopup="dialog">
        <span class="phase4-s3-item-main">
          <strong>${escapeHTML(displayFoodName(item))}</strong>
          <small>${escapeHTML(`${formatNumber(item.consumed_quantity, 3)} ${unitLabel(item.consumed_unit)} | P ${formatNumber(item.protein_grams_snapshot, 1)}g | C ${formatNumber(item.carbohydrate_grams_snapshot, 1)}g | F ${formatNumber(item.fat_grams_snapshot, 1)}g`)}</small>
          ${providerSource}
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
      else if (slice3State.day.status === "ready") void hydrateDutchDisplayLabels(slice3State.day.value);
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
    if (slice3State.day.status === "ready") void hydrateDutchDisplayLabels(slice3State.day.value);
  }

  function errorMessage(error, context = "") {
    const code = String(error?.code || "");
    const message = String(error?.message || error || "").toLowerCase();
    if (code === "40001" || message.includes("changed; refresh") || message.includes("no longer active")) return text("stale");
    if (code === "23505" || message.includes("already used with a different payload") || message.includes("uuid is unavailable")) return text("conflict");
    if (message.includes("seven local calendar days")) return text("freeHistory");
    if (message.includes("future nutrition")) return text("futureDay");
    if (message.includes("maximum 10 active custom foods") || message.includes("free nutrition limit")) return text("customLimitReached");
    if (message.includes("active loggable off product not found") || message.includes("off quantity unit")) return text("offUnavailable");
    if (message.includes("network") || message.includes("fetch") || message.includes("connection")) return text("networkRetry");
    if (context === "search") return text("searchFailed");
    if (context === "timezone") return text("timezoneFailed");
    if (context === "day") return text("loadDayFailed");
    return text("unexpected");
  }

  function isProviderSnapshot(item) {
    return Boolean(item && item.food_id === null && item.source_provider_snapshot === "usda_fdc");
  }

  function isTransientOffSnapshot(item) {
    return Boolean(
      item
      && item.food_id === null
      && item.source_provider_snapshot === "open_food_facts"
      && ["transient_off_log", "transient_off_replace"].includes(String(item?.metadata?.operation || ""))
    );
  }

  function isOffSnapshot(item) {
    return Boolean(
      item
      && item.food_id === null
      && item.source_provider_snapshot === "open_food_facts"
      && ["off_log", "off_replace", "transient_off_log", "transient_off_replace"].includes(String(item?.metadata?.operation || ""))
    );
  }

  function providerCountryCode() {
    const match = /-([a-z]{2})$/i.exec(String(navigator.language || ""));
    if (match) return match[1].toUpperCase();
    return { nl: "NL", en: "US", de: "DE" }[language()] || "NL";
  }

  function providerErrorMessage(error) {
    const code = String(error?.code || "");
    const status = Number(error?.status || 0);
    const message = String(error?.message || error || "").toLowerCase();
    if (status === 401 || code === "unauthorized") return text("providerAuthRequired");
    if (code === "provider_replace_stale") return text("providerStale");
    if (status === 429 || code.includes("rate_limited")) return text("providerRateLimited");
    if (status === 409 && (code.includes("candidate") || code.includes("candidate_token"))) return text("providerCandidateInvalid");
    if (status === 502 || status === 503 || code.includes("provider_unavailable") || code.includes("circuit")) return text("providerUnavailable");
    if (message.includes("network") || message.includes("fetch") || message.includes("connection")) return text("networkRetry");
    if (code.includes("request_conflict")) return text("conflict");
    return text("providerUnavailable");
  }

  async function providerRequest(route, body) {
    if (!supabaseClient?.auth?.getSession || !SUPABASE_URL || !SUPABASE_ANON_KEY) {
      const unavailable = new Error("provider client unavailable");
      unavailable.code = "provider_unavailable";
      unavailable.status = 503;
      throw unavailable;
    }
    const { data: sessionData, error: sessionError } = await supabaseClient.auth.getSession();
    const accessToken = sessionData?.session?.access_token;
    if (sessionError || !accessToken) {
      const unauthorized = new Error("authentication required");
      unauthorized.code = "unauthorized";
      unauthorized.status = 401;
      throw unauthorized;
    }
    let response;
    try {
      response = await fetch(`${SUPABASE_URL}/functions/v1/${PHASE4_PROVIDER_FUNCTION}/${route}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          apikey: SUPABASE_ANON_KEY,
          "content-type": "application/json"
        },
        body: JSON.stringify(body),
        cache: "no-store"
      });
    } catch (error) {
      const networkError = new Error("provider network failure");
      networkError.code = "network_failure";
      networkError.status = 0;
      throw networkError;
    }
    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    if (!response.ok || payload?.ok !== true || !payload?.data) {
      const requestError = new Error(String(payload?.error?.message || "provider request failed"));
      requestError.code = String(payload?.error?.code || "provider_unavailable");
      requestError.status = response.status;
      throw requestError;
    }
    return payload.data;
  }

  function normalizeGtin14(value) {
    const digits = String(value || "").replace(/[^0-9]/g, "");
    if (![8, 12, 13, 14].includes(digits.length)) return "";
    const body = digits.slice(0, -1);
    const check = Number(digits.at(-1));
    const sum = Array.from(body).reverse().reduce((total, digit, index) => (
      total + Number(digit) * (index % 2 === 0 ? 3 : 1)
    ), 0);
    if ((10 - (sum % 10)) % 10 !== check) return "";
    return digits.padStart(14, "0");
  }

  function scannerStatusMessage() {
    if (slice3State.scanner.status === "loading") return text("cameraLoading");
    if (slice3State.scanner.status === "ready") return text("cameraReady");
    if (slice3State.scanner.status === "lookup") return text("barcodeLookingUp");
    return slice3State.scanner.error || "";
  }

  function updateScannerStatus() {
    const portal = document.getElementById("phase4Slice3Portal");
    const status = portal?.querySelector("[data-phase4-s3-scanner-status]");
    if (status) {
      status.textContent = scannerStatusMessage();
      status.classList.toggle("error", slice3State.scanner.status === "error");
    }
    const start = portal?.querySelector("[data-phase4-s3-start-camera]");
    const stop = portal?.querySelector("[data-phase4-s3-stop-camera]");
    if (start) start.hidden = ["loading", "ready", "lookup"].includes(slice3State.scanner.status);
    if (stop) stop.hidden = !["loading", "ready"].includes(slice3State.scanner.status);
  }

  function stopBarcodeScanner({ update = false } = {}) {
    if (barcodeScannerFrame) window.cancelAnimationFrame(barcodeScannerFrame);
    barcodeScannerFrame = 0;
    try { barcodeScannerControls?.stop?.(); } catch { /* scanner cleanup is best effort */ }
    barcodeScannerControls = null;
    if (barcodeScannerStream) barcodeScannerStream.getTracks().forEach((track) => track.stop());
    barcodeScannerStream = null;
    const video = document.getElementById("phase4Slice3ScannerVideo");
    if (video) {
      try { video.pause(); } catch { /* no-op */ }
      video.srcObject = null;
    }
    barcodeScannerLocked = false;
    if (update && slice3State.portal.type === "scanner") {
      slice3State.scanner.status = "idle";
      slice3State.scanner.error = "";
      renderPortal();
    }
  }

  async function handleDecodedBarcode(value) {
    if (barcodeScannerLocked || slice3State.scanner.status === "lookup" || slice3State.portal.type !== "scanner") return;
    const normalized = normalizeGtin14(value);
    if (!normalized || normalized === slice3State.scanner.lastDecoded) return;
    barcodeScannerLocked = true;
    slice3State.scanner.lastDecoded = normalized;
    await lookupBarcode(value);
  }

  async function startNativeBarcodeScanner(video) {
    const supported = typeof window.BarcodeDetector?.getSupportedFormats === "function"
      ? await window.BarcodeDetector.getSupportedFormats()
      : ["ean_8", "ean_13", "upc_a", "upc_e"];
    const formats = ["ean_8", "ean_13", "upc_a", "upc_e"].filter((format) => supported.includes(format));
    if (!formats.length) throw new Error("native barcode formats unavailable");
    barcodeScannerStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    video.srcObject = barcodeScannerStream;
    await video.play();
    const detector = new window.BarcodeDetector({ formats });
    const detect = async () => {
      if (!barcodeScannerStream || slice3State.portal.type !== "scanner") return;
      try {
        const results = await detector.detect(video);
        if (results[0]?.rawValue) await handleDecodedBarcode(results[0].rawValue);
      } catch { /* individual undecodable frames are expected */ }
      if (barcodeScannerStream && slice3State.portal.type === "scanner" && !barcodeScannerLocked) {
        barcodeScannerFrame = window.requestAnimationFrame(detect);
      }
    };
    barcodeScannerFrame = window.requestAnimationFrame(detect);
  }

  async function startZxingBarcodeScanner(video) {
    const Reader = window.ZXingBrowser?.BrowserMultiFormatReader;
    if (typeof Reader !== "function") throw new Error("barcode decoder unavailable");
    const reader = new Reader();
    barcodeScannerControls = await reader.decodeFromConstraints(
      { audio: false, video: { facingMode: { ideal: "environment" } } },
      video,
      (result, _error, controls) => {
        if (controls) barcodeScannerControls = controls;
        const value = result?.getText?.() || result?.text || "";
        if (value) void handleDecodedBarcode(value);
      }
    );
    barcodeScannerStream = window.MediaStream && video.srcObject instanceof window.MediaStream ? video.srcObject : null;
  }

  async function startBarcodeScanner() {
    if (slice3State.portal.type !== "scanner" || slice3State.scanner.status === "loading") return;
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      slice3State.scanner.status = "error";
      slice3State.scanner.error = text("cameraUnsupported");
      renderPortal();
      return;
    }
    stopBarcodeScanner();
    slice3State.scanner.status = "loading";
    slice3State.scanner.error = "";
    renderPortal();
    const video = document.getElementById("phase4Slice3ScannerVideo");
    if (!video) return;
    try {
      if (typeof window.BarcodeDetector === "function") {
        try {
          await startNativeBarcodeScanner(video);
        } catch (nativeError) {
          const denied = ["NotAllowedError", "SecurityError", "PermissionDeniedError"].includes(String(nativeError?.name || ""));
          if (denied) throw nativeError;
          stopBarcodeScanner();
          await startZxingBarcodeScanner(video);
        }
      } else await startZxingBarcodeScanner(video);
      slice3State.scanner.status = "ready";
      updateScannerStatus();
    } catch (error) {
      stopBarcodeScanner();
      const denied = ["NotAllowedError", "SecurityError", "PermissionDeniedError"].includes(String(error?.name || ""));
      slice3State.scanner.status = "error";
      slice3State.scanner.error = text(denied ? "cameraDenied" : "cameraUnsupported");
      renderPortal();
    }
  }

  function mapLocalBarcodeResult(result) {
    if (result?.result_type === "off_branded_food") {
      return {
        result_type: "off_branded_food",
        source_provider: "open_food_facts",
        source_id: String(result.source_id || ""),
        id: String(result.source_id || ""),
        display_name: String(result.display_name || ""),
        name: String(result.display_name || ""),
        brand: String(result.brand || ""),
        nutrition_basis: String(result.nutrition_basis || ""),
        reference_amount: Number(result.reference_amount),
        reference_unit: String(result.reference_unit || ""),
        energy_kcal: Number(result.energy_kcal_reference),
        protein_grams: Number(result.protein_grams_reference),
        carbohydrate_grams: Number(result.carbohydrate_grams_reference),
        fat_grams: Number(result.fat_grams_reference),
        fiber_grams: result.fiber_grams_reference === null ? null : Number(result.fiber_grams_reference),
        quality_status: String(result.quality_status || ""),
        loggable: result.loggable === true
      };
    }
    if (!["custom_food", "generic_food"].includes(String(result?.result_type || ""))) return null;
    return { ...result, id: String(result.id || result.source_id || ""), name: String(result.name || result.display_name || "") };
  }

  function isSafeTransientOffCandidate(candidate) {
    return Boolean(
      candidate?.provider === "open_food_facts"
      && candidate?.candidate_id
      && candidate?.candidate_token
      && normalizeGtin14(candidate?.barcode) === candidate?.barcode
      && ["g", "ml"].includes(candidate?.reference_unit)
      && candidate?.reference_amount === 100
      && [candidate?.kcal, candidate?.protein, candidate?.carbohydrates, candidate?.fat]
        .every((value) => Number.isFinite(Number(value)) && Number(value) >= 0)
    );
  }

  function transientCandidateFood(candidate) {
    return {
      result_type: "transient_off_food",
      source_provider: "open_food_facts",
      source_id: candidate.candidate_id,
      id: candidate.candidate_id,
      display_name: candidate.name,
      name: candidate.name,
      brand: candidate.brand,
      barcode: candidate.barcode,
      nutrition_basis: candidate.nutrition_basis,
      reference_amount: 100,
      reference_unit: candidate.reference_unit,
      energy_kcal: candidate.kcal,
      protein_grams: candidate.protein,
      carbohydrate_grams: candidate.carbohydrates,
      fat_grams: candidate.fat,
      fiber_grams: candidate.fiber,
      metadata: { transient_off: true }
    };
  }

  function openScanner(meal, opener, item = null) {
    stopBarcodeScanner();
    slice3State.scanner = { status: "idle", error: "", barcode: "", lastDecoded: "", requestId: "", submittedBarcode: "", allowCustom: false };
    openPortal("scanner", opener, { meal, item });
  }

  async function lookupBarcode(value) {
    if (slice3State.portal.type !== "scanner") return;
    const original = String(value || "").trim();
    const normalized = normalizeGtin14(original);
    if (!normalized) {
      barcodeScannerLocked = false;
      slice3State.scanner.status = "error";
      slice3State.scanner.error = text("barcodeInvalid");
      slice3State.scanner.allowCustom = false;
      renderPortal();
      return;
    }
    if (slice3State.scanner.status === "lookup" && slice3State.scanner.submittedBarcode === normalized) return;
    if (!slice3State.scanner.requestId || slice3State.scanner.submittedBarcode !== normalized) {
      slice3State.scanner.requestId = uuid();
    }
    slice3State.scanner.barcode = original;
    slice3State.scanner.submittedBarcode = normalized;
    slice3State.scanner.status = "lookup";
    slice3State.scanner.error = "";
    slice3State.scanner.allowCustom = false;
    stopBarcodeScanner();
    renderPortal();
    try {
      const data = await providerRequest("off-barcode", { barcode: original, request_id: slice3State.scanner.requestId });
      if (slice3State.portal.type !== "scanner") return;
      if (data?.source === "local") {
        const food = mapLocalBarcodeResult(data.result);
        if (!food?.id) throw new Error("local barcode result invalid");
        if (food.result_type === "off_branded_food") openPortal("off", slice3State.portal.opener, { food, meal: slice3State.portal.meal, item: slice3State.portal.item });
        else openEntry(food, slice3State.portal.meal, slice3State.portal.opener, slice3State.portal.item);
        return;
      }
      if (data?.source !== "open_food_facts" || !isSafeTransientOffCandidate(data?.result)) throw new Error("transient OFF result invalid");
      const candidate = data.result;
      openPortal("off", slice3State.portal.opener, {
        food: transientCandidateFood(candidate),
        meal: slice3State.portal.meal,
        item: slice3State.portal.item,
        transientOff: true,
        providerCandidate: candidate,
        candidateToken: candidate.candidate_token
      });
    } catch (error) {
      if (slice3State.portal.type !== "scanner") return;
      const code = String(error?.code || "");
      const unavailableProduct = Number(error?.status || 0) === 404 || code.startsWith("off_product_");
      barcodeScannerLocked = false;
      slice3State.scanner.status = "error";
      slice3State.scanner.error = text(unavailableProduct ? "barcodeNotFound" : "barcodeUnavailable");
      slice3State.scanner.allowCustom = unavailableProduct;
      renderPortal();
    }
  }

  function cancelProviderSearchDebounce() {
    if (providerSearchDebounceTimer !== null) window.clearTimeout(providerSearchDebounceTimer);
    providerSearchDebounceTimer = null;
  }

  function cancelLocalSearchDebounce() {
    if (localSearchDebounceTimer !== null) window.clearTimeout(localSearchDebounceTimer);
    localSearchDebounceTimer = null;
  }

  function normalizedSearchQuery(value) {
    return String(value || "").normalize("NFKC").replace(/\s+/g, " ").trim();
  }

  function resetProviderSearch() {
    cancelProviderSearchDebounce();
    slice3State.providerSearch = {
      status: "idle",
      query: "",
      items: [],
      page: 1,
      hasMore: false,
      error: "",
      requestToken: slice3State.providerSearch.requestToken + 1,
      requestId: "",
      submittedFingerprint: "",
      lookupStatus: "idle",
      lookupCandidateId: "",
      lookupRequestId: ""
    };
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

  function dialogFrame(title, body, eyebrow = text("nutrition"), sheetClass = "") {
    return `
      <button class="phase4-s3-backdrop" data-phase4-s3-close type="button" aria-label="${escapeHTML(text("close"))}"></button>
      <section class="phase4-s3-sheet ${escapeHTML(sheetClass)}" role="dialog" aria-modal="true" aria-labelledby="phase4-s3-dialog-title">
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
      offProduct: options.offProduct === true,
      transientOff: options.transientOff === true,
      providerCandidate: options.providerCandidate || null,
      candidateToken: options.candidateToken || "",
      feedback: options.feedback || "",
      feedbackType: options.feedbackType || ""
    };
    document.body.classList.add("phase4-s3-dialog-open");
    renderPortal();
  }

  function closePortal(restoreFocus = true) {
    cancelLocalSearchDebounce();
    cancelProviderSearchDebounce();
    const opener = slice3State.portal?.opener;
    stopBarcodeScanner();
    document.getElementById("phase4Slice3Portal")?.remove();
    document.body.classList.remove("phase4-s3-dialog-open");
    slice3State.portal = { type: "", opener: null, meal: "breakfast", food: null, item: null, offProduct: false, transientOff: false, providerCandidate: null, candidateToken: "", feedback: "", feedbackType: "" };
    if (restoreFocus) opener?.focus?.();
  }

  function renderPortal({ preserveSearchFocus = false } = {}) {
    if (!slice3State.portal.type) return;
    let portal = document.getElementById("phase4Slice3Portal");
    const isNew = !portal;
    if (preserveSearchFocus && slice3State.portal.type === "search" && portal?.querySelector("#phase4Slice3SearchForm")) {
      renderSearchResults();
      return;
    }
    if (!portal) {
      portal = document.createElement("div");
      portal.id = "phase4Slice3Portal";
      portal.className = "phase4-s3-portal";
      document.body.appendChild(portal);
    }
    if (slice3State.portal.type === "search") portal.innerHTML = searchDialog();
    if (slice3State.portal.type === "scanner") portal.innerHTML = scannerDialog();
    if (slice3State.portal.type === "off") portal.innerHTML = offProductDialog();
    if (slice3State.portal.type === "entry") portal.innerHTML = entryDialog();
    if (slice3State.portal.type === "item") portal.innerHTML = itemDialog();
    if (slice3State.portal.type === "remove") portal.innerHTML = removeDialog();
    if (slice3State.portal.type === "custom") portal.innerHTML = customDialog();
    if (isNew) window.requestAnimationFrame(() => portal.querySelector("input, button, select")?.focus?.());
  }

  function openSearch(meal, opener, item = null) {
    slice3State.search = { status: "idle", query: "", items: [], afterRank: null, afterScore: null, afterName: null, afterSource: null, afterId: null, hasMore: false, error: "", rejectedCount: 0, requestToken: slice3State.search.requestToken + 1 };
    resetProviderSearch();
    openPortal("search", opener, { meal, item });
    searchFoods({ reset: true });
  }

  function providerSearchAllowed() {
    return !slice3State.portal.item || isProviderSnapshot(slice3State.portal.item);
  }

  function searchResultKey(food) {
    return `${food?.result_type || "unknown"}:${food?.source_id || food?.id || ""}`;
  }

  function isSafeUnifiedSearchResult(row) {
    const resultType = String(row?.result_type || "");
    const sourceId = String(row?.source_id || "");
    const displayName = String(row?.display_name || "").trim();
    const basis = String(row?.nutrition_basis || "");
    const referenceAmount = Number(row?.reference_amount);
    const referenceUnit = String(row?.reference_unit || "");
    const rankTier = Number(row?.rank_tier);
    const rankScore = Number(row?.rank_score);
    const nutrientValues = [row?.energy_kcal_reference, row?.protein_grams_reference, row?.carbohydrate_grams_reference, row?.fat_grams_reference]
      .map(Number);
    if (!['custom_food', 'generic_food', 'off_branded_food'].includes(resultType) || !sourceId || !displayName || row?.loggable !== true) return false;
    if (!Number.isFinite(referenceAmount) || referenceAmount <= 0 || !PHASE4_SLICE3_UNITS.includes(referenceUnit)) return false;
    if (!Number.isInteger(rankTier) || !Number.isFinite(rankScore) || !row?.cursor_name || !row?.cursor_source || !row?.cursor_id) return false;
    if (nutrientValues.some((value) => !Number.isFinite(value) || value < 0)) return false;
    if (resultType === 'generic_food' && !['reviewed', 'verified'].includes(String(row?.quality_status || ''))) return false;
    if (resultType === 'off_branded_food') {
      if (String(row?.source_provider || '') !== 'open_food_facts') return false;
      if (!['complete', 'reviewed'].includes(String(row?.quality_status || ''))) return false;
      if (!['per_100_g', 'per_100_ml'].includes(basis) || referenceAmount !== 100) return false;
      if ((basis === 'per_100_g' && referenceUnit !== 'g') || (basis === 'per_100_ml' && referenceUnit !== 'ml')) return false;
    }
    return true;
  }

  function mapUnifiedSearchResult(row) {
    if (!isSafeUnifiedSearchResult(row)) return null;
    const resultType = String(row.result_type);
    return {
      result_type: resultType,
      source_id: String(row.source_id),
      id: String(row.source_id),
      source_provider: String(row.source_provider || ''),
      barcode: row.barcode || null,
      display_name: String(row.display_name).trim(),
      name: String(row.display_name).trim(),
      brand: String(row.brand || '').trim() || null,
      catalog_scope: resultType === 'custom_food' ? 'custom' : resultType === 'generic_food' ? 'canonical' : 'off_branded',
      nutrition_basis: String(row.nutrition_basis || ''),
      reference_amount: Number(row.reference_amount),
      reference_unit: String(row.reference_unit),
      reference_mass_grams: null,
      reference_volume_ml: null,
      density_g_per_ml: null,
      energy_kcal: Number(row.energy_kcal_reference),
      protein_grams: Number(row.protein_grams_reference),
      carbohydrate_grams: Number(row.carbohydrate_grams_reference),
      fat_grams: Number(row.fat_grams_reference),
      fiber_grams: row.fiber_grams_reference === null || row.fiber_grams_reference === undefined ? null : Number(row.fiber_grams_reference),
      quality_status: String(row.quality_status || ''),
      loggable: true,
      status: 'active',
      metadata: resultType === 'generic_food' && language() === 'nl' ? { dutch_display_label: String(row.display_name).trim() } : {},
      rank_tier: Number(row.rank_tier),
      rank_score: Number(row.rank_score),
      cursor_name: String(row.cursor_name || ''),
      cursor_source: String(row.cursor_source || resultType),
      cursor_id: String(row.cursor_id || row.source_id)
    };
  }

  function shouldSupplementProvider(query, items = slice3State.search.items) {
    const normalizedQuery = normalizedSearchQuery(query);
    return providerSearchAllowed()
      && normalizedQuery.length >= 3
      && normalizedQuery.length <= 80
      && items.length < PHASE4_LOCAL_RESULTS_BEFORE_PROVIDER;
  }

  function providerResultRow(candidate) {
    const fiber = candidate.fiber === null || candidate.fiber === undefined ? "" : ` | ${text("fiber")} ${formatNumber(candidate.fiber, 1)}g`;
    return `
      <article class="phase4-s3-search-row">
        <div class="phase4-s3-search-head"><div><strong>${escapeHTML(candidate.name || "-")}</strong>${candidate.brand ? `<br><small>${escapeHTML(candidate.brand)}</small>` : ""}</div><button class="phase4-s3-gold" data-phase4-s3-select-provider="${escapeHTML(candidate.candidate_id)}" type="button" ${slice3State.providerSearch.lookupStatus === "loading" ? "disabled" : ""}>${escapeHTML(text("select"))}</button></div>
        <small>${escapeHTML(`100 g | ${formatNumber(candidate.kcal, 1)} kcal | P ${formatNumber(candidate.protein, 1)}g | C ${formatNumber(candidate.carbohydrates, 1)}g | F ${formatNumber(candidate.fat, 1)}g${fiber}`)}</small>
        <small class="phase4-s3-provider-source">${escapeHTML(text("providerAttribution"))}</small>
      </article>
    `;
  }

  function providerSearchMarkup() {
    if (!providerSearchAllowed()) return "";
    const provider = slice3State.providerSearch;
    const currentQuery = normalizedSearchQuery(slice3State.search.query);
    const queryReady = currentQuery.length >= 3 && currentQuery.length <= 80;
    const results = provider.items.length
      ? `<div class="phase4-s3-search-list" aria-live="polite">${provider.items.map(providerResultRow).join("")}</div>`
      : "";
    const status = provider.status === "scheduled" || provider.status === "loading"
      ? `<p class="phase4-s3-feedback" aria-live="polite">${escapeHTML(text("providerSearchLoading"))}</p>`
      : provider.status === "error"
        ? `<div class="phase4-s3-state error" aria-live="polite"><span>${escapeHTML(provider.error)}</span><button class="secondary-btn" data-phase4-s3-provider-retry type="button">${escapeHTML(text("retry"))}</button></div>`
        : "";
    const lookupFeedback = provider.lookupStatus === "loading"
      ? `<p class="phase4-s3-feedback" aria-live="polite">${escapeHTML(text("providerLookupLoading"))}</p>`
      : provider.lookupStatus === "error"
        ? `<p class="phase4-s3-feedback error" aria-live="polite">${escapeHTML(provider.error)}</p>`
        : "";
    if ((!queryReady || provider.status === "idle" || provider.status === "ready") && !results && !lookupFeedback) return "";
    return `
      <section class="phase4-s3-provider" aria-label="${escapeHTML(text("providerResults"))}">
        <div class="phase4-s3-provider-head"><strong>${escapeHTML(text("providerResults"))}</strong></div>
        ${results}
        ${status}
        ${lookupFeedback}
        ${provider.hasMore ? `<button class="secondary-btn" data-phase4-s3-provider-more type="button" ${provider.status === "loading" ? "disabled" : ""}>${escapeHTML(text("loadMore"))}</button>` : ""}
      </section>
    `;
  }

  function localSearchResultsMarkup() {
    const search = slice3State.search;
    const provider = slice3State.providerSearch;
    const query = normalizedSearchQuery(search.query);
    const queryReady = query.length >= 3 && query.length <= 80 && providerSearchAllowed();
    const providerExpected = queryReady && shouldSupplementProvider(query);
    const providerSettled = !providerExpected || provider.status === "ready" || provider.status === "error";
    const combinedEmpty = search.status === "ready" && !search.items.length && providerSettled && !provider.items.length;
    let results = "";
    if (search.status === "loading" && !search.items.length) results = `<div class="phase4-s3-state" aria-live="polite">${escapeHTML(text("searchLoading"))}</div>`;
    else if (search.status === "error" && !search.items.length) results = `<div class="phase4-s3-state error" aria-live="polite"><span>${escapeHTML(search.error)}</span><button class="secondary-btn" data-phase4-s3-retry-search type="button">${escapeHTML(text("retry"))}</button></div>`;
    else if (combinedEmpty) results = `<div class="phase4-s3-state" aria-live="polite"><strong>${escapeHTML(text("noFoods"))}</strong></div>`;
    else if (search.items.length) results = `
      ${searchResultGroup(text("myFoodsResults"), search.items.filter((food) => food.result_type === "custom_food"))}
      ${searchResultGroup(text("productResults"), search.items.filter((food) => food.result_type === "off_branded_food"))}
      ${searchResultGroup(text("catalogResults"), search.items.filter((food) => food.result_type === "generic_food"))}
      ${search.rejectedCount ? `<p class="phase4-s3-feedback error">${escapeHTML(text("unexpectedResult"))}</p>` : ""}
      ${search.status === "error" ? `<p class="phase4-s3-feedback error">${escapeHTML(search.error)}</p>` : ""}
      ${search.hasMore || search.status === "loading" ? `<button class="secondary-btn" data-phase4-s3-more-search type="button" ${search.status === "loading" ? "disabled" : ""}>${escapeHTML(search.status === "loading" ? text("searchLoading") : text("loadMore"))}</button>` : ""}
    `;
    return results;
  }

  function searchDialog() {
    const search = slice3State.search;
    const body = `
      <div class="phase4-s3-search-fixed">
        <form id="phase4Slice3SearchForm" class="phase4-s3-search-form" role="search"><label class="field"><span class="sr-only">${escapeHTML(text("searchFood"))}</span><input name="query" type="search" value="${escapeHTML(search.query)}" placeholder="${escapeHTML(text("searchPlaceholder"))}" autocomplete="off"></label><button class="phase4-s3-gold" type="submit">${escapeHTML(text("search"))}</button></form>
        ${feedbackMarkup()}
      </div>
      <div class="phase4-s3-search-results">
        <div id="phase4Slice3LocalSearchResults">${localSearchResultsMarkup()}</div>
        <div id="phase4Slice3ProviderSearchResults">${providerSearchMarkup()}</div>
      </div>
      <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" data-phase4-s3-scan-barcode type="button">${escapeHTML(text("scanBarcode"))}</button><button class="secondary-btn" data-phase4-s3-custom type="button">${escapeHTML(text("createCustom"))}</button></div>
    `;
    return dialogFrame(text("searchFood"), body, text(slice3State.portal.meal), "phase4-s3-search-sheet");
  }

  function scannerDialog() {
    const scanner = slice3State.scanner;
    const cameraVisible = ["loading", "ready"].includes(scanner.status);
    const customAction = scanner.allowCustom
      ? `<button class="phase4-s3-gold" data-phase4-s3-custom-barcode type="button">${escapeHTML(text("createCustomWithBarcode"))}</button>`
      : "";
    const body = `
      <div class="phase4-s3-scanner">
        <p class="phase4-s3-muted">${escapeHTML(text("scanBarcodeIntro"))}</p>
        <div class="phase4-s3-camera" ${cameraVisible ? "" : "hidden"}>
          <video id="phase4Slice3ScannerVideo" playsinline muted aria-label="${escapeHTML(text("scanBarcode"))}"></video>
          <span class="phase4-s3-camera-guide" aria-hidden="true"></span>
        </div>
        <p class="phase4-s3-feedback ${scanner.status === "error" ? "error" : ""}" data-phase4-s3-scanner-status aria-live="polite">${escapeHTML(scannerStatusMessage())}</p>
        <div class="phase4-s3-camera-actions">
          <button class="phase4-s3-gold" data-phase4-s3-start-camera type="button" ${["loading", "ready", "lookup"].includes(scanner.status) ? "hidden" : ""}>${escapeHTML(text("startCamera"))}</button>
          <button class="secondary-btn" data-phase4-s3-stop-camera type="button" ${["loading", "ready"].includes(scanner.status) ? "" : "hidden"}>${escapeHTML(text("stopCamera"))}</button>
        </div>
        <form id="phase4Slice3BarcodeForm" class="phase4-s3-manual" novalidate>
          <label class="field"><span>${escapeHTML(text("manualBarcode"))}</span><span class="phase4-s3-manual-row"><input name="barcode" inputmode="numeric" maxlength="18" value="${escapeHTML(scanner.barcode)}" placeholder="${escapeHTML(text("barcodePlaceholder"))}" autocomplete="off" required><button class="secondary-btn" type="submit" ${scanner.status === "lookup" ? "disabled" : ""}>${escapeHTML(text("lookupBarcode"))}</button></span></label>
        </form>
        <div class="phase4-s3-dialog-actions">${customAction}<button class="secondary-btn" data-phase4-s3-back-search type="button">${escapeHTML(text("back"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("close"))}</button></div>
      </div>
    `;
    return dialogFrame(text("scanBarcodeTitle"), body, text(slice3State.portal.meal), "phase4-s3-scan-sheet");
  }

  function renderSearchResults() {
    const portal = document.getElementById("phase4Slice3Portal");
    const localResults = portal?.querySelector("#phase4Slice3LocalSearchResults");
    const providerResults = portal?.querySelector("#phase4Slice3ProviderSearchResults");
    if (!localResults || !providerResults) return;
    localResults.innerHTML = localSearchResultsMarkup();
    providerResults.innerHTML = providerSearchMarkup();
  }

  function clearProviderSearchResults() {
    const providerResults = document.querySelector("#phase4Slice3ProviderSearchResults");
    if (providerResults?.hasChildNodes()) providerResults.replaceChildren();
  }

  function searchRow(food) {
    const offProduct = food.result_type === "off_branded_food";
    const basis = food.nutrition_basis === "per_100_ml" ? text("per100ml") : food.nutrition_basis === "per_100_g" ? text("per100g") : text("reference", { amount: formatNumber(food.reference_amount, 3), unit: unitLabel(food.reference_unit) });
    const action = offProduct ? text("offInspect") : text("select");
    return `
      <article class="phase4-s3-search-row${offProduct ? " off" : ""}">
        <div class="phase4-s3-search-head"><div><strong>${escapeHTML(displayFoodName(food))}</strong>${food.brand ? `<br><small>${escapeHTML(food.brand)}</small>` : ""}</div><button class="phase4-s3-gold" data-phase4-s3-select-food="${escapeHTML(searchResultKey(food))}" type="button">${escapeHTML(action)}</button></div>
        <div class="phase4-s3-search-meta"><small>${escapeHTML(basis)}</small>${offProduct ? `<small class="phase4-s3-source-label">${escapeHTML(text("offSource"))}</small>` : ""}</div>
        <small>${escapeHTML(`${formatNumber(food.energy_kcal, 1)} kcal | P ${formatNumber(food.protein_grams, 1)}g | C ${formatNumber(food.carbohydrate_grams, 1)}g | F ${formatNumber(food.fat_grams, 1)}g`)}</small>
      </article>
    `;
  }

  function searchResultGroup(title, items) {
    if (!items.length) return "";
    return `<section class="phase4-s3-search-group" aria-label="${escapeHTML(title)}"><p class="eyebrow">${escapeHTML(title)}</p><div class="phase4-s3-search-list" aria-live="polite">${items.map(searchRow).join("")}</div></section>`;
  }

  async function searchFoods({ reset = true, preserveSearchFocus = false } = {}) {
    if (!slice3State.userId || !supabaseClient) return;
    cancelLocalSearchDebounce();
    const search = slice3State.search;
    const requestQuery = normalizedSearchQuery(search.query);
    const requestToken = search.requestToken + 1;
    search.requestToken = requestToken;
    search.status = "loading";
    search.error = "";
    if (reset) {
      search.afterRank = null;
      search.afterScore = null;
      search.afterName = null;
      search.afterSource = null;
      search.afterId = null;
      search.hasMore = false;
      search.rejectedCount = 0;
    }
    renderPortal({ preserveSearchFocus });
    try {
      const { data, error } = await supabaseClient.rpc("fmz_phase4_search_nutrition_catalog", {
        p_query: requestQuery || null,
        p_locale: language(),
        p_page_size: PHASE4_SLICE3_SEARCH_PAGE_SIZE,
        p_after_rank: reset ? null : search.afterRank,
        p_after_score: reset ? null : search.afterScore,
        p_after_name: reset ? null : search.afterName,
        p_after_source: reset ? null : search.afterSource,
        p_after_id: reset ? null : search.afterId
      });
      if (error) throw error;
      if (search.requestToken !== requestToken || slice3State.portal.type !== "search" || normalizedSearchQuery(search.query) !== requestQuery) return;
      const rows = Array.isArray(data) ? data : [];
      const safeRows = rows.map(mapUnifiedSearchResult).filter(Boolean);
      const map = new Map((reset ? [] : search.items).map((food) => [searchResultKey(food), food]));
      safeRows.forEach((food) => map.set(searchResultKey(food), food));
      search.items = Array.from(map.values());
      search.rejectedCount += rows.length - safeRows.length;
      const last = rows[rows.length - 1];
      search.afterRank = last?.rank_tier ?? null;
      search.afterScore = last?.rank_score ?? null;
      search.afterName = last?.cursor_name || null;
      search.afterSource = last?.cursor_source || null;
      search.afterId = last?.cursor_id || null;
      search.hasMore = rows.length === PHASE4_SLICE3_SEARCH_PAGE_SIZE;
      search.status = "ready";
      if (reset && shouldSupplementProvider(requestQuery, search.items)) scheduleProviderSearch(requestQuery);
    } catch (error) {
      if (search.requestToken !== requestToken || slice3State.portal.type !== "search" || normalizedSearchQuery(search.query) !== requestQuery) return;
      search.status = "error";
      search.error = errorMessage(error, "search");
      if (reset && shouldSupplementProvider(requestQuery, [])) scheduleProviderSearch(requestQuery);
    }
    renderPortal({ preserveSearchFocus });
  }

  function scheduleLocalSearch(query) {
    const normalizedQuery = normalizedSearchQuery(query);
    cancelLocalSearchDebounce();
    slice3State.search.status = "scheduled";
    slice3State.search.error = "";
    localSearchDebounceTimer = window.setTimeout(() => {
      localSearchDebounceTimer = null;
      if (slice3State.portal.type !== "search" || normalizedSearchQuery(slice3State.search.query) !== normalizedQuery) return;
      searchFoods({ reset: true, preserveSearchFocus: true });
    }, PHASE4_LOCAL_SEARCH_DEBOUNCE_MS);
  }

  function scheduleProviderSearch(query) {
    const normalizedQuery = normalizedSearchQuery(query);
    if (!providerSearchAllowed() || normalizedQuery.length < 3 || normalizedQuery.length > 80) return;
    const provider = slice3State.providerSearch;
    if (provider.query === normalizedQuery && ["scheduled", "loading", "ready"].includes(provider.status)) return;
    cancelProviderSearchDebounce();
    provider.query = normalizedQuery;
    provider.status = "scheduled";
    provider.error = "";
    provider.page = 1;
    provider.hasMore = false;
    providerSearchDebounceTimer = window.setTimeout(() => {
      providerSearchDebounceTimer = null;
      if (slice3State.portal.type !== "search" || normalizedSearchQuery(slice3State.search.query) !== normalizedQuery) return;
      searchProviderFoods({ reset: true });
    }, PHASE4_PROVIDER_SEARCH_DEBOUNCE_MS);
  }

  async function searchProviderFoods({ reset = true } = {}) {
    const query = normalizedSearchQuery(slice3State.search.query);
    if (!providerSearchAllowed() || query.length < 3 || query.length > 80) return;
    const provider = slice3State.providerSearch;
    const page = reset ? 1 : Math.min(PHASE4_PROVIDER_MAX_PAGES, provider.page + 1);
    if (provider.status === "loading" && provider.query === query && provider.page === page) return;
    const fingerprint = JSON.stringify([query, language(), providerCountryCode(), page, PHASE4_PROVIDER_SEARCH_PAGE_SIZE]);
    if (!provider.requestId || provider.submittedFingerprint !== fingerprint) provider.requestId = uuid();
    provider.submittedFingerprint = fingerprint;
    provider.query = query;
    provider.page = page;
    provider.status = "loading";
    provider.error = "";
    provider.lookupStatus = "idle";
    if (reset) {
      provider.items = [];
      provider.hasMore = false;
    }
    const requestToken = provider.requestToken + 1;
    provider.requestToken = requestToken;
    renderPortal({ preserveSearchFocus: true });
    try {
      const data = await providerRequest("search", {
        query,
        locale: language(),
        country_code: providerCountryCode(),
        page_number: page,
        page_size: PHASE4_PROVIDER_SEARCH_PAGE_SIZE,
        request_id: provider.requestId
      });
      if (provider !== slice3State.providerSearch || provider.requestToken !== requestToken || slice3State.portal.type !== "search" || normalizedSearchQuery(slice3State.search.query) !== query) return;
      const rows = Array.isArray(data?.results) ? data.results.filter((candidate) => candidate?.candidate_id && candidate?.candidate_token) : [];
      const map = new Map((reset ? [] : provider.items).map((candidate) => [candidate.candidate_id, candidate]));
      rows.forEach((candidate) => map.set(candidate.candidate_id, candidate));
      provider.items = Array.from(map.values());
      provider.hasMore = rows.length === PHASE4_PROVIDER_SEARCH_PAGE_SIZE && page < PHASE4_PROVIDER_MAX_PAGES;
      provider.status = "ready";
    } catch (error) {
      if (provider !== slice3State.providerSearch || provider.requestToken !== requestToken || slice3State.portal.type !== "search" || normalizedSearchQuery(slice3State.search.query) !== query) return;
      provider.status = "error";
      provider.error = providerErrorMessage(error);
    }
    renderPortal({ preserveSearchFocus: true });
  }

  async function selectProviderFood(candidateId) {
    const provider = slice3State.providerSearch;
    const candidate = provider.items.find((entry) => entry.candidate_id === candidateId);
    if (!candidate?.candidate_token || provider.lookupStatus === "loading") return;
    if (provider.lookupCandidateId !== candidateId || !provider.lookupRequestId) {
      provider.lookupCandidateId = candidateId;
      provider.lookupRequestId = uuid();
    }
    const requestToken = provider.requestToken + 1;
    provider.requestToken = requestToken;
    provider.lookupStatus = "loading";
    provider.error = "";
    renderPortal();
    try {
      const data = await providerRequest("lookup", {
        candidate_token: candidate.candidate_token,
        request_id: provider.lookupRequestId
      });
      if (provider.requestToken !== requestToken || slice3State.portal.type !== "search") return;
      const verified = data?.result;
      if (!verified?.candidate_id || verified.candidate_id !== candidateId || !verified.candidate_token) throw new Error("provider lookup response invalid");
      openProviderEntry(verified, verified.candidate_token, slice3State.portal.meal, slice3State.portal.opener, slice3State.portal.item);
    } catch (error) {
      if (provider.requestToken !== requestToken || slice3State.portal.type !== "search") return;
      provider.lookupStatus = "error";
      provider.error = providerErrorMessage(error);
      renderPortal();
    }
  }

  function selectSearchFood(resultKey) {
    const food = slice3State.search.items.find((entry) => searchResultKey(entry) === resultKey);
    if (!food) return;
    if (food.result_type === "off_branded_food") {
      openPortal("off", slice3State.portal.opener, { food, meal: slice3State.portal.meal, item: slice3State.portal.item });
      return;
    }
    openEntry(food, slice3State.portal.meal, slice3State.portal.opener, slice3State.portal.item);
  }

  function offProductDialog() {
    const food = slice3State.portal.food || {};
    const basis = food.nutrition_basis === "per_100_ml" ? text("per100ml") : text("per100g");
    const body = `
      <div><strong>${escapeHTML(displayFoodName(food))}</strong>${food.brand ? `<br><small class="phase4-s3-muted">${escapeHTML(food.brand)}</small>` : ""}</div>
      <div class="phase4-s3-detail-grid">
        <div><span>${escapeHTML(basis)}</span><strong>${escapeHTML(`${formatNumber(food.energy_kcal, 1)} kcal`)}</strong></div>
        <div><span>${escapeHTML(text("protein"))}</span><strong>${escapeHTML(`${formatNumber(food.protein_grams, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(text("carbohydrate"))}</span><strong>${escapeHTML(`${formatNumber(food.carbohydrate_grams, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(text("fat"))}</span><strong>${escapeHTML(`${formatNumber(food.fat_grams, 1)} g`)}</strong></div>
      </div>
      <p class="phase4-s3-source-label">${escapeHTML(text("offAttribution"))}</p>
      <p class="phase4-s3-off-note">${escapeHTML(text("offUnitOnly", { unit: unitLabel(food.reference_unit) }))}</p>
      <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" data-phase4-s3-use-off type="button">${escapeHTML(text("offUseProduct"))}</button><button class="secondary-btn" data-phase4-s3-back-off type="button">${escapeHTML(text("back"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("close"))}</button></div>
    `;
    return dialogFrame(text("offInspectTitle"), body, text("offSource"));
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
    slice3State.submission = { kind, itemId: uuid(), requestId: uuid(), submittedFingerprint: "", inFlight: false };
  }

  function openEntry(food, meal, opener, item = null) {
    resetSubmission(item ? "edit" : "new");
    slice3State.portions = { status: "idle", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    openPortal("entry", opener, { food, meal, item });
    loadPortions(food.id);
  }

  function openProviderEntry(candidate, candidateToken, meal, opener, item = null) {
    resetSubmission(item ? "provider-edit" : "provider-new");
    slice3State.portions = { status: "ready", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    openPortal("entry", opener, {
      food: null,
      meal,
      item,
      providerCandidate: candidate || null,
      candidateToken: candidateToken || ""
    });
  }

  function openOffEntry(food, meal, opener, item = null) {
    resetSubmission(item ? "off-edit" : "off-new");
    slice3State.portions = { status: "ready", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    openPortal("entry", opener, { food, meal, item, offProduct: true });
  }

  function openTransientOffEntry(candidate, candidateToken, meal, opener, item = null) {
    resetSubmission(item ? "transient-off-edit" : "transient-off-new");
    slice3State.portions = { status: "ready", items: [], error: "", requestToken: slice3State.portions.requestToken + 1 };
    const food = candidate ? transientCandidateFood(candidate) : {
      result_type: "transient_off_food",
      source_provider: "open_food_facts",
      source_id: item?.metadata?.candidate_id || item?.provider_food_id_snapshot || "",
      id: item?.metadata?.candidate_id || item?.provider_food_id_snapshot || "",
      display_name: item?.food_name_snapshot || "",
      name: item?.food_name_snapshot || "",
      brand: item?.brand_snapshot || "",
      reference_amount: item?.reference_amount_snapshot || 100,
      reference_unit: item?.reference_unit_snapshot || item?.consumed_unit || "g",
      nutrition_basis: item?.metadata?.reference_basis || (item?.reference_unit_snapshot === "ml" ? "per_100_ml" : "per_100_g"),
      metadata: { transient_off: true }
    };
    openPortal("entry", opener, {
      food,
      meal,
      item,
      offProduct: true,
      transientOff: true,
      providerCandidate: candidate || null,
      candidateToken: candidateToken || ""
    });
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
    const candidate = slice3State.portal.providerCandidate;
    const offEntry = slice3State.portal.offProduct || isOffSnapshot(item);
    const providerEntry = Boolean(candidate) || isProviderSnapshot(item);
    if (offEntry) {
      const name = food?.id ? displayFoodName(food) : displayFoodName(item);
      const brand = food?.brand || item?.brand_snapshot || "";
      const unit = food?.reference_unit || item?.reference_unit_snapshot || item?.consumed_unit || "g";
      const body = `
        <div><strong>${escapeHTML(name)}</strong>${brand ? `<br><small class="phase4-s3-muted">${escapeHTML(brand)}</small>` : ""}</div>
        <form id="phase4Slice3EntryForm" class="phase4-s3-form" novalidate data-off-entry="true">
          <div class="phase4-s3-form-grid">
            <label class="field"><span>${escapeHTML(text("meal"))}</span><select name="meal">${PHASE4_SLICE3_MEALS.map((meal) => `<option value="${meal}" ${meal === (item?.meal_moment || slice3State.portal.meal) ? "selected" : ""}>${escapeHTML(text(meal))}</option>`).join("")}</select></label>
            <label class="field"><span>${escapeHTML(text("amount"))}</span><span class="phase4-s3-search-form"><input name="quantity" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" required value="${escapeHTML(item?.consumed_quantity ?? 100)}" autocomplete="off"><strong aria-hidden="true">${escapeHTML(unitLabel(unit))}</strong></span></label>
            <input name="selection" type="hidden" value="direct:${escapeHTML(unit)}">
            <label class="field wide"><span>${escapeHTML(text("notes"))}</span><textarea name="notes" maxlength="1000" rows="3">${escapeHTML(item?.notes || "")}</textarea></label>
          </div>
          <p class="phase4-s3-muted">${escapeHTML(text("offUnitOnly", { unit: unitLabel(unit) }))}</p>
          <p class="phase4-s3-provider-source">${escapeHTML(text("offAttribution"))}</p>
          ${isOffSnapshot(item) ? `<p class="phase4-s3-muted">${escapeHTML(text("offHistorical"))}</p>` : ""}
          <p class="phase4-s3-muted">${escapeHTML(text("serverCalculated"))}</p>
          ${feedbackMarkup()}
          <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" type="submit">${escapeHTML(text(item ? "saveEdit" : "saveEntry"))}</button><button class="secondary-btn" data-phase4-s3-change-food type="button">${escapeHTML(text("changeFood"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("cancel"))}</button></div>
        </form>
      `;
      return dialogFrame(text(item ? "editEntryTitle" : "entryTitle"), body, text(item?.meal_moment || slice3State.portal.meal));
    }
    if (providerEntry) {
      const name = candidate?.name || displayFoodName(item);
      const brand = candidate?.brand || item?.brand_snapshot || "";
      const body = `
        <div><strong>${escapeHTML(name)}</strong>${brand ? `<br><small class="phase4-s3-muted">${escapeHTML(brand)}</small>` : ""}</div>
        <form id="phase4Slice3EntryForm" class="phase4-s3-form" novalidate data-provider-entry="true">
          <div class="phase4-s3-form-grid">
            <label class="field"><span>${escapeHTML(text("meal"))}</span><select name="meal">${PHASE4_SLICE3_MEALS.map((meal) => `<option value="${meal}" ${meal === (item?.meal_moment || slice3State.portal.meal) ? "selected" : ""}>${escapeHTML(text(meal))}</option>`).join("")}</select></label>
            <label class="field"><span>${escapeHTML(text("amount"))}</span><span class="phase4-s3-search-form"><input name="quantity" type="number" inputmode="decimal" min="0.001" max="100000" step="0.001" required value="${escapeHTML(item?.consumed_quantity ?? 100)}" autocomplete="off"><strong aria-hidden="true">g</strong></span></label>
            <input name="selection" type="hidden" value="direct:g">
            <label class="field wide"><span>${escapeHTML(text("notes"))}</span><textarea name="notes" maxlength="1000" rows="3">${escapeHTML(item?.notes || "")}</textarea></label>
          </div>
          <p class="phase4-s3-muted">${escapeHTML(text("providerGramsOnly"))}</p>
          <p class="phase4-s3-provider-source">${escapeHTML(text("providerAttribution"))}</p>
          ${isProviderSnapshot(item) && !candidate ? `<p class="phase4-s3-muted">${escapeHTML(text("providerHistorical"))}</p>` : ""}
          <p class="phase4-s3-muted">${escapeHTML(text("serverCalculated"))}</p>
          ${feedbackMarkup()}
          <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" type="submit">${escapeHTML(text(item ? "saveEdit" : "saveEntry"))}</button><button class="secondary-btn" data-phase4-s3-change-food type="button">${escapeHTML(text("changeFood"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("cancel"))}</button></div>
        </form>
      `;
      return dialogFrame(text(item ? "editEntryTitle" : "entryTitle"), body, text(item?.meal_moment || slice3State.portal.meal));
    }
    const selection = entrySelection(food, item);
    const unitOptions = directUnits(food).map((unit) => `<option value="direct:${escapeHTML(unit)}" ${selection === `direct:${unit}` ? "selected" : ""}>${escapeHTML(text("directUnit", { unit: unitLabel(unit) }))}</option>`).join("");
    const portionOptions = slice3State.portions.items.map((portion) => `<option value="portion:${escapeHTML(portion.id)}" ${selection === `portion:${portion.id}` ? "selected" : ""}>${escapeHTML(text("portion", { label: portion.label, amount: formatNumber(portion.amount, 3), unit: unitLabel(portion.unit) }))}</option>`).join("");
    const body = `
      <div><strong>${escapeHTML(food?.id ? displayFoodName(food) : displayFoodName(item))}</strong>${food.brand ? `<br><small class="phase4-s3-muted">${escapeHTML(food.brand)}</small>` : ""}</div>
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

  function setSubmissionBusy(form, busy) {
    slice3State.submission.inFlight = busy;
    const submit = form?.querySelector?.('button[type="submit"]');
    if (submit) submit.disabled = busy;
  }

  function providerEntryFingerprint(payload, original, candidate) {
    return JSON.stringify([
      original?.id || null,
      candidate?.candidate_id || original?.provider_food_id_snapshot || null,
      payload.meal,
      payload.quantity,
      "g",
      payload.notes || null
    ]);
  }

  function offEntryFingerprint(payload, original, food) {
    return JSON.stringify([
      original?.id || null,
      food?.source_id || food?.id || original?.metadata?.candidate_id || original?.metadata?.off_product_id || null,
      payload.meal,
      payload.quantity,
      payload.consumedUnit,
      payload.notes || null
    ]);
  }

  function acceptAuthoritativeDay(day, noticeKey) {
    if (!day || day.log_date !== slice3State.selectedDate || !Array.isArray(day.items) || !day.totals) throw new Error("authoritative Nutrition day payload unavailable");
    slice3State.day = { status: "ready", value: day, error: "", requestToken: slice3State.day.requestToken + 1 };
    slice3State.notice = text(noticeKey);
    slice3State.submission = { kind: "", itemId: "", requestId: "", submittedFingerprint: "", inFlight: false };
    closePortal();
    renderRoot();
    void hydrateDutchDisplayLabels(day);
  }

  async function saveProviderEntry(form, payload, original) {
    const candidate = slice3State.portal.providerCandidate;
    const candidateToken = slice3State.portal.candidateToken;
    if (!candidate && !isProviderSnapshot(original)) return;
    if (original && !isProviderSnapshot(original)) {
      showFeedback(text("providerUnavailable"), "error");
      return;
    }
    if (candidate && !candidateToken) {
      showFeedback(text("providerCandidateInvalid"), "error");
      return;
    }
    const kind = original ? "provider-edit" : "provider-new";
    const fingerprint = providerEntryFingerprint(payload, original, candidate);
    prepareSubmission(kind, fingerprint);
    if (slice3State.submission.inFlight) return;
    setSubmissionBusy(form, true);
    showFeedback(text("saving"));
    try {
      const body = original
        ? {
            ...(candidateToken ? { candidate_token: candidateToken } : {}),
            original_item_id: original.id,
            replacement_item_id: slice3State.submission.itemId,
            request_id: slice3State.submission.requestId,
            expected_original_updated_at: original.updated_at,
            meal_moment: payload.meal,
            consumed_quantity: payload.quantity,
            consumed_unit: "g",
            notes: payload.notes || null
          }
        : {
            candidate_token: candidateToken,
            item_id: slice3State.submission.itemId,
            request_id: slice3State.submission.requestId,
            log_date: slice3State.selectedDate,
            timezone_name: slice3State.timezoneName,
            timezone_offset_minutes: timezoneOffsetMinutes(slice3State.selectedDate),
            meal_moment: payload.meal,
            consumed_quantity: payload.quantity,
            consumed_unit: "g",
            notes: payload.notes || null,
            consumed_at: localConsumedAt(slice3State.selectedDate)
          };
      const data = await providerRequest(original ? "replace" : "log", body);
      acceptAuthoritativeDay(data?.result?.day, original ? "edited" : "saved");
    } catch (error) {
      const code = String(error?.code || "");
      if (code.includes("request_conflict")) resetSubmission(kind);
      showFeedback(providerErrorMessage(error), "error");
      if (code === "provider_replace_stale") await loadDay(true);
    } finally {
      if (slice3State.portal.type === "entry") setSubmissionBusy(form, false);
    }
  }

  async function saveOffEntry(form, payload, original) {
    if (slice3State.portal.transientOff || isTransientOffSnapshot(original)) {
      return saveTransientOffEntry(form, payload, original);
    }
    const food = slice3State.portal.food || {};
    const offProductId = food.source_id || food.id || original?.metadata?.off_product_id;
    const expectedUnit = food.reference_unit || original?.reference_unit_snapshot;
    if (!offProductId || !["g", "ml"].includes(expectedUnit) || payload.consumedUnit !== expectedUnit) {
      showFeedback(text("offUnavailable"), "error");
      return;
    }
    const kind = original ? "off-edit" : "off-new";
    const fingerprint = offEntryFingerprint(payload, original, { ...food, source_id: offProductId });
    prepareSubmission(kind, fingerprint);
    if (slice3State.submission.inFlight) return;
    setSubmissionBusy(form, true);
    showFeedback(text("saving"));
    try {
      const response = original
        ? await supabaseClient.rpc("fmz_phase4_replace_off_food_log_item", {
            p_original_item_id: original.id,
            p_replacement_item_id: slice3State.submission.itemId,
            p_replacement_request_id: slice3State.submission.requestId,
            p_expected_original_updated_at: original.updated_at,
            p_meal_moment: payload.meal,
            p_off_product_id: offProductId,
            p_consumed_quantity: payload.quantity,
            p_consumed_unit: expectedUnit,
            p_notes: payload.notes || null
          })
        : await supabaseClient.rpc("fmz_phase4_log_off_food_item", {
            p_item_id: slice3State.submission.itemId,
            p_request_id: slice3State.submission.requestId,
            p_log_date: slice3State.selectedDate,
            p_timezone_name: slice3State.timezoneName,
            p_timezone_offset_minutes: timezoneOffsetMinutes(slice3State.selectedDate),
            p_meal_moment: payload.meal,
            p_off_product_id: offProductId,
            p_consumed_quantity: payload.quantity,
            p_consumed_unit: expectedUnit,
            p_notes: payload.notes || null,
            p_consumed_at: localConsumedAt(slice3State.selectedDate)
          });
      if (response.error) throw response.error;
      acceptAuthoritativeDay(response.data?.day, original ? "edited" : "saved");
    } catch (error) {
      const code = String(error?.code || "");
      if (code === "23505") resetSubmission(kind);
      showFeedback(errorMessage(error), "error");
      if (code === "40001") await loadDay(true);
    } finally {
      if (slice3State.portal.type === "entry") setSubmissionBusy(form, false);
    }
  }

  async function saveTransientOffEntry(form, payload, original) {
    const candidate = slice3State.portal.providerCandidate;
    const candidateToken = slice3State.portal.candidateToken;
    const expectedUnit = candidate?.reference_unit || slice3State.portal.food?.reference_unit || original?.reference_unit_snapshot;
    if (!isTransientOffSnapshot(original) && original && !candidateToken) {
      showFeedback(text("providerCandidateInvalid"), "error");
      return;
    }
    if (!original && (!candidate || !candidateToken)) {
      showFeedback(text("providerCandidateInvalid"), "error");
      return;
    }
    if (!["g", "ml"].includes(expectedUnit) || payload.consumedUnit !== expectedUnit) {
      showFeedback(text("offUnavailable"), "error");
      return;
    }
    const kind = original ? "transient-off-edit" : "transient-off-new";
    const fingerprint = offEntryFingerprint(payload, original, slice3State.portal.food || {});
    prepareSubmission(kind, fingerprint);
    if (slice3State.submission.inFlight) return;
    setSubmissionBusy(form, true);
    showFeedback(text("saving"));
    try {
      const body = original
        ? {
            ...(candidateToken ? { candidate_token: candidateToken } : {}),
            original_item_id: original.id,
            replacement_item_id: slice3State.submission.itemId,
            request_id: slice3State.submission.requestId,
            expected_original_updated_at: original.updated_at,
            meal_moment: payload.meal,
            consumed_quantity: payload.quantity,
            consumed_unit: expectedUnit,
            notes: payload.notes || null
          }
        : {
            candidate_token: candidateToken,
            item_id: slice3State.submission.itemId,
            request_id: slice3State.submission.requestId,
            log_date: slice3State.selectedDate,
            timezone_name: slice3State.timezoneName,
            timezone_offset_minutes: timezoneOffsetMinutes(slice3State.selectedDate),
            meal_moment: payload.meal,
            consumed_quantity: payload.quantity,
            consumed_unit: expectedUnit,
            notes: payload.notes || null,
            consumed_at: localConsumedAt(slice3State.selectedDate)
          };
      const data = await providerRequest(original ? "off-replace" : "off-log", body);
      acceptAuthoritativeDay(data?.result?.day, original ? "edited" : "saved");
    } catch (error) {
      const code = String(error?.code || "");
      if (code.includes("request_conflict")) resetSubmission(kind);
      showFeedback(providerErrorMessage(error), "error");
      if (code.includes("stale")) await loadDay(true);
    } finally {
      if (slice3State.portal.type === "entry") setSubmissionBusy(form, false);
    }
  }

  async function saveEntry(form) {
    const food = slice3State.portal.food;
    const original = slice3State.portal.item;
    if (!supabaseClient) return;
    const payload = entryPayload(form);
    const errors = validateEntry(payload);
    if (errors.length) {
      showFeedback(errors.join(" "), "error");
      return;
    }
    if (slice3State.portal.offProduct) return saveOffEntry(form, payload, original);
    if (slice3State.portal.providerCandidate || (isProviderSnapshot(original) && !food?.id)) return saveProviderEntry(form, payload, original);
    if (!food?.id) return;
    const kind = original ? "edit" : "new";
    const fingerprint = entryFingerprint(payload, food.id, original?.id || null);
    prepareSubmission(kind, fingerprint);
    if (slice3State.submission.inFlight) return;
    setSubmissionBusy(form, true);
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
      acceptAuthoritativeDay(response.data?.day, original ? "edited" : "saved");
    } catch (error) {
      const code = String(error?.code || "");
      const message = errorMessage(error);
      if (code === "23505") resetSubmission(kind);
      showFeedback(message, "error");
      if (code === "40001") loadDay(true);
    } finally {
      if (slice3State.portal.type === "entry") setSubmissionBusy(form, false);
    }
  }

  function findItem(itemId) {
    return (slice3State.day.value?.items || []).find((item) => item.id === itemId) || null;
  }

  function itemDialog() {
    const item = slice3State.portal.item || {};
    const source = isProviderSnapshot(item)
      ? text("providerSource")
      : isOffSnapshot(item)
        ? text("offSource")
        : (item.source_provider_snapshot || "-");
    const body = `
      <div class="phase4-s3-detail-grid">
        <div class="wide"><span>${escapeHTML(text("name"))}</span><strong>${escapeHTML(displayFoodName(item))}</strong></div>
        ${item.brand_snapshot ? `<div class="wide"><span>${escapeHTML(text("brand"))}</span><strong>${escapeHTML(item.brand_snapshot)}</strong></div>` : ""}
        <div><span>${escapeHTML(text("meal"))}</span><strong>${escapeHTML(text(item.meal_moment))}</strong></div>
        <div><span>${escapeHTML(text("amount"))}</span><strong>${escapeHTML(`${formatNumber(item.consumed_quantity, 3)} ${unitLabel(item.consumed_unit)}`)}</strong></div>
        <div><span>${escapeHTML(text("kcal"))}</span><strong>${escapeHTML(`${formatNumber(item.energy_kcal_snapshot, 1)} kcal`)}</strong></div>
        <div><span>${escapeHTML(text("protein"))}</span><strong>${escapeHTML(`${formatNumber(item.protein_grams_snapshot, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(text("carbohydrate"))}</span><strong>${escapeHTML(`${formatNumber(item.carbohydrate_grams_snapshot, 1)} g`)}</strong></div>
        <div><span>${escapeHTML(text("fat"))}</span><strong>${escapeHTML(`${formatNumber(item.fat_grams_snapshot, 1)} g`)}</strong></div>
        ${item.notes ? `<div class="wide"><span>${escapeHTML(text("notes"))}</span><strong>${escapeHTML(item.notes)}</strong></div>` : ""}
        <div class="wide"><span>${escapeHTML(text("sourceSnapshot"))}</span><strong>${escapeHTML(source)}</strong></div>
      </div>
      ${isProviderSnapshot(item) ? `<p class="phase4-s3-muted">${escapeHTML(text("providerHistorical"))}</p>` : ""}
      ${isOffSnapshot(item) ? `<p class="phase4-s3-provider-source">${escapeHTML(text("offAttribution"))}</p><p class="phase4-s3-muted">${escapeHTML(text("offHistorical"))}</p>` : ""}
      ${feedbackMarkup()}
      <div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" data-phase4-s3-edit-item type="button">${escapeHTML(text("edit"))}</button><button class="secondary-btn" data-phase4-s3-remove-item type="button">${escapeHTML(text("remove"))}</button><button class="secondary-btn" data-phase4-s3-close type="button">${escapeHTML(text("close"))}</button></div>
    `;
    return dialogFrame(displayFoodName(item, text("details")), body, text("details"));
  }

  function removeDialog() {
    const item = slice3State.portal.item || {};
    const body = `<p>${escapeHTML(text("removeBody"))}</p><strong>${escapeHTML(displayFoodName(item))}</strong>${feedbackMarkup()}<div class="phase4-s3-dialog-actions"><button class="phase4-s3-gold" data-phase4-s3-confirm-remove type="button">${escapeHTML(text("confirmRemove"))}</button><button class="secondary-btn" data-phase4-s3-back-item type="button">${escapeHTML(text("cancel"))}</button></div>`;
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
    if (isProviderSnapshot(item)) {
      openProviderEntry(null, "", item.meal_moment, opener, item);
      return;
    }
    if (isTransientOffSnapshot(item)) {
      openTransientOffEntry(null, "", item.meal_moment, opener, item);
      return;
    }
    if (isOffSnapshot(item)) {
      openOffEntry({
        id: item.metadata?.off_product_id,
        source_id: item.metadata?.off_product_id,
        result_type: "off_branded_food",
        source_provider: "open_food_facts",
        display_name: item.food_name_snapshot,
        name: item.food_name_snapshot,
        brand: item.brand_snapshot,
        reference_amount: item.reference_amount_snapshot,
        reference_unit: item.reference_unit_snapshot,
        nutrition_basis: item.metadata?.reference_basis,
        metadata: { dutch_display_label: item.metadata?.display_name_nl || "" }
      }, item.meal_moment, opener, item);
      return;
    }
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
    const barcodeField = slice3State.customDraft.barcode
      ? `<label class="field wide"><span>${escapeHTML(text("barcodeLabel"))}</span><input name="barcode" value="${escapeHTML(slice3State.customDraft.barcode)}" readonly></label>`
      : "";
    const body = `
      <form id="phase4Slice3CustomForm" class="phase4-s3-form" novalidate>
        <p class="phase4-s3-muted">${escapeHTML(text("customIntro"))}</p>
        <div class="phase4-s3-form-grid">
          <label class="field wide"><span>${escapeHTML(text("name"))}</span><input name="name" maxlength="240" required autocomplete="off"></label>
          <label class="field wide"><span>${escapeHTML(text("brand"))}</span><input name="brand" maxlength="160" autocomplete="off"></label>
          ${barcodeField}
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
      barcode: normalizeGtin14(data.get("barcode") || slice3State.customDraft.barcode),
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
    return JSON.stringify([payload.name, payload.brand, payload.barcode || null, payload.referenceAmount, payload.referenceUnit, payload.referenceMass, payload.referenceVolume, payload.energy, payload.protein, payload.carbohydrate, payload.fat, payload.fiber]);
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
      const rpcName = payload.barcode ? "fmz_phase4_upsert_custom_food_with_barcode" : "fmz_phase4_upsert_custom_food";
      const rpcPayload = {
        p_food_id: slice3State.customDraft.foodId,
        p_name: payload.name,
        p_brand: payload.brand || null,
        ...(payload.barcode ? { p_barcode: payload.barcode } : {}),
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
      };
      const { data, error } = await supabaseClient.rpc(rpcName, rpcPayload);
      if (error) throw error;
      if (!data?.id) throw new Error("custom food result unavailable");
      slice3State.customDraft = { foodId: "", submittedFingerprint: "", barcode: "" };
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
    if (button.dataset.phase4S3ProviderRetry !== undefined) return searchProviderFoods({ reset: true });
    if (button.dataset.phase4S3ProviderMore !== undefined) return searchProviderFoods({ reset: false });
    if (button.dataset.phase4S3SelectProvider) return selectProviderFood(button.dataset.phase4S3SelectProvider);
    if (button.dataset.phase4S3SelectFood) return selectSearchFood(button.dataset.phase4S3SelectFood);
    if (button.dataset.phase4S3ScanBarcode !== undefined) return openScanner(slice3State.portal.meal, slice3State.portal.opener || button, slice3State.portal.item);
    if (button.dataset.phase4S3StartCamera !== undefined) return startBarcodeScanner();
    if (button.dataset.phase4S3StopCamera !== undefined) return stopBarcodeScanner({ update: true });
    if (button.dataset.phase4S3UseOff !== undefined) {
      if (slice3State.portal.transientOff) return openTransientOffEntry(slice3State.portal.providerCandidate, slice3State.portal.candidateToken, slice3State.portal.meal, slice3State.portal.opener || button, slice3State.portal.item);
      return openOffEntry(slice3State.portal.food, slice3State.portal.meal, slice3State.portal.opener || button, slice3State.portal.item);
    }
    if (button.dataset.phase4S3BackOff !== undefined) return openPortal("search", slice3State.portal.opener || button, { meal: slice3State.portal.meal, item: slice3State.portal.item });
    if (button.dataset.phase4S3Custom !== undefined) {
      slice3State.customDraft = { foodId: uuid(), submittedFingerprint: "", barcode: "" };
      return openPortal("custom", slice3State.portal.opener || button, { meal: slice3State.portal.meal, item: slice3State.portal.item });
    }
    if (button.dataset.phase4S3CustomBarcode !== undefined) {
      slice3State.customDraft = { foodId: uuid(), submittedFingerprint: "", barcode: slice3State.scanner.submittedBarcode };
      return openPortal("custom", slice3State.portal.opener || button, { meal: slice3State.portal.meal, item: slice3State.portal.item });
    }
    if (button.dataset.phase4S3BackSearch !== undefined || button.dataset.phase4S3ChangeFood !== undefined) return openSearch(slice3State.portal.meal, slice3State.portal.opener || button, slice3State.portal.item);
    if (button.dataset.phase4S3EditItem !== undefined) return loadFoodForEdit(slice3State.portal.item, slice3State.portal.opener || button);
    if (button.dataset.phase4S3RemoveItem !== undefined) return openPortal("remove", slice3State.portal.opener || button, { item: slice3State.portal.item, meal: slice3State.portal.meal });
    if (button.dataset.phase4S3BackItem !== undefined) return openPortal("item", slice3State.portal.opener || button, { item: slice3State.portal.item, meal: slice3State.portal.meal });
    if (button.dataset.phase4S3ConfirmRemove !== undefined) return archiveItem();
  }

  function runUnifiedSearch(value, { forceLocal = false } = {}) {
    const rawQuery = String(value || "");
    const query = normalizedSearchQuery(rawQuery);
    const rawChanged = rawQuery !== slice3State.search.query;
    const providerQueryChanged = query !== normalizedSearchQuery(slice3State.search.query);
    if (!rawChanged && !forceLocal) return;
    slice3State.search.query = rawQuery;
    if (providerQueryChanged) {
      slice3State.search.requestToken += 1;
      resetProviderSearch();
      clearProviderSearchResults();
    }
    if (forceLocal) searchFoods({ reset: true, preserveSearchFocus: true });
    else if (providerQueryChanged) scheduleLocalSearch(query);
  }

  function handleInput(event) {
    if (event.target?.matches?.('#phase4Slice3BarcodeForm input[name="barcode"]')) {
      slice3State.scanner.barcode = event.target.value;
      return;
    }
    if (!event.target?.matches?.('#phase4Slice3SearchForm input[name="query"]')) return;
    runUnifiedSearch(event.target.value);
  }

  function handleSubmit(event) {
    if (event.target?.id === "phase4Slice3SearchForm") {
      event.preventDefault();
      runUnifiedSearch(new FormData(event.target).get("query"), { forceLocal: true });
    }
    if (event.target?.id === "phase4Slice3EntryForm") {
      event.preventDefault();
      saveEntry(event.target);
    }
    if (event.target?.id === "phase4Slice3BarcodeForm") {
      event.preventDefault();
      lookupBarcode(new FormData(event.target).get("barcode"));
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
  document.addEventListener("input", handleInput);
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
      activeItemCount: (slice3State.day.value?.items || []).length,
      localSearchStatus: slice3State.search.status,
      localResultCount: slice3State.search.items.length,
      localRejectedCount: slice3State.search.rejectedCount,
      selectedResultType: slice3State.portal.food?.result_type || "",
      providerSearchStatus: slice3State.providerSearch.status,
      providerResultCount: slice3State.providerSearch.items.length
    })
  });
})();
