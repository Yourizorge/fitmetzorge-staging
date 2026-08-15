(function phase1Foundation() {
  const PHASE1_LANGUAGES = ["nl", "en", "de"];
  const PHASE1_GENDERS = ["female", "male", "non_binary", "prefer_not_to_say", "not_relevant"];
  const PHASE1_GOAL_DIRECTIONS = ["lose_weight", "gain_muscle", "recomposition", "fitness", "health", "other"];

  const PHASE1_I18N = {
    nl: {
      onboardingTitle: "Mijn basisprofiel",
      onboardingIntro: "Vul je basisgegevens in. FitMetZorge berekent BMI en bewaakt dat je doel realistisch blijft.",
      save: "Basisprofiel opslaan",
      accountTitle: "Account & taal",
      language: "Taal",
      saved: "Basisprofiel opgeslagen",
      migrationNeeded: "Phase 1 database-migration is nog nodig voor online profielopslag.",
      complete: "Compleet",
      incomplete: "Nog aanvullen",
      country: "Land/regio",
      defaultCountry: "Nederland",
      units: "Eenheden",
      metric: "Metrisch",
      saveAccountSettings: "Accountinstellingen opslaan",
      accountSettingsSaved: "Accountinstellingen opgeslagen",
      settingsNav: "Instellingen",
      choose: "Kies...",
      accountEyebrow: "Account",
      firstName: "Voornaam",
      lastName: "Achternaam",
      age: "Leeftijd",
      gender: "Geslacht",
      heightCm: "Lengte cm",
      currentWeightKg: "Huidig gewicht kg",
      goalDirection: "Doelrichting",
      targetWeightKg: "Doelgewicht kg",
      trainingExperience: "Trainingservaring",
      availableDays: "Beschikbare dagen",
      bmi: "BMI",
      fitnessGoal: "Fitnessdoel",
      nutritionPreferences: "Voedingsvoorkeuren",
      practicalConstraints: "Praktische beperkingen",
      goalEngine: "Goal Engine",
      genderFemale: "Vrouw",
      genderMale: "Man",
      genderNonBinary: "Non-binair",
      genderPreferNot: "Zeg ik liever niet",
      genderNotRelevant: "Niet relevant",
      goalLoseWeight: "Afvallen",
      goalGainMuscle: "Spiermassa opbouwen",
      goalRecomposition: "Vet verliezen en sterker worden",
      goalFitness: "Fitter worden",
      goalHealth: "Gezondheid verbeteren",
      goalOther: "Anders",
      trainingBeginner: "Beginner",
      trainingIntermediate: "Gemiddeld",
      trainingAdvanced: "Ervaren",
      defaultGoalSafetyNote: "Vul lengte, gewicht, doelrichting en doelgewicht in voor een realistische inschatting.",
      goalNeedsInputNote: "Vul je huidige situatie en einddoel in. Een weektempo wordt niet vrij gekozen.",
      goalNeedsTargetNote: "Vul een doelgewicht in zodat FitMetZorge een realistische richting kan bewaken.",
      goalSavedNoTempoNote: "Doel opgeslagen zonder vrij weektempo. Verdere fasering komt in latere coachingstappen.",
      goalLoseMismatchNote: "Je doelrichting is afvallen, maar je doelgewicht ligt niet lager dan je huidige gewicht.",
      goalGainMismatchNote: "Je doelrichting is spiermassa opbouwen, maar je doelgewicht ligt niet hoger dan je huidige gewicht.",
      goalNeedsReviewNote: "Dit doel vraagt waarschijnlijk om extra fasering. Het wordt opgeslagen, maar moet later bewust worden beoordeeld.",
      goalRealisticTimelineNote: "Realistische basisrichting. Vrij weektempo wordt niet opgeslagen; indicatieve veilige fasering: ongeveer {weeks} weken.",
      entitlementActive: "Actief",
      entitlementInactive: "Niet actief",
      entitlementActiveViaCoaching: "Actief via coaching",
      entitlementLinked: "Gekoppeld",
      entitlementNotLinked: "Niet gekoppeld",
      freeUserName: "FitMetZorge gebruiker",
      saveFailed: "Opslaan mislukt",
      onlineProfileSaved: "Online profiel opgeslagen",
      onlineProfileSaveFailed: "Online profielopslag mislukt: {message}",
      onlineSettingsSaveFailed: "Online instellingen opslaan mislukt: {message}",
      originalError: "Oorspronkelijke fout: {message}",
      ageCheck: "FitMetZorge V1 is 18+. Controleer de leeftijd.",
      authLoginTab: "Inloggen",
      authRegisterTab: "Registreren",
      authAccountType: "Account type",
      authClient: "Lid",
      authTrainer: "Trainer",
      authName: "Naam",
      authEmail: "E-mail",
      authPassword: "Wachtwoord",
      authNewPassword: "Nieuw wachtwoord",
      authConfirmPassword: "Herhaal wachtwoord",
      authRegisterSubmit: "Account registreren",
      authLoginSubmit: "Inloggen",
      authForgotLink: "Wachtwoord vergeten?",
      authForgotIntro: "Vul je e-mailadres in. Je krijgt een link waarmee je een nieuw wachtwoord kunt instellen.",
      authResetSubmit: "Resetlink versturen",
      authBackToLogin: "Terug naar inloggen",
      authSetPasswordSubmit: "Wachtwoord opslaan",
      authRemember: "Inloggegevens onthouden op dit apparaat",
      authEmailPlaceholder: "email@voorbeeld.nl",
      authNamePlaceholder: "Naam",
      authPasswordPlaceholder: "Wachtwoord",
      authNewPasswordPlaceholderShort: "Minimaal 4 tekens",
      authNewPasswordPlaceholder: "Minimaal 6 tekens",
      authConfirmPasswordPlaceholder: "Herhaal wachtwoord",
      authInvitePasswordTitle: "Maak je wachtwoord aan",
      authInvitePasswordIntro: "Je uitnodiging is geopend. Kies nu een eigen wachtwoord, zodat je later normaal kunt inloggen met e-mail en wachtwoord.",
      authRecoveryPasswordTitle: "Nieuw wachtwoord instellen",
      authRecoveryPasswordIntro: "Kies een nieuw wachtwoord voor je account. Daarna kun je weer normaal inloggen.",
      trainerRegistrationUnavailable: "Trainerregistratie is niet beschikbaar via publieke registratie. Log in met een bestaand traineraccount.",
      passwordMin4: "Gebruik minimaal 4 tekens voor je wachtwoord.",
      passwordMin6: "Gebruik minimaal 6 tekens voor je wachtwoord.",
      passwordsMismatch: "De wachtwoorden zijn niet gelijk.",
      accountCreating: "Account wordt aangemaakt...",
      accountCreatedCheckEmail: "Account aangemaakt. Controleer je e-mail om je account te bevestigen en log daarna in.",
      clientAlreadyRegistered: "Dit lid is al geregistreerd. Log in met dit account.",
      passwordSetupNeedsSupabase: "Wachtwoord instellen werkt zodra Supabase in config.js is ingesteld.",
      passwordSaving: "Wachtwoord wordt opgeslagen...",
      passwordChangedLogin: "Wachtwoord gewijzigd. Je kunt nu inloggen.",
      passwordChangedLoginAgain: "Wachtwoord aangepast. Log opnieuw in met je nieuwe wachtwoord.",
      passwordChanged: "Wachtwoord aangepast.",
      passwordChangeFailed: "Wachtwoord aanpassen mislukt: {message}"
    },
    en: {
      onboardingTitle: "My base profile",
      onboardingIntro: "Enter your core details. FitMetZorge calculates BMI and keeps the goal realistic.",
      save: "Save base profile",
      accountTitle: "Account & language",
      language: "Language",
      saved: "Base profile saved",
      migrationNeeded: "Phase 1 database migration is still needed for online profile storage.",
      complete: "Complete",
      incomplete: "Needs input",
      country: "Country/region",
      defaultCountry: "Netherlands",
      units: "Units",
      metric: "Metric",
      saveAccountSettings: "Save account settings",
      accountSettingsSaved: "Account settings saved",
      settingsNav: "Settings",
      choose: "Choose...",
      accountEyebrow: "Account",
      firstName: "First name",
      lastName: "Last name",
      age: "Age",
      gender: "Gender",
      heightCm: "Height cm",
      currentWeightKg: "Current weight kg",
      goalDirection: "Goal direction",
      targetWeightKg: "Target weight kg",
      trainingExperience: "Training experience",
      availableDays: "Available days",
      bmi: "BMI",
      fitnessGoal: "Fitness goal",
      nutritionPreferences: "Nutrition preferences",
      practicalConstraints: "Practical constraints",
      goalEngine: "Goal Engine",
      genderFemale: "Female",
      genderMale: "Male",
      genderNonBinary: "Non-binary",
      genderPreferNot: "Prefer not to say",
      genderNotRelevant: "Not relevant",
      goalLoseWeight: "Lose weight",
      goalGainMuscle: "Gain muscle",
      goalRecomposition: "Lose fat and get stronger",
      goalFitness: "Improve fitness",
      goalHealth: "Improve health",
      goalOther: "Other",
      trainingBeginner: "Beginner",
      trainingIntermediate: "Intermediate",
      trainingAdvanced: "Advanced",
      defaultGoalSafetyNote: "Enter height, weight, goal direction and target weight for a realistic estimate.",
      goalNeedsInputNote: "Enter your current situation and end goal. A free weekly pace is not stored.",
      goalNeedsTargetNote: "Enter a target weight so FitMetZorge can guard a realistic direction.",
      goalSavedNoTempoNote: "Goal saved without a free weekly pace. Further phasing comes in later coaching steps.",
      goalLoseMismatchNote: "Your goal direction is weight loss, but your target weight is not below your current weight.",
      goalGainMismatchNote: "Your goal direction is muscle gain, but your target weight is not above your current weight.",
      goalNeedsReviewNote: "This goal probably needs extra phasing. It is saved, but should be reviewed consciously later.",
      goalRealisticTimelineNote: "Realistic foundation. Free weekly pace is not stored; indicative safe phasing: about {weeks} weeks.",
      entitlementActive: "Active",
      entitlementInactive: "Inactive",
      entitlementActiveViaCoaching: "Active via coaching",
      entitlementLinked: "Linked",
      entitlementNotLinked: "Not linked",
      freeUserName: "FitMetZorge user",
      saveFailed: "Save failed",
      onlineProfileSaved: "Online profile saved",
      onlineProfileSaveFailed: "Online profile save failed: {message}",
      onlineSettingsSaveFailed: "Online settings save failed: {message}",
      originalError: "Original error: {message}",
      ageCheck: "FitMetZorge V1 is 18+. Check the age.",
      authLoginTab: "Log in",
      authRegisterTab: "Register",
      authAccountType: "Account type",
      authClient: "Member",
      authTrainer: "Trainer",
      authName: "Name",
      authEmail: "Email",
      authPassword: "Password",
      authNewPassword: "New password",
      authConfirmPassword: "Repeat password",
      authRegisterSubmit: "Register account",
      authLoginSubmit: "Log in",
      authForgotLink: "Forgot password?",
      authForgotIntro: "Enter your email address. You will receive a link to set a new password.",
      authResetSubmit: "Send reset link",
      authBackToLogin: "Back to login",
      authSetPasswordSubmit: "Save password",
      authRemember: "Remember login details on this device",
      authEmailPlaceholder: "email@example.com",
      authNamePlaceholder: "Name",
      authPasswordPlaceholder: "Password",
      authNewPasswordPlaceholderShort: "At least 4 characters",
      authNewPasswordPlaceholder: "At least 6 characters",
      authConfirmPasswordPlaceholder: "Repeat password",
      authInvitePasswordTitle: "Create your password",
      authInvitePasswordIntro: "Your invitation is open. Choose your own password so you can log in normally with email and password later.",
      authRecoveryPasswordTitle: "Set a new password",
      authRecoveryPasswordIntro: "Choose a new password for your account. After that, you can log in normally again.",
      trainerRegistrationUnavailable: "Trainer registration is not available through public registration. Log in with an existing trainer account.",
      passwordMin4: "Use at least 4 characters for your password.",
      passwordMin6: "Use at least 6 characters for your password.",
      passwordsMismatch: "The passwords do not match.",
      accountCreating: "Creating account...",
      accountCreatedCheckEmail: "Account created. Check your email to confirm your account, then log in.",
      clientAlreadyRegistered: "This member is already registered. Log in with this account.",
      passwordSetupNeedsSupabase: "Password setup works once Supabase is configured in config.js.",
      passwordSaving: "Saving password...",
      passwordChangedLogin: "Password changed. You can now log in.",
      passwordChangedLoginAgain: "Password changed. Log in again with your new password.",
      passwordChanged: "Password changed.",
      passwordChangeFailed: "Password change failed: {message}"
    },
    de: {
      onboardingTitle: "Mein Basisprofil",
      onboardingIntro: "Trage deine Basisdaten ein. FitMetZorge berechnet BMI und achtet auf ein realistisches Ziel.",
      save: "Basisprofil speichern",
      accountTitle: "Account & Sprache",
      language: "Sprache",
      saved: "Basisprofil gespeichert",
      migrationNeeded: "Phase 1 Datenbankmigration ist noch fuer Online-Profilspeicherung erforderlich.",
      complete: "Vollstaendig",
      incomplete: "Noch ergaenzen",
      country: "Land/Region",
      defaultCountry: "Niederlande",
      units: "Einheiten",
      metric: "Metrisch",
      saveAccountSettings: "Kontoeinstellungen speichern",
      accountSettingsSaved: "Kontoeinstellungen gespeichert",
      settingsNav: "Einstellungen",
      choose: "Waehlen...",
      accountEyebrow: "Konto",
      firstName: "Vorname",
      lastName: "Nachname",
      age: "Alter",
      gender: "Geschlecht",
      heightCm: "Groesse cm",
      currentWeightKg: "Aktuelles Gewicht kg",
      goalDirection: "Zielrichtung",
      targetWeightKg: "Zielgewicht kg",
      trainingExperience: "Trainingserfahrung",
      availableDays: "Verfuegbare Tage",
      bmi: "BMI",
      fitnessGoal: "Fitnessziel",
      nutritionPreferences: "Ernaehrungsvorlieben",
      practicalConstraints: "Praktische Einschraenkungen",
      goalEngine: "Ziel-Engine",
      genderFemale: "Frau",
      genderMale: "Mann",
      genderNonBinary: "Non-binaer",
      genderPreferNot: "Sage ich lieber nicht",
      genderNotRelevant: "Nicht relevant",
      goalLoseWeight: "Abnehmen",
      goalGainMuscle: "Muskelmasse aufbauen",
      goalRecomposition: "Fett verlieren und staerker werden",
      goalFitness: "Fitter werden",
      goalHealth: "Gesundheit verbessern",
      goalOther: "Andere",
      trainingBeginner: "Anfaenger",
      trainingIntermediate: "Mittel",
      trainingAdvanced: "Fortgeschritten",
      defaultGoalSafetyNote: "Trage Groesse, Gewicht, Zielrichtung und Zielgewicht ein, damit eine realistische Einschaetzung moeglich ist.",
      goalNeedsInputNote: "Trage deine aktuelle Situation und dein Endziel ein. Ein freies Wochentempo wird nicht gespeichert.",
      goalNeedsTargetNote: "Trage ein Zielgewicht ein, damit FitMetZorge eine realistische Richtung bewachen kann.",
      goalSavedNoTempoNote: "Ziel ohne freies Wochentempo gespeichert. Weitere Phasierung folgt in spaeteren Coaching-Schritten.",
      goalLoseMismatchNote: "Deine Zielrichtung ist Abnehmen, aber dein Zielgewicht liegt nicht unter deinem aktuellen Gewicht.",
      goalGainMismatchNote: "Deine Zielrichtung ist Muskelaufbau, aber dein Zielgewicht liegt nicht ueber deinem aktuellen Gewicht.",
      goalNeedsReviewNote: "Dieses Ziel braucht wahrscheinlich extra Phasierung. Es wird gespeichert, sollte aber spaeter bewusst bewertet werden.",
      goalRealisticTimelineNote: "Realistische Basisrichtung. Freies Wochentempo wird nicht gespeichert; indikative sichere Phasierung: etwa {weeks} Wochen.",
      entitlementActive: "Aktiv",
      entitlementInactive: "Nicht aktiv",
      entitlementActiveViaCoaching: "Aktiv ueber Coaching",
      entitlementLinked: "Gekoppelt",
      entitlementNotLinked: "Nicht gekoppelt",
      freeUserName: "FitMetZorge Nutzer",
      saveFailed: "Speichern fehlgeschlagen",
      onlineProfileSaved: "Online-Profil gespeichert",
      onlineProfileSaveFailed: "Online-Profilspeicherung fehlgeschlagen: {message}",
      onlineSettingsSaveFailed: "Online-Einstellungen speichern fehlgeschlagen: {message}",
      originalError: "Urspruenglicher Fehler: {message}",
      ageCheck: "FitMetZorge V1 ist 18+. Pruefe das Alter.",
      authLoginTab: "Einloggen",
      authRegisterTab: "Registrieren",
      authAccountType: "Kontotyp",
      authClient: "Mitglied",
      authTrainer: "Trainer",
      authName: "Name",
      authEmail: "E-Mail",
      authPassword: "Passwort",
      authNewPassword: "Neues Passwort",
      authConfirmPassword: "Passwort wiederholen",
      authRegisterSubmit: "Konto registrieren",
      authLoginSubmit: "Einloggen",
      authForgotLink: "Passwort vergessen?",
      authForgotIntro: "Gib deine E-Mail-Adresse ein. Du erhaeltst einen Link, mit dem du ein neues Passwort festlegen kannst.",
      authResetSubmit: "Reset-Link senden",
      authBackToLogin: "Zurueck zum Login",
      authSetPasswordSubmit: "Passwort speichern",
      authRemember: "Login-Daten auf diesem Geraet merken",
      authEmailPlaceholder: "email@beispiel.de",
      authNamePlaceholder: "Name",
      authPasswordPlaceholder: "Passwort",
      authNewPasswordPlaceholderShort: "Mindestens 4 Zeichen",
      authNewPasswordPlaceholder: "Mindestens 6 Zeichen",
      authConfirmPasswordPlaceholder: "Passwort wiederholen",
      authInvitePasswordTitle: "Erstelle dein Passwort",
      authInvitePasswordIntro: "Deine Einladung ist geoeffnet. Waehle jetzt ein eigenes Passwort, damit du dich spaeter normal mit E-Mail und Passwort einloggen kannst.",
      authRecoveryPasswordTitle: "Neues Passwort festlegen",
      authRecoveryPasswordIntro: "Waehle ein neues Passwort fuer dein Konto. Danach kannst du dich wieder normal einloggen.",
      trainerRegistrationUnavailable: "Trainerregistrierung ist ueber die oeffentliche Registrierung nicht verfuegbar. Logge dich mit einem bestehenden Trainerkonto ein.",
      passwordMin4: "Verwende mindestens 4 Zeichen fuer dein Passwort.",
      passwordMin6: "Verwende mindestens 6 Zeichen fuer dein Passwort.",
      passwordsMismatch: "Die Passwoerter stimmen nicht ueberein.",
      accountCreating: "Konto wird erstellt...",
      accountCreatedCheckEmail: "Konto erstellt. Pruefe deine E-Mail, um dein Konto zu bestaetigen, und logge dich danach ein.",
      clientAlreadyRegistered: "Dieses Mitglied ist bereits registriert. Logge dich mit diesem Konto ein.",
      passwordSetupNeedsSupabase: "Passwort einrichten funktioniert, sobald Supabase in config.js eingerichtet ist.",
      passwordSaving: "Passwort wird gespeichert...",
      passwordChangedLogin: "Passwort geaendert. Du kannst dich jetzt einloggen.",
      passwordChangedLoginAgain: "Passwort geaendert. Logge dich erneut mit deinem neuen Passwort ein.",
      passwordChanged: "Passwort geaendert.",
      passwordChangeFailed: "Passwort aendern fehlgeschlagen: {message}"
    }
  };

  window.FMZ_PHASE1_TRANSLATION_KEYS = {
    languages: PHASE1_LANGUAGES.slice(),
    surfaces: ["onboarding", "account_settings", "goal_engine", "entitlements"],
    keys: Object.keys(PHASE1_I18N.nl)
  };

  function phase1NormalizeLanguage(language) {
    return PHASE1_LANGUAGES.includes(language) ? language : "nl";
  }

  function phase1DefaultCountry(language) {
    const normalized = phase1NormalizeLanguage(language);
    return PHASE1_I18N[normalized]?.defaultCountry || PHASE1_I18N.nl.defaultCountry;
  }

  function phase1AccountSettingsFrom(source = {}, fallback = {}) {
    const language = phase1NormalizeLanguage(source.language || fallback.language || "nl");
    const countryFallback = source.country || fallback.country || phase1DefaultCountry(language);
    return {
      language: "nl",
      country: phase1DefaultCountry(language),
      unitSystem: "metric",
      ...(fallback || {}),
      language,
      country: String(countryFallback).trim() || phase1DefaultCountry(language),
      unitSystem: source.unit_system || source.unitSystem || fallback.unitSystem || "metric"
    };
  }

  function phase1ApplyAccountSettings(source = {}) {
    state.accountSettings = phase1AccountSettingsFrom(source, state.accountSettings || {});
    return state.accountSettings;
  }

  function phase1Settings() {
    return phase1ApplyAccountSettings(state.accountSettings || {});
  }

  function phase1Text(key) {
    const language = phase1Settings().language;
    return PHASE1_I18N[language]?.[key] || PHASE1_I18N.nl[key] || key;
  }

  function phase1Format(key, values = {}) {
    let text = phase1Text(key);
    Object.entries(values).forEach(([name, value]) => {
      text = text.split(`{${name}}`).join(String(value ?? ""));
    });
    return text;
  }

  function phase1DefaultProfileData() {
    return {
      gender: "",
      goalDirection: "",
      trainingExperience: "",
      availableDays: "",
      nutritionPreferences: "",
      practicalConstraints: "",
      onboardingCompletedAt: "",
      bmi: "",
      bmiUpdatedAt: "",
      goalSafetyStatus: "needs_input",
      goalSafetyNote: phase1Text("defaultGoalSafetyNote"),
      goalTimelineWeeks: ""
    };
  }

  const phase1OriginalDefaultClientProfileData = defaultClientProfileData;
  defaultClientProfileData = function defaultClientProfileDataPhase1() {
    return {
      ...phase1OriginalDefaultClientProfileData(),
      ...phase1DefaultProfileData()
    };
  };

  function phase1CalculateBmi(weightKg, heightCm) {
    const weight = number(weightKg);
    const height = number(heightCm);
    if (!weight || !height) return "";
    const meters = height / 100;
    if (meters <= 0) return "";
    return Math.round((weight / (meters * meters)) * 10) / 10;
  }

  function phase1AssessGoal(profile, goalText = "") {
    const currentWeight = number(profile.currentWeight);
    const targetWeight = number(profile.targetWeight);
    const direction = String(profile.goalDirection || "");
    const hasGoal = Boolean(String(goalText || "").trim());

    if (!currentWeight || !direction || !hasGoal) {
      return {
        status: "needs_input",
        note: phase1Text("goalNeedsInputNote"),
        timelineWeeks: ""
      };
    }

    if (["lose_weight", "gain_muscle"].includes(direction) && !targetWeight) {
      return {
        status: "needs_input",
        note: phase1Text("goalNeedsTargetNote"),
        timelineWeeks: ""
      };
    }

    if (!targetWeight || direction === "fitness" || direction === "health" || direction === "other") {
      return {
        status: "realistic_foundation",
        note: phase1Text("goalSavedNoTempoNote"),
        timelineWeeks: ""
      };
    }

    const delta = targetWeight - currentWeight;
    const absDelta = Math.abs(delta);
    const maxReasonableTotalChange = currentWeight * 0.35;
    const safeWeeklyChange = direction === "gain_muscle"
      ? Math.max(0.15, currentWeight * 0.0025)
      : Math.max(0.25, currentWeight * 0.005);
    const timelineWeeks = Math.ceil(absDelta / safeWeeklyChange);

    if (direction === "lose_weight" && delta >= 0) {
      return {
        status: "needs_review",
        note: phase1Text("goalLoseMismatchNote"),
        timelineWeeks: ""
      };
    }

    if (direction === "gain_muscle" && delta <= 0) {
      return {
        status: "needs_review",
        note: phase1Text("goalGainMismatchNote"),
        timelineWeeks: ""
      };
    }

    if (absDelta > maxReasonableTotalChange) {
      return {
        status: "needs_review",
        note: phase1Text("goalNeedsReviewNote"),
        timelineWeeks
      };
    }

    return {
      status: "realistic_foundation",
      note: phase1Format("goalRealisticTimelineNote", { weeks: timelineWeeks }),
      timelineWeeks
    };
  }

  function phase1EntitlementsForClient(selected) {
    const profile = selected?.profile || {};
    const hasPersonalCoaching = Boolean(profile.package && profile.package !== "custom");
    return {
      plan: hasPersonalCoaching ? "personal_coaching" : "free",
      free: true,
      pro: hasPersonalCoaching,
      ai: hasPersonalCoaching,
      personalCoaching: hasPersonalCoaching,
      source: hasPersonalCoaching ? "legacy_trainer_package" : "phase1_default",
      updatedAt: new Date().toISOString()
    };
  }

  function phase1RefreshClient(selected) {
    if (!selected) return selected;
    const previousProfile = selected.profile || {};
    selected.profile = {
      ...defaultClientProfileData(),
      ...previousProfile
    };
    if (!selected.profile.firstName && selected.name) {
      selected.profile.firstName = String(selected.name).split(" ")[0] || "";
    }
    if (!selected.profile.lastName && selected.name && String(selected.name).split(" ").length > 1) {
      selected.profile.lastName = String(selected.name).split(" ").slice(1).join(" ");
    }
    const nextBmi = phase1CalculateBmi(selected.profile.currentWeight, selected.profile.height);
    if (String(nextBmi || "") !== String(previousProfile.bmi || "")) {
      selected.profile.bmiUpdatedAt = nextBmi ? new Date().toISOString() : "";
    }
    selected.profile.bmi = nextBmi;
    const assessment = phase1AssessGoal(selected.profile, selected.goal);
    selected.profile.goalSafetyStatus = assessment.status;
    selected.profile.goalSafetyNote = assessment.note;
    selected.profile.goalTimelineWeeks = assessment.timelineWeeks;

    state.entitlements = state.entitlements && typeof state.entitlements === "object"
      ? state.entitlements
      : { clients: {}, users: {} };
    state.entitlements.clients = state.entitlements.clients && typeof state.entitlements.clients === "object"
      ? state.entitlements.clients
      : {};
    const previousEntitlement = state.entitlements.clients[selected.id] || {};
    const nextEntitlement = phase1EntitlementsForClient(selected);
    const entitlementChanged = previousEntitlement.plan !== nextEntitlement.plan
      || previousEntitlement.pro !== nextEntitlement.pro
      || previousEntitlement.ai !== nextEntitlement.ai
      || previousEntitlement.personalCoaching !== nextEntitlement.personalCoaching;
    nextEntitlement.updatedAt = entitlementChanged
      ? new Date().toISOString()
      : previousEntitlement.updatedAt || nextEntitlement.updatedAt;
    state.entitlements.clients[selected.id] = nextEntitlement;
    return selected;
  }

  function phase1NormalizeState(next) {
    next.accountSettings = phase1AccountSettingsFrom(next.accountSettings || {}, next.accountSettings || {});
    next.entitlements = next.entitlements && typeof next.entitlements === "object"
      ? next.entitlements
      : { clients: {}, users: {} };
    next.entitlements.clients = next.entitlements.clients && typeof next.entitlements.clients === "object"
      ? next.entitlements.clients
      : {};
    next.entitlements.users = next.entitlements.users && typeof next.entitlements.users === "object"
      ? next.entitlements.users
      : {};
    (next.clients || []).forEach((item) => {
      state = next;
      phase1RefreshClient(item);
    });
    return next;
  }

  const phase1OriginalNormalizeState = normalizeState;
  normalizeState = function normalizeStatePhase1(raw) {
    return phase1NormalizeState(phase1OriginalNormalizeState(raw));
  };

  state = phase1NormalizeState(state);

  const phase1OriginalCreateClientProfile = createClientProfile;
  createClientProfile = function createClientProfilePhase1(input) {
    const created = phase1OriginalCreateClientProfile(input);
    return phase1RefreshClient(created);
  };

  function phase1OnboardingComplete(selected) {
    const profile = selected?.profile || {};
    const hasName = Boolean(String(profile.firstName || selected?.name || "").trim());
    const age = number(profile.age);
    const height = number(profile.height);
    const weight = number(profile.currentWeight);
    const hasTargetWhenNeeded = !["lose_weight", "gain_muscle"].includes(profile.goalDirection) || number(profile.targetWeight) > 0;
    return hasName
      && age >= 18
      && height > 0
      && weight > 0
      && PHASE1_GENDERS.includes(profile.gender)
      && PHASE1_GOAL_DIRECTIONS.includes(profile.goalDirection)
      && Boolean(String(selected?.goal || "").trim())
      && hasTargetWhenNeeded;
  }

  function phase1LanguageOptions(active) {
    return PHASE1_LANGUAGES
      .map((language) => `<option value="${language}" ${language === active ? "selected" : ""}>${language.toUpperCase()}</option>`)
      .join("");
  }

  function phase1GenderOptions(active) {
    const labels = {
      female: phase1Text("genderFemale"),
      male: phase1Text("genderMale"),
      non_binary: phase1Text("genderNonBinary"),
      prefer_not_to_say: phase1Text("genderPreferNot"),
      not_relevant: phase1Text("genderNotRelevant")
    };
    return [`<option value="">${escapeHTML(phase1Text("choose"))}</option>`].concat(PHASE1_GENDERS.map((item) => `<option value="${item}" ${item === active ? "selected" : ""}>${escapeHTML(labels[item])}</option>`)).join("");
  }

  function phase1GoalDirectionOptions(active) {
    const labels = {
      lose_weight: phase1Text("goalLoseWeight"),
      gain_muscle: phase1Text("goalGainMuscle"),
      recomposition: phase1Text("goalRecomposition"),
      fitness: phase1Text("goalFitness"),
      health: phase1Text("goalHealth"),
      other: phase1Text("goalOther")
    };
    return [`<option value="">${escapeHTML(phase1Text("choose"))}</option>`].concat(PHASE1_GOAL_DIRECTIONS.map((item) => `<option value="${item}" ${item === active ? "selected" : ""}>${escapeHTML(labels[item])}</option>`)).join("");
  }

  function phase1TrainingExperienceOptions(active) {
    const options = [
      ["", phase1Text("choose")],
      ["beginner", phase1Text("trainingBeginner")],
      ["intermediate", phase1Text("trainingIntermediate")],
      ["advanced", phase1Text("trainingAdvanced")]
    ];
    return options.map(([value, label]) => `<option value="${value}" ${value === active ? "selected" : ""}>${escapeHTML(label)}</option>`).join("");
  }

  function phase1SetText(selector, value) {
    const target = document.querySelector(selector);
    if (target) target.textContent = value;
  }

  function phase1SetPlaceholder(selector, value) {
    const target = document.querySelector(selector);
    if (target) target.placeholder = value;
  }

  function phase1SetFieldLabel(formSelector, fieldName, value) {
    const field = document.querySelector(`${formSelector} [name="${fieldName}"]`);
    const label = field?.closest(".field")?.querySelector("span");
    if (label) label.textContent = value;
  }

  function phase1ApplyAuthCopy(context = passwordSetupContext || "") {
    phase1SetText('.auth-tab[data-auth-mode="login"]', phase1Text("authLoginTab"));
    phase1SetText('.auth-tab[data-auth-mode="register"]', phase1Text("authRegisterTab"));
    phase1SetText("#registerForm h1", phase1Text("authRegisterTab"));
    phase1SetText("#loginForm h1", phase1Text("authLoginTab"));
    phase1SetText("#forgotPasswordForm h1", phase1Text("authForgotLink"));
    phase1SetText("#forgotPasswordForm .auth-note", phase1Text("authForgotIntro"));

    phase1SetFieldLabel("#registerForm", "role", phase1Text("authAccountType"));
    phase1SetFieldLabel("#registerForm", "name", phase1Text("authName"));
    phase1SetFieldLabel("#registerForm", "email", phase1Text("authEmail"));
    phase1SetFieldLabel("#registerForm", "password", phase1Text("authPassword"));
    phase1SetText('#registerForm button[type="submit"]', phase1Text("authRegisterSubmit"));
    phase1SetText("#registerForm .checkbox-row span", phase1Text("authRemember"));
    phase1SetPlaceholder('#registerForm [name="name"]', phase1Text("authNamePlaceholder"));
    phase1SetPlaceholder('#registerForm [name="email"]', phase1Text("authEmailPlaceholder"));
    phase1SetPlaceholder('#registerForm [name="password"]', phase1Text("authNewPasswordPlaceholderShort"));

    phase1SetFieldLabel("#loginForm", "role", phase1Text("authAccountType"));
    phase1SetFieldLabel("#loginForm", "email", phase1Text("authEmail"));
    phase1SetFieldLabel("#loginForm", "password", phase1Text("authPassword"));
    phase1SetText('#loginForm button[type="submit"]', phase1Text("authLoginSubmit"));
    phase1SetText('#loginForm [data-auth-mode="forgot"]', phase1Text("authForgotLink"));
    phase1SetText("#loginForm .checkbox-row span", phase1Text("authRemember"));
    phase1SetPlaceholder('#loginForm [name="email"]', phase1Text("authEmailPlaceholder"));
    phase1SetPlaceholder('#loginForm [name="password"]', phase1Text("authPasswordPlaceholder"));

    phase1SetFieldLabel("#forgotPasswordForm", "email", phase1Text("authEmail"));
    phase1SetText('#forgotPasswordForm button[type="submit"]', phase1Text("authResetSubmit"));
    phase1SetText('#forgotPasswordForm [data-auth-mode="login"]', phase1Text("authBackToLogin"));
    phase1SetPlaceholder('#forgotPasswordForm [name="email"]', phase1Text("authEmailPlaceholder"));

    document.querySelectorAll('option[value="client"]').forEach((option) => {
      option.textContent = phase1Text("authClient");
    });
    document.querySelectorAll('option[value="trainer"]').forEach((option) => {
      option.textContent = phase1Text("authTrainer");
    });

    const isRecovery = context === "recovery";
    phase1SetText("#setPasswordTitle", phase1Text(isRecovery ? "authRecoveryPasswordTitle" : "authInvitePasswordTitle"));
    phase1SetText("#setPasswordIntro", phase1Text(isRecovery ? "authRecoveryPasswordIntro" : "authInvitePasswordIntro"));
    phase1SetFieldLabel("#setPasswordForm", "password", phase1Text("authNewPassword"));
    phase1SetFieldLabel("#setPasswordForm", "passwordConfirm", phase1Text("authConfirmPassword"));
    phase1SetText('#setPasswordForm button[type="submit"]', phase1Text("authSetPasswordSubmit"));
    phase1SetPlaceholder('#setPasswordForm [name="password"]', phase1Text("authNewPasswordPlaceholder"));
    phase1SetPlaceholder('#setPasswordForm [name="passwordConfirm"]', phase1Text("authConfirmPasswordPlaceholder"));
  }

  const phase1OriginalShowAuthPanel = showAuthPanel;
  showAuthPanel = function showAuthPanelPhase1(mode) {
    phase1OriginalShowAuthPanel(mode);
    phase1ApplyAuthCopy();
  };

  const phase1OriginalRequirePasswordSetup = requirePasswordSetup;
  requirePasswordSetup = function requirePasswordSetupPhase1(context = "invite") {
    phase1OriginalRequirePasswordSetup(context);
    phase1ApplyAuthCopy(context);
  };

  function phase1RenderOnboardingPanel(selected) {
    phase1RefreshClient(selected);
    const profile = selected.profile;
    const complete = phase1OnboardingComplete(selected);
    const settings = phase1Settings();
    const statusClass = complete ? "ok" : "";
    const statusLabel = complete ? phase1Text("complete") : phase1Text("incomplete");
    return `
      <section class="phase1-onboarding-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase1Text("accountEyebrow"))}</p>
            <h2>${escapeHTML(phase1Text("onboardingTitle"))}</h2>
            <p class="muted">${escapeHTML(phase1Text("onboardingIntro"))}</p>
          </div>
          <span class="status ${statusClass}">${escapeHTML(statusLabel)}</span>
        </div>
        <form id="phase1OnboardingForm" class="phase1-form-grid">
          <label class="field"><span>${escapeHTML(phase1Text("firstName"))}</span><input name="firstName" required value="${escapeHTML(profile.firstName || "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("lastName"))}</span><input name="lastName" value="${escapeHTML(profile.lastName || "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("age"))}</span><input name="age" type="number" min="18" max="120" required value="${escapeHTML(profile.age ?? "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("gender"))}</span><select name="gender" required>${phase1GenderOptions(profile.gender || "")}</select></label>
          <label class="field"><span>${escapeHTML(phase1Text("heightCm"))}</span><input name="height" type="number" min="100" max="250" step="0.1" required value="${escapeHTML(profile.height ?? "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("currentWeightKg"))}</span><input name="currentWeight" type="number" min="30" max="300" step="0.1" required value="${escapeHTML(profile.currentWeight ?? "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("goalDirection"))}</span><select name="goalDirection" required>${phase1GoalDirectionOptions(profile.goalDirection || "")}</select></label>
          <label class="field"><span>${escapeHTML(phase1Text("targetWeightKg"))}</span><input name="targetWeight" type="number" min="30" max="300" step="0.1" value="${escapeHTML(profile.targetWeight ?? selected.goals?.targetWeight ?? "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("trainingExperience"))}</span><select name="trainingExperience">${phase1TrainingExperienceOptions(profile.trainingExperience || "")}</select></label>
          <label class="field"><span>${escapeHTML(phase1Text("availableDays"))}</span><input name="availableDays" type="number" min="0" max="7" step="1" value="${escapeHTML(profile.availableDays ?? "")}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("language"))}</span><select name="language">${phase1LanguageOptions(settings.language)}</select></label>
          <label class="field phase1-readonly"><span>${escapeHTML(phase1Text("bmi"))}</span><input readonly value="${escapeHTML(profile.bmi || "-")}" /></label>
          <label class="field full"><span>${escapeHTML(phase1Text("fitnessGoal"))}</span><textarea name="goal" rows="3" required>${escapeHTML(selected.goal || "")}</textarea></label>
          <label class="field full"><span>${escapeHTML(phase1Text("nutritionPreferences"))}</span><textarea name="nutritionPreferences" rows="2">${escapeHTML(profile.nutritionPreferences || "")}</textarea></label>
          <label class="field full"><span>${escapeHTML(phase1Text("practicalConstraints"))}</span><textarea name="practicalConstraints" rows="2">${escapeHTML(profile.practicalConstraints || "")}</textarea></label>
          <div class="phase1-goal-note ${profile.goalSafetyStatus === "needs_review" ? "warning" : ""}">
            <strong>${escapeHTML(phase1Text("goalEngine"))}</strong>
            <span>${escapeHTML(profile.goalSafetyNote || "")}</span>
          </div>
          <div class="settings-save-row full">
            <button class="primary-btn" type="submit">${escapeHTML(phase1Text("save"))}</button>
            <span class="save-feedback" data-save-feedback="phase1-onboarding"></span>
          </div>
        </form>
      </section>
    `;
  }

  function phase1InstallStyles() {
    if (document.getElementById("phase1FoundationStyles")) return;
    const style = document.createElement("style");
    style.id = "phase1FoundationStyles";
    style.textContent = `
      .phase1-onboarding-panel,
      .phase1-account-panel {
        background: var(--panel, rgba(255,255,255,.04));
        border: 1px solid var(--border, rgba(148,163,184,.25));
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 18px;
      }
      .phase1-form-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .phase1-form-grid .full,
      .phase1-goal-note,
      .phase1-entitlement-strip {
        grid-column: 1 / -1;
      }
      .phase1-readonly input {
        opacity: .86;
      }
      .phase1-goal-note,
      .phase1-entitlement-strip {
        border: 1px solid rgba(34,197,94,.3);
        border-radius: 8px;
        padding: 12px;
        display: grid;
        gap: 4px;
      }
      .phase1-goal-note.warning {
        border-color: rgba(245,158,11,.45);
      }
      .phase1-entitlement-strip {
        margin-top: 12px;
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }
      .phase1-entitlement-strip span {
        display: grid;
        gap: 3px;
        font-size: .84rem;
      }
      @media (max-width: 720px) {
        .phase1-form-grid,
        .phase1-entitlement-strip {
          grid-template-columns: 1fr;
        }
      }
    `;
    document.head.appendChild(style);
  }

  const phase1OriginalRenderClientHome = renderClientHome;
  renderClientHome = function renderClientHomePhase1() {
    phase1OriginalRenderClientHome();
    const selected = client();
    if (!isLoggedIn() || state.ui.role !== "client" || !hasSelectedClient(selected)) return;
    const target = $("#clientSummary");
    if (!target) return;
    target.insertAdjacentHTML("afterbegin", phase1RenderOnboardingPanel(selected));
  };

  function phase1RenderAccountSettingsPanel() {
    const settings = phase1Settings();
    const selected = state.ui.role === "client" ? client() : null;
    const entitlements = selected ? phase1EntitlementsForClient(selected) : null;
    return `
      <section class="panel settings-card phase1-account-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">${escapeHTML(phase1Text("accountEyebrow"))}</p>
            <h2>${escapeHTML(phase1Text("accountTitle"))}</h2>
          </div>
          <span class="status ok">${escapeHTML(settings.language.toUpperCase())}</span>
        </div>
        <form id="phase1AccountSettingsForm" class="settings-form-grid">
          <label class="field"><span>${escapeHTML(phase1Text("language"))}</span><select name="language">${phase1LanguageOptions(settings.language)}</select></label>
          <label class="field"><span>${escapeHTML(phase1Text("country"))}</span><input name="country" value="${escapeHTML(settings.country || phase1DefaultCountry(settings.language))}" /></label>
          <label class="field"><span>${escapeHTML(phase1Text("units"))}</span><select name="unitSystem"><option value="metric" ${settings.unitSystem === "metric" ? "selected" : ""}>${escapeHTML(phase1Text("metric"))}</option></select></label>
          <div class="settings-save-row full">
            <button class="primary-btn" type="submit">${escapeHTML(phase1Text("saveAccountSettings"))}</button>
            <span class="save-feedback" data-save-feedback="phase1-account-settings"></span>
          </div>
        </form>
        ${entitlements ? `
          <div class="phase1-entitlement-strip">
            <span><strong>Free</strong>${entitlements.free ? phase1Text("entitlementActive") : phase1Text("entitlementInactive")}</span>
            <span><strong>Pro</strong>${entitlements.pro ? phase1Text("entitlementActiveViaCoaching") : phase1Text("entitlementInactive")}</span>
            <span><strong>Youri AI</strong>${entitlements.ai ? phase1Text("entitlementActiveViaCoaching") : phase1Text("entitlementInactive")}</span>
            <span><strong>PT</strong>${entitlements.personalCoaching ? phase1Text("entitlementLinked") : phase1Text("entitlementNotLinked")}</span>
          </div>
        ` : ""}
      </section>
    `;
  }

  const phase1OriginalRenderSettingsPage = renderSettingsPage;
  renderSettingsPage = function renderSettingsPagePhase1() {
    const target = $("#settingsOverview");
    if (!target) return;
    if (isTrainer()) {
      phase1OriginalRenderSettingsPage();
      target.insertAdjacentHTML("afterbegin", phase1RenderAccountSettingsPanel());
      return;
    }
    target.innerHTML = `<div class="settings-layout">${phase1RenderAccountSettingsPanel()}</div>`;
  };

  function phase1UpdateNavigationLabel() {
    const settingsNav = NAV.client.find(([id]) => id === "settings");
    if (settingsNav) settingsNav[1] = phase1Text("settingsNav");
  }

  if (!NAV.client.some(([id]) => id === "settings")) {
    NAV.client.push(["settings", phase1Text("settingsNav")]);
  }
  phase1UpdateNavigationLabel();

  const phase1OriginalRenderNav = renderNav;
  renderNav = function renderNavPhase1() {
    phase1UpdateNavigationLabel();
    phase1OriginalRenderNav();
  };

  const phase1OriginalRenderAll = renderAll;
  renderAll = function renderAllPhase1() {
    phase1InstallStyles();
    state = phase1NormalizeState(state);
    phase1UpdateNavigationLabel();
    phase1OriginalRenderAll();
    phase1ApplyAuthCopy();
  };

  function phase1ApplyFormData(selected, data) {
    selected.profile = {
      ...defaultClientProfileData(),
      ...(selected.profile || {})
    };
    ["firstName", "lastName", "gender", "goalDirection", "trainingExperience", "nutritionPreferences", "practicalConstraints"].forEach((key) => {
      selected.profile[key] = String(data.get(key) || "").trim();
    });
    ["age", "height", "currentWeight", "targetWeight", "availableDays"].forEach((key) => {
      const value = data.get(key);
      selected.profile[key] = value === "" || value === null ? "" : number(value);
    });
    selected.goal = String(data.get("goal") || "").trim();
    selected.goals = selected.goals || { ...DEFAULT_GOALS };
    selected.goals.targetWeight = selected.profile.targetWeight || "";
    const profileName = `${selected.profile.firstName || ""} ${selected.profile.lastName || ""}`.trim();
    if (profileName) selected.name = profileName;
    phase1Settings().language = phase1NormalizeLanguage(data.get("language"));
    phase1RefreshClient(selected);
    if (phase1OnboardingComplete(selected)) {
      selected.profile.onboardingCompletedAt = selected.profile.onboardingCompletedAt || new Date().toISOString();
    }
  }

  function phase1OnboardingPayload(selected) {
    const profile = selected?.profile || {};
    return {
      client_id: selected?.id || "",
      first_name: profile.firstName || "",
      last_name: profile.lastName || "",
      age: profile.age || null,
      height_cm: profile.height || null,
      weight_kg: profile.currentWeight || null,
      gender: profile.gender || null,
      fitness_goal: selected?.goal || "",
      goal_direction: profile.goalDirection || null,
      target_weight_kg: profile.targetWeight || null,
      training_experience: profile.trainingExperience || "",
      available_days: profile.availableDays || null,
      nutrition_preferences: profile.nutritionPreferences || "",
      practical_constraints: profile.practicalConstraints || "",
      bmi: profile.bmi || null,
      goal_safety_status: profile.goalSafetyStatus || "needs_input",
      goal_safety_note: profile.goalSafetyNote || "",
      goal_timeline_weeks: profile.goalTimelineWeeks || null
    };
  }

  async function phase1SyncAccountFoundation(selected) {
    if (!isOnlineMode() || !supabaseClient || !onlineProfile) {
      return { ok: true, skipped: true };
    }
    const role = onlineProfile.role || state.ui.role || "client";
    const { data, error } = await supabaseClient.rpc("fmz_phase1_upsert_account_foundation", {
      p_role: role,
      p_name: selected?.name || state.ui.authName || "",
      p_language: phase1Settings().language,
      p_onboarding: selected ? phase1OnboardingPayload(selected) : {}
    });
    if (error) {
      return {
        ok: false,
        error,
        migrationNeeded: /fmz_phase1_upsert_account_foundation|schema cache|not find|does not exist/i.test(error.message || "")
      };
    }
    if (data?.profile) onlineProfile = data.profile;
    if (data?.settings) phase1ApplyAccountSettings(data.settings);
    return { ok: true, data };
  }

  async function phase1HydrateAccountSettings(profile) {
    if (!isOnlineMode() || !supabaseClient || !profile?.id) return null;
    try {
      const { data, error } = await supabaseClient
        .from("user_settings")
        .select("language,country,unit_system")
        .eq("user_id", profile.id)
        .maybeSingle();
      if (error) throw error;
      if (data) phase1ApplyAccountSettings(data);
      return data;
    } catch (error) {
      console.warn("Phase 1 accountinstellingen laden mislukt", error);
      return null;
    }
  }

  const phase1OriginalEnsureOnlineProfile = ensureOnlineProfile;
  ensureOnlineProfile = async function ensureOnlineProfilePhase1(roleHint = "", nameHint = "") {
    try {
      const profile = await phase1OriginalEnsureOnlineProfile(roleHint, nameHint);
      await phase1HydrateAccountSettings(profile);
      return profile;
    } catch (error) {
      const intendedRole = roleHint || "client";
      if (intendedRole !== "client") throw error;
      const result = await supabaseClient.rpc("fmz_phase1_upsert_account_foundation", {
        p_role: "client",
        p_name: nameHint || "",
        p_language: phase1Settings().language,
        p_onboarding: {}
      });
      if (result.error) {
        const message = /fmz_phase1_upsert_account_foundation|schema cache|not find|does not exist/i.test(result.error.message || "")
          ? phase1Text("migrationNeeded")
          : result.error.message;
        throw new Error(`${message} ${phase1Format("originalError", { message: error.message })}`);
      }
      onlineProfile = result.data?.profile;
      if (result.data?.settings) phase1ApplyAccountSettings(result.data.settings);
      if (!onlineProfile) throw error;
      return onlineProfile;
    }
  };

  const phase1OriginalLoadOnlineWorkspace = loadOnlineWorkspace;
  loadOnlineWorkspace = async function loadOnlineWorkspacePhase1(profile) {
    const remoteSettings = await phase1HydrateAccountSettings(profile);
    if (profile?.role === "client" && !profile.trainer_id) {
      const freeClient = createClientProfile({
        name: profile.name || profile.email || phase1Text("freeUserName"),
        email: profile.email || "",
        password: "",
        registered: true
      });
      freeClient.id = profile.client_id || `free-${profile.id}`;
      const freeState = seedState();
      freeState.clients = [freeClient];
      freeState.trainerAccount = null;
      freeState.ui = {
        ...freeState.ui,
        loggedIn: true,
        role: "client",
        authEmail: profile.email || "",
        authName: profile.name || profile.email || "",
        selectedClientId: freeClient.id,
        theme: state.ui.theme || "dark"
      };
      freeState.accountSettings = phase1AccountSettingsFrom(remoteSettings || state.accountSettings || {}, state.accountSettings || {});
      state = normalizeState(freeState);
      currentView = "client-home";
      onlineProfile = profile;
      onlineReady = true;
      onlineErrorMessage = "";
      renderNav();
      renderAll();
      showView(currentView);
      return;
    }
    await phase1OriginalLoadOnlineWorkspace(profile);
    if (remoteSettings) {
      phase1ApplyAccountSettings(remoteSettings);
      saveState();
      renderNav();
      renderAll();
      showView(currentView);
    }
  };

  const phase1OriginalSaveStateToCloud = saveStateToCloud;
  saveStateToCloud = async function saveStateToCloudPhase1() {
    if (onlineProfile?.role === "client" && !onlineProfile.trainer_id) {
      const result = await phase1SyncAccountFoundation(client());
      if (!result.ok) {
        onlineErrorMessage = phase1Text("saveFailed");
        syncStatus(phase1Text("saveFailed"), "error");
        return { ok: false, error: result.error };
      }
      onlineErrorMessage = "";
      syncStatus(phase1Text("onlineProfileSaved"), "ok");
      return { ok: true };
    }
    return phase1OriginalSaveStateToCloud();
  };

  function phase1ConfigurePublicRegisterRole() {
    const registerRole = document.querySelector('#registerForm select[name="role"]');
    if (!registerRole) return;
    registerRole.value = "client";
    Array.from(registerRole.options).forEach((option) => {
      if (option.value === "trainer") option.remove();
    });
    phase1ApplyAuthCopy();
  }

  function phase1ClearAuthUrl() {
    const url = new URL(window.location.href);
    [
      "access_token",
      "refresh_token",
      "expires_in",
      "expires_at",
      "token_type",
      "type",
      "code"
    ].forEach((key) => url.searchParams.delete(key));
    url.hash = "";
    const query = url.searchParams.toString();
    window.history.replaceState({}, document.title, `${url.pathname}${query ? `?${query}` : ""}`);
  }

  const phase1OriginalFinishPasswordSetup = finishPasswordSetup;
  finishPasswordSetup = function finishPasswordSetupPhase1() {
    passwordSetupRequired = false;
    passwordSetupContext = "";
    phase1ClearAuthUrl();
    renderRoleVisibility();
  };

  async function phase1ReturnRecoveryToLogin(message) {
    try {
      await supabaseClient.auth.signOut({ scope: "local" });
    } catch (error) {
      console.warn("Recovery sessie lokaal afsluiten mislukt", error);
    }
    onlineProfile = null;
    onlineReady = false;
    onlineErrorMessage = "";
    state.ui.loggedIn = false;
    state.ui.authEmail = "";
    state.ui.authName = "";
    passwordSetupRequired = false;
    passwordSetupContext = "";
    phase1ClearAuthUrl();
    renderAll();
    showAuthPanel("login");
    const loginMessage = $("#loginMessage");
    if (loginMessage) {
      loginMessage.className = "login-message ok";
      loginMessage.textContent = phase1Text("passwordChangedLogin");
    }
    if (message && message !== loginMessage) {
      message.className = "login-message";
      message.textContent = "";
    }
  }

  async function phase1CompletePasswordSetup(setupContext, message) {
    const { data: sessionData, error: sessionError } = await supabaseClient.auth.getSession();
    if (sessionError) throw sessionError;

    const { data: userData, error: userError } = await supabaseClient.auth.getUser();
    if (userError && sessionData?.session) throw userError;

    finishPasswordSetup();

    if (setupContext === "recovery") {
      await phase1ReturnRecoveryToLogin(message);
      return;
    }

    if (!sessionData?.session || !userData?.user) {
      onlineProfile = null;
      onlineReady = false;
      onlineErrorMessage = "";
      renderRoleVisibility();
      showAuthPanel("login");
      if (message) {
        message.className = "login-message ok";
        message.textContent = phase1Text("passwordChangedLoginAgain");
      }
      return;
    }

    await hydrateOnlineUser(setupContext === "invite" ? "client" : "");
    renderRoleVisibility();
    renderNav();
    renderAll();
    showView(currentView);
    if (message) {
      message.className = "login-message ok";
      message.textContent = phase1Text("passwordChanged");
    }
  }

  let phase1PasswordSetupCompleting = false;
  if (supabaseClient?.auth?.onAuthStateChange) {
    supabaseClient.auth.onAuthStateChange((event) => {
      if (event === "USER_UPDATED" && phase1PasswordSetupCompleting) {
        passwordSetupRequired = false;
        passwordSetupContext = "";
        phase1ClearAuthUrl();
        renderRoleVisibility();
      }
    });
  }

  phase1ConfigurePublicRegisterRole();

  document.addEventListener("submit", async (event) => {
    if (event.target?.id !== "registerForm") return;
    event.preventDefault();
    event.stopImmediatePropagation();

    const form = event.target;
    const data = new FormData(form);
    const requestedRole = String(data.get("role") || "client");
    const role = "client";
    const name = String(data.get("name") || "").trim();
    const email = cleanEmail(data.get("email"));
    const password = String(data.get("password") || "");
    const remember = form.elements.remember?.checked ?? true;
    const message = $("#registerMessage");
    if (message) message.className = "login-message";

    if (requestedRole !== "client") {
      if (message) {
        message.className = "login-message error";
        message.textContent = phase1Text("trainerRegistrationUnavailable");
      }
      phase1ConfigurePublicRegisterRole();
      return;
    }

    if (password.length < 4) {
      if (message) message.textContent = phase1Text("passwordMin4");
      return;
    }

    setRememberPreference(remember, email, role);
    if (isOnlineMode()) {
      try {
        if (message) message.textContent = phase1Text("accountCreating");
        const { data: authData, error } = await supabaseClient.auth.signUp({
          email,
          password,
          options: {
            data: { role: "client", name, signup_flow: "public_client" },
            emailRedirectTo: APP_AUTH_REDIRECT_URL
          }
        });
        if (error) throw error;
        if (!authData.session) {
          if (message) {
            message.className = "login-message ok";
            message.textContent = phase1Text("accountCreatedCheckEmail");
          }
          form.reset();
          phase1ConfigurePublicRegisterRole();
          updateRememberControls();
          return;
        }
        await hydrateOnlineUser("client", name);
        if (message) message.textContent = "";
        form.reset();
        phase1ConfigurePublicRegisterRole();
        updateRememberControls();
      } catch (error) {
        if (message) {
          message.className = "login-message error";
          message.textContent = error.message;
        }
      }
      return;
    }

    const existingClient = state.clients.find((item) => item.email === email);
    if (existingClient) {
      if (existingClient.registered) {
        if (message) message.textContent = phase1Text("clientAlreadyRegistered");
        return;
      }
      existingClient.password = password;
      existingClient.registered = true;
      loginAs("client", existingClient.email, existingClient.name);
      form.reset();
      phase1ConfigurePublicRegisterRole();
      return;
    }

    const profile = createClientProfile({ name, email, password, registered: true });
    state.clients.push(profile);
    loginAs("client", profile.email, profile.name);
    form.reset();
    phase1ConfigurePublicRegisterRole();
  }, true);

  document.addEventListener("submit", async (event) => {
    if (event.target?.id !== "setPasswordForm") return;
    event.preventDefault();
    event.stopImmediatePropagation();

    const form = event.target;
    const data = new FormData(form);
    const password = String(data.get("password") || "");
    const passwordConfirm = String(data.get("passwordConfirm") || "");
    const message = $("#setPasswordMessage");
    if (message) message.className = "login-message";

    if (!isOnlineMode()) {
      if (message) {
        message.className = "login-message error";
        message.textContent = phase1Text("passwordSetupNeedsSupabase");
      }
      return;
    }
    if (password.length < 6) {
      if (message) {
        message.className = "login-message error";
        message.textContent = phase1Text("passwordMin6");
      }
      return;
    }
    if (password !== passwordConfirm) {
      if (message) {
        message.className = "login-message error";
        message.textContent = phase1Text("passwordsMismatch");
      }
      return;
    }

    phase1PasswordSetupCompleting = true;
    try {
      if (message) message.textContent = phase1Text("passwordSaving");
      const setupContext = passwordSetupContext;
      const { error } = await supabaseClient.auth.updateUser({ password });
      if (error) throw error;
      form.reset();
      await phase1CompletePasswordSetup(setupContext, message);
    } catch (error) {
      if (message) {
        message.className = "login-message error";
        message.textContent = phase1Format("passwordChangeFailed", { message: error.message });
      }
      passwordSetupRequired = true;
      renderRoleVisibility();
    } finally {
      phase1PasswordSetupCompleting = false;
    }
  }, true);

  document.addEventListener("submit", async (event) => {
    if (event.target?.id === "phase1OnboardingForm") {
      event.preventDefault();
      const selected = client();
      if (!hasSelectedClient(selected)) return;
      const feedbackKey = "phase1-onboarding";
      const data = new FormData(event.target);
      const age = number(data.get("age"));
      if (age < 18) {
        setSaveFeedback(feedbackKey, phase1Text("ageCheck"), true);
        return;
      }
      phase1ApplyFormData(selected, data);
      const syncResult = await phase1SyncAccountFoundation(selected);
      const ok = await persistActionFeedback(feedbackKey, phase1Text("saved"));
      if (!syncResult.ok) {
        setSaveFeedback(
          feedbackKey,
          syncResult.migrationNeeded ? phase1Text("migrationNeeded") : phase1Format("onlineProfileSaveFailed", { message: syncResult.error.message }),
          true
        );
        return;
      }
      if (!ok) return;
      setSaveFeedback(feedbackKey, phase1Text("saved"));
      return;
    }

    if (event.target?.id === "phase1AccountSettingsForm") {
      event.preventDefault();
      const data = new FormData(event.target);
      const settings = phase1Settings();
      settings.language = phase1NormalizeLanguage(data.get("language"));
      settings.country = String(data.get("country") || phase1DefaultCountry(settings.language)).trim() || phase1DefaultCountry(settings.language);
      settings.unitSystem = "metric";
      const syncResult = await phase1SyncAccountFoundation(client());
      if (!syncResult.ok) {
        renderAll();
        setSaveFeedback(
          "phase1-account-settings",
          syncResult.migrationNeeded ? phase1Text("migrationNeeded") : phase1Format("onlineSettingsSaveFailed", { message: syncResult.error.message }),
          true
        );
        return;
      }
      saveState();
      renderAll();
      setSaveFeedback("phase1-account-settings", phase1Text("accountSettingsSaved"));
    }
  });

  document.addEventListener("change", (event) => {
    if (!event.target?.matches('#phase1AccountSettingsForm select[name="language"]')) return;
    phase1Settings().language = phase1NormalizeLanguage(event.target.value);
    phase1UpdateNavigationLabel();
    renderNav();
    renderSettingsPage();
    phase1ApplyAuthCopy();
  });

  document.addEventListener("input", (event) => {
    if (!event.target.closest("#phase1OnboardingForm")) return;
    const selected = client();
    if (!hasSelectedClient(selected)) return;
    const data = new FormData(event.target.form);
    const preview = {
      ...selected,
      profile: {
        ...selected.profile,
        currentWeight: data.get("currentWeight"),
        height: data.get("height"),
        targetWeight: data.get("targetWeight"),
        goalDirection: data.get("goalDirection")
      },
      goal: data.get("goal")
    };
    const bmiInput = event.target.form.querySelector(".phase1-readonly input");
    if (bmiInput) bmiInput.value = phase1CalculateBmi(preview.profile.currentWeight, preview.profile.height) || "-";
  });
})();
