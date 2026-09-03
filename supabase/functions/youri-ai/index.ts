import { createClient } from "npm:@supabase/supabase-js@2.95.0";
import { createYouriAiHandler } from "./handler.ts";
import type { TrustStatus } from "./contracts.ts";
import { createPhase6bHandler } from "./phase6b-handler.ts";
import type { BeginResult } from "./phase6b-handler.ts";
import { inspectOpenAiCredential, probeOpenAiModelRead } from "./openai-adapter.ts";
import { createPhase6cHandler } from "./phase6c-handler.ts";

function requiredEnvironment(name: string): string {
  const value = Deno.env.get(name)?.trim();
  if (!value) throw new Error(`Missing required environment variable: ${name}`);
  return value;
}

function firstPublishableKey(): string {
  for (const name of ["SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_PUBLISHABLE_KEYS"]) {
    const raw = Deno.env.get(name)?.trim();
    if (!raw) continue;
    if (!raw.startsWith("[") && !raw.startsWith("{")) return raw;
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const key = parsed.find((value) => typeof value === "string" && value.trim());
        if (typeof key === "string") return key.trim();
      }
    } catch {
      // Ignore unusable structured key collections.
    }
  }
  throw new Error("Missing usable Supabase publishable key");
}

function secretKeys(): string[] {
  const values: string[] = [];
  for (const name of ["SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEYS"]) {
    const raw = Deno.env.get(name)?.trim();
    if (!raw) continue;
    if (!raw.startsWith("[") && !raw.startsWith("{")) {
      values.push(raw);
      continue;
    }
    try {
      const parsed = JSON.parse(raw);
      const candidates = Array.isArray(parsed) ? parsed : Object.values(parsed);
      for (const value of candidates) if (typeof value === "string" && value.trim()) values.push(value.trim());
    } catch {
      // Ignore unusable structured secret collections.
    }
  }
  return [...new Set(values)];
}

async function equalSecret(candidate: string, expected: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [left, right] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(candidate)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected)),
  ]);
  const a = new Uint8Array(left);
  const b = new Uint8Array(right);
  let mismatch = a.length ^ b.length;
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) mismatch |= a[index] ^ b[index];
  return mismatch === 0;
}

const supabaseUrl = requiredEnvironment("SUPABASE_URL");
const publishableKey = firstPublishableKey();
const availableSecretKeys = secretKeys();
const adminKey = availableSecretKeys[0] || "";
const openAiCredential = inspectOpenAiCredential(Deno.env.get("OPENAI_API_KEY"));

function memberClient(token: string) {
  return createClient(supabaseUrl, publishableKey, {
    auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
    global: { headers: { Authorization: `Bearer ${token}`, "x-fmz-component": "youri-ai-phase6a" } },
  });
}

const handler = createYouriAiHandler({
  mockTestEnabled: Deno.env.get("FMZ_PHASE6A_MOCK_TEST_ENABLED") === "true",
  async verifyBearer(token) {
    const { data, error } = await memberClient(token).auth.getUser(token);
    return error || !data.user ? null : { id: data.user.id };
  },
  async readTrustStatus(token, featureCode) {
    const { data, error } = await memberClient(token).rpc("fmz_phase6a_get_trust_status", {
      p_feature_code: featureCode,
    });
    if (error || !data) throw new Error("trust_status_unavailable");
    return data as TrustStatus;
  },
});

const adminClient = adminKey
  ? createClient(supabaseUrl, adminKey, { auth: { persistSession: false, autoRefreshToken: false } })
  : null;

async function serviceRpc(name: string, input: Record<string, unknown> = {}) {
  if (!adminClient) throw new Error("service_client_unavailable");
  const { data, error } = await adminClient.rpc(name, input);
  if (error || !data) throw new Error(error?.code === "42501" ? "provider_gate_denied" : "provider_accounting_unavailable");
  return data as Record<string, unknown>;
}

const phase6bHandler = createPhase6bHandler({
  providerTestEnvironmentEnabled: Deno.env.get("FMZ_PHASE6B_SYNTHETIC_TEST_ENABLED") === "true",
  authDiagnosticEnvironmentEnabled: Deno.env.get("FMZ_PHASE6B_AUTH_DIAGNOSTIC_ENABLED") === "true",
  openAiApiKey: openAiCredential.apiKey,
  openAiCredentialChecks: openAiCredential.checks,
  runAuthProbe: () => probeOpenAiModelRead(openAiCredential.apiKey || ""),
  async authorizeServer(request) {
    const authorization = request.headers.get("Authorization") || "";
    const candidate = authorization.startsWith("Bearer ") ? authorization.slice(7).trim() : "";
    if (!candidate || !availableSecretKeys.length) return false;
    for (const key of availableSecretKeys) if (await equalSecret(candidate, key)) return true;
    return false;
  },
  readStatus: () => serviceRpc("fmz_phase6b_service_read_provider_status"),
  begin: (input) => serviceRpc("fmz_phase6b_service_begin_synthetic_test", input) as Promise<BeginResult>,
  complete: (input) => serviceRpc("fmz_phase6b_service_complete_synthetic_test", input),
  fail: (input) => serviceRpc("fmz_phase6b_service_fail_synthetic_test", input),
});

function rpcSafeCode(error: { code?: string; message?: string } | null): string {
  const raw = `${error?.code || ""} ${error?.message || ""}`;
  const match = raw.match(/\b(ai_[a-z0-9_]+|mock_[a-z0-9_]+|chat_[a-z0-9_]+|safety_hard_stop)\b/i);
  return match?.[1]?.toLowerCase() || "chat_rpc_unavailable";
}

const phase6cHandler = createPhase6cHandler({
  async verifyBearer(token) {
    const { data, error } = await memberClient(token).auth.getUser(token);
    return error || !data.user ? null : { id: data.user.id };
  },
  async memberRpc(token, name, input = {}) {
    const { data, error } = await memberClient(token).rpc(name, input);
    if (error || !data) throw new Error(rpcSafeCode(error));
    return data as Record<string, unknown>;
  },
  async serviceRpc(name, input = {}) {
    if (!adminClient) throw new Error("chat_service_unavailable");
    const { data, error } = await adminClient.rpc(name, input);
    if (error || !data) throw new Error(rpcSafeCode(error));
    return data as Record<string, unknown>;
  },
});

Deno.serve((request) => {
  const path = new URL(request.url).pathname;
  if (path.includes("/phase6b/")) return phase6bHandler(request);
  if (path.endsWith("/phase6c/chat")) return phase6cHandler(request);
  return handler(request);
});
