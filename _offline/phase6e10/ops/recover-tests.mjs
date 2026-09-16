import fs from "node:fs";
import path from "node:path";
import {broker,makeApi,root} from "../test/live.mjs";
import assert from "node:assert/strict";
if(fs.existsSync(path.join(root,"supabase/.temp/phase6e10-owner-window.json")))throw Error("owner_window_receipt_requires_explicit_owner_followup");
const b=broker();let cleaned=0;
try{
 const api=await makeApi(b);
 const home=(await api.raw("trainer",{op:"home"})).data;
 for(const w of home.windows||[]){
  assert.equal(w.package_version,"6e10@1");
  if(w.status==="cleaned")continue;
  if(w.status==="active"){
   const r=await api.raw("trainer",{op:"command",window:w.id,workspace:null,key:crypto.randomUUID(),expected:w.revision,action:"revoke",data:{}});
   assert.equal(r.status,200);
  }
  const current=(await api.raw("trainer",{op:"home"})).data.windows.find(x=>x.id===w.id);
  const r=await api.raw("trainer",{op:"command",window:w.id,workspace:null,key:crypto.randomUUID(),expected:current.revision,action:"cleanup",data:{}});
  assert.equal(r.status,200);cleaned++;
 }
 await b.call({op:"cleanup_controls"});
 console.log(JSON.stringify({test_windows_cleaned:cleaned,owner_window_not_opened:true,accounts_retained:3}));
}finally{b.assertQuiet();await b.close();}
