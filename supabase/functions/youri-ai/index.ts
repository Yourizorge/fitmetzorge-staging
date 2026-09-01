import { createClient } from "npm:@supabase/supabase-js@2.95.0";
import { createYouriAiHandler } from "./handler.ts";
import type { TrustStatus } from "./contracts.ts";

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

const supabaseUrl = requiredEnvironment("SUPABASE_URL");
const publishableKey = firstPublishableKey();

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

Deno.serve(handler);
