"use strict";
const {run}=require("./fixtures.cjs");
function examples(){return ["nl","en","de"].flatMap(locale=>[
  {locale,situation:"allowed_current_explicit_trainer_option",output:run({locale})},
  {locale,situation:"refused_missing_explicit_authority",output:run({locale,changes:[{path:["authority"],value:null}]})}
]);}
function boundaries(){return ["current","self_reported","recurring","unclear","technical","expired_fresh","missing_fresh"].map(scenario=>({scenario,output:run({scenario})}));}
module.exports={examples,boundaries};
if(require.main===module)process.stdout.write(JSON.stringify({examples:examples(),boundaries:boundaries()},null,2)+"\n");
