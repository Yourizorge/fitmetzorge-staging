# 6E-12 Gebundelde Ownerreview
Status: OFFLINE PRODUCTCONCEPT / GEEN OWNERACCEPTATIE OF FREEZE.
SU-487979 blijft de hosted 6E-11-keten blokkeren. Deze demo is geen servervenster.

## Wat Werkt
Nieuwe synthetische workoutregistratie op een historische snapshot, expliciete
reflectie, actuele versiegebonden trainerregels en afzonderlijke lidacceptatie,
trainergoedkeuring en toepassing. Een correctie bewaart de vorige registratie.
Terugzetten maakt een nieuw voorstel, nieuwe goedkeuringen en een nieuwe schemaversie.
Alleen simulatie in geheugen; geen echte accounts, writes, AI of opslag.

## Exacte Voorbeelden
De uitvoering gebruikt twee vergelijkbare synthetische sessies en vastgelegde
trainerregels. Dit zijn voorbeelden, geen algemene trainingsnormen.

| Taal | Oefening | Huidig doel / geregistreerd | Voorstel | Exacte korte reden |
| --- | --- | --- | --- | --- |
| NL | Squat | 2 x 8 op 55 kg / alle sets 8 | 2 x 9 op 55 kg | Alle vereiste geregistreerde sets halen het vastgelegde doel; het reps-plafond is nog niet bereikt. |
| NL | Roeien | 2 x 10 op 30 kg / alle sets 10 | 2 x 8 op 32,5 kg | Alle vereiste geregistreerde sets halen het reps-plafond; de testregel noemt de volgende beschikbare gewichtsstap. |
| NL | Schouderdrukken | 2 x 8 op 20 kg / geregistreerd 7 | 2 x 8 op 20 kg behouden | Het setdoel of een expliciete RIR/RPE-testvoorwaarde is niet in alle vereiste sets gehaald; de vastgelegde behoudregel geldt. |

De volledige exacte NL/EN/DE-antwoorden zijn uitvoerbaar in de demo onder
Exact antwoord en bronverwijzingen. Elke regel verwijst naar bron- en regelversies.
De gegenereerde data bevat 18 voorbeelden in elk van de drie talen.

W2, exact NL: "De lijst met brongewichten past niet bij de ingestelde stap.
Geen afronding, kleinere stap of alternatief reps-voorstel."
De concrete ingestelde stap (2,5 kg) en brongewichten staan erbij.

Onbekende demo-invoer, exact NL: "Deze invoer is niet vooraf doorgerekend:
alleen feiten, geen wijzigingsvoorstel."
De Node-bronvalidator kan zelfstandig gewijzigde synthetische registraties
berekenen. De publieke browserdemo doet dit bewust niet voor willekeurige invoer.

## Een Review, Drie Punten
| Punt | Voorstel dat nu werkt | Wat beoordelen |
| --- | --- | --- |
| P1 | Registratie vastleggen en daarna apart Workoutreflectie maken | Zijn bron, werkelijk geregistreerd resultaat, volgende voorstel en reden begrijpelijk? |
| P2 | Correctie maakt een nieuwe registratieversie en bewaart de historische snapshot | Is duidelijk welke registratie en oorspronkelijke opdracht zijn gebruikt? |
| P3 | Nieuwe bron/registratie maakt oude beoordeling onbruikbaar; opnieuw afzonderlijk beoordelen | Zijn de blokkade, aparte toestemming en aparte toepassing duidelijk? |

Na toepassing vereist een volgende echte cyclus een nieuw geldig plan- en
trainerbroncontract. De geheugendemo start daarvoor expliciet opnieuw; zij
verzint geen opvolgende trainerbevoegdheid. Dat is een beperking, geen stilzwijgende
automatische vrijgave.

## Korte Test
1. Kies NL en het voorbeeld Reps, gewicht en behouden.
2. Registratie vastleggen, dan Workoutreflectie maken.
3. Controleer plan, geregistreerde sets en voorstel. Open het exacte antwoord.
4. Als fictief lid: Accepteren. Als fictieve trainer: Goedkeuren.
5. Controleer dat versie 3 blijft staan tot Wijziging toepassen. Daarna versie 4.
6. Terugzetten voorstellen, opnieuw lidacceptatie en trainergoedkeuring, apart
   toepassen: nieuwe versie 5; versies 3 en 4 blijven in historie.
7. Nieuwe demo; kies W2, ontbrekende set of actuele klacht. Geen toepasbaar voorstel.
8. Wijzig een invoerwaarde naar een niet doorgerekend voorbeeld: alleen feiten.
9. Test EN/DE en donker. Verversen reset uitsluitend deze synthetische demo.

Geen login nodig; rolkeuze is geen echte authenticatie. De fysieke ownertest
staat open. Alle uitgevoerde mobiele controles zijn emulatie, geen echte telefoon.
D1-D12, O1-O5 en overige frozen besluiten blijven behouden. Medische, privacy-,
juridische en taalbeoordeling voor echte inzet blijven afzonderlijke voorwaarden.
