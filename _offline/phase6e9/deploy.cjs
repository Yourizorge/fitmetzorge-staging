"use strict";
const fs=require("node:fs"),path=require("node:path"),cp=require("node:child_process");
const root=path.resolve(__dirname,"../..");
const work=path.join(root,"supabase/.temp/phase6e9-edge-deploy");
const dest=path.join(work,"supabase/functions/fmz6e9-synthetic");
fs.mkdirSync(dest,{recursive:true});
for(const file of ["index.ts","handler.mjs","core.mjs","frozen.mjs"])
 fs.copyFileSync(path.join(__dirname,"edge",file),path.join(dest,file));
const cli="C:/Users/Fitme/AppData/Local/pnpm/store/v11/links/@supabase/cli-windows-x64/2.115.0/567b8c0d4b3839f7f3f4e2f65c98152b32151766052aa5db7b80e173657c326b/node_modules/@supabase/cli-windows-x64/bin/supabase.exe";
const r=cp.spawnSync(cli,["--workdir",work,"functions","deploy","fmz6e9-synthetic","--project-ref","mokxyyullfhkfalopbzd","--use-api"],{encoding:"utf8",windowsHide:true,timeout:120000});
console.log(r.stdout);console.error(r.stderr);process.exitCode=r.status;
