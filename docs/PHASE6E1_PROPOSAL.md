# Package 6E-1 Afzonderlijk Voorstel

Status: PROPOSAL ONLY / NOT STARTED / NO ACTIVATION AUTHORITY.
6E-0: COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE PREPARATION ONLY.
Phase 6E als geheel: ONVOLTOOID. Deze documentatieopdracht start 6E-1 NIET.
Actuele acceptatie en correctie: [6E-0 freeze receipt](PHASE6E0_FREEZE_RECEIPT.md).

## Een Aanbevolen Volgend Pakket

**6E-1 - Offline context-, inhouds- en hervattingscontract.**
Alleen na een afzonderlijke expliciete opdracht: vijf concrete contractonderdelen
hieronder uitwerken en met vooraf vastgelegde synthetische voorbeelden controleren.
Geen nieuwe algemene audit, geen live patch of automatische import van het 6E-0-model.
De vier oorspronkelijke known/R0-gaten zijn al hersteld naar uncertain/null.
Hun precieze regressiegevallen blijven behouden; ze zijn geen nieuw te repareren pakket.

De bevestigde D1-D12-richting blijft vaststaan: stop-/hulpwijzer zonder diagnose,
vijf voorlopige niveaus en afzonderlijke onzekerheid, behoud van bestaande toegang,
zelfrapportage zonder medische vrijgave, doelgebonden retentie, geen automatische
trainer-/noodmelding, NL/EN/DE, geen externe classifier, voorlopig ownerproductreview,
hulp binnen toegankelijke chat en geen impliciete live toestemming.
Dit pakket vraagt NIET opnieuw naar die keuzes.

## Concrete Resterende Onderdelen

| Onderdeel | Wat ontbreekt | Concreet toekomstig resultaat | Productbesluit / deskundige beoordeling | Alleen offline voorbereiden | Voor live aantoonbaar geregeld |
| --- | --- | --- | --- | --- | --- |
| Berichtcontext -> waarschuwing | De waarschuwingselectie gebruikt handmatige synthetische annotation/origin. Dit is geen betrouwbare live bron; actuele klacht, onbekend woord en contextverwijzing kunnen nog verkeerd worden onderscheiden | Versieerbaar contextcontract met herleidbare bron, timing/subject, zinsdeel-/ontkenningsscope en aparte onzekerheids-/uitvaluitkomst; expliciete mapping naar bestaande of conceptcopy | Product: exacte betekenis en conflictprioriteit van velden. Medisch/native/juridisch: copy, gemiste en onterechte waarschuwingen; geen zelfverzonnen urgentierangen | Beslistabel, NL/EN/DE positieve/negatieve/mixed cases, ontbrekende-contextgevallen en misbruiktests; annotaties blijven expliciet fixturelabels | Betrouwbare koppeling aan het echte berichtpad, relevante inhoudelijke validatie, geen door gebruiker te vervalsen vrijgaveveld; bron-/contextfouten krijgen aantoonbaar passende feedback |
| Taal- en technische misverstanden | Het experiment gebruikt losse synthetische afhandelingsrecords. Wie/wat een misverstand technisch kan vaststellen en hoe een retry gekoppeld wordt, is niet contractueel bewezen | Begrensde verduidelijkings-/retryflow die alleen de betreffende kwestie afhandelt, andere klachtmeldingen bewaart en een oude niet-medische fout niet permanent laat doorwerken | Product: welke verduidelijking of herstelbewijs voldoende is, zonder menselijke goedkeuringsdienst. Privacy/medisch: minimale gegevens en grens met werkelijke klacht | Voor/na-scenarios, subject-/revisiebinding, herhaalde retries, onbekende uitkomst, nieuwe klacht na afhandeling; geen opslag of echte gebruikers | Vertrouwde bewijsbron, servercontrole, idempotentie en foutgedrag; geen afhandeling door louter nieuwe R0, zelfrapportage, tijd, wissen of een handmatige approve-flag |
| Persoonlijke inhoud en hervatting | Toegestane persoonlijke inhoud per analyse en voorwaarden na zelfrapportage zijn niet af. Het vroegere aanvraagmodel is NIET gekozen | Expliciete inhouds-/hervattingsregels voor dag-, na-workout- en weekanalyse, met onderscheid tussen toegang, feiten, persoonlijk advies en uitvoering; begrijpelijke feedback zonder beoordelingswachtrij | Product: welke persoonlijke inhoud onder welke toestanden passend is. Medisch/juridisch: inhoudsgrenzen en consequenties na zelfrapportage; geen per-member menselijke goedkeuringsprocedure aannemen | Voorbeeldoutput en afkeurvoorbeelden, inhoudscontract, toestands-/revisietabel, nieuwe signalen en verschillende consent-/databeschikbaarheidssituaties | Beoordeelde inhouds-/herstelcriteria, contractueel juiste omgang met de bestaande 6D-gate, serverauth/consent en bewezen begrensde feitenbron; niet simpelweg oude blokkade verwijderen of R0 als vrijgave nemen |
| Ernstige, terugkerende en oningedeelde klachten | Criteria voor het vervolg na herstel ontbreken; handmatige casuslabels en voorlopige R3/R4 zijn geen medische onderbouwing | Toetsbare grenzen voor feedback en eventuele analysehervatting, inclusief herhaling en nieuwe meldingen; expliciet zichtbaar wat nog niet kan zonder fictieve dienst | Product: functioneel gedrag binnen D3/D4. Deskundig: benodigde actuele informatie, betekenis van ernstige/herhaalde/onbekende signalen en passende hulp-/herstelvoorwaarden; geen trainer als medische vrijgever | Open-criteriatabel, synthetische tijd-/revisie-/herhalingsscenarios, geen zelfgekozen medische drempel of automatisch herstel | Relevante medische/native/juridische beoordeling van de concrete criteria en teksten; nieuwe signalen krijgen een nieuwe beoordeling. Zorgverwijzing is geen app-aanvraag of goedkeuringsdienst |
| Doelgebonden retentie en ontbrekende gegevens | Doel/noodzakelijkheid, maximum en gevolgen van onopgeloste of verdwenen details zijn niet vastgesteld | Dataklassen-/doeltabel, minimale status, expliciete eind-/verwijderingsregels en gedrag bij ontbrekende context, zonder levenslange restblokkade of vrijgave door wissen | Product: doel en gedrag bij ontbrekende gegevens. Privacy/juridisch/medisch: noodzakelijkheid, maximum, verantwoordelijkheid en gevolgen; de D5-richting 30/90/180 per klasse wordt niet heropend als vrijbrief voor opslag | Synthetische tijdgrenzen en voor/na-voorbeelden met verdwenen details; geen echte opslag, cleanup, jobs of nieuwe gegevensverzameling | Goedgekeurd doelgebonden beleid, werkelijke autorisatie/verwijderings-/statussemantiek en controleerbare implementatie; unresolved niet alvast onbeperkt verzamelen |

## Productgrens: Geen Beoordelingsdienst

De owner heeft GEEN aparte menselijke aanvraag- of goedkeuringsprocedure voor
persoonlijke analyses geaccepteerd. Er bestaat geen beoordelingsdienst.
Aanvragen voorbereiden, doorsturen, een beoordelaar/wachtrij aanmaken of een
per-gebruiker goedkeuringsstap invoeren zijn daarom GEEN onderdeel van dit voorstel.
Ook het tegenovergestelde volgt niet: zelfrapportage geeft niet automatisch medische
vrijgave of toestemming voor onbegrensd persoonlijk advies.

Het toekomstige contract beschrijft productgedrag en toepasbare inhoudsregels.
Product-/deskundige beoordeling van DIE REGELS is niet hetzelfde als individuele
leden handmatig laten beoordelen door een nieuwe appdienst. Een zorgverwijzing
bij klachten blijft een hulpwijzer, geen verklaring dat een beoordeling is aangevraagd.
De bevroren experimentele velden/teksten met aanvraag-, review- of content-gate-taal
zijn uitsluitend historische bronartefacten en mogen niet stil als eisen worden overgenomen.

## Offline Pakketgrens En Oplevercriteria

Na afzonderlijke opdracht is de concrete oplevering:
1. Een versieerbaar context-/waarschuwingscontract plus vooraf vastgelegde NL/EN/DE-cases.
2. Een aparte verduidelijkings-/retrycontracttabel die niet-medische fouten afhandelt zonder veiligheidsinformatie te wissen.
3. Een inhouds-/hervattingstabel per analyse met expliciete open criteria, zonder menselijke aanvraagprocedure of automatische vrijgave.
4. Een matrix voor ernstige, terugkerende en oningedeelde klachten: bekende grenzen en exact nog te beoordelen inhoud.
5. Een doelgebonden retentie-/ontbrekende-data-contract met synthetische grensgevallen en expliciete open D5-details.

Technische contractchecks en inhoudelijke open punten worden afzonderlijk gerapporteerd.
Een testscore is geen medische nauwkeurigheid, deskundige goedkeuring of live gate.
Als inhoudelijke keuzes niet veilig kunnen worden ingevuld, worden die velden expliciet
open opgeleverd; een onafgemaakt herstelpad wordt niet als complete gebruikersflow verkocht.
De huidige opdracht wijzigt geen offline uitvoerbare bron en start geen van deze vijf outputs.

## Voor Elke Latere Live Integratie

Geen automatische vervolgstap vanuit een offline PASS of deze owneracceptatie.
Voor een concrete latere live opdracht moeten ten minste aantoonbaar aanwezig zijn:
- Afzonderlijk expliciet GO met exacte runtime-/adapter-/datagrens, stagingdoel en terugweg.
- Afgeronde relevante product-, medische, privacy-, juridische en moedertaalbeoordeling
  voor de werkelijk uit te rollen criteria, copy, gegevensverwerking en bereikbaarheid.
- Betrouwbare contextbron en gescheiden toegang, feiten, persoonlijke inhoud en uitvoering;
  bestaande auth, entitlements en toepasselijke consent blijven autoriteit.
- Bij facts-only weergave: toegestane bronnen, tijdvensters, units/plausibiliteit, ontbrekende
  data en veilige aansluiting op de frozen 6D-gate bewezen; geen vrije adviesvelden.
- Alleen noodzakelijk, goedgekeurd retentie-/statusgedrag; geen onbesliste opslag of
  automatische vrijgave door verloop, verwijdering, nieuwe chat of zelfrapportage.
- Vooraf passende regressie-/isolatie-/securitycriteria en een beperkte stagingverificatie.
  Geen geautoriseerde echte-member- of providerverwerking aannemen.
- Productie blijft verboden; reviewercontact, kosten en externe verwerking vergen hun
  eigen bevoegdheid en worden door dit voorstel niet gestart.

6E-0 is afgerond als offline voorbereiding. Phase 6E is ONVOLTOOID.
6E-1 is NIET GESTART. Aanbeveling is geen opdracht, freezeheropening of live toestemming.
