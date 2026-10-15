(function(root){
 'use strict';
 const model=typeof module!=='undefined'&&module.exports?require('../../assets/training-workout-model.js'):root.FMZ_WORKOUT_MODEL;
 const captions={mon:['Maandag','Monday','Montag'],tue:['Dinsdag','Tuesday','Dienstag'],wed:['Woensdag','Wednesday','Mittwoch'],thu:['Donderdag','Thursday','Donnerstag'],fri:['Vrijdag','Friday','Freitag'],sat:['Zaterdag','Saturday','Samstag'],sun:['Zondag','Sunday','Sonntag'],
 fitness:['Conditie','Fitness','Fitness'],strength:['Kracht','Strength','Kraft'],muscle:['Spieropbouw','Muscle development','Muskelaufbau'],beginner:['Beginner','Beginner','Anfänger'],experienced:['Ervaren','Experienced','Erfahren'],
 dumbbell:['Dumbbells','Dumbbells','Kurzhanteln'],bodyweight:['Lichaamsgewicht','Bodyweight','Körpergewicht'],band:['Weerstandsband','Resistance band','Widerstandsband']};
 function caption(value,language){return Array.isArray(value)?value[language]:(captions[value]?.[language]||value);}
 function weight(value,unit,preference){
  if(value===null||value===undefined)return null;
  if(typeof value!=='number'||!Number.isFinite(value)||value<0||!['kg','lb'].includes(unit)||!['metric','imperial'].includes(preference))return null;
  const target=preference==='imperial'?'lb':'kg';
  const display=target===unit?value:unit==='kg'?model.displayWeight(value,true):Math.round(model.storedWeight(value,true)*100)/100;
  return {original:value,originalUnit:unit,value:display,unit:target,approximate:target!==unit,sourceUnchanged:true};
 }
 function text(value,unit,preference,missing){const w=weight(value,unit,preference);return w?(w.approximate?'≈ '+w.value+' '+w.unit+' ('+w.original+' '+w.originalUnit+')':w.value+' '+w.unit):missing;}
 const api={caption,weight,text};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.FMZDisplay=Object.freeze(api);
})(typeof window!=='undefined'?window:globalThis);
