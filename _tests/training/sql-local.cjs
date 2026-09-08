const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process");
const root=path.resolve(__dirname,"../.."),bin="C:/Program Files/PostgreSQL/18/bin";
const work=fs.realpathSync(process.argv[2]||"");
const temp=fs.realpathSync(require("node:os").tmpdir());
if(!work.startsWith(temp+path.sep)||!path.basename(work).startsWith("fmz-local-rebuild-")||!fs.existsSync(path.join(work,"data/PG_VERSION")))throw Error("explicit_local_cluster_required");
const port=55881;
function run(file,args,input){const r=cp.spawnSync(file,args,{input,encoding:"utf8",windowsHide:true,maxBuffer:10000000,timeout:60000,stdio:args.includes("start")?"ignore":"pipe"});if(r.status!==0)throw Error(r.stderr||r.stdout||"process_failed");return r.stdout;}
const psql=(sql)=>run(path.join(bin,"psql.exe"),["-h","127.0.0.1","-p",String(port),"-U","postgres","-d","postgres","-v","ON_ERROR_STOP=1","-At"],sql);
let started=false;
try{
 run(path.join(bin,"pg_ctl.exe"),["-D",path.join(work,"data"),"-l",path.join(work,"training.log"),"-o","-p "+port+" -h 127.0.0.1","-w","start"]);started=true;
 // Exact table DDL from the accepted migration, without its unrelated AI schema.
 const original=fs.readFileSync(path.join(root,"supabase/migrations/20260906080455_phase6d_owner_safety_settings.sql"),"utf8");
 const table=original.slice(original.indexOf("create table public.member_app_preferences"),original.indexOf("create table ai_private.analysis_safety_recoveries"));
 if(psql("select to_regclass('public.member_app_preferences') is null;").trim()==="t")psql(table);
 const c=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/training-catalog.json"),"utf8"))[0];
 const literal=x=>"'"+String(x).replaceAll("'","''")+"'";
 psql("insert into public.exercises(id,canonical_slug,canonical_name,name_en,primary_muscle,body_region,equipment,equipment_group,movement_pattern,instructions_en) values("+[c.id,c.canonical_slug,c.name_en,c.name_en,c.primary_muscle,c.body_region,c.equipment,c.equipment_group,c.movement_pattern,c.instructions_en].map(literal).join(",")+") on conflict(id) do nothing;");
 if(psql("select to_regprocedure('public.fmz_training_get_preferences()') is null;").trim()==="t")psql(fs.readFileSync(path.join(root,"supabase/migrations/20260908100106_training_workout_editor.sql"),"utf8"));
 // Refresh only this authored validator in the verified disposable local cluster.
 const migration=fs.readFileSync(path.join(root,"supabase/migrations/20260908100106_training_workout_editor.sql"),"utf8");
 psql(migration.slice(migration.indexOf("create function public.fmz_training_valid_set_targets"),migration.indexOf("revoke all on function")).replace("create function","create or replace function"));
 const result=psql(fs.readFileSync(path.join(__dirname,"sql.test.sql"),"utf8"));
 console.log(result);
 console.log(JSON.stringify({local_cluster:work,port,files_deleted:0,scope:"22 canonical migrations plus exact member preference DDL and Training migration; no pg_cron/AI platform emulation"}));
}finally{if(started)run(path.join(bin,"pg_ctl.exe"),["-D",path.join(work,"data"),"-m","fast","-w","stop"]);}
