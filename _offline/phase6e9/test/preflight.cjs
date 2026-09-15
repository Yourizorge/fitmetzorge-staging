"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),crypto=require("node:crypto"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../../.."),phase=process.argv[2];
if(!["before","after"].includes(phase))throw Error("explicit_phase_required");
const python="C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
function query(sql){
 assert(/^select\b/i.test(sql.trim()));
 const r=JSON.parse(cp.execFileSync(python,[path.join(root,"supabase/tests/phase6d0-staging-query.py")],{input:sql,encoding:"utf8",windowsHide:true,timeout:60000,maxBuffer:3000000}));
 if(!r.ok)throw Error(r.error||"preflight_query_failed");return r.rows;
}
const dir=path.join(root,"supabase/.temp"),beforePath=path.join(dir,"phase6e9-preflight-before.json");
const names=phase==="before"?query("select n.nspname as schema,c.relname as name from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname in ('public','ai_private','legacy_auth_private') and c.relkind='r' order by 1,2;"):JSON.parse(fs.readFileSync(beforePath)).tables.map(x=>({schema:x.schema,name:x.name}));
for(const t of names)assert(/^[a-z0-9_]+$/.test(t.schema)&&/^[a-z0-9_]+$/.test(t.name));
const tables=[];
for(const t of names){
 const q="select count(*)::int as rows,encode(sha256(convert_to(coalesce(string_agg(h,',' order by h),''),'UTF8')),'hex') as sha256 from (select encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') as h from "+t.schema+"."+t.name+" t) s;";
 const [v]=query(q);tables.push({...t,...v});
}
const migrations=query("select version,name,cardinality(statements) as statement_count,encode(sha256(convert_to(array_to_string(statements,E'\\n'),'UTF8')),'hex') as statements_sha256 from supabase_migrations.schema_migrations order by version;");
const files=fs.readdirSync(path.join(root,"supabase/migrations")).filter(x=>x.endsWith(".sql"));
const canonical=files.map(file=>{const [_,version,name]=/^(\d+)_(.+)\.sql$/.exec(file);return {file,version,name,sha256:crypto.createHash("sha256").update(fs.readFileSync(path.join(root,"supabase/migrations",file))).digest("hex")};});
const pending=canonical.filter(x=>!migrations.some(m=>m.version===x.version));
assert(migrations.every(m=>canonical.some(f=>f.version===m.version&&f.name===m.name)));
assert.equal(new Set(canonical.map(x=>x.version)).size,canonical.length);
if(phase==="before")assert(pending.every(x=>x.name==="phase6e9_synthetic_authorization"));
const result={phase,at:new Date().toISOString(),project:"mokxyyullfhkfalopbzd",tables,migrations,canonical,pending:pending.map(x=>x.file)};
if(phase==="after"){const before=JSON.parse(fs.readFileSync(beforePath));result.changed_existing=tables.filter((x,i)=>x.rows!==before.tables[i].rows||x.sha256!==before.tables[i].sha256);}
fs.writeFileSync(path.join(dir,"phase6e9-preflight-"+phase+".json"),JSON.stringify(result,null,2)+"\n");
console.log(JSON.stringify({phase,tables:tables.length,live_migrations:migrations.length,pending:result.pending,changed_existing:result.changed_existing?.map(x=>x.schema+"."+x.name)}));
