"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const root=path.resolve(__dirname,"../../..");
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p)));
const sha=p=>crypto.createHash("sha256").update(fs.readFileSync(path.join(root,p))).digest("hex");
const files=["phase6e10-local.json","phase6e10-live.json","phase6e10-fresh.json","phase6e10-regressions.json","phase6e10-browser-local-ui/report.json","phase6e10-publication.json"];
const records=files.map(file=>{
 const p="supabase/.temp/"+file,r=read(p);
 return {file,sha256:sha(p),pass:r.pass??(r.counts?.fail===0),head:r.head,
  checks:r.checks,counts:r.counts,layouts:r.layouts,local_groups:r.local_groups,
  regressions:r.regressions,physical_phone:r.physical_phone,password_login_tested:r.password_login_tested,
  published_assets:r.assets?.length,private_404:r.private?.filter(x=>x.status===404).length};
});
const out={status:"VERIFICATION BLOCKED / NOT READY FOR OWNER RETEST",implementation_commit:"03eb55af7ab1897a3c6a12b82fcb5d182e88c4de",
 owner_window_open:false,owner_accepted:false,phase6e11_started:false,production_touched:false,
 historical_successful_receipts:records,investigation:read("docs/PHASE6E10_READONLY_INVESTIGATION.json"),
 pending:["Confirm legitimate human use of the non-enrolled password session; logs alone cannot do this.",
  "If resolved, explicitly document separate reconciled baseline without overwriting original evidence.",
  "Run final published UI workflow, post-test fingerprints and fresh owner window only after the gate is satisfied."],
 limits:["No overall technical pass or all-original-data-unchanged claim.","Historical tests are not reclassified as fresh hosted verification.",
  "Synthetic authority and manually selected safety fixtures do not establish real authority or medical reliability."]};
fs.writeFileSync(path.join(root,"docs/PHASE6E10_VERIFICATION_PENDING.json"),JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({status:out.status,receipts:records.length,original_unchanged:out.investigation.unchanged_tables}));
