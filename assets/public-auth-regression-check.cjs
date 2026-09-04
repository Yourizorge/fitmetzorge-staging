const fs=require("fs"),path=require("path"),{spawnSync}=require("child_process");
const root=path.resolve(__dirname,".."),archive=path.resolve(root,"../../..");
if(process.argv[2]==="--historical"){
  const name=process.argv[3];
  if(!["phase2-static-check.js","phase3-static-check.js"].includes(name))throw new Error("unknown historical suite");
  const proxy=new Proxy(fs,{get(target,key){
    if(!["readFileSync","existsSync","statSync","readdirSync"].includes(key))return target[key];
    return(file,...args)=>{
      const relative=path.relative(root,file);
      return fs[key](fs.existsSync(file)?file:path.join(archive,relative),...args);
    };
  }});
  let source=fs.readFileSync(path.join(archive,"assets",name),"utf8")
    .replace('const currentAppVersion = "20260826-phase4f-c1";','const currentAppVersion = "20260904-auth-lifecycle1";')
    .replace('const phase1Version = "20260818-member-ux-today-hydration1";','const phase1Version = "20260904-auth-lifecycle1";');
  const historicalRequire=name=>{
    if(name==="fs")return proxy;
    if(path.isAbsolute(name)&&!fs.existsSync(name)){
      const file=path.join(archive,path.relative(root,name)),module={exports:{}};
      new Function("require","__dirname","module","exports",fs.readFileSync(file,"utf8").replace(/^#![^\n]*\n/,""))(historicalRequire,path.dirname(file),module,module.exports);
      return module.exports;
    }
    return require(name);
  };
  new Function("require","__dirname",source)(historicalRequire,__dirname);
}else{
  const jobs=[
    ["assets/phase6d0-frozen-regression-check.cjs"],
    [__filename,"--historical","phase2-static-check.js"],
    [__filename,"--historical","phase3-static-check.js"],
    ...["phase4-static-check.js","phase4-nutrition-slice4fe-static-check.js","phase5-static-check.js","phase6a-static-check.js","phase6b-static-check.js","phase6c-static-check.js"].map(n=>["assets/"+n]),
    ["--test","supabase/functions/invite-client/handler.test.ts"],
    ["--test","supabase/functions/youri-ai/phase6c-handler.test.ts"],
    ["--test","supabase/tests/phase6d0-migration-identity-check.test.cjs"],
    ["assets/phase6d0-browser-check.js"],
    ["assets/phase5-browser-check.js"],
    ["assets/phase6c-browser-check.js"],
    ["assets/phase4-nutrition-slice3-browser-check.js"]
  ];
  for(const args of jobs){
    const result=spawnSync(process.execPath,args,{cwd:root,encoding:"utf8",windowsHide:true,timeout:180000,maxBuffer:5000000});
    const output=(result.stdout||"")+(result.stderr||"");
    const summary=output.split("\n").filter(l=>/passed:|passed|pass_count|fail_count|# tests|# pass|# fail|FAIL|Error|ENOENT/.test(l)).slice(-10);
    console.log(JSON.stringify({suite:args.join(" "),exit:result.status,summary}));
    if(result.status!==0)process.exitCode=1;
  }
}
