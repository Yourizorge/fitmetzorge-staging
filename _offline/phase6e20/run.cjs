'use strict';
const fs=require('node:fs'),p=require('node:path'),cp=require('node:child_process'),a=require('node:assert/strict'),out=process.argv[2];
const r=cp.spawnSync(process.execPath,['--require','./_offline/phase6e12/no_network.cjs','--test','--test-reporter=tap','_offline/phase6e20/contract.test.cjs'],{cwd:p.resolve(__dirname,'../..'),encoding:'utf8',windowsHide:true,timeout:180000,maxBuffer:30000000});
const counts=Object.fromEntries(['tests','pass','fail','skipped'].map(k=>[k,Number(r.stdout?.match(new RegExp('^# '+k+' (\\d+)$','m'))?.[1])]));
fs.writeFileSync(p.join(out,'contract-'+Date.now()+'.json'),JSON.stringify({counts,status:r.status,stdout:r.stdout,stderr:r.stderr,network_blocked:true},null,2),{flag:'wx'});console.log(counts);if(r.status)console.log(r.stdout.split(/(?=# Subtest:)/).filter(x=>x.includes('not ok')).join('\n'));a.equal(r.status,0);
