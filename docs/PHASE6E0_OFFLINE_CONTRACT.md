# Package 6E-0 Offline Contract

Versie: phase6e0.safety.v0.1.0. Status: UNREVIEWED_OFFLINE_PROPOSAL.
Contractbron: _offline/phase6e0/contract.json; uitvoerbare validators: engine.cjs.
Geen diagnose, medische triage, geschiktheidsverklaring of runtimeadapter.

## Input En Output

Input heeft exact contract_version, synthetic_only=true, text (maximaal 4096),
locale, availability en context {timing, subject}. Alleen verzonnen fixtures.
Context is onbetrouwbare contextinformatie, nooit autoriteit om een actueel signaal
uit te schakelen. Geen member-ID, chat-ID, provider, vrije metadata of tools.

Output heeft exact contract_version, review_status, evaluation_state, help_level,
signal_codes, context_states, uncertainty_codes, warning_key, recovery_intent,
medical_clearance=false en automatic_actions_allowed=false. Geen brontekst in output.
Onbekende velden/versies, duplicaten en afwaardering onder de gekozen voorlopige
regelrang worden verworpen. Dit valideert het contract, niet een medische uitkomst.

| Niveau / toestand | Betekenis in dit voorstel | Inhoudsgrens |
| --- | --- | --- |
| R0 | Geen signaal herkend in dit bericht; mogelijk gemist | Geen uitspraak over geschiktheid; alleen begrensde feiten |
| R1 | Voorlopige voorzichtigheid | Geen persoonlijk trainings-/hersteladvies |
| R2 | Stoppen/verduidelijken | Begrensde actuele-contextvraag; geen medische anamnese |
| R3 | Professionele beoordeling | Geen diagnose of terugkeer-naar-training-besluit |
| R4 | Urgente hulp | Concept-help-first; geen automatische melding of wachtrijbelofte |
| uncertain | Ontbrekende, tegenstrijdige, onbegrepen context, taal of instructiepoging | Eigen onzekerheidscodes; kan samengaan met herkend R1-R4, zonder herkenning help_level=null |
| unavailable | Misvormde input of technische onbeschikbaarheid | Eigen foutcode en vaste feedback, nooit vermomd als R0 |

known betekent alleen 'de beperkte regels markeerden geen onzekerheid', niet
betrouwbaar beoordeeld. De vier gedocumenteerde missers produceren zelfs known/R0.
Daarom mag geen runtimeadapter deze velden als medische autoriteit gebruiken.

## Deterministische Herkenning

Normalisatie van hoofdletters, enkele diakritische/spelfoutvarianten en zero-width
tekens; begrensde regexregels per zinsdeel. Citaten, ontkenningen, educatie,
hypothesen en verleden tijd worden apart behandeld. 'Sinds gisteren' geldt niet
als uitsluitend verleden. Nieuwe actuele clausules blijven apart beoordeeld.
Een educatieve opening of ontkende koorts mag actuele borstpijn niet inslikken.
Borstsignaal plus duizeligheid wordt in dit voorlopige ontwerp R4; dit is geen
deskundig vastgestelde drempel. Alle tien categorieen/rangen zijn reviewplichtig.

Complexe grammatica, referenten, impliciete symptomen, andere talen, sarcasme,
meerledige ontkenning en onbeperkte spelfouten zijn niet opgelost. De lexicale lijst
is niet volledig; er is geen model dat onbekende zinnen betrouwbaar kan begrijpen.
known-limitations.json registreert vier concrete missers. Een groene observatietest
betekent daar alleen dat de beperking reproduceerbaar is.

## Vier Afzonderlijke Beslissingen

| Onderdeel | Offline ontwerp | Niet toegestaan / niet geimplementeerd |
| --- | --- | --- |
| Functietoegang | Bestaande authenticatie, volwassenheid, entitlement en toepasselijke consent blijven autoriteit | Gezondheid verandert geen abonnement, rol of algemene toegang |
| Gegevensweergave | Eigen historie onder bestaande autorisatie; nieuwe dagelijkse/post-workout/weekweergave kan waarschuwing plus numerieke feiten tonen | Geen echte dataopvraging; ontbrekend blijft ontbrekend, nul blijft nul |
| Gepersonaliseerd advies | NOT_IMPLEMENTED_REVIEW_REQUIRED; advice=[] | Geen aanbevelingen over belasting, calorieen, doseringen, behandeling of herstel |
| Automatische uitvoering | actions=[], automatic_actions_allowed=false | Geen domain write, trainerdeling, provider of emergency call |

boundedAnalysis is een zuiver viewmodel, geen analyseroutine die echte feiten bewijst.
Alleen completed_workouts, recorded_sets, logged_minutes en reported_sleep_hours;
waarden numeriek/null, eindig, niet-negatief, begrensd; geen vrije tekst. Per-metriek
plausibiliteit, tijdvenster, bronherkomst en correcte serverautorisatie zijn een
toekomstige contracttaak. Een synthetisch authority-object is geen productie-ACL.
Afwezigheid van analyseconsent blijft een autorisatiereden, geen gezondheidsblokkade.

Waarschuwingen maken onbegrensde inhoud niet acceptabel. Hoe normale gepersonaliseerde
read-only analyses hervatten en welke inhoud passend is bij ernstige signalen blijft
OPEN. De huidige 6D-blokkade wordt nergens veranderd of weggeadapterd.

## Herstel En Herhaling

state.cjs simuleert syn- subject/request-identiteiten, verwachte revisie, monotone
synthetische tijd en idempotente verzoeken. Een nieuw of onzeker signaal verhoogt de
revisie en maakt een eerdere zelfrapportage niet actueel. Duplicaten veranderen niets;
zelfde request-ID met andere inhoud, verkeerde subject/revisie of teruglopende tijd
wordt geweigerd. Maximaal 128 events en 256 verzoeken; capaciteit geeft reviewstatus,
geen stille verwijdering. Detailverwijdering kan de synthetische buffer wel legen.

Eigen expliciet herstel via bevestiging of duidelijke actuele chat kan een rapport
vastleggen. Vraagvorm, citaat, verleden, hypothese, ontkende rapportage of herkenbare
ander-persooncontext verleent geen herstelintentie. Nieuwe symptomen in dezelfde
rapportage gaan voor. Deze korte patronen lossen niet alle referent-/grammaticafouten op.

Laag eerder niveau plus actuele eigen rapportage levert uitsluitend
normal_read_only_review_candidate, geen daadwerkelijke hervatting of vrijgave.
R3/R4 blijft serious_recovery_review_required; onzekerheid of verdwenen details blijft
unresolved_review_required. Bounded fact access staat los van die status.
Een nieuw gesprek, verwijdering of tijdverloop levert nooit medische vrijgave.
Dit is geen besluit tot permanente opslag of levenslange blokkade.

Het journal bevat alleen gestructureerde synthetische beslismetadata, geen vrije
chattekst; signalcodes zouden bij echte mensen nog steeds gevoelige gegevens zijn.
delete_details leegt in-memory events en oud journal, houdt een onduidelijkheidsmarker.
Geen bestand, database of echte gebruiker wordt verwijderd of aangepast.

## Voorlopige Retentie

| Soort | Doel / noodzakelijkheid | Bovengrens en anker |
| --- | --- | --- |
| episode_counter | Herhaalde gebeurtenissen tellen zonder chattekst; geen klinische predictie of automatische drempel | Rollend 30 dagen vanaf gebeurtenis; exacte grens valt buiten venster |
| closed_details | Noodzakelijke afhandeling van afgesloten/betwist signaal | Maximaal 90 dagen na expliciete afsluiting |
| minimal_audit | Alleen indien noodzakelijk minimale inhoudsloze beslismetadata | Maximaal 180 dagen vanaf creatie, niet opnieuw verjaren bij lezen |
| unresolved_signal / niet-afgesloten details | Doel, verantwoordelijke, maximum en verwijderingsgevolgen nog niet vastgesteld | review_ids; geen automatische 'bewaren voor altijd' of 'veilig door verwijderen' |

Niet-noodzakelijke afgesloten/minimale records worden direct voor verwijdering
voorgesteld. Grenzen mogen korter, nooit langer dan 30/90/180. retentionPlan/episodeCount
schrijven niets; delete_ids zijn alleen een synthetisch plan. Zelfs bij onnodig
genoemde onopgeloste data kiest het model geen beleid: review_ids is een blocker voor
latere opslag, geen toestemming deze data te verzamelen/bewaren. Chat en bestaande
analyses vallen buiten dit voorstel. Synthetische tijd bewijst geen productiecleanup.

## Hulp En Copy

copy.json: NL/EN/DE, DRAFT_NOT_EXPERT_APPROVED. Geen openbare hulppagina.
In een reeds toegankelijke sessie is de concepttekst onafhankelijk van een provider.
Een onbekend land blijft onbekend. Alleen een expliciet opgegeven NL/BE/DE/AT/IT/FR
selecteert de beperkte EU-conceptverwijzing; dit is geen volledige landenroutering.
112 is het EU-noodnummer volgens de [Europese Commissie](https://digital-strategy.ec.europa.eu/en/policies/112)
en [Your Europe](https://europa.eu/youreurope/citizens/travel/security-and-emergencies/emergency/indexamp_en.htm),
gecontroleerd 2026-09-07. Die broncontrole keurt de concepttekst of niveaumapping niet goed.

Uitgelogd, zonder AI-toegang/consent, bij onbruikbare sessie of niet geladen frontend
is deze plaatsing niet beschikbaar. Provideronafhankelijk betekent niet gegarandeerd
offline bereikbaar bij een volledige app-/authstoring. Taal, lokale hulproutes,
juridische verwachtingen en medische formulering blijven reviewplichtig.
