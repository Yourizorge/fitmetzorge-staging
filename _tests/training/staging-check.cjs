// Fixed staging only. Fingerprints expose counts/hashes, never member fields.
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),python="C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
function query(sql){
 const r=JSON.parse(cp.execFileSync(python,[path.join(root,"supabase/tests/phase6d0-staging-query.py")],{input:sql,encoding:"utf8",windowsHide:true,maxBuffer:10000000}));
 assert(r.ok,r.error);return r.rows;
}
const mode=process.argv[2];assert(["before","after","sql"].includes(mode));
if(mode==="sql"){
 const sql=fs.readFileSync(path.join(__dirname,"sql.test.sql"),"utf8");
 assert(sql.trim().endsWith("rollback;")&&sql.startsWith("-- Controlled synthetic fixtures only;"));
 const result=query(sql);
 fs.writeFileSync(path.join(root,"supabase/.temp/training-sql-live.json"),JSON.stringify(result,null,2));console.log(JSON.stringify(result)); 
}else{
 const tables=query("select schemaname,tablename from pg_tables where schemaname in ('public','ai_private','legacy_auth_private') or (schemaname='auth' and tablename='users') order by 1,2;");
 const selects=tables.map(({schemaname:s,tablename:t})=>{
  assert(/^[a-z0-9_]+$/.test(s+t));
  const excluded=t==="training_plan_exercises"?["set_targets","superset_id","superset_rest_seconds"]:t==="member_app_preferences"?["training_effort_mode","training_timer_enabled"]:[];
  const row="to_jsonb(r)"+excluded.map(c=>" - '"+c+"'").join("");
  return "select '"+s+"."+t+"' as table_name,count(*)::integer as rows,md5(coalesce(string_agg(h,'' order by h),'')) as fingerprint from (select md5(("+row+")::text) h from "+s+"."+t+" r) x";
 });
 const result=query("begin read only;"+selects.join(" union all ")+";commit;");
 const output={target:"mokxyyullfhkfalopbzd",checked_at:new Date().toISOString(),mode,tables:result};
 if(mode==="after"){
  const before=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/training-member-before.json"),"utf8"));
  output.changed=result.filter(r=>JSON.stringify(r)!==JSON.stringify(before.tables.find(b=>b.table_name===r.table_name)));
  output.existing_data_unchanged=output.changed.length===0;
  const synthetic=query("select count(*)::integer as remaining from auth.users where id in ('660e1000-0000-4000-8000-000000000001','660e1000-0000-4000-8000-000000000002');");
  output.synthetic_remaining=synthetic[0].remaining;assert.equal(output.synthetic_remaining,0);
 }
 fs.writeFileSync(path.join(root,"supabase/.temp/training-member-"+mode+".json"),JSON.stringify(output,null,2));
 console.log(JSON.stringify({target:output.target,tables:result.length,rows:result.reduce((n,t)=>n+t.rows,0),unchanged:output.existing_data_unchanged,changed:output.changed,synthetic_remaining:output.synthetic_remaining}));
 if(mode==="after")assert(output.existing_data_unchanged,"compare concurrent changes explicitly before proceeding");
}
