# Package 6E-1 Owneroverzicht

## Owneracceptatie O1-O5 - Actueel

COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE CONTRACTS ONLY.
Expliciet ownerakkoord op 2026-09-09, geen afgeleide acceptatie uit tests.
6E-0 blijft accepted/frozen. Phase 6E is NIET afgerond. Geen live vrijgave.
De fysieke telefoontest van de ronde timer blijft een afzonderlijke open test.

| Besluit | Geaccepteerd en offline uitgewerkt | Grens |
| --- | --- | --- |
| O1 Context | Waarschuwing aan bericht, context en revisie gekoppeld; bestaande conceptteksten behouden | Geen medische of taalvalidatie; beperkte regels zijn geen volledig taalbegrip |
| O2 Misverstanden | Opnieuw formuleren of retry EN verder chatten; geen verplichte vraaglus | Afhandeling van de eigen kwestie wist geen andere gezondheidsmelding |
| O3 Analyse-inhoud | Concrete dag/workout/weekfeiten en vergelijkbare absolute verschillen | Geen persoonlijke aanbevelingen, diagnose of automatische actie |
| O4 Hervatting | Zelfrapportage is geen medische vrijgave; chat/historie/feiten binnen bestaande rechten | Voorwaarden per aanbevelingstype zijn de afzonderlijke vervolgscope; deskundige ernstige/terugkerende/oningedeelde criteria blijven open |
| O5 Onopgelost | Recente meldingen volgen, herhaald uitvragen beperken; FitMetZorge beheert minimale datum/status/berichtverwijzing | Maximaal 30 dagen vanaf eerste registratie, eerder bij vervallen noodzaak; geen verlenging door bekijken/verwerken/retry/status; geen live opslag |

Na O5-verloop verdwijnt de extra registratie, niet automatisch de oorspronkelijke
chat of analyse. Hun bestaande retentie blijft gelden. Er volgt geen medische
vrijgave; ontbrekende context wordt niet gereconstrueerd. Een nieuwe klacht is
een nieuwe melding, niet een verlenging van de oude. Geen kopie van volledige chat,
geen menselijke beoordelingsdienst, geen automatische trainerdeling.

De waarschuwingen en voorbeelden hieronder zijn ongewijzigde conceptcopy. Wat nu
extra uitvoerbaar is: optionele vervolgkeuzes bij misverstanden en een afzonderlijke
minimale bewaarsimulatie met vaste eerste ankers, vroeger verval en ontbrekende bron.
Er is geen nieuwe medische classificatie of algemene account-/abonnementsblokkade.

O1-O5 en D1-D12 worden NIET opnieuw ter beslissing voorgelegd.
Voor latere live inzet blijven medische inhoud/hervattingscriteria, privacy/noodzaak/
retentie, juridische beoordeling en NL/EN/DE-taaltoepassing open, plus vertrouwde
bron/auth/consent/deletion-integratie en een afzonderlijke expliciete live GO.
Geen van deze ontbrekende beoordelingen is ingevuld met een fictieve dienst.

Bewijs en grenzen: [freeze receipt](PHASE6E1_FREEZE_RECEIPT.md).
Enig voorstel: [6E-2 offline persoonlijke aanbevelingscontracten](PHASE6E1_PROPOSAL.md),
NIET gestart. Eerst een expliciete afgebakende vervolgopdracht.

## Historische Productreview Voor O1-O5-Akkoord

Alle reviewvragen en niet-geaccepteerd-statussen hieronder zijn historische
leveringsinformatie, vervangen door het akkoord hierboven. De oorspronkelijke
voorbeelden, testuitslagen en beperkingen blijven behouden; de drie oude
herkenningsmissers zijn al hersteld door cf6c212 en zijn geen actuele missers.

Dit overzicht gebruikt de vijf opnieuw uitgevoerde voorbeelden uit
`_offline/phase6e1/test/examples.cjs`. Geen nieuwe AI-logica, algemene audit of
medische beoordeling. De drie oude herkenningsgaten zijn hersteld; de 36 bestaande
follow-upregressies slagen. Technische testuitslagen bewijzen geen klinische dekking.

Alle onderstaande functies zijn OFFLINE ONTWORPEN gedrag, niet nieuw live gedrag.
Chat, historie en begrensde feiten blijven binnen bestaande rechten en toestemming.
Persoonlijke aanbevelingen zijn nog niet gegenereerd/uitgewerkt; acties staan uit.
Dit is geen persoonsgebonden permanente blokkade en geen aanvraag- of goedkeuringsdienst.

| Situatie | Werkelijk uitvoerbaar conceptgedrag |
| --- | --- |
| Actuele oningedeelde klacht: "Mijn borst voelt loodzwaar" | "Stop nu met trainen. Je meldt klachten die Youri niet betrouwbaar kan beoordelen. Neem contact op met een bevoegde zorgprofessional voor beoordeling. Zoek bij direct gevaar onmiddellijk noodhulp; wacht dan niet op Youri of je trainer. Er is niemand automatisch gewaarschuwd." Chat, historie en begrensde registraties blijven toegankelijk. |
| Bestaand voorlopig signaal: "Ik heb borstpijn" | "Stop de activiteit waarover je klachten meldt en vraag een bevoegde zorgprofessional om beoordeling. Youri stelt geen diagnose." Geen nieuw medisch niveau of hervattingscriterium toegevoegd. |
| Taalprobleem: "flurbel" | "Ik begrijp nog niet wat je bedoelt. Kun je je bericht in andere woorden uitleggen?" Het gebonden antwoord "Ik bedoelde mijn borsttraining met gewichten" sluit alleen dit misverstand. Andere klachten blijven staan. |
| Technische uitval | "De beoordeling is niet beschikbaar. Je kunt het later opnieuw proberen. Er is geen nieuwe beoordeling gedaan." Retry gebruikt hetzelfde bericht met persoon/revisie/pogingbinding; alleen de technische kwestie sluit. Een alsnog herkende klacht krijgt een eigen waarschuwing. |
| Dag-, workout- en weekanalyse | Beschrijvende totalen en vergelijkbare absolute verschillen: bijvoorbeeld 35 trainingsminuten (+5), 12 sets (+2), of 105 weekminuten (+15). Geen diagnose, geschiktheid, intensiteitsadvies of behandel-/trainingsaanpassing. |
| "Mijn klachten zijn voorbij" | "Je meldt dat de klachten voorbij zijn. Dit is jouw verklaring, geen medische vrijgave." Alleen de bedoelde eigen meldingen krijgen zelfrapportagestatus. Historische veiligheidsinformatie blijft; chat/historie/feiten blijven. Geen persoonlijke adviesvrijgave. |
| Nieuwe/terugkerende klacht | Nieuwe beoordeling en waarschuwing; een eerder herstelantwoord kan de nieuwe melding niet afhandelen. Betekenis/criteria van medische terugkeer zijn niet door de simulator bepaald. |
| Onopgeloste melding | Blijft een zichtbare onzekerheid binnen de simulatie, geen beoordelingswachtrij. Doel/maximum/verantwoordelijke voor blijvende unresolved-opslag zijn onbeslist: geen persistente opslag activeren. |
| Ontbrekende/verwijderde gegevens | Bijvoorbeeld "Geen bruikbare registratie voor zelf geregistreerde slaapduur." Niet vervangen door nul of verzonnen waarden. Ontbrekende klachtcontext is onzekerheid, geen vrijgave; ook geen stilzwijgende eeuwige accountblokkade. |

### Alleen Resterende Ownerkeuzes

Concrete voorstellen ter beoordeling, NIET als akkoord of implementatie vastgelegd.
Dit concretiseert bestaande O1-O5; bevestigde D1-D12 worden niet heropend.

| ID | Concreet voorstel | Korte reden / nog benodigde beoordeling |
| --- | --- | --- |
| O1 Contextkoppeling | Beoordeel de concrete tekst-naar-context-uitkomsten van 6E-1 als productgedrag; voorstel: behoud de uitgevoerde fragment-/conflictregels en hun koppeling aan de al geaccepteerde 6E-0-conceptteksten. Die teksten en scheiding worden niet opnieuw ter acceptatie voorgelegd. | Nu gaat het om de nieuwe koppeling vanuit een bericht, zonder fixturecontext als invoer. Klinische toepassing/dekking, NL/EN/DE-taal en juridische juistheid blijven deskundige reviewpunten. |
| O2 Niet opgelost misverstand | Behoud gebonden verduidelijking/retry. Voorstel voor nog niet uitgewerkte eindbediening: na een mislukte verduidelijking toon de open vraag, laat vrij verder chatten en bied opnieuw formuleren aan; geen verplichte eindeloze vraaglus of dienst. Nieuwe klachten apart beoordelen. | Herstelbaar taalprobleem zonder andere veiligheidsinformatie te wissen. Productakkoord op deze eindbediening en privacy/medische beoordeling van betwisting van gezondheidscontext ontbreken nog. |
| O3 Analyse-inhoud | Accepteer de uitgevoerde dag/workout/week-totalen, vergelijkbare absolute verschillen en expliciete ontbrekend-datafeedback als eerste begrensde inhoud. Werk persoonlijke trainings-/voedingsaanbevelingen alleen uit in een apart afgebakende vervolgscope. | Maakt feitelijke observaties bruikbaar zonder ze als advies te verkopen. Bronnen/vensters, noodzakelijke data en consent moeten voor live bewezen zijn; persoonlijke adviesinhoud vraagt product- en deskundige inhoudsgrenzen. |
| O4 Persoonlijke hervatting | Werk in de aparte vervolgscope per gekozen aanbeveling uit welke actuele informatie nodig is na ernstige, terugkerende of oningedeelde klachten, samen met de inhoudsgrens uit O3. Voorstel: geen algemene knop die alle persoonlijke adviezen vrijgeeft; hervatting moet per inhoudstype aantoonbaar begrensd zijn. | De al bevestigde zelfrapportage, toegang en nieuwe beoordeling blijven staan; daarover is geen nieuw akkoord nodig. De inhoudsmatrix en concrete herstelvoorwaarden ontbreken en vragen product-/medische/juridische beoordeling, geen zelfbedachte termijn, drempel of menselijke aanvraagdienst. |
| O5 Onopgelost/ontbrekend | Activeer geen blijvende unresolved-opslag zolang doel, minimale gegevens, verantwoordelijke en maximum niet zijn vastgesteld. Laat ontbrekende context eerlijk ontbreken en vraag zo nodig actuele informatie, zonder verwijderde feiten te reconstrueren. | Voorkomt onbesliste onbeperkte gezondheidsopslag. Exact unresolved-doel/maximum/verantwoordelijkheid en gevolgen bij verdwenen details vragen ownerbesluit met privacy/juridische en inhoudelijke beoordeling. Bevestigde D5-doelgebonden 30/90/180-grenzen blijven staan. |

6E-0 blijft accepted/frozen OFFLINE ONLY; 6E-1 blijft TECHNICAL PASS, NIET
owner-accepted/frozen/live. Trainingsakkoord verandert dat niet.
Pas een apart goedgekeurde vervolgscope mag verdere AI-uitwerking starten.
Voor live: expliciete GO/scope/rollback, deskundige beoordelingen, vertrouwde
bericht-/aggregatebron, bestaande auth/consent/entitlements, 6D-gatecompatibiliteit,
inhoud/hervatting en doelgebonden retentie aantoonbaar geregeld.
Niemand benaderd; geen reviewdienst, automatische trainerdeling of automatische actie.

Follow-up 2026-09-08: de drie hieronder historisch gemelde herkenningsmissers zijn
gericht gecorrigeerd in cf6c212, met 36 vooraf gecommitteerde tests. Zie het
[actuele follow-uprapport](TRAINING_WORKOUT_FOLLOWUP_REPORT.md). Oude resultaten
en beperkingobservaties hieronder blijven historisch bewijs, geen actuele missers
of extra herkenningssuccessen. 6E-1 blijft uitsluitend offline en niet geaccepteerd.
De geautoriseerde nieuwe Training-runtime is afzonderlijk vastgelegd; de oude
algemene app-freezeclaim geldt niet voor die zeven Training-bestanden.

PACKAGE 6E-1 OFFLINE CONTRACTS - TECHNICAL PASS / READY FOR OWNER REVIEW.
Dit is een offline productvoorstel, geen medische goedkeuring of complete herstelroute.
6E-0 blijft owner-accepted/frozen. Phase 6E blijft onvoltooid. Geen live integratie.

## Complete Voorbeelden

Onderstaande resultaten komen uit de uitvoerbare synthetische voorbeelden.
Alle toegankelijkheid veronderstelt bestaande rechten, juiste persoon en toestemming.
Chat/historie blijven behouden; geen algemene abonnementsblokkade of trainerdeling.
Alle automatische acties blijven UIT, voor en na herstel.

### 1. Actuele Oningedeelde Klacht -> Daganalyse -> Herstel -> Nieuw Signaal

Bericht: "Mijn borst voelt loodzwaar".
Exacte waarschuwing:
"Stop nu met trainen. Je meldt klachten die Youri niet betrouwbaar kan beoordelen. Neem contact op met een bevoegde zorgprofessional voor beoordeling. Zoek bij direct gevaar onmiddellijk noodhulp; wacht dan niet op Youri of je trainer. Er is niemand automatisch gewaarschuwd."

Beschikbare dagfeiten: 1 workout, 35 min en 6000 stappen. Concrete observatie:
"Geregistreerde trainingstijd: 35 min. +5 min ten opzichte van het vorige vergelijkbare venster."
Ontbrekende slaapgegevens worden niet als nul ingevuld.

Herstelbericht: "Mijn klachten zijn voorbij".
Feedback: "Je meldt dat de klachten voorbij zijn. Dit is jouw verklaring, geen medische vrijgave."
Twijfel als misschien/think/glaube wordt niet als bevestigde eigen herstelmelding vastgelegd.
Dezelfde feiten blijven beschikbaar. De oorspronkelijke melding/waarschuwing blijft
in historie als zelf-gerapporteerd, niet als medisch beoordeeld. Een volgende
"Mijn borst voelt loodzwaar" krijgt een nieuwe actuele revisie en opnieuw de waarschuwing.
Persoonlijke aanbevelingen blijven niet-geimplementeerd; oningedeelde herstelcriteria open.

### 2. Bestaand Voorlopig Ernstig Signaal -> Workoutanalyse -> Herstel -> Herhaling

Bericht: "Ik heb borstpijn".
Exacte bestaande conceptwaarschuwing:
"Stop de activiteit waarover je klachten meldt en vraag een bevoegde zorgprofessional om beoordeling. Youri stelt geen diagnose."

Beschikbare workoutfeiten: 35 min, 12 sets, 96 herhalingen.
"Geregistreerde sets: 12. +2 ten opzichte van het vorige vergelijkbare venster."
Dit is geen uitspraak over intensiteit, prestatieverbetering of trainingsgeschiktheid.

Na "Mijn klachten zijn voorbij" blijft die beschrijvende inhoud beschikbaar, met
dezelfde expliciete zelfrapportagefeedback uit voorbeeld 1. Ernstige herstelcriteria
zijn NIET ingevuld. Bij herhaling komt een nieuwe actuele melding; oude zelfrapportage
geeft geen vrijgave. Er is geen beoordelaar, aanvraag of wachtrij aangemaakt.

### 3. Duitse Melding -> Weekanalyse -> Herstel -> Nieuwe Melding

Bericht: "Ich kriege kaum noch Luft".
Exacte waarschuwing:
"Beende jetzt das Training. Du meldest Beschwerden, die Youri nicht zuverlaessig beurteilen kann. Wende dich zur Beurteilung an qualifiziertes medizinisches Fachpersonal. Suche bei unmittelbarer Gefahr sofort Notfallhilfe; warte dann nicht auf Youri oder deinen Trainer. Niemand wurde automatisch benachrichtigt."

De Nederlandse reviewweergave toont 3 workouts en 105 min:
"Geregistreerde trainingstijd: 105 min. +15 min ten opzichte van het vorige vergelijkbare venster."
Deze synthetic_utc-vensters zijn beide 7 dagen en volledig geregistreerd.
Na gebonden zelfrapportage blijft dezelfde inhoud beschikbaar. Een nieuwe melding
wordt opnieuw beoordeeld; oningedeelde en herhalingscriteria blijven open.
Een taalwisseling is geen landkeuze of medische vrijgave.

### 4. Technische Fout -> Exacte Retry

Oorspronkelijk bericht: "Ik train borst en armen"; gesimuleerde beoordeling unavailable.
"De beoordeling is niet beschikbaar. Je kunt het later opnieuw proberen. Er is geen nieuwe beoordeling gedaan."

Chat/historie en afzonderlijk beschikbare begrensde feiten blijven onder rechten bruikbaar.
Een retry van precies die tekst, persoon, melding, revisie en poging slaagt.
Alleen de technische kwestie sluit. Zij blijft niet als oude fout doorwerken.
Als de oorspronkelijke tekst een klacht was, maakt de geslaagde retry daarvan juist
een gezondheidsmelding; hij geeft GEEN gezondheidsvrijgave of onbeperkt advies.

### 5. Taalprobleem -> Verduidelijking

Bericht: "flurbel".
"Ik begrijp nog niet wat je bedoelt. Kun je je bericht in andere woorden uitleggen?"

Gebonden antwoord: "Ik bedoelde mijn borsttraining met gewichten".
Alleen deze communicatiekwestie sluit; bestaande andere klachten blijven staan.
De dagfeiten blijven dezelfde. Een kale R0/approved, citaat of ontkende verduidelijking
sluit niets af. Nieuwe klachten tijdens verduidelijking worden apart vastgelegd.

## Productverschil Met 6E-0

| Onderdeel | Nu concreet voorbereid | Nog niet afgerond |
| --- | --- | --- |
| Waarschuwingselectie | Berichttekst -> afgebakende contextregels -> exact fragment -> copy, zonder fixturecontext als invoer | Representatief taalbegrip en juiste medische toepassing van copy |
| Verduidelijking/retry | Bericht-/persoon-/revisie-/poginggebonden, idempotent, alleen eigen kwestie | Vertrouwde echte bericht-/retrybron; geen live adapter |
| Persoonlijke inhoud | Concrete dagelijkse, workout- en weekfeiten en beschrijvende verschillen | Inhoud en hervatting van persoonlijke aanbevelingen |
| Zelfrapportage | Eigen chatzin of expliciete bevestiging met targets; nieuwe klacht blijft nieuw | Volledige ernstige/terugkerende/oningedeelde herstelroute |
| Retentie | Doelgebonden 30/90/180-projecties met ontbrekend-datafeedback | Definitieve maxima/verantwoordelijkheid voor unresolved, live opslag/verwijdering |

NIEUWE CONCEPTCOPY in NL/EN/DE voor inhoudsgrenzen, niet deskundig goedgekeurd:
NL: "Persoonlijke aanbevelingen en de voorwaarden voor hervatting zijn nog niet uitgewerkt. Er bestaat geen beoordelingsdienst."
EN: "Personalized recommendations and resumption criteria are not yet defined. There is no review service."
DE: "Persoenliche Empfehlungen und Voraussetzungen fuer die Wiederaufnahme sind noch nicht festgelegt. Es gibt keinen Beurteilungsdienst."
Bestaande waarschuwingen en medische niveaus zijn niet herschreven.

## Eenmalig Gebundelde Open Vragen

| ID | Nog exact te beslissen / beoordelen | Ownerproductreview | Deskundige beoordeling voor eventuele live inzet |
| --- | --- | --- | --- |
| O1 Context | Zijn fragmenten, conflictprioriteit, verduidelijkingsgrens en hulptekst passend? Hoe omgaan met klachten buiten de woordenlijst, derde personen en onduidelijke quote-overname? | Gedrag en begrijpelijkheid van concrete voorbeelden | Medisch, moedertaal en juridisch: gemiste/onterecht geselecteerde waarschuwingen en bereikbaarheid |
| O2 Misverstanden | Is de begrensde eigen-bedoelingflow bruikbaar, en wat is de vervolgstap als die verduidelijking niet lukt? Een eenmaal herkende gezondheidsmelding wordt niet als technische fout weggepoetst | Exacte misverstand-/betwistingsgrens, geen menselijke dienst | Privacy/product en waar gezondheid wordt geherinterpreteerd medisch/juridisch; betrouwbare binding/serverbron |
| O3 Inhoud | Welke van deze beschrijvende persoonlijke observaties zijn productmatig toegestaan; welke aanbevelingen per dag/workout/week en toestand mogen later bestaan? | Concrete inhoud, bronvensters en missing-dataweergave | Medisch/juridisch voor aanbevelingsgrenzen; privacy voor noodzakelijke bronnen/consent |
| O4 Hervatting | Welke actuele informatie en inhoudsvoorwaarden gelden na ernstige, herhaalde en oningedeelde klachten, ook na zelfrapportage? | Functioneel vervolg; geen automatische vrijgave of aanvraagdienst | Medisch/juridisch/native voor concrete herstel- en hulpcriteria; geen termijn/drempel/beoordelaar door Codex ingevuld |
| O5 Retentie | Welk doel, noodzakelijkheid, maximum en verantwoordelijke gelden voor unresolved en welk vervolg bij verdwenen details? | Ontbrekend-data- en eindgedrag binnen bevestigd D5 | Privacy/juridisch plus medisch-productgevolgen; geen onbesliste opslag activeren |

D1-D12 worden hiermee NIET heropend. Alleen ownerproductreview is nu gevraagd;
niemand is benaderd of ingehuurd. TECHNICAL PASS is geen medische validatie.
Historische observatie, inmiddels hersteld door cf6c212 (zie boven):
bij de oorspronkelijke levering kregen drie extra taalprobes alleen verduidelijking:
"Mijn borst brandt van binnen", "My left arm has gone numb",
"Mir schnürt es die Kehle zu". Dit zijn beperkingobservaties, geen herkenningssuccessen.

Voor latere live integratie blijven afzonderlijk expliciet GO/scope/terugweg,
relevante beoordelingen, betrouwbare bericht-/aggregatebron, bestaande serverauth/
entitlements/consent, 6D-gatecompatibiliteit en goedgekeurde retentie-/herstelregels nodig.
Geen automatische owneracceptatie, volledige Phase 6E-freeze of volgend pakket.
