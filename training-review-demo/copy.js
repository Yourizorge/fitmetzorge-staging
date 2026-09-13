/* Public concept copy; NL/EN/DE, not expert-approved. */
(function(root){ "use strict"; const rows={
  "short_versions": ["Versieconflict","Version conflict","Versionskonflikt"],
  "short_expired": ["Bron verlopen","Source expired","Quelle abgelaufen"],
  "short_consent": ["Toestemming ingetrokken","Consent withdrawn","Einwilligung widerrufen"],
  "short_relation": ["Trainerkoppeling ingetrokken","Trainer link revoked","Trainerlink widerrufen"],
  "short_incomplete": ["Onvolledige gegevens","Incomplete data","Unvollständige Daten"],
  "short_unavailable": ["Voorwaarden niet vervuld","Conditions not met","Bedingungen nicht erfüllt"],
  "short_no_trainer": ["Geen trainer gekoppeld","No linked trainer","Kein Trainer verknüpft"],
  "short_ambiguous": ["Meerdere passende regels","Multiple matching rules","Mehrere passende Regeln"],
  "title": [
    "Trainingsvoorstel",
    "Training proposal",
    "Trainingsvorschlag"
  ],
  "demo": [
    "Synthetische offline demo",
    "Synthetic offline demo",
    "Synthetische Offline-Demo"
  ],
  "resetNote": [
    "Alle gegevens zijn fictief. Alleen tijdelijk geheugen; verversen wist deze demo. Geen koppeling met de echte app.",
    "All data is fictional. Memory only; refreshing resets this demo. Not connected to the real app.",
    "Alle Daten sind fiktiv. Nur im Arbeitsspeicher; Neuladen setzt die Demo zurück. Keine Verbindung zur echten App."
  ],
  "scenario": [
    "Situatie",
    "Scenario",
    "Szenario"
  ],
  "language": [
    "Taal",
    "Language",
    "Sprache"
  ],
  "theme": [
    "Thema",
    "Theme",
    "Design"
  ],
  "light": [
    "Licht",
    "Light",
    "Hell"
  ],
  "dark": [
    "Donker",
    "Dark",
    "Dunkel"
  ],
  "reset": [
    "Demo resetten",
    "Reset demo",
    "Demo zurücksetzen"
  ],
  "member": [
    "Lid",
    "Member",
    "Mitglied"
  ],
  "trainer": [
    "Trainer",
    "Trainer",
    "Trainer"
  ],
  "system": [
    "Systeem",
    "System",
    "System"
  ],
  "persona": [
    "Gesimuleerde rol",
    "Simulated role",
    "Simulierte Rolle"
  ],
  "fiction": [
    "Fictief lid Sam / fictieve trainer Robin",
    "Fictional member Sam / fictional trainer Robin",
    "Fiktives Mitglied Sam / fiktiver Trainer Robin"
  ],
  "member_pending": [
    "Wacht op lid",
    "Awaiting member",
    "Wartet auf Mitglied"
  ],
  "trainer_pending": [
    "Wacht op trainer",
    "Awaiting trainer",
    "Wartet auf Trainer"
  ],
  "approved": [
    "Wacht op toepassing",
    "Awaiting application",
    "Wartet auf Anwendung"
  ],
  "applied": [
    "Toegepast in demo",
    "Applied in demo",
    "In der Demo angewendet"
  ],
  "rejected": [
    "Afgewezen",
    "Rejected",
    "Abgelehnt"
  ],
  "blocked": [
    "Geblokkeerd",
    "Blocked",
    "Blockiert"
  ],
  "maintained": [
    "Doel behouden",
    "Target retained",
    "Ziel beibehalten"
  ],
  "pending": [
    "Nog niet bevestigd",
    "Not confirmed",
    "Noch nicht bestätigt"
  ],
  "accepted": [
    "Bevestigd",
    "Accepted",
    "Bestätigt"
  ],
  "invalidated": [
    "Ongeldig geworden",
    "Invalidated",
    "Ungültig geworden"
  ],
  "not_applied": [
    "Niet toegepast",
    "Not applied",
    "Nicht angewendet"
  ],
  "plan": [
    "Huidig schema",
    "Current plan",
    "Aktueller Plan"
  ],
  "proposed": [
    "Voorgesteld schema",
    "Proposed plan",
    "Vorgeschlagener Plan"
  ],
  "oldPlan": [
    "Schema bij voorstel",
    "Plan when proposed",
    "Plan beim Vorschlag"
  ],
  "version": [
    "Versie",
    "Version",
    "Version"
  ],
  "accept": [
    "Voorstel accepteren",
    "Accept proposal",
    "Vorschlag akzeptieren"
  ],
  "reject": [
    "Afwijzen",
    "Reject",
    "Ablehnen"
  ],
  "approve": [
    "Goedkeuren",
    "Approve",
    "Genehmigen"
  ],
  "block": [
    "Blokkeren",
    "Blockieren",
    "Blockieren"
  ],
  "apply": [
    "Wijziging toepassen",
    "Apply change",
    "Änderung anwenden"
  ],
  "restore": [
    "Terugzetvoorstel maken",
    "Propose restore",
    "Wiederherstellung vorschlagen"
  ],
  "history": [
    "Bewaarde schemaversies",
    "Saved plan versions",
    "Gespeicherte Planversionen"
  ],
  "restoreTarget": [
    "Eerdere versie",
    "Earlier version",
    "Frühere Version"
  ],
  "inbox": [
    "Gesimuleerde meldingen",
    "Simulated notifications",
    "Simulierte Mitteilungen"
  ],
  "audit": [
    "Auditgeschiedenis",
    "Audit history",
    "Auditverlauf"
  ],
  "sources": [
    "Bronversies en trainergrenzen",
    "Source versions and trainer limits",
    "Quellversionen und Trainergrenzen"
  ],
  "empty": [
    "Nog geen meldingen",
    "No notifications yet",
    "Noch keine Mitteilungen"
  ],
  "exercise": [
    "Oefening",
    "Exercise",
    "Übung"
  ],
  "set": [
    "Set",
    "Set",
    "Satz"
  ],
  "weight": [
    "Gewicht",
    "Weight",
    "Gewicht"
  ],
  "reps": [
    "Reps",
    "Reps",
    "Wdh."
  ],
  "actual": [
    "Werkelijk geregistreerd",
    "Actually recorded",
    "Tatsächlich aufgezeichnet"
  ],
  "reason": [
    "Reden",
    "Reason",
    "Grund"
  ],
  "next": [
    "Volgende week",
    "Next week",
    "Nächste Woche"
  ],
  "facts": [
    "Beschikbare feiten",
    "Available facts",
    "Verfügbare Fakten"
  ],
  "noAdvice": [
    "Geen medische vrijgave. RIR en RPE zijn afzonderlijke zelfrapportages. Geen automatische acties.",
    "No medical clearance. RIR and RPE are separate self-reports. No automatic actions.",
    "Keine medizinische Freigabe. RIR und RPE sind getrennte Selbstauskünfte. Keine automatischen Aktionen."
  ],
  "review": [
    "Voorstel",
    "Proposal",
    "Vorschlag"
  ],
  "approval": [
    "Trainerakkoord",
    "Trainer approval",
    "Trainergenehmigung"
  ],
  "application": [
    "Toepassing",
    "Application",
    "Anwendung"
  ],
  "event": [
    "Gebeurtenis",
    "Event",
    "Ereignis"
  ],
  "date": [
    "Fictief tijdstip",
    "Simulated time",
    "Fiktiver Zeitpunkt"
  ],
  "state": [
    "Status",
    "Status",
    "Status"
  ],
  "simulate": [
    "Brongebeurtenis simuleren",
    "Simulate source event",
    "Quellereignis simulieren"
  ],
  "trigger": [
    "Simuleren",
    "Simulate",
    "Simulieren"
  ],
  "noChange": [
    "Geen schemawijziging voorgesteld.",
    "No plan change proposed.",
    "Keine Planänderung vorgeschlagen."
  ],
  "restoreWarning": [
    "Dit is een nieuw voorstel. Lid en trainer moeten opnieuw afzonderlijk akkoord geven.",
    "This is a new proposal. Member and trainer must each approve again.",
    "Dies ist ein neuer Vorschlag. Mitglied und Trainer müssen erneut getrennt zustimmen."
  ],
  "new_member": [
    "Youri heeft een voorstel voor je volgende training.",
    "Youri has a proposal for your next workout.",
    "Youri hat einen Vorschlag für dein nächstes Training."
  ],
  "new_trainer": [
    "Er wacht een trainingsvoorstel op jouw beoordeling.",
    "A training proposal is waiting for your review.",
    "Ein Trainingsvorschlag wartet auf deine Prüfung."
  ],
  "approved_notice": [
    "Het voorstel is goedgekeurd en wacht op toepassing.",
    "The proposal is approved and awaiting application.",
    "Der Vorschlag ist genehmigt und wartet auf die Anwendung."
  ],
  "applied_notice": [
    "Je trainingsschema heeft een nieuwe versie.",
    "Your training plan has a new version.",
    "Dein Trainingsplan hat eine neue Version."
  ],
  "restore_notice": [
    "Er is een voorstel gemaakt om een eerdere schemaversie te herstellen.",
    "A proposal was created to restore an earlier plan version.",
    "Ein Vorschlag zur Wiederherstellung einer früheren Planversion wurde erstellt."
  ],
  "rejected_notice": [
    "Het voorstel is afgewezen.",
    "The proposal was rejected.",
    "Der Vorschlag wurde abgelehnt."
  ],
  "blocked_notice": [
    "Het voorstel is geblokkeerd.",
    "The proposal was blocked.",
    "Der Vorschlag wurde blockiert."
  ],
  "member_declined": [
    "Het lid heeft niet ingestemd.",
    "The member did not agree.",
    "Das Mitglied hat nicht zugestimmt."
  ],
  "trainer_declined": [
    "De trainer heeft niet ingestemd.",
    "The trainer did not agree.",
    "Der Trainer hat nicht zugestimmt."
  ],
  "trainer_blocked": [
    "De trainer heeft het voorstel geblokkeerd.",
    "The trainer blocked the proposal.",
    "Der Trainer hat den Vorschlag blockiert."
  ],
  "version_conflict": [
    "De bronversies komen niet meer overeen.",
    "The source versions no longer match.",
    "Die Quellversionen stimmen nicht mehr überein."
  ],
  "expired": [
    "De geldigheid van de bron is verlopen.",
    "The source validity has expired.",
    "Die Gültigkeit der Quelle ist abgelaufen."
  ],
  "no_trainer": [
    "Er is geen gekoppelde trainer; een wijziging is niet toepasbaar.",
    "There is no linked trainer; a change cannot be applied.",
    "Es ist kein Trainer verknüpft; eine Änderung ist nicht anwendbar."
  ],
  "relation_revoked": [
    "De trainerkoppeling is ingetrokken.",
    "The trainer relationship was revoked.",
    "Die Trainerverknüpfung wurde widerrufen."
  ],
  "consent_revoked": [
    "De vereiste toestemming ontbreekt of is ingetrokken.",
    "Required consent is missing or withdrawn.",
    "Die erforderliche Einwilligung fehlt oder wurde widerrufen."
  ],
  "incomplete": [
    "De gekoppelde gegevens zijn onvolledig.",
    "The linked data is incomplete.",
    "Die verknüpften Daten sind unvollständig."
  ],
  "unavailable": [
    "Het voorstel is niet beschikbaar binnen de huidige voorwaarden.",
    "The proposal is unavailable under the current conditions.",
    "Der Vorschlag ist unter den aktuellen Bedingungen nicht verfügbar."
  ],
  "ambiguous_rules": [
    "Meerdere trainerregels passen; er is geen expliciete voorrang.",
    "Multiple trainer rules match; no explicit priority exists.",
    "Mehrere Trainerregeln passen; eine ausdrückliche Priorität fehlt."
  ],
  "weight_step_conflict": [
    "De beschikbare gewichten passen niet exact bij de volledige ingestelde stap. Geen afronding of alternatief voorstel.",
    "Available weights do not fit the full configured step exactly. No rounding or alternative proposal.",
    "Die verfügbaren Gewichte passen nicht genau zur vollständig festgelegten Stufe. Keine Rundung und kein Alternativvorschlag."
  ],
  "step": [
    "Ingestelde gewichtsstap",
    "Configured weight step",
    "Festgelegte Gewichtsstufe"
  ],
  "weights": [
    "Vastgelegde gewichten",
    "Recorded weights",
    "Festgelegte Gewichte"
  ],
  "increase_reps": [
    "Herhalingen verhogen",
    "Increase repetitions",
    "Wiederholungen erhöhen"
  ],
  "increase_weight": [
    "Gewicht verhogen",
    "Increase weight",
    "Gewicht erhöhen"
  ],
  "maintain": [
    "Doel behouden",
    "Keep target",
    "Ziel beibehalten"
  ],
  "all_required_targets_met_below_ceiling": [
    "De geregistreerde sets halen het doel. De trainerregel staat één rep erbij toe, onder het vastgelegde maximum.",
    "The recorded sets meet the target. The trainer rule allows one more rep, below its maximum.",
    "Die aufgezeichneten Sätze erreichen das Ziel. Die Trainerregel erlaubt eine weitere Wiederholung unter dem Maximum."
  ],
  "all_required_targets_met_at_ceiling": [
    "De sets halen het repmaximum. De trainerregel noemt de volledige gewichtsstap en het bijbehorende repdoel.",
    "The sets meet the rep ceiling. The trainer rule defines the full weight step and corresponding rep target.",
    "Die Sätze erreichen das Wiederholungsmaximum. Die Trainerregel nennt die vollständige Gewichtsstufe und das zugehörige Wiederholungsziel."
  ],
  "target_or_effort_not_met": [
    "De vastgelegde regel geeft geen verhoging; behoud het bestaande doel als voorstel.",
    "The recorded rule does not permit an increase; the proposal retains the target.",
    "Die dokumentierte Regel erlaubt keine Erhöhung; der Vorschlag behält das Ziel bei."
  ],
  "normal": [
    "Reps + gewicht + behouden",
    "Reps + weight + maintain",
    "Wdh. + Gewicht + Beibehalten"
  ],
  "lb": [
    "Zelfde regels in lb",
    "Same rules in lb",
    "Gleiche Regeln in lb"
  ],
  "all_maintain": [
    "Alle doelen behouden",
    "Retain all targets",
    "Alle Ziele beibehalten"
  ],
  "step_off_grid": [
    "W2: gewichtsstap past niet",
    "W2: incompatible weight step",
    "W2: unpassende Gewichtsstufe"
  ],
  "missing_set": [
    "Onvolledige setregistratie",
    "Incomplete set log",
    "Unvollständige Satzaufzeichnung"
  ],
  "no_analysis_consent": [
    "Toestemming ontbreekt",
    "Consent missing",
    "Einwilligung fehlt"
  ],
  "book_expired": [
    "Verlopen trainerbron",
    "Expired trainer source",
    "Abgelaufene Trainerquelle"
  ],
  "stale_request": [
    "Versieconflict",
    "Version conflict",
    "Versionskonflikt"
  ],
  "current": [
    "Actuele melding (synthetisch)",
    "Current report (synthetic)",
    "Aktuelle Meldung (synthetisch)"
  ],
  "self_reported": [
    "Zelf gemeld herstel",
    "Self-reported recovery",
    "Selbstberichtete Erholung"
  ],
  "missing": [
    "Ontbrekende context",
    "Missing context",
    "Fehlender Kontext"
  ],
  "rir_zero": [
    "RIR nul geregistreerd",
    "RIR zero recorded",
    "RIR null aufgezeichnet"
  ],
  "optional_effort_missing": [
    "RIR/RPE niet ingevuld",
    "RIR/RPE not recorded",
    "RIR/RPE nicht erfasst"
  ],
  "created": [
    "Voorstel aangemaakt",
    "Proposal created",
    "Vorschlag erstellt"
  ],
  "restore_created": [
    "Terugzetvoorstel aangemaakt",
    "Restore proposal created",
    "Wiederherstellungsvorschlag erstellt"
  ],
  "member_accept": [
    "Lidacceptatie",
    "Member acceptance",
    "Mitgliedszustimmung"
  ],
  "member_reject": [
    "Lidafwijzing",
    "Member rejection",
    "Ablehnung durch Mitglied"
  ],
  "trainer_approve": [
    "Trainergoedkeuring",
    "Trainer approval",
    "Trainergenehmigung"
  ],
  "trainer_reject": [
    "Trainerafwijzing",
    "Trainer rejection",
    "Trainerablehnung"
  ],
  "trainer_block": [
    "Trainerblokkade",
    "Trainer block",
    "Trainersperre"
  ],
  "source_event": [
    "Bron gewijzigd",
    "Source changed",
    "Quelle geändert"
  ],
  "create": [
    "Aangemaakt",
    "Created",
    "Erstellt"
  ],
  "restored": [
    "Nieuwe herstelversie toegepast",
    "New restore version applied",
    "Neue Wiederherstellungsversion angewendet"
  ],
  "error": [
    "Deze handeling is niet toegestaan in de huidige status.",
    "This action is not allowed in the current state.",
    "Diese Aktion ist im aktuellen Status nicht zulässig."
  ],
  "success": [
    "Handeling geregistreerd in de demo.",
    "Action recorded in the demo.",
    "Aktion in der Demo aufgezeichnet."
  ],
  "kept": [
    "Ongewijzigd",
    "Unchanged",
    "Unverändert"
  ],
  "changed": [
    "Gewijzigd",
    "Changed",
    "Geändert"
  ],
  "chat": [
    "Chat en eerdere resultaten",
    "Chat and earlier results",
    "Chat und frühere Ergebnisse"
  ],
  "chatNote": [
    "Bestaande toegang blijft afzonderlijk beoordeeld. Deze demo heeft geen echte chat of ledenresultaten.",
    "Existing access remains separately assessed. This demo has no real chat or member results.",
    "Bestehender Zugang wird getrennt beurteilt. Diese Demo enthält keinen echten Chat und keine Mitgliederergebnisse."
  ],
  "retention": [
    "O5: extra veiligheidsregistratie vervalt uiterlijk 30 dagen na eerste registratie. Tijdsverloop geeft geen medische vrijgave.",
    "O5: additional safety records expire within 30 days of first recording. Elapsed time is not medical clearance.",
    "O5: Zusätzliche Sicherheitsaufzeichnungen verfallen spätestens 30 Tage nach Ersterfassung. Zeitablauf ist keine medizinische Freigabe."
  ]
}; const copy=Object.fromEntries(["nl","en","de"].map((l,i)=>[l,Object.fromEntries(Object.entries(rows).map(([k,v])=>[k,v[i]]))])); if(typeof module==="object"&&module.exports)module.exports=copy;else root.FMZDemoCopy=copy;})(globalThis);
