# Package 6E-4 Bron-, Context- En Voorstelcontract

6E-4 TECHNICAL PASS / READY FOR OWNER REVIEW.
T1-T4 zijn expliciet geaccepteerde ontwikkelrichting; deze resultaten zijn NIET
owner-accepted/frozen. Geen live AI-vrijgave. Phase 6E blijft onvoltooid.
D1-D12/O1-O5/N1-N3/G1-G3 en alle frozen 6E-0..6E-3-bronnen behouden.

## Uitvoerbare Interface

Nieuwe map: _offline/phase6e4. prepare(state, now, options, previous) accepteert
alleen een uitgegeven frozen 6E-1-synthetische flowstaat en geinjecteerde tijd.
De opaque 6E-4-context bevat exacte subject/message/source/state-revisionbinding
en de ongewijzigde minimale O5-projectie. Oude/gekloonde contexten of onjuiste
lineage worden afgewezen. Geen systeemklok, IO, provider, database of storage.

suggest(request, context, authority) vereist synthetic_only, locale, binding,
expected_readset en sources. Bestaande auth/adult/entitlement/consent-regels
komen read-only uit 6E-1. Voor het nieuwe voorstel is ook beschikbare toegestane
chatcontext nodig; dit verandert geen rechten van historie, feiten of eerdere reflectie.
Alle uitvoer houdt mode=candidate_only, automatic_actions_allowed=false en
physical_advice_authorized=false. Alleen status=candidate_only bevat een kandidaat;
invalid_input, access_unavailable, clarification en unavailable bevatten candidate=null.

## Minimale Actuele Bronnen

| Bron | Vereiste betekenis / validator |
| --- | --- |
| readset | Synthetische eigen ID/revisie, read_at_ms gelijk aan het beoordelingsmoment en exacte current_refs voor doel, plan, relatie, bevoegdheid, grenzen en selectie. expected_readset voorkomt stil wisselen naar een nieuwere aanvraagversie |
| goal | Eigen actuele versie, een van de bestaande zeven doelcodes, actieve status, expliciete geldigheid. Geen vrij verzonnen doel of causaliteitsclaim |
| plan | Eigen actuele planversie, trainer-ID, bevoegdheidsreferentie, expliciete huidige doelkoppeling met tijd en exacte doelversie; link niet voor doel-capture en niet na plan-capture. Opties bevatten alleen bronlabels, workout-ID, catalogus-ID/revisie en geordende geplande sets |
| relationship | Eigen versiegebonden trainerrelatie, trainerrol, actieve geldigheid. Een profielkoppeling alleen voldoet niet |
| authority | Eigen expliciete trainer-ID, relatie/plan/doelrefs, toegestane workout-IDs, permission=propose_existing_next_option en member_source_consent=true. Alleen synthetic_declared_only als attestatietype |
| limits | Eigen actieve trainer-/bevoegdheids-/plan-/doelversies, complete dekking, exact gebonden rule-ID/workout/oefening/setindex, toegestane reps-/gewichtsgrenzen en allowed-flag. Ontbrekende regel is niet onbeperkt; verbod wint |
| selection | Eigen actuele trainerselectie, juiste plan/doel/bevoegdheid en basis=trainer_explicit_next_option. Ook bij een enkele optie geen keuze raden als option_id ontbreekt |
| catalog | Exacte oefeningsidentiteit en de door de planversie genoemde catalogusrevisie; begrensde NL/EN/DE-labels, geen naamovereenkomst als fallback |

Alle versiebronnen vereisen id, revision, subject_id, status, captured_at_ms,
valid_from_ms en valid_until_ms. Einde is exclusief: exact op de eindtijd niet geldig.
Actueel betekent de aangeleverde expliciete current_refs/readset, niet een zelfbedachte
maximale bronleeftijd. Dit is alleen synthetisch verklaarde consistentie:
coherent vervalste bronnen of een liegende bronleverancier worden NIET ontmaskerd.
Geen cryptografische, echte server- of live trainerautoriteit geclaimd.

Andere personen/trainers, extra velden, verkeerde settuples, dubbele/conflicterende
regels, onmogelijke vormen, toekomstige capturetijd en niet-finite getallen worden
afgewezen. Geen broninhoud bij ongeldige identiteit/invoer. Geldigheids-/dekkingstekorten
geven een concrete bronreden. Grenzen worden niet gerepareerd, geschat of samengevoegd.

## Voorstel En Eenheden

Elk getoond setnummer, reps-bereik, gewicht en doel komt uit het bestaande schema.
De hele voorgeschreven range/waarde moet binnen de bronregels vallen; geen optimale
training, extra set/volume, hogere belasting, voeding of trainingshervatting berekenen.
Meerdere opties zonder aangewezen volgende keuze geven geen voorstel.

kg/kg en lb/lb worden exact vergeleken. Binnen EEN geselecteerde optie is EEN
expliciete eenheid vereist; ook afzonderlijk correct gekoppelde kg- en lb-sets
samen geven mixed_units. Geen conversie, afronding of apparaatstap verzinnen.
Andere eenheden, ontbrekende waarden en onbekende oefening worden concreet genoemd.
RIR/RPE blijven afzonderlijke optionele schemavelden: null is niet nul; RIR 0 geldig,
RPE 0 niet volgens het bestaande invoerformaat. Het zijn hier geplande velden,
niet achteraf verzonnen uitgevoerde scores. Geen medische geschiktheid afleiden.

De kandidaat vermeldt alle zes bronrefs, readset, exacte set-/grensbasis en
berichtbinding. De invoer en geretourneerde historische resultaten worden niet
gemuteerd. De oude 6E-3-reflectie wordt read-only getest, niet omgeschreven:
nieuwe actuele schema-/doelversies kunnen geen oude sessiesnapshot vervangen.

## Context En Gerichte Taaladapter

De frozen 6E-2-probe bepaalt bestaande toegang, O5, waarschuwingen en feedback;
zij gebruikt een echte lege metriekset, geen verzonnen trainingsaggregaten.
assess in 6E-4 is een diagnostische adapter, geen rechtstreekse copyrenderer:
original bewaart de frozen beoordeling, de nieuwe view kiest de gebruikersfeedback.

- Volledig geconsumeerde reviewzinnen kunnen unresolved_meaning uitleggen.
  De oorspronkelijke "Ik bekijk mijn trainingsregistratie" en gerichte NL/DE-parafrases
  worden ordinary; bestaande EN-herkenning blijft behouden. Gewone umlautspelling
  is aanvullend getest. Geen nieuw medisch hulpniveau.
- Een bestaande klachttrace, ontkenning, citaat, historische/educatieve scope,
  technische fout, onbekende taal, ongebruikelijk symbool of conflict wordt nooit
  door de normale reviewphrase-uitzondering weggefilterd.
- Resttekst rond trainingsregistratie/workout log/training records/Trainingsprotokoll
  blijft onduidelijk als het geheel niet wordt begrepen, OOK wanneer een oud
  generiek trainingswoord ordinary gaf. Geen kandidaat; geen verzonnen gezondheidsalarm.
  Bijvoorbeeld "I am reviewing my workout log but my fingers tingle" wordt expliciete
  onzekerheid, niet een nieuw medisch label of bewezen goede medische herkenning.
- Bij die inline onzekerheid mag de gebruiker een NIEUW bericht formuleren
  (kind=new_message, reformulate_as_new_message) of verder chatten. Geen fictieve
  frozen issue/attempt aanmaken of verplichte vraaglus. Bestaande echte
  verduidelijking/retry gebruikt zijn ongewijzigde binding.
- Actuele, ernstige, terugkerende of oningedeelde klachten: bestaande waarschuwing
  eerst en geen workoutkandidaat. Een nieuwe klacht heeft prioriteit boven eerder herstel.
- Gebonden OF los genoemde zelfrapportage geeft dit nieuwe voorstel niet vrij.
  Een niet-actuele/ontkende/educatieve/geciteerde uitspraak bewijst evenmin actuele
  context voor deze kandidaat. Geen nieuwe gezondheidswaarschuwing uit die uitspraak.
- Bronverlies, O5-verval of verse context na een onopgeloste contextlacune geven
  geen kandidaatvrijgave. Dat is een nog onvolledige kandidaat-hervattingsgrens,
  geen afgeronde reviewdienst of medische beslissing.

Chat, historie, feiten en de eerder toegestane niet-fysieke reflectie houden hun
bestaande rechten en voorwaarden. Dat zij bruikbaar blijven betekent niet dat
deze nieuwe volgende-workoutkandidaat of fysieke aanbeveling is vrijgegeven.
Er is geen algemene gezondheidsgerelateerde abonnements-/functiesperre.

O5 blijft exact maximaal 30 dagen vanaf eerste registratie, eerder indien onnodig;
retry/status/view/reprocessing verlengt niet en verwijderde records herrijzen niet.
De adapter wijzigt geen frozen issues of events en voegt geen veiligheidsopslag,
tombstones of nieuwe bewaartermijn toe. De uitgebreide oude flowhistorie is alleen
in-memory synthetisch testmateriaal, NIET een toegestane live bewaarpayload.
Verlopen klachtinhoud wordt niet opnieuw in waarschuwingen/kandidaten uitgevoerd.

## Grenzen En Review

Known ordinary miss: "Ik inspecteer mijn trainingslogboek" blijft communicatie-
onzekerheid. Deze beperkingobservatie is GEEN herkenningssucces.
De oude 6E-3-module blijft byte-ongewijzigd en heeft haar historische taalbeperking;
de correctie geldt voor de nieuwe 6E-4-adapter, niet voor een live classifier.

Open: concrete antwoord-/weergavebeoordeling door owner; medische inhoud en
hervatting bij ernstige/terugkerende/oningedeelde klachten; privacy/juridische
noodzaak, toestemming, retentie/deletion en verantwoordelijkheden; NL/EN/DE-review
(inclusief voorlopige ASCII-transliteratie in DE). Voor live daarnaast betrouwbare
serverbronnen, actuele revisies/revocation/concurrency, auth/entitlements/consent,
security-/lifecyclebewijs en afzonderlijke GO. Geen beoordelingsdienst toegevoegd.

[Owneroverzicht](PHASE6E4_OWNER_OVERVIEW.md), [technisch bewijs](PHASE6E4_TECHNICAL_REPORT.md).
