# 6E-11 Migration 41: Clean CI Follow-up

24 september 2026. Alleen Yourizorge/fitmetzorge-staging, main, mokxyyullfhkfalopbzd.

**Schone CI-opbouw: PASS. Hosted toepassing en ownertelefoontest: NO-GO.**

Dit is een nieuw vervolg op PHASE6E11_MIGRATION41_REPORT.md. Het oorspronkelijke
rapport, zijn mislukte lokale opbouw en alle historische bestanden blijven ongewijzigd.
Deze receipt vervangt geen ontbrekend hosted meetpaar en verleent geen owneracceptatie.

## Uitgevoerde Fase 1

De Windows-machine mist Docker/WSL en de echte pgcrypto-, pg_trgm- en pg_cron-
extensies in de lokale PG17-bundel. De ontbrekende psql.exe op het oorspronkelijke
runnerpad was slechts de eerste fout; een ander clientpad lost de extensies niet op.

Een tijdelijke standaard ubuntu-24.04 GitHub-runner bouwde daarom een lege
Supabase-platformdatabase. Alle 41 canonical migrations zijn byte-identiek en
afzonderlijk in oorspronkelijke volgorde toegepast. Geen mockextensies, seeds met
ledengegevens, gekoppeld hosted project, overgeslagen migration of geschiedenisreparatie.

- CLI: 2.117.0, officiele release gecontroleerd met SHA256.
- PostgreSQL: 17.6 (server_version_num 170006).
- Image: public.ecr.aws/supabase/postgres:17.6.1.167.
- Image digest: sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb.
- Geinstalleerd: pgcrypto 1.3, pg_trgm 1.6, pg_cron 1.6.4.
- Volledige CLI-, image-ID-, bron- en bewijsmanifesthashes: PHASE6E11_MIGRATION41_CI_RECEIPT.json.
- [Geslaagde run 36034533557](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/36034533557).
- Immutable CI-kandidaat: 58 bronbestanden, SHA256
  34977f2d3533bf5016ead342062249ef79386e722983b78e4b84b327104a4413.
- Alle 58 werkboombestanden en 186 ontvangen bewijsbestanden opnieuw hash-gecontroleerd.

Deze standaard openbare runner gebruikte alleen joblogs, geen betaalde runner,
artifactopslag, cache, externe AI of Supabase-secrets. De owner gaf afzonderlijk
toestemming voor openbaar maken van migrations 39/40/41 en common.py/test_audit.py.
De overige kandidaatinhoud was al openbaar. Geen historische databasebewijsbestanden
of echte rijen opgenomen in de CI-kandidaat.

## Tests En Beveiliging

| Controle | Nieuw resultaat |
| --- | --- |
| Schone schemaopbouw en exacte historyvolgorde | 41/41 PASS |
| Bestaande transactionele SQL-regressies | 12/12 suites PASS |
| Migrationidentiteit | 12/12 tests PASS |
| Bestaande private auditkern | 22/22 tests PASS |
| Nieuwe private bridge: toegangsweigeringen | 16/16 PASS |
| Lokale CI-contracttests | 14/14 PASS |
| Bestaande private functiecatalogus voor/na migration 41 | Exact gelijk |
| Lokale Supabase db-push dry-run | EMPTY |
| Nieuwe bridge: advisor WARN/ERROR, lintfouten | 0 |
| Hosted JWT/Auth/workflowbewijs | Niet uitgevoerd; niet door CI vervangen |

Beide nieuwe functies zijn SECURITY INVOKER met search_path=pg_catalog, pg_temp.
Alleen postgres heeft uitvoerrechten. PUBLIC, anon, authenticated, service_role en
een onbevoegde testrol hebben geen toegang. Beide tabellen hebben RLS, geen
clientpolicies en alleen postgres-rechten; control staat standaard uit.
Geen publieke wrapper, nieuwe loginrol, service-role-secret in runtime of RLS-omweg.
De bestaande Edge-route bereikt de nieuwe private entry nog niet.

De actuele officiele Splinter-advisors zijn read-only en versiegebonden uitgevoerd:
e74a9e36cb12258cb67d1464bc1cb196e9cd8446, bron-SHA256
d8d558baad3e03832e521c527907fa50a9a172fabd899dd0f5c2504a5a0e9349.
Bestaande meldingen blijven: 47 RLS-initplan-WARN, 67 authenticated-definer-WARN,
1 mutable-search-path-WARN; 71 RLS-zonder-policy-INFO, 21 ongeindexeerde-FK-INFO
en 108 unused-index-INFO. Die laatste aantallen horen bij een lege CI-database.
Er zijn geen advisor-ERRORs of nieuwe bridge-WARNs. Dit is geen globale
security-vrijgave; hosted Auth-configuratie en bestaande waarschuwingen blijven apart.

## Twee Behouden CI-Fouten

1. Run 36032822899 bouwde alle 41 migrations, maar de historische 6A-test miste
   de later ingevoerde private-chattoestemming en synthetische leeftijdscontext.
   Een aparte hash-gebonden CI-adapter bewijst eerst de juiste weigering en voegt
   vervolgens uitsluitend deze synthetische voorwaarden toe. Iedere oorspronkelijke
   assertie en het originele testbestand blijven behouden.
2. Run 36033774034 bouwde alle 41 migrations en doorliep de regressies, maar de
   read-only advisorwrapper scheidde een upstreamquery zonder slotpuntkomma niet
   van ROLLBACK. De wrapper kreeg een expliciete scheiding met twee grenstests.

De derde run slaagde volledig. Geen automatische retry of hosted belasting door
deze CI-runs. Geen canonical migration aangepast om een test groen te maken.

## Git En Runtime

Canonical broncommit: d34799e1b4764572b8b8386691fafbe204bb1de8.
Migration 41 SHA256:
4d474becdc5c3a7343562602115f9333b5cffc6bed0c323fca3abc560843af7d.

Commits:
- 68ad3d365414e94aafc49cf76c6092f01e1b6ced: geisoleerde CI-gate.
- fe20405837dfda054f35aadea8a36891f812341d: aparte consentfixture-adapter.
- 4505ec03656adb3e0c21bdafdfa179f7f6527da5: advisorquerygrens.
- d34799e1b4764572b8b8386691fafbe204bb1de8: bewezen canonical bronnen en LF-regels.

Alleen CI, tests, canonical SQL-bronnen en documentatie worden gepusht.
Een broncommit is geen hosted migrationtoepassing. De actuele runtime blijft
ongewijzigd; ook alle bestaande ongecommitteerde runtimecorrecties blijven behouden.
De eindcontrole koppelt remote HEAD, Pages-resultaat, 84 live runtimehashes,
88 lokale kandidaatassets en HTTP404 voor offline-/testpaden. De actuele
publicatiereceipt wordt afzonderlijk lokaal bewaard en in het eindbericht benoemd.

363 bestanden uit het oude bewijsmanifest zijn opnieuw hash-gecontroleerd.
189 frozen bestanden zijn in deze werkronde gelijk bevonden. De 112 historische
meetparen en incomplete stap 113 blijven historisch, zonder retroactieve PASS.

## Hosted Stop En Databehoud

Lichte afsluitende metadata op 24 september 2026 om 19:55:43 Nederlandse tijd:
PG17.6, 40 migrations, nieuwste 20260924130052, bridgeschema afwezig,
nul andere actieve clientqueries en nul IO-wachters. De laatste CLI-dry-run
noemt uitsluitend migration 41. Dus **41 lokale bronnen / 40 hosted; niet leeg**.
Een hosted hash van migration 41 bestaat nog niet en wordt niet verzonnen.

De eigenaar kent het bestaande databasewachtwoord niet. De geteste native
TLS-meetclient vereist een veilige lokale credential en een geverifieerd CA-bestand.
Geen wachtwoord verkregen of gereset, geen geheim in Git/chat/logs, geen
uitvoeringsbeleid of certificaatcontrole versoepeld. Het lokale invoerscript
werd door Windows-beleid geweigerd; de bestaande Windows-invoer is aangeboden.
Er is geen opgeslagen credential door deze assistent aangemaakt.

De gezonde momentopname is geen volledig Disk-IO-budget- of databehoudsbewijs.
Geen nieuwe volledige tabelscan, oude zware fingerprintquery, hosted bridgeactie,
Auth-test, canary of cleanup uitgevoerd. Hosted canarygebruik: 0 acties, 0 cycli.
De limieten blijven 1 collector, 3 cycli, 128 querycommando's en geen retries.
Read-only cataloguscontroles en de normale tijdelijke CLI-loginrol worden
onderscheiden van app-/Auth-/memberwrites; laatstgenoemde zijn hier niet uitgevoerd.
Beschermde rijhashes zijn niet opnieuw gemeten. Geen claim van een nieuw
voor-/nameetpaar of een verklaarde achtergrondmutatie zonder dat bewijs.

CI-omgevingen zijn tijdelijk; alle lokale en hosted historische fixtures/bewijzen
zijn behouden. Geen nieuwe synthetische hosted fixtures gemaakt. Geen cleanup
van eerdere twee workspaces, controleaccounts of historische testsessies.
Geen Edge-deployment, owner-testvenster, vervaltijd, freeze of 6E-12.

## Exacte Volgende Stap

Eerst een bestaande stagingdatabasecredential veilig lokaal beschikbaar maken,
bijvoorbeeld uit de eigen wachtwoordbeheerder. Niets in de chat plaatsen.
Een reset is niet uitgevoerd en wordt niet uit deze ontbrekende credential afgeleid.

Daarna TLS/CA en de exacte serververbinding bewijzen, beschermde scoped metingen
vastleggen, migration 41 toepassen, hosted 41/41-SQL-identiteit en lege dry-run
bewijzen. Real-JWT/servertransport, observers, noodzakelijke Auth-routes en de
begrensde workflowproef blijven verplichte afzonderlijke gates. Alleen na volledige
databehouds- en cleanup-PASS kan een tijdelijk owner-testvenster worden geopend.

Bronnen: [Supabase CI](https://supabase.com/docs/guides/deployment/ci/testing),
[SSL en verify-full](https://supabase.com/docs/guides/platform/ssl-enforcement),
[Advisors](https://supabase.com/docs/guides/observability/advisors),
[Changelog](https://supabase.com/changelog).
SSL-enforcement wijzigen veroorzaakt een databaseherstart; dit is niet gedaan.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
