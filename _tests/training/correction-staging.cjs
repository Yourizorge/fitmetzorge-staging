const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."),python="C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",name="20260909215122_training_plan_effort_tracking.sql";
const read=f=>fs.readFileSync(path.join(root,f),"utf8"),out=(label,data)=>fs.writeFileSync(path.join(root,"supabase/.temp/training-correction-"+label+".json"),JSON.stringify(data,null,2));
function query(sql){const r=JSON.parse(cp.execFileSync(python,[path.join(root,"supabase/tests/phase6d0-staging-query.py")],{input:sql,encoding:"utf8",windowsHide:true,maxBuffer:20000000}));assert(r.ok,r.error);return r.rows;}
const mode=process.argv[2];assert(["before","after","sql-pre","sql-post","schema"].includes(mode));
if(mode.startsWith("sql")){
 let sql=read("_tests/training/correction.test.sql");assert(sql.trim().endsWith("rollback;"));
 if(mode==="sql-pre")sql=sql.replace("begin;",()=>"begin;\n"+read("supabase/migrations/"+name).replace(/\bbegin;\s*\n/,"").replace(/\bcommit;\s*$/,""));
 const result=query(sql);out(mode,result);console.log(JSON.stringify(result));
}else if(mode==="schema"){
 const f=query("begin read only;select prosrc,prosecdef,proconfig from pg_proc where oid='public.fmz_training_save_workout_v2(uuid,uuid,text,text,integer,jsonb,timestamptz,uuid,jsonb)'::regprocedure;commit;")[0];
 const source=read("supabase/migrations/"+name).replace(/\r\n/g,"\n").split("as $$")[1].split("$$;")[0];
 assert.equal(f.prosrc,source);assert.equal(f.prosecdef,false);out(mode,{function_source_identical:true,security_invoker:true});console.log("Exact source and invoker: PASS");
}else{
 const tables=query("begin read only;select schemaname,tablename from pg_tables where schemaname in ('public','ai_private','legacy_auth_private') or (schemaname='auth' and tablename='users') order by 1,2;commit;");
 const selects=tables.map(({schemaname:s,tablename:t})=>{assert(/^[a-z0-9_]+$/.test(s+t));return "select '"+s+"."+t+"' table_name,count(*)::integer rows,md5(coalesce(string_agg(h,'' order by h),'')) fingerprint from (select md5(to_jsonb(r)::text) h from "+s+"."+t+" r)x";});
 const data=query("begin read only;"+selects.join(" union all ")+";commit;");
 const result={target:"mokxyyullfhkfalopbzd",at:new Date().toISOString(),tables:data};
 if(mode==="after"){const before=JSON.parse(read("supabase/.temp/training-correction-before-data.json"));result.changed=data.filter(r=>JSON.stringify(r)!==JSON.stringify(before.tables.find(b=>b.table_name===r.table_name)));assert.equal(result.changed.length,0,JSON.stringify(result.changed));}
 out(mode+"-data",result);console.log(JSON.stringify({mode,tables:data.length,rows:data.reduce((n,t)=>n+t.rows,0),changed:result.changed}));
}
