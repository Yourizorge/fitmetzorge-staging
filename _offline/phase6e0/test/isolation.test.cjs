"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");
const root = path.resolve(__dirname, "../../..");
const directory = path.resolve(__dirname, "..");
const frozen = "bc6308fbf0f914b04c7faa711219d9ae46e9cbe3";
const git = (...args) => execFileSync("git", args, { cwd: root, encoding: "utf8", windowsHide: true }).trim();
const allowed = file => file.startsWith("docs/") || file.startsWith("_offline/phase6e0/");
const coreNames = ["engine.cjs", "state.cjs", "retention.cjs", "corpus.cjs"];
test("all tracked non-documentation frozen files unchanged, including Edge and migrations", () => {
  assert.equal(git("diff", "--name-only", frozen, "--", ".", ":(exclude)docs/**", ":(exclude)_offline/**"), "");
});
test("all additions/changes are restricted to documents and this offline package", () => {
  const changed = git("diff", "--name-only", frozen).split("\n").filter(Boolean);
  const untracked = git("ls-files", "--others", "--exclude-standard").split("\n").filter(Boolean);
  assert.ok([...changed, ...untracked].every(allowed));
});
test("no frozen runtime source references or imports the offline package", () => {
  const files = git("ls-tree", "-r", "--name-only", frozen).split("\n")
    .filter(file => !file.startsWith("docs/") && /\.(?:html|js|cjs|ts|tsx|json|ya?ml)$/.test(file));
  assert.ok(files.length > 50);
  for (const file of files) {
    assert.doesNotMatch(fs.readFileSync(path.join(root, file), "utf8"), /_offline|phase6e0\/|phase6e0\.safety/);
  }
});
test("Node-only guard rejects a browser context before requiring anything", () => {
  assert.throws(() => vm.runInNewContext(fs.readFileSync(path.join(directory, "engine.cjs"), "utf8"),
    { window: {}, require() { throw new Error("unexpected_import"); } }), /offline_node_only/);
});
test("private package has no dependencies or runtime integration scripts", () => {
  const pkg = require("../package.json");
  assert.equal(pkg.private, true);
  assert.deepEqual(pkg.dependencies || {}, {});
  assert.deepEqual(pkg.devDependencies || {}, {});
  assert.deepEqual(Object.keys(pkg.scripts), ["test"]);
  for (const name of coreNames) {
    const source = fs.readFileSync(path.join(directory, name), "utf8");
    assert.doesNotMatch(source, /\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|setTimeout|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
    for (const match of source.matchAll(/require\("([^"]+)"\)/g)) {
      assert.match(match[1], /^\.\/(?:engine\.cjs|contract\.json|rules\.json|copy\.json|context-hints\.json|fixture-seeds\.json)$/);
    }
  }
});
test("core works with only allowlisted local modules, without network, storage, clock or secrets", () => {
  const context = vm.createContext({ process: { versions: { node: "offline-test" } } });
  vm.runInContext("globalThis.Date = undefined; Math.random = () => { throw Error('random_forbidden'); }; globalThis.structuredClone = x => JSON.parse(JSON.stringify(x));", context);
  const cache = new Map();
  function load(name) {
    assert.match(name, /^\.\/(?:engine\.cjs|state\.cjs|retention\.cjs|corpus\.cjs|contract\.json|rules\.json|copy\.json|context-hints\.json|fixture-seeds\.json)$/);
    if (cache.has(name)) return cache.get(name);
    const source = fs.readFileSync(path.join(directory, name), "utf8");
    if (name.endsWith(".json")) {
      const result = vm.runInContext("(" + source + ")", context);
      cache.set(name, result);
      return result;
    }
    const module = { exports: {} };
    vm.runInContext("(function(require,module,exports) {" + source + "\n})", context)(load, module, module.exports);
    cache.set(name, module.exports);
    return module.exports;
  }
  context.engine = load("./engine.cjs");
  context.states = load("./state.cjs");
  context.retention = load("./retention.cjs");
  context.corpus = load("./corpus.cjs");
  const output = vm.runInContext(`(() => {
    const samples = corpus.corpus();
    const results = samples.map(sample => engine.classify({
      contract_version: engine.contract.version, synthetic_only: true,
      text: sample.text, locale: sample.locale, availability: "available",
      context: { timing: "unspecified", subject: "unspecified" }
    }));
    const state = states.createState("syn-isolated");
    const changed = states.transition(state, { type: "signal", subject_id: state.subject_id,
      request_id: "syn-request", expected_revision: 0, at_ms: 1, assessment: results[0] });
    return JSON.stringify({ count: results.length, valid: results.every(engine.validateAssessment),
      revision: changed.state.revision, retention: retention.retentionPlan([], 0).storage_or_cleanup_performed });
  })()`, context, { timeout: 2000 });
  assert.deepEqual(JSON.parse(output), { count: 360, valid: true, revision: 1, retention: false });
});
