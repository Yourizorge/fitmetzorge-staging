const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { audit, query, filename, expectedHash } = require("./phase6d0-migration-identity-check.cjs");
const bytes = fs.readFileSync(path.resolve(__dirname, "../migrations", filename));
function fixture() {
 const functions = [...bytes.toString("utf8").matchAll(
  /create or replace function public\.(\w+)\([\s\S]*?\bas \$fn\$([\s\S]*?)\$fn\$;/g
 )].map(m => ({ name: m[1], body: m[2] }));
 for (const name of ["fmz_current_profile_role","fmz_current_profile_trainer_id",
  "fmz_is_trainer","fmz_can_select_profile","fmz_can_access_workspace"]) functions.push({ name, body: "existing" });
 for (const f of functions) Object.assign(f, { security_definer: true, config: ["search_path=pg_catalog, pg_temp"] });
 return {
  files: [{ filename, bytes }],
  snapshot: { history: [{ version: "20260904105918", name: "phase6d0_legacy_authorization_gate",
   statement_count: 1, sha256: expectedHash }], functions }
 };
}
test("canonical file, bytes and body identity pass", () => {
 const f = fixture(), r = audit(f.files, f.snapshot);
 assert.equal(r.package_identity_pass, true);
 assert.equal(r.broad_db_push_allowed, true);
 assert.equal(r.function_body_checks.length, 8);
});
test("old Git version fails", () => {
 const f = fixture(); f.files[0].filename = filename.replace("20260904105918", "20260904093300");
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("duplicate old Git artifact fails", () => {
 const f = fixture(); f.files.push({filename: filename.replace("20260904105918", "20260904093300"), bytes});
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("CRLF conversion fails the exact byte gate", () => {
 const f = fixture(); f.files[0].bytes = Buffer.from(bytes.toString().replace(/\n/g, "\r\n"));
 assert.equal(audit(f.files, f.snapshot).checks.git_bytes_exact, false);
});
test("wrong live version fails", () => {
 const f = fixture(); f.snapshot.history[0].version = "20260904093300";
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("wrong history checksum fails", () => {
 const f = fixture(); f.snapshot.history[0].sha256 = "0".repeat(64);
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("changed live function body fails", () => {
 const f = fixture(); f.snapshot.functions[0].body += " ";
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("unsafe function search path fails", () => {
 const f = fixture(); f.snapshot.functions[0].config = ["search_path=public"];
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("missing history fails", () => {
 const f = fixture(); f.snapshot.history = [];
 assert.equal(audit(f.files, f.snapshot).package_identity_pass, false);
});
test("unrelated old drift blocks broad push, not package identity", () => {
 const f = fixture();
 f.files.push({filename: "20200101_old.sql", bytes: Buffer.from("select 1;")});
 f.snapshot.history.push({version: "20200102000000", name: "old"});
 const r = audit(f.files, f.snapshot);
 assert.equal(r.package_identity_pass, true);
 assert.equal(r.full_history_synchronized, false);
 assert.equal(r.broad_db_push_allowed, false);
});
test("duplicate historical versions block broad push", () => {
 const f = fixture();
 f.files.push({filename:"20200101_one.sql",bytes}, {filename:"20200101_two.sql",bytes});
 assert.deepEqual(audit(f.files, f.snapshot).duplicate_local_versions, ["20200101"]);
});
test("inspection uses SELECT metadata only", () => {
 assert.match(query, /^select /);
 assert.doesNotMatch(query, /\b(insert|update|delete|create|alter|drop|grant|revoke|call|execute)\b/i);
 assert.equal(query.split(";").filter(s => s.trim()).length, 1);
});
