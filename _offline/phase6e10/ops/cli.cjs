const fs=require("node:fs"),path=require("node:path"),os=require("node:os"),cp=require("node:child_process"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../.."),manifest=path.join(root,"supabase/.temp/phase6e10-cli.json");
const cli="C:/Users/Fitme/AppData/Local/pnpm/store/v11/links/@supabase/cli-windows-x64/2.115.0/567b8c0d4b3839f7f3f4e2f65c98152b32151766052aa5db7b80e173657c326b/node_modules/@supabase/cli-windows-x64/bin/supabase.exe";
const mode=process.argv[2],allowed=["prepare","list","dry-run","push"];
if(!allowed.includes(mode))throw Error("explicit_operation_required");
const run=args=>{
 const r=cp.spawnSync(cli,args,{cwd:root,encoding:"utf8",windowsHide:true,timeout:120000});
 const output=(r.stdout||"")+(r.stderr||"");
 if(/sbp_|eyJ[A-Za-z0-9_-]{20}/.test(output))throw Error("unexpected_sensitive_cli_output");
 console.log(output);if(r.status!==0)throw Error("cli_command_failed");
};
let work;
if(mode==="prepare"){
 if(fs.existsSync(manifest))throw Error("inspect_existing_cli_workspace");
 work=fs.mkdtempSync(path.join(os.tmpdir(),"fmz6e10-cli-"));
 run(["--workdir",work,"init","--yes"]);
 fs.mkdirSync(path.join(work,"supabase/migrations"),{recursive:true});
 fs.writeFileSync(manifest,JSON.stringify({work,project:"mokxyyullfhkfalopbzd"})+"\n");
 run(["--workdir",work,"link","--project-ref","mokxyyullfhkfalopbzd"]);
}else work=JSON.parse(fs.readFileSync(manifest)).work;
const files=fs.readdirSync(path.join(root,"supabase/migrations")).filter(x=>x.endsWith(".sql"));
const sha=b=>crypto.createHash("sha256").update(b).digest("hex");
for(const f of files){
 const src=path.join(root,"supabase/migrations",f),dest=path.join(work,"supabase/migrations",f);
 fs.copyFileSync(src,dest);if(sha(fs.readFileSync(src))!==sha(fs.readFileSync(dest)))throw Error("migration_copy_mismatch");
}
if(mode==="list")run(["--workdir",work,"migration","list","--linked"]);
if(mode==="dry-run"||mode==="push")run(["--workdir",work,"db","push",...(mode==="dry-run"?["--dry-run"]:["--yes"]),"--skip-vault"]);
console.log(JSON.stringify({work,canonical_copies:files.length,operation:mode}));
