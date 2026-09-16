const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process");
const root=path.resolve(__dirname,"../../.."),{work,project}=JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp/phase6e10-cli.json")));
if(project!=="mokxyyullfhkfalopbzd")throw Error("staging_only");
const dest=path.join(work,"supabase/functions/fmz6e10-synthetic");fs.mkdirSync(dest,{recursive:true});
for(const f of ["index.ts","handler.mjs"])fs.copyFileSync(path.join(root,"_offline/phase6e10/edge",f),path.join(dest,f));
const r=cp.spawnSync("C:/Users/Fitme/AppData/Local/pnpm/store/v11/links/@supabase/cli-windows-x64/2.115.0/567b8c0d4b3839f7f3f4e2f65c98152b32151766052aa5db7b80e173657c326b/node_modules/@supabase/cli-windows-x64/bin/supabase.exe",["--workdir",work,"functions","deploy","fmz6e10-synthetic","--project-ref",project,"--use-api"],{cwd:root,encoding:"utf8",windowsHide:true,timeout:120000});
console.log(r.stdout);console.error(r.stderr);process.exitCode=r.status;
