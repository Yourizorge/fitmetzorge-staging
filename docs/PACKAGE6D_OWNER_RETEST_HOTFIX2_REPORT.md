# Package 6D Owner Retest Hotfix 2 - Technisch Rapport

Datum: 2026-09-06.
Status: **PACKAGE 6D OWNER UX HOTFIX 2 - READY FOR OWNER RETEST**.
Package 6D is niet owner-accepted of frozen. Dit rapport vervangt voor de actuele
oplevering de eerdere handmatige analyseflow en hotfix-1-indeling.

## 1. Preflight En Grenzen

- Enige werkrepository: `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy`.
- Branch `main`; aanvankelijk schone worktree. Lokale HEAD, origin/main en werkelijk
  remote main waren `5c10ccf9ffec8871a6c3e7fb63143591c449c265`.
  De veel oudere verwachte `977e2311e969cb17dc753c007c3b3187675e4530` hoort bij de
  oorspronkelijke reconciliation-opdracht, niet bij deze later aangeleverde hotfix.
- AGENTS.md en .codex/config.toml gelezen: on-request, auto_review, workspace-write,
  project-network true en permanente staging-autonomie. Managed netwerkbeperkingen
  blijven leidend; noodzakelijke tools gebruikten de bestaande review/escalatieroute.
  Geen globale toestemming of writable root aangepast.
- Alleen `Yourizorge/fitmetzorge-staging`, Supabase `mokxyyullfhkfalopbzd` en
  [stagingfrontend](https://yourizorge.github.io/fitmetzorge-staging/) zijn gebruikt.
- De nieuwste ownerbijlage autoriseert hotfix 2 en automatische mockanalyses.
  Productie, echte member-providerprocessing, betalingen en nieuwe kosten bleven verboden.
- Owner-mailuitkomst behouden: geen resend, Brevo-onderzoek, handmatige bevestiging,
  trainerrol of trainerkoppeling op het bestaande testaccount.

## 2. Oorzaken En Herstel

| Bevinding | Aantoonbare oorzaak | Herstel |
| --- | --- | --- |
| Onrustige chat/composer | Bestaande chatgrid, meerdere kaders en een zichtbaar label namen composerbreedte in; dialog/scroll/keyboard waren onvoldoende op elkaar afgestemd. | Een flexkolom, rustige header, een scrollende tijdlijn, horizontale groeiende composer met schermlezerlabel en visualViewport-hoogte. |
| Teruglezen/geschiedenis | Her-renderen en vertraagde RPC-antwoorden konden scroll/selectie opnieuw bepalen. | Scrollanker, nabij-onderkant-follow, thread-drafts, historiepagina's, titels/datum en member/epoch/sequence-guards. |
| Avatar onduidelijk | De goedgekeurde avatar had geen chatbetekenis naast de afbeelding. | Chatballon rechtsonder binnen dezelfde knop; aparte unread-indicator; slepen/tikkencontract behouden. |
| Analyse afhankelijk van knop | Er waren prepare/analyze/due-select RPC's, maar geen actieve unattended dispatcher of completed-workoutqueue. | Private unieke jobqueue en echte minuutcron, gedeelde gates en deterministische servermock. |
| Laatste trainingssets | Completed-sessionopslag kon de gebeurtenis opleveren voordat de laatste sets authoritative waren gesynchroniseerd. | Minimale Phase 3-correctie: eerst actieve sets flushen, dan completion; mislukte online flush levert geen completion op. |
| Resultaat niet betrouwbaar bereikbaar | Lijstweergave had geen gedeelde exact-ID-detailroute vanuit melding/dashboard/deep link. | Een own-user read_analysis-route met detaildialog, export en bestaande revision-bound delete. |
| Geen werkende melding/Later | Geen authoritative notificationcontract of persistente deferred-inbox aangetroffen; evenmin veilige OS-pushinfrastructuur. | Een RPC-only member_notifications-autoriteit, resulttrigger, Now/Later/opened/archived en bounded dashboard. |
| Instellingen naast elkaar | Het centrale dialog toonde verschillende tab/formulierblokken tegelijk en bleef ook onderin bereikbaar. | Verticale hoofdmenulijst, een vervolgscherm per onderwerp, terugknop; settings/AI uit bottomnav. |
| Handmatige tijdzone/wereldbol | Vorige hotfix bood algemene tijdvelden en een generieke taaltrigger. | Automatische IANA-device-sync; alleen analyseklok/dag editable; NL/GB/DE-vlaggen met volledige labels. |
| Billing niet operationeel | Er is nog geen Phase 7-betaalcontract. | Geen schijnfix: alleen serverplan/status; billing expliciet voor Phase 7 op dezelfde instellingenlocatie. |

De goedgekeurde avatar is byte-identiek: SHA-256
`257f31e6fe4faa7fecf5fb9874eed06d4018dc8c60958aa714e7d4b79a7517dc`.
Lucide 0.468.0 en flag-icons 7.2.3 zijn lokaal gepind met hun licenties.
GB is de expliciete Engelse taalvlag; de vlag is nooit het enige toegankelijke label.

## 3. Automatische Serververwerking

Migration: `supabase/migrations/20260906092905_phase6d_automatic_inbox.sql`.
Nieuwe objecten: `ai_private.analysis_jobs`, `public.member_notifications`,
workout/resulttriggers, vier own-user RPC's, private prepare/comparison/mock/workerhelpers,
een thread-title-uitbreiding en de runtimeflag `inbox_worker_enabled`.
Geen brondata-backfill, historische migration-repair, SQL-replay of remote reset.

Een succesvolle completed-write maakt precies een job per member/kind/event.
De worker `fmz-phase6d-inbox-mock-worker` draait iedere minuut, batch 10 (maximum 50),
met singleton advisory lock en SKIP LOCKED. Hij controleert de actuele planning,
entitlement, aparte analyseconsent, leeftijd, safety, kwaliteit en budget opnieuw.
Technische/gate-retries krijgen een korte veilige foutcode en vijf minuten uitstel.
Een verouderde dag/weekjob wordt geannuleerd; aangepaste dag/klok wordt bij uitvoering
opnieuw beoordeeld. Bestaande/deleted-resultidentiteit voorkomt recreatie.

Dagelijks: lokale datum, maximaal eenmaal per datum, Luna.
Wekelijks: lokale ISO-week, gekozen dag en tijd, maximaal eenmaal per week, Terra.
Post-workout: exact authoritative completed-session-ID, Luna. Geen historische backfill.
Modelnamen zijn registraties, geen externe calls. Alleen mock-enabled + scheduled-enabled
+ worker-enabled + external-provider-disabled laat de worker door.
Dezelfde manifests, service begin/complete, budgetaccounts, runs en usage ledger blijven
de autoriteit. Output bevat `actions: []`, geen schemawijziging, diagnose of providercall.

Veilige operationele stop, uitsluitend in staging: zet
`ai_private.phase6d_runtime_config.inbox_worker_enabled=false` voor de singletonrij.
Dit stopt verwerking zonder brondata/resultaten/jobs te wissen. Herstel naar true mag
alleen met dezelfde mock-only gates. Een migrationrollback, tabeldrop of remote reset
is hiervoor niet nodig en is niet uitgevoerd.

Vergelijking: dichtstbijzijnde eerdere eigen completed training met dezelfde programmadag;
zonder programmadag een identieke, niet-lege oefeningenset. Geen passende vorige training
betekent expliciet eerste geschikte vergelijking. Maximaal 20 oefeningen. Bekende sets,
reps, gewichten, volume en RPE/RIR blijven herleidbaar; incomplete gegevens blijven
onbekend, niet nul of verzonnen. Beide training-ID's en datums zijn zichtbaar.
Duur is verstreken timestamp-tijd inclusief pauzes, niet bewezen actieve trainingstijd.
Een lager volume bewijst geen vermoeidheid; de reflectie blijft voorzichtig/read-only.

## 4. Resultaten, Inbox En Instellingen

Alle toegang gebruikt exact hetzelfde resultaat-ID: melding, dashboard, geschiedenis,
`#analysis=UUID` of `?analysis=UUID`. De server controleert eigendom, vervaldatum en
verwijderstatus. Interne user/request/run/manifest/eventmetadata wordt gestript.
Detail toont type, periode/tijdzone, kwaliteit, mock/model, huidige/vorige training,
gemeten verschillen, observaties, onzekerheden en veilige reflectie. Export is eigen
JSON; verwijderen gebruikt de bestaande expected-revision/confirmationflow.

De resulttrigger maakt een melding bij ready/partial/insufficient_data.
Nu bekijken opent exact dat resultaat en markeert opened. Later blijft server-side staan,
ook na refresh/login; een vertraagde Later-request kan opened niet terugdraaien.
Dashboard toont maximaal vijf nieuwe/uitgestelde items plus Alle analyses.
Geschiedenis is gepagineerd. Verwijderen archiveert de bijbehorende melding.
De niet-focusstelende in-app toast verdwijnt tijdens kritische schermen/dialogs/input.
De browser leest bij app-lifecycle/focus/online en iedere 45 seconden alleen wanneer zichtbaar.

Geen service worker, push subscription, VAPID of OS-deliverycontract is aanwezig.
Geen nep-push of browsertoestemmingsprompt toegevoegd. Echte OS/browserpush blijft
Phase 8-notificationbeleid plus Phase 12-mobile/PWA-delivery, met quiet hours, caps,
toestemming, tokenopruiming en own-user deep links.

Instellingen: Account, Privacy/gegevens, AI, Abonnement, Taal, Voorwaarden,
Privacyverklaring en Uitloggen, ieder met eigen vervolgscherm en terug.
Alle algemene AI-instellingen staan onder Instellingen > AI, niet onder de chat.
Safety-recovery blijft expliciet en revision-bound; historische safety/events blijven intact.
Nieuwe risicorevisie blokkeert opnieuw. Private-chatconsent blijft onafhankelijk.

Device-IANA-timezone wordt bij init/login/refresh/focus/visibility opnieuw gesynchroniseerd,
zonder wijziging van de gekozen analyseklok/dag. Browserwaarden zijn geen autorisatie.
Taal gebruikt dezelfde eigen user_settings-bron via quick choice en Instellingen > Taal.
Phase 7 sluit later maand/jaar, upgrade/downgrade, opzeggen, betaalgegevens en facturen aan.
Huidige UI maakt geen browser-entitlement, succesvolle betaling of opzegging na.

## 5. Echte Cronproef En Datagevolgen

De runtimefrontend was live geverifieerd voordat de worker werd geactiveerd.
Op 2026-09-06 12:52:12 UTC werd precies een nieuw synthetisch account gemaakt:
`hf2-cron-proof-20260906@example.invalid`, UUID
`cba55bb3-aa68-4d8f-b705-347cf724626f`. Geen email, Auth-login of tokenuitgifte.

Alleen die fixture kreeg tijdelijke entitlement, consent, UTC-planning en twee trainingen:
vorige `65c53d83-4862-489d-9e21-354ca305af22`, huidige
`ceb98e91-1e69-4b2d-a217-9c4814b4755f`.
Twee sets van 30 kg x 10 tegenover twee van 35 kg x 10: volume 600 tegenover 700;
RPE 7 tegenover 8, RIR 2 tegenover 1. De dubbele completed-update maakte geen tweede job.

Zonder handmatige worker-call verwerkte cron om 12:53:00 UTC alle vier jobs:
daily, weekly en de twee afzonderlijke workout-events. Vier exacte resultaten en
vier nieuwe meldingen, alle jobs attempts=1. De eerste workout had geen verzonnen
voorganger. De weekanalyse registreerde Terra/mock en onvoldoende data zonder observaties.
Om 12:54:00 UTC slaagde de volgende echte cronronde: nog steeds vier resultaten en
vier meldingen, geen duplicaat. Alle runs mock, cost_micros=0 en actions leeg.

Na controle van FK-cascades en exacte fixture-identiteit werd uitsluitend dit nieuwe
Auth-account verwijderd, met zijn eigen afhankelijke rijen. Cleanup om 12:59:19 UTC:
Auth/profiel/workouts/sets/results/jobs/notifications/runs allemaal nul.
Er zijn geen bestaande memberrijen verwijderd om tests te laten slagen.
De worker blijft ENABLED/mock-only; daarna verifier 23/23, queued_jobs=0,
notifications=0 en laatste cronruns succeeded.

De 21 allowlisted member/safety/domeintabellen hebben voor migration, na migration
en na fixturecleanup exact dezelfde counts en canonieke JSON-content-MD5.
Dit bewijst die 21 tabellen, niet een onuitgevoerde volledige databasebytevergelijking.
Nieuwe runtimeflag, schema, cronmetadata en tijdelijke synthetische rijen zijn de
bedoelde technische gevolgen. Geen providercall, externe AI-kosten of productieactie.

## 6. Tests En Live Verificatie

| Controle | Resultaat / betekenis |
| --- | --- |
| Hotfix-2 SQL, transactioneel rollback | 59/59, inclusief jobs/dedupe, vergelijking, routes, gates, tijdzone en isolation |
| Vorige recovery/settings SQL met nieuwe migration | 50/50, rollback |
| Current 6A contract | 47/47 |
| Actieve worker/schema/ACL/RLS-verifier | 23/23, worker=true, geen fixtures |
| Live 6B / 6D0 / basis 6D metadata | 36/36 / 40/40 / 4/4 |
| Live 6C transactioneel + request-scoped safety | overall_pass=true, fixtures_remaining=0 |
| Live 6D transactional | exit 0, rollback |
| Live 6D0 autorisatie | 48/48, rollback |
| Assembled ownerbrowser | 323/323 bij 320x700, 390x844, 820x1180, 1440x900; nogmaals vanuit verse clone |
| Workout flush-order test | 6/6; online fout/offline geven geen onterecht serverevent |
| Auth browser / focused static | 88/88 / 26/26, zonder echte mail |
| Chat + analysis Node handlers | 27/27, mock-only |
| Phase 1 / member UX / 2 / 3 static | 75 / 56 / 46 / 222 PASS |
| Phase 4 / 4F-E / 5 / 6A / 6B / 6C / 6D static | 90 / 45 / 116 / 93 / 98 / 117 / 17 PASS |
| 6D / 6D0 / 6C / 5 / Nutrition browserregressies | 48 / 41 / 85 / 53 / 138 PASS |
| Finale frozen regression runner | Alle suites exit 0, inclusief invite-handler en migration-identity |
| Live frontend | 39 HTTP-200 assets exact runtimecommit; vier publieke viewports, nul errors/mutaties |
| Edge | youri-ai ACTIVE v43, verify_jwt=true; ongeauthenticeerde analysis-route HTTP 401 |
| Migration list / dry-run | 29/29, upToDate=true, migrations/seeds/roles leeg; ook verse clone |
| Bestaande memberdata | 21/21 counts/hashes ongewijzigd |
| git diff --check | PASS voor runtime en documentwijzigingen |

Browsertests draaien de echte geassembleerde frontend met synthetische Auth/RPC/Edge.
Ze zijn geen claim van echte Safari/iOS/Android-toetsenbordacceptatie. Screenshots zijn
visueel gecontroleerd; keyboard/viewport/travel wordt gesimuleerd. De live publieke
browsercheck is read-only. Echte ingelogde ownertelefoontests blijven de volgende stap.

Oude 6A-installatie/freezeverifiers verwachten globale policy/documentaantallen en oude
digest-search-pathnamen die al door goedgekeurde 6C/6D-wijzigingen achterhaald zijn.
Hun ruwe failures (6 installatie, 3 oude freeze) worden niet als PASS gepresenteerd.
De nieuwe current-contractverifier behoudt de 47 controles voor de oorspronkelijke
objecten; nieuwe consent/policy/RPC-objecten worden apart getest. Geen securitygate
is weggehaald om een groene teller te krijgen.

## 7. Advisors En Resterend Risico

Security advisor: voor 91 (27 INFO, 64 WARN), na 96 (28 INFO, 68 WARN), nul ERROR.
Nieuw: private jobs zonder browserpolicy (bewuste deny-all) en vier authenticated
SECURITY DEFINER-member-RPC's, alle auth.uid-bound met deny/cross-membertests.
Zie [RPC-advisor](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable)
en [private RLS-advisor](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy).
Bestaand en niet stilzwijgend gewijzigd: mutable search_path van public.touch_updated_at
([remediatie](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable))
en disabled leaked-password protection
([Auth-instelling](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)).
Deze constateringen zijn geen nieuw aangetoonde hotfix-exploit; ze blijven expliciet open.

Performance advisor: 16 unindexed-FK INFO, 34 unused-index INFO en 47 auth-RLS-initplan WARN.
Geen notice benoemt de twee nieuwe tabellen; geen performance-ERROR.
Bestaande brede databaseoptimalisatie is niet als ongerelateerde refactor meegenomen.

## 8. Migration-Reconciliation, Verse Checkout En OneDrive

De eerdere 19 timestampverschillen, drie ontbrekende naamregistraties, dubbele oude
versie en ontbrekende basis-SQL blijven opgelost volgens
[historisch bewijs](PROJECT_MIGRATION_RECONCILIATION.md).
Een byte-exacte oorspronkelijke Phase 1-3-series was niet aantoonbaar terug te vinden;
de eerdere veilige sourcebaseline is geen claim van herontdekte historische SQL.
Deze hotfix voegt alleen de 29e migration toe en heropent geen history-repair.

Verse clone van committed runtime:
`C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\hf2-fresh-checkout`.
HEAD 2e1fd983385ad360632667c954d7f63725555b3c, schone main. Alleen clone-local
core.longpaths=true was nodig: zonder die instelling zijn lange Windows-paden
onleesbaar voor Git en verschijnen misleidende modified-meldingen. Geen SQL aangepast.
Fresh browser 323/323, migration list 29/29 en dry-run up-to-date.

Lokale PostgreSQL 18.6-build met --keep-temp: 22 migrations uitgevoerd tot
20260902045834, 15 verwachte object/RLS-asserties goed, zeven vanaf 6C expliciet
overgeslagen omdat pg_cron lokaal ontbreekt. Docker is niet beschikbaar.
**Een volledige 29-migration-replay en zero schema-diff met staging zijn niet bewezen.**
Daarvoor is een Supabase-compatibele lokale runtime met pg_cron nodig; daarna fresh reset
alleen lokaal, volledige replay en schema-only diff. Nooit remote reset of SQL-replay op staging.

Gecontroleerde paden, behouden en niet verwijderd:
- `C:\Users\Fitme\AppData\Local\Temp\fmz-local-rebuild-YsUaP4`: uitsluitend nieuw gegenereerde lokale rebuildcluster buiten OneDrive; PostgreSQL na test gestopt; --keep-temp.
- `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-tc26YR`: eerder auditpad, behouden.
- `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy\supabase\.temp\local-rebuild-YIC31o`: eerder auditpad, behouden.

Het volledige manifest van de 971 door OneDrive gemelde verwijderdoelen is niet
beschikbaar. Daardoor is niet bewezen dat elk doel een herbouwbaar tijdelijk PG-bestand
is. Geen van die items is alsnog verwijderd of vrijgegeven voor verwijdering.
Bij toekomstige cleanup is eerst het volledige OneDrive-doelmanifest met resolved
absolute paden en reparse-targets nodig; alleen aantoonbaar lokale herbouwbare clusters
mogen dan afzonderlijk beoordeeld worden. Tot die tijd blijft items behouden leidend.
Canonical migrations, bronnen, documentatie en Git zijn niet opgeschoond.
De databasecleanup hierboven betrof alleen de nieuw gemaakte synthetische fixture,
niet PostgreSQL-bestanden of bestaande staging-memberdata.

## 9. Commits En Deployment

Runtime/testcommit: `2e1fd983385ad360632667c954d7f63725555b3c`
(`feat: automate mock analysis delivery and refresh owner UX`), gepusht naar staging main.
43 bestanden; cache `20260906-owner-hotfix2`. Live assets SHA-256/commit-identiek.
Dit rapport en de status/evidencebestanden worden afzonderlijk logisch gecommit;
de exacte finale documentcommit staat in de eindoplevering en Git-log.

Migration 20260906092905 is via CLI op uitsluitend mokxyyullfhkfalopbzd toegepast na
review/rollbacktests/dry-run; niet achteraf gewijzigd. Workeractivatie is een begrensde
runtimeconfigwrite, geen history-repair. Frontend is via staging main gepubliceerd.
Edge broncode veranderde niet: v43 behouden en geverifieerd, geen onnodige redeploy.
Lokale read-only preview: http://127.0.0.1:8792/ (alleen app/assets, geen .git/.env/docs).
Geen productie-, SMTP-, betaling- of echte providerdeployment.

## 10. Exacte Owner-Retest

Open de staging-URL opnieuw op de telefoon en ververs. Gebruik het bestaande account;
verstuur geen nieuwe mail en voeg geen trainerrol toe. Test automatische analyses alleen
met een reeds toegestane AI-entitlement en expliciet zelf gekozen analyseconsent.
Geen entitlement/consent/ownerdata is hiervoor door deze hotfix opgewaardeerd.

1. Open/sluit/sleep de avatar op Vandaag en Training. Open een bestaande chat,
   lees terug, typ meerdere regels met toetsenbord open, stuur een bericht en wissel
   geschiedenis/nieuw gesprek. Controleer de oorspronkelijke pagina na sluiten.
2. Open tandwiel en alle verticale onderdelen. Verander taal via vlag en via Taal,
   ververs/log opnieuw in. Controleer aparte AI-toestemmingen en Analyseplanning.
3. Rond een eigen testtraining normaal af met opgeslagen sets; ga terug naar Vandaag.
   Wacht normaal maximaal circa twee minuten (minuutcron + zichtbare inboxrefresh).
   Kies Nu bekijken en controleer huidige/vorige training en het zichtbare mocklabel.
4. Stel dagelijkse klok en de huidige weekdag/klok enkele minuten vooruit in.
   Bestaande dag/weekresultaten mogen niet opnieuw ontstaan: dedupe is de bedoeling.
   Kies bij een nieuwe melding Later bekijken, ververs/log opnieuw in en open de kaart.
5. Open hetzelfde resultaat vanuit geschiedenis en eigen deep link; exporteer.
   Verwijder alleen een door de owner bewust gekozen testresultaat met bevestiging.
   Een gewijzigd/ander resultaat-ID moet veilig onbeschikbaar blijven.
6. Controleer Abonnement: alleen huidig serverplan/status, geen werkende betaal- of
   opzegknop. Controleer recovery alleen via de bestaande expliciete bevestigingen.
   Bevestig daarna per bevinding wat op de echte telefoon werkt; dit is nog geen freeze.

De volgende mapping dekt alle 47 verplichte ownercases. SQL/browser/cron PASS betekent
technisch getest; de fysieke owner-retest is nog niet uitgevoerd.

| Nr | Vereiste ownercase | Technisch bewijs / retest |
| --- | --- | --- |
| 1 | Rustige mobiele chat | Ownerbrowser vier maten + screenshot; telefoon stap 1 |
| 2 | Composer boven toetsenbord | visualViewport-simulatie; echte OS-keyboard stap 1 |
| 3 | Historie en nieuw gesprek | Ownerbrowser, paging/drafts/sequence; stap 1 |
| 4 | Avatar versleepbaar | Mouse/touch/keyboard browser; stap 1 |
| 5 | Chatbadge zichtbaar | Asset/DOM/screenshot; stap 1 |
| 6 | Tik opent, sleep niet | Touch/click browser; stap 1 |
| 7 | Sluiten naar vorig scherm | Exact-view/focus browser; stap 1 |
| 8 | Positie na refresh | Own-user persistence browser; stap 1 |
| 9 | Een job na completion | SQL 59 + echte cron + flush-order 6 |
| 10 | Geen retryduplicaat | SQL + tweede echte crontick |
| 11 | Juiste vorige training | SQL identity/metrics + echte 600/700-proef |
| 12 | Eerste training eerlijk | SQL + eerste cronworkout zonder predecessor |
| 13 | Max eenmaal per lokale dag | SQL eventidentity + cronherhaling |
| 14 | Max eenmaal per lokale week | SQL ISO-week + cronherhaling |
| 15 | Gewijzigde weekdag/klok | SQL recheck queued job + browser persistence |
| 16 | Onvoldoende data eerlijk | SQL en echte Terra-insufficient zonder observaties |
| 17 | Geen normale startknop nodig | Ownerbrowser + unattended cron; stap 3/4 |
| 18 | Direct detail na afronden | Exact-ID read RPC/browser; stap 3 |
| 19 | Nu opent exact resultaat | Browser Now + SQL result ownership |
| 20 | Later bewaart dashboardkaart | SQL later + browser |
| 21 | Kaart na refresh/login | Persistente SQL staat + browser lifecycle |
| 22 | Dashboard/geschiedenis openen | Exact-ID browserroutes; stap 5 |
| 23 | Export | Own-user SQL + single-result JSON browser |
| 24 | Delete uitsluitend eigen resultaat | SQL isolation/revision + browser confirmation |
| 25 | Read/unread consistent | SQL monotonic opened + browserbadge |
| 26 | Verticale instellingen | Acht rijen, alle vier browsermaten |
| 27 | Afzonderlijk vervolgscherm | Alle acht routes/back in browser |
| 28 | Geen Settings-bottomtab | Assembled browser |
| 29 | Tandwiel ingelogde schermen | Navigation/critical-surface browser |
| 30 | AI-instellingen centraal | Geen formulieren onder chat; browser |
| 31 | Planning persistent | SQL source + browser refresh |
| 32 | Safety-recovery behouden | Oude 50 SQL + nieuwe safetycases + handler/browser |
| 33 | Device datum/tijd/zone | Intl + lifecycle/sync RPC/browser |
| 34 | Geen handmatige systeemvelden | Browser absence checks |
| 35 | Reizen zonder duplicaat | SQL tijdzone/tombstone + gesimuleerde CDP-travel |
| 36 | Vlag actuele taal | NL/GB/DE browser |
| 37 | NL/EN/DE direct | Quick en centrale taalbron browser |
| 38 | Taal na refresh/login | Eigen serverbron + browser |
| 39 | Cross-member isolation | SQL auth.uid/RLS/ACL, trainer/anon denial |
| 40 | Auth/registratie | Auth 88/26, live public vier maten, geen mail |
| 41 | Frozen Phase 1-6 | Finale regressierunner alle suites exit 0 |
| 42 | Geen consolefouten | Assembled en live public browser |
| 43 | Geen overflow | 320x700, 390x844, 820x1180, 1440x900 |
| 44 | Fixtures opgeruimd | Rollbacks + exacte committed-croncleanup nul |
| 45 | Externe AI-calls nul | Mock-only worker/config/runadapter + handler tests |
| 46 | Externe AI-kosten EUR 0,00 | Run cost_micros=0; geen provider/billingactie |
| 47 | Productie onaangeraakt | Exacte stagingrefs/remote/command scope |

## 11. Resterende Gates En Volgende Stap

Geen nieuwe ownerbeslissing is nodig om deze mock-only staginghotfix te gebruiken.
Wel blijft owneracceptatie/een eventuele freeze uitsluitend aan de owner.
Voer nu de telefoonretest hierboven uit. Echte keyboard-/OS-interactie is niet door
browseremulatie bewezen. Full local replay/schema-diff vereist eerst pg_cron/Docker;
deze beperking wordt niet verborgen als een groene full-build.
Billing blijft Phase 7, echte push Phase 8/12, accountdeletion een apart privacy/security-
contract, en echte member-provideractivatie een apart juridisch/privacy/provider-GO.
Productie blijft volledig verboden.
