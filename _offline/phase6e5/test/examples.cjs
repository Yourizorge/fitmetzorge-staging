"use strict";
const F=require("./fixtures.cjs");
function generate(){
 const all=[];
 for(const locale of ["nl","en","de"]){
  for(const name of ["normal","too_few_sessions","effort_conflict","current","lb","required_rir_missing","no_trainer"])
   all.push({id:locale+"-"+name,locale,scenario:name,output:F.run(name,locale)});
  for(const path of ["accept","reject","version_conflict_and_reassessment"]){
   const f=F.setup("normal",locale),proposal=F.engine.propose(f.request,f.context,f.authority);
   let state=F.review.create(proposal.plan_option),timeline=[];
   const take=(decision,role="member")=>{const result=F.apply(state,f,decision,role);timeline.push({decision,role,...result});state=result.state;};
   take("view");take("accept");
   if(path==="accept"){take("accept","trainer");take("apply","trainer");take("apply","trainer");}
   if(path==="reject")take("reject","trainer");
   if(path==="version_conflict_and_reassessment"){
    F.changedPlan(f);take("accept","trainer");
    const reassessed=F.engine.propose(f.request,f.context,f.authority);
    timeline.push({decision:"reassess",output:reassessed,state:F.review.create(reassessed.plan_option)});
   }
   all.push({id:locale+"-"+path,locale,scenario:path,initial:proposal,timeline});
  }
 }
 return all;
}
if(require.main===module)process.stdout.write(JSON.stringify(generate(),null,2)+"\n");
module.exports={generate};
