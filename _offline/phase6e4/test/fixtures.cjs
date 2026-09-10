"use strict";
const engine=require("../engine.cjs"),flow=require("../../phase6e1/flow.cjs"),helpers=require("../../phase6e1/test/helpers.cjs"),prereg=require("../preregistered-cases.json");
const clone=x=>JSON.parse(JSON.stringify(x)),DAY=86400000;
function setup(c={}){
  const locale=c.locale||"nl",scenario=c.scenario||"ordinary";
  let state=flow.create(prereg.fixture.subject_id),clock=prereg.clock_ms-1,previous=null,options={};
  function apply(type,body){const e={...helpers.event(state,type,body),at_ms:++clock};const r=flow.apply(state,e);if(r.state===state)throw Error("fixture "+r.status);state=r.state;return r;}
  function send(text,availability="available"){return apply("message",{expected_revision:state.revision,message_id:"syn-message-"+(state.revision+1),text,locale,availability});}
  const normal={nl:"Ik train mijn benen",en:"I train my legs",de:"Ich trainiere meine Beine"}[locale];
  const first=c.text!==undefined?c.text:
    ["unclear","clarified","continue_chat","clarification_other_health"].includes(scenario)?"flurbel":
    ["current","serious_recovered","recurring","new_after_recovery","technical_retry_health"].includes(scenario)?"Ik heb borstpijn":
    ["unclassified","self_reported","expired","expired_fresh","missing","missing_fresh","unnecessary","unnecessary_fresh"].includes(scenario)?"Mijn borst voelt loodzwaar":
    scenario==="unbound_recovery"?"Mijn klachten zijn voorbij":
    scenario==="historical"?"Vorige maand had ik borstpijn":scenario==="negated"?"Ik heb geen pijn op de borst":
    scenario==="quoted"?'"Ik heb borstpijn" is een citaat.':normal;
  if(scenario!=="no_message")send(first,c.availability||(["technical","technical_retry","technical_retry_health"].includes(scenario)?"unavailable":"available"));
  else clock=prereg.clock_ms;
  if(scenario==="clarification_other_health")send("Ik heb borstpijn");
  if(["self_reported","serious_recovered","recurring","new_after_recovery"].includes(scenario)){
    apply("self_report",{expected_revision:state.revision,targets:state.issues.filter(i=>i.kind==="health_report").map(i=>({message_id:i.message_id,source_revision:i.source_revision})),
      method:"chat",confirmed:false,text:"Mijn klachten zijn voorbij",locale:"nl"});
    if(scenario==="recurring")send("Ik heb borstpijn");
    if(scenario==="new_after_recovery")send("Nu heb ik moeite met ademhalen");
  }
  if(["technical_retry","technical_retry_health","clarified","clarification_other_health"].includes(scenario)){
    const issue=state.issues.find(i=>i.kind!=="health_report"),mode=issue.kind==="technical"?"retry":"clarify";
    const attempt=apply("begin",{expected_revision:state.revision,message_id:issue.message_id,source_revision:issue.source_revision,mode});
    apply(mode,mode==="retry"?{binding:attempt.binding,availability:"available"}:{binding:attempt.binding,text:"Ik bedoelde mijn borsttraining met gewichten",locale:"nl"});
  }
  if(scenario==="continue_chat")send(normal);
  if(/^(expired|missing|unnecessary)/.test(scenario)){
    previous=engine.prepare(state,clock);
    if(scenario.startsWith("expired"))clock=prereg.clock_ms+30*DAY;
    if(scenario.startsWith("missing"))options={missing_message_ids:[state.messages[0].id]};
    if(scenario.startsWith("unnecessary"))options={unnecessary_message_ids:[state.messages[0].id]};
    previous=engine.prepare(state,clock,options,previous);
    if(scenario.endsWith("_fresh"))send(normal);
  }
  const context=engine.prepare(state,clock,options,previous),sources=clone(prereg.fixture);
  sources.readset.read_at_ms=clock;
  const request={synthetic_only:true,locale,binding:clone(context.binding),expected_readset:{id:sources.readset.id,revision:sources.readset.revision},sources};
  for(const {path,value}of c.changes||[]){let target=sources;for(const key of path.slice(0,-1))target=target[key];target[path.at(-1)]=clone(value);}
  const authority={...clone(helpers.authority),subject_id:state.subject_id};
  if(c.authority_change)authority[c.authority_change.field]=c.authority_change.value;
  return {state,clock,context,request,authority,options};
}
function run(c={}){const f=setup(c);return engine.suggest(f.request,f.context,f.authority);}
module.exports={setup,run,clone,engine,flow,helpers,prereg,DAY};
