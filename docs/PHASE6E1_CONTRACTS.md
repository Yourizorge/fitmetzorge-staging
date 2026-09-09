# Package 6E-1 Offline Contracten

Status: COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE CONTRACTS ONLY.
Owner accepteert O1-O5 expliciet op 2026-09-09; zie Decision 0039 en de
[freeze receipt](PHASE6E1_FREEZE_RECEIPT.md). Geen medische/deskundige goedkeuring,
complete herstelimplementatie of live integratie/opslag.
D1-D12 blijven behouden. 6E-0 blijft owner-accepted/frozen; Phase 6E blijft onvoltooid.

## Versies En Vertrouwensgrens

phase6e1.offline.v0.2.0; context/flow/content v1, retention v2.
Actuele runtimebaseline f3ab33c6553c2d5dd3fc06518c150bd474fb6159,
inclusief ronde timer en inline RIR/RPE. Alle 60 runtime-assets blijven behouden.
Nieuwe bron uitsluitend _offline/phase6e1; private Node-module zonder dependencies.
De 23 frozen _offline/phase6e0-bestanden worden niet gewijzigd.
Alleen vier frozen JSON-bronnen worden read-only hergebruikt: rules, context-hints,
copy en de warnings uit warning-recovery-proposal. De historische aanvraagflow
wordt NIET aangeroepen of als productkeuze overgenomen.

Alle invoer is synthetisch, alle toestand is in geheugen. Een WeakSet-brand en
deep-freeze voorkomen vervalste of gemuteerde stateobjecten binnen deze simulator.
Dat is GEEN serverauthenticatie, opslag-, multi-process- of cryptografisch bewijs.
synthetic_only, availability en authority zijn simulatorinvoer, geen vertrouwde
velden die een echte gebruiker later zelf mag aanleveren. Geen live adapter.
create initialiseert een synthetische persoon, nooit een nieuwe chat als veiligheidsreset.
Er wordt geen opslagbeleid geactiveerd en geen review-/aanvraagdienst aangemaakt.

## A. Berichtcontext Naar Feedback

Invoer: uitsluitend synthetic_only=true, text (maximaal 4096 UTF-16-code-units),
locale en availability. Extra velden als annotation, context, expected, approved
of help_level worden afgewezen. Fixtures leveren dus GEEN beslissende contextlabels.

Uitvoer bevat versie, categorie, afzonderlijk voorlopig niveau/null, onzekerheden,
conflicten, exact gekozen feedback en trace. Iedere trace heeft oorspronkelijke
UTF-16-start/eindpositie, letterlijk fragment, zinsdeelgrenzen, regel-ID,
contextreden en subjectbewijs (self_text/other/unspecified).
Normalisatie behoudt de terugmapping naar accenten, quotes en zero-width-tekens.

| Berichtcontext | Begrensde beslissing | Feedback |
| --- | --- | --- |
| Actuele gemelde klacht met bestaande regel | Alleen bestaande voorlopige R1-R4; bestaande borst+duizeligheidcombinatie blijft R4 | Ongewijzigde 6E-0-conceptcopy van dat niveau |
| Actuele gemelde klacht zonder bestaand niveau | Hints of resterend gezondheidswoord in eigen scope; null, geen nieuw medisch niveau | current_unclassified met expliciete stop-/hulpinstructie |
| Alleen educatief, ontkend, historisch, geciteerd of hypothetisch | Signaal blijft traceerbaar maar wordt niet als actuele klacht gerekend | noncurrent; vraag of het toch actueel is |
| Taal-/contextonzekerheid, ander persoon, ongesloten citaat of onbekende lichaamscontext | Onzekerheid expliciet, geen medische rang of zekerheid uit R0 | unclear; verduidelijking, niet automatisch dezelfde gezondheidswaarschuwing |
| Beschikbaarheid unavailable of ongeldig technisch contract | Geen nieuwe beoordeling, geen gezondheidsinferentie | technical; eerdere klachtwaarschuwingen blijven in de toestand |
| Gewone herkende trainingsuitspraak of ondubbelzinnige eigen herstelzin | no_signal/R0 is uitsluitend geen herkend actueel signaal | Bestaande no_signal-copy; herstel vereist daarnaast gebonden flow |

Ontkenning wordt per gevonden signaal afgegrensd; intrinsiek ademtekort als
cannot breathe wordt niet door zijn eigen negatie ontkend. Dubbele ontkenning
is een conflict, geen vrijgave. Niet-actuele context kan doorlopen in gecoördineerde
zinsdelen; een nieuwe actuele melding of zin doorbreekt die scope. Een geruststellend
zinsdeel wist een ander signaal niet. Een onbekend lichaamszinsdeel krijgt expliciete
onzekerheid, ook na een herkend/ontkend zinsdeel.
Duitse werkwoord-ik-inversie voor het bestaande beperkte-lucht-hint is toegevoegd,
zonder niveau toe te kennen. Er is geen algemene grammatica of begripsgarantie.

De vier oorspronkelijke gaten leveren alle current_unclassified/null met exacte
stop-/hulpconceptcopy; de 6E-0-bronnen zelf blijven unchanged.
Conflicten blijven zichtbaar naast de leidende waarschuwing, ook als een bestaand
niveau voorrang heeft. Taalkeuze bepaalt geen land/noodnummer.
Hulp blijft ontworpen binnen toegankelijke AI-chat, niet een nieuwe publieke dienst.
De simulatorfeedback zelf bewijst GEEN daadwerkelijke bereikbaarheid in de app.

## B. Verduidelijking En Retry

| Stap | Invoer / binding | Effect | Afwijzing / open grens |
| --- | --- | --- | --- |
| Nieuwe melding | subject, unieke event/message-ID, expected_revision, synthetische klok, tekst/locale/beschikbaarheid | Nieuwe globale revisie; per bericht health/communication/technical-kwestie indien nodig | Andere persoon, extra velden, stale globale revisie, hergebruikte identiteit of teruglopende klok |
| Start retry/verduidelijking | Persoon, message-ID, oorspronkelijke source_revision, actuele globale revisie | issue_revision en attempt omhoog; alleen passende niet-medische kwestie | Gezondheidsmelding is geen verduidelijkings-/retrydoel |
| Retry-resultaat | Exact subject/message/source_revision/issue_revision/attempt; beschikbaarheid | Beoordeelt oorspronkelijke tekst opnieuw; alleen eigen technische kwestie sluit bij succes. Nieuwe gezondheids-/taalkwestie wordt afzonderlijk vastgelegd | Geen vervangende tekst/approved; oude poging kan nieuwste niet afsluiten |
| Verduidelijking | Dezelfde vijfdelige binding plus nieuwe tekst | Eigen bevestigende beginzin Ik bedoelde / I meant / Ich meinte en herkende gewone/niet-actuele inhoud kunnen alleen de communicatiekwestie afsluiten | Ontkende, geciteerde, hypothetische, onduidelijke of kale R0/reactie sluit niet. Nieuwe klacht wordt wel vastgelegd |
| Nieuw signaal elders tijdens poging | Eigen nieuwe berichtrevisie | Oudere nog geldige issue-binding mag alleen eigen kwestie afhandelen; ander signaal blijft | Geen globale afhandeling of wissen van andere klachten |
| Dubbel resultaat | Zelfde event-ID met exact canoniek gelijke payload | Idempotent, geen tweede effect | Andere payload is ID-conflict; nieuw ID op afgehandelde poging is stale |

Geslaagde retry stopt aantoonbaar de betreffende technische fout, zonder er een
permanente reststatus van te maken. Historische events blijven in deze geheugenrun
traceerbaar. Eventpayloads zijn GEEN voorstel voor langdurige auditopslag.
O2: view.nonclinical_options biedt reformulate of retry EN continue_chat.
clarification_required=false; een mislukte poging verplicht niet tot een vraaglus.
Vrij verder chatten laat de eigen onopgeloste kwestie en andere klachten intact.
Een gezondheidskwestie achteraf betwisten vraagt nog inhoudsregels; deze simulator
registreert twijfel als misschien/think/glaube ook niet als ondubbelzinnig herstel en
doet geen medische herinterpretatie of menselijke beoordelingsprocedure.

## C. Inhoud Per Analyse

O3 owner-accepted offline. Alleen allowlisted synthetische aggregaten: eigen subject, source-ID, source-kind,
methodeversie, eenheid, exact begin/eindvenster en volledige/deels ontbrekende dekking.
Bronherkomst is hier een controleerbaar synthetisch contract, geen live verificatie
van die bron. Geen vrije adviesvelden, doelen, diagnose, belastbaarheid of causaal
verband. Een berekende nul wordt alleen getoond als daadwerkelijk aangeleverde waarde.

| Analyse | Venster / methode | Toegestane beschrijvende feiten | Geen conclusie over |
| --- | --- | --- | --- |
| Dag | Exact 24 uur synthetic_utc; day_totals_v1 | Workouts, trainingsminuten, stappen, zelf geregistreerde slaapuren | Genoeg slaap/beweging, herstel, intensiteit, calorieadvies |
| Na workout | Expliciet begin/einde, maximaal een synthetische dag; workout_totals_v1 | Duur, sets, herhalingen, afstand | Veiligheid, geschiktheid, prestatieverbetering, trainingsaanpassing |
| Week | Exact 7 synthetische dagen; week_totals_v1 | Workouts, trainingsminuten, stappen | Overbelasting, causaliteit, nieuw schema of coachingactie |

Dit is geen live lokale-kalenderadapter: tijdzone/DST, echte workoutidentiteit,
coverage en vertrouwde aggregatelevering moeten voor integratie worden uitgewerkt.
Een vergelijking vereist gelijke metriek, unit, subject, methode en duur, volledige
dekking in beide niet-overlappende vensters. Alleen absoluut verschil, nooit procent
delen door nul of vooruitgang/slechter worden suggereren. Totalen zijn geen bewijs
van vergelijkbare intensiteit of oefeningssamenstelling. Bij ontbrekend/onvergelijkbaar
bewijs verschijnt concrete ontbrekende-datafeedback; geen verzonnen nul of delta.
Integer-/tijdvenstercontroles zijn technische datavormgrenzen, geen medische normen.

| As | Voor herstel | Na eigen herstelmelding | Hervattingsvoorstel / grens |
| --- | --- | --- | --- |
| Functietoegang | Chat/historie/analyse ieder onder eigen bestaande authority/consent | Ongewijzigd; gezondheid verandert entitlement niet | Geen algemene abonnements- of functieblokkade |
| Feiten en persoonlijke beschrijvende observaties | Dezelfde allowlisted waarden en vergelijkingen, met klachtwaarschuwing waar actueel | Dezelfde inhoud plus expliciete zelfrapportagestatus | Kan worden getoond zodra eigen bron/eenheid/venster/consent bruikbaar zijn; geen gezondheidsvrijgave nodig voor dit begrensde voorstel |
| Persoonlijke aanbevelingen | Niet gegenereerd | Niet automatisch hervat | Open inhoud per soort en hersteltoestand; GEEN individuele aanvraag/goedkeuringsdienst |
| Automatische wijzigingen | UIT | UIT | Latere coachingambitie uit masterplan blijft bestaan, maar hoort niet bij deze uitvoering |

Ontworpen feitenweergave is GEEN versoepeling van de bestaande 6D safety_hard_stop-gate.
Bij ontbrekende analyseconsent worden geen waarden/waarschuwingdetails via analyze
teruggegeven; chat-/historietoegang blijven afzonderlijk beoordeeld.
O4: aanbevelingsinhoud en hervatting worden per aanbevelingstype apart uitgewerkt.
Het nog niet implementeren van aanbevelingen is een globale ontbrekende inhoudspolicy,
geen levenslange blokkade op basis van een oude individuele onzekerheidsstatus.
Dit lost de ernstige/onduidelijke medische herstelvoorwaarden niet stilzwijgend op.

## D. Toestands- En Revisiematrix

| Eerdere toestand | Gebeurtenis | Technisch bewezen nieuwe toestand | Blijft toegankelijk / inhoud | Nog open |
| --- | --- | --- | --- | --- |
| Geen gezondheidsmelding | Nieuwe actuele R3/R4 of null-klacht | Nieuwe bronrevisie, actuele melding met exact tekstbewijs | Chat/historie en begrensde feiten onder rechten; stop-/hulpconceptfeedback | Medische labels/copy; ernstige of oningedeelde vervolgcriteria |
| Actuele klacht | Expliciete bevestiging met exacte targets en actuele revisie | self_reported voor uitsluitend die meldingen; oorspronkelijke waarschuwing in historie | Dezelfde beschrijvende inhoud; bericht dat dit geen vrijgave is | Toegestane aanbevelingen en daadwerkelijke hervattingscriteria |
| Actuele klacht | Eigen ondubbelzinnige chat-herstelzin met binding | Dezelfde zelfrapportage, zonder beroep op een approved-veld | Dezelfde toegang en feiten | Geen medische controle uitgevoerd |
| Actuele klacht | Herstelzin met nieuwe klacht elders | Nieuwe klachtrevisie, geen zelfrapportage uit conflicterende tekst | Actuele waarschuwing; eerdere historie behouden | Conflicterende/terugkerende/ernstige beoordeling |
| Zelf gerapporteerd voorbij | Nieuw of opnieuw genoemd signaal | Nieuwe actuele bronrevisie; oude herstelmelding geldt niet voor die melding | Opnieuw passende feedback; feiten/historie blijven | repeated_signal is alleen eerder gelijke code in deze geheugenrun, geen medische recidiefdrempel |
| Meerdere open klachten | Herstel voor een subset | Alleen gebonden subset zelf-gerapporteerd; overige meldingen actueel | Overige waarschuwing blijft zichtbaar | Geen globale vrijgave |
| Taal/techniek open | Juiste verduidelijking of retry | Alleen eigen niet-medische kwestie settled | Geen permanente technische blokkade; feiten onveranderd | Geen impliciete aanbevelingsbevoegdheid |
| Elke gezondheidsstatus | Nieuw gesprek, R0, approved, tijd, verwijderen | Geen ondersteunde vrijgaveovergang | Toegang/feiten niet gewijzigd | Retentie/ontbrekende details apart, geen clearance |
| Details ontbreken | Retentieprojectie | context_missing zolang de minimale O5-registratie nodig is en niet verlopen; geen reconstructie | Begrensde inhoud binnen bronnen/rechten | Zo nodig actuele context vragen, niet een verdwenen medische toestand verzinnen |

Concrete open criteria: inhoud per analyse en toestand; relevante actuele informatie
bij R3/R4; betekenis van herhaling; voorwaarden na een niet-ingedeelde klacht; grenzen
na verdwenen details. Er is geen hersteltermijn, medische urgentiedrempel of bevoegde
appbeoordelaar verzonnen. complete_health_resumption_flow blijft false.
Deze open criteria zijn geen afgeronde gebruikersflow. De bewezen toegang en
begrensde inhoud worden wel opgeleverd, niet stilgelegd door ontbrekend medisch beleid.

## E. Retentie En Ontbrekende Gegevens

| Klasse | Doel / noodzakelijkheid | Voorlopige bovengrens D5 | Synthetisch gedrag |
| --- | --- | --- | --- |
| episode_counter | Rollende beschrijvende telling, niet medische risicoscore | 30 dagen vanaf vastlegging | Exacte grens projecteert verloop; geen medisch herstel door verstrijken |
| closed_details | Alleen noodzakelijke uitleg van afgesloten/betwiste kwestie | Maximaal 90 dagen vanaf afsluiting, korter mogelijk | Verloopt in projectie; ongesloten details krijgen geen stille 90-dagenregel |
| minimal_audit | Minimale inhoudsloze beslismetadata | Maximaal 180 dagen vanaf vastlegging | Geen chattekst/medische details in deze klasse; daarna verloopprojectie |
| unresolved_signal / O5 | Recente meldingen volgen en onnodig herhaald uitvragen voorkomen; beheer FitMetZorge | Owner-accepted OFFLINE: maximaal 30 dagen vanaf eerste registratie, eerder weg wanneer niet nodig | Alleen datum, status, berichtverwijzing; iedere status dezelfde eindgrens; live opslag UIT |
| Ontbrekende details | Eerlijk weergeven wat niet meer aantoonbaar is | Geen nieuwe reststatus-levensduur gekozen | Geen vrijgave, geen nagebootste reconstructie, geen levenslange toegangssperre |

O5 wordt uitsluitend vertegenwoordigd door projectSafety(...).records. Elk record
heeft first_registered_at_ms, status en message_ref (message_id/source_revision).
Geen tekstkopie, medische score, extra detail- of auditkopie. Verloop bij
nowMs >= first_registered_at_ms + 30 * 86400000; dit zijn verstreken uren,
geen opnieuw beginnende kalendermaand. Datum/identiteit komen uit de eerste
synthetische bronmelding. Retry behoudt die oorsprong, ook wanneer pas later een
gezondheidsmelding wordt herkend. Bekijken, opnieuw verwerken, settled, awaiting,
self_reported en context_missing verlengen niets. Een werkelijk nieuw bericht
met een nieuwe klacht krijgt wel een eigen eerste registratie.

In een simulatiereeks moet steeds de vorige uitgegeven projectie worden doorgegeven.
Een revisiewatermerk voorkomt dat eerder als onnodig verwijderde bronnen terugkomen;
er blijft geen verlopen bericht-ID, tekst of per-melding-tombstone in records over.
De eerste null-projectie is alleen initialisatie van een synthetisch experiment,
geen reset/new-chat/herlaadroute. Ontbrekende bronnen worden met expliciete
synthetische opties gemodelleerd: geen reconstructie of nieuwe bewaartermijn.
De bron is zo nodig opnieuw te vragen als actuele context, zonder medische vrijgave
door ontbreken, verwijdering of tijdsverloop en zonder algemene toegangssperre.

plan() blijft een vergelijkende D5-diagnose, GEEN opslagpayload. Zijn diagnostische
items kunnen ook afgewezen/verlopen invoer beschrijven. Raw flow-events en oude
test-snapshots blijven alleen historisch geheugenbewijs, niet een bewaareis.
O5-records kunnen niet door een statuswisseling naar closed_details/minimal_audit
doorstromen: hun 30-dagengrens blijft staan. Zelfstandige andere D5-doeleinden en
bestaande chat-/analyseretentie worden niet veranderd. Onnodige data vervalt eerder.
De planner/projectie wijzigt geen input, bestand, echte chat of database.

Dit is geen juridisch/medisch gevalideerd bewaarbeleid of live verwijderimplementatie.
De klok, noodzakelijkheid en bronbinding zijn synthetisch. Vertrouwde eerste
registratie, duurzame hervatting, concurrency, bronverwijdering, fout-/klokafhandeling
en doelgebonden daadwerkelijke deletion moeten voor live nog aantoonbaar kloppen.
Opslag is UIT; geen menselijke medische beoordelingsdienst of heimelijke reststatus.

## Grenzen En Vervolg

[Owneroverzicht](PHASE6E1_OWNER_OVERVIEW.md) legt de geaccepteerde O1-O5 vast.
[Technisch rapport](PHASE6E1_TECHNICAL_REPORT.md) scheidt technische tests,
tekst-naar-feedbackbewijs, beperkingobservaties en medische onbewezen aannames.
Geen expert benaderd, geen provider/DB/membertest, kosten, cleanup of productie.
Owneracceptatie berust uitsluitend op expliciet O1-O5-akkoord, niet op technische tests.
Medische, privacy-, juridische en NL/EN/DE-taalreviews blijven voor live open.
Het [enige vervolgvoorstel](PHASE6E1_PROPOSAL.md) is niet gestart.
