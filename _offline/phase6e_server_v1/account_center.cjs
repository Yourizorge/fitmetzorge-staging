'use strict';
const policy = require('./access_policy.cjs');

// Called only with a server-selected entitlement source and server time.
// Absence is not Free access. This projection cannot authorize an action.
function access(source, now) {
  if (source == null) return {status: 'source_missing', read_only: true};
  try {
    const result = policy.view(source, now);
    const trial = source.grants.find(grant => grant.kind === 'trial');
    return {
      status: 'verified_synthetic', read_only: true, synthetic_only: true,
      source: {id: source.id, version: source.version}, evaluated_at: now,
      policy: result,
      trial: trial ? {
        id: trial.id, start: trial.start, end: trial.end,
        status: trial.revoked ? 'revoked' : now < trial.start ? 'scheduled' : now < trial.end ? 'active' : 'expired',
        fallback: trial.revoked ? null : {at: trial.end, tier: policy.view(source, trial.end).tier}
      } : null
    };
  } catch (_) {
    return {status: 'source_invalid', read_only: true};
  }
}

module.exports = {access};
