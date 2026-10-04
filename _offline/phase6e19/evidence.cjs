"use strict";
const fs=require('node:fs'),p=require('node:path'),c=require('node:crypto'),a=require('node:assert/strict'),M=require('../../recovery-checkin-demo/model.js'),R=require('../../recovery-checkin-demo/review.js'),C=require('../../recovery-checkin-demo/copy.js');
const root=p.resolve(__dirname,'../..'),out=process.argv[2],sha=x=>c.createHash('sha256').update(x).digest('hex'),read=f=>JSON.parse(fs.readFileSync(p.join(out,f))),names=fs.readdirSync(out),last=prefix=>names.filter(f=>f.startsWith(prefix)&&f.endsWith('.json')).sort().at(-1);
const unit=read(last('contract-'));a.equal(unit.counts.tests,343);a.equal(unit.counts.pass,343);a.equal(unit.counts.fail,0);
const browser=read(last('local-browser-'));a.equal(browser.status,'BROWSER_PASS');a(browser.checks.every(x=>x.pass));a.equal(browser.layouts.length,385);
for(const [f,h]of Object.entries(browser.source_sha256))a.equal(sha(fs.readFileSync(p.join(root,'recovery-checkin-demo',f))),h,f);
let frozen=0;const reg=read('unit-regressions.json');for(const x of Object.values(reg.groups)){a.equal(x.exit,0);a.equal(x.counts.fail,0);frozen+=x.counts.pass;}
for(const [n,count]of [[13,233],[14,389],[16,536],[17,289],[18,335]]){const r=read(last('frozen-'+n+'-'));a.equal(r.status,0);frozen+=count;}a.equal(frozen,4373);
const preserve=read(last('preserve-'));a.equal(preserve.status,'PASS');a.equal(preserve.files,1260);a.equal(preserve.historical,58);
const pub=read(last('publication-before-'));a.equal(pub.status,'PUBLICATION_PASS');a.equal(pub.existing.length,132);
const files=[];for(const d of ['_offline/phase6e19','recovery-checkin-demo'])for(const f of fs.readdirSync(p.join(root,d)).filter(f=>fs.statSync(p.join(root,d,f)).isFile()))files.push(d+'/'+f);
const source_sha256=Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(p.join(root,f)))]));
const evidence={package:'6E-19',status:'LOCAL_TECHNICAL_PASS; publication separately verified',source_sha256,tests:{new19:unit.counts,frozen,total:frozen+unit.counts.pass,network_blocked:true,medical_validation:false,known_limitation_observations_not_recognition_success:true},browser:{assertions:browser.checks.length,layouts:browser.layouts.length,settings:24,scenarios:16,widths:[320,390,768,1280],languages:['nl','en','de'],themes:['light','dark'],physical_phone:false,no_unexpected_requests:browser.errors.length===0},preserve,publication_before:{old:132,private404:pub.private.length},raw_evidence:Object.fromEntries(names.filter(f=>f.endsWith('.json')).map(f=>[p.relative(root,p.join(out,f)).replaceAll('\\','/'),sha(fs.readFileSync(p.join(out,f)))])),screenshots:browser.screenshots.map(f=>({file:p.relative(root,f).replaceAll('\\','/'),sha256:sha(fs.readFileSync(f))})),support_hold:'SU-487979',external_ai_calls:0,external_cost_eur:0,real_member_ai:false,production_touched:false,owner_accepted:false};
const examples=[];for(const spec of R.scenarios)for(let l=0;l<3;l++){const r=R.run(spec.id),s=r.model.view();a(R.assess(r).pass);examples.push({case:spec.id,language:['nl','en','de'][l],title:spec.title[l],status:C.get(s.status==='facts'?'factsOnly':s.status,l),message:C.reason(s.reason,l),explanation:C.reason(spec.id==='atomic'?'atomic_fault':spec.reason,l),facts:s.facts,proposal:s.proposal?{label:C.get(s.proposal.option,l),time:s.proposal.at,basis:s.input.rule?.id,version:s.input.rule?.version,applied:s.status==='applied'}:null,next_checkin:M.nextCheckin(s),active_version:s.active.version,plans_unchanged:M.same(s.input.plan,require('../../recovery-checkin-demo/fixtures.js').cases[spec.id].plan),automatic_actions_allowed:false});}
for(const [file,data]of [['docs/PHASE6E19_EVIDENCE.json',evidence],['docs/PHASE6E19_EXAMPLES.json',examples]]){
 const target=p.join(root,file),bytes=JSON.stringify(data,null,2)+'\n';
 if(fs.existsSync(target)){
  const old=fs.readFileSync(target);if(old.toString()===bytes)continue;
  const archive=file.endsWith('_EXAMPLES.json')?'docs/PHASE6E19_INITIAL_EXAMPLES.json':fs.existsSync(p.join(root,'docs/PHASE6E19_INITIAL_EVIDENCE.json'))?'docs/PHASE6E19_REQUEST_ID_EVIDENCE.json':'docs/PHASE6E19_INITIAL_EVIDENCE.json';
  fs.writeFileSync(p.join(root,archive),old,{flag:'wx'});
  fs.writeFileSync(target,bytes);
 }else fs.writeFileSync(target,bytes,{flag:'wx'});
}
console.log({status:evidence.status,sources:files.length,total:evidence.tests.total,browser:evidence.browser.assertions,examples:examples.length});
