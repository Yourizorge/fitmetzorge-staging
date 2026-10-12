(function(root){'use strict';const old=typeof module==='object'?require('../daily-coach-demo/copy.js'):root.FMZ20Copy;
const text={
 "actualShort":["Logboek","Log","Erfasst"],
 "goalShort":["Doel","Target","Ziel"],
 "differenceShort":["Verschil","Delta","Differenz"],
 "setsReps":["sets met herhalingen","sets with repetitions","Saetze mit Wiederholungen"],
 "setsLoad":["sets met gewicht","sets with weight","Saetze mit Gewicht"],
 "partialDay":["Afgerond met ontbrekende producten","Finished with missing products","Mit fehlenden Produkten abgeschlossen"],
 "title": [
  "Vandaag: je volledige planlogboek",
  "Today: your full plan log",
  "Heute: dein vollstaendiges Planprotokoll"
 ],
 "demo": [
  "Alex is fictief. Alle invoer betreft synthetische testgegevens. Alleen geheugen: verversen reset alles. Geen echte AI-chat, duurzame opslag of achtergrondmeldingen.",
  "Alex is fictional. All input concerns synthetic test data. Memory only: refreshing resets everything. No real AI chat, durable storage or background notifications.",
  "Alex ist fiktiv. Alle Eingaben betreffen synthetische Testdaten. Nur im Speicher: Neuladen setzt alles zurueck. Kein echter KI-Chat, dauerhafter Speicher oder Hintergrundmeldungen."
 ],
 "records": [
  "Workout registreren",
  "Record a workout",
  "Workout erfassen"
 ],
 "chooseWorkout": [
  "Workout uit het plan",
  "Workout from the plan",
  "Workout aus dem Plan"
 ],
 "set": [
  "Set",
  "Set",
  "Satz"
 ],
 "load": [
  "Gewicht",
  "Weight",
  "Gewicht"
 ],
 "reps": [
  "Herhalingen",
  "Repetitions",
  "Wiederholungen"
 ],
 "saveSet": [
  "Set opslaan",
  "Save set",
  "Satz speichern"
 ],
 "finish": [
  "Workout afronden",
  "Finish workout",
  "Workout abschliessen"
 ],
 "open": [
  "Nog niet afgerond",
  "Not finished",
  "Noch nicht abgeschlossen"
 ],
 "closed": [
  "Expliciet afgerond",
  "Explicitly finished",
  "Explizit abgeschlossen"
 ],
 "partialFinish": [
  "Afgerond met ontbrekende setgegevens",
  "Finished with missing set data",
  "Mit fehlenden Satzdaten abgeschlossen"
 ],
 "summary": [
  "Reflectie op de oorspronkelijke snapshot",
  "Reflection on the original snapshot",
  "Reflexion zur urspruenglichen Momentaufnahme"
 ],
 "reflectionLimit": [
  "Dit vergelijkt alleen je registratie met het oorspronkelijke plan. Geen oordeel over trainingsgeschiktheid of nieuwe progressiestap. Zonder passende regel geen wijzigingsvoorstel.",
  "This only compares your record with the original plan. No assessment of fitness to train or new progression step. No change proposal without a matching rule.",
  "Dies vergleicht nur deinen Eintrag mit dem urspruenglichen Plan. Keine Aussage zur Trainingsfaehigkeit oder neue Progressionsstufe. Ohne passende Regel kein Aenderungsvorschlag."
 ],
 "noSummary": [
  "Rond de workout expliciet af voor een samenvatting. De ingevulde sets blijven bewaard.",
  "Finish the workout explicitly for a summary. Entered sets remain saved.",
  "Workout fuer eine Zusammenfassung explizit abschliessen. Erfasste Saetze bleiben erhalten."
 ],
 "missingLoad": [
  "Geen vergelijkbaar gewicht",
  "No comparable weight",
  "Kein vergleichbares Gewicht"
 ],
 "self": [
  "RIR en RPE zijn afzonderlijke, optionele zelfrapportages. Leeg is niet nul.",
  "RIR and RPE are separate optional self-reports. Empty is not zero.",
  "RIR und RPE sind getrennte optionale Selbstauskuenfte. Leer ist nicht null."
 ],
 "foodLog": [
  "Maaltijden registreren",
  "Record meals",
  "Mahlzeiten erfassen"
 ],
 "chooseMeal": [
  "Maaltijd uit het plan",
  "Meal from the plan",
  "Mahlzeit aus dem Plan"
 ],
 "product": [
  "Product",
  "Product",
  "Produkt"
 ],
 "foodState": [
  "Registratiestatus",
  "Record status",
  "Erfassungsstatus"
 ],
 "eaten": [
  "Gegeten",
  "Eaten",
  "Gegessen"
 ],
 "not_eaten": [
  "Niet gegeten",
  "Not eaten",
  "Nicht gegessen"
 ],
 "saveFood": [
  "Product opslaan",
  "Save product",
  "Produkt speichern"
 ],
 "finishDay": [
  "Planlogboek afronden",
  "Finish plan log",
  "Planprotokoll abschliessen"
 ],
 "foodSummary": [
  "Geregistreerd subtotaal en bestaand doel",
  "Recorded subtotal and existing target",
  "Erfasste Zwischensumme und bestehendes Ziel"
 ],
 "goal": [
  "Bestaand doel",
  "Existing target",
  "Bestehendes Ziel"
 ],
 "difference": [
  "Verschil met doel",
  "Difference from target",
  "Differenz zum Ziel"
 ],
 "scope": [
  "Alleen de geplande producten tellen mee. Ook 12/12 registraties bewijzen niet je volledige daginname. Geen calorie- of macroaanpassing.",
  "Only planned products count. Even 12/12 records do not prove your full daily intake. No calorie or macro adjustment.",
  "Nur geplante Produkte zaehlen. Auch 12/12 Eintraege belegen nicht die gesamte Tagesaufnahme. Keine Kalorien- oder Makroanpassung."
 ],
 "full": [
  "Beide workouts: 6/6 sets geregistreerd en elk afzonderlijk afgerond. Alle oorspronkelijke snapshots blijven behouden.",
  "Both workouts: 6/6 sets recorded and each finished separately. All original snapshots retained.",
  "Beide Workouts: 6/6 Saetze erfasst und jeweils separat abgeschlossen. Alle urspruenglichen Momentaufnahmen erhalten."
 ],
 "partial": [
  "Slechts 1/3 sets heeft herhalingen. Expliciet afgerond, maar zichtbaar onvolledig; geen volledige prestatieconclusie.",
  "Only 1/3 sets has repetitions. Explicitly finished but visibly incomplete; no complete performance conclusion.",
  "Nur 1/3 Saetze hat Wiederholungen. Explizit abgeschlossen, aber sichtbar unvollstaendig; keine vollstaendige Leistungsbewertung."
 ],
 "zero": [
  "Gewicht 0, herhalingen 0 en RIR 0 blijven echte nulwaarden. RPE 7,5 staat apart. Opslaan rondt geen workout af.",
  "Weight 0, repetitions 0 and RIR 0 remain real zero values. RPE 7.5 stays separate. Saving does not finish a workout.",
  "Gewicht 0, Wiederholungen 0 und RIR 0 bleiben echte Nullwerte. RPE 7,5 bleibt getrennt. Speichern schliesst kein Workout ab."
 ],
 "food": [
  "3 maaltijden / 12 producten: 1725 kcal geregistreerd tegenover bestaand doel 1800 kcal. Verschil -75 kcal is alleen rekenkundig, geen eetadvies.",
  "3 meals / 12 products: 1725 kcal recorded versus existing target 1800 kcal. Difference -75 kcal is arithmetic only, not dietary advice.",
  "3 Mahlzeiten / 12 Produkte: 1725 kcal erfasst gegenueber bestehendem Ziel 1800 kcal. Differenz -75 kcal ist nur rechnerisch, keine Ernaehrungsempfehlung."
 ],
 "missing_food": [
  "Alleen de eerste maaltijd is vastgelegd: 4/12 producten, 575 kcal. De andere maaltijden zijn ontbrekend, niet nul.",
  "Only the first meal is recorded: 4/12 products, 575 kcal. Other meals are missing, not zero.",
  "Nur die erste Mahlzeit ist erfasst: 4/12 Produkte, 575 kcal. Andere Mahlzeiten fehlen, sie sind nicht null."
 ],
 "uneaten": [
  "Rijst is expliciet niet gegeten: 0 g en 0 kcal. De andere 11 producten blijven ontbrekend.",
  "Rice explicitly not eaten: 0 g and 0 kcal. The other 11 products remain missing.",
  "Reis explizit nicht gegessen: 0 g und 0 kcal. Die anderen 11 Produkte fehlen weiterhin."
 ],
 "portion": [
  "Deze portie valt buiten de bestaande productgrenzen of stapgrootte. Niets opgeslagen; geen afronding of vervangend product.",
  "This portion is outside existing product limits or step size. Nothing saved; no rounding or substitute product.",
  "Diese Portion liegt ausserhalb bestehender Produktgrenzen oder Schrittweite. Nichts gespeichert; keine Rundung oder Ersatzprodukt."
 ],
 "unit": [
  "De invoereenheid past niet bij de snapshot. Niets opgeslagen; kg en lb worden nooit stilzwijgend omgerekend.",
  "The input unit does not match the snapshot. Nothing saved; kg and lb are never silently converted.",
  "Die Eingabeeinheit passt nicht zur Momentaufnahme. Nichts gespeichert; kg und lb werden nie stillschweigend umgerechnet."
 ],
 "record_source": [
  "De product- of setbron klopt niet exact. Niets opgeslagen en geen ontbrekende bron gereconstrueerd.",
  "The product or set source does not match exactly. Nothing saved and no missing source reconstructed.",
  "Die Produkt- oder Satzquelle stimmt nicht exakt ueberein. Nichts gespeichert und keine fehlende Quelle rekonstruiert."
 ],
 "duplicate": [
  "Herhaald opslaan of afronden maakt geen tweede registratie, melding of afronding.",
  "Repeated saving or finishing creates no second record, notice or completion.",
  "Wiederholtes Speichern oder Abschliessen erzeugt keinen zweiten Eintrag, Hinweis oder Abschluss."
 ],
 "correct": [
  "Een nieuwe setregistratie trekt eerdere goedkeuringen in. Het actuele voorstel moet opnieuw worden beoordeeld.",
  "A new set record withdraws previous approvals. The current proposal must be reviewed again.",
  "Ein neuer Satzeintrag hebt fruehere Freigaben auf. Der aktuelle Vorschlag muss erneut geprueft werden."
 ],
 "reopen": [
  "De set is gecorrigeerd van 10 naar 9 herhalingen. De oude samenvatting blijft bewaard; deze workout moet opnieuw expliciet worden afgerond.",
  "The set was corrected from 10 to 9 repetitions. The old summary is retained; this workout must be explicitly finished again.",
  "Der Satz wurde von 10 auf 9 Wiederholungen korrigiert. Die alte Zusammenfassung bleibt erhalten; dieses Workout muss erneut explizit abgeschlossen werden."
 ],
 "trainerFlow": [
  "Route A: lidacceptatie, trainergoedkeuring en afzonderlijk toepassen. Te vroeg toepassen wordt geweigerd; de registratie blijft aan planversie 1 gebonden.",
  "Route A: member acceptance, trainer approval and separate application. Early application is rejected; the record remains bound to plan version 1.",
  "Route A: Mitgliedsannahme, Trainerfreigabe und separate Anwendung. Vorzeitige Anwendung wird abgelehnt; der Eintrag bleibt an Planversion 1 gebunden."
 ],
 "snapshot": [
  "De eerste trainingsdag is handmatig gewijzigd. De nieuwe planversie begint met lege registraties. Het oude plan en de geregistreerde sets blijven in de historie.",
  "The first training day was manually changed. The new plan version starts with empty records. The old plan and recorded sets stay in history.",
  "Der erste Trainingstag wurde manuell geaendert. Die neue Planversion beginnt mit leeren Eintraegen. Der alte Plan und die erfassten Saetze bleiben im Verlauf."
 ],
 "expired": [
  "De bron is verlopen. Geen nieuwe registratie of voorstel; bestaande historie blijft zichtbaar.",
  "The source has expired. No new record or proposal; existing history remains visible.",
  "Die Quelle ist abgelaufen. Kein neuer Eintrag oder Vorschlag; bestehender Verlauf bleibt sichtbar."
 ],
 "record_binding": [
  "Deze registratie past niet bij de workout, maaltijd of versie. Niets gewijzigd.",
  "This record does not match the workout, meal or version. Nothing changed.",
  "Dieser Eintrag passt nicht zum Workout, zur Mahlzeit oder Version. Nichts geaendert."
 ],
 "value": [
  "Ongeldige invoer. Leeg blijft ontbrekend; RPE gebruikt stappen van 0,5. Niets gewijzigd.",
  "Invalid input. Empty stays missing; RPE uses increments of 0.5. Nothing changed.",
  "Ungueltige Eingabe. Leer bleibt fehlend; RPE nutzt Schritte von 0,5. Nichts geaendert."
 ],
 "below": [
  "Onder gepland bereik",
  "Below planned range",
  "Unter geplantem Bereich"
 ],
 "within": [
  "Binnen gepland bereik",
  "Within planned range",
  "Im geplanten Bereich"
 ],
 "above": [
  "Boven gepland bereik",
  "Above planned range",
  "Ueber geplantem Bereich"
 ],
 "energy": [
  "Energie (kcal)",
  "Energy (kcal)",
  "Energie (kcal)"
 ],
 "protein": [
  "Eiwit (g)",
  "Protein (g)",
  "Eiweiss (g)"
 ],
 "carb": [
  "Koolhydraten (g)",
  "Carbohydrate (g)",
  "Kohlenhydrate (g)"
 ],
 "fat": [
  "Vet (g)",
  "Fat (g)",
  "Fett (g)"
 ],
 "catalog": [
  "Exacte product-/receptbron",
  "Exact product/recipe source",
  "Exakte Produkt-/Rezeptquelle"
 ],
 "closures": [
  "Eerdere afrondingen",
  "Earlier completions",
  "Fruehere Abschluesse"
 ],
 "registrationNote": [
  "Alle workouts en maaltijden uit het beschikbare plan. Gepland betekent niet uitgevoerd; toekomstige trainingen blijven afzonderlijk herkenbaar.",
  "All workouts and meals in the available plan. Planned does not mean performed; future workouts remain identifiable.",
  "Alle Workouts und Mahlzeiten des vorhandenen Plans. Geplant bedeutet nicht durchgefuehrt; zukuenftige Workouts bleiben erkennbar."
 ]
};
function get(k,l=0){return text[k]?.[l]||old.get(k,l);}function reason(k,l=0){return text[k]?.[l]||old.reason(k,l);}
const api={text,get,reason};if(typeof module==='object')module.exports=api;else root.FMZ21Copy=api;
})(globalThis);
