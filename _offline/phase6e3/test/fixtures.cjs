"use strict";
const legacy=require("../../phase6e2/test/fixtures.cjs"),prereg=require("../preregistered-cases.json");
const engine=require("../engine.cjs");
const clone=x=>JSON.parse(JSON.stringify(x));
function setup(c={}) {
  const f=legacy.setup({kind:"post_workout",locale:c.locale||"nl",scenario:c.scenario||"ordinary"});
  const request={synthetic_only:true,locale:c.locale||"nl",binding:clone(f.context.binding),sources:clone(prereg.fixture)};
  for(const {path,value} of c.changes||[]) {
    let target=request.sources;for(const key of path.slice(0,-1))target=target[key];
    target[path.at(-1)]=clone(value);
  }
  return {...f,request};
}
function run(c={}) {const f=setup(c);return engine.reflect(f.request,f.context,f.authority);}
module.exports={setup,run,clone,legacy,engine,prereg};
