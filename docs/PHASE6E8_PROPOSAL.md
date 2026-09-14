# Package 6E-8 Proposal

## Superseding Owner GO: Dual Route (2026-09-13)

The owner accepted 6E-7 physically and authorized revised 6E-8, Decision 0049.
The historical proposal below is retained for traceability; its NOT STARTED wording
and single-route scope are superseded. See PHASE6E8_OWNER_OVERVIEW.md and
PHASE6E8_TECHNICAL_REPORT.md for the implemented dual-route synthetic panel.
Only index.html changes in the existing runtime; 59 other legacy assets and 141
frozen sources remain protected. Independent AI membership is a separate fictional
eligibility route, never a missing-trainer fallback. No live auth/data/provider GO.
The next proposal is PHASE6E9_PROPOSAL.md, PROPOSED / NOT STARTED.

PROPOSED / NOT STARTED. Dit document geeft GEEN implementatie-GO.
Enig aanbevolen vervolg: **Afgeschermde synthetische mockintegratie in de echte
stagingapp**, na ownerreview van 6E-7.

## Resultaat

Een expliciete demo-ingang in de bestaande stagingapp die de 6E-7-workflow als
afgeschermd synthetisch paneel toont. De volledige lid/trainer-review, toepassing,
restore en minimale meldingen blijven in memory. Geen echte schema-, account- of
gegevenskoppeling; geen externe AI. Dit test samenhang met navigatie, thema,
mobiele viewport en terugkeer naar Training, niet echte servertransacties.

Geen nieuwe algemene audit en geen heropening van D1-D12/O1-O5 of latere besluiten.
Medische/privacy/juridische/taalreview blijft open voor latere echte verwerking.
De bestaande fysieke timer-/RIR-/RPE-acceptatie blijft geldig en wordt niet vervangen
door een synthetische browsertest.

## Gegevensstroom En Componenten

1. De eigenaar opent een expliciete synthetische route/ingang in staging.
   Geen standaardlid krijgt stilzwijgend een nieuw trainingsvoorstel.
2. De app toont een apart sandboxed iframe met de bestaande standalone democode.
   Voorgestelde grens: sandbox=allow-scripts, ZONDER allow-same-origin, forms,
   popups, downloads of top-navigation. Geen toegang tot parent DOM, cookies
   of appstorage. Dit moet in de echte browser worden bewezen, niet aangenomen.
3. Alleen allowlisted taal/thema als niet-persoonlijke initiële URL-parameters.
   Geen lid-ID, JWT, authsession, chat, setlogs, doel of schema vanuit de app.
   Geen generieke postMessage-commandbus of toepassing vanuit de parent.
4. De demo gebruikt uitsluitend de gecontroleerde publieke synthetische fixtures.
   Wisselen van route/verversen mag de mock resetten; dit blijft zichtbaar.
5. Terugkeer sluit de mock zonder appdata te schrijven of Training te veranderen.

Frontend: een kleine expliciet benoemde ingang/route en afgeschermde container.
De exacte betrokken bestaande runtimebestanden worden VOOR wijziging geselecteerd,
in een beperkt behoudsmanifest vastgelegd en uitsluitend na nieuwe owner-GO aangepast.
Alle andere runtime-assets en frozen 6E-0..6E-6 blijven byte-identiek.
6E-7 wordt niet automatisch frozen; na owneracceptatie eerst zijn eigen bronreceipt.

Edge/Auth/RLS/database: GEEN wijzigingen of aanroepen nodig voor dit pakket.
Geen mock-data opslaan in bestaande ledentabellen. Geen servicekey, provider of
goedkeuringsvlag aanzetten. De huidige appauth blijft ongewijzigd; voor de test wordt
een volledig synthetische testharness gebruikt. Real-member API-verkeer tijdens de
mocktest is een testfout, niet een te accepteren gevolg van de appbootstrap.

## Beveiliging En Tests

- Browser-evidence voor iframe-isolatie, geweigerde parent-/storage-/navigatietoegang,
  geen provider-/database-/Edge-egress en geen echte context in URL/logs.
- Geen permissies voor top-navigation, popups of downloads; restrictive CSP behouden.
- Regressies van het exacte 6E-7-workflowcontract, incl. cross-proposal binding,
  W1/W2, dubbele commando's, consent-/versieconflicten, restore en neutrale inbox.
- Appnavigatie heen/terug en herhaald openen maakt geen dubbele mock of listener.
- Geen verslepen van echte Training-state, timers, schema's, setlogs, RIR/RPE of
  sessiesnapshots; hashbehoud plus gerichte bestaande Training-regressies.
- NL/EN/DE, licht/donker, 320/390/768/1280 px; keyboardfocus, iframehoogte,
  scrollherstel en screenshots. Fysieke telefoontest blijft een aparte ownerretest.
- Negatieve URL-parameters, iframe-inhoud op onbekend origin, geweigerde egress en
  browser zonder toegestane scripts leveren een duidelijke gesloten fouttoestand.
- Offline/testbestanden blijven via Pages HTTP404. Publieke fixturedata blijft
  expliciet synthetisch; een verborgen URL is geen beveiligingsmaatregel.

Acceptatie: uitsluitend TECHNICAL PASS / READY FOR OWNER REVIEW wanneer de mock
in de echte appbediening werkt, bestaande werking behouden is en alle negatieve
grensproeven slagen. Geen live-AI-vrijgave of echte-data-goedkeuring afleiden.

## Migrations, Rollback En Kosten

Migrations: **geen** voor 6E-8. Duurzame proposals/approvals/apply/restore, bronversies,
trainerauthoriteit, RLS en transactionele outbox blijven een apart later serverpakket.
Dat latere pakket vereist echte SQL-/RLS-/concurrencytests met uitsluitend synthetische
identiteiten en afzonderlijke owner-GO; de 6E-7/8-browsermock bewijst dit niet.

Rollback: verwijder de nieuwe ingang/container via een gerichte revertcommit van
alleen de goedgekeurde integratie. Niet de hele runtime terugzetten en geen eerdere
legitieme wijzigingen overschrijven. Geen database-rollback of gegevensopruiming.
De zelfstandige 6E-7-demo kan afzonderlijk blijven bestaan.

Externe AI-calls: **0**. Maximale externe AI-kosten: **EUR 0**.
Geen nieuwe betaalde diensten. Onverwachte kosten of noodzakelijke wijziging buiten
de afgebakende runtimebestanden eerst voorleggen.

## Nieuwe Ownerkeuzes

| Keuze | Aanbevolen keuze | Reden |
| --- | --- | --- |
| I1 Integratie-GO | Een expliciete synthetische demo-ingang in staging, geen automatische uitrol naar normale ledenflow | Echte appbediening testen zonder echte verwerking |
| I2 Isolatie | Sandbox-iframe zonder same-origin, met alleen initiële taal/themawaarden | Geen toegang tot parent appdata of verborgen schrijfroute |
| I3 Levensduur | Reset bij sluiten/heropenen; geen opslag of migratie van 6E-7-demostate | Heldere scheiding van apphistorie en fictieve workflow |

Pas na deze keuzes en een aparte GO de implementatie starten. Goedkeuring van dit
voorstel geeft geen toestemming voor echte data, serverapply of externe AI.
