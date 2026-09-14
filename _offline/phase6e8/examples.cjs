"use strict";
const M=require("../../coach-review-demo/model.js"),C=require("../../coach-review-demo/catalog.js"),copy=require("../../coach-review-demo/copy.js");
function generate(){
 const m=M.create();m.command(m.event("build"));const plan=m.view().draft.plan;
 const results=[];
 for(const [n,locale]of ["nl","en","de"].entries()){
  const t=k=>copy[locale][k],ex=plan.training.sessions[0].exercises[0];
  results.push({id:"normal-"+locale,locale,status:m.view().status,answer:[
   t("proposal"),t("fixture"),
   t("training")+": "+plan.training.days.map(t).join(", ")+". "+C.exercises.find(x=>x.id===ex.id).label[n]+": "+ex.sets+" "+t("sets")+" x "+ex.reps+" "+t("reps")+". "+t("rest")+": "+ex.rest+" s. RIR "+ex.rir+" / RPE "+ex.rpe+". "+t("start_principle"),
   t("nutrition")+": "+plan.nutrition.totals.kcal+" kcal; "+t("protein")+" "+plan.nutrition.totals.protein+" g; "+t("carbs")+" "+plan.nutrition.totals.carbs+" g; "+t("fat")+" "+plan.nutrition.totals.fat+" g. "+plan.nutrition.meals.map(x=>x.items.map(y=>C.foods.find(f=>f.id===y.food).label[n]+" "+y.g+" g").join(" + ")).join("; "),
   t("recoveryPlan")+": "+t("sleepGoal")+" "+plan.recovery.sleepGoal+" h; "+t("restDays")+": "+plan.recovery.restDays.map(t).join(", ")+". "+t("checkins")+": "+t(plan.recovery.checkins)+".",
   t("confirm")+" → "+t("apply")+"."
  ].join("\n"),plan});
  const blocked=M.create();blocked.inject("current");const denied=blocked.command(blocked.event("build"));
  results.push({id:"blocked-"+locale,locale,allowed:denied.ok,reason:denied.reason,answer:t("warning_health")+"\n"+t("safetyNote"),active:blocked.view().active});
  for(const id of Object.keys(C.signals))results.push({id:"signal-"+id+"-"+locale,locale,answer:t("why_"+id),source:C.signals[id]});
 }
 return {synthetic_only:true,medical_validation:false,external_ai_calls:0,examples:results};
}
if(require.main===module){const fs=require("node:fs"),path=require("node:path");fs.writeFileSync(path.resolve(__dirname,"../../docs/PHASE6E8_EXAMPLES.json"),JSON.stringify(generate(),null,2)+"\n");console.log("33 exact NL/EN/DE concept examples generated");}
module.exports={generate};
