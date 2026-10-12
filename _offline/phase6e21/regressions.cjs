'use strict';
const fs=require('node:fs'),p=require('node:path'),cp=require('node:child_process'),a=require('node:assert/strict');
const out=process.argv[2],results=[];
for(const script of ['_offline/phase6e12/run_tests.cjs','_offline/phase6e20/regressions.cjs']){
 const r=cp.spawnSync(process.execPath,[script,out],{cwd:p.resolve(__dirname,'../..'),encoding:'utf8',windowsHide:true,timeout:900000,maxBuffer:40000000});
 const item={script,exit:r.status,stdout:r.stdout,stderr:r.stderr};results.push(item);console.log(r.stdout);
 fs.writeFileSync(p.join(out,'frozen-run-'+Date.now()+'.json'),JSON.stringify(item,null,2),{flag:'wx'});a.equal(r.status,0);
}
fs.writeFileSync(p.join(out,'frozen-summary.json'),JSON.stringify({status:'PASS',results,expected:4947,hosted_calls:0},null,2),{flag:'wx'});
