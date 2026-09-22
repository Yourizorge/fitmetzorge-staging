# 6E-11 Staging Disk IO Onderzoek

22 september 2026. **NO-GO / HOSTED PROOFRUN GEPAUZEERD.**
Uitsluitend `mokxyyullfhkfalopbzd`, staging main. Geen owner-testvenster,
cleanup, volledige fingerprintcyclus of nieuwe hosted proofrun in dit onderzoek.
Dit afzonderlijke rapport verandert geen historisch bewijs of eerdere NO-GO.

## 1. Conclusie En Bewijssterkte

De herhaalde volledige fingerprints hebben aantoonbaar zeer veel tijdelijke
database-IO veroorzaakt en zijn een sterke, materiele bijdrager aan de waarschuwing.
Twee 6E-11-queryvarianten van 21 september zijn samen 649 keer uitgevoerd:
65,819 GiB tijdelijke schrijfblokken en circa 65,629 GiB leesblokken. Dit zijn
PostgreSQL-tempbloktellers, NIET rechtstreeks gefactureerde/fysieke EBS-bytes.

De lokale bewijsbestanden bevatten 664 unieke voltooide 143-tabellensnapshots
op 21 september. Kopieen in receipts tellen niet dubbel. De 649 uitvoeringen
betreffen alleen twee dominante queryvarianten; 664 betreft bewaarde snapshots
van meerdere varianten en voorbereidingen. Deze tellingen meten verschillende
verzamelingen en zijn geen tegenstrijdige aantallen.

De precieze uurpiek en het aandeel van deze queries in het volledige Disk IO-budget
zijn NIET bewezen. Uurlijkse IOPS/throughput/CPU-grafieken geven in het dashboard
"Unable to load data", zowel bij 60 minuten als 24 uur. De infrastructuurgrafiek
toont wel dagwaarden, maar exposeert geen precieze bucket-/sampletijd. De waarschuwing
zelf bevat in deze opdracht geen verzendtijd. Geen oorzaak exclusief verklaren.

Actuele korte steekproef: database bereikbaar, weinig CPU-belasting, geen lopende
fingerprint of achtergebleven lokale 6E-11-worker. IO-budgetherstel is echter niet
aangetoond. De nieuwe, zuinigere bewijsmethode is nog niet equivalent bewezen.
Daarom GEEN hervatting.

## 2. Tijdlijn

Nederlandse tijd = UTC + 2 uur. Bewijstijden hieronder komen uit behouden bestanden,
niet uit reconstructie van ontbrekende nametingen.

| 21 september, Nederlandse tijd | Bewaarde volledige 143-tabellensnapshots |
| --- | ---: |
| 11:00-11:59 | 1 |
| 12:00-12:59 | 177 |
| 13:00-13:59 | 151 |
| 15:00-15:59 | 79 |
| 16:00-16:59 | 165 |
| 17:00-17:59 | 91 |
| Totaal | 664 |

Eerste bewaarde meting 11:25:34; laatste 17:38:26.
V2-hoofdcanary 54, V2-full 274; V3-hoofdcanary 54, V3-full 278;
vier eerdere voorbereidingsmetingen samen 4. Eerste canary-opslagfout bewaarde
geen snapshot; dat betekent niet dat er geen query uitgevoerd was.

De V3-worker stopte om 17:38:38 door de eerder gerapporteerde batch-IPC-deadline.
De laatste afzonderlijke stopinventarisatie gebeurde VOOR de IO-pauze; zij wordt
nu niet herhaald. Het ontbrekende meetpaar 113 blijft ontbrekend.

Dashboardtooltip, letterlijk op datumlabel overgenomen:

| Datumlabel | CPU | Geheugen | Disk IO |
| --- | ---: | ---: | ---: |
| 16 september | 89% | 55% | 1% |
| 17 september | 49% | 59% | 1% |
| 18 september | 57% | 59% | 2% |
| 19 september | 8% | 60% | 1% |
| 20 september | 8% | 59% | 1% |
| 21 september | 9% | 46% | 1% |
| 22 september | 68% | 56% | 57% |

Dit is geen uurlijkse tijdlijn. Vooral het datumlabel 22 september bij 57% mag
niet zonder bucketmetadata rechtstreeks aan een bepaald uur op 21 september
worden gelijkgesteld. Ook is 57% geen gemeten actuele throughput of bewezen
resterend budget van 43%. De projectpagina bevestigt `t4g.nano`, circa 406,52 MiB
zichtbaar geheugen en 27% gebruikte opslag; opslagruimte is geen IO-budget.

## 3. Veroorzakende Queries En Overige Belasting

| Query-ID | Query-MD5 (identificatie, geen inhoud) | Calls | Gemiddeld | Temp geschreven |
| --- | --- | ---: | ---: | ---: |
| -3957083696356868595 | 6e7505ca1f72669bf1849c5b7f6cc23d | 323 | 11,960 s | 4.300.448 blokken |
| -699327191976944610 | 096c360fcf4e3f78e1179304fc4e4b2a | 326 | 12,477 s | 4.326.616 blokken |

Blokgrootte aantoonbaar 8192 bytes. Eerste statistiektijden respectievelijk
21 september 12:06:55 en 15:36:25 Nederlandse tijd. Tellers bleven gelijk tussen
21 september 18:04 en 22 september 10:29. Alle 15 grote fingerprintvarianten
samen: 1.003 calls, 13.286.749 geschreven tempblokken en 3,168 uur uitvoertijd.
De oudste van die varianten komt uit 16 september; niet alle 1.003 zijn 143-tabellenruns.

Bron `hosted_v3/snapshot.py` maakt per tabel SHA256 van canonieke JSON-rijen en
twee geordende `string_agg`-cohorten (alle rijen en beschermde rijen).
De statistieken bevestigen deze queryvorm en 6E-11-scope zonder SQL-inhoud te tonen.
Met `work_mem=2184kB` leiden dergelijke sorteringen aantoonbaar tot veel
tempblokken. Exacte verdeling per tabel/sorteerknoop is niet gemeten:
geen zware EXPLAIN ANALYZE tijdens deze pauze.

- Cache hit rate op 21 september circa 99,999915%; de twee dominante queries hadden
  nul nieuwe shared-block-reads. Dit sluit temp-/swap-IO niet uit.
- `track_io_timing=off`: nul gemelde blokleestijd bewijst geen nul IO-wachttijd.
  `pg_stat_statements.track=top`: geen complete afzonderlijke nested-queryattributie.
- Catalogi `nutrition_off_product_names` en `nutrition_off_products` zijn de
  grootste objecten (dashboard 70,66 en 49,06 MB inclusief objectopslag).
  Volledige inhoudshashes moeten alle relevante rijen bezoeken. Sequential scans
  bewijzen hier geen ontbrekende index; een gewone extra index lost dit niet op.
- Hoge cumulatieve scan-/rollbacktellers hebben oudere resetdatums en zijn geen
  huidige queryloop. Een historische query met ruim 1,086 miljard calls veranderde
  niet tussen de twee onderzochte momenten.
- Actieve cron: 6C-retentie iedere minuut, 6D-retentie iedere 15 minuten,
  6D-inboxworker iedere minuut. Recente metadata toont geslaagde runs; worker
  circa 0,52-1,82 s, 6C-retentie circa 0,005-0,026 s. Om 10:24 was alleen de bekende
  inboxworker zichtbaar actief (2 s). Niet stilgelegd of gewijzigd.
- Geen actieve vacuum in de steekproef. WAL-archivering: nul fouten; archivering
  loopt door. Backup-API: geen backups in de lijst, PITR false, WAL-G true.
  Dit sluit interne platformonderhouds-IO niet universeel uit.
- Database-tempbytes groeiden ook na het stoppen van fingerprints:
  497.376.338.398 op 21 september 18:03 naar 508.736.445.763 op 22 september 10:09.
  De extra circa 10,58 GiB is met deze top-level metadata niet volledig toegerekend.
  Dus niet beweren dat fingerprints de enige achtergrondbelasting zijn.
- Begrensde gatewaylogaggregatie (21 september 11:00-18:00 Nederlandse tijd):
  543 Auth- en 531 REST-requests, geconcentreerd in dezelfde testuren.
  Geen inhoud, actor-ID, header, token of URL-query opgeslagen. Deze logbron
  leverde geen afzonderlijke function-routeaantallen; geen bewijs van nul Edge-calls.
  Eerdere SQL-metadata: 626 6E-11-RPC-calls, circa 149,4 s cumulatief, nul eigen
  tempblokken. Geen sluitende Edge-naar-DB-IO-attributie uit alleen deze bron.

## 4. Actuele Status En Veilige Begrenzing

Twee eenmalige Metrics-API-samples op 22 september 10:07:36 en 10:09:23:
106,75 seconden tellerinterval. Geen retry-/pollingloop.

- CPU circa 95,54% idle; 1,74% actief rekenen; 2,71% IO-wait.
- Beide fysieke disks samen circa 85,6 IOPS en 2,35 MB/s lezen/schrijven.
  Drukste disk circa 4,63% busy. Dit zijn korte intervallen, geen piekuurwaarden.
- Circa 171,3 MiB geheugen beschikbaar; circa 423,7 MiB swap bezet.
  Swap-in 2.750 pagina's, swap-out 31; paginaformaat niet verondersteld.
- Metrics-GETs 2,969 en 2,782 s inclusief netwerk/managementlaag.
  Geen representatieve app-p95-latencytest uitgevoerd.
- Korte metadataqueries slagen met een statement-timeout van 5 s.
- Windowscontrole: nul lokale node/python/supabase-processen met 6E-11-commandline,
  zowel na stop op 21 september als op 22 september. Geen proces hoeven stoppen.
- Geen volledige fingerprints, cleanup, accounts, vensters, migrations, DB-restart,
  compute-upgrade, Edge-deploy of apppublicatie door dit IO-onderzoek.

Oordeel: **korte actuele belasting laag, historisch dagverbruik verhoogd;
volledig budgetherstel of duurzame stabiliteit niet bewezen**.

## 5. Zuinigere Meetmethode: Voorstel, Niet Toegepast

Vier volledige meetmomenten zijn een mogelijke doelarchitectuur:
nulmeting, eindmeting voor cleanup, directe cleanup-voorcontrole (kan alleen dezelfde
meting zijn als werkelijk geen tussenliggende writes plaatsvonden), en nacontrole.
Daartussen direct gerichte before/after-metingen van aantoonbare mutatietabellen.

Maar alleen bookends + rijenaantallen/updated_at/pg_stat-tellers/cached hashes
behouden NIET vanzelf de huidige bewijssterkte. Een beschermde wijziging die
tussen bookends wordt teruggedraaid kan onzichtbaar blijven.

Vereiste equivalentie voordat scanreductie mag worden toegepast:
1. Volledige, onafhankelijk geteste write-dekking voor triggers, cascades, Auth,
   admin/service-acties, cron en appwrites via een betrouwbare versie-/mutatieketen,
   of aantoonbare uitsluiting van alle schrijvers naar hergebruikte cohorten.
2. Onveranderlijke hashbinding aan bronversie, cohortdefinitie, schema en consistente
   snapshot. Onbekende wijziging of dekking betekent NO-GO; geen stil hashhergebruik.
3. Lokale failure-injecties voor write-then-revert, cross-table-trigger, concurrente
   write, delete, ontbrekende eventregistratie en processtop. Geen vermindering van
   actor-/versie-/mutatiebewijs of de bestaande zes fasen.

Er is nu GEEN bewezen volledige write-dekking voor de 143 tabellen. Deze reductie
wordt daarom niet in de hosted runner gezet.

Eerst offline uitvoerbaar alternatief: behoud volledige inhoudshashsemantiek,
maar onderzoek streaming van uitsluitend rijhashes onder een consistente
read-only snapshot, met sorteren en eindhashen lokaal. Geen persoonlijke rijinhoud
exporteren; controleer privacy van rijhashes en identieke canonisering, collation,
volgorde, duplicaten, NULL en lege tabellen. Test exacte hash-equivalentie met
synthetische PostgreSQL-data. Dit vermindert mogelijk DB-sortspill, maar totale
CPU/IO/netwerkbelasting moet later in een afzonderlijk begrensde proef blijken.

Operationele begrenzing voor dat toekomstige ontwerp:
- Een SQL-aanvraag tegelijk, een runner, geen automatische volledige-run-retry.
- Geen herhaalde fingerprints voor passieve layouts; checkpoints verwijzen alleen
  naar dezelfde meting als er aantoonbaar geen relevante write tussen zit.
- Per stap een eigen deadline; geen batchdeadline die een nieuwe mutatie afbreekt.
  Ontbrekende nameting blijft harde NO-GO, zonder automatische cleanup.
- Metadata maximaal eens per 60 s tijdens een later toegestane run, eindige duur.
  Geen permanente monitor of achtergrondtaak aangemaakt.
- Voorlopig conservatief stopvoorstel: IO-wait >5%, throughput of IOPS >60% van de
  bevestigde sustained-capaciteit in twee meetintervallen, CPU >60%, of metadata-
  latency >2x de vastgestelde rustige basislijn; onmiddellijk stoppen bij timeout,
  oplopend temp-/swapverbruik zonder verklaring of een nieuwe IO-budgetwaarschuwing.
  Dit zijn te valideren operationele grenzen, geen Supabase-garanties of hervattings-GO.
  Ontbrekende budget-/latencymetadata sluit een zware run uit.

## 6. Compute-Upgrade

**Niet aantoonbaar noodzakelijk; nu niet uitvoeren.** De vermijdbare meetbelasting
moet eerst worden verminderd. Nano heeft volgens de actuele officiële documentatie
minimaal 5 MB/s en 250 IOPS sustained; gp3-diskwaarden van 125 MB/s/3000 IOPS zijn
niet automatisch de effectieve Nano-capaciteit. De korte huidige steekproef ligt
onder de Nano-basiswaarden, maar bewijst geen capaciteit voor een nieuwe proofrun.

Een latere upgrade kan zinvol zijn bij blijvende normale workload-/geheugendruk,
na representatieve metingen met een geoptimaliseerde runner. Zij kost geld en kan
downtime veroorzaken; daarvoor blijft expliciete ownerkeuze nodig.
Geen prijsbesluit, upgrade of betaalde monitoring gedaan.

## 7. Hervattingsvoorwaarden En Volgende Stap

6E-11 blijft **NO-GO**, ook los van de IO-waarschuwing door ontbrekend meetpaar 113.
Geen 6E-12. Eerst uitsluitend offline hash-equivalentie en runnerbegrenzing ontwerpen
en testen. Hosted hervatting vereist daarna afzonderlijk aantoonbaar:
geen actieve ongecontroleerde processen, normaal responsgedrag, stabiel IO-budget
met bruikbare uurmetadata, gelijkwaardige bewijsdekking en geen beschermde datadrift.
De laatste schone datameting van VOOR deze pauze mag niet als verse controle worden
gepresenteerd. Tijdens de IO-pauze is geen nieuwe 143-tabellenscan toegestaan.

Lokale/remote HEAD opnieuw read-only bevestigd:
`96fc380e47420474efde5509eab0a944398b1190`.
Bestaande vuile werkboom behouden. Geen commit, push of publicatie in dit onderzoek.
Laatste historische migrationstatus 39/39, dry-run leeg; niet opnieuw uitgevoerd.
Laatste historische Pagescontrole 84 assets identiek / 304 afgeschermde paden 404;
geen nieuwe publicatieclaim. Runtime en frozen bronnen niet gewijzigd door IO-werk.

## Bewijsbestanden En Controles

Nieuwe metadata: [PHASE6E11_DISK_IO_OBSERVATIONS.json](PHASE6E11_DISK_IO_OBSERVATIONS.json).
SHA256: `289daf04eb1350e67c019831a4694d144b0019e1fdd0923b519d5d6a667b29da`.

Nieuwe immutable lokale receipts in `supabase/.temp/`, elk met SHA256-sidecar:
- `phase6e11-io-metrics-6bdced8fbab9422ea3d0906f88693c31.json`
  SHA256 `8c0901d58d64d699b9d3c2739292a365761f92082c55f5578c09bd08240e7090`.
- `phase6e11-io-metrics-179de1b5d49240e5b528fe7068c407ba.json`
  SHA256 `2102a9d8c69ade1a75bd4bd2143fd0edfaed11fb5d2e2a5e5cec259fd6912039`.
- `phase6e11-io-local-a36621fbdec74d45970497e564c60b6e.json`
  SHA256 `fd3ac4886505a58ad83f4809ee193944ed8860f1a309204b439b44c4af3cff98`.
- `phase6e11-io-services-ceb4217fa0c0427892eff85f8e8c7ccf.json`
  SHA256 `bb84a5785443599d1175c12031818005bd0e80d682c43c3e3a2b1ce8efbc72f2`.

Lokale inventaris leest 2.166 JSON-bestanden, alle aanwezige sidecars kloppen.
12 lokale parser-/deduplicatie-/sanitizatietests PASS, zonder credentials of netwerk.
Geen applicatiesuite of hosted proofrun opnieuw gestart. Behouden historisch bewijs,
fixtures en eerdere nulmetingen niet overschreven of verwijderd.

Officiele bronnen, geraadpleegd 22 september:
[Compute en Disk IO](https://supabase.com/docs/guides/platform/compute-and-disk),
[Disk IO troubleshooting](https://supabase.com/docs/guides/troubleshooting/exhaust-disk-io),
[Metrics](https://supabase.com/docs/guides/observability/metrics),
[Changelog](https://supabase.com/changelog).
Managementlogs gebruiken de huidige `logs`-route, niet de aangekondigde vervallen
`logs.all`-route. Geen provider- of goedkeuringsinstellingen aangepast.

External AI calls/cost: **0 / EUR 0.00**.
Real-member AI enabled: **NO**.
Production touched: **NO**.
