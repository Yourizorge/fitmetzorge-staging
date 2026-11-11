# 6E-11 gezamenlijke toelatingsvoorbereiding - 2026-11-02

Status: NO-GO voor hosted uitvoering. Geen owneracceptatie of freeze.

## Scope en uitvoering

Uitsluitend Yourizorge/fitmetzorge-staging/main. Deze opdracht voerde geen
Supabase-hosted verzoek, JIT, migrationtoepassing, fixturecleanup of ownervenster
uit. Hosted migrationstand is laatst bewezen 44, niet opnieuw gemeten. De
canonical kandidaat 45 en private appmigrations 46/47 zijn uitsluitend lokaal/CI.
Package 21 blijft uitgeschakeld. De oude oktoberbinding is niet gebruikt of gewijzigd.

Zes gespecialiseerde agents werkten onder een coordinator aan CLI/protocol,
Auth-foutpaden, fixturecleanup, foutmatrix, budgetcompiler en onafhankelijke review.
Alleen de coordinator committeert, pusht en start disposable CI.

## Gebouwde onderdelen

| Onderdeel | Nieuw resultaat | Niet geclaimd |
| --- | --- | --- |
| CLI | Gepinde 2.117.0-bron, fsync-ledger voor dispatch, protocolframes apart, geen refund bij onzekerheid; instrumentatie voor app46/47 en lege dry-run | Niet gelijkgesteld aan de ongewijzigde releasebinary; werkelijk PG-bewijs vereist |
| Auth | Elf echte lokale GoTrue-foutgevallen voorbereid, begrensde HTTP-framing, eigendomscontrole, terminalbarriers en afzonderlijke veiligheidsreconciliatie | Geen globale Auth-zero of claimvrijgave zonder bewijs |
| Fixtures | Dertien-tabelleninventaris, gedeeltelijke objecten, exacte eigendom, insert/update/delete en commit-/afwezigheidsbewijs; verliesloze journals | Nul gevonden rijen is geen bewezen delete; onbekende commit blijft NO-GO |
| Foutmatrix | Twee read-only migrationgrenshooks en twaalf native/Auth-componentpaden | Geen volledige duurzame 14-fasen-endchain op basis van rollbackcomponenten |
| Budget | Uitvoerbaar register met 1717 referentierijen, 11.724 stop-prefixmodeluitkomsten na de prechargecorrectie, concrete open kosten en verliesloze export | Modelgevallen zijn geen uitgevoerde tests; geen verzonnen nieuwe bovengrens |
| Runbinding | Nieuwe voorbereidings-ID 11a909f4-7113-424a-aa4b-ce9964720a3e, bronregisters en vervalvalidatie | Geen DB-quota of hosted bevoegdheid |
| CI | Een same-source disposable PG17/Auth/app12-20-kandidaat, harde stop op onbevestigde componentcleanup en afzonderlijke artifactverificatie | Component-PASS is geen totale toelating |

## Eerste brongebonden poging

Commit `373fce1e029adece158e5da8b4ca97c75da87412`, CI
[41507466863](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41507466863).
Candidate SHA-256 `6bbd6e8e407191f11e9f9993df9f5bca7c030e861728d2e83670363c4d456b96`.
ZIP SHA-256 `5e92d6c4e25fa4fa4cff78e452a9c355c9db3e8ca69ca90450ce32485138237b`.
528 bronnen; 93 bewijsbestanden plus manifest onafhankelijk gecontroleerd.

CLI-build, 29 Node-tests, 42 Python-tests en help-smoke slaagden; de help-smoke
is uitdrukkelijk geen databaseproef. Schone opbouw bereikte migration 44 op
PostgreSQL 17.6 (170006). De nieuwe migrationgrenscontrole stopte voor 45 met
`migration_boundary_dispatcher_source`. Dit is geen 47/47-PASS en geen fout
in hosted Supabase. De dispatcher stond in de vertrouwde checkout, terwijl
de helper vanuit de gereconstrueerde kandidaat werd geladen. Beide wortels
moeten exact gebonden blijven; het verwijderen van broncontrole is geen oplossing.

De oorspronkelijke run en bestanden blijven ongewijzigd. Latere correcties
zijn afzonderlijke bronversies en promoveren deze mislukte poging niet naar PASS.

## Tweede brongebonden poging

Commit `9580e5e207328dda8a180ae36d09409d44605156`, CI
[41510381749](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41510381749).
Candidate SHA-256 `846b4f8df3d3ce7df610ae2c7e7bc563f2b69b4ba3c7da95751fe4c9b44d2ec1`.
ZIP SHA-256 `908d332509c327e05b3a12fe50c9e7a7d7e6bdee92d8a5c41080c11826b6cb5f`.
530 bronnen; 117 bewijsbestanden plus manifest geverifieerd.

Schone canonical opbouw 45/45, pre-/post-migrationgrenscontrole en module-origin
binding zijn uitgevoerd. Voor private appmigration 46 stopte de instrumentatie:
CLI-exitcode 1, geen dispatchledger, `FileNotFoundError` bij het uitlezen daarvan.
Geen migration46-PASS, geen 47/47-PASS, geen nul-dispatchclaim. De volledige
64-eenhedenreservering blijft verbruikt; de acht disposable-isolatiecommando's
en bevestigde restauratie staan apart geregistreerd. De concrete CLI-startfout
is lokaal gereproduceerd: de nieuwe hook accepteerde uitsluitend 14-cijferige
historyversies en verwierp de bestaande `20260813` en `20260818` voordat de
ledger werd geopend. Alleen deze twee exacte legacy-identiteiten zijn toegevoegd
aan beide historycontroles; nieuwe migrationtargets blijven 14-cijferig en de
volledige history moet exact overeenkomen met de geregistreerde bronlijst.
Deze run wordt niet heropend.

Dezelfde gepinde CLI-entry met de exacte CI2-policy (45 historyversies en 42
ASTs) faalde voor de correctie en gaf daarna exit0 bij een help-only start,
zonder verbinding of SQL. Dit is geen database-applybewijs.
Before-receipt SHA-256 `ab4eb2e2a8c8dfc9e34d53cbe0f800d73ac3afcfe498f2886b23542e0bced41a`;
after-receipt SHA-256 `1eb8192525b0849afd9d2baa084a046207a9f8348016978dc6cbf833317e8efa`.
De geintegreerde CLI-correctie: 47 Python- en 33 Node-tests PASS; dit zijn
afzonderlijke suites, geen nieuwe volledige-keten-PASS. Een vaste gesanitiseerde
foutclassificatie bewaart nu de CLI-exitcode voordat de ledger wordt uitgelezen.

Lokale samengevoegde regressie op deze bron: 348 tests, 346 geslaagd en twee
echte symlinktests overgeslagen vanwege Windows-privilege. Hun Linux-CI-uitvoering
is op deze run nog niet bereikt. De eerdere kleinere rondes worden niet bij
dit totaal opgeteld.

Het complete offline register is in negen verliesloze bestanden gegenereerd,
met bronhashes gelijk aan deze kandidaat. Register-SHA-256:
`95508987f0aa62606b842a72c5841683a6c23b5f3f88d8e1961d1d89e0cfc0d3`.
Locatie onder `supabase/.temp/phase6e-server-ci-fec8549bf78c48aba62800df478d3f90/`
is `offline-budget-73c352cddf7e40cd81f3faea9b344bdd/`.
Dit is een lokale generatie, niet uitgevoerd CI-bewijs; status
`NO_GO_INCOMPLETE_BOUND` en `minimal_cap=None` blijven behouden.

## Derde brongebonden CI en gerichte meetcorrectie

CI [41513763310](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41513763310)
op `32cbb1518a46bd65511187ae99b53d68c3446448` blijft NO_GO.
Candidate SHA-256 `df74adf2a99707daa3058ebc5157394be2cf0c3b85dd27d92cbf8cf9e01ffeda`;
ZIP SHA-256 `6d5c7833857e5c549b8cb99a58380937c672e232ded4bf3eea05b9d3dd6e0681`.
117 bewijsbestanden plus manifest zijn behouden. De instrumentatie voerde de
private appmigration daadwerkelijk uit: exit0, 47 bevestigde SQL-dispatches,
47 numeriek waargenomen top-level opdrachten, nul eigen tijdelijke writes.
De keten stopte daarna op `cli_predispatch_pending_numeric`: de toelatingscode
vereiste uitsluitend track=all terwijl de reader expliciet alleen toplevel
selecteert. De feitelijke trackingmodes werden in deze receipt niet opgeslagen;
deze run wordt daarom niet achteraf als PASS verklaard, ook niet als 47/47.

De correctie accepteert uitsluitend een onveranderde top/top of all/all met
utility on/on en registreert die instellingen expliciet. Onbekende, uitgeschakelde
of veranderde instellingen blijven geblokkeerd. Dit bewijst geen nested workload.
Onafhankelijke bronreview: geen P1/P2-blokker voor een nieuwe disposable CI.
WAL-, IO-, tijd-, Auth- en hosted grenzen zijn niet gewijzigd.

## Vierde disposable CI: 47/47 en appcomponent, nog geen eindtoelating

CI [41619169140](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41619169140)
op `82b51fe167ad74545eb835af3d56268f154ae4e9`, 3 november 2026.
Candidate SHA-256 `80a564afadb3114b061bd5b36c0fd5e2ae9d696885417c8e713540236f5be425`;
ZIP SHA-256 `6e2c66fa349e775dc104d8a2ba193ad235dc8f8425bef96f7c7c530ae7d00685`.
570 bewijsbestanden plus manifest zijn geverifieerd en behouden.

Schone 47/47-opbouw op PG17.6 is PASS. De twee geinstrumenteerde private
appmigrationstappen hebben respectievelijk 47 en 22 bevestigde dispatches,
exact gelijke numerieke waarneming en nul eigen tijdelijke writes. Beide
bewaren top/top, utility on/on en acht afzonderlijke observercommando's.
De semantiek volgt de [PG17-documentatie](https://www.postgresql.org/docs/17/pgstatstatements.html):
`toplevel` begrenst deze vergelijking tot rechtstreeks uitgevoerde opdrachten.
Dit is geen bewijs voor alle geneste serveractiviteiten of fysieke WAL0.

De bestaande appcomponent is op dezelfde kandidaat opnieuw uitgevoerd:
12/12 SQL-regressies, 74 database- en 46 domeintests, vier echte lokale
Auth-controles en 209 integratiebrowserchecks. De afzonderlijke browser- en
release-deelsuites staan in result.json; zij worden niet tot een kunstmatig
groter totaal opgeteld. Controller- en request-security zijn PASS. Package21
blijft uit. Dit is uitsluitend disposable CI, niet hosted staging.

Stop: `admission-test_migration_failure_boundaries_exit_1`, vijf fouten in
26 tests. Deze tests laadden de checkout-harness vanuit de kandidaatwortel;
checkout-only `controller_v1/ci.py` en de gepinde runner ontbreken daar bewust.
De daadwerkelijk eerder uitgevoerde migrationgrenshooks waren geslaagd.
De nieuwe elf Auth-foutgevallen, volledige componentmatrix, fixturecleanup
en afsluitende instrumented dry-run zijn niet bereikt. NO_GO blijft staan.
Dit was geen vierde WAL-diagnose en geen hosted poging.

De vijf testfouten zijn gericht hersteld: de testharness komt uit de expliciete
checkout, de helper uit de kandidaat. 28 tests PASS, inclusief twee regressies
voor die echte mapopbouw. Geen ontbrekende checkoutcode aan de kandidaat
toegevoegd en geen bronpin versoepeld.

Aanvullende lokale correcties: Auth-vrijgave volgt pas na duurzame receipts en
volledige acht-tellernulcontrole (42 tests PASS). De budgetcompiler onderscheidt
voorafgaande afschrijving, verzending en validatie, behoudt onzekere capaciteit
en herhaalt een begonnen verwijdergroep niet (92 tests PASS). De huidige grafiek
bevat 11.724 prefixuitkomsten; die zijn modellen, geen werkelijk uitgevoerde
foutproeven. Oudere exports blijven onveranderd. De aparte parent-fixturehelper
is voorbereid en unit-getest, maar wordt zonder bewezen producer-/mintbarriere
niet aangeroepen. Dit is geen globale cleanup-PASS.

## Vijfde kandidaat en aanvullende lokale aansluiting

Commit `b00a2a5f59b116023d28716eb1bb80c19756653d` bindt de canonical
M45-uitvoering aan dezelfde pre-dispatchmeter. De parent voert precies eenmaal
`before -> run_canonical -> after` uit. De oorspronkelijke ledger en policy
blijven als begrensde, exclusief geschreven en gehashte bytebestanden bewaard;
ook een gedeeltelijke ledger wordt niet gereconstrueerd. Onzekere uitvoering
blijft 64 gereserveerde eenheden verbruiken. Observer- en isolatiecommando's
blijven afzonderlijk zichtbaar. Dit is geen verhoging van hosted capaciteit.

Lokale verificatie: 78 CLI/protocoltests PASS en 171 gerichte
admission-/fixture-/migrationgrenscontroles PASS. Deze suites en eerdere
deelcontroles worden niet als een nieuw totaal opgeteld. De onafhankelijke
review gaf source-only akkoord voor disposable CI, niet voor hosted uitvoering.

De negatieve fixturecontrole heeft nu een afzonderlijk, vooraf opgeslagen
parent-eigendomsbewijs. Exacte rowversions moeten na de negatieve test gelijk
zijn; gewijzigde, extra of ontbrekende rijen blokkeren de latere cleanup.
Het negatieve testresultaat zelf blijft NO_GO. De witness heeft maximaal vijf
vooraf getelde commando's, inclusief de gereserveerde rollback. Dit is nog geen
bewijs dat alle parent-fixtures en Auth-objecten daadwerkelijk zijn verwijderd.

CI [41628119054](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41628119054)
is eenmaal gestart op deze bron, met 535 bronbestanden en candidate SHA-256
`4f6b22aff6b07fde31f4ba76aaac707745be0132a1dff6e7310f01db89fc0834`.
De artifact-ZIP is geverifieerd: SHA-256
`d0a41f81b1fe6d49af7ae6dc3205b434beac50aca5dca0da080395805867bcb1`,
109 bewijsbestanden plus manifest. De canonical CLI voerde 14 bevestigde
protocolcommando's uit, met 14 overeenkomende numerieke waarnemingen, nul eigen
temp writes, acht observercommando's en acht isolatiecommando's. Cron is aantoonbaar
hersteld. Ledger-SHA-256
`9d4b18d7a2ff12bf2bc80f6bbf1700e72ec787f07fd803b9ab6aa670c7404494`;
oorspronkelijke policy-SHA-256
`fee70f3d1a1af4ecc3aaed7013022c0c002d84ef6e3a0675e0795c3bbaeaa96f`.

De onafhankelijke nameting werd geblokkeerd door
`migration_boundary_instrumented_m45_ast`; de run blijft NO_GO. Migration45 is
door de CLI uitgevoerd, maar de parent heeft de stap niet als bevestigd opgenomen:
`migrations_applied=44`. Geen clean45/47- of Auth-/fixture-PASS op deze run.

De oorzaak is offline gereproduceerd met de exacte migrationbytes. De gepinde
Node-parser `@libpg-query/parser@17.6.10` rapporteert PG170004; de onafhankelijke
Python-parser pglast v7.20 rapporteert PG170007. Alleen bij de functiedefinitie
voegt Python `DefElem.arg_location` toe: een bronpositie, geen SQL-inhoud. De
gerichte normalisatie verwijdert uitsluitend dit integerpositieveld binnen
DefElem. Daarna komen alle negen AST-hashes overeen met de oorspronkelijke
Node-policy. Andere velden en de volledige migration-SHA blijven verplicht.
44 boundarytests PASS, inclusief een regressie tegen de echte gepinde migration
en tests dat inhoudswijzigingen of ongeldige positievelden worden geweigerd.
Dit lokale herstel promoveert CI5 niet naar PASS.

## CI6: onafhankelijke migrationcontrole hersteld

CI [41630541810](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/41630541810)
op commit `5bdcdfd451c768d5c61d1a5b31b73111a543bc92` heeft een schone
47/47-opbouw bewezen. Candidate SHA-256:
`d921593e766deab6708d6b063a018447fce3ec9e224737b0a8ce64b165f335a8`.
De geverifieerde ZIP bevat 565 bewijsbestanden; SHA-256:
`d8896fc3aa77377a2ac942845e0eab585ab8372073f4756e0130957fef6dc48d`.

De echte canonical CLI-dispatch en onafhankelijke migration-nameting sluiten nu
aan: 14 bevestigde protocolcommando's, 14 numerieke waarnemingen, nul onbekende
dispatches en nul eigen temp writes. Acht observer- en acht lokale
isolatiecommando's zijn afzonderlijk verantwoord. Dit is disposable CI-bewijs,
geen hosted uitvoering of bewijs van volledige fysieke WAL0.
De post-migrationreceipt bewijst `component_verified=true`, maar behoudt
`terminal_complete=false`: geen volledige eindketenafsluiting.
Oorspronkelijke ledger-SHA-256:
`422017bf1dcfc5769f664f85b36fc79f60c03ba51f208131cba05ed4ed34c0cb`;
policy-SHA-256:
`3167bcad54ee465d44bfbd5646582d8500d2a70571b546428e067bbc8a2bd8f0`.

De app-integratie bereikte opnieuw 209 browsercontroles, 46 domeintests en
12/12 SQL-regressies. Deze overlappende resultaten worden niet bij eerdere
CI-totalen opgeteld. De run stopte daarna op `offline_shell_browser`.
De nieuwe Auth-, integrale foutpad- en fixturecomponenten zijn op deze bron dus
nog niet uitgevoerd. Status blijft NO_GO; geen automatische herhaling en geen
hosted toegang. Check 66 lokaliseert de browserfout bij de tweede B-login na
offline herladen. De oorspronkelijke oorzaak blijft UNKNOWN: de bewaarde
metadata bevat geen HTTP-status of responsevolgorde van die login.

Afzonderlijk is een race gereproduceerd waarbij de nog lopende anonieme
bootstrap een reeds ingevuld testformulier wist. De test wacht nu op de
bestaande GET/403 en verwerkte sessiestatus voordat velden worden ingevuld.
Geen runtimewijziging, extra request, retry of verhoogde timeout. De test
bewaart uitsluitend begrensde fase-/methode-/statuscategorieen, zonder headers,
body, URL-query, credentials of foutinhoud. 88 gerichte Node-tests PASS;
Chromium/GoTrue-verificatie van deze correctie blijft apart vereist.
Een aanvullende onafhankelijke review wees op vrije Playwright-fouttekst in
de buitenste NO_GO-envelope. Die is vervangen door vaste foutcategorieen.
Drie extra sentineltests bewijzen dat foutnaam, message, stack en cause niet
worden gepubliceerd. De gerichte browser-testsuite omvat nu 15 tests PASS;
dit is geen nieuwe fysieke telefoontest.

## Checkpoint: geregistreerde producers

Commit `3969f0bd15bef864c665ef55da0fc25d300a2665` voegt uitsluitend opt-in
disposable CI-instrumentatie toe. Auth-aanvragen krijgen vooraf een duurzame
registratie en reserveringsreferentie. Onzekere verzending wordt niet
terugbetaald. De journal controleert volledige writes, fsync/readback en de
oorspronkelijke hashes van alle records voor afsluiting, bewijsgebruik en export.
De onafhankelijke review vond en liet twee opslagfouten herstellen voordat
deze bron werd opgenomen. Default app/Auth-gedrag blijft ongewijzigd.

De fixturefactory registreert werkelijke backendidentiteit voor de eerste
fixturequery. Bootstrap en fixturetests delen deze factory. Afsluiting wordt
gevolgd door een afzonderlijke serverwaarneming van geregistreerde backends.
Dit bewijst niet automatisch afwezigheid van andere producers of volledige
Auth-cleanup; die aansluitingen blijven afzonderlijke vereisten.

Lokale verificatie: 122 Auth-/wiringtests, 105 fixturetests en 16 gerichte
orchestratie-/bootstraptests PASS. Deze overlappende suites worden niet
opgeteld. Daadwerkelijke GoTrue/PG17-uitvoering van deze nieuwe opt-in
samenstelling is nog niet bewezen. De hoofdstatus blijft NO_GO.

Een afzonderlijke parent-Auth-finalizer is voorbereid voor exact de drie
oorspronkelijk geregistreerde fictieve accounts. Zij vereist de gehashte,
verzegelde C-closurereceipt voordat een obserververbinding of delete is
toegestaan. De review vond en sloot een ontbrekende hashvereiste. 27 tests
PASS met echte localhost-HTTP en gemockte SQL/C-bewijzen. De reservering is
402 lokale diagnostische eenheden (18 observers plus drie maal 128 voor
delete); dit is geen waargenomen hosted bovengrens en geen toevoeging aan
de toegestane 2349. Werkelijke gezamenlijke afsluiting blijft te bewijzen.

## Budget en harde grenzen

### Nieuwe lokale opruimkoppeling, nog geen PG/Auth-PASS

De nieuwe opt-in samenstelling houdt een metadatawaarneming, een fysieke
schrijfuitsluiting en de Auth-afsluiting apart. De scopelezer controleert de
dertien tabellen, versiegebonden functies/triggers, foreign keys, effectieve
rechten en gesloten RPC-grenzen. Een lege activitylijst is geen globale
writerbarrier. De registry-suffix houdt locks over de scopecontrole, actuele
afwezigheidscontrole en exacte registry-deletes; een tweede verbinding bewijst
daarna afwezigheid. Verloren historische COMMIT-antwoorden blijven NO_GO.

De admin-obserververbinding wordt tijdens de scopewaarneming daadwerkelijk
gesloten; een ExitStack bezit ook de opnieuw geopende verbinding. Dezelfde
protocolledger blijft in gebruik. De Auth-finalizer mag pas volgen op de
verzegelde fysieke-closurereceipt met exacte bron- en actorbinding.

154 gerichte lokale fixture/journal/orchestratieregressies PASS; daarna 21
gerichte orchestratiecontroles PASS na hergebruik van de bestaande strikte
receiptlezer. Deze suites overlappen en worden niet opgeteld. Het zijn deels
gemockte tests, geen nieuwe echte PG17-/GoTrue-cleanupclaim. De werkelijke
gezamenlijke uitvoering en het volledige foutpadregister blijven vereist.

De nieuwe PhysicalCProof-consumer en compositie hebben aanvullend 52 tests
PASS (43 Auth-finalizer en negen compositiecontroles; 94,308 seconden).
Onafhankelijke source-review: geen blokkerende P1/P2 in C, Main-wiring of
PhysicalCProof. Deze review is geen werkelijke PG/GoTrue-uitvoering.

Actuele documentatiecontrole: de Supabase-changelog noemt een aanstaande
uitfasering van oude HTTP TLS1.2-ciphers op 10 november 2026 en een tzdata-fix
voor drie tijdzones. Dit is geen reden om de gepinde disposable stack of
stagingconfiguratie stilzwijgend te veranderen. De officiële Auth-documentatie
behoudt de koppeling van session_id aan auth.sessions; rijverwijdering wordt
niet als onmiddellijke intrekking van iedere stateless JWT voorgesteld.
Bronnen: [changelog](https://supabase.com/changelog),
[Auth-sessies](https://supabase.com/docs/guides/auth/sessions),
[PG17-locks](https://www.postgresql.org/docs/17/explicit-locking.html).

De veertien matrixfasen zijn niet als veertien volledige keten-PASS-resultaten
geregistreerd. De uitvoerbare componentgrenzen zijn:

| Fase | Component | Open volledige-keteneis |
| --- | --- | --- |
| pre-migration | Read-only clean44 en stop voor dispatcher | Volledige afgebroken runprefix |
| post-migration | Een echte M45-bootstrap en object/historycontrole | Migration-failureclosure |
| mid-Auth | GoTrue-login met verloren antwoord | Geregistreerde endchain-Auth |
| controller | Controller/NativeStore en action_started | Duurzame request-/meetparen |
| Route A | Native api_call/source_append | HTTP/JWT/meetpaarketen |
| Route B | Frozen berekening en internal_b | HTTP/JWT/meetpaarketen |
| restore | Werkelijke actieprefix en restore | Duurzame closure in plaats van rollbackisolatie |
| lost reply | Verloren GoTrue-createantwoord | Verloren workflow-commitantwoord |
| duplicate | Native replaycontrole | Duplicaat via geregistreerd transport |
| timeout | PG-cancel 57014 binnen bestaande limiet | Worker-/endchain-timeout |
| partial cleanup | Scoped delete gevolgd door fout | Gecommitteerde gedeeltelijke cleanup |
| cleanup failure | FK-fout 23503, oorspronkelijke fout behouden | Volledige cleanup-suffix onder endchainmeter |
| final check failure | Onafhankelijke afwezigheidsmeting en fout | Globale FINAL_PRE/POST-inventaris |
| closure failure | NativeStore-close en fout | Duurzame closure en claimvrijgave |

Deze tabel beschrijft de implementatie, niet een geslaagde nieuwe uitvoering.
Ontbrekende of onvolledige componentreceipts blokkeren de volgende fixturemutatie.

Zie [volledig budgetoverzicht](PHASE6E11_ADMISSION_BUDGET_STATUS_20261102.md).
De behouden referentie is 2338; maximum 2349; cleanup/final/closure 731 zit
binnen 2338. De 11 resterende eenheden bewijzen niet dat de nieuwe samenstelling
past. `minimal_cap=None`: volledige executor-, managed-Auth-, CLI-fout- en
recoverykosten zijn nog niet allemaal bewezen. Geen willekeurige verhoging.

Het nieuwe offline planmodel houdt historische SQL apart van dertig actuele
bronafleidingen (verplaatsingen en gewijzigde afsluitqueries). Het reserveert
ook het eerder ontbrekende conditionele rollback_setup-commando. De kosten
van de nieuwe C/B-diagnostiek zijn afzonderlijk uitgewerkt over 286
parametercombinaties en 66 fysieke suffixvormen. Dit is geen bewijs dat die
diagnostiek binnen het hosted maximum valt en geen gefabriceerde volledige
dispatch-DAG. De drie budgettestsuites: 137 PASS, 46,537 seconden. Een werkelijke
zelfde-bron executortrace en alle integrale foutprefixen blijven vereist.

Zie [WAL-beoordeling](PHASE6E11_ADMISSION_WAL_ASSESSMENT_20261102.md).
De drie historische pogingen en incomplete intervallen blijven behouden.
Geen vierde WAL-diagnose. Logisch objectbehoud bewijst niet dezelfde fysieke
WAL0-eis. Die norm is niet versoepeld en blijft een zelfstandige harde blokkade.

## Behoud en publicatie

De bestaande werkboomwijzigingen zijn behouden en niet bulk-gecommit.
Behoudcontrole: 1376 bestanden, 1372 byte-identiek en vier eerder toegestane
wijzigingen apart verantwoord; nul nieuwe onverwachte afwijkingen.
M45 SHA-256: `64498fa910966497e92705dcf66b76f40c40f01c006aed98c191ce109dd88635`.
Historische autorisatie SHA-256:
`ad79d3c4c0dd79879567cee7c20999ba7ae05e2205ddc3c89a6597767286ef7e`.

Pages op 373fce1: run 41507249344 geslaagd, 152 runtime-assets byte-identiek,
private roots ontbreken in het deployartifact en zeven private HTTP-probes 404.
Dit bewijst publicatiebehoud, geen hosted databasebehoud.

Checkpoint 3969f0b: Pages-run 41633708684 geslaagd; artifact 13228952662,
SHA-256 `678ef03475ccbf4fc21171dbe2d593c1c981786199d42421622dcfe7ecc4a534`.
Alle 152 runtime-assets byte-identiek, private roots afwezig, zeven private
HTTP-probes 404. De eerste controle vond nog geen geslaagde publicatie van de
nieuwe commit en gaf daarom geen PASS; de latere controle is apart opgeslagen.

Checkpoint 263cc2b472f9e1d40a7fc926342c3b55a733b441: Pages-run 41636776559,
artifact 13230273606, SHA-256
`b8cb0b85d1104597c3d0a9dd33cb35fb263d06d95957d038781613d8b26c07d0`.
817 artifactentries, 152 ongewijzigde runtime-assets, private roots afwezig
en zeven private probes 404. Nul Supabase-calls tijdens deze controle.

## Grenzen voor de eigenaar

### Zevende brongebonden CI-controle

CI-run `41641017988` op commit
`3e64988aede9f56192da2a22e1b226fa6677b369` is NO-GO, niet opnieuw als PASS
geclassificeerd. Candidate SHA-256:
`a5cc54ff2463c59d479201038cd804d848a9f15c0f91a5e683b954f79ab9538a`.
Het gevalideerde ZIP-artifact heeft SHA-256
`f01bc37dd3318e8e2528f21fbabed3d2a8c8dc813a712abd548d764f094f5f68`
en 618 bestanden. De oorspronkelijke bewijsbestanden blijven ongewijzigd.

De schone 47/47-opbouw slaagt. Afzonderlijke appresultaten: 74 databasechecks,
46 domeintests, 4 Auth-tests, 209 browserchecks, 191 samengestelde browserchecks,
79 accountbrowserchecks en 73 offline-shellchecks. Dit zijn overlappende
suites; er wordt geen gecombineerd succesgetal van gemaakt. De browserstop
uit CI6 treedt in deze uitvoering niet op. Dat bewijst geen historische oorzaak.

De echte lokale Auth-foutcomponent geeft `LOCAL_AUTH_FAILURE_COMPONENT_PASS`.
De oude workflowcomponentmatrix bereikt vijf van twaalf geselecteerde
foutgrenzen. Zeven gevallen stoppen met `FileNotFoundError` voor de bedoelde
injectie; bij Route A volgt dit na het zestiende SQL-commando, tijdens de
voorbereiding van de scenarioacties. De afzonderlijke componentactors zijn
volgens hun eigen receipt verwijderd. Dit is geen globale Auth-cleanupclaim:
de parent-finalizer blokkeert omdat de fixturefase nog niet is begonnen.

De dependencybinding en een expliciet pre-fixture-afsluitpad worden gericht
hersteld. De vijftien afzonderlijke volledige-ketenproeven blijven nog
onbewezen. Er is geen hosted verbinding, fixturehandeling of WAL-herhaling
uitgevoerd en geen gebruikte poging opnieuw geopend.

De bronkoppelfout is offline gereproduceerd: `scenario` kon reeds uit de
checkoutcache zijn geladen, terwijl de bijbehorende niet-gecommitteerde
workflowbron alleen in de kandidaatbundel aanwezig was. De correctie compileert
de exacte kandidaatbytes in een eigen module, controleert beide bronhashes en
de capture-digest voor de eerste mutatie en wijzigt de globale modulecache niet.
Een nieuwe echte PG-uitvoering is nog nodig om het oorspronkelijke stoppunt
voorbij te bewijzen.

Nieuwe lokale regressieronde: 157 tests uitgevoerd, 156 PASS en een expliciete
Windows-symlink-SKIP. Deze ronde omvat de stackfinalisatie, hoofdaansluiting,
fixturebootstrap en workflowfoutpaden met lokale testdoubles; het is geen nieuwe
PG-/GoTrue-toelating. Een onbekend BEGIN-antwoord leidt nu ook bij de
fixturebootstrap tot een getelde veiligheidsrollback, zonder herhaling.

De afzonderlijke matrix-artifactcontrole heeft 23 tests PASS, onafhankelijk
herhaald. Drie reviewbevindingen zijn gesloten: exacte bronmapvergelijking tegen
de gehashte voorbereide bundel, uniek PostgreSQL-cluster-ID los van database-OID,
en gesanitiseerde foutuitvoer wanneer receiptopslag zelf faalt. Dit bewijst de
controlecode, niet de nog uit te voeren vijftien ketencases.

Pages-controle op `3e64988aede9f56192da2a22e1b226fa6677b369`: run
`41640749083`, artifact `13233191332`, SHA-256
`90160959d22ff1c7d1f4a1545d7a14656c0b94de0510c91f77ed15edac469240`.
Alle 152 runtime-assets ongewijzigd, 817 entries, private roots afwezig,
zeven gecontroleerde paden HTTP 404, nul Supabase-calls. De nieuwe lokale
behoudcontrole vindt opnieuw nul onverwachte afwijkingen in 1376 bestanden;
dezelfde vier eerdere toegestane verschillen blijven afzonderlijk benoemd.

Geen hosted poging vrijgeven op basis van losse componentresultaten.
Volledige same-source toelating, zelfstandig beoordeelde cleanup/prefixbudgetten
en de ongewijzigde WAL-voorwaarde moeten eerst slagen. Tot die tijd blijft de
voorbereidingsbinding niet-uitvoerbaar. Er wordt nu geen nieuwe hosted
toestemming gevraagd en geen ownervenster geopend.

### Offline vervolg: pre-fixture Auth-afsluiting

De onafhankelijke review reproduceerde dat het ontbreken van een fixture-runtime
op zichzelf geen bewijs is dat Auth-deletes geen onverwachte trigger- of
cascadegevolgen hebben. Het nieuwe afsluitpad hergebruikt daarom de bestaande
producer-scopevalidator: tien vooraf getelde read-only protocolcommando's,
inclusief rollback, met twaalf duurzame intent-/charge-/resultaatrecords.
Een eerdere mislukte scopepoging wordt niet herhaald en staat geen deletes toe.
De actuele bronbinding, catalogusuitkomst en oorspronkelijke recordhashes worden
opnieuw gecontroleerd voordat de bestaande Auth-delete-engine wordt toegelaten.

Dit afzonderlijke lokale diagnostische pad reserveert 412 eenheden: tien voor
de cataloguscontrole en 402 voor de bestaande observer/delete-engine. Dit is
geen verhoging of bewijs van voldoende ruimte binnen het globale maximum 2349.
De oorspronkelijke fout, onzekere uitkomst en claims blijven NO-GO; succesvolle
gerichte cleanup maakt de oorspronkelijke proef niet alsnog geslaagd.
Agent B rapporteert 122/122 lokale tests; de onafhankelijke C-review 18/18.
De hoofdworker herhaalde de 122 tests: PASS in 334,301 seconden.
Deze aantallen overlappen en gebruiken SQL-testdoubles. Echte PG-/GoTrue-
verificatie van dit nieuwe samengestelde afsluitpad blijft afzonderlijk vereist.

De matrixcollector eist naast positieve artifactreceipts ook een daadwerkelijk
geslaagde GitHub-run. Een opgeslagen PASS gevolgd door een fout bij duurzame
opslag kan daardoor geen positieve eindtoelating opleveren. De gerichte suite
heeft 25 PASS, onafhankelijk herhaald; dit is geen uitgevoerde foutpadmatrix.

Checkpoint `0bdf53a967ac1e56e1ef2b5f5e00b85d4de078fa`: Pages-run
`41646273660`, artifact `13234044527`, SHA-256
`5ffb3275445bf6548b4aaa9bb9330c6b6ae34e7210dc28caff6b5c98324cfccf`.
817 entries, 152 runtime-assets byte-identiek, private roots afwezig en zeven
private HTTP-paden 404. Dit is publicatiebewijs, geen hosted databasebewijs.

### PG17-cataloguscorrectie voor de volgende CI

De voorcontrole vond een bronfout voordat een nieuwe CI-run werd gestart:
`pg_type.typelem <> 0` betekent niet uitsluitend SQL-array. Ook scalar `name`
heeft een elementtype. De eerdere query zou daardoor `attach(regclass,name,name)`
verkeerd vergelijken als twee `char[]`-argumenten en de bootstrap blokkeren.
De query gebruikt nu de wederkerige relatie `element.typarray = type.oid`,
zowel voor elementkeuze als voor het arraykenmerk. De echte geparste SQL-
expressies zijn getest met de PG17-cataloguswaarden voor `name` en `name[]`;
de in-memory expressietest is uitdrukkelijk geen echte PostgreSQL-uitvoering.
24/24 tests PASS, apart herhaald door hoofdworker en onafhankelijke reviewer.
De vooraf voorbereide bundel `e61a8334ee27aa3280504e0c24312f9903c160d94b776a711c8abd165a1d0c89`
blijft ongewijzigd en ongebruikt; een nieuwe bundel moet de correctie bevatten.

### Achtste brongebonden CI-controle

Run `41650754444`, commit `8293ed4ee8838e43b8e85d9ea2bf75d49979df11`:
schone 47/47-opbouw PASS, totale toelating NO-GO. Candidate SHA-256
`40b27c6484e7a266e261a6a67a345d79a5eb80fe3f33251af109ad6bd046f10d`
(550 bestanden); gevalideerd ZIP-artifact SHA-256
`f920c5884a769c6449d8e44dfe98af18e1e80eb5a8c8e13b580077ae6eee0f17`
met 365 bewijsbestanden plus manifest. De run is niet heropend.

Stop: `admission-auth-prefixture-unit_exit_1`. Vijf van 64 tests konden de
werkelijke Gate niet importeren uit de kandidaat: de geerfde module
`controller_v1/ci.py` ontbrak daar. De checkout bevatte deze module wel, waardoor
de eerdere lokale tests dit distributieverschil niet zagen. Geen nieuwe
Auth-/fixturecomponent-PASS en geen same-source app-PASS voor deze run.

De correctie registreert de volledige bestaande CI-overervingsketen expliciet.
Een nieuwe subprocessregressie importeert de zeven echte Gate-klassen uitsluitend
uit een geisoleerde kopie van de gedeclareerde kandidaat; netwerk is geblokkeerd.
Daarbij werd tevens gevonden dat de releasecompiler de bewust niet-vervoerde
frozen bodies in de kandidaat zocht. Alleen in de exacte staging/main-CI-context
wordt nu het bestaande `frozen_root`-argument op de checkout gericht; alle
bestaande inhoudshashes blijven vereist en deze bytes worden niet toegevoegd
aan de kandidaattransportbundel. Ontbrekende bodies en vreemde CI-scope blijven
geblokkeerd. De definitieve import- en bestaande CI-contracttests: 18 PASS in
20,913 seconden. De vijf eerder falende Auth-tests slagen afzonderlijk vanuit
de geisoleerde kandidaat (35,325 seconden); hun lokale HTTP-testserver is geen
GoTrue-/PostgreSQL-bewijs. Onafhankelijke bronreview van de vier codebestanden:
geen resterende P1/P2; zes packagingtests onafhankelijk PASS in 42,359 seconden.
Ook geneste testhelpers behouden nu de oorspronkelijke checkoutbinding, zonder
een fallback naar niet-geregistreerde code of ongepinde frozen bodies.
Dit is geen echte PG-verificatie van de nog niet bereikte samengestelde cleanup.

Pages op `03123625b59d0e9d4491b90f8c73f415042aad97`: run `41649138706`,
artifact `13236946553`, SHA-256
`18b7d37deccdaa45e34bd254c727ac5913646b3b3d0412600d73727e92384e79`.
152 runtime-assets ongewijzigd, 817 entries, zeven private paden 404 en
geen Supabase-calls. Nieuwe behoudcontrole: 1376 bestanden, dezelfde vier
eerder toegestane verschillen, nul nieuwe onverwachte afwijkingen.

External AI calls/cost: 0 / EUR 0,00.
Real-member AI enabled: NO.
Production touched: NO.

### Checkpoint: kandidaatverpakking en vroege foutafsluiting

Commit `e6958539ed10887d1be873510db43d6a3b19aa8f` bevat uitsluitend de
beoordeelde CI-verpakkingscorrectie en rapportage. Nieuwe disposable CI-run
`41656238735` gebruikt kandidaat
`cb4f401a7e808874b78c49f7da6b060a1591a7dc943e2589aab1b491c01fe451`
(556 bronbestanden). Een lopende run is geen nieuwe integrale PASS.

Pages-run `41655931750`, artifact `13240340691`, SHA-256
`a8dfbd0a666069ae105b65bc198380b49142674a32e84016803ad4d5cdc532c7`:
817 entries, alle 152 runtime-assets ongewijzigd, private roots afwezig en
zeven gecontroleerde private paden HTTP 404. Nul Supabase-calls. Lokale
behoudcontrole: 1376 bestanden, 1372 byte-identiek en uitsluitend dezelfde
vier eerder toegestane documentatie/attributes-afwijkingen. Geen nulmeting
overschreven; dit is geen hosted databehoudsmeting.

De nieuwe matrixcollector valideert voor uitsluitend `pre_migration` en
`post_migration` de oorspronkelijke brongebonden afwezigheidsreceipts.
Ontbrekende Auth is daar geen algemene uitzondering: exacte Docker-inventaris,
vier afsluitcommando's, PostgreSQL-identiteit, migratiegrens en gepinde bronnen
blijven vereist. De overige dertien cases vereisen echte lokale Auth. De
collector importeert geen code uit artifacts en controleert per case een
unieke databaseclusteridentiteit. De voorlopige bron en tests zijn nog geen
uitgevoerde vijftien-case matrix. Gerichte matrixregressies: 28 PASS; aparte
synthetische receipt-tamperingtests: 25 PASS (87,137 seconden). Onafhankelijke
review en daadwerkelijke integrale uitvoering blijven afzonderlijke gates.

### Negende CI: componentresultaten en behouden foutregistratie

Run `41656238735` is afgesloten met NO-GO op commit
`e6958539ed10887d1be873510db43d6a3b19aa8f`. Het oorspronkelijke ZIP-artifact
is gevalideerd: SHA-256
`17f824dfeffaae153de80b8c70075fa55eedac25f0770e5105f1e68c746b0ab1`,
634 bewijsbestanden plus manifest. De kandidaat is ongewijzigd:
`cb4f401a7e808874b78c49f7da6b060a1591a7dc943e2589aab1b491c01fe451`.

Schone lokale 47/47-opbouw, controller-/requestbeveiliging en appcontroles
slagen. Afzonderlijke suites: app 74 database/46 domein/4 Auth/209 browser;
composed-browser 191; account 79; offline-shell 73; registratie-12 25;
transport 4 Auth/46 database; release 359 controles, acht slices en 27 HTTP;
SQL 12; numeriek 4; filters 36. Deze overlappende suites worden niet opgeteld.
Geen package 21, echte leden-AI of hosted Supabase-uitvoering.

Alle twaalf uitgevoerde component-foutscenario's bereikten hun bedoelde
fase. Hun eigen Auth-cleanup werd bevestigd. De componentmeter registreert
2105 vooraf gereserveerde diagnostische eenheden, 313 native dispatches en
175 waargenomen managed SQL-commando's. Dit zijn verschillende teldefinities,
geen optelbare volledige eindketen. De normale case en twee migration-cases,
de integrale reserves, WAL-toelating en onafhankelijke eindreview ontbreken
nog. `diagnostic_subset_verified` is geen volledige vijftien-case PASS.

De samengestelde fixturevoorcontrole stopte bij
`producer_unexpected_privilege`. Alle tien commando's inclusief ROLLBACK
zijn bevestigd; de betreffende voorcontrole liet geen fixturemutatie toe.
De oude receipt bewaart niet welke rol/flag afweek. De officiële
Supabase-initbron noemt CREATEROLE voor Auth, maar dat is geen bewijs welke
flag in deze run faalde en geen reden om de controle te versoepelen.
De nieuwe diagnostische patch bewaart uitsluitend vaste rol-/flag-enums.
De acht metadataqueries blijven byte-identiek; geen extra SQL. Gerichte
lokale controle: 29/29 PASS. Het oude artifact blijft ongewijzigd.

Daarnaast faalde budgetpublicatie met `FileNotFoundError`. De fout is niet
gereproduceerd bij assemble in een volledig geisoleerde kandidaat of bij
het read-only verwerken van het bewaarde artifact. De precieze oorzaak is
daarom nog ONBEKEND. Nieuwe foutregistratie bewaart vaste budgetstappen en
allowlisted bronbestandsnaam/regelnummers, nooit exceptiontekst, locals,
OS-paden of credentials. Zes gerichte fouttests PASS na correctie van de
test zelf: unittest wist de traceback voordat de diagnose werd aangeroepen.
De overige 57 budget-/verpakkingstests slaagden in de voorafgaande suite.
Geen veiligheidsgrens of hosted poging is hierdoor gewijzigd.

Onafhankelijke review bevestigt de rechtenpatch (29 PASS) en de zes
foutregistratietests. Zij vond daarnaast een testvolgorde-afhankelijkheid:
in een vers lokaal proces was de reeds gepinde PG17-parser nog niet geladen.
De verpakkingstest gebruikt nu eerst de bestaande versiegebonden loader,
zonder nieuwe fallback of afhankelijkheid. Dit is een testharnesscorrectie,
geen bewijs dat de FileNotFoundError uit CI9 daarmee is verklaard.

De onafhankelijke hercontrole vond dat import-only checks geen parser nodig
hebben. De loader is daarom uitsluitend aan de budgetoperatie gekoppeld.
Beide relevante tests samen slagen in een vers proces: 2 PASS, 94,857 s.
Voorbereide kandidaat `4981c09de499d553f6dc1cff001875f5f418990efe4d85262f3996430c02099a`
blijft ongebruikt en ongewijzigd; zij is niet als CI-run gestart.
Pages op checkpoint `83665d9e238b4f6cb7d9db856f8ce3da181f1ab9`:
run `41663389407`, artifact `13243706356`, SHA-256
`f9daab5627969e062f0587946a9fd9b79b797bbcc81e718e8f64236d6e3a5da2`.
152 runtime-assets byte-identiek; 817 entries; private roots afwezig,
zeven private HTTP-paden 404; geen Supabase-calls.

Hosted blijft NO-GO; historische incomplete meetparen blijven incompleet.
External AI calls/cost: 0 / EUR 0,00. Real-member AI enabled: NO.
Production touched: NO.

### Tiende CI: twee concrete oorzaken, geen hosted toelating

Run `41664912809`, broncommit `6b9126471c4f4bea7be7e2e5f7405ce9f743f99d`,
kandidaat `ffef0563862272cdb6293150d1d7011bd07cf95fdb56d795d1310a6d1a89dec7`
(556 bestanden). Het oorspronkelijke, geverifieerde ZIP-artifact:
`1b038f458841557fea1fb06f75f38fa0a815cfab1fa662ff8d972f9a45132d75`,
634 bewijsbestanden plus manifest. Resultaat NO-GO; deze run is niet heropend.
Schone 47/47-opbouw en twaalf component-foutpaden zijn opnieuw bevestigd.
De laatste leveren 2105 prepaid eenheden, 313 native dispatches en 175
waargenomen managed SQL-commando's; geen nieuwe volledige ketenclaim.

De gesanitiseerde rechtenreceipt identificeert nu uitsluitend
`supabase_auth_admin.createrole=true`. De overige getoetste vlaggen en rollen
zijn niet als afwijkend gemeld. De tien read-only commando's inclusief
ROLLBACK zijn bevestigd. Er is geen uitzondering aan de validator toegevoegd.
Een eventuele strengere disposable Auth-runtimeconfiguratie moet afzonderlijk
worden gebouwd, brongebonden getest en als NIET-hosted-equivalent worden
herkend; een lokaal beperkt recht bewijst geen gelijke hosted configuratie.

De budgetfout is gelokaliseerd op `workflow_component` bij het laden van
`scenario.capture()`. `scenario.py` staat in Git; de originele
`workflow_local.py` zit wel in de expliciete kandidaatbundel, maar niet in
de checkout. Hergebruik van het eerder geladen checkoutmodule kan daarom
een ontbrekend pad opleveren. De regressie reproduceert die FileNotFoundError.
De correctie compileert de twee bronbestanden uit dezelfde bronroot, zonder
modulecache/pyc-fallback, en controleert oorsprong en bytes na capture opnieuw.
Beide bronhashes staan expliciet in het budgetmanifest. Ontbrekende of tijdens
capture gewijzigde bronnen blijven fouten. Alle vier budgetmodules worden
voor publicatie tevens door de bestaande kandidaatbroncontrole geverifieerd.
Gerichte suites: 105 budget-/receipttests PASS (166,808 s); orchestration en
modulebinding 25 PASS, twee platformafhankelijke tests overgeslagen. Dit is
lokale regressiecontrole, nog geen CI-bevestiging van deze laatste correctie.

De actuele officiele changelog is read-only geraadpleegd. De
[17.11-releasewaarschuwing](https://supabase.com/changelog/postgres-15-19-17-11-breaking-changes)
noemt beveiligings- en extensiewijzigingen sinds 17.6. De gepinde 17.6-image
blijft hier uitsluitend reproduceerbaar, geisoleerd synthetisch testbewijs;
geen claim dat deze de actuele veilige hosted runtimeversie is. De pin is
niet stilzwijgend vervangen. [Auth-URL-wijzigingen](https://supabase.com/changelog/47093-self-hosted-supabase-api-external-url-to-include-auth-v1)
en [HTTP TLS-cipheruitfasering](https://supabase.com/changelog/cbc-tls-ciphers-deprecated)
geven geen aanleiding voor een beveiligingsverlaging of hosted aanpassing.
Geen hosted verbinding, migration, JIT, fixturecleanup of owner-testvenster.

Onafhankelijke bronreview van de vier correctiebestanden: geen P1/P2.
Drie scenario-bronregressies PASS; twee gerichte volgordecontroles PASS.
De gewijzigde componenten en hun budgetregistratie draaien nu voor de
onaangeraakte app-/browsermatrix. Een component- of budgetexception stopt
die vervolgmatrix; geen verplichte check is verwijderd. De gerichte
orchestration-suite na deze volgordewijziging: 13 PASS, 0,147 s.
Dit voorkomt herhaling van dure, ongewijzigde suites bij een reeds bekende
vroege blokkade. Het vervangt geen same-source volledige CI-toelating.

### Kandidaatstart voor database-installatie afgeschermd

De entry gebruikt een gehashte, exclusief opgeslagen pre-databasehandoff en
een verse `-B -I`-interpreter vanuit de kandidaat. Zij controleert bronnen
opnieuw en maakt eenmaal de prepared-owner; dezelfde ledger moet naar de
platforminstallatie en de case gaan. Geen tweede fetch, UUID of ledger-open.
De platforminstaller ontbreekt nog in de volledige samenstelling: daarom
blijft de entry gesloten en is geen matrixdatabase gestart.

Agenttest 18 PASS; onafhankelijke review 18 PASS (3,038 s), geen P1/P2;
na integratie 18 PASS (1,642 s). Dit is dezelfde suite, niet 54 unieke tests.
Main behoudt CRLF; de inhoud is na LF-normalisatie exact de beoordeelde
levering. Raw SHA-256 van `case_stack_v1/ci.py`:
`6bf681fc68b0ea47bb91a0f17c522553f8e0a9955432fadd669d17c6ac494432`;
`case_stack_v1/test_ci.py`:
`ea28e946074249e3ea8b8ed26446463821b8acd4b622b3c72e914e753ed82168`.
Geen PG-, GoTrue-, volledige-keten- of hosted-PASS uit deze tests afgeleid.

### 4 november: gedeeltelijke Auth-start en originele bewijsbestanden

De bestaande opt-in lokale Auth-helper bewaart nu de bevestigde synthetische
accountidentiteit voor de login begint. Bij een fout voor het teruggeven van
de context kan alleen de daadwerkelijk geregistreerde subset worden opgeruimd.
Een onbekend createantwoord, onvolledige writerbarrier of ontbrekend
eigenaarschapsbewijs blijft NO-GO. Dezelfde parent-delete-engine wordt gebruikt;
geen automatische retry, refund, globale nulclaim of nieuwe hosted bevoegdheid.
Een secundaire opslag- of containerafsluitfout vervangt de oorspronkelijke
fout niet. De standaard app-Auth-route blijft ongewijzigd; de uitbreiding is
expliciet opt-in voor de lokale bewijsroute.

Na integratie: 29 gerichte regressies PASS, 183,974 s. Dit zijn filesystem- en
lokale HTTP-tests met gesimuleerde PG/Dockergrenzen, geen echte GoTrue/PG- of
hosted-PASS. De onafhankelijke gerichte hercontrole van de vier aanvullende
foutbehoudcorrecties voerde drie tests uit (60,783 s); de vierde wijziging is
bronmatig beoordeeld. Deze overlappende aantallen worden niet opgeteld.
De bestaande parent-finalizerregressies blijven behouden: 46 PASS, 132,009 s.

De nieuwe case-afsluiting gebruikt originele bewijsbestanden in submappen.
De bestaande CI-upload neemt uitsluitend flat bestanden mee. Daarom is een
expliciete, verliesvrije verpakking toegevoegd: alleen vooraf genoemde
bestanden, originele paden en hashes, begrensde fragmenten, exclusieve opslag
en onafhankelijke readback. Geen recursieve export. Een ontbrekend fragment,
gewijzigde bron, dubbel record, afgebroken index of tegenstrijdige flat kopie
blokkeert. Windows-padaliassen met afsluitende punten en device-namen worden
geweigerd na een onafhankelijk gereproduceerde reviewbevinding.

De lokale combinatie archive/matrix/bootstrap: 80 tests, 79 PASS en een
Windows-symlinktest overgeslagen wegens ontbrekend symlinkrecht, 50,180 s.
Dit is transport- en orchestrationbewijs. De oorspronkelijke journals moeten
daarnaast inhoudelijk opnieuw worden gecontroleerd. De collector geeft daarom
geen complete matrixstatus op basis van alleen CASE_PASS en isolatievelden.
Zolang de onafhankelijke terminalcontrole ontbreekt, blijft de betreffende
case expliciet `terminal_semantics_unverified`.

De application-job van de nieuwe matrix is afzonderlijk gemaakt: dezelfde
app-regressies, advisors, dry-run en lokale contracttests blijven verplicht.
De read-only bridgeoverride blijft behouden; de oude quota-DML wordt niet
opnieuw geintroduceerd. De vijftien geisoleerde echte cases vervangen de oude
componentuitvoering alleen in deze nieuwe matrix. Oude CI-fouten blijven
ongewijzigd historische fouten. `CLEAN_CI_PASS` voor de application-job is
geen volledige toelating; de overige cases en onafhankelijke beoordeling
blijven vereist. Deze nieuwe samenstelling is nog niet als CI gestart.

Laatste geverifieerde publicatie: bron
`f0ed6b2136edd283cbef3c989b65aceb3704f153`, Pages-run `41856131067`, artifact
`13336933092`, SHA-256
`cd8ffbe04629075de677ced32336f55f30a57f5731b524546950926e6525e375`.
152 runtime-assets byte-identiek, 817 entries, private bronroots afwezig en
zeven private HTTP-paden 404. Deze publicatie bewijst niet de latere lokale
wijzigingen. De laatste lokale behoudcontrole bevat 1376 bestanden: 1372
exact gelijk en vier eerder toegestane bronverschillen ongewijzigd; nul
onverwachte verschillen. Dit is geen meting van hosted ledengegevens.

Actief: volledige platform-/Auth-startbegroting, native-querybinding,
echte vijftien-case-samenstelling en inhoudelijke terminalcontrole.
Hosted blijft gesloten; de onafhankelijke WAL-blokkade blijft staan.
Geen Supabase-, JIT-, migration-, Auth- of fixturehandeling uitgevoerd.

Onafhankelijke checkpointreview: geen resterende P1/P2 in de archive- en
matrixdelta; negen gerichte regressies PASS, 0,096 s. De review bevestigt
uitsluitend deze bron-/orchestrationvoorbereiding, niet C-closeout,
D-terminalsemantiek, een echte PG-keten of hosted toelating.
Aanvullende gerichte CI-/verpakkingscontrole: 20 tests PASS, 42,240 s.

### Gepubliceerde checkpoint en verplichte Auth-dekking

Checkpoint `582e051e7e5b098f66162e174725ccd66bce220d` is gepusht. Pages-run
`41862460770` had eerst een geslaagde build en een wachtende deploy. Daarbij
is uitsluitend read-only status bekeken; geen omgevingsregel, approval of
runnerinstelling is gewijzigd. Een afzonderlijke build-only receipt claimt
uitdrukkelijk geen publicatie. Daarna is de voltooide publicatie onafhankelijk
geverifieerd: artifact `13340696554`, SHA-256
`5f5b188d5e97b5996156315f6277ff33b5658c8eda020d1586c7ae8b175bb547`.
817 entries, alle 152 runtime-assets byte-identiek, private bronroots afwezig
en zeven private HTTP-paden 404. Geen Supabase-calls.

Een verdere collectorcontrole weigert ook Windows-devicenamen in flat
ZIP-entries en bindt de volledige terminal-broninventaris aan de onafhankelijk
voorbereide kandidaat. De vijftien fasecases vervangen niet de elf bestaande
Auth-foutprobes. De matrix blijft daarom ook geblokkeerd zolang onafhankelijk
geverifieerde Auth-dekking ontbreekt of niet aan hetzelfde originele artifact
en bronmanifest is gebonden. De actuele lokale matrixsuite: 38 PASS, 0,514 s;
geen uitvoering van echte Auth of PostgreSQL in die suite.

In de nog niet geintegreerde root-ledger vond onafhankelijke review een P2:
een preread-fout in `_save` zette de permanente foutblokkering niet. Een
herhaalde settlement kon daardoor dezelfde waarneming 17 naar 34 tellen.
De oude snapshot blijft fout; haar hash is
`a30774a116adfde69dd60099ce0f37fd909c6afb87b23c0eee4c5c12ba33a134`.
De gecorrigeerde snapshot omvat preread en serialisatie in dezelfde blijvende
foutafhandeling als append/fsync. Hash:
`d10a9910efb127fa6b805c5eee1aa16b939a95ccecf1267cea64605a5634a809`.
Onafhankelijke hercontrole: 68 tests PASS, 1,548 s, plus een afzonderlijke
vierpadreproducer. Herhaling en close worden geweigerd, dezelfde oorspronkelijke
exception en journalbytes blijven behouden, geen refund. Dit sluit die ene
P2, niet de volledige commandobegroting of matrix.

De onafhankelijke review van de daaropvolgende matrixdelta vond geen P1/P2:
tien geselecteerde tests PASS (0,051 s) en 32 aanvullende negatieve controles.
Deze controleren Windows-devicepaden, exacte terminal-bronmappen en alle elf
afzonderlijke Auth-probes. Beide onafhankelijke verifiervelden blijven `None`
tot de oorspronkelijke journals semantisch zijn gecontroleerd; aangeleverde
PASS-labels of gelijkvormige JSON-objecten zijn daarvoor niet voldoende.

### 11 november: originele canonical-prefix en foutbehoud

Werk hervat met maximaal twee bestaande agents: A voor onafhankelijke
bron-/budgetreplay en D voor originele worker-/afsluitbewijzen. Geen nieuwe
agent, hosted poging, Supabase-verbinding, JIT, Auth, migration, fixturecleanup,
ownerwindow of package21-handeling. Start-HEAD lokaal
`483785b4bd27525c7d0f808f24df7e399f27ce96`; remote read-only bevestigd op
`582e051e7e5b098f66162e174725ccd66bce220d`. Oudere werkboomwijzigingen blijven
behouden. Deze paragraaf is geen volledige toelating of afrondingsclaim.

De lokale schone-opbouwadapter bewaart nu voor ieder van de oorspronkelijke
44 migrations de originele policy, dispatchledger, preregistratie, numerieke
voor-/nameting en isolatiereceipt. Een unieke case-UUID en de echte CI-run-ID
lopen door tot de onderliggende policy en ledgerheader. De compiler weigert
hergebruik, verkeerde bronbytes, andere migrationvolgorde en niet-lokale
doelen. De nieuwe prefix is uitsluitend voor de disposable lokale CI-opbouw;
de bestaande hosted-equivalente CLI-grenzen blijven ongewijzigd.

Een exclusief geschreven, fsync/readback-gecontroleerd prefixmanifest verbindt
alle 44 originele meetsets met kandidaat, bronnen en case. Het wordt opgeslagen
voordat de M45-foutcallback kan starten. De bestaande catalogusmeting na M40
heeft een eigen vooraf opgeslagen reservering, intent en oorspronkelijke
commandoreceipt. De lege lokale migrationregistratietabel wordt eenmaal
voorbereid met zeven normale commando's en een vooraf gereserveerde rollback.
Er wordt daarbij geen migrationversie geregistreerd. Een verloren commitantwoord
blijft onbekend; ontbrekende bewijsbestanden worden niet gereconstrueerd.

Tijdens gerichte review is een dubbel foutpad gereproduceerd: een fout in de
nameting kon de eerdere uitvoeringsfout vervangen. Drie nieuwe tests faalden
eerst (een assertion en twee ontbrekende fasevelden). De adapter bewaart nu
de oorspronkelijke fout, de afzonderlijke meetfase/foutklasse en de reeds
beschikbare voormeting. Een ontbrekende nameting blijft NO-GO. Een fout bij
runtime-afsluiting verhindert niet langer het bewaren van de oorspronkelijke
ledger; een mislukte runtimeconstructie bij provisioning krijgt eveneens een
duurzame mislukte receipt. Geen exceptioninhoud of credential wordt toegevoegd.

Actuele lokale bewijzen, niet kunstmatig opgeteld:

- CLI Python-regressies: 100 PASS, 30,226 s. De gerichte 46 PASS in 27,173 s
  zijn hierin opgenomen en worden niet als extra tests geteld.
- Node hook/policy: 40 PASS, 7,454 s; waaronder parsing van alle 44 werkelijke
  migrationbronnen met de vastgelegde PG17-parser.
- Case-stack/original-reference-suite: 71 PASS, 112,761 s.
- Behoudscontrole: 1376 beschermde bestanden, 1372 byte-identiek en dezelfde
  vier eerder toegestane verschillen; nul onverwachte verschillen. De
  oorspronkelijke baseline blijft ongewijzigd, SHA-256
  `213673e2a04f04b715f247efe3f27263c0dc998859d5d7e54685a356412f8fef`.

Dit zijn lokale parser-, protocol-, filesystem- en fake-transporttests. Zij
bewijzen geen nieuwe echte PG/GoTrue-uitvoering, volledige foutpadmatrix,
hosted databehoud of publicatie van deze delta. Het prefixmanifest vermeldt
daarom expliciet `independent_numeric_validation=false`, onbekende impliciete
driverkosten en een onbekend volledig SQL-totaal.

Onafhankelijke bronreview vond daarna twee P2's: niet-transitief gecontroleerde
catalogusreferenties en een directe bootstraproute die twee gereserveerde
UUID's niet expliciet weigerde. De producer controleert nu ook de originele
command-, reserve- en intentbestanden en de volledige catalogusidentiteit.
Zowel bootstrap als prefix-plan weigeren de oktober- en preparation-UUID.
De run-ID-controle staat voor het schrijven van de bronreceipt, zodat een
afgewezen ID geen volgende testaanroep met een bestaand bewijsbestand blokkeert.

De uitgebreide case-suite telde 77 tests: 76 geslaagd, een fout in de tweede
gereserveerde-UUID-controle door die te late bronreceipt. Na vervroeging van de
controle slagen alle 18 gerichte identiteit-/catalogusregressies (59,966 s).
De afzonderlijke prefix-ID-test slaagt ook (0,578 s). Eerdere rode uitkomsten
blijven historische fouten; deze overlappende tests worden niet opgeteld of
gepresenteerd als een nieuwe volledige CI-run.

Onafhankelijke herreview sluit beide P2's voor de huidige bron: geen resterende
P1/P2 binnen deze twee correcties. A's reader/source-controles: 45 PASS,
67,091 s, uitsluitend synthetisch/brongebonden. Gebonden SHA-256:

- bootstrap.py: `6e3f2b1ecaa1945a0bd20256c4fec91f9c25310153ae499eebcc6e4c986b3c33`.
- prefix_receipt.py: `aaa3e8991d4b3f3914a7f461dd93c28ceeb513de5317b9b570df8bc80f72c8d3`.
- prefix.py: `a4d20abb8a583dab4f9c683d3d515efc86e32c8e23a5298194e72048f4706546`.

Deze review betreft originele referentievolledigheid en vroege run-ID-weigering,
niet de volledige numerieke replay, driverkosten of volledige CI-toelating.

De 44 lokale bestanden bevatten 1552 body-statements; hun afzonderlijke
CLI-reserveringen tellen op tot 2256. Dit is niet het volledige lokale of
hosted register: observers, isolatie, provisioning, startup, drivers en latere
fasen zijn daarin niet inbegrepen. De onafhankelijke rootkandidaat heeft
evenmin een bewezen volledige bovengrens: een eerdere onvolledige
bronberekening gaf normale broncapaciteit 2340 en meterondergrens 2352.
Dit is geen opnieuw berekend maximum voor D's latere bronwijzigingen.
Dispatch-/herstelverbindingen en platform- en managed-Auth-kosten ontbreken
nog. Historisch 2338/731 en de geautoriseerde hostedgrens
2349 blijven ongewijzigd. Er wordt geen nieuwe willekeurige grens gevraagd.

Nog actief: onafhankelijke inhoudelijke replay van deze oorspronkelijke
prefixbestanden; originele gewachte worker-exit/result/exportregistraties;
volledige native-/recoverydekking, platform/resetepochs, Linux-driverbinding,
Auth- en afsluitmetingen. Daarna pas kan een nieuwe volledige brongebonden CI
worden toegelaten. De bestaande WAL-beperking blijft afzonderlijk staan;
geen vierde diagnose volgens de uitgeputte methode. Hosted en ownertelefoontest
blijven NO-GO. Geen owneracceptatie, freeze of overdracht aan JARVIS.
