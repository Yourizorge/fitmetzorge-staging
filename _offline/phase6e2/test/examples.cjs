"use strict";
const { setup, engine, types } = require("./fixtures.cjs");
function examples() {
  const result = [];
  for (const locale of ["nl", "en", "de"]) for (const kind of Object.keys(types)) {
    const f = setup({ kind, locale });
    result.push({ id: kind + "-" + locale, kind, locale, input: f.request.analysis,
      output: engine.recommend(f.request, f.context, f.authority) });
  }
  return result;
}
function transitions() {
  const result = [];
  for (const scenario of ["ordinary", "current", "unclassified", "unclear", "technical", "clarified",
    "technical_retry", "self_reported", "serious_recovered", "new_after_recovery", "recurring",
    "expired", "expired_fresh", "missing", "missing_fresh", "continue_chat"]) {
    result.push({ scenario, results: Object.keys(types).map(kind => {
      const f = setup({ scenario, kind }), output = engine.recommend(f.request, f.context, f.authority);
      return { kind, output };
    }) });
  }
  return result;
}
module.exports = { examples, transitions };
if (require.main === module) console.log(JSON.stringify({ examples: examples(), transitions: transitions() }, null, 2));
