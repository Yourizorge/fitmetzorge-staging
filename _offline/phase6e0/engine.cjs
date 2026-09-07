"use strict";

if (typeof window !== "undefined" || !process.versions.node) throw new Error("offline_node_only");
const contract = require("./contract.json");
const rules = require("./rules.json");
const copy = require("./copy.json");
function freeze(value) {
  if (value && typeof value === "object") {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
freeze(contract); freeze(rules); freeze(copy);
const plain = value => value !== null && typeof value === "object" &&
  !Array.isArray(value) && [Object.prototype, null].includes(Object.getPrototypeOf(value));
const exact = (value, keys) => plain(value) &&
  Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const oneOf = (value, choices) => choices.includes(value);
const uniqueList = (value, choices) => Array.isArray(value) &&
  value.length <= choices.length && new Set(value).size === value.length &&
  value.every(item => choices.includes(item));
const rank = level => level === null ? -1 : Number(level.slice(1));
const codes = rules.map(rule => rule.code);
const compiled = rules.map(rule => ({ ...rule, patterns: rule.patterns.map(pattern => new RegExp(pattern, "g")) }));
const warnings = ["no_signal", "caution", "stop_clarify", "professional_review", "urgent_help"];
const assessmentKeys = ["contract_version", "review_status", "evaluation_state", "help_level",
  "signal_codes", "context_states", "uncertainty_codes", "warning_key", "recovery_intent",
  "medical_clearance", "automatic_actions_allowed"];
function normalize(text) {
  return text.normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .replace(/\u00df/g, "ss").replace(/[\u200B-\u200D\uFEFF]/g, "")
    .replace(/[\u201C\u201D]/g, '"').replace(/[\u2018\u2019']/g, "")
    .toLowerCase().replace(/[^\p{L}\p{N}".!?;\n]+/gu, " ").replace(/[ \t]+/g, " ").trim();
}
function result(overrides = {}) {
  return {
    contract_version: contract.version, review_status: "PROVISIONAL_REVIEW_REQUIRED",
    evaluation_state: "known", help_level: "R0", signal_codes: [], context_states: [],
    uncertainty_codes: [], warning_key: "no_signal", recovery_intent: null,
    medical_clearance: false, automatic_actions_allowed: false, ...overrides
  };
}
function unavailable(code) {
  return result({ evaluation_state: "unavailable", help_level: null,
    uncertainty_codes: [code], warning_key: "unavailable" });
}
function validInput(input) {
  return exact(input, ["contract_version", "synthetic_only", "text", "locale", "availability", "context"]) &&
    input.contract_version === contract.version && input.synthetic_only === true &&
    typeof input.text === "string" && input.text.length <= contract.max_text_length &&
    oneOf(input.locale, [...contract.locales, ...contract.deferred_locales, "unknown"]) &&
    oneOf(input.availability, ["available", "unavailable"]) &&
    exact(input.context, ["timing", "subject"]) &&
    oneOf(input.context.timing, ["unspecified", "current", "past", "hypothetical"]) &&
    oneOf(input.context.subject, ["unspecified", "self", "other"]);
}
function validateAssessment(value) {
  if (!exact(value, assessmentKeys) || value.contract_version !== contract.version ||
    value.review_status !== "PROVISIONAL_REVIEW_REQUIRED" ||
    !oneOf(value.evaluation_state, contract.evaluation_states) ||
    !oneOf(value.help_level, [null, ...Object.keys(contract.help_levels)]) ||
    !uniqueList(value.signal_codes, codes) ||
    !uniqueList(value.context_states, contract.context_states) ||
    !uniqueList(value.uncertainty_codes, contract.uncertainty_codes) ||
    !oneOf(value.warning_key, contract.warning_keys) ||
    !oneOf(value.recovery_intent, contract.recovery_intents) ||
    value.medical_clearance !== false || value.automatic_actions_allowed !== false) return false;
  if (value.evaluation_state === "unavailable") return value.help_level === null &&
    value.warning_key === "unavailable" && value.recovery_intent === null && value.signal_codes.length === 0 &&
    value.uncertainty_codes.some(code => ["invalid_input", "technical_unavailable"].includes(code));
  if (value.evaluation_state === "known" && (value.help_level === null || value.uncertainty_codes.length)) return false;
  if (value.evaluation_state === "uncertain" && (!value.uncertainty_codes.length || value.help_level === "R0")) return false;
  if (rank(value.help_level) >= 1 && !value.signal_codes.length) return false;
  if (value.signal_codes.length && rank(value.help_level) < 1) return false;
  const minimum = value.signal_codes.length ? Math.max(...rules.filter(rule => value.signal_codes.includes(rule.code)).map(rule => rank(rule.level))) : 0;
  if (rank(value.help_level) >= 0 && rank(value.help_level) < minimum) return false;
  if (value.signal_codes.includes("chest") && value.signal_codes.includes("dizziness") && value.help_level !== "R4") return false;
  const expectedWarning = value.help_level === null ? "uncertain" : warnings[rank(value.help_level)];
  if (value.warning_key !== expectedWarning) return false;
  if (value.recovery_intent !== null && (value.evaluation_state !== "known" || value.help_level !== "R0")) return false;
  return true;
}
const personalNow = /\b(?:ik (?:heb|ben|voel|wil|kan)|i (?:have|am|feel|want|cannot|cant)|ich (?:habe|bin|will|kann)|mijn partner|my partner|mein partner|nu|now|jetzt|momenteel|currently)\b/;
const explicitNow = /\b(?:nu|now|jetzt|momenteel|currently)\b/;
const educational = /\b(?:wat (?:is|zijn|betekent)|leg uit|what (?:is|are|does)|explain|was (?:ist|sind|bedeutet)|erklar|erklaer)\b/;
const past = /\b(?:vorige maand|last month|letzten monat|vroeger|previously|fruher|frueher|gisteren|yesterday|gestern)\b/;
const continuing = /\b(?:sinds|since|seit)\b/;
const hypothetical = /\b(?:stel dat|denkbeeldig|hypothetical|imagine|if i ever|wenn ich jemals|angenommen)\b/;
const negation = /\b(?:geen|zonder|niet|no|without|not|kein|keine|keinen|ohne|nicht)\b(?:\s+[\p{L}]+){0,2}\s*$/u;
const afterNegation = /^\s+(?:(?:is|are|ist|sind|zijn)\s+)?(?:afwezig|absent|nicht vorhanden)\b/;
const recovery = /\b(?:het gaat weer goed|geen klachten meer|de pijn is weg|klachten zijn voorbij|i feel (?:well|fine) again|no symptoms (?:now|anymore)|pain is gone|mir geht es wieder gut|keine beschwerden mehr)\b/;
const dispute = /\b(?:verkeerd begrepen|misunderstood|missverstanden)\b/;
function classify(input) {
  if (!validInput(input)) return unavailable("invalid_input");
  if (input.availability === "unavailable") return unavailable("technical_unavailable");
  const text = normalize(input.text), uncertainties = new Set(), contexts = new Set();
  const active = new Set(), inactive = new Set();
  let hasRecovery = false, hasDispute = false;
  if (!contract.locales.includes(input.locale)) uncertainties.add("unsupported_language");
  if (!text) uncertainties.add("missing_context");
  if (/[^\u0000-\u024F\u0300-\u036F\u2000-\u206F]/u.test(input.text)) uncertainties.add("unusual_unicode");
  if (/\b(?:ho dolore|petto|poitrine|douleur|respirare)\b/.test(text)) uncertainties.add("unrecognized_language");
  if (/\b(?:ignore|negeer|ignorier|override|system prompt|system message|developer message|roleplay)\b/.test(text)) uncertainties.add("instruction_attempt");
  const pieces = text.match(/"[^"]*"|[^"]+/g) || [];
  for (const piece of pieces) {
    const quoted = piece.startsWith('"');
    // Clause boundaries prevent a preceding negation or educational question swallowing a new signal.
    const clauses = piece.replace(/"/g, "").split(/[.!?;\n]+|\b(?:maar|but|aber|en|and|und)\b/);
    for (const clause of clauses) {
      const now = explicitNow.test(clause);
      let context = quoted ? "quoted" : "current";
      if (!quoted && hypothetical.test(clause) && !now) context = "hypothetical";
      else if (!quoted && past.test(clause) && !now && !continuing.test(clause)) context = "past";
      else if (!quoted && educational.test(clause) && !personalNow.test(clause)) context = "educational";
      if ((past.test(clause) || hypothetical.test(clause)) && now) uncertainties.add("contradictory_context");
      const ownCurrentReport = context === "current" && input.context.subject !== "other" &&
        !["past", "hypothetical"].includes(input.context.timing) &&
        !/\b(?:mijn partner|my partner|mein partner)\b/.test(clause);
      if (ownCurrentReport && !piece.includes("?")) {
        const recovered = clause.match(recovery), disputed = clause.match(dispute);
        const affirmative = match => match && !/\b(?:niet|not|nicht)\b/.test(clause.slice(0, match.index));
        hasRecovery ||= Boolean(affirmative(recovered));
        hasDispute ||= Boolean(affirmative(disputed));
      }
      for (const rule of compiled) {
        for (const pattern of rule.patterns) {
          for (const match of clause.matchAll(pattern)) {
            let matchedContext = context;
            const before = clause.slice(0, match.index).trimEnd();
            const after = clause.slice(match.index + match[0].length);
            const negations = before.match(/\b(?:geen|niet|no|not|kein|keine|nicht)\b/g) || [];
            if (context === "current" && negation.test(before) && negations.length < 2) matchedContext = "negated";
            if (context === "current" && afterNegation.test(after)) matchedContext = "negated";
            if (negations.length >= 2) uncertainties.add("ambiguous_context");
            contexts.add(matchedContext);
            if (matchedContext === "current") {
              active.add(rule.code);
              if (!personalNow.test(clause) && input.context.subject === "unspecified") contexts.add("unspecified");
              if (input.context.timing === "past" || input.context.timing === "hypothetical") uncertainties.add("contradictory_context");
            } else inactive.add(rule.code);
          }
        }
      }
    }
  }
  if ([...active].some(code => inactive.has(code))) uncertainties.add("contradictory_context");
  if ((hasRecovery || hasDispute) && active.size) uncertainties.add("contradictory_context");
  if (quotedHealthWithCurrentOutside(pieces)) uncertainties.add("ambiguous_context");
  if (!active.size && !inactive.size && /\b(?:klachten|symptoms|beschwerden|medicatie|medication|schmerz|pijn|pain|ziek|ill|krank)\b/.test(text) && !hasRecovery) {
    uncertainties.add("unrecognized_health_context");
  }
  if (active.size && !personalNow.test(text) && input.context.timing === "unspecified" &&
      !inactive.size && text.split(/\s+/).length <= 3) uncertainties.add("missing_context");
  let level = active.size ? "R" + Math.max(...rules.filter(rule => active.has(rule.code)).map(rule => rank(rule.level))) : "R0";
  if (active.has("chest") && active.has("dizziness")) level = "R4";
  const state = uncertainties.size ? "uncertain" : "known";
  if (!active.size && uncertainties.size) level = null;
  const assessment = result({
    evaluation_state: state, help_level: level, signal_codes: [...active].sort(),
    context_states: [...contexts].sort(), uncertainty_codes: [...uncertainties].sort(),
    warning_key: level === null ? "uncertain" : warnings[rank(level)],
    recovery_intent: state === "known" && !active.size && !inactive.size ?
      hasRecovery ? "symptoms_resolved" : hasDispute ? "disputed" : null : null
  });
  if (!validateAssessment(assessment)) throw new Error("offline_contract_defect");
  return assessment;
}
function quotedHealthWithCurrentOutside(pieces) {
  return pieces.some(piece => piece.startsWith('"')) &&
    pieces.filter(piece => !piece.startsWith('"')).some(piece => personalNow.test(piece));
}
const authorityKeys = ["synthetic_only", "authenticated", "adult", "ai_entitlement",
  "private_chat_consent", "ai_analysis_consent", "own_history_access"];
function access(snapshot) {
  const valid = exact(snapshot, authorityKeys) && snapshot.synthetic_only === true &&
    authorityKeys.every(key => typeof snapshot[key] === "boolean");
  const base = valid && snapshot.authenticated && snapshot.adult && snapshot.ai_entitlement;
  return {
    chat: Boolean(base && snapshot.private_chat_consent),
    history: Boolean(valid && snapshot.authenticated && snapshot.own_history_access),
    new_analysis: Boolean(base && snapshot.ai_analysis_consent),
    entitlements_modified: false
  };
}
function help(assessment, locale, snapshot, explicitCountry = null) {
  if (!contract.locales.includes(locale)) return { available: false, reason: "unsupported_locale", text: null };
  if (!access(snapshot).chat) return { available: false, reason: "outside_accessible_chat", text: null };
  const checked = validateAssessment(assessment) ? assessment : unavailable("invalid_input");
  const country = ["NL", "BE", "DE", "AT", "IT", "FR"].includes(explicitCountry) ? explicitCountry : null;
  const urgent = checked.help_level === "R4";
  return {
    available: true, reason: "draft_local_copy", status: copy.status,
    text: copy[locale][checked.warning_key], country,
    extra: urgent && country ? copy[locale].eu_help : null,
    automatic_contact: false, provider_calls: 0
  };
}
function boundedAnalysis(request, assessment, snapshot) {
  if (!exact(request, ["synthetic_only", "kind", "facts"]) || request.synthetic_only !== true ||
    !contract.analysis_kinds.includes(request.kind) || !Array.isArray(request.facts) || request.facts.length > 20) {
    return { status: "invalid_input", facts: [], advice: [], actions: [] };
  }
  const validFacts = request.facts.every(fact => exact(fact, ["code", "value"]) &&
    contract.fact_codes.includes(fact.code) &&
    (fact.value === null || (typeof fact.value === "number" && Number.isFinite(fact.value) && fact.value >= 0 && fact.value <= 1000000)));
  if (!validFacts || new Set(request.facts.map(fact => fact.code)).size !== request.facts.length) {
    return { status: "invalid_input", facts: [], advice: [], actions: [] };
  }
  const permission = access(snapshot);
  const checked = validateAssessment(assessment) ? assessment : unavailable("invalid_input");
  const facts = permission.new_analysis ? request.facts.filter(fact => fact.value !== null).map(fact => ({ ...fact })) : [];
  return {
    contract_version: contract.version, status: !permission.new_analysis ? "access_unavailable" :
      facts.length ? "bounded_facts" : "insufficient_data",
    access: permission, warning_key: checked.warning_key,
    help_first: checked.help_level === "R4", facts,
    personalized_advice: "NOT_IMPLEMENTED_REVIEW_REQUIRED", advice: [], actions: [],
    medical_clearance: false, automatic_actions_allowed: false, provider_calls: 0,
    trainer_sharing: false
  };
}
module.exports = { contract, rules, copy, exact, plain, rank, normalize, classify, validateAssessment,
  access, help, boundedAnalysis };
