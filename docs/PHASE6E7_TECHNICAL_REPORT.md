# Package 6E-7 Technical Report

TECHNICAL PASS / READY FOR OWNER REVIEW - SYNTHETIC DEMO ONLY.
Owner GO K1-K4 verwerkt; resultaten NIET owner-accepted/frozen.
Phase 6E ONVOLTOOID. 6E-8 PROPOSED / NOT STARTED.

## Baseline En Scope

Repositoryroot: supabase/.temp/phase4fb-staging-deploy, Yourizorge/fitmetzorge-staging,
main. Start lokaal/cached/direct remote ef42876164f82330de016cb38c5213034cd2f072;
beginwerkboom schoon. Geen nieuwere wijzigingen teruggezet.
AGENTS/config gelezen: auto_review, on-request, workspace-write, projectnetwerk
en permanente stagingautonomie. Managed toegangsgrenzen niet gewijzigd/omzeild.

Preregistratie: 5e59074ce78b6c409cec43d47712c98c62ff5ecb.
Implementatie: c38d9d89797cd1f794463b645579f65fe4851930.
12 private 6E-7-bestanden (inclusief preregistratie), 7 publieke demobestanden.
Exacte Git-blobs/raw/checkout SHA-256: PHASE6E7_EVIDENCE.json.
Alle 122 frozen 6E-0..6E-6-bronnen en 60 bestaande runtime-assets behouden.

## Uitvoerbare Implementatie

- adapter.cjs voert de bestaande frozen 6E-6-engine read-only uit. Controle op
  uitgegeven voorstel, eigenaar, planhash, exacte oefening/set en alle wijzigingen.
- build.cjs genereert alleen de publieke synthetische allowlist: 16 vaste scenario's.
  Geen private modules, safety-records, chat, authsessies of credentials in data.js.
- training-review-demo/model.js is een NIEUW publiek mockcontract, gedeeld door
  offline tests en UI. Import uitsluitend private -> public; geen frozen bundel.
- De private workspace controleert frozen bronnen/context opnieuw voor commando's.
  De browser gebruikt expliciete gesimuleerde brongebeurtenissen, geen live classifier.
- Volgorde verplicht: lidacceptatie -> trainerakkoord -> aparte trainer-apply.
  Geen trainer, weigering, blokkade, consentverlies, incomplete data of bronconflict
  geeft geen gedeeltelijke wijziging. Beide akkoorden alleen wijzigen niets.
- Commando bindt actor, subject, proposal-ID, exacte inhoudsbasis en reviewrevision.
  De inhoudsbasis bevat de frozen bron-/regelbinding. Zelfde ID/inhoud is retry;
  andere inhoud bij zelfde ID wordt geweigerd. Geen dubbele versie/audit/melding.
- Eén in-memory publicatiegrens voor plan, vorige versie, status, audit en outbox.
  Fout voor commit publiceert niets. Dit is GEEN duurzame DB-transactie.
- Restore neemt een bewaarde inhoud over in een nieuwe monotone versie, na twee
  NIEUWE akkoorden en aparte apply. v3 -> v4 -> restore v3-inhoud = v5. Bestaande
  historische sessies/bronnen worden nooit als nieuw oorspronkelijk schema herschreven.
- Meldingen volgen een vaste neutrale allowlist. Geen medische of privéchatdetails.
  Onbekende/ongeldige commando's leveren een fout zonder mutatie; audit bevat alle
  geregistreerde workflow- en gesimuleerde bronovergangen, niet een echte securitylog.
- W2 toont ingestelde numerieke stap/unit en beschikbare gewichten, zonder afgerond
  alternatief of extra reps. Frozen 6E-6 blijft ongewijzigd; oude weergavebeperking
  is opgelost in deze nieuwe presentatie-adapter, niet teruggeschreven in oud bewijs.

## Technisch Testbewijs

1323/1323 PASS, 0 FAIL/SKIP:
186 nieuwe 6E-7-checks, plus 1137 frozen functionele regressies.
Frozen groepen: 6E-6 112; 6E-5 144; 6E-4 229; 6E-3 111; 6E-2 159;
6E-1 292; 6E-0 90. Oude scope-isolatiechecks accepteren terecht geen nieuwe
pakketten en zijn vervangen door de nieuwe streng afgebakende 122/60-hashcontrole,
niet door runtime-uitzonderingen. Bekende taalobservaties zijn GEEN herkenningssucces.

Nieuwe matrix omvat 112 status/rol/actiecombinaties, volledige restore en meerdere
versies, bronverlies in drie reviewfasen, foutinjectie, dubbele opdrachten, bindings-
en tampertests, W1/W2, RIR0/null/RPE en lb/kg, exacte O5-grens/earlier omission,
private verse contextcontrole en minimummeldingen.
De 30 bestaande NL/EN/DE-voorbeelden zijn opnieuw uitgevoerd en exact gelijk aan
het oorspronkelijke 6E-6-bewijs. Daarnaast 15 nieuwe uitvoerbare workflowvoorbeelden
in PHASE6E7_EXAMPLES.json/.md.

Browser: 343/343 lokale checks, 24 combinaties:
320/390/768/1280 px x NL/EN/DE x licht/donker. Volledige accept/approve/apply/restore,
herladen/reset, afwijzing/blokkade, W2 en consentverlies bediend.
0 page errors, 0 browseropslagpogingen; statische demo-GETs alleen in de bewaakte flows.
Geen provider- of app-API. Responsive metingen controleren document/elementgrenzen
en zes exact gewijzigde cellen. Vier screenshots, visueel bekeken.
Alles is headless Edge/Playwright-EMULATIE; geen fysieke telefoontest geclaimd.

## Gevonden En Hersteld Voor Oplevering

1. Op 320 px drukten lange select/grid-inhouden het document tot 486 px breed.
   Min-width/gridcorrectie, mobiele keuzelayout en korte menulabels herstelden dit.
   De oorspronkelijke lokale foutuitslag blijft als artifact bewaard.
2. Bronreview vond een generieke fictieve doelomschrijving die niet exact bij de
   broncode strength hoorde. De presentatie gebruikt nu de aanwezige doelcode,
   niet een nieuw verondersteld historisch doel.
3. Gelijke lokale proposal-ID/revisions lieten aanvankelijk een kg-akkoordcommando
   naar de lb-fixture overzetten. Vooraf toegevoegd regressiegeval faalde 1/1.
   Expliciete proposal_basis-binding herstelt dit; finale suite inclusief die test groen.
   Een eerdere importvolgordefout in deze testharness is apart opgelost en is geen
   bewijs van de productfout of van geslaagde herkenning.
4. Browserharness gebruikt de aanwezige Edge-installatie; Chrome was niet aanwezig.
   Geen softwareinstallatie, nieuw abonnement of kosten.

## Publicatie En Behoud

Alleen docs, _offline/phase6e7 en training-review-demo gewijzigd.
Geen bestaande frontendasset, workflow, runtime, database, migration, Edge,
Auth/RLS, memberdata, entitlement, providerinstelling of productie gewijzigd.
De publieke demo is statisch; geen publieke private bronmap. Bestaande Pages-build
blijft ongewijzigd. Het vóórbewijs vergelijkt alle 60 assets met de frozen hashes;
de oude checker zijn drie Training-uitzonderingen worden NIET gebruikt.

Na push: controle van Pages-run/remote HEAD, alle 7 publieke demo-assets tegen
raw Git-bytes, alle private offline/testpaden HTTP404, dezelfde browsercheck op
de gepubliceerde demo en opnieuw alle 122/60 hashes plus schone werkboom.
Definitief lokaal deliveryreceipt: supabase/.temp/phase6e7-delivery.json.
Dit voorkomt een zichzelf verwijzende commit-hash in het committed bronreceipt.

## Grenzen En Vervolg

De mockklok en expiry-events zijn fictief. Reset wist de hele simulatie, geen
echte veiligheidsregistratie; geen medische vrijgave door reset/herstel/O5-verloop.
De O5-tests gebruiken frozen logica, geen nieuwe live bewaarlaag. Geen echte
trainerautoriteit, RLS, concurrente DB-isolatie, herstel na crash of medische veiligheid
bewezen. Ownerconceptcopy is geen deskundige taal-/medische validatie.
Nieuwe retentie/consent/privacyscope voor echte data blijft apart open.

[Owneroverzicht](PHASE6E7_OWNER_OVERVIEW.md) en
[enig 6E-8-voorstel](PHASE6E8_PROPOSAL.md).
Geen live-AI-integratie. Externe AI-calls 0; externe AI-kosten EUR 0.
Geen automatische owneracceptatie/freeze of vervolgpakket gestart.
