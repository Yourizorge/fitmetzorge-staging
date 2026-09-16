import test from "node:test";
import assert from "node:assert/strict";
import cp from "node:child_process";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {copy} from "../../../coach-source-demo/strings.mjs";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../../..");
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,encoding:"utf8"}).trim().split(/\r?\n/).filter(Boolean);
test("6E10 approved scope replaces historical 6E9 package-only gate",()=>{
 const files=[...git("diff","--name-only","53b7d36a9dd45ba2c6f0326f5f563304f2e5583f"),...git("ls-files","--others","--exclude-standard")];
 for(const file of files)assert(/^(docs\/|_offline\/phase6e10\/|coach-source-demo\/|supabase\/migrations\/(20260915104711_phase6e10_sources_managed_windows|20260916071416_phase6e10_source_reference_indexes|20260916072203_phase6e10_strict_command_versions|20260916073923_phase6e10_api_conflict_sqlstate)\.sql$)/.test(file),file);
});
test("NL EN DE concept keys complete, no medical authorization",()=>{
 for(const lang of ["en","de"])assert.deepEqual(Object.keys(copy[lang]).sort(),Object.keys(copy.nl).sort());
 for(const c of Object.values(copy))for(const value of Object.values(c))assert.equal(typeof value,"string");
});
