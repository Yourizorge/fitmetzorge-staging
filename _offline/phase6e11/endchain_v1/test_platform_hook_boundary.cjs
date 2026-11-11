'use strict';
// Run the existing pinned hook, not a reimplementation. No sockets/CLI/Docker.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const Module = require('node:module');
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const sourceRoot = process.env.FMZ_PLATFORM_SOURCE_ROOT;
const deps = process.env.FMZ_EXISTING_HOOK_DEPS;
assert.ok(sourceRoot && deps, 'explicit existing source and dependency paths required');
const filename = path.join(sourceRoot, '_offline/phase6e11/endchain_v1/cli_predispatch/hook.cjs');
const raw = fs.readFileSync(filename);
assert.equal(sha(Buffer.from(raw.toString().replaceAll('\r\n', '\n'))),
  '55d6d14c392f760cff0f7abfd3af9aa1794865823195829efcddcf7323524be9');
const actual = new Module(filename, module);
actual.filename = filename;
actual.paths = Module._nodeModulePaths(path.resolve(deps));
actual._compile(raw.toString(), filename);
const hook = actual.exports;
const policy = () => ({version: 1, environment: 'disposable_ci', upstream_commit: hook.UPSTREAM,
  source_commit: 'a'.repeat(40), candidate_sha256: 'b'.repeat(64),
  invocation_id: '11111111-1111-4111-8111-111111111111', slot: 'pre_auth',
  cap: 28, closure_reserve: 0, dry_run: true, host: '127.0.0.1', port: 54322,
  database: 'postgres', user: 'postgres', ca_sha256: sha('fixture-ca'), migrations: []});

test('existing hook rejects local plaintext before the driver connect', async () => {
  await hook.load();
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'fmz-platform-boundary-'));
  const file = path.join(folder, 'ledger.txt');
  const ledger = new hook.Ledger(policy(), file);
  let called = 0;
  class Client {
    constructor() {
      this.connectionParameters = {host: '127.0.0.1', port: 54322, database: 'postgres',
        user: 'postgres', password: 'disposable-fixture', ssl: false,
        options: '-c statement_timeout=5000 -c lock_timeout=1000'};
      this._connectionTimeoutMillis = 5000;
    }
    connect() { called++; throw new Error('no socket permitted in this test'); }
  }
  const restore = hook.install(Client, ledger);
  try {
    assert.throws(() => new Client().connect(), /cli_predispatch_connection_boundary/);
    assert.equal(called, 0);
    const receipt = ledger.finish(1);
    assert.equal(receipt.complete, false);
    assert.equal(receipt.connection_attempts, 0);
    assert.equal(receipt.sql_dispatches, 0); // This rejected client only, never startup total.
    assert.equal(fs.readFileSync(file, 'utf8').includes('disposable-fixture'), false);
  } finally {
    restore();
    fs.unlinkSync(file);
    fs.rmdirSync(folder);
  }
});

test('current migration policy does not silently admit bootstrap SQL or role setup', async () => {
  await hook.load();
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'fmz-platform-policy-'));
  const ledger = new hook.Ledger(policy(), path.join(folder, 'ledger.txt'));
  try {
    for (const sql of ['SET SESSION ROLE postgres', 'CREATE EXTENSION pgcrypto']) {
      assert.throws(() => ledger.describe(sql), /cli_predispatch_unregistered_sql/);
    }
    assert.equal(ledger.finish(1).complete, false);
  } finally {
    fs.unlinkSync(path.join(folder, 'ledger.txt'));
    fs.rmdirSync(folder);
  }
});
