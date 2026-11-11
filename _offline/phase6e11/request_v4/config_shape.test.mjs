import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectConfiguration} from './config_shape.mjs';
const project='https://mokxyyullfhkfalopbzd.supabase.co';
const host='aws-0-eu-west-2.pooler.supabase.com';
const direct='postgresql://postgres:synthetic-secret@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres';
const run=u=>inspectConfiguration(project,u,host);
test('allowed direct and exact session shapes, not credential validity',()=>{
  assert.deepEqual(run(direct),[]);
  assert.deepEqual(run('postgresql://postgres.mokxyyullfhkfalopbzd:synthetic-secret@'+host+':5432/postgres?sslmode=verify-full'),[]);
});
for(const [name,value,expected] of [
  ['absent',undefined,'database_url_absent'],
  ['empty','','database_url_absent'],
  ['type',123,'database_url_type'],
  ['format','synthetic-secret','database_url_format'],
  ['protocol',direct.replace('postgresql:','https:'),'database_protocol'],
  ['port',direct.replace(':5432',':6543'),'database_session_port'],
  ['database',direct.replace(/\/postgres$/, '/other'),'database_name'],
  ['password',direct.replace(':synthetic-secret',''),'database_password_absent'],
  ['role',direct.replace('//postgres:','//other:'),'database_role'],
  ['role encoding',direct.replace('//postgres:','//%zz:'),'database_role_encoding'],
  ['password encoding',direct.replace('synthetic-secret','%zz'),'database_password_encoding'],
  ['options',direct+'?arbitrary=synthetic-secret','database_url_options'],
  ['ssl',direct+'?sslmode=require','database_sslmode'],
  ['duplicate ssl',direct+'?sslmode=verify-full&sslmode=require','database_sslmode_duplicate'],
  ['fragment',direct+'#synthetic-secret','database_url_fragment'],
]) test(name,()=>{
  const result=run(value);assert.ok(result.includes(expected));
  assert.ok(!JSON.stringify(result).includes('synthetic-secret'));
  assert.ok(result.every(x=>/^(database|project)_[a-z_]+$/.test(x)));
});
test('unknown host is only a fixed predicate failure',()=>{
  assert.deepEqual(run(direct.replace('db.mokxyyullfhkfalopbzd.supabase.co','synthetic-unknown.invalid')),
    ['database_host_allowlist','database_role']);
});
test('all differing fields are reported in one probe, not sequential retries',()=>{
  const result=run(direct.replace(':5432',':6543')+'?sslmode=require');
  assert.deepEqual(result,['database_session_port','database_sslmode']);
});
test('project binding fails closed',()=>{
  assert.deepEqual(inspectConfiguration('https://other.invalid',direct,host),['project_binding']);
});
