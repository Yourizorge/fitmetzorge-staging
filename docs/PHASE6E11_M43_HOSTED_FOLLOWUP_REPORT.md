# 6E-11: M43 hosted follow-up, 12 October 2026

Status: **M43 HOSTED PASS / CONTROLLER AUTH NO-GO**.
Ownertelefoontest gesloten. Geen owneracceptatie, freeze of 6E-12-serverstart.
6E-21 blijft ongeaccepteerd. Stagingworker blijft actief; geen overdracht aan JARVIS.

## Afgerond

- Start-HEAD lokaal/remote: `f7833846ce74406cadbaabc044b14241d16a4d9a`, main.
- JIT-aanvraag nu geslaagd met afzonderlijke gesanitiseerde fasebewijzen:
  enable, applied-readback, owner/rol-toekenning en mappingcontrole elk HTTP 200.
  De oorspronkelijke 406 is niet gereproduceerd. Het oude hulpmiddel bewaarde
  subrequest en response onvoldoende: de precieze oude oorzaak is niet bewijsbaar.
  Geen ongefundeerde claim dat een configuratierace de oude fout veroorzaakte.
- Bestaande owner-PAT uit de beveiligde Windows-credentialroute; korte bestaande
  postgres-JIT, uitsluitend project `mokxyyullfhkfalopbzd`. Geen nieuwe rol/rechten.
  Officiele session-pooler, `jit=true`, CA en volledige hostnamecontrole behouden.
  SSL-enforcement bleef aan. Na elke lease expliciet ingetrokken: nul mappings.
  Geen IP-pin verzonnen waar het exacte uitgaande adres niet bewezen was.
- M43 via de migration-aware CLI 2.117.0 toegepast na de bestaande schone
  43/43-CI-PASS en een nieuwe directe voor-/nameting. Vervolg-dry-run leeg.
  Lokaal/hosted **43/43**; geregistreerde SQL gecontroleerd tegen de lokale SQL.
- M43 SHA256: `bab79b7ca5876c2dcef055d0e95997595772aebc051283e69bbeb2ca1dc4bd57`.
  Drie lege private bewijstabellen, RLS aan, geen functies, geen client-/PUBLIC-
  grants. Migrations 1-42 en bestaande objecten/rechten ongewijzigd.
- Alle 155 bestaande tabelcohorten gelijk, 100850 gemeten rijen voor en na.
  Bestaande uitsluitingen blijven expliciet: cron-runloginhoud en de nieuwe
  M43-historyrij. Drie nieuwe lege bewijstabellen afzonderlijk gecontroleerd.
  Dit is geen claim dat die twee uitgesloten categorieen byte-identiek zijn.
- Auth-voorcontrole: drie exacte synthetische identiteiten/rollen/relaties aanwezig,
  geen actief venster (negen historische vensters behouden), geen onvolledig
  M42-request. Vier read-only SQL-commando's, bevestigde rollback en JIT-intrekking.
  Geen Auth-, applicatie-, leden- of fixturewrites in deze vervolgcontrole.

## Belasting en behouden fouten

M43-installatie: twee zuinige streams van 65 en 72 commando's. 198/296 inclusief
40 gereserveerde CLI-commando's en 21 historische commando's. Dit is het reeds
vastgelegde installatiebudget, niet een verhoging van het canarybudget van 128.
Een collector, geen automatische retries. Alle eigen meetquery-temp-writes nul.
Hoogste gemeten profieltotalen 1166.17 en 1862.35 ms binnen hun eigen grenzen.
Nameting zag 12290584 bytes achtergrond-temp-writes, niet aan een specifieke
achtergrondtaak toegerekend en niet als collectorbelasting voorgesteld. Geen
claim dat hiermee het gehele dagelijkse Disk-IO-budget hersteld is bewezen.

Een eerdere nieuwe metadata-proef in deze ronde faalde na geslaagde authenticatie:
`SHOW transaction_read_only` paste niet bij de strikte libpq-rijtellingsadapter.
De fout is lokaal gereproduceerd. De bestaande SELECT-/drain-/rollback-adapter
werkt aantoonbaar en is vervolgens voor de geslaagde metingen gebruikt.
De incomplete proef blijft staan: haar detailreceipt telt drie commando's;
de oude aggregaatreceipt vermeldt ten onrechte nul. Geen historische overschrijving.
De oorspronkelijke 406, 112 geldige paren en incomplete stap 113 blijven behouden.

## Lokale verbeteringen en bewijs

- Nieuwe JIT-fasejournal, brongebonden M43-hervatting en read-only Auth-admission.
- Controller bewaart na een niet-bevestigde actie een begrensde nameting in de
  stopregistratie. Geen fictieve action_confirmed of pair_validated, geen retry,
  volgende actie of cleanup. Een mislukte stopopslag wordt expliciet gemeld.
- PG17 bewijst ook een daadwerkelijk gecommitteerde synthetische write met
  verloren antwoord: before=0, after=1 duurzaam opgeslagen, run blijft gestopt.
- Auth-helper eist een serverguard voor uitgifte; ontbrekende/onvolledige
  identiteit of aliasbescherming blokkeert voor de eerste Auth-HTTP-aanroep.
- 168 Node-tests, 51 Python-tests: PASS. Lokale PG17: 6 metadata-, 4 Auth-
  voorcontrole-, 67 store-/rechten- en 6 identity-lockcontroles. Auth-stubs zijn
  geen hosted Auth-bewijs. De aliasbeperking telt niet als geslaagde afscherming.
- Nieuwe controllerbron wijkt af van de oude CI-kandidaat. Oude CI-admission
  weigert deze terecht. M43 zelf blijft exact de reeds geteste/toegepaste versie.
- 1376 behouden bestanden en 530 historische bron-/bewijsverwijzingen: hashes gelijk.
  Oudere lokale app.js/index.html/AGENTS/statuswijzigingen blijven ongemoeid.

## Werkelijke nieuwe toegangsgrens

De lokale PG17-concurrencytest bewijst: KEY SHARE voorkomt verwijderen en laat
de nodige niet-sleutelupdates toe, maar beschermt email niet met Supabase's
gedeeltelijke unieke e-mailindex. De hosted, expliciet read-only cataloguscheck
bevestigt: `email_protected_by_key_share=false`, een gedeeltelijke unieke index.
Een gelijktijdige adreswijziging kan dus de adresgebaseerde Auth-uitgifte van de
vooraf geregistreerde identiteit losmaken. Supabase admin generate_link kan
bovendien een ontbrekend magiclink-account aanmaken. Dat is niet toegelaten.

Daarom geen muterende controllerdeploy of hosted Auth-canary. Er is eenmaal een
ownerbesluit gevraagd voor een extra tijdelijke serverguard in het beheerde
Auth-schema: alleen de drie geregistreerde synthetische identiteiten/loginadressen,
maximaal tien minuten, eerst lokaal/CI bewijzen, daarna exact verwijderen.
Geen wijziging van wachtwoorden, gewone accounts, globale Auth-instellingen of RLS.
Dit is nog geen uitgevoerde of als veilig bewezen managed-schemawijziging.
Alternatief: deze Auth-routes gesloten houden en uitsluitend offline verderwerken.

## Nog niet afgerond

Server-compiled controllercompositie en fixture prepare/activate, echte Auth-
request-/sessieprovenance, de hosted Route A/B-paren, afwijzen/blokkeren/conflict,
apart toepassen, terugzetten, dubbelverwerking en synthetische cleanup/delete.
De 45 bestaande lokale workflowparen blijven geldig, maar vervangen dit niet.
Er is geen fixturecleanup of nieuw ownervenster uitgevoerd. Oude fixtures blijven
intact. Na complete hosted bewijsvoering volgt pas duurzame synthetische 6E-12.

Onderbouwing: [nieuw bewijsmanifest](PHASE6E11_M43_HOSTED_FOLLOWUP_EVIDENCE.json),
[historische controller-CI](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38243722556),
[Supabase JIT API](https://supabase.com/docs/reference/api/v1-update-jit-access-config),
[Auth-configveldnaam](https://supabase.com/docs/reference/api/v1-get-auth-service-config),
[generate_link-bron](https://github.com/supabase/auth/blob/v2.197.0/internal/api/mail.go),
[gedeeltelijke index](https://github.com/supabase/auth/blob/v2.197.0/migrations/20221215195500_modify_users_email_unique_index.up.sql).
De oude Auth-policyreceipt gebruikte een niet-bestaande rotatieveldnaam; de null
bewijst niets over rotatie. De lezer is gecorrigeerd naar het gedocumenteerde veld;
geen Auth-instelling is gewijzigd en geen refresh-PASS afgeleid.

Commit/publicatiebewijs komt in de afzonderlijke publicatiereceipt. Alleen offline
controllercode, tests en documentatie; geen normale runtime- of Edge-publicatie.

External AI calls/cost: 0 / EUR 0.00. Real-member AI enabled: NO.
Production touched: NO. JARVIS touched: NO.
