(function(root){"use strict";
const C=typeof module==="object"?require("./catalog.js").data:root.FMZ16Catalog.data,copy=x=>JSON.parse(JSON.stringify(x));
const clock=Date.UTC(2026,9,1,10),base={synthetic_only:true,route:"B",person:"syn16-member",clock,catalog:copy(C),
 intake:{goal:"fitness",experience:"beginner",days:["mon","wed","fri"],frequency:2,minutes:30,equipment:["mat","dumbbell","band"],favorites:["row"],excluded:[],rir:false,rpe:false,unit:"kg",health:"none",consent:true,history:null}};
const edits={beginner:()=>{},muscle:f=>{f.intake.goal="muscle";f.intake.experience="experienced";},strength:f=>{f.intake.goal="strength";f.intake.experience="experienced";},short:f=>f.intake.minutes=10,
 days:()=>{},equipment:f=>{f.intake.equipment=["mat"];f.intake.favorites=["bridge"];},preferences:f=>{f.intake.favorites=["bridge"];f.intake.excluded=["row","squat"];},
 valid_edit:()=>{},invalid_edit:()=>{},rules:()=>{},rir:f=>f.intake.rir=true,both:f=>{f.intake.rir=true;f.intake.rpe=true;},
 units:f=>{f.intake.history=[{id:"syn16-history-1",person:"syn16-member",exercise:"row",session:"syn16-session-1",version:1,at:clock-3600000,expires:clock+82800000,weight:{value:20,unit:"kg"},reps:10,rir:0,rpe:null}];},
 source:()=>{},restore:()=>{},safety:()=>{}};
const cases={};for(const [k,edit]of Object.entries(edits)){cases[k]=copy(base);edit(cases[k]);}
const api={base,cases};if(typeof module==="object")module.exports=api;else root.FMZ16Fixtures=api;
})(globalThis);
