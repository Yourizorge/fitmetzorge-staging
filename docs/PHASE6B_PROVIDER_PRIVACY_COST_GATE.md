# Phase 6B Provider, Privacy And Cost Gate

Status: PAID SYNTHETIC TEST BLOCKED BY OPENAI API AUTHENTICATION

Date: 2026-09-01
Repository: `Yourizorge/fitmetzorge-staging` / `main`
Supabase: `mokxyyullfhkfalopbzd`
Production: FORBIDDEN

## Scope

Package 6B proves a server-only OpenAI Responses API boundary with deterministic synthetic fixtures, strict structured output, minimized payloads, explicit cost reservation and fail-closed legal/privacy configuration. It does not expose member AI chat, send member data, execute AI actions, start Package 6C, or alter frozen domain authority.

## Official Provider Contract

Official OpenAI documentation was checked on 2026-09-01. The exact routes are `gpt-5.6-luna` and `gpt-5.6-terra`; both support Responses and structured outputs. No model substitution or cross-provider fallback is allowed.

| Route | Exact model | Synthetic purpose | Input USD / 1M | Cached input USD / 1M | Output USD / 1M |
| --- | --- | --- | ---: | ---: | ---: |
| Luna | `gpt-5.6-luna` | connectivity and normal structured contract | 0.20 | 0.02 | 1.20 |
| Terra | `gpt-5.6-terra` | approved complex structured contract | 2.00 | 0.20 | 12.00 |

Sources: `https://developers.openai.com/api/docs/models/gpt-5.6-luna`, `https://developers.openai.com/api/docs/models/gpt-5.6-terra`, `https://developers.openai.com/api/reference/cli/resources/responses/methods/create`, and `https://developers.openai.com/api/docs/guides/your-data`.

## Architecture

The browser has no OpenAI route or credential. The existing JWT-verified `youri-ai` Edge Function keeps the frozen 6A member mock path and adds two service-only operational paths: `/phase6b/status` and `/phase6b/synthetic-test`. A browser `Origin` is denied and the caller must present a server secret already held by the Edge environment. The caller can supply only a UUID request ID and one locked fixture code; it cannot supply a prompt, member context, model, endpoint, tools or output schema.

The Edge adapter sends only the locked synthetic object through `https://api.openai.com/v1/responses`. Every request has `store: false`, `background: false`, `tools: []`, `tool_choice: none`, a fixed pseudonymous synthetic safety identifier and a strict JSON schema. Timeout is at most 20 seconds and attempts are at most two. Provider errors are reduced to allowlisted safe codes; provider response bodies, credentials and raw prompts are not logged.

## Database Boundary

Migration: `supabase/migrations/20260901230000_phase6b_provider_privacy_cost_gate.sql`.

Private tables:

1. `provider_configurations` - provider, execution mode and owner/legal/privacy gates.
2. `provider_models` - exact model IDs, support, prices and test limits.
3. `provider_payload_fields` - field-by-field synthetic payload allowlist and purpose.
4. `provider_test_budget` - one locked EUR 5 / six-attempt staging budget.
5. `provider_test_runs` - request identity, hashes, safe status, usage and cost only.

All five are in non-exposed `ai_private`, have RLS with no browser policy, and revoke base-table access from `PUBLIC`, `anon` and `authenticated`. Four fixed-search-path `SECURITY DEFINER` service RPCs are executable only by `service_role`; two pure helpers are invoker functions. There is no authenticated/member 6B RPC.

## Privacy And Real-Member Gate

Real-member processing remains impossible in 6B. The Edge exposes no member provider route and the database gate always reports `allowed=false`. A database constraint also prevents `real_member_processing_enabled=true` unless all of these states are complete: ZDR verified, owner-executed DPA complete, DPIA complete, exact EU route verified, privacy notice approved, consent copy approved, transfer assessment complete, lifecycle verification complete, later owner activation true, and endpoint exactly `https://eu.api.openai.com/v1/responses`.

`store: false` is mandatory but is not evidence of ZDR. OpenAI documents default abuse-monitoring retention of up to 30 days and requires prior approval/configuration for Zero Data Retention. The exact project-level ZDR and Europe data-control state must be evidenced before any member data is eligible.

Current gates:

- DPA: INCOMPLETE - owner must execute.
- DPIA: INCOMPLETE - draft only.
- EU route: UNVERIFIED.
- ZDR: UNVERIFIED.
- Privacy notice and AI-consent copy: DRAFT.
- Transfer/subprocessor assessment: INCOMPLETE.
- Lifecycle verification: INCOMPLETE.
- Later real-member owner activation: FALSE.

## Synthetic Fixtures And Payload

`luna_connectivity_v1` and `terra_structured_v1` contain only fixed synthetic aggregates. The exact allowed fields are documented in `docs/privacy/PHASE6B_DATA_FLOW_INVENTORY.md` and enforced in TypeScript and SQL. No internal user UUID, name, email, phone, address, member history, injury, medication, trainer note or private chat is accepted.

## Cost And Retry Contract

The single staging test budget is EUR 5, converted conservatively at EUR 1.25 per USD for accounting, with at most six external attempts. The maximum route cost is reserved atomically before a call using per-request and global advisory locks. Exact replay never reserves twice. Completion reconciles returned input, cached-input and output tokens. If an attempted provider call has unknown cost, the full reservation is consumed. Application code cannot recharge an account.

The member subscription budget from frozen 6A remains separate: EUR 3 included, EUR 2.40 warning, Luna-only EUR 1 grace, EUR 4 hard cap and Terra denied before grace. No 6B synthetic route can alter that policy.

## Secret Method

`OPENAI_API_KEY` and `FMZ_PHASE6B_SYNTHETIC_TEST_ENABLED` are server-only Supabase Edge secrets. They are never placed in chat, GitHub, frontend files, SQL or logs. Missing credentials or a missing explicit test flag fails before reservation or provider access. Synthetic calls require a staging OpenAI account with billing/model access; no credential is generated or accepted by Codex.

## Evidence Artifacts

- Read-only verifier: `supabase/verification/20260901230000_phase6b_provider_privacy_cost_gate_verification.sql`.
- Rollback E2E: `supabase/tests/20260901230000_phase6b_provider_privacy_cost_gate_transactional_e2e.sql`.
- Provider tests: `supabase/functions/youri-ai/phase6b-provider.test.ts`.
- Static/security suite: `assets/phase6b-static-check.js`.
- Medical copy drafts: `docs/PHASE6B_MEDICAL_SAFETY_COPY.md`.
- Privacy/legal working documents: `docs/privacy/PHASE6B_*.md`.

## Staging Execution Result

- Migration SHA-256: `6B432DA3AA389920D5A8EEA4F15F74D35E2A9E2D6F7BF44C7B0FBF62473CC526`.
- Live migration history: `20260902045834_phase6b_provider_privacy_cost_gate`.
- Corrected read-only verifier SHA-256: `761AE2F7A1F411A100862CE3254381A7AEB9C94727220674439F29E3869A8489`.
- Verifier result after the controlled retry: `overall_pass=true`, 36 PASS, 0 FAIL, two metadata-only test runs.
- Transactional E2E SHA-256: `B71A7D96C4BCB776A0175CA72E81C6E2EB0D3614C15E8A7A116816915C22ED40`.
- E2E result: PASS against the non-empty live ledger with rollback, zero persisted fixtures, zero provider calls and EUR 0 additional provider cost.
- `youri-ai`: final version 23, ACTIVE, JWT verification enabled, bundle SHA-256 `ae1f6dc8c102b1c55effe8c42bc38fec8e3917c7330052344c0b104cd82f40df`.
- Live bundle: all eight runtime files match the reviewed local files after newline normalization.
- Unauthenticated `/phase6b/status`: HTTP 401.
- Provider-adapter tests: 23/23 PASS. Phase 6A mock/Edge tests: 11/11 PASS.
- Package 6A static: 93/93 PASS. Package 6B static: 95/95 PASS.
- Current frozen gates: Phase 4F-D 100/100, Phase 4F-E 45/45, Nutrition browser 138/138, Phase 5 static 116/116 and Phase 5 browser 53/53 PASS.
- Security advisors: no new actionable 6B warning; intentional private RLS/no-policy INFO only. Performance advisors: expected low-use/unused-index INFO with two controlled ledger rows.

The real-member gate reports denied with ZDR unverified, DPA/DPIA incomplete, EU route unverified, draft copy, incomplete transfer/lifecycle checks and owner activation false.

## Paid Synthetic Acceptance Attempt

On 2026-09-02 the required Edge secret names were confirmed from the staging dashboard without retrieving their values. The original locked `luna_connectivity_v1` request and one owner-authorized retry after key replacement were sent through the Responses API using exactly `gpt-5.6-luna`. Each request was built only from the nine allowlisted deterministic synthetic fields with `store:false`, `background:false`, `tools:[]`, `tool_choice:none`, strict structured output and no fallback. OpenAI rejected both attempts with the sanitized error `provider_authentication_failed` before any response/model identity or token usage was returned. No Terra request was made.

Both failed runs are recorded as metadata only: two provider attempts, requested model `gpt-5.6-luna`, input/cached/output token counts not returned (`NULL`), no response hashes, no raw request or response columns, and a conservative full-reservation charge of EUR 0.003585 per attempt because provider usage was unknown. The global budget now has two completed attempts, zero reservations, EUR 0.007170 consumed and EUR 4.992830 remaining under the owner-approved EUR 5 cap.

`FMZ_PHASE6B_SYNTHETIC_TEST_ENABLED` was replaced with `false` after the retry failed. A subsequent controlled request returned HTTP 503 `synthetic_test_environment_disabled` before reservation or provider access and did not create a third run.

## Authentication Root-Cause Diagnostic

On 2026-09-02 one non-generative model-read probe ran from the same staging Edge runtime and reused the adapter's normalized credential and exact Authorization-header builder. It called the official global endpoint category `GET /v1/models/gpt-5.6-luna`; no prompt, Responses generation, tools, member data or generation-ledger reservation was used. OpenAI returned HTTP `401`, `error.type=invalid_request_error` and `error.code=invalid_api_key`. External diagnostic cost: EUR 0.00.

Credential inspection returned booleans only: the environment value exists and is non-empty after one trim; leading/trailing whitespace, quote characters, newline characters and an embedded `Bearer` prefix are absent; current project-key format compatibility is false. The outbound request uses `api.openai.com`, exactly one `Authorization: Bearer <trimmed-key>` header, and no organization, project, forwarded or proxy headers. The live bundle does not use `eu.api.openai.com` for this unverified synthetic path. No key value, fragment, length, fingerprint, request body, full provider body or response header was stored or reported.

The previous two `provider_authentication_failed` mappings are therefore resolved to a credential condition rather than an adapter endpoint/header defect. The two existing internal safety charges remain EUR 0.003585 each and are deliberately separate from actual OpenAI billing evidence. The free probe created no third test row: live ledger remains two failed Luna rows, zero Terra rows, zero tokens, zero provider request/response hashes, zero open reservations and EUR 0.007170 internal budget consumption.

The adapter now preserves only safe upstream status/type/code/classification, distinguishes 401 authentication from 403 permission, 404 resource/model and 429 quota/rate conditions, and has regression coverage for the zero-cost probe and exact header contract. The old Phase 6A verifier was also scoped to its frozen 6A function inventory after additive 6B functions caused three verifier-only false failures; corrected live result is 47/47 PASS, with no database change. Edge version 23 is ACTIVE with JWT verification enabled; all eight live files are source-identical to the repository runtime and the deployed bundle SHA-256 is `ae1f6dc8c102b1c55effe8c42bc38fec8e3917c7330052344c0b104cd82f40df`.

## Exact Account Blocker

The replacement staging `OPENAI_API_KEY` is conclusively rejected by OpenAI with `invalid_api_key` and does not match the expected current project-key format class. The exact owner action is to create or select an active API project key in the intended billed OpenAI API project, copy the complete key value directly into the staging Edge secret, and leave the synthetic-test flag false until a separately authorized controlled retry. The value must never be shared in chat or committed. The exact Luna/Terra model-access gate remains untested because authentication fails first. No automatic retry or model substitution is permitted.

Package 6B is not owner-accepted or frozen. Package 6C and member AI chat remain unstarted.
