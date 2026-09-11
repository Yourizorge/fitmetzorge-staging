# Package 6E-5 Owneroverzicht

## Owneracceptatie 2026-09-11

COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE ONLY.
Alle drie onderstaande reviewpunten P1-P3 zijn expliciet geaccepteerd.
[Freeze receipt](PHASE6E5_FREEZE_RECEIPT.md). Geen live of medische vrijgave.
Onderstaande leveringsstatus is historisch, niet de actuele acceptatiestatus.

TECHNICAL PASS / READY FOR OWNER REVIEW - OFFLINE ONLY.
6E-4/V1/V2 is nu accepted/frozen. 6E-5 is NIET accepted/frozen of live vrijgegeven.
Hier staan concrete progressievoorstellen, niet opnieuw alleen "bekijk je schema".

## Concrete Uitkomst

ALLE cijfers en regels hieronder zijn synthetische TESTregels, geen echte
trainingsnorm, trainergrens, progressiegarantie of medische goedkeuring.

| Oefening | Werkelijke recente registratie | Bestaand schema | Voorstel volgende bronweek | Regelreden |
| --- | --- | --- | --- | --- |
| Squat | Twee voltooide trainingen, elk 2 x 8 met 55 kg | 2 x 8 met 55 kg | 2 x 9 met 55 kg | Alle vereiste targets gehaald, onder plafond 10; bronstap +1 rep |
| Roeien | Twee voltooide trainingen, elk 2 x 10 met 30 kg | 2 x 10 met 30 kg | 2 x 8 met 32,5 kg | Plafond 10 gehaald; bron noemt stap 30 naar 32,5 en reset naar 8 |
| Schouderdrukken | Twee voltooide trainingen, elk 2 x 7 met 20 kg | 2 x 8 met 20 kg | Bestaande 2 x 8 met 20 kg behouden | Doel niet overal gehaald; expliciete behoudregel. De werkelijke 7 wordt niet herschreven |

De echte gegenereerde NL-voorstelregels zijn:
- "Voorstel volgende week: 2 sets x 9 herhalingen met 55 kg. Keuze: herhalingen verhogen."
- "Voorstel volgende week: 2 sets x 8 herhalingen met 32,5 kg. Keuze: gewicht verhogen."
- "Voorstel volgende week: 2 sets x 8 herhalingen met 20 kg. Keuze: belasting behouden."

[Volledige NL/EN/DE-uitvoer](PHASE6E5_EXAMPLES.md) bevat alle 30 uitvoerbare
voorbeelden/tijdlijnen, inclusief afzonderlijke actuele setregistraties, bronnen,
regels en veiligheidsfeedback. [Gestructureerde uitvoer](PHASE6E5_EXAMPLES.json)
bewaart exact dezelfde engine-uitvoer, geen handgeschreven vervangende antwoorden.

## Bij Grenzen Of Goedkeuring

| Situatie | Uitgewerkt gedrag |
| --- | --- |
| Vereiste RIR ontbreekt | "De vereiste RIR ontbreekt." Geen nul invullen; andere geldige rijen mogen zichtbaar blijven, geen gezamenlijke schemawijziging |
| Betwist of expliciet conflicterend gegeven | Concrete beperking, ook wanneer een oudere registratie buiten de laatste N ligt maar binnen het meegeleverde venster |
| Onvoldoende trainingen | Geen voorstel voor die oefening; ontbrekend minimum volgens de TESTregel genoemd |
| Geen trainer | Ontbrekend apart FMZ-coachingsbeleid benoemd; geen standaardregels verzonnen |
| Actuele klacht of zelf gemeld herstel | Geen progressievoorstel; bestaande waarschuwing/contextgrens behouden. Chat/historie/feiten houden hun eigen rechten |
| Alleen lid accepteert | "Nog niet toegepast. Goedkeuring ontbreekt van: de bevoegde trainer." |
| Lid en trainer accepteren | Exacte versie approved, bestaand schema nog actief; daarna aparte expliciete trainersimulatie |
| Afwijzen | Bestaand schema blijft actief |
| Schema/bron/context inmiddels veranderd | needs_recheck; opnieuw berekenen en nieuwe goedkeuringen, oude niet kopieren |
| Dubbele of parallelle toepassing | Hoogstens eenmaal per actieve schemaversie in dezelfde offline simulatieomgeving |

Alleen de offline simulatie maakt een gewijzigde optie. Geen echt schema,
klantgegeven, toegang, timer of RIR/RPE-werking is aangepast.
De gesimuleerde planuitvoer is geen live-authoritatieve bron voor vervolgadvies.

## Alleen Nieuwe Productkeuzes

- P1: is deze concrete vorm bruikbaar: registratie + bestaand plan + volgende-week-
  reps/gewicht + exacte regelreden? Voorstel: behouden, inclusief het expliciete
  verschil tussen een lagere werkelijke prestatie en het ongewijzigde plandoel.
  De laatste N trainingen en getoonde testregelparameters zijn geen goedgekeurd
  echt coachingsbeleid; echte parameterkeuze vereist inhoudelijke beoordeling.
- P2: deze simulator vereist zowel lid als trainer, en daarna een aparte expliciete
  trainershandeling voor toepassing. Voorstel: dit duidelijke concept behouden.
  Verplichte trainerautoriteit staat al vast en wordt niet heropend; de extra
  bevestiging/bediening is de nieuwe productuitwerking, geen medische dienst.
- P3: bij een probleem in een oefening wel de andere onderbouwde rijen tonen,
  maar geen gedeeltelijke gezamenlijke schemawijziging laten toepassen.
  Voorstel: behouden; exact aangeven welke oefening/bron eerst ontbreekt.

Medische/trainingstechnische review van echte regels en hervatting blijft open,
net als privacy, juridische en NL/EN/DE-beoordeling. Geen ownerklik vervangt die.
Voor leden zonder trainer moet afzonderlijk beleid worden vastgesteld; nog niet
implementeren met de synthetische fixtures als standaard.
Geen automatische owneracceptatie/freeze van 6E-5 en geen volgend pakket starten.
[Contract](PHASE6E5_CONTRACTS.md) en [technisch rapport](PHASE6E5_TECHNICAL_REPORT.md).
