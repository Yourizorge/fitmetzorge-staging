# 6E-11 extra Edge-proef: verbinding PASS, workflow nog NO-GO

12 oktober 2026. Dit is een aanvulling op de behouden resumption-, M42- en
supportrapporten. De nieuwste owneropdracht vervangt de eerdere supportwacht;
een antwoord op SU-487979 is geen vereiste meer voor technisch vervolg.
Baseline main: `ea77e48cb16e50178cf43508fd14e2f2f9a6be40`.

## Hosted bewezen

De afzonderlijk toegestane extra poging is geslaagd:
[CI-run 38234059128](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38234059128).
Geen hergebruik van het eerder opgebruikte budget, geen automatische retry.

| Bewijs | Resultaat |
| --- | --- |
| Verbinding | Een IPv4 session-poolerverbinding, poort 5432 |
| Driver | Deno-native Postgres.js 3.4.7; max:1; prepare:false; fetch_types:false; geen voorafgaande reserve() |
| TLS | Officiele CA en hostnamecontrole in DEZE poging; handshake bevestigd op 262 ms |
| Authenticatie | BEGIN-bevestiging op 1388 ms; niet uitsluitend afgeleid uit TLS |
| Transactie | Expliciet BEGIN TRANSACTION READ ONLY; readonly=true; hetzelfde backendnummer |
| Projectbinding | Exacte verwachte instance-fingerprint en database-/rolcontrole |
| SQL | Vier bevestigde commando's: BEGIN, guard, identity, ROLLBACK |
| Einde | ROLLBACK bevestigd op 1651 ms; driver gesloten; totaal 1652 ms |
| Toegang | Exact main/commit/run/attempt-1 OIDC; uiterste vervaltijd 12:14:59 CEST |
| Sluiting | Exacte tijdelijke functie verwijderd om 12:07:53 CEST; management GET 404 |
| JIT | Uitgeschakeld, nul mappings; voor de Edge-proef niet geopend |

De voorheen lokaal gereproduceerde eerste-reserve-startfout wordt met de
ongewijzigde read_only.mjs-correctie ook hosted vermeden. Dit bevestigt deze
drivercorrectie; het bewijst niet dat iedere oudere time-out dezelfde oorzaak had
of dat Supabase een algemeen poolerprobleem heeft opgelost.

De bestaande applicatie-Edge `fmz-phase6e11` op staging blijft versie 2;
zijn hash en die van de vijf overige stagingfuncties zijn gelijk aan de nulmeting.
Alleen de tijdelijke diagnosefunctie is gedeployed en vervolgens verwijderd.
Geen databasegeheim, Auth-token, sessie of inloglink is teruggegeven.

## Begrensde vervolgcontrole

Na de verbindings-PASS is een aparte read-only metadata-admission uitgevoerd
via de reeds bewezen native verify-full/JIT-route. Een collector, maximaal
32 commando's, 120 seconden, geen retries. Werkelijk: 13 commando's, nul volledige
fingerprints. JIT is daarna direct ingetrokken; ROLLBACK is bevestigd.

- Alle 42 migration-identiteiten en geregistreerde statementhashes zijn gelijk
  aan de vorige geslaagde native meting. M41 en M42 zijn niet gewijzigd/herhaald.
- Vijf M42-functies: SECURITY INVOKER en vaste veilige search_path. Twee tabellen
  met RLS. Geen schema-USAGE of functie-EXECUTE voor anon/authenticated/service_role.
- Alle drie geregistreerde synthetische identiteiten, rollen en trainerkoppelingen
  kloppen; alleen de bestaande synthetische A-trainer is operator.
- Nul actieve vensters, workspaces, request-receipts, audit-runs of pending intents.
  Request- en workflow-auditcontrols blijven uit. De bestaande proof is aanwezig.
- Querygebonden eigen temp reads/writes: nul bij deze native metadata-/bewakingsquery's.
  Achtergrond-tempdelta in dit korte venster: nul. Langdurig Disk-IO-herstel wordt
  hiermee niet geclaimd; Edge-queryspills zijn niet apart gemeten.

De nieuwe admissionteller verwachtte aanvankelijk 62 TOTALE observers en stopte
op 64. De complete meting is bewaard als NO-GO. Migration 40 bevat expliciet twee
eigen auditfixtures; daarnaast staan precies 62 applicatie-observers geregistreerd.
Een afzonderlijke offline review verifieert de complete nameting, loadprofielen,
beide exacte fixturenamen en ongewijzigde migrations. De inhoudelijke metadata-
admission is daarmee PASS zonder nieuwe hosted query. De oude stop is niet gewist.
Dit is geen nieuwe volledige triggerbody-/write-coverage- of beschermde-datameting.

## Tests en behoud

- 175 gerichte Node-tests en 25 Python-tests: 200 PASS, nul failures.
- Aanvullende uitvoering van de metadataquery op lokale PG17-fixtures: PASS.
  Dit is geen nieuwe lege opbouw van alle 42 migrations; het bestaande CI-bewijs blijft gelden.
- 1366 reeds aanwezige bronbestanden en 465 historische bewijsverwijzingen ongewijzigd.
  De 112 historische geldige paren en incomplete stap 113 blijven historisch bewijs.
- De eerder behaalde 4947 frozen regressies zijn niet opnieuw uitgevoerd omdat
  de frozen bronnen en applicatieruntime niet zijn gewijzigd.
- Beide hosted transacties waren read-only. Geen applicatie-/ledenwrites, Auth-acties,
  fixturewrites of fixturecleanup. Geen nieuwe globale fingerprint; gelijktijdige
  niet-gerelateerde activiteit is daarom niet gecertificeerd afwezig.
- Een nieuwe CLI dry-run en volledige hosted workflows zijn nog niet uitgevoerd.

Bronhashes, exacte fasegebeurtenissen en lokale evidencebindingen staan in
[het aanvullende bewijsmanifest](PHASE6E11_EXTRA_EDGE_EVIDENCE.json).
De zelfvoorzienende offline receipt-validator kan een verbindings-PASS nooit
promoveren tot workflowvrijgave. Private operatorharnassen blijven lokaal;
alleen de validator/tests en gesanitiseerde documentatie worden gecommit.

## Exacte resterende grens

De bestaande GitHub-OIDC-toegang is uitdrukkelijk ALLEEN read-only goedgekeurd.
Zij mag niet stilzwijgend Auth-sessies of workflowmutaties gaan uitvoeren.
De oude secret-exporterende controller wordt niet hergebruikt. Secrets worden
niet uit Edge gehaald en echte leden/accounts blijven buiten scope.

Er is een gebundeld ownerbesluit gevraagd voor een afzonderlijke standaard
gesloten testcontroller, exact een CI-run en maximaal tien minuten: uitsluitend
de drie geregistreerde synthetische accounts en vooraf geteste acties, met
server-side secrets, meetparen en audit, daarna verwijdering. Nog niet gedeployed.
Dit is een nieuwe toegangsgrens, geen herhaalde vraag om routine-toestemming.

Na dit besluit: eerst die controller lokaal/CI bewijzen, verse beperkte Auth-
contracten en writesets binden, dan de minimale canary (een collector, maximaal
drie cycli/128 commando's, geen retries). De volledige 45-case proofrun blijft
een afzonderlijk begroot vervolg; niet in een te klein canarybudget persen.
Auth-uitgifte/verificatie/refresh/logout en de werkelijke A/B-request-/auditparen,
apply/restore/afwijzen/blokkeren/conflict, beschermde data en synthetische DELETE/
cleanup moeten nog hosted worden bewezen. Onbewijsbare Auth-routes blijven dicht.

Daarna pas publicatie van bewezen runtime en een begrensd ownertelefoontestvenster.
De duurzame synthetische 6E-12-registratie blijft afhankelijk van de VOLLEDIGE
6E-11-keten; geen bundelactivering van 12-20. 6E-21 blijft ongeaccepteerd.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.

Officiele bronnen opnieuw gecontroleerd op 12 oktober 2026:
[Supabase changelog](https://supabase.com/changelog),
[Postgresverbindingen](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Edge en Postgres](https://supabase.com/docs/guides/functions/connect-to-postgres),
[Auth-sessies](https://supabase.com/docs/guides/auth/sessions).
Een JWT alleen is geen bewijs dat een sessie na logout nog actief is: de live
session_id-controle blijft onderdeel van de nog vereiste Auth-proef.
