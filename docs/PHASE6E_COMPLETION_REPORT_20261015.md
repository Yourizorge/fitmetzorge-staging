# Gecombineerd afbouwrapport, 15 oktober 2026

## Eindstand

**6E-11 hosted: NO-GO. Lokale integratie: CI PASS. Ownertelefoontest: NO-GO.**
De oude utility-oorzaak blijft volgens ownerbesluit UNKNOWN. De nieuwe proef
heeft een eigen, aantoonbare stopreden. Geen oude mislukking is gepromoveerd.
De ene vrijgegeven nieuwe hosted poging is gebruikt; geen tweede gestart.

## Nieuwe Hosted Proef

Run: `acd473d0-5a81-4aca-928a-3907b2bda3a3`.
Tijdvak inclusief toegangscontrole/intrekking: 10:47:50-10:48:19 Nederlandse tijd.
Toelating: CI38707409636, bron1ce8d3f29c100c1f72db28017b43db165afaf684.
De huidige projectbinding, beveiligde verbinding en43 migrations zijn bevestigd.
De meettransactie was expliciet read-only. SSL-enforcement, CA- en hostcontrole
zijn behouden; geen geheim is gepubliceerd.

De negende FETCH bracht de overdracht op73.728 hashes bij een limiet van65.536.
De proef stopte bij `stream_row_ceiling`, nog voordat de nulmeting compleet was.
Het toenmalige SQL filterde uitgesloten rijen pas na overdracht in de client.
Hoeveel rijen per hosted tabel hiervan de oorzaak waren, is niet vastgelegd en
wordt niet verzonnen. Geen nieuwe scan is uitgevoerd om dit achteraf te raden.

| Bewijs | Resultaat |
| --- | --- |
| Werkelijk SQL-verbruik |31/2.226: preflight4, nulmeting/protocol27 inclusief rollback |
| Uitvoeringstijd | Worker9,625s; meter tot rollback11,438s |
| Utility-voor/naparen |10 compleet, alle met eenduidige querytoerekening |
| Eigen tijdelijke writes |0 blokken |
| Achtergrond-tempdelta |0 bytes in deze meetvensters; geen globale herstelclaim |
| Eigen gemeten WAL |1.196.543 bytes; niet gelijkstellen aan applicatie-DML |
| Langste gemeten statement |510,291ms |
| Beschermde datavergelijking |Niet compleet; geen volledige databehoud-PASS |
| Applicatie-/Auth-/fixturewrites |Niet begonnen; uitsluitend read-only SQL |
| Tijdelijke JIT |Ingetrokken en uitgeschakeld,0 mappings |
| Eigen tijdelijke guards/observers |Niet geinstalleerd |
| Hosted migrationstand |43; kandidaat44 niet toegepast; geen nieuwe hosted dry-run |
| Oude fixtures/bewijzen |Niet opgeruimd of gewijzigd;112 paren en incomplete113 behouden |

De85 nieuwe bewijsbestanden zijn ongewijzigd gearchiveerd. Manifest:
`972c30c5c80536df40af0fbabef6813cf844f9c7b44c86e7bf6437c03987c97a`.
[Details en bewijsverwijzingen](PHASE6E11_RESERVED_RUN_20261015.md).

## Correctie En Lokale Bewijsketen

De offline correctie gebruikt exact dezelfde uitsluitingsvoorwaarden, nu voor
hashing en transport. Geen nieuwe uitgesloten tabel, ruimere rijlimiet of timeout.
NULL-behandeling en dubbele beschermde rijen blijven behouden. Nieuwe fouten
krijgen een concrete gesanitiseerde fase/reden en de query-/bronbinding wordt
voor de overdracht opgeslagen. Deze correctie is niet opnieuw hosted uitgevoerd.

CI38710056451 is volledig PASS: schone44/44,169 Python- en131 JS-tests,33
migrationcontroles,18 lokale Auth-controles,71 meetparen,295 writes waaronder
123 deletes, drie echte foutpaden en zes PG17-equivalentiecontroles. De gerichte
synthetische test transporteert4 beschermde rijen in plaats van73.728, met exact
dezelfde multiset inclusief NULL en duplicaten. Dit bewijst niet hoeveel
beschermde rijen de actuele hosted database bevat; de limiet blijft hard.

Bron: `037f819e8248485f88e702217974a8b8b55be7f5`.
Kandidaat: `477235001cf0ae9ea62e11411283e365fb5ef5265132acbcec0d5fc15006090a`.
Archief: `0fb949ba9d392b45dc1a11a1e718c45eb69b054706fad1d00a96811ff7d9168c`.
Werkelijk lokaal verbruik2.154; normale capaciteit2.196; zwaarste pad2.207.

| Fase | Gereserveerde capaciteit |
| --- | ---: |
| Projectcontrole |4 |
| Migration |42 |
| Nulmeting |51 |
| Inrichting |33 |
| Guard |13 |
| Auth |318 |
| Controller |286 |
| Route A |191 |
| Route B |286 |
| Terugzetten |54 |
| Meetregistraties |126 |
| IO-bewaking |97 |
| Cleanup |633 |
| Eindmeting |61 |
| Afsluiting |1 |
| Normaal totaal |2.196 |
| Zwaarste toegestane fout-/afsluitpad |2.207 |

De archieflezer vereiste een beperkte correctie van1.400 naar1.410 bestanden
om de werkelijk aanwezige1.406 entries te lezen. Alle pad-/hash-/bytecontroles
bleven intact;11 lokale negatieve extractietests PASS. Het originele ZIP bleef
bewaard. Dit is geen verhoging van een hosted budget of nieuwe CI-uitvoering.

## Onafhankelijke Integratie

CI38710983711 is PASS op bron3288eb046abf08ddc4d44eb0752645e0ca15f599:
schone46/46 met uitsluitend lokale kandidaten45/46. De eerdere mislukte
CI38710026337 wegens ontbrekend driverpad in een los testproces blijft bewaard.

Gebouwd en opnieuw bewezen: gedeelde opslag/rollen, registraties en correcties,
historische snapshots, vergelijkingsvensters, proactieve signalen, beperkte
brongebonden voorstellen, Route A/B, outbox, check-inplanning en Vandaag-bediening.
Afzonderlijke bevestiging/toepassing, conflictsituaties, idempotentie, rollback,
opnieuw inloggen en behoud van oude versies worden met lokale PG17/Auth getest.

- Minimale registratie12:25 database-,15 browser- en4 Auth-controles.
- Gezamenlijke kandidaat:62 database-,209 browser- en4 Auth-controles.
- Aanvullend:29 domeintests,12 SQL-regressies,33 M44-rechtencontroles,
  15 nieuwe scope/transport-unittests en zes PG17-filtercontroles.
- NL/EN/DE, licht/donker, mobiel390 en desktop1280: browseremulatie,
  geen nieuwe fysieke ownerhandelingen geclaimd.

Kandidaat: `ce8c729e322c05e1281a773a732d686c64556f086461f2122de90017629e0342`.
Archief: `0076c471780cb5b6f83d9efa885c7cc88804f7a7b2a6edee24871a27d3a3b8fa`.
De78 geselecteerde bewijzen en het release-dossier staan onder
`_offline/phase6e_server_v1/receipts/ci-38710983711-completion/`.

## Eerstvolgende Release, Nog Niet Vrijgegeven

Registratie12 is apart afgebakend: alleen historische registratie/feiten, M45,
exacte workspace/lidkoppeling, RLS, actuele vervaltijd en een standaard uitgeschakelde
ingang. Geen M46-outbox, planactivering of package21. De nieuwe private
transportkandidaat heeft geen listener; zijn unit-Auth-responses zijn synthetisch.
Dat is geen hosted transportbewijs. De echte lokale Auth-tests gebruiken de
bestaande loopbackadapter.

Het release-dossier telt970 werkelijk gemeten lokale SQL-commando's: migration47,
CI-isolatie/herstel16, dry-run2, numerieke observers16, fixture/admin26,
Auth488, registratie/transacties365 en meterconfiguratie/afsluiting10.
Dit is geen hosted maximum. Voor de toekomstige geselecteerde release ontbreken
nog de daadwerkelijke drie-account Auth/guard/meetlifecycle, integraal gemeten
hosted-kandidaatregister en toelating op de dan geldige bronnen. Die mogen niet
uit de oude4.135-schatting of de lokale970 worden afgeleid.

[Exacte releasegrenzen en rollback](PHASE6E12_SELECTED_RELEASE_BOUNDARY.md).
Rollback schakelt de nieuwe ingang en exacte testsubjecten uit; historie en
audit blijven behouden. Geen migration rewind. Hosted12 blijft afhankelijk van
complete11, fysieke ownerreview en de geselecteerde releasebeslissing.

## Behoud, Publicatie En Vervolg

1.376 bestaande beschermde bestanden gelijk.152 gepubliceerde runtime-assets
byte-identiek in de uitgevoerde controles. Oudere ongecommitteerde wijzigingen
blijven bewust staan; de werkboom wordt niet als schoon voorgesteld.
Alle nieuwe commits bevatten alleen toegestane offline kandidaatcode, kandidaten,
bewijzen en documentatie. Geen nieuwe runtime- of Edge-deployment.
De laatste Pages-/privatepadencontrole en definitieve remote HEAD worden in het
afsluitende chatbericht vermeld; gesanitiseerde publicatiereceipts blijven bewaard.

Er is geen ownertelefoontestlink of vervaltijd: het venster is niet geopend.
Volgende hosted stap vereist een afzonderlijk vrijgegeven nieuwe poging, nieuwe
runidentiteit en actuele brongebonden toelating. De gebruikte poging wordt niet
heropend. Geen automatische freeze, owneracceptatie of bulk12-21-activatie.
Een aanvullende lokale startguard weigert de gebruikte run ook in een verse
checkout op basis van het gecommitteerde bewijs, nog voor netwerk/toegang.
Zeven gerichte gate-tests PASS; deze extra blokkade is geen nieuwe hosted toelating.
6E-21 blijft pending. Medische, voedings-, taal-, privacy- en juridische reviews
worden niet vervangen door technische tests.

External AI calls/cost:0 / EUR0.00. Real-member AI enabled:NO.
Production touched:NO. APPFMZ, website en JARVIS niet gewijzigd.
