"use strict";
if (typeof window !== "undefined" || typeof process === "undefined" || !process.versions?.node) throw Error("offline_node_only");
const plain = x => x !== null && typeof x === "object" && !Array.isArray(x) &&
  [Object.prototype, null].includes(Object.getPrototypeOf(x));
const exact = (x, keys) => plain(x) && Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x, k));
const id = x => typeof x === "string" && /^syn-[a-z0-9-]{1,64}$/.test(x);
const integer = x => Number.isSafeInteger(x) && x >= 0;
function freeze(x) {
  if (x && typeof x === "object") { Object.values(x).forEach(freeze); Object.freeze(x); }
  return x;
}
function canonical(x) {
  if (Array.isArray(x)) return "[" + x.map(canonical).join(",") + "]";
  if (plain(x)) return "{" + Object.keys(x).sort().map(k => JSON.stringify(k) + ":" + canonical(x[k])).join(",") + "}";
  return JSON.stringify(x);
}
function normalized(text) {
  let value = ""; const starts = [], ends = [];
  for (let offset = 0; offset < text.length;) {
    const char = String.fromCodePoint(text.codePointAt(offset)), end = offset + char.length;
    const next = char.normalize("NFKD").replace(/[\u0300-\u036f\u200b-\u200d\ufeff]/g, "")
      .replace(/\u00df/g, "ss").replace(/[\u201c\u201d\u201e]/g, '"')
      .replace(/[\u2018\u2019']/g, "").toLowerCase();
    for (let i = 0; i < next.length; i++) { starts.push(offset); ends.push(end); }
    value += next; offset = end;
  }
  return { value, starts, ends };
}
const locales = ["nl", "en", "de"];
module.exports = { plain, exact, id, integer, freeze, canonical, normalized, locales };
