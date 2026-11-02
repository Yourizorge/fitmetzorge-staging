'use strict';
const { test, before } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const pg = require('pg');
const Connection = require('pg/lib/connection');
const { Ledger, attach, install, statements, sha, UPSTREAM, load, HISTORY, METADATA } = require('./hook.cjs');
before(load);

function policy(extra = {}) {
  return { version: 1, environment: 'disposable_ci', upstream_commit: UPSTREAM,
    source_commit: 'a'.repeat(40), candidate_sha256: 'b'.repeat(64), invocation_id: '12345678-1234-4234-8234-123456789abc',
    slot: 'quota', cap: 64, closure_reserve: 1, dry_run: false, host: '127.0.0.1',
    port: 54322, database: 'postgres', user: 'postgres', ca_sha256: sha('synthetic-ca'), migrations: [], ...extra };
}
function setup(t, p = policy()) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fmz-predispatch-'));
  const file = path.join(dir, 'ledger.jsonl');
  const ledger = new Ledger(p, file); const writes = [];
  const stream = { writable: true, write(buffer) {
    // This is the actual pg serialized output boundary, not a fake SQL method.
    const durable = fs.readFileSync(file, 'utf8').trim().split('\n').map(JSON.parse);
    const frame = durable.at(-1);
    assert.equal(frame.event, 'frontend_frame');
    for (const id of frame.sql_ids || []) assert(durable.some(e => e.event === 'dispatch' && e.id === id));
    writes.push(Buffer.from(buffer)); return true;
  }, end() {} };
  const conn = new Connection({ stream }); attach(conn, ledger);
  t.after(() => { try { fs.closeSync(ledger.fd); } catch {} fs.rmSync(dir, { recursive: true }); });
  return { ledger, file, conn, writes, stream };
}
function complete(conn, n = 1) { for (let i = 0; i < n; i++) conn.emit('commandComplete', {text: 'SELECT 1'}); }

test('pending migration cannot dispatch before the existing history query is validated', t => {
  const {conn, writes} = setup(t, policy({expected_history_versions: ['20260101000000']}));
  assert.throws(() => conn.query('BEGIN'), /dispatch_denied/);
  assert.equal(writes.length, 0);
});

test('existing history query validates exact versions without adding SQL', t => {
  const {conn, ledger, file} = setup(t, policy({expected_history_versions: ['20260101000000']}));
  conn.query(METADATA[1]);
  conn.emit('dataRow', {fields: ['20260101000000']}); complete(conn);
  conn.query('BEGIN'); complete(conn);
  assert.equal(ledger.rows.length, 2);
  const event = fs.readFileSync(file, 'utf8').trim().split('\n').map(JSON.parse).find(e => e.event === 'history_snapshot');
  assert.equal(event.matches_policy, true);
  assert.equal(event.count, 1);
});

test('already-applied target or extra history blocks before migration writes', t => {
  const {conn, ledger, writes} = setup(t, policy({expected_history_versions: ['20260101000000']}));
  conn.query(METADATA[1]);
  conn.emit('dataRow', {fields: ['20260101000000']});
  conn.emit('dataRow', {fields: ['20261102000000']});
  assert.throws(() => complete(conn), /history_snapshot_binding/);
  assert.throws(() => conn.query('BEGIN'), /dispatch_denied/);
  assert.equal(writes.length, 1);
  assert.equal(ledger.rows[0].outcome, 'command_complete');
  assert.equal(ledger.finish(1).complete, false);
});

test('missing expected history fails closed', t => {
  const {conn, ledger} = setup(t, policy({expected_history_versions: ['20260101000000']}));
  conn.query(METADATA[1]);
  assert.throws(() => complete(conn), /history_snapshot_binding/);
  assert.equal(ledger.historyValidated, false);
});

test('malformed history row is never copied into receipt', t => {
  const {conn, file} = setup(t, policy({expected_history_versions: []}));
  conn.query(METADATA[1]);
  assert.throws(() => conn.emit('dataRow', {fields: ['private-invalid-row']}), /history_row/);
  assert(!fs.readFileSync(file, 'utf8').includes('private-invalid-row'));
});

test('history policy rejects duplicate or unsorted versions', t => {
  assert.throws(() => setup(t, policy({expected_history_versions: ['20260101000000', '20260101000000']})), /history_policy/);
  assert.throws(() => setup(t, policy({expected_history_versions: ['20260102000000', '20260101000000']})), /history_policy/);
});

test('real pg serializer: durable prepayment precedes transport write boundary', t => {
  const { conn, ledger, writes } = setup(t);
  conn.query('select 1'); assert.equal(writes[0][0], 81);
  assert.equal(ledger.rows[0].outcome, 'unknown_consumed'); complete(conn);
  assert.equal(ledger.finish(0).confirmed_sql, 1);
});
test('PG17 parser counts batches, not semicolons in bodies or strings', t => {
  assert.equal(statements("DO $$ BEGIN PERFORM 1; END $$; SELECT ';';").length, 2);
  const {conn, ledger} = setup(t); conn.query('select 1; select 1');
  assert.equal(ledger.rows.length, 2); assert.equal(ledger.frames.Q, 1);
  complete(conn, 2); assert.equal(ledger.finish(0).complete, true);
});
test('actual extended frontend emits P/B/D/E/S but one SQL dispatch', t => {
  const {conn, ledger, writes} = setup(t);
  conn.parse({name: '', text: 'select 1', types: []});
  conn.bind({portal: '', statement: '', values: []});
  conn.describe({type: 'P', name: ''}); conn.execute({portal: ''}); conn.sync();
  assert.equal(writes.map(b => String.fromCharCode(b[0])).join(''), 'PBDES');
  assert.equal(ledger.rows.length, 1); complete(conn);
  assert.deepEqual(ledger.finish(0).frontend_frames_by_type, {P: 1, B: 1, D: 1, E: 1, S: 1});
});
test('Parse without Execute incurs a frame but no executed SQL claim', t => {
  const {conn, ledger} = setup(t); conn.parse({name: 'x', text: 'select 1'});
  assert.equal(ledger.rows.length, 0); assert.equal(ledger.frames.P, 1);
});
test('same prepared statement can be rebound: each Execute is charged once', t => {
  const {conn, ledger} = setup(t); conn.parse({name: 's', text: 'select 1'});
  for (let i = 0; i < 2; i++) { conn.bind({statement: 's', portal: '', values: []}); conn.execute({portal: ''}); complete(conn); }
  assert.equal(ledger.rows.length, 2);
  assert.throws(() => conn.execute({portal: ''}), /dispatch_denied/);
});
test('rollback capacity stays reserved and cap is enforced before write', t => {
  const {conn, ledger, writes} = setup(t);
  for (let i = 0; i < 63; i++) { conn.query('select 1'); complete(conn); }
  assert.throws(() => conn.query('select 1'), /dispatch_denied/); assert.equal(writes.length, 63);
  conn.query('ROLLBACK'); complete(conn); assert.equal(ledger.rows.length, 64);
  assert.throws(() => conn.query('ROLLBACK'), /dispatch_denied/); assert.equal(writes.length, 64);
});
test('dry cap 28 accepts 28 but blocks 29 before dispatch', t => {
  const p = policy({slot: 'final', cap: 28, dry_run: true, closure_reserve: 0});
  const {conn, ledger, writes} = setup(t, p);
  for (let i = 0; i < 28; i++) {conn.query('select 1'); complete(conn);}
  assert.throws(() => conn.query('select 1'), /dispatch_denied/);
  assert.equal(writes.length, 28); assert.equal(ledger.rows.length, 28);
  assert.throws(() => setup(t, {...p, cap: 29}), /policy/);
});
test('lost response consumes credit and prevents later work', t => {
  const {conn, ledger, writes} = setup(t); conn.query('select 1'); conn.emit('error', new Error('SECRET'));
  assert.throws(() => conn.query('select 1'), /dispatch_denied/);
  assert.equal(writes.length, 1); const result = ledger.finish(1);
  assert.equal(result.unknown_consumed, 1); assert.equal(result.complete, false);
});
test('write throws after prepay: no refund or secret error text', t => {
  const {conn, ledger, stream, file} = setup(t); stream.write = () => {throw new Error('sbp_secret');};
  assert.throws(() => conn.query('select 1'), /^Error: cli_predispatch_dispatch_denied$/);
  assert.equal(ledger.rows.length, 1); assert(!fs.readFileSync(file, 'utf8').includes('sbp_secret'));
});
test('journal write failure prevents transport dispatch', t => {
  const {conn, ledger, writes} = setup(t); fs.closeSync(ledger.fd);
  assert.throws(() => conn.query('select 1'), /dispatch_denied/); assert.equal(writes.length, 0);
});
test('unregistered and secret SQL rejected before serialization and not exported', t => {
  const {conn, file, writes} = setup(t);
  assert.throws(() => conn.query("SELECT 'private-member-value'"), /dispatch_denied/);
  assert.equal(writes.length, 0); assert(!fs.readFileSync(file, 'utf8').includes('private-member-value'));
});
test('migration AST and history bound parameters, without SQL or values in ledger', t => {
  const sql = 'SELECT 872619'; const p = policy({migrations: [{version:'20990101000000', name:'probe',
    sha256:sha(sql), ast_hashes: statements(sql).map(s=>s.ast_sha256)}]});
  const {conn, ledger, file} = setup(t, p); conn.query(sql); complete(conn);
  conn.parse({name:'h', text:HISTORY}); conn.bind({statement:'h', portal:'h', values:['20990101000000', 'probe', '{"SELECT 872619"}']});
  conn.execute({portal:'h'}); complete(conn);
  assert.deepEqual(ledger.rows.map(r=>r.category), ['migration','migration_history']);
  assert(!fs.readFileSync(file,'utf8').includes(sql));
});
test('wrong history payload denied before Bind is sent', t => {
  const sql='SELECT 872619'; const p=policy({migrations:[{version:'20990101000000',name:'probe',sha256:sha(sql),ast_hashes:statements(sql).map(s=>s.ast_sha256)}]});
  const {conn,writes}=setup(t,p); conn.parse({name:'h',text:HISTORY});
  assert.throws(()=>conn.bind({statement:'h',portal:'',values:['19990101000000','probe',[sql]]}),/dispatch_denied/);
  assert.equal(writes.length,1);
});
test('error during pipeline preserves every uncertain dispatch', t => {
  const {conn,ledger}=setup(t); conn.query('select 1; select 1'); complete(conn);
  conn.emit('errorMessage',{message:'secret SQL'}); conn.emit('readyForQuery',{status:'I'});
  const r=ledger.finish(1); assert.equal(r.confirmed_sql,1); assert.equal(r.unknown_consumed,1);
});
test('journal cannot be reused and hashes form a complete chain', t => {
  const {conn,ledger,file}=setup(t); conn.query('select 1'); complete(conn); ledger.finish(0);
  assert.throws(()=>new Ledger(policy(),file),/EEXIST/);
  let previous='0'.repeat(64);
  for(const line of fs.readFileSync(file,'utf8').trim().split('\n')) {
    assert.equal(JSON.parse(line).previous_sha256,previous); previous=sha(line);
  }
});
test('real pg Client boundary rejects hosted, bad TLS, wrong limits before dial', t => {
  for(const change of [{host:'example.com'},{ssl:false},{connectionTimeoutMillis:6000},
    {ssl:{rejectUnauthorized:true,ca:'synthetic-ca',checkServerIdentity:()=>undefined}},
    {options:'-c jit=true'},{password:'sbp_not_allowed'}]) {
    const {ledger}=setup(t); const undo=install(pg.Client,ledger);
    try {
      const client=new pg.Client({host:'127.0.0.1',port:54322,user:'postgres',database:'postgres',password:'synthetic',
        connectionTimeoutMillis:5000,options:'-c statement_timeout=5000 -c lock_timeout=1000',
        ssl:{rejectUnauthorized:true,ca:'synthetic-ca'},...change});
      assert.throws(()=>client.connect(),/connection_boundary/); assert.equal(ledger.connections,0);
    } finally {undo();}
  }
});
test('one invocation denies a second physical connection before dial', t => {
  const {ledger}=setup(t); ledger.connections=1; const undo=install(pg.Client,ledger);
  try {assert.throws(()=>new pg.Client().connect(),/connection_boundary/);} finally {undo();}
});
test('raw _send, COPY and cancellation cannot bypass the hook', t => {
  const {conn,writes}=setup(t);
  assert.throws(()=>conn._send(Buffer.from([81,0,0,0,5,0])),/unhooked_frame/);
  assert.throws(()=>conn.sendCopyFromChunk(Buffer.from('secret')),/unsupported_protocol/);
  assert.equal(writes.length,0);
});
test('oversized SQL is denied without allocating a command', t => {
  const {conn,ledger}=setup(t); assert.throws(()=>conn.query(' '.repeat(8193)),/dispatch_denied/);
  assert.equal(ledger.rows.length,0);
});
