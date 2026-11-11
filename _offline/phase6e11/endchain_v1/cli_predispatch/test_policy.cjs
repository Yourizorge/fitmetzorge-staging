'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {compile} = require('./policy.cjs');
const hook = require('./hook.cjs');

function fixture(t, name, sql) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'cli-predispatch-policy-'));
  t.after(() => fs.rmSync(root, {recursive: true}));
  const file = path.join(root, name);
  fs.writeFileSync(file, sql);
  return file;
}

test('policy compiler binds file bytes and real PG17 statements without SQL export', async t => {
  const sql = "SELECT 1; DO $$ BEGIN PERFORM 'literal;not-a-command'; END $$;";
  const file = fixture(t, '20261102000000_synthetic.sql', sql);
  const result = await compile({migration_paths: [file]});
  assert.equal(result.migrations[0].sha256, hook.sha(sql));
  assert.equal(result.migrations[0].ast_hashes.length, 2);
  assert.equal(result.upstream_commit, hook.UPSTREAM);
  assert(!JSON.stringify(result).includes('literal'));
  assert(!JSON.stringify(result).includes(file));
});

test('UTF8 byte locations preserve statement hashes', async t => {
  const sql = "SELECT '\u00e9'; SELECT 1;";
  const file = fixture(t, '20261102000000_synthetic.sql', sql);
  const result = await compile({migration_paths: [file]});
  assert.deepEqual(result.migrations[0].ast_hashes, hook.statements(sql).map(s => s.ast_sha256));
});

test('oversized statement fails policy compilation', async t => {
  const file = fixture(t, '20261102000000_synthetic.sql', "SELECT '" + 'x'.repeat(8192) + "';");
  await assert.rejects(compile({migration_paths: [file]}), /sql_bound/);
});

test('file name and whole file bounds remain fixed', async t => {
  const bad = fixture(t, 'not_a_migration.sql', 'SELECT 1;');
  await assert.rejects(compile({migration_paths: [bad]}), /migration_name/);
  const huge = fixture(t, '20261102000000_synthetic.sql', ' '.repeat(131073));
  await assert.rejects(compile({migration_paths: [huge]}), /migration_bound/);
});

test('prefix compiler derives local-only limits, leaving quota policy unchanged', async t => {
  const file = fixture(t, '20260813_synthetic.sql', "SELECT '" + 'x'.repeat(9000) + "';");
  const p = await compile({slot:'ci_prefix',local_bootstrap_only:true,prefix_index:2,
    migration_paths:[file],expected_history_versions:['20260812000000']});
  assert.equal(p.migrations[0].version,'20260813');
  assert.equal(p.cap,17);
  assert.equal(p.frame_cap,152);
  assert(p.sql_bytes>8192);
  assert.equal(hook.CAPS.quota,64);
  await assert.rejects(compile({slot:'quota',migration_paths:[file]}),/migration_name/);
});

test('unknown short migration identity remains invalid even for a prefix', async t => {
  const file=fixture(t,'20260814_unknown.sql','SELECT 1;');
  await assert.rejects(compile({slot:'ci_prefix',migration_paths:[file]}),/migration_name/);
});

test('all 44 canonical prefix files compile without changing their bytes or hosted caps', async t => {
  const root = path.resolve(__dirname, '../../../..');
  const folder = path.join(root, 'supabase/migrations');
  const names = fs.readdirSync(folder).filter(n => n.endsWith('.sql')).sort();
  assert.equal(names.length, 45);
  assert.equal(names[44], '20261018070231_phase6e11_recovery_run_quota.sql');
  const ledgerRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'cli-prefix-compile-'));
  t.after(() => fs.rmSync(ledgerRoot, {recursive:true}));
  let statements = 0, reserved = 0, largest = 0;
  for (const [index, name] of names.slice(0, 44).entries()) {
    const file = path.join(folder, name), before = hook.sha(fs.readFileSync(file));
    const p = await compile({version:1,environment:'disposable_ci',slot:'ci_prefix',
      local_bootstrap_only:true,prefix_index:index+1,migration_paths:[file],
      run_id:'129c55a7-748c-4f07-96b2-e198e08b8e04',ci_run:'123',
      expected_history_versions:names.slice(0,index).map(n=>n.split('_')[0]),
      source_commit:'a'.repeat(40),candidate_sha256:'b'.repeat(64),
      invocation_id:'12345678-1234-4234-8234-123456789abc',closure_reserve:1,dry_run:false,
      host:'127.0.0.1',port:54322,database:'postgres',user:'postgres',ca_sha256:'c'.repeat(64)});
    const ledger = new hook.Ledger(p, path.join(ledgerRoot, index + '.jsonl'));
    fs.closeSync(ledger.fd);
    assert.equal(p.migrations[0].sha256, before);
    assert.equal(hook.sha(fs.readFileSync(file)), before);
    statements += p.migrations[0].ast_hashes.length;
    reserved += p.cap; largest = Math.max(largest,p.sql_bytes);
  }
  assert.equal(statements,1552);
  assert.equal(reserved,2256);
  assert.equal(hook.CAPS.quota,64);
  t.diagnostic(JSON.stringify({scope:'local_prefix_policy_compilation_only', files:44,
    body_statements:statements,cli_reserve:reserved,largest_statement_bytes:largest,
    total_run_commands:null,hosted_admission:false}));
});
