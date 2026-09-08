"use strict";
const test = require("node:test"), assert = require("node:assert/strict"), fs = require("node:fs"),
  path = require("node:path"), vm = require("node:vm"), crypto = require("node:crypto"), cp = require("node:child_process");
const root = path.resolve(__dirname, "../../.."), directory = path.resolve(__dirname, "..");
const base = "abfea682aac53d5e32f4962d6917aa958bd09cb4", frozen = "bc6308fbf0f914b04c7faa711219d9ae46e9cbe3";
const git = (...a) => cp.execFileSync("git", a, { cwd: root, encoding: "utf8", windowsHide: true }).trim();
const core = ["common.cjs", "context.cjs", "flow.cjs", "analysis.cjs", "retention.cjs"];
test("I01 exact staging target and changes restricted to docs and new 6E-1", () => {
  assert.equal(git("remote", "get-url", "origin"), "https://github.com/Yourizorge/fitmetzorge-staging.git");
  assert.equal(git("branch", "--show-current"), "main");
  assert.equal(git("diff", "--name-only", base, "--", ".", ":(exclude)docs/**", ":(exclude)_offline/phase6e1/**"), "");
  const additions = git("ls-files", "--others", "--exclude-standard").split("\n").filter(Boolean);
  assert.ok(additions.every(f => f.startsWith("docs/") || f.startsWith("_offline/phase6e1/")));
});
test("I01 all 23 frozen 6E-0 files retain original Git identities and working bytes", () => {
  const receipt = require("../../../docs/PHASE6E0_FREEZE_EVIDENCE.json");
  assert.equal(receipt.offline_sources.length, 23);
  assert.equal(git("rev-parse", "HEAD:_offline/phase6e0"), receipt.offline_tree);
  for (const f of receipt.offline_sources) {
    assert.equal(git("rev-parse", "HEAD:" + f.file), f.git_blob, f.file);
    const bytes = fs.readFileSync(path.join(root, f.file));
    assert.equal(bytes.length, f.bytes, f.file);
    assert.equal(crypto.createHash("sha256").update(bytes).digest("hex"), f.sha256, f.file);
  }
});
test("I01 frozen app/Edge/migrations/workflows and D1-D12 unchanged", () => {
  assert.equal(git("diff", "--name-only", frozen, "--", ".", ":(exclude)docs/**", ":(exclude)_offline/**"), "");
  for (const f of ["docs/PHASE6E0_OWNER_DECISIONS.md", "docs/PACKAGE6D_CORRECTED_FREEZE_AND_6E_OWNER_DECISIONS.md",
    "docs/PHASE6E0_FREEZE_RECEIPT.md", "docs/PHASE6E0_FREEZE_EVIDENCE.json"]) {
    assert.equal(git("diff", base, "--", f), "");
  }
});
test("I01 no frozen runtime source imports or embeds either offline package", () => {
  const files = git("ls-tree", "-r", "--name-only", frozen).split("\n").filter(f =>
    !f.startsWith("docs/") && /\.(?:html|js|cjs|ts|tsx|json|ya?ml)$/.test(f));
  assert.ok(files.length > 50);
  for (const f of files) assert.doesNotMatch(fs.readFileSync(path.join(root, f), "utf8"), /_offline|phase6e[01]\./, f);
});
test("I02 Node-only guards precede any module import", () => {
  for (const name of core) assert.throws(() => vm.runInNewContext(fs.readFileSync(path.join(directory, name), "utf8"),
    { window: {}, require() { throw Error("unexpected_import"); } }), /offline_node_only/);
});
test("I02 core has local allowlisted imports and no IO, clock, env, random, scheduler or provider", () => {
  const pkg = require("../package.json");
  assert.equal(pkg.private, true);
  assert.deepEqual(pkg.dependencies || {}, {}); assert.deepEqual(pkg.devDependencies || {}, {});
  assert.deepEqual(Object.keys(pkg.scripts), ["test"]);
  for (const name of core) {
    const src = fs.readFileSync(path.join(directory, name), "utf8");
    assert.doesNotMatch(src, /\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|setTimeout|Date)\b|process\.env|Math\.random|\bimport\s*\(/);
    for (const m of src.matchAll(/require\("([^"]+)"\)/g)) assert.match(m[1],
      /^(?:\.\/(?:common|context|flow)\.cjs|\.\/(?:contract|content-contract)\.json|\.\.\/phase6e0\/(?:rules|context-hints|copy|warning-recovery-proposal)\.json)$/);
  }
});
test("I02 complete examples run in memory without network, clock, storage or environment", () => {
  const context = vm.createContext({ process: { versions: { node: "synthetic" } } });
  vm.runInContext("globalThis.Date=undefined; Math.random=()=>{throw Error('random_forbidden')}", context);
  const allowed = new Set([...core, "contract.json", "content-contract.json", "test/helpers.cjs", "test/examples.cjs",
    "../phase6e0/rules.json", "../phase6e0/context-hints.json", "../phase6e0/copy.json", "../phase6e0/warning-recovery-proposal.json"]
    .map(f => path.resolve(directory, f)));
  const cache = new Map();
  function load(file) {
    assert.ok(allowed.has(file), file);
    if (cache.has(file)) return cache.get(file);
    const src = fs.readFileSync(file, "utf8");
    if (file.endsWith(".json")) {
      const data = vm.runInContext("(" + src + ")", context); cache.set(file, data); return data;
    }
    const module = { exports: {} };
    const localRequire = name => { assert.ok(name.startsWith(".")); return load(path.resolve(path.dirname(file), name)); };
    vm.runInContext("(function(require,module,exports){" + src + "\n})", context)(localRequire, module, module.exports);
    cache.set(file, module.exports); return module.exports;
  }
  context.examples = load(path.join(directory, "test/examples.cjs"));
  const output = vm.runInContext("JSON.stringify(examples.examples())", context, { timeout: 3000 });
  const results = JSON.parse(output);
  assert.equal(results.length, 5);
  assert.ok(results.every(r => r.before.observations.length && r.after.observations.length));
  assert.ok(results.every(r => r.after.medical_clearance === false && r.after.actions.length === 0));
});
test("I03 preregistration precedes implementation and expectations remain unchanged", () => {
  const f = "_offline/phase6e1/preregistered-cases.json";
  const prereg = git("log", "--diff-filter=A", "--format=%H", "--", f).split("\n")[0];
  assert.ok(prereg.startsWith("086a05f"));
  assert.equal(git("diff", prereg, "--", f, "docs/PHASE6E1_PREREGISTRATION.md"), "");
  const existed = git("ls-tree", "-r", "--name-only", prereg, "--", "_offline/phase6e1");
  assert.equal(existed, f);
  assert.equal(require("../preregistered-cases.json").cases.length, 42);
});
