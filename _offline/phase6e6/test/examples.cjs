"use strict";
const f=require("./fixtures.cjs"),cases=require("../preregistered-cases.json");
function generate(){
 const examples=[];
 for(const locale of cases.examples.locales)for(const scenario of cases.examples.scenarios){
  const x=f.setup(["approval_timeline","rejection","version_conflict"].includes(scenario)?"normal":scenario,locale),out=f.run(x);
  const row={locale,scenario,output:out,timeline:[]};
  if(["approval_timeline","rejection","version_conflict"].includes(scenario)){
   let state=f.review.create(out.plan_option);
   const step=(role,decision)=>{const r=f.act(x,state,role,decision);state=r.state;row.timeline.push({decision,role,reason:r.reason,messages:r.messages,
    member_acceptance:state.member_acceptance,trainer_approval:state.trainer_approval,application:state.application,status:state.status,
    active_plan_ref:f.ref(state.active_plan),applications:state.applications,previous_plan_refs:state.previous_plans.map(f.ref),audit_hashes:state.audit.map(a=>a.hash)});};
   step("member","view");step("member","accept");
   if(scenario==="rejection")step("trainer","reject");
   else {step("trainer","accept");if(scenario==="version_conflict"){x.book.revision+=1;x.request.expected_rulebook.revision+=1;}
    step("trainer","apply");if(scenario==="approval_timeline")step("trainer","apply");}
  }
  examples.push(row);
 }
 return examples;
}
module.exports={generate};
