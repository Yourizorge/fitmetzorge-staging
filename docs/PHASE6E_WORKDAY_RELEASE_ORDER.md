# Gecontroleerde releasevolgorde

Dit register beschrijft de vervolgintegratie, niet een bulkpublicatie of nieuwe
toestemming. De concrete lokale kandidaat staat in `_offline/phase6e_server_v1`.
De huidige hosted blokkade, exacte budgetvoorstellen en bewijs staan in
[het werkdagrapport](PHASE6E_WORKDAY_RESULT_20261015.md). Geaccepteerde
broncontracten13-20 blijven read-only;21 is niet geaccepteerd en default-off.

## Gemeenschappelijke grens

Elke slice gebruikt servermatige identiteit/workspacebinding, een actuele Auth-
sessie, private RLS, exacte bron- en schemaversie, CAS en een idempotency-key.
Een browserrol verleent geen rechten. De lokale kandidaten45/46 zijn geen
hosted migrations en hun nummering is geen reservering van toekomstige slots.
Nieuwe canonical migrationnamen pas via de CLI maken bij een concrete release.

Elke hosted vrijgave vereist de volledige11-keten en noodzakelijke ownerreview,
brongebonden schone CI, actuele project/migration/dry-runcontrole, een concreet
commandoregister met veilige stopreserve en een afzonderlijk toegelaten budget.
De oude registration12-dossiers bevatten gemeten lokale commando's, geen
doorlopende hosted toestemming. Numerieke omvang alleen bewijst geen databehoud.

## Increments

| Volgorde en gedrag | Bestaande bronnen en lokale opslag | Toelating en gerichte tests | Terugdraaien |
| --- | --- | --- | --- |
| 1. Minimale historische registratie12: opslaan, corrigeren, herladen, opnieuw aanmelden | `registration12.cjs`, `registration_store.py`, `registration_transport.py`; private workspaces/revisions/requests/audit uit kandidaat45 | `registration_database.py`, `registration_proof.py`, `registration_browser.cjs`;22 gemeten transportparen; exact geselecteerde accounts, bron en writeset; geen lifecycle of outbox meepubliceren | Nieuwe ingang sluiten; versies en audit behouden; uitsluitend bewezen eigen fixtures verwijderen |
| 2. Brongebonden signalen13-14 en opnieuw beoordelen | `domain.cjs`, `windows.cjs`, immutable bronrevisies; geen nieuwe adviesregels | Complete vergelijkbare vensters; ontbrekende/tegenstrijdige bron; deduplicatie; broncorrectie trekt voorstel en goedkeuring in; exact benodigde statekeys selecteren | Signaalverwerking default-off; oude registraties en geldige historie blijven |
| 3. Route B-intake15 en planbasis | `panels.js`, `domain.cjs`, frozen intake-/catalogusvalidators; versiegebonden intakeHistory | Catalogusverval, allergieconflict, ontbrekende toestemming, bronwijziging; Route A ongewijzigd; geen trainerstap voor B | Nieuwe intakebewerking sluiten; eerdere intake/planversies behouden |
| 4. Trainingsplan16 en voedselplan17 bewerken | `presentation.cjs`, frozen training-/nutrition-rules models; gezamenlijke private state met afzonderlijke bronversies | Exacte oefening/productversie; sets/reps/rust/RIR/RPE; portiegrenzen, ontbrekend versus nul; geplande totalen nooit als gegeten presenteren | Bewerking sluiten; geen achteraf herschrijven van oude snapshots |
| 5. Gezamenlijke review18 | `domain.cjs`, `store.py`; CAS-transactie plus request/audit | A: lid, trainer, apart apply; B: lid, apart activate; conflict, dubbel verzoek, rollback na fout, restore als nieuwe versie | Toepasroute sluiten; oud plan blijft bestaan; terugzetten alleen via nieuw goedgekeurd voorstel |
| 6. Herstel/check-in19 en Vandaag20 | `windows.cjs`, `planning.py`, `outbox.py`; kandidaat46 voor transactionele outbox, geen echte push | Bronvensters, tijdzone/DST, check-inoptie, ontdubbeling, intrekking en verlies van antwoord na commit; serverklok expliciet | Nieuwe verwerking/delivery uit; niet-bezorgde events niet opnieuw als nieuw voorstellen; historie behouden |
| 7. Samengestelde historische workoutbediening | `workout12.cjs`, `composed_store.py`; dezelfde login, afzonderlijke historische workspace | Expliciet starten/afronden, partial blijft partial, oorspronkelijke snapshot, geen auth/workspaceverwisseling; niet automatisch onderdeel van slice1 | Lifecycle-ingang uit; minimale registratie en vorige closures niet verwijderen |
| 8. Voorkeuren en leesbare eenheden | `presentation.cjs`, `display.js`; originele meetwaarden/eenheden blijven leidend | NL/EN/DE, thema, metric/imperial display, herladen; voorkeur wijzigt geen voorschrift of eerdere goedkeuring | Voorkeursingang sluiten zonder bronwaarden om te rekenen |

Deze selectie hergebruikt dezelfde lokale app, geen acht nieuwe demo's. De
frontendnavigatie kan lokaal samen werken terwijl serveracties afzonderlijk
default-off worden vrijgegeven. Lokale migratie45 ondersteunt meerdere onderdelen;
dat is geen reden om alle acties bij de eerste hosted slice aan te zetten.

## Nog geen uitvoerbare release

- Volledige actuele workout-/maaltijdregistratie21: owneracceptatie ontbreekt;
  serverweigering blijft actief. Historische registratie12 vervangt die niet.
- Duurzame browserconcepten voor historische registratie/herstel zijn lokaal
  geintegreerd en in CI38746007554 bewezen. Geen automatische verzending,
  goedkeuring/toepassing of21-invoer in de wachtrij. Een volledig offline
  opstartbare shell en gecachte offline login zijn niet gebouwd/vrijgegeven.
- Free/Pro/AI: read-only proefperiode-/terugvalcontract bestaat. Autoritatieve
  uitgifte/abusebescherming is Phase7; exacte final-day/tijdzonebezorging blijft
  een open productregel. Geen betalingen of entitlementwijzigingen activeren.
- Badges/streaks, sport, wearables en media: geen complete bron-/kwaliteitsregels
  afleiden uit de roadmap. Echte providers en foto/videoanalyse blijven apart.
- Medische, voedingskundige, taal-, privacy- en juridische reviews, consent en
  providervoorwaarden voor echte leden blijven buiten deze synthetische PASS.

## Checkpoint

Het actuele werkregister benoemt uitvoerbare functies, afhankelijkheden en tests.
Een volgende sessie begint met gitstatus en behoudcontrole, niet met reset of
hergebruik van een verbruikte hosted poging. De112 historische meetparen blijven
geldig binnen hun oorspronkelijke scope; stap113 blijft incompleet.
