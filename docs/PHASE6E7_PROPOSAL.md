# Package 6E-7 Proposal

PROPOSED / NOT STARTED. Geen implementatie-GO.
Opgesteld 2026-09-11 na owneracceptatie W1/W2; Decision 0047.
Enig aanbevolen volgend pakket: **Synthetische workflowdemo voor voorstel,
dubbele bevestiging, toepassing, restore en meldingen**.

## Doel En Afbakening

Maak na aparte owner-GO een klikbare, uitsluitend synthetische workflowdemo op
staging Pages en een nieuwe offline workflowadapter. Laat zien hoe een concreet
trainerbegrensd voorstel door afzonderlijke lidacceptatie, trainergoedkeuring en
expliciete toepassing gaat, of wordt geblokkeerd/afgewezen. Demonstreer een
controleerbare terugzetaanvraag en twee geminimaliseerde meldingenoverzichten.

Dit pakket bewijst productgedrag en deterministische contracten, NIET echte
authenticatie, trainerauthoriteit, duurzame databaseatomiciteit of medische veiligheid.
Geen echte accounts, leden, schemawijzigingen, provider, live AI, Edge of database.
De publieke demo bevat alleen vooraf gecontroleerde verzonnen gegevens. Een
afzonderlijke URL is GEEN toegangsbeveiliging en geen bewijs van RLS.

Frozen 6E-0..6E-6 blijven read-only; huidige 60 runtime-assets, timer/RIR/RPE en
bestaande rechten blijven identiek. D1-D12/O1-O5 en alle latere acceptaties behouden.
6E als geheel blijft onvoltooid.

## Concrete Oplevering

- Nieuwe private map _offline/phase6e7 met adapter, bronvalidators, vooraf
  vastgelegde gevallen, tests en reproduceerbare NL/EN/DE-uitvoer. Geen wijziging
  van frozen modules. Gebruik de bestaande 6E-6-engine read-only.
- Afzonderlijke nieuwe publieke demo, voorgesteld training-review-demo/index.html,
  met eigen styles en controller. Geen navigatie/import in de werkende app.
  Publiceer geen offline broncode, tests, manifests of frozen CJS-modules.
- Genereer expliciet publieke synthetische fixtures/readmodels en verwachte
  overgangen uit de offline runner. De mockcontroller wordt tegen die resultaten
  getest; een fixtureweergave wordt niet als live-engine-integratie gepresenteerd.
- Per oefening: huidig plandoel, gekoppelde werkelijke prestatie, volgende-week-
  voorstel, reden, bronversies, trainergrenzen en drie afzonderlijke statussen.
- W1: meerdere passende regels blijven geblokkeerd; geen nieuwe prioriteitsheuristiek.
  W2: bij een niet-passende stap ook het exacte getal en de broneenheid tonen,
  bijvoorbeeld: "De ingestelde gewichtsstap is 2,5 kg. De beschikbare gewichten
  passen daar niet exact bij. Daarom is er geen wijzigingsvoorstel."
  Dit sluit de gedocumenteerde R01-presentatiekloof zonder frozen code te wijzigen.
- Aparte toestanden voor geen trainer, ingetrokken relatie, ontbrekende regel,
  onvolledige gegevens, versieconflict, klachten, afwijzing en dubbele verwerking.
- Lid/trainer-personakeuze duidelijk als simulatie; geen medische beoordelingsdienst.
  Chat/historie worden uitsluitend als toegankelijke mocksecties weergegeven.

## Gegevensstroom

1. Een vaste fixture-ID laadt synthetisch lid, trainerrelatie, actuele versiegebonden
   bevoegdheid/doel/plan/regel, historische sessiesnapshot en registratie.
2. Validators controleren eigendom, exacte oefeningen/sets, versies, eenheden,
   gegevensvolledigheid en veiligheidscontext; oude snapshots blijven onveranderd.
3. Frozen 6E-6 berekent een kandidaat of feitenfallback. Nieuwe adapter levert een
   geminimaliseerd readmodel met betrouwbare provenance, inclusief W2-detail.
4. Lidacceptatie en trainergoedkeuring binden afzonderlijk aan dezelfde proposal-ID,
   volledige inhoudshash en bron-/relatie-/regelversies. Afwijzen is geen toepassen.
5. Expliciete traineractie "Toepassen" hercontroleert alle bindingen en blokkades.
   Alleen een volledige geldige overgang publiceert in memory de nieuwe planversie,
   het vorige plan, auditrecord en meldings-events als een geheel.
6. Een command-ID met dezelfde payload geeft hetzelfde resultaat; dezelfde ID met
   andere payload wordt geweigerd. Een stale bron of deels ongeldige oefening geeft
   GEEN gedeeltelijke wijziging. Hetzelfde geldt voor herstel-/restorecommando's.
7. Twee mockinboxen lezen toegestane status-events. Een notificatieretry verandert
   nooit opnieuw het plan en maakt geen dubbele melding.
8. Reset/verversen start opnieuw met de vaste fixture. Geen browserpersistency,
   echte chatimport of claim van herstel na servercrash.

Getallen worden deterministisch uit expliciete trainerregels gekozen, niet door
een taalmodel. kg blijft kg, lb blijft lb; geen conversie/afronding. RIR/RPE
blijven afzonderlijk, nul is niet ontbrekend en zelfrapportage is geen belastbaarheid.
Ontbrekende doelen, ranges of precisie die de bronadapter niet betrouwbaar ondersteunt
geven feiten/uitleg; geen gegokte puntwaarde of historische eenheid.

## Toepassing En Terugzetten

Voorgestelde NIEUWE productkeuze K2: terugzetten is een aparte kandidaatwijziging,
met eigen diff, lidacceptatie, trainergoedkeuring en expliciete trainer-toepassing.
Herstel de bewaarde inhoud als een NIEUWE monotone versie: v3 naar v4 en daarna
v3-inhoud terugzetten geeft v5, niet opnieuw versie-ID v3.

Behoud het volledige vorige plan, units, oefeningsidentiteiten, RIR/RPE-keuzes,
bronversies en audit. Bestaande setlogs en sessiesnapshots worden nooit herschreven.
Een latere planwijziging maakt een oude restoreaanvraag stale; niet overschrijven.
Nieuwe klachten, ingetrokken bevoegdheid of onvoldoende herstelcontext blokkeren
ook restore. Een oud plan is niet vanzelf een veilig plan.

Afwijzen/intrekken stopt verdere toepassing, maar maakt een al toegepaste wijziging
niet stilzwijgend ongedaan. Dat vraagt bovenstaande afzonderlijke flow.
De demo moet laten zien wat nog op welke bevestiging wacht, zonder een fictieve
medische wachtrij of automatische vrijgave te suggereren.
Retentie van echte versies/audit is apart te besluiten; "audit behouden" betekent
geen onbeperkte opslag van persoonlijke gegevens.

## Meldingen En Veiligheidsgrenzen

Voorgestelde K3: uitsluitend twee gesimuleerde in-app-inboxen. Geen mail, push,
sms of externe diensten. Toon voorstel beschikbaar, lid bevestigd, trainer akkoord,
afgewezen, geblokkeerd, toegepast, teruggezet of vervangen. Deduplicatie op event-ID.
Geen bericht uitsturen voordat de bijbehorende overgang is vastgelegd.

Het lid ziet de eigen passende uitleg. De trainer ontvangt alleen het geautoriseerde
voorstel/diff en noodzakelijke status, niet automatisch private chat, klachttekst,
diagnose of herstelmelding. Een trainerstatus kan "Voorstel niet beschikbaar" tonen.
Een trainerrelatie alleen geeft geen toegang tot alle veiligheidsinformatie.

Actuele/ernstige/terugkerende/oningedeelde klachten houden fysieke voorstellen dicht.
Zelfrapportage, bronverwijdering of O5-verloop geven geen medische vrijgave.
O5: maximaal 30 dagen vanaf eerste registratie, eerder indien onnodig; retry,
raadplegen of statuswijziging verlengt niet. Een andere status mag geen permanente
kopie van verlopen veiligheidsdata vasthouden. Geen reconstructie van verdwenen tekst.
Feiten, niet-fysieke reflectie, chat, advies en uitvoering blijven afzonderlijk.
Misverstanden mogen worden verduidelijkt OF men kan verder chatten; geen verplichte lus.

## Onderdelen Per Laag

| Laag | Binnen 6E-7 na GO | Later apart serverpakket, NIET nu |
| --- | --- | --- |
| Frontend | Nieuwe zelfstandige synthetische demo met fixture- en personakeuze | Echte lid/trainer-schermen, bronstatus, bevestigingen, conflicten, inbox en herstel binnen bestaande apprechten |
| Edge | Geen functie, deployment of aanpassing aan youri-ai | Smalle geauthenticeerde proposal/decision/apply/restore/inbox-handlers, zonder providervereiste |
| Database | Geen tabel/RPC/migration; alleen in-memory mockaggregate | Versiegebonden bronnen, rulebooks, voorstellen, goedkeuringen, commands, planhistorie en outbox |
| RLS/ACL | Niets aanpassen; synthetische allow/deny-specificaties zijn geen RLS-bewijs | Gescheiden lid/trainer-selectrechten en uitsluitend gecontroleerde schrijfcommando's |
| Bestaande Training | Alle 60 assets en schema-/sessiewerking behouden | Expliciete bronadapter en versieconflictdetectie, ook na bestaande handmatige editorwijzigingen |
| Provider | Geen SDK, call of key | Alleen na afzonderlijke privacy-, inhouds-, kosten- en ownergates |

Gebruik later het bestaande bearer-authpatroon, maar leid actor/rol/relatie op de
server af en vertrouw geen meegestuurde actor-ID of "approved"-boolean. Bewijs
trainerauthoriteit uit actuele geautoriseerde records, niet uit synthetische velden.
Beperk payloads, bronvelden, requestlengte, toegestane acties en foutmeldingen.
Servicekeys nooit naar browser. Geef geen generieke schrijf- of service-role-proxy.

RLS en object-/functierechten moeten samen worden ontworpen en getest. Gebruik
security invoker waar mogelijk; een noodzakelijke privileged RPC vereist expliciete
actor/relatie/scopechecks, vaste search_path en ingetrokken PUBLIC-uitvoering.
Controleer ook views en serverrollen die RLS kunnen omzeilen.
[Supabase RLS-documentatie](https://supabase.com/docs/guides/database/postgres/row-level-security).

Bestaande eigen planbewerkingsrechten blijven behouden. AI-wijzigingen mogen de
dubbele goedkeuring niet via die handmatige editorroute omzeilen. Iedere relevante
handmatige wijziging moet oude AI-bindingen ongeldig maken.

## Eventuele Latere Migrations

GEEN SQL-bestanden, timestamps, remote checks of migrations maken in deze opdracht
of het voorgestelde browsermockpakket. Eerst aparte scope en GO:

| Groep | Te ontwerpen resultaat | Verplichte controles |
| --- | --- | --- |
| M1 Bronversies | Immutable plan-/doel-/trainerregelversies, actuele bevoegdheid/relatie, historische unit/precision-contract | Geen terugwerkend verzonnen doel of unit; numeric(7,2) kan niet alle frozen decimalen opslaan; geen stille afronding/backfill |
| M2 Commands | Proposal/review/apply/restore-ledger, vorige planinhoud, monotone revision, volledige audit | Composite eigendomsbindingen, CAS, locks, request-ID/payloadhash-uniciteit, volledig atomair plan+audit+outbox |
| M3 Lifecycle | Minimale notificatie-outbox/inbox, consentbinding, doelgebonden expiry/delete | Geen private klachttekst in trainerinbox, O5 vaste oorsprong, verwijdering/export/relatieverlies, geen eeuwige statuskopie |

Bepaal expliciet of bestaande 6A-objecten veilig additief kunnen worden uitgebreid
of nieuwe afgeschermde 6E-tabellen nodig zijn. Hun huidige action/status-enums en
member-only rechten bewijzen geen trainerreview/apply. De bestaande
member_notifications is analysis_ready/analysis_id-gebonden en geen proposal-outbox.
De huidige workout-save-RPC is een membereditor, geen kant-en-klare AI-commandroute.

Voor enige latere databasepublicatie: reproduceerbare lokale migrationopbouw,
gerichte echte SQL/RLS-tests met meerdere identiteiten en twee transacties,
leeg/onverwacht-vrij dry-run, additive review en bewijs van ongewijzigde bestaande
leden. De eerdere 33/33 migration-reconciliatie is historisch bewijs, geen nu
uitgevoerde livecheck. Bestaande lokale rebuildbeperkingen eerst aantoonbaar oplossen;
geen OneDrive-opruiming of historische replay uit dit voorstel afleiden.

## Tests En Acceptatiecriteria

Voor implementatie de scenario's vastleggen, daarna technische resultaten en
beperkingobservaties gescheiden tellen. Minimaal:

1. Reps, volledige gewichtsstap, behouden, geen trainer, geen regel, overlap W1
   en W2 buiten gewichtsgrid; exact NL/EN/DE-antwoord uit de runner.
2. Verkeerd lid/trainer, ingetrokken relatie, andere oefening/set, stale plan/doel/
   regel/goedkeuring; geen gedeeltelijke toepassing of gekopieerde oude acceptatie.
3. Ontbrekende waarden versus RIR 0, afzonderlijke RPE, kg/lb, ranges, precisie en
   later aangepast schema zonder wijziging van historische opdracht.
4. Actuele/nieuwe/terugkerende klachten, zelfrapportage, onbekende of verlopen context
   en O5; alle frozen veiligheidsgrenzen blijven gelden.
5. Lidakkoord alleen, trainerakkoord alleen en beide zonder apply wijzigen niets.
   Daarna precies een geheel toepassen; foutinjectie publiceert geen halve state.
6. Herhaald commando, identieke/verschillende payload met dezelfde ID, dubbele klik,
   oude restore na latere wijziging en afgewezen restore. Oude snapshots blijven exact.
7. Meldingsdeduplicatie, inboxscope, private reden niet naar trainer en retry zonder
   planmutatie. Mockconcurrency niet als echte DB-isolatie tellen.
8. Geen auth/provider/Supabaseclient, appstorage, analytics, uploads of vrije
   persoonlijke invoer; uitsluitend allowlisted fixture-ID's. Geen dynamische egress.
9. 320/390 px mobiel en 1280 px desktop, licht/donker, alle acties en statuslabels,
   zichtbare reset bij refresh. Screenshots en onderscheid emulatie/fysieke ownerretest.
10. Alle 122 frozen bronnen en 60 bestaande assets byte-identiek voor/na Pages.
    Alle offline/testpaden, ook nieuwe private bestanden, HTTP404; publieke bundel
    bevat alleen expliciet publieke synthetische demo en geen bronmaps met private code.

Gebruik een restrictive demo-CSP, onder meer connect-src 'none'; alleen lokale
statische assets, geen CDN/fonts/telemetrie. Controleer daadwerkelijk browsernetwerk,
bundel/imports en mogelijke appstorage-interactie, niet alleen een configuratievlag.

Acceptatie voor technische oplevering: alle verplichte gevallen PASS, negatieve
gevallen blokkeren aantoonbaar, exacte voorbeelden/bronbinding aanwezig, geen
runtime/frozen drift, geen externe AI-calls en geen echte gegevens. Eindstatus:
6E-7 TECHNICAL PASS / READY FOR OWNER REVIEW. Geen automatische freeze of live-GO.

## Rollbackstrategie

Mockpublicatie: de afzonderlijke demo-invoeging via een gecontroleerde revertcommit
terugdraaien; geen bestaande Training-assets of frozen bronnen terugzetten.
Een mockreset herlaadt uitsluitend de fixture, geen echte gegevens.
Operationele rollback is niet hetzelfde als product-restore.

Later serverwerk: commands kunnen expliciet fail-closed worden uitgeschakeld;
bewaar planhistorie/audit volgens goedgekeurde retentie en herstel forward-only.
Geen destructieve downmigration, tabeldrop of terugzetten van een hele database
als normale product-undo. Een echte schema-restore volgt de afzonderlijk bevestigde
versiegebonden transactie, inclusief veiligheidschecks en idempotency.

## Kosten En Nieuwe Ownerkeuzes

Verwachte externe AI-calls: **0**. Maximaal extern AI-budget: **EUR 0**.
Geen nieuwe betaalde diensten. Bestaande Pages-herpublicatie; geen uitspraak dat
alle hosting/arbeid kosteloos is. Een onverwachte nieuwe kostenpost vereist eerst GO.

| Keuze | Concreet voorstel | Reden |
| --- | --- | --- |
| K1 GO en plaats | Bouw alleen bovenstaande publieke synthetische standalone demo, niet in de echte app | Eerst productflow testen zonder echte accounts/data of wijziging van Training |
| K2 Restore | Nieuwe monotone planversie na opnieuw lidakkoord, trainerakkoord en aparte trainer-toepassing | Geen stille overschrijving of medische vrijgave via undo |
| K3 Meldingen | Alleen geminimaliseerde mockin-app-inboxen voor lid en trainer, geen externe kanalen/klachtdeling | Review van de volledige flow zonder privacy- of provideruitbreiding |
| K4 Mockduur | State alleen in memory; refresh/reset start herkenbaar opnieuw | Geen onbedoelde echte opslag en geen valse claim van serverduurzaamheid |

Voor latere echte verwerking blijft K5 uit de audit open: concrete bewaartermijnen,
doelen/ontvangers van proposals/approvals/audit/meldingen en passende datatoestemming.
O5 wordt niet heropend en niet als algemene 30-dagenregel voor alle objecten gebruikt.

Medische/trainingsinhoudelijke herstel- en safetycriteria, privacy/juridische
beoordeling en NL/EN/DE-taalreview blijven open. Voor nieuwe echte-ledenverwerking
en eventuele providerverwerking gelden de afzonderlijke gates uit de
[Remaining Work Audit](PHASE6E_REMAINING_WORK_AUDIT.md#5-echte-leden-gescheiden-privacy--en-providergates).
Geen medische aanvraagdienst, nieuwe progressienorm, voedingswijziging of automatische
actie. Dit document is een voorstel; geen enkele 6E-7-implementatiestap is gestart.
