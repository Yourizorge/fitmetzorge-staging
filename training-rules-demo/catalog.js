/* Fictional, unreviewed Route B rule catalog. Never a medical/training standard. */
(function(root){"use strict";
const X=typeof module==="object"?require("../coach-review-demo/catalog.js"):root.FMZ8Catalog;
const exercises=X.exercises.map(x=>({...JSON.parse(JSON.stringify(x)),type:["raise","deadbug","bandpull"].includes(x.id)?"accessory":"compound",role:["raise","deadbug","bandpull"].includes(x.id)?"support":"main"}));
const rules=[];
for(const goal of ["fitness","muscle","strength"])for(const experience of ["beginner","experienced"])for(const role of ["main","support"]){
 const main=role==="main",advanced=experience==="experienced",strength=goal==="strength";
 const sets=main?(advanced?[3,5,4]:[2,3,2]):(advanced?[2,4,3]:[1,2,1]);
 const reps=strength?(main?[3,6,5]:[6,10,8]):(main?[8,12,10]:[10,15,12]);
 const rest=strength?(main?[90,180,120]:[60,120,75]):(main?[45,120,advanced?90:60]:[30,90,advanced?60:45]);
 rules.push({id:"syn16-"+goal+"-"+experience+"-"+role,version:1,goal,experience,role,type:main?"compound":"accessory",
 frequencies:[2,4],minutes:[10,15,30,45,60],sets:{min:sets[0],max:sets[1],default:sets[2],step:1},
 reps:{min:reps[0],max:reps[1],default:reps[2],step:1},rest:{min:rest[0],max:rest[1],default:rest[2],step:15},
 rir:{min:0,max:4,default:main?3:2,step:1},rpe:{min:1,max:10,default:main?7:6,step:1},
 alternatives:exercises.filter(e=>e.role===role).map(e=>e.id),timing:{rep_seconds:3,setup_seconds:45},
 progression:{kind:"reps",step:1,ceiling:reps[1],automatic:false},
 reason:["Bestaande conceptregel voor dit doel, deze ervaring en oefenrol.","Existing concept rule for this goal, experience and exercise role.","Bestehende Konzeptregel fuer Ziel, Erfahrung und Uebungsrolle."]});
}
const data={id:"syn16-training-rules",version:1,source:"synthetic-platform-catalog",review:"unreviewed",effective:1790812800000,expires:1798761600000,
 overhead_seconds:180,exercises,rules,layouts:[{id:"syn16-week2",version:1,frequency:2,roles:["main","support"]},{id:"syn16-week4",version:1,frequency:4,roles:["main","support"]}]};
const api={data};if(typeof module==="object")module.exports=api;else root.FMZ16Catalog=api;
})(globalThis);
