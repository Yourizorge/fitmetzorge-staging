# 6E-15 Ownerreview
**TECHNICAL PASS / READY FOR OWNER REVIEW. Nog niet accepted/frozen.**
[Demo](https://yourizorge.github.io/fitmetzorge-staging/independent-intake-demo/).
Geen login; alleen fictieve gegevens in geheugen. Verversen reset alles.

## Resultaat
Vul doelen, ervaring, dagen, duur, locatie/materiaal, voorkeuren/uitsluitingen,
eenheden, voeding/allergieen, dagritme, registraties, klachten en toestemming in.
Onbekend is geen ingevuld antwoord. Een expliciet lege lijst betekent geen.
Een volledige ondersteunde intake levert een bewerkbare week, maaltijdsjabloon
en herstel/check-inplanning met versiegebonden bronregels.

Voorbeeld: kracht, beginner, ma/wo/vr,30 minuten, mat/dumbbell/elastiek,
favoriet roeien, plantaardig. De bestaande bron geeft2 sets,8 reps,90sec rust,
geen verzonnen startgewicht. Maaltijden komen uit vaste fictieve porties.
Deze waarden zijn geen gevalideerd persoonlijk advies of caloriebehoefte.
Exacte NL/EN/DE-conceptteksten en gegenereerde voorbeeldplannen:
PHASE6E15_EXAMPLES.json.

## Alleen Nieuwe Reviewpunten
- **Q1 - Intake en ontbrekende regels:** akkoord met expliciet bekend/geen/onbekend,
  afzonderlijk minder-leuk versus uitgesloten, broncontrole en weigeren bij een
  ontbrekende apparaat-/dieetregel of te kleine catalogus? Voorstel: behouden.
- **Q2 - Bewerkbare catalogusgrenzen:** akkoord met geschikte oefening/maaltijd/
  productalternatieven, reps binnen de bestaande grens en vaste sets per ervaring?
  Voorstel: behouden. Een vrij aantal sets wordt NU niet ondersteund; het invoerveld
  weigert een niet-passende waarde. Een ruimere regel vergt latere aparte goedkeuring.
  kg/lb geldt voor trainingsgewichten; voedingsporties blijven bron-grammen.
- **Q3 - Nieuwe intake en planversies:** akkoord met nieuwe beoordeling na elke
  intakewijziging, aparte bevestiging/activering, idempotentie en terugzetten als
  nieuwe versie onder actuele uitsluitingen? Voorstel: behouden.

Eerdere besluiten en Route A blijven frozen. Dit is geen verzoek tot live release,
nieuwe medische norm of expertgoedkeuring.6E-11 blijft hosted op SUPPORT HOLD.

## Telefoontest
1. Open Volledige intake. Bekijk de vier intakegroepen en kies Voorstel maken.
2. Vervang een oefening, pas reps aan, beoordeel de bewerking. Test ook een
   niet-toegestaan aantal sets: foutmelding, geen gedeeltelijke wijziging.
3. Vervang een maaltijd/product. Controleer bronvermelding en de allergievariant.
4. Kies Voorstel bevestigen, test dubbel bevestigen en daarna Afzonderlijk activeren.
   Dubbel activeren mag geen extra versie maken.
5. Maak/beoordeel een aangepast voorstel en activeer versie2. Vorige versie
   voorstellen, opnieuw bevestigen/activeren: versie3, historie blijft.
6. Wijzig dagen of kg/lb via Intake bewaren; oud voorstel verdwijnt, oude actieve
   versie blijft tot een nieuwe activering. Test ontbrekende intake, klacht,
   bronconflict en ingetrokken toestemming.
7. Test NL/EN/DE, licht/donker en verversen. Alle fysieke controles nog open.

Meld Q1-Q3 akkoord of de precieze afwijking. Expertbeoordeling van medische,
voedings-, privacy-, juridische en taalinhoud blijft apart en open.
