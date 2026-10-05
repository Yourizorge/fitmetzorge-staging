'use strict';
const fs=require('node:fs'),p=require('node:path'),cp=require('node:child_process'),a=require('node:assert/strict'),out=process.argv[2],results=[];
for(const [n,script,expected]of [[13,'run_tests.cjs',233],[14,'run_tests.cjs',389],[16,'run.cjs',536],[17,'run.cjs',289],[18,'run.cjs',335],[19,'run.cjs',343],[20,'run.cjs',231]]){
 const dir=p.join(out,'suite-'+n+'-'+Date.now());fs.mkdirSync(dir);const r=cp.spawnSync(process.execPath,['_offline/phase6e'+n+'/'+script,dir],{cwd:p.resolve(__dirname,'../..'),encoding:'utf8',windowsHide:true,timeout:240000,maxBuffer:30000000});
 const files=fs.readdirSync(dir).filter(x=>x.endsWith('.json')),raw=files.map(f=>JSON.parse(fs.readFileSync(p.join(dir,f))));const counts=raw.find(x=>x.counts)?.counts;
 const item={package:n,exit:r.status,expected,counts,dir,stdout:r.stdout,stderr:r.stderr};results.push(item);
 fs.writeFileSync(p.join(out,'suite-result-'+n+'-'+Date.now()+'.json'),JSON.stringify(item,null,2),{flag:'wx'});console.log({package:n,exit:r.status,counts});a.equal(r.status,0);a.equal(counts.pass,expected);a.equal(counts.fail,0);
}
fs.writeFileSync(p.join(out,'selected-regressions-'+Date.now()+'.json'),JSON.stringify(results,null,2),{flag:'wx'});
