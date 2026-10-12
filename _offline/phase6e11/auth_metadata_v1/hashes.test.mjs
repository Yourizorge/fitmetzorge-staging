import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {bindSession} from './hashes.mjs';
import {sha} from '../controller_v1/core.mjs';
const id='68000000-0000-4000-8000-000000000001',auth={session:()=>id};
test('both hash algorithms are explicitly bound to the same UUID',async()=>{
 const json=await sha(id),r=await bindSession(auth,{session_sha:json,http_status:200});
 assert.equal(r.key_sha,createHash('sha256').update(id).digest('hex'));assert.notEqual(r.key_sha,json);
 assert.equal(r.session_sha,json);assert.equal(r.version,1);assert(!JSON.stringify(r).includes(id));
});
test('wrong canonical session hash is denied',async()=>{await assert.rejects(bindSession(auth,{session_sha:'0'.repeat(64)}));});
test('untrusted identifier is denied',async()=>{await assert.rejects(bindSession({session:()=> 'invalid'},{session_sha:'0'.repeat(64)}));});
test('arbitrary extra fields cannot carry secrets',async()=>{await assert.rejects(bindSession(auth,{session_sha:await sha(id),access_token:'do-not-export'}));});
