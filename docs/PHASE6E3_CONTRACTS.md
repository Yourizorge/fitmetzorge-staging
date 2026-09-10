# Package 6E-3 Historisch Doel- En Setcontract

TECHNICAL PASS / READY FOR OWNER REVIEW. Offline uitvoerings-GO ontvangen op 2026-09-10.
Geen owneracceptatie/freeze van 6E-3, geen live AI-vrijgave of vervolgstart.
6E-0/6E-1/6E-2 blijven frozen; D1-D12, O1-O5 en N1-N3 behouden.

## Minimaal Broncontract

Alle IDs zijn synthetisch (syn-...), tijden geinjecteerde UTC-milliseconden.
Invoer: synthetic_only, locale, exacte frozen contextbinding en sources.
De doelversie moet zijn vastgelegd uiterlijk op het tijdstip van de historische koppeling.
Onbekende extra velden, echte UUIDs, verkeerde eigenaars, dubbele IDs of ongeldige
typen worden afgewezen. Geen provider, netwerk, systeemklok, storage of live adapter.

| Bron | Vereiste identiteit en inhoud | Afbakening |
| --- | --- | --- |
| session | Eigen ID, eigenaar, start/einde, gevraagde snapshot- en recording-ID/revisie | De geselecteerde versie is expliciet; dit is een synthetisch readset, geen serverattestatie |
| snapshot | Historische snapshot-ID/revisie, eigenaar/sessie, capturetijd niet na start, plan-ID/revisie, oefeningen en geordende geplande sets | Geen huidig plan als fallback. Alleen het historische pakket mag geplande waarden leveren |
| goal_link en goal | Expliciete toenmalige memberkoppeling voor DEZE workout, exacte doel-ID/revisie, capturetijd, actieve status en geldigheid bij start | Geen verband afleiden uit gewicht, reps of een huidig profiel. Het actuele live schema heeft deze historische doelbinding niet aantoonbaar als broncontract |
| catalog | Exacte oefenings-ID en vastgelegde catalogusrevisie, NL/EN/DE-labels | Onbekende identiteit/revisie wordt niet met een gelijkende naam vervangen |
| recording | Eigen ID/revisie, sessie/snapshotbinding, registratietijd, dekking en unieke log-ID per oefening/setindex | De combinatie snapshot/oefening/index koppelt een set, nooit alleen lijstpositie |
| set | Gestructureerd reps-bereik min/max bij planning; werkelijk geregistreerde reps; afzonderlijke load.value/unit, RIR en RPE | null is ontbrekend, niet nul. Geen ranges raden uit vrije tekst. Scores zijn zelfrapportage |

RIR: bestaande invoervorm integer 0..10; RPE: 1..10 in stappen van 0.5.
Dit zijn overgenomen registratievormen, geen medische normen. Nieuwe technische
array-/getalgrenzen beschermen de invoer, niet iemands belastbaarheid.
Het ene workoutvenster blijft binnen het frozen 6E-1-formaat van maximaal 24 uur;
dit is een adaptergrens, geen aanbevolen trainingsduur.

## Uitvoerbare Beslissingen

- Een complete, exact gekoppelde registratie plus een geldig toenmalig doel geeft
  een niet-fysiek reflectievoorstel. Alle zeven bestaande doelcodes kunnen alleen
  met dezelfde expliciete workoutbinding worden benoemd; geen causaliteitsclaim.
- Planned versus actual gebruikt exacte sets en catalogusidentiteit. Reps worden
  onder/binnen/boven het vastgelegde bereik geplaatst als rekenfeit, niet als
  prestatie-, veiligheids- of belastbaarheidsoordeel. Gewicht wordt niet verhoogd.
- Alleen eenduidige kg-waarden worden vergeleken. lb, plates, null of gemengde
  eenheden worden niet omgerekend of als kg gepresenteerd.
- Bij gedeeltelijke registratie blijven bruikbare setfeiten zichtbaar, maar volgt
  geen compleet reflectievoorstel. Ook een onterechte complete-dekkingclaim wordt
  niet geloofd wanneer geplande sets ontbreken. Geen ontbrekende set wordt nul.
- Als een doel ontbreekt, later is gewijzigd, nog niet actief was, al was vervallen
  bij start of niet expliciet was gekoppeld: setfeiten kunnen blijven, doelreflectie niet.
- Een later schema/revisie vervangt de oorspronkelijke snapshot nooit. Een historische
  bron wordt niet onbruikbaar door leeftijd alleen: er is geen verzonnen houdbaarheidstermijn.
- Onjuiste persoon-/sessie-/setbinding wijst de bronbundel af zonder setinhoud te tonen.
  Dit verwijdert geen chat, historie of andere veiligheidsmeldingen.

## Frozen Veiligheid Read-Only

prepare is de ongewijzigde 6E-2 prepare-functie: immutable issued context, event-lineage,
bericht-/revisiebinding, superseded-contextafwijzing en bestaande O5-projectie.
reflect gebruikt de frozen workout-aanvraag met een waarheidsgetrouwe LEGE
metriclijst en het echte synthetische sessievenster als contextprobe. Er worden
geen aggregaten verzonnen om oude datavoorwaarden groen te maken.
Alleen de bestaande toegang/context/waarschuwingen worden hergebruikt; de nieuwe
setgegevens hebben bovenstaande eigen validators. De gepinde adapter controleert
de verwachte outputvorm en scope; onbekende veiligheidsoutput wordt afgewezen.

De bestaande frozen feedback staat voor de nieuwe feiten/reflectie. Actuele
klachten, ook ernstige/oningedeelde/terugkerende, houden reflectie tegen.
Misverstand of technische fout: optionele verduidelijking/retry EN verder chatten.
Gebonden zelfrapportage laat hoogstens niet-fysieke reflectie terugkomen zonder
resterende actuele melding; ernstige herstelcriteria blijven expliciet open.
Een nieuwe melding wordt opnieuw beoordeeld. Geen medische vrijgave.

O5 blijft exact maximaal 30 dagen vanaf EERSTE registratie, eerder indien onnodig.
Herhalen, retry en statuswisseling verlengen niet. Verlopen/ontbrekende inhoud
wordt niet gereconstrueerd. Nieuwe duidelijke gewone context kan beperkte reflectie
dragen, zonder andere meldingen te wissen of een algemene toegangssperre te maken.
Chat, historie, feiten, reflectie en automatische uitvoering blijven afzonderlijk.
Zonder chatconsent geen waarschuwing-/klachtinhoud uit private context; eigen feiten
hebben hun afzonderlijke bestaande analyse-rechten. Automatische acties altijd UIT.

## Wat Dit Niet Bewijst

Synthetische identifiers, verklaringen over versies/capturetijd, cataloguslabels en
doelkoppelingen zijn geen cryptografisch, medisch of live backendbewijs. De validators
kunnen niet bewijzen dat een bronleverancier liegt over een samenhangende bronbundel.
Voor live zijn betrouwbare bronattestatie, historische snapshots en hun daadwerkelijke
beschikbaarheid, auth/consent, deletion/retentie, herstart/concurrency en aparte GO nodig.
Geen nieuwe bewaarpayload voor ruwe safety-history, bindings of testresultaten.

De beperkte frozen tekstregels herkennen niet iedere normale formulering.
"Ik bekijk mijn trainingsregistratie" blijft communicatie-onzekerheid zonder
gezondheidswaarschuwing. Dat is een beperkingobservatie, GEEN geslaagde herkenning.
De eerdere drie gezondheidsherkenningsgaten blijven hersteld; geen classifieruitbreiding.
NL/EN/DE-copy (DE voorlopig ASCII-transliteratie), medische inhoud/hervatting,
privacy, juridische claims en taalinterpretatie blijven deskundige reviewpunten.
Geen trainergrenzen, voedingsnormen of medische hervattingscriteria toegevoegd.

Zie [ownerreview](PHASE6E3_OWNER_OVERVIEW.md), [technisch rapport](PHASE6E3_TECHNICAL_REPORT.md)
en [preregistratie](PHASE6E3_PREREGISTRATION.md).
