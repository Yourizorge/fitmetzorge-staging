# 6E-10: onderzoek en eindstand van de onderbroken verificatie

Status: VERIFICATION BLOCKED / NOT READY FOR OWNER RETEST.
Geen owneracceptatie, freeze of 6E-11-start. Onderzoek afgerond op 16 september 2026.

## Wat al was uitgevoerd

6E-9 is owner-accepted/frozen. Het oude venster is gesloten, oude sessies zijn
ingetrokken en de drie synthetische accounts met bestaande wachtwoorden zijn behouden.
Commit `f3a1fc8ea5274938ad1eff77a115b438421b6ede` legt dit vast.

Commit `03eb55af7ab1897a3c6a12b82fcb5d182e88c4de` bevat de gebouwde 6E-10:
onveranderlijke trainerbronversies, brongebonden voorstellen/goedkeuringen,
afzonderlijk atomair/idempotent toepassen en terugzetten, W1/W2 en maximaal
24 uur geldige vensters voor exact drie synthetische identiteiten.
Alleen de aangewezen synthetische A-trainer heeft de beperkte beheerbevoegdheid.
Route B blijft in dit pakket een afgeschermde isolatiecontrole.

Vier nieuwe additieve migrations en de nieuwe `fmz6e10-synthetic` Edge Function
waren voor de onderbreking al op staging gepubliceerd. De oude 34 migrations
zijn inhoudelijk ongewijzigd; totaal nu 38. Geen nieuwe migrations in dit onderzoek.
Pages-run 35074169463 was succesvol voor de implementatiecommit.
De aparte demo is gepubliceerd, maar er is GEEN actief owner-testvenster.

## Waarom werd gepauzeerd?

De oorspronkelijke nulmeting van 15 september 2026 14:46:55 UTC bevat 68
tabelvingerafdrukken van de bestaande cohort, buiten de drie synthetische accounts.
59 bleven gelijk; negen verschilden, zonder gewijzigde aantallen rijen.
Dit is een echte inhoudelijke hashafwijking, niet alleen sorteervolgorde of tijdzone.
De oorspronkelijke nulmeting is behouden; niets is teruggezet of stilzwijgend herijkt.

## Wat het read-only bewijs laat zien

Onderzochte logs: 16 september 2026 06:50-07:00 UTC, dus 08:50-09:00 Nederlandse tijd.
106 gatewayrequests, niet afgekapt; 72 met een authenticated JWT.
Alle 72 horen bij dezelfde bestaande account/sessie, buiten de drie 6E-10-identiteiten.
Het account bestaat sinds 15 augustus. De sessie begon op 16 september om
08:56:17 Nederlandse tijd met een succesvolle gewone wachtwoordlogin.
De browsermetadata vermeldt mobiele Safari en de staging GitHub Pages-origin.
Dat zijn ondersteunende metadata, geen bewijs van de fysieke persoon of het apparaat.

Er zijn in dit afgebakende tijdvak geen service-role JWT-requests, geen 6E-10-paden
en geen requests van de drie ingeschreven synthetische identiteiten gevonden.
De testbroker gebruikt voor die drie accounts een andere, magic-link-verificatieflow
zonder e-mail. Die flow verklaart deze gewone wachtwoordlogin niet.

In elk van de negen tabellen is precies een na de nulmeting bijgewerkte rij gevonden,
telkens van dezelfde niet-ingeschreven account. De requestpaden en transactiemetadata
passen bij de reeds bestaande gewone appfuncties:

| Tabellen | Request / databasepad | Laatste wijziging, Nederlandse tijd |
| --- | --- | --- |
| progress_preferences | fmz_phase5_set_progress_timezone | 08:56:20.592861 |
| workout_sessions | POST workout_sessions, bestaande owner-RLS/trigger | 08:56:22.310429 |
| member_notifications | fmz_phase6d_mark_notification | 08:56:29.836431 |
| nutrition_preferences | fmz_phase4_set_nutrition_timezone | 08:56:45.778343 |
| member_app_preferences | fmz_phase6d_update_member_settings | 08:57:39.135103 |
| profiles, user_settings, user_onboarding, entitlements | fmz_phase1_upsert_account_foundation | 08:57:39.954225 |

De laatste vier delen exact dezelfde PostgreSQL-transactie. De bestaande
account-foundationfunctie werkt deze eigen-accounttabellen bij en zet updated_at
op now(), ook wanneer een deel van de waarden inhoudelijk gelijk blijft.
De onderzochte functies gebruiken auth.uid(); workout-RLS controleert de eigenaar
bij lezen, schrijven en wijzigen. Geen 6E-10-trigger schrijft deze bestaande tabellen.

## Wat niet bewezen is

De technische route is goed verklaarbaar als gewone stagingappactiviteit. Er is
in het onderzochte bewijs geen aanwijzing gevonden voor een 6E-10-fixturelek of
service-rolemisbruik. Dit is NIET hetzelfde als bewezen legitiem menselijk gebruik.
De owner herkende de activiteit niet. Een geldige wachtwoordlogin kan niet aantonen
wie het wachtwoord gebruikte of uitsluiten dat een credential eerder is uitgelekt.
Een referer of browsernaam is evenmin identiteitsbewijs.

Er is geen volledige historische voor/na-rijaudit: log_statement is ddl en
track_commit_timestamp staat uit. De oorspronkelijke tabelhashes bevatten geen
oude veldwaarden. Request-/tijd-/transactiekoppeling is sterke ondersteuning,
maar geen volledige forensische reconstructie van iedere eerdere wijziging.
Een beperkt logtijdvak kan niet alle mogelijke ongeautoriseerde toegang uitsluiten.
Daarom is de aanvullende voorwaardelijke GO nog NIET aantoonbaar vervuld.

## Verificatie die wel gereed is

- 1.734 contract-/frozen regressies geslaagd, geen failures of skips.
- 65 lokale PostgreSQL-testgroepen geslaagd; minimale Auth-stubs, geen volledige Supabase-stack.
- 65 strikte hosted Auth/Edge/SQL-groepen geslaagd; technische 503 telt niet als toegangsweigering.
- 27 browsercontroles met lokale UI en echte synthetische stagingbackend geslaagd.
  18 geemuleerde combinaties mobiel/tablet/desktop, NL/EN/DE en licht/donker.
- Verse checkout van 03eb55a: 10 gerichte tests en 65 lokale SQL-groepen geslaagd.
- 243 frozen bron-/runtimebestanden behouden, waaronder alle 80 bestaande publieke assets.
- Eerdere Pages-controle: 84 assets byte-identiek aan Git (80 bestaand + 4 nieuwe demo-assets);
  alle 209 toen getrackte offline/testpaden 404.
- Oude 34 migrationregistraties inclusief inhoudshashes identiek; 38 totaal.
- Herhaalde CLI-controle: migration list 38/38 gelijk; db push --dry-run leeg.
- Gerichte lokale nacontrole van deze rapportage: 10 scope-/Edge-tests geslaagd,
  protected-files controle geslaagd, git diff --check zonder fouten.
- Laatste read-only controle: nul actieve vensters, nul synthetische workspaces,
  drie ingeschreven identiteiten en een aangewezen beheerder.

De volledige workflow tegen de gepubliceerde UI, de finale data-gate en het
nieuwe fysieke owner-testvenster zijn NIET afgerond. Geen fysieke telefoontest
geclaimd; bestaande wachtwoorden zijn niet getest, gewijzigd of gepubliceerd.
Historische mislukte tests blijven historische mislukte tests.

## Exacte vervolgstap

De owner moet via de bestaande beveiligde Supabase Auth-beheeromgeving laten
vaststellen of de niet-synthetische account/sessie met aanmaaktijd
16 september 2026 08:56:17 Nederlandse tijd bewust en bevoegd is gebruikt.
Vraag geen wachtwoord, token of sessiegeheim op en plaats die niet in de chat.
Benodigde uitkomst: bevestiging van de bevoegde gebruiker en de genoemde appactiviteit,
of expliciet dat de activiteit onbekend blijft. Dit is geen vraag om blind akkoord.

Bij bevestigde legitieme activiteit: oorspronkelijke afwijkingen blijven in het
bewijs staan; daarna een afzonderlijke, verklaarde nieuwe voor/na-meting voor de
resterende synthetische publicatietest, vervolgens pas een vers <=24h ownervenster.
Bij onbekende activiteit: securityonderzoek voortzetten, geen testvenster openen.
Er is nu geen nieuwe baseline, rechtenverruiming, credentialrotatie of dataterugzetting uitgevoerd.

## Grenzen en bewijsbestanden

Tijdens dit vervolg alleen read-only Supabase-onderzoek en lokale bewijs/documentatie.
Geen normale app, database, Edge, Auth-account of autorisatie gewijzigd.
Geen echte chat-/gezondheids-/foto-/schema-inhoud opgehaald of in fixtures gekopieerd.
Alleen minimaal noodzakelijke account-, tijd-, ownership- en aggregaatmetadata onderzocht.
Geen secrets, ruwe actor-/sessie-ID's of volledige persoonsgegevens in het rapport.
Geen externe AI-calls, e-mails, nieuwe kosten, productie of andere repositories.

[Gesaneerde metadata](PHASE6E10_READONLY_INVESTIGATION.json).
[Bestaande testbewijzen en expliciete blokkade](PHASE6E10_VERIFICATION_PENDING.json).
[Implementatierapport](PHASE6E10_TECHNICAL_REPORT.md).

Gebruikte actuele primaire documentatie: [Supabase changelog](https://supabase.com/changelog),
[logfilters](https://supabase.com/docs/guides/observability/advanced-log-filtering),
[Auth auditlogs](https://supabase.com/docs/guides/auth/audit-logs).
De ClickHouse logs-route is gebruikt; ontbrekende logregels worden niet als bewijs
van afwezigheid van activiteit behandeld.
