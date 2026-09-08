"use strict";
const { create, apply, view } = require("../flow.cjs");
const { analyze } = require("../analysis.cjs");
const { authority, subject, message, begin, recover, event, sample } = require("./helpers.cjs");
function examples() {
  const result = [];
  for (const [id, text, kind] of [["unclassified-daily", "Mijn borst voelt loodzwaar", "daily"],
    ["serious-workout", "Ik heb borstpijn", "post_workout"],
    ["repeated-week", "Ich kriege kaum noch Luft", "weekly"]]) {
    let first = message(create(subject), text, id === "repeated-week" ? "de" : "nl");
    const before = analyze(sample(kind), first.state, authority);
    const recovered = recover(first.state, "chat", "Mijn klachten zijn voorbij");
    const after = analyze(sample(kind), recovered.state, authority);
    const repeated = message(recovered.state, text, id === "repeated-week" ? "de" : "nl");
    result.push({ id, message: text, warning: first.assessment.feedback, before,
      recovery_message: "Mijn klachten zijn voorbij", recovery_status: recovered.status, after,
      next_same_report: { warning: repeated.assessment.feedback, flow: view(repeated.state) } });
  }
  for (const [id, text, availability, clarification] of [
    ["technical-retry", "Ik train borst en armen", "unavailable", null],
    ["language-clarification", "flurbel", "available", "Ik bedoelde mijn borsttraining met gewichten"]
  ]) {
    const first = message(create(subject), text, "nl", availability), started = begin(first.state);
    const done = apply(started.state, event(started.state, clarification ? "clarify" : "retry",
      clarification ? { binding: started.binding, text: clarification, locale: "nl" } :
        { binding: started.binding, availability: "available" }));
    result.push({ id, message: text, warning: first.assessment.feedback,
      before: analyze(sample(), first.state, authority), clarification_or_retry: clarification || "retry original text / available",
      outcome: done.status, after: analyze(sample(), done.state, authority), medical_clearance: false });
  }
  return result;
}
module.exports = { examples };
if (require.main === module) console.log(JSON.stringify(examples(), null, 2));
