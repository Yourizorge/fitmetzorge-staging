/* Synthetic in-memory pair adapter. Frozen source engines are read-only dependencies. */
(function(root){"use strict";
const T=typeof module==='object'?require('../training-rules-demo/model.js'):root.FMZ16Model;
const N=typeof module==='object'?require('../nutrition-rules-demo/model.js'):root.FMZ17Model;
const copy=x=>JSON.parse(JSON.stringify(x)),same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),fail=x=>{throw Error(x);},int=Number.isSafeInteger;
const exact=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&same(Object.keys(o).sort(),keys.slice().sort());
function shape(f){
 if(!exact(f,['synthetic_only','route','person','clock','revision','link','training','nutrition'])||f.synthetic_only!==true||f.route!=='B'||f.person!=='syn18-member'||!int(f.clock)||!int(f.revision)||f.revision<1)fail('binding');
 const l=f.link;
 if(!exact(l,['id','version','person','trainingPerson','nutritionPerson','trainingGoal','nutritionGoal','at','expires'])||l.id!=='syn18-explicit-link'||!int(l.version)||l.version<1||l.person!==f.person||l.trainingPerson!=='syn16-member'||l.nutritionPerson!=='syn17-member'||!int(l.at)||!int(l.expires)||l.expires<=l.at)fail('identity');
 for(const [key,person]of [['training',l.trainingPerson],['nutrition',l.nutritionPerson]]){
  const s=f[key];if(!exact(s,['revision','at','expires','fixture','plan'])||!int(s.revision)||s.revision<1||!int(s.at)||!int(s.expires)||s.expires<=s.at||!s.fixture||s.fixture.person!==person||s.fixture.route!=='B'||s.fixture.synthetic_only!==true)fail('identity');
 }
}
const consent=f=>f.training.fixture.intake.consent===true&&f.nutrition.fixture.intake.consent?.status==='known'&&f.nutrition.fixture.intake.consent.value===true;
const health=f=>f.training.fixture.intake.health!=='none'||f.nutrition.fixture.intake.health?.status!=='known'||f.nutrition.fixture.intake.health.value!=='none';
function inspect(f,clock=f.clock){
 shape(f);if(!consent(f))fail('consent');if(health(f))fail('safety');
 for(const x of [f.link,f.training,f.nutrition])if(x.at>clock||x.expires<=clock)fail('expired');
 const t=f.training.fixture,n=f.nutrition.fixture;
 if(f.link.trainingGoal!==t.intake.goal||f.link.nutritionGoal!==n.intake.goal?.value||n.intake.goal?.status!=='known')fail('goal');
 if(n.intake.trainingFrequency?.status!=='known')fail('missing');
 if(t.intake.frequency!==n.intake.trainingFrequency.value)fail('frequency');
 const plans={};
 for(const [key,M]of [['training',T],['nutrition',N]]){
  const g=copy(f[key].fixture);g.clock=clock;const m=M.create(g),r=m.command(m.event('build'));
  if(!r.ok)fail(key+':'+r.reason);
  const built=key==='training'?r.state.draft.plan:r.state.draft;
  const p=f[key].plan===null?built:copy(f[key].plan);
  try{M.validatePlan(p,g.intake,g.catalog,clock);}catch(e){fail(key+':'+e.message);}
  plans[key]=p;
 }
 return {training:plans.training,nutrition:plans.nutrition,source:copy(f),sourceRevision:f.revision,linkVersion:f.link.version,trainingRevision:f.training.revision,nutritionRevision:f.nutrition.revision,automatic_actions_allowed:false,physical_advice_authorized:false};
}
function create(input){
 const initial=copy(input);let serial=0,s={sources:copy(input),clock:input.clock,epoch:0,status:'intake',version:0,draft:null,active:null,history:[],audit:[],revoked:false,healthLatch:false,automatic_actions_allowed:false,physical_advice_authorized:false,external_calls:0};
 try{s.healthLatch=health(input);}catch{ s.healthLatch=true; }
 s.selection=null;s.restores=null;
 const done=new Map(),view=()=>copy(s),binding=()=>JSON.stringify([s.epoch,s.version,s.sources]);
 const event=(action,data={})=>({id:'syn18-request-'+(++serial),person:'syn18-member',route:'B',binding:binding(),action,data:copy(data)});
 function gate(){
  shape(s.sources);if(s.revoked||!consent(s.sources))fail('consent');if(s.healthLatch)fail('safety');const pair=inspect(s.sources,s.clock);
  if(s.selection){T.validatePlan(s.selection.training,s.sources.training.fixture.intake,s.sources.training.fixture.catalog);N.validatePlan(s.selection.nutrition,s.sources.nutrition.fixture.intake,s.sources.nutrition.fixture.catalog,s.clock);pair.training=copy(s.selection.training);pair.nutrition=copy(s.selection.nutrition);}return pair;
 }
 function command(e,options={}){
  const old=copy(s);try{
   shape(initial);
   if(!exact(e,['id','person','route','binding','action','data'])||!/^syn18-request-[a-zA-Z0-9-]+$/.test(e.id)||e.person!=='syn18-member'||e.route!=='B'||!e.data||Array.isArray(e.data)||typeof e.data!=='object')fail('binding');
   const fp=JSON.stringify(e);
   if(done.has(e.id)){
    if(done.get(e.id)!==fp)fail('duplicate_conflict');
    if(e.action!=='revoke'){gate();}
    return {ok:true,reason:'idempotent',state:view()};
   }
   if(e.binding!==binding())fail('version_conflict');
   if(!['sources','restore','edit'].includes(e.action)&&!exact(e.data,[]))fail('payload');
   if(e.action==='revoke'){s.revoked=true;s.draft=null;s.status='blocked';}
   else{
    if(s.revoked||!consent(s.sources))fail('consent');
    if(e.action==='sources'){
     shape(e.data);const p=s.sources,n=e.data;
     if(n.clock!==p.clock||n.revision!==p.revision+1||n.link.version<p.link.version)fail('source_version');
     for(const key of ['training','nutrition']){
      if(n[key].revision<p[key].revision||(!same(n[key],p[key])&&n[key].revision!==p[key].revision+1))fail('source_version');
      const nc=n[key].fixture.catalog,pc=p[key].fixture.catalog;
      if(nc.version<pc.version||(!same(nc,pc)&&nc.version<=pc.version))fail('source_version');
     }
     if(!same(n.link,p.link)&&n.link.version!==p.link.version+1)fail('source_version');
     s.sources=copy(n);s.healthLatch=s.healthLatch||health(n);s.draft=null;s.selection=null;s.restores=null;s.status='reassess';
    }else if(e.action==='reject'){
     if(!['pending','confirmed'].includes(s.status))fail('status');s.draft=null;s.status='rejected';
    }else{
     const current=gate();
     if(e.action==='build'){s.draft=current;s.restores=null;s.status='pending';}
     else if(e.action==='edit'){
      if(!['pending','confirmed'].includes(s.status)||!exact(e.data,['domain','value']))fail('payload');
      const pair=copy(current);
      if(e.data.domain==='training_day')pair.training.sessions[0].day=e.data.value;
      else if(e.data.domain==='nutrition_moment'){
       const raw=N.raw(pair.nutrition);raw[0].moment=e.data.value;pair.nutrition=N.calculate(raw,s.sources.nutrition.fixture.intake,s.sources.nutrition.fixture.catalog,s.clock);
      }else fail('payload');
      T.validatePlan(pair.training,s.sources.training.fixture.intake,s.sources.training.fixture.catalog);
      N.validatePlan(pair.nutrition,s.sources.nutrition.fixture.intake,s.sources.nutrition.fixture.catalog,s.clock);
      s.selection={training:pair.training,nutrition:pair.nutrition};s.draft=gate();s.restores=null;s.status='pending';
     }
     else if(e.action==='confirm'){
      if(s.status!=='pending'||!same(s.draft,current))fail('status');s.status='confirmed';
     }else if(e.action==='activate'){
      if(s.status!=='confirmed'||!same(s.draft,current))fail('version_conflict');
      // Prepare both snapshots before a single in-memory commit.
      const training=copy(current.training);if(options.fault==='after_training')fail('atomic_fault');
      const nutrition=copy(current.nutrition);if(options.fault==='after_nutrition')fail('atomic_fault');
      const next={version:s.version+1,training,nutrition,source:copy(s.sources),at:s.clock,restores:s.restores};
      s.version++;s.active=next;s.history.push(copy(next));s.draft=null;s.status='active';
     }else if(e.action==='restore'){
      if(!exact(e.data,['version'])||!int(e.data.version)||e.data.version===s.version)fail('version_conflict');
      const previous=s.history.find(x=>x.version===e.data.version);if(!previous)fail('version_conflict');
      // Do not pretend an old instruction was issued under a newer source version.
      if(!same(previous.source,s.sources))fail('restore_source');
      s.selection={training:copy(previous.training),nutrition:copy(previous.nutrition)};s.draft=gate();s.restores=e.data.version;s.status='pending';
     }else fail('action');
    }
   }
   if(options.fault==='before_commit')fail('atomic_fault');
   s.epoch++;s.clock+=1000;s.audit.push({request:e.id,action:e.action,from:old.version,to:s.version,source:s.sources.revision,training:s.sources.training.revision,nutrition:s.sources.nutrition.revision,status:s.status,at:s.clock,restore:e.action==='restore'?e.data.version:null});
   done.set(e.id,fp);return {ok:true,reason:'success',state:view()};
  }catch(e){s=old;return {ok:false,reason:e.message,state:view()};}
 }
 return Object.freeze({event,command,view});
}
const api={copy,same,shape,inspect,create};if(typeof module==='object')module.exports=api;else root.FMZ18Model=api;
})(globalThis);
