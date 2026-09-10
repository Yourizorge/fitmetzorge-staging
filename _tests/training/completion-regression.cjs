// Preserve the six historical assertions; supply current mutex and snapshot dependencies.
const fs=require("node:fs"),path=require("node:path"),Module=require("node:module"),assert=require("node:assert/strict");
const file=path.resolve(__dirname,"../../assets/phase6d-workout-event-check.cjs");
const source=fs.readFileSync(file,"utf8"),needle="const context={phase3State:";
assert.equal(source.split(needle).length,2);
const engine=fs.readFileSync(path.resolve(__dirname,"../../assets/phase3-training-engine.js"),"utf8");
const effort=engine.match(/  function phase3SessionEffort\(session\) \{[\s\S]*?\n  \}/)[0];
const fixture=source.replace(needle,"const context={window:{FMZ_WORKOUT_MODEL:require('./training-workout-model.js')},phase3FinishSaving:false,phase3SetSaving:false,phase3State:")
 .replace('planTitle:"Synthetic",setLogs:', 'planTitle:"Synthetic",plannedExercises:[],setLogs:')
 .replace('vm.createContext(context);','vm.createContext(context);vm.runInContext('+JSON.stringify(effort)+',context);');
const loaded=new Module(file,module);loaded.filename=file;loaded.paths=Module._nodeModulePaths(path.dirname(file));loaded._compile(fixture,file);
