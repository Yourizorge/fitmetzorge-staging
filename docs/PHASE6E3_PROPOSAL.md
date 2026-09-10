# Volgende Offline AI-Stap: 6E-3 Doel- En Schemagebonden Workoutreflectie

PROPOSED / NOT STARTED. Geen uitvoerings-GO, acceptatie of freeze.
6E-2 blijft TECHNICAL PASS / READY FOR OWNER REVIEW; N1-N3 staan open.
6E-0/6E-1 en D1-D12/O1-O5 blijven accepted/frozen binnen hun bestaande offline scope.
De trainingscorrecties en fysieke telefoontest staan hier los van.

## Eerstvolgende Uitvoerbare Uitbreiding

Bouw na afzonderlijke GO EEN offline contract dat een workout aan zijn eigen
sessiesnapshot, exacte oefening/sets en een bestaand actief doel koppelt.
Laat Youri concrete geplande versus geregistreerde sets bespreken, in plaats
van alleen workouttotalen te herhalen. Geen nieuwe belasting voorschrijven.

Synthetisch concept, nog geen geimplementeerde 6E-3-output:
"Je doel is sterker worden. In deze workout stond voor set 1 8 herhalingen met
55 kg; je registreerde 8 met 55 kg. Noteer wat je aan deze set wilt onthouden
en bekijk bij je volgende voorbereiding het bestaande schema. Ik verhoog
het gewicht niet op basis van deze ene set."

Bij ontbrekend doel: geen doel of motivatie invullen. Bij een gewijzigde
schemaversie: de historische sessiesnapshot vergelijken, niet het nieuwe schema
achteraf als de oude opdracht presenteren. Bij onbekende oefeningsidentiteit,
eenheid of brondekking: alleen aantoonbare feiten, met de concrete ontbrekende bron.

Uitvoerbaar resultaat: nieuwe afzonderlijke offline map, expliciete bronvalidators,
exacte NL/EN/DE-antwoorden, toestands-/inhoudsmatrix en vooraf vastgelegde
synthetische positieve EN geweigerde voorbeelden. Geen live adapter of provider.
Dit maakt doelgerichte coaching concreter maar levert nog geen persoonlijk
trainings-, voedings- of medisch herstelvoorschrift op.

## Wat Bestaat Al, Wat Mist Nog In Het AI-Contract?

Beschikbaar betekent hieronder: aangetroffen in repository/schema en de bestaande
domeinarchitectuur. Niet: iedere gebruiker heeft dit ingevuld, of AI mag het al lezen.

| Bron | Bestaande velden / gezag | Nog nodig voor AI |
| --- | --- | --- |
| Persoonlijke doelen | progress_goals: goal_code, baseline_weight_kg, target_weight_kg, target_date, status en updated_at; eigen, versie-veilige Progress-route. Doelcodes omvatten o.a. strength, muscle_gain, running en healthier_living | Een toegestaan doelbronobject met eigenaar, versie/status, actualiteit en toestemming. Gewicht of datum is geen gevalideerde norm. Vrije notes niet automatisch toevoegen |
| Schema | training_plans/days/exercises: UUID-identiteit, dag, volgorde, target sets/reps/weight, set_targets, RIR/RPE, rust en supersets; huidige route source=phase3_client | Toegestane snapshot-/set-ID-bron, eenheden, versie, tijdstip en volledige/partiele dekking. Geen trainergoedkeuring afleiden uit de aanwezigheid van een schema |
| Uitvoering | workout_sessions metadata.plannedExercises en effortTracking; workout_set_logs actual_reps/actual_weight/rir/rpe, completed_at, exercise_id; exact voltooid event | Geplande en uitgevoerde set betrouwbaar koppelen; leeg versus nul, wijziging versus historie, echte vergelijkbare uitvoering onderscheiden. RIR/RPE zijn zelfrapportage, geen belastbaarheidstest |
| Trainergrenzen | profiles.trainer_id en legacy coach_workspaces bestaan, maar zijn geen genormaliseerd, gevalideerd AI-contract voor belasting, frequentie of oefeningsgrenzen. Trainerprioriteit is architectuurambitie, geen ingevulde autoriteit | Afzonderlijk schema voor expliciete grens, auteur/bevoegdheid, toepassingsgebied, versie, geldigheid, intrekking/conflict en benodigde toestemming. Ontbrekend blijft ontbrekend, nooit een verzonnen standaard |
| Voeding | nutrition_targets bevat kcal/macros/optionele vezels, effective_from/to, status, auteur en acceptatie; food_logs/items bewaren gezaghebbende voedingssnapshots | De huidige member-write-route is daily/member-controlled. Het mogelijke enumlabel trainer of calculator bewijst geen werkende traineradviesroute. AI heeft nog geen toegestane doel-/voedingssnapshotadapter, portieadvies of beoordeelde wijzigingsgrenzen |
| Herstel | recovery_logs: slaapduur/-kwaliteit, stappen, ervaren energie/stress/motivatie/herstel; handmatige bron en datum. training_load_status is aanvankelijk unknown/placeholder | Eerst bron/actualiteit/ontbrekendheid vastleggen; geen medische gereedheid of herstelcriterium uit deze scores. Vrije recovery_note niet stilzwijgend toevoegen |

De uitvoerbare 6E-1/6E-2-input accepteert nu uitsluitend beperkte synthetische
dag-/workout-/weekaggregaten. Doelen, individuele oefeningen/gewichten,
trainergrenzen en voedingsdoelen zijn daarin NIET toegestaan.
Domeinopslag en een toegestaan AI-broncontract zijn dus verschillende zaken.

Bronnen: [Progress](PHASE5_PROGRESS_ARCHITECTURE.md),
[AI-architectuur](PHASE6_AI_CORE_ARCHITECTURE_READINESS.md),
[6E-2-contract](PHASE6E2_CONTRACTS.md);
schema: 20260812000000 legacy source baseline, 20260818 Nutrition slice1,
20260831145357 Progress foundation en 20260908100106 Training editor.
De huidige Training-correctie voegt alleen onafhankelijke weergavekeuzes toe.

## Afzonderlijke Beslissingen

- Eerst N1-N3 beoordelen; deze nieuwe opdracht accepteert ze niet stilzwijgend.
- Nieuwe product-GO voor uitsluitend bovengenoemde doel-/schemagebonden reflectie,
  de minimale bronvelden en de concrete antwoordstijl. Geen nieuwe algemene audit.
- Product- en privacykeuze voor later trainergrenzencontract en doelgebonden
  toestemming. Een trainerkoppeling is geen automatische deling of bewijs van grenzen.
- Deskundige beoordeling voor latere fysieke progressie: welke belastings-,
  oefenings- en frequentievoorstellen wel mogen, met welke betrouwbare invoer en
  welke klacht-/hervattingsvoorwaarden. Deze criteria nu niet zelf invullen.
- Voedingsdeskundige/medische beoordeling voor toekomstige portie-, energie-,
  macro- en herstelcoaching; bestaande gebruikersdoelen niet als medische norm behandelen.
- Medische, privacy-, juridische en NL/EN/DE-review blijven nodig voor live inzet,
  naast serverauth/consent, retentie/verwijdering, bronbinding, securitytests en expliciete live GO.

## Te Bewijzen Grenzen

Nieuwe onafhankelijke tests: werkelijk passend doel/snapshot, ontbrekend/vervallen
doel, latere schemawijziging, verkeerde gebruiker/oefening/eenheid, niet-vergelijkbare
sets, RIR 0 versus leeg, expliciete versus ontbrekende trainerbron en conflicten.
Behoud context-/message-binding, waarschuwing eerst, optioneel verduidelijken
EN verder chatten, O5 maximaal 30 dagen vanaf de eerste registratie zonder verlenging.

Zelfrapportage, tijdsverloop of verwijderen geven geen medische vrijgave.
Zonder passende inhouds-/hervattingscriteria blijft fysiek advies buiten scope.
Chat, historie, feiten, aanbevelingen en automatische uitvoering blijven gescheiden;
automatische acties UIT. Geen menselijke aanvraag- of beoordelingsdienst.
Training-, voeding- en herstelcoaching blijven de ambitie, maar niet als reeds
geleverd of deskundig goedgekeurd presenteren. Start dit voorstel niet automatisch.
