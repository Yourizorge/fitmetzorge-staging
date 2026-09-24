# 6E-11 Secure Hosted Access: Read-only Follow-up

24 september 2026. Alleen Yourizorge/fitmetzorge-staging, main,
Supabase mokxyyullfhkfalopbzd. Start-HEAD 6156e585d87f138b322549157797580f7c9f6f0a.

**NO-GO voor migration 41, hosted workflow en ownertelefoontest.**
De schone CI-PASS blijft geldig. Er is nu wel een bestaande veilige tokenbron
en aantoonbaar een tijdelijke CLI-loginvoorziening gevonden. Het vaste
databasewachtwoord is niet teruggevonden. De volledige native verbindingscontrole
heeft nog geen PASS; een reset is NIET als noodzakelijke oplossing bewezen.

## Bestaande Bronnen

| Bron | Read-only resultaat |
| --- | --- |
| Process-, user- en machine-environment | Geen relevante databasecredentialvariabelen |
| Gitignored .env-bestanden in werkrepository | Geen gevonden |
| Gecontroleerde gekoppelde CLI-werkmap .env-paden | Geen gevonden |
| Windows Credential Manager | Een bestaande Supabase CLI-tokenbron; veilig in geheugen gebruikt |
| Specifieke ownerdatabase- en tijdelijke credentialtargets | Geen opgeslagen databasecredential |
| pgpass / pg_service op standaard Windows-paden | Niet aanwezig |
| Supabase CLI-configuratie | Projectgebonden session-pooler, geen opgeslagen password in die URI |
| Repository Actions-secrets | Geen |
| Environment github-pages-secrets | Geen |
| Organisatiesecrets | Niet van toepassing op deze persoonlijke GitHub-repository; endpoint gaf 422 |
| Password-managerconnector | Niet beschikbaar in de actieve tools |

Geen brede scan van andere repositories, wachtwoordkluizen, browserprofielen,
persoonlijke documenten of CLI-tracelogs uitgevoerd. Geen secretwaarde afgedrukt
of opgeslagen. Bestaande GitHub-authenticatie is alleen voor secretmetadata gebruikt.

De nieuwere PAT/JIT-databasetoegang is op dit project niet beschikbaar:
ssl_enforcement_required. SSL enforcement staat uit. Die optie inschakelen kan
een databaseherstart veroorzaken; geen instelling, mapping, rolrecht of
netwerkrestrictie daarvoor gewijzigd.

De afzonderlijke, bestaande officiele CLI-loginroute werkt wel:
POST /v1/projects/{ref}/cli/login-role met read_only=true levert een tijdelijke
managed login en TTL 300 seconden. Dit is geen reset van postgres of een
wijziging van een echt ledenaccount. Er zijn geen rechten aan een appclient gegeven.

## CA En TLS

Het certificaat is gedownload via de exact waargenomen link in de officiele
Database Settings van het stagingproject:
https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt

- CA SHA256: 700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7.
- Alleen opgeslagen onder de gitignored supabase/.temp-evidencepaden.
- Directe projecthost: lokale DNS-resolutie mislukt (gaierror 11001);
  geen credential of SQL naar die host verzonden.
- Reeds projectgebonden session-pooler: poort 5432, TLS 1.3.
- CA-keten en hostnamecontrole geslaagd, equivalente Python verify-full-handshake.
- Peer-certificaathash:
  03709ca44d1b06e4504da0a83b6ca065761edc704cd5634bcc3894fd5c7b3248.
- Native libpq gebruikt expliciet sslmode=verify-full en dit sslrootcert.
  Geen terugval naar require/prefer/disable, geen installatie in globale truststores.

De eerste native verbinding bereikte met de tijdelijke read-only login een
metadataquery. De geteste LocalDB.rows-reader is ongewijzigd hergebruikt.

## Twee Afzonderlijke Probe-uitkomsten

1. 20:27:15 Nederlandse tijd: tijdelijke login en native TLS-connectie bereikten
   de metadatafase; de metadata-assertie stopte. De eerste foutreceipt bewaart
   fase en foutcode maar niet de afgewezen metadatavelden. De exacte eerste
   waardeafwijking is daardoor niet achteraf bewezen en wordt niet ingevuld.
2. De adapter is lokaal gericht verbeterd: expliciete BEGIN READ ONLY,
   metadatavelden bewaren VOOR validatie, en client-TLS onderscheiden van
   pg_stat_ssl van de upstream pooler/databasehop. Acht lokale tests slagen.
   Een afzonderlijke gecorrigeerde poging op 20:29:10 werd al bij verbinden
   geweigerd. De oude foutreceipt is niet overschreven.

De gesanitiseerde projectlogs bewijzen voor de tweede poging:
supavisor_logs, password_authentication_failed, een gebeurtenis op
2026-09-24T18:29:11.483855Z, gefilterd op uitsluitend de tijdelijke CLI-login.
Geen ruwe logregels, adressen, DSNs, wachtwoorden of payloads getoond.
De oorzaak achter die authenticatiefout, bijvoorbeeld credentialverversing of
een poolercache, is NIET bewezen. Geen derde login, automatische retry, andere
privilegerol, verzwakte TLS of passwordreset gebruikt om de fout te omzeilen.

De acht lokale tests zijn technische grens- en foutregistratietests, geen
bewijs van een succesvolle hosted databinding of volledige workflow.

## Afsluitende Metadata

Op 24 september 2026 om 20:35:16 Nederlandse tijd:
- Beide aangetroffen managed CLI-loginwachtwoorden verlopen.
- Nieuwste read-only credential verlopen om 20:34:11 Nederlandse tijd.
- Geen resterende CLI-/probesessies, geen andere actieve clientquery, geen IO-wachter.
- 40 hosted migrations; alle namen/versies komen overeen met de lokale eerste 40.
- 41 lokale migrations; uitsluitend 20260924155822_phase6e11_rpc_bridge.sql pending.
- Nieuwe bridgeschema afwezig; migration 41 niet toegepast.
- Geen nieuwe CLI-dry-run na de stop, omdat die opnieuw een login zou aanmaken.
  De eerdere dry-run met alleen migration 41 pending blijft het laatste dry-runbewijs.

Geen volledige fingerprint, beschermde datarijscan, synthetische workflow,
apply/restore, afwijzing, conflictactie, Auth-ledentest of fixturecleanup uitgevoerd.
Wel twee gecontroleerde managed tijdelijke CLI-login-uitgiften; geen app-/ledenwrites.
De metadataquery van de eerste native probe duurde ongeveer 47 ms.
De TLS-probes verzonden geen SQL. Dit is geen volledige Disk-IO-budgetmeting of
nieuwe before/after-databehoud-PASS. Geen temp-writeoorzaak of globale gelijkheid
afgeleid uit enkel de rustige momentopname.

Beheerde CLI-rolobjecten zijn niet verwijderd: dat kan ook normale CLI-toegang raken.
Hun wachtwoorden zijn servermatig verlopen en alle probesessies zijn gesloten.
Historische workspaces, 112 meetparen en incomplete stap 113 blijven behouden.
Runtime, Edge Functions, migrations, frozen bronnen en gewone accounts niet gewijzigd.

## Bewijs En Vervolg

Originele inventory, CA en eerste probe:
supabase/.temp/phase6e11-access-f897c0277fc04ae28c1882605a92f03e.
Gecorrigeerde probe:
supabase/.temp/phase6e11-access-corrected-6dd1ca2efb674fb3b47af81921fd82c2.
closing-metadata.json bevat uitsluitend gesanitiseerde migration-, verval- en
foutclassificatiemetadata. De nieuwe broncode staat afzonderlijk in access_v1.

Volgende technische gate: de authenticatiefout bij het vernieuwen van de managed
CLI-login oorzakelijk verklaren en een volledige retryvrije, projectgebonden
native read-only controle bewijzen. Vervolgens pas databehoudsnulmeting,
migration 41, 41/41/dry-run/ACL, minimale workflow en cleanup. De bestaande
server/JWT/observervoorwaarden blijven onverminderd gelden.

Een passwordreset is niet aangewezen op basis van dit bewijs. De onderzochte
Edge-bronnen gebruiken HTTPS/API-credentials, geen direct databasewachtwoord;
de CI-workflow heeft geen hosted databasecredential. Dit is GEEN volledige
reset-impactvrijgave voor alle mogelijke processen. Voor een eventuele reset
blijft een complete afhankelijkheden-/herstelcontrole nodig; geen reset gevraagd.

[Officiele CLI-loginroute](https://supabase.com/docs/reference/api/v1-create-login-role),
[JIT-voorwaarden](https://supabase.com/docs/guides/platform/temporary-access),
[SSL/CA](https://supabase.com/docs/guides/platform/ssl-enforcement).
De statuspagina meldde ook een lopend API/JWT-incident. Er is geen bewijs dat dit
de gemeten poolerauthenticatiefout veroorzaakt; geen upgrade/restart uitgevoerd.

External AI calls/cost: 0 / EUR 0.00.
Real-member AI enabled: NO.
Production touched: NO.
