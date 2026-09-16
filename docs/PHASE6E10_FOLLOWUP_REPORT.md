# 6E-10 Follow-up: ownermatch, databehoud en retestvenster

TECHNICAL PASS / READY FOR OWNER REVIEW - SYNTHETIC STAGING ONLY.
Geen owneracceptatie/freeze van 6E-10. Phase 6E blijft onvoltooid; 6E-11 niet gestart.

Dit rapport volgt op het ongewijzigd bewaarde
[read-only onderzoeksrapport](PHASE6E10_READONLY_INVESTIGATION.md).
De eerdere NO-GO was terecht zolang de accountidentiteit niet bevestigd was.
De owner heeft nu het telefoongebruik bevestigd en onafhankelijk het exacte
loginadres opgegeven. Er is geen stilzwijgende nieuwe nulmeting gemaakt.

## Technische match

- Het bevestigde loginadres matcht exact met de enige JWT-identiteit in het tijdvak.
- Een enkele Auth-sessie, aangemaakt op 16 september 2026 om 08:56:17.931666 CEST.
- 106 gatewayrequests, waarvan 72 authenticated; allemaal dezelfde mobiele Safari-sessie.
- Exacte staging-origin. De referer bevat alleen de origin, niet het volledige paginapad.
- Alle negen betrokken rijen behoren aan deze ene bevestigde owneraccount.
- Geen tweede ingelogde identiteit, service-role JWT/apikey of 6E-10-request in dit tijdvak.
- Een normale wachtwoordlogin, geen synthetische admin/magic-link-testlogin.
- Achtergrond: 20 geslaagde bestaande cronruns (jobs 1 en 7), 4 checkpointregels
  en 5 PostgREST transport-timeoutmeldingen. Geen onbekende cronjob of SQLSTATE-fout.
  De timeoutmeldingen blijven vermeld; ze zijn geen geslaagde autorisatietests.
- De ownerbevestiging plus deze technische koppeling voldoet aan de voorwaardelijke GO.

Het gaat om de onderzochte periode 08:50-09:00 CEST, niet om een universele garantie
tegen credentialmisbruik. Geen wachtwoord, token, link, e-mailadres, IP-adres,
ruwe actor-/sessie-ID of inhoud van chat/gezondheid is in dit matchrapport opgenomen.
[Volledig gesaneerd matchbewijs](PHASE6E10_OWNER_MATCH.json).

## Oorzaak van de negen oorspronkelijke verschillen

| Tabel | Normale apphandeling / functie | Nederlandse tijd |
| --- | --- | --- |
| progress_preferences | fmz_phase5_set_progress_timezone | 08:56:20.592861 |
| workout_sessions | POST workout_sessions, met bestaande owner-RLS/trigger | 08:56:22.310429 |
| member_notifications | fmz_phase6d_mark_notification | 08:56:29.836431 |
| nutrition_preferences | fmz_phase4_set_nutrition_timezone | 08:56:45.778343 |
| member_app_preferences | fmz_phase6d_update_member_settings | 08:57:39.135103 |
| profiles | fmz_phase1_upsert_account_foundation | 08:57:39.954225 |
| user_settings | Dezelfde account-foundationtransactie | 08:57:39.954225 |
| user_onboarding | Dezelfde account-foundationtransactie | 08:57:39.954225 |
| entitlements | Dezelfde account-foundationtransactie | 08:57:39.954225 |

De laatste vier delen dezelfde PostgreSQL-transactie. De bestaande functie zet
updated_at bij een upsert opnieuw, ook als andere waarden gelijk blijven.
De request-, tijd-, account- en transactiemetadata verklaren de route. De oude
hashes bevatten geen individuele oude veldwaarden; er wordt geen volledige
historische veldreconstructie geclaimd.

## Databehoud voor iedere vervolgtest

Er zijn 127 bestaande niet-systeemtabellen gemeten, inclusief applicatie-, private,
Auth-, storage-, cron- en migrationtabellen. Iedere snapshot bevat aantallen en
SHA-256 van de volledige tabel EN van de beschermde cohort. Geen rijinhoud verlaat
de meetquery. De negen tabellen hierboven zijn ook afzonderlijk opgenomen.

35 meetparen tot en met het openen van het ownervenster:
1 read-only preflight, 28 browser/cleanup, 4 publicatie/CLI, 2 owner-opening/cleanup.
Een gedeelde meetgrens is de nameting van de vorige en de voormeting van de volgende
test; er zitten geen testhandelingen tussen die twee toepassingen van dezelfde grens.
Ook tussen de afzonderlijke meetfasen zijn alle beschermde fingerprints gelijk.

Uitsluitend als verwacht veranderlijk behandeld:
- De exact drie synthetische Auth-identiteiten en hun sessie-/tokenmetadata.
- Het synthetische A-lidprofiel tijdens de expliciete trainer-linktest; koppeling hersteld.
- De geauditete 6E-10-window-, bron-, voorstel-, schema- en audit/requests-fixtures.
- Bestaande cron.job_run_details voor de bekende jobs 1, 2 en 7.
  Dit zijn verwachte operationele achtergrondlogs, geen testwrites of memberwijzigingen.

Config, bevoegdheden, identity-registry en alle niet-synthetische gegevens blijven
beschermd. De volledige profiles-tabel veranderde dus tijdens de synthetische test;
de zeven bestaande niet-testprofielen, inclusief het ownerprofiel, bleven gelijk.
Er wordt nadrukkelijk NIET beweerd dat alle 127 volledige tabellen onveranderd waren.

### De negen beschermde cohorten

Hieronder dezelfde fingerprint in iedere voor- en nameting, na de verklaarde
owneractiviteit. De oorspronkelijke 15-september-hashes blijven afzonderlijk bewaard.

| Tabel | Beschermde rijen voor / na | SHA-256 voor EN na |
| --- | --- | --- |
| public.entitlements | 4 / 4 | `5d0fdc0845ac6b84029b1e422412809913732582fd1ab2caf6e41566f03e5e42` |
| public.member_app_preferences | 1 / 1 | `65c19d1faacd13ff5d0a20b07b5334ab3e7064b82bd963f6d6638093ec833b78` |
| public.member_notifications | 12 / 12 | `eebfec7303be087b48506b5cd836e976c923bfafb27b6bfbcc605a4a2e1cf198` |
| public.nutrition_preferences | 2 / 2 | `cc52196284473dc9e9b04e1b1f67c7e98c4ce33bad68a481152f58567ba10d29` |
| public.profiles | 7 / 7 | `2dbee634b2d1ae08bef74889f5c8a85d3d572658ccdb4748f0cb34b2d21d9478` |
| public.progress_preferences | 2 / 2 | `9f03be3969d861de514bc3acbe349d4c7ef3344859498edfd7cef39254a253ee` |
| public.user_onboarding | 3 / 3 | `ca147237194e4193e7e352113f60dd80d5a8c03dc2a96153ede120b8d6eaacf8` |
| public.user_settings | 3 / 3 | `bc5cbf2315eeca1a1658597fb0890889dfda08c98519b3a20113e7f9d57a9d5a` |
| public.workout_sessions | 21 / 21 | `ae04b7ebb0f280abf8703f5bf2fdfce53a48fbc2265cf1017a4ef0a9caca6ed3` |

[Alle fingerprints, aantallen, meetparen en handelingen](PHASE6E10_FOLLOWUP_EVIDENCE.json).
In dat bestand verwijzen table_refs en nine_table_refs naar fingerprint_catalog.
rows/sha256 zijn de volledige tabel; protected_rows/protected_sha256 de beschermde cohort.
Het historische veld nine_unchanged in de meetreceipts slaat op die beschermde cohort.

## Handelingen en cleanup

75 gesaneerd geregistreerde handelingen/pogingen, met actorlabels a_member,
a_trainer, b_member en test_operator. Inclusief geweigerde acties, Auth-sessies,
dezelfde-aanvraag-retry en logout: 75 betekent niet 75 databasecommits.
Succesvolle transacties zijn gekoppeld aan de serveraudit; per test zijn ook alle
tabelverschillen vastgelegd. Geen clientmetadata bepaalt rollen of routes.

De broker maakt uitsluitend voor de bestaande drie synthetische accounts standaard
Auth-testsessies, zonder e-mail. De bestaande beperkte Auth-adminvoorziening blijft
server-side; browser en Edge krijgen geen service-rolebevoegdheid. De nulmeting van
het historische ownergebruik bevat geen dergelijke service-role-request.

- Geen nieuwe accounts gemaakt; nul tijdelijke controleaccounts over.
- Automatisch browser-testvenster ingetrokken en fixtures/workspaces opgeruimd.
- Trainerkoppeling en gecontroleerde consent-/guardfixtures hersteld.
- Gegenereerde testsessies via Auth afgemeld; wachtwoorden niet gewijzigd.
- Minimale bestaande audit-/cleanupreceipts blijven behouden.
- Het aparte ownervenster blijft bewust actief met twee uitsluitend synthetische
  workspaces, bron v1, oorspronkelijke planversie v1 en nul voorstellen.
- Automatisch verval weigert servertoegang. Fysieke fixturecleanup volgt na de
  ownerretest of een afzonderlijke gerichte cleanup na verval; geen scheduler geclaimd.

De oorspronkelijke before.json, data-differences.json, broker.py, evidence.cjs
en het read-only rapport/JSON zijn byte-identiek gebleven. Hun hashes staan in
het matchbewijs en worden opnieuw gecontroleerd door iedere snapshot.

## Tests en publicatie

- Bestaand bewijs: 1.734 regressies, 65 lokale SQL-groepen en 65 strikte hosted groepen PASS.
- Nieuwe daadwerkelijke gepubliceerde UI: 27 functionele controles / 18 layouts PASS.
- Mobiel 390px, tablet 768px, desktop 1440px; NL/EN/DE, licht/donker. Geemuleerd.
- 10 gerichte scope-/Edge-regressies opnieuw PASS.
- 243 beschermde frozen bron-/runtimebestanden byte-identiek.
- 38/38 migration list, oude 34 inhoudshashes ongewijzigd, db push --dry-run leeg.
- Geen nieuwe migration, Edge-deployment, runtimewijziging of providerconfiguratie.
- Pages na auditcommit: 84 assets exact (80 oorspronkelijk + 4 bestaande demo-assets),
  alle 214 getrackte offline/testpaden geven 404.
- Eerste read-only meetaanroep mislukte VOOR testsessies of fixtures; nul functionele
  tests uitgevoerd. Het mislukte rapport is behouden en telt niet als PASS.
  Afzonderlijke hercontrole en de volledige latere meetreeks zijn geslaagd.
- Geen fysieke telefoontest of ownerwachtwoordtest door de agent geclaimd.

Commits tot de definitieve documentatiecommit:
- 03eb55af7ab1897a3c6a12b82fcb5d182e88c4de: bestaande 6E-10-implementatie.
- 7626580962acb9375d28152bf434b4d7578d7020: eerdere read-only NO-GO en bewijs.
- 97e29f6c494e0adb399573e11073b0c62227461c: exacte ownermatch en offline meetinstrumentatie.
De definitieve documentatiecommit/remote HEAD en laatste Pages-resultaat worden
in het opleverbericht vermeld. Die commit verandert uitsluitend offline bewijs/docs.

## Tijdelijk owner-testvenster

Link: [6E-10 Trainerbronnen](https://yourizorge.github.io/fitmetzorge-staging/coach-source-demo/index.html).

Start: 16 september 2026 16:22:25.720 CEST.
Verval: **donderdag 17 september 2026 om 16:22:20.720 CEST** (14:22:20.720 UTC).
Duur: 23 uur, 59 minuten, 55 seconden. Servermatig afgedwongen.
Uitsluitend de drie bestaande synthetische testaccounts; alle andere gebruikers
hebben geen participanttoegang. Alleen de gekozen synthetische A-trainer beheert.
Anonieme toegang, directe private Data API/RPC en A-trainer -> B zijn geweigerd.

### Eenvoudige telefoontest

Gebruik telkens je bestaande wachtwoord bij het gekozen testaccount. Geen nieuwe
mails of wachtwoorden nodig. Bij oude scherminhoud: ververs; bij verlopen login:
uitloggen en opnieuw inloggen. Wachtwoorden/tokens nooit in chat of screenshots.

1. Kies zorgeyouri+6e9-a-lid@gmail.com en Inloggen. Controleer Route A / Lid en
   trainerbron v1. Na Nieuw voorstel maken verschijnen plandoel, registratie en voorstel.
2. Nieuw voorstel maken -> Als lid afwijzen. Het schema mag niet veranderen.
   Maak opnieuw een voorstel -> Als lid accepteren. Status: Wacht op trainer.
3. Uitloggen; kies zorgeyouri+6e9-a-trainer@gmail.com. Test bronconflict VOOR toepassen:
   Nieuwe bronversie -> wijzig alleen de synthetische toelichting ->
   Bronversie vastleggen. Het oude voorstel wordt verouderd en mag niet toegepast worden.
4. Uitloggen; A-lid: Nieuw voorstel maken -> Als lid accepteren.
   Uitloggen; A-trainer: Als trainer goedkeuren. Nog geen schemawijziging.
   Pas Wijziging toepassen maakt planversie v2. Nogmaals toepassen is niet beschikbaar.
5. Uitloggen; A-lid: open de oude planversie v1 -> Terugzetten voorstellen ->
   Als lid accepteren. Uitloggen; A-trainer: Als trainer goedkeuren ->
   Wijziging toepassen. Dit maakt v3; het overschrijft v1 niet.
6. Uitloggen; kies zorgeyouri+6e9-b-lid@gmail.com. Route B heeft geen trainer,
   A-bronnen, A-voorstellen, A-schema's of vensterbeheer. Dit pakket test B-isolatie,
   niet een nieuw autonoom B-coachingvoorstel.
7. Ververs en log opnieuw in: dezelfde synthetische serverstatus moet blijven staan.
   Meld daarna of bronversies, conflict, afzonderlijke stappen, terugzetten,
   B-isolatie en mobiel licht/donker correct werkten.

Voor aanvullende trainerafwijzing/blokkering: doe dat op een nieuw, nog niet
toegepast en door het lid geaccepteerd voorstel; gebruik Als trainer afwijzen of
Als trainer blokkeren. Maak hiervoor eerst een geldige vergelijkbare broncontext.
De automatische test heeft beide terminale routes en W2 met stap 3 kg/uitkomst
43 kg expliciet bewezen. Ongeschikte of onvergelijkbare bronnen mogen blokkeren.
Gebruik Venster intrekken of Fixtures opruimen pas als je klaar bent met de test.

## Open grenzen

L1-L3 en de fysieke ownerretest staan open. Geen 6E-10-freeze.
D1-D12, O1-O5 en W1/W2 blijven ongewijzigd. Alle frozen 6E-0-6E-9-bronnen behouden.
Geen medische vrijgave, echte trainerbronvalidatie, live AI of echte ledencontent als test-/AI-invoer.
Medische, privacy-, juridische, taal- en eventuele toekomstige providerreviews blijven
voor echte inzet gelden. Geen echte push/e-mail, externe AI-calls of nieuwe kosten.
Production touched: NO.
