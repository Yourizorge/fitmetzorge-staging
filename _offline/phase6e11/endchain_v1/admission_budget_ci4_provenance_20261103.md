# Admission-budget: CI4-provenance (2026-11-03)

Status: NO_GO_INCOMPLETE_BOUND. Alleen offline receiptcontrole en documentatie;
geen codewijziging, hosted actie, nieuwe CI, migratie of budgetverhoging.

## Werkelijk bewijs

CI4 41619169140: commit 82b51fe167ad74545eb835af3d56268f154ae4e9.
Candidate SHA256: 80a564afadb3114b061bd5b36c0fd5e2ae9d696885417c8e713540236f5be425.
Resultaat: NO_GO, stop admission-test_migration_failure_boundaries_exit_1.

Acht geselecteerde bestanden zijn byte-exact tegen artifact-manifest.json gecontroleerd.
De candidate zelf is op raw SHA gecontroleerd. Beide hooksets (5 bestanden) en
migration-source-inventarissen (46/47 bestanden) matchen de candidate.

| Receipt | Dispatch/bevestigd/numeriek | Unknown | Observers | Isolatie | CLI-reserve |
| --- | --- | --- | --- | --- | --- |
| cli-predispatch-pending-0.json | 47/47/47 | 0 | 8 | 8 | 64 |
| cli-predispatch-pending-2.json | 22/22/22 | 0 | 8 | 8 | 64 |
| migration-boundary-pre.json | 8 lokale diagnostische opdrachten | n.v.t. | apart hierboven | apart hierboven | cap12 |
| migration-boundary-post.json | 8 lokale diagnostische opdrachten | n.v.t. | apart hierboven | apart hierboven | cap12 |

App0/app2: eigen temp_written=0, top/top en utility on/on. Dit bewijst uitsluitend
top-level protocolcorrelatie, niet nested SQL, fysieke WAL0, canonical45 of hosted.
cli-protocol-0/2 zijn compatibiliteitsweergaven: extra charge0.
De CLI-sluitreserve1 zit al IN64. Boundarypaar: normaal16, cap24.

## Binding aan huidige grafiek

De bestaande API admission_budget.run(gate) is uitsluitend in geheugen aangeroepen:
gate.out wijst naar de CI4-receipts; gate.result is het echte CI4-resultaat;
gate.save bewaart uitsluitend geheugenobjecten. Geen oud exportbestand gewijzigd.
Lossless round-trip PASS: 15 members, maximaal 1333598 bytes.
Volledige export alleen in geheugen; dit JSON/MD-paar is de blijvende provenance.

Huidig model: 1717 referentierijen, 11724 prefixuitkomsten, referentiecapaciteit2338;
limiet2349 en sluitreserve731 ongewijzigd, minimal_cap=null.
Full-register SHA256: fed4e9d2ca1d6cfad5b8a5d7b3ada7a3a3095c6b8dc1478a48dfdefab8a4d49d.
Grafiek SHA256: 6391223fe66a82b4f8a566107476d5897315301c26c07128e4d145532731ac75.

De bronset is NIET de CI4-candidate. Verschillend binnen model-source_hashes:
- admission_budget_graph.py
- admission_budget_register.py
- admission_ci.py
- auth_failure.py
- test_migration_failure_boundaries.py
Dit maakt de CI4-receipts geen uitvoeringstest van de huidige grafiek.
De twee appreceipts vervangen GEEN canonical45-knoop of normale budgetrij.
Alle bron- en receipthashes staan in het bijbehorende JSON-bestand.

## Kosten versus ontwerp

- Canonical45: instrumented receipt nog ontbrekend. A1/D bouwen volgens Main
  CLI64 + observers8 + bestaande isolatie8 + boundary16/24.
  Rekenkundig96 normaal gereserveerd /104 met boundarycaps, uitsluitend voor
  die opgegeven tak. Geen gemeten totaal, bewezen foutmaximum of hosted cap.
- Volgende concrete sluiting: exact canonical45-ledger plus bron/bytebinding,
  startup/unknown/cancel/isolatieherstel-prefixen en eenmalige boundary-close.
  Nog aantonen dat isolatie8 elke fouttak dekt; rollback1 niet nogmaals optellen.
- Pre_auth/final: huidige referentie elk28+8=36. CI4 heeft geen afsluitende
  cli-predispatch.json. Werkelijke slotreceipts en foutafsluiting blijven nodig.
- Auth: gemeten create/login/logout/delete-kosten en unknown-consumed grenzen
  plus plaatsing ontbreken. Diagnostisch524/case of128/actie bewijst geen
  releasekosten. De360 workflowprecharge, inclusief130 cleanup, is al betaald.
- Fixture/recovery: prepare4 + capture1 per echte writer + cleanup22 zijn
  componentkosten. De74 bronankers bewijzen geen74 echte captures.
  Producer-/mintbarriere, vervanging versus toevoeging en unieke
  rollback-/close-eigenaar per foutprefix moeten nog worden verbonden.

Geen nieuwe minimumcap afgeleid. Geen full-chain PASS. Code blijft bevroren
voor review F; alleen deze twee nieuwe documentatiebestanden zijn toegevoegd.
