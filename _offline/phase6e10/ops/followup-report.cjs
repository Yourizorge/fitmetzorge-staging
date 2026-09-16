"use strict";
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p))),temp=p=>read('supabase/.temp/'+p);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const match=read('docs/PHASE6E10_OWNER_MATCH.json');assert.equal(match.pass,true);
for(const [file,hash] of Object.entries(match.preserved_files))assert.equal(sha(fs.readFileSync(path.join(root,file))),hash,file);
const runs=['browser-published','owner-window'].map(label=>temp('phase6e10-followup-'+label+'.json'));
const browser=temp('phase6e10-browser-published/report.json'),owner=temp('phase6e10-owner-window.json'),publication=temp('phase6e10-publication.json');
for(const r of [...runs,browser,publication])assert.equal(r.pass,true);
assert.equal(owner.opened,true);assert.equal(browser.checks.length,27);assert.equal(browser.layouts.length,18);
assert.equal(new Date(owner.ends_at)-new Date(owner.starts_at)<=86400000,true);
const catalog=[],interned=new Map();
function intern(row){const key=JSON.stringify(row);if(!interned.has(key)){interned.set(key,catalog.length);catalog.push(row);}return interned.get(key);}
const packed=runs.map(run=>({label:run.label,started_at:run.started_at,finished_at:run.finished_at,pass:run.pass,
 events:run.events,tests:run.tests,snapshots:run.snapshots.map(s=>({at:s.at,table_refs:s.tables.map(intern),nine_table_refs:s.nine.map(intern),
 audit:s.audit,cron:s.cron,state:s.state,preserved_files_match:JSON.stringify(s.preserved_files)===JSON.stringify(match.preserved_files)}))}));
for(const run of runs)for(const t of run.tests){
 assert.equal(t.pass,true);assert.equal(t.existing_protected_unchanged,true);assert.equal(t.nine_unchanged,true);
 const before=run.snapshots[t.before],after=run.snapshots[t.after];assert.equal(before.tables.length,127);assert.equal(after.tables.length,127);
 assert.deepEqual(before.tables.map(r=>[r.name,r.protected_rows,r.protected_sha256]),after.tables.map(r=>[r.name,r.protected_rows,r.protected_sha256]));
}
const final=runs[1].snapshots.at(-1).state[0];assert.equal(final.active_windows,1);assert.equal(final.workspaces,2);assert.equal(final.temporary_controls,0);
const history=temp('phase6e10-browser-published-preflight-failed.json');assert.equal(history.pass,false);assert.equal(history.checks.length,0);
const files=['_offline/phase6e10/ops/followup.py','_offline/phase6e10/ops/followup-audit.mjs','_offline/phase6e10/ops/open-owner.mjs','_offline/phase6e10/test/live.mjs','_offline/phase6e10/test/browser.mjs'];
const out={status:'TECHNICAL PASS / READY FOR OWNER REVIEW',created_at:new Date().toISOString(),
 implementation_commit:'03eb55af7ab1897a3c6a12b82fcb5d182e88c4de',current_git_head:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),
 tested_files:files.map(file=>({file,sha256:sha(fs.readFileSync(path.join(root,file)))})),
 owner_match:match,original_baseline_overwritten:false,original_differences_preserved:true,
 measurement_format:'table_refs and nine_table_refs are zero-based indices into fingerprint_catalog; a shared boundary is after one test and before the next.',
 fingerprint_catalog:catalog,runs:packed,
 cleanup:{browser_test_window_cleaned:true,new_accounts_created:0,temporary_control_accounts_remaining:0,retained_synthetic_identities:3,
 generated_test_sessions_signed_out:true,owner_window_left_active:true,owner_workspaces_retained:2,physical_cleanup_on_expiry_automatic:false},
 owner_window:{opened:true,url:owner.url,starts_at:owner.starts_at,ends_at:owner.ends_at,expires_nl:owner.expires_nl,source_version:owner.source_version,source_hash:owner.source_hash},
 publication:{head:publication.head,pass:true,assets:publication.assets.length,old_assets:80,private404:publication.private.length},
 browser:{checks:browser.checks,layouts:browser.layouts,physical_phone:false,password_login_tested:false},
 historical_failed_attempt:{file:'supabase/.temp/phase6e10-browser-published-preflight-failed.json',sha256:sha(fs.readFileSync(path.join(root,'supabase/.temp/phase6e10-browser-published-preflight-failed.json'))),checks:0,reason:'Read-only initial measurement failed before synthetic operations; retained, not counted as pass.'},
 owner_accepted:false,phase6e11_started:false,production_touched:false,external_ai_calls:0,emails:0,
 limits:['Recorded operation-level write attribution and table fingerprints, not an unrestricted historical WAL audit.',
 'Synthetic sources and manually selected safety fixtures do not establish real trainer authority or medical reliability.',
 'Viewports are emulated; the physical owner phone retest and password entry remain open.',
 'Expiry denies server access; physical cleanup follows owner completion or a separate scoped cleanup after expiry.']};
fs.writeFileSync(path.join(root,'docs/PHASE6E10_FOLLOWUP_EVIDENCE.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({status:out.status,measurement_pairs:runs.reduce((n,r)=>n+r.tests.length,0),catalog_entries:catalog.length,owner_expiry:owner.expires_nl}));
