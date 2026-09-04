// Read-only inventory. This tool cannot repair history or execute migration SQL.
const fs=require("fs"),path=require("path"),crypto=require("crypto"),{execFileSync}=require("child_process");
const root=path.resolve(__dirname,"../.."),git=process.env.FMZ_GIT||"git";
const sha=bytes=>crypto.createHash("sha256").update(bytes).digest("hex");
const gitRead=args=>execFileSync(git,args,{cwd:root,windowsHide:true,maxBuffer:10000000});
const files=gitRead(["ls-files","supabase/migrations"]).toString().trim().split("\n").filter(f=>f.endsWith(".sql"));
const local=files.map(file=>{
  const bytes=gitRead(["show","HEAD:"+file]),sql=bytes.toString("utf8"),match=path.basename(file).match(/^(\d+)_(.*)\.sql$/);
  const objects=[...sql.matchAll(/^\s*(?:create\s+(?:or\s+replace\s+)?(?:table\s+(?:if\s+not\s+exists\s+)?|function\s+)|alter\s+table\s+(?:if\s+exists\s+)?)([\w.]+)/gim)].map(m=>m[1]);
  return{file,local_id:match[1],name:match[2],bytes:bytes.length,sha256:sha(bytes),
    lf_trim_sha256:sha(sql.replace(/\r\n/g,"\n").trim()),object_candidates:[...new Set(objects)].sort()};
});
const query=`select jsonb_build_object(
 'history',(select jsonb_agg(jsonb_build_object('version',version,'name',name,
 'statement_count',cardinality(statements),
 'sha256',encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex'),
 'lf_trim_sha256',encode(sha256(convert_to(btrim(replace(array_to_string(statements,E'\\n'),E'\\r\\n',E'\\n'),E' \\t\\r\\n'),'UTF8')),'hex')) order by version) from supabase_migrations.schema_migrations),
 'objects',(select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',c.relname,'type',c.relkind,'rls',c.relrowsecurity))
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','ai_private','legacy_auth_private') and c.relkind in ('r','p')),
 'functions',(select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',p.proname,'identity',pg_get_function_identity_arguments(p.oid),'definition_sha256',encode(sha256(convert_to(pg_get_functiondef(p.oid),'UTF8')),'hex')))
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','ai_private','legacy_auth_private') and p.prokind='f')
 ) as inventory;`;
if(!process.env.FMZ_PYTHON)throw new Error("FMZ_PYTHON_required");
const result=JSON.parse(execFileSync(process.env.FMZ_PYTHON,[path.join(__dirname,"phase6d0-staging-query.py")],{input:query,encoding:"utf8",windowsHide:true,timeout:60000,maxBuffer:3000000}));
if(!result.ok)throw new Error("read_only_inventory_failed");
const live=result.rows[0].inventory,duplicates=local.filter(f=>local.filter(other=>other.local_id===f.local_id).length>1).map(f=>f.local_id);
const migrations=local.map(file=>{
  const row=live.history.find(h=>h.name===file.name),exact=row?.statement_count===1&&row.sha256===file.sha256;
  const normalized=row?.statement_count===1&&row.lf_trim_sha256===file.lf_trim_sha256;
  const evidence=file.object_candidates.map(object=>{
    const [schema,name]=object.includes(".")?object.split("."):["public",object];
    return{object,present:live.objects.some(o=>o.schema===schema&&o.name===name)||live.functions.some(o=>o.schema===schema&&o.name===name)};
  });
  return{...file,remote_id:row?.version||null,remote_sha256:row?.sha256||null,remote_statement_count:row?.statement_count||0,
    classification:exact||normalized?1:5,classification_label:exact?"same SQL byte-exact":normalized?"same SQL after line-ending/outer-whitespace normalization":"execution identity not sufficiently proven",
    duplicate_version_conflict:duplicates.includes(file.local_id),duplicate_classification:duplicates.includes(file.local_id)?4:null,
    canonical_id:exact||normalized?row.version:null,current_object_presence:evidence,
    current_definitions_prove_historical_execution:false,
    required_action:exact&&file.local_id===row.version?"none":exact||normalized?"identity candidate proven; defer rename until full dependency/history blockers resolved":"recover and review complete historical baseline/evolution evidence; do not replay or mark applied",
    repair_executed:false,sql_reexecuted:false};
});
const after=JSON.parse(execFileSync(process.env.FMZ_PYTHON,[path.join(__dirname,"phase6d0-staging-query.py")],{input:query,encoding:"utf8",windowsHide:true,timeout:60000,maxBuffer:3000000}));
if(!after.ok)throw new Error("after_inventory_failed");
const report={target:"mokxyyullfhkfalopbzd",git_head:gitRead(["rev-parse","HEAD"]).toString().trim(),local_count:local.length,remote_count:live.history.length,
  before_history:live.history,after_history:after.rows[0].inventory.history,migrations,
  live_tables:live.objects,live_function_definition_hashes:live.functions,
  object_inventory_scope:"Table/function name candidates, table RLS and live function hashes; not an exhaustive SQL parser or historical semantic equivalence proof",
  two_read_history_equal:JSON.stringify(live.history)===JSON.stringify(after.rows[0].inventory.history),
  duplicate_versions:[...new Set(duplicates)],history_changed:false,migration_sql_executed:false,
  full_history_synchronized:false,empty_database_rebuild:"BLOCKED: Git lacks CREATE TABLE baselines for profiles, coach_workspaces, user_settings and entitlements",
  broad_db_push_allowed:false};
if(process.argv.includes("--write-manifest")){
  fs.writeFileSync(path.join(root,"docs/PROJECT_MIGRATION_RECONCILIATION_MANIFEST.json"),JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({local:report.local_count,remote:report.remote_count,same_sql:migrations.filter(m=>m.classification===1).length,uncertain:migrations.filter(m=>m.classification===5).length,history_unchanged:report.two_read_history_equal,full_history_synchronized:false}));
}else console.log(JSON.stringify(report,null,2));
