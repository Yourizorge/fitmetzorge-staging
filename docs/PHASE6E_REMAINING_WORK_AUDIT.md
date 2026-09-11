# Phase 6E Remaining Work Audit

READ-ONLY AUDIT COMPLETE. 6E-6 OWNER-ACCEPTED/FROZEN - OFFLINE ONLY.
6E als geheel ONVOLTOOID. 6E-7 PROPOSED / NOT STARTED.
Datum: 2026-09-11. Geen implementatie-, configuratie- of activatietoestemming afgeleid.

## Reikwijdte En Bewijsniveau

Baseline ad7df47a2406f55582ab3b2fe5779c88b1b31ba1, staging main,
supabase/.temp/phase4fb-staging-deploy. Lokaal/cached/direct remote gelijk; schoon.
AGENTS/config, huidige status/masterplan/architectuur/testmatrix, beslisregister,
6E-1/5-freeze, 6E-6-code/tests/rapporten, bestaande frontend, Edge en canonical
migrations READ-ONLY onderzocht. Bestaande auto_review en managed grenzen behouden.

Bewijs hier is actuele REPOSITORYCODE plus historische deploymentbewijzen en
read-only synthetische probes. GEEN nieuwe live database/config/ledeninspectie.
De eerdere 33/33 migrationhistorie en 67 tabelfingerprints/100332 rijen zijn bewijs
van de Training-controle van 2026-09-10, niet vandaag opnieuw gevalideerd.
PROJECT_MIGRATION_RECONCILIATION.md zegt RESOLVED; oude 19 timestampverschillen
worden NIET opnieuw als actuele blokkade opgevoerd. Volledige lokale rebuild/
pg_cron-/OneDrive-beperkingen blijven wel open; geen cleanup/reset/replay gedaan.

6E-0..6E-6 leveren 122 frozen offline bestanden. 6E-6-bron:
6479711ffb4fa97ad4934e8245c9ae334f5b1337, tree89aee1f, 16 bestanden.
Oorspronkelijk 1142/1142 technisch PASS, 30 conceptscenario's, geen medische validatie.
Voor deze freeze: vijf bestaande isolatiechecks opnieuw PASS en alle 30 voorbeelden
in de bestaande IO-/netwerkvrije VM. Geen applicatie- of database-tests uitgevoerd.
Een read-only W2-probe registreert een weergavegat, geen nieuwe herkenningsmisscore.

## Bestaande Bouwstenen

| Ref | Aantoonbare bron | Wat dit wel/niet bewijst |
| --- | --- | --- |
| S01 | _offline/phase6e6/rules.cjs:10; engine.cjs:7; review.cjs:5 | Deterministische bronregels, drie statussen, in-memory CAS/audit. Geen live herkomst, undo of duurzame opslag |
| S02 | supabase/migrations/20260812000000_legacy_phase1_3_source_baseline.sql:185,248,274,1368 | training_plans/days/exercises, workout_sessions/set_logs en own-user policies bestaan in Git; geen immutable volledige planversieketen |
| S03 | assets/phase3-training-engine.js:1515,1880,2258,2353 | Werkelijke laad-/bewaarroute en metadata.plannedExercises/effortTracking. Snapshotdata bestaat; gezaghebbende historische doel-/regel-/unitversie is niet daarmee bewezen |
| S04 | supabase/migrations/20260908100106_training_workout_editor.sql:48; 20260909215122_training_plan_effort_tracking.sql:3 | Member-owned atomic save met updated_at-conflict en save-ID; geen trainergoedkeurings- of AI-applyprotocol |
| S05 | supabase/migrations/20260901183914_phase6a_ai_trust_foundation.sql:127,157,174,490 | Voorstel-/decision-/safetyfundering. Bestaande action/status-enums en eigen-lid policies zijn geen passend volledig 6E-contract |
| S06 | supabase/functions/youri-ai/index.ts:149; phase6d-handler.ts:222 | Bestaande bearer/member/service-RPC-routes en read-only analyse-output met actions=[]; geen 6E-apply/undo-endpoint |
| S07 | assets/phase6d-analysis-inbox.js:105,176; supabase/migrations/20260906092905_phase6d_automatic_inbox.sql:27 | Memberinbox uitsluitend analysis_ready met verplichte analysis_id, geen trainerproposal/outbox |
| S08 | supabase/migrations/20260902045834_phase6b_provider_privacy_cost_gate.sql:7-60 | Git-contract voor ZDR/DPA/DPIA/EU/consent/lifecycle/owner-GO; actuele live waarden niet opnieuw gelezen |
| S09 | docs/PHASE6E0_OWNER_DECISIONS.md; PHASE6E1_FREEZE_RECEIPT.md | D1-D12/O1-O5 blijven leidend; geen algemene gezondheidsblokkade, geen medische menselijke aanvraagdienst |
| S10 | assets/training-workout-model.js:1; training-workout-ui.js:195 | Compacte settargets, onafhankelijke RIR/RPE. Geen AI-invoeradapter of versiegebonden trainerregelbeheer |

S04 mag later niet blind voor AI-apply worden aangeroepen: hij vereist een client-
actor, accepteert brede editorvelden en bewaart geen twee onafhankelijke goedkeuringen.
Het oude handmatig bewerken van een eigen schema blijft buiten de AI-goedkeuringsflow;
P2/W1/W2 geven GEEN GO om die bestaande rechten globaal in te trekken.
Een toekomstige AI-route mag die handmatige route niet als goedkeuringsomweg gebruiken.

## Volledige Resterende Werkvoorraad

O = veilig offline uitwerkbaar; M = synthetische stagingmock na GO;
T = echte stagingdienst vereist technisch integratiebewijs; E = inhoud/privacyreview waar relevant.

| ID / functie | Al aanwezig | Exact ontbrekend resultaat | Volgorde / afsluitbewijs |
| --- | --- | --- | --- |
| R01 Reps/gewicht/behoud | 6E-5/6 berekening, bronregels, concrete teksten | Readmodel/UI-contract dat per oefening plan/actual/next/reason/status EN bij blokkade ingestelde stap/unit toont; geen alternatief. step_off_grid geeft nu facts_only/weight_step_conflict maar geen numerieke stap/rule_provenance | O -> M; exacte NL/EN/DE-diff-/foutvoorbeelden. T pas met R02/R03/R06 |
| R02 Trainerregels | Offline rulebook/selector/versies | Geauthenticeerd trainerbeheer, effectieve relatie, bevoegdheid, geldigheid/intrekking, doel-/schemabinding en gecertificeerde readset. Expliciete prioriteit bestaat nog niet; zonder nieuw contract alle overlap blokkeren | O contract -> T schema/RLS/actor/intrekkingsracebewijs; echte normen E |
| R03 Betrouwbare bronnen | Plan/session/setlogs en snapshots | Server-attested versies en units op capture, historische doel/plan/regelbinding, complete vensters en catalogus/variant/apparaat-ID; geen terugdateren uit huidige onboardingdoelen | O fixtures -> T coherente capture/revisionadapter; ontbrekende oude bron blijft onbekend |
| R04 Lidacceptatie | Opaque testactor en aparte status | Eigen-lid UI met volledige diff, expliciete bevestiging/reject, voorstelhash/revisie/consentbinding en actuele sessiecontrole | M bediening; T twee echte gescheiden testidentiteiten + herlogin/revoked-consent tests |
| R05 Trainergoedkeuring | Aparte offline actor/status | Geautoriseerde trainerinbox, eigen relatie/rol/statuscontrole, bevestiging exact dezelfde versie, geen client-geselecteerde actor | M persona is alleen simulatie; T cross-member/trainer/RLS- en revoke-races |
| R06 Afzonderlijk toepassen | In-memory aggregate-CAS, idempotency, vorige plan/audit | Beperkte commandroute en echte transactionele RPC met locks, versiecontrole, beide signatures, actuele bronnen/rechten/safety en commit van plan+audit+outbox+idempotency in EEN transactie | O adversarial contract -> T transactiefouten/herstart/twee verbindingen/timeout-after-commit |
| R07 Blokkeren/afwijzen | Terminal reject, needs_recheck, safetygate | UI van redenen/nieuwe beoordeling, server-side terminaliteit, geen verborgen apply bij stale bron; geen verplichte verduidelijkingslus | O/M direct; T actuele context-/consentversie wordt bij commit opnieuw gecontroleerd |
| R08 Terugdraaien | Vorige schema's alleen bewaard | Compensating-revision-contract, rollbackdiff, rechten/goedkeuring, CAS, idempotency, audit en conflictscenario na latere wijziging; geen destructieve historische rewind | NIEUW ownerkeuzepunt K2; O/M eerst; T aparte restore-RPC. Geen medisch herstel door rollback |
| R09 Meldingen | analysis_ready voor lid | Proposal-eventoutbox voor lid EN actuele trainer, dedupe, read/dismiss/retry, revoke-/expiry-filter, privacyveilige tekst; geen fictief analysis_id of healthchatdeling | NIEUW K3; M twee mockinboxen; T transactionele outbox en least-privilege readmodel |
| R10 Zonder trainer | Facts-only, geen plan_option | Eind-tot-eind UX voor geen/verloren relatie, bestaande resultaten onder eigen rechten, accept/apply onmogelijk, geen generiek FMZ-regelfallback | O/M/T expliciete tests; geen nieuw productbesluit over trainerverplichting |
| R11 Safety/herstel | Contextbinding/O5/voorlopige labels en conservatieve proposalstop | Adapter naar actuele runtime-safetystate zonder brede toegangssperre; betrouwbare taal/contextdekking; ernstige/terugkerende/oningedeelde klachten en persoonsgebonden hervatting | O/M technische flows kunnen door; echte herkenning/advies/hervatting E + T, geen criteria verzinnen |
| R12 Consent/privacy/retentie | Events/revisies, privatechat/analysis-lifecycle, offline O5 | Nieuwe doelen/ontvangers/fields/termijnen voor voorstellen/approvals/audit/outbox; withdrawal/deletion/export/backuprestore/racebewijs. O5 geen forever-status/sentinel | O schema/testontwerp; T + E voor echte data; geen automatische 30/90/180-copy naar elk nieuw object |
| R13 Kosten/provider | Mock, reservering en providerprivacyfundering | Bewijs actuele org/project/model/endpoint/featuretoelating, budgetreservering/finalisatie/caps/alerts/kill-switch en afzonderlijke live-GO | Geen provider nodig voor reps/gewichtsregels; 6E-7 0 calls/EUR0. Eventuele latere taalprovider apart T/E |
| R14 Operatie/release | Bestaande Pages/hashgates | Afgebakende releasemanifesten, lokaal reproduceerbare additive SQL-chain, staging schema/RLS-diff, monitoring zonder inhoudlek, incidenthandleiding en rollbackdrill | M isolatie; T voor echte dienst. Oude migrationreconciliation niet heropenen |
| R15 Overige Phase-6E-ambitie | Dag/workout/week-feiten en beperkte niet-fysieke reflectie | Persoonlijke voeding/herstel/meer trainingscategorieen, FR/IT en lokale hulp-/taaldekking nog geen gereviewde live scope | Niet in 6E-7. Aparte inhouds-/productkeuzes en deskundige reviews; geen compleet 6E claim |

Datamodelverschillen zijn concreet: huidige planreps kunnen tekstbereiken zoals 8-10
zijn; frozen progressie vereist uniforme point-targets. Huidige legacy gewichtkolommen
zijn numeric(7,2), terwijl 6E-6 synthetisch tot zes decimalen kan valideren. Units zijn
niet bewezen immutable per bron. Geen 0,125 stilzwijgend naar 0,13 schrijven of
huidige gebruikersvoorkeur als historische eenheid nemen. Later eerst expliciet
compatibel opslag-/weergavecontract; bestaande waarden niet omzetten/backfillen.
RPE-formatteringsgrenzen kunnen eveneens verschillen; ongemerkte normalisatie verboden.

## 1. Veilig Offline Verder

Uitvoerbare workflowreadmodels en vaste foutteksten (R01), rollback/notification-
contracten (R08/R09), transactie- en bron-/auth-interfaces met synthetische actors,
doelgebonden lifecyclecases, security-/concurrencytestontwerp en compacte UI-mocks.
Ook bronvormadapters voor ranges/precisie mogen uitsluitend afwijzen/uitleggen totdat
een passende scope is gekozen. Geen deskundige medische review nodig om een CAS,
dedupe of ongemodificeerde RIR0-test te programmeren.
Geen mutatie aan frozen 6E-0..6E-6; nieuwe adapter en bewijs in nieuwe scope.

## 2. Stagingmock Zonder Externe AI Of Echte Leden

Aanbevolen: apart herkenbaar synthetisch demo-oppervlak, met vaste fixtures en
lid-/trainerpersonas, geen appauth, Supabaseclient, imports van frozen offlinecode,
AI-provider, upload of vrij tekstveld voor persoonsgegevens.
Test klikken, aparte akkoordstappen, blokkades, afwijzen, mockapply/restore,
twee mockinboxen, mobiele layout en reset/verversen. Geen RLS-/live trainerbewijs claimen.
Publieke demo mag alleen reeds bedoelde synthetische voorbeelden bevatten;
de app en bestaande 60 assets blijven ongewijzigd. Separate GO voor publicatie nodig.
Een LATERE echte servermock met synthetische accounts is een aparte scope:
daarvoor zijn auth, dedicated fixture-isolatie, RLS en additive SQL nodig,
maar nog steeds geen provider. Browser-personas vervangen die controle nooit.

## 3. Nieuwe Ownerbeslissingen

| Keuze | Concreet voorstel | Niet hiermee beslist |
| --- | --- | --- |
| K1 Volgende scope | 6E-7 alleen uitvoerbaar offline workflowmodel plus zelfstandige synthetische stagingdemo | Geen app/Edge/DB-integratie, echte accounts of leden |
| K2 Rollbackproductflow | Beide partijen bevestigen een zichtbare restore-diff; aparte trainer-apply maakt nieuwe revisie op exact actuele versie. Bij conflict blokkeren | Geen auto-undo, geen terugschrijven van historie, geen medische vrijgave |
| K3 Meldingen | In 6E-7 alleen twee mockinboxen met voorstelstatus, geen email/push/chat- of gezondheidsinhoud | Voor echte ontvangers later kanaal-/deelgrondslag en actuele relatiecontrole |
| K4 Mocklevensduur | Alleen geheugen; verversen/reset begint bewust opnieuw met fixture, geen webstorage van appdata | Geen bewijs van duurzame herstart/idempotency; nieuwe bewaartermijnen blijven open |
| K5 Latere echte bron-/datareikwijdte | Voor een later serverpakket eerst exacte velden/ontvangers, serverbronversies en doelgebonden retentie afzonderlijk besluiten | Geen nieuw bedrag, algemene FMZ-trainervervanger of prioriteitsnorm nu |

W1/W2/P1-P3/D1-D12/O1-O5 blijven geaccepteerd. Er wordt niet opnieuw gevraagd of
trainerakkoord nodig is. De uitzondering voor expliciet vastgelegde prioriteit
is GEEN automatisch ondersteunde rulebookfeature. K1-K4 zijn voor 6E-7; K5 is later.

## 4. Deskundige Reviews

Medisch/trainingsinhoud: de echte min/max/stap/N/effortregels en toepassingspopulatie,
stop-/hulpteksten, foutpositieven/missers, onvoldoende/terugkerend herstel en gevolgen
van gewijzigde schema's/restore. Een trainerlink of ownerakkoord valideert geen kliniek.
Privacy: bronminimalisatie, doelen/ontvangers, relation-loss, consentwithdrawal,
verwijdering/export/retentie en minimale audit. Auditimmutable is niet eeuwig bewaren.
Juridisch: rollen/aansprakelijkheid, bedoelde toepassing en claims, eventuele relevante
zorg-/productregelgeving en geautomatiseerde besluitvorming beoordelen; geen risicoklasse
of wettelijke vrijstelling door deze audit. Taal: NL/EN/DE-context/conceptcopy en
latere talen/landkeuze; bekende misser en historische handmatige context blijven open.
Geen deskundigen benaderd. Een verplichte menselijke medische aanvraagdienst is verboden
productaanname; technische trainergoedkeuring is een andere, reeds geaccepteerde functie.

## 5. Echte Leden: Gescheiden Privacy- En Providergates

**Eerste-partijverwerking is niet automatisch een externe AI-call.**
Geauthenticeerde eigen trainingrecords lezen/schrijven heeft eigen privacy-, security-
en productvoorwaarden. Voor nieuwe 6E-functionaliteit is de bestaande toestemming
voor 6D niet stilzwijgend voldoende. Geen echte data gebruiken in een mock.
Als er GEEN providerverkeer is, is OpenAI-ZDR geen technisch vereiste om code te bouwen;
dit is GEEN ontheffing van bestaande privacyflags of toestemming voor echte 6E-data.

**Voor nieuwe verwerking van echte ledengegevens:** beschrijf doel en minimale velden,
rechtmatige basis en eventuele bijzondere-gegevensvoorwaarde, ontvangers/rollen,
doelgebonden bewaring en intrekking, privacytekst/versiegebonden toestemming,
rechten/export/delete en verantwoordelijke. Benoem DPA hier als Data Processing
Agreement/verwerkersovereenkomst, niet de toezichthouder. Contractuele processorrollen
en instructies moeten vastliggen. [Europese Commissie: rollen en verwerkers](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/application-gdpr_en).

Een DPIA moet aan risicovolle nieuwe verwerking voorafgaan; ook de gekozen mitigerende
maatregelen en resterende risico's moeten beoordeeld zijn. De projectgate verlangt
DPIA-completion en goedgekeurde copy; deze audit vult die statussen niet in.
Toestemming is niet hetzelfde als trainerakkoord, lidacceptatie of owner-GO.
[Europese Commissie: informatieplichten en DPIA](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/obligations_en).

**Daarbovenop, VOOR enige externe AI-call met echte data:** account-/projectspecifiek
ZDR-bewijs, geschikte route/model/endpoint/features, verwerkersafspraken/subverwerkers,
EU-route en doorgiftebeoordeling, payloadallowlist, veilige logging/lifecycle,
kostencaps en expliciete owneractivatie. De code vereist onder meer zdr_verified,
alle completionvelden en https://eu.api.openai.com/v1/responses (S08).
store:false alleen bewijst geen ZDR; regionale verwerking en opslag/metadata zijn
afzonderlijke controles. De actuele documentatie noemt voor niet-US-gebruik
geschiktheid voor monitoringcontrols en een Modified Retention-amendement;
FitMetZorge's strengere ZDR-eis wordt hierdoor niet versoepeld. Verifieer het
daadwerkelijke project en iedere gebruikte feature, geen defaultmodelroute aannemen.
[OpenAI Data Controls, gecontroleerd 2026-09-11](https://developers.openai.com/api/docs/guides/your-data).

Geen provideraccount of juridische dossierstukken geinspecteerd; dus geen actuele
ZDR/DPA/DPIA/EU-goedkeuring bewezen. Oude historische unverified/incomplete-uitkomsten
blijven historisch. Maak later een bewijsregister met reviewer/eigenaar, scope/versie,
datum, bewijsreferentie en herbeoordelingstrigger; niet een vinkje zonder bewijs.
EUR-Lex/AP/enkele EDPB-pagina's waren bij directe opvraag beperkt; bovenstaande
geopende officiele Commissie-/OpenAI-bronnen zijn gebruikt, geen juridische eindbeoordeling.

## 6. Welke Blokkade Raakt Wat?

| Blokkade | Wat geblokkeerd blijft | Wat technisch verder kan |
| --- | --- | --- |
| Medische/hervattingscriteria onbekend | Nieuwe echte fysieke progressie/hervatting in die context, geen traineroverride | Offline/mock akkoordstatussen, feitenweergave, versiebeheer, audit, notificatiestatussen en conflict-/undo-tests |
| Beperkte taalherkenning | Geen claim dat R0 trainingsgeschiktheid of volledige klachtdekking bewijst | Nieuwe vaste bron-/workflowfuncties; onbekende taal fail-closed, optioneel verduidelijken en verder chatten |
| ZDR/EU/provideraccount nog niet bewezen | Extern providerverkeer met echte data | Deterministische berekening uit synthetische expliciete regels; mock UI; geen provider nodig voor getallenkeuze |
| DPA/DPIA/grondslag/consent/retentie open | Nieuwe verwerking of deling van echte ledengegevens in deze scope | Ontwerp, synthetische tests en demo zonder echte gegevens; geen stille reuse van bestaande consent |
| Echte auth/RLS/concurrency niet getest | Iedere claim dat live apply/restore veilig is | Browsermock en lokale transactionele testvoorbereiding, als simulatie gelabeld |
| Geen gekoppelde trainer | Geen toepasbare schemawijziging via Youri | Betrouwbare eigen feiten en eerdere resultaten onder bestaande rechten; geen gezondheidsgerelateerde abonnementsblokkade |
| Voorstel stale/rejected/expired | Het betreffende voorstel toepassen, niet de gehele app | Chat/historie en nieuwe beoordeling met echt nieuwe bronnen; geen oude handtekeningen overnemen |

Geen van deze scheidingen geeft nu integratie-GO. Niet-medische ADMINISTRATIEVE
functionaliteit kan veilig als mock verder; lichamelijk belastende aanbevelingen
zijn niet automatisch niet-medisch veilig omdat de wiskunde deterministisch is.
Ook rollback kan een oude zwaardere belasting terugzetten: geen safetyomweg.

## Pad Naar Veilige Stagingbeschikbaarheid

1. K1-K4 beantwoorden en afzonderlijke GO voor [6E-7](PHASE6E7_PROPOSAL.md):
   klikbare synthetische workflow plus W2-detail/restore/notificatiecontract.
2. Na die ownerretest een apart serverintegratiepakket afbakenen:
   versioned readsets/rules/proposals/approvals/commands/outbox en eerst lokale SQL/RLS-tests.
3. Daarna uitsluitend eigen synthetische stagingfixtures onder echte gescheiden
   auth-identiteiten, zero provider egress, concurrency/rollback/lifecycle en schema-
   behoudsproeven. Geen echte leden of automatisch trainerlinken.
4. Echte-data- en inhoudsgates per functie aantoonbaar afronden, daarna expliciete
   beperkte real-member staging-GO. Medische onderdelen blijven dicht waar criteria ontbreken.
5. Een externe taalprovider is optioneel en een aparte gate; nooit bron van
   gewichtsstappen, trainerautoriteit of toepassing. Geen betaalde test nu.

De volledige beschikbaarheid vergt dus meer dan de offline freeze of een mooier scherm.
Alleen de huidige docs-only freeze/audit/voorstel worden opgeleverd; geen volgende stap gestart.
