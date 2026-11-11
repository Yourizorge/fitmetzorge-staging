import fs from 'node:fs';
import hook from './hook.cjs';

export async function start(Client) {
  const policyPath = process.env.FMZ_CLI_PREDISPATCH_POLICY;
  const receiptPath = process.env.FMZ_CLI_PREDISPATCH_LEDGER;
  if (!policyPath || !receiptPath || process.env.SUPABASE_ACCESS_TOKEN ||
      process.env.SUPABASE_DB_PASSWORD || process.env.NODE_OPTIONS || process.env.BUN_OPTIONS ||
      process.env.DO_NOT_TRACK !== '1' || process.env.SUPABASE_NO_UPDATE_NOTIFIER !== '1' ||
      process.argv.includes('--debug')) throw new Error('cli_predispatch_environment');
  const raw = fs.readFileSync(policyPath);
  if (raw.length > 262144) throw new Error('cli_predispatch_policy_size');
  const policy = JSON.parse(raw);
  if (raw.length > 8192 && policy.slot !== 'ci_prefix') throw new Error('cli_predispatch_policy_size');
  await hook.load();
  const ledger = new hook.Ledger(policy, receiptPath);
  hook.install(Client, ledger);
  process.once('exit', code => {
    try { ledger.finish(code); } catch { process.exitCode = 2; }
  });
}
