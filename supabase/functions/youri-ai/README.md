# Youri AI Phase 6A

Provider-neutral trust-boundary scaffold for staging.

- External AI calls: none.
- Provider credentials: none.
- Service-role credential: none.
- Normal member operation: disabled by database flags.
- Deterministic mock operation: additionally disabled unless the explicit staging-only `FMZ_PHASE6A_MOCK_TEST_ENABLED=true` environment flag is present.
- The mock adapter only emits fixture-controlled structured output and never represents real coaching.

Phase 6B owns provider activation, privacy/legal completion, real model identifiers, secrets and controlled paid-call acceptance.

## Phase 6B staging gate

- Official routes: `gpt-5.6-luna` and `gpt-5.6-terra` through the Responses API.
- Synthetic requests only; callers cannot supply prompts, context, tools, model IDs or member data.
- `store: false`, empty tools and `tool_choice: none` are immutable request properties.
- `/phase6b/status` and `/phase6b/synthetic-test` are server-only and require a service credential; browser/member JWTs are rejected.
- Real-member provider processing has no Edge route and remains database-blocked until ZDR, DPA, DPIA, EU route, approved copy, transfer/lifecycle checks and a later owner activation all pass.
- `OPENAI_API_KEY` and `FMZ_PHASE6B_SYNTHETIC_TEST_ENABLED` are server-only Supabase Edge secrets. Their absence fails closed and is never logged.
- The global staging test ledger reserves conservatively and cannot exceed EUR 5 or six external attempts.
