import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import {broker,makeApi,root} from "../test/live.mjs";
const file=path.join(root,"supabase/.temp/phase6e10-owner-window.json");
if(fs.existsSync(file))throw Error("owner_window_exists_inspect_do_not_replace");
const receipt=p=>JSON.parse(fs.readFileSync(path.join(root,"supabase/.temp",p)));
assert.equal(receipt("phase6e10-live.json").pass,true);
assert.equal(receipt("phase6e10-browser-published/report.json").pass,true);
assert.equal(receipt("phase6e10-publication.json").pass,true);
assert.equal(receipt("phase6e10-regressions.json").counts.fail,0);
assert.equal(receipt("phase6e10-after.json").all_existing_unchanged,true);
const b=broker(),out={opened:false,synthetic_only:true,production_touched:false,emails:0,external_ai_calls:0};
try{
 const api=await makeApi(b);
 const request=async(role,p)=>{const r=await api.raw(role,p);assert.equal(r.status,200,JSON.stringify(r.data));return r.data;};
 let home=await request("trainer",{op:"home"});
 assert(home.operator);
 assert(!home.windows.some(w=>w.status==="active"||w.status==="prepared"),"unclosed_internal_window");
 // Guard later cleanup/tests before the first mutation, including uncertain responses.
 fs.writeFileSync(file,JSON.stringify(out,null,2)+"\n");
 const now=Date.now();
 const command=(window,expected,action,data,workspace=null)=>request("trainer",{op:"command",window,workspace,key:crypto.randomUUID(),expected,action,data});
 const prepared=await command(null,0,"prepare",{scenario:"kg",starts_at:new Date(now).toISOString(),ends_at:new Date(now+86400000-5000).toISOString()});
 out.window=prepared.window;fs.writeFileSync(file,JSON.stringify(out,null,2)+"\n");
 await command(prepared.window,prepared.revision,"activate",{});
 home=await request("trainer",{op:"home"});
 const workspace=home.workspaces.find(w=>w.window===prepared.window).workspace;
 let v=await request("trainer",{op:"read",window:prepared.window,workspace});
 await command(prepared.window,v.window.revision,"source_append",{body:v.source_template,valid_from:v.window.starts_at,valid_until:v.window.ends_at},workspace);
 v=await request("member",{op:"read",window:prepared.window,workspace});
 assert.equal(v.sources.length,1);assert.equal(v.sources[0].version,1);assert.equal(v.plans.length,1);assert.equal(v.proposals.length,0);
 const bh=await request("b",{op:"home"});assert(!bh.operator);assert.equal(bh.workspaces.length,1);
 const bv=await request("b",{op:"read",window:prepared.window,workspace:bh.workspaces[0].workspace});
 assert.equal(bv.route,"B");assert.equal(bv.sources.length,0);assert.equal(bv.plans.length,0);
 const cross=await api.raw("trainer",{op:"read",window:prepared.window,workspace:bh.workspaces[0].workspace});assert.equal(cross.status,403);
 const final=await request("trainer",{op:"home"});assert.equal(final.windows.filter(w=>w.status==="active").length,1);
 Object.assign(out,{opened:true,workspace,ends_at:v.window.ends_at,starts_at:v.window.starts_at,
 expires_nl:new Date(v.window.ends_at).toLocaleString("nl-NL",{timeZone:"Europe/Amsterdam",dateStyle:"full",timeStyle:"long"}),
 url:"https://yourizorge.github.io/fitmetzorge-staging/coach-source-demo/index.html",
 source_version:1,source_hash:v.sources[0].hash,identities:3,operator:"synthetic_a_trainer",cross_route_denied:true});
 fs.writeFileSync(file,JSON.stringify(out,null,2)+"\n");
 console.log(JSON.stringify(out));
}catch(e){console.error("owner_window_open_incomplete_inspect_receipt");process.exitCode=1;}
finally{b.assertQuiet();await b.close();}
