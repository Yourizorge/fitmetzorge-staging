# Package 6E-4 Voorstel: Trainerbegrensde Workoutkandidaten

PROPOSED / NOT STARTED. Dit is het ENIGE aanbevolen volgende offline AI-pakket.
Geen uitvoerings-GO, owneracceptatie, freeze of live-vrijgave voor 6E-4.
6E-3/G1-G3 en 6E-0/6E-1/6E-2 blijven frozen; D1-D12/O1-O5/N1-N3 niet heropenen.

## Resultaat En Stap Richting Trainingsadvies

Bouw na afzonderlijke GO een uitvoerbaar offline contract dat een persoonlijke
workoutkandidaat uit een bestaand, aantoonbaar bevoegd trainerschema onderbouwt.
Het gaat om een reeds expliciet aangewezen volgende workout/optie, niet om AI
die zelf een volgend gewicht, extra volume of oefeningswissel bedenkt.
Historische doel-/setreflectie uit 6E-3 blijft read-only; de nieuwe kandidaat
gebruikt apart de actuele, geldige doel-, plan- en trainergrensversie.
Een latere versie mag nooit de oorspronkelijke opdracht van een oude sessie worden.

Concreet productconcept, nog NIET uitvoerbaar of deskundig goedgekeurd:
"Bekijk workout A, de vastgelegde volgende optie in je trainerschema voor sterker
worden. Bij squat staat 1 set van 8 herhalingen met 55 kg. Die optie valt binnen
de expliciet vastgelegde trainergrenzen. Ik wijzig je schema niet en geef hiermee
geen oordeel over of je nu kunt trainen."
Alle namen, cijfers en de aangewezen volgorde moeten uit de synthetische bron komen.
Dit voorbeeld is geen echte trainergrens, trainingsopdracht of medische beoordeling.

Nieuwe uitvoer: candidate_only met exacte bron-/grensverwijzingen, beschikbaarheid,
concrete reden en ontbrekende gegevens. automatic_actions_allowed=false en
physical_advice_authorized=false. Ook zonder herkend actueel signaal is
trainingsgeschiktheid niet bewezen. Een passende grens maakt fysiek advies niet
automatisch medisch geschikt. Fysieke voorschriften wachten op afzonderlijke
inhouds-/hervattingscriteria en product-/deskundige besluiten.

Dit is de eerstvolgende noodzakelijke stap: van terugkijken naar een controleerbaar
persoonlijk voorstel uit bestaand voorschrift. Niet opnieuw alleen een algemene audit,
niet meteen vrije progressiecoaching. Lever validators, beslislogica, exacte
NL/EN/DE-concepten en vooraf vastgelegde synthetische toegestane/geweigerde gevallen
in een NIEUWE offline map; geen huidige frozen bron wijzigen of live adapter bouwen.

## Minimale Bronnen En Trainergrenzen

| Onderdeel | Bestaande basis | Nieuw te leveren offline contract / ontbrekend live bewijs |
| --- | --- | --- |
| Historie | 6E-3 historische workout, doelbinding, catalogus en settuples | Read-only hergebruik; oude opdracht blijft los van nieuwe actuele kandidaat. Nooit een huidig doel als historische fallback |
| Actuele doel- en planversie | progress_goals en training_plans/days/exercises bestaan in de domeinarchitectuur | Eigenaar, ID/revisie, status, bron/capturetijd, geldigheid en expliciete doelbinding aan deze actuele workout. Beschikbare opslag is nog geen toegestane AI-readset |
| Bronautoriteit | Bestaande eigen-user routes en sessiesnapshots; 6E-3 heeft alleen synthetische verklaringen | Een intern consistente synthetische readset met verwachte revisies en herkomst. Live later server-auth, toegestane velden, betrouwbare versie-/capturebewijzen en intrekking; coherent vervalste verklaringen zijn offline niet te ontmaskeren |
| Trainergezag | profiles.trainer_id / legacy coach_workspaces tonen hoogstens een relatie | Expliciete auteur, bevoegde trainer/relatie, member, plan/workout/oefening/setscope, revisie, begin/eindgeldigheid, intrekking en toestemming voor dit doel. Geen private chat delen |
| Voorgeschreven optie | Bestaande setdoelen zijn nog geen trainerautorisatie voor een AI-aanbeveling | Expliciet aangewezen volgende optie plus exact toegestane sets, reps-bereik en load/unit; toepasselijke verboden of uitgesloten opties. Ontbrekende grens is unknown, niet onbeperkt |
| Conflicten | Trainerprioriteit is architectuurbeleid, geen ingevulde grens | Alle toepasselijke verboden gelden; conflicterende versies/gezag/opties geven geen kandidaat. Geen eigen "strengste waarde" uit onvergelijkbare grenzen afleiden. Geen AI-override of nieuwe menselijke aanvraagdienst |

Geen kandidaat wanneer bron, bevoegdheid, doelbinding of een vereiste toepasselijke
grens ontbreekt, verlopen, ingetrokken, tegenstrijdig of verkeerd gekoppeld is.
Bij meerdere toegestane opties zonder expliciete volgende keuze geen optimale
training raden; optioneel verduidelijken EN verder chatten. Een member zonder
bewezen trainergrenzen houdt bestaande chat/historie/feiten en niet-fysieke reflectie;
deze smalle kandidaatfunctie verzint dan geen vervangend zelfstandig trainingsbeleid.
Geen nieuwe wachtrij, trainerportaal, automatische trainerdeling of beoordelingsdienst.

## lb En Taalbeperking: Expliciet In De Volgorde

1. Eerst het bron-/trainercontract en kg-kandidaten tegen synthetische grenzen bewijzen.
2. In hetzelfde voorgestelde pakket een AFZONDERLIJKE unitadapter voor expliciete kg/lb
   plannen, zonder 6E-3 te herschrijven. Begin met vergelijkingen binnen dezelfde eenheid.
   Bewaar oorspronkelijke waarde/eenheid en herkomst; kg en lb niet mengen of gokken.
   Cross-unit berekening alleen na vastgelegde conversieautoriteit en afrondingsbeleid.
   Geen aanbevolen gewicht afronden naar een apparaatstap zonder expliciete bron.
   Onbekende plates/bodyweight blijven expliciet buiten deze kg/lb-uitbreiding.
3. Gericht vervolg op EXACT "Ik bekijk mijn trainingsregistratie", nu nog communicatie-
   onzekerheid zonder gezondheidsalarm. Leg voor een afzonderlijke 6E-4-contextadapter
   vooraf normale NL/EN/DE-parafrases EN gezondheids-/ontkennings-/samengestelde
   tegenvoorbeelden vast. Geen blanket-regel die "trainingsregistratie" altijd veilig maakt.
   Test dat een klacht elders in het bericht of een andere melding intact blijft.
   Frozen 6E-0/6E-1/classifierbytes blijven gelijk; nieuwe interpretatie mag geen
   bestaand herkend signaal of gebonden veiligheidsmelding wissen.
   Als dit niet aantoonbaar veilig in de nieuwe adapter kan, blijft optional clarification
   met continue_chat bestaan en volgt een exact afgebakend correctievoorstel, geen
   stilzwijgende uitzondering. Een beperkingobservatie telt ook dan niet als herkenningssucces.

lb is dus zichtbaar gepland maar niet achteraf als 6E-3-capaciteit geclaimd.
De taalbeperking is nog open, niet door owneracceptatie technisch opgelost.
Taaldekking en medische betekenis vereisen eigen deskundige beoordeling.

## Alleen Nieuwe Ownerkeuzes Voor GO

| Nieuw punt | Aanbevolen keuze en reden |
| --- | --- |
| T1 Eerste aanbevelingsinhoud | Een expliciet als volgende aangewezen traineroptie voorstellen om te bekijken, met exacte bron en grenzen; geen autonome optimalisatie. Dit levert een concreet persoonlijk voorstel zonder een nieuwe trainingsnorm te verzinnen |
| T2 Trainerbron en ontbrekende grenzen | Alleen expliciete, versiegebonden bevoegdheid plus toepasselijke grensvelden tellen; conflict/ontbrekend betekent geen kandidaat. Een trainerlink of memberplan alleen bewijst geen toestemming of grens |
| T3 Eerste lb-scope | Eigen kg/kg en lb/lb-vergelijkingen met oorspronkelijke waarden ondersteunen. Gemengde vergelijking voorlopig weigeren met concrete ontbrekende conversie-/afrondingskeuze; zo ontstaat geen verborgen gewichtswijziging |
| T4 Smalle taalcorrectie | Alleen de bekende registratiereview-betekenis en vooraf vastgelegde varianten in een nieuwe offline adapter, met gemengde-klachttegenvoorbeelden. Beoordeel de concrete antwoord-/verduidelijkingscopy, geen algemene classifieruitbreiding |

Dit zijn voorstellen, geen reeds ontvangen besluiten. GO is uitsluitend offline;
ownerproductreview van de daadwerkelijke uitvoer volgt apart. Geen heropening van
D1-D12/O1-O5/N1-N3/G1-G3. Geen nieuwe bewaartermijn of verplichte vraaglus.

## Gerichte Acceptatiecriteria

- Elke toegestane kandidaat citeert exacte eigen actuele doel/plan/oefening/setversies,
  volgende-optiebron en alle toepasselijke trainergrenzen; geen nieuwe cijfers/normen.
- Verkeerde persoon, trainer, workout/setbinding, vervalste inconsistentie, ingetrokken
  bron, ontbrekende authorisatie of conflicterende revisie geeft geen kandidaat/bronlek.
  Een synthetische coherent vervalste readset blijft expliciet geen bewezen authentieke bron.
- Latere plan-/doelwijziging laat historische reflectie identiek; een stale actuele
  aanvraag faalt zonder nieuwere data als oude opdracht te presenteren.
- kg/kg en lb/lb krijgen positieve en grensgevallen; gemengde/onbekende eenheid
  expliciete weigering zolang conversiebeleid ontbreekt. RIR/RPE blijven afzonderlijke
  zelfrapportage, null niet nul, RIR 0 behouden; geen belastbaarheid afleiden.
- Actuele/ernstige/terugkerende/oningedeelde klachten houden de nieuwe kandidaat tegen.
  Zelfrapportage kan alleen de geaccepteerde NIET-FYSIEKE reflectie herstellen;
  geen automatische toegang tot deze volgende-workoutkandidaat na een klacht.
  Ontbrekende deskundige hervattingscriteria blijven als concrete inhoudsgrens zichtbaar.
- Misverstand/technische fout geeft optionele herformulering/retry EN verder chatten.
  Geen andere meldingen wissen. Ontbrekende/verlopen context geeft geen trainingsvrijgave.
  Test O5 exact 30 dagen vanaf eerste registratie, eerder verval en geen retry-/statusverlenging.
- Verse duidelijke context kan bestaande niet-fysieke reflectie dragen, nooit verdwenen
  informatie reconstrueren of fysieke hervatting autoriseren. Chat/historie/feiten blijven
  onder eigen rechten en toestemming, geen algemene gezondheidsgerelateerde blokkade.
- Exacte bekende taalzin, onafhankelijke parafrases, educatieve/historische/ontkende
  context en gemengde klachten afzonderlijk beoordelen. Technische PASS, herstelde
  herkenning en resterende observaties apart tellen; geen groen medisch label forceren.
- Minimaal een normaal en een geweigerd exact antwoord in NL/EN/DE, deterministisch
  uitvoerbaar zonder provider, klok/netwerk/storage, echte leden of kosten.
- Alle frozen 6E-0..6E-3-bronnen en runtimebytes gelijk; geen app-import/embedding en
  alle nieuwe offline bronpaden HTTP404 op staging Pages. Geen automatische acties.

## Apart Open Voor Fysiek Advies Of Live Inzet

Deskundig: inhoud van echte trainingsprogressie, individuele belasting/volume/frequentie,
ernstige/terugkerende/oningedeelde klachten en hervatting; geen criteria hier invullen.
Trainergrenzen zijn geen medische vrijgave. Voedingsaanpassing en herstelcoaching
blijven latere, afzonderlijk te begrenzen categorieen binnen de bestaande ambitie.

Privacy/juridisch: noodzakelijkheid en gezag van nieuwe doel-/trainerbronnen,
doelgebonden toestemming, retentie/verwijdering, claims en verantwoordelijkheid.
O5 en chat-/analyseretentie blijven onveranderd; geen nieuwe opslagmachtiging.
Taal: NL/EN/DE-copy, interpretatie en de genoemde beperkte taalcorrectie.
Technisch voor live: aantoonbare historische en actuele bronlevering, serverauth,
bestaande entitlements/consent, revocation, gelijktijdige revisies, lifecycle-/security-
bewijs en afzonderlijke live GO. Offline verklaringvalidatie vervangt dit niet.

Geen deskundigen benaderen in deze voorbereiding. Geen live opslag/integratie,
provider, rechtenwijziging of productie. Dit voorstel START NIET AUTOMATISCH.

Bronnen: [geaccepteerd 6E-3-contract](PHASE6E3_CONTRACTS.md),
[freeze receipt](PHASE6E3_FREEZE_RECEIPT.md),
[broninventaris in het historische 6E-3-voorstel](PHASE6E3_PROPOSAL.md),
[actuele architectuur](ARCHITECTURE.md).
