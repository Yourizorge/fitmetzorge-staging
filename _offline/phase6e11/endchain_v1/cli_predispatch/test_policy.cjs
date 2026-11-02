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
