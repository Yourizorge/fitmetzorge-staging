# Training Mobile Follow-Up

## Scope And Baseline

Owner-requested three-point refinement after phone testing. Work began 2026-09-08;
technical verification/publication 2026-09-09. No automatic owner acceptance or freeze.
Only Yourizorge/fitmetzorge-staging / main and its staging Pages site are authorized.
Preflight: clean worktree, exact Git root supabase/.temp/phase4fb-staging-deploy,
local HEAD, origin/main and direct remote main all
633e9f9ab50bd298a66088e6cc0cb824215e98f5.
AGENTS.md and .codex/config.toml read. Existing auto_review / on-request /
workspace-write and scoped autonomy retained; managed boundaries honored with
reviewed commands. No permission, workflow, provider or entitlement changes.

Prior Training runtime: ed1f485af87d68ad7ec6cbee55ba9fda074af9ce.
New cache identity: 20260908-training-mobile1.
Runtime/test commit: 58515aa99792e99c8b733e0c3c7b54ecb0d2a634.
Six authorized runtime paths: app.js, index.html,
assets/phase3-training-engine.js, assets/training-workout-ui.js,
assets/training-workout.css and new assets/vendor/lucide-clock.svg.
The model and owner-settings runtime sources remain unchanged.
Commit, Pages and byte verification: [publication receipt](TRAINING_MOBILE_PUBLICATION.md).
Detailed checks/hashes: [machine evidence](TRAINING_MOBILE_EVIDENCE.json).

## Cause And Correction

| Phone finding | Cause | Correction |
| --- | --- | --- |
| Familiar exercises require prior knowledge/search | Alphabetical 72-item first batch without a curated entry view | 35 exact existing identities in six expanded groups before the 72-item remainder; no extra load/tab for basics |
| Previous result and effort below the set | Mobile CSS explicitly assigned both to grid-row:2; labels repeated per set | One shared six-column row/header, five columns for None; 44px save targets; full previous value can wrap inside its own same-row cell |
| Checkbox does not open a usable timer | Global preference only gated automatic rest; panel existed only with an active countdown | Clock + Rusttimer opens an idle duration/Start panel; per-session opt-in, manual start before any set; explicit off removes it |

Search and filters cover all 898 catalog identities, including multilingual basic
aliases. Selections survive filtering and details; returning from details preserves
search/scroll. A new entry into the library resets to the expanded basic selection.
No catalog insert, merge, replacement ID or fuzzy matching is performed.
Each basic entry requires BOTH its stored UUID and canonical slug to match;
a missing identity is not silently substituted with a similar exercise.
Names remain consistent in selection, details and the editor.
Existing correct owner-hosted exercise media and the own logo fallback are retained.
No external exercise images/instructions were copied or newly licensed.
The added clock is Lucide's ISC icon; existing vendor license is retained.

Execution keeps one exercise, previous/next navigation, all sets and existing draft
persistence. Optional blanks, explicit RIR 0 and hidden historical RIR/RPE retain
their original semantics. Weight conversion is unchanged. Input text fits measured
content between 12 and 16px, not viewport-sized typography; resize recalculates it.
No new horizontal overflow clipping/hiding rule masks the row geometry.

## Timer Contract

New workout: focus.timerEnabled=false, rest=null regardless of the old global
timer preference. Opening the panel sets this flag only in that workout.
An idle panel offers duration and Start immediately; opening alone starts nothing.
The existing metadata.focus JSON and own-user local session cache retain the
choice, paused remainder and absolute deadline across navigation/refresh.
Existing global preference storage/API fields are left compatible but no longer
enable/disable the active session timer.

Manual rest has an explicit manual marker. Finishing or skipping it does not
register a set, advance an exercise or complete a workout.
Double Start is ignored while a countdown exists; only one interval is allocated.
After explicit opt-in, existing successful-set logic may start automatic rest.
Supersets still alternate exercises and rest only after the round; failed set
writes never start new rest. Corrections reuse the existing set identity.
Pause/resume, +15, skip and off remain reachable without covering set inputs.
The workout elapsed-time clock is separate from the optional rest countdown.

An already-running pre-upgrade timer is retained, including server hydration.
Code review found that the initial new-default merge would have erased an old
server-side timer. Hydration now uses the common focus normalizer, with a
separate regression covering this compatibility case.
Explicit off is respected. New sessions never inherit the old session choice.
No closed-app notification or cross-device real-time timer guarantee is added.

## Exact Basic Mapping

The owner's selection is authoritative. The cited
[StrengthLog reference](https://www.strengthlog.com/most-popular-exercises/) was read;
it is a selection reference, not a source of copied instructions or images.
Evidence uses the existing 898-row read-only catalog snapshot from the preceding
staging delivery. No live catalog or member mutation is needed for this view.

| Group | Display variant (NL) | Existing canonical slug | Existing UUID |
| --- | --- | --- | --- |
| Borst | Bankdrukken (halterstang) | `barbell-bench-press` | `bfcda5e1-5a31-551b-ab00-a34e1d51d9be` |
| Borst | Dumbbell bench press | `dumbbell-bench-press` | `48b83d53-5b2e-5d65-94cc-c0c874e021a2` |
| Borst | Incline dumbbell press | `incline-dumbbell-press` | `7fc87a35-b24f-53c9-bf76-f299bb89f948` |
| Borst | Chest press (toestel) | `machine-bench-press` | `83336082-92c1-5ffc-9577-d66242ec8163` |
| Borst | Pec deck | `butterfly` | `065131ba-6d12-53f9-a737-6b501bda164f` |
| Borst | Cable fly (hoge kabels) | `cable-chest-fly` | `fa6ff1f2-c453-58da-9510-a26d5fd6d5b5` |
| Rug | Lat pulldown (brede greep) | `wide-grip-lat-pulldown` | `fbd17d30-8eec-500a-a123-d2873f5981cd` |
| Rug | Seated cable row (smalle greep) | `seated-cable-rows` | `7e11783e-3582-5023-b965-afaf877e4e1b` |
| Rug | Barbell row | `bent-over-barbell-row` | `06baffb3-553f-5f3c-8a00-717203bb347f` |
| Rug | Eenarmige dumbbell row | `one-arm-dumbbell-row` | `f4b3d183-68b9-5d6e-91a7-751fb49fc444` |
| Rug | Pull-up | `pull-up` | `ee7e42f1-3ade-5ccc-92e2-a29fb9d51f4f` |
| Schouders | Dumbbell shoulder press (zittend) | `dumbbell-shoulder-press` | `8deb73f1-ca3e-5f31-b089-077b66316a84` |
| Schouders | Overhead press (halterstang, staand) | `standing-military-press` | `e2229c50-85ca-5eb6-a22d-c21eaf7c56b0` |
| Schouders | Shoulder press (toestel, schijven) | `leverage-shoulder-press` | `1feff4cc-8c69-5c92-8d83-2200bad83b70` |
| Schouders | Lateral raise (dumbbells) | `lateral-raise` | `9e9fc710-be0c-5fe0-998c-c69f4f6be489` |
| Schouders | Reverse pec deck | `reverse-machine-flyes` | `e7669f95-1624-5f4a-a5ab-08fc82e15208` |
| Schouders | Face pull | `face-pull` | `ee29b63d-e33f-5c62-9677-dafc1b5b9200` |
| Benen / billen | Squat (halterstang) | `barbell-squat` | `62ac4931-aa57-5795-a722-3888f965e3df` |
| Benen / billen | Leg press | `leg-press` | `55b90c36-5e1b-5582-a1f4-e3adbe4c71d8` |
| Benen / billen | Leg extension | `leg-extensions` | `6b01e0b0-4d0c-5c4e-a001-afa2d1096b98` |
| Benen / billen | Leg curl (zittend) | `seated-leg-curl` | `c2a48629-90de-5237-9ef9-438b9d61281f` |
| Benen / billen | Leg curl (liggend) | `lying-leg-curls` | `d1112790-f11f-514b-9319-ce7589d0b109` |
| Benen / billen | Deadlift (halterstang) | `deadlift` | `a521421d-dc22-533c-a570-b8131e068a7f` |
| Benen / billen | Romanian deadlift (halterstang) | `romanian-deadlift` | `32613884-3784-591e-af61-027451680252` |
| Benen / billen | Hip thrust (halterstang) | `hip-thrust` | `846cb8a7-4939-5509-943c-1efeee5e2d0a` |
| Benen / billen | Bulgarian split squat (dumbbells) | `split-squat-with-dumbbells` | `5824adeb-3e94-50fd-b1ba-61496cfda317` |
| Benen / billen | Hip abduction (toestel) | `thigh-abductor` | `c4bb9acb-7973-5245-95a1-e6016c3dd8d3` |
| Benen / billen | Calf raise (staand, toestel) | `standing-calf-raises` | `fdefc70c-dbd2-5f84-a3b8-7eae3c5b2643` |
| Armen | Dumbbell curl | `dumbbell-bicep-curl` | `8c8fba33-55d1-5a58-a4a9-33ff13cd2252` |
| Armen | Barbell curl | `barbell-curl` | `9fedd062-4d81-546a-8eac-e0db59b0ff76` |
| Armen | Hammer curl | `hammer-curls` | `640a857e-3b6b-521e-be8d-da729825ac37` |
| Armen | Triceps pushdown (stang) | `triceps-pushdown` | `2cefd973-2a11-5a85-b372-c31b7d1d4e7c` |
| Armen | Triceps pushdown (touw) | `triceps-pushdown-rope-attachment` | `704e0ce4-c007-573f-94f2-b6dee76f376b` |
| Buik | Crunch | `crunches` | `f2380b42-08ca-5c9b-a074-5cf394b8a91b` |
| Buik | Cable crunch | `cable-crunch` | `300b0022-6c14-5b99-91fb-9f5bb49ce3e5` |

Execution distinctions were checked against catalog equipment/instructions:
standing barbell overhead press is not seated barbell shoulder press; machine
chest press is not cable or dumbbell press; reverse pec deck is not a dumbbell fly.
The Bulgarian entry is the existing dumbbell split squat with rear foot elevated,
not the catalog's bodyweight jumping split squat. Cable fly uses the high-pulley
standing variant; seated cable row uses the close neutral V-bar grip; calf raise
uses the standing machine. Both pushdown attachments remain separate identities.

## Verification And Limits

The focused unit contract was written before runtime correction: initial 2 PASS /
4 FAIL because the basic mapping/manual-session API did not yet exist.
Current focused checks include an additional server-hydration regression.
These are technical UI/state/data-identity tests, not medical or training efficacy proof.
Local final result: 29/29 unit/preservation/theme checks, 6/6 historical completion
regressions and 940/940 browser assertions. The browser matrix records 90 geometry
probes and 71 unique screenshots: 244 assertions on each phone width, 208 on desktop.
Syntax checks of the three changed JavaScript files and git diff --check pass.
Published matrix: 940/940 PASS on the same four sizes; 60/60 assets match Git.
54 assets retain the phone baseline; 56 offline/test paths return HTTP404 on Pages.
Exact publication and byte records are retained separately in the receipt/evidence.

The browser matrix uses actual application JS/CSS, real controls, retained catalog
identities and exclusively synthetic backend fixtures. Every network request is
intercepted; unexpected live Supabase requests fail the test.
Sizes: 320x700, 360x780, 390x844 and 1440x900.
Execution covers NL/EN/DE in both light/dark, all RIR/RPE/None modes, long previous
performance, large numeric inputs, 0/blank values and geometry/tap targets.
The maker also covers NL light, EN dark and DE system/dark with basic aliases,
selection/search/details retention and correctly loaded media/fallback.
Existing plan editor/drag/reorder, atomic save/retry, failed parent/set writes,
supersets, active timer refresh/background return, lost completion response and
one completion/history entry remain in the matrix.

Keyboard coverage is focused typing plus a reduced viewport representing keyboard
space. Desktop Edge automation does not open a physical iOS/Android OS keyboard.
Physical keyboard, device browser chrome, zoom and touch acceptance remain for
the owner's phone retest. No claim of full physical-device acceptance is made.
A test fixture initially expected 2721.76 lb for 1234.56 kg; corrected to 2721.74.
The conversion implementation was not changed to satisfy that test.
Historical reports and TRAINING_WORKOUT_EVIDENCE.json remain intact.

No database, migration, Edge, member, provider or production operation is performed
in this task. All mutation/retry/completion tests are synthetic, not real accounts.
There is no new live before/after member fingerprint claim; the previous package's
fingerprint evidence is historical. Source preservation and absence of live member
calls are the data-safety evidence for this frontend-only delivery.
No file deletion or OneDrive/PostgreSQL cleanup.

## Phone Retest

1. Open staging en vernieuw. Kies Training -> Workout maken / Oefeningen toevoegen.
2. Controleer Basisoefeningen direct; scroll tot Buik zonder Meer te gebruiken.
3. Selecteer een basisvariant, zoek/filter en open details; controleer behoud.
4. Start een workout: vorige prestatie, gewicht, reps en RIR/RPE staan op een rij.
5. Test met open toetsenbord; kies ook Geen en controleer de verdwenen kolom.
6. Zonder setregistratie: Rusttimer -> duur -> Start; test pauze/+15/overslaan/uit.
7. Controleer refresh en de volgende nieuwe workout: dezelfde keuze blijft,
   maar een nieuwe workout begint weer zonder timer.
8. Registreer een superset en rond eenmaal af; controleer historie.

6E-0 remains accepted/frozen OFFLINE ONLY. All offline 6E-1 sources and D1-D12
remain unchanged. Phase 6E is incomplete. No new package, live AI integration,
expert-review contact, owner freeze or production action.
Only next step: owner phone retest of these three Training refinements.
