# 6E-11 Filtercorrectie En Onafhankelijke Integratie

15 oktober 2026. Opdracht cead148d-244b-4676-b6a3-907098ac55df.
Uitsluitend Yourizorge/fitmetzorge-staging, main, mokxyyullfhkfalopbzd.
Uitgangscommit c8ce051ed6774fdabbe697e705db8a2371b81da9.

## Uitkomst

6E-11 en de ownertelefoontest blijven **NO-GO**. De nieuwe toegestane poging is
gebruikt en afgesloten. De filtercorrectie werkt, maar de begrensde telling
vindt ook na de bestaande uitsluitingen **minstens 65.537 beschermde rijen**.
Dat past niet binnen de ongewijzigde grens van 65.536 getransporteerde rijhashes.
65.537 is een ondergrens, niet de exacte volledige omvang. Geen extra uitsluiting,
limietverhoging of tweede hosted poging uitgevoerd.

De onafhankelijke lokale/CI-integratie is verder gebouwd en opnieuw bewezen.
Dit is geen hosted activering van registratie-12 of bulkpublicatie van 12-21.
6E-21 blijft ongeaccepteerd. Geen owneracceptatie of freeze afgeleid.

## Nieuwe Hosted Poging

- Run: debe3298-9772-40b1-a9f4-8e3d99c8fd20.
- Venster: 15 oktober 2026,12:57:59-12:58:28 Europe/Amsterdam.
- Stop: row_capacity / stream_row_ceiling, na numerieke telling op commando11
  en complete nameting op12; ROLLBACK bevestigd op13.
- Verbruik:13 van maximaal2226 SQL;4 voorcontrole,9 nulmeting/protocol.
- Getransporteerde rijhashes:0. Hashcursor niet geopend.
- Eigen tijdelijke writes:0; databasebrede temp-delta in dit meetpaar:0.
- Telling458.772ms; tekstvrije lezer47.960ms; eigen WAL1564 bytes.
- Worker4609ms; meter8031ms bij ROLLBACK. Dit is geen claim van nul fysieke IO.
- JIT ingetrokken en uitgeschakeld; actieve mappings0; SSL-enforcement behouden.
- Geen migration, Auth-tokenuitgifte, fixture-, controller- of applicatiewrites.
- Geen nieuwe guard/auditobjecten of testsessies; dus geen nieuwe fixtures te
  verwijderen. Historische fixtures en bewijzen zijn bewust behouden.

De read-only nulmeting was onvolledig. Daarom **geen volledige databehoud-PASS**
en geen claim dat alle beschermde rijhashes opnieuw vergeleken zijn. Geen
afhankelijke mutatie of cleanup gestart. Alle52 originele JSON-receipts zijn
byte-identiek bewaard, inclusief foutfase, meter, querybinding en afsluiting.

Manifest SHA256:
902bdc83b391a533b7c30d2499217a14ff70b3f365c537277b954824f8c35bc5.
Pad: `_offline/phase6e11/endchain_v1/receipts/reserved-debe3298-9772-40b1-a9f4-8e3d99c8fd20/`.
De gebruikte identiteit blijft ook vanuit een verse checkout geblokkeerd.
Oude runs acd473d0 en32321f17,112 geldige meetparen en incomplete113 blijven
historisch ongewijzigd. De eerdere utility-oorzaak blijft UNKNOWN.

## Migraties En Toelating

Hosted opnieuw waargenomen:43, laatste20261012104331. Kandidaat44 is NIET
toegepast; de nieuwe hosted dry-run is door de eerdere stop niet bereikt.
De lokale standaardketen bouwt44 schoon; de afzonderlijke integratie-CI bouwt
46 inclusief twee uitsluitend lokale kandidaten. Dit is geen hosted46/46.

M44 SHA256:
2973c826dd2c177cdade43422013204bbbb2b354ef7bba67cd7b35af6ef823fd.
Alleen de nieuwe runbinding is aangepast; oude uitzonderingen zijn niet hergebruikt.

Hosted-toelating was gebaseerd op CI38722956194, attempt1, bron
3db50cb00e68c3636ade0d4b5ba017143f35e307, kandidaat
5c8b9b16b83a631c279f724f3c74704676b95e15ccc688fc4d039a5465efbfaa,
artifact3691c3571aac08d952cee5dd526e1b01332b5aa71b47b9baecebf9bcf35183e6.
Het volledige register blijft2196 normaal,2207 zwaarste prefix plus veilige
afsluiting,2226 maximum. De fasetabel en alle reserves staan in
[het uitvoeringsrapport](PHASE6E11_FILTERED_RUN_20261015.md).

## Testbewijs

| Samenstelling | Werkelijk bewijs |
| --- | --- |
| 6E-11 CI38722956194 | Schone44;36 migrationchecks;175 Python- en131 JS-tests;36 PG17 filter/capaciteitscontroles;18 echte lokale Auth-contracten;71 workflow/cleanupparen,295 writes waaronder123 deletes;3 foutpaden |
| Lokale endchain regressies | 183 Python-tests; afzonderlijk van hosted bewijs |
| Integratie CI38725094585 | Schone46;12 SQL-regressies;36 M44-checks;29 domeintests;36 PG17 filterchecks;request/controller/security/advisors en lege lokale dry-run |
| Registratie-12 oorspronkelijke adapter | 25 databasechecks,15 browserchecks,4 lokale Auth/sessiechecks; M45 onafhankelijk vanM46 |
| Registratie-12 nieuwe private adapter | 46 databasechecks,4 echte lokale Auth/sessiechecks,22 complete scoped meetparen;23 checks per ledenroute |
| Gezamenlijke lokale bediening | 62 databasechecks,209 browserchecks,4 lokale Auth/sessiechecks |
| Lokale helperregressies | 51 tests, waaronder17 scope/transport,5 meetpaar- en2 accountingtests |

Testcategorieen overlappen inhoudelijk en zijn geen opgetelde medische
betrouwbaarheidsscore. NL/EN/DE, licht/donker,390px mobiel en1280px desktop zijn
browser-emulatie. Geen nieuwe fysieke ownerhandeling geclaimd.

Voorafgaande CI-fouten blijven behouden:38721412989 had een SQL-placeholderfout
in de nieuwe synthetische grenswaardetest;38722727718 stopte bij kandidaat-
toelating door een nog niet gecommitteerde bronallowlist. Correcties zijn opnieuw
brongebonden getest, niet met terugwerkende kracht tot PASS verklaard.

## Werkelijke Lokale Registratie-12

De nieuwe private transportadapter gebruikt echte disposable GoTrue-authenticatie
en PostgreSQL met CA/hostnamecontrole. Exact drie synthetische identiteiten;
alleen de twee leden krijgen elk een eigen registratie-workspace. De trainer
kan geen ledenregistratie schrijven. Geen listener, publieke route of hosted
activeringsvlag toegevoegd. De CI-factory weigert staging-endpoints.

Bronbinding CI38725094585: cd2ca05f4e7c0044f48cba0de75ca10029d526e0;
kandidaat4af7d3f2af7cda8e020f361437f54bd46438e1fe4d0a443ceb092378fc0bc220;
artifact4b0821791a32af95c008a65870834202c3925dea78551d254800e60f01e6e67f.
527 artifactbestanden geverifieerd;157 gesanitiseerde receipts apart gearchiveerd
in `_offline/phase6e_server_v1/receipts/ci-38725094585-completion/`.

De22 meetparen binden actor,request,payloadhash,transactie en rijsleutel. Zes
geslaagde requests hebben elk exact3 writes;16 geweigerde/herhaalde/teruggerolde
acties hebben0 nieuwe writes. Fouten na iedere mutatiestap rollen atomair terug.
Per route zijn8 cleanupdeletes met blijvend auditbewijs gecontroleerd. Historische
snapshots en registratieversies blijven behouden na herstart en opnieuw inloggen.
RIR0 en ontbrekende RPE blijven afzonderlijk. Verloop en toestemming werken fail-closed.

Uitgevoerd lokaal register:1433 SQL =863 native/protocol +570 beheerde Auth.
Hierin zitten176 scoped meetcommando's,18 fixturecleanup- en4 afsluitcommando's.
Register SHA256 ad131a50314723d494520c42b5a825626b0c6b1ddef9cc3fcd8c61f6bed969c5.
Eigen tijdelijke writes in de lokale rolmetingen0. Dit is geen hosted maximum,
geen toestemming om970 of4135 te hergebruiken en geen volledige hosted guard-
begroting. Die laatste toelating hangt van de werkelijk afgeronde11-keten af.

De bestaande lokale integratie omvat daarnaast correcties, snapshots,
vergelijkingen, voorstellen, transactionele outbox, check-inplanning en gezamenlijke
bediening. Geen echte AI-chat, achtergrondbezorging of duurzame hosted opslag
geclaimd. De21-uitbreiding blijft standaard uit en ongeaccepteerd.

Minimale rechten, exacte bron-/identiteitsbinding, verplichte fasekosten en
veilige afsluitreserves worden door de private scopecompiler gecontroleerd.
Ontbrekende11-PASS, fysieke review, selected12-besluit of volledige hosted
budgetbinding blokkeert activering. Rollback sluit uitsluitend de nieuwe ingang
en synthetische toegang, behoudt historie/audit en draait geen migraties terug.
Zie [de concrete releasegrens](PHASE6E12_SELECTED_RELEASE_BOUNDARY.md).

## Behoud, Publicatie En Vervolg

1.376 beschermde bestanden opnieuw gecontroleerd:0 wijzigingen. De zes oudere
tracked werkboomwijzigingen en oude untracked bestanden zijn behouden. De
werkboom wordt daarom niet als schoon gepresenteerd. Geen applicatieruntime,
frozen AI-bron, productie-, APPFMZ-, website- of JARVIS-bestand gewijzigd.
Voorpublicatie:152 runtime-assets byte-identiek en19 bestaande private paden404.
Na de documentatie-/bewijscommit worden Pages en de uitgebreide private padset
opnieuw gecontroleerd; de uitkomst wordt afzonderlijk vastgelegd.

Implementatiecommits:36c0007 (capaciteit/filter),c12d92e (PG-testcorrectie),
3db50cb (begrensde artifactcollector),34b7d5a (registratietransport/meetparen),
cd2ca05 (onveranderlijke poging-/CI-receipts). Geen runtimecommit of hosted
deployment. De uiteindelijke documentatiecommit en remote HEAD staan in het
afsluitbericht en het publicatiebewijs.

**Kleinste hosted vervolgstap:** afzonderlijk toestemming voor een begrensde
numerieke omvangbepaling zonder hashtransport, om een passende meetcapaciteit te
onderbouwen. Daarna een expliciet capaciteitsbesluit en nieuwe afzonderlijke
pogingstoestemming. Geen willekeurig groter maximum en geen huidige retry.
Tot die tijd blijft de ownertelefoontest NO-GO en is er geen testlink/vervaltijd.

External AI calls/cost:0 / EUR0.00.
Real-member AI enabled:NO.
Production touched:NO.
