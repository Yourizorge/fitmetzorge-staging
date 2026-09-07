const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"theme-authority.js"),"utf8");
const authKey="sb-mokxyyullfhkfalopbzd-auth-token",prefix="fmz.theme.v1:",user="member-a";
function boot({dark=false,local={},session={},url="https://yourizorge.github.io/fitmetzorge-staging/",blocked=false}={}){
 const storage=entries=>({getItem:k=>{if(blocked)throw new Error("blocked");return entries[k]??null;},setItem:(k,v)=>{if(blocked)throw new Error("blocked");entries[k]=v;}});
 const classes=new Set(),events={},media={matches:dark,addEventListener:(_n,fn)=>{media.change=fn;}},root={dataset:{},style:{}},meta={setAttribute:(_k,v)=>{meta.content=v;}};
 const document={documentElement:root,body:{classList:{toggle:(key,yes)=>yes?classes.add(key):classes.delete(key)}},querySelector:()=>meta};
 const c={document,localStorage:storage(local),sessionStorage:storage(session),location:{href:url},URL,URLSearchParams,Date,JSON,Event:class{constructor(type){this.type=type;}},matchMedia:()=>media,addEventListener:(n,f)=>{events[n]=f;},dispatchEvent:e=>events[e.type]?.(e)};
 c.window=c;vm.createContext(c);vm.runInContext(source,c);
 return {api:c.FMZ_THEME,root,classes,meta,local,events,c,system:value=>{media.matches=value;media.change();}};
}
test("fresh and legacy-global-only users default system",()=>{
 for(const local of [{},{"fmz-coach-app-v1":JSON.stringify({ui:{theme:"dark"}})}]){
  const a=boot({local});assert.equal(a.root.dataset.theme,"light");assert.equal(a.root.dataset.themeMode,"system");
  a.system(true);assert.equal(a.root.dataset.theme,"dark");
 }
});
test("explicit choices resist system changes; automatic remains automatic",()=>{
 const a=boot({dark:true});a.api.setUser(user);
 assert.equal(a.api.accept(user,"light"),true);a.system(false);a.system(true);assert.equal(a.root.dataset.theme,"light");
 a.api.accept(user,"dark");a.system(false);assert.equal(a.root.dataset.theme,"dark");
 a.api.accept(user,"system");a.system(true);assert.equal(a.root.dataset.theme,"dark");a.system(false);assert.equal(a.root.dataset.theme,"light");
 assert.equal(a.root.dataset.themeMode,"system");
});
test("own-user cache is not shared and server value overrides cache",()=>{
 const a=boot();a.api.setUser(user);a.api.accept(user,"dark");
 a.api.setUser("member-b");assert.equal(a.root.dataset.theme,"light");
 assert.equal(a.api.accept(user,"light"),false);assert.equal(a.root.dataset.theme,"light");
 a.api.accept("member-b","light");a.api.setUser(user);assert.equal(a.root.dataset.theme,"dark");
 a.api.accept(user,"system");assert.equal(a.root.dataset.theme,"light");
});
test("logout follows system, later same-user login restores chosen mode",()=>{
 const a=boot();a.api.setUser(user);a.api.accept(user,"dark");a.api.clear();
 assert.equal(a.api.snapshot().owner,"");assert.equal(a.root.dataset.themeMode,"system");assert.equal(a.root.dataset.theme,"light");
 a.api.setUser(user);assert.equal(a.root.dataset.theme,"dark");
});
test("preview never persists before successful own-user response",()=>{
 const a=boot();a.api.setUser(user);a.api.accept(user,"dark");const old=a.local[prefix+user];
 a.api.preview(user,"light");assert.equal(a.root.dataset.theme,"light");assert.equal(a.local[prefix+user],old);
 a.api.accept(user,"dark");assert.equal(a.root.dataset.theme,"dark");
 assert.equal(a.api.preview("member-b","light"),false);
});
test("prepaint bootstrap only uses cache matching current unexpired session",()=>{
 const cache=JSON.stringify({user,mode:"dark"}),session=JSON.stringify({user:{id:user},expires_at:Date.now()/1000+300});
 const a=boot({local:{[prefix+user]:cache,[authKey]:session}});
 assert.equal(a.root.dataset.theme,"dark");assert.equal(a.meta.content,"#070b12");assert(a.classes.has("light")===false);
 const b=boot({local:{[prefix+user]:cache},session:{[authKey]:session}});assert.equal(b.root.dataset.theme,"dark");
 for(const raw of [null,"broken",JSON.stringify({user:{id:"member-b"},expires_at:Date.now()/1000+300}),JSON.stringify({user:{id:user},expires_at:1})]){
  const x=boot({local:{[prefix+user]:cache,[authKey]:raw}});assert.equal(x.root.dataset.theme,"light");
 }
});
test("public auth links and forced confirmation always follow system",()=>{
 for(const suffix of ["?type=signup","#type=recovery","#type=invite","?error=expired","?code=synthetic","#access_token=synthetic"]){
  const a=boot({url:"https://yourizorge.github.io/fitmetzorge-staging/"+suffix,local:{[prefix+user]:JSON.stringify({user,mode:"dark"}),[authKey]:JSON.stringify({user:{id:user},expires_at:Date.now()/1000+300})}});
  assert.equal(a.root.dataset.theme,"light",suffix);
 }
});
test("cache and storage failures fail to system without losing usable controls",()=>{
 for(const raw of ["bad",JSON.stringify({user:"other",mode:"dark"}),JSON.stringify({user,mode:"invalid"})]){
  const a=boot({local:{[prefix+user]:raw}});a.api.setUser(user);assert.equal(a.root.dataset.theme,"light");
 }
 const b=boot({blocked:true});b.api.setUser(user);assert(b.api.accept(user,"dark"));assert.equal(b.root.dataset.theme,"dark");
});
test("auth removal clears presentation; another user cache cannot change this user",()=>{
 const a=boot();a.api.setUser(user);a.api.accept(user,"dark");
 a.events.storage({key:prefix+"other",newValue:'{"mode":"light"}'});assert.equal(a.root.dataset.theme,"dark");
 a.events.storage({key:authKey,newValue:null});assert.equal(a.root.dataset.theme,"light");
});
test("theme color, body mirror and color scheme share one authority",()=>{
 const a=boot();assert.equal(a.root.style.colorScheme,"light");assert(a.classes.has("light"));assert.equal(a.meta.content,"#f7f8fa");
 a.system(true);assert.equal(a.root.style.colorScheme,"dark");assert(!a.classes.has("light"));assert.equal(a.meta.content,"#070b12");
 vm.runInContext(source,a.c);assert.equal(a.c.FMZ_THEME,a.api);
});
