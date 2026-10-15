# Gecontroleerde releasevolgorde

Dit register beschrijft de vervolgintegratie, niet een bulkpublicatie of nieuwe
toestemming. De concrete lokale kandidaat staat in `_offline/phase6e_server_v1`.
Historisch bewijs staat in [het werkdagrapport](PHASE6E_WORKDAY_RESULT_20261015.md).
De [actuele preregistratie](PHASE6E_COMPLETION_RUN_20261015.md) legt de expliciete
toestemming vast voor precies een nieuwe 11-run met 106496 rijplaatsen en 2237
SQL-commando's. Volgens de actuele parentmelding is deze run inmiddels verbruikt:
NO-GO bij gereserveerd meterblok66-87 in de M44 CLI-bewijsvergelijking
(16 numeriek tegenover14 verwacht).73 commando's zijn expliciet bevestigd;
87 is het gereserveerde meterverbruik, niet het bewezen werkelijke aantal.
CLI-exit0 meldt M44-toepassing. Onafhankelijke hosted44/44-, SQL-identiteits-
en afsluitende dry-runcontrole ontbreken. JIT gesloten; geen Auth/workflowfixtures. De parent
bewaart de exacte bronadmission en oorspronkelijke receipts; geen heropening
of bronwijziging van deze poging. Geen hernieuwd owner-capaciteitsbesluit
gevraagd. Deze toestemming is geen vrijgave van de acht volgende slices. Geaccepteerde
broncontracten13-20 blijven read-only;21 is niet geaccepteerd en default-off.

## Gemeenschappelijke grens

Elke slice gebruikt servermatige identiteit/workspacebinding, een actuele Auth-
sessie, private RLS, exacte bron- en schemaversie, CAS en een idempotency-key.
Een browserrol verleent geen rechten. De lokale kandidaten45/46 zijn geen
hosted migrations en hun nummering is geen reservering van toekomstige slots.
Nieuwe canonical migrationnamen pas via de CLI maken bij een concrete release.

Elke hosted vrijgave vereist de volledige11-keten en noodzakelijke ownerreview,
brongebonden schone CI, actuele project/migration/dry-runcontrole, een concreet
commandoregister met veilige stopreserve en een afzonderlijk toegelaten budget.
De oude registration12-dossiers bevatten gemeten lokale commando's, geen
doorlopende hosted toestemming. Numerieke omvang alleen bewijst geen databehoud.

## Increments

| Volgorde en gedrag | Bestaande bronnen en lokale opslag | Toelating en gerichte tests | Terugdraaien |
| --- | --- | --- | --- |
| 1. Minimale historische registratie12: opslaan, corrigeren, herladen, opnieuw aanmelden | `registration12.cjs`, `registration_store.py`, `registration_transport.py`; private workspaces/revisions/requests/audit uit kandidaat45 | `registration_database.py`, `registration_proof.py`, `registration_browser.cjs`;22 gemeten transportparen; exact geselecteerde accounts, bron en writeset; geen lifecycle of outbox meepubliceren | Nieuwe ingang sluiten; versies en audit behouden; uitsluitend bewezen eigen fixtures verwijderen |
| 2. Brongebonden signalen13-14 en opnieuw beoordelen | `domain.cjs`, `windows.cjs`, immutable bronrevisies; geen nieuwe adviesregels | Complete vergelijkbare vensters; ontbrekende/tegenstrijdige bron; deduplicatie; broncorrectie trekt voorstel en goedkeuring in; exact benodigde statekeys selecteren | Signaalverwerking default-off; oude registraties en geldige historie blijven |
| 3. Route B-intake15 en planbasis | `panels.js`, `domain.cjs`, frozen intake-/catalogusvalidators; versiegebonden intakeHistory | Catalogusverval, allergieconflict, ontbrekende toestemming, bronwijziging; Route A ongewijzigd; geen trainerstap voor B | Nieuwe intakebewerking sluiten; eerdere intake/planversies behouden |
| 4. Trainingsplan16 en voedselplan17 bewerken | `presentation.cjs`, frozen training-/nutrition-rules models; gezamenlijke private state met afzonderlijke bronversies | Exacte oefening/productversie; sets/reps/rust/RIR/RPE; portiegrenzen, ontbrekend versus nul; geplande totalen nooit als gegeten presenteren | Bewerking sluiten; geen achteraf herschrijven van oude snapshots |
| 5. Gezamenlijke review18 | `domain.cjs`, `store.py`; CAS-transactie plus request/audit | A: lid, trainer, apart apply; B: lid, apart activate; conflict, dubbel verzoek, rollback na fout, restore als nieuwe versie | Toepasroute sluiten; oud plan blijft bestaan; terugzetten alleen via nieuw goedgekeurd voorstel |
| 6. Herstel/check-in19 en Vandaag20 | `windows.cjs`, `planning.py`, `outbox.py`; kandidaat46 voor transactionele outbox, geen echte push | Bronvensters, tijdzone/DST, check-inoptie, ontdubbeling, intrekking en verlies van antwoord na commit; serverklok expliciet | Nieuwe verwerking/delivery uit; niet-bezorgde events niet opnieuw als nieuw voorstellen; historie behouden |
| 7. Samengestelde historische workoutbediening | `workout12.cjs`, `composed_store.py`; dezelfde login, afzonderlijke historische workspace | Expliciet starten/afronden, partial blijft partial, oorspronkelijke snapshot, geen auth/workspaceverwisseling; niet automatisch onderdeel van slice1 | Lifecycle-ingang uit; minimale registratie en vorige closures niet verwijderen |
| 8. Voorkeuren en leesbare eenheden | `presentation.cjs`, `display.js`; originele meetwaarden/eenheden blijven leidend | NL/EN/DE, thema, metric/imperial display, herladen; voorkeur wijzigt geen voorschrift of eerdere goedkeuring | Voorkeursingang sluiten zonder bronwaarden om te rekenen |

Deze selectie hergebruikt dezelfde lokale app, geen acht nieuwe demo's. De
frontendnavigatie kan lokaal samen werken terwijl serveracties afzonderlijk
default-off worden vrijgegeven. Lokale migratie45 ondersteunt meerdere onderdelen;
dat is geen reden om alle acties bij de eerste hosted slice aan te zetten.

## Uitvoerbare offline pakketten

`_offline/phase6e_server_v1/workday_release.py` compileert en valideert de acht
pakketten in `workday_release_packets.json`. Dit is een offline controle, geen
hosted executor, nieuwe opslaglaag of vervanging van de bestaande admission-
en accountinghelpers. De helper importeert `registration_accounting`,
`receipt_accounting` en de canonieke JSON-hash uit `registration_scope`.
`registration_release.py` en alle bestaande accountingbestanden blijven gelijk.

De builder en17 packettests zijn lokaal PASS, samen met12 pure selectietests,
26 bestaande Python-helpertests en41 Node-tests. De volledige samenstelling
is daarna bewezen in CI38764963091 op1deac64. Het gegenereerde manifest in dat
artifact is aan de exacte geselecteerde CI-kandidaat gebonden. Een lokale JSON is een werksnapshot
en vervangt die bron-CI niet. `work_register.json`, nieuwe
gegenereerde manifesten en actuele statusreceipts zijn geen runtime-broninputs.

Elk pakket bevat de exacte ingangbestanden en transitieve lokale imports met
SHA256 van de werkelijke bytes, kandidaat-SQL met SHA256, rollen/rechten,
toegestane acties en edit-subdomeinen, JSON-statevelden, tabel-/sleutelwritesets,
testcommando's, SQL-profielen, ontbrekende runbindingen, gesloten gate en rollback.
Gedeelde ingeladen code is geen actiebevoegdheid. Een gewijzigde bron, ontbrekend
bestand, gewijzigd pakket of corrupt gebruikt receipt maakt `check` NO-GO.
Een nieuwe build legt gewijzigde bytes vast en vereist opnieuw review; hij
herstelt geen CI- of hosted bewijs.

Vanaf de repositoryroot, met Python 3.12 en Node beschikbaar:

```powershell
python -B _offline/phase6e_server_v1/test_workday_release.py
python -B _offline/phase6e_server_v1/workday_release.py build
python -B _offline/phase6e_server_v1/workday_release.py check
python -B _offline/phase6e_server_v1/workday_release.py show --slice registration12
python -B _offline/phase6e_server_v1/workday_release.py gate --slice registration12
python -B _offline/phase6e_server_v1/workday_release.py status
```

`gate` eindigt opzettelijk met exitcode3, `enabled=false`. `check` eindigt bij
geldige pakketten met0 en `PACKETS_VALID_NOT_RELEASED`; fouten geven2. Er is geen
optie om hiermee een hosted gate te openen. `test --slice <id>` voert alleen de
vaste lokale unitcommando's van dat pakket plus de packettests uit, zonder shell,
CI-dispatch, database of Auth. Het artefact wordt vooraf en achteraf gecontroleerd.

| Volgorde / pakket-ID | Lokale tests in de bestaande servermap | Aanvullend noodzakelijk op echte geisoleerde stack |
| --- | --- | --- |
| 1 / `registration12` | `registration12.test.cjs`; `test_registration_scope.py`, `test_registration_release.py`, `test_registration_accounting.py`, `test_receipt_accounting.py` | `registration_database.py`, `registration_browser.cjs`, `registration_proof.py`: beide routes, relogin, exact writeset/pairs |
| 2 / `signals13_14` | `domain.test.cjs`, `windows.test.cjs`; `test_outbox.py` | `database_tests.py`, `browser_checks.cjs`: broncorrectie, vensters, intrekking |
| 3 / `intake15` | `domain.test.cjs`, `presentation.test.cjs`; `test_outbox.py` | `database_tests.py`, `composed_browser.cjs`: B-intake/planbasis, A-weigering |
| 4 / `plans16_17` | `domain.test.cjs`, `presentation.test.cjs`; `test_outbox.py` | `database_tests.py`, `composed_browser.cjs`: exacte training/productversie en porties |
| 5 / `review18` | `domain.test.cjs`; `test_outbox.py`, `test_protocol.py` | `database_tests.py`, `browser_checks.cjs`, `composed_browser.cjs`: aparte acceptatie/apply, restore, foutrollback |
| 6 / `recovery19_today20` | `domain.test.cjs`, `windows.test.cjs`, `presentation.test.cjs`; `test_outbox.py`, `test_planning.py` | `database_tests.py`, `composed_browser.cjs`: DST, outbox, verloren antwoord |
| 7 / `workout12` | `registration12.test.cjs`, `workout12.test.cjs`; `test_protocol.py` | `database_tests.py`, `composed_browser.cjs`: aparte workspace, expliciet starten/afronden |
| 8 / `preferences` | `presentation.test.cjs`, `display.test.cjs`, `domain.test.cjs`; `test_outbox.py` | `database_tests.py`, `composed_browser.cjs`: NL/EN/DE, herladen, bronwaarden gelijk |

De JSON-pakketten bevatten volledige argv-lijsten en cwd. Node-tests draaien met
`node --test`; Python-tests met `python -B`. De echte stackgroepen worden door de
bestaande `ci.py` aangeroepen binnen zijn bestaande kandidaat-/runneromgeving:
PostgreSQL17, GoTrue, verify-full, psycopg en Playwright. Een los browserbestand
zonder zijn server/fixture-invoer is geen uitvoerbare stackproef. Deze lokale
voorbereiding start geen stack of hosted verbinding. De daadwerkelijke volledige
stackrun38764963091 is afzonderlijk geslaagd; niet acht afzonderlijke deployments.

## Opslag, rechten en accounting

De minimale registratie gebruikt alleen lokale kandidaat
`20261014105919_phase6e_synthetic_server_candidate.sql` (M45). `Store` leest en
schrijft onvoorwaardelijk de outbox: slices2-6 en8 hebben daarom ook
`20261014160019_phase6e_local_outbox.sql` (M46) nodig. Slice7 gebruikt voor de
historische acties M45, maar zijn samengestelde mount heeft voor de primaire
workspace eveneens M46 nodig. Dit is een werkelijke codeafhankelijkheid, geen
reden om bezorging of andere acties vroeg te activeren. Geen nieuwe migration
gemaakt; canonical hosted identiteit blijft oningevuld tot afzonderlijke toelating.

De bestaande private schema-ACL weigert PUBLIC/anon/authenticated/service_role.
De NOLOGIN/NOBYPASSRLS-serverrol heeft select, beperkte workspace-update,
revision/request/audit-insert en bij M46 beperkte outboxwrites. Er zijn geen
applicatie-DELETE-rechten. RLS, servermatige actor/workspacebinding en actuele
sessiecontrole blijven vereist. Het pakket beschrijft bestaande grants;
het lokale per-slice serverfilter dwingt de gekozen acties af. De hosted
aansluiting en eigen toelating zijn nog niet uitgevoerd.

Een gewijzigde historische registratie schrijft exact workspace UPDATE,
revision INSERT en request INSERT, met drie metadata-auditregels. Een primaire
mutatie voegt de exacte, uit gelockte state afgeleide outboxdelta toe. Een
primaire no-op schrijft nog een requestreceipt en mogelijk outboxstatussen;
een replay van hetzelfde verzoek schrijft niets. Denial/rollback laat geen
gecommitteerde applicatie-/auditrijen achter; sequencegaten zijn wel mogelijk.
Acteur, request, xid en SHA256-sleutels moeten exact matchen. Fixturecleanup
vereist apart toegelaten eigen sleutels en blijvend deletebewijs.

De helper leest de bestaande Python-SQL-literals via AST, zonder adapters te
importeren of SQL uit te voeren. Statische aantallen omvatten BEGIN en terminal:
historisch read8/write12/replay8; primair member-read9/trainer-read8,
gewijzigd13+N/ongewijzigd11+N/replay8. N is het exacte aantal outboxwrites.
Dit zijn **bronmodellen, geen metingen**. Elke commandoprefix vermeldt de
rollbackpoging; de volledige afsluiting, managed Auth, CLI, observers, guards,
fixtures, cleanup en beschermde metingen blijven afzonderlijk te binden.
Daarom blijven normaal hosted totaal, maximale veilige afsluiting en toegelaten
slice-budget `null`, nooit fictief0 of een overgenomen2237/4135.

Waar het lokale archief beschikbaar is, verifieert de helper gebruikte receipts
tegen MANIFEST en herberekent het bestaande transportregister en metercontrols.
De historische minimale970 SQL en de afzonderlijke private-transportmeting zijn
geen optelbare slice-budgetten. Ontbreekt het archief op CI, dan staat er expliciet
`ARCHIVE_NOT_AVAILABLE`, zonder gemeten totalen of bronmatchclaim. Aanwezig maar
beschadigd bewijs faalt; ontbrekend bewijs wordt niet als PASS behandeld.

## Lokale selectie en CI

- Parent heeft NEW/EXTRA aangevuld met `workday_release.py`,
  `test_workday_release.py`, `release_selection.py`, `test_release_selection.py`,
  `release_selection_http.py`, `receipt_accounting.py` en
  `test_receipt_accounting.py`; bestaande registrationhelpers blijven nodig.
- Voer packettests uit, gevolgd door `build` en `check` op de exacte CI-kandidaat.
  Verzamel het gegenereerde JSON als artifact. Het hoeft niet als inputbron in
  NEW; lokale bytes kunnen afwijken van een andere checkout. Geen historische
  receiptmap verplicht meenemen en geen oude CI als nieuwe bron-PASS gebruiken.
  Bij de bestaande Python-integratie: `packet = build(root=source, archive=archive)`
  en `verify(packet, root=source, archive=archive)` met dezelfde bron/archiefpaden,
  daarna opslaan. De lokale werksnapshot blokkeert deze CI-generatie niet.
- `release_selection.py` bevat de gedeelde SLICES en pure `validate_slice` en
  `require_action`. Parent heeft optionele `Application.release_slice` en
  `FMZ_LOCAL_RELEASE_SLICE` geintegreerd: uitsluitend operatorconfiguratie;
  requestdata kan de selectie niet wijzigen. DefaultNone houdt de bestaande
  lokale bulkbediening. Een geselecteerde actie gebruikt eerst verse
  `store.read`-identiteit/route/capabilities en daarna de guard voor execute.
  De guard leest geen pakket, bestand, budget of bewijs en kent geen hosted
  admission toe. Historische views hebben geen route: None is alleen bij de
  exact historische member-workspace toegestaan. Payloadvalidatie, sessie,
  consent, CAS en writeset blijven bij de bestaande Store/domain.
- De verse guard-read kost aanvullend8/9 applicatiecommando's plus managed Auth,
  ook bij een geweigerde buuractie. Dat zit niet impliciet in oudere registers.
  Parent voert `release_selection_http.py` op echte lokale PG/Auth uit met
  uitsluitend de preferences-selectie, niet alle acht geselecteerde releases.
  CI38764963091 bewijst27 controles voor die selectie. Hosted adapter,
  exacte per-slice registers en veilige afsluiting blijven afzonderlijk nodig.
- `work_register.json` onderscheidt gebouwd, lokaal/CI, hosted, review,
  vrijgegeven en dependency, naast de oudere velden. `status` verdraagt de
  oudere vorm en laat lopende CI lopend. De parent registreert finale actuele
  CI-/hostedstatus; de toegestane11-run is verbruikt met NO_GO bij de
  M44 CLI-evidencevergelijking. Geen hergebruik van die bronadmission.

## Nog geen hosted vrijgave

- Volledige actuele workout-/maaltijdregistratie21: owneracceptatie ontbreekt;
  serverweigering blijft actief. Historische registratie12 vervangt die niet.
- Duurzame browserconcepten voor historische registratie/herstel zijn lokaal
  geintegreerd en in CI38746007554 bewezen. Geen automatische verzending,
  goedkeuring/toepassing of21-invoer in de wachtrij. Een volledig offline
  opstartbare, algemene privacy-shell is gebouwd en doorstaat73 controles met
  echte lokale Auth in CI38764963091. Offline accounttoegang en gecachte login
  worden niet ondersteund.
- Free/Pro/AI: read-only proefperiode-/terugvalcontract bestaat. Autoritatieve
  uitgifte/abusebescherming is Phase7; exacte final-day/tijdzonebezorging blijft
  een open productregel. Geen betalingen of entitlementwijzigingen activeren.
- Badges/streaks, sport, wearables en media: geen complete bron-/kwaliteitsregels
  afleiden uit de roadmap. Echte providers en foto/videoanalyse blijven apart.
- Medische, voedingskundige, taal-, privacy- en juridische reviews, consent en
  providervoorwaarden voor echte leden blijven buiten deze synthetische PASS.

## Checkpoint

Het actuele werkregister benoemt uitvoerbare functies, afhankelijkheden en tests.
Een volgende sessie begint met gitstatus en behoudcontrole, niet met reset of
hergebruik van een verbruikte hosted poging. De112 historische meetparen blijven
geldig binnen hun oorspronkelijke scope; stap113 blijft incompleet.
