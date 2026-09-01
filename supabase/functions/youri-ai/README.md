# Youri AI Phase 6A

Provider-neutral trust-boundary scaffold for staging.

- External AI calls: none.
- Provider credentials: none.
- Service-role credential: none.
- Normal member operation: disabled by database flags.
- Deterministic mock operation: additionally disabled unless the explicit staging-only `FMZ_PHASE6A_MOCK_TEST_ENABLED=true` environment flag is present.
- The mock adapter only emits fixture-controlled structured output and never represents real coaching.

Phase 6B owns provider activation, privacy/legal completion, real model identifiers, secrets and controlled paid-call acceptance.
