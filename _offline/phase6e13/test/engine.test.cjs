"use strict";
const test=require("node:test"),a=require("node:assert/strict");
const {fixture,scenarios,seal,corrected,restore}=require("../fixtures.cjs"),{evaluate,hash,clone}=require("../engine.cjs"),safety=require("../safety.cjs"),{copy}=require("../../../proactive-signals-demo/copy.js");
const candidates=new Set(["changes","sleep_only","recovery_only","nutrition_only","training_only","zero","independent","self_reported"]);
const facts=new Set(["current","unclassified","recurring","expired_context","missing_context","technical","unclear"]);
for(const l of ["nl","en","de"])for(const n of scenarios)test(l+" "+n+" expected contract",()=>{
 const f=fixture(n,l),before=hash(f.bundle),r=evaluate(f.bundle,f.gate,l);
 a.equal(r.status,candidates.has(n)?"candidate_only":facts.has(n)?"facts_only":n==="unchanged"?"unchanged":"blocked");
 a.equal(r.automatic_actions_allowed,false);a.equal(r.physical_advice_authorized,false);a.equal(r.medical_clearance,false);a.equal(r.trainer_sharing,false);a.equal(hash(f.bundle),before);
 if(r.status==="candidate_only"){a.equal(r.proposal.type,"nonphysical_record_review");a.match(r.proposal.text,new RegExp(copy[l].proposal.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")));a.equal(r.proposal.source_hash,hash(f.bundle));}
 else a.equal(r.proposal,null);
 if(n==="consent_revoked"){a.equal(r.access.chat,true);a.equal(r.access.history,true);a.equal(r.facts.length,0);}
});
test("exact transparent arithmetic and references",()=>{
 const f=fixture(),r=evaluate(f.bundle,f.gate);
 a.deepEqual(r.calculations.map(c=>[c.metric,c.previous.sum,c.current.sum,c.delta_numerator,c.delta_divisor]),[
 ["sleep",1350,1080,-270,3],["recovery",24,18,-6,3],["nutrition",6600,5700,-900,3],["training",18,12,-6,1]]);
 a(r.calculations.every(c=>c.previous.refs.length===3&&c.current.refs.length===3));
 a.deepEqual(r.changes,["sleep","recovery","nutrition","training"]);
});
for(const metric of ["sleep","recovery","nutrition","training"])test("only "+metric+" signal",()=>{
 const f=fixture(metric+"_only");a.deepEqual(evaluate(f.bundle,f.gate).changes,[metric]);
});
const negatives={
 "different subject":b=>b.subject_id="syn-other",
 "unknown route":b=>b.route="TRAINER_FREE",
 "missing goal":b=>b.goal_ref=null,
 "empty snapshot":b=>b.snapshot_ref.id="",
 "unauthorized policy":b=>b.policy.window_days=7,
 "extra private field":b=>b.chat_text="must not be emitted",
 "future source":(b,g)=>b.issued_at_ms=g.now_ms+1,
 "expired exact boundary":(b,g)=>b.valid_until_ms=g.now_ms,
 "overlong validity":(b,g)=>b.valid_until_ms=g.now_ms+2*safety.DAY,
 "future window":(b,g)=>b.window_end_ms+=safety.DAY,
 "stale window":b=>b.window_end_ms-=2*safety.DAY,
 "missing row":b=>b.rows.pop(),
 "extra row":b=>b.rows.push(clone(b.rows[0])),
 "duplicate ID":b=>b.rows[1].id=b.rows[0].id,
 "duplicate date":b=>b.rows[1].day_ms=b.rows[0].day_ms,
 "overlap previous window":b=>b.rows[0].day_ms=b.rows[3].day_ms,
 "bad unit":b=>b.rows[0].unit="h",
 "wrong method":b=>b.rows[0].method="inferred",
 "missing value":b=>b.rows[0].value=null,
 "fractional minute":b=>b.rows[0].value=4.3,
 "NaN":b=>b.rows[0].value=NaN,
 "out of range time":b=>b.rows[0].value=1441,
 "negative":b=>b.rows[0].value=-1,
 "zero recovery is not allowed":b=>b.rows[6].value=0,
 "disputed":b=>b.rows[0].quality="disputed",
 "partial":b=>b.rows[0].coverage="partial",
 "foreign row":b=>b.rows[0].subject_id="syn-other",
 "changed historical goal":b=>b.rows[0].goal_ref.revision++,
 "changed historical plan":b=>b.rows[0].snapshot_ref.revision++,
 "zero row version":b=>b.rows[0].revision=0,
 "extra row field":b=>b.rows[0].note="private",
 "fractional day":b=>b.rows[0].day_ms++,
 "unknown metric":b=>b.rows[0].metric="body_fat",
 "independent forged trainer":b=>b.route="INDEPENDENT"
};
for(const [name,mutate]of Object.entries(negatives))test(name+" blocks all conclusions",()=>{
 const f=fixture();mutate(f.bundle,f.gate);seal(f.bundle);const r=evaluate(f.bundle,f.gate);a.equal(r.status,"blocked");a.equal(r.proposal,null);a.equal(r.facts.length,0);
});
for(const change of [b=>b.source_manifest[0].sha256="0".repeat(64),b=>b.source_manifest[0].revision++,b=>b.source_manifest.pop(),b=>b.source_manifest[1]=b.source_manifest[0]])test("manifest tamper "+String(change),()=>{
 const f=fixture();change(f.bundle);a.equal(evaluate(f.bundle,f.gate).status,"blocked");
});
test("forged safety receipt is rejected",()=>{const f=fixture();a.equal(evaluate(f.bundle,clone(f.gate)).reason,"unissued_safety");});
test("exact valid expiry minus one",()=>{const f=fixture();f.bundle.valid_until_ms=f.gate.now_ms+1;a.equal(evaluate(f.bundle,f.gate).status,"candidate_only");});
test("integer zeros not missing",()=>{const f=fixture("zero"),r=evaluate(f.bundle,f.gate);a.equal(r.facts.find(x=>x.metric==="sleep").current.sum,0);a.equal(r.facts.find(x=>x.metric==="training").current.sum,0);});
test("any actual numerical difference is explicit DEMO rule not clinical threshold",()=>{
 const f=fixture("unchanged");f.bundle.rows[0].value++;seal(f.bundle);a.deepEqual(evaluate(f.bundle,f.gate).changes,["sleep"]);
});
test("input order does not change calculation order",()=>{
 const f=fixture(),g=clone(f.bundle);g.rows.reverse();g.source_manifest.reverse();a.deepEqual(evaluate(g,f.gate).calculations,evaluate(f.bundle,f.gate).calculations);
});
test("original and correction remain immutable on restore with fresh versions",()=>{
 const one=fixture(),h=hash(one.bundle),two=corrected(one),three=restore(two,one);
 a.equal(hash(one.bundle),h);a.equal(three.bundle.revision,3);a.equal(three.bundle.previous_hash,hash(two.bundle));
 a.equal(three.bundle.rows[0].value,one.bundle.rows[0].value);a.equal(three.bundle.rows[0].revision,3);a.notEqual(hash(three.bundle),hash(one.bundle));
});
test("current health preserves facts/chat but cannot produce review",()=>{const f=fixture("current"),r=evaluate(f.bundle,f.gate);a.equal(r.facts.length,4);a.equal(r.access.chat,true);a(r.feedback.length>0);});
test("self report remains nonphysical and retains explicit no clearance",()=>{const f=fixture("self_reported"),r=evaluate(f.bundle,f.gate);a.equal(r.context_mode,"self_reported");a.equal(r.medical_clearance,false);a(r.feedback.some(t=>t.includes("geen medische vrijgave")));});
test("O5 expiry removes safety record, not permission to invent clearance",()=>{const f=fixture("expired_context"),r=evaluate(f.bundle,f.gate);a.equal(r.context_mode,"context_missing");a.equal(r.proposal,null);});
test("private chat revocation is not silently bypassed for new reflection",()=>{const f=fixture(),g=safety.create("chat_revoked");f.bundle.issued_at_ms=g.now_ms;f.bundle.valid_until_ms=g.now_ms+safety.DAY;a.equal(evaluate(f.bundle,g).status,"facts_only");});
test("unrecognized German paraphrase OBSERVATION ONLY; not recognition success",()=>{a.equal(safety.create("german_observation","de").mode,"clarification");});
