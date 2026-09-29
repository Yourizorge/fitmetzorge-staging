# 6E-12 Afhankelijkheden En Vooraf Vastgelegde Cases
De nieuwste owner-GO vervangt uitsluitend het eerdere uitstel van onafhankelijke
6E-12-offlinebouw. SU-487979 blokkeert het hosted deel van 6E-11 nog steeds.
Geen acceptatie of freeze afgeleid.

| Onafhankelijk: nu bouwen | Afhankelijk: nog geblokkeerd |
| --- | --- |
| Strikte synthetische bronvalidators en immutable workoutversies | Echte Auth/sessie/requestbinding |
| Frozen trainerregels read-only gebruiken voor reps/gewicht/behouden | Database-, Edge- en appintegratie |
| Historische snapshot/doelkoppeling, geen reconstructie | RLS, hosted writesets, cleanup en transportbewijs |
| Simulatie aparte goedkeuring/toepassing/rollback | Server-side tijdelijk ownervenster |
| NL/EN/DE, mobiel/desktop, licht/donker, bronvergelijking | Fysieke owneracceptatie van de hosted flow |
| Afzonderlijke geheugendemo en uitsluitend nieuwe bestanden pushen | Geen secretreset/JIT/poolerproef tijdens hold |

P1-P3 zijn ontwikkelvoorstellen: expliciet reflectiemoment, nieuwe onveranderlijke
registratie bij correctie, nieuwe review bij gewijzigde bronnen. Geen nieuwe medische
norm, trainergrens, voedingswijziging of automatische actie.

## Preregistratie Voor Implementatie
Positief: normale drie oefeningen met reps verhogen, volledige gewichtsstap en
behouden; kg/kg, lb/lb; typegebonden regel; RIR 0; optioneel leeg; nieuwe registratie
en correctie zonder oude snapshot te veranderen; alle drie talen.
Negatief: vreemde gebruiker/workspace/sessie/snapshot/oefening/set, dubbele set,
onbekende velden, ontbrekende reps/load, verkeerde eenheid, RPE 0, ontbrekende regel,
W1 ambiguiteit, W2 niet-passende stap, geen trainer, intrekking, onvolledige data,
oude plan-/goal-/regelversie, bronverandering na goedkeuring, actuele/onbeoordeelde
klacht, zelfrapportage en O5-verloop zonder medische vrijgave.
Workflow: geen traineractie voor lidacceptatie; apart toepassen; afwijzen/blokkeren;
exacte dubbele request en payloadconflict; stale command; fout voor commit zonder
gedeeltelijke wijziging; terugzetten als nieuw voorstel en nieuwe versie.
UI: 320/390/768/1280 px x NL/EN/DE x licht/donker; geen horizontale overflow;
invoerbehoud, taalwissel, refreshreset, audit/historie, geen opslag of externe requests.
Preserve: alle bestaande bestanden, migrations 41-42, frozen 6E-0..10 en 6E-11-bewijs.
Geen gesimuleerd resultaat als hosted security-PASS tellen.
