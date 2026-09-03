# Package 6C Private AI Chat

Status: TECHNICAL PASS / READY FOR OWNER TESTING / NOT FROZEN

Date: 2026-09-03

Environment: Supabase staging `mokxyyullfhkfalopbzd` and `Yourizorge/fitmetzorge-staging` only. Production was not touched.

## Scope

Package 6C provides the mobile-first FitMetZorge AI Coach private-chat foundation in NL, EN and DE. The deployed route uses a deterministic staging mock only. It does not invoke OpenAI, does not expose a provider or model selector, and cannot execute or propose application changes.

## Data And Ownership

The implementation reuses `public.ai_threads`, `public.ai_messages`, `public.ai_data_lifecycle_requests`, `ai_private.runs`, the Phase 6A consent and entitlement helpers, rate/budget/safety state, and the frozen completion/failure service RPCs. Added fields provide stable client request identity, thread revision, message sequence and run-to-source-message correlation. The only new table is `ai_private.phase6c_runtime_config`, which fixes mock mode on and external-provider mode off.

Browser roles have no direct table writes. Member RPCs derive the user from `auth.uid()`, bind threads/messages to that user, enforce current status and use fixed safe search paths. There is no trainer policy or trainer RPC. Message content is immutable; only the guarded transition to a scrubbed deleted state is permitted.

## Member RPCs

- `fmz_phase6c_get_chat_status`
- `fmz_phase6c_create_thread`
- `fmz_phase6c_list_threads`
- `fmz_phase6c_read_thread`
- `fmz_phase6c_submit_message`
- `fmz_phase6c_export_chat`
- `fmz_phase6c_delete_thread`

`fmz_phase6c_service_begin_mock_run` is service-role only. Existing Phase 6A service completion/failure RPCs persist the strict assistant response or sanitized failure state.

## Consent, Entitlement And Retention

Chat creation and message processing require age 18+, active versioned `ai_processing` consent, and a current active `ai` or `personal_coaching` entitlement. Free, Pro-only, missing, future, inactive and expired entitlements are denied. Consent withdrawal blocks new processing immediately while preserving own history/export/delete access.

Entitlement loss starts a server-authoritative read/export/delete-only grace period of at most 90 days. Reactivation before the deadline restores active state. A minute `pg_cron` sweep scrubs message content no later than the deadline. Deletion is own-user, revision-protected and idempotent; only non-content lifecycle audit metadata remains.

## Edge And Frontend

The `youri-ai/phase6c/chat` route requires a valid member JWT and an exact bounded payload containing request, attempt and thread identities, expected revision, locale and content. It first stores or replays the user message, reserves an idempotent zero-cost mock run, validates strict localized mock output and completes the run. Serious signals return the deterministic professional-help hard stop; diagnosis, medication and treatment requests receive a safe refusal. Actions are always empty.

The member UI provides consent activation/withdrawal, thread list, new thread, bounded history, composer, sending/failure/retry, offline handling, export and delete confirmation. Previously hydrated content may remain visible offline, but new content is never silently queued or represented as processed. Mobile layouts cover 320x700 and 390x844, with tablet and desktop compatibility.

## Evidence

- Migration: `supabase/migrations/20260902203000_phase6c_private_ai_chat.sql`
- Migration SHA-256: `131E63FF165069A4D2861EADEC838AD47906CF74A382C0F7CE8AB99F91D8D26F`
- Live migration history: `20260903085454` / `phase6c_private_ai_chat`
- Read-only verifier: `supabase/verification/20260902203000_phase6c_private_ai_chat_verification.sql`
- Verifier SHA-256: `CA1A5D407E8631A36B4C8629EFF5A529EF0010B8D408760CEF54E2339114552D`
- Verifier result: 37 PASS / 0 FAIL
- Transactional E2E: `supabase/tests/20260902203000_phase6c_private_ai_chat_transactional_e2e.sql`
- E2E SHA-256: `A3372F6DC48ECD97549F1BA8C7D499FA1981EF653A1565AC3A06C1A450DDBD22`
- E2E result: PASS with rollback; fixtures remaining 0
- Edge: `youri-ai` v39 ACTIVE; JWT verification enabled; bundle SHA-256 `d2856ac587d37d72967a383ae03ddaa21324d1ba37963133cb0a1e39b88a43e6`
- Package 6C static: 82/82 PASS
- Package 6C browser/responsive: 35/35 PASS
- Combined Phase 6 Edge tests: 44/44 PASS
- Frozen regressions: Phase 5 116/116 and 53/53; Phase 6A 93/93; Phase 6B 98/98; Nutrition 45/45 and 138/138
- Security advisor: no Package 6C ERROR; intended private no-policy and authenticated RPC notices reviewed
- Performance advisor: no Package 6C finding

## Safety Boundary

External AI calls during Package 6C: 0. External AI cost: EUR 0.00. Real-member OpenAI processing enabled: NO. Trainers can read private chat: NO. Member data changed during verification: NO. Test fixtures remaining: 0. Production touched: NO. Package 6D started: NO.
