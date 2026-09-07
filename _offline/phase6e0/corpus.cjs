"use strict";
const seeds = require("./fixture-seeds.json");
const words = {
  nl: { now: "Nu", quote: "Citaat", educate: "Wat betekent", past: "Vorige maand",
    hypothetical: "Stel dat", negation: "Geen", mixed: "Ik heb geen koorts maar", recovery: "Het gaat weer goed" },
  en: { now: "Now", quote: "Quote", educate: "Explain", past: "Last month",
    hypothetical: "Imagine", negation: "No", mixed: "I have no fever but", recovery: "I feel fine again" },
  de: { now: "Jetzt", quote: "Zitat", educate: "Was bedeutet", past: "Letzten Monat",
    hypothetical: "Angenommen", negation: "Kein", mixed: "Ich habe kein Fieber aber", recovery: "Mir geht es wieder gut" }
};
function corpus() {
  return seeds.flatMap(seed => {
    const w = words[seed.locale];
    const variants = [
      ["current", w.now + ": " + seed.text + ".", seed.expected_level, "known"],
      ["plain", seed.text + ".", seed.expected_level, "known"],
      ["uppercase", (w.now + ": " + seed.text + ".").toUpperCase(), seed.expected_level, "known"],
      ["quote", w.quote + ': "' + seed.text + '"', "R0", "known"],
      ["education", w.educate + ": " + seed.term + "?", "R0", "known"],
      ["past", w.past + ": " + seed.text + ".", "R0", "known"],
      ["hypothetical", w.hypothetical + ": " + seed.text + ".", "R0", "known"],
      ["negation", w.negation + " " + seed.term + ".", "R0", "known"],
      ["mixed_negation", w.mixed + " " + seed.text + ".", seed.expected_level, "known"],
      ["mixed_education", w.educate + ": " + seed.term + "? " + w.now + ": " + seed.text + ".", seed.expected_level, "uncertain"],
      ["recovery_conflict", w.recovery + ". " + w.now + ": " + seed.text + ".", seed.expected_level, "uncertain"],
      ["current_other", w.now + ": " + seed.third + ".", seed.expected_level, "known"]
    ];
    return variants.map(([variant, text, level, evaluation]) => ({
      id: seed.id + "-" + variant, locale: seed.locale, category: seed.category, variant, text,
      expected: { help_level: level, evaluation_state: evaluation },
      label_status: seed.label_status, synthetic_only: true,
      interpretation: "Lexical/context contract probe, not a clinical observation or accuracy estimate."
    }));
  });
}
module.exports = { corpus };
