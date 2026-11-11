import test from 'node:test';
import assert from 'node:assert/strict';
import {connectionOptions} from './connection_options.mjs';
const host='aws-0-eu-west-2.pooler.supabase.com';
const ca='-----BEGIN CERTIFICATE-----\nsynthetic\n-----END CERTIFICATE-----';
const base='postgresql://postgres:synthetic%2Bvalue@db.mokxyyullfhkfalopbzd.supabase.co:5432/postgres';
for(const mode of ['', 'disable','allow','prefer','require','verify-ca','verify-full']) {
  test('explicit verified TLS regardless of URL selector '+mode,()=>{
    const options=connectionOptions(base+(mode?'?sslmode='+mode:''),ca,host);
    assert.deepEqual(options.ssl,{ca,rejectUnauthorized:true,servername:options.host});
    assert.equal(options.password,'synthetic+value');
    assert.equal(options.username,'postgres');assert.equal(options.port,5432);
    assert.equal(options.debug,false);assert.equal(options.max,1);
  });
}
for(const [name,url] of [
  ['unknown host',base.replace('db.mokxyyullfhkfalopbzd.supabase.co','other.invalid')],
  ['port',base.replace(':5432',':6543')],['role',base.replace('//postgres:','//other:')],
  ['missing password',base.replace(':synthetic%2Bvalue','')],
  ['unknown option',base+'?options=synthetic'],['fragment',base+'#synthetic'],
  ['duplicate ssl',base+'?sslmode=require&sslmode=verify-full'],
]) test('still rejects '+name,()=>assert.throws(()=>connectionOptions(url,ca,host),/configuration/));
test('CA and exact Connect session-host binding remain mandatory',()=>{
  assert.throws(()=>connectionOptions(base,'',host),/configuration/);
  assert.throws(()=>connectionOptions(base,ca,'other.invalid'),/configuration/);
});
