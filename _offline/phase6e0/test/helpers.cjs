"use strict";
const { contract, classify } = require("../engine.cjs");
function input(text, locale = "nl", patch = {}) {
  return { contract_version: contract.version, synthetic_only: true, text, locale,
    availability: "available", context: { timing: "unspecified", subject: "unspecified" }, ...patch };
}
const authority = { synthetic_only: true, authenticated: true, adult: true, ai_entitlement: true,
  private_chat_consent: true, ai_analysis_consent: true, own_history_access: true };
const assess = (text, locale = "nl", patch = {}) => classify(input(text, locale, patch));
module.exports = { input, authority, assess };
