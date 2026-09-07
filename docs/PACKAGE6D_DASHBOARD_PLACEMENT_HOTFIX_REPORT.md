# Package 6D Final Dashboard Placement Hotfix

Datum: 2026-09-07.
Status: **PACKAGE 6D FINAL DASHBOARD PLACEMENT HOTFIX - READY FOR OWNER RETEST**.
Niet owner-accepted of frozen. Alleen frontend/dashboardpresentatie.

## Preflight En Scope

Werkrepository: `C:\Users\Fitme\OneDrive\Documenten\Fit Met Zorge\Zip github fitmetzorge staging\fitmetzorge-staging-main\supabase\.temp\phase4fb-staging-deploy`.
Schone main bij aanvang; HEAD, origin/main en werkelijke remote main waren alle
`ef7d1eeebda5fff91b8bbf01e3000ad83c0d16f8`.
AGENTS.md en .codex/config.toml gelezen: on-request met auto_review,
workspace-write, project network_access=true en permanente staging-autonomie.
Managed netwerkbeperkingen blijven leidend; geen globale instellingen veranderd.

De owner bevestigt dat Later, openen, read-persistentie, mobiel detail en overige
Package 6D-onderdelen werken. Dat bewijs blijft geldig. De nieuwste bijlage vraagt
uitsluitend correcte dashboardvolgorde en styling. Productie blijft verboden.

Alleen Yourizorge/fitmetzorge-staging/main en zijn
[stagingfrontend](https://yourizorge.github.io/fitmetzorge-staging/) zijn gebruikt.
Geen databasequery/write, migration, Edge-deploy, mail, Brevo-onderzoek, handmatige
bevestiging, bestaande trainerkoppeling, provideractivatie, betaling of bestandscleanup.

## Oorzaak En Correctie

1. **Verkeerde compositie.** renderDashboard gebruikte home.prepend(node) op de hele
   client-home-view. De inbox stond daardoor voor clientSummary, buiten de echte
   member-ux-today-simplified-structuur. De analyse begon in de 390px-nulmeting op
   documentpositie y=76, terwijl de begroeting pas op y=321.58 begon.
2. **Afwijkende stijl.** De inbox gebruikte randloze/transparante rijen met 0px
   hoekradius, 0px horizontale padding, 0px rijafstand en secondary-knoppen.
   Check-in gebruikt member-ux-card: 8px hoeken, 14px padding, 12px onderlinge
   ruimte, de bestaande surface/rand en primary-knoppen.
3. **Hydrationverspringing op tablet.** Een oude zijbalkregel zette content in gridrij 3,
   terwijl de member-shell twee expliciete rijen had. De lege 1fr-rij verschoof de
   begroeting bij toenemende dashboardhoogte. Alleen op het actieve memberdashboard
   wordt content nu expliciet in rij 2 geplaatst.

De inbox wordt direct NA de bestaande trainingskaart gemonteerd, binnen dezelfde
dashboard-shell. Bij onvolledig profiel volgt hij de bestaande profiel-CTA, nooit
de begroeting voorafgaand. Zonder gereed dashboardanker wordt geen los alternatief
bovenaan aangemaakt. Het bestaande renderClientHome wordt na zijn normale render
aangevuld; ook rechtstreekse dashboardherbouw behoudt het analyseonderdeel.

Volgorde: begroeting plus bestaande intro, Check-in, Klaar om te trainen,
Klaar voor jou, overige bestaande onderdelen. Geen nieuwe tweede dashboardbron.
De groepssectie is onframed; elk herhaald analyseresultaat gebruikt de bestaande
member-ux-card-klasse, zonder kaarten-in-kaarten.

Kaarten bevatten type, compacte tweeregelige titel, datum/tijd, eventueel Nieuw,
de bestaande primary-knop en archieficoon. De volledige korte titel blijft in DOM/title
beschikbaar en in het detail; lange woorden wrappen. Alle analyses is een rustige
onderstreepte knop onder de lijst en opent dezelfde geschiedenis.
Een gereserveerde statusruimte voorkomt hoogteverschil wanneer Nieuw verdwijnt.
De actierij houdt aan beide kanten ruimte voor de bestaande zwevende avatar, zonder
avatarbron, positievoorkeur of gedrag te veranderen; op smalle schermen wrappen acties.

## Ongewijzigd Gedrag

Server-RPCs en alle notification/result/generatie/retentiecontracten zijn byte-ongewijzigd.
Nog steeds maximaal drie server-authoritative recente analyses. Later sluit de toast;
opened behoudt de kaart zonder Nieuw. Refresh, nieuwe login, retry, archief, delete,
verdringing en exacte deep links behouden hun bestaande gedrag. Geen browserpersistente
analysekopie, nieuwe user-ID-parameter, directe tablewrite of providerroute.

Git-diff tegen de startcommit bevestigt geen wijziging in supabase (inclusief alle
migrations/tests/Edge-bronnen), app.bundle.js, member-ux-consistency.js,
phase1-foundation.js, phase3-training-engine.js, phase6c-private-ai-chat.js,
phase6d-owner-settings.js/.css of de goedgekeurde avatar.
De mobile-detail-CSS is behouden. Alleen inboxpresentatie, dashboardcompositie en de
drie relevante cacheverwijzingen in app.js/index.html zijn runtimewijzigingen.

## Verificatie

Nieuwe suite: assets/phase6d-dashboard-placement-browser-check.cjs.
Zij gebruikt het volledige echte dashboard met een ingevuld synthetisch memberprofiel,
inclusief de ongewijzigde onboarding- en dashboardrenderers. Geen HTML-dashboardmock,
beschermende test-CSS of echte memberlogin. In live-modus worden de gepubliceerde
assets opgehaald; uitsluitend Auth/RPC-antwoorden zijn synthetisch en elke echte
Supabase-memberrequest wordt geblokkeerd. Synthetische browsercontexten worden gesloten.

De suite controleert documentvolgorde, echte rectangles van alle zichtbare analyse-
descendants, html/body scrollWidth, kaartstijlen tegenover Check-in, titel/knoptypografie,
spacing, lifecycle, beide avatarzijden en stabiele ankers tijdens vertraagde hydration.
Ook directe renderClientHome, terugkeer naar Vandaag en onvolledig onboardingprofiel
zijn getest. NL/EN/DE, lange titels en licht/donker blijven binnen dezelfde kaartbreedte.

| Viewport | Check-in- en analysekaartbreedte | Overbrede analyse-elementen |
| --- | --- | --- |
| 320x700 | 292px | 0 |
| 360x800 | 332px | 0 |
| 390x844 | 362px | 0 |
| 820x1180 | 770.8125px | 0 |
| 1180x900 | 420px | 0 |
| 1440x900 | 420px | 0 |

De bestaande smallere desktopdashboardkolom is bewust behouden; dit is geen redesign.
Zie [machineleesbaar bewijs](PACKAGE6D_DASHBOARD_PLACEMENT_HOTFIX_EVIDENCE.json) voor
alle layoutmetingen, behouden regressies en de afzonderlijke live asset-SHA256s.
Alle kaarten delen 14px padding, 8px radius, rand/surface/schaduw, 17px titeltypografie en
12px tussenruimte. Bestaande begroeting/Check-in/training verplaatsen niet door
inboxhydration; een identieke vertraagde refresh wijzigt ook de kaartgeometrie niet.

- Plaatsingssuite: 426/426, 36 layouts, lokaal en met live staging-assets.
- Behouden mobiele analyse/detail/lifecyclesuite: 180/180, 25 layouts, lokaal.
- Assembled ownerbrowser: 323/323; publieke Auth-browser: 88/88.
- Frozen runner: alle 20 suites exitcode 0, inclusief 6D-browser 48, 6D0-browser 41,
  Phase5-browser 53, 6C-browser 85 en Nutrition-browser 138.
- Static: Phase1 75, MemberUX 56, Phase2 46, Phase3 222, Phase4 90, 4F-E 45,
  Phase5 116, 6A 93, 6B 98, 6C 117, 6D 17 en Auth 26.
- Workout flush-order 6; invite/chat/analysis handlers en migrationidentitytests PASS.
- 42 live assets HTTP 200 en byte-identiek aan runtimecommit, met SHA256-bewijs.
  Vier publieke live viewports: nul errors, mutating requests en verkeerde projecttargets.
- Syntax/diffcontrole PASS. Er zijn geen live databasefixtures aangemaakt.

### Testharnas Correcties

De vorige ownerfixture had geen geselecteerde client, waardoor de echte begroeting en
Check-in niet verschenen. De gedeelde testprobe maakt nu uitsluitend in het browser-
geheugen een synthetisch ingevuld profiel via de bestaande apphelper. Geen runtimegate
of onboardingcontract is gemockt/weggelaten.

Er is tevens een Edge/Playwright-testbijwerking bewezen: op een lege lange testpagina
gaf een fullPage-screenshot voor de opname pointer:coarse/touch1 en daarna
pointer:fine/touch0. Met het nu echt gevulde dashboard trad dit ook in de oude chat-
Enter-test op. Die toets werd daardoor als desktop-Enter behandeld, conform de
ongewijzigde chatlogica. Viewport-screenshots behouden touch-emulatie; de mobiele test
assert nu ook expliciet coarse-pointer. Geen product-CSS of chatlogica hiervoor gewijzigd.

De scrolltest wacht nu op de bestaande hydration/render-animationframes voordat hij
een gebruikersscroll simuleert; de initialisatieanimatie wordt eveneens eerst voltooid
voor stabiele geometrievergelijking. De asserts blijven intact. Er is geen CSS toegevoegd
om fouten te maskeren. Alleen aantoonbaar afgeronde eindruns gelden als PASS.

## Achttien Ownergevallen

| Nr | Geval | Technisch bewijs |
| --- | --- | --- |
| 1 | Begroeting bovenaan | Echte shell-first en documentgeometrie, zes formaten |
| 2 | Analyse nooit voor begroeting | Inbox in dezelfde shell, ook incomplete onboarding |
| 3 | Na Check-in en training | training.nextElementSibling is exact de inbox |
| 4 | Dezelfde stijl | Computed padding/radius/rand/surface/shadow/typografie/knoppen gelijk |
| 5 | Later op juiste plek | Werkelijke browseractie en direct volgende compositiemeting |
| 6 | Nieuw-label | Serverfixture-new/later plus zichtbaar label |
| 7 | Openen verwijdert alleen Nieuw | Exact open/read, badge weg en gelijke kaarthoogte |
| 8 | Kaart blijft na bekijken | Aantal en exacte resultaat-ID behouden |
| 9 | Refresh | Volledige pagereload en hydration |
| 10 | Nieuwe login | Logout/nieuwe application entry en hydration |
| 11 | Hoogstens drie | Vijf eigen resultaten leveren exact de nieuwste drie IDs |
| 12 | Alle analyses | Dezelfde geschiedenis toont alle vijf toegestane testresultaten |
| 13 | Geen duplicaten | Herhaalde hydration, directe render, viewwissel en reload |
| 14 | Geen overflow | Alle zichtbare analyse-descendants plus html/body, zes formaten |
| 15 | Eerdere regressies | 180 analysechecks, 323 ownerchecks, 88 Auth en frozen runner PASS |
| 16 | Live gelijk Git | 42 afzonderlijke assets byte-identiek aan immutable runtimecommit |
| 17 | 0 externe calls / EUR 0,00 | Synthetische browser-RPCs; echte requests geblokkeerd; providers ongewijzigd |
| 18 | Productie onaangeraakt | Alleen staging Git/Pages; geen DB/Edge/production handelingen |

Own-user isolation wordt in de behouden tests afgedwongen via exacte resultaat-ID en
membergebonden contracten; de eerder geteste SQL/RLS/RPC-implementatie is ongewijzigd.
De nieuwe tests zijn geen claim van een nieuwe live SQL-securityaudit.

## Deployment, Data En Grenzen

Runtime/testcommit: `7fec9da7cb00cb7dff4a601810ddd2c977db0f5f`
(`fix(phase6d): place recent analyses in the member dashboard`), gepusht naar staging main.
Cache voor app-entry/inbox/hotfix-CSS: `20260907-dashboard-placement1`.
De nieuwe live assetcontrole bevat ook member-ux-consistency.js, de bron van de
hergebruikte dashboardstijlen. Documentatie/bewijs wordt apart logisch gecommit;
de finale documentcommit staat in de eindoplevering en Git-log.

Geen migration aangemaakt of toegepast. De bestaande reeks van 30 migrations is niet
veranderd; migration list/dry-run/SQL-replay zijn voor deze frontend-only wijziging
niet opnieuw uitgevoerd. Geen Edge-deploy of wijziging van workerconfig/consent/data.
Daarom is er geen nieuwe datafingerprint-/schema-diffclaim; het bewijs is nul database-
writehandelingen en ongewijzigde beschermde bronbestanden. Externe AI-calls door deze
opdracht: 0, kosten EUR 0,00. Geen bestaande memberdata naar een provider gestuurd.

Geen PostgreSQL- of OneDrive-bestanden verwijderd. De eerdere beperking rond het
onbekende verwijdermanifest van 971 items en de lokale pg_cron-rebuild blijft ongewijzigd.
Geen billing, nieuw juridisch/productcontract of volgende package gestart.

## Exacte Volgende Stap

Open [staging](https://yourizorge.github.io/fitmetzorge-staging/) opnieuw op de telefoon
en ververs. Controleer achtereenvolgens begroeting/intro, Check-in, Klaar om te trainen
en Klaar voor jou. Open de bestaande analyse: alleen Nieuw verdwijnt, de kaart blijft.
Controleer na refresh/nieuwe login dezelfde plaatsing en dat de avatar geen analyseknop
bedekt. De eerdere mobiele detailfix blijft behouden.

De owner hoeft geen nieuwe mail te versturen of trainerrol te krijgen.
Geen technisch blocker voor deze presentatiehotfix; fysieke ownerretest en expliciete
acceptatie blijven vereist voordat Package 6D accepted/frozen kan worden verklaard.
