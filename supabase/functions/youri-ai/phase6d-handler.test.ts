import assert from "node:assert/strict";
import test from "node:test";
import {
  createPhase6dHandler,
  createPhase6dMockAnalysis,
  parsePhase6dAnalysisRequest,
  validatePhase6dAnalysisOutput,
} from "./phase6d-handler.ts";

const input = {
  request_id: "10000000-0000-4000-8000-000000000001",
  analysis_kind: "daily" as const,
  locale: "nl" as const,
};

const context = {
  schema_version: "phase6d.context.v1",
  analysis_kind: "daily",
  feature_code: "daily_analysis",
  event_key: "daily:2026-09-04",
  source_cutoff_at: "2026-09-04T10:00:00Z",
  period: { start_local: "2026-09-04", end_local: "2026-09-04", timezone_name: "Europe/Amsterdam", max_lookback_days: 30 },
  quality: { level: "sufficient", reliable: true, domain_count: 3, observation_count: 6, missing_sources: [], stop_before_provider: false },
  sources: {
    training: { completed_workouts: 1, set_count: 8 },
    nutrition: { days_logged: 1, items_logged: 4 },
    recovery: { days_logged: 2, avg_sleep_hours: 7.2 },
    progress: { weight_logs: 1, body_measurement_logs: 0 },
  },
  unavailable_sources: [],
  privacy: { private_chat_included: false, raw_prompts_included: false, raw_notes_included: false, trainer_visible: false, domain_writes_allowed: false },
};

function invoke(body: unknown, options: { token?: string; fail?: boolean; prepared?: Record<string, unknown>; begun?: Record<string, unknown> } = {}) {
  const calls: { name: string; input: Record<string, unknown> }[] = [];
  const handler = createPhase6dHandler({
    async verifyBearer(token) {
      return token === "member-token" ? { id: "10000000-0000-4000-8000-000000000010" } : null;
    },
    async memberRpc(_token, name, args = {}) {
      calls.push({ name, input: args });
      return options.prepared || {
        status: "prepared",
        result_id: "10000000-0000-4000-8000-000000000011",
        analysis_kind: "daily",
        feature_code: "daily_analysis",
        model_tier: "luna",
        context,
      };
    },
    async serviceRpc(name, args = {}) {
      calls.push({ name, input: args });
      if (options.fail && name.includes("complete")) throw new Error("analysis_controlled_failure");
      return name.includes("begin")
        ? options.begun || { run_id: "10000000-0000-4000-8000-000000000012", status: "reserved" }
        : { status: "completed" };
    },
  });
  return {
    calls,
    response: handler(new Request("https://example.test/youri-ai/phase6d/analyze", {
      method: "POST",
      headers: { Authorization: `Bearer ${options.token || "member-token"}`, Origin: "https://yourizorge.github.io", "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })),
  };
}

test("analysis request is exact and browser cannot choose provider", () => {
  assert.deepEqual(parsePhase6dAnalysisRequest(input), input);
  assert.throws(() => parsePhase6dAnalysisRequest({ ...input, model: "gpt-5.6-terra" }), /analysis_request_invalid/);
  assert.throws(() => parsePhase6dAnalysisRequest({ ...input, provider: "openai" }), /analysis_request_invalid/);
  assert.throws(() => parsePhase6dAnalysisRequest({ ...input, request_id: "bad" }), /analysis_identity_invalid/);
});

test("mock analysis is deterministic, no-action and privacy bounded", () => {
  const first = createPhase6dMockAnalysis(context, "nl");
  const second = createPhase6dMockAnalysis(context, "nl");
  assert.deepEqual(first, second);
  assert.equal(validatePhase6dAnalysisOutput(first), true);
  assert.deepEqual(first.actions, []);
  assert.equal(JSON.stringify(first).includes("private_chat"), false);
  assert.equal(JSON.stringify(first).includes("service_role"), false);
});

test("weekly mock keeps Terra feature contract without browser authority", () => {
  const weekly = createPhase6dMockAnalysis({ ...context, analysis_kind: "weekly", feature_code: "weekly_checkin" }, "en");
  assert.equal(weekly.feature_code, "weekly_checkin");
  assert.equal(validatePhase6dAnalysisOutput(weekly), true);
  assert.equal("model" in weekly, false);
});

test("authenticated request prepares, reserves and completes zero-cost mock", async () => {
  const { calls, response } = invoke(input);
  const result = await response;
  const body = await result.json();
  assert.equal(result.status, 200);
  assert.equal(body.external_ai_calls, 0);
  assert.equal(body.external_ai_cost_eur, 0);
  assert.deepEqual(calls.map((item) => item.name), [
    "fmz_phase6d_prepare_analysis",
    "fmz_phase6d_service_begin_analysis",
    "fmz_phase6d_service_complete_analysis",
  ]);
  assert.equal(Object.keys(calls[0].input).some((key) => /provider|model|fixture|entitlement|user_id/.test(key)), false);
  assert.equal(calls[1].input.p_analysis_kind, "daily");
});

test("insufficient data stops before service run", async () => {
  const prepared = {
    replay: false,
    status: "insufficient_data",
    result: { id: "10000000-0000-4000-8000-000000000021", status: "insufficient_data", summary: "Niet genoeg data." },
  };
  const { calls, response } = invoke(input, { prepared });
  const result = await response;
  const body = await result.json();
  assert.equal(result.status, 200);
  assert.equal(body.result.status, "insufficient_data");
  assert.deepEqual(calls.map((item) => item.name), ["fmz_phase6d_prepare_analysis"]);
});

test("completed run replays without another completion", async () => {
  const { calls, response } = invoke(input, { begun: { run_id: "10000000-0000-4000-8000-000000000012", status: "completed" } });
  assert.equal((await response).status, 200);
  assert.equal(calls.some((item) => item.name.includes("complete_analysis")), false);
});

test("controlled failure is sanitized and reconciled", async () => {
  const { calls, response } = invoke(input, { fail: true });
  const result = await response;
  assert.equal(result.status, 422);
  assert.deepEqual(await result.json(), { error: "analysis_controlled_failure" });
  assert.equal(calls.at(-1)?.name, "fmz_phase6d_service_fail_analysis");
});

test("auth and origin fail closed", async () => {
  assert.equal(await (await invoke(input, { token: "bad" }).response).status, 401);
  const handler = createPhase6dHandler({ async verifyBearer() { return { id: "x" }; }, async memberRpc() { return {}; }, async serviceRpc() { return {}; } });
  assert.equal((await handler(new Request("https://example.test/youri-ai/phase6d/analyze", { method: "POST", headers: { Origin: "https://evil.example" }, body: "{}" }))).status, 403);
});
