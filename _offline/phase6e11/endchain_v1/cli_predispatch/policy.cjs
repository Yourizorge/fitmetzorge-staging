'use strict';
// Parent-owned, secret-free policy compiler. Never opens a network connection.
const fs = require('node:fs');
const path = require('node:path');
const hook = require('./hook.cjs');

async function compile(input) {
  await hook.load();
  const migrations = (input.migration_paths || []).map(file => {
    const match = /^([0-9]{14})_([a-z0-9_]+)\.sql$/.exec(path.basename(file));
    if (!match) throw new Error('cli_predispatch_migration_name');
    const raw = fs.readFileSync(file);
    if (raw.length > 131072) throw new Error('cli_predispatch_migration_bound');
    // Files can contain many statements; each dispatched statement remains <=8KiB.
    const parser = require('@libpg-query/parser');
    const tree = parser.parseSync(raw.toString('utf8'));
    const bytes = Buffer.from(raw);
    const hashes = tree.stmts.flatMap(row => {
      const start = row.stmt_location || 0;
      const end = row.stmt_len ? start + row.stmt_len : bytes.length;
      return hook.statements(bytes.subarray(start, end).toString('utf8')).map(s => s.ast_sha256);
    });
    return {version: match[1], name: match[2], sha256: hook.sha(raw), ast_hashes: hashes};
  });
  const policy = {...input, migrations, upstream_commit: hook.UPSTREAM, version: 1};
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
