# Package 6E-5 Contracten

TECHNICAL PASS / READY FOR OWNER REVIEW - OFFLINE ONLY.
Geen owneracceptatie/freeze van 6E-5, geen live AI of volgend pakket.
6E-4/V1/V2 is afzonderlijk accepted/frozen; eerdere besluiten blijven intact.

## Architectuur En Afbakening

Enige nieuwe code: _offline/phase6e5. common/validate/engine/review en tests.
6E-0..6E-4 worden read-only gebruikt; hun 89 bestanden blijven byte-identiek.
Het oude voorlopige 6E-5-providerlabel was nooit geimplementeerd. Deze expliciete
GO benoemt offline progressie/goedkeuringssimulatie, GEEN provider-/actieintegratie.

Bestaande domeinen leveren later eventueel doelen, schema's, oefeningen,
sessiesnapshots en setlogs. Hun aanwezigheid is geen geautoriseerde AI-readset.
6E-4 levert read-only actuele doel/plan/relatie/bevoegdheid/grenzen/selectie/catalogus,
toegang en context. Nieuwe testregels leveren apart de bevoegdheid en inhoud voor
DEZE synthetische progressiesimulatie; een trainerlink of bestaande 6E-4-kandidaat
verleent op zichzelf geen progressie- of wijzigingsrecht.

propose(request, context, authority) gebruikt de opaque uitgegeven 6E-4-context.
Request bevat synthetic_only, locale, binding, base (exact 6E-4-request),
expected_progression (policy_ref/history_ref), policy en history.
Alleen synthetische IDs en deterministische, geinjecteerde tijden. Geen klok,
netwerk, provider, filesystem of storage in de kern; SHA-256 is uitsluitend een
deterministische inhoudsidentiteit, GEEN live handtekening of trainerattestatie.

## Bronnen En Validators

| Bron | Expliciete voorwaarden |
| --- | --- |
| Actuele base | Ongewijzigde 6E-4-validators: exact eigen lid, huidige zes bronrefs, readset op beoordelingsmoment, actieve trainerbevoegdheid/relatie, expliciete volgende optie en volledige grenzen |
| policy | Eigen ID/revisie/status/capture/geldigheid, exacte trainer/relatie/bevoegdheid/plan/doel/grenzenrefs. purpose=synthetic_test_rules_only, permission=simulate_progression_and_plan_review. required_approvals exact lid EN trainer |
| Tijdvensters | Expliciet huidige en aansluitende volgende bronweek, elk zeven dagen; evaluatievenster ligt binnen huidige week. Historisch beoordelingsvenster eindigt niet na de start van evaluatie. Begin inclusief, evaluatie-einde exclusief. Geen systeemklok of verzonnen maximale ouderdom |
| rules | Unieke oefening/catalogus/workout/variant/apparaat/setcount, kg of lb, minimumaantal trainingen, expliciet vergelijkbare historische plan- en doelrefs, reps-stap/plafond/reset, strikt oplopende beschikbare gewichten, aparte RIR/RPE-voorwaarden en expliciete uitzonderingsparen |
| history | Eigen versie en read_at op hetzelfde moment, exact gedeclareerd compleet venster en workout. Bounded lijst sessies met unieke IDs en voltooimomenten; geen cherry-picking door de engine uit onvolledig gedeclareerde dekking |
| Historische sessie | Eigen lid/workout/revisie, start/voltooitijd, voltooide status. Historische snapshot-ID/lid/sessie/plan/doel/workout plus exacte oefening/catalogus/variant/apparaat/sets; snapshot niet na sessiestart |
| Setlog | Unieke eigen ID plus exact lid/sessie/snapshot/oefening/setnummer; voltooid, reps/load/unit, aparte null-of-RIR/RPE en confirmed/disputed bronkwaliteit. Geen onbekende tuple, dubbel log, ontbrekende set of toekomstige uitvoering |

Actuele schema- en doelversies vervangen nooit historische snapshotrefs.
Alleen een expliciete huidige regel mag oude versies vergelijkbaar verklaren;
ook dan moeten variant/apparaat/unit/setopzet en oorspronkelijke plandoelen passen.
De snapshot is geen verwijzing die later opnieuw met actuele schemawaarden wordt gevuld.
Herhalingsbereiken of ongelijke geplande setdoelen krijgen in deze versie een
concrete beperking: geen keuze uit het bereik of gemiddelde als nieuw voorschrift.

Bronconsistentie bewijst GEEN authentieke live herkomst, complete echte historie,
geldige medische trainerautoriteit of niet-vervalste verklaringen. Een coherent
liegende bronleverancier wordt offline niet ontmaskerd. Later zijn serverauth,
betrouwbare capture/versies/intrekking, complete bronlevering en concurrentiebewijs vereist.

## Berekening Per Oefening

De expliciete testregel bepaalt minimumaantal en recent venster. Deze contractversie
evalueert de laatste N voltooide trainingen, N=minimum_sessions, gesorteerd op
voltooitijd. Een betwiste registratie of expliciet conflicterend RIR/RPE-paar in
het GEHELE meegeleverde recente venster wordt nooit door die selectie genegeerd.

Alle gebruikte historische geplande sets moeten dezelfde exacte huidige
reps/load-opzet hebben; geregistreerde reps mogen uiteraard onder het doel liggen.
Dat is een prestatie, geen ontbrekende set. Ontbrekende/partiele setlogs zijn
daarentegen onvoldoende bronbewijs en worden niet als een voltooide nulset behandeld.

1. Alle vereiste werkelijke sets halen huidige targetreps en de expliciete
   RIR/RPE-testvoorwaarden, huidige target onder het reps-plafond: reps_step erbij.
   De volledige stap moet passen; niet clampen naar een zelfgekozen kleiner verschil.
2. Alle vereiste sets halen het expliciete reps-plafond: uitsluitend de eerstvolgende
   waarde uit available_weights, met exact de bron-resetreps. Huidige en volgende
   waarde moeten beide voorkomen; geen impliciete afronding, plate- of kg/lb-conversie.
3. Het repsdoel of een expliciete inspanningsvoorwaarde wordt niet in alle vereiste
   sets gehaald: de aangeleverde maintain_when-regel behoudt het BESTAANDE PLANDOEL.
   Dit betekent niet dat een werkelijk lagere geregistreerde prestatie wordt herschreven
   of dat de volgende uitvoering gegarandeerd dat doel haalt.
4. Ontbrekende gegevens/regel, betwiste bron, verkeerde binding of een voorgestelde
   waarde buiten een exacte trainergrens: concrete beperking, geen verzonnen fallback.
   Behouden is niet de automatische uitkomst van onvoldoende informatie.

Geen wijziging van oefeningsidentiteit, setaantal, frequentie of medische criteria.
RIR/RPE blijven afzonderlijk. Null is niet nul; RIR 0 is geldig en RPE 0 niet volgens
het bestaande invoerformaat. Zonder expliciete pair-rule wordt geen inverse relatie
of tegenstrijdigheid aangenomen. De testregels zelf bewijzen geen belastbaarheid.

Uitvoer: per oefening huidige planwaarden, werkelijke gelinkte setregistraties,
volgende-weekwaarden, keuze/reden, testregel en exacte grenzen/bronrefs.
Geldige rijen kunnen bij ontbrekende informatie elders getoond worden als partial;
er komt dan GEEN toepasbare gezamenlijke schema-optie. Alles behouden geeft
concrete waarden maar geen onnodig wijzigingsvoorstel.

## Goedkeuringssimulatie

workspace(issuedOption) maakt een afzonderlijk in-memory scenario voor een plan.
create(issuedOption, workspace) hergebruikt binnen diezelfde omgeving een bestaand
reviewresultaat voor dezelfde voorstel-ID. Zonder workspace ontstaat bewust een
NIEUW onafhankelijk testscenario, niet een tweede transactie in dezelfde database.
Gebruik dezelfde workspace voor concurrerende voorstellen voor hetzelfde schema.

act(state, event, freshRequest, currentContext, authority) accepteert:
view, accept, reject en een APARTE expliciete trainer-only apply.
Event-ID, reviewrevisie, voorstel-ID/-versie, basisplanref, eigen lid en actorrol/
-ID/relatierevisie moeten exact kloppen. De bestaande strikte toegangsvalidator
wordt hergebruikt; truthy velden of extra pseudo-adminvelden geven geen gezag.

| Overgang | Uitkomst |
| --- | --- |
| Bekijken | Geen plan-/statuswijziging |
| Alleen lid of alleen trainer accepteert | pending; andere goedkeuring ontbreekt |
| Beide accepteren exact dezelfde versie | approved; huidig plan nog niet gewijzigd |
| Lid probeert apply | geweigerd, ook na eigen akkoord |
| Bevoegde trainer voert daarna expliciet apply uit | hoogstens eenmaal nieuwe gesimuleerde planversie met uitsluitend de exacte changes |
| Lid of trainer wijst af | rejected; huidig plan behouden; geen latere stille acceptatie |
| Bron/doel/plan/regel/historie/context gewijzigd of veiligheidsvoorwaarde niet vervuld | needs_recheck; oude goedkeuringen niet overnemen |
| Zelfde event-ID met zelfde payload opnieuw | idempotente bevestiging; geen tweede toepassing |
| Zelfde event-ID met andere payload | conflict |
| Andere event-ID maar reeds geaccepteerd/toegepast | geen tweede acceptatie/toepassing |
| Parallel voorstel voor reeds gewijzigde actieve versie in dezelfde workspace | active_plan_changed; nieuwe beoordeling nodig |

Iedere nieuwe goedkeuring/toepassing roept propose opnieuw aan met actuele context
en verklaarde bronnen. Inhoudsfingerprint omvat exacte broninhoud, bindings en
volgende bronweek; alleen taal en herleestijden zijn niet de inhoudsidentiteit.
Een planrevision-CAS in de gedeelde simulatie voorkomt twee toepassingen op dezelfde
actieve versie. Het resultaat is nadrukkelijk offline_simulated_not_authoritative:
geen live plan/readset, authority of medische vrijgave; historische sources blijven intact.

Bij een extern gewijzigde bronversie is een nieuw coherent bronpakket nodig,
een opnieuw berekend voorstel en lege nieuwe goedkeuringen. De voorbeelden tonen
deze expliciete herbeoordeling in een nieuw scenario. Geen oude autorisatie of
trainergrens wordt voor een nieuwe echte planversie automatisch aangemaakt.
Dit is geen duurzame workflowservice of bewijs van echte databaseconcurrency,
restart-idempotency, intrekkingsnotificaties of live sessieauthenticiteit.

## Veiligheid, O5 En Toekomstige Live Voorwaarden

Alle output: automatic_actions_allowed=false, physical_advice_authorized=false,
medical_clearance=false, storage_enabled=false, nul provider/member/database/Edge-acties.
Het berekende concept is alleen offline productreview met synthetische testregels.
Een goedgekeurd concept in de simulator is geen trainingsopdracht, garantie of live GO.

Actuele/ernstige/terugkerende/oningedeelde klachten blokkeren deze progressie.
Zelfrapportage heft dat niet op; ontbrekend herkend signaal is geen geschiktheidsbewijs.
Misverstanden/technische fouten houden hun eigen optionele verduidelijkingsroute.
Nieuwe signalen worden opnieuw beoordeeld; andere meldingen blijven behouden.
O5 blijft read-only uiterlijk 30 dagen vanaf eerste registratie, eerder indien onnodig;
retry/status/read verlengt niet. Verval/verwijderen/contextverlies geeft geen vrijgave.
Chat/historie/feiten/eerder toegestane niet-fysieke reflectie houden hun eigen regels.
Geen trainerdeling van private chat of menselijke medische aanvraagdienst.

De simulator bewaart geen nieuwe kopie van gezondheidsinhoud of O5-statussen in
voorstel/review. Zijn bron-/reviewobjecten zijn in-memory testmateriaal, geen
goedgekeurde live bewaarpayload. Doelgebonden retentie van toekomstige voorstellen,
besluiten en auditbewijs vereist nog een afzonderlijk privacy-/juridisch contract.

Zonder geldige trainerbron ontbreekt een APART FitMetZorge-coachingsbeleid.
Dat moet later minstens vastleggen: bevoegde auteur en versie/geldigheid/intrekking,
toepasselijke doelen/oefeningen/set- en belastingsgrenzen, bron-/vergelijkingsregels,
evaluatiemomenten, gewichtsstappen, individuele inspanningsvoorwaarden,
eigenaar/goedkeuring van schemawijzigingen en deskundig beoordeelde inhoud/herstelgrenzen.
Geen parameter uit deze testfixtures wordt ongemerkt een algemeen FMZ-beleid.

Open: echte trainings-/progressieregels en expertcriteria voor inhoud/hervatting,
privacy/juridische noodzaak/consent/retentie/verantwoordelijkheid, NL/EN/DE-tekst-
en interpretatiereview en betrouwbare live source/auth/lifecycle/concurrency.
De bestaande bekende taalbeperking blijft zichtbaar; geen classifieruitbreiding.
Voeding en herstelcoaching blijven ambitie, niet gerealiseerde 6E-5-functionaliteit.
