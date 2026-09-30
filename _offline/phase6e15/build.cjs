"use strict";
const fs=require("node:fs"),p=require("node:path"),crypto=require("node:crypto"),F=require("../phase6e13/fixtures.cjs"),E=require("../phase6e13/engine.cjs"),C=require("../../coach-review-demo/catalog.js");
const root=p.resolve(__dirname,"../.."),clone=x=>JSON.parse(JSON.stringify(x)),clock=Date.UTC(2026,8,30,10),sha=f=>crypto.createHash("sha256").update(fs.readFileSync(p.join(root,f))).digest("hex");
const source={policy:C.policy.id,catalog:C.policy.catalog,nutrition:C.policy.nutrition,recovery:C.policy.sleep,progression:C.policy.progression,catalog_sha256:sha("coach-review-demo/catalog.js"),model_sha256:sha("coach-review-demo/model.js")};
const registry={source,safety:{}};
for(const [key,value]of Object.entries({none:"changes",current:"current",recurring:"recurring",unclassified:"unclassified",self_reported:"self_reported",expired_context:"expired_context",technical:"technical"})){
 registry.safety[key]={plan_allowed:key==="none",messages:{}};
 for(const l of ["nl","en","de"]){const f=F.fixture(value,l),o=E.evaluate(f.bundle,f.gate,l);registry.safety[key].messages[l]=o.feedback;
 if(key==="none")registry.safety[key].plan_allowed=o.context_mode==="ordinary_or_settled"&&o.access.new_analysis;}
}
const intake={...clone(C.defaults),location:"home",machines:[],disliked:["overhead"],dietLimits:[],locale:"nl",health:"none",consent:true,
 records:{id:"syn-records",revision:1,subject:"syn-intake-member",at:clock-3600000,expires:clock+82800000,coverage:"complete",sleep:7,recovery:"okay",activity_minutes:30}};
const base={synthetic_only:true,route:"B",subject:"syn-intake-member",clock,source,intake},fixtures={};
const cases={complete:()=>{},incomplete:f=>f.intake.goal=null,favorites:f=>{f.intake.favorites=["bridge"];f.intake.avoided=["squat"];},limited:f=>{f.intake.equipment=["mat"];f.intake.favorites=["bridge"];},too_limited:f=>f.intake.equipment=["band"],
 allergy:f=>{f.intake.diet="omnivore";f.intake.allergies=["nuts","dairy"];f.intake.excludedFoods=["tofu"];},conflict:f=>f.intake.avoided=["row"],
 imperial:f=>f.intake.unit="lb",complaint:f=>f.intake.health="current",recurring:f=>f.intake.health="recurring",self_reported:f=>f.intake.health="self_reported",
 expired_context:f=>f.intake.health="expired_context",technical:f=>f.intake.health="technical",revoked:f=>f.intake.consent=false,
 expired:f=>f.clock=C.policy.expires,missing_rule:f=>f.source.policy=null,conflicting_rule:f=>f.source.policy="other",
 missing_record:f=>f.intake.records.activity_minutes=null,conflicting_record:f=>f.intake.records.sleep=6,expired_record:f=>f.intake.records.expires=clock,
 unsupported_diet:f=>f.intake.dietLimits=["medical_diet"],unsupported_machine:f=>f.intake.machines=["cable"]};
for(const [n,edit]of Object.entries(cases)){fixtures[n]=clone(base);edit(fixtures[n]);}
fs.writeFileSync(p.join(root,"independent-intake-demo/data.js"),"/* Synthetic versioned intake fixtures only. */\nglobalThis.FMZ15Data="+JSON.stringify({registry,fixtures})+";\n");
console.log(JSON.stringify({fixtures:Object.keys(fixtures).length,locales:3,catalog:source.policy}));
