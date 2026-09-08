# Package 6E-1 Owneroverzicht

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
Drie extra taalprobes krijgen nog alleen verduidelijking, niet de gezondheidswaarschuwing:
"Mijn borst brandt van binnen", "My left arm has gone numb",
"Mir schnürt es die Kehle zu". Dit zijn beperkingobservaties, geen herkenningssuccessen.

Voor latere live integratie blijven afzonderlijk expliciet GO/scope/terugweg,
relevante beoordelingen, betrouwbare bericht-/aggregatebron, bestaande serverauth/
entitlements/consent, 6D-gatecompatibiliteit en goedgekeurde retentie-/herstelregels nodig.
Geen automatische owneracceptatie, volledige Phase 6E-freeze of volgend pakket.
