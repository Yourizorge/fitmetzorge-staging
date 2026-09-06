# Package 6D Final Owner Mobile Hotfix - Technisch Rapport

Datum: 2026-09-06.
Status: **PACKAGE 6D FINAL OWNER MOBILE HOTFIX - READY FOR FINAL OWNER RETEST**.
Niet owner-accepted of frozen. Geen billing of volgende package gestart.

## 1. Scope En Preflight

Enige werkrepository:
`C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy`.

Bij aanvang: schone `main`; lokale HEAD, origin/main en werkelijke remote main
`f881ea968b2f3453e525caa1205a8f686b3613b1`. De oudere verwachte
`977e2311e969cb17dc753c007c3b3187675e4530` hoort bij de oorspronkelijke
reconciliation-opdracht en is door eerdere goedgekeurde stagingcommits opgevolgd.
AGENTS.md, .codex/config.toml, actuele status/plan/architectuur/testmatrix,
reconciliation, public-auth en Package 6D-documenten zijn gelezen.

Projectconfig: on-request, auto_review, workspace-write, network_access=true en
permanente staging-autonomie. Managed netwerkbeperkingen blijven leidend; de
bestaande review/escalatieroute is gebruikt. Geen globale permissies aangepast.
Uitsluitend Yourizorge/fitmetzorge-staging, Supabase mokxyyullfhkfalopbzd en
[stagingfrontend](https://yourizorge.github.io/fitmetzorge-staging/) gebruikt.

De nieuwste ownerbijlage vervangt de eerdere bredere hotfixopdracht: precies het
dashboard en mobiele analysedetail zijn gecorrigeerd. Chat, avatar, instellingen,
taal, tijdzone, recovery en automatische mockworker blijven behouden.
Geen mail verzonden, Brevo-onderzoek, handmatige accountbevestiging of bestaande
trainerrol/koppeling gewijzigd. De bevestigde ontvangst van de accountmail blijft PASS.

## 2. Dashboard: Oorzaak En Herstel

De bestaande get_inbox-RPC begon bij member_notifications met een INNER JOIN en
filterde uitsluitend new/later. Het dashboard gebruikte dezelfde unread-items als
de toast en toonde maximaal vijf. Daardoor verdween een gelezen analyse automatisch
uit het dashboard, ondanks een beschikbaar analyseresultaat. Een resultaat zonder
notificationrecord kon helemaal niet zichtbaar worden.

Live read-only nulmeting, zonder persoonlijke inhoud of IDs te publiceren:
- Een post_workout-resultaat was ready, beschikbaar en had notificationstatus opened.
- Een daily-resultaat was partial en beschikbaar, maar had geen notificationrecord.
- Beide vielen aantoonbaar buiten de oude dashboardfilter.

Dit was geen mislukte analysecompletion en geen ontbrekende loginhydration.
De bestaande oefen-/analyse-ID-relatie was intact. Het serverselectiecontract was fout.

De get_inbox-RPC leest nu beschikbare eigen ai_analysis_results en LEFT JOINt de
eigen notificationstatus. Beschikbaar betekent ready/partial/insufficient_data,
geen verwijderde content, niet verlopen en niet gearchiveerd. Resultaten zonder
notification krijgen alleen in de respons standaardstatus new: GET schrijft niets.

Dezelfde RPC retourneert:
- recent: de drie nieuwste beschikbare resultaten, inclusief opened.
- items: maximaal vijf new/later-resultaten voor toast en unread-weergave.
- unread_count: het volledige aantal beschikbare new/later-resultaten.
- Type, korte titel (maximaal 120 tekens), datum/tijd en exacte analyse-ID.
Sortering: completed_at, anders created_at, aflopend, met analyse-ID als stabiele tie-breaker.

Nieuw en Later tonen Nieuw. Now/opened behoudt de kaart zonder Nieuw. Archiveren
verwijdert alleen de betreffende recente kaart; het resultaat blijft via Alle analyses
bereikbaar binnen bestaande bewaartermijnen. Verwijderen gebruikt de bestaande
own-user revision-bound delete. Nieuwere resultaten verdringen alleen de oudste kaart.

Alleen een expliciete memberactie kan via mark_notification de ontbrekende status
aanmaken. Een unieke member/result-upsert voorkomt duplicaten. Archived blijft
dominant en een late Later mag opened niet terugzetten. De resultaatrij wordt
gelockt om een race met verwijdering te serialiseren, niet herschreven.

De browser gebruikt recent, geen lokale persistente analysekopie. Auth/profile/epoch
guards blijven behouden. Een nieuwe inboxVersion verwerpt een oude inflight snapshot
na een statusactie en forceert een verse serverread. De race is bewust vertraagd getest.
Hydration gebeurt bij login/refresh, terugkeer naar het dashboard, AI-state-events,
focus/visibility/online en elke 45 seconden wanneer zichtbaar. Geen logout/login nodig.
De bestaande minuutcron blijft ongewijzigd; normale detectie kan circa twee minuten
vragen door cron plus zichtbare refresh, zonder realtime-pushclaim.

## 3. Mobiele Overflow: Oorzaak En Herstel

De globale styles.css bevat een table min-width van 860px. Het analysedetail zette
wel width:100% en table-layout:fixed, maar reset die minimummaat niet.
Lange ononderbroken oefennamen in h3 verbreedden bovendien het scrollende main.

De echte app met volledige productie-CSS reproduceerde bij 320x700:
- html/body waren al 320/320: alleen die check zou het defect dus missen.
- main had clientWidth 302 en scrollWidth 3772.
- De tabel was 860px breed; een lange h3 had scrollWidth 3760.
- 35 zichtbare elementen hadden horizontale overschrijding.
- De geopende analyse had nul dashboardkaarten.

Het eerdere isolated analyseharnas gebruikte een minimaal gestileerd testdocument,
niet de volledige applicatiestylesheet. De eerdere assembled ownertest controleerde
alleen de buitenste dialogbreedte. Beide bewijzen waren onvoldoende voor interne
overflow. Die historische PASS wordt niet als bewijs voor dit defect hergebruikt.

De productruntime zelf is nu gecorrigeerd met uitsluitend scoped analysedetailregels:
minmax(0,1fr), min-width:0, max-width:100%, border-box en overflow-wrap:anywhere;
table min-width wordt gereset, code/pre wrappen en media blijven binnen hun container.
Op maximaal 480px staan vergelijkingsrijen gestapeld met gelokaliseerde labels voor
de huidige en vorige training. Header/export/delete/close passen zonder horizontaal
swipen. Geen nieuwe globale overflow-x:hidden-maskering toegevoegd.

## 4. Gerenderd Bewijs

Nieuwe test: assets/phase6d-final-mobile-browser-check.cjs.
De volledige index, appmodules en stylesheets worden geladen. Alleen synthetische
Auth/RPC-antwoorden worden ingebracht; geen stylesheet wordt vervangen of toegevoegd.
Live-modus haalt de werkelijk gepubliceerde assets op. Echte Supabase-memberrequests
worden geblokkeerd en de test eist dat er geen zijn. Dit is geen echte memberlogin.

| Viewport | html en body scroll/client | Detail main scroll/client | Overbrede descendants |
| --- | --- | --- | --- |
| 320x700 | 320/320 | 302/302 | 0 |
| 360x800 | 360/360 | 342/342 | 0 |
| 390x844 | 390/390 | 372/372 | 0 |
| 820x1180 | 820/820 | 758/758 | 0 |
| 1440x900 | 1440/1440 | 758/758 | 0 |

Per viewport: NL, EN, DE, zonder vorige training en refresh/deep link. In totaal
25 layouts met 77-85 zichtbare elementen per layout, elk op geometrie en interne
scrollbreedte gecontroleerd. Zeer lange titels/oefennamen/woorden, grote getallen,
UUIDs, datums, veiligheidsinhoud, export/delete en de vaste header zijn opgenomen.
Lokale, verse-checkout- en live-assetsruns: elk 180/180 PASS.
Mobiele en desktop screenshots zijn visueel bekeken; gestapelde waarden blijven leesbaar.
De extreem grote waarden zijn uitsluitend stresstestfixtures, geen memberdata.

De compacte gecommitteerde
[bewijsregistratie](PACKAGE6D_FINAL_OWNER_MOBILE_HOTFIX_EVIDENCE.json) bevat layoutmetingen,
asset-SHA256s, SQLchecks, functionpariteit, migratiehistorie en 23 before/after-fingerprints.
Uitgebreide per-descendant JSON en screenshots staan lokaal onder
`supabase/.temp/final-mobile-*`; synthetisch en Git-ignored.

## 5. Verplichte 25 Acceptatiegevallen

Alle onderstaande resultaten zijn technische PASS; fysieke owneracceptatie staat apart.

| Nr | Ownergeval | Bewijs |
| --- | --- | --- |
| 1 | Nieuwe post-workout automatisch zichtbaar | SQL completion-trigger + nieuwe readmodelselectie; browserhydratatie zonder login |
| 2 | Nieuwe analyse Nieuw | SQL state en browserbadge, vijf viewports |
| 3 | Later behoudt kaart | SQL later + browseractie, Nieuw blijft |
| 4 | Nu opent exact resultaat | Exact-ID RPC-argument en gerenderd detail |
| 5 | Bekijken verwijdert kaart niet | SQL recent + browser na mark opened |
| 6 | Gelezen zonder Nieuw | SQL opened + afwezige browserbadge |
| 7 | Refresh behoudt kaart | Serverread + browserreload/deep link |
| 8 | Nieuwe login behoudt kaart | Verse identityhydration + browserlogout/login |
| 9 | Hoogstens drie recente | SQL limiet/sortering/verdringing + browser exacte top drie |
| 10 | Alle analyses geschiedenis | SQL list + browser inclusief gearchiveerd resultaat |
| 11 | Exact verwijderen | SQL/browsers verwijderen alleen synthetisch gekozen resultaat |
| 12 | Exact archiveren | SQL/browsers: kaart weg, andere kaarten/resultaat behouden |
| 13 | Geen duplicaten | Unieke SQL completion/upsert + retry/refresh + vertraagde stale-response-test |
| 14 | Cross-member isolation | Echte rollback-SQL: andere member, trainer en anon geweigerd; geen grants |
| 15 | Geen overflow 320px | Live-assets alle descendants + html/body/main, vijf scenario's |
| 16 | Geen overflow 390px | Idem; ook 360px PASS |
| 17 | Tablet/desktop | 820x1180 en 1440x900, geometrie en screenshots |
| 18 | Lange NL/EN/DE-content | Elke taal op alle vijf viewports, lange ononderbroken tekst |
| 19 | Huidige/vorige leesbaar | Gestapeld mobiel; kolommen desktop; geen vorige expliciet |
| 20 | Geen beschermende test-CSS | Volledige echte stylesheets, geen CSS-injectie; before/after dezelfde meetmethode |
| 21 | Chat/avatar/settings/taal/recovery | Assembled ownerbrowser 323/323, bestaande modulebronnen behouden |
| 22 | Frozen regressies | Volledige runner exit 0; aanvullende Auth, handlers en workoutvolgorde PASS |
| 23 | Live gelijk Git | 41 assets HTTP 200 en byte-identiek aan runtimecommit, inclusief styles.css/config.js |
| 24 | Productie onaangeraakt | Alle write/deploytargets uitsluitend staging; nul productiehandelingen |
| 25 | Externe AI-calls/kosten 0 | Live mock-only/workerconfig en runkostencheck; geen provideractivatie; EUR 0.00 |

## 6. SQL, Tests En Datagevolgen

Enige nieuwe migration:
`20260906134827_phase6d_recent_dashboard_analyses.sql`.
CLI 2.115.0 genereerde deze versie. De CLI kreeg bij migration new in de bestaande
migrationsdirectory AlreadyExists; generatie in een lege, genegeerde scratchworkdir
leverde de echte timestamp. Canonical migrations zijn niet verplaatst of verwijderd.
De beoordeelde SQL vervangt uitsluitend get_inbox en mark_notification, met dezelfde
RPC-ACLs en expliciete membercontrole. Geen tabel/backfill/scheduler/providerwijziging.

Voor toepassing: nieuwe 40-check transactionele suite en oude workerregressie 59/59
met nieuwe functiedefinities, alles rollback. Dry-run bevatte uitsluitend deze migration.
Daarna via CLI toegepast op mokxyyullfhkfalopbzd; de toegepaste migration is niet aangepast.
Na toepassing: canonieke nieuwe suite 40/40 rollback, read-only verifier 18/18,
beide live function bodies gelijk aan de migration, vaste search_path en ACLs intact.
Migration list 30/30 en dry-run upToDate=true, migrations/seeds/roles leeg.

Aanvullend tijdens deze hotfix:
- Owner assembled browser 323/323; public Auth browser 88/88; Auth static 26/26.
- Chat/analysis handler tests 27/27, mock-only; workout flush-order 6/6.
- Frozen static: Phase 1 75, Member UX 56, Phase 2 46, Phase 3 222, Phase 4 90,
  4F-E 45, Phase 5 116, 6A 93, 6B 98, 6C 117; 6D focused static 17.
- Frozen browsers: 6D0 41, Phase 5 53, 6C 85, Nutrition 138.
- Invite handler en canonieke migrationidentitysuite: exit 0.
- Syntaxcontrole en git diff --check PASS.
- Live publieke routes op vier viewports: nul errors en mutating requests.

Oude cachetokenasserties zijn gericht bijgewerkt voor alleen de gewijzigde entry/inbox/CSS.
Een eerste ownerbrowserrun selecteerde de nu ook achter de modal bestaande dashboardknop;
de historieselector is specifiek op de chatmodal begrensd. De definitieve runs zijn groen.

Alle 21 bestaande allowlisted member/domain/safetytabellen plus member_notifications
en member_app_preferences hebben exact dezelfde rijtellingen en inhoudshashes als de
verse nulmeting van deze hotfix. Geen vergelijking met verouderde hashes van voor de
ownerretest. Alle transactionele synthetische fixtures zijn teruggedraaid; restanten nul.
Geen bestaande analyse, notification, settings, chat, safety of trainingsdata aangepast.
De enige blijvende DB-wijziging is het tweefunctiecontract plus de nieuwe historyrij.

Security advisor: dezelfde 96 notices voor en na, nul toegevoegd of verwijderd:
28 INFO [RLS zonder policy](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy),
1 [mutable search_path](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable),
66 [authenticated SECURITY DEFINER](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable),
1 [leaked-password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).
Dit is geen all-green securityclaim. Browsergrants, own-userbinding en trainer/anon-denials
zijn afzonderlijk getest. Onverwante bestaande advisories zijn niet veranderd.
De gebruikte [officiele functiehandleiding](https://supabase.com/docs/guides/database/functions)
ondersteunt expliciete search_path/EXECUTE-beperking; de changelog.md-fetch leverde 400,
dus geen claim dat die changelog inhoudelijk gelezen kon worden.

## 7. Reconciliation, Verse Checkout En OneDrive

De eerdere reconciliation blijft opgelost; geen history-repair/replay/reset of wijziging
van de bronbaseline. Deze hotfix voegt alleen de 30e migration toe.

Verse committed checkout van runtime 468d450329700028add8d13eb74c44931ab0389e:
`C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\final-mobile-fresh-checkout`.
Clone-local core.longpaths=true, schone main, browser 180/180, migration list 30/30
en lege staging-dry-run. Dit is bronreproduceerbaarheid, geen volledige lokale DB-replay.

De eerdere lokale PostgreSQL-build kon 22 migrations uitvoeren en sloeg zeven wegens
ontbrekende pg_cron over; Docker is niet beschikbaar. Voor deze tweefunctiehotfix is
geen nieuwe volledige lokale database opgebouwd. Een volledige 30-migration-replay
en globale zero schema-diff zijn niet bewezen. Wel zijn de twee gewijzigde live
function bodies exact vergeleken. Voor volledige replay is later een compatibele
lokale Supabase/PostgreSQL-runtime met pg_cron nodig, nooit een staging reset.

Opnieuw uitsluitend read-only gecontroleerde, behouden paden:
- `C:\Users\Fitme\AppData\Local\Temp\fmz-local-rebuild-YsUaP4`
- `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-tc26YR`
- `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-YIC31o`

De twee OneDrive-entries hebben Directory/ReparsePoint-attributen (1040); deze
Get-Item-meting geeft geen resolved LinkType/Target terug. Het volledige manifest
van de 971 verwijderdoelen, waaronder config_exec_params/pg_control, is nog niet
beschikbaar. Geen doel wordt hierdoor als disposable gecertificeerd. Niets verwijderd:
geen PostgreSQL-bestanden, canonical migrations, bronnen, documenten, Git of stagingdata.
Voor eventuele latere cleanup is eerst het volledige doelmanifest met resolved absolute
paden/reparse-targets en clusterherkomst vereist. Tot dan blijft items behouden leidend.

## 8. Commits En Deployment

Runtime/test/migrationcommit:
`468d450329700028add8d13eb74c44931ab0389e`
(`fix(phase6d): retain recent analyses and bound mobile details`), gepusht naar staging main.
Cache entry/inbox/detail-CSS: `20260906-final-mobile1`; overige runtimecachetokens behouden.
Alle 41 gecontroleerde assets zijn live commit-identiek. De aanvullende assetchecker
controleert nu expliciet ook globale styles.css en config.js.
Dit rapport, bewijs, relevante statusdocs en die checkeruitbreiding krijgen een aparte
logische documentatie/verificatiecommit; de exacte finale hash staat in de eindoplevering.

Frontend is via staging main gepubliceerd. Supabase migration toegepast; Edge youri-ai
v43 ACTIVE/JWT=true behouden, geen bronwijziging of onnodige Edge-redeploy.
Geen productie-, provider-, betalings-, SMTP- of externe infrastructuurdeployment.

## 9. Resterend En Exacte Volgende Stap

Geen technisch blocker voor deze gerichte staging-hotfix. Fysieke ownerretest is nog
nodig; de browsertests zijn geen bewijs van een daadwerkelijke iOS/Android-aanmelding.
Volledige lokale pg_cron-replay/schema-diff en een gecertificeerd OneDrive-delete-manifest
blijven afzonderlijke beperkingen, niet stilzwijgend opgelost.

Open [staging](https://yourizorge.github.io/fitmetzorge-staging/) opnieuw op de telefoon
en ververs met het bestaande account, zonder nieuwe mail of trainerrol.
Controleer de bestaande trainingsanalyse bij Klaar voor jou. Open haar en sluit:
de kaart blijft staan zonder Nieuw. Ververs en meld opnieuw aan: dezelfde kaart blijft.
Controleer een nieuw mockresultaat met Later en Nu, maximaal drie recente kaarten en
Alle analyses. Bekijk het detail in portret, inclusief vergelijking en lange teksten:
geen horizontaal swipen nodig, header/export/delete zichtbaar. Delete/archive alleen
op een bewust gekozen synthetisch owner-testresultaat. Controleer kort dat chat,
avatar en instellingen nog hetzelfde werken.

Daarna is expliciete ownerbevestiging vereist voordat Package 6D accepted/frozen mag
worden. Geen volgende package of productiehandeling wordt automatisch gestart.
