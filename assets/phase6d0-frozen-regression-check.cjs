// Run historical assertions against the actual deployment runtime, not a stale source copy.
const fs=require("fs"),path=require("path");
const root=path.resolve(__dirname,"..");
const archive=process.env.FMZ_ARCHIVE_ROOT||path.resolve(root,"../../..");
const testFs=new Proxy(fs,{get(target,key){
 if(key!=="readFileSync")return target[key];
 return (file,...args)=>{
  const relative=path.relative(root,file);
  const targetFile=!fs.existsSync(file)&&/^supabase[\\/](migrations|verification)[\\/]/.test(relative)
   ?path.join(archive,relative):file;
  return fs.readFileSync(targetFile,...args);
 };
}});
for(const name of ["phase1-static-check.js","member-ux-static-check.js"]){
 const file=path.join(archive,"assets",name);
 let source=fs.readFileSync(file,"utf8");
 // Refresh obsolete deployment constants without changing runtime or security assertions.
 if(!source.includes('const currentAppVersion = "20260826-phase4f-c1";'))throw new Error("Historical cache assertion changed");
 source=source.replace('const currentAppVersion = "20260826-phase4f-c1";','const currentAppVersion = "20260904-phase6d0-auth1";');
 if(name==="phase1-static-check.js"){
  if(!source.includes('const phase1Version = "20260818-member-ux-today-hydration1";'))throw new Error("Historical Phase 1 cache assertion changed");
  source=source.replace('const phase1Version = "20260818-member-ux-today-hydration1";','const phase1Version = "20260901-phase5-unit-switch1";');
 }
 if(name==="member-ux-static-check.js"){
  const oldCheck = `memberUx.includes('class="primary-btn member-ux-primary-action" data-member-open-detail=')`;
  if(!source.includes(oldCheck))throw new Error("Historical tracker assertion changed");
  // Phase 5 already routes Progress to its page; assert rendered markup for both branches.
  source=source.replace(oldCheck,`(() => {
   const render=vm.runInNewContext("("+extractFunction(memberUx,"memberUxTrackerCard")+")",
    {window:{FMZ_PHASE5_PROGRESS:true},escapeHTML:String,memberUxText:String});
   const sleep=render("sleep","Slaap","8",""),progress=render("progress","Voortgang","","");
   return [sleep,progress].every(html=>html.includes('class="primary-btn member-ux-primary-action"'))
    && sleep.includes('data-member-open-detail="sleep"') && progress.includes('data-member-open-view="progress"');
  })()`);
 }
 new Function("require","__dirname","__filename",source)(name=>name==="fs"?testFs:require(name),path.join(root,"assets"),file);
}
