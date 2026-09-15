import {A,B,C,data} from "./frozen.mjs";
export {A,B,C,data};
const clone=x=>JSON.parse(JSON.stringify(x));
const fail=reason=>{throw Error(reason);};
const keys=(o,allowed)=>{if(!o||typeof o!=="object"||Array.isArray(o)||Object.keys(o).some(k=>!allowed.includes(k)))fail("payload_invalid");};
const exact=(o,required)=>{keys(o,required);if(Object.keys(o).length!==required.length)fail("payload_invalid");};
const actions=["open","build","edit","member_accept","member_reject","trainer_approve","trainer_reject","trainer_block","confirm","apply","reject","reopen","restore","signal","photo","clarify"];
export function validate(command,route){
 exact(command,["action","data"]);
 if(!actions.includes(command.action))fail("command_invalid");
 const {action,data:d}=command;
 if(action==="build"){exact(d,["intake"]);B.validateIntake(d.intake);}
 else if(action==="edit"){
 const shape={replace:["kind","session","index","id"],add:["kind","session","id"],remove:["kind","session","index"],
 move:["kind","session","index","to"],meal:["kind","index","id"],food:["kind","meal","index","id"],
 sleep:["kind","hours"],light_week:["kind"]}[d?.kind];
 if(!shape)fail("payload_invalid");exact(d,shape);
 for(const k of ["session","index","to","meal"])if(k in d&&(!Number.isInteger(d[k])||d[k]<0||d[k]>20))fail("payload_invalid");
 if("id" in d&&![...C.exercises,...C.recipes,...C.foods].some(x=>x.id===d.id))fail("payload_invalid");
 if("hours" in d&&![7,8,9].includes(d.hours))fail("payload_invalid");
 }else if(action==="restore"){exact(d,["version"]);if(!Number.isInteger(d.version)||d.version<1||d.version>500)fail("payload_invalid");}
 else if(action==="signal"){exact(d,["id"]);if(!Object.keys(C.signals).includes(d.id))fail("payload_invalid");}
 else if(action==="photo"){exact(d,["corroborated"]);if(typeof d.corroborated!=="boolean")fail("payload_invalid");}
 else if(action==="clarify"){exact(d,["source"]);if(d.source!=="syn-new-clear-context@1")fail("payload_invalid");}
 else exact(d,[]);
 if(route==="A"&&!["open","member_accept","member_reject","trainer_approve","trainer_reject","trainer_block","apply","restore"].includes(action))fail("route_action_denied");
 if(route==="B"&&action.startsWith("trainer_")||route==="B"&&action.startsWith("member_"))fail("route_action_denied");
}
export function replay(row){
 if(row.basis?.model&&row.basis.model!=="1993a8073f40c583f108cc6baa2ef78c1d522d52b81b0f6071f10f109ca4753b")fail("source_invalid");
 if(!["A","B"].includes(row.route)||!data.seeds[row.seed]||!Array.isArray(row.events)||row.events.length>500)fail("source_invalid");
 const model=row.route==="A"?A.create(data.seeds[row.seed]):B.create();
 for(const item of row.events){validate(item,row.route);execute(model,row.route,item);}
 return model;
}
function execute(model,route,c){
 if(c.action==="open")return;
 let r;
 if(route==="A"){
 const role=c.action.startsWith("trainer_")||c.action==="apply"?"trainer":"member";
 r=model.command(model.event(c.action,role,"cmd-backend-"+(model.view().revision+1),c.data.version??null));
 }else{
 if(c.action==="build"){r=model.command(model.event("intake",c.data.intake));if(!r.ok)fail(r.reason);}
 r=model.command(model.event(c.action,c.action==="build"?{}:c.data));
 }
 if(!r.ok)fail(r.reason);
}
function summary(row,model){
 const s=clone(model.view()),isA=row.route==="A";
 return {view:s,status:isA?s.proposal.status:s.status,version:isA?s.active.revision:s.revision,
 content:isA?s.active:s.active?.plan??null,candidate:isA?s.proposal.target:s.draft?.plan??null};
}
export async function digest(x){
 const bytes=new TextEncoder().encode(JSON.stringify(x));
 return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),x=>x.toString(16).padStart(2,"0")).join("");
}
export async function next(row,command){
 validate(command,row.route);
 const trainer=command.action.startsWith("trainer_")||(row.route==="A"&&command.action==="apply");
 if(row.actor_role!==(trainer?"trainer":"member"))fail("actor_denied");
 if(!row.consent)fail("consent_required");
 if(row.guard!=="clear"&&!["reject","member_reject","trainer_reject","trainer_block","clarify"].includes(command.action))fail("safety_block");
 const model=replay(row);execute(model,row.route,command);
 const result=summary(row,model);
 return {...result,event:clone(command),candidate_hash:result.candidate?await digest(result.candidate):null};
}
export function present(row){
 const result=summary(row,replay(row));
 delete result.view.audit;delete result.view.notifications;
 return {workspace:row.workspace,revision:row.revision,route:row.route,actor_role:row.actor_role,seed:row.seed,
 basis:row.basis,versions:clone(row.versions||[]),guard:row.guard,consent:row.consent,...result,
 synthetic_only:true,automatic_actions_allowed:false,physical_advice_authorized:false};
}
