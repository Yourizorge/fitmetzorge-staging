'use strict';

// Synchronous foreign-driver boundary: fsync must finish before pg's TLS write.
const fs = require('node:fs');
const crypto = require('node:crypto');
const tls = require('node:tls');
const parser = require('@libpg-query/parser');
const UPSTREAM = '21db855916f2c2b12f61cde923a27094b8528b23';
const CAPS = Object.freeze({ quota: 64, pre_auth: 28, final: 28 });
const MARK = Symbol('fmz-predispatch');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const fail = code => { throw new Error('cli_predispatch_' + code); };
// Only the two immutable legacy history identities are shorter than a timestamp.
const historyVersion = value => typeof value === 'string' &&
  (/^[0-9]{14}$/.test(value) || value === '20260813' || value === '20260818');
const cleanAst = value => Array.isArray(value) ? value.map(cleanAst) :
  value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort()
    .filter(k => !['location', 'stmt_location', 'stmt_len'].includes(k))
    .map(k => [k, cleanAst(value[k])])) : value;

function statements(sql, limit = 8192) {
  if (!Number.isInteger(limit) || limit < 8192 || limit > 131072 ||
      typeof sql !== 'string' || Buffer.byteLength(sql) > limit) fail('sql_bound');
  let tree;
  try { tree = parser.parseSync(sql); } catch { fail('parse'); }
  if (Math.floor(tree.version / 10000) !== 17 || !tree.stmts?.length) fail('pg17');
  return tree.stmts.map(row => ({ ast_sha256: sha(JSON.stringify(cleanAst(row.stmt))),
    kind: Object.keys(row.stmt)[0], transaction: row.stmt.TransactionStmt?.kind }));
}

const HISTORY = 'INSERT INTO supabase_migrations.schema_migrations(version, name, statements) VALUES($1, $2, $3)';
const METADATA = [
  'select 1',
  'SELECT version FROM supabase_migrations.schema_migrations ORDER BY version',
  "SELECT count(*) = 3 AS provisioned FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid = a.attrelid WHERE a.attrelid = pg_catalog.to_regclass('supabase_migrations.schema_migrations') AND c.relkind IN ('r', 'p') AND NOT a.attisdropped AND a.attname IN ('version', 'name', 'statements')",
];
function prefixPolicy(p) {
  return p.slot === 'ci_prefix' && p.local_bootstrap_only === true &&
    typeof p.run_id === 'string' && /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(p.run_id) &&
    typeof p.ci_run === 'string' && /^[1-9][0-9]{0,18}$/.test(p.ci_run) &&
    Number.isInteger(p.prefix_index) && p.prefix_index >= 1 && p.prefix_index <= 44 &&
    Array.isArray(p.migrations) && p.migrations.length === 1 &&
    Array.isArray(p.migrations[0].ast_hashes) && p.migrations[0].ast_hashes.length <= 2048 &&
    p.cap === p.migrations[0].ast_hashes.length + 16 &&
    p.frame_cap === p.cap * 8 + 16 && Number.isInteger(p.sql_bytes) &&
    p.sql_bytes >= 8192 && p.sql_bytes <= 131072 &&
    Array.isArray(p.expected_history_versions) && p.expected_history_versions.length === p.prefix_index - 1;
}

function validatePolicy(p) {
  const prefix = p && prefixPolicy(p);
  if (!p || p.version !== 1 || p.environment !== 'disposable_ci' || p.upstream_commit !== UPSTREAM ||
      (!prefix && (!Object.hasOwn(CAPS, p.slot) || p.cap !== CAPS[p.slot])) || p.closure_reserve !== (p.dry_run ? 0 : 1) ||
      !/^[a-f0-9]{40}$/.test(p.source_commit) || !/^[a-f0-9]{64}$/.test(p.candidate_sha256) ||
      !/^[a-f0-9-]{36}$/.test(p.invocation_id) || p.dry_run !== (!prefix && p.slot !== 'quota') ||
      p.host !== '127.0.0.1' || !Number.isInteger(p.port) || p.port < 1024 || p.port > 65535 ||
      p.database !== 'postgres' || p.user !== 'postgres' || !/^[a-f0-9]{64}$/.test(p.ca_sha256) ||
      !Array.isArray(p.migrations) || p.migrations.length > 1 || (p.dry_run && p.migrations.length)) fail('policy');
  for (const m of p.migrations) {
    if (!(prefix ? historyVersion(m.version) : /^[0-9]{14}$/.test(m.version)) || !/^[a-z0-9_]+$/.test(m.name) ||
        !/^[a-f0-9]{64}$/.test(m.sha256) || !Array.isArray(m.ast_hashes) || !m.ast_hashes.length ||
        m.ast_hashes.some(h => !/^[a-f0-9]{64}$/.test(h))) fail('migration_policy');
  }
  if (p.expected_history_versions !== undefined && (!Array.isArray(p.expected_history_versions) ||
      p.expected_history_versions.length > 47 || p.expected_history_versions.some(v => !historyVersion(v)) ||
      new Set(p.expected_history_versions).size !== p.expected_history_versions.length ||
      JSON.stringify([...p.expected_history_versions].sort()) !== JSON.stringify(p.expected_history_versions))) fail('history_policy');
  return p;
}

class Ledger {
  constructor(policy, file) {
    this.policy = validatePolicy(policy);
    this.file = file;
    this.fd = fs.openSync(file, 'wx', 0o600);
    this.rows = []; this.frames = {}; this.accepted = {}; this.connections = 0; this.stopped = false;
    this.rollbackUsed = false; this.previous = '0'.repeat(64); this.sequence = 0;
    this.append({ event: 'preregister', policy_sha256: sha(JSON.stringify(policy)),
      source_commit: policy.source_commit, upstream_commit: UPSTREAM,
      candidate_sha256: policy.candidate_sha256, invocation_id: policy.invocation_id,
      environment: policy.environment, slot: policy.slot, cap: policy.cap,
      closure_reserve: policy.closure_reserve, observer_commands_reserved: 8, dry_run: policy.dry_run,
      ...(policy.slot === 'ci_prefix' ? {local_bootstrap_only: true,
        run_id: policy.run_id, ci_run: policy.ci_run,
        prefix_index: policy.prefix_index, frame_cap: policy.frame_cap, sql_bytes: policy.sql_bytes,
        migration_statements: policy.migrations[0].ast_hashes.length} : {}),
      hosted_admission: false, schema: 1 });
    this.metadata = new Set(METADATA.flatMap(s => statements(s)).map(s => s.ast_sha256));
    this.history = statements(HISTORY)[0].ast_sha256;
    this.historyRead = statements(METADATA[1])[0].ast_sha256;
    this.historyValidated = false;
    this.migrations = new Set(policy.migrations.flatMap(m => m.ast_hashes));
  }
  append(data) {
    try {
      const event = { sequence: ++this.sequence, previous_sha256: this.previous, ...data };
      const encoded = JSON.stringify(event);
      const line = Buffer.from(encoded + '\n');
      if (line.length > 8192 || fs.writeSync(this.fd, line) !== line.length) fail('journal_write');
      fs.fsyncSync(this.fd);
      this.previous = sha(encoded);
    } catch { this.stopped = true; fail('journal'); }
  }
  describe(sql) {
    return statements(sql, this.policy.slot === 'ci_prefix' ? this.policy.sql_bytes : 8192).map(s => {
      let category;
      if (s.transaction === 'TRANS_STMT_ROLLBACK') category = 'closure';
      else if (['TRANS_STMT_BEGIN', 'TRANS_STMT_COMMIT'].includes(s.transaction)) category = 'transaction';
      else if (this.metadata.has(s.ast_sha256)) category = 'migration_metadata';
      else if (!this.policy.dry_run && s.ast_sha256 === this.history) category = 'migration_history';
      else if (!this.policy.dry_run && this.migrations.has(s.ast_sha256)) category = 'migration';
      else if (!this.policy.dry_run && s.ast_sha256 === statements('RESET ALL')[0].ast_sha256) category = 'migration_setup';
      else fail('unregistered_sql');
      if (this.policy.dry_run && category !== 'migration_metadata') fail('dry_mutation');
      if (this.policy.expected_history_versions !== undefined && !this.historyValidated &&
          !['migration_metadata', 'closure'].includes(category)) fail('history_not_validated');
      return { ast_sha256: s.ast_sha256, kind: s.kind, category };
    });
  }
  prepay(items, protocol) {
    const closure = items.length === 1 && items[0].category === 'closure';
    if (!items.length || (this.stopped && !closure) || (closure && this.rollbackUsed) ||
        this.rows.length + items.length > this.policy.cap - (closure ? 0 : this.policy.closure_reserve)) fail('capacity_or_stopped');
    if (closure) this.rollbackUsed = true;
    const ids = [];
    for (const item of items) {
      const row = { id: this.rows.length + 1, ...item, protocol, outcome: 'unknown_consumed' };
      this.rows.push(row); ids.push(row.id);
      this.append({ event: 'dispatch', ...row });
    }
    return ids;
  }
  outcome(id, outcome) {
    const row = this.rows[id - 1];
    if (!row || row.outcome !== 'unknown_consumed' || outcome !== 'command_complete') fail('duplicate_confirmation');
    this.append({ event: 'outcome', id, outcome }); row.outcome = outcome;
  }
  frame(type, ids = []) {
    this.frames[type] = (this.frames[type] || 0) + 1;
    if (Object.values(this.frames).reduce((a, b) => a + b, 0) >
        (this.policy.slot === 'ci_prefix' ? this.policy.frame_cap : 512)) fail('frame_cap');
    this.append({ event: 'frontend_frame', type, sql_ids: ids });
  }
  stop() { this.stopped = true; }
  acceptedFrame(type) {
    this.append({ event: 'frontend_write_returned', type });
    this.accepted[type] = (this.accepted[type] || 0) + 1;
  }
  finish(exitCode) {
    const receipt = { event: 'terminal', sql_dispatches: this.rows.length,
      confirmed_sql: this.rows.filter(r => r.outcome === 'command_complete').length,
      unknown_consumed: this.rows.filter(r => r.outcome === 'unknown_consumed').length,
      frontend_frames_by_type: this.frames, frontend_write_returned_by_type: this.accepted,
      frame_semantics: 'prepaid attempts; write-return is not backend receipt', connection_attempts: this.connections,
      complete: exitCode === 0 && !this.stopped && this.rows.every(r => r.outcome === 'command_complete'),
      hosted_admission: false, observer_commands: 0 };
    this.append(receipt); fs.closeSync(this.fd); return receipt;
  }
}

function validateClient(client, ledger) {
  const p = client.connectionParameters; const policy = ledger.policy;
  if (ledger.connections || p.host !== policy.host || p.port !== policy.port ||
      p.database !== policy.database || p.user !== policy.user ||
      client._connectionTimeoutMillis !== 5000 || !p.ssl || p.ssl.rejectUnauthorized !== true ||
      p.ssl.checkServerIdentity || p.ssl.key || p.ssl.cert ||
      typeof p.ssl.ca !== 'string' || sha(p.ssl.ca) !== policy.ca_sha256 ||
      p.options !== '-c statement_timeout=5000 -c lock_timeout=1000' ||
      typeof p.password !== 'string' || p.password.startsWith('sbp_')) fail('connection_boundary');
  ledger.connections++;
  ledger.append({ event: 'connect_attempt', id: ledger.connections, tls_verify_full: true });
}

function attach(connection, ledger) {
  if (connection[MARK]) fail('duplicate_hook');
  connection[MARK] = true;
  const prepared = new Map(); const portals = new Map(); const waiting = []; const histories = new Map();
  let permit = null; let dispatchIds = [];
  const send = connection._send;
  connection._send = function (buffer) {
    const type = String.fromCharCode(buffer[0]);
    if (!permit || type !== permit || buffer.readInt32BE(1) !== buffer.length - 1) fail('unhooked_frame');
    permit = null;
    const ids = dispatchIds; dispatchIds = [];
    ledger.frame(type, ids);
    if (!this.stream.writable) { ledger.stop(); fail('unwritable'); }
    try {
      const result = send.call(this, buffer);
      ledger.acceptedFrame(type); return result;
    } catch { ledger.stop(); fail('write_unknown'); }
  };
  function wrap(name, type, before = () => []) {
    const original = connection[name];
    connection[name] = function (...args) {
      try {
        if (permit) fail('reentrant');
        dispatchIds = before(...args); permit = type;
        return original.apply(this, args);
      } catch { ledger.stop(); fail('dispatch_denied'); }
      finally { permit = null; dispatchIds = []; }
    };
  }
  function charge(items, protocol) {
    const ids = ledger.prepay(items, protocol); waiting.push(...ids);
    if (ledger.policy.expected_history_versions !== undefined) {
      items.forEach((item, index) => { if (item.ast_sha256 === ledger.historyRead) histories.set(ids[index], []); });
    }
    return ids;
  }
  wrap('query', 'Q', sql => charge(ledger.describe(sql), 'simple'));
  wrap('parse', 'P', query => {
    const name = query.name || '';
    if (ledger.stopped || typeof name !== 'string' || name.length > 64) fail('parse_state');
    const items = ledger.describe(query.text);
    if (items.length !== 1) fail('extended_multi');
    prepared.set(name, items[0]); return [];
  });
  wrap('bind', 'B', config => {
    const item = prepared.get(config.statement || '');
    if (!item || ledger.stopped || String(config.portal || '').length > 64) fail('bind_state');
    if (item.category === 'migration_history') {
      const values = config.values || [];
      const m = ledger.policy.migrations[0];
      // The pinned CLI batch encodes text[] before it reaches node-postgres.
      const parts = typeof values[2] === 'string' ? require('pg').types.getTypeParser(1009)(values[2]) : values[2];
      if (!m || values.length !== 3 || values[0] !== m.version || values[1] !== m.name ||
          !Array.isArray(parts) || JSON.stringify(parts.flatMap(s => statements(s,
            ledger.policy.slot === 'ci_prefix' ? ledger.policy.sql_bytes : 8192)).map(s => s.ast_sha256)) !==
          JSON.stringify(m.ast_hashes)) fail('history_binding');
      ledger.append({event: 'history_bind', migration_sha256: m.sha256,
        version: m.version, statement_count: m.ast_hashes.length});
    } else if ((config.values || []).length) fail('unexpected_parameters');
    portals.set(config.portal || '', item); return [];
  });
  wrap('execute', 'E', config => {
    const item = portals.get(config.portal || '');
    if (!item || (config.rows && config.rows !== 0)) fail('execute_state');
    // This bounded CLI path never resumes a portal; every Execute needs a new Bind.
    portals.delete(config.portal || ''); return charge([item], 'extended');
  });
  wrap('describe', 'D'); wrap('sync', 'S');
  wrap('close', 'C', config => {
    if (config.type === 'P') portals.delete(config.name);
    else if (config.type === 'S') prepared.delete(config.name);
    else fail('close_type');
    return [];
  });
  // Authentication payloads are deliberately opaque and never hashed/exported.
  for (const name of ['password', 'sendSASLInitialResponseMessage', 'sendSCRAMClientFinalMessage']) wrap(name, 'p');
  for (const name of ['sendCopyFromChunk', 'endCopyFrom', 'sendCopyFail', 'cancel']) {
    connection[name] = () => { ledger.stop(); fail('unsupported_protocol'); };
  }
  for (const [name, type] of [['startup', 'StartupMessage'], ['requestSsl', 'SSLRequest'], ['flush', 'H'], ['end', 'X']]) {
    const original = connection[name];
    connection[name] = function (...args) {
      if ((name === 'flush' && !this.stream.writable) ||
          (name === 'end' && (!this._connecting || !this.stream.writable))) return original.apply(this, args);
      ledger.frame(type);
      try { const result = original.apply(this, args); ledger.acceptedFrame(type); return result; }
      catch { ledger.stop(); fail('control_write_unknown'); }
    };
  }
  connection.on('dataRow', message => {
    const versions = histories.get(waiting[0]);
    if (!versions) return;
    const value = message.fields?.[0];
    const version = Buffer.isBuffer(value) ? value.toString('utf8') : value;
    if (message.fields.length !== 1 || !historyVersion(version) || versions.length >= 47) {
      ledger.stop(); fail('history_row');
    }
    versions.push(version);
  });
  connection.on('commandComplete', () => {
    const id = waiting.shift();
    if (id === undefined) { ledger.stop(); fail('unmatched_complete'); }
    ledger.outcome(id, 'command_complete');
    if (histories.has(id)) {
      const versions = histories.get(id); histories.delete(id);
      const agrees = JSON.stringify(versions) === JSON.stringify(ledger.policy.expected_history_versions);
      ledger.append({event: 'history_snapshot', command_id: id, count: versions.length,
        versions_sha256: sha(JSON.stringify(versions)), matches_policy: agrees});
      if (!agrees) { ledger.stop(); fail('history_snapshot_binding'); }
      ledger.historyValidated = true;
    }
  });
  // Parse/Bind errors and pipelined skips are not falsely assigned to one SQL row.
  connection.on('errorMessage', () => { ledger.stop(); waiting.length = 0; });
  connection.on('error', () => { ledger.stop(); waiting.length = 0; });
  connection.on('readyForQuery', () => {
    if (waiting.length) { ledger.stop(); waiting.length = 0; }
  });
  connection.on('end', () => { if (waiting.length) ledger.stop(); });
}

function install(Client, ledger) {
  if (Client.prototype[MARK]) fail('duplicate_install');
  const original = Client.prototype.connect;
  Client.prototype[MARK] = true;
  Client.prototype.connect = function (...args) {
    validateClient(this, ledger); attach(this.connection, ledger);
    const identityCheck = this.connection.ssl.checkServerIdentity;
    if (identityCheck) fail('identity_override');
    // node-postgres does not supply SNI for IP hosts. Explicitly preserve IP SAN verification.
    this.connection.ssl.checkServerIdentity = (_hostname, cert) => tls.checkServerIdentity(ledger.policy.host, cert);
    return original.apply(this, args);
  };
  return () => { Client.prototype.connect = original; delete Client.prototype[MARK]; };
}

module.exports = { Ledger, attach, install, statements, sha, UPSTREAM, CAPS, METADATA, HISTORY,
  load: () => parser.loadModule() };
