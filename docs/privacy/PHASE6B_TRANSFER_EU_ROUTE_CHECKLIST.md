# Phase 6B EU Route, Transfer And ZDR Checklist

Status: UNVERIFIED / REAL-MEMBER PROCESSING BLOCKED

- [ ] Exact OpenAI API project is configured for Europe data residency.
- [ ] Exact selected models/endpoints are eligible in that project.
- [ ] Real-member calls use `https://eu.api.openai.com/v1/responses`.
- [ ] Zero Data Retention is approved and enabled for the exact project.
- [ ] Project-level Data Retention status is evidenced; `store:false` is not accepted as ZDR proof.
- [ ] No endpoint/feature incompatible with ZDR is enabled.
- [ ] DPA and applicable SCC/transfer assessment are complete.
- [ ] Current subprocessor destinations and safeguards are recorded.
- [ ] Deletion, export and consent withdrawal are tested end to end.
- [ ] Owner performs a later explicit real-member activation.

OpenAI documentation states that Europe data residency for API projects requires eligible data controls and the Europe endpoint; ZDR requires prior approval/configuration. Synthetic 6B testing may use the standard endpoint but grants no member-data permission.
