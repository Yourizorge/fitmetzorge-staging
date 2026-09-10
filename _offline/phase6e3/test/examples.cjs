"use strict";
const {setup,prereg,engine}=require("./fixtures.cjs");
function examples() {
  return prereg.cases.filter(c=>c.exact_excerpt).map(c=>{
    const f=setup(c);return {locale:c.locale,output:engine.reflect(f.request,f.context,f.authority)};
  });
}
function boundaries() {
  return ["goal-absent","partial-records","unit-lb-not-converted","safety-current","safety-self_reported",
    "safety-expired","safety-expired_fresh","safety-new_after_recovery"].map(id=>{
      const c=prereg.cases.find(x=>x.id===id),f=setup(c);
      return {id,output:engine.reflect(f.request,f.context,f.authority)};
    });
}
module.exports={examples,boundaries};
if(require.main===module)process.stdout.write(JSON.stringify({examples:examples(),boundaries:boundaries()},null,2)+"\n");
