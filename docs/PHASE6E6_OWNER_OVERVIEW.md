# Package 6E-6 Owneroverzicht

## Owneracceptatie W1/W2 (2026-09-11)

COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE ONLY.
[Freeze receipt](PHASE6E6_FREEZE_RECEIPT.md). Onderstaande leveringsstatus is historisch.
Geen live/medische vrijgave. Het W2-weergavedetail bij blokkade en andere resterende
integratiepunten staan expliciet in de [Remaining Work Audit](PHASE6E_REMAINING_WORK_AUDIT.md).

TECHNICAL PASS / READY FOR OWNER REVIEW - OFFLINE ONLY.
6E-5/P1-P3 is expliciet accepted/frozen; 6E-6-resultaten nog niet.
Alle cijfers hieronder zijn synthetische TEST-trainerregels, geen algemeen
trainingsadvies, medische norm of impliciet FitMetZorge-coachingsbeleid.

## Wat Nu Echt Werkt

| Oefening | Bestaand plan | Werkelijk geregistreerd | Volgende-weekconcept | Controleerbare reden |
| --- | --- | --- | --- | --- |
| Squat | 2 x 8, 55 kg | Beide sets in beide brontrainingen 8, 55 kg; RIR 1/RPE 8 | 2 x 9, 55 kg | Expliciete regel: doel gehaald, onder plafond 10, reps-stap 1 |
| Roeien | 2 x 10, 30 kg | Beide sets in beide brontrainingen 10, 30 kg; RIR 1/RPE 8 | 2 x 8, 32,5 kg | Expliciete regel: plafond 10 gehaald, gewichtsstap 2,5 en reset 8 |
| Schouderdrukken | 2 x 8, 20 kg | Beide sets in beide brontrainingen 7, 20 kg; RIR 1/RPE 8 | Bestaand doel 2 x 8, 20 kg behouden | Doel niet in alle vereiste sets gehaald; expliciete behoudregel |

Dit verklaart brongetallen, niet wat een echt lid fysiek aankan.
RIR en RPE blijven onafhankelijke zelfrapportages; leeg wordt nooit nul.
Iedere oefening toont de oorspronkelijke trainerregel en zijn oefening/typebinding,
minimum/maximumreps, setcount, reps-stap en gewichtsstap.

## Exacte Conceptantwoorden

Onderstaande zinnen komen rechtstreeks uit de uitvoerbare normale voorbeelden.
De volledige antwoorden, inclusief feiten, regels, grenzen en statussen:
[30 gegenereerde NL/EN/DE-scenario's](PHASE6E6_EXAMPLES.md);
[exacte machine-uitvoer](PHASE6E6_EXAMPLES.json).

| Taal | Exact Nederlands of overeenkomstig uitvoerbaar concept |
| --- | --- |
| NL, reps | Voorstel volgende week: 2 sets x 9 herhalingen met 55 kg. Keuze: herhalingen verhogen. |
| NL, gewicht | Voorstel volgende week: 2 sets x 8 herhalingen met 32,5 kg. Keuze: gewicht verhogen. |
| NL, behoud | Voorstel volgende week: 2 sets x 8 herhalingen met 20 kg. Keuze: belasting behouden. |

Exact bij geen trainer:
"Geen wijzigingsvoorstel: een geldige gekoppelde trainer ontbreekt; trainergoedkeuring
is niet beschikbaar. Betrouwbaar gekoppelde registraties blijven als feiten beschikbaar."
(Alleen de afbreking hierboven is documentopmaak; de uitvoer is een aaneengesloten zin.)

Exacte nieuwe statuszin:
"Wacht op afzonderlijke lidbevestiging en trainergoedkeuring; daarna is nog expliciete toepassing nodig."

De EN/DE-teksten worden volledig door dezelfde implementatie gegenereerd, niet
achteraf als losse vertaling toegevoegd. Alle 30 scenario's zijn deterministisch getest.
Duitse ASCII-transliteratie blijft een taalreviewpunt.

## Wat Kan Wel En Niet

Lidbevestiging, trainergoedkeuring en toepassing hebben elk een eigen zichtbare status.
Zelfs na beide bevestigingen blijft het bestaande schema actief tot aparte trainer-apply.
Afwijzen, onvolledige informatie, actuele klachten, onvoldoende herstelcontext,
ingetrokken grenzen of een versieconflict geven geen toepassing. Geen gedeeltelijke writes.
Zonder trainer of geschikte regel: alleen betrouwbare historische feiten/uitleg.

De testsimulator bewaart bij toepassing het vorige volledige schema, bronversies
en auditketen. Een storing voor commit verandert niets; opnieuw proberen voert
hoogstens eenmaal uit. Dit is GEEN echte database-/serverimplementatie.
Chat, historie, feiten en niet-fysieke reflectie houden hun bestaande regels.
O5, herstelmeldingen en ontbrekende bronnen geven geen medische vrijgave.

## Alleen Nieuwe Reviewpunten

**W1 - Meerdere passende trainerregels.**
Voorstel: bij een oefeningregel EN een passende typeregel niet zelf kiezen;
geen voorstel totdat de trainerbron een eenduidige passende regel levert.
Reden: verborgen voorrang zou de expliciete trainerbedoeling kunnen veranderen.
Dit heropent niet de al geaccepteerde trainergoedkeuring of P1-P3.

**W2 - Een exacte stap past niet.**
Voorstel: geen eigen kleinere stap, afronding of automatisch behoud als de
opgegeven reps-/gewichtsstap niet past. Toon de betrouwbare feiten en benoem
het concrete regelconflict. Behoud als progressie-uitkomst blijft uitsluitend
de expliciete behoudregel bij niet-gehaalde targets/effortvoorwaarden.
Reden: ontbrekende of tegenstrijdige regels zijn iets anders dan een geldige behoudkeuze.

De concrete uitvoer, regelherkomst en nieuwe foutteksten zijn onderdeel van deze
resultaatreview. Er wordt niet gevraagd de synthetische getallen tot echte
standaardnormen te verheffen. Geen nieuwe keuze over automatische acties:
die blijven uit, zoals al geaccepteerd.

## Nog Open Voor Latere Live Inzet

Deskundige beoordeling van echte trainingsregels, inhoud en hervattingscriteria;
privacy/juridische grondslag, consent en doelgebonden audit-/voorstelretentie;
NL/EN/DE-tekst en interpretatiereview; authentieke trainer-/bron-/intrekkingscontrole;
duurzame atomaire toepassing en restart/concurrency-idempotency.
Geen deskundigen benaderd of fictieve beoordelingsdienst toegevoegd.

Bekende taalbeperking blijft open, niet als herkenningssucces geteld.
6E-0..6E-5 en D1-D12/O1-O5 blijven behouden. Training-owneracceptatie blijft intact.
Phase 6E is ONVOLTOOID. Geen live AI, automatische freeze of vervolgstart.
