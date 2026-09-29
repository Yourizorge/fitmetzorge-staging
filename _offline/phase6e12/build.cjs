"use strict";
const fs=require("node:fs"),path=require("node:path");
const {fixture,create,scenarios,hash}=require("./core.cjs");
const root=path.resolve(__dirname,"../.."),data={version:"6e12-synthetic-v1",synthetic_only:true,profiles:{}};
for(const name of scenarios){data.profiles[name]={};for(const locale of ["nl","en","de"]){
 const f=fixture(name,locale),w=create(f),draft=w.draft();if(!w.register(draft).ok)throw Error("fixture");
 const result=w.reflect();if(!result.ok)throw Error("reflection");
 const shortReasons=require("../phase6e5/copy.json")[locale].reasons;
 data.profiles[name][locale]={draft,snapshot:w.view().snapshot,pack:result.pack,messages:result.result.messages,
   status:result.result.status,source_hash:result.source_hash,short_reasons:Object.fromEntries(result.result.rows.map(r=>[r.exercise_id,shortReasons[r.reason]||""]))};
}}
data.hash=hash(data);
fs.mkdirSync(path.join(root,"workout-reflection-demo"),{recursive:true});
fs.writeFileSync(path.join(root,"workout-reflection-demo/data.js"),"/* Generated synthetic examples only; no credentials or member data. */\nglobalThis.FMZ6E12Data="+JSON.stringify(data)+";\n");
console.log(JSON.stringify({profiles:scenarios.length,localized:scenarios.length*3,sha256:data.hash}));
