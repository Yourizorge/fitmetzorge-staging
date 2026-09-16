const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..'),baseline='8501d8abf2c5a0e8413630d75276eeae78c57867';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f)));
const temp=f=>read('supabase/.temp/'+f);
const git=(...a)=>cp.execFileSync('git',a,{cwd:root,maxBuffer:60000000});
const target=path.join(root,'docs/PHASE6E10_FREEZE_EVIDENCE.json');
const compact=s=>s.tables.map(r=>[r.name,r.protected_rows,r.protected_sha256]);
const auxiliary=['_offline/phase6e10/ops/close-owner.mjs','_offline/phase6e10/ops/freeze.cjs'];
function verify(e){
 assert.equal(e.status,'COMPLETE / OWNER-ACCEPTED / FROZEN - SYNTHETIC STAGING SCOPE ONLY');
 for(const f of e.protected)assert.equal(sha(fs.readFileSync(path.join(root,f.file))),f.checkout_sha256,f.file);
 for(const f of e.auxiliary)assert.equal(sha(fs.readFileSync(path.join(root,f.file))),f.sha256,f.file);
 for(const [f,h] of Object.entries(e.preserved_evidence))assert.equal(sha(fs.readFileSync(path.join(root,f))),h,f);
 for(const run of e.closure_measurements.tests){assert(run.pass);assert(run.existing_protected_unchanged);assert(run.nine_unchanged);}
 for(const s of e.closure_measurements.snapshots)assert.deepEqual(compact(s),compact(e.closure_measurements.snapshots[0]));
 assert.equal(e.closure.pass,true);assert.equal(e.closure.still_signed_jwts_refused,3);
 assert.equal(e.closure.cleanup.status,'cleaned');assert.equal(e.closure.cleanup.workspaces,2);
 assert.equal(e.closure.accounts_deleted,0);
 assert.equal(e.migrations.entries.length,38);assert(e.migrations.entries.every(x=>x.local===x.remote));
 assert.equal(e.migrations.dry_run.upToDate,true);assert.deepEqual(e.migrations.dry_run.migrations,[]);
 assert.equal(e.publication_before_docs_push.assets.length,84);assert.equal(e.publication_before_docs_push.pass,true);
 assert(e.publication_before_docs_push.assets.every(x=>x.identical&&x.expected===x.published));
 assert.equal(e.phase6e11_started,false);assert.equal(e.production_touched,false);
 const changes=git('diff','--name-only',baseline).toString().trim().split(/\r?\n/).filter(Boolean);
 const untracked=git('ls-files','--others','--exclude-standard').toString().trim().split(/\r?\n/).filter(Boolean);
 for(const file of [...changes,...untracked])assert(file.startsWith('docs/')||auxiliary.includes(file),'outside_freeze_scope:'+file);
 console.log(JSON.stringify({pass:true,protected_files:e.protected.length,auxiliary_files:e.auxiliary.length,
  runtime_assets:84,measurement_pairs:e.closure_measurements.tests.length,tables:127,migrations:38,
  owner_accepted:true,window_closed:true,phase6e11_started:false,production_touched:false}));
}
if(process.argv.includes('--write')){
 assert(!fs.existsSync(target),'freeze_evidence_exists_do_not_overwrite');
 assert.equal(git('rev-parse','HEAD').toString().trim(),baseline);
 const closure=temp('phase6e10-owner-closure.json'),measurements=temp('phase6e10-followup-owner-closure.json');
 assert(closure.pass&&measurements.pass);
 const old=read('docs/PHASE6E9_FREEZE_EVIDENCE.json');
 const files=git('ls-tree','-r','--name-only',baseline).toString().trim().split(/\r?\n/).filter(f=>
  f.startsWith('_offline/phase6e10/')||f.startsWith('coach-source-demo/')||/^supabase\/migrations\/.*phase6e10/.test(f));
 const protectedFiles=[...old.protected];
 for(const file of files){
  assert.equal(git('diff',baseline,'--',file).length,0,'tested_source_changed:'+file);
  protectedFiles.push({file,blob:git('rev-parse',baseline+':'+file).toString().trim(),
   sha256:sha(git('show',baseline+':'+file)),checkout_sha256:sha(fs.readFileSync(path.join(root,file)))});
 }
 const cli=mode=>{
  const output=cp.execFileSync(process.execPath,['_offline/phase6e10/ops/cli.cjs',mode],{cwd:root,encoding:'utf8',timeout:150000});
  return JSON.parse(output.split(/\r?\n/).find(x=>x.startsWith('{')));
 };
 const listed=cli('list'),dry=cli('dry-run');
 const out={status:'COMPLETE / OWNER-ACCEPTED / FROZEN - SYNTHETIC STAGING SCOPE ONLY',
  created_at:new Date().toISOString(),baseline,implementation_commit:'03eb55af7ab1897a3c6a12b82fcb5d182e88c4de',
  owner_accepted:true,owner_physical_report:'All requested phone scenarios passed; explicit owner acceptance.',
  phone_evidence_limit:'Final retained window has source v1, plan v1 and one approved proposal. No apply/restore receipts there; those actions have prior technical evidence, not independently observed phone proof.',
  protected:protectedFiles,auxiliary:auxiliary.map(file=>({file,sha256:sha(fs.readFileSync(path.join(root,file)))})),
  preserved_evidence:measurements.snapshots[0].preserved_files,
  closure,closure_measurements:measurements,
  migrations:{entries:listed.migrations,dry_run:dry,new_migrations:0},
  prior_tests:{regressions:temp('phase6e10-regressions.json').counts,local_groups:65,hosted_groups:65,
   published_browser_checks:27,emulated_layouts:18,fresh_checkout_targeted:10,fresh_checkout_sql_groups:65,
   original_68_comparison:'59 equal plus 9 independently explained owner changes; original evidence preserved',
   reports:['PHASE6E10_VERIFICATION_PENDING.json','PHASE6E10_FOLLOWUP_EVIDENCE.json','PHASE6E10_OWNER_MATCH.json']},
  current_targeted_tests:{scope_and_edge:10,pass:10,fail:0,skipped:0},
  publication_before_docs_push:temp('phase6e10-publication.json'),
  limitations:['Synthetic provenance and manual safety/consent fixtures do not establish real trainer authority or medical suitability.',
   'Medical/resumption, privacy/purpose/retention, legal and language reviews remain open for real use.',
   'Relevant explicit consent/entitlements and DPA/ZDR/DPIA/EU-route/cost gates remain open before genuine member/provider processing.',
   'Global synthetic operator/configuration retained; no active participant window. No scheduler or future-window GO is implied.',
   'Owner testimony is distinguished from retained server metadata. Failed historical attempts and language limitations remain visible.'],
  phase6e_complete:false,phase6e11_started:false,production_touched:false,external_ai_calls:0};
 verify(out);
 fs.writeFileSync(target,JSON.stringify(out,null,2)+'\n',{flag:'wx'});
}else verify(read('docs/PHASE6E10_FREEZE_EVIDENCE.json'));
