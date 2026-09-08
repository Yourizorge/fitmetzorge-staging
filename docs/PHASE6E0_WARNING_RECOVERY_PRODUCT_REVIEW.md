# 6E-0 Productreview: Waarschuwing En Herstelflow

Status: OFFLINE CONCEPT / TECHNICAL PASS / OWNER PRODUCT REVIEW OPEN.
Datum: 2026-09-08. Baseline: c1e3b634e95c3d8911f31c414b198e2dfff415be, main, aanvankelijk schoon.
Geen owneracceptatie, medische vrijgave, freeze, 6E-1 of wijziging van de frozen app.

## 1. Afzonderlijk Tekstvoorstel

Alle vier rijen zijn NIEUWE CONCEPTTEKSTEN, niet deskundig goedgekeurd.
De bestaande copy.json, classifier en medische niveaus zijn NIET gewijzigd.
Voor bestaande herkende R1-R4 blijven de huidige niveaugebonden conceptteksten staan;
de nieuwe tekst geeft de vier oorspronkelijke gaten nog steeds GEEN medisch hulpniveau.

| Situatie | Exact NL | Exact EN | Exact DE |
| --- | --- | --- | --- |
| Actuele gemelde klacht, onvoldoende ingedeeld | Stop nu met trainen. Je meldt klachten die Youri niet betrouwbaar kan beoordelen. Neem contact op met een bevoegde zorgprofessional voor beoordeling. Zoek bij direct gevaar onmiddellijk noodhulp; wacht dan niet op Youri of je trainer. Er is niemand automatisch gewaarschuwd. | Stop exercising now. You report symptoms that Youri cannot reliably assess. Contact a qualified healthcare professional for assessment. In immediate danger, seek emergency help immediately; do not wait for Youri or your trainer. Nobody has been notified automatically. | Beende jetzt das Training. Du meldest Beschwerden, die Youri nicht zuverlaessig beurteilen kann. Wende dich zur Beurteilung an qualifiziertes medizinisches Fachpersonal. Suche bei unmittelbarer Gefahr sofort Notfallhilfe; warte dann nicht auf Youri oder deinen Trainer. Niemand wurde automatisch benachrichtigt. |
| Onduidelijke taal / context ontbreekt | Ik begrijp nog niet wat je bedoelt. Kun je je bericht in andere woorden uitleggen? | I do not yet understand what you mean. Can you explain your message in different words? | Ich verstehe noch nicht, was du meinst. Kannst du deine Nachricht mit anderen Worten erklaeren? |
| Technische uitval | De beoordeling is niet beschikbaar. Je kunt het later opnieuw proberen. Er is geen nieuwe beoordeling gedaan. | Assessment is unavailable. You can try again later. No new assessment has been made. | Die Beurteilung ist nicht verfuegbar. Du kannst es spaeter erneut versuchen. Es wurde keine neue Beurteilung vorgenommen. |
| Alleen educatief, ontkend, historisch, geciteerd of hypothetisch | Ik lees dit als uitleg, een citaat, een ontkenning of een eerdere of denkbeeldige situatie. Gaat het toch om klachten die je nu hebt? | I read this as an explanation, a quotation, a denial, or a past or hypothetical situation. Are you actually describing symptoms you have now? | Ich verstehe dies als Erklaerung, Zitat, Verneinung oder fruehere oder hypothetische Situation. Geht es doch um Beschwerden, die du jetzt hast? |

Toepassing en ontbrekende inhoudelijke beoordeling:
- De stoptekst hoort bij gemelde actuele klachten die onvoldoende kunnen worden ingedeeld,
  waaronder de vier oorspronkelijke voorbeelden; niet bij alleen een woord, emoji of uitval.
  De ernst is NIET vastgesteld. Reikwijdte van stoppen, zorgverwijzing, urgentieformulering
  en de grens tussen een klachtmelding en een losse gezondheidsvraag vragen medische review.
- De annotaties in dit voorstel zijn handmatig vastgelegde synthetische casuscontext.
  De classifier levert nog geen voldoende betrouwbare beslisbron voor al deze verschillen.
  Een annotation/origin-veld is GEEN door de gebruiker te bedienen vrijgave of productie-ACL.
- Een actuele klacht in een tweede zinsdeel krijgt eigen feedback. Een ontkenning, citaat
  of verleden tijd in een ander deel wist haar niet. Een technische fout blijft technische
  feedback; eerder gemelde klachten blijven afzonderlijk zichtbaar als eerdere melding.
- Hulp blijft binnen toegankelijke AI-chat. Zonder toegang wordt deze copy niet getoond.
  Geen automatische trainerdeling, hulpdienstmelding of succesvolle providercall vereist.

## 2. Functies Voor En Na Zelf Gemeld Herstel

A = chat en bestaande resultaten. F = nieuwe begrensde feitenanalyses.
A/F blijven in alle rijen onder bestaande autorisatie, entitlement en toepasselijke consent.
Feiten zijn geen persoonlijk advies. Het voorstel wijzigt geen werkelijke appfuncties.

| Synthetische situatie | Voor 'mijn klachten zijn voorbij' | Na alleen die zelfrapportage | Concrete vervolgstap / bestemming | Automatische acties |
| --- | --- | --- | --- | --- |
| Mijn borst voelt loodzwaar; idem de andere drie oorspronkelijke gaten | A + F, nieuwe stoptekst; geen persoonlijke analyse | A + F; herstelmelding vastgelegd, geen vrijgave | Klacht blijft oningedeeld. Herstelbeleid ontbreekt: ownerroute en deskundige criteria nodig; geen fictieve beoordelingswachtrij | UIT |
| Een los onbekend woord/emoji was geen klachtmelding | A + F; vraag om verduidelijking | A + F; zelfrapportage alleen sluit het misverstand niet | Verduidelijk oorspronkelijke betekenis; afzonderlijke niet-medische afhandeling per revisie. Daarna nieuwe persoonlijke analyseaanvraag via aparte inhoudspoort, niet levenslang tegengehouden door oude onzekerheid | UIT |
| Een eerdere technische beoordeling viel uit | A + F voor zover de sessie/databron bruikbaar is | A + F; herstelverklaring herstelt geen techniek | Opnieuw beoordelen wanneer beschikbaar; afzonderlijk technisch probleem afhandelen. Andere klachtmeldingen blijven open. Daarna dezelfde aparte inhoudspoort | UIT |
| Bestaand voorlopig lager niveau, zonder vastgesteld herhalingsgeval | A + F; mogelijkheid tot eigen herstelmelding | A + F; kandidaat voor nieuwe persoonlijke aanvraag | Expliciete aanvraag voor een gekozen analyse; inhoudsvoorwaarden nog open. Geen medische geschiktheidsclaim of automatische hervatting | UIT |
| Bestaand R3/R4, of expliciet synthetisch terugkerende klacht | A + F; bestaande niveaugebonden feedback | A + F; herstelmelding, geen vrijgave | Ernst-/herhalingsspecifieke route, bevoegde rol, benodigde informatie en besliscriteria ontbreken. Dit deel is uitdrukkelijk NIET af als gebruikersflow | UIT |
| Nieuwe klacht na herstel of na afhandeling van een taalprobleem | A + F; nieuwe melding krijgt eigen revisie | Oude herstelmelding geldt niet voor de nieuwe melding | Nieuwe klacht opnieuw beoordelen. Oude niet-medische afhandeling blijft staan; niets wissen of herclassificeren | UIT |

Concreet ontworpen pad: melding bekijken -> expliciet herstel melden OF betekenis
verduidelijken -> specifieke eerdere kwestie afzonderlijk afhandelen -> nieuwe aanvraag
voor dag-/na-workout-/weekanalyse voorbereiden -> apart inhoudsbesluit voor die aanvraag.
Pas na later vastgestelde en goedgekeurde inhouds-/herstelcriteria zou een persoonlijke
read-only uitkomst kunnen volgen; dat eindpunt wordt hier NIET uitgevoerd of vrijgegeven.
Een aanvraag voorbereiden is geen aanvraag versturen. Er bestaat nog geen beoordelingsdienst.

Exacte Nederlandse flowfeedback:
- Zelfrapportage, BESTAAND: "Je meldt dat de klachten voorbij zijn. Dit is jouw verklaring, geen medische vrijgave."
- Niet-medische afhandeling, NIEUW CONCEPT: "De eerdere taal- of technische onzekerheid is in dit concept afgehandeld; de registratie blijft bewaard. Je kunt een nieuwe aanvraag voor persoonlijke analyses voorbereiden. De inhoudelijke toelatingsvoorwaarden moeten nog worden vastgesteld."
- Ontbrekend gezondheidsherstelpad, NIEUW CONCEPT: "Voor persoonlijke analyses na deze klachtmelding is de vervolgstap nog niet vastgesteld. Chat, bestaande resultaten en begrensde feiten blijven onder je bestaande toegangsrechten beschikbaar. Er is geen beoordeling aangevraagd en niemand gewaarschuwd."
- Nieuwe melding, NIEUW CONCEPT: "Je nieuwe melding wordt opnieuw beoordeeld. Je eerdere herstelmelding geldt niet voor deze nieuwe melding."

Afhandeling bevat alleen een synthetisch record voor dezelfde persoon/revisie, met
herbeoordelingsrevisie en conceptbeslisgrond. Oudere bronregistraties blijven onveranderd.
Een losse nieuwe R0, zelfrapportage, nieuw gesprek, tijdverloop of verwijderen is geen
afhandeling. Een afhandeling voor taal/techniek mag nooit een aparte gezondheidsmelding
sluiten. Bewaren in dit testmodel is GEEN keuze voor onbeperkte retentie.

## 3. Verschillen En Exacte Open Beslissingen

Nieuw: vier feedbacksoorten naast bestaande copy, een expliciet vier-assig functiebeeld,
en afhandeling van niet-medische onzekerheid los van het veiligheidsverleden.
Het bestaande state.cjs blijft onzekerheid onthouden; alleen het aparte conceptviewmodel
toont een toekomstige afhandelroute. Geen classifieruitbreiding of daadwerkelijke analysehervatting.

| Punt | Exacte ownerbeslissing | Deskundige beoordeling blijft nodig |
| --- | --- | --- |
| P1 Stoptekst en betekenis | Deze aparte NL/EN/DE-teksten en scheiding accepteren voor verdere offline uitwerking, of tekstwijzigingen aanwijzen? | Medisch: scope en zorg-/urgentieformulering; native taal; juridisch: verwachtingen. Nog geen criteria om ernst automatisch vast te stellen |
| P2 Misverstand/techniek afhandelen | Akkoord met verduidelijking plus afzonderlijke afhandeling per kwestie, in plaats van herstelcheckbox of wissen? Wie mag de niet-medische afhandeling vaststellen, met welke bron? | Privacy/juridisch: minimale metadata, aantoonbare correctie en toegangsrollen; medisch: grens waar geen niet-medische afhandeling mag plaatsvinden |
| P3 Persoonlijke analyses | Welke gepersonaliseerde inhoud mag per dag-/na-workout-/weekaanvraag terugkomen, en welk expliciet inhoudsbesluit is daarvoor nodig? Tot die keuze blijft dit alleen aanvraagvoorbereiding | Medisch/product: inhoud die niet tot onbedoeld trainings-/voedings-/hersteladvies leidt. Geen drempel afgeleid uit R0 of zelfrapportage |
| P4 Ernst, onzekerheid en herhaling | Wie draagt het toekomstige hervattingsproces, waar ziet de gebruiker de aanvraag/status, welke reactie-/escalatietermijn geldt en hoe kan een afwijzing worden herbeoordeeld? Geen aanvraagbelofte voordat dit bestaat | Medisch: welke actuele informatie/bevoegde beoordeling vereist is voor oningedeelde, ernstige en terugkerende signalen; geldigheid en gevolgen van nieuwe signalen. Trainer is niet automatisch medische vrijgever |
| P5 Ontbrekende details en bewaarbeleid | Wie beslist bij ontbrekende gegevens en wat is de doelgebonden maximale duur van onopgeloste status? | D5 blijft open: privacy/juridisch plus medische gevolgen. Geen permanente restblokkade of automatische vrijgave door wissen/termijnverloop |

D1-D12 blijven ongewijzigd. Voorlopig uitsluitend ownerproductreview; geen reviewers
benaderd, kosten gemaakt of medische/productkeuzes stilzwijgend goedgekeurd.

## Technisch Bewijs

193/193 gerichte offline tests PASS: 58 voorsteltests + 39 state + 83 recognition-followup
+ 7 beperkingsregressies + 6 isolatie. Dit zijn contractchecks, geen klinische validatie.
De vier gaten blijven uncertain/null; gewone woorden/emoji en uitval krijgen andere feedback.
Geen volledige brede suite, theme-, browser-, database- of membertests gestart voor deze scope.
Nieuwe bestanden: _offline/phase6e0/warning-recovery-proposal.cjs, bijbehorende .json,
test/warning-recovery-proposal.test.cjs en dit overzicht. README/status/testmatrix verwijzen hierheen.
Publicatiebewijs en exacte commits: PHASE6E0_WARNING_RECOVERY_PUBLICATION.md.

Reproduceer de gerichte checks vanaf de repositoryroot, zonder installatie of netwerk:

```powershell
node --test _offline/phase6e0/test/warning-recovery-proposal.test.cjs _offline/phase6e0/test/state.test.cjs _offline/phase6e0/test/recognition-followup.test.cjs _offline/phase6e0/test/limitations.test.cjs _offline/phase6e0/test/isolation.test.cjs
```

Geen runtime/frontend/Edge/database/migration/memberdata/entitlement/provider/workflow/
rechtenwijziging, externe AI-call of bestandsopruiming. Production touched: NO.
Volgende stap: ownerproductreview van P1-P5. Geen freeze of automatische 6E-1-start.
