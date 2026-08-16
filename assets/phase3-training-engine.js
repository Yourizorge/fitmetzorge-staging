(function phase3TrainingEngine() {
  if (window.FMZ_PHASE3_TRAINING_ENGINE_LOADED) return;
  window.FMZ_PHASE3_TRAINING_ENGINE_LOADED = true;

  const PHASE3_VERSION = "20260816-phase3-step1";
  const PHASE3_LANGUAGES = ["nl", "en", "de"];
  const PHASE3_FREE_ACTIVE_PLAN_LIMIT = 4;
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
      freeLimitText: "Free kan maximaal 4 actieve trainingsschema's gebruiken.",
      activePlans: "{count}/{limit} actieve schema's",
      unlimitedPlans: "Onbeperkt via Pro/PT",
      createPlan: "Schema maken",
      planTitle: "Naam schema",
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
      addPlan: "Actief schema opslaan",
      limitReached: "Free limiet bereikt. Archiveer eerst een schema of upgrade later naar Pro/PT.",
      plans: "Schema's",
      noPlans: "Nog geen normalized schema's. Legacy schema's blijven hieronder beschikbaar als bridge.",
      legacyPlan: "Legacy schema",
      legacyBridge: "Legacy training blijft zichtbaar en wordt niet aangepast door Phase 3.",
      startWorkout: "Workout starten",
      continueWorkout: "Workout hervatten",
      pause: "Pauzeren",
      resume: "Hervatten",
      completeWorkout: "Workout afronden",
      activeWorkout: "Actieve workout",
      paused: "Gepauzeerd",
      active: "Actief",
      completed: "Voltooid",
      completeSet: "Set opslaan",
      setDone: "Set opgeslagen",
      timer: "Rusttimer",
      timerDone: "Rust voorbij",
      previousPerformance: "Vorige prestatie",
      noPrevious: "Nog geen vorige prestatie",
      prTitle: "PR foundation",
      historyTitle: "Workout history",
      noHistory: "Nog geen afgeronde workouts.",
      overloadTitle: "Progressive overload",
      overloadNeutral: "Log eerst prestaties; daarna verschijnt een veilige trendstatus.",
      overloadRepeat: "Vorige prestatie beschikbaar. Herhaal eerst stabiel voordat je verhoogt.",
      overloadPotential: "Alle sets gehaald met ruimte over. Kleine verhoging kan later overwogen worden.",
      exerciseLibrary: "Oefenbibliotheek",
      archivePlan: "Archiveren",
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
      freeLimitText: "Free can use up to 4 active training plans.",
      activePlans: "{count}/{limit} active plans",
      unlimitedPlans: "Unlimited through Pro/PT",
      createPlan: "Create plan",
      planTitle: "Plan name",
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
      addPlan: "Save active plan",
      limitReached: "Free limit reached. Archive a plan first or upgrade later to Pro/PT.",
      plans: "Plans",
      noPlans: "No normalized plans yet. Legacy plans remain available below as a bridge.",
      legacyPlan: "Legacy plan",
      legacyBridge: "Legacy training stays visible and is not modified by Phase 3.",
      startWorkout: "Start workout",
      continueWorkout: "Continue workout",
      pause: "Pause",
      resume: "Resume",
      completeWorkout: "Complete workout",
      activeWorkout: "Active workout",
      paused: "Paused",
      active: "Active",
      completed: "Completed",
      completeSet: "Save set",
      setDone: "Set saved",
      timer: "Rest timer",
      timerDone: "Rest done",
      previousPerformance: "Previous performance",
      noPrevious: "No previous performance yet",
      prTitle: "PR foundation",
      historyTitle: "Workout history",
      noHistory: "No completed workouts yet.",
      overloadTitle: "Progressive overload",
      overloadNeutral: "Log performances first; then a safe trend status appears.",
      overloadRepeat: "Previous performance available. Repeat it steadily before increasing.",
      overloadPotential: "All sets completed with room left. A small increase can later be considered.",
      exerciseLibrary: "Exercise library",
      archivePlan: "Archive",
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
      freeLimitText: "Free kann maximal 4 aktive Trainingsplaene nutzen.",
      activePlans: "{count}/{limit} aktive Plaene",
      unlimitedPlans: "Unbegrenzt ueber Pro/PT",
      createPlan: "Plan erstellen",
      planTitle: "Planname",
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
      addPlan: "Aktiven Plan speichern",
      limitReached: "Free Limit erreicht. Archiviere zuerst einen Plan oder upgrade spaeter auf Pro/PT.",
      plans: "Plaene",
      noPlans: "Noch keine normalisierten Plaene. Legacy-Plaene bleiben unten als Bridge verfuegbar.",
      legacyPlan: "Legacy-Plan",
      legacyBridge: "Legacy-Training bleibt sichtbar und wird durch Phase 3 nicht angepasst.",
      startWorkout: "Workout starten",
      continueWorkout: "Workout fortsetzen",
      pause: "Pausieren",
      resume: "Fortsetzen",
      completeWorkout: "Workout abschliessen",
      activeWorkout: "Aktives Workout",
      paused: "Pausiert",
      active: "Aktiv",
      completed: "Abgeschlossen",
      completeSet: "Satz speichern",
      setDone: "Satz gespeichert",
      timer: "Pausentimer",
      timerDone: "Pause vorbei",
      previousPerformance: "Fruehere Leistung",
      noPrevious: "Noch keine fruehere Leistung",
      prTitle: "PR Foundation",
      historyTitle: "Workout History",
      noHistory: "Noch keine abgeschlossenen Workouts.",
      overloadTitle: "Progressive Overload",
      overloadNeutral: "Logge zuerst Leistungen; danach erscheint ein sicherer Trendstatus.",
      overloadRepeat: "Fruehere Leistung verfuegbar. Wiederhole sie stabil, bevor du steigerst.",
      overloadPotential: "Alle Saetze mit Reserve geschafft. Eine kleine Steigerung kann spaeter erwogen werden.",
      exerciseLibrary: "Uebungsbibliothek",
      archivePlan: "Archivieren",
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

  const PHASE3_EXERCISES = [
    {
      slug: "bodyweight-squat",
      names: { nl: "Squat", en: "Squat", de: "Kniebeuge" },
      primary: { nl: "Benen", en: "Legs", de: "Beine" },
      equipment: { nl: "Bodyweight", en: "Bodyweight", de: "Koerpergewicht" },
      instructions: {
        nl: "Zak gecontroleerd, houd knieen stabiel en duw via je hele voet omhoog.",
        en: "Lower with control, keep knees stable and drive through the whole foot.",
        de: "Kontrolliert absenken, Knie stabil halten und ueber den ganzen Fuss hochdruecken."
      }
    },
    {
      slug: "bench-press",
      names: { nl: "Bench press", en: "Bench press", de: "Bankdruecken" },
      primary: { nl: "Borst", en: "Chest", de: "Brust" },
      equipment: { nl: "Barbell", en: "Barbell", de: "Langhantel" },
      instructions: {
        nl: "Schouderbladen vast, gecontroleerd zakken en krachtig uitstoten.",
        en: "Set the shoulder blades, lower under control and press strongly.",
        de: "Schulterblaetter fixieren, kontrolliert absenken und kraftvoll druecken."
      }
    },
    {
      slug: "deadlift",
      names: { nl: "Deadlift", en: "Deadlift", de: "Kreuzheben" },
      primary: { nl: "Rug/benen", en: "Back/legs", de: "Ruecken/Beine" },
      equipment: { nl: "Barbell", en: "Barbell", de: "Langhantel" },
      instructions: {
        nl: "Houd rug neutraal, breng spanning op de stang en strek heupen gecontroleerd.",
        en: "Keep a neutral back, take tension on the bar and extend the hips with control.",
        de: "Ruecken neutral halten, Spannung aufbauen und Huefte kontrolliert strecken."
      }
    },
    {
      slug: "lat-pulldown",
      names: { nl: "Lat pulldown", en: "Lat pulldown", de: "Latzug" },
      primary: { nl: "Rug", en: "Back", de: "Ruecken" },
      equipment: { nl: "Cable", en: "Cable", de: "Kabelzug" },
      instructions: {
        nl: "Trek ellebogen omlaag, houd borst hoog en controleer de terugweg.",
        en: "Pull elbows down, keep the chest tall and control the return.",
        de: "Ellbogen nach unten ziehen, Brust hoch halten und Rueckweg kontrollieren."
      }
    },
    {
      slug: "dumbbell-row",
      names: { nl: "Dumbbell row", en: "Dumbbell row", de: "Kurzhantelrudern" },
      primary: { nl: "Rug", en: "Back", de: "Ruecken" },
      equipment: { nl: "Dumbbell", en: "Dumbbell", de: "Kurzhantel" },
      instructions: {
        nl: "Trek naar je heup, blijf stabiel en laat het gewicht gecontroleerd zakken.",
        en: "Row toward the hip, stay stable and lower the weight with control.",
        de: "Zur Huefte ziehen, stabil bleiben und das Gewicht kontrolliert absenken."
      }
    },
    {
      slug: "plank",
      names: { nl: "Plank", en: "Plank", de: "Plank" },
      primary: { nl: "Core", en: "Core", de: "Core" },
      equipment: { nl: "Bodyweight", en: "Bodyweight", de: "Koerpergewicht" },
      instructions: {
        nl: "Span buik en billen aan, houd je lichaam lang en adem rustig door.",
        en: "Brace abs and glutes, keep the body long and breathe calmly.",
        de: "Bauch und Gesäß anspannen, Koerper lang halten und ruhig atmen."
      }
    }
  ];

  window.FMZ_PHASE3_TRAINING_ENGINE = {
    version: PHASE3_VERSION,
    surfaces: ["client_training", "active_workout", "training_history", "exercise_library"],
    tables: [
      "training_plans",
      "training_plan_days",
      "training_plan_exercises",
      "workout_sessions",
      "workout_set_logs"
    ],
    freeActivePlanLimit: PHASE3_FREE_ACTIVE_PLAN_LIMIT,
    noAiCalls: PHASE3_NO_AI_CALLS,
    noMutationObserver: PHASE3_NO_MUTATION_OBSERVER,
    noPolling: PHASE3_NO_POLLING,
    noFullWorkspaceSetSave: PHASE3_NO_FULL_WORKSPACE_SET_SAVE
  };

  let phase3UserKey = "";
  let phase3State = phase3EmptyState();
  let phase3Hydrating = false;
  let phase3TimerId = null;
  let phase3TimerEndsAt = 0;
  let phase3TrainingInitialHtml = "";

  function phase3EmptyState() {
    return {
      hydrated: false,
      migrationReady: false,
      syncMessage: "",
      plans: [],
      history: [],
      activeSession: null
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

  function phase3Id(prefix = "phase3") {
    const random = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return `${prefix}-${random}`;
  }

  function phase3IsoNow() {
    return new Date().toISOString();
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

  function phase3ExerciseName(slug) {
    const item = phase3Exercise(slug);
    if (!item) return String(slug || phase3Text("exercise"));
    return item.names[phase3Language()] || item.names.nl;
  }

  function phase3ExerciseMeta(slug) {
    const item = phase3Exercise(slug) || PHASE3_EXERCISES[0];
    const language = phase3Language();
    return {
      name: item.names[language] || item.names.nl,
      primary: item.primary[language] || item.primary.nl,
      equipment: item.equipment[language] || item.equipment.nl,
      instructions: item.instructions[language] || item.instructions.nl
    };
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

  function phase3ActivePlanLimit() {
    return phase3HasUnlimitedTraining() ? Infinity : PHASE3_FREE_ACTIVE_PLAN_LIMIT;
  }

  function phase3ActivePlans() {
    return phase3State.plans.filter((plan) => plan.status === "active");
  }

  function phase3CanCreateActivePlan() {
    const limit = phase3ActivePlanLimit();
    return limit === Infinity || phase3ActivePlans().length < limit;
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

  function phase3LoadLocal() {
    try {
      const raw = localStorage.getItem(phase3StorageKey());
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        phase3State.activeSession = parsed.activeSession || phase3State.activeSession;
        phase3State.plans = Array.isArray(parsed.localPlans) ? parsed.localPlans : phase3State.plans;
        phase3State.history = Array.isArray(parsed.localHistory) ? parsed.localHistory : phase3State.history;
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
        localHistory: phase3State.history.filter((entry) => entry.localOnly).slice(0, 20)
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
    phase3LoadLocal();
  }

  function phase3UsesSupabase() {
    return Boolean(isOnlineMode() && supabaseClient && onlineProfile?.role === "client" && onlineProfile?.id);
  }

  function phase3MigrationMissing(error) {
    return /fmz_phase3_create_training_plan|training_plans|workout_sessions|workout_set_logs|schema cache|not find|does not exist|relation/i.test(error?.message || "");
  }

  function phase3PlanFromRow(row, daysByPlan, exercisesByDay) {
    const days = (daysByPlan[row.id] || []).map((day) => ({
      id: day.id,
      label: day.day_label,
      order: day.day_order,
      notes: day.notes || "",
      exercises: (exercisesByDay[day.id] || []).map((exercise) => ({
        id: exercise.id,
        key: exercise.id,
        slug: exercise.exercise_slug,
        name: exercise.exercise_name_snapshot,
        order: exercise.exercise_order,
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
          .select("id,training_plan_id,day_label,day_order,notes")
          .in("training_plan_id", planIds)
          .order("day_order", { ascending: true });
        if (dayResult.error) throw dayResult.error;
        days = dayResult.data || [];
        const dayIds = days.map((day) => day.id);
        if (dayIds.length) {
          const exerciseResult = await supabaseClient
            .from("training_plan_exercises")
            .select("id,training_plan_day_id,exercise_slug,exercise_name_snapshot,exercise_order,target_sets,target_reps,target_weight,target_rir,target_rpe,rest_seconds,tempo,notes")
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
          .select("id,user_id,workout_session_id,training_plan_exercise_id,planned_exercise_key,exercise_slug,exercise_name_snapshot,set_index,target_reps,target_weight,actual_reps,actual_weight,rir,rpe,notes,completed_at,source")
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
          completedAt: session.completed_at,
          source: session.source,
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
      } else if (localActive) {
        phase3State.activeSession = localActive;
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
      completedAt: session.completed_at || "",
      plannedExercises: Array.isArray(session.metadata?.plannedExercises) ? session.metadata.plannedExercises : [],
      setLogs: setMap
    };
  }

  async function phase3PersistPlan(plan) {
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
    phase3SaveLocal();
    return { ok: true };
  }

  function phase3BuildPlanFromForm(form) {
    const data = new FormData(form);
    const slug = String(data.get("exerciseSlug") || PHASE3_EXERCISES[0].slug);
    const meta = phase3ExerciseMeta(slug);
    const planId = phase3Id("plan");
    const dayId = phase3Id("day");
    const exerciseId = phase3Id("plan-exercise");
    const dayLabel = String(data.get("dayLabel") || "Maandag");
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
        notes: "",
        exercises: [{
          id: exerciseId,
          key: exerciseId,
          slug,
          name: meta.name,
          order: 0,
          targetSets: Math.max(1, Math.min(20, phase3Number(data.get("sets"), 3))),
          targetReps: String(data.get("reps") || "8-10").slice(0, 40),
          targetWeight: phase3Number(data.get("targetWeight"), ""),
          targetRir: phase3Number(data.get("targetRir"), ""),
          targetRpe: phase3Number(data.get("targetRpe"), ""),
          restSeconds: Math.max(0, Math.min(3600, phase3Number(data.get("restSeconds"), 90))),
          tempo: "",
          notes: String(data.get("notes") || "").trim().slice(0, 500)
        }]
      }],
      localOnly: false
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
    const id = phase3Id("session");
    const startedAt = phase3IsoNow();
    const plannedExercises = day.exercises.map((exercise, index) => ({
      ...exercise,
      key: exercise.key || exercise.id || `${exercise.slug}-${index}`
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
      completedAt: "",
      plannedExercises,
      setLogs: {}
    };
  }

  async function phase3StartWorkout(planId, dayId) {
    const plan = phase3PlansForDisplay().find((item) => item.id === planId);
    const day = plan?.days.find((item) => item.id === dayId);
    if (!plan || !day || !day.exercises.length) return;
    if (phase3State.activeSession && ["active", "paused"].includes(phase3State.activeSession.status)) {
      renderTraining();
      return;
    }
    phase3State.activeSession = phase3CreateSession(plan, day);
    phase3SaveLocal();
    await phase3SyncActiveSession();
    renderTraining();
  }

  async function phase3SyncActiveSession() {
    const session = phase3State.activeSession;
    if (!session || !phase3UsesSupabase()) return { ok: false, skipped: true };
    try {
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
          completed_at: session.completedAt || null,
          source: session.source,
          metadata: {
            phase: 3,
            version: PHASE3_VERSION,
            plannedExercises: session.plannedExercises
          }
        }, { onConflict: "id" });
      if (error) throw error;
      const unsynced = Object.values(session.setLogs || {}).filter((setLog) => !setLog.syncedAt);
      for (const setLog of unsynced) {
        await phase3PersistSetLog(setLog);
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
          training_plan_exercise_id: setLog.trainingPlanExerciseId || null,
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
          source: setLog.source || phase3State.activeSession.source
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

  async function phase3CompleteSet(setKey) {
    const session = phase3State.activeSession;
    if (!session) return;
    const [exerciseKey, rawSetIndex] = setKey.split("__");
    const exercise = session.plannedExercises.find((item) => String(item.key) === exerciseKey);
    if (!exercise) return;
    const setIndex = Number(rawSetIndex);
    const inputs = phase3ReadSetInputs(setKey);
    const setLog = {
      id: session.setLogs[setKey]?.id || phase3Id("set-log"),
      plannedExerciseKey: String(exercise.key),
      trainingPlanExerciseId: exercise.id && !String(exercise.id).startsWith("legacy") ? exercise.id : "",
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
    phase3SaveLocal();
    phase3StartTimer(exercise.restSeconds || 90);
    await phase3SyncActiveSession();
    renderTraining();
  }

  async function phase3SetSessionStatus(status) {
    const session = phase3State.activeSession;
    if (!session) return;
    session.status = status;
    if (status === "paused") session.pausedAt = phase3IsoNow();
    if (status === "active") session.pausedAt = "";
    phase3SaveLocal();
    await phase3SyncActiveSession();
    renderTraining();
  }

  async function phase3CompleteWorkout() {
    const session = phase3State.activeSession;
    if (!session) return;
    session.status = "completed";
    session.completedAt = phase3IsoNow();
    await phase3SyncActiveSession();
    const historyEntry = {
      id: session.id,
      title: session.planTitle,
      dayLabel: session.dayLabel,
      completedAt: session.completedAt,
      source: session.source,
      localOnly: true,
      sets: Object.values(session.setLogs || {})
    };
    phase3State.history.unshift(historyEntry);
    phase3State.activeSession = null;
    phase3StopTimer();
    phase3SaveLocal();
    renderTraining();
  }

  function phase3RecordCandidates(setLog) {
    const exerciseSlug = setLog.exerciseSlug || setLog.exercise_slug || "";
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
      .filter((candidate) => exerciseSlug && candidate.value)
      .map((candidate) => ({
        exercise_slug: exerciseSlug,
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
          exerciseSlug: setLog.exerciseSlug || setLog.exercise_slug,
          actualReps: setLog.actualReps ?? setLog.actual_reps,
          actualWeight: setLog.actualWeight ?? setLog.actual_weight,
          completedAt: setLog.completedAt || setLog.completed_at
        };
        phase3RecordCandidates(normalized).forEach((candidate) => {
          const key = `${candidate.exercise_slug}:${candidate.metric}`;
          const previous = records[key];
          if (!previous || Number(candidate.value) > Number(previous.value || 0)) {
            records[key] = candidate;
          }
        });
      });
    return Object.values(records);
  }

  function phase3PreviousPerformance(exerciseSlug) {
    const sets = phase3State.history
      .flatMap((entry) => entry.sets || [])
      .filter((setLog) => setLog.exercise_slug === exerciseSlug || setLog.exerciseSlug === exerciseSlug)
      .sort((a, b) => String(b.completed_at || b.completedAt || "").localeCompare(String(a.completed_at || a.completedAt || "")));
    const first = sets[0];
    if (!first) return "";
    const reps = first.actual_reps ?? first.actualReps ?? "-";
    const weight = first.actual_weight ?? first.actualWeight ?? "-";
    return `${weight} kg x ${reps}`;
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

  function phase3StartTimer(seconds) {
    phase3StopTimer();
    phase3TimerEndsAt = Date.now() + Math.max(0, Number(seconds || 0)) * 1000;
    phase3UpdateTimerText();
    phase3TimerId = window.setInterval(() => {
      phase3UpdateTimerText();
      if (Date.now() >= phase3TimerEndsAt) phase3StopTimer(true);
    }, 1000);
  }

  function phase3StopTimer(done = false) {
    if (phase3TimerId) {
      window.clearInterval(phase3TimerId);
      phase3TimerId = null;
    }
    if (done) {
      const target = document.querySelector("[data-phase3-timer]");
      if (target) target.textContent = phase3Text("timerDone");
    }
  }

  function phase3UpdateTimerText() {
    const target = document.querySelector("[data-phase3-timer]");
    if (!target || !phase3TimerEndsAt) return;
    const remaining = Math.max(0, Math.ceil((phase3TimerEndsAt - Date.now()) / 1000));
    const minutes = Math.floor(remaining / 60);
    const seconds = String(remaining % 60).padStart(2, "0");
    target.textContent = `${phase3Text("timer")}: ${minutes}:${seconds}`;
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
      .phase3-card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; box-shadow: var(--shadow); }
      .phase3-form-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
      .phase3-form-grid .wide { grid-column: 1 / -1; }
      .phase3-plan-list, .phase3-history-list, .phase3-library-list { display: grid; gap: 10px; }
      .phase3-plan-card { border: 1px solid var(--line); border-radius: 8px; padding: 12px; display: grid; gap: 10px; }
      .phase3-plan-head, .phase3-day-head, .phase3-set-row, .phase3-history-item { display: flex; justify-content: space-between; gap: 10px; align-items: center; flex-wrap: wrap; }
      .phase3-exercise-list { display: grid; gap: 8px; }
      .phase3-exercise-line { border-top: 1px solid var(--line); padding-top: 8px; display: grid; gap: 8px; }
      .phase3-workout-panel { display: grid; gap: 12px; border-color: rgba(200,147,18,.45); }
      .phase3-set-grid { display: grid; grid-template-columns: repeat(5, minmax(70px, 1fr)) auto; gap: 8px; align-items: end; }
      .phase3-set-grid label { display: grid; gap: 4px; font-size: .82rem; color: var(--muted); }
      .phase3-set-grid input { min-width: 0; }
      .phase3-library-item { border: 1px solid var(--line); border-radius: 8px; padding: 10px; display: grid; gap: 4px; }
      .phase3-timer-pill { min-height: 28px; display: inline-flex; align-items: center; }
      @media (max-width: 880px) {
        .phase3-grid, .phase3-form-grid, .phase3-set-grid { grid-template-columns: 1fr; }
      }
    `;
    document.head.appendChild(style);
  }

  function phase3RenderStatus() {
    const limit = phase3ActivePlanLimit();
    const limitLabel = limit === Infinity
      ? phase3Text("unlimitedPlans")
      : phase3Format("activePlans", { count: phase3ActivePlans().length, limit });
    return `
      <div class="phase3-status-row">
        <span class="status ok">${escapeHTML(limitLabel)}</span>
        <span class="status ${phase3State.migrationReady ? "ok" : ""}">${escapeHTML(phase3State.syncMessage || phase3Text("localSafe"))}</span>
        <span class="status">${PHASE3_VERSION}</span>
      </div>
    `;
  }

  function phase3RenderPlanForm() {
    const disabled = !phase3CanCreateActivePlan();
    return `
      <section class="phase3-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase3Text("createPlan"))}</p>
            <h2>${escapeHTML(phase3Text("freeLimitTitle"))}</h2>
            <p class="muted">${escapeHTML(phase3Text("freeLimitText"))}</p>
          </div>
        </div>
        ${disabled ? `<p class="empty-mini">${escapeHTML(phase3Text("limitReached"))}</p>` : ""}
        <form id="phase3PlanForm" class="phase3-form-grid">
          <label class="field"><span>${escapeHTML(phase3Text("planTitle"))}</span><input name="title" required placeholder="Full body A" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("day"))}</span><select name="dayLabel" ${disabled ? "disabled" : ""}>${DAYS.map((day) => `<option value="${escapeHTML(day)}">${escapeHTML(phase3Text(day))}</option>`).join("")}</select></label>
          <label class="field"><span>${escapeHTML(phase3Text("exercise"))}</span><select name="exerciseSlug" ${disabled ? "disabled" : ""}>${PHASE3_EXERCISES.map((exercise) => `<option value="${exercise.slug}">${escapeHTML(phase3ExerciseName(exercise.slug))}</option>`).join("")}</select></label>
          <label class="field"><span>${escapeHTML(phase3Text("sets"))}</span><input name="sets" type="number" min="1" max="20" value="3" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("reps"))}</span><input name="reps" value="8-10" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("targetWeight"))}</span><input name="targetWeight" type="number" min="0" step="0.5" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("rir"))}</span><input name="targetRir" type="number" min="0" max="10" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("rpe"))}</span><input name="targetRpe" type="number" min="1" max="10" step="0.5" ${disabled ? "disabled" : ""} /></label>
          <label class="field"><span>${escapeHTML(phase3Text("rest"))}</span><input name="restSeconds" type="number" min="0" max="3600" value="90" ${disabled ? "disabled" : ""} /></label>
          <label class="field wide"><span>${escapeHTML(phase3Text("notes"))}</span><textarea name="notes" rows="2" ${disabled ? "disabled" : ""}></textarea></label>
          <div class="settings-save-row wide">
            <button class="primary-btn" type="submit" ${disabled ? "disabled" : ""}>${escapeHTML(phase3Text("addPlan"))}</button>
            <span class="save-feedback" data-save-feedback="phase3-plan"></span>
          </div>
        </form>
      </section>
    `;
  }

  function phase3RenderPlans() {
    const plans = phase3PlansForDisplay().filter((plan) => plan.status === "active");
    return `
      <section class="phase3-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase3Text("plans"))}</p>
            <h2>${escapeHTML(phase3Text("startWorkout"))}</h2>
          </div>
        </div>
        <div class="phase3-plan-list">
          ${plans.length ? plans.map((plan) => phase3RenderPlanCard(plan)).join("") : `<div class="empty-state">${escapeHTML(phase3Text("noPlans"))}</div>`}
        </div>
        ${phase3LegacyPlan() ? `<p class="muted">${escapeHTML(phase3Text("legacyBridge"))}</p>` : ""}
      </section>
    `;
  }

  function phase3RenderPlanCard(plan) {
    return `
      <article class="phase3-plan-card">
        <div class="phase3-plan-head">
          <div>
            <strong>${escapeHTML(plan.title)}</strong>
            <span class="muted">${escapeHTML(plan.source === "legacy_bridge" ? phase3Text("legacyPlan") : phase3Text("synced"))}</span>
          </div>
          ${plan.source !== "legacy_bridge" ? `<button class="secondary-btn" data-phase3-archive-plan="${escapeHTML(plan.id)}" type="button">${escapeHTML(phase3Text("archivePlan"))}</button>` : ""}
        </div>
        ${plan.days.map((day) => `
          <div class="phase3-exercise-line">
            <div class="phase3-day-head">
              <strong>${escapeHTML(phase3Text(day.label) || day.label)}</strong>
              <button class="primary-btn" data-phase3-start-workout="${escapeHTML(plan.id)}:${escapeHTML(day.id)}" type="button">${escapeHTML(phase3Text("startWorkout"))}</button>
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
      <section class="phase3-card phase3-workout-panel">
        <div class="phase3-plan-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase3Text("activeWorkout"))}</p>
            <h2>${escapeHTML(session.planTitle)} ${session.dayLabel ? `- ${escapeHTML(phase3Text(session.dayLabel) || session.dayLabel)}` : ""}</h2>
            <span class="status ${isPaused ? "" : "ok"}">${escapeHTML(isPaused ? phase3Text("paused") : phase3Text("active"))}</span>
          </div>
          <div class="phase3-status-row">
            <span class="status phase3-timer-pill" data-phase3-timer>${escapeHTML(phase3Text("timer"))}</span>
            <button class="secondary-btn" data-phase3-session-status="${isPaused ? "active" : "paused"}" type="button">${escapeHTML(isPaused ? phase3Text("resume") : phase3Text("pause"))}</button>
            <button class="primary-btn" data-phase3-complete-workout type="button">${escapeHTML(phase3Text("completeWorkout"))}</button>
          </div>
        </div>
        ${session.plannedExercises.map((exercise) => phase3RenderWorkoutExercise(exercise, session)).join("")}
      </section>
    `;
  }

  function phase3RenderWorkoutExercise(exercise, session) {
    const previous = phase3PreviousPerformance(exercise.slug);
    return `
      <article class="phase3-plan-card">
        <div>
          <strong>${escapeHTML(exercise.name)}</strong>
          <p class="muted">${escapeHTML(phase3Text("previousPerformance"))}: ${escapeHTML(previous || phase3Text("noPrevious"))}</p>
          <p class="muted">${escapeHTML(phase3Text("overloadTitle"))}: ${escapeHTML(phase3OverloadSignal(exercise, session))}</p>
        </div>
        ${Array.from({ length: Number(exercise.targetSets || 1) }).map((_, index) => phase3RenderSetRow(exercise, index + 1, session)).join("")}
      </article>
    `;
  }

  function phase3RenderSetRow(exercise, setIndex, session) {
    const key = phase3SetKey(exercise, setIndex);
    const saved = session.setLogs?.[key] || {};
    return `
      <div class="phase3-set-grid" data-phase3-set-row="${escapeHTML(key)}">
        <label>${escapeHTML(phase3Text("reps"))}<input data-phase3-reps="${escapeHTML(key)}" type="number" min="0" value="${escapeHTML(saved.actualReps ?? "")}" placeholder="${escapeHTML(exercise.targetReps || "")}" /></label>
        <label>${escapeHTML(phase3Text("weight"))}<input data-phase3-weight="${escapeHTML(key)}" type="number" min="0" step="0.5" value="${escapeHTML(saved.actualWeight ?? "")}" placeholder="${escapeHTML(String(exercise.targetWeight ?? ""))}" /></label>
        <label>${escapeHTML(phase3Text("rir"))}<input data-phase3-rir="${escapeHTML(key)}" type="number" min="0" max="10" value="${escapeHTML(saved.rir ?? "")}" /></label>
        <label>${escapeHTML(phase3Text("rpe"))}<input data-phase3-rpe="${escapeHTML(key)}" type="number" min="1" max="10" step="0.5" value="${escapeHTML(saved.rpe ?? "")}" /></label>
        <label>${escapeHTML(phase3Text("notes"))}<input data-phase3-notes="${escapeHTML(key)}" value="${escapeHTML(saved.notes ?? "")}" /></label>
        <button class="secondary-btn" data-phase3-complete-set="${escapeHTML(key)}" type="button">${escapeHTML(saved.completedAt ? phase3Text("setDone") : phase3Text("completeSet"))}</button>
      </div>
    `;
  }

  function phase3RenderHistory() {
    const history = phase3State.history.slice(0, 5);
    const records = phase3DerivedPersonalRecords().slice(0, 6);
    return `
      <section class="phase3-card">
        <div class="panel-head compact-head">
          <h2>${escapeHTML(phase3Text("historyTitle"))}</h2>
        </div>
        <div class="phase3-history-list">
          ${history.length ? history.map((entry) => `
            <div class="phase3-history-item">
              <span>${escapeHTML(entry.title)} ${entry.dayLabel ? `- ${escapeHTML(phase3Text(entry.dayLabel) || entry.dayLabel)}` : ""}</span>
              <strong>${escapeHTML(String(entry.completedAt || "").slice(0, 10))}</strong>
            </div>
          `).join("") : `<div class="empty-mini">${escapeHTML(phase3Text("noHistory"))}</div>`}
        </div>
        <div class="panel-head compact-head">
          <h2>${escapeHTML(phase3Text("prTitle"))}</h2>
        </div>
        <div class="phase3-history-list">
          ${records.length ? records.map((record) => `
            <div class="phase3-history-item">
              <span>${escapeHTML(phase3ExerciseName(record.exercise_slug) || record.exercise_slug)} - ${escapeHTML(record.metric)}</span>
              <strong>${escapeHTML(String(record.value))} ${escapeHTML(record.unit)}</strong>
            </div>
          `).join("") : `<div class="empty-mini">${escapeHTML(phase3Text("overloadNeutral"))}</div>`}
        </div>
      </section>
    `;
  }

  function phase3RenderLibrary() {
    return `
      <section class="phase3-card">
        <div class="panel-head compact-head">
          <h2>${escapeHTML(phase3Text("exerciseLibrary"))}</h2>
        </div>
        <div class="phase3-library-list">
          ${PHASE3_EXERCISES.map((exercise) => {
            const meta = phase3ExerciseMeta(exercise.slug);
            return `
              <article class="phase3-library-item">
                <strong>${escapeHTML(meta.name)}</strong>
                <span>${escapeHTML(phase3Text("muscle"))}: ${escapeHTML(meta.primary)} - ${escapeHTML(phase3Text("equipment"))}: ${escapeHTML(meta.equipment)}</span>
                <p class="muted">${escapeHTML(meta.instructions)}</p>
              </article>
            `;
          }).join("")}
        </div>
      </section>
    `;
  }

  function phase3RenderClientTraining() {
    const selected = client();
    if (!hasSelectedClient(selected)) {
      return `<div class="empty-state">${escapeHTML(phase3Text("noPlans"))}</div>`;
    }
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
        <div class="phase3-grid">
          <div class="phase3-shell">
            ${phase3RenderPlanForm()}
            ${phase3RenderPlans()}
          </div>
          <div class="phase3-shell">
            ${phase3RenderHistory()}
            ${phase3RenderLibrary()}
          </div>
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
      phase3UpdateTimerText();
      return;
    }
    const section = document.getElementById("training");
    if (section?.dataset.phase3Mode === "client") {
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
      const hydrated = await phase3HydrateTraining(profile);
      if (hydrated && isLoggedIn() && state.ui.role === "client") renderTraining();
    }
  };

  const phase3OriginalShowView = showView;
  showView = function showViewPhase3(view) {
    if (view !== "training") phase3StopTimer();
    return phase3OriginalShowView(view);
  };

  const phase3OriginalRenderAll = renderAll;
  renderAll = function renderAllPhase3() {
    if (!isLoggedIn()) {
      phase3StopTimer();
      phase3State = phase3EmptyState();
      phase3UserKey = "";
    }
    return phase3OriginalRenderAll();
  };

  document.addEventListener("submit", async (event) => {
    if (event.target?.id !== "phase3PlanForm") return;
    event.preventDefault();
    if (!phase3CanCreateActivePlan()) {
      setSaveFeedback("phase3-plan", phase3Text("limitReached"), true);
      return;
    }
    const plan = phase3BuildPlanFromForm(event.target);
    const result = await phase3PersistPlan(plan);
    if (!result.ok) {
      setSaveFeedback("phase3-plan", phase3Format("saveFailed", { message: result.error.message }), true);
      return;
    }
    event.target.reset();
    setSaveFeedback("phase3-plan", result.local ? phase3Text("localSafe") : phase3Text("saved"));
    renderTraining();
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    if (button.dataset.phase3StartWorkout) {
      const [planId, dayId] = button.dataset.phase3StartWorkout.split(":");
      await phase3StartWorkout(planId, dayId);
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
      if (!result.ok) setSaveFeedback("phase3-plan", phase3Format("saveFailed", { message: result.error.message }), true);
      renderTraining();
    }
  });

  window.addEventListener("online", () => {
    if (!phase3State.activeSession) return;
    phase3SyncActiveSession().then(() => {
      if (currentView === "training") renderTraining();
    });
  });
})();
