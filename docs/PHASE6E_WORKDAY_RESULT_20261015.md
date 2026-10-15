# Geintegreerde lokale coachkandidaat en hosted omvang

## Uitkomst en afbakening

Startbron `5917d9f642bda65150496e5e9963b0435b23f833`, uitsluitend staging/main.
De gekoppelde lokale gebruikersbediening heeft echte PostgreSQL/GoTrue-CI-PASS.
Dit is geen volledige hosted 6E-11-PASS, owneracceptatie of volledige appoplevering.
6E-21 blijft ongeaccepteerd en standaard servermatig uitgeschakeld.

De Windows-host heeft geen Docker/WSL. De echte lokale stack en browsers draaiden
op de bestaande geisoleerde CI-runner. Er draait geen blijvende PostgreSQL-app op
deze Windows-pc en er is geen nieuwe publieke demo of owner-testvenster geopend.

## Nieuwe werkende gebruikershandelingen

| Handeling | Werkelijk resultaat | Waar bewezen |
| --- | --- | --- |
| Een login, samenhangende navigatie | Vandaag, training, voeding, herstel, intake, voorstel, voortgang, historie en instellingen gebruiken dezelfde bevoegde versiegebonden staat | Echte lokale Auth/PG17 en browser |
| Catalogusplannen met 21 uit | Training en voeding blijven zichtbaar; de server weigert onvrijgegeven volledige dagregistratie | Integrale lokale CI |
| Plan bewerken | Beschikbare dagen, toegestane oefeningen, sets/reps/rust, afzonderlijke RIR/RPE, exacte productversie en portiegrenzen; aparte review en toepassing | Domein, database en browser |
| Intake bijwerken | Dagen/frequentie/tijd, materiaal, voorkeuren/uitsluitingen, allergiegegevens; broncorrecties bewaren oude intake en maken oude goedkeuringen ongeldig | Domein en browser |
| Historische workout registreren | Zelfde login, afzonderlijke originele snapshot; expliciet starten, registreren en afronden; gedeeltelijk blijft gedeeltelijk | Echte lokale opslag, opnieuw inloggen en browser |
| Betrouwbare registratie | Leeg blijft leeg, RIR 0 blijft 0, RPE blijft afzonderlijk; registratie rondt niet automatisch af | Domein/database/browser |
| Voeding begrijpen | Exacte geplande subtotalen en bronversies; nadrukkelijk geen claim dat gepland gelijk is aan gegeten | Domein en browser |
| Herstel/voortgang | Bestaande complete vergelijkbare vensters, brongebonden check-inopties, historie en ontdubbelde duurzame in-app-outbox samengebracht | Bestaande componenten plus integrale regressie |
| Opslaguitval herstellen | Een verloren antwoord na commit toont onzekerheid; expliciet dezelfde request controleren maakt geen tweede versie | Werkelijke HTTP-onderbreking in browser |
| Offline concept behouden | Historische workout/herstelregistratie blijft account-/workspace-/brongebonden in IndexedDB; opnieuw inloggen en expliciet verzenden; conflict en intrekking blokkeren | Echt browser-offline, PG17 en GoTrue |
| Voorkeuren bewaren | NL/EN/DE, licht/donker, eenhedenkeuze blijven na herladen; benaderde weergave toont originele waarde/eenheid en herschrijft niets | Domein en browser |

Route A behoudt lidacceptatie, trainergoedkeuring en afzonderlijk toepassen.
Route B heeft geen trainerstap. De samengestelde registratie-workspaces worden
servermatig gemount: een browserrol kan geen extra toegang toekennen. De oude
snapshot is niet het huidige catalogusplan. De minimale toekomstige registratie12-
release blijft afzonderlijk, zonder stilzwijgende start/finish- of outboxuitbreiding.

## Bewijs en herstelde fouten

CI [38739029524](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38739029524)
is gebonden aan `c0624a2e015ee675769f0c0c915bc34372c14f63`, kandidaat
`dd312b3ad9d504391750da0c5206db3e24750a50b91f2550d8f227cc7b23047a`.
Artifact SHA256 `835435fcfa7fcd70dd0395d646c4f684502d160ed034f61f8158824a842a955b`.
Alle 349 bronbestanden zijn voor de numerieke proef met deze CI vergeleken.

De volledige herhaling inclusief de grotere PG17-proef is
[CI38742498080](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38742498080):
bron `4712f7a8ac5a591aef794f44884336dbba11cb06`,353 kandidaatbestanden,
kandidaat `ca5b39fc8a7f39b08eeeada5c0ac2495445cfd4dc4b496fa41b4a5636510e2bc`,
artifact `ee4d07ab291f1b2cf9618b18b7922f298ca6806ebb0a30e96db737acfc045e76`.
Alle onderstaande integratietotalen zijn opnieuw PASS.172 gesanitiseerde
receipts/screenshots staan in `receipts/ci-38742498080-completion` met manifest.

De aanvullende duurzame conceptwachtrij is daarna integraal PASS in
[CI38746007554](https://github.com/Yourizorge/fitmetzorge-staging/actions/runs/38746007554):
bron `ec97596902931dcc6c56d44e26a0b46ab6cc8a85`,356 bestanden,
kandidaat `02441afc2cc09b00c292e6bb114f11498c6b0fe4aa60ebac3b2bb43613234154`,
artifact `aba33ce3480334c51abf790c613fcfcf13365f9dcf40f29515f8b14ffafbe043`.
124 samengestelde browsercontroles zijn PASS; de overige groepen hieronder
blijven gelijk.3 extra queue-integriteitstests en61 lokale Python-helpertests.
172 nieuwe receipts zijn apart bewaard. Geen hosted Auth of workflowwrites.

- Schone 46/46 lokale opbouw: 44 behouden canonical migrations plus alleen lokale kandidaten45/46. Dit is NIET hosted46.
- 25 minimale registratie-DB-controles; 46 private-transport-DB-controles; 62 gezamenlijke DB-controles.
- 15 minimale registratie-browserchecks; 209 bestaande gezamenlijke checks; 108 nieuwe samengestelde browserchecks.
- Drie afzonderlijke lokale Auth/sessiecomposities met elk4 controles; private transport22 complete meetparen.
- 39 domein/lifecycle/presentatietests,4 voorbereide contracttests,2 eenhedenweergavetests; afzonderlijk60 lokale Python-helpertests inclusief de nieuwe behoudcontrole.
- 12 SQL-regressies,36 M44-controles,36 PG17-filterchecks,4 exacte numerieke PG17-cases; rechten/advisors en lege lokale dry-run PASS.
- NL/EN/DE, licht/donker,390px telefoon en1280px desktop: browseremulatie, geen nieuwe fysieke ownerhandeling.

CLI2.117.0; PostgreSQL17.6; `ghcr.io/supabase/postgres:17.6.1.167`,
repositorydigest `sha256:6942962433a569e87f228b4d4ab7e11db5deca64e43babb3a038443ad6c4f1bb`;
echte disposable GoTrue v2.197.0. Geen extensiemocks of hosted credentials in CI.

CI38734722189 bleef NO-GO door een vertaalde checkboxnaam in plaats van een
technische veldnaam. CI38736428879 bleef NO-GO doordat de minimale transport-
factory de nieuwe optionele lifecycle-eigenschap niet had. Beide zijn gericht
hersteld en opnieuw brongebonden getest. CI38737848805 was daarna volledig PASS.
Een lokale numerieke startcontrole faalde vervolgens op een lang Windows-pad,
voor JIT/SQL; die leesfout is hersteld en opnieuw in CI38739029524 getest.
Deze fouten zijn niet achteraf tot PASS verklaard.

CI38740787205 bleef NO-GO in de nieuwe lokale capaciteitsproef: de hashstroom
werd ten onrechte gecontroleerd met de validator voor precies een statistiekrij.
De query had terecht106.496 rijen. Commit4712f7a scheidt die twee controles,
behoudt nul temp/sorts en de bestaande2,5s-querygrens. De nieuwe regressie
weigert verkeerde aantallen, temp reads/writes, sorts en ongeldige looptijden.
Dit was uitsluitend een disposable CI-fout, geen nieuwe hosted poging.

## Hosted numerieke diagnose

Run `91ba398d-8888-4026-9f0b-3aafd988e5b3` is afzonderlijk uitgevoerd binnen
de expliciete numerieke toestemming. Exact dezelfde historische uitsluitingen,
filterhash `b94f4eea413204787b134198bcaae488bf6c98082687e44bf466f735920ef85a`.

- 100.843 beschermde rijen,158 tabellen; geen rij-inhoud of rijhashtransport.
- 13/128 SQL, inclusief BEGIN READ ONLY/repeatable-read, project/TLS-binding en ROLLBACK.
- Telling679,258ms, tekstvrije lezer48,707ms. Eigen temp0, eigen WAL0; gemeten achtergrond-tempdelta0, niet aan collector toegeschreven.
- Geen Auth-tokenuitgifte, fixture-, applicatie-, cleanup- of migrationwrites.
- Officiele Connect/session5432, jit=true, CA/verify-full; tijdelijke mapping ingetrokken,0 resterende mappings, JIT uit, SSL-enforcement aan.
- Dit is een omvangmeting, GEEN volledige vergelijking van beschermde inhoud en GEEN workflowvrijgave.

Zeventig gesanitiseerde receipts staan onveranderlijk in
`_offline/phase6e_server_v1/receipts/numeric-91ba398d-8888-4026-9f0b-3aafd988e5b3/`.
De eerdere gebruikte run en alle112 geldige historische meetparen/incomplete113
blijven ongewijzigd. Hosted laatst bewezen43; M44 blijft kandidaat. Geen nieuwe
hosted migrationcontrole of dry-run geclaimd op basis van deze uitsluitend numerieke proef.

## Volledige capaciteit, geen nieuwe toestemming afgeleid

De volledige oude registervolgorde is uit de gehashte fasebestanden hersteld en
alle prefixes/afsluitreserves opnieuw berekend. Dertien pagina's van8192 geven
106.496 rijplaatsen:5.653 boven de gemeten omvang. Geen nieuwe uitsluitingen.
Per cyclus41 in plaats van31 protocolcommando's, drie cycli. Normaal2.226;
zwaarste prefix plus veilige afsluiting2.237. Kleinste berekende maximum2.237,
dus11 boven het eerder toegestane maximum2.226.

| Fase | SQL-capaciteit |
| --- | ---: |
| Voorcontrole | 4 |
| Migration | 42 |
| Nulmeting | 61 |
| Inrichting | 33 |
| Guard | 13 |
| Auth | 318 |
| Controller | 286 |
| Route A | 191 |
| Route B | 286 |
| Terugzetten | 54 |
| Metingen | 136 |
| IO | 97 |
| Cleanup | 633 |
| Eindmeting | 71 |
| Afsluiting | 1 |
| Normaal | 2226 |
| Inclusief zwaarste veilige stop | 2237 |

Alle594 beheerde Auth-commando's, CLI, observer, protocol en cleanup blijven
meegeteld. Clienttransportproef:100.843 synthetische hashes,13 frames,
9.478.643 JSON-bytes,1,844s en22.014.271 Python-piekbytes. Dit meet geen process-RSS,
werkelijke server-rijbreedte of hosted netwerklatentie.

De afzonderlijke PG17-proef in CI38742498080 is PASS:106.496 synthetische rijen,
158 tabellen,13 cursorpagina's,253,565ms hashquery,1,388s client fetch/reduce,
10.010.025 JSON-framebytes en24.508.470 Python-piekbytes. Nul temp blocks en
geen Sort; read-only transactie, afsluitende ROLLBACK en gesloten verbinding.
Alle272 lokale commando's inclusief tijdelijke synthetische inrichting zijn
geregistreerd. Dit is geen hostedbudget. De uitgevoerde bron bevat integers,
144 tekens (`repeat('synthetic',16)`), NULL en JSON. Het onveranderlijke receipt
noemt abusievelijk128 tekens; deze tekstcorrectie verandert de meetuitkomst niet.
Werkelijke rijbreedte, servergeheugen en hosted netwerklatentie blijven onbewezen.
Geen ongewijzigde retry of eigen verhoging van een hosted limiet.

De uiteindelijke gecombineerde vrijgave vereist nieuwe exacte runbinding,
actuele integrale bron-CI, capaciteit106.496/maximum2.237 en behoud van alle
deadlines:1 collector,3 cycli,geen retries,5s query/connect,2,5s eigen queryload,
600s totaal/540s gewoon pad,120s worker,180s guard. Geen limiet is al toegepast.

Voorstel voor precies een nieuwe run: `1c3bf7e7-bc78-40c5-9ac1-5ba3512ec66d`.
Dit ID is alleen vooraf voorgesteld, niet in een controller/migration ingesteld.
De bestaande framegrens blijft1MiB;13 frames geven maximaal13MiB gevalideerde
framecapaciteit per cyclus en39MiB voor drie cycli. Werkelijke TCP/TLS-overhead
is daarin niet gemeten. Python-geheugenmeting is geen RSS-garantie; geheugen- en
transportfouten blijven fail-closed. De volledige nieuwe run moet na een
capaciteitsbesluit opnieuw aan de exacte bron-CI en M44-identiteit worden gebonden.
Geen oude poging heropenen, geen nieuwe filters of uitsluitingen, geen langere
time-outs. Bij NO-GO geen nieuwe afhankelijke write; veilige eigen afsluiting
en behoud van foutbewijs blijven verplicht. De historische utility-oorzaak
blijft UNKNOWN en is niet opnieuw onderzocht.

## Wat nog niet af is

De duurzame browserconceptwachtrij voor historische workout/herstel is nu
geintegreerd. Zij bewaart maximaal10 concepten, geen credentials, en verzendt
niets automatisch. Goedkeuren/toepassen en21-acties zijn uitgesloten. Een
volledig offline opstartbare shell of offline login is niet gebouwd; voor
opnieuw aanmelden is serververbinding nodig. Free/Pro/AI-
proefperiode is een read-only synthetische beleidsmodule, geen nieuwe entitlement-
uitgifte, betaalfunctie of volledige instellingenintegratie. Definitieve final-day-
melding/tijdzoneregel, badges/streaks, sport/wearables/media-interfaces zijn niet
als werkend afgevinkt. Ontbrekende inhoudelijke criteria blijven zichtbaar open.

Volledige nieuwe workout-/maaltijdregistratie op het actuele gezamenlijke plan
blijft de onvrijgegeven21-uitbreiding. Bestaande geaccepteerde runtime blijft
werken, maar is niet stiekem door deze kandidaat vervangen. Geen echte AI-chat,
achtergrondbezorging, medische/voedingskundige/taalkundige validatie geclaimd.

Zie [de concrete releasevolgorde per slice](PHASE6E_WORKDAY_RELEASE_ORDER.md).
Releasevolgorde: volledige11-keten + noodzakelijke ownerreview, daarna minimale
registratie12, vervolgens afzonderlijk signalen/broncorrecties, plannen/review,
intake, training, voeding, gezamenlijke toepassing, herstel en Vandaag. Per slice
blijven private opslag/RLS, sessiecontrole, writesets, idempotency, audit,
default-off ingang, schone opbouw, afzonderlijk commandoregister en hosted
databehoud vereist. Rollback sluit alleen de nieuwe ingang/toegang; historie en
audit blijven. Een planherstel maakt na vereiste goedkeuringen een nieuwe versie.

## Behoud en checkpoint

Van de oorspronkelijke1.376 bestanden zijn1.373 byte-identiek. Alleen de expliciet
bijgewerkte architectuur, masterplan en testmatrix kregen een nieuwe statusprefix
en historische kop; hun volledige oudere body blijft gelijk. De oorspronkelijke
strikte controle bleef terecht NO-GO voor deze drie docs; het nieuwe gescheiden
behoudreceipt toont de toegestane wijzigingen en herschrijft de nulmeting niet.
152 stagingassets byte-identiek;19 vaste private paden404. De zes oudere tracked wijzigingen blijven bewust buiten deze
commits, evenals alle historische untracked11-bestanden. Geen schone worktree
geclaimd. De definitieve Pages-/private-padcheck en commit staan in het
bijbehorende publicatiereceipt en eindbericht.

Functionele checkpoints: b80a753,7f02bc5,38da185,c0624a2. Bewijs/capaciteitscheckpoint:
25db2bb en4712f7a. Geen hosted app-, Edge- of databasedeployment. Geen telefoontestlink of
vervaltijd zolang11 NO-GO is. Geen JARVIS-overdracht.

Aanvullend functioneel checkpoint ec97596 implementeert de duurzame lokale
conceptwachtrij. De eerdere volledige HTTP-padronde bij d3e74e9 blijft INCOMPLETE
na607 bewezen404's en een503, niet als publieke toegang of PASS bestempeld.
Vervangend bewijs op ec97596: officieel Pages-artifact met771 entries, alle152
runtimehashes gelijk en geen `_offline`, `supabase` of `.github` erin. Zeven
gerichte HTTP-probes geven404, inclusief het eerder503-pad. Dit voorkomt een
nieuwe lange HTTP-pollingronde; de oorspronkelijke foutregistratie blijft bestaan.

External AI calls/cost:0 / EUR0.00. Real-member AI enabled:NO. Production touched:NO.
