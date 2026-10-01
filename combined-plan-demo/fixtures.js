(function(root){"use strict";
const T=typeof module==='object'?require('../training-rules-demo/fixtures.js'):root.FMZ16Fixtures;
const N=typeof module==='object'?require('../nutrition-rules-demo/fixtures.js'):root.FMZ17Fixtures;
const copy=x=>JSON.parse(JSON.stringify(x)),clock=T.base.clock,training=copy(T.base),nutrition=copy(N.base);
nutrition.intake.trainingFrequency=N.known(2);
const base={synthetic_only:true,route:'B',person:'syn18-member',clock,revision:1,
 link:{id:'syn18-explicit-link',version:1,person:'syn18-member',trainingPerson:'syn16-member',nutritionPerson:'syn17-member',trainingGoal:'fitness',nutritionGoal:'maintain',at:clock-1000,expires:clock+3600000},
 training:{revision:1,at:clock-1000,expires:clock+3600000,fixture:training,plan:null},
 nutrition:{revision:1,at:clock-1000,expires:clock+3600000,fixture:nutrition,plan:null}};
const cases={};
for(const id of ['valid','missing','identity','frequency','goal','expired','health','recovery','consent','changed','atomic','duplicate','stale','restore','allergy','units'])cases[id]=copy(base);
cases.missing.nutrition.fixture.intake.age=N.missing();
cases.identity.nutrition.fixture.person='syn-other';
cases.frequency.nutrition.fixture.intake.trainingFrequency=N.known(3);
cases.goal.link.nutritionGoal='performance';
cases.expired.nutrition.expires=clock;
cases.health.training.fixture.intake.health='current';
cases.allergy.nutrition.fixture.intake.allergies=N.known(['peanut']);
cases.allergy.nutrition.fixture.intake.favorites=N.known(['peanut']);
cases.units.training.fixture.intake=copy(T.cases.units.intake);
cases.units.training.fixture.intake.unit='lb';cases.units.training.fixture.intake.rir=true;
cases.units.nutrition.fixture.intake.weight=N.known({value:165,unit:'lb'});
cases.units.nutrition.fixture.intake.units=N.known('imperial');
const api={base,cases,copy};if(typeof module==='object')module.exports=api;else root.FMZ18Fixtures=api;
})(globalThis);
