# Package 6E-1 Afzonderlijk Voorstel

Status: PROPOSAL ONLY / NOT STARTED / NO ACTIVATION AUTHORITY.
6E-0 productreview geeft niet automatisch 6E-1-GO.
De huidige toestemming omvat geen reviewercontact, kosten of integratie.

## Aanbevolen Begrensde Opdracht

Eerst ownerreview van 6E-0. Daarna, alleen op een expliciete afzonderlijke opdracht:
werk de vier bekende herkenningsgaten en een onafhankelijk samengestelde contextset
verder offline uit. Selecteer na relevante deskundige beoordeling hoogstens een
kleine correctie van bewezen lexicale/contextfouten in de bestaande 6C classifier
en recovery-intent, zonder vijf nieuwe live niveaus, schema, retentie of nieuwe UI.

Dat is geen uitrol van dit offline model. De huidige vijf-niveau klinische labels
zijn niet klaar om in een live requestpad te worden gebruikt. Verbetering van enkele
strings toont evenmin complete herkenning aan. Onopgeloste review verhindert een
live slice; verdere expliciet opgedragen offline uitwerking kan wel.

## Uitvoerbare Werkvolgorde En Gates

| Stap | Concrete output | Vrijgavevoorwaarde |
| --- | --- | --- |
| 1 Productafbakening | Owner bevestigt beslisregister, bounded facts versus normaal advies en chat-only bereikbaarheid | Geen impliciete blanket block of blanket adviesvrijgave |
| 2 Onafhankelijke cases | Vooraf vastgelegde NL/EN/DE negatieve/positieve/context/recurrence cases, inclusief vier bekende missers; cases niet enkel uit regels gegenereerd | Klinische rangen, terughoudendheid en minimale hulpteksten krijgen relevante beoordeling; reviewers en budget eerst apart bevoegd regelen |
| 3 Interfacebesluit | Behoud clear/hard_stop alleen indien aantoonbaar passend bij de beperkte correctie; versieer toekomstige mapping apart | R0 niet gelijk aan vrijgave; onzekerheid niet stil als clear; geen vijf niveaus in bestaande enum persen |
| 4 Minimale patch | Eventueel alleen phase6c-handler.ts en eigen pure handler tests, plus docs | Expliciet GO voor concrete runtimebestanden; relevante medische/juridische/privacyreview afgerond; geen scopegroei |
| 5 Niet-mutatieve lokale regressie | Positief, negatief, mixed, quote, historisch, actueel-sinds, injectie, herstelconflict en ongewijzigde actions[] | Vooraf overeengekomen technische criteria PASS en inhoudelijke beoordeling niet vervangen door testscore |
| 6 Stagingreleasebesluit | Exact diff, rollbackcommit, beperkte verificatie en ownerretestplan | Apart GO voor staging Edge deploy; productie verboden. Alleen goedgekeurde synthetische inputs, geen ongeautoriseerde member/providerverwerking |

Mogelijke latere patchlocaties: supabase/functions/youri-ai/phase6c-handler.ts en
supabase/functions/youri-ai/phase6c-handler.test.ts. Ze zijn NU NIET gewijzigd.
Frontend, huidige analyse/recovery-RPC, migrations, cron, entitlements en providerflags
blijven buiten deze minimale slice. Als een noodzakelijke verbetering daar toch
wijzigingen vergt: stop dat onderdeel, herformuleer scope en vraag materieel besluit.

## D3/D4 Ontwerp Dat Niet Mag Worden Overgeslagen

Nieuwe gewaarschuwde feitenanalyse botst met huidige 6D safety_hard_stop. Voor een
latere slice moet een afzonderlijke, servergeautoriseerde facts-only route contractueel
worden ontworpen: toegestane bronnen/tijdvensters, bronherkomst, metric-units/plausibiliteit,
onvoldoende data, waarschuwing/help-first, geen vrije adviesvelden, eigen consent en
eventuele recoverybinding. Geen gate schrappen of bestaande analyse stil omnoemen.

Normale gepersonaliseerde read-only hervatting na zelf gemeld herstel is nog niet
uitgewerkt of goedgekeurd. Ernstige/terugkerende signalen, onzekere context en verwijdering
vereisen expliciete criteria. Geen permanente gezondheidsblokkade en geen automatische
medische vrijgave afleiden uit dit geheugentestmodel.

D5 unresolved opslag blijft buiten een eerste runtimecorrectie: eerst verantwoordelijke,
doel/noodzakelijkheid, maximumtermijn en verwijderingsgevolgen beslissen. Geen
onopgeloste data alvast verzamelen onder een later-te-bepalen bewaartermijn.

## Acceptatie En Terugweg

- Technisch: schema-exacte output, geen silent downgrade, geen action/provider;
  frozen auth/consent/history/recovery-authority regressies PASS.
- Inhoudelijk: vooraf gedefinieerde gemiste/onterechte signalen en copy beoordeeld;
  geen numerieke medische accuratesseclaim op eigen fixtures.
- Bereikbaarheid: owner bevestigt dat lokale feedback een geladen toegankelijke chat
  vergt, en geen openbare/no-access hulpvoorziening pretendeert te zijn.
- Vrijgave: exacte runtimecommit en relevante reviews plus expliciet stagingrelease-GO.
- Terugweg later: uitsluitend reviewed patch revert en vorige goedgekeurde Edgeversie
  herstellen via afzonderlijk geautoriseerde release; geen database-reset of memberdataherstel.

Niet gekozen: het hele 6E-0 model importeren, R0 als clearance gebruiken, warnings als
vrijbrief voor vrij advies, algemene functieblokkade, automatische trainer/noodmelding,
retentiejob of automatische 6E-1-start. De concrete volgende stap NU is ownerproductreview.
