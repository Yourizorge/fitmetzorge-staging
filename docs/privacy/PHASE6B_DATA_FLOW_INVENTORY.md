# Phase 6B Data Flow Inventory

Status: TECHNICAL CONTRACT / SYNTHETIC ONLY

## Synthetic Test Flow

1. A server-only caller submits `request_id` and one locked fixture code to the staging `youri-ai` Edge Function.
2. The Edge builds a deterministic synthetic payload and validates its exact keys.
3. A service-only RPC atomically reserves the global staging call/cost budget.
4. The Edge calls OpenAI Responses with `store:false`, no tools and strict JSON output.
5. The Edge validates output before returning it and stores only hashes, token counts, estimated cost, fixture purpose, model and safe status.

No browser/member route exists. No member record is read for the synthetic flow.

| Provider field | Purpose | Classification |
| --- | --- | --- |
| `schema_version` | immutable parser contract | contract |
| `feature_code` | select reviewed response schema | contract |
| `locale` | synthetic language contract | contract |
| `synthetic_subject_token` | unmistakably synthetic pseudonym | synthetic non-personal |
| `snapshot.goal_code` | fixture goal context | synthetic non-personal |
| `snapshot.training.completed_sessions_7d` | bounded synthetic aggregate | aggregate synthetic |
| `snapshot.nutrition.average_energy_kcal_7d` | bounded synthetic aggregate | aggregate synthetic |
| `snapshot.recovery.average_sleep_hours_7d` | bounded synthetic aggregate | aggregate synthetic |
| `request_purpose` | auditable route purpose | contract |

Excluded: member UUIDs, account identity, names, email, address, phone, raw rows, unrelated history, raw chat, trainer notes, injury/medication details and credentials.

## Future Member Flow

BLOCKED. A future package must separately define task-specific minimization, consent purpose, pseudonym rotation, retention and exact fields. It may not reuse the synthetic contract as permission to send member data.
