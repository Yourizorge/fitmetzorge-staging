# Package 6D Read-Only Analyses - Architecture And Readiness

Status: AUDIT COMPLETE / OWNER DECISIONS REQUIRED / IMPLEMENTATION NOT STARTED

Date: 2026-09-04
Scope: Yourizorge/fitmetzorge-staging / main; Supabase mokxyyullfhkfalopbzd only.
Audit baseline: f8050c26e9b773b7954901ded780b13efa6fe040.
Package 6C: COMPLETE / OWNER-ACCEPTED / FROZEN.
All designs, names, retention periods and cadence below are recommendations, not implemented or silently approved product decisions.

## 1. Current Reusable Architecture

The live 6A trust boundary supplies versioned consent, current AI/PT entitlement, age eligibility, private schemas, RLS/ACL, source manifests, run identity, rate buckets, budget reservation/reconciliation, safety state and lifecycle records. The 6B adapter supplies exact model routing, Responses API structured output, usage parsing, sanitized failures and no fallback. The 6C member chat, deterministic NL/EN/DE medical classifier, immutable messages, sequenced retries, export/deletion and grace are owner-accepted. No new parallel provider, entitlement or budget authority is justified.

Evidence inspected:
- `supabase/migrations/20260901193000_phase6a_ai_trust_foundation.sql`, especially `fmz_phase6a_get_context_manifest`, `trust_status`, `service_begin_run`, `service_complete_run` and `service_fail_run`.
- `supabase/migrations/20260901230000_phase6b_provider_privacy_cost_gate.sql`, `supabase/functions/youri-ai/{contracts,provider-contracts,openai-adapter,phase6b-handler,phase6c-handler,index}.ts`.
- Frozen Phase 3 foundation/ownership, Phase 4 logging/replacement/provider snapshots, Phase 5 foundation/dashboard and unit-preference migrations; member Tracker rendering in `assets/member-ux-consistency.js`.
- Read-only staging catalog metadata, not member health values or chat contents.

Live audit: 6B 36/36; 6C 37/37; request-scoped safety 16/16. The post-6C 6A freeze variant passes 47/47. All 18 inspected domain source tables retain RLS. Edge v41 has JWT enabled and all nine source files match implementation commit `bb5076a6d19e304a5e093af38090314fa85379dc`. Mock chat is enabled, member provider processing and all 6A feature flags are disabled. No OpenAI call, provider probe, application RPC or fixture write was performed.

## 2. Gaps And Blockers

1. The existing context RPC is an availability foundation, not an analysis-ready metric API: active-plan count, recent-session counts, logged-day counts and latest timestamps. It does not supply macros, workload or weight trends. It also uses database `current_date` for some windows rather than a unified member-local day.
2. Phase 5 calculates useful server metrics but its dashboard payload also contains raw IDs, notes, absolute measurements and a seven-observation weight average. Forwarding that payload wholesale would violate minimization. Seven observations are not seven calendar days.
3. Recovery sleep/steps/wellbeing are normalized. Water, bedtime/wake time and legacy tracker goals still use workspace/browser fields. No authorized normalized water source exists for 6D; report unavailable instead of reading a whole `coach_workspaces.state`.
4. There is no reviewed analysis-purpose/category opt-in, canonical AI timezone policy, stable daily/weekly/event identity, evidence-linked output schema or analysis retention/export/delete implementation.
5. The generic 6A response validator permits up to eight allowlisted actions. A 6D-specific strict no-action validator is mandatory; the generic validator alone is insufficient.
6. Generic `service_complete_run` persists a result only with a thread. Reusing private-chat threads would mix 6C history/retention with analysis delivery. A result record with independent lifecycle is recommended, reusing run/manifest/budget tables.
7. 6B paid endpoints accept locked synthetic fixtures only. They must never be repurposed by passing member aggregates into a synthetic fixture. The 6A failure function releases reservations; a future paid member path must distinguish known-no-charge from unknown-charge failure and reconcile conservatively as proven in 6B.
8. 6A general trust treats retained serious safety state as an operational denial; 6C intentionally separates communication. 6D needs an explicit fail-closed analysis decision, not a relaxation of either frozen gate. A blocked analysis returns reviewed local safety copy while private chat remains independently available.
9. Historical nutrition target snapshots exist on `food_logs`; do not compare every past day with today's target. A logged day is not a certified complete intake day. Training plans lack an immutable scheduling denominator; active plans/days do not prove scheduled attendance.
10. Provider legal activation is blocked independently of technical implementation: ZDR, DPA, DPIA, exact EU route, privacy/medical copy and owner activation remain unresolved. Approval of 6B paid synthetic tests is not member-processing approval.
11. Latest schema is PostgreSQL 17; no schema compatibility work is needed for this audit. Future additive grants must be explicit. No current read-only audit blocker arose from the Supabase changelog.

12. Additional material legacy authorization finding from the read-only advisor follow-up: `public.fmz_bootstrap_trainer_profile(uuid,text,text)` is SECURITY DEFINER with anon/authenticated EXECUTE and accepts a supplied user ID without an auth.uid/service authorization guard in its body. It can write profiles/workspaces. `accept_client_invite` uses user-editable JWT user_metadata to choose trainer/client linkage; the Auth trigger also reads raw_user_meta_data role. These are pre-existing paths outside 6C, not 6D changes. No exploit or mutating test was run. Separate owner-scoped security review/correction is required before relying on these identity/linkage boundaries for 6D or real-member provider activation. Do not fix them automatically in a frozen read-only audit.

These are readiness gaps, not changes made to frozen 6C. Do not repair domain data, broaden access or deploy a partial analysis route during this audit.

## 3. Authoritative Source Matrix

Closed-world allowlist: every field not explicitly allowed below is prohibited in a provider manifest. R = required for the named feature when available (otherwise missing/insufficient); O = optional only if it improves that feature; P = prohibited externally. Gate-only fields remain internal. All sources are member-owned, accessed through an authenticated server boundary, never browser-authoritative.

Retention codes: E = ephemeral context in Edge memory only, no prompt log; R90 = proposed validated-result lifetime at most 90 days; M180 = proposed metadata-only audit lifetime at most 180 days, purpose/retention owner review still required. Frozen source retention is unchanged. Source IDs/revisions stay internal for replay/freshness; provider uses short evidence tokens and an unrelated per-request pseudonym, never an auth UUID or hash of an email.

| Source / candidate fields | Class and representation | Lookback / authority | Sensitivity and retention | External eligibility after ALL gates |
| --- | --- | --- | --- | --- |
| Auth/profile `id,role,trainer_id,client_id` | R gate-only, exact server binding | current; Auth + profiles | identity; no new copy | NO |
| Profile/onboarding names, email, address, birth date | P | never selected | direct identity; none | NO |
| `user_onboarding.age` | R internal >=18 boolean; no exact age sent | latest saved, freshness flagged; Phase 1 | identity/health; E | NO, gate only |
| `user_settings.language,unit_system` | R locale; O presentation setting | current Phase 1 | low; E/R90 | locale only; canonical metrics remain kg/cm |
| `user_settings.country` | O local emergency-copy selector, not prompt identity | current Phase 1 | location; E | NO for initial analyses |
| `nutrition_preferences.timezone_name`, `progress_preferences.timezone_name` | R internal calendar/window boundaries | current + recorded domain dates | location-adjacent; E/internal manifest | relative day/week offsets only; no zone needed externally |
| `progress_goals.goal_code` | R for goal feedback; enum | active normalized goal; Phase 5 | fitness intent; E/R90 | YES enum |
| `progress_goals.baseline_weight_kg,target_weight_kg,target_date` | O aggregate distance/progress direction; no raw target date | active goal plus <=28d evidence | health; E/R90 | YES derived distance/change only |
| `user_onboarding.fitness_goal,goal_direction,training_experience,available_days` | O typed context; explicit fallback if no active progress goal | latest; Phase 1; freshness required | fitness; E/R90 | bounded enums/count; planned days not attendance denominator |
| `goal_safety_status` | R internal safety gate | current Phase 1; no inference from empty | health; E/safety metadata | NO raw value needed; local stop |
| Onboarding `height_cm,weight_kg,gender,bmi,target_weight_kg,goal_timeline_weeks` | P for initial provider analyses; normalized progress supersedes stale starting weight | no prompt use | health; none | NO; no calculator/BMI/diagnosis |
| Onboarding preferences/constraints/safety notes; goal notes | P free text | no prompt use | potentially health/private; none | NO |
| Active `training_plans/days/exercises` status, planned sets/reps | O bounded counts; current plan context only | current Phase 3, all parent/child owners checked | fitness; E/R90 | counts only; never plan titles/notes or mutation suggestions |
| `workout_sessions.status,started_at,completed_at` | R completed-only counts, recency, elapsed-time caveat | selected completed session or 7/28d; Phase 3 | activity; E/R90 | aggregate counts and relative dates |
| Session pause/resume/metadata | P raw; O validated duration only if server-verifiable | session; Phase 3 | behavioral; E | NO browser timer authority; elapsed != active training duration |
| `workout_set_logs.actual_reps,actual_weight` | R per-exercise grouped sets/reps/volume and bounded trend | completed owned parent, selected/28d | fitness; E/R90 | derived metrics, no set-level dump |
| `exercise_id,exercise_slug,training_plan_exercise_id` | R internal grouping; O controlled exercise taxonomy | same canonical ID/legacy slug; Phase 3 | identity linkage; E/internal manifest | short local evidence label; no internal IDs |
| `rir,rpe` | O aggregates with sample count | selected/7/28d | subjective fitness; E/R90 | YES, explicitly self-reported |
| Set `target_reps,target_weight` | O safe typed snapshot comparison; discard unparseable target-reps text | selected session only | fitness; E | numeric ratio only; no missing target interpreted as zero |
| Exercise/session names, notes, metadata, legacy planned keys | P raw untrusted text | no prompt use | injection/private; none | NO |
| `food_logs.log_date,status`; item `status` | R active parent + active child, own-user join | today/7/28d in recorded nutrition-local date | diet; E/R90 | coverage counts/relative dates |
| `food_log_items.energy_kcal_snapshot,protein_grams_snapshot,carbohydrate_grams_snapshot,fat_grams_snapshot` | R authoritative sums per logged day | active items, same user; Phase 4 | health; E/R90 | YES aggregate kcal/g; never recalc from browser/catalog |
| `fiber_grams_snapshot` | O sum + missingness | same domain/window | health; E/R90 | only if feature explicitly needs fiber |
| `food_logs.target_*_snapshot` | R for historical target comparisons | exact day snapshot; Phase 4 | health; E/R90 | aggregate ratios/deltas, missing target explicit |
| `nutrition_targets.energy_kcal,protein_grams,carbohydrate_grams,fat_grams` | O current target only, effective-window aware | current active member-authoritative daily target | health; E | aggregate current comparison; no new targets |
| Foods/brands/barcodes/portions/quantities/provenance/provider IDs/notes | P raw external context | snapshots remain DB authority | diet/licence/private; no copy | NO; OFF/USDA details and ODbL provenance remain intact internally |
| `weight_logs.weight_kg,log_date,status` | R sample count, bounded trend/delta | active entries <=28d; Phase 5 | health; E/R90 | rounded aggregate deltas; absolute weight unnecessary initially |
| `body_measurements.*_cm` | O per-measurement delta/sample count; no composite body-fat claim | active entries <=28d; Phase 5 | health; E/R90 | only purpose-selected deltas |
| Progress `notes,measured_at,source,request_id,supersedes_*` | P external; R internal lineage where needed | Phase 5 | private/technical; E/internal manifest | NO |
| `recovery_logs.sleep_hours,sleep_quality` | R for recovery, O combined summary; mean/range/coverage | manual entries 7/28d; Phase 2 | health; E/R90 | YES aggregates; not wearable/clinical measurements |
| `steps` | O mean/trend and days with values | 7/28d; Phase 2 | activity; E/R90 | YES; no GPS and no invented activity energy |
| `wellbeing_energy,wellbeing_stress,wellbeing_motivation,recovery_feeling` | O bounded score aggregates/sample count | 7/28d; Phase 2 | health; E/R90 | YES only selected purpose; no diagnosis |
| `wellbeing_mood,training_load_status,training_load_source` | O recognized enum frequencies/subjective-source marker | 7/28d; Phase 2 | health; E/R90 | allowlisted categories only, no causal/physiological inference |
| `recovery_note,metadata` | P prompt input | no bulk read | health/private; none | NO; no silent chat/note harvesting for medical triage |
| Water/bedtime/wake time/legacy step or water goals | P initial source, unavailable marker | browser/legacy workspace, not normalized authority | health; no copy | NO |
| Entitlement code/status/start/end/source | R gate-only; current `ai|personal_coaching` | exact current server time; Phase 1 | access/billing metadata; existing authority | NO |
| `ai_consent_events` version/purpose/categories/state | R gate-only; latest ordered event + active document | current 6A/6C; recheck at delivery | consent/private; existing authority | NO |
| `ai_member_safety_state` status/revision | R local analysis/action gate, not raw history | current 6A/6C | health; existing retention, no new raw copy | NO; stop locally when blocked |
| `ai_threads,ai_messages` all content | P; chat is NOT analysis context | no lookback in 6D v1 | highly private; 6C retention unchanged | NO, separate future scoped consent required |
| Trainer messages/notes, progress photos, GPS, legacy workspace blob | P | never selected | high sensitivity; none | NO |
| Request/schema/policy/evidence tokens and missingness | R non-identifying manifest | current run | operational; E/R90/M180 | YES opaque per-request token, enums and relative window only |

Authority rules:
- Prefer active Phase 5 progress goal over historical onboarding intention; label disagreement, never overwrite either.
- Nutrition totals include canonical, private custom, USDA transient and OFF snapshot items without joining nullable `food_id`. No ml=g conversion and no catalog promotion.
- No food entries means unknown/unlogged, not zero consumption. No targets means no adherence percentage. Ratios do not prove dietary adequacy.
- Compare like-for-like exercises; do not sum load across incompatible exercises or infer calorie burn. Phase 5 estimated 1RM is an estimate, not measured strength; omit unless separately approved for the specific analysis.
- Recovery and Nutrition dates are already local-domain labels; don't shift them again. Training timestamps require a server-approved AI timezone. Do not silently unify differing Nutrition and Progress timezones.
- No authoritative injury/medical record, running activity, wearable/Health sync, photo analysis or trainer-sharing relation exists here. Honest missingness is required.

## 4. Minimum Manifests Per Analysis Type

Common required envelope: schema/policy version, analysis_kind, locale, random request token, relative window length, source coverage/freshness, bounded evidence tokens and confidence reason codes. Context assembly is a bounded SELECT-only server read under authenticated ownership. Source revisions and exact source cutoff stay internal, not prompt text. Unknown fields fail closed.

| Analysis | Minimum domain fields | Window / proposed trigger | Insufficient-data behavior |
| --- | --- | --- | --- |
| Daily status | completed-session count, logged kcal/macros vs same-day target, available recovery scores; optional goal enum | local current day + 7d context; user-open/request first | partial-day label; summarize only present domains |
| Post-workout | completed session, grouped set/repetition/volume counts, optional RIR/RPE | one session + at most 3 comparable sessions within28d; event-keyed on request | zero sets => completion fact only; no progression |
| Training trends | two 7d aggregate windows, comparable-exercise sample counts, volume delta | <=28d; weekly or explicit request | fewer than2 comparable sessions => no trend |
| Nutrition adherence | logged-day kcal/P/C/F sums, per-day target snapshots, coverage, optional fiber |7d; user-request/daily reuse | no completeness marker => describe logged intake only, not compliance judgment |
| Recovery/sleep/activity | sleep/quality, recovery feeling, optional steps/energy/stress/motivation aggregates |7d compared with prior7d, <=28d | fewer than3 observations per window => insufficient trend |
| Weight/measurement progress | sample dates as relative offsets, delta/trend, optional goal-distance direction |28d; user-request/weekly | fewer than2 measurements => no change; never project body fat |
| Weekly check-in | completion counts, nutrition comparisons, recovery and progress summaries + goal enum | local completed7d vs prior7d; once/week on request initially | explicit partial-domain confidence, no reconstructed absent week |
| Motivation/goal progress | member goal enum, own observed completion/progress direction |7/28d; on request or included in weekly | encourage logging without fabricated successes or goals |
| Missing-data/confidence | domain presence, sample counts, freshness and reason enums | same requested window | deterministic local response, no provider needed |
| Serious/unclear health escalation | local current safety gate; any future explicit symptom input needs separate consent | current event, not continuous surveillance | deterministic stop/help copy; NO provider call |

Proposed trend thresholds are quality/product decisions, not clinical rules. Missing optional data never forces a provider call. No analysis result is a new source of health truth. No embeddings, vector database or long-lived provider conversation is needed.

Private-chat boundary: initial 6D manifests categorically exclude 6C. Any later use requires a distinct purpose/category, unselected explicit consent, bounded user-chosen text and new safety/privacy review. Neither trainer-summary consent nor ordinary chat consent grants that use. Withdrawal must invalidate queued and cached analysis contexts.

## 5. Read-Only Output Schema Proposal

Use a versioned 6D schema alongside the frozen 6A response, not an in-place broadening. Proposed shape (documentation only):

```json
{
  "schema_version": "phase6d.analysis.v1",
  "analysis_kind": "daily",
  "status": "partial",
  "summary": "Localized, bounded explanation",
  "observations": [
    {"text": "A descriptive observation", "evidence": ["training_7d"]}
  ],
  "uncertainties": ["nutrition_day_incomplete"],
  "confidence": {"level": "low", "reasons": ["missing_domains"]},
  "suggestions": [
    {"kind": "consider_later_review", "text": "Discuss a change before making one"}
  ],
  "actions": [],
  "safety": {"status": "clear", "message_key": "", "automatic_execution_blocked": true}
}
```

Require exact keys, bounded text/arrays, allowed NL/EN/DE, known evidence references and matching analysis kind. A suggested starting cap: summary800 characters, observations6x240, suggestions3x240, reason enums12, total output <=8KB. Status enum: ready/partial/insufficient_data/hard_stop/review_required. Confidence is computed from source quality server-side; the model cannot raise it. Numeric facts must match deterministic metrics and units, not novel model arithmetic.

Allowed: summarize, explain, compare observed trends, highlight missingness, motivate, suggest considering a later review. Forbidden: new kcal/macro targets, weight/load prescriptions, scheduling/reminders, domain mutations, action/proposal IDs, RPC/function calls, 6F proposals or 6G execution. The browser renders escaped text and no executable controls. `actions` must have maxItems0 in schema AND runtime/database validation. Route capability permits only analysis lifecycle/run writes; domain write privilege is absent.

## 6. Safety And Validation Pipeline

1. Authenticate member, verify age, current entitlement, latest purpose-specific consent and flags. No model choice, source values, role or user authority accepted from browser.
2. Validate exact request shape, timezone/window/event identity, resource ownership, request equality, source availability, freshness and byte/token ceilings.
3. Apply deterministic medical/safety gate before any reservation/provider call. Reuse reviewed 6C concepts/copy without changing its communication behavior. Retained unresolved serious/unclear state denies health/performance analysis and returns local reviewed copy; chat remains independently accessible.
4. If a future explicitly supplied symptom request is approved, severe/current or unclear health signals stop locally. Do not scan all private notes or infer a disease from sleep/weight statistics. Low coverage returns uncertainty, not medical escalation.
5. Serialize allowlisted aggregates as data, isolated from policy instructions. Reject unexpected strings/IDs, invalid units, stale/future timestamps, impossible numbers, unknown enums and oversized payloads.
6. Reserve the maximum affordable cost under shared per-user and global limits. Select exact Luna or explicitly justified Terra; no fallback, no unbounded retry, no hosted tools.
7. After a later legally approved call, validate strict schema, returned model, refusal/incomplete status, evidence IDs, numeric consistency, language and safety. Reject concealed commands, new targets and unsupported causal claims. Never auto-run another model to repair malformed output.
8. Recheck consent/entitlement/feature state and source versions before publishing. Withdrawal or deletion during a run discards content but reconciles actual cost; changed source marks stale instead of rewriting history.
9. Commit validated result + run completion + usage atomically. No domain writes. Failed/uncertain provider outcomes preserve conservative cost accounting and retry identity.

6C classifier tests are deterministic regression evidence, not clinical validation or proof that every natural-language risk will be detected. Reviewed professional-help/no-diagnosis copy remains local and non-generative. New 6D medical thresholds, translations or emergency destinations need owner-qualified medical/legal review. Repeated risk blocks the risky request; it never locks the person out of all communication. Persistent action blocking cannot be cleared by an analysis, conversation deletion or a model output.

Prompt injection in exercise names, meal names, notes, source metadata or model strings cannot become instructions: these fields are excluded or normalized to closed enums. Aggregated member entries remain self-reported, not independently verified truth. No causal diagnosis, eating-disorder classification or automatic progression from correlations.

## 7. Entitlement Matrix

All rows additionally require age18+, separate valid analysis consent, runtime gates and (for any external call) every legal gate.

| State | New provider analysis | Existing own results / local behavior |
| --- | --- | --- |
| Free / missing entitlement | DENIED | proposed bounded read/export/delete grace only; no hidden context bypass |
| Pro alone | DENIED | Pro Nutrition/Progress privileges do not grant AI |
| AI trial | only a current authoritative ai row; no new trial system | same data boundary/budgets; Phase7 owns lifecycle |
| Active AI | eligible, subject to gates/budget | own results only |
| Active personal_coaching | eligible, subject to gates/budget | no trainer chat/results access |
| Inactive / expired / future | DENIED | do not grant by source label or browser package |
| Warning at EUR2.40 | retain allowed route within remaining reservation | internal fair-use feedback, no automatic charge |
| EUR3 included ceiling | Terra denied if reservation would exceed it; Luna-only remaining grace | at most EUR1 grace; not an additional subscription |
| EUR4 hard cap | DENIED | history/export/delete remain possible; no provider retries |
| Consent withdrawn / new purpose not accepted | DENIED immediately, including queued work | export/delete; result retention choice requires approval |
| Trainer-disabled AI | deny applicable analyses only if a future authenticated authoritative disable exists | no existing trainer-disable authority may be invented from browser flags; 6H/9 gate |
| Other valid simultaneous AI/PT source | current authority resolves access without overwriting existing rows | expired row does not cancel a separate current valid source |

Source transitions/trial renewal must not reset spend or permit duplicate event runs. Test that against the shared subscription-period authority before paid 6D activation. Member costs are internal; no payment/invoice flow is introduced.

## 8. Retention, Export And Deletion Recommendation

A transient response alone cannot guarantee refresh/history/exact retry without another paid call. Recommend ONE additive own-user `ai_analysis_results` table, reusing existing manifests/runs/ledger/lifecycle rather than creating a second chat system. It stores only validated minimized result, kind, status, source cutoff/hash/version, event/request identity and expiry. No raw prompt, raw source rows or conversation copy.

Proposed content lifetime: <=90days after creation, also bounded by <=90days after entitlement loss; earlier member delete wins. Raw assembled context stays in memory only and is discarded after validation/completion. Keep minimal non-content idempotency/deletion tombstones and cost/audit metadata for a proposed180days, subject to privacy review and billing-window needs. These are NOT modifications of frozen 6C retention.

RLS: own-user defense-in-depth; no trainer/public access; revoke all base-table privileges from PUBLIC/anon/authenticated, member access through specific auth.uid-bound read/export/delete RPCs. Service-only completion must bind to an already-authorized run; it cannot trust a browser user_id. No RPC for arbitrary member queries or JSON patches.

Deletion is idempotent irreversible content scrub with replay tombstone: late workers cannot recreate deleted content, exact retry returns deleted, and no automatic regeneration. Export includes own result/context provenance labels and dates, not operational IDs/keys or others' data. Consent withdrawal stops assembly/processing immediately; propose leaving bounded read/export/delete access rather than silently deleting all records. Owner must approve content/metadata retention and consent-withdrawal policy. Document backup expiry and restoration scrub rules; do not promise instant deletion from immutable backups.

Do not widen `fmz_phase6c_export_chat/delete_thread`. A dedicated analysis scope composes into a later account lifecycle after review. Chat/analysis deletion never deletes frozen Training/Nutrition/Progress data or clears retained safety authority.

## 9. Provider, Model And Cost Envelopes

No provider call was made. These are conservative planning estimates from the FROZEN 6B price contract, not a new supplier quote: Luna USD0.20 input /0.02 cached /1.20 output per million tokens; Terra USD2.00 /0.20 /12.00. Exact IDs: `gpt-5.6-luna` and `gpt-5.6-terra`. No model substitution or cross-provider fallback.

Use uncached estimates, including policy/schema overhead and all output/reasoning tokens. Formula: ceil USD-micros from token rates, then ceil to EUR-micros at the frozen conservative EUR1.25/USD factor. Taxes/infrastructure are excluded and need separate commercial review. Before activation revalidate price/model/EU/ZDR availability without changing the frozen contract silently.

| Analysis | Proposed model | Input/output cap | EUR maximum per single attempt | Cadence |
| --- | --- | --- | --- | --- |
| Daily | Luna |1500/500|0.001125|once/local day on request |
| Post-workout | Luna |2200/650|0.001525|once/completed event |
| Training trend | Luna |4000/900|0.002350|weekly/request, deduplicate weekly output |
| Nutrition | Luna |2500/700|0.001675|daily/request, reuse same-source result |
| Recovery/activity | Luna |2200/600|0.001450|daily/request, bounded window |
| Body progress | Luna |1800/500|0.001200|weekly/request |
| Weekly routine | Luna |5000/1200|0.003050|once/completed local week |
| Weekly genuinely complex | Terra |5000/1200|0.030500|instead of routine; explicit server criteria, never automatic fallback |
| Motivation | Luna |1200/450|0.000975|include weekly or user-request |
| Missing-data / serious-unclear safety | local deterministic |0/0|0.000000|as needed, no provider |

Example monthly envelope:30 daily +16 workout +4 complex weekly +4 each training/nutrition/recovery/body/motivation = EUR0.21075 at these caps; routine weekly instead = EUR0.10095. This is an illustration, not a promise of usage or permission for automatic daily calls. 6C and future features share the EUR3 included / EUR2.40 warning / EUR1 Luna-only grace / EUR4 cap. Reservations account for concurrent requests and any explicitly bounded retry. Unknown-charge failures retain conservative accounting; no blind release or exploratory repeats.

At1000 users this illustrative analysis-only maximum is EUR210.75/month before tax/infrastructure, with a4,000EUR shared user hard-ceiling upper bound if all1000 reach it. It does not reserve a global commercial allowance. Owner must approve global budget/concurrency/provider spend ceilings separately. Suggested initial 6D cadence is demand-driven, no background scheduler; later approved event/day/week jobs use idempotent checkpointing, timezone spreading and backpressure, never browser polling.

## 10. Feature Flags And Kill Switches

Preserve current live state: 6C mock_chat_enabled=true, external_provider_enabled=false; all6A flags disabled; 6B real-member gate false. Prior 6B evidence records FMZ_PHASE6B_SYNTHETIC_TEST_ENABLED=false; its secret value was not fetched or changed in this audit. DB synthetic configuration is distinct from that Edge environment flag and is not proof of its current value.

Recommend separate default-off6D flags for analysis mock, purpose/kind enablement, external provider, scheduled generation and global kill. No6C flag may turn6D on. Route choice is explicit mock or provider, never fallback. User opt-in cannot override global disable, age, consent, entitlement, safety, budget, trainer restriction or legal block.

Global kill denies new context assembly/reservations/calls; in-flight completions reconcile cost but suppress delivery as required. Own read/export/delete stays possible under lifecycle rules. Provider circuit/timeout/overload returns localized unavailable, not another model. All flags are server-authoritative and fail closed when missing.

Mandatory real-member gate bundle: approved ZDR for exact project/models/endpoints; executed DPA; owner-approved DPIA; verified European route; approved privacy and medical copy; explicit purpose consent; current entitlement; explicit owner real-member activation. Transfer/subprocessor and lifecycle evidence remain required by6B. The current Supabase eu-west-2 location does not prove an OpenAI EU processing route.

Official OpenAI data-controls documentation reviewed 2026-09-04: ZDR requires approval, is endpoint/capability dependent and is distinct from store:false; regional support still needs exact project/model/endpoint evidence. Background processing and hosted tools remain disabled. This is a deployment gate, not a legal-compliance certification. [Official data controls](https://developers.openai.com/api/docs/guides/your-data). Supabase exposure/changelog context: [official changelog](https://supabase.com/changelog).

## 11. Proposed Implementation Impact

No files in this section were created or deployed.

- Database: likely one additive result table plus bounded member-context/read/export/delete and service begin/complete/fail RPCs; event uniqueness and purpose consent/category support. Reuse 6A private run/manifest/budget/lifecycle authority. No domain table changes.
- Context: own-user STABLE SELECT-only RPC; exact field allowlist, active-status joins, local windows, row/byte limits, source cutoff. Use safe search_path and explicit revoked ACL; SECURITY DEFINER only for the necessary denied-table boundary with auth.uid checks.
- Result/run writes: service-only, no trainer path; atomic compare-and-complete, exact replay hash equality, current gate revalidation and deletion tombstones. Shared budget locks in fixed order, expiry/dead-worker handling and cross-feature concurrency tests required.
- Edge: separate bounded6D handler under `youri-ai`, no changes to6C classification/route/appearance. Mock first. 6B adapter primitives reusable after member-policy review; synthetic accounting endpoint not reusable for real data.
- Frontend: future member-mobile-first overview with collapsed evidence/uncertainty, no permanent expanded forms; separate analysis entry/detail without redesigning frozen Vandaag/Trackers/chat. Owner must approve placement. Trainer environment remains desktop-first but no trainer feature belongs here.
- Performance: indexed user/date/status reads, <=28d initial windows, at most10 comparable exercise groups, proposed context16KB and result8KB. Run EXPLAIN in staging with synthetic density, bounded pagination and load tests before accepting these provisional ceilings. No unbounded member scan, N+1 calls, MutationObserver, polling or model-based metric calculation.

## 12. Recommended Implementation Slices

1. **6D-1 Contract lock and local mocks:** owner decisions in section14; JSON/context/evidence contracts, timezone policy, quality thresholds, consent boundary, deterministic safety/missingness tests. No provider call or live writes.
2. **6D-2 Reviewed additive database boundary:** minimal result/lifecycle/event identity + bounded context and service RPCs; SQL review, read-only verifier, synthetic rollback/concurrency tests, separate exact staging GO before execution.
3. **6D-3 Mock-only vertical slice:** server metrics -> mock result -> own overview/detail -> retry/history/export/delete. NL/EN/DE and four viewports. Real-member external route remains structurally off.
4. **6D-4 Full isolation/safety/cost validation:** cross-user/trainer, withdrawal midflight, expiry, source-change, deletion/replay, medical/injection, budgets/timeout and frozen regressions; owner real-phone mock acceptance.
5. **6D-5 Separate provider/legal activation gate:** only after every legal gate and explicit owner authority. Approve strictly synthetic paid acceptance first; any real-member activation is a separate permission. No automatic transition from mock PASS.

Daily/weekly/post-workout scheduling beyond request-time execution needs explicit cadence/global-spend approval. No6E continuous risk monitoring,6F,6G or6H is pulled into these slices.

## 13. Tests And Acceptance Criteria

Audit-time rerun results are in `TEST_MATRIX.md` and the6C freeze evidence. Database E2Es that write then rollback were NOT rerun because this assignment is read-only. Prior accepted12/12 live safety and transactional proofs remain historical evidence, not new tests.

Required before6D technical PASS:
- Schema/ACL: own-user results only; PUBLIC/anon/direct browser writes/trainer reads denied; closed service RPC inventory and no frozen domain writes.
- Sources: exact snapshot totals for canonical/custom/USDA/OFF, null-food isolation, archives/replacements excluded, no ml=g, matching historic targets, sparse/partial days, completed vs open workouts, missing exercise IDs, timezone/DST/day-crossing and future-date boundaries.
- Manifest: reject every unallowlisted field; no names/email/IDs/chat/notes/photos/GPS; owner joins; max rows/bytes/tokens; missing/conflicting/stale sources never invented.
- Output: strict schema, actions always empty, no target/schedule change, evidence-only numbers, model mismatch/refusal/incomplete response safe, injection and HTML escaped.
- Safety: all frozen NL/EN/DE phrases/negation/education/chest-training controls; risky analysis stopped with no provider charge; normal chat still works; no output can resolve persistent action block.
- Access: Free/Pro/trial/AI/PT/inactive/future/expired/withdrawn/under18; simultaneous sources; source changes cannot reset budget or replay identity; trainer sharing denied.
- Concurrency: double tap, two devices, late response, retry after timeout, changed-payload same ID, timezone change, source revision, delete/withdraw/expiry midflight, identical event different request IDs; one authorized result/charge.
- Cost: requested/returned exact model, cached and reasoning usage, warning/reservation/grace/hard cap, cross-feature budget, global kill, unknown-cost conservative outcome; no account billing.
- Retention: export/delete/expiry restoration, backup scrub policy and tombstones; independent analysis lifecycle cannot erase chat/domain history.
- UX:320x700 and390x844 primary;820x1180 and1440x900 compatibility; readable focus/detail/error states; no overflow, duplicate result, layout shift or automatic paid refresh.
- Scale: representative synthetic1000-user load, indexed bounded queries, global backpressure and no surprise fan-out.
- Complete frozen Phase1-5/Member UX/6A/6B/6C matrix, immutable runtime hashes and owner real-phone acceptance.

Verifier limitations: source-string checks prove contracts are present, not every runtime behavior. The legacy request-scoped verifier's `package6d_absent` checks a trainer table, which is not sufficient6D absence proof. This audit separately inspected repo routes/schema scope and enforced a docs/status-verifier-only diff. Its `no_action_rows_added` literal is not a row-count proof; the separate read-only count query confirmed no proposals/decisions. Never relabel those literals as new E2E evidence.

## 14. Exact Owner Decisions Required

Before 6D implementation, approve or amend these recommendations together:

1. Initial categories/placement: demand-driven daily, post-workout and weekly with optional domain details; separate member analysis surface, no frozen Today/Trackers/chat redesign; no automatic scheduler initially.
2. Privacy scope: allowlisted aggregates only; separate analysis-purpose consent with selectable domain categories; NO6C chat context, water/legacy details, trainer messages, photos or free-text harvesting.
3. Calendar/quality: dedicated member-confirmed AI timezone, no silent Nutrition/Progress timezone merge; <=28d windows; minimum trend samples above; incomplete intake explicitly not adherence proof.
4. Storage/lifecycle: one result table, <=90d content, proposed180d minimized metadata/tombstones, withdrawal stops processing while preserving bounded read/export/delete, backup deletion policy.
5. Cost/cadence: token envelopes, exact criteria for Terra weekly complexity, per-kind frequency, global budget/concurrency/unknown-charge policy; shared6B user caps stay unchanged.
6. Safety/authority: approve analysis-specific escalation/missingness copy and unresolved-state behavior, no diagnosis or new prescriptions, no actions/proposals, no automatic trainer sharing.

7. Authorize a separate narrowly scoped legacy identity/ACL security review and remediation gate for the findings in section 2 before 6D relies on those authorities. No profile/linkage/ACL repair is approved by this documentation task.

Separately, before ANY real-member provider activation: owner must supply/approve actual ZDR/DPA/DPIA/EU-route/privacy/medical/transfer/lifecycle evidence and give explicit activation GO. Technical mock readiness is not that approval.

The temporary6C owner entitlement is unchanged: one active AI test row through2026-09-10T23:59:59Z. Its expiry is not automatically extended for6D.

## 15. Explicit Out Of Scope

No6D implementation, migration creation/execution, frontend/Edge deployment, member source writes, consent changes, entitlement changes, OpenAI/provider calls (including synthetic), provider key inspection, real-member activation or production access. No proposals/actions/automatic changes, reminders, continuous risk monitoring, trainer sharing or6H/9 work. No new nutrition/provider import, exercise catalog modification, progress measurement rewrite, legacy cleanup or frozen6C redesign.

This assignment changes documentation and one SELECT-only status verifier only. The verifier preserves the immutable6A installation checker and adapts its six accepted6C columns plus two no-longer-empty lifecycle expectations; it is not a database repair. Rollback is reverting documentation/verifier commits only, never a database rollback.

Conclusion: architecture/readiness audit COMPLETE; implementation NOT STARTED. Await the six owner product/architecture decisions, the separate legacy security gate and a new implementation GO.

## Audit Evidence: Existing Advisor Findings

The project-wide Advisor is NOT all-green. Current security output: 24 INFO `rls_enabled_no_policy`, 1 WARN mutable function search_path, 8 WARN anon SECURITY DEFINER execution, 47 WARN authenticated SECURITY DEFINER execution, and 1 WARN leaked-password protection disabled. Performance: 13 INFO unindexed foreign keys, 45 WARN RLS initplan opportunities and 37 INFO unused indexes. This is a metadata snapshot, not proof of exploitability for every warning.

No-policy private operational tables and intentionally callable authenticated ownership-guarded RPCs are expected patterns; the exact 6A/6B/6C ACL verifiers pass. However the legacy bootstrap and metadata-linking bodies warrant the separate material review described above. Mutable `public.touch_updated_at` and Auth password protection also remain open existing hardening items. No grants, policies, Auth settings or indexes were changed. Production was not inspected.

References: [SECURITY DEFINER exposure](https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable), [mutable search path](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable), [RLS initplan guidance](https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan). These findings supersede any historical blanket claim that the project currently has zero advisor notices.

## Package 6D-0 Closure (2026-09-04)

The legacy authorization blocker identified by the read-only 6D audit is now remediated
on staging under separate owner GO: migration history 20260904105918, invite-client v16,
runtime commit ab9b3f186898522ae91dba230e8df0adf1f9d895. Own-user bootstrap, server-issued
email-bound one-use invitations, protected profile fields and own-client workspace RPCs
replace editable metadata and broad member workspace access. Existing relationships and
data are unchanged; live verifier 40/40, rollback E2E 48/48 and concurrency 8/8 PASS.
See [the security receipt](PHASE6D0_LEGACY_AUTHORIZATION_SECURITY.md).
This closes that security prerequisite only. Package 6D analysis implementation and real
member external AI remain unapproved; existing 6D product/privacy decisions are unchanged.
