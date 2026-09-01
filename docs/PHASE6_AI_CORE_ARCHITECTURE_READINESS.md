# Phase 6 Youri AI Core - Architecture And Readiness

Status: ARCHITECTURE / READINESS AUDIT COMPLETE; PACKAGE 6A IMPLEMENTATION IN PROGRESS

Audit date: 2026-09-01
Target repository: `Yourizorge/fitmetzorge-staging` / `main`
Target Supabase: `mokxyyullfhkfalopbzd`
Production: FORBIDDEN

## 1. Audit Result

Phase 6 is ready for owner architecture decisions, but not yet ready for provider activation or feature implementation. The repository contains no AI runtime, no AI provider dependency, no AI secret, no AI tables, and no member chat implementation. Read-only staging metadata confirms that the frozen Identity, Recovery, Training, Nutrition, and Progress sources exist with RLS while the directional AI tables from the Master Plan do not yet exist.

The correct direction is a provider-neutral, backend-mediated Youri AI service. The browser may submit a member request and render validated results, but it may never hold provider credentials, author nutrition/training authority, choose its own entitlement, or directly execute an AI-proposed domain mutation.

## 2. Existing AI Architecture In The Repository

Existing and reusable:

- Supabase Auth and member JWT flow.
- RLS-first normalized member domains.
- Phase 1 time-bounded `entitlements` source of truth.
- A proven Edge Function deployment pattern in `nutrition-provider`, including strict CORS, JWT verification, secrets, bounded requests, deterministic tests, rate limits, circuit state, service-only operations, and safe logging.
- Feature-flag direction through `ai_coach_enabled`.
- Youri-avatar placeholders in Training without an invented final face or runtime AI media generation.
- Master Plan rules for backend mediation, structured validation, proposals, trainer priority, safety, cost control, and no browser AI call.

Not present:

- No `youri-ai` Edge Function or provider adapter.
- No `ai_threads`, `ai_messages`, recommendations, actions, usage ledger, safety event, scheduler checkpoint, or trainer-signal storage.
- No AI consent, retention, export, deletion, or trainer-summary sharing contract.
- No prompt policy, schema versioning, model policy, provider key, paid API account, or approved cost envelope.
- No live AI UI. Current Youri references are entitlement labels or avatar/media placeholders only.

## 3. Frozen Authoritative Inputs

AI context must be assembled server-side from the minimum facts needed for the current feature. It may not accept browser-supplied summaries as authority.

| Domain | Frozen source | Allowed Phase 6 use | Limits |
| --- | --- | --- | --- |
| Identity | `profiles` | authenticated user, client role, linked-trainer state | never send email, auth UUID, or legacy client identifiers to a provider |
| Preferences | `user_settings` | language, country/region when relevant, metric/imperial presentation | canonical domain units remain unchanged |
| Onboarding | `user_onboarding` | age, height, starting/current context, goal, experience, available days and constraints when relevant | minimize fields per feature; onboarding values may be stale |
| Entitlements | `entitlements` | server-side AI access decision | status and time window are mandatory; browser package state is not authority |
| Recovery | `recovery_logs` | sleep hours/quality, steps, wellbeing dimensions, recovery feeling and training-load status | manual/basic data only; no Health or wearable claim |
| Training plan | `training_plans`, `training_plan_days`, `training_plan_exercises` | current member-authored plan context and proposed plan changes | no trainer access expansion; active/archive state respected |
| Training history | `workout_sessions`, `workout_set_logs` | completed workouts, performance, workload and post-workout summaries | immutable snapshots remain historical authority |
| Nutrition | `nutrition_targets`, `food_logs`, `food_log_items` | target and authoritative daily/weekly aggregate context | prefer aggregates; no browser nutrients; immutable snapshots remain authority |
| Progress | `progress_goals`, `weight_logs`, `body_measurements`, Phase 5 dashboard calculations | goal, raw values, trend and descriptive cross-domain progress | no photo data; no body-fat or diagnostic inference |
| Private chat | future `ai_threads` and `ai_messages` | member's own bounded conversation context | absent today; must never be trainer-readable |

Unavailable or insufficient inputs must remain explicit: no authoritative running activities, no Health sync, no progress photos, no validated injury/medical record, and no normalized trainer-client consent relationship. The model must never fill those gaps with invented facts.

## 4. Missing Data Contracts And Gaps

Blocking gaps before live AI calls:

- Explicit AI data-use consent and withdrawal behavior.
- Chat retention, member deletion, account deletion, export, and legal-hold rules.
- AI provider/model selection, DPA/subprocessor and international-transfer review.
- Hard per-user, per-feature, daily and monthly cost budgets.
- Reviewed medical/injury/eating-disorder crisis and escalation policy with localized copy.
- Prompt/model/structured-output version policy and model deprecation process.
- Private AI storage schema, RLS, ACL, service-only operational state, and read APIs.
- Exact trainer-summary consent and active-link revocation contract.
- Event identity for daily, weekly, post-workout, and deviation-triggered analyses.
- Domain-specific action allowlists, stale guards, approval rules, and rollback behavior.
- Reviewed NL/EN/DE AI and safety copy; FR/IT are not yet implemented product languages.

Deferred gaps that do not block the first non-provider foundation:

- Final Youri avatar asset.
- Health/wearable and authoritative running context.
- Progress-photo analysis, which remains behind its own privacy and consent gate.
- Push notifications and frequency caps, which remain Phase 8.
- Normalized trainer workflows and Copilot, which remain Phases 9 and 10.

## 5. Target Server Boundary

Use one dedicated `youri-ai` Edge Function with a provider-neutral internal adapter. Do not extend `nutrition-provider`; its provider, licence, rate, and trust contract is a separate frozen domain.

Required request flow:

1. Browser sends the member JWT, request UUID, feature code, language, thread ID where relevant, and bounded user text.
2. Edge gateway and function validate JWT, origin, method, content type, body size, IDs, and feature allowlist.
3. A member-scoped Supabase client forwards the JWT to an authenticated context RPC. That RPC derives `auth.uid()` and reads only authorized own-user context.
4. Server resolves current AI entitlement and consent. No valid entitlement or consent means no paid provider call.
5. Server applies rate, budget, replay, safety, and context-freshness gates.
6. Server serializes context as untrusted data under an immutable policy prompt; it does not concatenate notes into system instructions.
7. The selected adapter calls one approved provider with a pinned model-policy version and strict structured-output schema.
8. Server validates schema, ranges, allowed action types, safety outcome, language and evidence references.
9. Server persists the member message/result, usage metadata and any proposal atomically or marks the run failed without a partial assistant message.
10. Browser receives a bounded, escaped response. It never receives a provider key, internal prompt, trainer-only signal or service credential.

Provider-hosted conversation state is not the source of truth. FitMetZorge owns the thread history and sends only a bounded recent window plus a separately versioned conversation summary if later approved.

## 6. Directional Data Model

Exact SQL remains a separately reviewed Package 6A artifact. The minimum directional responsibilities are:

- `ai_member_settings`: own-user consent state, language and enabled analysis categories; entitlement is not stored here.
- `ai_threads`: private member thread identity, feature kind, status and archive state.
- `ai_messages`: immutable user/assistant message records with structured response version and safe status; no trainer policy.
- `ai_recommendations`: read-only member insights such as daily, weekly and post-workout summaries with evidence references and expiry.
- `ai_action_proposals`: typed proposed domain changes, expected source versions, reason, safety class, status and expiry.
- `ai_action_decisions`: append-only member/trainer/system decisions for approve, reject, expire, supersede and execution result.
- `ai_runs`: service-only request identity, feature, policy/model versions, context hash/manifest, status, latency, token counts, estimated/actual cost and safe error class; no raw prompt in operational logs.
- `ai_usage_daily`: service-only per-user/feature/model counters and reserved/actual budget.
- `ai_rate_buckets`: service-only atomic request/token/cost ceilings.
- `ai_context_checkpoints`: service-only idempotency keys for local day, ISO week and source events.
- `ai_safety_events`: service-only minimized category/outcome records without unnecessary conversation content.

Trainer summaries/signals must use a future separate `ai_trainer_signals` contract. It may contain only an approved minimized summary, severity, evidence references and change explanation. It must never expose or join through to full `ai_messages` content. No trainer ACL belongs in the initial member AI slice.

All public AI tables must have RLS and no direct browser write privileges. Member reads and user-message submission should use narrow RPCs. Operational tables should live in a non-exposed private schema or remain reachable only through fixed-search-path service-only functions. `PUBLIC` and `anon` receive nothing. `authenticated` receives only exact reviewed RPC execution.

## 7. Prompt Injection And Untrusted Content

Treat all member text, workout notes, recovery notes, Nutrition notes, custom food names, imported provider labels and future trainer text as untrusted data.

Controls:

- Immutable server policy and feature instructions are separate from user/context payloads.
- Structured context envelopes include source type, source timestamp, units and confidence/availability; text fields are length-bounded and control characters normalized.
- User text cannot select a model, feature entitlement, SQL, RPC, tool, recipient, trainer, or action type.
- No arbitrary URL fetch, web browsing, code execution, dynamic SQL, dynamic RPC name, or provider tool use in the initial Phase 6 contract.
- Output uses an allowlisted JSON schema and is parsed/validated before storage or rendering.
- Rendered member text is escaped; provider HTML/Markdown is not trusted as executable content.
- The model cannot write domain tables. It can only emit a typed proposal that server validation may reject.
- Adversarial fixtures cover instruction override, data exfiltration, cross-user prompts, hidden markup, oversized notes, fabricated authority and requests to ignore safety rules.

## 8. Private Chat And Trainer Separation

Private member chat is always private from trainers, including PT-linked accounts. Neither legacy `coach_workspaces.state`, `profiles.trainer_id`, nor a future trainer role may create a chat-read path.

A linked trainer may eventually receive only separately generated, minimized and consented summaries/signals with a documented purpose. Revoking the trainer link or sharing consent must remove trainer access immediately without deleting member-owned chat/history. Phase 6 may tag that a member is linked for authority decisions, but normalized trainer read access remains blocked until the later linked-client contract exists.

Trainer override means:

- Chat may explain and support, but may not silently override a trainer-authored active plan or strategic target.
- For a linked PT client, meaningful training, calorie, macro or phase changes remain proposal-only until a reviewed trainer approval path exists.
- A future trainer decision supersedes a pending AI proposal with an append-only decision record; it never rewrites the private chat.

## 9. Auditability And Explainability

Every AI output that influences behavior must record:

- request/run UUID and idempotency identity;
- feature code and trigger source;
- policy, prompt, schema, adapter and model versions;
- source-domain manifest, source timestamps and context hash;
- structured safety category and result;
- token counts, latency, provider request ID where safe, and cost estimate/actual cost;
- evidence references used in the member-facing explanation;
- proposal, decision and execution status where applicable.

Operational logs exclude raw chat, raw prompts, email, auth JWT, provider secrets and unnecessary health/fitness values. Member-facing explanations distinguish observed facts, interpretation, uncertainty and recommendation. Unsupported causality is forbidden.

## 10. Idempotency, Stale Data, Conflict And Rollback

- Every request has a stable UUID unique per user and feature.
- Exact replay returns the prior result without a second provider charge; changed-payload reuse is rejected.
- Per-user/request advisory locks or equivalent atomic state prevent concurrent duplicate runs.
- Daily key: `user_id + local_date + feature + policy_version`.
- Weekly key: `user_id + ISO week in member timezone + feature + policy_version`.
- Post-workout key: completed `workout_session_id + feature + policy_version`.
- Proposals carry expected source IDs and `updated_at`/revision values. Execution fails stale rather than overwriting newer member or trainer state.
- A failed provider call never creates a successful assistant message or action. Reserved budget is reconciled to actual usage or released.
- Domain changes reuse the existing authoritative RPC/revision/archive model. No direct AI table-to-domain table write is allowed.
- First releases are recommendation/proposal only. Rollback means disable feature/provider, preserve private history, expire pending proposals and leave frozen domain data unchanged.

## 11. Safety And Medical Hard Stops

Youri may provide general fitness and lifestyle information, explain data and encourage appropriate professional help. It may not diagnose, claim certainty about injury/illness/body fat, prescribe medical treatment, or continue automatic progression through serious or unclear warning signals.

The runtime needs deterministic pre-model and post-model safety gates. A flagged serious or unclear situation must:

- stop automatic progression and action execution;
- avoid increasing training load or intensifying calorie restriction;
- provide reviewed, localized escalation copy appropriate to urgency;
- record only a minimized safety category/outcome;
- require explicit later review before resuming an automatic path.

The exact red-flag taxonomy, emergency wording, age/pregnancy/eating-disorder handling, calorie bounds and escalation destinations require medical/legal owner review before provider activation. The conservative default is no automatic change.

## 12. Entitlements And The 30-Day Trial

AI generation access is granted only by a current time-valid `ai` or `personal_coaching` entitlement:

- `status = 'active'`;
- `starts_at <= now()`;
- `ends_at IS NULL OR ends_at > now()`.

`free` and `pro` alone never authorize a paid AI call. Missing, future, inactive or expired rows deny generation. Browser package state and metadata never grant access.

The live entitlement primary key `(user_id, entitlement_code, source)` supports a future 30-day trial as an `ai` row with a distinct trial source while preserving paid or coaching sources. Phase 6 consumes this generic contract; Phase 7 remains responsible for trial creation, one-trial abuse prevention, reminder timing, expiry and subscription lifecycle. At expiry, new AI calls stop and data is retained. Whether expired members may still read old chat while generation is locked is an owner privacy/product decision.

Tier behavior:

- Free: AI entry may be visible and locked; zero paid AI calls.
- Pro: no AI calls without an independent current AI entitlement.
- AI Coach or active AI trial: member chat and approved AI features within budgets.
- Active Personal Coaching: AI included, with linked-trainer strategic authority rules.

## 13. Provider Architecture And Options

Use one internal adapter contract and one primary provider at launch. Do not automatically fail over member health/fitness context to another provider unless that second provider has its own owner, legal, privacy and cost approval.

Adapter responsibilities:

- model-policy lookup by server feature code;
- strict timeout and bounded retry policy;
- structured JSON response;
- token/usage parsing;
- safe provider error mapping;
- `store=false` or equivalent where supported;
- no provider-hosted conversation authority;
- deterministic mock adapter for tests with zero external call.

Current official options to evaluate, not approvals:

- OpenAI API: structured server API with token pricing; API content is not used for training by default, while default abuse-monitoring retention and endpoint-specific application-state rules still require review. ZDR/modified monitoring require eligibility/approval.
- Anthropic Claude API: token pricing and a Messages API; ZDR and HIPAA-ready arrangements are documented but feature/model eligibility and exceptions require contract review.
- Google Gemini API: token pricing, paid-tier context caching/batch options and paid-tier no-training statements; project quotas, data handling and regional/legal terms require review.

Official sources reviewed on 2026-09-01:

- `https://developers.openai.com/api/docs/pricing`
- `https://developers.openai.com/api/docs/guides/your-data`
- `https://platform.claude.com/docs/en/about-claude/pricing`
- `https://platform.claude.com/docs/en/manage-claude/api-and-data-retention`
- `https://ai.google.dev/gemini-api/docs/pricing`
- `https://supabase.com/docs/guides/functions`

No provider is selected by this audit.

## 14. Cost, Rate And Abuse Model

The owner must approve a hard budget before any paid key is configured. Monthly cost must be estimated from:

- eligible AI/PT/trial users;
- chats per active user per day;
- daily analyses, weekly check-ins and post-workout summaries per user;
- average input, cached input and output tokens by feature;
- context size and conversation-summary frequency;
- safety/validation second-pass rate;
- retry, timeout and provider-error rate;
- model mix and future model price changes;
- currency conversion, tax, minimum spend/support and infrastructure overhead;
- Edge invocations, database writes, storage, monitoring and export/deletion work.

Required controls are per-user request/token/cost ceilings, per-feature ceilings, rolling short windows, daily/monthly account budgets, global circuit breaker, provider timeout, bounded retries, concurrency cap, exact replay suppression and owner-visible spend reporting. Budget reservation occurs before the provider call and reconciles against returned usage. No entitlement means EUR 0 provider spend.

## 15. Privacy, Internationalization And Scale

Privacy requirements before live processing:

- explicit purpose and legal basis for fitness/health-adjacent AI processing;
- separate consent where required, with withdrawal and generation lock;
- processor/DPA, subprocessors, retention and international-transfer assessment;
- DPIA determination and breach/incident process;
- member export/deletion covering messages, recommendations, proposals and settings;
- no raw private data in operational logs or analytics;
- pseudonymous provider request identity, never email or auth UUID;
- minimum context by feature and bounded retention.

NL/EN/DE are the current product languages. Prompt templates, structured enums, UI, safety copy and escalation text must be versioned per locale. FR/IT must be supported by the architecture but cannot be marked ready until the application, legal copy and safety content are reviewed in those languages. Model-generated translation cannot substitute for reviewed safety copy.

For 1,000+ registered/active users, use bounded context queries, aggregate views/RPCs, indexed event identities, short synchronous Edge calls for chat, queues/background workers for scheduled analyses, no N+1 member history hydration, no polling, and a global budget/circuit breaker. Scheduled workloads must spread by member timezone and never fan out unbounded function-to-function calls.

## 16. Exact Phase 6 Package Sequence

1. **6A - AI Trust Boundary And Contract Foundation, no paid provider.** Reviewed AI storage/RLS/ACL/RPC migration, consent/retention contract, provider-neutral TypeScript interfaces, strict JSON schemas, deterministic mock adapter, context-manifest fixtures, replay/rate/budget/safety state, feature flag off.
2. **6B - Provider, Privacy And Cost Gate.** Owner chooses provider/model policy and budgets; DPA/retention/transfer/safety review; secrets configured only after approval; controlled staging call with no member UI.
3. **6C - Private Youri Chat MVP.** Mobile-first member chat, own private history, entitlement/consent gate, bounded context, NL/EN/DE, streaming only if it preserves replay and cost accounting.
4. **6D - Read-Only Coaching Summaries.** Post-workout summary, daily combined analysis and fixed weekly check-in with timezone/event idempotency; no domain mutations.
5. **6E - Deviation, Risk And Safety Signals.** Evidence-backed member alerts, hard stops, uncertainty and reviewed escalation; notification delivery remains Phase 8.
6. **6F - Proposal And Decision Engine.** Typed explainable proposals, member decisions, stale/conflict/expiry and audit log; no automatic execution.
7. **6G - Bounded Action Execution.** Separately approved domain allowlists using existing authoritative RPCs and revision checks. Linked PT strategic actions remain blocked or trainer-approved until the later trainer contract exists.
8. **6H - Trainer Summary Separation Readiness.** Minimized signal contract and immediate revocation behavior without private-chat access; actual Trainer Environment/Copilot surfaces remain Phases 9/10.
9. **6I - Final E2E, Security, Cost And Owner Acceptance.** Cross-user/trainer isolation, injection/safety red-team, entitlement/trial boundaries, budgets, rollback, mobile UX, frozen regressions and owner freeze.

This sequence stays inside Phase 6 and does not pull subscriptions/payment growth from Phase 7, Trainer Environment from Phase 9, or Copilot from Phase 10 forward.

## 17. Exact First Build Package Without Paid Provider

Package 6A is the next build package after owner decisions. It must not configure a provider key or make an external AI call.

Expected deliverables:

- locked consent, retention/export/deletion and expired-entitlement history behavior;
- reviewed additive migration and read-only verifier for the minimum AI tables and private operational state;
- zero direct base-table browser writes and no trainer policy;
- authenticated user-message/history RPCs deriving `auth.uid()`;
- service-only assistant/run/rate/budget/safety functions with safe search paths;
- read-only own-user context RPC returning a typed minimized context envelope plus freshness manifest;
- provider-neutral adapter and response schemas;
- deterministic local mock adapter and adversarial fixtures;
- stable request IDs, exact replay, stale/error state and no partial-message semantics;
- `ai_coach_enabled = false` and no live member entry that appears operational;
- frozen Phase 1-5 and Member UX regression gates.

## 18. Owner Decisions Required

Blocking before Package 6A migration review:

1. AI chat retention, deletion, export and post-expiry read behavior.
2. Exact AI consent categories and withdrawal effect.
3. Whether member messages may be stored until user deletion or require a fixed retention window.

Blocking before Package 6B paid provider activation:

4. Primary provider/model policy and whether any fallback provider is allowed.
5. Per-user, per-feature and global monthly budgets/rate ceilings.
6. Legal/AVG/DPA, subprocessor, retention, international-transfer and DPIA outcome.
7. Reviewed medical/injury/eating-disorder hard-stop and escalation policy.

Blocking before action execution or trainer sharing:

8. Which changes may ever auto-execute versus always require member approval.
9. Which linked-client changes require trainer approval and how trainer authority/revocation is proven.
10. Exactly which minimized summaries/signals may be shared with a trainer and under what consent.

Later asset/content gates:

11. Definitive Youri avatar asset.
12. Reviewed FR/IT AI and safety content before those markets are enabled.

## 19. Test And Exit Gate

Phase 6 cannot exit until all applicable packages pass:

- auth, entitlement, consent and expired/future/inactive denial;
- cross-user and cross-trainer isolation;
- private chat never trainer-readable;
- no browser provider key, model selection, nutrient/training authority or service role;
- prompt-injection and output-schema adversarial suite;
- missing/stale/conflicting data honesty;
- exact replay without duplicate cost or messages;
- per-user/global rate and budget enforcement under concurrency;
- safety hard stops and no diagnosis;
- proposal/decision/execution audit and rollback;
- NL/EN/DE mobile-first UX; FR/IT only when separately reviewed;
- performance and scheduled-workload backpressure;
- Phase 1/2/3, Member UX, Phase 4 Nutrition and Phase 5 Progress frozen regressions;
- owner real-phone acceptance and explicit freeze.

## 20. Audit Verification And Preservation

- Repository scan: no AI provider/runtime implementation found.
- Read-only staging metadata: all audited frozen source tables exist with RLS; all five directional AI tables checked are absent.
- Live entitlement contract: `(user_id, entitlement_code, source)` primary key; codes `free|pro|ai|personal_coaching`; active/inactive/expired status and start/end window available.
- Supabase current Edge/Auth documentation and relevant 2026 changelog items reviewed; no audit blocker found. Implementation must use explicit grants/RLS because automatic Data API exposure behavior has changed, and must test against the current Deno runtime.
- Database changed: NO.
- Runtime changed: NO.
- Provider called or activated: NO.
- Production touched: NO.

Rollback for this audit is documentation-only: revert the audit documentation commit. No persistent application state changed.

## 21. Owner Decisions And Package 6A Start

On 2026-09-01 the owner approved the Package 6A contracts and autonomous staging execution. OpenAI is the future primary provider; `GPT-5.6 Luna` and `GPT-5.6 Terra` are routing-policy labels only. No key, model ID or paid call is active. Consent, withdrawal, 90-day post-entitlement raw-chat retention, separate trainer-summary permission, EUR 3 included plus EUR 1 grace budget, action bounds and medical/risk hard stops are locked in `docs/PHASE6A_AI_TRUST_FOUNDATION.md`.

Package 6A does not resolve or bypass the Package 6B provider privacy/legal gate. OpenAI activation, DPA/international-transfer/DPIA completion, final medical/legal copy and controlled paid-call acceptance remain separate work.
