"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const { exact, freeze, normalized, locales } = require("./common.cjs");
const contract = freeze(require("./contract.json"));
const rules = freeze(require("../phase6e0/rules.json"));
const hints = freeze(require("../phase6e0/context-hints.json"));
const existingCopy = freeze(require("../phase6e0/copy.json"));
const warningCopy = freeze(require("../phase6e0/warning-recovery-proposal.json")).warnings;
const issued = new WeakSet();
const now = /\b(?:nu|now|jetzt|momenteel|currently)\b/;
const personal = /\b(?:ik|mijn|mij|me|i|my|ich|mein(?:e|er)?|mir)\b/;
const other = /\b(?:mijn partner|my partner|mein partner|zij heeft|he has|she has|er hat|sie hat)\b/;
const present = /\b(?:heb|heeft|have|has|habe|hat|is|ben|bin|ist|voelt|feels|fuehlt|fuhlt|krijg|kriege|bekomme|kost|faellt|fallt|verliest|verliert)\b/;
const past = /\b(?:gisteren|yesterday|gestern|vorige maand|last month|letzten monat|vroeger|previously|fruher|frueher|had|was|were|hatte|war|voelde|felt|fuehlte|fuhlte|fiel)\b/;
const education = /\b(?:wat (?:is|zijn|betekent)|leg uit|what (?:is|are|does)|explain|was (?:ist|sind|bedeutet)|erklar(?:e|en)?|erklaer(?:e|en)?)\b/;
const hypothesis = /\b(?:stel dat|denkbeeldig|hypothetical|imagine|if (?:i|my)|wenn (?:ich|meine)|angenommen)\b/;
const recovery = /\b(?:mijn klachten zijn voorbij|klachten zijn voorbij|het gaat weer goed|geen klachten meer|de pijn is weg|my symptoms are gone|my symptoms have ended|i feel (?:well|fine) again|no symptoms (?:now|anymore)|pain is gone|meine beschwerden sind vorbei|mir geht es wieder gut|keine beschwerden mehr)\b/g;
const ordinary = /\b(?:train(?:ing|iere|ingseinheit)?|borsttraining|brusttraining|workout|curls|dumbbell|halter|hantel|gewichten|weights|gewichten|arming|armspieren|arm muscles|armmuskeln|warming.up|warm.up|sets|satz|arm strength|armkraft|rustige ademhaling|ruhige atmung|voel me prima|feel fine|geht es gut|wandelen|walking|spazieren)\b/;
const negatives = /\b(?:geen|zonder|niet|no|without|not|kein|keine|keinen|ohne|nicht)\b/g;
const healthWords = /\b(?:klachten|symptomen|symptoms|beschwerden|schmerz|pijn|pain|ziek|ill|krank)\b/g;
const levels = ["no_signal", "caution", "stop_clarify", "professional_review", "urgent_help"];
function finish(data) {
  const x = freeze({ contract_version: contract.context.version, ...data,
    medical_clearance: false, automatic_actions_allowed: false, provider_calls: 0,
    clinical_validation: "OPEN", country_inferred: false });
  issued.add(x); return x;
}
function makeFeedback(key, locale) {
  return { key, text: warningCopy[key]?.[locale] || existingCopy[locale][key],
    copy_source: warningCopy[key] ? "6e0_accepted_product_concept_not_expert_approved" : "6e0_provisional_copy" };
}
function assess(input) {
  const locale = locales.includes(input?.locale) ? input.locale : "en";
  const base = { locale, locale_fallback: locale !== input?.locale, trace: [], conflicts: [], recovery: false };
  if (!exact(input, ["synthetic_only", "text", "locale", "availability"]) || input.synthetic_only !== true ||
      typeof input.text !== "string" || input.text.length > 4096 || typeof input.locale !== "string" ||
      !["available", "unavailable"].includes(input.availability)) {
    return finish({ ...base, category: "technical", level: null, uncertainty: ["invalid_input"], feedback: makeFeedback("technical", locale) });
  }
  if (input.availability === "unavailable") return finish({ ...base, category: "technical", level: null,
    uncertainty: ["technical_unavailable"], feedback: makeFeedback("technical", locale) });
  const map = normalized(input.text), text = map.value, trace = [], conflicts = new Set(), uncertainty = new Set();
  if (!locales.includes(input.locale)) uncertainty.add("unsupported_language");
  if (!text.trim()) uncertainty.add("missing_context");
  if (/[^\u0000-\u024f\u2000-\u206f]/u.test(input.text)) uncertainty.add("unusual_symbols");
  let quoted = false, start = 0, inherited = null, sentencePersonal = false, recovered = false, quoteCount = 0;
  const clauses = [];
  // Sentence boundaries reset timing; conjunctions retain non-current scope until a new current report.
  const split = /"|[.!?;\n]|,|\b(?:maar|but|aber|en|and|und|terwijl|while|wahrend|waehrend)\b/g;
  for (const m of text.matchAll(split)) {
    clauses.push({ text: text.slice(start, m.index), offset: start, quoted, reset: false,
      question: m[0] === "?" });
    if (m[0] === '"') { quoted = !quoted; quoteCount++; }
    if (/^[.!?;\n]$/.test(m[0])) clauses.push({ reset: true });
    start = m.index + m[0].length;
  }
  clauses.push({ text: text.slice(start), offset: start, quoted, question: false });
  if (quoted) { conflicts.add("unclosed_quote"); uncertainty.add("unclosed_quote"); }
  function add(c, m, rule, context, basis) {
    const from = c.offset + m.index, to = from + m[0].length;
    trace.push({ rule_id: rule.id, signal: rule.code, provisional_level: rule.level,
      context, subject: other.test(c.text) ? "other" : personal.test(c.text) ? "self_text" : "unspecified",
      start: map.starts[from], end: map.ends[to - 1], fragment: input.text.slice(map.starts[from], map.ends[to - 1]),
      clause_start: map.starts[c.offset] ?? input.text.length,
      clause_end: map.ends[c.offset + c.text.length - 1] ?? input.text.length,
      context_basis: basis });
  }
  for (const c of clauses) {
    if (c.reset) { inherited = null; sentencePersonal = false; continue; }
    const t = c.text; if (!t.trim()) continue;
    const current = now.test(t), continuing = /\b(?:sinds|since|seit)\b/.test(t);
    let context = "current", basis = ["default_report_candidate"];
    if (c.quoted) { context = "quoted"; basis = ["quotation_span"]; }
    else if (hypothesis.test(t)) { context = "hypothetical"; basis = ["hypothesis_phrase"]; }
    else if (education.test(t)) { context = "educational"; basis = ["education_phrase"]; }
    else if (past.test(t) && !current && !continuing) { context = "past"; basis = ["past_phrase"]; }
    else if (inherited && !current && !(personal.test(t) && present.test(t))) { context = inherited; basis = ["coordinated_scope"]; }
    if (!c.quoted && current && ["past", "hypothetical"].includes(context)) {
      context = "current"; conflicts.add("timing_conflict"); basis.push("explicit_current_conflict");
    }
    inherited = ["past", "educational", "hypothetical"].includes(context) ? context : null;
    const covered = [], recoveryMatches = [...t.matchAll(recovery)];
    sentencePersonal ||= !c.quoted && !other.test(t) && personal.test(t);
    if (c.question && /\b(?:zijn mijn klachten voorbij|are my symptoms gone|sind meine beschwerden vorbei)\b/.test(t)) {
      const m = t.match(/\b(?:zijn mijn klachten voorbij|are my symptoms gone|sind meine beschwerden vorbei)\b/);
      covered.push([m.index, m.index + m[0].length]);
      add(c, m, { id: "recovery.question.v1", code: "self_report_phrase", level: null }, "unspecified", ["recovery_question"]);
    }
    for (const m of recoveryMatches) {
      covered.push([m.index, m.index + m[0].length]);
      const neg = /\b(?:niet|not|nicht)\b/.test(t.slice(0, m.index));
      if (context === "current" && !c.question && !other.test(t) && !neg) recovered = true;
      else add(c, m, { id: "recovery.noncurrent", code: "self_report_phrase", level: null },
        c.question && context === "current" ? "unspecified" : context, basis);
    }
    const matches = [];
    for (const m of t.matchAll(/\b(?:kriege|bekomme) ich (?:(?:kaum|wenig)(?: noch)?|nur wenig) luft\b/g)) {
      matches.push({ m, id: "context.limited_air_inversion.v1", code: "limited_air", level: null, internal: false });
    }
    for (const r of rules) r.patterns.forEach((p, i) => {
      for (const m of t.matchAll(new RegExp(p, "g"))) matches.push({ m, id: "6e0." + r.code + "." + i,
        code: r.code, level: r.level, internal: false });
    });
    for (const r of hints.hints) r.patterns.forEach((p, i) => {
      for (const m of t.matchAll(new RegExp(p, "g"))) matches.push({ m, id: "6e0.hint." + r.code + "." + i,
        code: r.code, level: null, internal: !r.intrinsic_shortage });
    });
    for (const m of t.matchAll(healthWords)) matches.push({ m, id: "context.health_word.v1", code: "unclassified",
      level: null, internal: false });
    for (const r of matches) {
      const m = r.m, end = m.index + m[0].length;
      if (covered.some(([s, e]) => m.index >= s && end <= e)) continue;
      covered.push([m.index, end]);
      let scoped = context, reasons = [...basis];
      if (scoped === "current") {
        const prefix = t.slice(0, m.index).match(/\b(?:geen|zonder|niet|no|without|not|kein|keine|keinen|ohne|nicht)\b(?:\s+\p{L}+){0,3}\s*$/u)?.[0] || "";
        const negCount = [...(prefix + " " + (r.internal ? m[0] : "")).matchAll(negatives)].length;
        const after = /^\s+(?:(?:is|are|ist|sind|zijn)\s+)?(?:afwezig|absent|nicht vorhanden)\b/.test(t.slice(end));
        if (negCount > 1) { conflicts.add("negation_conflict"); reasons.push("negation_conflict"); }
        else if (negCount === 1 || after) { scoped = "negated"; reasons.push("signal_local_negation"); }
        else if (other.test(t)) { scoped = "other"; reasons.push("other_subject"); }
        else if (!sentencePersonal && !personal.test(t) && !present.test(t) && !current && t.trim().split(/\s+/).length <= 3) {
          scoped = "unspecified"; reasons.push("missing_subject_timing");
        }
      }
      add(c, m, r, scoped, reasons);
    }
    const body = t.match(/\b(?:borst|arm|linkerarm|rechterarm|chest|brust)\b/);
    if (body && context === "current" && personal.test(t) && !other.test(t) && !ordinary.test(t) &&
        !covered.some(([s, e]) => body.index >= s && body.index < e)) {
      uncertainty.add("unmapped_body_context");
      add(c, body, { id: "context.unmapped_body.v1", code: "unmapped_body", level: null },
        "unspecified", ["unmapped_body_context_not_a_medical_label"]);
    }
  }
  const active = trace.filter(t => t.context === "current");
  if (trace.some(t => ["other", "unspecified"].includes(t.context))) uncertainty.add("missing_subject_or_context");
  if (recovered && active.length) { conflicts.add("recovery_conflict"); recovered = false; }
  if (recovered && /\b(?:misschien|mogelijk|denk|think|maybe|perhaps|possibly|glaube|vielleicht|eventuell)\b/.test(text)) {
    uncertainty.add("tentative_self_report"); recovered = false;
  }
  if (quoteCount && /\b(?:dat heb ik nu ook|that is happening to me|das habe ich jetzt auch)\b/.test(text)) {
    conflicts.add("quoted_adoption_unresolved"); uncertainty.add("quoted_adoption_unresolved");
  }
  if (active.some(a => trace.some(t => t.signal === a.signal && t.context !== "current"))) conflicts.add("mixed_signal_context");
  if (active.some(a => a.provisional_level === null)) uncertainty.add("unclassified_health_context");
  const ranked = active.filter(a => a.provisional_level !== null);
  let level = ranked.length ? "R" + Math.max(...ranked.map(a => Number(a.provisional_level.slice(1)))) : null;
  if (ranked.some(t => t.signal === "chest") && ranked.some(t => t.signal === "dizziness")) level = "R4";
  let key, category;
  if (active.length) { key = level ? levels[Number(level.slice(1))] : "current_unclassified"; category = "health_report"; }
  else if (uncertainty.size || conflicts.size) { key = "unclear"; category = "communication"; }
  else if (trace.length) { key = "noncurrent"; level = "R0"; category = "noncurrent"; }
  else if (recovered || ordinary.test(text)) { key = "no_signal"; level = "R0"; category = "ordinary"; }
  else { key = "unclear"; category = "communication"; uncertainty.add("unresolved_meaning"); }
  return finish({ ...base, category, level, trace, conflicts: [...conflicts].sort(),
    uncertainty: [...uncertainty].sort(), recovery: recovered && category === "ordinary",
    feedback: makeFeedback(key, locale) });
}
const isAssessment = x => issued.has(x);
module.exports = { assess, isAssessment, contract };
