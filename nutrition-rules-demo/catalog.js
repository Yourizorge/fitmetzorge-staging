/* All numbers and product values are fictional test fixtures, not dietary advice. */
(function(root){"use strict";
const fields=['goal','age','eligible','height','weight','activity','trainingFrequency','target','meals','moments','favorites','excluded','allergies','diet','restrictions','maxRecipes','prepMinutes','budget','language','units','health','consent'];
const foods=[
 ['rice',['Rijst (test)','Rice (test)','Reis (Test)'],['rijst','rice','reis'],'grain',130,2,28,1,[],2],
 ['potato',['Aardappel (test)','Potato (test)','Kartoffel (Test)'],['aardappel','potato','kartoffel'],'grain',80,2,17,0,[],2],
 ['beans',['Bonen (test)','Beans (test)','Bohnen (Test)'],['bonen','beans','bohnen'],'protein',110,7,18,1,[],3],
 ['lentils',['Linzen (test)','Lentils (test)','Linsen (Test)'],['linzen','lentils','linsen'],'protein',120,8,19,1,[],3],
 ['tofu',['Tofu (test)','Tofu (test)','Tofu (Test)'],['tofu','sojablok'],'protein',140,14,2,8,['soy'],4],
 ['peanut',['Pinda (test)','Peanut (test)','Erdnuss (Test)'],['pinda','arachide','groundnut','peanut','erdnuss'],'protein',560,25,16,46,['peanut'],1],
 ['vegetables',['Groente (test)','Vegetables (test)','Gemuese (Test)'],['groente','vegetables','gemuese'],'vegetable',30,2,5,0,[],2],
 ['oil',['Olie (test)','Oil (test)','Oel (Test)'],['olie','oil','oel'],'fat',900,0,0,100,[],0]
].map(([id,name,aliases,category,kcal,protein,carb,fat,allergens,prep])=>({id,version:1,name,aliases,category,unit:'g',basis:100,nutrients:{energy:kcal*1000,protein:protein*1000,carb:carb*1000,fat:fat*1000},allergens,mayContain:[],diet:'plant',budget:'low',prep,ingredients:[id],review:'synthetic_unreviewed'}));
const recipes=[['bowl','beans'],['lentil_bowl','lentils'],['tofu_bowl','tofu'],['peanut_bowl','peanut']].map(([id,protein])=>({id,version:1,name:id==='bowl'?['Rijst-bonenkom','Rice and bean bowl','Reis-Bohnen-Schale']:id==='lentil_bowl'?['Linzenkom','Lentil bowl','Linsenschale']:id==='tofu_bowl'?['Tofukom','Tofu bowl','Tofuschale']:['Pindakom','Peanut bowl','Erdnussschale'],items:['rice',protein,'vegetables','oil'].map(food=>({food,version:1})),prep:10,review:'synthetic_unreviewed'}));
const rule={id:'syn17-existing-target-rule',version:1,required:fields.filter(x=>x!=='budget'),method:'existing_target_only',calculation_rule:null,validation:'synthetic_unreviewed',categories:['grain','protein','vegetable','fat'],excludedAllergens:[],excludedProducts:[],rounding:'exact_milli_no_rounding',portionUnit:'g',
 portions:{grain:{min:50,max:400,step:25},protein:{min:50,max:300,step:25},vegetable:{min:50,max:400,step:25},fat:{min:5,max:20,step:5}},
 substitutions:{grain:['rice','potato'],protein:['beans','lentils','tofu','peanut'],vegetable:['vegetables'],fat:['oil']},
 layouts:[{meals:2,distribution:[50,50],grams:[300,225,300,15]},{meals:3,distribution:[34,33,33],grams:[200,150,200,10]},{meals:4,distribution:[25,25,25,25],grams:[150,100,150,10]}],
 reason:['Bestaand doel en expliciete conceptcatalogus; geen nieuw doel berekend.','Existing target and explicit concept catalog; no new target calculated.','Bestehendes Ziel und expliziter Konzeptkatalog; kein neues Ziel berechnet.']};
const clock=Date.UTC(2026,9,1,10),target={id:'syn17-target',version:1,person:'syn17-member',goal:'maintain',source:'synthetic-existing-record',at:clock-3600000,expires:clock+82800000,
 totals:{energy:1800000,protein:60000,carb:280000,fat:45000},bounds:{energy:{min:1500000,max:2100000},protein:{min:40000,max:100000},carb:{min:200000,max:330000},fat:{min:25000,max:80000}},review:'synthetic_unreviewed'};
const data={id:'syn17-food-catalog',version:1,effective:clock-86400000,expires:clock+86400000,synthetic_only:true,validation:'synthetic_unreviewed',foods,recipes,rules:[rule],targets:[target],calculationRules:[]};
const api={data,fields,clock};if(typeof module==='object')module.exports=api;else root.FMZ17Catalog=api;
})(globalThis);
