# 6E-0 Offline Recognition Follow-Up

Status: 6E-0 OFFLINE RECOGNITION FOLLOW-UP - TECHNICAL PASS / READY FOR OWNER PRODUCT REVIEW.
Datum: 2026-09-07. Uitsluitend offline; geen 6E-1, owner-freeze of live integratie.
Publicatiebewijs volgt in PHASE6E0_RECOGNITION_PUBLICATION.md; oude evidence blijft geschiedenis.

## Baseline En Werkwijze

Exacte repository: Yourizorge/fitmetzorge-staging, main, werkmap
supabase/.temp/phase4fb-staging-deploy binnen de door de owner genoemde repositorymap.
Vooraf HEAD, origin/main en direct remote: e5dc0ef948d22225f8b2907a2be41f74f4b15d3d;
werkboom schoon. Frozen runtime: bc6308fbf0f914b04c7faa711219d9ae46e9cbe3.
Projectinstructies, technisch rapport, D1-D12, contract, regels, copy, state en tests gelezen.
Geen bestaande wijzigingen teruggezet. Na wijziging van toegestane werkmappen zijn
benodigde writes via reguliere escalatie en apply_patch uitgevoerd, zonder rechten te wijzigen.

Voor de logica veranderde zijn 79 handgeschreven NL/EN/DE-gevallen en 4 toegang/hersteltests
vastgelegd in commit fddcea1d4cb92c102a3517376cbcc9a0d02ec22d.
PHASE6E0_RECOGNITION_BEFORE.json bevat de oorspronkelijke uitvoer per geval.
Inputs/verwachtingen zijn niet gegenereerd uit regexp-matches en niet versoepeld na de fix.
Dit is wel een door de ontwikkelaar gemaakte synthetische set, geen onafhankelijke validatie.

## Oorzaak En Uitkomst Per Gat

Alle vier originele inputs zijn exact behouden. Alle nieuwe uitkomsten:
evaluation_state=uncertain, help_level=null, warning_key=uncertain,
unrecognized_health_context, medical_clearance=false, automatic_actions_allowed=false.

| Exacte oorspronkelijke input | Oorzaak van known/R0 | Correctie |
| --- | --- | --- |
| Mijn borst voelt loodzwaar | Geen patroon voor deze gewichts-/gevoelsomschrijving; ook geen generiek gezondheidswoord dat de fallback activeerde | Relatie tussen borst, gevoelswerkwoord en zwaarte als oningedeelde gezondheidscontext; geen nieuwe R3/R4-toekenning |
| Ich kriege kaum noch Luft | Bestaande Duitse regels dekten andere formuleringen, niet nauwelijks lucht krijgen | Begrensde luchttekortformulering als oningedeelde context; nauwelijks is hier geen ontkenning van klachten |
| Ik heb geen pijn op de borst. Nu heb ik moeite met ademhalen | Ademhalingsformulering ontbrak; bovendien sloot een eerder herkend/ontkend signaal de globale fallback uit | Per-clause beoordeling en alleen gematchte tekstspans afdekken; ontkende borstpijn maskeert ademhalingscontext niet |
| Ik voel me prima terwijl mijn linkerarm plots kracht verliest | Krachtverliesformulering ontbrak. Er was geen bewezen aparte 'prima'-override; de melding werd niet herkend | Functionele armomschrijving als oningedeelde context, terwijl/while/waehrend als grens; geruststelling wist andere melding niet |

Nieuwe context-hints hebben GEEN medisch niveau. Bestaande rules.json, contract.json,
copy.json en D1-D12-register zijn ongewijzigd tegenover e5dc0ef.
Bestaande voorlopige R3 blijft in gemengde berichten behouden, met onzekerheid ernaast.

Ontkenning wordt aan het betreffende matchbereik gekoppeld, inclusief interne ontkenning
in nieuwe hints. Komma's blijven zichtbaar als zinsdeelgrenzen. Historische/educatieve/
hypothetische context kan binnen een samengestelde zin doorlopen; nieuwe zinnen en expliciete
actuele meldingen krijgen een eigen beoordeling. Citaten blijven apart. Dit zijn heuristieken,
geen algemene grammatica- of medische begripsengine.

## Testuitslagen

| Categorie | Resultaat | Wat dit bewijst |
| --- | --- | --- |
| Vooraf geregistreerde set op oude code | 15 PASS / 68 FAIL van 83 tests | Niet 68 klinische missers: ook ontbrekende contexttags en toegang/herstelgrenzen faalden |
| Vier oorspronkelijke gevallen | 4/4 verbeterd | Nu expliciete onzekerheid, geen ongemerkte known/R0 |
| Alle geregistreerde taalgevallen | 79/79 PASS | 4 originelen, 18 parafrases, 9 ontkenningen, 6 historisch, 6 educatief, 3 citaten, 3 hypothetisch, 15 training, 12 samengesteld, 3 bestaand niveau behouden |
| Aanvullende toegang/hersteltests | 4/4 PASS | Feiten/toegang behouden; zelfrapportage zonder vrijgave; acties leeg |
| Volledige offline suite | 659/659 PASS, 0 FAIL/skip/todo | 487 engine, 39 state, 37 retentie, 6 isolatie, 7 regressie/beperkingen, 83 follow-up |
| Bestaande frozen thematests | 10/10 PASS | Alleen in-memory unit tests |
| Beperkingregistratie | 4 historische gevallen behouden, 0 tests die oude missers als gewenste herkenning accepteren | De vier actuele regressietests eisen verbeterd gedrag; dubbele coverage niet dubbel als unieke herkenning tellen |
| Bekende missers binnen de 79 vooraf bepaalde gevallen | 0 resterend | Geen claim dat alle denkbare taal wordt herkend |
| Nieuwe medische labels | 0 toegewezen | Bestaande medische labels nog onbeoordeeld |
| Live database/member-/Edge-/migrationtests | NOT RUN | Niet toegestaan of nodig binnen deze offline opdracht |

Reproduceren vanaf de repositoryroot, Node 24+ en Git; geen installatie, netwerk of tempfiles:

```powershell
node --test _offline/phase6e0/test/*.test.cjs
node --test assets/phase6d-theme-authority.test.cjs
git diff --check
git diff bc6308fbf0f914b04c7faa711219d9ae46e9cbe3 -- . ':(exclude)docs/**' ':(exclude)_offline/**'
```

## Exacte Bestanden

Offline toegevoegd: recognition-followup-cases.json, context-hints.json,
test/recognition-followup.test.cjs, alle onder _offline/phase6e0/.
Offline aangepast: engine.cjs, known-limitations.json, test/limitations.test.cjs,
test/isolation.test.cjs, README.md, onder dezelfde map.

Nieuwe docs: PHASE6E0_RECOGNITION_PREREGISTRATION.md, PHASE6E0_RECOGNITION_BEFORE.json,
PHASE6E0_RECOGNITION_FOLLOWUP.md, PHASE6E0_PRODUCT_REVIEW.md,
PHASE6E0_RECOGNITION_PUBLICATION.md en PHASE6E0_RECOGNITION_EVIDENCE.json.
Bijgewerkt: docs/PHASE6E0_OFFLINE_CONTRACT.md, docs/PHASE6E0_TECHNICAL_REPORT.md,
docs/BUILD_STATUS.md, docs/TEST_MATRIX.md, docs/MASTER_BUILD_PLAN.md, docs/ARCHITECTURE.md.
Historische resultaten worden niet herschreven tot later succes. Actuele addenda verwijzen hierheen.
Exacte correction/receiptcommits en push-/Pages-status staan in de publicatiereceipt.

## Isolatie En Grenzen

De protected Gitdiff tegenover bc6308f blijft leeg. Frontend, Edge, database, canonical
migrations, entitlements, providerinstellingen, workflows en approvals zijn ongewijzigd.
De isolatietest laat uitsluitend de nieuwe lokale JSON-hints toe, geen extra IO of importpad.
Private Node-only code wordt niet door de app/bundler/scheduler geladen.
Publieke staging GETs controleren 56 frozen assets byte voor byte en vijf offlinepaden
op HTTP404, voor en na toegestane automatische Pages-publicatie. Geen appuitvoering.

Geen database-/memberdata-/Auth-/consent-/provideractie, externe AI-call, nieuwe kosten,
reviewercontact, bestandsopruiming of productiehandeling. Er is geen actuele
live datahashmeting gedaan en geen claim over gelijktijdige wijzigingen door anderen.

## Productreview En Resterende Grenzen

PHASE6E0_PRODUCT_REVIEW.md bevat de exacte bestaande Nederlandse conceptteksten.
Voorgestelde tekstwijzigingen: GEEN. D1-D12 blijven behouden, inclusief vier gescheiden
assen (toegang, feiten, persoonlijk advies, uitvoering), geen algemene gezondheidsblokkade,
zelfrapportage zonder medische vrijgave, geen automatische trainerdeling en chat-only hulp.
Alleen ownerproductreview; medische, privacy-, juridische en moedertaalreview blijven OPEN.
Voorwaarden voor ernstige herstelgevallen, onopgeloste retentie en normale analysehervatting
blijven OPEN. De frozen 6D safetygate is niet aangepast.

De set is beperkt en door dezelfde ontwikkelaar opgesteld. Ongeziene metaforen,
complexe verwijzingen/ontkenningen, gemengde talen en indirecte klachten kunnen nog misgaan.
Geen complete herkenning of medische nauwkeurigheid bewezen.
Volgende stap: ownerproductreview; geen automatische start van een volgend pakket.
