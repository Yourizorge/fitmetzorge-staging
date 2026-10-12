# 6E-11 afgeschermde synthetische testcontroller

12 oktober 2026. **NO-GO voor hosted workflow en ownertelefoontest.**
De eerder bewezen hosted Edge-verbinding blijft PASS. Deze opdracht levert
geen nieuwe owneracceptatie of freeze op; 6E-21 blijft ongeaccepteerd.

## Gebouwd en lokaal bewezen

De nieuwe offline controllercomponenten staan in
`_offline/phase6e11/controller_v1/`. Ze bevatten exacte GitHub-OIDC-binding
aan repository, main-SHA, workflow, run, attempt en maximaal tien minuten;
vaste synthetische identiteits-/werkruimte-/actiecontrole; duurzame eenmalige
runregistratie; geordende meetparen; gesanitiseerde foutafhandeling; en
onafhankelijke controle van request, sessie, transactie en writeset.

Ontbrekende, dubbele of extra auditregels blokkeren. DELETE-bewijs blijft
aanwezig als gehashte oude rijsleutel. Een lege, gestopte of incomplete run
kan niet als `complete` worden afgesloten. Geen publieke RPC of clientgrant.
Het concrete ontwerp en de rechten staan in `PHASE6E11_CONTROLLER_DESIGN.md`.

| Controle | Resultaat |
|---|---|
| Controller/OIDC/Auth-helper/manifest/writeset, netwerk geblokkeerd | 143/143 |
| Installer, 155-tabellentransport en JIT-foutfase | 22/22 |
| Duurzame bewijsopslag, echte lokale PostgreSQL 17 | 62/62 |
| Bestaande request-/securityregressies | 33/33 |
| Bestaande Route A/B-productfuncties, lokale driver | 45 complete meetparen |
| Schone Supabase-container, migrations 1-43 | 43/43 PASS |
| SQL-regressiebestanden in CI | 12/12 |
| CI-dry-run | leeg, uitsluitend lokale CI-database |

De 63 CI-Node-tests overlappen de 143 lokale tests; niet dubbel opgeteld.
Auth-responses in lokale tests zijn stubs. De 45 meetparen zijn geen hosted
Auth-, lifecycle- of ownerbewijs. De laatste CI staat op
[run 38243722556](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38243722556).
CLI 2.117.0; PostgreSQL 17.6; image
`public.ecr.aws/supabase/postgres:17.6.1.167`, digest
`sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb`.
Geen echte ledengegevens of stagingcredentials in CI.

## Hosted verloop

1. De eerste M43-voorcontrole opende de bewezen native session-poolerroute met
   officiele CA, hostnamevalidatie, `verify-full`, tijdelijke owner-JIT en een
   expliciete read-onlytransactie. De database meldde PostgreSQL 17.6 en 42
   migrations. Na 18 SQL-commando's stopte de adapter **voor** DECLARE/FETCH:
   de frozen transportgrens was 153 tabellen, terwijl M42 twee tabellen had
   toegevoegd, totaal 155. Rollback bevestigd; JIT ingetrokken.
2. Een afzonderlijke adapter ondersteunt precies die 155 tabellen, zonder
   frozen code, hashmethode of rij-/geheugen-/IO-limieten te veranderen. Negen
   lokale transportregressies slagen. De oorspronkelijke poging blijft incompleet.
3. Een eenmalige oorzaakgerichte correctiepoging werd al bij tijdelijke
   JIT-toegang geweigerd: **Management API HTTP 406**. Er werd daarbij geen
   databaseverbinding geopend en geen SQL uitgevoerd. Geen verdere herhaling.

De oude JIT-helper bewaarde niet welke enable-/roltoewijzings-/bevestigingscall
406 teruggaf. Daarom is de onderliggende platformoorzaak niet bewezen. Dit is
geen bewijs van een ongeldig wachtwoord of een teruggekeerde poolertime-out.
Nieuwe, lokaal geteste fasejournalisering bewaart die onderscheiden voortaan
zonder geheime waarden; zij is niet alsnog hosted uitgevoerd.

Beide afsluitingen zijn vastgelegd. Laatste bevestiging:
`2026-10-12T11:29:12.814862Z`, JIT `disabled`, actieve mappings `0`,
SSL-enforcement `true`. Geen geheimreset, beveiligingsverlaging of omzeiling.

## Migrations, IO en databehoud

- Migration 43 is additief: drie lege private bewijstabellen met RLS en zonder
  publieke functies of clientrechten. Lokaal/CI getest en in Git vastgelegd,
  **niet hosted toegepast**. Lokaal 43; hosted laatst vastgesteld 42.
- SHA-256 M43:
  `bab79b7ca5876c2dcef055d0e95997595772aebc051283e69bbeb2ca1dc4bd57`.
  Geen hosted SQL-hash of nieuwe lege hosted dry-run geclaimd.
- Metadataqueries voor observerregister en catalogus: beide nul eigen
  tijdelijke blocks gelezen/geschreven, respectievelijk 11,69 en 277,17 ms.
  De complete collector-/databehoudscyclus is niet voltooid; geen algemene
  IO-PASS of volledig hashmeetpaar afgeleid uit deze deelmetingen.
- Eerste poging 18 werkelijke SQL-commando's, tweede poging 0. De 40
  CLI-commando's waren alleen reserveringen; de CLI heeft geen migration
  uitgevoerd. Het canarybudget blijft 128; er is geen workflowcanary gestart.
- Nul Auth-calls, applicatie-/ledenwrites, nieuwe fixtures of fixturecleanup.
  Tijdelijke JIT-configuratie is wel gecontroleerd aan-/uitgezet.
- Alle 1376 vooraf geregistreerde bronbestanden zijn ongewijzigd, inclusief
  oudere werkboomwijzigingen. Historische 112 meetparen, incomplete stap 113,
  migrations 1-42 en eerdere bewijzen blijven behouden.

## Niet afgerond

Er is nog geen muterende controller gedeployed. De definitieve servermanifest-
en fixture-lifecycleaansluiting, scoped Auth-meetadapter en end-to-end
controlleruitvoering zijn nog niet bewezen. De bestaande 45 workflowpaden
zijn lokaal beschikbaar, niet als volledige hosted keten vrijgegeven.

Hosted Auth, request-/auditbinding, Route A/B, goedkeuren/toepassen, conflicten,
terugzetten, cleanup/DELETE en afsluitend beschermd databehoud blijven open.
Een werkende verbinding of private lege opslag vervangt geen van deze bewijzen.
Geen ownervenster geopend; geen 6E-12-serverintegratie gestart.

## Concrete volgende stap

Eerst de JIT-406 aan een specifieke Management-API-requestfase en verklaarbare
platformvoorwaarde koppelen, zonder nieuwe automatische grantpogingen of
beveiligingsverlaging. Daarna een nieuw begrensd admissionrecord vastleggen;
oude markers niet verwijderen. De voorbereide schone CI- en lokale bewijzen
blijven bruikbaar zolang hun bronhashes exact overeenkomen. Pas na een geldige
M43-voor-/nameting volgt de afgeschermde synthetische workflowcanary.

Commits, bronhashes en lokale bewijsverwijzingen staan in
`PHASE6E11_CONTROLLER_EVIDENCE.json`; de afsluitende publicatiereceipt volgt
afzonderlijk. Er zijn geen werkende runtime- of Edge-bestanden gepubliceerd.

External AI calls/cost: **0 / EUR 0,00**.
Real-member AI enabled: **NO**. Production touched: **NO**.
