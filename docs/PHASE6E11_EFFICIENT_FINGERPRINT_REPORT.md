# 6E-11 Offline Zuinige Fingerprints En Harde Limieten

22 september 2026. **OFFLINE IMPLEMENTATION / LOCAL TECHNICAL PASS.**
**6E-11 blijft NO-GO. Geen hosted canary, proofrun, cleanup of owner-testvenster.**
Geen 6E-12. Start-HEAD: `96fc380e47420474efde5509eab0a944398b1190`.

## 1. Oude Methode En Belasting

Het [IO-rapport](PHASE6E11_DISK_IO_REPORT.md) en de oorspronkelijke bewijsbestanden
blijven behouden. De 57% IO-consumptie is de laatst waargenomen dagwaarde, geen
nieuwe resourcecheck in deze offline opdracht.

| Query-ID | Genormaliseerde query-MD5 | Calls op 21 september |
| --- | --- | ---: |
| -3957083696356868595 | 6e7505ca1f72669bf1849c5b7f6cc23d | 323 |
| -699327191976944610 | 096c360fcf4e3f78e1179304fc4e4b2a | 326 |

Samen 65,819 GiB tijdelijke schrijfblokken. Beide gebruiken dezelfde builder in
`hosted_v2/snapshot.py` en `hosted_v3/snapshot.py`. Beide bewaarde bronbestanden
hebben SHA256 `47fb3c25497de26a3b7c17eda8a975d31fd14b1c483f16f08cbb8d4874a41252`.
Queryvarianten verschillen door de versiegebonden synthetische/cohortselectie;
query-MD5 is een identificatiemiddel, niet de inhoudsfingerprint.

Exacte inhoudsvolgorde:
1. Per rij: PostgreSQL `to_jsonb(t)::text`, dus alle niet-verwijderde kolommen.
2. UTF-8 bytes daarvan -> SHA256 -> 64 lowercase hextekens.
3. Per tabel/cohort: rijhashes sorteren op `h`, inclusief iedere identieke herhaling.
4. Met een komma samenvoegen, zonder laatste komma; lege verzameling is lege tekst.
5. UTF-8 bytes -> SHA256. Rijenaantal afzonderlijk bewaren.

JSONB-canonicalisatie komt van PostgreSQL, niet van een eigen JSON-rewriter.
De oude methode heeft geen vastgelegd TimeZone-/localecontract. Binaire uitvoer,
tijdzone en type-uitvoerfuncties kunnen daarom relevant zijn.
`work_mem=2184kB` en de geordende aggregaten veroorzaken bewezen tempblokken.
Een hoge shared-buffer-cache-hit-rate voorkomt deze tijdelijke sorteer-IO niet.

De behouden inventaris bevat alle 143 tabelnamen in
`_offline/phase6e11/fingerprint_v1/inventory.json`.
Elke rij bevat alle tabelkolommen, niet alleen een primary key of updated_at.
Het oude bewijs bevat geen volledige historische kolom-/typebeschrijving.
Die niet-bewaarde beschrijving wordt niet verzonnen: de nieuwe collector leest en
bindt de daadwerkelijke kolomnaam, positie, SQL-type, nullability en collation.
De synthetische fixtures gebruiken de 143 namen, NIET een exacte kopie van alle
historische live DDL, extensietypen of ledenrijen.

De gecorrigeerde oude full-run bevatte 278 bewaarde volledige snapshots, dus minstens
278 geslaagde grote hashqueries, plus 2 catalogusqueries bij initialisatie.
Met zijn canary: 54 + 278 = 332 volledige scans, plus catalogus- en actiequeries.
Over alle behouden pogingen op 21 september: 664 snapshots.
Het exacte totaal inclusief alle RPC-, eventexport- en mislukte queries is niet
volledig vastgelegd; 664 is geen verzonnen exact totaal van alle databaseaanroepen.

## 2. Geimplementeerde Methode

Nieuwe zelfstandige map: `_offline/phase6e11/fingerprint_v1/`.
Geen import van Supabase-credentials, geen remote DSN en geen koppeling aan de oude
hosted orchestrator. Transport accepteert alleen 127.0.0.1 en lokale testpoorten.

- Een read-only REPEATABLE READ-transactie voor schema, selectie en rijstream.
- Vaste, versiegebonden sessie-instellingen: UTC, ISO/YMD, postgres-intervalstijl,
  hex-bytea, UTF-8, extra_float_digits=3 en C voor numerieke/monetaire/tijdlocale.
- Dezelfde PostgreSQL-rijhash als hierboven; alleen tabelindex, rijhash en
  cohortlidmaatschap verlaten de database. Geen inhoud van rijen in bewijsbestanden.
- Een UNION ALL over alle 143 tabellen, zonder ORDER BY, OFFSET, ctid of rij-key.
  libpq single-row mode voorkomt het verzamelen van de volledige response.
- Lokaal sorteren in blokken van maximaal 16.384 hashrecords; daarna k-way merge.
  Elke hash blijft voor elke duplicaatrij aanwezig.
- Tijdens de merge incrementeel SHA256 bijwerken met exact dezelfde komma-volgorde.
  Chunkinhoud wordt tijdens het lezen tegen zijn vastgelegde SHA256 gecontroleerd.
- Geen identiteit voordat de server de volledige stream met het juiste
  eindrijenaantal bevestigt, de merge klopt, de transactie voltooit en het
  identiteitbestand duurzaam is opgeslagen.
- Operationele receipts houden run-ID/tijd/foutfase. De afzonderlijke
  identiteitmanifesten bevatten geen klok/run-ID en zijn byte-reproduceerbaar.

Ruwe en beschermde tabelcohorten behouden de oude selectie. Tevens ondersteund:
synthetische Auth-cohorten en behouden workspace/window-cohorten.
Auth-users, user_id, null-eigenaars, mfa-sessionkoppeling, actor_id en
public-controluitsluitingen volgen de oude expressies. Cron-detail en 6E-11-private
rijen blijven in de raw-cohort en hebben dezelfde beschermde uitsluiting als voorheen.
Dit is geen nieuwe uitzondering voor echte leden.

De bestaande aparte request-, actor-, sessie-, migration- en cronbewijzen van de
orchestrator worden NIET vervangen door alleen een tabelhash. Hosted aansluiting
en bewijs van die aanvullende contracten blijven latere vereisten.

## 3. Onderzochte Alternatieven

| Methode | Oordeel |
| --- | --- |
| Keyset-paginering | Alleen correct met complete unieke sleutel, vaste null-/collationregels en dezelfde transactionele snapshot. Niet generiek voor alle 143 tabellen. |
| Bestaande PK/unique-volgorde | Bruikbaar om rijen te bezoeken, maar keyvolgorde is niet de oude hashvolgorde. Verandert de eindhash zonder aanvullende hash-sortering. |
| OFFSET of ctid | Afgewezen: onstabiele/ongedefinieerde identiteit of onnodige herhaalde scans. |
| Rijhashes als verzameling zonder telling | Afgewezen: verliest duplicaatmultipliciteit. |
| XOR/som van hashes | Afgewezen als stille vervanging van de oude geordende identiteit. |
| Single-row stream + lokaal gesorteerde rijhashes | Gekozen. Werkt ook zonder unieke sleutel en behoudt duplicaten. |
| Incrementeel hashen | Toegepast NA de lokale sorteerstap, met de oude separators en lege waarde. |

Geen nieuwe stagingtrigger, permanente hashadministratie, index of databaseinstelling.

## 4. Equivalentiebewijs

**36 gerichte tests PASS**, plus **12 bestaande lokale IO-diagnoseregressies PASS**.
Tests gebruiken PostgreSQL 18.6 en volledig gegenereerde gegevens.

Getest: insert/update/delete, identieke duplicaten/multipliciteit, omgekeerde
invoervolgorde, lege tabellen, null-eigenaars, source/cohortuitsluitingen,
schemawijziging, ontbrekende tabel, gelijktijdige write tijdens een consistente
snapshot, queryfout na gedeeltelijke resultaten, ontbrekende terminal/count,
beschadigde chunks, timeouts, echte child-process-exit en parallelle processen.

Representatieve kolommen: UUID-koppelingen, numeric(16,4), double precision
(inclusief NaN en nul), JSON/JSONB, integerarrays met NULL en leegte, timestamptz
(inclusief infinity), timestamp, interval, Unicode/verschillende normalisatievormen,
bytea met nulbytes/ff/leegte, boolean en NULL. De collector hashte alle kolommen.
Geen medische gegevens of echte ledenkopie gebruikt.

Met hetzelfde pinned contract zijn oude en nieuwe tabel-/cohorthashes exact gelijk.
Drie bulkidentiteiten (oud, nieuw, nieuw) zijn byte-identiek:
`c9c1666c6a4d5314839d09d8cb35e6f677d5dc53c511e9ab88d13a1ca6af7b1c`.

Verschillende aanvankelijke TimeZone, DateStyle, bytea_output, IntervalStyle en
lc_numeric worden door het nieuwe contract vastgezet en leveren dezelfde identiteit.
Dit bewijst geen universele gelijkheid tussen verschillende PostgreSQL-majorversies,
niet-geteste collations of extensie-uitvoerfuncties.

### Expliciet Overgangsbewijs

De oude ongepinde timestamp-hash verandert aantoonbaar bij UTC tegenover New York.
Daarom geen claim dat de nieuwe pinned hash automatisch iedere historische nulmeting
mag vervangen. Het algoritme-/canonicalisatiecontract heeft een nieuwe versie.

[Volledig synthetisch overgangsmanifest](PHASE6E11_FINGERPRINT_TRANSITION.json):
oude en nieuwe hashes voor alle 143 tabellen/cohorten, exact dezelfde read-only
snapshot, beide canonicalisatiecontracten, datasetidentiteit en versie.
Alleen `public.foods` verandert in dit kleine timestampvoorbeeld.
Manifest-SHA256:
`6f3f991c4756a9f798402dfa9878fbf5feb901a96a52a8332ac18fdf11640c6a`.
Datasetidentiteit:
`f409d61218a06e0ff5217288cfed003a91d96a8d1519cfd695541c93f2e2e361`.

Dit is een uitgewerkt overgangsmechanisme met synthetisch bewijs, GEEN
overgangsgoedkeuring voor de werkelijke stagingbaseline. De oorspronkelijke
nulmetingen en het ontbrekende historische meetpaar 113 blijven ongewijzigd.

## 5. Lokale Benchmark

Definitieve bronversie:
[benchmark en bronhashes](PHASE6E11_FINGERPRINT_FINAL_BENCHMARK.json).
Run-ID `0e51c0c5-b59b-467f-9bcc-f61ba3dee4c8`.
143 tabellen; daarnaast 25.000 + 75.000 gegenereerde catalogusrijen.
Oud en nieuw gebruiken dezelfde dataset en dezelfde canonicalisatie.

| Maatstaf | Oude aggregatie | Nieuwe stream | Nieuwe herhaling |
| --- | ---: | ---: | ---: |
| Collectortijd | 3,406 s | 2,297 s | 2,359 s |
| Client peak working set | 25,81 MiB | 30,53 MiB | 30,54 MiB |
| Backend peak working set | 136,00 MiB | 91,88 MiB | 91,93 MiB |
| PostgreSQL tempbytes | 15.515.648 | 0 | 0 |
| PostgreSQL tempbestanden | 4 | 0 | 0 |
| Lokale sorteerbytes geschreven | 0 | 7.201.976 | 7.201.976 |
| Lokale sorteerbytes gelezen | 0 | 7.201.976 | 7.201.976 |
| Lokale hashchunks | 0 | 7 | 7 |
| Resultaatpayload | 132.131 bytes | 6.892.214 bytes | 6.892.214 bytes |
| Querycommando's per collector | 6 | 6 | 6 |
| Volledige cycli per collector | 1 | 1 | 1 |
| Automatische retries | 0 | 0 | 0 |

De zes commando's zijn BEGIN, settings, schema, servermetadata, inhoudsstream en COMMIT.
De inhoudsstream bezoekt 143 tabellen; zes commando's betekenen niet zes losse
volledige scans. De benchmark heeft drie volledige bulkcycli; de afzonderlijke
kleine overgangsvergelijking heeft twee scans. Setup en meetinstrumentatie zijn
afzonderlijk en geen verborgen hosted werk.

Windows-backendtransfercounters oud: 16.662.639 gelezen / 69.234.308 geschreven
bytes; nieuw: 111 gelezen / 0 geschreven. Dit zijn OS-procescounters, geen
rechtstreekse EBS- of SSD-metingen. Pg-buffer-reads 2.446 versus 573/557 blokken.
Cachetoestand en volgorde zijn niet gelijkgetrokken; geen cold-cache- of cloudclaim.
Het harde waargenomen resultaat is nul DB-sortspill in deze nieuwe synthetische
runs, met meer lokale IO en circa 52x zoveel hashpayload. Kosten/egress in staging
zijn NIET gemeten. Piekgeheugen is Windows process working set, niet Python-heap.

De eerdere geslaagde benchmark blijft apart bewaard in
PHASE6E11_FINGERPRINT_BENCHMARK.json; zij ging vooraf aan de repositorybrede lock.
De meting 776d5820 blijft in haar oorspronkelijke receipt behouden; de definitieve
meting hierboven bindt ook de laatste whitespace-opmaak aan exacte bronhashes.
Een eerdere rapportopslagfout door Windows-padlengte is lokaal hersteld; haar
cluster/intermediaire bestanden zijn niet verwijderd en tellen niet als eindbewijs.

## 6. Harde Limieten En Bewijsketen

- Hoogstens 3 volledige cycli en 128 querycommando's per expliciet meetbudget.
  Reserveren wordt VOOR de query duurzaam vastgelegd. Nieuwe run-ID reset niets.
- Een repositorybrede exclusieve proceslock, ook bij verschillende budgetmappen.
  Geen automatische overname van achtergelaten locks; een processtop blokkeert.
- Hoogstens 1 actieve cyclus; nul fingerprintretries; geen vervangend meetbudget
  of nieuwe runner starten als automatische foutafhandeling.
- Run maximaal 900 s; DB-statementtimeout 30 s, locktimeout 3 s; stream/sort 120 s.
- Maximaal 1.000.000 rijen, 128 MiB hashchunkwrites, 64 chunks, 16.384 records/buffer.
- Laatste rij zonder terminal, corrupt chunk of fout betekent NO-GO, geen identiteit.
- Per actie blijft vereist:
  before_saved -> action_started -> action_confirmed -> after_saved ->
  pair_validated -> next_step_allowed.
- Gewijzigd schema/selectie/canonicalisatie, beschermde drift of onverklaarde raw
  wijzigingen blokkeren het paar. Ontbrekende after blokkeert vervolg EN cleanup.
- Test met 649 aanvragen: slechts 3 toelatingen; de vierde zet een blijvende halt.
  Tests met nieuw proces/run-ID en verschillende budgetmappen bevestigen de grenzen.

Dit beschermt het nieuwe collectorpad. De oude hosted code is bewust niet vervangen:
zij blijft buiten gebruik. Opzettelijk code wijzigen of een handmatig nieuw
autorisatiebudget aanmaken is geen automatische retry en valt niet onder deze
technische claim. De toekomstige orchestrator mag dat niet zelf doen.

## 7. Nieuwe Architectuur En Open Voorwaarden

Doel voor later: (1) volledige nulmeting, (2) directe gerichte before/after-paren
rond iedere mutatie, (3) volledige meting voor cleanup, (4) volledige nacontrole.
Dat zijn drie volledige cycli; de gerichte metingen zijn geen verkapte full scans.
Een noodzakelijke extra volledige foutmeting vereist een expliciet nieuw begrensd
onderzoeksbudget, nooit een automatische vierde cyclus.

Die reductie is nu NIET bewijswaardig voor alle 143 tabellen: er is geen compleet
bewezen schrijfjournal of writer-isolatie voor triggers, cascades, Auth, cron,
service-acties en gewone appgebruikers. Bookends missen mogelijk write-then-revert.
Rijtellingen/updated_at/pg_stat-tellers zijn geen vervanging. Daarom faalt
`targeted()` expliciet met `write_coverage_not_proven`.

Voor hosted aansluiting blijven concreet nodig:
1. Stabiele, aantoonbaar herstelde Disk IO en bruikbare latency-/uurmetadata.
2. Vergelijking op de staging PostgreSQL 17-versie; exacte oude sessie-instellingen,
   collation en volledige werkelijke type-/schemamanifest controleren.
3. Veilige, begrensde streamingtransportkeuze en afscherming van rijhashes.
   Rijhashes zijn pseudoniem, niet automatisch anoniem.
4. Versiegebonden vooraf vastgelegde cohortselectie; geen dynamisch gewijzigde
   uitsluitingen ongemerkt als hetzelfde meetcontract gebruiken.
5. Volledige write-dekking bewijzen OF de beperkte scanarchitectuur niet gebruiken.
   Geen triggers/retentie-infrastructuur toegevoegd in deze opdracht.
6. De nieuwe gates aansluiten op alle hosted mutaties, inclusief bestaande request-,
   actor-, migration- en cleanupreceipts; foutinjecties daarna opnieuw uitvoeren.

**Huidige hosted canary: NO-GO.** Na bewezen IO-herstel is het eerste veilige
canaryvoorstel uitsluitend read-only synthetische CTE-data (maximaal 1.000 rijen),
twee inhoudsqueries plus strikt begrensde metadata, geen fixtures/DDL/memberdata.
Doel: PostgreSQL-17-canonicalisatie en transport vergelijken. Het is geen volledige
143-tabellenpreservatie en geen hervatting van de proofrun. Deze canary is niet
gebouwd/uitgevoerd of impliciet vrijgegeven door deze lokale PASS.

## 8. Behoud, Commit En Publicatie

Voor push: 84 gepubliceerde baseline-assets byte-identiek; alle 88 behouden lokale
runtimebestanden eveneens identiek; 316 toen aanwezige offline/testpaden HTTP404.
De later toegevoegde README valt onder de volledige nacontrole.
Receipt: `phase6e11-fingerprint-publication-5b93efb1-6691-4561-8eae-582c51f73847.json`.

Alleen de nieuwe offline map en expliciet geselecteerde rapporten worden gecommit.
Geen bestaande runtimecandidate, migration, Edge-bron, frozen 6E-0--6E-10-bron,
providerinstelling of goedkeuringsinstelling in de commit. Voorbestaande vuile
wijzigingen blijven staan. Na push worden commitdiff, remote HEAD, Pages-status,
84 live assethashes, 88 lokale runtimehashes en alle private paden opnieuw gecontroleerd.
De nieuwe onveranderlijke publicatiereceipt in supabase/.temp en het eindbericht
leggen de uiteindelijke commit/publicatiestatus vast; dit rapport beweert geen
succesvolle publicatie voordat die werkelijk is geverifieerd.

Geen Supabase-databasequery, migration, Edge-deploy, nieuwe fingerprint tegen staging,
hosted cleanup, ownerwindow of nieuwe databehoudsclaim in deze opdracht.
Alle nieuwe lokale PostgreSQL-clusters zijn gestopt; bestanden blijven behouden.

Officiele onderbouwing:
[libpq single-row mode en foutafhandeling](https://www.postgresql.org/docs/current/libpq-single-row-mode.html),
[PostgreSQL command execution](https://www.postgresql.org/docs/current/libpq-exec.html),
[JSON-canonicalisatie](https://www.postgresql.org/docs/current/functions-json.html).
Deze documentatie valideert geen niet-uitgevoerde PostgreSQL-17-proef.

External AI calls/cost: **0 / EUR 0.00**.
Real-member AI enabled: **NO**.
Production touched: **NO**.
