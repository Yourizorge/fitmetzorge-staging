"use strict";
const fs=require("node:fs"),p=require("node:path"),F=require("./fixtures.cjs"),E=require("./engine.cjs"),{catalogs,clone}=require("./catalog.cjs");
const packets={};
for(const name of F.scenarios){packets[name]={};for(const locale of ["nl","en","de"]){
 const f=F.fixture(name,locale),next=F.corrected(f),cat=catalogs[f.source.template];
 packets[name][locale]={route:f.source.route,baseRevision:f.source.plan_ref.revision,before:clone(cat.before),now_ms:f.gate.now_ms,
 initial:E.evaluate(f.source,f.gate,locale),corrected:E.evaluate(next.source,next.gate,locale),correctedPrevious:next.source.previous_hash,
 provenance:{template:cat.id,source_sha256:cat.source_sha256,source_clock:cat.source_clock,source_commit:cat.source_commit||"owner-accepted-6e8",
  refs:cat.refs||cat.policy,observations:cat.observations||cat.signal,original_subject:cat.original_subject||"syn-ai-member",synthetic_rebased_clock:true}};
}}
fs.writeFileSync(p.resolve(__dirname,"../../bounded-adjustments-demo/data.js"),"/* Generated synthetic packets only. */\nglobalThis.FMZ14Data="+JSON.stringify(packets)+";\n");
console.log(JSON.stringify({scenarios:F.scenarios.length,locales:3,source_versions:2}));
