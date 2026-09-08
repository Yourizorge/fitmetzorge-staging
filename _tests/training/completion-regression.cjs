// Preserve the six historical assertions verbatim; supply only the new mutex fixture values.
const fs=require("node:fs"),path=require("node:path"),Module=require("node:module"),assert=require("node:assert/strict");
const file=path.resolve(__dirname,"../../assets/phase6d-workout-event-check.cjs");
const source=fs.readFileSync(file,"utf8"),needle="const context={phase3State:";
assert.equal(source.split(needle).length,2);
const fixture=source.replace(needle,"const context={phase3FinishSaving:false,phase3SetSaving:false,phase3State:");
const loaded=new Module(file,module);loaded.filename=file;loaded.paths=Module._nodeModulePaths(path.dirname(file));loaded._compile(fixture,file);
