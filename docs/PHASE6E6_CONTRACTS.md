# Package 6E-6 Contracten

## Owneracceptatie W1/W2 (2026-09-11)

COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE ONLY.
[Freeze receipt](PHASE6E6_FREEZE_RECEIPT.md). Onderstaande leveringsstatus is historisch.
Geen live/medische vrijgave. Het W2-weergavedetail bij blokkade en andere resterende
integratiepunten staan expliciet in de [Remaining Work Audit](PHASE6E_REMAINING_WORK_AUDIT.md).

OFFLINE ONLY / resultaten voor ownerreview. Geen owneracceptatie of live GO.
6E-5/P1-P3: COMPLETE / OWNER-ACCEPTED / FROZEN - OFFLINE ONLY.
D1-D12/O1-O5 en alle eerdere geaccepteerde keuzes blijven ongewijzigd.

## Nieuwe Afbakening

Alleen _offline/phase6e6. De 106 bronnen van 6E-0..6E-5 blijven read-only;
alle 60 applicatie-assets, inclusief accepted Training, blijven byte-identiek.
Geen provider, dependency, live AI, database, migration, Edge, echte leden of schemawrites.

6E-5 berekende al concrete reps/load/behoud uit expliciete oefeningregels.
6E-6 voegt een expliciet trainerregelboek toe met minimum/maximumreps,
scalar gewichtsstap, brongebonden oefeningstype-selectie, aparte betrouwbare
feitenfallback en inspecteerbare review-/transactieaggregate.
Geen nieuwe brede classifier of vervanging van geaccepteerde teksten/niveaus.

## Invoer En Regelresolutie

propose({synthetic_only:true, base, expected_rulebook, rulebook}, context, authority).
base is het bestaande 6E-5-request met geldige policy-envelope maar rules=[].
De NIEUWE adapter vult alleen een kopie van die rules vanuit gevalideerde bronnen.
Twee gelijktijdige regelautoriteiten (niet-lege base.policy.rules) worden geweigerd.

rulebook heeft ID/revisie/lid/trainer/policy_ref, status, capture en geldigheidsvenster,
bindings en rules. expected_rulebook moet exact passen; status actief, capture niet
toekomstig, geldig vanaf inclusief en tot exclusief. Trainer/lid/policy moeten
exact de huidige verklaarde bronnen zijn. De frozen validators controleren daarna
huidige relatie, bevoegdheid, doel, schema, grenzen, selectie en bronvensters.
Consistente synthetische verklaringen zijn GEEN bewijs van echte trainerautoriteit.

Per binding: exercise_ref (ID/catalogusrevisie), workout, variant, apparaat en een
optionele expliciete type_ref. Type is brondata, geen gok op basis van een naam.
Een regel heeft eigen ID/revisie/status, selector exercise OF type met exacte ref,
en de volgende verplichte parameters:

| Parameter | Betekenis |
| --- | --- |
| reps_min / reps_max | Expliciete trainergrenzen; huidig target en reset moeten passen |
| reps_step | Volledige expliciete positieve reps-stap, niet clampen |
| weight_step / available_weights | Positieve expliciete stap EN exact beschikbare gewichten; geen impliciete afronding |
| set_count / unit | Exact bestaand setaantal en kg/kg of lb/lb |
| minimum_sessions | Expliciet N laatste voltooide vergelijkbare sessies; geen zelfgekozen norm |
| comparable_plan_refs / comparable_goal_refs | Expliciet toegestane historische versies, nooit vervangen door actuele bronnen |
| rir / rpe | Afzonderlijke required/min/max; niet omrekenen of medisch interpreteren |
| forbidden_effort_pairs | Alleen expliciete bronregel kan een getallenpaar conflicterend verklaren |
| maintain_when | Expliciete target_or_effort_not_met-regel, geen fallback voor ontbrekende data |

Nul, een of meerdere passende regels worden onderscheiden. Nul: feiten-only.
Meer dan een: conflict, ook bij oefeningregel plus typeregel; GEEN verborgen voorrang.
Een passende ingetrokken regel kan niet stilzwijgend door een andere worden vervangen.
Verschillende oefeningen mogen expliciet hetzelfde type delen; hun concrete identiteit,
variant, apparaat, geplande en historische sets blijven afzonderlijk gebonden.

Gewichten: maximaal zes decimale plaatsen in deze technische bronrepresentatie.
De validator vergelijkt exacte decimale integer-eenheden; geen epsilon-rounding.
De lijst moet exact de verklaarde stap volgen. Andere precisie, gaten of onbekende/
gemengde eenheden geven een uitleg, geen conversie, alternatieve stap of afronding.
Dit is een technisch formaat, geen norm voor beschikbare apparatuur.

## Beslissing En Controleerbare Uitvoer

Na resolutie blijft de 6E-5-berekening intact:
onder plafond + alle vereiste targets/effortvoorwaarden gehaald: expliciete reps-stap;
op plafond: volgende expliciete gewichtwaarde en resetreps;
targets of expliciete effortvoorwaarden niet gehaald: bestaand plandoel behouden.
Alle proposed sets moeten ook binnen de actuele exacte trainergrenzen passen.
Geen extra sets, nieuwe oefening, voedingswijziging of medische hervatting.

Per rij: current_plan, historische observations met oorspronkelijke plan/doelrefs,
next_week, kind/reason, eigen rule_provenance en approval_status.
Het rulebook-ID/revisie en de volledige inhoudshash binden het voorstel; een
regelboekrevisie geeft een nieuw voorstel ook wanneer de uitkomstgetallen gelijk zijn.
Bronbasis bevat de relevante inhoud; alleen herleestijden/locale zijn geen nieuwe autoriteit.

Herhalingsbereiken en ongelijke point-targets blijven expliciet niet ondersteund.
Onvoldoende historie/sets, ontbrekende verplichte RIR/RPE of betwiste gegevens:
geen toepasbare gezamenlijke planoptie. Geen gedeeltelijke toepassing.
Alles behouden: concrete reflectie, geen onnodig wijzigingsobject.

## Feiten Zonder Toepasbaar Voorstel

Bij geen trainer of geen geschikte regel: geen plan_option, hoogstens betrouwbare
historische feiten en uitleg. Er wordt GEEN tijdelijke/fictieve trainer aangemaakt.
Een afzonderlijke validator controleert eigen lid, uitgegeven context, analyse- en
historietoegang, historyref/leesmoment, sessie/snapshot/plan/doel/oefening/setbinding,
tijden, bronkwaliteit en afzonderlijke null/getalwaarden.
Ambigue sessie-/snapshot-/log-ID's: geen van de tegenstrijdige kopieen tonen.
Fout gekoppelde sets worden weggelaten; ontbrekende reps/load blijven null en
complete=false. RIR 0 blijft echt nul; RPE 0 is ongeldig volgens bestaand invoerformaat.
Historisch geplande waarden worden expliciet historisch genoemd, niet als huidig plan.

De feitenfallback beweert geen volledige historie, vergelijkbaarheid, trainingsgeschiktheid
of toekomstige progressie. Ontbrekende bronnen worden niet gereconstrueerd.
Gezondheidswaarschuwingen en optionele verduidelijking blijven ook bij ontbrekende regels
behouden. Toegang/chat/historie/feiten/niet-fysieke reflectie houden hun eigen frozen regels.

## Drie Statussen En Transactiesimulatie

workspace(issuedProposal), create(issuedProposal, workspace), act(state,event,freshRequest,context,authority).
Herbruik dezelfde workspace voor concurrerende voorstellen op hetzelfde schema.
Een nieuwe onafhankelijke workspace is een NIEUW synthetisch scenario, geen live database.

- member_acceptance: pending / accepted / rejected / invalidated.
- trainer_approval: pending / accepted / rejected / invalidated.
- application: not_applied / applied.
- Globale reviewstatus: pending / approved / rejected / needs_recheck / applied.

Bekijken verandert niets. Beide acceptaties gelden exact dezelfde voorstel-/bronversie.
approved verandert het schema nog NIET. Alleen een APARTE expliciete trainer-apply
mag na beide acceptaties alle changes volledig in memory uitvoeren.
Afwijzen is terminal. Nieuwe geldige bronnen vereisen nieuw voorstel en nieuwe lege
bevestigingen; geen oude handtekeningen meenemen. Er is geen menselijke medische dienst.

Ieder muterend event bindt actorrol/ID, relatie, voorstelversie, reviewrevisie,
basisplanref en unieke event-ID. Context moet opaque uitgegeven zijn.
Bij acceptatie/apply worden alle actuele bronnen, regels, context en rechten opnieuw
beoordeeld. Huidige klachten, zelfrapportage, O5-verval of ontbrekend herstelbewijs
geven GEEN medische vrijgave; nieuwe/terugkerende/ernstige/oningedeelde meldingen blokkeren.
Een CAS op gedeelde actieve planref EN inhoudshash blokkeert parallelle oude voorstellen.

De simulator bouwt eerst lokaal de volledige nieuwe aggregate op:
nieuw schema, aparte statussen, vorige volledige schema-snapshot, gebruikte bronrefs/
inhoudshashes, hash-gekoppelde audit en globale event-idempotencyledger.
Pas daarna wordt de hele aggregate in een enkele synchrone in-memory stap gepubliceerd.
Een geinjecteerde fout VOOR die stap laat alles, inclusief audit en eventledger,
ongewijzigd. Dezelfde eventretry kan daarna precies eenmaal slagen.
Dezelfde event-ID met andere payload/voorstel wordt geweigerd; een reeds toegepaste
wijziging wordt niet opnieuw uitgevoerd. Behouden vorige schema's blijven inspecteerbaar.

Dit bewijst GEEN duurzame storage, echte database-transactie, procescrash-/restart-
idempotency, netwerkconcurrency, live sessieauthenticiteit of externe intrekkingsfeed.
Een audit-hash is inhoudscontrole, geen handtekening of fraudebestendig live log.
Retentie van toekomstige voorstellen/goedkeuringen/audit is niet live goedgekeurd.

## Grenzen Die Openblijven

O5 blijft uiterlijk 30 dagen vanaf eerste registratie, eerder indien onnodig.
Lezen/status/retry verlengt niet; afloop geeft geen vrijgave. Geen extra gezondheids-
tekstkopie in audit. Alleen synthetische testvoorbeelden worden lokaal gedocumenteerd.
Dezelfde known_language_miss blijft open en is GEEN herkenningssucces.
Geen nieuwe taalreparatie, medische beoordeling of deskundigencontact.

Live inzet vereist nog echte trainerherkomst/autorisatie/versies/intrekking, beoordeelde
trainingsregels en inhoud/hervattingscriteria, privacy/juridische grondslag/consent/
doelgebonden retentie/deletion en NL/EN/DE-review, plus duurzame transactionele checks.
Alle output blijft automatic_actions_allowed=false, physical_advice_authorized=false,
medical_clearance=false. Phase 6E onvoltooid; geen automatische freeze of volgend pakket.
