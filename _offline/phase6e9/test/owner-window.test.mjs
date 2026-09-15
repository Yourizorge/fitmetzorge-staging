import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
const source=fs.readFileSync(new URL("../../../coach-backend-demo/app.js",import.meta.url),"utf8");
const gate=source.split(/\r?\n/).find(l=>l.includes(".includes(email)"));
const expression=gate.match(/if\(!(.+?)\)\{/)[1];
const permitted=["zorgeyouri+6e9-a-lid@gmail.com","zorgeyouri+6e9-a-trainer@gmail.com","zorgeyouri+6e9-b-lid@gmail.com"];
for(const email of permitted)test("exact approved alias "+email.split("+")[1].split("@")[0],()=>assert.equal(vm.runInNewContext(expression,{email}),true));
for(const email of ["zorgeyouri@gmail.com","zorgeyouri+6e9-admin@gmail.com","zorgeyouri+6e9-a-lid@gmail.com.evil.invalid","6e9-test@example.invalid","other@gmail.com","Zorgeyouri+6e9-a-lid@gmail.com"])
 test("unapproved alias denied "+email.split("@")[0],()=>assert.equal(vm.runInNewContext(expression,{email}),false));
test("only a client compatibility gate; existing server flow retained",()=>{
 assert(source.includes('request({op:"home"})'));
 assert(!source.includes("service_role"));
 assert(source.includes('request({op:"read",workspace:homes[0].workspace})'));
});
