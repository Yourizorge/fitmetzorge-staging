# Package 6E-2 Offline Aanbevelingscontract

COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE CONTRACTS ONLY.
N1-N3 expliciet geaccepteerd op 2026-09-10; zie PHASE6E2_FREEZE_RECEIPT.md.
Geen live integratie of deskundige validatie.
6E-0/6E-1 blijven accepted/frozen; D1-D12 en O1-O5 blijven behouden.
Bronbaseline e356a4cb951fc3d614035fa0bf547e669b4d045a; code uitsluitend _offline/phase6e2.

## Inhoud Die Nu Echt Werkt

| Type | Concreet voorstel bovenop feiten | Vereist bewijs | Alleen feiten/verduidelijking wanneer |
| --- | --- | --- | --- |
| daily_record_check | Eigen dagregistratie controleren; ontbrekende slaap alleen aanvullen als de gebruiker die weet, anders leeg laten; bij bekende slaap alleen een bevestigbare invoerfout corrigeren | Volledige eigen training_minutes en steps, dezelfde bronbundel; slaap alleen tonen uit een bruikbare eigen bron | Vereiste totalen ontbreken/onvolledig zijn of bronbundels niet samenhangen |
| workout_reflection | Zelf een bestaande geregistreerde set kiezen om terug te kijken en een aandachtspunt noteren; geen set/oefening door Youri verzonnen | Volledige completed_sets, completed_reps, duration_minutes uit dezelfde workout-aggregatebron; minstens een geregistreerde set | Bron ontbreekt/partial, geen setbasis, actuele klacht of nog onvoldoende context |
| weekly_review | Vergelijkbare eigen weektotalen naast elkaar zetten en een moment/aandachtspunt voor eigen weekevaluatie kiezen | Volledige training_minutes en completed_workouts, coherent huidig en vorig bronpakket; gelijke methode/eenheden/duur en aansluitende niet-overlappende vensters | Een van deze vergelijkingsvoorwaarden ontbreekt, actuele klacht of onvoldoende context |

Minstens een set is hier bewijs dat een set kan worden teruggekeken, geen medische norm.
Nul is alleen een werkelijk geregistreerde nul. Geen verzonnen slaap, doel, trainergrens,
belasting, techniek, oorzaak, gereedheid of vooruitgang. Een hogere/lagere delta is
geen beter/slechter-oordeel. De gebruiker kiest het reflectiepunt zelf; de engine kent
geen set-ID of oorzaak uit totalen. Alle voorstellen zijn optioneel en voeren niets uit.

De reeds toegestane aggregate-invoer bevat GEEN beoordeelde persoonlijke doelen,
trainergrenzen, oefeningsgewichten, techniek of voedings-/hersteladviescontract.
Daarom gebruiken deze drie typen alleen registraties en vergelijkingen. goal_source
en trainer_limits_source blijven null; extra goal/trainer/approved-velden worden
afgewezen, niet als betrouwbare grens overgenomen. Bestaande doelen/plannen worden
niet aangeraakt. Latere trainings-, voedings- en herstelcoaching blijft de ambitie,
maar is niet ten onrechte als geleverd of geschikt verklaard.

training_load, nutrition_change, recovery_return en goal_adjustment hebben een
uitvoerbare content_boundary in ELKE toestand, met expliciete ontbrekende bron-/
inhouds-/deskundige criteria. Er is geen fictieve trainer of medische aanvraagdienst.

## Vijf Afzonderlijke Onderdelen

Chat en bestaande historie gebruiken hun eigen frozen authorityvelden.
Nieuwe feiten gebruiken het bestaande analysis-consent/entitlement-contract.
Aanbevelingen vereisen daarnaast hun eigen data-/vergelijkings-/contextvoorwaarden.
Automatische uitvoering blijft altijd UIT; geen writes, sharing, provider of scheduler.
Een geweigerd voorstel wijzigt geen toegang of abonnement. De bestaande live
6D safety_hard_stop is NIET versoepeld of omzeild door dit offline ontwerp.

## Hervatting Per Type: Geaccepteerd Offline Ontwerp

Alle cellen veronderstellen eigen rechten en de hierboven vereiste gegevens.

| Bericht-/veiligheidscontext | Dagregistratiecontrole | Workout-/weekreflectie | Fysieke/voedings-/hersteladviezen |
| --- | --- | --- | --- |
| Geen herkend actueel signaal / gewone training | Mogelijk | Mogelijk | Inhoudsgrens blijft |
| Alleen historisch, ontkend, educatief of geciteerd | Mogelijk met bestaande niet-actuele feedback waar van toepassing | Mogelijk; niet gelijkgesteld aan geschiktheid | Inhoudsgrens blijft |
| Actuele, ernstige of oningedeelde klacht | Mogelijk NAAST ongewijzigde klachtfeedback, waarschuwing eerst | Alleen feiten, geen reflectievoorstel bij deze melding | Geen vrijgave; deskundige criteria open |
| Taalmisverstand / technische fout | Mogelijk, geen gezondheidswaarschuwing verzonnen uit een fout | Feiten plus optioneel verduidelijken/retry of verder chatten | Inhoudsgrens blijft |
| Exacte verduidelijking/retry slaagt | Ongewijzigd | Mogelijk als geen andere actuele klacht resteert | Inhoudsgrens blijft |
| Nieuwe gewone context na een onopgelost misverstand | Ongewijzigd | Alleen niet-fysieke reflectie kan weer; oude kwestie wordt niet gewist | Geen medische vrijgave |
| Zelf gemeld herstel met frozen binding | Ongewijzigd, expliciete zelfrapportagefeedback | Alleen niet-fysieke reflectie onder eigen bronvoorwaarden | Geen medische vrijgave; ernstige/terugkerende/oningedeelde criteria open |
| Nieuwe/terugkerende klacht | Waarschuwing opnieuw, registratiecontrole apart | Weer alleen feiten | Inhoudsgrens blijft |
| O5 verlopen/vroeger vervallen of bron ontbreekt | Datacontrole mogelijk zonder reconstructie | Eerst actuele context vragen als geen nieuwe bruikbare context bestaat; chat blijft vrij | Geen vrijgave door tijd/verwijderen |
| Nieuwe duidelijke gewone context na zo'n gat | Datacontrole | Alleen niet-fysieke reflectie mogelijk; geen historische diagnose gereconstrueerd | Inhoudsgrens blijft |

Dit introduceert GEEN medische herstelcriteria. Het is het geaccepteerde offline ontwerp voor het opnieuw
aanbieden van lezen/registreren/reflecteren, niet hervatten van lichamelijk advies.
Een bekend actueel signaal houdt voorrang op latere geruststellende gewone tekst.
Een oud verlopen probleem wordt geen eeuwige algemene accountblokkade. Het voorgestelde
gedrag en exacte conceptcopy zijn als offline product geaccepteerd, niet deskundig
goedgekeurd; complete_health_resumption_flow=false.

## Uitvoerbaar Koppelvlak En Vertrouwen

prepare(state, nowMs, options, previousContext) gebruikt een uitgegeven immutable
6E-1-state, de bestaande synthetische klok en O5-projectie. Snapshotbinding bevat
subject_id, revision, message_id en source_revision; waarschuwingen behouden ook
issue_revision en attempt. Een volgende snapshot maakt de vorige ongeldig.
Een afwijkende event-lineage, vervalste state of teruglopende klok wordt afgewezen.
Binnen dezelfde reeks moet previousContext steeds worden doorgegeven; null is alleen
initialisatie van een synthetisch experiment, geen nieuw-gesprek-/herlaadreset.

recommend({synthetic_only:true,type,binding,analysis}, context, authority) accepteert
uitsluitend de exacte frozen analysis-/authorityschemas. Geen fixtureverwachting,
medisch niveau of vrije adviesinstructie als beslisinvoer. Bronvensters mogen niet
in de toekomst liggen ten opzichte van de geinjecteerde klok. De eigen cijfers,
bronreferenties, toegangsuitkomst, waarschuwingen, voorstel en redenen zijn afzonderlijk
zichtbaar. De negen normale voorbeelden tonen echte berekende waarden en deltas.

Bij ingetrokken chatconsent worden geen private waarschuwingen/klinische context uit
de state teruggegeven. Beschikbare eigen feiten en datacontrole worden apart beoordeeld.
Contextgebonden reflectie vraagt bruikbare context onder de bestaande toestemming.
Het actuele source-record/authorityobject is hier synthetisch, geen live backendbewijs.

## O5 En Ontbrekende Bronnen

Alleen de bestaande minimale O5-records blijven: eerste datum, status, berichtverwijzing.
Eerste registratie + 30 * 86400000 ms is de exacte maximumgrens, eerder indien onnodig.
Bekijken/verwerken/retry/zelfrapportage vernieuwen niets. Nieuwe meldingen krijgen
alleen hun eigen nieuwe bronanker. Geen 90/180-dagenroute via een andere status.
Binnen een reeks blijft een ontbrekende bron ontbreken, ook als de volgende verwerking
de optie niet herhaalt. Alleen nog niet verlopen O5-verwijzingen dragen die status;
geen nieuwe onbeperkte tombstone. Verlopen/ontbrekende broninhoud wordt niet gelezen
om oude waarschuwingen of medische criteria opnieuw te maken.

Opties voor missing/unnecessary verwijzen naar bestaande synthetische O5-bronnen.
Dit is GEEN algemene chat-deleteadapter, duurzame opslag of echte verwijdering.
Raw flowhistorie, contextbindings en testresultaten zijn geen nieuwe bewaarpayload.
Bestaande chat-/analyseretentie blijft ongewijzigd. Live source-availability, herstel
na procesrestart, concurrency, autorisatie en daadwerkelijke deletion moeten nog
apart aantoonbaar worden uitgewerkt. Er bestaat geen menselijke beoordelingsdienst.

## Grenzen En Productreview

[Owneroverzicht](PHASE6E2_OWNER_OVERVIEW.md) toont exacte NL/EN/DE-conceptantwoorden,
alleen nieuwe keuzes en het verschil met feiten. [Technisch rapport](PHASE6E2_TECHNICAL_REPORT.md)
bevat preregistratie, tests, commits, frozen bewijs en publicatiecontroles.
Medische inhoud/toepassing/hervatting, privacy/noodzaak/retentie, juridische claims
en moedertaalbeoordeling blijven OPEN voor eventuele live inzet. Geen expert benaderd.
6E-2 owner-accepted/frozen uitsluitend offline. Afzonderlijke GO ontvangen voor 6E-3;
geen live AI of verdere automatische pakketstart. Timer/RIR/RPE door de owner getest
en geaccepteerd; alleen de nieuwe kolomuitlijning blijft pending owner retest.
