(function(root){"use strict";
const words={
title:['Gezamenlijke planreview','Combined plan review','Gemeinsame Planpruefung'],
mon:['Maandag','Monday','Montag'],tue:['Dinsdag','Tuesday','Dienstag'],wed:['Woensdag','Wednesday','Mittwoch'],thu:['Donderdag','Thursday','Donnerstag'],fri:['Vrijdag','Friday','Freitag'],sat:['Zaterdag','Saturday','Samstag'],sun:['Zondag','Sunday','Sonntag'],
fitness:['Fitheid','Fitness','Fitness'],maintain:['Behoud','Maintenance','Erhalt'],muscle:['Spieropbouw','Muscle building','Muskelaufbau'],strength:['Kracht','Strength','Kraft'],performance:['Prestaties','Performance','Leistung'],
subtitle:['Route B - training en voeding','Route B - training and nutrition','Route B - Training und Ernaehrung'],
notice:['Synthetische offline demo. Verversen wist de test. Geen medisch of voedingskundig gevalideerd plan.','Synthetic offline demo. Refresh resets the test. No medically or nutritionally validated plan.','Synthetische Offline-Demo. Neuladen setzt den Test zurueck. Kein medizinisch oder ernaehrungsfachlich validierter Plan.'],
tests:['Testscenario\u2019s','Test scenarios','Testszenarien'],start:['Begeleide test starten','Start guided test','Gefuehrten Test starten'],
previous:['Vorige stap','Previous step','Vorheriger Schritt'],next:['Volgende stap','Next step','Naechster Schritt'],
step:['Stap','Step','Schritt'],of:['van','of','von'],changed:['Gewijzigde gegevens','Changed data','Geaenderte Daten'],
expected:['Verwacht resultaat','Expected result','Erwartetes Ergebnis'],result:['Zichtbaar resultaat','Visible result','Sichtbares Ergebnis'],
pass:['PASS','PASS','PASS'],fail:['AFWIJKING','MISMATCH','ABWEICHUNG'],neutral:['Handmatige controle','Manual review','Manuelle Pruefung'],
allowed:['Een gezamenlijk voorstel mag klaarstaan; niets wordt automatisch geactiveerd.','A combined proposal may be prepared; nothing is activated automatically.','Ein gemeinsamer Vorschlag darf vorbereitet werden; nichts wird automatisch aktiviert.'],
blocked:['Geen nieuwe gezamenlijke activatie. Bestaande versies blijven behouden.','No new combined activation. Existing versions are preserved.','Keine neue gemeinsame Aktivierung. Bestehende Versionen bleiben erhalten.'],
pending:['Voorstel klaar','Proposal ready','Vorschlag bereit'],confirmed:['Bevestigd; nog niet actief','Confirmed; not active yet','Bestaetigt; noch nicht aktiv'],active:['Actief in deze test','Active in this test','In diesem Test aktiv'],intake:['Broncontrole nodig','Source review needed','Quellenpruefung noetig'],reassess:['Opnieuw beoordelen','Review again','Erneut pruefen'],rejected:['Afgewezen','Rejected','Abgelehnt'],
source:['Gebonden bronnen','Bound sources','Gebundene Quellen'],mapping:['Expliciete fictieve koppeling','Explicit fictional link','Explizite fiktive Verknuepfung'],
training:['Training','Training','Training'],nutrition:['Voeding','Nutrition','Ernaehrung'],goal:['Doel','Goal','Ziel'],
version:['Versie','Version','Version'],revision:['Intakeversie','Intake version','Anamneseversion'],frequency:['Trainingen','Workouts','Trainings'],
current:['Huidige testversie','Current test version','Aktuelle Testversion'],proposal:['Gezamenlijk voorstel','Combined proposal','Gemeinsamer Vorschlag'],
none:['Geen','None','Keine'],build:['Opnieuw beoordelen','Review again','Erneut pruefen'],confirm:['Beide plannen bevestigen','Confirm both plans','Beide Plaene bestaetigen'],activate:['Samen activeren','Activate together','Gemeinsam aktivieren'],
reject:['Voorstel afwijzen','Reject proposal','Vorschlag ablehnen'],restore:['Versie 1 terugzetten','Restore version 1','Version 1 wiederherstellen'],
duplicate:['Activatie nogmaals versturen','Resend activation','Aktivierung erneut senden'],reset:['Test opnieuw beginnen','Restart test','Test neu starten'],
revoke:['Toestemming intrekken','Withdraw consent','Einwilligung widerrufen'],change:['Nieuwe bronversie simuleren','Simulate new source version','Neue Quellversion simulieren'],
day:['Eerste trainingsdag','First training day','Erster Trainingstag'],moment:['Eerste maaltijdmoment','First meal time','Erste Mahlzeitzeit'],save:['Keuze opslaan','Save choice','Auswahl speichern'],
history:['Versiegeschiedenis','Version history','Versionsverlauf'],audit:['Technisch testspoor','Technical test trail','Technisches Testprotokoll'],
target:['Bestaand fictief doel','Existing fictional target','Bestehendes fiktives Ziel'],actual:['Exact berekend voorstel','Exactly calculated proposal','Exakt berechneter Vorschlag'],difference:['Verschil','Difference','Differenz'],
energy:['Energie (kcal)','Energy (kcal)','Energie (kcal)'],protein:['Eiwit (g)','Protein (g)','Protein (g)'],carb:['Koolhydraten (g)','Carbohydrates (g)','Kohlenhydrate (g)'],fat:['Vet (g)','Fat (g)','Fett (g)'],
unit:['Oorspronkelijke eenheden','Original units','Urspruengliche Einheiten'],load:['Nieuw gewicht','New load','Neues Gewicht'],rest:['rust (sec)','rest (sec)','Pause (Sek)'],
empty:['niet geregistreerd','not recorded','nicht erfasst'],manual:['Keuze gewijzigd; beoordeel opnieuw.','Choice changed; review again.','Auswahl geaendert; erneut pruefen.'],
noPrediction:['Geen calorie- of belastingsaanpassing afgeleid uit de combinatie.','No calorie or load adjustment inferred from combining the plans.','Keine Kalorien- oder Belastungsanpassung aus der Kombination abgeleitet.']
};
const reasons={
success:['Beide broncontracten zijn geldig. De inhoud blijft binnen de bestaande synthetische regels.','Both source contracts are valid. Content remains within existing synthetic rules.','Beide Quellvertraege sind gueltig. Inhalte bleiben innerhalb bestehender synthetischer Regeln.'],
idempotent:['Deze aanvraag was al verwerkt. Er is geen extra versie gemaakt.','This request was already processed. No extra version was created.','Diese Anfrage wurde bereits verarbeitet. Keine zusaetzliche Version wurde erstellt.'],
identity:['De bronnen horen niet bij dezelfde expliciet gekoppelde testidentiteit.','Sources do not belong to the same explicitly linked test identity.','Quellen gehoeren nicht zur selben explizit verknuepften Testidentitaet.'],
binding:['Deze aanvraag hoort niet bij de toegestane synthetische Route B.','This request does not belong to the permitted synthetic Route B.','Diese Anfrage gehoert nicht zur erlaubten synthetischen Route B.'],
frequency:['De bronnen noemen verschillende aantallen trainingen. Corrigeer de bron; ik kies niet zelf.','The sources record different numbers of workouts. Correct the source; I will not choose.','Die Quellen nennen unterschiedliche Trainingszahlen. Quelle korrigieren; ich entscheide nicht selbst.'],
goal:['De expliciete doelkoppeling klopt niet. Ik verzin geen gezamenlijk doel.','The explicit goal link does not match. I will not invent a combined goal.','Die explizite Zielverknuepfung stimmt nicht. Ich erfinde kein gemeinsames Ziel.'],
expired:['Een bron is verlopen. Er is een actuele, betrouwbare bron nodig.','A source has expired. A current reliable source is needed.','Eine Quelle ist abgelaufen. Eine aktuelle verlaessliche Quelle ist erforderlich.'],
safety:['Een klacht of onopgeloste herstelcontext blokkeert fysieke planvorming. Zelf gemeld herstel is geen medische vrijgave.','A complaint or unresolved recovery context blocks physical planning. Self-reported recovery is not medical clearance.','Eine Beschwerde oder ungeklaerter Erholungskontext blockiert physische Planung. Selbst gemeldete Genesung ist keine medizinische Freigabe.'],
consent:['Toestemming is ingetrokken of ontbreekt. Geen verdere verwerking of nieuw voorstel.','Consent was withdrawn or is missing. No further processing or new proposal.','Einwilligung wurde widerrufen oder fehlt. Keine weitere Verarbeitung oder neuer Vorschlag.'],
version_conflict:['De aanvraag is verouderd of nog niet bevestigd. Niets is toegepast. Beoordeel de huidige versie opnieuw.','The request is stale or not confirmed. Nothing was applied. Review the current version again.','Die Anfrage ist veraltet oder nicht bestaetigt. Nichts wurde angewendet. Aktuelle Version erneut pruefen.'],
atomic_fault:['De toepassing is onderbroken. Noch training, noch voeding is gewijzigd.','Activation was interrupted. Neither training nor nutrition changed.','Aktivierung wurde unterbrochen. Weder Training noch Ernaehrung wurde geaendert.'],
restore_source:['De oude versie past niet meer bij de huidige bronnen. Geen automatische terugzetting.','The old version no longer matches current sources. No automatic restoration.','Die alte Version passt nicht mehr zu aktuellen Quellen. Keine automatische Wiederherstellung.'],
source_version:['Een gewijzigde bron mist een geldige nieuwe versie.','A changed source lacks a valid new version.','Einer geaenderten Quelle fehlt eine gueltige neue Version.'],
'nutrition:missing:age':['De leeftijd ontbreekt. Ik maak geen voedingsplan met verzonnen gegevens.','Age is missing. I will not create a nutrition plan using invented data.','Das Alter fehlt. Ich erstelle keinen Ernaehrungsplan mit erfundenen Daten.'],
'nutrition:preference_conflict':['Pinda is zowel uitgesloten door allergie als gekozen als favoriet. Geen voorstel; pinda komt niet in een plan terecht.','Peanut is excluded by allergy and selected as a favorite. No proposal; peanut is not included in a plan.','Erdnuss ist wegen Allergie ausgeschlossen und als Favorit ausgewaehlt. Kein Vorschlag; keine Erdnuss in einem Plan.'],
fallback:['De broncontrole is niet geslaagd. Er wordt niets toegepast.','Source validation failed. Nothing will be applied.','Quellenpruefung fehlgeschlagen. Nichts wird angewendet.']
};
const api={words,reasons,get:(k,l=0)=>(words[k]||[k,k,k])[l],reason:(k,l=0)=>(reasons[k]||reasons.fallback)[l]};
if(typeof module==='object')module.exports=api;else root.FMZ18Copy=api;
})(globalThis);
