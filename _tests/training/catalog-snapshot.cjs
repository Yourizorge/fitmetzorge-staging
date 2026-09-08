const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process");
const root=path.resolve(__dirname,"../.."),python=process.env.FMZ_PYTHON||"C:/Users/Fitme/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const query="select id,canonical_slug,name_en,name_de,primary_muscle,secondary_muscles,body_region,equipment,equipment_group,movement_pattern,animation_url,legacy_animation_url,animation_source,animation_status,source_reference,is_active,instructions_nl,instructions_en,instructions_de from public.exercises where is_active order by canonical_slug;";
const r=JSON.parse(cp.execFileSync(python,[path.join(root,"supabase/tests/phase6d0-staging-query.py")],{input:query,encoding:"utf8",windowsHide:true,maxBuffer:10000000}));
if(!r.ok||r.rows.length!==898)throw Error("catalog_snapshot_failed");
fs.writeFileSync(path.join(root,"supabase/.temp/training-catalog.json"),JSON.stringify(r.rows));
console.log(JSON.stringify({read_only_catalog:true,count:r.rows.length,member_reads:false,target:"mokxyyullfhkfalopbzd"}));
