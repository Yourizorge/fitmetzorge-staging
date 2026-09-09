"use strict";
// Explicit operator-run verification helper, never imported by the offline model.
const fs = require("node:fs"), path = require("node:path"), cp = require("node:child_process");
const crypto = require("node:crypto"), assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../../..");
const baseline = "f3ab33c6553c2d5dd3fc06518c150bd474fb6159";
const base = "https://yourizorge.github.io/fitmetzorge-staging/";
const git = (...args) => cp.execFileSync("git", args, { cwd: root, windowsHide: true, maxBuffer: 30000000 });
const hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const list = (...args) => git(...args).toString().trim().split("\n").filter(Boolean);
const phase = process.argv[2];
assert(["before", "after-source", "after-freeze"].includes(phase), "explicit verification phase required");
assert.equal(git("remote", "get-url", "origin").toString().trim(), "https://github.com/Yourizorge/fitmetzorge-staging.git");
assert.equal(git("branch", "--show-current").toString().trim(), "main");
const head = git("rev-parse", "HEAD").toString().trim();
const runtimeFile = f => (!f.includes("/") && /\.(html|css|js|png)$/.test(f)) ||
  (f.startsWith("assets/") && !/(-check|-benchmark|\.test)\.(cjs|js)$/.test(f));
const files = list("ls-tree", "-r", "--name-only", baseline).filter(runtimeFile);
assert.deepEqual(list("ls-tree", "-r", "--name-only", "HEAD").filter(runtimeFile), files);
assert.equal(files.length, 60);
const changed = list("diff", "--name-only", baseline);
assert(changed.every(f => f.startsWith("docs/") || f.startsWith("_offline/phase6e1/")), "authorized scope only");
(async () => {
  const assets = [];
  for (const file of files) {
    const expected = git("cat-file", "blob", baseline + ":" + file);
    assert(git("cat-file", "blob", "HEAD:" + file).equals(expected), "Git runtime " + file);
    const local = fs.readFileSync(path.join(root, file));
    assert.equal(local.length, fs.statSync(path.join(root, file)).size);
    assert.equal(git("hash-object", "--path=" + file, file).toString().trim(),
      git("rev-parse", baseline + ":" + file).toString().trim(), "working runtime " + file);
    const response = await fetch(base + file + "?6e1=" + head + "-" + phase);
    assert.equal(response.status, 200, file);
    const actual = Buffer.from(await response.arrayBuffer());
    assert(actual.equals(expected), "published runtime " + file);
    if (/\.(js|html)$/.test(file)) assert.doesNotMatch(actual.toString(), /_offline|phase6e[01]\./, file);
    assets.push({ file, bytes: expected.length, sha256: hash(expected), working_sha256: hash(local) });
  }
  const privateFiles = [...new Set([...list("ls-files", "_offline", "_tests"),
    ...list("ls-files", "--others", "--exclude-standard", "_offline", "_tests")])].sort();
  const probes = [];
  for (const file of privateFiles) {
    const response = await fetch(base + file + "?6e1=" + head + "-" + phase);
    await response.arrayBuffer();
    assert.equal(response.status, 404, "private source " + file);
    probes.push({ file, status: 404 });
  }
  const result = { phase, checked_at: new Date().toISOString(), head, runtime_baseline: baseline,
    target: base, assets, private_source_probes: probes, runtime_byte_identical: true,
    offline_isolated: true, production_touched: false };
  const output = path.join(root, "supabase/.temp/phase6e1-acceptance-" + phase + ".json");
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
  console.log(JSON.stringify({ head, phase, runtime: assets.length, private_404: probes.length, pass: true, output }));
})().catch(error => { console.error(error); process.exitCode = 1; });
