# Package 6E Risk, Safety And Escalation Readiness

Datum: 2026-09-07.
Auditstatus: COMPLETE. Implementatie: NOT STARTED.
Ownerbeslissingen en medische/privacy/juridische goedkeuring: OPEN.
Uitsluitend staging Yourizorge/fitmetzorge-staging / main / mokxyyullfhkfalopbzd.

## 1. Uitkomst En Freeze

Actuele gecorrigeerde baseline: Package 6D COMPLETE / OWNER-ACCEPTED / FROZEN,
inclusief expliciet op een echte telefoon geaccepteerde Automatisch/Licht/Donker,
systeemvolging en blijvende voorkeur; eerdere geaccepteerde flows zijn herbevestigd.
Runtime: bc6308fbf0f914b04c7faa711219d9ae46e9cbe3.
Geaccepteerde theme-documentatie: 3453ea2e14a1737922b53e106c04c3aea747f65b.
31 canonical migrations, Youri AI v43, theme cache 20260907-theme1; 44 live assets
Git-identiek. Zie PHASE6D_FREEZE_RECEIPT.md voor de gecorrigeerde documentatiecommit
en publicatiestatus. De eerdere baseline hieronder is superseded/historisch.
Edge-bronnen zijn tussen 7fec9da en bc6308f ongewijzigd; de oorspronkelijke
6E-probes/evidence blijven historisch bewijs, geen nieuwe klinische validatie.
Package 6E blijft alleen documentair: audit COMPLETE, implementatie NOT STARTED.

Historisch was Package 6D COMPLETE / OWNER-ACCEPTED / FROZEN op basis van expliciete
owneracceptatie van de volledige flow op een echte telefoon. Dat bewijs blijft behouden.
Frozen runtime: `7fec9da7cb00cb7dff4a601810ddd2c977db0f5f`.
Frozen documentatiecommit: `d53fea94f50c23c059104045f899fde4da25c2ec`.
Geaccepteerde documentatie voor freeze: `c1a71dea1bd651a12c738a94ce8ac2e56bcc26b9`.
Zie [6D freeze receipt](PHASE6D_FREEZE_RECEIPT.md) en
[freeze evidence](PHASE6D_FREEZE_EVIDENCE.json).

6E is architectonisch voorbereid, maar NIET vrijgegeven voor echte nieuwe
safetyverwerking, diagnose, triage, trainerdeling of automatische uitvoering.
De huidige kleine deterministische classifier is geen breed gevalideerde
gezondheidsdetector. De onderstaande voorstellen veranderen geen frozen contract.

Er zijn aantoonbare gemiste signalen, onjuiste contextuitsluitingen en een ontbrekend
begrensd bewaarbeleid voor safety/recovery-events. Het veiligste vervolg is een
offline contract/testslice na expliciete ownerkeuzes, gevolgd door klinische review
en een afzonderlijke opdracht voor minimaal noodzakelijke compatibele correcties.
Geen nieuwe medische productclaim of runtimebeleid wordt met deze audit goedgekeurd.

## 2. Methode En Bewijs

- Git-root, schone main, HEAD/origin/main en werkelijke remote gecontroleerd.
- AGENTS.md en .codex/config.toml gelezen; auto_review, workspace-write,
  projectnetwerk en staging-autonomie geconfigureerd; managed beperkingen behouden.
- 30 lokale migrations exact gelijk aan 30 live versies/namen; niets uitgevoerd.
- Edge youri-ai v43 ACTIVE/JWT, tien bronbestanden gelijk na newline-normalisatie.
- 42 live assets byte-identiek aan runtimecommit; cache 20260907-dashboard-placement1.
- Huidige SELECT-only trust 47/47, inbox/recent 18/18, worker 23/23 PASS.
- Alle twintig frozen regressiesuites opnieuw PASS; bestaande volledige
  browserbaselines 426/180/323/88 behouden en in het freeze receipt onderscheiden.
- Aanvullend acht live catalogus/ACL/gatepredicaten PASS. Geen member-RPC aangeroepen.
- 36 synthetische classifier/recoveryprobes uitgevoerd op de bestaande module.
  Geen provider, echte tekst, lidlogin, databasefixture of functionele 6E-code.
- Officiele hulp-, medische en privacybronnen op 2026-09-07 geraadpleegd.
  Broninformatie is een reviewinput, geen goedgekeurde runtimecopy.

[Machineleesbaar auditbewijs](PHASE6E_SAFETY_RISK_READINESS_EVIDENCE.json) bevat alle
36 zinnen/uitkomsten en de uitgevoerde READ ONLY catalogusquery.
Twaalf controlevoorbeelden behouden hun bestaande verwachte gedrag; 24 aanvullende
gevallen tonen uitbreidings-/contextproblemen. Dit is geen sensitiviteit,
specificiteit, klinische validatie of statistisch representatieve score.
Een waarde expected=review betekent klinische beleidsreview nodig, geen bestaande enum.
Het localeveld labelt alleen de synthetische taal: de probe roept pure functies aan,
niet de HTTP-parser. it/fr requests zijn niet toegestaan; zulke tekst kan wel in een
toegestane nl/en/de payload voorkomen. Recovery-intent is nooit een uitgevoerde recovery.

Reproductie vanuit de werkrepo met de bestaande Node-runtime (geen nieuwe testfile,
netwerk of database; controleert geregistreerd gedrag, niet medische juistheid):

```powershell
@'
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { classifyPhase6cSafety, phase6dRecoveryIntent } from './supabase/functions/youri-ai/phase6c-handler.ts';
const evidence = JSON.parse(readFileSync('docs/PHASE6E_SAFETY_RISK_READINESS_EVIDENCE.json', 'utf8'));
assert.equal(evidence.probe.cases.length, 36);
for (const c of evidence.probe.cases) {
  assert.equal(classifyPhase6cSafety(c.text), c.actual, c.id);
  assert.equal(phase6dRecoveryIntent(c.text), c.recovery_intent, c.id);
}
console.log('36/36 recorded observations reproduced; NOT clinical validation.');
'@ | & 'C:\Users\Fitme\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --input-type=module
```

Bronbeperkingen: juridische EUR-Lex artikel-9-tekst is via de officiele zoekindex
geverifieerd; directe HTML/PDF-opvraging kreeg een anti-botpagina, geen volledig
nieuw documentonderzoek. Legal moet de toepasselijke tekst en uitzonderingen zelf
valideren. De overige gelinkte hulp-/guidancepagina's zijn inhoudelijk geopend.
Italies operatoruren vereisen de extra actuele bevestiging beschreven in sectie 13.

Er is geen nieuwe live transactionele E2E, databaseopbouw of globale schema-diff
geclaimd. De cronworker bleef normaal actief; deze audit startte of wijzigde hem niet.

## 3. Bestaande Architectuur

| Onderdeel | Aangetroffen contract en concrete bron | Beoordeling voor 6E |
| --- | --- | --- |
| 6A trust | 20260901183914_phase6a_ai_trust_foundation.sql:900 trust_status; eigen identiteit, entitlement, consent, budget, flags en safety | Hergebruik autorisatie, niet de oude chatblokkade |
| Action allowlist | Dezelfde migration:780; contracts.ts:125 | Vijf begrensde, verklaarbare, omkeerbare proposaltypen; geen executor |
| Medische acties | contracts.ts:16, 125, 146; SQL validators | Diagnose, medicatie en behandeling niet allowlisted; 6C/6D actions blijven leeg |
| 6C input/classifier | phase6c-handler.ts:78-148 | NFKD, accenten/ss, interpunctie/whitespace; regexconcepten NL/EN/DE; clear/hard_stop |
| Contextuitsluiting | phase6c-handler.ts:113-141 | Beperkte voorafgaande ontkenning; hele bericht kan educationalOnly worden |
| Communicatie | 20260906080455_phase6d_owner_safety_settings.sql:443 | private_chat-consent, leeftijd, entitlement en mockgate; oud safety-event blokkeert chat niet |
| Safetygeheugen | 6A migration:393, 1659; public.ai_member_safety_state | Private categorische events plus current state/revision; geen raw tekstkolom |
| Recovery | 20260906080455 migration:20-94; phase6c-handler.ts:151 | Intent biedt formulier; expliciete bevestigingen + auth.uid + exacte revisie + lock |
| Analyseblokkade | 20260906080455 migration:202; 20260906092905:423, 511 | Voorbereiding/completion/worker gebruiken actuele gate; worker/completion dezelfde safetylock |
| Herhaald signaal | 6A migration:1707; 6D recovery join op revisie | Nieuwe eventrevisie blokkeert opnieuw; geen longitudinal prediction/episodesysteem |
| Trainer | 6A migration:988 can_share_trainer_summary | Consenthelper alleen, geen relatie-/summarydelivery-/klinische bevoegdheid |
| Retentie | 6C sweeps; 6D 90/180 dagen; recoverytabel zonder expiry | Chat/analyses begrensd, safety/recovery TTL niet aangetoond |
| Providers | 6B provider_configurations; phase6b-handler/openai-adapter | Alleen afzonderlijke synthetische testroute; echte memberroute gesloten |
| Presentatie | phase6d-owner-settings.js:371, 386, 548; inboxmodule | Frozen formulieren, avatar, instellingendialogen en kaartvolgorde niet wijzigen |

Bronpaden hierboven zijn relatief aan supabase/migrations, supabase/functions/youri-ai
of assets. Regelverwijzingen gelden voor frozen runtime 7fec9da.
De huidige 6D worker produceert vaste mockanalyses, geen nieuwe medische classifier.
Ontbrekende of onbetrouwbare data geeft insufficient_data, geen verzonnen conclusie.

De classifier wordt in 6C binnen de mockreplyfase uitgevoerd, na JWT, member-submit
en mock-reservering. Dat is geen bewijs dat een toekomstige externe providerroute
al een onafhankelijke pre-call safetyfilter heeft. Een nieuwe route moet deze
beveiligingsvolgorde apart afdwingen.

## 4. Herbruikbare Frozen Regels

1. Een herkend actueel ernstig signaal onderdrukt normale coaching en acties.
2. Safetygeschiedenis blokkeert automatische acties, niet gewone volgende privechat.
3. Toegestane chat blijft onder eigen consent-, leeftijd- en entitlementgates vallen.
4. 6D-recovery herstelt uitsluitend de analysepoort voor de bevestigde revisie.
   Het historische event en automatic_execution_blocked blijven behouden.
5. Een nieuw serieus signaal maakt de eerdere recovery verouderd en blokkeert opnieuw.
6. Een normale vervolgvraag is geen recoverybewijs; een intent is geen statewijziging.
7. Geen diagnose, medicatiewijziging, behandeladvies of impliciete medische geschiktheid.
8. Geen trainerinzage in privechat; geen analyses als verborgen chat-samenvatting.
9. Resultaathistorie/export/deletion blijft eigen-lid; waarschuwingen zijn geen
   reden om deze rechten of de niet-AI-app stilzwijgend weg te nemen.
10. Strikte output en servergates blijven leidend, ook bij timeout, retries en injectie.

Live metadata bevestigt deze scheiding met acht gerichte predicates. Historische
gedragstests in 20260903145000_phase6c_request_scoped_safety_e2e.sql,
20260906080455_phase6d_owner_hotfix.sql en 20260906092905_phase6d_automatic_inbox.sql
bevatten normale follow-up, recovery, nieuwe riskrevisie, stale confirmation,
delete-bypass, trainerisolatie en queued-workoutblokkade. Ze zijn niet opnieuw live
uitgevoerd binnen deze read-only audit.

## 5. Bewezen Hiaten

| ID | Bewijs | Gevolg en noodzakelijke begrenzing |
| --- | --- | --- |
| G-A | G01-G15: neurologische uitval, keelzwelling, indirecte crisis, restrictie/braken, ernstig letsel, hitte/koude geven clear | Geen brede safetydekking claimen; categoriebeleid en klinisch gelabelde tests nodig |
| G-B | G16: 'Ik heb geen koorts maar borstpijn.' geeft clear | Ontkenningsvenster slokt positief signaal na 'maar' op; clause-aware correctie vereist |
| G-C | G17: educatieve openingsvraag plus instortende partner geeft clear | Globale education-exit kan actueel derde-persoonssignaal onderdrukken |
| G-D | G18: 'borst pijn' en 'duiselig' geven clear | Woordsplitsing/spelfouten niet robuust; geen onbegrensde fuzzy matching toevoegen |
| G-E | G19/G20: hypothetische of oude duizeligheid geeft hard_stop | Tijd/ervaarder/actualiteit onvoldoende; false-positive correctie moet bereikbaar blijven |
| G-F | G21/G22: Italiaans/Frans niet herkend; requestlocale zelf alleen nl/en/de | Marktaanbod is geen taalondersteuning; IT/FR launchgate open |
| G-G | R06: 'I feel fine again. My face is drooping.' geeft clear en recovery-intent | Formulier wist niet automatisch, maar intent leunt op beperkte classifier; niet als medische recovery beoordelen |
| G-H | Recovery-RPC accepteert drie booleans, reden en revisie zonder categorie/clearanceprotocol | Goedgekeurde mockanalyseherstel is geen vrijgave voor automatische training/voeding |
| G-I | safety_events en analysis_safety_recoveries hebben geen expirykolom; inspected sweeps wissen ze niet | 6D 180-dagenmetadatabeleid dekt deze tabellen niet vanzelf |
| G-J | Alleen twee classifieruitkomsten en brede serious_health-categorie | Geen vijf niveaus, onzekerheidsstatus, hulpregister of herhaalde-episodereview |
| G-K | Geen trainerdelivery, bevoegdheid of acknowledgementpad; consenthelper alleen | Geen trainerwaarschuwing beloven; aparte autorisatie/privacyreview nodig |
| G-L | Auth/entitlement/ratechecks kunnen voorafgaan aan mockclassificatie | Geen bewezen crisisroute buiten betaalde/ingelogde chat; voorstel statische hulp is productbeslissing |
| G-M | Provider-/privacygates live incomplete/unverified; outputcontractcontrole geen medische validatie | Real-member providergebruik blijft technisch en organisatorisch verboden |

Dit zijn geen wijzigingen aan de frozen baseline. G-B/G-C zijn ook concrete
veiligheidsgrenzen van bestaand gedrag, niet slechts toekomstige wensen.
Owneracceptatie van 6D blijft geldig voor de afgesproken mockflow, maar legitimeert
geen bredere medische claim. Een gerichte compatibele correctie vereist een nieuwe
opdracht; geen stilzwijgende hotfix in deze audit.
Een enkele denylist of LLM-classifier kan false negatives niet uitsluiten.

## 6. Voorgestelde Risicotaxonomie

Aanbevolen: vijf **hulp-/actiebeperkingsniveaus**, geen diagnose of kans op ziekte.
Intern R0-R4, aangevuld met evaluation_state=known/uncertain/unavailable en een
afzonderlijke action_gate. R0 betekent alleen 'geen relevant signaal in deze input
herkend', nooit 'medisch veilig'. Geen percentage, medisch groen vinkje of fitnesscertificaat.

| Niveau | Betekenis | Voorgestelde route |
| --- | --- | --- |
| R0 | Geen relevant signaal herkend | Gewone niet-medische coaching onder overige gates |
| R1 | Voorzichtigheid/monitoren | Conservatieve stop-/rustcontext, geen verhoging van belasting of restrictie |
| R2 | Stoppen en beperkt uitvragen | Relevante coaching/analyses pauzeren; kort verduidelijken zonder diagnose |
| R3 | Professionele beoordeling adviseren | Stop relevante activiteit; passende professionele hulp, geen AI-clearance |
| R4 | Mogelijke spoed/acute hulp | Direct hulpadvies; geen wachten op vragen, provider, trainer of recoveryformulier |

Onzeker is niet R0. Bij een mogelijke acute rode vlag direct de spoedroute; bij
onbegrepen niet-acute gezondheidscontext R2 plus passende professionele route.
Unsupported taal of classifierstoring geeft geen onterechte geruststelling.

Voor zelfbeschadiging/suicidaliteit mogen deze codes alleen de reactie beperken,
niet toekomstig zelfmoordrisico voorspellen of toegang tot zorg bepalen. NICE raadt
dergelijke risicoscores/laag-middel-hoogvoorspellingen af. Dit ontwerp is dus geen
klinisch risico-instrument. [NICE NG225, 1.6](https://www.nice.org.uk/guidance/ng225/chapter/Recommendations#risk-assessment-tools-and-scales)

Voorrang: actueel acuut signaal > recoveryverklaring > historische context.
Een gekopieerde quote of education-label mag een zelfstandig actueel signaal niet
uitschakelen. Meerdere signalen worden afzonderlijk beoordeeld, niet gemiddeld.
Een zelfverklaarde professional, trainer of prompt kan deze volgorde niet overrulen.

## 7. Actiegevolgen Per Niveau

Onderstaande matrix is een VOORSTEL voor toekomstige functionaliteit, geen runtime.
'Beperkt' betekent uitsluitend gereviewde niet-medische uitleg, geen nieuw trainings-
of voedingsplan. Voor alle niveaus blijven voorstellen/uitvoering nu afwezig.

| Niveau | Chat | Nieuwe analyses | Training | Voeding | Herstel | Toekomstige proposals | Toekomstige uitvoering | Trainer-signaal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0 | Normaal, overige gates | Toegestaan onder consent/kwaliteit | Bestaande grenzen | Bestaande grenzen | Bestaande grenzen | Alleen allowlist + review | Alleen later aparte GO en actuele gates | Geen safetybericht |
| R1 | Ondersteunend, voorzichtig | Alleen niet-aanjagend; onzekerheid zichtbaar | Geen verhoging/intensivering | Geen extra calorierestrictie | Rust niet als behandeling formuleren | Alleen expliciet niet-escalerend na review | Aanbevolen uit in eerste 6E | Geen standaardmelding |
| R2 | Korte verduidelijking en veilige gewone follow-up | Relevante soorten gepauzeerd; eerste slice alle drie | Pauze suggesties | Pauze persoonlijke wijzigingen | Geen gepersonaliseerd herstelplan | Geen nieuwe, relevante pending ongeldig | Blokkeer | Alleen gekozen niet-acute workflow, later |
| R3 | Hulpgerichte communicatie; geen permanente chatban | Geen nieuwe relevante analyses | Geen hervattingsadvies | Geen target-/supplementaanpassing | Geen medisch hersteladvies | Blokkeer | Blokkeer tot professioneel gereviewd pad | Minimaal, apart consent, geen acute zorgclaim |
| R4 | Korte spoedboodschap; normale coaching onderdrukt | Pauze alle nieuwe analyses | Stopadvies, geen schema | Geen dieet-/drink-/medicatieprotocol | Geen afwachten-/herstartadvies | Blokkeer en invalideer pending | Blokkeer onmiddellijk | Niet op trainer wachten; geen automatische verzending |

Bestaande analysehistorie blijft leesbaar, met versie/tijd en zonder medische
hervattingsclaim; geen inhoudelijke mutatie of stilzwijgende verwijdering.
Gewone chat op een volgende veilige input blijft mogelijk, ook wanneer actieblokkades
voortduren. Review/hulpbericht mag niet telkens de gehele chat onbruikbaar maken.
Een trainer-veto blijft in de toekomst een extra deny-gate; AI mag het niet opheffen.
Een trainer 'go' of R0 wist nooit een klinische of consentblokkade.

Aanbevolen eerste 6E-beleid: bij R2-R4 alle drie nieuwe analysevormen pauzeren.
Selectief alleen een domein stoppen is pas verantwoord met aantoonbare data-afhankelijkheden.
Bij een storing fail-closed voor nieuwe verwerking/acties, met bereikbare statische hulp.

## 8. Gezondheidscategorieen

Dit is een **reviewtaxonomie**, geen diagnostische beslisboom of volledig uitvraagprotocol.
Niveaus bij voorbeelden zijn voorstelroutes, te valideren door bevoegde reviewers.
Geen afwezigheidsbewijs uit een gemiste match; geen wearables, foto's of labwaarden
als bewijs dat het veilig is. Alle auditvoorbeelden zijn synthetisch.

| Categorie | Verantwoord begrensd herkennen/zeggen | Niet doen; escalatie |
| --- | --- | --- |
| Borstpijn/benauwdheid/flauwvallen/ernstige duizeligheid | Actuele expliciete klachten herkennen, activiteit stoppen en hulp adviseren | Geen spierpijn/angstdiagnose. Mogelijke acute combinatie direct R4; geen wachttimer. [Thuisarts](https://www.thuisarts.nl/pijn-op-je-borst/pijn-op-borst-wat-kan-het-zijn) |
| Acute neurologische signalen | Plots scheve mond, armzwakte of spraak-/zichtproblemen als hulpbehoefte behandelen | Geen FAST-test als verplichte poort, geen afwachten als klachten verdwijnen; voorstel R4. [NHS](https://www.nhs.uk/conditions/stroke/symptoms/) |
| Ernstige allergische reactie | Plots keel-/tongzwelling, slik-/ademproblemen herkennen | Niet wachten op huiduitslag; geen nieuw medicatie/doseringsadvies; R4-route. [NHS](https://www.nhs.uk/conditions/anaphylaxis/) |
| Mogelijk ernstig letsel | Trauma met vervorming, gevoelsverlies of ernstig functieverlies vraagt professionele hulp | Geen breuk/peesdiagnose, repositiemanoeuvre of 'train erdoorheen'; urgente beoordeling, R4 bij acute rode vlag. [NHS](https://www.nhs.uk/conditions/sprains-and-strains/) |
| Overbelasting/onveilig herstel | Aanhoudende vermoeidheid, pijn en doortrainen als onzeker belastingssignaal benoemen | Geen diagnose overtrainingssyndroom of readinesspercentage; R1/R2, bij ernstige bijkomende klachten hoger |
| Extreme hitte/koude/dehydratie | Blootstelling plus verwardheid, bewustzijns-/ademproblemen als acuut signaal | Geen berekende vocht-/zoutdosis, temperatuur alleen niet beslissend; R4 bij acute tekenen. [Hitte](https://www.nhs.uk/conditions/heat-exhaustion-heatstroke/), [koude](https://www.nhs.uk/conditions/hypothermia/) |
| Eetstoornissignalen/extreme restrictie | Expliciet compenseren, braken, extreme restrictie of dwangmatig sporten vraagt steun/professionele beoordeling | Geen BMI-diagnose, drempelcalorieen, gewichtslof of restrictietips; R2/R3, acute tekenen R4. [NICE NG69](https://www.nice.org.uk/guidance/ng69/chapter/Recommendations) |
| Zwangerschap, later | Alleen vrijwillig gemelde context, aangepast productbereik bespreken | Zwangerschap op zichzelf geen noodsituatie; geen inferentie of trainingsgeschiktheid. Persoonlijke adviezen buiten scope tot aparte review. [NHS](https://www.nhs.uk/pregnancy/keeping-well/exercise/) |
| Medicatie/aandoeningen | Alleen expliciete context gebruiken om niet te personaliseren en zorgprofessional/apotheker te adviseren | Geen dosering, stoppen/starten of interactiecheck door AI; stabiele aandoening niet automatisch spoed, actuele alarmsignalen wel |
| Zelfbeschadiging/suicidaliteit/mentale crisis | Warm/direct reageren, huidige veiligheid centraal; geen methode-details uitvragen | Geen risicokans of diagnose. Bij onmiddellijk gevaar/nood direct acute hulp; anders passende crisissteun, geen fitnesscoaching. [NICE NG225](https://www.nice.org.uk/guidance/ng225/chapter/Recommendations) |
| Minderjarigheid | Bekende <18 of tegenstrijdige leeftijd blokkeert AI-producttoegang | Niet profileren/verzamelen om minderjarigen alsnog toe te laten; hulpinformatie niet achter betaalmuur voorstellen |

NHS-bronnen zijn medische input, geen lokalisatiebron voor NL/BE/DE/AT/IT:
hun Britse 999/111-nummers worden NIET overgenomen. Klinische review bepaalt exact
welke signalen rechtstreeks acute hulp vragen. Geen ongereviewde uitgebreide
zelfbehandeling, reanimatie- of medicatie-instructies toevoegen aan FitMetZorge.
Sport/recovery-score alleen kan nooit een ernstig vrijetekstsignaal neutraliseren.

## 9. Beperkte Uitvraag En Recovery

Voorstel beperkte niet-acute uitvraag: maximaal twee korte stappen, een vraag tegelijk.
Voorbeelden voor review: 'Gaat dit over klachten die je nu hebt of over algemene
informatie?' en 'Gaat het over jou of iemand bij je?' Bij onduidelijkheid kan de app
vragen of er op dit moment direct gevaar is, zonder methoden of details te vragen.
Antwoord niet verplicht om hulp te tonen. Geen 'doe eerst een inspanningstest',
symptoomscore of geruststelling op basis van een ontkenning alleen.

Bij een acute rode vlag GEEN vervolgvragen die hulp vertragen: toon direct hulp,
geef aan niet op AI/trainer te wachten en laat contact starten door de gebruiker.
Een vraag naar land mag de acute boodschap niet blokkeren.
Crisiscommunicatie moet steunend zijn en verbinden met echte hulp, nooit met de
belofte dat FitMetZorge iemand bewaakt of automatisch hulpdiensten heeft gewaarschuwd.

| Situatie | Aanbevolen recoverybeleid, nog niet geimplementeerd |
| --- | --- |
| Alleen gewoon gesprek hervatten | Geen medische clearance nodig; actuele input beoordelen, overige chatgates behouden |
| R1 zonder acute historie | Expliciete eigen verklaring kan beperkte analysehervatting ondersteunen na gereviewde vragen |
| False positive | Specifiek event als betwist markeren; nieuw actueel signaal apart behouden; geen hele geschiedenis wissen |
| R2 onzeker | Revisiegebonden bevestiging plus adequate verduidelijking; bij resterende twijfel professional |
| R3/R4 of herhaalde ernstige episodes | Geen self-declared toestemming voor automatische acties; eerst professioneel gereviewd proces |
| Tegenstrijdige hersteltekst | Hoogste relevante actuele stop gaat voor; geen recovery-intent op onbegrepen gezondheidsinhoud |
| Nieuwe risk tijdens recovery | Gemeenschappelijke lock/revisie; oude bevestiging stale, geen release |
| Tijd verstreken of thread verwijderd | Geen medische recovery; expiry/deletion mag acties niet vanzelf vrijgeven |

De bestaande 6D bevestigingsflow blijft ongewijzigd, ook waar dit voorstel strenger
is voor toekomstige automatisering. 'Klachten voorbij' en 'medisch geschikt voor
automatische training' zijn verschillende zaken.
Professionele clearance is een nog niet bestaand product-/autorisatieproces:
geen AI-beoordeling van geuploade doktersbrief en geen gewone trainer als arts.
Aanbevolen eerste slices: alle automatische uitvoering blijft uit, zodat er geen
ongedefinieerd clearancepad hoeft te worden nagebootst.

## 10. Herhaalde Signalen En Misbruik

Herbruikbaar: nieuwe safetyrevisie maakt oude recovery ongeldig. Aanvullend voorstel:
beperkt episodevenster met eigen eventidentiteit, tijd en categorie, geen levenslang
risicoprofiel of analyse van de volledige privechat.
Twee afzonderlijke relevante ernstige episodes binnen een voorgesteld 30-dagenvenster
kunnen een professionele reviewroute vasthouden; dit getal is een te beoordelen
productinstelling, geen medische grens of voorspeller. Duplicaten/retries tellen niet.
Een enkel acuut event heeft die teller niet nodig en blokkeert direct.

Prompt injection, roleplay, 'mijn trainer/arts zegt doorgaan', hersteltekst en
'negeer safety' mogen inputprioriteit niet wijzigen. Normaliseer Unicode en
clausegrenzen, maar behoud negatie/actualiteit/ervaarder. Test quotes, URL-tekst,
codeblocks, gemengde talen, homoglyphs, zero-width tekens en zeer lange berichten.
Geen modelgegenereerde SQL, URLs, tools of policywijzigingen uitvoeren.

Misbruik apart van medisch signaal loggen. Herhaalde noodberichten zijn NIET
automatisch misbruik. Bounded request/rate-limits voorkomen resourceuitputting;
statische hulp en gewone niet-AI-toegang blijven bereikbaar.
Een bypasspoging kan automatische verwerking stoppen, nooit als straf alle hulp afsluiten.
Geen onbeperkte retry of automatische betaalde modelescalatie.

## 11. Privacy En Retentie

Veiligheidsmetadata blijft potentieel gezondheidsinformatie, ook zonder raw chat.
Er is een expliciete grondslag-/doeltoets nodig, niet alleen een technische checkbox.
De DPIA moet de nieuwe classificatie, blokkade, correctie en eventuele ontvangers
meenemen; de EDPB behandelt onder meer systematische evaluatie en gevoelige verwerking
als relevante DPIA-factoren. [EDPB](https://www.edpb.europa.eu/sme/be-compliant/be-compliant_en)

Voorgesteld minimaal event: opaque event-ID, interne ownerbinding, categoriecode,
hulpniveau, request/episode-ID, policyversie, occurred_at, bronsoort en revisie.
Recovery: event/revisie, beperkte reden, bevestigings-/reviewsoort en timestamp.
Geen diagnoseveld, kansscore, medicatielijst, quote, locatiegeschiedenis, trainer-notities
of gedragsprofiel. Interne IDs zijn geen anonimisering en verlaten de backend niet.
Raw chat blijft alleen onder het bestaande private_chat-retentiecontract; geen tweede
raw kopie in safety-, recovery-, telemetry- of errorlogs. Geen raw hash als anonieme
oplossing presenteren: korte voorspelbare klachten kunnen via hashes herleidbaar zijn.

| Dataklasse | Nu | Aanbevolen optie voor review |
| --- | --- | --- |
| Bestaande raw chat | Frozen actief + maximaal 90 dagen grace na entitlementverlies | Niet via 6E verlengen of opnieuw kopieren |
| Bestaande analyses | Content 90, metadata 180 dagen | Behouden, los van safetyrecords |
| Requesttekst bij classifier | Tijdelijk verwerkt, bestaande chat kan opgeslagen zijn | Alleen in memory buiten toegestane chatopslag; geen operational raw logging |
| Episodecounter | Niet aanwezig | Rollend 30 dagen, daarna weg; geen lifetime teller |
| Afgesloten/betwiste safety/recoverydetails | Geen TTL bewezen | Maximaal 90 dagen na sluiting, daarna verwijderen |
| Minimaal niet-inhoudelijk beslisaudit | Geen afzonderlijk 6E-schema | Hoogstens 180 dagen indien noodzakelijk en gemotiveerd; korter waar mogelijk |
| Onopgeloste blokkade | Bestaande state/revisie blijft | Expiry nooit auto-clear; uiterlijk 90 dagen review of hulpniveau verwijderen en capability niet vrijgeven zonder nieuwe review |
| Land voor hulp | Geen betrouwbare fysieke landbron | Expliciete sessiekeuze; geen GPS/IP-historie, niet uit timezone afleiden |

De genoemde termijnen zijn aanbevelingen voor owner/DPO-review, geen automatisch
gekozen wettelijk bewaartermijn. 'Capability niet vrijgegeven' kan zelf informatie
onthullen en valt ook onder de bewaartoets. Een onopgelost-retentiebeleid zonder
revieweigenaar en maximale termijn is GEEN launch-ready ontwerp.
Alternatief is korter bewaren en automatisering geheel buiten scope laten.
Geen auditgrondslag mag onbegrensde medische historie legitimeren.

Expiry, accountdelete, export en consentwithdrawal moeten in eigen-lid RPCs worden
getest. Correctie van een false positive wist geen ander nieuw event.
Auditimmutability betekent niet 'nooit verwijderen'. Backupretentie, herstelscenario's,
legal holds en cascadegedrag horen bij DPO/securityreview; geen nieuwe bewaarplicht
of medische dossierplicht veronderstellen.

## 12. Trainergrenzen

Aanbevolen eerste 6E: trainerdeling UIT. Bestaande trainer_summary_sharing is geen
automatische toestemming om ernstige gezondheids-/crisissignalen door te sturen.
De bestaande helper toetst alleen consent; hij bewijst geen actuele relatie of
bevoegdheid van een concrete ontvanger.

Een later voorstel vraagt afzonderlijk, specifiek, intrekbaar consent voor
safety-signaaldeling, liefst met preview en expliciete bevestiging per verzending.
Mogelijke minimuminhoud: 'automatische suggesties tijdelijk gepauzeerd; professionele
beoordeling geadviseerd', tijd en geldig bereik. Zelfs deze tekst is gevoelig.
Geen categorie mentale crisis, diagnoses, raw chat, quotes, transcript, locatie,
attachments of geschiedenis standaard delen.

Vereiste toekomstige checks: actuele servergevalideerde relatie, juiste trainer,
einde/revocation onmiddellijk verwerkt, beperkte bewaartermijn, own-member-preview,
read audit en minimale notificatie zonder medische tekst op lockscreen.
Trainer kan een extra actieveto plaatsen; geen chat lezen, zelf een medisch verdict
geven, AI-veiligheidsstop overrulen of een lid stilzwijgend geschikt verklaren.
Geen belofte van trainerbereikbaarheid of monitoring buiten echte organisatorische dekking.

Bij acute nood prevaleert direct hulpadvies boven wachten op toestemming voor
trainercontact. Dit geeft NIET automatisch recht om privegegevens te delen.
AVG artikel 9(2)(c) bevat een beperkte uitzondering voor noodzakelijke bescherming
van vitale belangen wanneer iemand lichamelijk/juridisch geen toestemming kan geven;
het is geen generieke crisis-override voor een fitnessapp of alternatief voor consent.
Een eventuele nooddisclosure vereist afzonderlijke juridische procedure, noodzaak,
proportionaliteit, juiste ontvanger en menselijke beoordeling. [AVG artikel 9](https://eur-lex.europa.eu/eli/reg/2016/679/ojv)

Geen koppeling met hulpdiensten wordt ontworpen alsof die al bestaat; trainers
zijn geen vervanging van professionele crisiszorg.

## 13. Internationale Lokalisatie

Alle hieronder genoemde routes zijn op 2026-09-07 tegen officiele overheid- of
dienstverlenersbronnen onderzocht. Geen nummer of tekst is aan runtime toegevoegd.
De Europese Commissie bevestigt 112 als gratis noodnummer in de hele EU; alle vijf
markten vallen daarin. Geen garantie voor ieder land buiten de EU.
[Europese Commissie](https://digital-strategy.ec.europa.eu/en/policies/112)

| Markt | Acute route | Niet-levensbedreigende medische hulp | Crisissteun, geen vervanging spoed |
| --- | --- | --- | --- |
| Nederland | 112 | Eigen huisarts; avond/nacht/weekend huisartsen-spoedpost, lokale praktijkroute. [Thuisarts](https://www.thuisarts.nl/spoed-wie-bel-je) | 113 / 0800 0113; 24/7. [Rijksoverheid](https://www.rijksoverheid.nl/themas/familie-zorg-en-gezondheid/geestelijke-gezondheidszorg/zelfmoorden-verminderen) |
| Belgie | 112 | 1733 voor niet-levensbedreigende ongeplande zorg buiten huisartsuren, regioafhankelijk; buitenlandse aansluiting: +32 2 524 98 89. Geen landelijk-dekkingsclaim. [FOD](https://www.health.belgium.be/nl/themas/gezondheid/dringende-geneeskundige-hulpverlening/actoren-dringende-geneeskundige-hulpverlening/dokter-wacht-nodig-bel-1733) | Nederlandstalig 1813 24/7; Franstalig 0800 32 123 24/7. Taalkeuze niet gokken. [1813](https://www.zelfmoord1813.be/), [CPS](https://www.preventionsuicide.be/la-ligne-decoute-0800-32-123) |
| Duitsland | 112 | 116117 bij urgent maar niet levensbedreigend buiten praktijkuren | Telefonseelsorge 116123. [Federale gezondheidsportal](https://gesund.bund.de/notfallnummern) |
| Oostenrijk | 112; medische Rettung 144 | 1450 gezondheidsadvies; 141 artsenwachtdienst | Telefonseelsorge 142, rond de klok. [Noodnummers](https://www.gesundheit.gv.at/service/notruf/notrufnummern.html), [hotlines](https://www.gesundheit.gv.at/service/notruf/hotline.html) |
| Italie | 112; medische 118 | 116117 alleen waar daadwerkelijk actief; regionale continuita assistenziale elders | Telefono Amico Italia 02 2327 2327, luisterdienst en geen spoedcentrale; belkosten volgens provider. [Ministerie spoed](https://www.salute.gov.it/new/it/tema/112-118-e-pronto-soccorso/), [116117](https://www.salute.gov.it/new/it/tema/nuova-assistenza-distrettuale/numero-europeo-cure-non-urgenti-116117/), [operator](https://www.telefonoamico.it/cosa-facciamo/come-contattarci/) |

Italie: de ministeriele 116117-pagina is bijgewerkt op 03-09-2026 en onderscheidt
volledig actieve, gedeeltelijk actieve en slechts geautoriseerde regio's. Autorisatie
is geen beschikbaarheid. Geen statische lijst aannemen als landelijke dekking.
De actuele Telefono Amico-contactpagina noemt 24 uur; een
[eigen publicatie uit 2023](https://www.telefonoamico.it/z_site2021/wp-content/uploads/CS_2023_Dati-Telefono-Amcio-Italia.pdf)
noemt 10-24. Het nummer is bevestigd, maar beschikbaarheidsuren moeten voor runtime nog
door een tweede actuele operatorbevestiging worden gedekt; geen oude uren hardcoden.
Voor Belgie geldt eveneens geen aanname dat 1733 overal al werkt.

Taal en locatie zijn verschillende velden: NL/EN/DE-interface, GB-taalvlag,
abonnementland of automatische IANA-tijdzone bewijzen geen fysieke verblijfplaats.
Vraag hoogstens expliciet het huidige land wanneer nuttig; eerste acute boodschap
blijft direct zichtbaar. Bij onzeker land: 'in de EU 112; anders het lokale noodnummer',
zonder ongeverifieerde lokale fallback. Geen stilzwijgende geolocatie.

Voorgesteld hulpregister: country, locale, purpose, nummer, bereik/regio, bron-URL,
checked_at, reviewer, review_due, goedgekeurde copyversie. Controle voor iedere
release en voorgesteld elke 90 dagen; een verouderde detailroute valt terug op
gereviewde algemene hulp, niet op door AI bedachte nummers. Dit is geen automationopdracht.
Toegankelijkheid (spraak/gehoor, landgebonden tekst/appmogelijkheden) moet apart worden
geverifieerd; geen algemene SMS-naar-112-claim.

IT en Franstalig Belgie zijn taalreadinessblockers. Aanbeveling: geen Italiaanse of
Franse gezondheidsdialoog aanbieden totdat vertaling, classifiercorpus en medische
copy door moedertaalreview zijn gevalideerd. Een EN-interface is geen bewezen oplossing.
De 18+-grens blijft; crisisinformatie mag als aanbevolen apart statisch hulppad
beschikbaar blijven zonder minderjarigen tot het AI-product toe te laten.

## 14. Medische En Juridische Gates

De bovenstaande hulpniveaus zijn technische productopties, niet klinische goedkeuring.
Noodzakelijk voor elk nieuw operationeel safetycontract:

- Bevoegde medische reviewer keurt categorieen, acute-first routes, beperkte vragen,
  false-positivecorrectie, contra-indicaties en hervattingsgrenzen goed.
- Specialistische mentale-crisis/eetstoornisreview voorkomt risicovoorspelling,
  beschaming, schadelijke restrictieadviezen en onveilige recovery.
- Juridische beoordeling van intended purpose: het woord 'geen diagnose' voorkomt
  niet automatisch kwalificatie als medische software. De MDCG-guidance over
  softwarekwalificatie/classificatie is een relevante reviewbron, geen automatisch
  oordeel dat deze app wel/niet een medisch hulpmiddel is.
  [MDCG 2019-11 rev.1, juni 2025](https://health.ec.europa.eu/document/download/b45335c5-1679-4c71-a91c-fc7a4d37f12b_en?filename=mdcg_2019_11_en.pdf)
- DPO/legal bepaalt grondslag, afzonderlijke verwerking van gezondheidsinformatie,
  ontvangers, DPIA, correctie/bezwaar, retentie en eventuele gevolgen van automatische
  blokkades. Geen zelfverklaarde AVG-compliance.
- AI Act applicability, chatbottransparantie en actuele nationale/EU-verplichtingen
  toetsen. De Commissie publiceert een gewijzigd implementatietijdpad en nog
  ontwikkelende classificatierichtlijnen; deze audit geeft geen juridisch deadline-
  of risicoklasseoordeel. [Europese Commissie](https://digital-strategy.ec.europa.eu/en/policies/enforcement-ai-act)
- Medische en native-language copyreview voor alle daadwerkelijk aangeboden markten,
  plus productaansprakelijkheid, incident-/supportverantwoordelijkheid en bereikbaarheid.

Nooit de owner laten 'aftekenen als arts' om review over te slaan. Aanstellen/inkopen
van reviewers is een aparte beslissing; deze audit maakt geen kosten of afspraken.
Officiele webinformatie is voldoende om een auditvraag te onderbouwen, niet om een
volledige medische beslisboom met ongeteste grenzen te lanceren.

## 15. Providergrenzen En Kosten

Live provider_configurations bevestigt: real_member_processing_enabled=false,
owner_activation=false; ZDR/EU-route unverified, DPA/DPIA/transfer/lifecycle incomplete,
privacy-/consentcopy draft. Geen wijziging, secretinspectie of externe modeltest.

Aanbevolen toekomstige volgorde: bounded input en actuele auth/consent -> deterministische
serverclassificatie en safetygate -> relevante contextselectie -> entitlement/budget/
rate-reservering -> uitsluitend eventueel goedgekeurde providerroute -> strikte
output- en safetycontrole -> hercontrole actuele revisie/consent bij commit.
Statische hulp moet niet wachten op deze betaalde keten. Voor onbevoegde verwerking
geen persoonsgebonden safetyrecord aanmaken onder het mom van gratis hulp.

R2-R4/uncertain/unavailable stoppen providercoaching; hulp komt uit gereviewde vaste
copy. Provider mag nooit een deterministische stop downgraden.
Voor R0/R1 komt eventueel alleen een doelgebonden allowlist van minimale aggregates
in aanmerking na aparte GO. Geen raw safety/recoveryteksten, privechat, trainer-notities,
contactgegevens, UUIDs, GPS, foto's of medische dossiers via een 6E-classifiercall.
Ook gepseudonimiseerde aggregaten kunnen gezondheidsinformatie zijn.

OpenAI documenteert project-/orgspecifieke retentiecontroles, endpointbeperkingen en
mogelijke wijzigingen in modelgeschiktheid voor ZDR. store:false bewijst geen ZDR;
de exacte project-, model-, endpoint- en uitzonderingsvoorwaarden moeten actueel
worden vastgelegd. De frozen eis voor Europa/ZDR wordt niet afgezwakt door nieuwe
provideropties. [OpenAI Data Controls](https://developers.openai.com/api/docs/guides/your-data)

Geen achtergrondprovider, tools, files/vectorstores, live vertaling of cross-provider
fallback aanzetten. Prompt-/outputinhoud nooit in operationele logs; alleen begrensde
foutcodes, requestidentiteit, timings en werkelijk noodzakelijke usage. Geen raw
requestbody in exception- of monitoringtelemetry.

Kosten deze freeze/audit: 0 externe AI-calls / EUR 0,00. Historische 6B betaalde
synthetische tests zijn niet opnieuw uitgevoerd en worden niet tot nul herschreven.
Eerste offline/deterministische slice heeft geen providerverbruik, maar implementatie,
klinische review, hosting en support kunnen later wel kosten hebben; geen gratis
operationele dienst beloven. Frozen EUR 3 + maximaal EUR 1/Luna-grace, EUR 4 cap blijft.
Een toekomstig providerbudget vereist actuele prijs-/tokenmeting en aparte toestemming.

## 16. Teststrategie En Acceptatie

Gebruik uitsluitend synthetische cases. Maak een klinisch gelabelde golden set
met case-ID, taal, actuele/historische/hypothetische context, ervaarder, verwachte
hulpactie, toegestane communicatie, analyse/actiongate en verboden output.
Twee onafhankelijke reviews voor acute/mentale cases en een holdout-set.
Niet automatisch labels uit de huidige classifier afleiden.

Voorgestelde kern: tien categorieen x drie huidige talen x twaalf taal/contextvarianten
= minimaal 360 cases, plus IT/FR-gatecases, combinaties, state/race/securitytests.
Geen percentage PASS als vervanging van inspectie per acute case.
Alle gereviewde acute sentinelcases moeten de directe hulproute krijgen; een gemiste
acute case blokkeert release. Specificiteits-/false-positivecriteria per categorie
door reviewers vastleggen; niet verzinnen uit de 36 auditvoorbeelden.

| Testgroep | Minimale varianten | Vereiste uitkomst |
| --- | --- | --- |
| NL/EN/DE natuurlijk | Synoniemen, vervoegingen, natuurlijke zinnen | Zelfde gereviewde hulpactie, zonder diagnose |
| Spelling/spreektaal | Gesplitste woorden, typefouten, accenten, contractions | Geen triviale bypass; normale taal niet breed blokkeren |
| Ontkenning | Voor/na match, maar/but/aber, dubbele ontkenning | Negatie alleen eigen clause; positief actueel signaal blijft |
| Education/quotes | Vraag plus actueel zelf/ander signaal | Actuele hulpbehoefte wint, zuiver onderwijs geen incident |
| Hypothetisch/historisch | Ooit, vorige maand, derde persoon, herhaling nu | Geen permanente chatban; actuele herhaling wel stop |
| Trainingstaal | Borsttraining, gewone spierpijn, 'killer workout', uitgeput als metafoor | Geen diagnose/ongefundeerde crisis; contextgereviewd |
| Actuele klachten | Alle categorieen, combinaties en korte berichten | Acute copy onmiddellijk; geen provider voordat stop vastgesteld |
| Recoverytegenstrijdigheid | R06 plus beide clausulevolgorden | Geen intent/clearance ondanks gemist nieuw symptoom |
| Herhaling | Nieuwe request, replay, nieuw thread, meerdere devices | Nieuwe episode blokkeert; retry telt niet dubbel |
| Prompt injection | Arts-/trainerclaim, roleplay, systemtext, encoded/Unicode | Geen downgrade, tools of policywijziging |
| Cross-member | IDs aanpassen, raden, adminachtige payload | Geen read/write/event-/statuslek |
| Trainerprivacy | Geen consent, ingetrokken consent, einde relatie, andere trainer | Geen private tekst; default geen signalen |
| Retentie | Grensmoment, accountdelete, export, backups/restore | Termijnen aantoonbaar; TTL maakt geen medische clearance |
| Idempotency | Timeout, dubbelklik, gelijke ID/andere payload, event/recoveryrace | Een event per identity; conflict/revision beschermd |
| No domain writes | Training/Nutrition/Recovery/Progress hashes en RPC-allowlist | Geen mutation/proposal/executor; alleen aparte goedgekeurde auditopslag later |
| Gewone chat na event | Nieuwe normale input, threaddelete, entitlementwithdrawal | Safety geen ban; andere gates blijven gelden |
| Internationale copy | NL/BE/DE/AT/IT, land onbekend, reizen, verkeerde taalvlag | Alleen gereviewde juiste route, geen UK-copy of verkeerde regio |
| Mobiel/toegankelijk | 320x700,360x800,390x844,820x1180,1440x900, toetsenbord/zoom/screenreader | Geen overflow; hulpactie zichtbaar en niet onder avatar |
| Provider/failure | Tijdelijke fout, policy ontbreekt, ratecap, provider injection | Fail-closed voor coaching, vaste hulp bereikbaar, geen betaald retryloop |
| Frozen regressie | 6A-6D huidige baseline + eerder geaccepteerde telefoonflow | Geen chatban, recoverydowngrade, privacy- of plaatsingsregressie |

Latere SQL-gate pas onder aparte implementatieopdracht: rolled-back synthetic
transactions, echte concurrerende transacties, ACL/RLS, before/after allowlisted
memberdatafingerprints en volledig bewijs van cleanup. In deze audit geen SQL-DML.
Selectieve bronpredicaten bewijzen lockaanwezigheid, niet alle race-interleavings.

## 17. Voorgestelde Implementatiepackages

| Slice | Inhoud na aparte GO | Exitgate |
| --- | --- | --- |
| 6E-0 | Offline contract, expliciete compatibiliteitsmapping, synthetische golden set, klinische copy-/beleidreview | Beslissingen D1-D5, D8/D10; geen runtime-import of live data |
| 6E-1 | Minimale classifier/contextcorrecties en vaste hulpregels, achter bestaand mockpad na nieuwe scope | G-B/G-C/G-D/G-G plus acutecorpus/frozen regressies; medische review |
| 6E-2 | Alleen indien noodzakelijk nieuwe forward-only event/recovery/retentie-authority | Owner/DPO-retentie, ACL/RLS, race/idempotency, cleanup en memberdatahashgates |
| 6E-3 | Gereviewde hulp-/recoverypresentatie, internationale directory, toegankelijkheid | Klinische/native copy, vijf viewportchecks, geen chatban |
| 6E-4 | Optionele minimale trainer-signaaldeling | Afzonderlijk consent, relatieautoriteit, veto en privacyreview; default uit |
| 6E-5 | Afzonderlijke provider- en toekomstige actieintegratie | Alle 6B/6E gates, actuele budgetproef en nieuwe expliciete owneractivatie |

Geen slice wordt door deze tabel gestart. Geen 6E-flag aangemaakt.
Package 6E betekent niet automatisch voorstellen/uitvoering bouwen; daarvoor blijven
de volgende masterplanpackages en trainerautoriteit leidend.
Een eventuele toekomstige migration mag nooit de huidige 31 applied files herschrijven
of historische SQL replayen. De oorspronkelijke audit gebruikte de pre-theme keten van 30.

## 18. Eerste Veilige Slice En Ownerbeslissingen

Aanbevolen eerstvolgende opdracht: **6E-0 OFFLINE SAFETY CONTRACT + SYNTHETIC CORPUS**,
geen import in app/Edge, geen databaseverbinding/provider, geen live schema of flag.
Begin met de bewezen negation/education/recoverycounterexamples en acute categorieen.
Exit: gereviewde labels, compatibiliteitsmapping naar frozen clear/hard_stop en
afzonderlijke actiepoort, golden tests en een exact wijzigingsvoorstel voor 6E-1.
Zonder medische review kan de corpusstructuur klaar zijn, niet de medische release.

| Beslissing | Opties | Aanbeveling en nog vereiste autoriteit |
| --- | --- | --- |
| D1 Productdoel | Fitness-stop/hulpwijzer of medische triage | Stop/hulpwijzer; intended-purpose review door legal/medical, geen diagnosemodel |
| D2 Hulpniveaus | Twee frozen uitkomsten of vijf interne help-/actionniveaus | Vijf + uncertain/unavailable, geen gezondheids-/suicidekans; klinische mapping vereist |
| D3 Blokkadebereik | Alle drie analyses of selectief domein | Eerst alle nieuwe analyses bij R2-R4; gewone veilige chat en historie blijven |
| D4 Recovery | Self-declared voor alle acties of aparte analyse-/actiepoort | Frozen analyseflow behouden; automatische acties uit. R3/R4 later professioneel gereviewd pad |
| D5 Bewaarbeleid | Kort episodevenster / 90 dagen afgesloten details / max180 minimale audit of korter | 30/90/180 als bespreekvoorstel, DPO motiveert; onopgeloste status heeft revieweigenaar/limiet nodig |
| D6 Trainer | Uit / expliciet per bericht / permanente opt-in | Uit in eerste 6E; later per bericht met specifiek consent en preview |
| D7 Crisis zonder consent | Automatische nooddisclosure of alleen hulpwijzer | Alleen directe hulpwijzer; disclosure niet bouwen zonder aparte juridische/menselijke procedure |
| D8 Markten/talen | NL/EN/DE eerst of direct ook IT/FR | Gefaseerd, geen IT/Franstalige gezondheidsdialoog voor native clinical review; land apart kiezen |
| D9 Provider | Deterministisch of LLM als primaire safetyclassifier | Deterministisch eerst, externe safetyclassificatie uit; bestaande providerprivacygates behouden |
| D10 Reviewproces | Owner alleen of bevoegde medische/legal/privacy reviewers | Bevoegde reviewers; owner kiest scope/budget maar geeft geen medische vrijwaring |
| D11 Hulpbereikbaarheid | Alleen betaalde chat of apart statisch hulppad | Statische hulp onafhankelijk van login/AI-entitlement/ratecap, na product/copyreview |
| D12 Vervolgopdracht | Offline 6E-0 of direct nieuwe runtime | Alleen 6E-0; runtimecorrecties expliciet apart scopegeven |

Structuurcontrole: D1-D12 bestaan elk eenmaal, zonder ontbrekend of dubbel nummer.
D5 is niet eenduidig als keuzelijst: episodevenster, afgesloten details en minimale audit
zijn verschillende dataklassen, geen onderling uitwisselbare opties. De tabel blijft
inhoudelijk ongewijzigd. Het volledige begrijpelijke keuzerapport onderscheidt daarom
het bestaande 30/90/180-bespreekvoorstel van een korter doelgebonden beleid; exacte
termijnen en de onopgeloste-statusregel blijven open voor owner/DPO/review.
Zie PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md voor vraag, keuzes, gevolgen,
aanbeveling en vereiste review per D-nummer. Dit voegt geen gekozen beleid toe.

Geen optie is namens de owner gekozen of technisch geactiveerd.
De aanbevelingen zijn beslisvoorstellen, geen verzoek om tussentijdse toestemming
voor de huidige documentatieopdracht.

## 19. Blockers En Exacte Volgende Stap

Voor echte NIEUWE 6E-memberverwerking blijven geblokkeerd:
klinische categorie-/copyvalidatie, false-negative/contextcorrecties, onzekere-
taalroute, recovery-/retentiebeleid, noodzakelijke grondslag/DPIA, intended-purpose-
en AI Act-review, incident/supporteigenaarschap en volledige state/securitytests.
Voor trainerdeling extra specifiek consent/relatie/ontvangerbeleid.
Voor externe provider extra alle live incomplete/unverified 6B gates en owner-GO.
Voor volledige lokale DBreproduceerbaarheid blijft Docker/pg_cron ontbreken;
geen oude partial replay als volledige rebuild presenteren.
Geen blokkade voor de voltooiing van deze read-only audit zelf.

De 6D-themaretest is geaccepteerd en de gecorrigeerde definitieve freeze is vastgelegd;
de eventuele publicatieblokkade staat apart in het freeze receipt.
De volgende inhoudelijke 6E-stap: owner beslist over D1-D12, wijst bevoegde reviewers aan en
geeft uitsluitend een expliciete 6E-0-opdracht binnen de genoemde offlinegrenzen.
Nieuwe runtime-, schema-, trainer-, provider- of productiebeslissingen volgen apart.
Er worden nu geen credentials gevraagd, kosten gemaakt of beslissingen geforceerd.

Eindstatus:
- Package 6D definitief owner-accepted/frozen: YES, inclusief theme restoration.
- Package 6E readiness audit: COMPLETE.
- Package 6E implementation started: NO.
- Database changed by this task: NO.
- Migration created/executed: NO.
- Frontend/Edge changed for 6E: NO.
- External AI calls/cost: 0 / EUR 0,00.
- Production touched: NO.

Alleen documentatie en synthetisch auditbewijs zijn gecommit.
Geen PostgreSQL-/OneDrive-bestanden verwijderd; het onbekende 971-item-manifest
blijft ongewijzigd. Geen membercontent gelezen/geexporteerd, mail verzonden,
rol/koppeling gewijzigd of volgende functionaliteit gestart.
