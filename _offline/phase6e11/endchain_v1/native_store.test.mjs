import test from 'node:test';
import assert from 'node:assert/strict';
import {NativeStore} from './native_store.mjs';
const id='69000000-0000-4000-8000-000000000001',h='a'.repeat(64);
function setup(){const rows=[];return {rows,store:new NativeStore(async(sql,args)=>{rows.push({sql,args});return [{id,phase:'confirmed'}];})};}
test('before metadata is a typed object for the native JSONB serializer',async()=>{
 const {store,rows}=setup();await store.before(id,{step:0,action_id:id,request_id:id,actor:id,workspace:id,kind:'workflow',operation:'apply'},{sha256:h},h);
 assert.deepEqual(rows[0].args[9],{sha256:h});assert.equal(rows.length,1);
});
test('all four record phases keep metadata objects and separate SQL commands',async()=>{
 const {store,rows}=setup();for(const phase of ['action_started','action_confirmed','after_saved','pair_validated'])await store.record(id,0,phase,{sha256:h});
 assert.equal(rows.length,4);for(const row of rows)assert.deepEqual(row.args[4],{sha256:h});
});
test('failure metadata is typed too, without a raw exception',async()=>{
 const {store,rows}=setup();await store.halt(id,0,{phase:'after_saved',code:'pair_missing'});
 assert.deepEqual(rows[0].args[2],{phase:'after_saved',code:'pair_missing'});
});
test('claim and close keep their original non-JSON parameter types',async()=>{
 const {store,rows}=setup();await store.claim({id,run:'1',sha:'a'.repeat(40),manifest_sha:h,expires:10000});
 await store.close(id,false,12);assert.equal(rows[0].args[4],10000);assert.equal(rows[1].args[2],12);
});
test('changed parameter slots fail closed before SQL',async()=>{
 const {store,rows}=setup();await assert.rejects(()=>store.one('select $1',[1,2,3,4]),/native_metadata_slot_changed/);
 assert.equal(rows.length,0);
});
test('an untyped or secret-containing metadata value is rejected',async()=>{
 const {store,rows}=setup();await assert.rejects(()=>store.one('select $3::jsonb',[1,2,'"text"',4]),/native_metadata_invalid/);
 await assert.rejects(()=>store.one('select $3::jsonb',[1,2,'{"password":"hidden"}',4]),/metadata_field_denied/);
 assert.equal(rows.length,0);
});
