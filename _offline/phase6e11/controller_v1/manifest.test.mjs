import test from 'node:test';import assert from 'node:assert/strict';
import {validateManifest,boundController} from './manifest.mjs';
import {sha,PROJECT} from './core.mjs';
const id=n=>'65000000-0000-4000-8000-'+String(n).padStart(12,'0');
const now=1791801900000;
function fixture(){return {version:1,max_commands:128,
 identities:[{id:id(1),role:'a_member',trainer_id:id(2)},{id:id(2),role:'a_trainer',trainer_id:null},{id:id(3),role:'b_member',trainer_id:null}],
 workspaces:[{id:id(4),window:id(6),route:'A',member:id(1),trainer:id(2)},{id:id(5),window:id(6),route:'B',member:id(3),trainer:null}],
 actions:[{step:0,action_id:id(7),request_id:id(8),actor:id(1),workspace:null,kind:'auth',operation:'issue',writes:[]}]};}
test('exact three identities and shared window',()=>assert.equal(validateManifest(fixture()).identities.length,3));
for(const [name,mutate] of [
 ['fourth actor',m=>m.identities.push({id:id(20),role:'owner',trainer_id:null})],
 ['missing trainer',m=>m.identities.splice(1,1)],['duplicate identity',m=>m.identities[2].id=id(1)],
 ['wrong A trainer',m=>m.identities[0].trainer_id=id(3)],['B with trainer',m=>m.identities[2].trainer_id=id(2)],
 ['foreign workspace member',m=>m.workspaces[0].member=id(20)],['mixed windows',m=>m.workspaces[1].window=id(20)],
 ['foreign actor',m=>m.actions[0].actor=id(20)],['unlisted auth',m=>m.actions[0].operation='delete_user'],
 ['auth writes in app',m=>m.actions[0].writes=[{}]],['wrong auth scope',m=>m.actions[0].workspace=id(4)],
 ['lifecycle not implemented',m=>m.actions[0].kind='lifecycle'],['budget escalation',m=>m.max_commands=129],
 ['duplicate request',m=>m.actions.push({...m.actions[0],step:1,action_id:id(30)})]])
test('deny '+name,()=>{const m=fixture();mutate(m);assert.throws(()=>validateManifest(m));});
for(const [role,operation,route,allowed] of [
 ['a_member','member_accept','A',true],['a_member','trainer_approve','A',false],['a_member','apply','A',false],
 ['a_trainer','trainer_approve','A',true],['a_trainer','b_apply','B',false],['b_member','b_apply','B',true],
 ['b_member','member_accept','A',false],['a_trainer','cleanup_batch','A',true]])
test(`${role} ${operation} ${route}`,()=>{
 const m=fixture();m.actions[0]={...m.actions[0],actor:m.identities.find(x=>x.role===role).id,workspace:m.workspaces.find(x=>x.route===route).id,kind:'workflow',operation};
 if(allowed)assert.doesNotThrow(()=>validateManifest(m));else assert.throws(()=>validateManifest(m));
});
test('hash binding and immutable registered action precede measurement',async()=>{
 const m=fixture();let measured=0;
 const grant={project:PROJECT,id:id(99),sha:'a'.repeat(40),run:'100',manifest_sha:await sha(m),starts:now,expires:now+600000};
 const {controller,manifest}=await boundController({manifest:m,grant,now:()=>now,store:{}});
 m.actions[0].actor=id(20);assert.equal(manifest.actions[0].actor,id(1));
 await assert.rejects(controller.execute(m.actions[0],{measure:async()=>measured++}),/contract_not_registered/);
 assert.equal(measured,0);assert.throws(()=>manifest.actions[0].actor=id(30));
 await assert.rejects(boundController({manifest:fixture(),grant:{...grant,manifest_sha:'b'.repeat(64)},store:{},now:()=>now}),/manifest_hash/);
});
