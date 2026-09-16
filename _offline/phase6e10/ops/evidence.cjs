const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),read=p=>JSON.parse(fs.readFileSync(path.join(root,p))),temp=p=>read("supabase/.temp/"+p);
const git=(...a)=>cp.execFileSync("git",a,{cwd:root,maxBuffer:60000000}),sha=b=>crypto.createHash("sha256").update(b).digest("hex");
const head=git("rev-parse","HEAD").toString().trim(),before=temp("phase6e10-before.json"),after=temp("phase6e10-after.json");
const local=temp("phase6e10-local.json"),live=temp("phase6e10-live.json"),fresh=temp("phase6e10-fresh.json"),publication=temp("phase6e10-publication.json"),reg=temp("phase6e10-regressions.json");
const localUi=temp("phase6e10-browser-local-ui/report.json"),publishedUi=temp("phase6e10-browser-published/report.json");
for(const r of [local,live,fresh,publication,localUi,publishedUi])assert.equal(r.pass,true);
assert.equal(after.all_existing_unchanged,true);assert.deepEqual([...before.tables].sort((a,b)=>a.name.localeCompare(b.name)),[...after.tables].sort((a,b)=>a.name.localeCompare(b.name)));assert.equal(reg.counts.fail,0);
const files=git("ls-files").toString().trim().split(/\r?\n/).filter(p=>p.startsWith("_offline/phase6e10/")||p.startsWith("coach-source-demo/")||/supabase\/migrations\/.*phase6e10/.test(p));
const source=files.map(file=>({file,blob:git("rev-parse","HEAD:"+file).toString().trim(),sha256:sha(git("show","HEAD:"+file)),checkout_sha256:sha(fs.readFileSync(path.join(root,file)))}));
const browser=r=>({pass:r.pass,checks:r.checks,layouts:r.layouts,physical_phone:r.physical_phone,password_login_tested:r.password_login_tested,standard_auth_sessions:r.standard_auth_sessions,errors:r.errors});
const out={status:"TECHNICAL PASS / READY FOR OWNER REVIEW",scope:"synthetic staging only",verified_at:new Date().toISOString(),source_commit:head,
owner_accepted:false,phase6e_complete:false,phase6e11_started:false,production_touched:false,external_ai_calls:0,new_emails:0,
source,protected_baseline:read("docs/PHASE6E9_FREEZE_EVIDENCE.json").baseline,protected_files:243,existing_runtime_assets:80,
tests:{regressions:reg.counts,superseded_scope_gate:1,local_groups:local.checks,hosted_groups:live.checks,local_browser:browser(localUi),published_browser:browser(publishedUi),fresh:{head:fresh.head,pass:fresh.pass,local_groups:fresh.local_groups,regressions:fresh.regressions,full_supabase_stack:false,auth_stubs:true}},
data:{unchanged:true,tables:after.tables,existing_migrations_unchanged:34,migrations:after.migrations},
security:read("_offline/phase6e10/evidence/security.json"),
publication:{head:publication.head,pass:publication.pass,assets:publication.assets,private:publication.private},
limitations:["Synthetic authority is not authenticated real trainer-source provenance.","Manually selected health fixtures are not medical recognition.","Observation tests are not recognition successes.","Local Auth stubs are not a full Supabase stack.","Phone/tablet viewports are emulated; owner passwords not tested.","Expired access is not automatic physical cleanup.","Restore conservatively rejects multiple matching rules.","Historic failed/loose runs are not final proof."]};
fs.writeFileSync(path.join(root,"docs/PHASE6E10_EVIDENCE.json"),JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({source_commit:head,source_files:source.length,regressions:reg.counts,local:local.checks.length,hosted:live.checks.length,local_browser:localUi.checks.length,published_browser:publishedUi.checks.length,assets:publication.assets.length,private404:publication.private.length}));
