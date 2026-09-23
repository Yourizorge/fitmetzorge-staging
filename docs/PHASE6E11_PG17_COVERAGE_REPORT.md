# 6E-11 PG17, Write-Coverage En Canarybesluit

23 september 2026. Start-HEAD `7883c2a90c7bed9e6bb27dbabf11ddedce0d08de`.
**OFFLINE PG17 / STATIC CONTRACT TESTS PASS. HOSTED CANARY EN PROOFRUN: NO-GO.**
Alle hosted waarnemingen hieronder dateren van 22 september; geen claim over de
actuele belasting op 23 september. Geen nieuwe zware hosted meting uitgevoerd.

## 1. PG17-equivalentie

Read-only vastgesteld: staging draait PostgreSQL **17.6**, server_version_num
170006, Linux aarch64. De nieuwe tests gebruiken exact **17.6**, lokaal Windows
x64, uit de officiele EDB-binarydistributie. Geen service/installatie of wijziging
aan de bestaande PG18-installatie. Clusters buiten OneDrive zijn gestopt en bewaard.
[Binaryherkomst, ziphash en volledige benchmark](PHASE6E11_PG17_BENCHMARK.json).

De vooraf vastgelegde 36 bestaande collectortests slagen op PG17.6 (49,894 s).
Daarna slagen 24 nieuwe register/bewijsketentests en 2 aanvullende PG17-tests
(26 tests, 21,431 s). Totaal: **62 verschillende gerichte tests PASS**. Eerdere
herhalingen tellen niet dubbel. Geen applicatie-, hosted workflow- of medische PASS.

De 143 synthetische tabelnamen gebruiken representatieve, niet gekopieerde live
DDL/ledenrijen: insert/update/delete, duplicaten, NULL, JSON/JSONB, arrays,
timestamps, numeric/float, Unicode en bytea. Cohortuitsluitingen blijven dezelfde.
Getest zijn verschillende uitgangsinstellingen voor tijdzone, DateStyle, locale,
bytea en floats, en het vastzetten daarvan door hetzelfde canonicalisatiecontract.

| PG17.6 benchmark | Oud | Nieuw | Nieuw herhaald |
| --- | ---: | ---: | ---: |
| Collectortijd | 8,688 s | 6,141 s | 8,015 s |
| Client peak working set, bytes | 26.984.448 | 31.547.392 | 31.383.552 |
| Backend peak working set, bytes | 138.452.992 | 94.404.608 | 94.449.664 |
| PostgreSQL tempbytes | 15.515.648 | 0 | 0 |
| PostgreSQL tempbestanden | 4 | 0 | 0 |
| Lokale sorteerbytes geschreven/gelezen | 0 / 0 | 7.201.976 / 7.201.976 | 7.201.976 / 7.201.976 |
| Querycommando's | 6 | 6 | 6 |
| Volledige cycli | 1 | 1 | 1 |
| Retries | 0 | 0 | 0 |

Run `4daf8437-a66c-4525-ad54-94b71a14d8bc`: alle drie bulkidentiteiten byte-identiek,
SHA256 `3aa70944e57bc61ef56a4fe4939bd96002336b45558e594650d791537c1c7262`.
De benchmark omvat 100.000 extra synthetische catalogusrijen. Daarnaast zijn twee
kleine lokale overgangsscans uitgevoerd; geen verborgen hosted cycli. Identieke
inhoud is bewezen, geen eerlijke cold-cache- of cloudperformancevergelijking.
Meer netwerkhashpayload en lokale sorteer-IO blijven een expliciete afweging.

**Historische equivalentie blijft apart open.** Staging rapporteert
extra_float_digits=0, de nieuwe collector pinning=3. Een PG17-test bewijst dat
dezelfde float daarbij verschillende rijhashes kan geven. Oude meetreceipts
leggen niet alle historische sessie-instellingen vast. Ook locale/platform en
werkelijke extensietypen zijn niet volledig gereconstrueerd. De nieuwe methode
mag daarom niet stilzwijgend de historische verwachting vervangen. Het bestaande
synthetische overgangsmanifest blijft onveranderd; geen echte baseline overschreven.

## 2. Write-actionregister

[Machineleesbaar register](../_offline/phase6e11/readiness_v1/register.json):
**52 categorieen**, 153 exacte lokale bronhashes, 59 gevonden gemeten callsites,
107 waargenomen FK-relaties en 5 relevante triggers. A=10, B=7, shared=2,
vensters=4, denial=8, replay=1, Auth=6, directe SQL=7, configuratie=1 en strikt
lokale failurefixtures=6. Dit is een register van acties/uitkomsten, geen claim
dat iedere categorie een afzonderlijke HTTP-route is.

Per categorie: route-/stap-ID, transport/RPC/Edge-dispatch, directe tabel-I/U/D,
before, transactiereceipt, directe after, NO-GO en cleanupgrens. Ook afwijzing en
idempotente replay kunnen een event schrijven; management-replay kan read-only
zijn. Cleanup bevat cascades EN bewaarde window/audit/request-tombstones.

De testbare volgorde is:
`before_saved -> action_started -> action_confirmed -> after_saved -> pair_validated -> next_step_allowed`.
Receipts zijn apart, onveranderlijk en gekoppeld via run, stap, actor, request,
scope, timestamp en voorgaande receipt-hash. Ontbrekend after, verkeerde binding,
onbekende route, bronwijziging/nieuw bestand, budgetoverschrijding en premature
cleanup falen gesloten. Tests gebruiken synthetische assertions; zij bewijzen
geen daadwerkelijk gecommitteerde hosted transactie. De oude runner is niet
aangesloten op deze nieuwe simulator en is niet hervat.

**Volledige hosted schrijfdekking: NIET BEWEZEN.** De registervelden maken dit
expliciet false. Auth-serviceneveneffecten en recursieve trigger/FK-effecten zijn
nog niet uitputtend gesloten. Onafhankelijke cron/gebruikerswriters kunnen bij
alleen begin/eindmetingen onzichtbare write-then-revert veroorzaken. Een register
is geen volledige writer-isolatie of schrijfjournal.

Alle 17 gecontroleerde live 6E-11-functiebodies matchen de lokale SQL-bodyhash.
De Auth-bootstraptrigger matcht de lokale no-op `return new`; een profielwrite
is een afzonderlijke SQL-route, geen aangenomen signupwrite. Voor
`public.touch_updated_at()` matcht de bodyhash NIET:
- live: `a168126301b25f7fe7be9694c104cb8e0b4a75bae20fb0abf805045dbf91e93f`;
- lokale baseline: `3c6d6c41d6262a20e7c102dbd49bb3383bd86a4138c8a3ab6b9b04a1ec2420a5`.

Dit is onopgeloste bronbinding, geen bewezen nieuwe datadrift of ongeoorloofde
write. Whitespace/semantische gelijkheid is niet aangenomen. Geen reparatie gedaan.
De beperkte SQL-extractor is geen algemene SQL-parser; ontbrekende matches blokkeren.

Het register bindt ook behouden ongecommitteerde runner/Edge/migrationbronnen.
Die worden niet met deze offline commit gepubliceerd. Een verse checkout zonder
die bronnen faalt bewust gesloten; dit is geen zelfstandig deploybaar hosted pakket.

## 3. 143 Tabellen En 128 Querycommando's

Een volledige collector gebruikt zes commando's: BEGIN, instellingen, schema,
servermetadata, een UNION ALL-inhoudsstream over 143 tabellen en COMMIT.
143 tabelscans zijn dus niet 143 netwerkqueries; de IO blijft wel alle rijen omvatten.

Een beperkte toekomstige read-only canary reserveert **14 commando's**:
6 collector + 8 metadatareserve, maximaal 1 cyclus, 0 retries, 30 s per statement,
120 s totaal en 0 tijdelijke PostgreSQL-schrijfbytes. Dat past onder 128.
Dit is een offline toelatingscontract, nog geen werkende hosted transportadapter.

Voor een volledige workflow is 128 NIET zonder meer voldoende. Het conservatieve
catalogusmodel rekent 3*6 + n*8 voor before/after-transacties + n*3 actieverzoeken
+ 8 reserve = 26 + 11n. Voor alle 52 categorieen is dat **598**, dus afwijzen onder
128. Dit is een capaciteitsvoorbeeld, GEEN exact uitvoerbaar proofrunplan: de
catalogus bevat onder meer lokale-only fixtures en onderling alternatieve paden.

De limiet is niet verhoogd of omzeild. Voor een latere full proofrun moet eerst
de concrete sequentie, SQL versus HTTP-telling, alle foutpaden en globale IO/duur
worden doorgerekend en een passende harde limiet expliciet worden vastgesteld.
Een nieuwe run-ID of retry mag het budget niet vernieuwen.

## 4. Lichte IO-herstelstatus

[Gesanitiseerde read-only SQL-metadata](PHASE6E11_PG17_READONLY_METADATA.json) en
[afgeleide metingen/gates](PHASE6E11_PG17_READINESS_EVIDENCE.json).
Exact drie metadataqueries, twee infrastructuurmetingen; geen reset, rijinhoud,
oude zware query, nieuwe fingerprint of live mutatie. De infra-aanroepen lezen
bestaande metrics/diskutil; geen wijziging van resources of instellingen.

| Waarneming op 22 september 2026 | Resultaat |
| --- | --- |
| Dashboard na verversen | 57% Disk IO consumed; geen actieve warningbanner |
| Infrastructuurinterval UTC | 11:41:16,822 tot 11:53:10,337 |
| CPU busy exclusief iowait | 2,713% |
| IO-wait | 4,031% |
| Swap gebruikt op eindpunt | 439.894.016 bytes |
| Swap-in / swap-out verschil | 30.284 / 15.042 pagina's |
| Database tempbytes, 11:37:18,565 UTC | 511.312.122.109 |
| Database tempbytes, 11:45:18,667 UTC | 511.416.208.449 |
| Database tempbytes, 11:53:17,639 UTC | 511.529.466.436 |
| Verschil eerste/laatste SQL-meting | +217.344.327 bytes, +31 tempbestanden |
| Stats reset | Ongewijzigd |
| Actieve relevante queries op meetmomenten | Geen |
| Achtergebleven lokale synthetische workers | Geen aangetroffen |
| MCP roundtrip voor drie samples | 10.176 / 5.531 / 3.734 ms |

Roundtrip is NIET database-uitvoertijd. Uurtrend en stabiele DB-latency zijn niet
bewezen. De swap- en tempactiviteit rechtvaardigen geen herstart op basis van een
verdwenen banner alleen. Status: **herstel niet aantoonbaar**, geen actuele
23-september-meting of blijvend normale responstijden geclaimd.

De 15 vergelijkbare zware fingerprint-queryvarianten tonen geen toename van calls
of tempblokken sinds het eerdere IO-rapport; de dominante twee blijven 323/326.
Hun historische bijdrage van 65,819 GiB blijft staan. De nu waargenomen extra
tempbytes zijn daarmee niet aan een nieuwe uitvoering van deze varianten toe te
schrijven; de overige oorzaak is niet volledig vastgesteld. Drie actieve cronjobs
(1 min, 15 min, 1 min) zijn geen zelfstandig causaliteitsbewijs. Niets uitgezet.
Er is geen bewijs dat een betaalde compute-upgrade noodzakelijk is; niet uitgevoerd.

## 5. Canaryresultaat

**NIET TOEGELATEN / NIET UITGEVOERD.** Nul hosted fingerprintcycli, nul automatische
retries, nul fixture-/account-/windowwrites en nul cleanup. Er is dus geen nieuw
143/143-hosted hashresultaat, geen historische live vergelijking en geen nieuwe
claim dat beschermde data onveranderd is. Het laatste historische bewijs blijft staan.

PG17-tests en afwezigheid van een achtergebleven worker slagen als deelgates.
Volledige schrijfdekking, IO-herstel, stabiele latency, historische hashbinding
en gecontroleerd hosted streamingtransport zijn nog niet allemaal bewezen.

## 6. Voor/Na En Bewijsbehoud

De drie SQL-samples en twee infrastructuursamples zijn lichte voor/nametingen
van diagnose, NIET van een canary. Oorspronkelijke receipts zijn niet vervangen:
- `phase6e11-io-metrics-d0afdca3172a4df0ae5395008693960d.json`;
- `phase6e11-io-metrics-76f4108affc843ac8e96b165a5ad5f2f.json`;
- `phase6e11-fingerprint-benchmark-4daf8437-a66c-4525-ad54-94b71a14d8bc.json`.

Deze staan onder `supabase/.temp/`. Oude nulmetingen, incompleet meetpaar 113,
historische controlaccounts/fixtures, frozen AI-bronnen en dirty runtime blijven
ongewijzigd. Geen migration/dry-run opnieuw gestart: 39/39 en lege dry-run zijn
historisch bewijs, geen nieuw resultaat van deze opdracht. Geen Edge-deployment.

## 7. GO/NO-GO En Publicatie

**NO-GO voor precies een volledige geoptimaliseerde proofrun.** Eerst offline:
sluit transitieve write-effecten en de triggerbronbinding; bewijs coverage van
onafhankelijke writers of wijs de beperkte scanstrategie af. Koppel daarna een
gecontroleerde transportadapter en concrete querybegroting. Bewijs een overgang
naar de historische verwachtingen zonder oude bewijsbestanden te vervangen.
Pas na nieuwe lichte IO/latency-herstelmetingen mogen canarygates opnieuw worden
beoordeeld. Deze opdracht hervat geen full proofrun, zelfs niet na een canary-PASS.

Alleen readiness_v1, dit bewijs/rapport en de nieuwe statusparagraaf worden
gecommit. Geen runtime-, workflow-, permission-, database-, migration- of Edge-edit.
De pre/post-publicatiecheck vergelijkt 84 gepubliceerde assets met de frozen
6E-10-baseline, bewaart alle 88 lokale kandidaatassets en eist HTTP404 voor alle
offline/testpaden. Unieke lokale publicatiereceipts en het eindbericht leggen de
feitelijk geverifieerde commit, remote HEAD en Pages-status vast.
Voor push zijn 84/84 live assets byte-identiek, 88/88 kandidaatassets ongewijzigd
en 324/324 offline/testpaden HTTP404. Receipt:
`phase6e11-fingerprint-publication-dddf44c8-833b-4be1-89ce-237261702c07.json`.
Voorbestaande ongecommitteerde wijzigingen blijven zichtbaar; geen schone worktree
claim. Geen owneracceptatie, freeze, venster of 6E-12.

Reproductie: zie [offline README](../_offline/phase6e11/readiness_v1/README.md).
Officiele bronnen: [PostgreSQL Windows-distributie](https://www.postgresql.org/download/windows/),
[EDB PostgreSQL binaries](https://www.enterprisedb.com/download-postgresql-binaries),
[Supabase changelog](https://supabase.com/changelog).
Supabase SDK-retries worden niet gebruikt; nieuwe code bevat geen netwerktransport.

External AI calls/cost: **0 / EUR 0.00**.
Real-member AI enabled: **NO**.
Production touched: **NO**.
