(function phase3TrainingEngine() {
  if (window.FMZ_PHASE3_TRAINING_ENGINE_LOADED) return;
  window.FMZ_PHASE3_TRAINING_ENGINE_LOADED = true;

  const PHASE3_VERSION = "20260817-phase3-compact-entry1";
  const PHASE3_LANGUAGES = ["nl", "en", "de"];
  const PHASE3_FREE_ACTIVE_DAY_LIMIT = 4;
  const PHASE3_REAL_CATALOG_EXPECTED_COUNT = 898;
  const PHASE3_EXERCISE_UUID_NAMESPACE = "9439f2af-0e84-5e41-9482-d4b6765154ed";
  const PHASE3_CATALOG_CACHE_KEY = "fmz-phase3-exercise-catalog:kinetic-8652d873";
  const PHASE3_CATALOG_DETAILS_CACHE_KEY = "fmz-phase3-exercise-details:kinetic-8652d873";
  const PHASE3_PICKER_PORTAL_ID = "phase3-exercise-picker-portal";
  const PHASE3_FOCUS_PORTAL_ID = "phase3-workout-focus-portal";
  const PHASE3_HISTORY_PORTAL_ID = "phase3-workout-history-portal";
  const PHASE3_CATALOG_QUERY_PAGE_SIZE = 500;
  const PHASE3_PICKER_PAGE_SIZE = 36;
  const PHASE3_UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const PHASE3_NO_AI_CALLS = true;
  const PHASE3_NO_MUTATION_OBSERVER = true;
  const PHASE3_NO_POLLING = true;
  const PHASE3_NO_FULL_WORKSPACE_SET_SAVE = true;

  const PHASE3_I18N = {
    nl: {
      eyebrow: "Training Engine",
      title: "Training",
      intro: "Start bewust je workout, log sets snel en houd vorige prestaties en PR's bij.",
      dbPending: "Normalized trainingtabellen zijn nog niet live. Je actieve workout wordt lokaal veilig bewaard tot sync mogelijk is.",
      synced: "Gesynchroniseerd",
      localSafe: "Lokaal veilig",
      freeLimitTitle: "Free limiet",
      freeLimitText: "Free kan maximaal 4 actieve workouts gebruiken. Het aantal oefeningen per workout wordt niet door Free beperkt.",
      activeWorkouts: "{count}/{limit} actieve workouts",
      unlimitedWorkouts: "Onbeperkte workouts via Pro/PT",
      createPlan: "Workout maken",
      myWorkouts: "Mijn workouts",
      workoutHistory: "Workout History",
      personalRecords: "Persoonlijke records / PR's",
      builderSummary: "Maak of bewerk een workout",
      workoutCounts: "{active} actief · {archived} gearchiveerd",
      historyCount: "{count} afgerond",
      recordCount: "{count} records",
      planTitle: "Naam workout",
      day: "Trainingsdag",
      exercise: "Oefening",
      muscle: "Spiergroep",
      equipment: "Materiaal",
      instructions: "Instructies",
      sets: "Sets",
      reps: "Reps",
      weight: "Gewicht",
      targetWeight: "Doel kg",
      rir: "RIR",
      rpe: "RPE",
      rest: "Rust",
      notes: "Notities",
      chooseExercise: "Oefening kiezen",
      selectedExercise: "Gekozen oefening",
      exercisePickerTitle: "Oefening selecteren",
      openExercisePicker: "Open oefeningkiezer",
      closePicker: "Sluiten",
      clearFilters: "Filters wissen",
      catalogLoading: "Oefencatalogus laden...",
      catalogProgress: "{loaded} van {total} oefeningen geladen",
      catalogLoadError: "De oefencatalogus kon niet worden geladen. Probeer opnieuw of sluit de kiezer.",
      retryCatalog: "Opnieuw proberen",
      pickerResults: "Resultaten",
      showingResults: "{shown} van {total} zichtbaar",
      loadMoreExercises: "Meer oefeningen laden",
      animationPreview: "Animatiepreview",
      animationPlaceholder: "Branded placeholder",
      youriAvatarPending: "Youri-avatar animatie volgt later",
      activeExercisePreview: "Actieve oefening preview",
      addExercise: "Oefening toevoegen",
      archiveExercise: "Oefening archiveren",
      removeExercise: "Verwijderen",
      editExercise: "Wijzigen",
      updateExercise: "Oefening bijwerken",
      cancelEdit: "Bewerken annuleren",
      moveExerciseUp: "Omhoog",
      moveExerciseDown: "Omlaag",
      selectedExercises: "Gekozen oefeningen",
      noBuilderExercises: "Nog geen oefeningen toegevoegd. Gebruik 'Oefening toevoegen' of sla direct op om de huidige oefening mee te nemen.",
      exerciseCount: "{count} oefeningen",
      exerciseFreeNote: "Free beperkt workouts, niet het aantal oefeningen in een workout.",
      searchLibrary: "Zoek oefening",
      allCategories: "Alle spiergroepen",
      allEquipment: "Alle materialen",
      noLibraryResults: "Geen oefeningen gevonden.",
      partialSave: "Workout deels opgeslagen. De opgeslagen oefeningen blijven bewaard; probeer de resterende oefeningen opnieuw te syncen.",
      retryPartialSave: "Resterende oefeningen opnieuw syncen",
      partialRetrying: "Opnieuw syncen...",
      addPlan: "Actieve workout opslaan",
      limitReached: "Free limiet bereikt. Archiveer eerst een workout of upgrade later naar Pro/PT.",
      plans: "Workouts",
      noPlans: "Nog geen normalized workouts. Legacy schema's blijven hieronder beschikbaar als bridge.",
      legacyPlan: "Legacy schema",
      legacyBridge: "Legacy training blijft zichtbaar en wordt niet aangepast door Phase 3.",
      startWorkout: "Workout starten",
      continueWorkout: "Workout hervatten",
      openFocus: "Open workout",
      closeFocus: "Workout verkleinen",
      pause: "Pauzeren",
      resume: "Hervatten",
      completeWorkout: "Workout afronden",
      activeWorkout: "Actieve workout",
      paused: "Gepauzeerd",
      active: "Actief",
      completed: "Voltooid",
      completeSet: "Set opslaan",
      setDone: "Set opgeslagen",
      currentSet: "Huidige set",
      exerciseProgress: "Oefening {current} van {total}",
      setProgress: "Set {current} van {total}",
      workoutDuration: "Workoutduur",
      trainingPaused: "Training gepauzeerd",
      skipExercise: "Oefening overslaan",
      exerciseCompleted: "Oefening voltooid",
      allExercisesCompleted: "Alle oefeningen zijn doorlopen. Rond de training af wanneer je klaar bent.",
      next: "Volgende",
      timer: "Rusttimer",
      timerDone: "Rust voorbij",
      restTitle: "Rust",
      skipRest: "Rust overslaan",
      addFifteen: "+15 sec",
      restartRest: "Herstart",
      vibrationSetting: "Trillen bij einde rusttimer",
      setValidationFailed: "Vul minimaal 1 geldige herhaling in. Gewicht mag leeg zijn; RIR moet 0-10 en RPE 1-10 zijn.",
      setSaveFailed: "Set kon niet veilig worden opgeslagen. Controleer je verbinding en probeer opnieuw.",
      previousPerformance: "Vorige prestatie",
      previousTime: "Vorige keer",
      noPrevious: "Nog geen vorige prestatie",
      noPerformedSets: "Geen uitgevoerde sets opgeslagen.",
      prTitle: "PR foundation",
      maxWeight: "Max gewicht",
      maxReps: "Max reps",
      estimatedOneRm: "Geschatte 1RM",
      historyTitle: "Workout history",
      noHistory: "Nog geen afgeronde workouts.",
      openHistory: "Workout bekijken",
      historyDetail: "Workoutdetails",
      durationUnavailable: "Duur niet beschikbaar",
      englishInstructionFallback: "Engelse instructie; Nederlandse vertaling volgt na inhoudsreview.",
      overloadTitle: "Progressive overload",
      overloadNeutral: "Log eerst prestaties; daarna verschijnt een veilige trendstatus.",
      overloadRepeat: "Vorige prestatie beschikbaar. Herhaal eerst stabiel voordat je verhoogt.",
      overloadPotential: "Alle sets gehaald met ruimte over. Kleine verhoging kan later overwogen worden.",
      archivePlan: "Workout archiveren",
      editPlan: "Bewerken",
      editWorkout: "Workout bewerken",
      saveWorkoutChanges: "Wijzigingen opslaan",
      cancelWorkoutEdit: "Bewerken annuleren",
      activePlans: "Actief",
      archivedPlans: "Gearchiveerd",
      archivedStatus: "Gearchiveerd",
      restorePlan: "Herstellen",
      noActivePlans: "Nog geen actieve workouts.",
      noArchivedPlans: "Nog geen gearchiveerde workouts.",
      archiveHistoryHelp: "Archiveren maakt een herbruikbare workout inactief. Afgeronde trainingen blijven altijd in Workout History staan.",
      planArchived: "Workout gearchiveerd. Je vindt deze onder Gearchiveerd.",
      planRestored: "Workout hersteld en weer actief.",
      planUpdated: "Workout bijgewerkt. Eerdere Workout History is ongewijzigd.",
      restoreLimitReached: "Deze workout kan niet worden hersteld: Free staat maximaal 4 actieve workouts toe. Archiveer eerst een andere workout.",
      saveFailed: "Opslaan mislukt: {message}",
      saved: "Opgeslagen",
      started: "Workout gestart",
      completedWorkout: "Workout opgeslagen in history",
      pendingSync: "Wacht op sync",
      Maandag: "Maandag",
      Dinsdag: "Dinsdag",
      Woensdag: "Woensdag",
      Donderdag: "Donderdag",
      Vrijdag: "Vrijdag",
      Zaterdag: "Zaterdag",
      Zondag: "Zondag",
      Monday: "Maandag",
      Tuesday: "Dinsdag",
      Wednesday: "Woensdag",
      Thursday: "Donderdag",
      Friday: "Vrijdag",
      Saturday: "Zaterdag",
      Sunday: "Zondag"
    },
    en: {
      eyebrow: "Training Engine",
      title: "Training",
      intro: "Start your workout intentionally, log sets quickly and track previous performance and PRs.",
      dbPending: "Normalized training tables are not live yet. Your active workout is kept safely local until sync is possible.",
      synced: "Synced",
      localSafe: "Local safe",
      freeLimitTitle: "Free limit",
      freeLimitText: "Free can use up to 4 active workouts. The number of exercises inside a workout is not limited by Free.",
      activeWorkouts: "{count}/{limit} active workouts",
      unlimitedWorkouts: "Unlimited workouts through Pro/PT",
      createPlan: "Create workout",
      myWorkouts: "My workouts",
      workoutHistory: "Workout history",
      personalRecords: "Personal records / PRs",
      builderSummary: "Create or edit a workout",
      workoutCounts: "{active} active · {archived} archived",
      historyCount: "{count} completed",
      recordCount: "{count} records",
      planTitle: "Workout name",
      day: "Training day",
      exercise: "Exercise",
      muscle: "Muscle group",
      equipment: "Equipment",
      instructions: "Instructions",
      sets: "Sets",
      reps: "Reps",
      weight: "Weight",
      targetWeight: "Target kg",
      rir: "RIR",
      rpe: "RPE",
      rest: "Rest",
      notes: "Notes",
      chooseExercise: "Choose exercise",
      selectedExercise: "Selected exercise",
      exercisePickerTitle: "Select exercise",
      openExercisePicker: "Open exercise picker",
      closePicker: "Close",
      clearFilters: "Clear filters",
      catalogLoading: "Loading exercise catalog...",
      catalogProgress: "{loaded} of {total} exercises loaded",
      catalogLoadError: "The exercise catalog could not be loaded. Retry or close the picker.",
      retryCatalog: "Retry",
      pickerResults: "Results",
      showingResults: "{shown} of {total} visible",
      loadMoreExercises: "Load more exercises",
      animationPreview: "Animation preview",
      animationPlaceholder: "Branded placeholder",
      youriAvatarPending: "Youri avatar animation will follow later",
      activeExercisePreview: "Active exercise preview",
      addExercise: "Add exercise",
      archiveExercise: "Archive exercise",
      removeExercise: "Remove",
      editExercise: "Edit",
      updateExercise: "Update exercise",
      cancelEdit: "Cancel edit",
      moveExerciseUp: "Move up",
      moveExerciseDown: "Move down",
      selectedExercises: "Selected exercises",
      noBuilderExercises: "No exercises added yet. Use 'Add exercise' or save directly to include the current exercise.",
      exerciseCount: "{count} exercises",
      exerciseFreeNote: "Free limits workouts, not exercises inside a workout.",
      searchLibrary: "Search exercise",
      allCategories: "All muscle groups",
      allEquipment: "All equipment",
      noLibraryResults: "No exercises found.",
      partialSave: "Workout partly saved. The saved exercises remain available; retry syncing the remaining exercises.",
      retryPartialSave: "Retry remaining exercises",
      partialRetrying: "Retrying sync...",
      addPlan: "Save active workout",
      limitReached: "Free limit reached. Archive a workout first or upgrade later to Pro/PT.",
      plans: "Workouts",
      noPlans: "No normalized workouts yet. Legacy plans remain available below as a bridge.",
      legacyPlan: "Legacy plan",
      legacyBridge: "Legacy training stays visible and is not modified by Phase 3.",
      startWorkout: "Start workout",
      continueWorkout: "Continue workout",
      openFocus: "Open workout",
      closeFocus: "Minimize workout",
      pause: "Pause",
      resume: "Resume",
      completeWorkout: "Complete workout",
      activeWorkout: "Active workout",
      paused: "Paused",
      active: "Active",
      completed: "Completed",
      completeSet: "Save set",
      setDone: "Set saved",
      currentSet: "Current set",
      exerciseProgress: "Exercise {current} of {total}",
      setProgress: "Set {current} of {total}",
      workoutDuration: "Workout duration",
      trainingPaused: "Training paused",
      skipExercise: "Skip exercise",
      exerciseCompleted: "Exercise completed",
      allExercisesCompleted: "All exercises have been covered. Complete the workout when you are ready.",
      next: "Next",
      timer: "Rest timer",
      timerDone: "Rest done",
      restTitle: "Rest",
      skipRest: "Skip rest",
      addFifteen: "+15 sec",
      restartRest: "Restart",
      vibrationSetting: "Vibrate at the end of the rest timer",
      setValidationFailed: "Enter at least 1 valid repetition. Weight may be empty; RIR must be 0-10 and RPE 1-10.",
      setSaveFailed: "The set could not be saved safely. Check your connection and retry.",
      previousPerformance: "Previous performance",
      previousTime: "Last time",
      noPrevious: "No previous performance yet",
      noPerformedSets: "No performed sets were saved.",
      prTitle: "PR foundation",
      maxWeight: "Max weight",
      maxReps: "Max reps",
      estimatedOneRm: "Estimated 1RM",
      historyTitle: "Workout history",
      noHistory: "No completed workouts yet.",
      openHistory: "View workout",
      historyDetail: "Workout details",
      durationUnavailable: "Duration unavailable",
      englishInstructionFallback: "English instruction fallback.",
      overloadTitle: "Progressive overload",
      overloadNeutral: "Log performances first; then a safe trend status appears.",
      overloadRepeat: "Previous performance available. Repeat it steadily before increasing.",
      overloadPotential: "All sets completed with room left. A small increase can later be considered.",
      archivePlan: "Archive workout",
      editPlan: "Edit",
      editWorkout: "Edit workout",
      saveWorkoutChanges: "Save changes",
      cancelWorkoutEdit: "Cancel editing",
      activePlans: "Active",
      archivedPlans: "Archived",
      archivedStatus: "Archived",
      restorePlan: "Restore",
      noActivePlans: "No active workouts yet.",
      noArchivedPlans: "No archived workouts yet.",
      archiveHistoryHelp: "Archiving makes a reusable workout inactive. Completed sessions always remain in Workout history.",
      planArchived: "Workout archived. You can find it under Archived.",
      planRestored: "Workout restored and active again.",
      planUpdated: "Workout updated. Earlier Workout history is unchanged.",
      restoreLimitReached: "This workout cannot be restored: Free allows up to 4 active workouts. Archive another workout first.",
      saveFailed: "Save failed: {message}",
      saved: "Saved",
      started: "Workout started",
      completedWorkout: "Workout saved to history",
      pendingSync: "Waiting for sync",
      Maandag: "Monday",
      Dinsdag: "Tuesday",
      Woensdag: "Wednesday",
      Donderdag: "Thursday",
      Vrijdag: "Friday",
      Zaterdag: "Saturday",
      Zondag: "Sunday",
      Monday: "Monday",
      Tuesday: "Tuesday",
      Wednesday: "Wednesday",
      Thursday: "Thursday",
      Friday: "Friday",
      Saturday: "Saturday",
      Sunday: "Sunday"
    },
    de: {
      eyebrow: "Training Engine",
      title: "Training",
      intro: "Starte dein Workout bewusst, logge Saetze schnell und verfolge fruehere Leistungen und PRs.",
      dbPending: "Normalisierte Trainingstabellen sind noch nicht live. Dein aktives Workout wird lokal sicher gespeichert, bis Sync moeglich ist.",
      synced: "Synchronisiert",
      localSafe: "Lokal sicher",
      freeLimitTitle: "Free Limit",
      freeLimitText: "Free kann maximal 4 aktive Workouts nutzen. Die Anzahl der Uebungen in einem Workout ist durch Free nicht begrenzt.",
      activeWorkouts: "{count}/{limit} aktive Workouts",
      unlimitedWorkouts: "Unbegrenzte Workouts ueber Pro/PT",
      createPlan: "Workout erstellen",
      myWorkouts: "Meine Workouts",
      workoutHistory: "Workout History",
      personalRecords: "Persoenliche Rekorde / PRs",
      builderSummary: "Workout erstellen oder bearbeiten",
      workoutCounts: "{active} aktiv · {archived} archiviert",
      historyCount: "{count} abgeschlossen",
      recordCount: "{count} Rekorde",
      planTitle: "Workoutname",
      day: "Trainingstag",
      exercise: "Uebung",
      muscle: "Muskelgruppe",
      equipment: "Geraet",
      instructions: "Anleitung",
      sets: "Saetze",
      reps: "Wdh.",
      weight: "Gewicht",
      targetWeight: "Ziel kg",
      rir: "RIR",
      rpe: "RPE",
      rest: "Pause",
      notes: "Notizen",
      chooseExercise: "Uebung waehlen",
      selectedExercise: "Ausgewaehlte Uebung",
      exercisePickerTitle: "Uebung auswaehlen",
      openExercisePicker: "Uebungsauswahl oeffnen",
      closePicker: "Schliessen",
      clearFilters: "Filter loeschen",
      catalogLoading: "Uebungskatalog wird geladen...",
      catalogProgress: "{loaded} von {total} Uebungen geladen",
      catalogLoadError: "Der Uebungskatalog konnte nicht geladen werden. Erneut versuchen oder die Auswahl schliessen.",
      retryCatalog: "Erneut versuchen",
      pickerResults: "Ergebnisse",
      showingResults: "{shown} von {total} sichtbar",
      loadMoreExercises: "Mehr Uebungen laden",
      animationPreview: "Animationsvorschau",
      animationPlaceholder: "Branded Placeholder",
      youriAvatarPending: "Youri-Avatar Animation folgt spaeter",
      activeExercisePreview: "Aktive Uebung Vorschau",
      addExercise: "Uebung hinzufuegen",
      archiveExercise: "Uebung archivieren",
      removeExercise: "Entfernen",
      editExercise: "Bearbeiten",
      updateExercise: "Uebung aktualisieren",
      cancelEdit: "Bearbeiten abbrechen",
      moveExerciseUp: "Nach oben",
      moveExerciseDown: "Nach unten",
      selectedExercises: "Ausgewaehlte Uebungen",
      noBuilderExercises: "Noch keine Uebungen hinzugefuegt. Nutze 'Uebung hinzufuegen' oder speichere direkt, um die aktuelle Uebung mitzunehmen.",
      exerciseCount: "{count} Uebungen",
      exerciseFreeNote: "Free begrenzt Workouts, nicht Uebungen innerhalb eines Workouts.",
      searchLibrary: "Uebung suchen",
      allCategories: "Alle Muskelgruppen",
      allEquipment: "Alle Geraete",
      noLibraryResults: "Keine Uebungen gefunden.",
      partialSave: "Workout teilweise gespeichert. Gespeicherte Uebungen bleiben erhalten; synchronisiere die restlichen Uebungen erneut.",
      retryPartialSave: "Restliche Uebungen erneut syncen",
      partialRetrying: "Sync wird wiederholt...",
      addPlan: "Aktives Workout speichern",
      limitReached: "Free Limit erreicht. Archiviere zuerst ein Workout oder upgrade spaeter auf Pro/PT.",
      plans: "Workouts",
      noPlans: "Noch keine normalisierten Workouts. Legacy-Plaene bleiben unten als Bridge verfuegbar.",
      legacyPlan: "Legacy-Plan",
      legacyBridge: "Legacy-Training bleibt sichtbar und wird durch Phase 3 nicht angepasst.",
      startWorkout: "Workout starten",
      continueWorkout: "Workout fortsetzen",
      openFocus: "Workout oeffnen",
      closeFocus: "Workout verkleinern",
      pause: "Pausieren",
      resume: "Fortsetzen",
      completeWorkout: "Workout abschliessen",
      activeWorkout: "Aktives Workout",
      paused: "Pausiert",
      active: "Aktiv",
      completed: "Abgeschlossen",
      completeSet: "Satz speichern",
      setDone: "Satz gespeichert",
      currentSet: "Aktueller Satz",
      exerciseProgress: "Uebung {current} von {total}",
      setProgress: "Satz {current} von {total}",
      workoutDuration: "Workoutdauer",
      trainingPaused: "Training pausiert",
      skipExercise: "Uebung ueberspringen",
      exerciseCompleted: "Uebung abgeschlossen",
      allExercisesCompleted: "Alle Uebungen wurden durchlaufen. Schliesse das Workout ab, wenn du fertig bist.",
      next: "Als Naechstes",
      timer: "Pausentimer",
      timerDone: "Pause vorbei",
      restTitle: "Pause",
      skipRest: "Pause ueberspringen",
      addFifteen: "+15 Sek.",
      restartRest: "Neu starten",
      vibrationSetting: "Am Ende des Pausentimers vibrieren",
      setValidationFailed: "Trage mindestens 1 gueltige Wiederholung ein. Gewicht darf leer bleiben; RIR muss 0-10 und RPE 1-10 sein.",
      setSaveFailed: "Der Satz konnte nicht sicher gespeichert werden. Verbindung pruefen und erneut versuchen.",
      previousPerformance: "Fruehere Leistung",
      previousTime: "Letztes Mal",
      noPrevious: "Noch keine fruehere Leistung",
      noPerformedSets: "Keine ausgefuehrten Saetze gespeichert.",
      prTitle: "PR Foundation",
      maxWeight: "Max Gewicht",
      maxReps: "Max Wdh.",
      estimatedOneRm: "Geschaetztes 1RM",
      historyTitle: "Workout History",
      noHistory: "Noch keine abgeschlossenen Workouts.",
      openHistory: "Workout ansehen",
      historyDetail: "Workoutdetails",
      durationUnavailable: "Dauer nicht verfuegbar",
      englishInstructionFallback: "Englische Anleitung als Fallback.",
      overloadTitle: "Progressive Overload",
      overloadNeutral: "Logge zuerst Leistungen; danach erscheint ein sicherer Trendstatus.",
      overloadRepeat: "Fruehere Leistung verfuegbar. Wiederhole sie stabil, bevor du steigerst.",
      overloadPotential: "Alle Saetze mit Reserve geschafft. Eine kleine Steigerung kann spaeter erwogen werden.",
      archivePlan: "Workout archivieren",
      editPlan: "Bearbeiten",
      editWorkout: "Workout bearbeiten",
      saveWorkoutChanges: "Aenderungen speichern",
      cancelWorkoutEdit: "Bearbeiten abbrechen",
      activePlans: "Aktiv",
      archivedPlans: "Archiviert",
      archivedStatus: "Archiviert",
      restorePlan: "Wiederherstellen",
      noActivePlans: "Noch keine aktiven Workouts.",
      noArchivedPlans: "Noch keine archivierten Workouts.",
      archiveHistoryHelp: "Archivieren macht ein wiederverwendbares Workout inaktiv. Abgeschlossene Trainings bleiben immer in der Workout History.",
      planArchived: "Workout archiviert. Du findest es unter Archiviert.",
      planRestored: "Workout wiederhergestellt und erneut aktiv.",
      planUpdated: "Workout aktualisiert. Die fruehere Workout History bleibt unveraendert.",
      restoreLimitReached: "Dieses Workout kann nicht wiederhergestellt werden: Free erlaubt maximal 4 aktive Workouts. Archiviere zuerst ein anderes Workout.",
      saveFailed: "Speichern fehlgeschlagen: {message}",
      saved: "Gespeichert",
      started: "Workout gestartet",
      completedWorkout: "Workout in History gespeichert",
      pendingSync: "Wartet auf Sync",
      Maandag: "Montag",
      Dinsdag: "Dienstag",
      Woensdag: "Mittwoch",
      Donderdag: "Donnerstag",
      Vrijdag: "Freitag",
      Zaterdag: "Samstag",
      Zondag: "Sonntag",
      Monday: "Montag",
      Tuesday: "Dienstag",
      Wednesday: "Mittwoch",
      Thursday: "Donnerstag",
      Friday: "Freitag",
      Saturday: "Samstag",
      Sunday: "Sonntag"
    }
  };

  function phase3Localized(values) {
    return { nl: values[0], en: values[1], de: values[2] };
  }

  function phase3CatalogSlug(value) {
    return String(value || "exercise")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 96) || "exercise";
  }

  function phase3Utf8Bytes(value) {
    const bytes = [];
    for (const character of String(value)) {
      const code = character.codePointAt(0);
      if (code <= 0x7f) bytes.push(code);
      else if (code <= 0x7ff) bytes.push(0xc0 | (code >> 6), 0x80 | (code & 0x3f));
      else if (code <= 0xffff) bytes.push(0xe0 | (code >> 12), 0x80 | ((code >> 6) & 0x3f), 0x80 | (code & 0x3f));
      else bytes.push(0xf0 | (code >> 18), 0x80 | ((code >> 12) & 0x3f), 0x80 | ((code >> 6) & 0x3f), 0x80 | (code & 0x3f));
    }
    return bytes;
  }

  function phase3Sha1(inputBytes) {
    const bytes = inputBytes.slice();
    const bitLength = bytes.length * 8;
    bytes.push(0x80);
    while ((bytes.length % 64) !== 56) bytes.push(0);
    const high = Math.floor(bitLength / 0x100000000);
    const low = bitLength >>> 0;
    for (let shift = 24; shift >= 0; shift -= 8) bytes.push((high >>> shift) & 0xff);
    for (let shift = 24; shift >= 0; shift -= 8) bytes.push((low >>> shift) & 0xff);

    let h0 = 0x67452301;
    let h1 = 0xefcdab89;
    let h2 = 0x98badcfe;
    let h3 = 0x10325476;
    let h4 = 0xc3d2e1f0;
    const words = new Array(80);
    for (let offset = 0; offset < bytes.length; offset += 64) {
      for (let i = 0; i < 16; i += 1) {
        const index = offset + i * 4;
        words[i] = ((bytes[index] << 24) | (bytes[index + 1] << 16) | (bytes[index + 2] << 8) | bytes[index + 3]) >>> 0;
      }
      for (let i = 16; i < 80; i += 1) {
        const value = words[i - 3] ^ words[i - 8] ^ words[i - 14] ^ words[i - 16];
        words[i] = ((value << 1) | (value >>> 31)) >>> 0;
      }
      let a = h0;
      let b = h1;
      let c = h2;
      let d = h3;
      let e = h4;
      for (let i = 0; i < 80; i += 1) {
        let f;
        let k;
        if (i < 20) {
          f = (b & c) | ((~b) & d);
          k = 0x5a827999;
        } else if (i < 40) {
          f = b ^ c ^ d;
          k = 0x6ed9eba1;
        } else if (i < 60) {
          f = (b & c) | (b & d) | (c & d);
          k = 0x8f1bbcdc;
        } else {
          f = b ^ c ^ d;
          k = 0xca62c1d6;
        }
        const rotatedA = ((a << 5) | (a >>> 27)) >>> 0;
        const temp = (rotatedA + f + e + k + words[i]) >>> 0;
        e = d;
        d = c;
        c = ((b << 30) | (b >>> 2)) >>> 0;
        b = a;
        a = temp;
      }
      h0 = (h0 + a) >>> 0;
      h1 = (h1 + b) >>> 0;
      h2 = (h2 + c) >>> 0;
      h3 = (h3 + d) >>> 0;
      h4 = (h4 + e) >>> 0;
    }
    return [h0, h1, h2, h3, h4].flatMap((word) => [24, 16, 8, 0].map((shift) => (word >>> shift) & 0xff));
  }

  function phase3UuidBytes(value) {
    if (!PHASE3_UUID_PATTERN.test(String(value || ""))) throw new Error("Invalid Phase 3 UUID namespace");
    return String(value).replace(/-/g, "").match(/.{2}/g).map((pair) => Number.parseInt(pair, 16));
  }

  function phase3UuidV5(name, namespace = PHASE3_EXERCISE_UUID_NAMESPACE) {
    const bytes = phase3Sha1([...phase3UuidBytes(namespace), ...phase3Utf8Bytes(name)]).slice(0, 16);
    bytes[6] = (bytes[6] & 0x0f) | 0x50;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = bytes.map((byte) => byte.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20, 32)}`;
  }

  function phase3StableUuid(seed) {
    return phase3UuidV5(phase3CatalogSlug(seed));
  }

  function phase3ExerciseDef(slug, names, primary, equipment, instructions, secondary = ["", "", ""], options = {}) {
    const canonicalSlug = phase3CatalogSlug(slug);
    const item = {
      id: phase3StableUuid(canonicalSlug),
      slug: canonicalSlug,
      canonicalSlug,
      names: phase3Localized(names),
      category: phase3Localized(primary),
      primary: phase3Localized(primary),
      secondary: phase3Localized(secondary),
      equipment: phase3Localized(equipment),
      instructions: phase3Localized(instructions),
      bodyRegion: options.bodyRegion || "general",
      equipmentGroup: options.equipmentGroup || equipment[1] || equipment[0] || "Other",
      movementPattern: options.movementPattern || "general",
      animationStatus: options.animationStatus || "placeholder",
      animationSource: options.animationSource || "placeholder",
      animationUrl: options.animationUrl || "",
      legacyAnimationUrl: options.legacyAnimationUrl || "",
      sourceReference: options.sourceReference || "fmz_core_seed"
    };
    item.searchIndex = [
      ...Object.values(item.names || {}),
      ...Object.values(item.primary || {}),
      ...Object.values(item.secondary || {}),
      ...Object.values(item.equipment || {}),
      ...Object.values(item.instructions || {}),
      item.canonicalSlug,
      item.equipmentGroup,
      item.movementPattern
    ].join(" ").toLowerCase();
    return item;
  }

  const PHASE3_CORE_EXERCISES = [
    phase3ExerciseDef("bodyweight-squat", ["Squat", "Squat", "Kniebeuge"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Zak gecontroleerd, houd knieen stabiel en duw via je hele voet omhoog.", "Lower with control, keep knees stable and drive through the whole foot.", "Kontrolliert absenken, Knie stabil halten und ueber den ganzen Fuss hochdruecken."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("barbell-squat", ["Barbell squat", "Barbell squat", "Langhantel-Kniebeuge"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Barbell", "Barbell", "Langhantel"], ["Span je romp aan, houd de stang stabiel en beweeg gecontroleerd door de hele rep.", "Brace the trunk, keep the bar stable and move with control through the whole rep.", "Rumpf anspannen, Stange stabil halten und die Wiederholung kontrolliert ausfuehren."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("leg-press", ["Leg press", "Leg press", "Beinpresse"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Machine", "Machine", "Maschine"], ["Plaats voeten stevig, zak gecontroleerd en strek zonder je knieen hard te blokkeren.", "Plant the feet firmly, lower with control and extend without hard-locking the knees.", "Fuesse stabil platzieren, kontrolliert absenken und ohne hartes Durchdruecken strecken."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("leg-extension", ["Leg extension", "Leg extension", "Beinstrecker"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Machine", "Machine", "Maschine"], ["Strek gecontroleerd, pauzeer kort bovenin en laat rustig zakken.", "Extend with control, pause briefly at the top and lower calmly.", "Kontrolliert strecken, oben kurz halten und ruhig absenken."], ["", "", ""]),
    phase3ExerciseDef("bulgarian-split-squat", ["Bulgarian split squat", "Bulgarian split squat", "Bulgarian Split Squat"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Houd je voorste voet stabiel en beweeg recht omlaag zonder te draaien.", "Keep the front foot stable and move straight down without rotating.", "Vorderen Fuss stabil halten und gerade nach unten bewegen, ohne zu rotieren."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("romanian-deadlift", ["Romanian deadlift", "Romanian deadlift", "Rumaenisches Kreuzheben"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Barbell", "Barbell", "Langhantel"], ["Scharnier vanuit de heupen, houd rug neutraal en voel spanning in hamstrings.", "Hinge from the hips, keep a neutral back and feel tension in the hamstrings.", "Aus der Huefte beugen, Ruecken neutral halten und Spannung in den Beinbeugern spueren."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("lying-leg-curl", ["Lying leg curl", "Lying leg curl", "Beinbeuger liegend"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Machine", "Machine", "Maschine"], ["Krul gecontroleerd omhoog, houd je heupen op het kussen en rem de terugweg.", "Curl up with control, keep the hips on the pad and resist the return.", "Kontrolliert beugen, Huefte auf dem Polster halten und den Rueckweg bremsen."], ["", "", ""]),
    phase3ExerciseDef("seated-leg-curl", ["Seated leg curl", "Seated leg curl", "Beinbeuger sitzend"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Machine", "Machine", "Maschine"], ["Stel de machine strak in en trek de hakken gecontroleerd naar beneden.", "Set the machine snugly and pull the heels down with control.", "Maschine passend einstellen und die Fersen kontrolliert nach unten ziehen."], ["", "", ""]),
    phase3ExerciseDef("hip-thrust", ["Hip thrust", "Hip thrust", "Hip Thrust"], ["Billen", "Glutes", "Gesaess"], ["Barbell", "Barbell", "Langhantel"], ["Duw vanuit je hakken, kantel bekken licht en knijp bovenin kort aan.", "Drive through the heels, slightly tuck the pelvis and squeeze briefly at the top.", "Ueber die Fersen druecken, Becken leicht kippen und oben kurz anspannen."], ["Hamstrings", "Hamstrings", "Beinbeuger"]),
    phase3ExerciseDef("glute-bridge", ["Glute bridge", "Glute bridge", "Glute Bridge"], ["Billen", "Glutes", "Gesaess"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Breng heupen omhoog, houd ribben laag en knijp gecontroleerd aan.", "Lift the hips, keep ribs down and squeeze with control.", "Huefte anheben, Rippen unten halten und kontrolliert anspannen."], ["Core", "Core", "Core"]),
    phase3ExerciseDef("standing-calf-raise", ["Standing calf raise", "Standing calf raise", "Wadenheben stehend"], ["Kuiten", "Calves", "Waden"], ["Machine", "Machine", "Maschine"], ["Zak volledig uit, duw hoog op je tenen en pauzeer kort bovenin.", "Use a full stretch, rise high onto the toes and pause briefly at the top.", "Voll dehnen, hoch auf die Zehen druecken und oben kurz halten."], ["", "", ""]),
    phase3ExerciseDef("seated-calf-raise", ["Seated calf raise", "Seated calf raise", "Wadenheben sitzend"], ["Kuiten", "Calves", "Waden"], ["Machine", "Machine", "Maschine"], ["Beweeg gecontroleerd door volledige range en vermijd stuiteren.", "Move through the full range with control and avoid bouncing.", "Kontrolliert durch die volle Bewegung gehen und nicht wippen."], ["", "", ""]),
    phase3ExerciseDef("bench-press", ["Bench press", "Bench press", "Bankdruecken"], ["Borst", "Chest", "Brust"], ["Barbell", "Barbell", "Langhantel"], ["Schouderbladen vast, gecontroleerd zakken en krachtig uitstoten.", "Set the shoulder blades, lower under control and press strongly.", "Schulterblaetter fixieren, kontrolliert absenken und kraftvoll druecken."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("incline-dumbbell-press", ["Incline dumbbell press", "Incline dumbbell press", "Schraegbank-Kurzhanteldruecken"], ["Borst", "Chest", "Brust"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Houd controle onderin, druk schuin omhoog en laat schouders laag.", "Control the bottom, press up on the incline and keep shoulders down.", "Unten kontrollieren, schraeg nach oben druecken und Schultern tief halten."], ["Schouders", "Shoulders", "Schultern"]),
    phase3ExerciseDef("push-up", ["Push-up", "Push-up", "Liegestuetz"], ["Borst", "Chest", "Brust"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Houd je lichaam in een lijn, zak rustig en duw krachtig terug.", "Keep the body in one line, lower calmly and press back strongly.", "Koerper in einer Linie halten, ruhig absenken und kraftvoll hochdruecken."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("cable-fly", ["Cable fly", "Cable fly", "Kabel-Flys"], ["Borst", "Chest", "Brust"], ["Cable", "Cable", "Kabelzug"], ["Beweeg vanuit de borst, houd ellebogen licht gebogen en controleer de rek.", "Move from the chest, keep elbows slightly bent and control the stretch.", "Aus der Brust bewegen, Ellbogen leicht gebeugt halten und die Dehnung kontrollieren."], ["", "", ""]),
    phase3ExerciseDef("chest-press-machine", ["Chest press machine", "Chest press machine", "Brustpresse"], ["Borst", "Chest", "Brust"], ["Machine", "Machine", "Maschine"], ["Stel de handgrepen op borsthoogte in en druk zonder je schouders op te trekken.", "Set handles at chest height and press without shrugging the shoulders.", "Griffe auf Brusthoehe einstellen und druecken, ohne die Schultern hochzuziehen."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("deadlift", ["Deadlift", "Deadlift", "Kreuzheben"], ["Rug/benen", "Back/legs", "Ruecken/Beine"], ["Barbell", "Barbell", "Langhantel"], ["Houd rug neutraal, breng spanning op de stang en strek heupen gecontroleerd.", "Keep a neutral back, take tension on the bar and extend the hips with control.", "Ruecken neutral halten, Spannung aufbauen und Huefte kontrolliert strecken."], ["Hamstrings", "Hamstrings", "Beinbeuger"]),
    phase3ExerciseDef("lat-pulldown", ["Lat pulldown", "Lat pulldown", "Latzug"], ["Rug", "Back", "Ruecken"], ["Cable", "Cable", "Kabelzug"], ["Trek ellebogen omlaag, houd borst hoog en controleer de terugweg.", "Pull elbows down, keep the chest tall and control the return.", "Ellbogen nach unten ziehen, Brust hoch halten und Rueckweg kontrollieren."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("seated-cable-row", ["Seated cable row", "Seated cable row", "Kabelrudern sitzend"], ["Rug", "Back", "Ruecken"], ["Cable", "Cable", "Kabelzug"], ["Trek richting romp, houd borst open en knijp schouderbladen samen.", "Pull toward the torso, keep the chest open and squeeze shoulder blades together.", "Zum Oberkoerper ziehen, Brust offen halten und Schulterblaetter zusammenziehen."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("barbell-row", ["Barbell row", "Barbell row", "Langhantelrudern"], ["Rug", "Back", "Ruecken"], ["Barbell", "Barbell", "Langhantel"], ["Houd romp stabiel, trek naar je onderribben en laat gecontroleerd zakken.", "Keep the torso stable, row to the lower ribs and lower with control.", "Oberkoerper stabil halten, zu den unteren Rippen ziehen und kontrolliert absenken."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("dumbbell-row", ["Dumbbell row", "Dumbbell row", "Kurzhantelrudern"], ["Rug", "Back", "Ruecken"], ["Dumbbell", "Dumbbell", "Kurzhantel"], ["Trek naar je heup, blijf stabiel en laat het gewicht gecontroleerd zakken.", "Row toward the hip, stay stable and lower the weight with control.", "Zur Huefte ziehen, stabil bleiben und das Gewicht kontrolliert absenken."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("pull-up", ["Pull-up", "Pull-up", "Klimmzug"], ["Rug", "Back", "Ruecken"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Start vanuit controle, trek borst richting stang en laat rustig zakken.", "Start with control, pull the chest toward the bar and lower calmly.", "Kontrolliert starten, Brust zur Stange ziehen und ruhig absenken."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("overhead-press", ["Overhead press", "Overhead press", "Schulterdruecken"], ["Schouders", "Shoulders", "Schultern"], ["Barbell", "Barbell", "Langhantel"], ["Span romp en billen aan, druk recht omhoog en houd ribben laag.", "Brace trunk and glutes, press straight up and keep ribs down.", "Rumpf und Gesaess anspannen, gerade nach oben druecken und Rippen unten halten."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("dumbbell-shoulder-press", ["Dumbbell shoulder press", "Dumbbell shoulder press", "Kurzhantel-Schulterdruecken"], ["Schouders", "Shoulders", "Schultern"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Druk gecontroleerd boven je hoofd en houd polsen boven ellebogen.", "Press overhead with control and keep wrists above elbows.", "Kontrolliert ueber Kopf druecken und Handgelenke ueber den Ellbogen halten."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("lateral-raise", ["Lateral raise", "Lateral raise", "Seitheben"], ["Schouders", "Shoulders", "Schultern"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Til tot schouderhoogte, houd spanning en vermijd zwaaien.", "Lift to shoulder height, keep tension and avoid swinging.", "Bis Schulterhoehe heben, Spannung halten und Schwung vermeiden."], ["", "", ""]),
    phase3ExerciseDef("rear-delt-fly", ["Rear delt fly", "Rear delt fly", "Reverse Fly"], ["Achterste schouder", "Rear delts", "Hintere Schulter"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Buig licht voorover, open de armen en houd nek ontspannen.", "Hinge slightly forward, open the arms and keep the neck relaxed.", "Leicht vorbeugen, Arme oeffnen und Nacken entspannt halten."], ["Bovenrug", "Upper back", "Oberer Ruecken"]),
    phase3ExerciseDef("face-pull", ["Face pull", "Face pull", "Face Pull"], ["Achterste schouder", "Rear delts", "Hintere Schulter"], ["Cable", "Cable", "Kabelzug"], ["Trek naar je gezicht, ellebogen hoog en schouderbladen actief.", "Pull toward the face, elbows high and shoulder blades active.", "Zum Gesicht ziehen, Ellbogen hoch und Schulterblaetter aktiv halten."], ["Bovenrug", "Upper back", "Oberer Ruecken"]),
    phase3ExerciseDef("barbell-curl", ["Barbell curl", "Barbell curl", "Langhantelcurl"], ["Biceps", "Biceps", "Bizeps"], ["Barbell", "Barbell", "Langhantel"], ["Houd ellebogen stil, krul gecontroleerd en rem de terugweg.", "Keep elbows still, curl with control and resist the return.", "Ellbogen ruhig halten, kontrolliert curlen und den Rueckweg bremsen."], ["", "", ""]),
    phase3ExerciseDef("dumbbell-curl", ["Dumbbell curl", "Dumbbell curl", "Kurzhantelcurl"], ["Biceps", "Biceps", "Bizeps"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Draai rustig in, houd romp stil en beweeg zonder zwaai.", "Rotate smoothly, keep the torso still and move without swinging.", "Ruhig eindrehen, Oberkoerper still halten und ohne Schwung bewegen."], ["", "", ""]),
    phase3ExerciseDef("hammer-curl", ["Hammer curl", "Hammer curl", "Hammercurl"], ["Biceps", "Biceps", "Bizeps"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Houd duimen omhoog, ellebogen naast je lichaam en controleer elke rep.", "Keep thumbs up, elbows by the body and control every rep.", "Daumen nach oben halten, Ellbogen am Koerper und jede Wiederholung kontrollieren."], ["Onderarmen", "Forearms", "Unterarme"]),
    phase3ExerciseDef("cable-curl", ["Cable curl", "Cable curl", "Kabelcurl"], ["Biceps", "Biceps", "Bizeps"], ["Cable", "Cable", "Kabelzug"], ["Houd constante spanning en laat de kabel gecontroleerd teruglopen.", "Keep constant tension and let the cable return with control.", "Konstante Spannung halten und das Kabel kontrolliert zurueckfuehren."], ["", "", ""]),
    phase3ExerciseDef("triceps-pushdown", ["Triceps pushdown", "Triceps pushdown", "Trizepsdruecken"], ["Triceps", "Triceps", "Trizeps"], ["Cable", "Cable", "Kabelzug"], ["Houd ellebogen naast je romp en strek volledig zonder te zwaaien.", "Keep elbows by the torso and fully extend without swinging.", "Ellbogen am Oberkoerper halten und voll strecken, ohne zu schwingen."], ["", "", ""]),
    phase3ExerciseDef("overhead-triceps-extension", ["Overhead triceps extension", "Overhead triceps extension", "Trizepsstrecken ueber Kopf"], ["Triceps", "Triceps", "Trizeps"], ["Cable", "Cable", "Kabelzug"], ["Houd bovenarmen stabiel en voel rek zonder je rug te overstrekken.", "Keep upper arms stable and feel the stretch without overextending the back.", "Oberarme stabil halten und Dehnung spueren, ohne den Ruecken zu ueberstrecken."], ["", "", ""]),
    phase3ExerciseDef("close-grip-bench-press", ["Close-grip bench press", "Close-grip bench press", "Enges Bankdruecken"], ["Triceps", "Triceps", "Trizeps"], ["Barbell", "Barbell", "Langhantel"], ["Gebruik een smallere greep, houd ellebogen gecontroleerd en druk krachtig uit.", "Use a narrower grip, control the elbows and press strongly.", "Engeren Griff nutzen, Ellbogen kontrollieren und kraftvoll druecken."], ["Borst", "Chest", "Brust"]),
    phase3ExerciseDef("dips", ["Dips", "Dips", "Dips"], ["Triceps", "Triceps", "Trizeps"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Zak alleen zo diep als schouders comfortabel blijven en duw gecontroleerd omhoog.", "Lower only as deep as shoulders stay comfortable and press up with control.", "Nur so tief absenken, wie die Schultern komfortabel bleiben, und kontrolliert hochdruecken."], ["Borst", "Chest", "Brust"]),
    phase3ExerciseDef("plank", ["Plank", "Plank", "Plank"], ["Core", "Core", "Core"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Span buik en billen aan, houd je lichaam lang en adem rustig door.", "Brace abs and glutes, keep the body long and breathe calmly.", "Bauch und Gesaess anspannen, Koerper lang halten und ruhig atmen."], ["", "", ""]),
    phase3ExerciseDef("crunch", ["Crunch", "Crunch", "Crunch"], ["Buik", "Abs", "Bauch"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Rol gecontroleerd op, houd spanning op je buik en trek niet aan je nek.", "Curl up with control, keep abdominal tension and avoid pulling the neck.", "Kontrolliert aufrollen, Bauchspannung halten und nicht am Nacken ziehen."], ["", "", ""]),
    phase3ExerciseDef("cable-crunch", ["Cable crunch", "Cable crunch", "Kabelcrunch"], ["Buik", "Abs", "Bauch"], ["Cable", "Cable", "Kabelzug"], ["Rond je bovenrug gecontroleerd en trek vanuit je buik, niet vanuit je armen.", "Round the upper back with control and pull from the abs, not the arms.", "Oberen Ruecken kontrolliert runden und aus dem Bauch ziehen, nicht aus den Armen."], ["", "", ""]),
    phase3ExerciseDef("hanging-knee-raise", ["Hanging knee raise", "Hanging knee raise", "Haengendes Knieheben"], ["Buik", "Abs", "Bauch"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Kantel bekken licht, hef knieen gecontroleerd en vermijd zwaaien.", "Slightly tuck the pelvis, lift knees with control and avoid swinging.", "Becken leicht kippen, Knie kontrolliert heben und Schwung vermeiden."], ["Heupflexoren", "Hip flexors", "Hueftbeuger"]),
    phase3ExerciseDef("dead-bug", ["Dead bug", "Dead bug", "Dead Bug"], ["Core", "Core", "Core"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Houd onderrug rustig, beweeg langzaam en behoud spanning.", "Keep the lower back quiet, move slowly and maintain tension.", "Unteren Ruecken ruhig halten, langsam bewegen und Spannung halten."], ["", "", ""]),
    phase3ExerciseDef("pallof-press", ["Pallof press", "Pallof press", "Pallof Press"], ["Core", "Core", "Core"], ["Cable", "Cable", "Kabelzug"], ["Druk de kabel recht vooruit en voorkom dat je romp draait.", "Press the cable straight forward and prevent the trunk from rotating.", "Kabel gerade nach vorne druecken und Rotation im Rumpf verhindern."], ["", "", ""]),
    phase3ExerciseDef("smith-machine-squat", ["Smith machine squat", "Smith machine squat", "Smith-Machine-Kniebeuge"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Smith machine", "Smith machine", "Smith Machine"], ["Zet voeten stabiel, blijf gecontroleerd in de rail en duw gelijkmatig omhoog.", "Set the feet stable, stay controlled in the rail and press up evenly.", "Fuesse stabil setzen, kontrolliert in der Fuehrung bleiben und gleichmaessig hochdruecken."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("hack-squat", ["Hack squat", "Hack squat", "Hackenschmidt-Kniebeuge"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Machine", "Machine", "Maschine"], ["Houd rug tegen het kussen, zak gecontroleerd en duw via je hele voet.", "Keep the back against the pad, lower with control and drive through the whole foot.", "Ruecken am Polster halten, kontrolliert absenken und ueber den ganzen Fuss druecken."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("goblet-squat", ["Goblet squat", "Goblet squat", "Goblet Squat"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Dumbbell", "Dumbbell", "Kurzhantel"], ["Houd de dumbbell dicht bij je borst en beweeg rustig door de squat.", "Hold the dumbbell close to the chest and move smoothly through the squat.", "Kurzhantel nah an der Brust halten und ruhig durch die Kniebeuge bewegen."], ["Core", "Core", "Core"]),
    phase3ExerciseDef("walking-lunge", ["Walking lunge", "Walking lunge", "Ausfallschritte gehend"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Stap lang genoeg, houd romp rechtop en duw gecontroleerd door naar de volgende stap.", "Step far enough, keep the torso upright and drive with control into the next step.", "Ausreichend weit steigen, Oberkoerper aufrecht halten und kontrolliert in den naechsten Schritt druecken."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("front-squat", ["Front squat", "Front squat", "Frontkniebeuge"], ["Quadriceps", "Quadriceps", "Quadrizeps"], ["Barbell", "Barbell", "Langhantel"], ["Houd ellebogen hoog, romp stevig en zak gecontroleerd recht omlaag.", "Keep elbows high, trunk firm and lower straight down with control.", "Ellbogen hoch halten, Rumpf fest und kontrolliert gerade absenken."], ["Core", "Core", "Core"]),
    phase3ExerciseDef("good-morning", ["Good morning", "Good morning", "Good Morning"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Barbell", "Barbell", "Langhantel"], ["Houd rug neutraal, beweeg vanuit de heupen en houd de knieen zacht.", "Keep a neutral back, hinge from the hips and keep the knees soft.", "Ruecken neutral halten, aus der Huefte beugen und Knie leicht gebeugt halten."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("single-leg-romanian-deadlift", ["Single-leg Romanian deadlift", "Single-leg Romanian deadlift", "Einbeiniges rumaenisches Kreuzheben"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Dumbbell", "Dumbbell", "Kurzhantel"], ["Houd heupen recht, reik gecontroleerd naar voren en blijf stabiel op een been.", "Keep hips square, reach forward with control and stay stable on one leg.", "Huefte gerade halten, kontrolliert nach vorne reichen und stabil auf einem Bein bleiben."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("sumo-deadlift", ["Sumo deadlift", "Sumo deadlift", "Sumo-Kreuzheben"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Barbell", "Barbell", "Langhantel"], ["Zet breed, houd borst hoog en trek de stang dicht langs je lichaam omhoog.", "Use a wide stance, keep the chest tall and pull the bar close to the body.", "Breit stehen, Brust hoch halten und die Stange nah am Koerper hochziehen."], ["Billen", "Glutes", "Gesaess"]),
    phase3ExerciseDef("back-extension", ["Back extension", "Back extension", "Rueckenstrecker"], ["Hamstrings", "Hamstrings", "Beinbeuger"], ["Machine", "Machine", "Maschine"], ["Beweeg vanuit heupen, houd romp stevig en kom gecontroleerd omhoog.", "Move from the hips, keep the trunk firm and rise with control.", "Aus der Huefte bewegen, Rumpf fest halten und kontrolliert aufrichten."], ["Onderrug", "Lower back", "Unterer Ruecken"]),
    phase3ExerciseDef("cable-kickback", ["Cable kickback", "Cable kickback", "Kabel-Kickback"], ["Billen", "Glutes", "Gesaess"], ["Cable", "Cable", "Kabelzug"], ["Houd bekken stabiel en duw je hiel gecontroleerd naar achteren.", "Keep the pelvis stable and drive the heel back with control.", "Becken stabil halten und die Ferse kontrolliert nach hinten druecken."], ["Hamstrings", "Hamstrings", "Beinbeuger"]),
    phase3ExerciseDef("abductor-machine", ["Abductor machine", "Abductor machine", "Abduktorenmaschine"], ["Billen", "Glutes", "Gesaess"], ["Machine", "Machine", "Maschine"], ["Zit stabiel, open gecontroleerd en houd spanning op de terugweg.", "Sit stable, open with control and keep tension on the return.", "Stabil sitzen, kontrolliert oeffnen und Spannung auf dem Rueckweg halten."], ["Heupen", "Hips", "Huefte"]),
    phase3ExerciseDef("leg-press-calf-raise", ["Leg press calf raise", "Leg press calf raise", "Wadenheben an der Beinpresse"], ["Kuiten", "Calves", "Waden"], ["Machine", "Machine", "Maschine"], ["Gebruik de leg press rustig voor volledige enkelbeweging zonder kniebuiging.", "Use the leg press calmly for full ankle motion without bending the knees.", "Die Beinpresse ruhig fuer volle Sprunggelenksbewegung nutzen, ohne die Knie zu beugen."], ["", "", ""]),
    phase3ExerciseDef("pec-deck", ["Pec deck", "Pec deck", "Butterfly"], ["Borst", "Chest", "Brust"], ["Machine", "Machine", "Maschine"], ["Houd borst hoog, breng armen gecontroleerd samen en rem de opening.", "Keep the chest tall, bring arms together with control and resist the opening.", "Brust hoch halten, Arme kontrolliert zusammenfuehren und die Oeffnung bremsen."], ["", "", ""]),
    phase3ExerciseDef("dumbbell-pullover", ["Dumbbell pullover", "Dumbbell pullover", "Kurzhantel-Pullover"], ["Borst", "Chest", "Brust"], ["Dumbbell", "Dumbbell", "Kurzhantel"], ["Houd ribben laag, beweeg gecontroleerd over je hoofd en trek terug vanuit borst/rug.", "Keep ribs down, move overhead with control and pull back from chest/back.", "Rippen unten halten, kontrolliert ueber Kopf bewegen und aus Brust/Ruecken zurueckziehen."], ["Rug", "Back", "Ruecken"]),
    phase3ExerciseDef("machine-row", ["Machine row", "Machine row", "Maschinenrudern"], ["Rug", "Back", "Ruecken"], ["Machine", "Machine", "Maschine"], ["Trek handgrepen naar je romp, houd borst tegen het kussen en controleer de terugweg.", "Pull handles toward the torso, keep the chest on the pad and control the return.", "Griffe zum Oberkoerper ziehen, Brust am Polster halten und Rueckweg kontrollieren."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("t-bar-row", ["T-bar row", "T-bar row", "T-Bar Rudern"], ["Rug", "Back", "Ruecken"], ["Barbell", "Barbell", "Langhantel"], ["Houd romp stevig, trek ellebogen naar achter en laat gewicht beheerst zakken.", "Keep the torso firm, pull elbows back and lower the load under control.", "Oberkoerper fest halten, Ellbogen nach hinten ziehen und Gewicht kontrolliert absenken."], ["Biceps", "Biceps", "Bizeps"]),
    phase3ExerciseDef("straight-arm-pulldown", ["Straight-arm pulldown", "Straight-arm pulldown", "Latziehen mit gestreckten Armen"], ["Rug", "Back", "Ruecken"], ["Cable", "Cable", "Kabelzug"], ["Houd armen bijna gestrekt en trek vanuit je lats naar je heupen.", "Keep arms nearly straight and pull from the lats toward the hips.", "Arme fast gestreckt halten und aus dem Lat Richtung Huefte ziehen."], ["Core", "Core", "Core"]),
    phase3ExerciseDef("arnold-press", ["Arnold press", "Arnold press", "Arnold Press"], ["Schouders", "Shoulders", "Schultern"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Draai gecontroleerd van voor naar boven en houd de beweging vloeiend.", "Rotate with control from front to overhead and keep the motion smooth.", "Kontrolliert von vorne nach oben rotieren und die Bewegung ruhig halten."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("cable-lateral-raise", ["Cable lateral raise", "Cable lateral raise", "Seitheben am Kabel"], ["Schouders", "Shoulders", "Schultern"], ["Cable", "Cable", "Kabelzug"], ["Til zijwaarts tot schouderhoogte en houd constante kabelspanning.", "Lift sideways to shoulder height and keep constant cable tension.", "Seitlich bis Schulterhoehe heben und konstante Kabelspannung halten."], ["", "", ""]),
    phase3ExerciseDef("machine-shoulder-press", ["Machine shoulder press", "Machine shoulder press", "Schulterpresse"], ["Schouders", "Shoulders", "Schultern"], ["Machine", "Machine", "Maschine"], ["Stel zitting goed in, druk gecontroleerd omhoog en laat rustig terugkomen.", "Set the seat correctly, press up with control and return calmly.", "Sitz passend einstellen, kontrolliert hochdruecken und ruhig zurueckfuehren."], ["Triceps", "Triceps", "Trizeps"]),
    phase3ExerciseDef("preacher-curl", ["Preacher curl", "Preacher curl", "Scottcurl"], ["Biceps", "Biceps", "Bizeps"], ["Machine", "Machine", "Maschine"], ["Houd bovenarmen op het kussen en krul zonder onderin te stuiteren.", "Keep upper arms on the pad and curl without bouncing at the bottom.", "Oberarme am Polster halten und curlen, ohne unten zu wippen."], ["", "", ""]),
    phase3ExerciseDef("incline-dumbbell-curl", ["Incline dumbbell curl", "Incline dumbbell curl", "Schraegbank-Kurzhantelcurl"], ["Biceps", "Biceps", "Bizeps"], ["Dumbbells", "Dumbbells", "Kurzhanteln"], ["Laat armen lang hangen, krul gecontroleerd en houd schouders stil.", "Let arms hang long, curl with control and keep shoulders still.", "Arme lang haengen lassen, kontrolliert curlen und Schultern ruhig halten."], ["", "", ""]),
    phase3ExerciseDef("concentration-curl", ["Concentration curl", "Concentration curl", "Konzentrationscurl"], ["Biceps", "Biceps", "Bizeps"], ["Dumbbell", "Dumbbell", "Kurzhantel"], ["Steun je arm stabiel en beweeg langzaam zonder te zwaaien.", "Support the arm steadily and move slowly without swinging.", "Arm stabil abstuetzen und langsam ohne Schwung bewegen."], ["", "", ""]),
    phase3ExerciseDef("skull-crusher", ["Skull crusher", "Skull crusher", "French Press liegend"], ["Triceps", "Triceps", "Trizeps"], ["Barbell", "Barbell", "Langhantel"], ["Houd bovenarmen stil, buig gecontroleerd en strek zonder ellebogen te laten uitwaaieren.", "Keep upper arms still, bend with control and extend without flaring elbows.", "Oberarme ruhig halten, kontrolliert beugen und strecken, ohne Ellbogen ausweichen zu lassen."], ["", "", ""]),
    phase3ExerciseDef("bench-dips", ["Bench dips", "Bench dips", "Bank-Dips"], ["Triceps", "Triceps", "Trizeps"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Houd schouders laag en zak alleen tot comfortabele diepte.", "Keep shoulders down and lower only to a comfortable depth.", "Schultern tief halten und nur bis zu komfortabler Tiefe absenken."], ["Borst", "Chest", "Brust"]),
    phase3ExerciseDef("rope-overhead-extension", ["Rope overhead extension", "Rope overhead extension", "Trizepsseil ueber Kopf"], ["Triceps", "Triceps", "Trizeps"], ["Cable", "Cable", "Kabelzug"], ["Houd ellebogen stabiel en strek het touw gecontroleerd boven je hoofd.", "Keep elbows stable and extend the rope overhead with control.", "Ellbogen stabil halten und das Seil kontrolliert ueber Kopf strecken."], ["", "", ""]),
    phase3ExerciseDef("side-plank", ["Side plank", "Side plank", "Seitstuetz"], ["Core", "Core", "Core"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Houd heupen hoog, lichaam lang en adem rustig door.", "Keep hips high, body long and breathe calmly.", "Huefte hoch halten, Koerper lang und ruhig weiteratmen."], ["Schuine buik", "Obliques", "Schraege Bauchmuskeln"]),
    phase3ExerciseDef("mountain-climber", ["Mountain climber", "Mountain climber", "Mountain Climber"], ["Core", "Core", "Core"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Houd romp stabiel en breng knieen ritmisch naar voren.", "Keep the trunk stable and drive knees forward rhythmically.", "Rumpf stabil halten und Knie rhythmisch nach vorne fuehren."], ["Conditie", "Conditioning", "Kondition"]),
    phase3ExerciseDef("russian-twist", ["Russian twist", "Russian twist", "Russian Twist"], ["Core", "Core", "Core"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Draai rustig vanuit je romp en houd spanning op je buik.", "Rotate calmly from the trunk and keep abdominal tension.", "Ruhig aus dem Rumpf rotieren und Bauchspannung halten."], ["Schuine buik", "Obliques", "Schraege Bauchmuskeln"]),
    phase3ExerciseDef("ab-wheel-rollout", ["Ab wheel rollout", "Ab wheel rollout", "Ab-Wheel Rollout"], ["Core", "Core", "Core"], ["Bodyweight", "Bodyweight", "Koerpergewicht"], ["Rol alleen zo ver als je romp stabiel blijft en trek gecontroleerd terug.", "Roll only as far as the trunk stays stable and pull back with control.", "Nur so weit rollen, wie der Rumpf stabil bleibt, und kontrolliert zurueckziehen."], ["Schouders", "Shoulders", "Schultern"])
  ];

  const PHASE3_MUSCLE_LABELS = {
    chest: phase3Localized(["Borst", "Chest", "Brust"]),
    back: phase3Localized(["Rug", "Back", "Ruecken"]),
    shoulders: phase3Localized(["Schouders", "Shoulders", "Schultern"]),
    biceps: phase3Localized(["Biceps", "Biceps", "Bizeps"]),
    triceps: phase3Localized(["Triceps", "Triceps", "Trizeps"]),
    quadriceps: phase3Localized(["Quadriceps", "Quadriceps", "Quadrizeps"]),
    hamstrings: phase3Localized(["Hamstrings", "Hamstrings", "Beinbeuger"]),
    "hip-flexors": phase3Localized(["Heupbuigers", "Hip flexors", "Hueftbeuger"]),
    glutes: phase3Localized(["Billen / Glutes", "Glutes", "Gesaess"]),
    calves: phase3Localized(["Kuiten", "Calves", "Waden"]),
    core: phase3Localized(["Core / Buik", "Core / Abs", "Core / Bauch"]),
    forearms: phase3Localized(["Onderarmen", "Forearms", "Unterarme"]),
    trapezius: phase3Localized(["Trapezius", "Trapezius", "Trapezmuskel"]),
    adductors: phase3Localized(["Adductoren", "Adductors", "Adduktoren"]),
    abductors: phase3Localized(["Abductoren", "Abductors", "Abduktoren"]),
    "lower-back": phase3Localized(["Lower back", "Lower back", "Unterer Ruecken"]),
    "full-body": phase3Localized(["Full body", "Full body", "Ganzkoerper"]),
    neck: phase3Localized(["Nek", "Neck", "Nacken"])
  };

  const PHASE3_EQUIPMENT_LABELS = {
    machine: phase3Localized(["Machine", "Machine", "Maschine"]),
    cable: phase3Localized(["Kabel", "Cable", "Kabelzug"]),
    dumbbell: phase3Localized(["Dumbbell", "Dumbbell", "Kurzhantel"]),
    barbell: phase3Localized(["Halterstang / Barbell", "Barbell", "Langhantel"]),
    "smith-machine": phase3Localized(["Smith Machine", "Smith Machine", "Smith Machine"]),
    bodyweight: phase3Localized(["Lichaamsgewicht", "Bodyweight", "Koerpergewicht"]),
    "ez-bar": phase3Localized(["EZ-Bar", "EZ-Bar", "SZ-Stange"]),
    kettlebell: phase3Localized(["Kettlebell", "Kettlebell", "Kettlebell"]),
    "resistance-band": phase3Localized(["Resistance Band", "Resistance Band", "Widerstandsband"]),
    suspension: phase3Localized(["TRX/Suspension", "TRX/Suspension", "TRX/Suspension"]),
    landmine: phase3Localized(["Landmine", "Landmine", "Landmine"]),
    plate: phase3Localized(["Plate", "Plate", "Gewichtsscheibe"]),
    other: phase3Localized(["Overig", "Other", "Sonstiges"])
  };

  let PHASE3_EXERCISES = PHASE3_CORE_EXERCISES.map((exercise) => ({ ...exercise, catalogBacked: false }));

  window.FMZ_PHASE3_TRAINING_ENGINE = {
    version: PHASE3_VERSION,
    surfaces: ["client_training", "active_workout_focus", "training_history", "exercise_picker"],
    tables: [
      "training_plans",
      "training_plan_days",
      "training_plan_exercises",
      "workout_sessions",
      "workout_set_logs"
    ],
    freeActiveDayLimit: PHASE3_FREE_ACTIVE_DAY_LIMIT,
    exerciseLibrarySize: PHASE3_EXERCISES.length,
    realCatalogExpectedCount: PHASE3_REAL_CATALOG_EXPECTED_COUNT,
    catalogSource: "public.exercises; curated core is internal legacy/offline compatibility only",
    syntheticProductionEntries: 0,
    noAiCalls: PHASE3_NO_AI_CALLS,
    noMutationObserver: PHASE3_NO_MUTATION_OBSERVER,
    noPolling: PHASE3_NO_POLLING,
    noFullWorkspaceSetSave: PHASE3_NO_FULL_WORKSPACE_SET_SAVE,
    canonicalIdentity: "stable canonical slug plus FitMetZorge namespaced UUIDv5",
    canonicalUuidNamespace: PHASE3_EXERCISE_UUID_NAMESPACE,
    exerciseLanguagePolicy: "nl_canonical_english_name_nl_instruction_en_english_de_reviewed_or_english_fallback",
    coreExerciseIdentities: PHASE3_EXERCISES.map((exercise) => ({ slug: exercise.canonicalSlug, id: exercise.id })),
    animationArchitecture: "placeholder_or_legacy_now_youri_avatar_ready_later"
  };

  let phase3UserKey = "";
  let phase3State = phase3EmptyState();
  let phase3Hydrating = false;
  let phase3TimerId = null;
  let phase3TimerEndsAt = 0;
  let phase3LastVibrationSecond = null;
  let phase3RestVibrationEnabled = true;
  let phase3TrainingInitialHtml = "";
  let phase3BuilderExercises = [];
  let phase3BuilderEditIndex = null;
  let phase3BuilderDraft = phase3EmptyBuilderDraft();
  let phase3LibraryFilters = { search: "", category: "", equipment: "" };
  let phase3PickerOpen = false;
  let phase3PickerVisibleCount = PHASE3_PICKER_PAGE_SIZE;
  let phase3PickerLoading = false;
  let phase3PickerError = "";
  let phase3CatalogHydrated = false;
  let phase3CatalogLoading = null;
  let phase3CatalogLoadState = { loaded: 0, total: PHASE3_REAL_CATALOG_EXPECTED_COUNT, error: "" };
  let phase3CatalogDetailsCacheRead = false;
  let phase3FocusOpen = false;
  let phase3HistoryDetailId = "";
  let phase3OpenTrainingSection = "plans";
  let phase3PlanView = "active";
  let phase3EditingPlanId = "";
  let phase3EditingDayId = "";
  let phase3PlanFeedback = null;
  const phase3CatalogDetails = new Map();

  function phase3EmptyBuilderDraft() {
    return {
      title: "",
      dayLabel: "Maandag",
      exerciseSlug: PHASE3_EXERCISES[0]?.slug || "",
      sets: "3",
      reps: "8-10",
      targetWeight: "",
      targetRir: "",
      targetRpe: "",
      restSeconds: "90",
      notes: ""
    };
  }

  function phase3CaptureBuilderDraft(form) {
    if (!form) return;
    const data = new FormData(form);
    const fieldValue = (name, fallback) => {
      const field = form.elements?.namedItem?.(name);
      return String(field?.value ?? data.get(name) ?? fallback);
    };
    phase3BuilderDraft = {
      title: fieldValue("title", phase3BuilderDraft.title || ""),
      dayLabel: fieldValue("dayLabel", phase3BuilderDraft.dayLabel || "Maandag"),
      exerciseSlug: fieldValue("exerciseSlug", phase3BuilderDraft.exerciseSlug || PHASE3_EXERCISES[0]?.slug || ""),
      sets: fieldValue("sets", phase3BuilderDraft.sets || "3"),
      reps: fieldValue("reps", phase3BuilderDraft.reps || "8-10"),
      targetWeight: fieldValue("targetWeight", phase3BuilderDraft.targetWeight || ""),
      targetRir: fieldValue("targetRir", phase3BuilderDraft.targetRir || ""),
      targetRpe: fieldValue("targetRpe", phase3BuilderDraft.targetRpe || ""),
      restSeconds: fieldValue("restSeconds", phase3BuilderDraft.restSeconds || "90"),
      notes: fieldValue("notes", phase3BuilderDraft.notes || "")
    };
  }

  function phase3EmptyState() {
    return {
      hydrated: false,
      migrationReady: false,
      syncMessage: "",
      plans: [],
      history: [],
      activeSession: null,
      pendingPlanRetry: null
    };
  }

  function phase3Language() {
    const language = state?.accountSettings?.language || "nl";
    return PHASE3_LANGUAGES.includes(language) ? language : "nl";
  }

  function phase3Text(key) {
    const language = phase3Language();
    return PHASE3_I18N[language]?.[key] || PHASE3_I18N.nl[key] || key;
  }

  function phase3Format(key, values = {}) {
    let text = phase3Text(key);
    Object.entries(values).forEach(([name, value]) => {
      text = text.split(`{${name}}`).join(String(value ?? ""));
    });
    return text;
  }

  function phase3IsUuid(value) {
    return PHASE3_UUID_PATTERN.test(String(value || ""));
  }

  function phase3CatalogLabel(dictionary, key, fallback) {
    const labels = dictionary[key] || phase3Localized([fallback, fallback, fallback]);
    return labels;
  }

  function phase3CatalogRowToExercise(row) {
    const muscle = phase3CatalogLabel(PHASE3_MUSCLE_LABELS, row.primary_muscle, row.primary_muscle || "General");
    const secondary = (row.secondary_muscles || [])
      .map((key) => phase3CatalogLabel(PHASE3_MUSCLE_LABELS, key, key))
      .reduce((labels, item) => ({
        nl: [...labels.nl, item.nl].filter(Boolean),
        en: [...labels.en, item.en].filter(Boolean),
        de: [...labels.de, item.de].filter(Boolean)
      }), { nl: [], en: [], de: [] });
    const equipment = phase3CatalogLabel(PHASE3_EQUIPMENT_LABELS, row.equipment_group, row.equipment || "Other");
    const item = {
      id: row.id,
      slug: row.canonical_slug,
      canonicalSlug: row.canonical_slug,
      names: { nl: row.name_en, en: row.name_en, de: row.name_de || row.name_en },
      category: muscle,
      primary: muscle,
      secondary: { nl: secondary.nl.join(", "), en: secondary.en.join(", "), de: secondary.de.join(", ") },
      equipment,
      instructions: {
        nl: row.instructions_nl || row.instructions_en || "",
        en: row.instructions_en || "",
        de: row.instructions_de || row.instructions_en || ""
      },
      instructionLocales: {
        nl: row.instructions_nl ? "nl" : row.instructions_en ? "en" : "",
        en: row.instructions_en ? "en" : "",
        de: row.instructions_de ? "de" : row.instructions_en ? "en" : ""
      },
      detailsHydrated: Boolean(row.instructions_en),
      bodyRegion: row.body_region || "general",
      equipmentGroup: row.equipment_group || "other",
      movementPattern: row.movement_pattern || "general",
      animationStatus: row.animation_status || "placeholder",
      animationSource: row.animation_source || "placeholder",
      animationUrl: row.animation_url || "",
      legacyAnimationUrl: row.legacy_animation_url || "",
      sourceReference: row.source_reference || "public.exercises",
      catalogBacked: true
    };
    item.searchIndex = [
      ...Object.values(item.names),
      ...Object.values(item.primary),
      ...Object.values(item.secondary),
      ...Object.values(item.equipment),
      item.canonicalSlug,
      item.equipmentGroup,
      item.movementPattern
    ].join(" ").toLowerCase();
    return item;
  }

  function phase3ApplyCatalogRows(rows) {
    const catalog = new Map();
    (rows || [])
      .filter((row) => phase3IsUuid(row.id) && row.canonical_slug)
      .forEach((row) => catalog.set(row.canonical_slug, phase3CatalogRowToExercise(row)));
    PHASE3_EXERCISES = Array.from(catalog.values()).sort((a, b) => a.canonicalSlug.localeCompare(b.canonicalSlug));
    phase3CatalogHydrated = PHASE3_EXERCISES.length === PHASE3_REAL_CATALOG_EXPECTED_COUNT;
    window.FMZ_PHASE3_TRAINING_ENGINE.exerciseLibrarySize = PHASE3_EXERCISES.length;
    window.FMZ_PHASE3_TRAINING_ENGINE.loadedCatalogRecords = PHASE3_EXERCISES.length;
  }

  function phase3ReadCatalogCache() {
    try {
      const cached = window.sessionStorage?.getItem(PHASE3_CATALOG_CACHE_KEY);
      if (!cached) return false;
      const rows = JSON.parse(cached);
      if (!Array.isArray(rows) || rows.length !== PHASE3_REAL_CATALOG_EXPECTED_COUNT) {
        window.sessionStorage?.removeItem(PHASE3_CATALOG_CACHE_KEY);
        return false;
      }
      phase3ApplyCatalogRows(rows);
      return phase3CatalogHydrated;
    } catch {
      try {
        window.sessionStorage?.removeItem(PHASE3_CATALOG_CACHE_KEY);
      } catch {
        // A blocked session storage implementation must not block live hydration.
      }
      return false;
    }
  }

  function phase3WriteCatalogCache(rows) {
    try {
      window.sessionStorage?.setItem(PHASE3_CATALOG_CACHE_KEY, JSON.stringify(rows));
    } catch {
      // The global catalog remains usable in memory when session storage is unavailable.
    }
  }

  function phase3ApplyCatalogDetailRows(rows) {
    (rows || []).forEach((row) => {
      if (!phase3IsUuid(row.id)) return;
      const details = {
        id: row.id,
        instructions_nl: row.instructions_nl || null,
        instructions_en: row.instructions_en || "",
        instructions_de: row.instructions_de || null
      };
      phase3CatalogDetails.set(row.id, details);
      const exercise = phase3ExerciseById(row.id);
      if (!exercise) return;
      exercise.instructions = {
        nl: details.instructions_nl || details.instructions_en,
        en: details.instructions_en,
        de: details.instructions_de || details.instructions_en
      };
      exercise.instructionLocales = {
        nl: details.instructions_nl ? "nl" : details.instructions_en ? "en" : "",
        en: details.instructions_en ? "en" : "",
        de: details.instructions_de ? "de" : details.instructions_en ? "en" : ""
      };
      exercise.detailsHydrated = true;
      exercise.searchIndex = phase3ExerciseSearchText(exercise);
    });
  }

  function phase3ReadCatalogDetailsCache() {
    if (phase3CatalogDetailsCacheRead) return;
    phase3CatalogDetailsCacheRead = true;
    try {
      const cached = JSON.parse(window.sessionStorage?.getItem(PHASE3_CATALOG_DETAILS_CACHE_KEY) || "[]");
      if (Array.isArray(cached)) phase3ApplyCatalogDetailRows(cached);
    } catch {
      // Detail hydration remains available from Supabase when cache data is unavailable.
    }
  }

  function phase3WriteCatalogDetailsCache() {
    try {
      window.sessionStorage?.setItem(PHASE3_CATALOG_DETAILS_CACHE_KEY, JSON.stringify(Array.from(phase3CatalogDetails.values())));
    } catch {
      // Selected exercise details remain available in memory for the active session.
    }
  }

  async function phase3LoadExerciseDetails(exercises) {
    phase3ReadCatalogDetailsCache();
    const catalogExercises = (exercises || []).filter((exercise) => exercise?.catalogBacked && phase3IsUuid(exercise.id));
    phase3ApplyCatalogDetailRows(catalogExercises.map((exercise) => phase3CatalogDetails.get(exercise.id)).filter(Boolean));
    const ids = Array.from(new Set(catalogExercises.filter((exercise) => !exercise.detailsHydrated).map((exercise) => exercise.id)));
    if (!ids.length || !phase3UsesSupabase()) return true;
    try {
      const { data, error } = await supabaseClient
        .from("exercises")
        .select("id,instructions_nl,instructions_en,instructions_de")
        .in("id", ids);
      if (error) throw error;
      phase3ApplyCatalogDetailRows(data || []);
      phase3WriteCatalogDetailsCache();
      return true;
    } catch (error) {
      if (!phase3MigrationMissing(error)) console.warn("Phase 3 exercise detail hydrate skipped", error);
      return false;
    }
  }

  async function phase3LoadCanonicalCatalog() {
    if (phase3CatalogHydrated || phase3ReadCatalogCache()) return true;
    if (!isLoggedIn() || !isOnlineMode() || !supabaseClient) return false;
    if (phase3CatalogLoading) return phase3CatalogLoading;
    phase3CatalogLoading = (async () => {
      try {
        phase3CatalogLoadState = { loaded: 0, total: PHASE3_REAL_CATALOG_EXPECTED_COUNT, error: "" };
        if (supabaseClient.auth?.getSession) {
          const { data: authData, error: authError } = await supabaseClient.auth.getSession();
          if (authError || !authData?.session) throw authError || new Error("Authenticated catalog session is not ready");
        }
        const pageCount = Math.ceil(PHASE3_REAL_CATALOG_EXPECTED_COUNT / PHASE3_CATALOG_QUERY_PAGE_SIZE);
        const pageRequests = Array.from({ length: pageCount }, async (_, pageIndex) => {
          const from = pageIndex * PHASE3_CATALOG_QUERY_PAGE_SIZE;
          const { data, error } = await supabaseClient
            .from("exercises")
            .select("id,canonical_slug,name_en,name_de,primary_muscle,secondary_muscles,body_region,equipment,equipment_group,movement_pattern,animation_url,legacy_animation_url,animation_source,animation_status,source_reference,is_active")
            .eq("is_active", true)
            .order("canonical_slug", { ascending: true })
            .range(from, from + PHASE3_CATALOG_QUERY_PAGE_SIZE - 1);
          if (error) throw error;
          phase3CatalogLoadState.loaded += (data || []).length;
          if (phase3PickerOpen) phase3SyncPickerPortal();
          return data || [];
        });
        const rows = (await Promise.all(pageRequests)).flat();
        if (rows.length !== PHASE3_REAL_CATALOG_EXPECTED_COUNT) {
          throw new Error(`Expected ${PHASE3_REAL_CATALOG_EXPECTED_COUNT} canonical exercises, received ${rows.length}`);
        }
        if (new Set(rows.map((row) => row.id)).size !== PHASE3_REAL_CATALOG_EXPECTED_COUNT
          || new Set(rows.map((row) => row.canonical_slug)).size !== PHASE3_REAL_CATALOG_EXPECTED_COUNT) {
          throw new Error("Canonical exercise catalog contains duplicate identities");
        }
        phase3ApplyCatalogRows(rows);
        if (!phase3CatalogHydrated) throw new Error("Canonical exercise catalog identity validation failed");
        phase3WriteCatalogCache(rows);
        return true;
      } catch (error) {
        phase3CatalogLoadState.error = String(error?.message || "catalog_load_failed");
        if (!phase3MigrationMissing(error)) console.warn("Phase 3 exercise catalog hydrate skipped", error);
        return false;
      } finally {
        phase3CatalogLoading = null;
      }
    })();
    return phase3CatalogLoading;
  }

  function phase3DbId() {
    const random = window.crypto?.randomUUID?.();
    if (phase3IsUuid(random)) return random;
    const hex = Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16));
    hex[12] = "4";
    hex[16] = (8 + Math.floor(Math.random() * 4)).toString(16);
    return `${hex.slice(0, 8).join("")}-${hex.slice(8, 12).join("")}-${hex.slice(12, 16).join("")}-${hex.slice(16, 20).join("")}-${hex.slice(20).join("")}`;
  }

  function phase3EnsureDbId(value, label) {
    if (phase3IsUuid(value)) return String(value);
    const repaired = phase3DbId();
    console.warn(`Phase 3 repaired non-UUID ${label || "id"} before database sync`, value);
    return repaired;
  }

  function phase3LocalKey(prefix, id = phase3DbId()) {
    return `fmz:phase3:${prefix}:${id}`;
  }

  function phase3IsoNow() {
    return new Date().toISOString();
  }

  function phase3TimestampMs(value) {
    const parsed = Date.parse(String(value || ""));
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function phase3CompletedDurationSeconds(startedAt, completedAt, focus = {}) {
    const start = phase3TimestampMs(startedAt);
    const end = phase3TimestampMs(completedAt);
    if (!start || !end || end < start || !focus || !Number.isFinite(Number(focus.accumulatedPausedMs))) return null;
    const pausedMs = Math.max(0, Number(focus?.accumulatedPausedMs || 0));
    return Math.max(0, Math.floor((end - start - pausedMs) / 1000));
  }

  function phase3WorkoutElapsedSeconds(session) {
    if (!session) return 0;
    const start = phase3TimestampMs(session.startedAt);
    if (!start) return 0;
    const focus = phase3EnsureSessionFocus(session);
    const end = phase3TimestampMs(session.completedAt) || Date.now();
    const openPauseMs = focus.pauseStartedAt ? Math.max(0, end - phase3TimestampMs(focus.pauseStartedAt)) : 0;
    return Math.max(0, Math.floor((end - start - focus.accumulatedPausedMs - openPauseMs) / 1000));
  }

  function phase3FormatDuration(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined || !Number.isFinite(Number(totalSeconds))) return phase3Text("durationUnavailable");
    const safe = Math.max(0, Math.floor(Number(totalSeconds)));
    const hours = String(Math.floor(safe / 3600)).padStart(2, "0");
    const minutes = String(Math.floor((safe % 3600) / 60)).padStart(2, "0");
    const seconds = String(safe % 60).padStart(2, "0");
    return `${hours}:${minutes}:${seconds}`;
  }

  function phase3Number(value, fallback = null) {
    if (value === "" || value === null || value === undefined) return fallback;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function phase3DayOrder(dayLabel) {
    const index = DAYS.indexOf(dayLabel);
    return index >= 0 ? index : 0;
  }

  function phase3Exercise(slug) {
    return PHASE3_EXERCISES.find((item) => item.slug === slug) || null;
  }

  function phase3ExerciseById(id) {
    return phase3IsUuid(id) ? PHASE3_EXERCISES.find((item) => item.id === id) || null : null;
  }

  function phase3ExerciseName(slug) {
    const item = phase3Exercise(slug);
    if (!item) return String(slug || phase3Text("exercise"));
    return item.names[phase3Language()] || item.names.nl;
  }

  function phase3ExerciseRecordName(record) {
    const exerciseId = record?.exerciseId || record?.exercise_id || "";
    const exerciseSlug = record?.exerciseSlug || record?.exercise_slug || "";
    const item = phase3ExerciseById(exerciseId) || phase3Exercise(exerciseSlug);
    if (!item) return String(record?.exerciseName || record?.exercise_name_snapshot || exerciseSlug || phase3Text("exercise"));
    return item.names[phase3Language()] || item.names.en || item.names.nl;
  }

  function phase3ExerciseMeta(slug) {
    const item = phase3Exercise(slug);
    const language = phase3Language();
    if (!item) {
      return {
        id: "",
        catalogBacked: false,
        canonicalSlug: String(slug || ""),
        name: String(slug || phase3Text("exercise")),
        category: "",
        primary: "",
        secondary: "",
        equipment: "",
        equipmentGroup: "other",
        movementPattern: "general",
        animationStatus: "placeholder",
        animationSource: "placeholder",
        animationUrl: "",
        legacyAnimationUrl: "",
        instructions: "",
        instructionLocale: "",
        sourceReference: "legacy_snapshot"
      };
    }
    return {
      id: item.id,
      catalogBacked: item.catalogBacked === true,
      canonicalSlug: item.canonicalSlug || item.slug,
      name: item.names[language] || item.names.nl,
      category: item.category?.[language] || item.category?.nl || item.primary[language] || item.primary.nl,
      primary: item.primary[language] || item.primary.nl,
      secondary: item.secondary?.[language] || item.secondary?.nl || "",
      equipment: item.equipment[language] || item.equipment.nl,
      equipmentGroup: item.equipmentGroup || item.equipment?.en || item.equipment?.nl || "Other",
      movementPattern: item.movementPattern || "general",
      animationStatus: item.animationStatus || "placeholder",
      animationSource: item.animationSource || "placeholder",
      animationUrl: item.animationUrl || "",
      legacyAnimationUrl: item.legacyAnimationUrl || "",
      instructions: item.instructions[language] || item.instructions.nl || "",
      instructionLocale: item.instructionLocales?.[language] || (item.catalogBacked ? "" : language),
      sourceReference: item.sourceReference || ""
    };
  }

  function phase3ExerciseSearchText(exercise) {
    if (exercise.searchIndex) return exercise.searchIndex;
    return [
      ...Object.values(exercise.names || {}),
      ...Object.values(exercise.primary || {}),
      ...Object.values(exercise.secondary || {}),
      ...Object.values(exercise.equipment || {}),
      ...Object.values(exercise.instructions || {})
    ].join(" ").toLowerCase();
  }

  function phase3LibraryOptions(field) {
    const language = phase3Language();
    const values = new Map();
    PHASE3_EXERCISES.forEach((exercise) => {
      const group = exercise[field] || {};
      const value = group.nl || group.en || "";
      if (!value) return;
      values.set(value, group[language] || group.nl || value);
    });
    return Array.from(values.entries())
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }

  function phase3FilteredExercises() {
    const search = String(phase3LibraryFilters.search || "").trim().toLowerCase();
    return PHASE3_EXERCISES.filter((exercise) => {
      const categoryMatch = !phase3LibraryFilters.category || exercise.category?.nl === phase3LibraryFilters.category;
      const equipmentMatch = !phase3LibraryFilters.equipment || exercise.equipment?.nl === phase3LibraryFilters.equipment;
      const searchMatch = !search || phase3ExerciseSearchText(exercise).includes(search);
      return categoryMatch && equipmentMatch && searchMatch;
    });
  }

  function phase3ClientEntitlement() {
    const selected = client();
    const entitlement = state?.entitlements?.clients?.[selected?.id] || {};
    return {
      pro: Boolean(entitlement.pro),
      personalCoaching: Boolean(entitlement.personalCoaching),
      free: entitlement.free !== false
    };
  }

  function phase3HasUnlimitedTraining() {
    const entitlement = phase3ClientEntitlement();
    return entitlement.pro || entitlement.personalCoaching;
  }

  function phase3ActiveDayLimit() {
    return phase3HasUnlimitedTraining() ? Infinity : PHASE3_FREE_ACTIVE_DAY_LIMIT;
  }

  function phase3ActiveWorkoutDays() {
    return phase3State.plans
      .filter((plan) => plan.status === "active" && plan.source !== "legacy_bridge")
      .flatMap((plan) => (plan.days || [])
        .filter((day) => (day.status || "active") === "active")
        .map((day) => ({ plan, day })));
  }

  function phase3CanCreateActiveWorkoutDay() {
    const limit = phase3ActiveDayLimit();
    return limit === Infinity || phase3ActiveWorkoutDays().length < limit;
  }

  function phase3CanActivatePlanLocally(plan) {
    const limit = phase3ActiveDayLimit();
    if (limit === Infinity) return true;
    const activatingDays = (plan?.days || []).filter((day) => (day.status || "active") === "active").length;
    return phase3ActiveWorkoutDays().length + activatingDays <= limit;
  }

  function phase3IsFreeLimitError(error) {
    const message = String(error?.message || "").toLowerCase();
    return String(error?.code || "") === "23514" && message.includes("free training limit reached") && message.includes("maximum 4 active training days");
  }

  function phase3SetPlanFeedback(key, error = false, message = "") {
    phase3PlanFeedback = { key, error, message };
  }

  function phase3PlanFeedbackText() {
    if (!phase3PlanFeedback) return "";
    return phase3PlanFeedback.message || phase3Text(phase3PlanFeedback.key);
  }

  function phase3ProfileId() {
    return onlineProfile?.role === "client" && onlineProfile?.id ? onlineProfile.id : "";
  }

  function phase3CurrentUserKey() {
    return phase3ProfileId() || `local-${String(state?.ui?.authEmail || client()?.id || "guest").toLowerCase()}`;
  }

  function phase3StorageKey() {
    return `fmz-phase3-training:${phase3CurrentUserKey()}`;
  }

  function phase3VibrationStorageKey() {
    return `fmz-phase3-rest-vibration:${phase3CurrentUserKey()}`;
  }

  function phase3DefaultRestVibration() {
    return !window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  }

  function phase3LoadRestVibrationPreference() {
    try {
      const stored = localStorage.getItem(phase3VibrationStorageKey());
      phase3RestVibrationEnabled = stored === null ? phase3DefaultRestVibration() : stored === "true";
    } catch {
      phase3RestVibrationEnabled = phase3DefaultRestVibration();
    }
  }

  function phase3SaveRestVibrationPreference() {
    try {
      localStorage.setItem(phase3VibrationStorageKey(), String(phase3RestVibrationEnabled));
    } catch {
      // The preference remains active in memory when local storage is unavailable.
    }
  }

  function phase3DefaultFocusState() {
    return {
      currentExerciseIndex: 0,
      currentSetIndex: 1,
      skippedExerciseKeys: [],
      accumulatedPausedMs: 0,
      pauseStartedAt: "",
      rest: null,
      feedback: "",
      allExercisesCompleted: false
    };
  }

  function phase3EnsureSessionFocus(session) {
    if (!session) return phase3DefaultFocusState();
    const current = session.focus && typeof session.focus === "object" ? session.focus : {};
    session.focus = {
      ...phase3DefaultFocusState(),
      ...current,
      currentExerciseIndex: Math.max(0, Number(current.currentExerciseIndex || 0)),
      currentSetIndex: Math.max(1, Number(current.currentSetIndex || 1)),
      skippedExerciseKeys: Array.isArray(current.skippedExerciseKeys) ? current.skippedExerciseKeys.map(String) : [],
      accumulatedPausedMs: Math.max(0, Number(current.accumulatedPausedMs || 0)),
      rest: current.rest && typeof current.rest === "object" ? { ...current.rest } : null
    };
    return session.focus;
  }

  function phase3LoadLocal() {
    try {
      const raw = localStorage.getItem(phase3StorageKey());
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        phase3State.activeSession = parsed.activeSession || phase3State.activeSession;
        phase3State.plans = Array.isArray(parsed.localPlans) ? parsed.localPlans : phase3State.plans;
        phase3State.history = Array.isArray(parsed.localHistory) ? parsed.localHistory : phase3State.history;
        phase3State.pendingPlanRetry = parsed.pendingPlanRetry || phase3State.pendingPlanRetry;
      }
    } catch {
      phase3State.syncMessage = phase3Text("localSafe");
    }
  }

  function phase3SaveLocal() {
    try {
      localStorage.setItem(phase3StorageKey(), JSON.stringify({
        activeSession: phase3State.activeSession,
        localPlans: phase3State.plans.filter((plan) => plan.localOnly),
        localHistory: phase3State.history.filter((entry) => entry.localOnly).slice(0, 20),
        pendingPlanRetry: phase3State.pendingPlanRetry
      }));
    } catch {
      phase3State.syncMessage = phase3Text("localSafe");
    }
  }

  function phase3EnsureUserContext() {
    const nextKey = phase3CurrentUserKey();
    if (phase3UserKey === nextKey) return;
    phase3StopTimer();
    phase3UserKey = nextKey;
    phase3State = phase3EmptyState();
    phase3ResetPlanEditor();
    phase3OpenTrainingSection = "plans";
    phase3PlanView = "active";
    phase3PlanFeedback = null;
    phase3LibraryFilters = { search: "", category: "", equipment: "" };
    phase3FocusOpen = false;
    phase3HistoryDetailId = "";
    phase3CloseExercisePicker();
    phase3RemoveFocusPortal();
    phase3RemoveHistoryPortal();
    phase3LoadRestVibrationPreference();
    phase3LoadLocal();
  }

  function phase3UsesSupabase() {
    return Boolean(isOnlineMode() && supabaseClient && onlineProfile?.role === "client" && onlineProfile?.id);
  }

  function phase3MigrationMissing(error) {
    return /fmz_phase3_create_training_plan|training_plans|workout_sessions|workout_set_logs|public\.exercises|exercise_id|schema cache|not find|does not exist|relation/i.test(error?.message || "");
  }

  function phase3PlanFromRow(row, daysByPlan, exercisesByDay) {
    const days = (daysByPlan[row.id] || []).map((day) => ({
      id: day.id,
      label: day.day_label,
      order: day.day_order,
      status: day.status || "active",
      archivedAt: day.archived_at || "",
      notes: day.notes || "",
      exercises: (exercisesByDay[day.id] || []).map((exercise) => ({
        id: exercise.id,
        key: exercise.id,
        exerciseId: exercise.exercise_id || phase3Exercise(exercise.exercise_slug)?.id || "",
        catalogBacked: phase3IsUuid(exercise.exercise_id),
        canonicalSlug: exercise.exercise_slug,
        slug: exercise.exercise_slug,
        name: exercise.exercise_name_snapshot,
        primaryMuscle: phase3ExerciseMeta(exercise.exercise_slug).primary,
        secondaryMuscles: phase3ExerciseMeta(exercise.exercise_slug).secondary,
        equipment: phase3ExerciseMeta(exercise.exercise_slug).equipment,
        order: exercise.exercise_order,
        status: exercise.status || "active",
        archivedAt: exercise.archived_at || "",
        targetSets: exercise.target_sets,
        targetReps: exercise.target_reps,
        targetWeight: exercise.target_weight ?? "",
        targetRir: exercise.target_rir ?? "",
        targetRpe: exercise.target_rpe ?? "",
        restSeconds: exercise.rest_seconds,
        tempo: exercise.tempo || "",
        notes: exercise.notes || ""
      }))
    }));
    return {
      id: row.id,
      title: row.title,
      status: row.status,
      source: row.source,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
      days,
      localOnly: false
    };
  }

  async function phase3HydrateTraining(profile) {
    if (!profile || profile.role !== "client" || !phase3UsesSupabase() || phase3Hydrating) return false;
    phase3Hydrating = true;
    try {
      const { data: plans, error: planError } = await supabaseClient
        .from("training_plans")
        .select("id,title,status,source,created_at,updated_at")
        .eq("user_id", profile.id)
        .order("created_at", { ascending: false });
      if (planError) throw planError;

      const planIds = (plans || []).map((plan) => plan.id);
      let days = [];
      let exercises = [];
      if (planIds.length) {
        const dayResult = await supabaseClient
          .from("training_plan_days")
          .select("id,training_plan_id,day_label,day_order,status,archived_at,notes")
          .in("training_plan_id", planIds)
          .order("day_order", { ascending: true });
        if (dayResult.error) throw dayResult.error;
        days = dayResult.data || [];
        const dayIds = days.map((day) => day.id);
        if (dayIds.length) {
          const exerciseResult = await supabaseClient
            .from("training_plan_exercises")
            .select("id,training_plan_day_id,exercise_id,exercise_slug,exercise_name_snapshot,exercise_order,status,archived_at,target_sets,target_reps,target_weight,target_rir,target_rpe,rest_seconds,tempo,notes")
            .in("training_plan_day_id", dayIds)
            .order("exercise_order", { ascending: true });
          if (exerciseResult.error) throw exerciseResult.error;
          exercises = exerciseResult.data || [];
        }
      }

      const { data: sessions, error: sessionError } = await supabaseClient
        .from("workout_sessions")
        .select("id,user_id,training_plan_id,training_plan_day_id,local_session_key,status,title_snapshot,day_label,started_at,paused_at,resumed_at,completed_at,source,metadata")
        .eq("user_id", profile.id)
        .order("started_at", { ascending: false })
        .limit(25);
      if (sessionError) throw sessionError;

      const sessionIds = (sessions || []).map((session) => session.id);
      let setLogs = [];
      if (sessionIds.length) {
        const setResult = await supabaseClient
          .from("workout_set_logs")
            .select("id,user_id,workout_session_id,training_plan_exercise_id,exercise_id,planned_exercise_key,exercise_slug,exercise_name_snapshot,set_index,target_reps,target_weight,actual_reps,actual_weight,rir,rpe,notes,completed_at,source,metadata")
          .in("workout_session_id", sessionIds);
        if (setResult.error) throw setResult.error;
        setLogs = setResult.data || [];
      }

      const daysByPlan = {};
      days.forEach((day) => {
        daysByPlan[day.training_plan_id] ||= [];
        daysByPlan[day.training_plan_id].push(day);
      });
      const exercisesByDay = {};
      exercises.forEach((exercise) => {
        exercisesByDay[exercise.training_plan_day_id] ||= [];
        exercisesByDay[exercise.training_plan_day_id].push(exercise);
      });
      const setsBySession = {};
      setLogs.forEach((setLog) => {
        setsBySession[setLog.workout_session_id] ||= [];
        setsBySession[setLog.workout_session_id].push(setLog);
      });

      const localActive = phase3State.activeSession;
      const localPlans = phase3State.plans.filter((plan) => plan.localOnly);
      const localHistory = phase3State.history.filter((entry) => entry.localOnly);
      const hydratedPlans = (plans || []).map((plan) => phase3PlanFromRow(plan, daysByPlan, exercisesByDay));
      const hydratedHistory = (sessions || [])
        .filter((session) => session.status === "completed")
        .map((session) => ({
          id: session.id,
          title: session.title_snapshot,
          dayLabel: session.day_label || "",
          startedAt: session.started_at,
          completedAt: session.completed_at,
          source: session.source,
          metadata: session.metadata || {},
          durationSeconds: phase3CompletedDurationSeconds(session.started_at, session.completed_at, session.metadata?.focus),
          sets: setsBySession[session.id] || []
        }));
      phase3State.plans = [
        ...hydratedPlans,
        ...localPlans.filter((localPlan) => !hydratedPlans.some((plan) => plan.id === localPlan.id))
      ];
      phase3State.history = [
        ...hydratedHistory,
        ...localHistory.filter((localEntry) => !hydratedHistory.some((entry) => entry.id === localEntry.id))
      ];
      const active = (sessions || []).find((session) => session.status === "active" || session.status === "paused");
      if (active && !localActive) {
        phase3State.activeSession = phase3SessionFromDb(active, setsBySession[active.id] || []);
        phase3FocusOpen = true;
      } else if (localActive) {
        phase3State.activeSession = localActive;
        phase3EnsureSessionFocus(localActive);
        phase3SyncActiveSession();
      }
      phase3State.hydrated = true;
      phase3State.migrationReady = true;
      phase3State.syncMessage = phase3Text("synced");
      phase3SaveLocal();
      return true;
    } catch (error) {
      phase3State.hydrated = true;
      phase3State.migrationReady = !phase3MigrationMissing(error);
      phase3State.syncMessage = phase3MigrationMissing(error) ? phase3Text("localSafe") : phase3Format("saveFailed", { message: error.message });
      console.warn("Phase 3 training hydrate skipped", error);
      return false;
    } finally {
      phase3Hydrating = false;
    }
  }

  function phase3SessionFromDb(session, setLogs) {
    const setMap = {};
    setLogs.forEach((setLog) => {
      setMap[`${setLog.planned_exercise_key}__${setLog.set_index}`] = {
        id: setLog.id,
        plannedExerciseKey: setLog.planned_exercise_key,
        exerciseSlug: setLog.exercise_slug,
        exerciseId: setLog.exercise_id || "",
        catalogBacked: phase3IsUuid(setLog.exercise_id),
        exerciseName: setLog.exercise_name_snapshot,
        setIndex: setLog.set_index,
        targetReps: setLog.target_reps || "",
        targetWeight: setLog.target_weight ?? "",
        actualReps: setLog.actual_reps ?? "",
        actualWeight: setLog.actual_weight ?? "",
        rir: setLog.rir ?? "",
        rpe: setLog.rpe ?? "",
        notes: setLog.notes || "",
        completedAt: setLog.completed_at,
        syncedAt: phase3IsoNow()
      };
    });
    return {
      id: session.id,
      localSessionKey: session.local_session_key,
      status: session.status,
      planId: session.training_plan_id || "",
      dayId: session.training_plan_day_id || "",
      planTitle: session.title_snapshot,
      dayLabel: session.day_label || "",
      source: session.source,
      startedAt: session.started_at,
      pausedAt: session.paused_at || "",
      resumedAt: session.resumed_at || "",
      completedAt: session.completed_at || "",
      plannedExercises: Array.isArray(session.metadata?.plannedExercises) ? session.metadata.plannedExercises : [],
      setLogs: setMap,
      focus: {
        ...phase3DefaultFocusState(),
        ...(session.metadata?.focus || {}),
        accumulatedPausedMs: Math.max(0, Number(session.metadata?.focus?.accumulatedPausedMs || 0))
      }
    };
  }

  function phase3ExerciseInsertRow(dayId, exercise, order) {
    const canonicalExerciseId = exercise.catalogBacked && phase3IsUuid(exercise.exerciseId) ? exercise.exerciseId : "";
    return {
      id: phase3EnsureDbId(exercise.id, "training_plan_exercises.id"),
      training_plan_day_id: dayId,
      ...(canonicalExerciseId ? { exercise_id: canonicalExerciseId } : {}),
      exercise_slug: exercise.slug,
      exercise_name_snapshot: exercise.name,
      exercise_order: order,
      status: "active",
      target_sets: exercise.targetSets,
      target_reps: exercise.targetReps,
      target_weight: exercise.targetWeight === "" ? null : exercise.targetWeight,
      target_rir: exercise.targetRir === "" ? null : exercise.targetRir,
      target_rpe: exercise.targetRpe === "" ? null : exercise.targetRpe,
      rest_seconds: exercise.restSeconds,
      tempo: exercise.tempo || null,
      notes: exercise.notes || null
    };
  }

  async function phase3PersistFirstExerciseCatalogLink(dayId, exercise) {
    if (!exercise?.catalogBacked || !phase3IsUuid(exercise.exerciseId)) return { ok: true, skipped: true };
    const { error } = await supabaseClient
      .from("training_plan_exercises")
      .update({ exercise_id: exercise.exerciseId })
      .eq("id", exercise.id)
      .eq("training_plan_day_id", dayId);
    if (error) throw error;
    return { ok: true };
  }

  function phase3EnsurePlanDbIds(plan) {
    if (!plan || plan.source === "legacy_bridge") return plan;
    plan.id = phase3EnsureDbId(plan.id, "training_plans.id");
    (plan.days || []).forEach((day) => {
      day.id = phase3EnsureDbId(day.id, "training_plan_days.id");
      (day.exercises || []).forEach((exercise) => {
        exercise.id = phase3EnsureDbId(exercise.id, "training_plan_exercises.id");
        exercise.key = exercise.key || exercise.id;
      });
    });
    return plan;
  }

  function phase3EnsureSessionDbIds(session) {
    if (!session) return session;
    session.id = phase3EnsureDbId(session.id, "workout_sessions.id");
    Object.values(session.setLogs || {}).forEach((setLog) => {
      setLog.id = phase3EnsureDbId(setLog.id, "workout_set_logs.id");
      if (!phase3IsUuid(setLog.trainingPlanExerciseId)) setLog.trainingPlanExerciseId = "";
    });
    return session;
  }

  async function phase3PersistRemainingExercises(day) {
    const remainingExercises = (day.exercises || []).slice(1);
    if (!remainingExercises.length) return { ok: true };
    const { error } = await supabaseClient
      .from("training_plan_exercises")
      .upsert(remainingExercises.map((item, index) => phase3ExerciseInsertRow(day.id, item, index + 1)), { onConflict: "id" });
    if (error) throw error;
    return { ok: true };
  }

  async function phase3HydrateAfterPartialPlanFailure(plan, error, mode = "create") {
    const pending = {
      plan,
      mode,
      failedAt: phase3IsoNow(),
      message: error?.message || phase3Text("partialSave")
    };
    phase3State.pendingPlanRetry = pending;
    phase3State.syncMessage = phase3Text("partialSave");
    if (onlineProfile?.role === "client") {
      await phase3HydrateTraining(onlineProfile);
      phase3State.pendingPlanRetry = pending;
      phase3State.syncMessage = phase3Text("partialSave");
    }
    phase3SaveLocal();
  }

  async function phase3RetryPendingPlanSave() {
    const pending = phase3State.pendingPlanRetry;
    const plan = pending?.plan;
    const day = plan?.days?.[0];
    if (!plan || !day || !phase3UsesSupabase()) return { ok: false, error: new Error(phase3Text("saveFailed")) };
    if (pending.mode === "edit") return phase3PersistEditedPlan(plan);
    try {
      phase3EnsurePlanDbIds(plan);
      phase3State.syncMessage = phase3Text("partialRetrying");
      await phase3PersistRemainingExercises(day);
      phase3State.pendingPlanRetry = null;
      if (onlineProfile?.role === "client") await phase3HydrateTraining(onlineProfile);
      phase3State.syncMessage = phase3Text("synced");
      phase3SaveLocal();
      return { ok: true };
    } catch (error) {
      await phase3HydrateAfterPartialPlanFailure(plan, error);
      return { ok: false, partial: true, error };
    }
  }

  async function phase3PersistPlan(plan) {
    phase3EnsurePlanDbIds(plan);
    if (!phase3UsesSupabase()) {
      plan.localOnly = true;
      phase3State.plans.unshift(plan);
      phase3SaveLocal();
      return { ok: true, local: true };
    }
    try {
      const day = plan.days[0];
      const exercise = day.exercises[0];
      const { error: planError } = await supabaseClient.rpc("fmz_phase3_create_training_plan", {
        p_plan_id: plan.id,
        p_day_id: day.id,
        p_plan_exercise_id: exercise.id,
        p_title: plan.title,
        p_day_label: day.label,
        p_day_order: day.order,
        p_exercise_slug: exercise.slug,
        p_exercise_name: exercise.name,
        p_target_sets: exercise.targetSets,
        p_target_reps: exercise.targetReps,
        p_target_weight: exercise.targetWeight === "" ? null : exercise.targetWeight,
        p_target_rir: exercise.targetRir === "" ? null : exercise.targetRir,
        p_target_rpe: exercise.targetRpe === "" ? null : exercise.targetRpe,
        p_rest_seconds: exercise.restSeconds,
        p_notes: exercise.notes || null
      });
      if (planError) throw planError;

      try {
        await phase3PersistFirstExerciseCatalogLink(day.id, exercise);
        await phase3PersistRemainingExercises(day);
      } catch (exerciseError) {
        await phase3HydrateAfterPartialPlanFailure(plan, exerciseError);
        return { ok: false, partial: true, error: exerciseError };
      }

      phase3State.pendingPlanRetry = null;
      plan.localOnly = false;
      phase3State.plans.unshift(plan);
      phase3State.migrationReady = true;
      phase3State.syncMessage = phase3Text("synced");
      phase3SaveLocal();
      return { ok: true };
    } catch (error) {
      if (phase3MigrationMissing(error)) {
        plan.localOnly = true;
        phase3State.migrationReady = false;
        phase3State.plans.unshift(plan);
        phase3State.syncMessage = phase3Text("localSafe");
        phase3SaveLocal();
        return { ok: true, local: true };
      }
      return { ok: false, error };
    }
  }

  async function phase3PersistEditedPlan(plan) {
    phase3EnsurePlanDbIds(plan);
    const day = plan.days?.find((item) => item.id === phase3EditingDayId) || plan.days?.[0];
    if (!day) return { ok: false, error: new Error("Workout day missing") };

    if (!phase3UsesSupabase() || plan.localOnly) {
      const planIndex = phase3State.plans.findIndex((item) => item.id === plan.id);
      if (planIndex < 0) return { ok: false, error: new Error("Workout not found") };
      plan.localOnly = true;
      phase3State.plans[planIndex] = plan;
      phase3State.pendingPlanRetry = null;
      phase3SaveLocal();
      return { ok: true, local: true };
    }

    try {
      const { error: planError } = await supabaseClient
        .from("training_plans")
        .update({ title: plan.title })
        .eq("id", plan.id)
        .eq("user_id", phase3ProfileId());
      if (planError) throw planError;

      const { error: dayError } = await supabaseClient
        .from("training_plan_days")
        .update({ day_label: day.label, day_order: day.order })
        .eq("id", day.id)
        .eq("training_plan_id", plan.id);
      if (dayError) throw dayError;

      const { error: archiveError } = await supabaseClient
        .from("training_plan_exercises")
        .update({ status: "archived" })
        .eq("training_plan_day_id", day.id)
        .eq("status", "active");
      if (archiveError) throw archiveError;

      const exerciseRows = (day.exercises || []).map((exercise, index) => phase3ExerciseInsertRow(day.id, exercise, index));
      const { error: exerciseError } = await supabaseClient
        .from("training_plan_exercises")
        .upsert(exerciseRows, { onConflict: "id" });
      if (exerciseError) throw exerciseError;

      phase3State.pendingPlanRetry = null;
      if (onlineProfile?.role === "client") await phase3HydrateTraining(onlineProfile);
      phase3State.syncMessage = phase3Text("synced");
      phase3SaveLocal();
      return { ok: true };
    } catch (error) {
      await phase3HydrateAfterPartialPlanFailure(plan, error, "edit");
      return { ok: false, partial: true, error };
    }
  }

  async function phase3ArchivePlan(planId) {
    const plan = phase3State.plans.find((item) => item.id === planId);
    if (!plan || plan.source === "legacy_bridge") return { ok: true };
    if (phase3UsesSupabase() && !plan.localOnly) {
      const { error } = await supabaseClient
        .from("training_plans")
        .update({ status: "archived" })
        .eq("id", plan.id)
        .eq("user_id", phase3ProfileId());
      if (error) return { ok: false, error };
    }
    plan.status = "archived";
    plan.updatedAt = phase3IsoNow();
    if (phase3State.pendingPlanRetry?.plan?.id === plan.id) {
      phase3State.pendingPlanRetry = null;
    }
    phase3SaveLocal();
    return { ok: true };
  }

  async function phase3RestorePlan(planId) {
    const plan = phase3State.plans.find((item) => item.id === planId);
    if (!plan || plan.source === "legacy_bridge" || plan.status !== "archived") return { ok: false, error: new Error("Archived workout not found") };

    if (phase3UsesSupabase() && !plan.localOnly) {
      const { error } = await supabaseClient
        .from("training_plans")
        .update({ status: "active" })
        .eq("id", plan.id)
        .eq("user_id", phase3ProfileId());
      if (error) return { ok: false, limit: phase3IsFreeLimitError(error), error };
    } else if (!phase3CanActivatePlanLocally(plan)) {
      return { ok: false, limit: true, error: new Error(phase3Text("restoreLimitReached")) };
    }

    plan.status = "active";
    plan.updatedAt = phase3IsoNow();
    phase3SaveLocal();
    return { ok: true };
  }

  async function phase3ArchivePlanExercise(planId, dayId, exerciseId) {
    const plan = phase3State.plans.find((item) => item.id === planId);
    const day = plan?.days?.find((item) => item.id === dayId);
    const exercise = day?.exercises?.find((item) => item.id === exerciseId);
    if (!plan || !day || !exercise || plan.source === "legacy_bridge") return { ok: true };
    if (phase3UsesSupabase() && !plan.localOnly && phase3IsUuid(exercise.id)) {
      const { error } = await supabaseClient
        .from("training_plan_exercises")
        .update({ status: "archived" })
        .eq("id", exercise.id)
        .eq("training_plan_day_id", day.id);
      if (error) return { ok: false, error };
    }
    exercise.status = "archived";
    exercise.archivedAt = phase3IsoNow();
    phase3SaveLocal();
    return { ok: true };
  }

  function phase3ExerciseFromForm(form, order = 0, id = phase3DbId(), current = null) {
    const data = new FormData(form);
    const slug = String(data.get("exerciseSlug") || PHASE3_EXERCISES[0].slug);
    const meta = phase3ExerciseMeta(slug);
    const keepsCurrentIdentity = current?.slug === slug && current?.catalogBacked && phase3IsUuid(current.exerciseId);
    return {
      id,
      key: id,
      exerciseId: meta.catalogBacked ? meta.id : (keepsCurrentIdentity ? current.exerciseId : ""),
      catalogBacked: Boolean(meta.catalogBacked || keepsCurrentIdentity),
      canonicalSlug: meta.canonicalSlug || current?.canonicalSlug || slug,
      slug,
      name: meta.name,
      primaryMuscle: meta.primary,
      secondaryMuscles: meta.secondary,
      equipment: meta.equipment,
      order,
      status: "active",
      archivedAt: "",
      targetSets: Math.max(1, Math.min(20, phase3Number(data.get("sets"), 3))),
      targetReps: String(data.get("reps") || "8-10").slice(0, 40),
      targetWeight: phase3Number(data.get("targetWeight"), ""),
      targetRir: phase3Number(data.get("targetRir"), ""),
      targetRpe: phase3Number(data.get("targetRpe"), ""),
      restSeconds: Math.max(0, Math.min(3600, phase3Number(data.get("restSeconds"), 90))),
      tempo: "",
      notes: String(data.get("notes") || "").trim().slice(0, 500)
    };
  }

  function phase3NormalizeBuilderExercises() {
    phase3BuilderExercises = phase3BuilderExercises
      .filter((exercise) => exercise && (exercise.status || "active") === "active")
      .map((exercise, index) => ({
        ...exercise,
        key: exercise.key || exercise.id,
        order: index
      }));
  }

  function phase3AddBuilderExercise(form) {
    phase3CaptureBuilderDraft(form);
    if (phase3BuilderEditIndex !== null && phase3BuilderExercises[phase3BuilderEditIndex]) {
      const current = phase3BuilderExercises[phase3BuilderEditIndex];
      phase3BuilderExercises[phase3BuilderEditIndex] = phase3ExerciseFromForm(form, current.order, current.id, current);
      phase3BuilderEditIndex = null;
    } else {
      phase3BuilderExercises.push(phase3ExerciseFromForm(form, phase3BuilderExercises.length));
    }
    phase3NormalizeBuilderExercises();
  }

  function phase3RemoveBuilderExercise(index) {
    phase3BuilderExercises.splice(index, 1);
    if (phase3BuilderEditIndex === index) phase3BuilderEditIndex = null;
    if (phase3BuilderEditIndex !== null && phase3BuilderEditIndex > index) phase3BuilderEditIndex -= 1;
    phase3NormalizeBuilderExercises();
  }

  function phase3MoveBuilderExercise(index, direction) {
    const target = index + direction;
    if (target < 0 || target >= phase3BuilderExercises.length) return;
    const current = phase3BuilderExercises[index];
    phase3BuilderExercises[index] = phase3BuilderExercises[target];
    phase3BuilderExercises[target] = current;
    if (phase3BuilderEditIndex === index) phase3BuilderEditIndex = target;
    else if (phase3BuilderEditIndex === target) phase3BuilderEditIndex = index;
    phase3NormalizeBuilderExercises();
  }

  function phase3EditBuilderExercise(index) {
    const exercise = phase3BuilderExercises[index];
    if (!exercise) return;
    phase3BuilderEditIndex = index;
    phase3BuilderDraft = {
      ...phase3BuilderDraft,
      exerciseSlug: exercise.slug,
      sets: String(exercise.targetSets || "3"),
      reps: String(exercise.targetReps || "8-10"),
      targetWeight: exercise.targetWeight === "" ? "" : String(exercise.targetWeight),
      targetRir: exercise.targetRir === "" ? "" : String(exercise.targetRir),
      targetRpe: exercise.targetRpe === "" ? "" : String(exercise.targetRpe),
      restSeconds: String(exercise.restSeconds || 90),
      notes: exercise.notes || ""
    };
  }

  function phase3CancelBuilderEdit(form) {
    phase3CaptureBuilderDraft(form);
    phase3BuilderEditIndex = null;
    phase3BuilderDraft = {
      ...phase3BuilderDraft,
      exerciseSlug: PHASE3_EXERCISES[0]?.slug || "",
      sets: "3",
      reps: "8-10",
      targetWeight: "",
      targetRir: "",
      targetRpe: "",
      restSeconds: "90",
      notes: ""
    };
  }

  function phase3BuilderExercisesForSubmit(form) {
    if (phase3BuilderEditIndex !== null && phase3BuilderExercises[phase3BuilderEditIndex]) {
      phase3AddBuilderExercise(form);
    }
    phase3NormalizeBuilderExercises();
    if (phase3BuilderExercises.length) {
      return phase3BuilderExercises.map((exercise, index) => {
        const id = phase3EnsureDbId(exercise.id, "training_plan_exercises.id");
        return {
          ...exercise,
          id,
          key: exercise.key || id,
          order: index
        };
      });
    }
    return [phase3ExerciseFromForm(form, 0)];
  }

  function phase3BuildPlanFromForm(form) {
    phase3CaptureBuilderDraft(form);
    const data = new FormData(form);
    const planId = phase3DbId();
    const dayId = phase3DbId();
    const dayLabel = String(data.get("dayLabel") || "Maandag");
    const exercises = phase3BuilderExercisesForSubmit(form);
    return {
      id: planId,
      title: String(data.get("title") || "").trim() || phase3Text("createPlan"),
      status: "active",
      source: "phase3_client",
      createdAt: phase3IsoNow(),
      updatedAt: phase3IsoNow(),
      days: [{
        id: dayId,
        label: dayLabel,
        order: phase3DayOrder(dayLabel),
        status: "active",
        archivedAt: "",
        notes: "",
        exercises
      }],
      localOnly: false
    };
  }

  function phase3ResetPlanEditor() {
    phase3EditingPlanId = "";
    phase3EditingDayId = "";
    phase3BuilderExercises = [];
    phase3BuilderEditIndex = null;
    phase3BuilderDraft = phase3EmptyBuilderDraft();
  }

  function phase3BeginPlanEdit(planId) {
    const plan = phase3State.plans.find((item) => item.id === planId && item.status === "active" && item.source !== "legacy_bridge");
    const day = plan?.days?.find((item) => (item.status || "active") === "active");
    if (!plan || !day) return false;
    const activeExercises = (day.exercises || []).filter((exercise) => (exercise.status || "active") === "active");
    phase3EditingPlanId = plan.id;
    phase3EditingDayId = day.id;
    phase3BuilderExercises = activeExercises.map((exercise, index) => {
      const meta = phase3ExerciseMeta(exercise.slug);
      return {
        ...exercise,
        key: exercise.key || exercise.id,
        exerciseId: exercise.exerciseId || (meta.catalogBacked ? meta.id : ""),
        catalogBacked: Boolean(exercise.catalogBacked || (meta.catalogBacked && phase3IsUuid(meta.id))),
        canonicalSlug: exercise.canonicalSlug || meta.canonicalSlug,
        order: index
      };
    });
    const first = phase3BuilderExercises[0];
    phase3BuilderEditIndex = first ? 0 : null;
    phase3BuilderDraft = {
      ...phase3EmptyBuilderDraft(),
      title: plan.title,
      dayLabel: day.label,
      ...(first ? {
        exerciseSlug: first.slug,
        sets: String(first.targetSets || "3"),
        reps: String(first.targetReps || "8-10"),
        targetWeight: first.targetWeight === "" ? "" : String(first.targetWeight),
        targetRir: first.targetRir === "" ? "" : String(first.targetRir),
        targetRpe: first.targetRpe === "" ? "" : String(first.targetRpe),
        restSeconds: String(first.restSeconds ?? 90),
        notes: first.notes || ""
      } : {})
    };
    phase3OpenTrainingSection = "builder";
    phase3PlanFeedback = null;
    return true;
  }

  function phase3BuildEditedPlanFromForm(form) {
    phase3CaptureBuilderDraft(form);
    const current = phase3State.plans.find((item) => item.id === phase3EditingPlanId);
    const currentDay = current?.days?.find((item) => item.id === phase3EditingDayId);
    if (!current || !currentDay) return null;
    const data = new FormData(form);
    const dayLabel = String(data.get("dayLabel") || currentDay.label || "Maandag");
    const exercises = phase3BuilderExercisesForSubmit(form);
    return {
      ...current,
      title: String(data.get("title") || "").trim() || current.title,
      updatedAt: phase3IsoNow(),
      days: (current.days || []).map((day) => day.id === currentDay.id ? {
        ...day,
        label: dayLabel,
        order: phase3DayOrder(dayLabel),
        exercises
      } : day)
    };
  }

  function phase3LegacyPlan() {
    const selected = client();
    const rows = Array.isArray(selected?.trainingPlan) ? selected.trainingPlan : [];
    const visible = rows.filter((exercise) => exercise.published !== false);
    if (!visible.length) return null;
    const days = DAYS.map((day, dayIndex) => {
      const exercises = visible
        .map((exercise, index) => ({ exercise, index }))
        .filter(({ exercise }) => (exercise.day || "Maandag") === day)
        .map(({ exercise, index }) => ({
          id: `legacy-ex-${index}`,
          key: `legacy-ex-${index}`,
          slug: phase3Slugify(exercise.exercise || `legacy-${index}`),
          name: exercise.exercise || phase3Text("exercise"),
          order: index,
          status: "active",
          archivedAt: "",
          targetSets: Math.max(1, phase3Number(exercise.sets, 1)),
          targetReps: String(exercise.reps || "8-10"),
          targetWeight: exercise.targetWeight ?? "",
          targetRir: "",
          targetRpe: "",
          restSeconds: phase3RestSeconds(exercise.rest),
          tempo: exercise.tempo || "",
          notes: exercise.notes || ""
        }));
      return {
        id: `legacy-day-${dayIndex}`,
        label: day,
        order: dayIndex,
        status: "active",
        archivedAt: "",
        notes: "",
        exercises
      };
    }).filter((day) => day.exercises.length);
    return {
      id: "legacy-bridge-plan",
      title: phase3Text("legacyPlan"),
      status: "active",
      source: "legacy_bridge",
      createdAt: "",
      updatedAt: "",
      days
    };
  }

  function phase3PlansForDisplay() {
    const legacy = phase3LegacyPlan();
    return legacy ? [...phase3State.plans, legacy] : phase3State.plans.slice();
  }

  function phase3Slugify(value) {
    return String(value || "exercise")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 90) || "exercise";
  }

  function phase3RestSeconds(value) {
    const match = String(value || "").match(/\d+/);
    return match ? Math.max(0, Math.min(3600, Number(match[0]))) : 90;
  }

  function phase3CreateSession(plan, day) {
    const id = phase3DbId();
    const startedAt = phase3IsoNow();
    const plannedExercises = (day.exercises || [])
      .filter((exercise) => (exercise.status || "active") === "active")
      .map((exercise, index) => ({
      ...exercise,
      key: exercise.key || exercise.id || `${exercise.slug}-${index}`,
      instructions: phase3ExerciseMeta(exercise.slug).instructions
    }));
    return {
      id,
      localSessionKey: `${phase3CurrentUserKey()}-${plan.id}-${day.id}-${startedAt}`,
      status: "active",
      planId: plan.source === "legacy_bridge" ? "" : plan.id,
      dayId: plan.source === "legacy_bridge" ? "" : day.id,
      planTitle: plan.title,
      dayLabel: day.label,
      source: plan.source === "legacy_bridge" ? "legacy_bridge" : "phase3_client",
      startedAt,
      pausedAt: "",
      resumedAt: "",
      completedAt: "",
      plannedExercises,
      setLogs: {},
      focus: phase3DefaultFocusState()
    };
  }

  async function phase3StartWorkout(planId, dayId) {
    const plan = phase3PlansForDisplay().find((item) => item.id === planId);
    const day = plan?.days
      .filter((item) => (item.status || "active") === "active")
      .find((item) => item.id === dayId);
    const activeExercises = (day?.exercises || []).filter((exercise) => (exercise.status || "active") === "active");
    if (!plan || !day || !activeExercises.length) return;
    if (phase3State.activeSession && ["active", "paused"].includes(phase3State.activeSession.status)) {
      renderTraining();
      return;
    }
    await phase3LoadExerciseDetails(activeExercises.map((exercise) => phase3ExerciseById(exercise.exerciseId) || phase3Exercise(exercise.slug)).filter(Boolean));
    phase3State.activeSession = phase3CreateSession(plan, { ...day, exercises: activeExercises });
    phase3FocusOpen = true;
    phase3SaveLocal();
    await phase3SyncActiveSession();
    renderTraining();
  }

  async function phase3SyncActiveSession() {
    const session = phase3State.activeSession;
    if (!session || !phase3UsesSupabase()) return { ok: false, skipped: true };
    try {
      phase3EnsureSessionDbIds(session);
      const { error } = await supabaseClient
        .from("workout_sessions")
        .upsert({
          id: session.id,
          user_id: phase3ProfileId(),
          training_plan_id: session.planId || null,
          training_plan_day_id: session.dayId || null,
          local_session_key: session.localSessionKey,
          status: session.status,
          title_snapshot: session.planTitle,
          day_label: session.dayLabel || null,
          started_at: session.startedAt,
          paused_at: session.pausedAt || null,
          resumed_at: session.resumedAt || null,
          completed_at: session.completedAt || null,
          source: session.source,
          metadata: {
            phase: 3,
            version: PHASE3_VERSION,
            plannedExercises: session.plannedExercises,
            focus: phase3EnsureSessionFocus(session)
          }
        }, { onConflict: "id" });
      if (error) throw error;
      const unsynced = Object.values(session.setLogs || {}).filter((setLog) => !setLog.syncedAt);
      for (const setLog of unsynced) {
        const setResult = await phase3PersistSetLog(setLog);
        if (!setResult.ok) throw setResult.error || new Error("Phase 3 set sync failed");
      }
      phase3State.migrationReady = true;
      phase3State.syncMessage = phase3Text("synced");
      phase3SaveLocal();
      return { ok: true };
    } catch (error) {
      phase3State.syncMessage = phase3MigrationMissing(error) ? phase3Text("localSafe") : phase3Format("saveFailed", { message: error.message });
      phase3SaveLocal();
      console.warn("Phase 3 workout sync skipped", error);
      return { ok: false, error };
    }
  }

  async function phase3PersistSetLog(setLog) {
    if (!phase3UsesSupabase() || !phase3State.activeSession) return { ok: false, skipped: true };
    try {
      const { error } = await supabaseClient
        .from("workout_set_logs")
        .upsert({
          id: setLog.id,
          user_id: phase3ProfileId(),
          workout_session_id: phase3State.activeSession.id,
          training_plan_exercise_id: phase3IsUuid(setLog.trainingPlanExerciseId) ? setLog.trainingPlanExerciseId : null,
          ...(setLog.catalogBacked && phase3IsUuid(setLog.exerciseId) ? { exercise_id: setLog.exerciseId } : {}),
          planned_exercise_key: setLog.plannedExerciseKey,
          exercise_slug: setLog.exerciseSlug,
          exercise_name_snapshot: setLog.exerciseName,
          set_index: setLog.setIndex,
          target_reps: setLog.targetReps || null,
          target_weight: setLog.targetWeight === "" ? null : setLog.targetWeight,
          actual_reps: setLog.actualReps === "" ? null : setLog.actualReps,
          actual_weight: setLog.actualWeight === "" ? null : setLog.actualWeight,
          rir: setLog.rir === "" ? null : setLog.rir,
          rpe: setLog.rpe === "" ? null : setLog.rpe,
          notes: setLog.notes || null,
          completed_at: setLog.completedAt,
          source: setLog.source || phase3State.activeSession.source,
          metadata: {
            phase: 3,
            version: PHASE3_VERSION,
            exerciseId: setLog.exerciseId || "",
            canonicalSlug: setLog.exerciseSlug || ""
          }
        }, { onConflict: "workout_session_id,planned_exercise_key,set_index" });
      if (error) throw error;
      setLog.syncedAt = phase3IsoNow();
      phase3State.syncMessage = phase3Text("synced");
      phase3SaveLocal();
      return { ok: true };
    } catch (error) {
      phase3State.syncMessage = phase3MigrationMissing(error) ? phase3Text("localSafe") : phase3Format("saveFailed", { message: error.message });
      phase3SaveLocal();
      return { ok: false, error };
    }
  }

  function phase3SetKey(exercise, setIndex) {
    return `${exercise.key || exercise.id || exercise.slug}__${setIndex}`;
  }

  function phase3ReadSetInputs(setKey) {
    return {
      actualReps: phase3Number(document.querySelector(`[data-phase3-reps="${setKey}"]`)?.value, ""),
      actualWeight: phase3Number(document.querySelector(`[data-phase3-weight="${setKey}"]`)?.value, ""),
      rir: phase3Number(document.querySelector(`[data-phase3-rir="${setKey}"]`)?.value, ""),
      rpe: phase3Number(document.querySelector(`[data-phase3-rpe="${setKey}"]`)?.value, ""),
      notes: String(document.querySelector(`[data-phase3-notes="${setKey}"]`)?.value || "").trim().slice(0, 500)
    };
  }

  function phase3ValidateSetInputs(inputs) {
    const repsValid = Number.isInteger(inputs.actualReps) && inputs.actualReps >= 1;
    const weightValid = inputs.actualWeight === "" || (Number.isFinite(inputs.actualWeight) && inputs.actualWeight >= 0);
    const rirValid = inputs.rir === "" || (Number.isFinite(inputs.rir) && inputs.rir >= 0 && inputs.rir <= 10);
    const rpeValid = inputs.rpe === "" || (Number.isFinite(inputs.rpe) && inputs.rpe >= 1 && inputs.rpe <= 10);
    return repsValid && weightValid && rirValid && rpeValid;
  }

  function phase3ExerciseKey(exercise) {
    return String(exercise?.key || exercise?.id || exercise?.slug || "");
  }

  function phase3NextExerciseIndex(session, startIndex) {
    const focus = phase3EnsureSessionFocus(session);
    for (let index = Math.max(0, startIndex); index < session.plannedExercises.length; index += 1) {
      if (!focus.skippedExerciseKeys.includes(phase3ExerciseKey(session.plannedExercises[index]))) return index;
    }
    return -1;
  }

  function phase3ApplyFocusStep(session, step, completedExercise = false) {
    const focus = phase3EnsureSessionFocus(session);
    focus.rest = null;
    phase3TimerEndsAt = 0;
    phase3LastVibrationSecond = null;
    if (!step || step.exerciseIndex < 0) {
      focus.allExercisesCompleted = true;
      focus.feedback = phase3Text("allExercisesCompleted");
      return;
    }
    focus.currentExerciseIndex = step.exerciseIndex;
    focus.currentSetIndex = step.setIndex;
    focus.allExercisesCompleted = false;
    focus.feedback = completedExercise ? phase3Text("exerciseCompleted") : "";
  }

  function phase3NextStepAfterSet(session, exercise, setIndex) {
    const exerciseIndex = session.plannedExercises.indexOf(exercise);
    const totalSets = Math.max(1, Number(exercise.targetSets || 1));
    if (setIndex < totalSets) return { exerciseIndex, setIndex: setIndex + 1, completedExercise: false };
    const nextExerciseIndex = phase3NextExerciseIndex(session, exerciseIndex + 1);
    return nextExerciseIndex >= 0
      ? { exerciseIndex: nextExerciseIndex, setIndex: 1, completedExercise: true }
      : { exerciseIndex: -1, setIndex: 1, completedExercise: true };
  }

  async function phase3CompleteSet(setKey) {
    const session = phase3State.activeSession;
    if (!session) return;
    const [exerciseKey, rawSetIndex] = setKey.split("__");
    const exercise = session.plannedExercises.find((item) => String(item.key) === exerciseKey);
    if (!exercise) return;
    const setIndex = Number(rawSetIndex);
    const inputs = phase3ReadSetInputs(setKey);
    const focus = phase3EnsureSessionFocus(session);
    if (!phase3ValidateSetInputs(inputs)) {
      focus.feedback = phase3Text("setValidationFailed");
      phase3SaveLocal();
      const feedback = document.querySelector("[data-phase3-focus-feedback]");
      if (feedback) {
        feedback.hidden = false;
        feedback.textContent = focus.feedback;
      }
      document.querySelector(`[data-phase3-reps="${setKey}"]`)?.reportValidity?.();
      return;
    }
    const setLog = {
      id: phase3IsUuid(session.setLogs[setKey]?.id) ? session.setLogs[setKey].id : phase3DbId(),
      plannedExerciseKey: String(exercise.key),
      trainingPlanExerciseId: phase3IsUuid(exercise.id) ? exercise.id : "",
      exerciseId: exercise.catalogBacked && phase3IsUuid(exercise.exerciseId) ? exercise.exerciseId : "",
      catalogBacked: exercise.catalogBacked === true,
      exerciseSlug: exercise.slug,
      exerciseName: exercise.name,
      setIndex,
      targetReps: exercise.targetReps || "",
      targetWeight: exercise.targetWeight === "" ? "" : phase3Number(exercise.targetWeight, ""),
      actualReps: inputs.actualReps,
      actualWeight: inputs.actualWeight,
      rir: inputs.rir,
      rpe: inputs.rpe,
      notes: inputs.notes,
      completedAt: phase3IsoNow(),
      source: session.source,
      syncedAt: ""
    };
    session.setLogs[setKey] = setLog;
    focus.feedback = "";
    phase3SaveLocal();
    const persisted = phase3UsesSupabase() ? await phase3PersistSetLog(setLog) : { ok: true, local: true };
    if (!persisted.ok) {
      focus.feedback = phase3Text("setSaveFailed");
      phase3SaveLocal();
      renderTraining();
      return;
    }
    const nextStep = phase3NextStepAfterSet(session, exercise, setIndex);
    phase3StartTimer(exercise.restSeconds || 0, nextStep);
    await phase3SyncActiveSession();
    renderTraining();
  }

  function phase3SkipCurrentExercise() {
    const session = phase3State.activeSession;
    if (!session) return;
    const focus = phase3EnsureSessionFocus(session);
    const exercise = session.plannedExercises[focus.currentExerciseIndex];
    if (!exercise) return;
    const key = phase3ExerciseKey(exercise);
    if (!focus.skippedExerciseKeys.includes(key)) focus.skippedExerciseKeys.push(key);
    const nextExerciseIndex = phase3NextExerciseIndex(session, focus.currentExerciseIndex + 1);
    phase3StopTimer();
    phase3ApplyFocusStep(session, nextExerciseIndex >= 0 ? { exerciseIndex: nextExerciseIndex, setIndex: 1 } : null);
    phase3SaveLocal();
    phase3SyncActiveSession();
    renderTraining();
  }

  async function phase3SetSessionStatus(status) {
    const session = phase3State.activeSession;
    if (!session) return;
    const focus = phase3EnsureSessionFocus(session);
    const now = phase3IsoNow();
    session.status = status;
    if (status === "paused" && !focus.pauseStartedAt) {
      session.pausedAt = now;
      focus.pauseStartedAt = now;
      phase3PauseRestTimer();
    }
    if (status === "active" && focus.pauseStartedAt) {
      focus.accumulatedPausedMs += Math.max(0, Date.now() - phase3TimestampMs(focus.pauseStartedAt));
      focus.pauseStartedAt = "";
      session.resumedAt = now;
      phase3ResumeRestTimer();
    }
    phase3SaveLocal();
    await phase3SyncActiveSession();
    renderTraining();
  }

  async function phase3CompleteWorkout() {
    const session = phase3State.activeSession;
    if (!session) return;
    const focus = phase3EnsureSessionFocus(session);
    const previousStatus = session.status;
    const previousCompletedAt = session.completedAt;
    if (focus.pauseStartedAt) {
      focus.accumulatedPausedMs += Math.max(0, Date.now() - phase3TimestampMs(focus.pauseStartedAt));
      focus.pauseStartedAt = "";
    }
    session.status = "completed";
    session.completedAt = phase3IsoNow();
    phase3StopTimer();
    const synced = await phase3SyncActiveSession();
    if (phase3UsesSupabase() && !synced.ok) {
      session.status = previousStatus;
      session.completedAt = previousCompletedAt;
      focus.feedback = phase3Text("setSaveFailed");
      phase3SaveLocal();
      phase3FocusOpen = true;
      renderTraining();
      return;
    }
    const historyEntry = {
      id: session.id,
      title: session.planTitle,
      dayLabel: session.dayLabel,
      startedAt: session.startedAt,
      completedAt: session.completedAt,
      source: session.source,
      localOnly: true,
      metadata: { focus },
      durationSeconds: phase3WorkoutElapsedSeconds(session),
      sets: Object.values(session.setLogs || {})
    };
    phase3State.history.unshift(historyEntry);
    phase3State.activeSession = null;
    phase3FocusOpen = false;
    phase3RemoveFocusPortal();
    phase3SaveLocal();
    renderTraining();
  }

  function phase3ExerciseIdentity(value) {
    const exerciseId = value?.exerciseId || value?.exercise_id || "";
    if (phase3IsUuid(exerciseId)) return `id:${exerciseId}`;
    const slug = value?.exerciseSlug || value?.exercise_slug || value?.slug || value?.canonicalSlug || "";
    return slug ? `slug:${slug}` : "";
  }

  function phase3SameExercise(left, right) {
    const leftId = left?.exerciseId || left?.exercise_id || "";
    const rightId = right?.exerciseId || right?.exercise_id || "";
    if (phase3IsUuid(leftId) && phase3IsUuid(rightId)) return leftId === rightId;
    const leftSlug = left?.exerciseSlug || left?.exercise_slug || left?.slug || "";
    const rightSlug = right?.exerciseSlug || right?.exercise_slug || right?.slug || "";
    return Boolean(leftSlug && rightSlug && leftSlug === rightSlug);
  }

  function phase3RecordCandidates(setLog) {
    const exerciseSlug = setLog.exerciseSlug || setLog.exercise_slug || "";
    const exerciseId = setLog.exerciseId || setLog.exercise_id || "";
    const exerciseIdentity = phase3ExerciseIdentity(setLog);
    const candidates = [
      { metric: "max_weight", value: phase3Number(setLog.actualWeight, 0), unit: "kg" },
      { metric: "max_reps", value: phase3Number(setLog.actualReps, 0), unit: "reps" }
    ];
    const reps = phase3Number(setLog.actualReps, 0);
    const weight = phase3Number(setLog.actualWeight, 0);
    if (reps > 0 && weight > 0) {
      candidates.push({
        metric: "estimated_1rm",
        value: Math.round((weight * (1 + reps / 30)) * 100) / 100,
        unit: "kg"
      });
    }
    return candidates
      .filter((candidate) => exerciseIdentity && candidate.value)
      .map((candidate) => ({
        exercise_id: phase3IsUuid(exerciseId) ? exerciseId : null,
        exercise_slug: exerciseSlug,
        exercise_identity: exerciseIdentity,
        metric: candidate.metric,
        value: candidate.value,
        unit: candidate.unit,
        source_set_log_id: setLog.id || "",
        achieved_at: setLog.completedAt || setLog.completed_at || ""
      }));
  }

  function phase3DerivedPersonalRecords() {
    const records = {};
    phase3State.history
      .flatMap((entry) => entry.sets || [])
      .forEach((setLog) => {
        const normalized = {
          id: setLog.id,
          exerciseId: setLog.exerciseId || setLog.exercise_id || "",
          exerciseSlug: setLog.exerciseSlug || setLog.exercise_slug,
          actualReps: setLog.actualReps ?? setLog.actual_reps,
          actualWeight: setLog.actualWeight ?? setLog.actual_weight,
          completedAt: setLog.completedAt || setLog.completed_at
        };
        phase3RecordCandidates(normalized).forEach((candidate) => {
          const key = `${candidate.exercise_identity}:${candidate.metric}`;
          const previous = records[key];
          if (!previous || Number(candidate.value) > Number(previous.value || 0)) records[key] = candidate;
        });
      });
    return Object.values(records);
  }

  function phase3PreviousPerformance(exercise) {
    const first = phase3PreviousPerformanceSets(exercise)[0];
    if (!first) return "";
    const reps = first.actual_reps ?? first.actualReps ?? "-";
    const weight = first.actual_weight ?? first.actualWeight ?? "-";
    return `${weight} kg x ${reps}`;
  }

  function phase3PreviousPerformanceSets(exercise) {
    const latestEntry = phase3State.history
      .slice()
      .sort((a, b) => String(b.completedAt || "").localeCompare(String(a.completedAt || "")))
      .find((entry) => (entry.sets || []).some((setLog) => phase3SameExercise(exercise, setLog)));
    return (latestEntry?.sets || [])
      .filter((setLog) => phase3SameExercise(exercise, setLog))
      .slice()
      .sort((a, b) => Number(a.set_index ?? a.setIndex ?? 0) - Number(b.set_index ?? b.setIndex ?? 0));
  }

  function phase3OverloadSignal(exercise, session) {
    const completedSets = Object.entries(session?.setLogs || {})
      .filter(([key]) => key.startsWith(`${exercise.key}__`))
      .map(([, value]) => value);
    if (!completedSets.length) return phase3Text("overloadNeutral");
    const allDone = completedSets.length >= Number(exercise.targetSets || 1);
    const hasRoom = completedSets.some((setLog) => Number(setLog.rir) >= 2 || Number(setLog.rpe) <= 8);
    if (allDone && hasRoom) return phase3Text("overloadPotential");
    return phase3Text("overloadRepeat");
  }

  function phase3CancelVibration() {
    try {
      if (typeof navigator.vibrate === "function") navigator.vibrate(0);
    } catch {
      // Vibration is optional and must never interrupt workout state.
    }
  }

  function phase3StartTimer(seconds, nextStep = null) {
    const session = phase3State.activeSession;
    if (!session) return;
    const focus = phase3EnsureSessionFocus(session);
    const durationSeconds = Math.max(0, Number(seconds || 0));
    if (!durationSeconds) {
      phase3ApplyFocusStep(session, nextStep, Boolean(nextStep?.completedExercise));
      phase3SaveLocal();
      return;
    }
    phase3TimerEndsAt = Date.now() + durationSeconds * 1000;
    phase3LastVibrationSecond = null;
    focus.rest = {
      durationSeconds,
      endsAt: phase3TimerEndsAt,
      remainingMs: durationSeconds * 1000,
      paused: false,
      nextExerciseIndex: Number(nextStep?.exerciseIndex ?? -1),
      nextSetIndex: Number(nextStep?.setIndex || 1),
      completedExercise: Boolean(nextStep?.completedExercise)
    };
    phase3SaveLocal();
    phase3EnsureTimerRunning();
    phase3UpdateTimerText();
  }

  function phase3EnsureTimerRunning() {
    if (phase3TimerId || !phase3FocusOpen || !phase3State.activeSession) return;
    phase3TimerId = window.setInterval(() => phase3UpdateTimerText(), 1000);
  }

  function phase3StopTimer(done = false) {
    if (phase3TimerId) {
      window.clearInterval(phase3TimerId);
      phase3TimerId = null;
    }
    phase3LastVibrationSecond = null;
    phase3CancelVibration();
    if (done) phase3TimerEndsAt = 0;
  }

  function phase3PauseRestTimer() {
    const rest = phase3EnsureSessionFocus(phase3State.activeSession).rest;
    if (!rest || rest.paused) return;
    rest.remainingMs = Math.max(0, Number(rest.endsAt || 0) - Date.now());
    rest.endsAt = 0;
    rest.paused = true;
    phase3TimerEndsAt = 0;
    phase3LastVibrationSecond = null;
    phase3CancelVibration();
  }

  function phase3ResumeRestTimer() {
    const rest = phase3EnsureSessionFocus(phase3State.activeSession).rest;
    if (!rest || !rest.paused) return;
    rest.endsAt = Date.now() + Math.max(0, Number(rest.remainingMs || 0));
    rest.paused = false;
    phase3TimerEndsAt = rest.endsAt;
    phase3LastVibrationSecond = null;
  }

  function phase3FinishRestTimer() {
    const session = phase3State.activeSession;
    const rest = phase3EnsureSessionFocus(session).rest;
    if (!session || !rest) return;
    phase3ApplyFocusStep(session, {
      exerciseIndex: Number(rest.nextExerciseIndex),
      setIndex: Number(rest.nextSetIndex || 1)
    }, Boolean(rest.completedExercise));
    phase3SaveLocal();
  }

  function phase3SkipRestTimer() {
    phase3FinishRestTimer();
    renderTraining();
  }

  function phase3AddRestSeconds(seconds = 15) {
    const rest = phase3EnsureSessionFocus(phase3State.activeSession).rest;
    if (!rest) return;
    if (rest.paused) rest.remainingMs = Math.max(0, Number(rest.remainingMs || 0)) + seconds * 1000;
    else rest.endsAt = Math.max(Date.now(), Number(rest.endsAt || Date.now())) + seconds * 1000;
    phase3TimerEndsAt = Number(rest.endsAt || 0);
    phase3LastVibrationSecond = null;
    phase3SaveLocal();
    phase3UpdateTimerText();
  }

  function phase3RestartRestTimer() {
    const rest = phase3EnsureSessionFocus(phase3State.activeSession).rest;
    if (!rest) return;
    rest.remainingMs = Math.max(0, Number(rest.durationSeconds || 0)) * 1000;
    rest.endsAt = rest.paused ? 0 : Date.now() + rest.remainingMs;
    phase3TimerEndsAt = Number(rest.endsAt || 0);
    phase3LastVibrationSecond = null;
    phase3SaveLocal();
    phase3UpdateTimerText();
  }

  function phase3UpdateTimerText() {
    const session = phase3State.activeSession;
    if (!session) return;
    const durationText = phase3FormatDuration(phase3WorkoutElapsedSeconds(session));
    document.querySelectorAll("[data-phase3-workout-duration]").forEach((target) => {
      target.textContent = durationText;
    });
    const rest = phase3EnsureSessionFocus(session).rest;
    if (!rest) return;
    const remainingMs = rest.paused ? Number(rest.remainingMs || 0) : Math.max(0, Number(rest.endsAt || 0) - Date.now());
    const remaining = Math.max(0, Math.ceil(remainingMs / 1000));
    const minutes = Math.floor(remaining / 60);
    const seconds = String(remaining % 60).padStart(2, "0");
    const target = document.querySelector("[data-phase3-rest-countdown]");
    if (target) target.textContent = `${String(minutes).padStart(2, "0")}:${seconds}`;
    if (!rest.paused && remaining > 0 && remaining <= 3 && phase3LastVibrationSecond !== remaining) {
      phase3LastVibrationSecond = remaining;
      if (phase3RestVibrationEnabled && phase3FocusOpen && session.status === "active" && document.visibilityState === "visible") {
        try {
          if (typeof navigator.vibrate === "function") navigator.vibrate(80);
        } catch {
          // Unsupported haptics remain a no-op.
        }
      }
    }
    if (!rest.paused && remaining <= 0) {
      phase3FinishRestTimer();
      renderTraining();
    }
  }

  function phase3ExerciseMediaLabel(exercise) {
    const status = exercise?.animationStatus || "placeholder";
    if (status === "legacy") return "Legacy";
    if (status === "youri_avatar_ready") return "Youri";
    return "Youri";
  }

  function phase3RenderExerciseMedia(exercise, mode = "thumb") {
    const meta = phase3ExerciseMeta(exercise?.slug || exercise?.canonicalSlug || phase3BuilderDraft.exerciseSlug);
    const label = meta.animationStatus === "legacy" ? phase3Text("animationPreview") : phase3Text("youriAvatarPending");
    return `
      <div class="phase3-media phase3-media-${escapeHTML(mode)}" aria-label="${escapeHTML(phase3Text("animationPreview"))}">
        <span class="phase3-media-avatar">${escapeHTML(phase3ExerciseMediaLabel(exercise))}</span>
        <span class="phase3-media-caption">${escapeHTML(label)}</span>
      </div>
    `;
  }

  function phase3SelectedExerciseMeta() {
    return phase3ExerciseMeta(phase3BuilderDraft.exerciseSlug || PHASE3_EXERCISES[0]?.slug || "");
  }

  function phase3RenderPickerChips(type, options) {
    const activeValue = phase3LibraryFilters[type] || "";
    const allLabel = type === "category" ? phase3Text("allCategories") : phase3Text("allEquipment");
    return `
      <div class="phase3-chip-row" role="list">
        <button class="phase3-chip ${!activeValue ? "active" : ""}" data-phase3-picker-filter="${type}:" type="button">${escapeHTML(allLabel)}</button>
        ${options.map((item) => `
          <button class="phase3-chip ${activeValue === item.value ? "active" : ""}" data-phase3-picker-filter="${escapeHTML(type)}:${escapeHTML(item.value)}" type="button">${escapeHTML(item.label)}</button>
        `).join("")}
      </div>
    `;
  }

  function phase3RenderPickerResults() {
    const results = phase3FilteredExercises();
    const visible = results.slice(0, phase3PickerVisibleCount);
    return `
      <div class="phase3-picker-count">${escapeHTML(phase3Format("showingResults", { shown: visible.length, total: results.length }))}</div>
      <div class="phase3-picker-results">
        ${visible.map((exercise) => {
          const meta = phase3ExerciseMeta(exercise.slug);
          return `
            <article class="phase3-picker-card">
              ${phase3RenderExerciseMedia(exercise, "thumb")}
              <div>
                <strong>${escapeHTML(meta.name)}</strong>
                <p class="muted">${escapeHTML(meta.primary)} · ${escapeHTML(meta.equipment)}</p>
                ${meta.instructions ? `<p class="muted">${escapeHTML(meta.instructions)}</p>` : ""}
              </div>
              <button class="primary-btn" data-phase3-select-exercise="${escapeHTML(exercise.slug)}" type="button">${escapeHTML(phase3Text("chooseExercise"))}</button>
            </article>
          `;
        }).join("") || `<div class="empty-mini">${escapeHTML(phase3Text("noLibraryResults"))}</div>`}
      </div>
      ${visible.length < results.length ? `<button class="secondary-btn phase3-load-more" data-phase3-load-more-exercises type="button">${escapeHTML(phase3Text("loadMoreExercises"))}</button>` : ""}
    `;
  }

  function phase3RefreshPickerResults() {
    const container = document.querySelector("[data-phase3-picker-results]");
    if (container) container.innerHTML = phase3RenderPickerResults();
  }

  function phase3PickerPortal() {
    let portal = document.getElementById(PHASE3_PICKER_PORTAL_ID);
    if (portal) return portal;
    portal = document.createElement("div");
    portal.id = PHASE3_PICKER_PORTAL_ID;
    portal.className = "phase3-picker-portal";
    portal.dataset.phase3PickerPortal = "";
    document.body.appendChild(portal);
    return portal;
  }

  function phase3RemovePickerPortal() {
    document.getElementById(PHASE3_PICKER_PORTAL_ID)?.remove();
    document.body.classList.remove("phase3-picker-open");
  }

  function phase3SyncPickerPortal(disabled = false) {
    if (!phase3PickerOpen || disabled) {
      phase3RemovePickerPortal();
      return;
    }
    const portal = phase3PickerPortal();
    portal.innerHTML = phase3RenderExercisePicker();
    document.body.classList.add("phase3-picker-open");
  }

  async function phase3RetryExerciseCatalog() {
    phase3PickerLoading = true;
    phase3PickerError = "";
    phase3SyncPickerPortal();
    const loaded = await phase3LoadCanonicalCatalog();
    phase3PickerLoading = false;
    if (!loaded || !phase3CatalogHydrated || window.FMZ_PHASE3_TRAINING_ENGINE.loadedCatalogRecords !== PHASE3_REAL_CATALOG_EXPECTED_COUNT) {
      phase3PickerError = "catalog_load_failed";
    }
    phase3SyncPickerPortal();
    return !phase3PickerError;
  }

  async function phase3OpenExercisePicker(form) {
    phase3CaptureBuilderDraft(form);
    phase3PickerOpen = true;
    phase3PickerVisibleCount = PHASE3_PICKER_PAGE_SIZE;
    await phase3RetryExerciseCatalog();
  }

  function phase3CloseExercisePicker() {
    phase3PickerOpen = false;
    phase3PickerLoading = false;
    phase3PickerError = "";
    phase3PickerVisibleCount = PHASE3_PICKER_PAGE_SIZE;
    phase3RemovePickerPortal();
  }

  function phase3FocusPortal() {
    let portal = document.getElementById(PHASE3_FOCUS_PORTAL_ID);
    if (portal) return portal;
    portal = document.createElement("div");
    portal.id = PHASE3_FOCUS_PORTAL_ID;
    portal.className = "phase3-focus-portal";
    document.body.appendChild(portal);
    return portal;
  }

  function phase3RemoveFocusPortal() {
    document.getElementById(PHASE3_FOCUS_PORTAL_ID)?.remove();
    document.body.classList.remove("phase3-focus-open");
  }

  function phase3SyncFocusPortal() {
    if (!phase3FocusOpen || !phase3State.activeSession) {
      phase3RemoveFocusPortal();
      return;
    }
    phase3FocusPortal().innerHTML = phase3RenderWorkoutFocus();
    document.body.classList.add("phase3-focus-open");
    phase3EnsureTimerRunning();
    phase3UpdateTimerText();
  }

  function phase3OpenFocus() {
    if (!phase3State.activeSession) return;
    phase3EnsureSessionFocus(phase3State.activeSession);
    phase3FocusOpen = true;
    phase3SyncFocusPortal();
  }

  function phase3CloseFocus() {
    phase3FocusOpen = false;
    phase3StopTimer();
    phase3RemoveFocusPortal();
  }

  function phase3HistoryPortal() {
    let portal = document.getElementById(PHASE3_HISTORY_PORTAL_ID);
    if (portal) return portal;
    portal = document.createElement("div");
    portal.id = PHASE3_HISTORY_PORTAL_ID;
    portal.className = "phase3-history-portal";
    document.body.appendChild(portal);
    return portal;
  }

  function phase3RemoveHistoryPortal() {
    document.getElementById(PHASE3_HISTORY_PORTAL_ID)?.remove();
    document.body.classList.remove("phase3-history-open");
  }

  function phase3SyncHistoryPortal() {
    if (!phase3HistoryDetailId || !phase3HistoryEntry(phase3HistoryDetailId)) {
      phase3RemoveHistoryPortal();
      return;
    }
    phase3HistoryPortal().innerHTML = phase3RenderHistoryDetail();
    document.body.classList.add("phase3-history-open");
  }

  function phase3OpenHistory(entryId) {
    if (!phase3HistoryEntry(entryId)) return;
    phase3HistoryDetailId = String(entryId);
    phase3SyncHistoryPortal();
  }

  function phase3CloseHistory() {
    phase3HistoryDetailId = "";
    phase3RemoveHistoryPortal();
  }

  async function phase3SelectExercise(slug) {
    const exercise = phase3Exercise(slug);
    if (!exercise) return;
    await phase3LoadExerciseDetails([exercise]);
    phase3BuilderDraft.exerciseSlug = slug;
    phase3CloseExercisePicker();
  }

  function phase3RenderExercisePicker() {
    if (!phase3PickerOpen) return "";
    const categories = phase3LibraryOptions("category");
    const equipment = phase3LibraryOptions("equipment");
    const content = phase3PickerLoading
      ? `<div class="phase3-picker-state" role="status"><strong>${escapeHTML(phase3Text("catalogLoading"))}</strong><span>${escapeHTML(phase3Format("catalogProgress", phase3CatalogLoadState))}</span></div>`
      : phase3PickerError || !phase3CatalogHydrated
        ? `<div class="phase3-picker-state phase3-picker-error" role="alert">
            <p>${escapeHTML(phase3Text("catalogLoadError"))}</p>
            <small>${escapeHTML(phase3Format("catalogProgress", phase3CatalogLoadState))}</small>
            <button class="primary-btn" data-phase3-retry-catalog type="button">${escapeHTML(phase3Text("retryCatalog"))}</button>
          </div>`
        : `
          <label class="field"><span>${escapeHTML(phase3Text("searchLibrary"))}</span><input data-phase3-picker-search value="${escapeHTML(phase3LibraryFilters.search)}" placeholder="${escapeHTML(phase3Text("searchLibrary"))}" /></label>
          <div>
            <strong>${escapeHTML(phase3Text("muscle"))}</strong>
            ${phase3RenderPickerChips("category", categories)}
          </div>
          <div>
            <strong>${escapeHTML(phase3Text("equipment"))}</strong>
            ${phase3RenderPickerChips("equipment", equipment)}
          </div>
          <div class="settings-save-row">
            <button class="secondary-btn" data-phase3-clear-picker-filters type="button">${escapeHTML(phase3Text("clearFilters"))}</button>
          </div>
          <div data-phase3-picker-results>
            ${phase3RenderPickerResults()}
          </div>
        `;
    return `
      <div class="phase3-picker-backdrop" data-phase3-picker-backdrop>
        <section class="phase3-picker-sheet" role="dialog" aria-modal="true" aria-labelledby="phase3-picker-title">
          <div class="phase3-plan-head">
            <div>
              <p class="eyebrow">${escapeHTML(phase3Text("exercisePickerTitle"))}</p>
              <h2 id="phase3-picker-title">${escapeHTML(phase3Text("chooseExercise"))}</h2>
            </div>
            <button class="secondary-btn" data-phase3-close-picker type="button">${escapeHTML(phase3Text("closePicker"))}</button>
          </div>
          ${content}
        </section>
      </div>
    `;
  }

  function phase3InstallStyles() {
    if (document.getElementById("phase3-training-engine-styles")) return;
    const style = document.createElement("style");
    style.id = "phase3-training-engine-styles";
    style.textContent = `
      .phase3-shell { display: grid; gap: 14px; }
      .phase3-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
      .phase3-status-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
      .phase3-grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(280px, .7fr); gap: 14px; align-items: start; }
      .phase3-card { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px; box-shadow: var(--shadow); }
      .phase3-accordion-list { display: grid; gap: 10px; min-width: 0; }
      .phase3-accordion { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); min-width: 0; overflow: clip; }
      .phase3-accordion-toggle { width: 100%; min-height: 62px; padding: 12px 14px; border: 0; background: transparent; color: var(--text); display: flex; align-items: center; justify-content: space-between; gap: 12px; text-align: left; }
      .phase3-accordion-toggle:hover { background: var(--surface-2); }
      .phase3-accordion-heading { display: grid; gap: 2px; min-width: 0; }
      .phase3-accordion-heading strong { font-size: 1rem; }
      .phase3-accordion-heading small { color: var(--muted); overflow-wrap: anywhere; }
      .phase3-accordion-chevron { width: 28px; height: 28px; flex: 0 0 28px; display: grid; place-items: center; font-size: 1.3rem; transform: rotate(0deg); transition: transform .18s ease; }
      .phase3-accordion-toggle[aria-expanded="true"] .phase3-accordion-chevron { transform: rotate(90deg); }
      .phase3-accordion-body { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .18s ease; }
      .phase3-accordion-body.open { grid-template-rows: 1fr; }
      .phase3-accordion-body > div { min-height: 0; overflow: hidden; }
      .phase3-accordion-content { border-top: 1px solid var(--line); padding: 14px; min-width: 0; }
      .phase3-plan-tabs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px; padding: 4px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-2); }
      .phase3-plan-tab { min-height: 44px; border: 0; border-radius: 6px; background: transparent; color: var(--text); }
      .phase3-plan-tab.active { background: var(--surface); box-shadow: var(--shadow); font-weight: 700; }
      .phase3-plan-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
      .phase3-start-action { background: #c89312; border-color: #c89312; color: #111; font-weight: 800; }
      .phase3-start-action:hover { background: #d8a72a; border-color: #d8a72a; }
      .phase3-tertiary-action { border-color: transparent; background: transparent; color: var(--muted); }
      .phase3-plan-feedback { margin: 10px 0 0; }
      .phase3-plan-feedback.error { border-color: #b64242; }
      .phase3-archive-help { margin: 10px 0 0; }
      .phase3-form-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
      .phase3-form-grid .wide { grid-column: 1 / -1; }
      .phase3-plan-list, .phase3-history-list { display: grid; gap: 10px; }
      .phase3-plan-card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; display: grid; gap: 10px; }
      .phase3-plan-head, .phase3-day-head, .phase3-set-row, .phase3-history-item { display: flex; justify-content: space-between; gap: 10px; align-items: center; flex-wrap: wrap; }
      .phase3-builder-list { display: grid; gap: 8px; }
      .phase3-builder-item { border: 1px solid var(--line); border-radius: 8px; padding: 10px; display: grid; gap: 8px; }
      .phase3-builder-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
      .phase3-exercise-list { display: grid; gap: 8px; }
      .phase3-exercise-line { border-top: 1px solid var(--line); padding-top: 8px; display: grid; gap: 8px; }
      .phase3-active-summary { display: grid; gap: 12px; border-color: rgba(200,147,18,.45); }
      .phase3-media { min-height: 86px; border: 1px dashed var(--line); border-radius: 8px; display: grid; place-items: center; align-content: center; gap: 4px; background: linear-gradient(135deg, rgba(30,90,86,.08), rgba(200,147,18,.10)); color: var(--text); text-align: center; }
      .phase3-media-large { min-height: 160px; }
      .phase3-media-avatar { font-weight: 800; letter-spacing: 0; }
      .phase3-media-caption { font-size: .78rem; color: var(--muted); }
      body.phase3-picker-open, body.phase3-focus-open, body.phase3-history-open { overflow: hidden; }
      .phase3-picker-portal { position: relative; z-index: 70; }
      .phase3-picker-backdrop { position: fixed; inset: 0; z-index: 70; background: rgba(10,18,24,.58); display: grid; place-items: center; padding: 18px; }
      .phase3-picker-sheet { position: relative; z-index: 1; width: min(880px, calc(100vw - 36px)); max-height: min(760px, calc(100dvh - 36px)); overflow-y: auto; overscroll-behavior: contain; background: var(--bg); color: var(--text); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); padding: 16px; display: grid; gap: 14px; }
      .phase3-picker-state { min-height: 180px; display: grid; place-items: center; align-content: center; gap: 12px; padding: 24px; text-align: center; }
      .phase3-picker-error { color: var(--text); }
      .phase3-chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
      .phase3-chip { border: 1px solid var(--line); background: var(--surface-2); color: var(--text); border-radius: 999px; min-height: 34px; padding: 0 12px; }
      .phase3-chip.active { border-color: var(--brand); background: rgba(30,90,86,.12); font-weight: 700; }
      .phase3-picker-count { color: var(--muted); font-size: .86rem; }
      .phase3-picker-results { display: grid; gap: 10px; }
      .phase3-picker-card { display: grid; grid-template-columns: 96px minmax(0, 1fr) auto; gap: 12px; align-items: center; border: 1px solid var(--line); border-radius: 8px; padding: 10px; }
      .phase3-load-more { justify-self: center; }
      .phase3-focus-portal { position: relative; z-index: 65; }
      .phase3-focus-backdrop { position: fixed; inset: 0; z-index: 65; background: rgba(7,11,18,.72); display: grid; place-items: center; padding: 18px; }
      .phase3-focus-sheet { width: min(960px, calc(100vw - 36px)); max-height: min(860px, calc(100dvh - 36px)); overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; background: var(--bg); color: var(--text); border: 1px solid var(--line); border-radius: 8px; box-shadow: var(--shadow); padding: 18px; display: grid; gap: 16px; }
      .phase3-focus-header, .phase3-focus-header-actions, .phase3-focus-actions { display: flex; gap: 10px; justify-content: space-between; align-items: center; flex-wrap: wrap; }
      .phase3-focus-header h2, .phase3-focus-main h3, .phase3-focus-previous h3 { margin: 0; }
      .phase3-focus-context { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
      .phase3-focus-context > div { border: 1px solid var(--line); border-radius: 8px; padding: 10px; display: grid; gap: 2px; }
      .phase3-focus-context span { color: var(--muted); font-size: .82rem; }
      .phase3-focus-context strong { font-size: 1.08rem; }
      .phase3-focus-progress { height: 6px; border-radius: 999px; overflow: hidden; background: var(--surface-2); }
      .phase3-focus-progress span { display: block; height: 100%; max-width: 100%; background: var(--brand); }
      .phase3-focus-exercise { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(240px, .55fr); gap: 14px; align-items: start; }
      .phase3-focus-main, .phase3-focus-previous { display: grid; gap: 12px; min-width: 0; }
      .phase3-focus-previous { border-left: 1px solid var(--line); padding-left: 14px; }
      .phase3-instruction { border: 1px solid var(--line); border-radius: 8px; padding: 10px; }
      .phase3-instruction summary { cursor: pointer; font-weight: 700; }
      .phase3-instruction p { line-height: 1.5; }
      .phase3-instruction small { color: var(--muted); }
      .phase3-previous-list { display: grid; gap: 6px; }
      .phase3-previous-list > div { display: flex; justify-content: space-between; gap: 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
      .phase3-focus-set { display: grid; gap: 8px; width: 100%; max-width: 680px; }
      .phase3-focus-inputs { display: grid; gap: 8px; min-width: 0; }
      .phase3-focus-numeric-grid { display: grid; grid-template-columns: minmax(88px, 1.35fr) repeat(3, minmax(58px, .75fr)); gap: 8px; min-width: 0; }
      .phase3-focus-inputs label { display: grid; gap: 4px; min-width: 0; color: var(--muted); font-size: .78rem; }
      .phase3-focus-inputs input { width: 100%; min-width: 0; min-height: 44px; padding: 8px; font-size: 1rem; }
      .phase3-focus-notes { width: 100%; }
      .phase3-gold-save { min-height: 54px; width: 100%; background: #c89312; border-color: #c89312; color: #111; font-weight: 800; }
      .phase3-gold-save:hover { background: #d8a72a; border-color: #d8a72a; }
      .phase3-rest-state, .phase3-paused-state, .phase3-complete-state { min-height: 230px; display: grid; place-items: center; align-content: center; gap: 14px; text-align: center; border: 1px solid var(--line); border-radius: 8px; padding: 20px; }
      .phase3-rest-countdown { font-size: 5.5rem; line-height: 1; font-variant-numeric: tabular-nums; }
      .phase3-focus-feedback { border-left: 3px solid #c89312; padding: 8px 10px; background: rgba(200,147,18,.10); }
      .phase3-vibration-setting { display: flex; gap: 10px; align-items: center; min-height: 44px; }
      .phase3-vibration-setting input { width: 20px; height: 20px; }
      .phase3-history-button { width: 100%; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-2); color: var(--text); padding: 12px; text-align: left; min-height: 52px; }
      .phase3-history-open { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 6px; color: var(--accent); font-weight: 700; }
      .phase3-pr-list { display: grid; gap: 8px; }
      .phase3-pr-row { display: grid; grid-template-columns: minmax(150px, 1.4fr) repeat(3, minmax(90px, 1fr)); gap: 10px; align-items: center; border: 1px solid var(--line); border-radius: 8px; padding: 10px; }
      .phase3-pr-row > div { display: grid; gap: 2px; }
      .phase3-pr-row span { color: var(--muted); font-size: .78rem; }
      .phase3-history-portal { position: relative; z-index: 68; }
      .phase3-history-backdrop { position: fixed; inset: 0; z-index: 68; background: rgba(7,11,18,.68); display: grid; place-items: center; padding: 18px; }
      .phase3-history-sheet { width: min(760px, calc(100vw - 36px)); max-height: min(800px, calc(100dvh - 36px)); overflow-x: hidden; overflow-y: auto; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; display: grid; gap: 14px; }
      .phase3-history-detail-list, .phase3-history-detail-list article { display: grid; gap: 10px; }
      .phase3-history-set { display: grid; grid-template-columns: 70px minmax(120px, 1fr) repeat(2, auto); gap: 10px; border-top: 1px solid var(--line); padding-top: 8px; }
      @media (max-width: 880px) {
        .phase3-grid, .phase3-form-grid, .phase3-focus-exercise, .phase3-pr-row { grid-template-columns: 1fr; }
        .phase3-picker-backdrop { align-items: end; padding: 0; }
        .phase3-picker-sheet { width: 100%; max-height: calc(100dvh - 12px); border-radius: 8px 8px 0 0; padding-bottom: calc(16px + env(safe-area-inset-bottom)); }
        .phase3-picker-card { grid-template-columns: 82px minmax(0, 1fr); }
        .phase3-picker-card .primary-btn { grid-column: 1 / -1; }
        .phase3-focus-backdrop, .phase3-history-backdrop { align-items: end; padding: 0; }
        .phase3-focus-sheet, .phase3-history-sheet { width: 100%; max-height: 100dvh; min-height: calc(100dvh - env(safe-area-inset-top)); border-radius: 0; padding: max(14px, env(safe-area-inset-top)) 14px calc(18px + env(safe-area-inset-bottom)); }
        .phase3-focus-sheet { gap: 12px; }
        .phase3-focus-header { align-items: flex-start; }
        .phase3-focus-header-actions { justify-content: flex-start; }
        .phase3-focus-context { grid-template-columns: 1fr 1fr; }
        .phase3-focus-previous { border-left: 0; border-top: 1px solid var(--line); padding: 12px 0 0; }
        .phase3-media-large { min-height: 190px; }
        .phase3-rest-countdown { font-size: 4rem; }
        .phase3-history-set { grid-template-columns: 55px minmax(110px, 1fr); }
        .phase3-history-set span:nth-child(n+3) { font-size: .82rem; }
        .phase3-accordion-toggle { min-height: 66px; }
        .phase3-accordion-content { padding: 12px; }
        .phase3-plan-actions { display: grid; grid-template-columns: 1fr 1fr; width: 100%; }
        .phase3-plan-actions .phase3-start-action, .phase3-plan-actions .phase3-restore-action { grid-column: 1 / -1; min-height: 48px; }
      }
      @media (max-width: 359px) {
        .phase3-focus-numeric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
    `;
    document.head.appendChild(style);
  }

  function phase3RenderStatus() {
    const limit = phase3ActiveDayLimit();
    const limitLabel = limit === Infinity
      ? phase3Text("unlimitedWorkouts")
      : phase3Format("activeWorkouts", { count: phase3ActiveWorkoutDays().length, limit });
    return `
      <div class="phase3-status-row">
        <span class="status ok">${escapeHTML(limitLabel)}</span>
        <span class="status ${phase3State.migrationReady ? "ok" : ""}">${escapeHTML(phase3State.syncMessage || phase3Text("localSafe"))}</span>
        <span class="status">${PHASE3_VERSION}</span>
      </div>
    `;
  }

  function phase3RenderBuilderExercises(disabled) {
    phase3NormalizeBuilderExercises();
    return `
      <div class="phase3-builder-list wide">
        <div class="panel-head compact-head">
          <h3>${escapeHTML(phase3Text("selectedExercises"))}</h3>
          <span class="status">${escapeHTML(phase3Format("exerciseCount", { count: phase3BuilderExercises.length }))}</span>
        </div>
        ${phase3BuilderExercises.length ? phase3BuilderExercises.map((exercise, index) => `
          <article class="phase3-builder-item">
            <div class="phase3-plan-head">
              <div>
                <strong>${escapeHTML(exercise.name)}</strong>
                <p class="muted">${escapeHTML(String(exercise.targetSets))} x ${escapeHTML(exercise.targetReps)}${exercise.targetWeight !== "" ? ` - ${escapeHTML(String(exercise.targetWeight))} kg` : ""}</p>
              </div>
              <div class="phase3-builder-actions">
                <button class="secondary-btn" data-phase3-edit-builder-exercise="${index}" type="button" ${disabled ? "disabled" : ""}>${escapeHTML(phase3Text("editExercise"))}</button>
                <button class="secondary-btn" data-phase3-move-builder-exercise="${index}:-1" type="button" ${disabled || index === 0 ? "disabled" : ""}>${escapeHTML(phase3Text("moveExerciseUp"))}</button>
                <button class="secondary-btn" data-phase3-move-builder-exercise="${index}:1" type="button" ${disabled || index === phase3BuilderExercises.length - 1 ? "disabled" : ""}>${escapeHTML(phase3Text("moveExerciseDown"))}</button>
                <button class="secondary-btn" data-phase3-remove-builder-exercise="${index}" type="button" ${disabled ? "disabled" : ""}>${escapeHTML(phase3Text("removeExercise"))}</button>
              </div>
            </div>
            ${exercise.notes ? `<p class="muted">${escapeHTML(exercise.notes)}</p>` : ""}
          </article>
        `).join("") : `<p class="empty-mini">${escapeHTML(phase3Text("noBuilderExercises"))}</p>`}
        <p class="muted">${escapeHTML(phase3Text("exerciseFreeNote"))}</p>
      </div>
    `;
  }

  function phase3RenderPendingPlanRetry() {
    const pending = phase3State.pendingPlanRetry;
    if (!pending?.plan) return "";
    return `
      <div class="empty-mini">
        ${escapeHTML(phase3Text("partialSave"))}
        <button class="secondary-btn" data-phase3-retry-plan-exercises type="button">${escapeHTML(phase3Text("retryPartialSave"))}</button>
      </div>
    `;
  }

  function phase3RenderPlanForm() {
    const editing = Boolean(phase3EditingPlanId && phase3EditingDayId);
    const disabled = !editing && !phase3CanCreateActiveWorkoutDay();
    const selectedMeta = phase3SelectedExerciseMeta();
    return `
      <div>
        <div class="panel-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase3Text(editing ? "editWorkout" : "createPlan"))}</p>
            <h2>${escapeHTML(editing ? phase3BuilderDraft.title : phase3Text("freeLimitTitle"))}</h2>
            <p class="muted">${escapeHTML(phase3Text("freeLimitText"))}</p>
          </div>
        </div>
        ${disabled ? `<p class="empty-mini">${escapeHTML(phase3Text("limitReached"))}</p>` : ""}
        ${phase3RenderPendingPlanRetry()}
        <form id="phase3PlanForm" class="phase3-form-grid">
          <label class="field"><span>${escapeHTML(phase3Text("planTitle"))}</span><input name="title" required placeholder="Full body A" value="${escapeHTML(phase3BuilderDraft.title)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("day"))}</span><select name="dayLabel" ${disabled ? "disabled" : ""}>${DAYS.map((day) => `<option value="${escapeHTML(day)}" ${phase3BuilderDraft.dayLabel === day ? "selected" : ""}>${escapeHTML(phase3Text(day))}</option>`).join("")}</select></label>
          <div class="field">
            <span>${escapeHTML(phase3Text("selectedExercise"))}</span>
            <input name="exerciseSlug" type="hidden" value="${escapeHTML(phase3BuilderDraft.exerciseSlug)}" />
            <div class="phase3-plan-card">
              <strong>${escapeHTML(selectedMeta.name)}</strong>
              <p class="muted">${escapeHTML(selectedMeta.primary)} · ${escapeHTML(selectedMeta.equipment)}</p>
              <button class="secondary-btn" data-phase3-open-picker type="button" ${disabled ? "disabled" : ""}>${escapeHTML(phase3Text("openExercisePicker"))}</button>
            </div>
          </div>
          <label class="field"><span>${escapeHTML(phase3Text("sets"))}</span><input name="sets" type="number" min="1" max="20" value="${escapeHTML(phase3BuilderDraft.sets)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("reps"))}</span><input name="reps" value="${escapeHTML(phase3BuilderDraft.reps)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("targetWeight"))}</span><input name="targetWeight" type="number" min="0" step="0.5" value="${escapeHTML(phase3BuilderDraft.targetWeight)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("rir"))}</span><input name="targetRir" type="number" min="0" max="10" value="${escapeHTML(phase3BuilderDraft.targetRir)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("rpe"))}</span><input name="targetRpe" type="number" min="1" max="10" step="0.5" value="${escapeHTML(phase3BuilderDraft.targetRpe)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("rest"))}</span><input name="restSeconds" type="number" min="0" max="3600" value="${escapeHTML(phase3BuilderDraft.restSeconds)}" ${disabled ? "disabled" : ""} /></label>
          <label class="field wide"><span>${escapeHTML(phase3Text("notes"))}</span><textarea name="notes" rows="2" ${disabled ? "disabled" : ""}>${escapeHTML(phase3BuilderDraft.notes)}</textarea></label>
          <div class="settings-save-row wide">
            <button class="secondary-btn" data-phase3-add-builder-exercise type="button" ${disabled ? "disabled" : ""}>${escapeHTML(phase3Text(phase3BuilderEditIndex !== null ? "updateExercise" : "addExercise"))}</button>
            ${phase3BuilderEditIndex !== null ? `<button class="secondary-btn" data-phase3-cancel-builder-edit type="button">${escapeHTML(phase3Text("cancelEdit"))}</button>` : ""}
          </div>
          ${phase3RenderBuilderExercises(disabled)}
          <div class="settings-save-row wide">
            <button class="primary-btn" type="submit" ${disabled ? "disabled" : ""}>${escapeHTML(phase3Text(editing ? "saveWorkoutChanges" : "addPlan"))}</button>
            ${editing ? `<button class="secondary-btn" data-phase3-cancel-plan-edit type="button">${escapeHTML(phase3Text("cancelWorkoutEdit"))}</button>` : ""}
            <span class="save-feedback" data-save-feedback="phase3-plan"></span>
          </div>
        </form>
      </div>
    `;
  }

  function phase3RenderPlans() {
    const normalizedPlans = phase3State.plans.filter((plan) => plan.source !== "legacy_bridge");
    const plans = phase3PlanView === "archived"
      ? normalizedPlans.filter((plan) => plan.status === "archived")
      : phase3PlansForDisplay().filter((plan) => plan.status === "active");
    const emptyKey = phase3PlanView === "archived" ? "noArchivedPlans" : "noActivePlans";
    const feedbackText = phase3PlanFeedbackText();
    return `
      <div>
        <div class="phase3-plan-tabs" role="tablist" aria-label="${escapeHTML(phase3Text("myWorkouts"))}">
          <button class="phase3-plan-tab ${phase3PlanView === "active" ? "active" : ""}" data-phase3-plan-view="active" type="button" role="tab" aria-selected="${phase3PlanView === "active"}">${escapeHTML(phase3Text("activePlans"))}</button>
          <button class="phase3-plan-tab ${phase3PlanView === "archived" ? "active" : ""}" data-phase3-plan-view="archived" type="button" role="tab" aria-selected="${phase3PlanView === "archived"}">${escapeHTML(phase3Text("archivedPlans"))}</button>
        </div>
        ${feedbackText ? `<p class="empty-mini phase3-plan-feedback ${phase3PlanFeedback?.error ? "error" : ""}" role="${phase3PlanFeedback?.error ? "alert" : "status"}">${escapeHTML(feedbackText)}</p>` : ""}
        <p class="muted phase3-archive-help">${escapeHTML(phase3Text("archiveHistoryHelp"))}</p>
        <div class="phase3-plan-list">
          ${plans.length ? plans.map((plan) => phase3RenderPlanCard(plan)).join("") : `<div class="empty-state">${escapeHTML(phase3Text(emptyKey))}</div>`}
        </div>
        ${phase3PlanView === "active" && phase3LegacyPlan() ? `<p class="muted">${escapeHTML(phase3Text("legacyBridge"))}</p>` : ""}
      </div>
    `;
  }

  function phase3RenderPlanCard(plan) {
    if (plan.status === "archived") {
      const activeDays = (plan.days || []).filter((day) => (day.status || "active") === "active");
      const exerciseCount = activeDays.reduce((count, day) => count + (day.exercises || []).filter((exercise) => (exercise.status || "active") === "active").length, 0);
      return `
        <article class="phase3-plan-card">
          <div class="phase3-plan-head">
            <div>
              <strong>${escapeHTML(plan.title)}</strong>
              <span class="status">${escapeHTML(phase3Text("archivedStatus"))}</span>
              <p class="muted">${escapeHTML(phase3Format("exerciseCount", { count: exerciseCount }))}</p>
            </div>
            <div class="phase3-plan-actions">
              <button class="primary-btn phase3-start-action phase3-restore-action" data-phase3-restore-plan="${escapeHTML(plan.id)}" type="button">${escapeHTML(phase3Text("restorePlan"))}</button>
            </div>
          </div>
        </article>
      `;
    }
    const activeDays = (plan.days || [])
      .filter((day) => (day.status || "active") === "active")
      .map((day) => ({
        ...day,
        exercises: (day.exercises || []).filter((exercise) => (exercise.status || "active") === "active")
      }))
      .filter((day) => day.exercises.length);
    return `
      <article class="phase3-plan-card">
        <div class="phase3-plan-head">
          <div>
            <strong>${escapeHTML(plan.title)}</strong>
            <span class="muted">${escapeHTML(plan.source === "legacy_bridge" ? phase3Text("legacyPlan") : phase3Text("synced"))}</span>
          </div>
          ${plan.source !== "legacy_bridge" ? `
            <div class="phase3-plan-actions">
              ${activeDays[0] ? `<button class="primary-btn phase3-start-action" data-phase3-start-workout="${escapeHTML(plan.id)}:${escapeHTML(activeDays[0].id)}" type="button">${escapeHTML(phase3Text("startWorkout"))}</button>` : ""}
              <button class="secondary-btn" data-phase3-edit-plan="${escapeHTML(plan.id)}" type="button">${escapeHTML(phase3Text("editPlan"))}</button>
              <button class="secondary-btn phase3-tertiary-action" data-phase3-archive-plan="${escapeHTML(plan.id)}" type="button">${escapeHTML(phase3Text("archivePlan"))}</button>
            </div>
          ` : ""}
        </div>
        ${activeDays.map((day) => `
          <div class="phase3-exercise-line">
            <div class="phase3-day-head">
              <strong>${escapeHTML(phase3Text(day.label) || day.label)}</strong>
              ${plan.source === "legacy_bridge" ? `<button class="primary-btn phase3-start-action" data-phase3-start-workout="${escapeHTML(plan.id)}:${escapeHTML(day.id)}" type="button">${escapeHTML(phase3Text("startWorkout"))}</button>` : ""}
            </div>
            <div class="phase3-exercise-list">
              ${day.exercises.map((exercise) => `
                <span>${escapeHTML(exercise.name)} - ${escapeHTML(String(exercise.targetSets))} x ${escapeHTML(exercise.targetReps)}${exercise.targetWeight !== "" ? ` - ${escapeHTML(String(exercise.targetWeight))} kg` : ""}</span>
              `).join("")}
            </div>
          </div>
        `).join("")}
      </article>
    `;
  }

  function phase3RenderActiveWorkout() {
    const session = phase3State.activeSession;
    if (!session) return "";
    const isPaused = session.status === "paused";
    return `
      <section class="phase3-card phase3-active-summary">
        <div class="phase3-plan-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase3Text("activeWorkout"))}</p>
            <h2>${escapeHTML(session.planTitle)} ${session.dayLabel ? `- ${escapeHTML(phase3Text(session.dayLabel) || session.dayLabel)}` : ""}</h2>
            <span class="status ${isPaused ? "" : "ok"}">${escapeHTML(isPaused ? phase3Text("paused") : phase3Text("active"))}</span>
          </div>
          <div class="phase3-status-row">
            <span class="status"><span>${escapeHTML(phase3Text("workoutDuration"))}</span> <strong data-phase3-workout-duration>${escapeHTML(phase3FormatDuration(phase3WorkoutElapsedSeconds(session)))}</strong></span>
            <button class="primary-btn" data-phase3-open-focus type="button">${escapeHTML(phase3Text("openFocus"))}</button>
          </div>
        </div>
      </section>
    `;
  }

  function phase3CurrentFocusExercise(session) {
    const focus = phase3EnsureSessionFocus(session);
    if (focus.allExercisesCompleted) return null;
    return session.plannedExercises[focus.currentExerciseIndex] || null;
  }

  function phase3RenderPreviousSets(exercise) {
    const sets = phase3PreviousPerformanceSets(exercise);
    if (!sets.length) return `<p class="muted">${escapeHTML(phase3Text("noPrevious"))}</p>`;
    return `
      <div class="phase3-previous-list">
        ${sets.map((setLog) => {
          const index = setLog.set_index ?? setLog.setIndex ?? "-";
          return `<div><span>Set ${escapeHTML(String(index))}</span><strong>${escapeHTML(phase3FormatSetPerformance(setLog))}</strong></div>`;
        }).join("")}
      </div>
    `;
  }

  function phase3FormatSetPerformance(setLog) {
    const weight = setLog.actual_weight ?? setLog.actualWeight ?? "";
    const reps = setLog.actual_reps ?? setLog.actualReps ?? "";
    const hasWeight = weight !== "" && weight !== null && weight !== undefined;
    const hasReps = reps !== "" && reps !== null && reps !== undefined;
    if (hasWeight && hasReps) return `${weight} kg x ${reps}`;
    if (hasWeight) return `${weight} kg`;
    if (hasReps) return `${reps} ${phase3Text("reps")}`;
    return "-";
  }

  function phase3RenderSetRow(exercise, setIndex, session, disabled = false) {
    const key = phase3SetKey(exercise, setIndex);
    const saved = session.setLogs?.[key] || {};
    return `
      <div class="phase3-focus-set" data-phase3-set-row="${escapeHTML(key)}">
        <div class="phase3-focus-inputs">
          <div class="phase3-focus-numeric-grid">
            <label>${escapeHTML(phase3Text("weight"))}<input data-phase3-set-field="weight" data-phase3-weight="${escapeHTML(key)}" type="number" min="0" step="0.5" inputmode="decimal" enterkeyhint="next" autocomplete="off" value="${escapeHTML(saved.actualWeight ?? "")}" placeholder="${escapeHTML(String(exercise.targetWeight ?? ""))}" ${disabled ? "disabled" : ""} /></label>
            <label>${escapeHTML(phase3Text("reps"))}<input data-phase3-set-field="reps" data-phase3-reps="${escapeHTML(key)}" type="number" min="1" required inputmode="numeric" enterkeyhint="next" autocomplete="off" value="${escapeHTML(saved.actualReps ?? "")}" placeholder="${escapeHTML(exercise.targetReps || "")}" ${disabled ? "disabled" : ""} /></label>
            <label>${escapeHTML(phase3Text("rir"))}<input data-phase3-set-field="rir" data-phase3-rir="${escapeHTML(key)}" type="number" min="0" max="10" inputmode="numeric" enterkeyhint="next" autocomplete="off" value="${escapeHTML(saved.rir ?? "")}" ${disabled ? "disabled" : ""} /></label>
            <label>${escapeHTML(phase3Text("rpe"))}<input data-phase3-set-field="rpe" data-phase3-rpe="${escapeHTML(key)}" type="number" min="1" max="10" step="0.5" inputmode="decimal" enterkeyhint="done" autocomplete="off" value="${escapeHTML(saved.rpe ?? "")}" ${disabled ? "disabled" : ""} /></label>
          </div>
          <label class="phase3-focus-notes">${escapeHTML(phase3Text("notes"))}<input data-phase3-notes="${escapeHTML(key)}" autocomplete="off" value="${escapeHTML(saved.notes ?? "")}" ${disabled ? "disabled" : ""} /></label>
        </div>
        <button class="primary-btn phase3-gold-save" data-phase3-complete-set="${escapeHTML(key)}" type="button" ${disabled ? "disabled" : ""}>${escapeHTML(saved.completedAt ? phase3Text("setDone") : phase3Text("completeSet"))}</button>
      </div>
    `;
  }

  const PHASE3_SET_INPUT_SEQUENCE = ["weight", "reps", "rir", "rpe"];

  function phase3HandleSetInputKeydown(event) {
    if (event.key !== "Enter" || !event.target?.matches?.("[data-phase3-set-field]")) return false;
    const row = event.target.closest("[data-phase3-set-row]");
    const currentIndex = PHASE3_SET_INPUT_SEQUENCE.indexOf(event.target.dataset.phase3SetField || "");
    if (!row || currentIndex < 0) return false;
    event.preventDefault();
    const nextField = PHASE3_SET_INPUT_SEQUENCE[currentIndex + 1];
    if (nextField) row.querySelector(`[data-phase3-set-field="${nextField}"]`)?.focus();
    else event.target.blur();
    return true;
  }

  function phase3RenderRestState(session) {
    const focus = phase3EnsureSessionFocus(session);
    const rest = focus.rest;
    if (!rest) return "";
    const nextExercise = Number(rest.nextExerciseIndex) >= 0 ? session.plannedExercises[Number(rest.nextExerciseIndex)] : null;
    const remainingMs = rest.paused ? Number(rest.remainingMs || 0) : Math.max(0, Number(rest.endsAt || 0) - Date.now());
    const remaining = Math.ceil(remainingMs / 1000);
    return `
      <section class="phase3-rest-state" aria-live="polite">
        <span class="eyebrow">${escapeHTML(phase3Text("restTitle"))}</span>
        <strong class="phase3-rest-countdown" data-phase3-rest-countdown>${escapeHTML(phase3FormatDuration(remaining).slice(3))}</strong>
        <p>${escapeHTML(phase3Text("next"))}: ${escapeHTML(nextExercise ? `Set ${rest.nextSetIndex} · ${nextExercise.name}` : phase3Text("completeWorkout"))}</p>
        <div class="phase3-focus-actions">
          <button class="secondary-btn" data-phase3-skip-rest type="button">${escapeHTML(phase3Text("skipRest"))}</button>
          <button class="secondary-btn" data-phase3-add-rest type="button">${escapeHTML(phase3Text("addFifteen"))}</button>
          <button class="secondary-btn" data-phase3-restart-rest type="button">${escapeHTML(phase3Text("restartRest"))}</button>
        </div>
      </section>
    `;
  }

  function phase3RenderWorkoutFocus() {
    const session = phase3State.activeSession;
    if (!session || !phase3FocusOpen) return "";
    const focus = phase3EnsureSessionFocus(session);
    const exercise = phase3CurrentFocusExercise(session);
    const isPaused = session.status === "paused";
    const totalExercises = session.plannedExercises.length;
    const meta = exercise ? phase3ExerciseMeta(exercise.slug) : null;
    const instructions = meta?.instructions || exercise?.instructions || "";
    const instructionLocale = meta?.instructionLocale || phase3Exercise(exercise?.slug)?.instructionLocales?.[phase3Language()] || "";
    const totalSets = Math.max(1, Number(exercise?.targetSets || 1));
    return `
      <div class="phase3-focus-backdrop">
        <section class="phase3-focus-sheet" role="dialog" aria-modal="true" aria-labelledby="phase3-focus-title">
          <header class="phase3-focus-header">
            <div>
              <p class="eyebrow">${escapeHTML(phase3Text("activeWorkout"))}</p>
              <h2 id="phase3-focus-title">${escapeHTML(session.planTitle)}</h2>
            </div>
            <div class="phase3-focus-header-actions">
              <button class="secondary-btn" data-phase3-session-status="${isPaused ? "active" : "paused"}" type="button">${escapeHTML(isPaused ? phase3Text("resume") : phase3Text("pause"))}</button>
              <button class="secondary-btn" data-phase3-close-focus type="button">${escapeHTML(phase3Text("closeFocus"))}</button>
            </div>
          </header>
          <div class="phase3-focus-context">
            <div><span>${escapeHTML(phase3Text("workoutDuration"))}</span><strong data-phase3-workout-duration>${escapeHTML(phase3FormatDuration(phase3WorkoutElapsedSeconds(session)))}</strong></div>
            <div><span>${escapeHTML(exercise ? phase3Format("exerciseProgress", { current: focus.currentExerciseIndex + 1, total: totalExercises }) : phase3Text("completed"))}</span><strong>${escapeHTML(exercise ? phase3Format("setProgress", { current: focus.currentSetIndex, total: totalSets }) : `${totalExercises}/${totalExercises}`)}</strong></div>
          </div>
          <div class="phase3-focus-progress"><span style="width:${escapeHTML(String(exercise ? ((focus.currentExerciseIndex + (focus.currentSetIndex / totalSets)) / Math.max(1, totalExercises)) * 100 : 100))}%"></span></div>
          ${isPaused ? `
            <section class="phase3-paused-state">
              <span class="eyebrow">${escapeHTML(phase3Text("trainingPaused"))}</span>
              <button class="primary-btn" data-phase3-session-status="active" type="button">${escapeHTML(phase3Text("resume"))}</button>
            </section>
          ` : focus.allExercisesCompleted || !exercise ? `
            <section class="phase3-complete-state">
              <h3>${escapeHTML(phase3Text("exerciseCompleted"))}</h3>
              <p>${escapeHTML(phase3Text("allExercisesCompleted"))}</p>
              <button class="primary-btn" data-phase3-complete-workout type="button">${escapeHTML(phase3Text("completeWorkout"))}</button>
            </section>
          ` : `
            <div class="phase3-focus-exercise">
              <div class="phase3-focus-main">
                <div>
                  <h3>${escapeHTML(exercise.name)}</h3>
                  <p class="muted">${escapeHTML(exercise.primaryMuscle || meta.primary)} · ${escapeHTML(exercise.equipment || meta.equipment)}</p>
                </div>
                ${phase3RenderExerciseMedia(exercise, "large")}
                ${instructions ? `<details class="phase3-instruction" open><summary>${escapeHTML(phase3Text("instructions"))}</summary><p>${escapeHTML(instructions)}</p>${phase3Language() === "nl" && instructionLocale === "en" ? `<small>${escapeHTML(phase3Text("englishInstructionFallback"))}</small>` : ""}</details>` : ""}
              </div>
              <aside class="phase3-focus-previous">
                <h3>${escapeHTML(phase3Text("previousTime"))}</h3>
                ${phase3RenderPreviousSets(exercise)}
                <p class="muted">${escapeHTML(phase3OverloadSignal(exercise, session))}</p>
              </aside>
            </div>
            <p class="phase3-focus-feedback" data-phase3-focus-feedback role="status" ${focus.feedback ? "" : "hidden"}>${escapeHTML(focus.feedback || "")}</p>
            ${focus.rest ? phase3RenderRestState(session) : `
              <section>
                <p class="eyebrow">${escapeHTML(phase3Text("currentSet"))}</p>
                ${phase3RenderSetRow(exercise, focus.currentSetIndex, session)}
                <div class="phase3-focus-actions">
                  <button class="secondary-btn" data-phase3-skip-exercise type="button">${escapeHTML(phase3Text("skipExercise"))}</button>
                  <button class="secondary-btn" data-phase3-complete-workout type="button">${escapeHTML(phase3Text("completeWorkout"))}</button>
                </div>
              </section>
            `}
          `}
          <label class="phase3-vibration-setting">
            <input data-phase3-vibration-setting type="checkbox" ${phase3RestVibrationEnabled ? "checked" : ""} />
            <span>${escapeHTML(phase3Text("vibrationSetting"))}</span>
          </label>
        </section>
      </div>
    `;
  }

  function phase3GroupedPersonalRecords() {
    const groups = new Map();
    phase3DerivedPersonalRecords().forEach((record) => {
      const key = record.exercise_identity;
      if (!groups.has(key)) groups.set(key, { name: phase3ExerciseRecordName(record), records: {} });
      groups.get(key).records[record.metric] = record;
    });
    return Array.from(groups.values()).sort((a, b) => a.name.localeCompare(b.name));
  }

  function phase3HistoryEntry(entryId) {
    return phase3State.history.find((entry) => String(entry.id) === String(entryId)) || null;
  }

  function phase3HistoryGroups(entry) {
    const groups = new Map();
    (entry?.sets || []).forEach((setLog) => {
      const key = phase3ExerciseIdentity(setLog) || `snapshot:${setLog.exercise_name_snapshot || setLog.exerciseName || "exercise"}`;
      if (!groups.has(key)) groups.set(key, { name: phase3ExerciseRecordName(setLog), sets: [] });
      groups.get(key).sets.push(setLog);
    });
    return Array.from(groups.values()).map((group) => ({
      ...group,
      sets: group.sets.sort((a, b) => Number(a.set_index ?? a.setIndex ?? 0) - Number(b.set_index ?? b.setIndex ?? 0))
    }));
  }

  function phase3RenderHistoryDetail() {
    const entry = phase3HistoryEntry(phase3HistoryDetailId);
    if (!entry) return "";
    const duration = Number.isFinite(Number(entry.durationSeconds))
      ? phase3FormatDuration(entry.durationSeconds)
      : phase3FormatDuration(phase3CompletedDurationSeconds(entry.startedAt, entry.completedAt, entry.metadata?.focus));
    return `
      <div class="phase3-history-backdrop">
        <section class="phase3-history-sheet" role="dialog" aria-modal="true" aria-labelledby="phase3-history-title">
          <div class="phase3-plan-head">
            <div><p class="eyebrow">${escapeHTML(phase3Text("historyDetail"))}</p><h2 id="phase3-history-title">${escapeHTML(entry.title)}</h2></div>
            <button class="secondary-btn" data-phase3-close-history type="button">${escapeHTML(phase3Text("closePicker"))}</button>
          </div>
          <p class="muted">${escapeHTML(String(entry.completedAt || "").slice(0, 10))} · ${escapeHTML(duration)}</p>
          <div class="phase3-history-detail-list">
            ${phase3HistoryGroups(entry).map((group) => `
              <article>
                <h3>${escapeHTML(group.name)}</h3>
                ${group.sets.map((setLog) => `
                  <div class="phase3-history-set">
                    <span>Set ${escapeHTML(String(setLog.set_index ?? setLog.setIndex ?? "-"))}</span>
                    <strong>${escapeHTML(phase3FormatSetPerformance(setLog))}</strong>
                    ${(setLog.rir ?? "") !== "" ? `<span>RIR ${escapeHTML(String(setLog.rir))}</span>` : ""}
                    ${(setLog.rpe ?? "") !== "" ? `<span>RPE ${escapeHTML(String(setLog.rpe))}</span>` : ""}
                    ${setLog.notes ? `<span>${escapeHTML(setLog.notes)}</span>` : ""}
                  </div>
                `).join("")}
              </article>
            `).join("") || `<p>${escapeHTML(phase3Text("noPerformedSets"))}</p>`}
          </div>
        </section>
      </div>
    `;
  }

  function phase3RenderHistory() {
    const history = phase3State.history.slice(0, 5);
    return `
      <div class="phase3-history-list">
        ${history.length ? history.map((entry) => `
          <button class="phase3-history-item phase3-history-button" data-phase3-open-history="${escapeHTML(entry.id)}" type="button">
            <span><strong>${escapeHTML(entry.title)}</strong>${entry.dayLabel ? ` <small>${escapeHTML(phase3Text(entry.dayLabel) || entry.dayLabel)}</small>` : ""}</span>
            <span>${escapeHTML(String(entry.completedAt || "").slice(0, 10))}</span>
            <span class="phase3-history-open">${escapeHTML(phase3Text("openHistory"))}<span aria-hidden="true">&rsaquo;</span></span>
          </button>
        `).join("") : `<div class="empty-mini">${escapeHTML(phase3Text("noHistory"))}</div>`}
      </div>
    `;
  }

  function phase3RenderPersonalRecords() {
    const records = phase3GroupedPersonalRecords().slice(0, 6);
    return `
      <div class="phase3-pr-list">
        ${records.length ? records.map((group) => `
          <article class="phase3-pr-row">
            <strong>${escapeHTML(group.name)}</strong>
            <div><span>${escapeHTML(phase3Text("maxWeight"))}</span><strong>${escapeHTML(String(group.records.max_weight?.value ?? "-"))}${group.records.max_weight ? " kg" : ""}</strong></div>
            <div><span>${escapeHTML(phase3Text("maxReps"))}</span><strong>${escapeHTML(String(group.records.max_reps?.value ?? "-"))}</strong></div>
            <div><span>${escapeHTML(phase3Text("estimatedOneRm"))}</span><strong>${escapeHTML(String(group.records.estimated_1rm?.value ?? "-"))}${group.records.estimated_1rm ? " kg" : ""}</strong></div>
          </article>
        `).join("") : `<div class="empty-mini">${escapeHTML(phase3Text("overloadNeutral"))}</div>`}
      </div>
    `;
  }

  function phase3RenderAccordionSection(key, title, summary, content) {
    const expanded = phase3OpenTrainingSection === key;
    const panelId = `phase3-section-${key}`;
    return `
      <section class="phase3-accordion" data-phase3-section="${escapeHTML(key)}">
        <button class="phase3-accordion-toggle" data-phase3-toggle-section="${escapeHTML(key)}" type="button" aria-expanded="${expanded}" aria-controls="${escapeHTML(panelId)}">
          <span class="phase3-accordion-heading"><strong>${escapeHTML(title)}</strong><small>${escapeHTML(summary)}</small></span>
          <span class="phase3-accordion-chevron" aria-hidden="true">&rsaquo;</span>
        </button>
        <div id="${escapeHTML(panelId)}" class="phase3-accordion-body ${expanded ? "open" : ""}" aria-hidden="${!expanded}" ${expanded ? "" : "inert"}>
          <div><div class="phase3-accordion-content">${content}</div></div>
        </div>
      </section>
    `;
  }

  function phase3ApplyAccordionState() {
    document.querySelectorAll(".phase3-accordion").forEach((section) => {
      const key = section.dataset.phase3Section || "";
      const expanded = key === phase3OpenTrainingSection;
      const toggle = section.querySelector(".phase3-accordion-toggle");
      const body = section.querySelector(".phase3-accordion-body");
      toggle?.setAttribute("aria-expanded", String(expanded));
      body?.setAttribute("aria-hidden", String(!expanded));
      body?.classList.toggle("open", expanded);
      if (expanded) body?.removeAttribute("inert");
      else body?.setAttribute("inert", "");
    });
  }

  function phase3RenderClientTraining() {
    const selected = client();
    if (!hasSelectedClient(selected)) {
      return `<div class="empty-state">${escapeHTML(phase3Text("noPlans"))}</div>`;
    }
    const activePlanCount = phase3State.plans.filter((plan) => plan.status === "active").length;
    const archivedPlanCount = phase3State.plans.filter((plan) => plan.status === "archived").length;
    const historyCount = phase3State.history.length;
    const recordCount = phase3GroupedPersonalRecords().length;
    return `
      <div class="phase3-shell">
        <div class="view-head phase3-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase3Text("eyebrow"))}</p>
            <h1>${escapeHTML(phase3Text("title"))}</h1>
            <p class="muted">${escapeHTML(phase3Text("intro"))}</p>
          </div>
          ${phase3RenderStatus()}
        </div>
        ${!phase3State.migrationReady ? `<div class="phase3-card"><p class="muted">${escapeHTML(phase3Text("dbPending"))}</p></div>` : ""}
        ${phase3RenderActiveWorkout()}
        <div class="phase3-accordion-list">
          ${phase3RenderAccordionSection("builder", phase3Text(phase3EditingPlanId ? "editWorkout" : "createPlan"), phase3Text("builderSummary"), phase3RenderPlanForm())}
          ${phase3RenderAccordionSection("plans", phase3Text("myWorkouts"), phase3Format("workoutCounts", { active: activePlanCount, archived: archivedPlanCount }), phase3RenderPlans())}
          ${phase3RenderAccordionSection("history", phase3Text("workoutHistory"), phase3Format("historyCount", { count: historyCount }), phase3RenderHistory())}
          ${phase3RenderAccordionSection("records", phase3Text("personalRecords"), phase3Format("recordCount", { count: recordCount }), phase3RenderPersonalRecords())}
        </div>
      </div>
    `;
  }

  const phase3OriginalRenderTraining = renderTraining;
  phase3TrainingInitialHtml = document.getElementById("training")?.innerHTML || "";
  renderTraining = function renderTrainingPhase3() {
    phase3EnsureUserContext();
    if (isLoggedIn() && state.ui.role === "client") {
      phase3InstallStyles();
      const section = document.getElementById("training");
      if (!section) return;
      section.dataset.phase3Mode = "client";
      section.innerHTML = phase3RenderClientTraining();
      phase3SyncPickerPortal(!phase3EditingPlanId && !phase3CanCreateActiveWorkoutDay());
      phase3SyncFocusPortal();
      phase3SyncHistoryPortal();
      phase3UpdateTimerText();
      return;
    }
    const section = document.getElementById("training");
    if (section?.dataset.phase3Mode === "client") {
      phase3CloseExercisePicker();
      section.innerHTML = phase3TrainingInitialHtml;
      delete section.dataset.phase3Mode;
    }
    return phase3OriginalRenderTraining();
  };

  const phase3OriginalLoadOnlineWorkspace = loadOnlineWorkspace;
  loadOnlineWorkspace = async function loadOnlineWorkspacePhase3(profile) {
    await phase3OriginalLoadOnlineWorkspace(profile);
    if (profile?.role === "client") {
      phase3EnsureUserContext();
      const [hydrated] = await Promise.all([
        phase3HydrateTraining(profile),
        phase3LoadCanonicalCatalog()
      ]);
      if (hydrated && isLoggedIn() && state.ui.role === "client") renderTraining();
    }
  };

  const phase3OriginalShowView = showView;
  showView = function showViewPhase3(view) {
    if (view !== "training") {
      phase3FocusOpen = false;
      phase3HistoryDetailId = "";
      phase3StopTimer();
      phase3CloseExercisePicker();
      phase3RemoveFocusPortal();
      phase3RemoveHistoryPortal();
    }
    const result = phase3OriginalShowView(view);
    if (view === "training" && isLoggedIn() && state.ui.role === "client") {
      phase3LoadCanonicalCatalog().then((loaded) => {
        if (loaded && currentView === "training") renderTraining();
      });
    }
    return result;
  };

  const phase3OriginalRenderAll = renderAll;
  renderAll = function renderAllPhase3() {
    if (!isLoggedIn()) {
      phase3StopTimer();
      phase3CloseExercisePicker();
      phase3FocusOpen = false;
      phase3HistoryDetailId = "";
      phase3RemoveFocusPortal();
      phase3RemoveHistoryPortal();
      phase3State = phase3EmptyState();
      phase3UserKey = "";
      phase3ResetPlanEditor();
      phase3OpenTrainingSection = "plans";
      phase3PlanView = "active";
      phase3PlanFeedback = null;
    }
    return phase3OriginalRenderAll();
  };

  document.addEventListener("submit", async (event) => {
    if (event.target?.id !== "phase3PlanForm") return;
    event.preventDefault();
    const editing = Boolean(phase3EditingPlanId && phase3EditingDayId);
    if (!editing && !phase3CanCreateActiveWorkoutDay()) {
      setSaveFeedback("phase3-plan", phase3Text("limitReached"), true);
      return;
    }
    const plan = editing ? phase3BuildEditedPlanFromForm(event.target) : phase3BuildPlanFromForm(event.target);
    if (!plan) {
      setSaveFeedback("phase3-plan", phase3Format("saveFailed", { message: "Workout not found" }), true);
      return;
    }
    const result = editing ? await phase3PersistEditedPlan(plan) : await phase3PersistPlan(plan);
    if (!result.ok) {
      if (result.partial) {
        phase3OpenTrainingSection = "builder";
        renderTraining();
      }
      setSaveFeedback("phase3-plan", result.partial ? phase3Text("partialSave") : phase3Format("saveFailed", { message: result.error.message }), true);
      return;
    }
    phase3ResetPlanEditor();
    phase3PlanView = "active";
    phase3OpenTrainingSection = "plans";
    phase3SetPlanFeedback(editing ? "planUpdated" : "saved");
    renderTraining();
  });

  document.addEventListener("input", (event) => {
    if (event.target?.dataset.phase3PickerSearch === undefined) return;
    phase3LibraryFilters.search = String(event.target.value || "");
    phase3PickerVisibleCount = PHASE3_PICKER_PAGE_SIZE;
    phase3RefreshPickerResults();
  });

  document.addEventListener("change", (event) => {
    if (event.target?.dataset.phase3VibrationSetting !== undefined) {
      phase3RestVibrationEnabled = Boolean(event.target.checked);
      phase3SaveRestVibrationPreference();
      if (!phase3RestVibrationEnabled) phase3CancelVibration();
    }
  });

  document.addEventListener("click", async (event) => {
    if (event.target?.dataset?.phase3PickerBackdrop !== undefined) {
      phase3CloseExercisePicker();
      renderTraining();
      return;
    }
    const button = event.target.closest("button");
    if (!button) return;

    if (button.dataset.phase3ToggleSection) {
      phase3CaptureBuilderDraft(document.getElementById("phase3PlanForm"));
      const section = button.dataset.phase3ToggleSection;
      phase3OpenTrainingSection = phase3OpenTrainingSection === section ? "" : section;
      phase3ApplyAccordionState();
      return;
    }

    if (button.dataset.phase3PlanView) {
      phase3PlanView = button.dataset.phase3PlanView === "archived" ? "archived" : "active";
      phase3PlanFeedback = null;
      renderTraining();
      return;
    }

    if (button.dataset.phase3EditPlan) {
      if (phase3BeginPlanEdit(button.dataset.phase3EditPlan)) renderTraining();
      return;
    }

    if (button.dataset.phase3CancelPlanEdit !== undefined) {
      phase3ResetPlanEditor();
      phase3OpenTrainingSection = "plans";
      renderTraining();
      return;
    }

    if (button.dataset.phase3AddBuilderExercise !== undefined) {
      const form = button.closest("form");
      if (form) {
        phase3AddBuilderExercise(form);
        renderTraining();
      }
      return;
    }

    if (button.dataset.phase3OpenPicker !== undefined) {
      await phase3OpenExercisePicker(button.closest("form"));
      renderTraining();
      return;
    }

    if (button.dataset.phase3ClosePicker !== undefined) {
      phase3CloseExercisePicker();
      renderTraining();
      return;
    }

    if (button.dataset.phase3RetryCatalog !== undefined) {
      await phase3RetryExerciseCatalog();
      renderTraining();
      return;
    }

    if (button.dataset.phase3ClearPickerFilters !== undefined) {
      phase3LibraryFilters = { search: "", category: "", equipment: "" };
      phase3PickerVisibleCount = PHASE3_PICKER_PAGE_SIZE;
      renderTraining();
      return;
    }

    if (button.dataset.phase3PickerFilter) {
      const [type, value = ""] = button.dataset.phase3PickerFilter.split(":");
      if (type === "category" || type === "equipment") {
        phase3LibraryFilters[type] = value;
        phase3PickerVisibleCount = PHASE3_PICKER_PAGE_SIZE;
        renderTraining();
      }
      return;
    }

    if (button.dataset.phase3LoadMoreExercises !== undefined) {
      phase3PickerVisibleCount += PHASE3_PICKER_PAGE_SIZE;
      phase3RefreshPickerResults();
      return;
    }

    if (button.dataset.phase3SelectExercise) {
      await phase3SelectExercise(button.dataset.phase3SelectExercise);
      renderTraining();
      return;
    }

    if (button.dataset.phase3EditBuilderExercise) {
      phase3CaptureBuilderDraft(button.closest("form"));
      phase3EditBuilderExercise(Number(button.dataset.phase3EditBuilderExercise));
      renderTraining();
      return;
    }

    if (button.dataset.phase3CancelBuilderEdit !== undefined) {
      phase3CancelBuilderEdit(button.closest("form"));
      renderTraining();
      return;
    }

    if (button.dataset.phase3RemoveBuilderExercise) {
      phase3CaptureBuilderDraft(button.closest("form"));
      phase3RemoveBuilderExercise(Number(button.dataset.phase3RemoveBuilderExercise));
      renderTraining();
      return;
    }

    if (button.dataset.phase3MoveBuilderExercise) {
      phase3CaptureBuilderDraft(button.closest("form"));
      const [rawIndex, rawDirection] = button.dataset.phase3MoveBuilderExercise.split(":");
      phase3MoveBuilderExercise(Number(rawIndex), Number(rawDirection));
      renderTraining();
      return;
    }

    if (button.dataset.phase3RetryPlanExercises !== undefined) {
      const retryMode = phase3State.pendingPlanRetry?.mode || "create";
      setSaveFeedback("phase3-plan", phase3Text("partialRetrying"));
      const result = await phase3RetryPendingPlanSave();
      if (result.ok) {
        phase3ResetPlanEditor();
        phase3PlanView = "active";
        phase3OpenTrainingSection = "plans";
        phase3SetPlanFeedback(retryMode === "edit" ? "planUpdated" : "saved");
      } else {
        phase3OpenTrainingSection = "builder";
      }
      renderTraining();
      if (!result.ok) setSaveFeedback("phase3-plan", phase3Format("saveFailed", { message: result.error.message }), true);
      return;
    }

    if (button.dataset.phase3StartWorkout) {
      const [planId, dayId] = button.dataset.phase3StartWorkout.split(":");
      await phase3StartWorkout(planId, dayId);
      return;
    }

    if (button.dataset.phase3OpenFocus !== undefined) {
      phase3OpenFocus();
      return;
    }

    if (button.dataset.phase3CloseFocus !== undefined) {
      phase3CloseFocus();
      renderTraining();
      return;
    }

    if (button.dataset.phase3SkipExercise !== undefined) {
      phase3SkipCurrentExercise();
      return;
    }

    if (button.dataset.phase3SkipRest !== undefined) {
      phase3SkipRestTimer();
      return;
    }

    if (button.dataset.phase3AddRest !== undefined) {
      phase3AddRestSeconds(15);
      return;
    }

    if (button.dataset.phase3RestartRest !== undefined) {
      phase3RestartRestTimer();
      return;
    }

    if (button.dataset.phase3OpenHistory) {
      phase3OpenHistory(button.dataset.phase3OpenHistory);
      return;
    }

    if (button.dataset.phase3CloseHistory !== undefined) {
      phase3CloseHistory();
      return;
    }

    if (button.dataset.phase3CompleteSet) {
      await phase3CompleteSet(button.dataset.phase3CompleteSet);
      return;
    }

    if (button.dataset.phase3SessionStatus) {
      await phase3SetSessionStatus(button.dataset.phase3SessionStatus);
      return;
    }

    if (button.dataset.phase3CompleteWorkout !== undefined) {
      await phase3CompleteWorkout();
      return;
    }

    if (button.dataset.phase3ArchivePlan) {
      const result = await phase3ArchivePlan(button.dataset.phase3ArchivePlan);
      if (result.ok) {
        if (phase3EditingPlanId === button.dataset.phase3ArchivePlan) phase3ResetPlanEditor();
        phase3PlanView = "archived";
        phase3OpenTrainingSection = "plans";
        phase3SetPlanFeedback("planArchived");
      } else {
        phase3SetPlanFeedback("", true, phase3Format("saveFailed", { message: result.error.message }));
      }
      renderTraining();
      return;
    }

    if (button.dataset.phase3RestorePlan) {
      const result = await phase3RestorePlan(button.dataset.phase3RestorePlan);
      if (result.ok) {
        phase3PlanView = "active";
        phase3SetPlanFeedback("planRestored");
      } else if (result.limit) {
        phase3SetPlanFeedback("restoreLimitReached", true);
      } else {
        phase3SetPlanFeedback("", true, phase3Format("saveFailed", { message: result.error.message }));
      }
      phase3OpenTrainingSection = "plans";
      renderTraining();
      return;
    }

    if (button.dataset.phase3ArchiveExercise) {
      const [planId, dayId, exerciseId] = button.dataset.phase3ArchiveExercise.split(":");
      const result = await phase3ArchivePlanExercise(planId, dayId, exerciseId);
      if (!result.ok) setSaveFeedback("phase3-plan", phase3Format("saveFailed", { message: result.error.message }), true);
      renderTraining();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (phase3HandleSetInputKeydown(event)) return;
    if (event.key !== "Escape") return;
    if (phase3PickerOpen) {
      event.preventDefault();
      phase3CloseExercisePicker();
      renderTraining();
      return;
    }
    if (phase3HistoryDetailId) {
      event.preventDefault();
      phase3CloseHistory();
      return;
    }
    if (phase3FocusOpen) {
      event.preventDefault();
      phase3CloseFocus();
      renderTraining();
    }
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") phase3CancelVibration();
  });

  window.addEventListener("online", () => {
    if (!phase3State.activeSession) return;
    phase3SyncActiveSession().then(() => {
      if (currentView === "training") renderTraining();
    });
  });
})();
