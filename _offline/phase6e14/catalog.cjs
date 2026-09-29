"use strict";
const A=require("../phase6e7/adapter.cjs"),B=require("../../coach-review-demo/model.js"),C=require("../../coach-review-demo/catalog.js");
const {hash,clone,freeze}=require("../phase6e5/common.cjs");
function trainer(name="normal"){
 const f=A.fixtures.setup(name),pack=A.fromFixture(f,name);
 const normalize=plan=>({training:{workout_id:plan.options[0].workout_id,exercises:plan.options[0].exercises.map(e=>({...clone(e),labels:clone(pack.catalog.find(c=>c.id===e.exercise_id).labels)}))},nutrition:null,recovery:null});
 return freeze({id:"syn-trainer-catalog-"+name,revision:1,before:normalize(pack.plan),after:normalize(pack.target),gate:pack.gate,
  refs:pack.refs,observations:pack.rows,rulebook:clone(f.book),
  history:clone(f.request.base.history),source_clock:f.clock,
  original_subject:f.request.base.base.sources.subject_id,
  source_sha256:hash({request:f.request,pack}),source_commit:"6479711ffb4fa97ad4934e8245c9ae334f5b1337"});
}
function independent(){
 const m=B.create();for(const action of ["build","confirm","apply"]){if(!m.command(m.event(action)).ok)throw Error("frozen_b_seed");}
 const before=clone(m.view().active.plan);
 const r=m.command(m.event("signal",{id:"missed"}));if(!r.ok)throw Error("frozen_b_signal");
 return freeze({id:C.policy.id,revision:1,before:{plan:before,intake:clone(C.defaults)},after:{plan:clone(r.state.draft.plan),intake:clone(C.defaults)},
  policy:clone(C.policy),signal:clone(C.signals.missed),source_sha256:hash(C),source_clock:1789293600000});
}
const catalogs=freeze({a_progression:trainer(),a_maintain:trainer("all_maintain"),a_lb:trainer("lb"),b_schedule:independent()});
module.exports={catalogs,B,C,hash,clone,freeze};
