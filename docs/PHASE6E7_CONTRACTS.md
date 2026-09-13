# Package 6E-7 Contracts

TECHNICAL PASS / READY FOR OWNER REVIEW. Synthetic standalone mock only.
K1-K4 accepted as scope on 2026-09-13; no acceptance/freeze of the built results.
D1-D12/O1-O5/N1-N3/G1-G3/T1-T4/V1-V2/P1-P3/W1-W2 retained.

## Contract Boundaries

Private source validation: issued frozen 6E-6 proposal, exact owner/plan/set bindings,
source refs and basis. Public mock: only generated synthetic fixtures and a new
in-memory controller. The public controller is not a trusted trainer authority.
Frozen code never imported by the browser. No appstorage, account, network or DB.

Command fields: id, action, actor, subject, proposal_id, proposal_basis,
expected_revision, target_version, reason. No extra fields. Reasons are a fixed
neutral allowlist. Approval is for the exact proposal and binding, not a generic
permission for subsequent proposals or a different kg/lb fixture.

| State | Permitted changes |
| --- | --- |
| member_pending | Member accept or reject |
| trainer_pending | Linked synthetic trainer approve, reject or block |
| approved | Separate trainer apply only |
| applied | New restore proposal from a retained version, if gates still valid |
| restore member_pending | New member acceptance, then new trainer approval/apply |
| blocked/rejected/maintained | No application; whole plan unchanged |

No partial write. Plan/history/status/audit/outbox published together in memory.
Retry of identical successful command returns current view without a second event.
Same command ID with different content is rejected. Wrong source/review/proposal
binding is rejected. A changed source invalidates both pending approvals.
Old applied state is not automatically undone by subsequent withdrawal.

Restore is a new proposal with current source refs and stored target contents.
New revision is current+1; never reset the version counter or rewrite old snapshots.
No medical or trainer eligibility is inferred from an old plan or self-report.

## Presentation And Tests

Current/next per-set comparison, exact changed cells, recorded facts with source
versions, independent RIR/RPE, numeric W2 step and weights. No alternative invented.
No-change maintain results do not create artificial schema mutations.
In-app notifications contain only fixed status/reason/time fields.
Fixture names/personas are visible simulations, not privacy controls on real data.

No free text or upload, no providers or paid services, no automatic actions.
No broader language classifier change; known limitations remain explicit.
[Evidence](PHASE6E7_EVIDENCE.json), [technical report](PHASE6E7_TECHNICAL_REPORT.md),
[owner review](PHASE6E7_OWNER_OVERVIEW.md).
