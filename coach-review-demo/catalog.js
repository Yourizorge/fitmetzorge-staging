/* Versioned fictional fixtures. No real-member prescription or nutrition database. */
(function(root){"use strict";
const exercises=[
 ["squat",["Goblet squat","Goblet squat","Goblet-Kniebeuge"],"legs","dumbbell",["deep_knee"],["strength","muscle"]],
 ["row",["Dumbbell roeien","Dumbbell row","Kurzhantelrudern"],"back","dumbbell",[],["strength","muscle"]],
 ["press",["Vloerdrukken","Floor press","Bodendruecken"],"chest","dumbbell",[],["strength","muscle"]],
 ["bridge",["Heupbrug","Hip bridge","Hueftbruecke"],"legs","mat",[],["consistency","muscle"]],
 ["bandrow",["Elastiek roeien","Band row","Bandrudern"],"back","band",[],["consistency","strength"]],
 ["wallpress",["Muurdrukken","Wall push-up","Wandliegestuetz"],"chest","mat",[],["consistency","strength"]],
 ["raise",["Zijwaarts heffen","Lateral raise","Seitheben"],"shoulders","dumbbell",[],["muscle","strength"]],
 ["overhead",["Schouderdrukken","Shoulder press","Schulterdruecken"],"shoulders","dumbbell",["overhead"],["strength","muscle"]],
 ["deadbug",["Dead bug","Dead bug","Dead Bug"],"core","mat",[],["consistency","strength"]],
 ["bandpull",["Elastiek uit elkaar","Band pull-apart","Band auseinanderziehen"],"shoulders","band",[],["consistency","muscle"]]
].map(([id,label,muscle,equipment,constraints,goals])=>({id,label,muscle,equipment,constraints,goals}));
// kcal/protein/carbohydrate/fat per 100 g are intentionally synthetic fixture values.
const foods=[
 ["rice",["Rijst","Rice","Reis"],[130,3,28,1],[],true,"none",0.20],
 ["beans",["Bonen","Beans","Bohnen"],[100,7,16,1],[],true,"none",0.30],
 ["lentils",["Linzen","Lentils","Linsen"],[110,8,18,1],[],true,"none",0.30],
 ["vegetables",["Groenten","Vegetables","Gemuese"],[40,2,6,1],[],true,"none",0.30],
 ["potato",["Aardappel","Potato","Kartoffel"],[90,2,19,0],[],true,"microwave",0.20],
 ["oats",["Haver","Oats","Hafer"],[370,12,60,7],["gluten"],true,"none",0.20],
 ["fruit",["Fruit","Fruit","Obst"],[60,1,14,0],[],true,"none",0.25],
 ["yogurt",["Yoghurt","Yogurt","Joghurt"],[70,5,6,3],["dairy"],false,"none",0.30],
 ["tofu",["Tofu","Tofu","Tofu"],[120,12,3,7],["soy"],true,"full",0.70],
 ["nuts",["Noten","Nuts","Nuesse"],[600,18,12,54],["nuts"],true,"none",1.00]
].map(([id,label,nutrients,allergens,plant,kitchen,cost])=>({id,label,nutrients,allergens,plant,kitchen,cost}));
const recipes=[
 ["ricebeans",["Rijst-bonenkom","Rice and beans","Reis-Bohnen-Schale"],[["rice",220],["beans",180],["vegetables",150]]],
 ["ricelentils",["Rijst-linzenkom","Rice and lentils","Reis-Linsen-Schale"],[["rice",220],["lentils",180],["vegetables",150]]],
 ["beansalad",["Bonen-linzensalade","Bean and lentil salad","Bohnen-Linsen-Salat"],[["beans",200],["lentils",150],["vegetables",200]]],
 ["potatobowl",["Aardappel-linzenkom","Potato and lentils","Kartoffel-Linsen-Schale"],[["potato",300],["lentils",180],["vegetables",150]]],
 ["oatbowl",["Haver-fruitkom","Oats and fruit","Hafer-Obst-Schale"],[["oats",100],["fruit",200],["nuts",20]]],
 ["yogurtbowl",["Yoghurt met fruit","Yogurt and fruit","Joghurt mit Obst"],[["yogurt",300],["fruit",200],["oats",70]]],
 ["tofubowl",["Tofu-rijstkom","Tofu and rice","Tofu-Reis-Schale"],[["tofu",200],["rice",200],["vegetables",150]]]
].map(([id,label,items])=>({id,label,items:items.map(([food,g])=>({food,g}))}));
const defaults={goal:"strength",secondary:["mobility"],experience:"beginner",days:["mon","wed","fri"],minutes:30,equipment:["mat","dumbbell","band"],favorites:["row"],avoided:[],movement:[],rir:true,rpe:true,diet:"plant",allergies:[],excludedFoods:[],meals:3,kitchen:"full",budget:"low",rhythm:"early",sleep:7,recovery:"okay",unit:"kg"};
const policy={id:"syn-coach-policy@1",catalog:"syn-catalog@1",nutrition:"syn-portions@1",sleep:"syn-sleep@1",progression:"syn-reps@1",
 sets:{beginner:2,regular:3},reps:{strength:8,muscle:10,consistency:8},repMax:12,repStep:1,
 rest:{strength:90,muscle:75,consistency:60},sleepGoal:8,budget:{low:8,medium:14},expires:1798761600000};
const signals={
 sleep:{values:[6,6,5.5],window:"3 days",kind:"sleep",unchanged:["training","nutrition"]},
 recovery:{values:["low","low","low"],window:"3 days",kind:"checkin",unchanged:["training","nutrition"]},
 rpe:{values:[7,8,9],window:"3 workouts",kind:"facts",unchanged:["training","nutrition","recovery"]},
 rir:{values:[3,2,1],window:"3 workouts",kind:"facts",unchanged:["training","nutrition","recovery"]},
 missed:{values:[false,false,true],window:"1 week",kind:"schedule",unchanged:["nutrition","recovery"]},
 food:{values:[1,0,1],window:"3 days",kind:"facts",unchanged:["training","nutrition","recovery"]},
 plateau:{values:[8,8,8],window:"3 workouts",kind:"swap",unchanged:["nutrition","recovery"]},
 improvement:{values:[8,9,10],window:"3 workouts",kind:"reps",unchanged:["nutrition","recovery"]},
 outlier:{values:[5.5],window:"1 night",kind:"facts",unchanged:["training","nutrition","recovery"]}
};
const api={synthetic_only:true,exercises,foods,recipes,defaults,policy,signals};
function freeze(x){if(x&&typeof x==="object"){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
if(typeof module==="object"&&module.exports)module.exports=freeze(api);else root.FMZ8Catalog=freeze(api);
})(globalThis);
