# Phase 6B DPIA Draft

Status: INCOMPLETE DRAFT / OWNER, PRIVACY AND LEGAL APPROVAL REQUIRED

## Proposed Processing

Future Youri AI may process minimized member-selected fitness, nutrition, recovery and progress context to produce non-medical coaching information. Package 6B processes only synthetic fixtures and does not authorize that future processing.

## Necessity And Proportionality Questions

- Is each proposed member field necessary for the exact task?
- Can an aggregate, category or short-lived pseudonym replace the raw value?
- Is separate explicit AI consent current and withdrawable?
- Can the product work without AI after refusal/withdrawal?
- Are retention, export, deletion and entitlement expiry independently verified?

## Principal Risks And Controls

| Risk | Required control |
| --- | --- |
| special-category/health inference | task minimization, ZDR, no diagnostic authority, deterministic hard stops |
| identity leakage | no direct identity, rotating pseudonym, no raw account IDs |
| cross-member access | JWT ownership, RLS, service-only operational state |
| unsafe coaching | strict output, allowlisted actions, no direct domain write, review/escalation |
| prompt/tool abuse | no hosted tools, bounded input, strict schema, no dynamic URL/RPC/SQL |
| international transfer | DPA/SCC assessment, verified EU project/endpoint, ZDR |
| hidden cost | pre-call reservation, EUR caps, no automatic billing |

Residual risk, lawful basis, data-subject consultation, DPO involvement and final approval remain OWNER DECISION REQUIRED.
