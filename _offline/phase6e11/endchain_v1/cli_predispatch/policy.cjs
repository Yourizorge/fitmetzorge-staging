'use strict';
// Parent-owned, secret-free policy compiler. Never opens a network connection.
const fs = require('node:fs');
const path = require('node:path');
const hook = require('./hook.cjs');

async function compile(input) {
  await hook.load();
  const prefix = input.slot === 'ci_prefix';
  let sqlBytes = 8192;
  const migrations = (input.migration_paths || []).map(file => {
    const match = /^(20260813|20260818|[0-9]{14})_([a-z0-9_]+)\.sql$/.exec(path.basename(file));
    if (!match) throw new Error('cli_predispatch_migration_name');
    if (!prefix && match[1].length !== 14) throw new Error('cli_predispatch_migration_name');
    const raw = fs.readFileSync(file);
    if (raw.length > 131072) throw new Error('cli_predispatch_migration_bound');
    // Hosted-equivalent slots retain 8KiB; the local prefix binds its actual size.
    const parser = require('@libpg-query/parser');
    const tree = parser.parseSync(raw.toString('utf8'));
    const bytes = Buffer.from(raw);
    const hashes = tree.stmts.flatMap(row => {
      const start = row.stmt_location || 0;
      const end = row.stmt_len ? start + row.stmt_len : bytes.length;
      const statement = bytes.subarray(start, end).toString('utf8');
      sqlBytes = Math.max(sqlBytes, Buffer.byteLength(statement));
      return hook.statements(statement, prefix ? 131072 : 8192).map(s => s.ast_sha256);
    });
    return {version: match[1], name: match[2], sha256: hook.sha(raw), ast_hashes: hashes};
  });
  const policy = {...input, migrations, upstream_commit: hook.UPSTREAM, version: 1};
  if (prefix) {
    if (migrations.length !== 1) throw new Error('cli_predispatch_prefix_single');
    policy.cap = migrations[0].ast_hashes.length + 16;
    policy.frame_cap = policy.cap * 8 + 16;
    policy.sql_bytes = sqlBytes;
  }
  delete policy.migration_paths;
  return policy;
}
module.exports = {compile};
if (require.main === module) {
  Promise.resolve().then(() => {
    if (process.argv.length > 3) throw new Error('cli_predispatch_policy_arguments');
    const raw = fs.readFileSync(process.argv[2] || 0, 'utf8');
    if (Buffer.byteLength(raw) > 8192) throw new Error('cli_predispatch_policy_input_bound');
    return compile(JSON.parse(raw));
  }).then(p => process.stdout.write(JSON.stringify(p)),
    () => { process.stderr.write('cli_predispatch_policy_failed\n'); process.exitCode = 2; });
}
