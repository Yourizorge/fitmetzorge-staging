"use strict";
const fs=require("node:fs"),p=require("node:path"),{fixture,corrected,restore,scenarios}=require("./fixtures.cjs"),{evaluate,hash}=require("./engine.cjs");
const root=p.resolve(__dirname,"../..");
function build(){
 const data={version:"6e13.synthetic.v1",scenarios,locales:{}};
 for(const locale of ["nl","en","de"]){
  data.locales[locale]={};
  for(const name of scenarios){
   const first=fixture(name,locale),second=corrected(first),third=restore(second,first);
   data.locales[locale][name]={clock_ms:first.gate.now_ms,versions:[first,second,third].map((f,i)=>({
    key:"v"+(i+1),revision:f.bundle.revision,previous_hash:f.bundle.previous_hash,source_hash:hash(f.bundle),
    restore_of:i===2?hash(first.bundle):null,source:f.bundle,result:evaluate(f.bundle,f.gate,locale)
   }))};
  }
 }
 return data;
}
if(require.main===module){
 const output=build();fs.writeFileSync(p.join(root,"proactive-signals-demo/data.js"),"globalThis.FMZ13Data = "+JSON.stringify(output)+";\n");
 console.log(JSON.stringify({scenarios:scenarios.length,locales:3,evaluations:scenarios.length*9}));
}
module.exports={build};
