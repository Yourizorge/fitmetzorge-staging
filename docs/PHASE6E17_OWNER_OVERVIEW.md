# 6E-17 Ownerreview

Demo: https://yourizorge.github.io/fitmetzorge-staging/nutrition-rules-demo/

Alleen fictieve voedingsgegevens, geen persoonlijk voedingsadvies. Verversen
reset de demo. 6E-16 is nu accepted/frozen;6E-17 nog niet.

## Wat werkt

De demo gebruikt een bestaand fictief calorie-/macrodoel. Een ontbrekend doel wordt
niet berekend of verzonnen. Bronvelden tonen afzonderlijk bekend, niet van
toepassing en ontbrekend. Ontbrekende verplichte gegevens blokkeren een voorstel.

De maaltijden tonen bron-grammen, calorieen/macro's, vervangingen, allergenencontrole,
optelsommen en het verschil met het bestaande doel. Je kunt maaltijden/producten,
porties, eetmomenten en voorkeuren wijzigen. Elke wijziging wordt opnieuw getoetst.
Bevestigen en activeren blijven apart; herstel maakt een nieuwe versie.

Voorbeeld: bestaand doel1800kcal, berekend plan1725kcal, zichtbaar verschil-75kcal.
Het plan wordt niet stiekem groter gemaakt en het doel wordt niet veranderd.
Alle getallen en producten zijn conceptuele testdata, niet deskundig gevalideerd.

Exacte demoantwoorden:

- NL: "Doel blijft 1800 kcal. Berekend plan: 1725 kcal. Verschil: -75 kcal."
- EN: "Target remains 1800 kcal. Calculated plan: 1725 kcal. Difference: -75 kcal."
- DE: "Ziel bleibt 1800 kcal. Berechneter Plan: 1725 kcal. Differenz: -75 kcal."

Alle60 concrete scenarioantwoorden met brongegevens en plannen staan in
PHASE6E17_EXAMPLES.json. Ze komen uit de uitvoerbare beslislogica.

## Nieuwe reviewpunten

- **17-R1 Bronnen en doelen:** voorstel is de duidelijke bronstatus en het gebruik
  van een bestaand doel te accepteren als productstructuur. Zonder goedgekeurde
  berekeningsregel komt geen zelfbedacht calorie-/macrodoel.
- **17-R2 Bewerken en blokkeren:** voorstel is de zichtbare allergenen-/uitsluitings-
  controle, vervangingen en gehele-plancontrole na bewerkingen te accepteren.
  Ontbrekende waarden en medische beperkingen blijven blokkeren.
- **17-R3 Rekenen en versies:** voorstel is exacte optelsommen en doelverschillen,
  bronbehoud, aparte bevestiging/activering en herstel als nieuwe versie te behouden.

Dit vraagt geen voedingskundige goedkeuring van de fictieve cijfers. Eerdere
besluiten worden niet heropend. Medische, voedingskundige, privacy-, juridische
en taalbeoordelingen voor later werkelijk gebruik blijven afzonderlijk open.

## Korte telefoontest

1. Open de demo en druk **Start begeleide test**. Het resultaat komt direct in beeld.
2. Gebruik **Volgende stap** voor alle20 situaties. Een terechte blokkade hoort PASS
   te tonen; er mag dan geen nieuw plan worden geactiveerd.
3. Controleer vooral5/6 (allergie/andere naam),9/10 (portie),11 (optelsommen),14-16
   (bronnen/versies) en17/18 (klacht/toestemming). Probeer ook EN/DE en donker thema.
4. Meld17-R1 t/m17-R3 akkoord of noem het stapnummer en de afwijking.

Route A en de echte voedingsmodule zijn niet veranderd. Geen18 gestart.
6E-11 hosted blijft SUPPORT HOLD SU-487979.
