import type { ContractRequest, ProviderNeutralAdapter } from "./contracts.ts";
import { PHASE6A_RESPONSE_SCHEMA_VERSION } from "./contracts.ts";

export class DeterministicMockAdapter implements ProviderNeutralAdapter {
  readonly adapterCode = "mock";
  readonly externalCalls = 0 as const;

  async run(request: ContractRequest): Promise<unknown> {
    if (request.fixture === "failure") throw new Error("mock_provider_failure");
    if (request.fixture === "timeout") throw new Error("mock_provider_timeout");
    if (request.fixture === "malformed") return { unexpected: true };

    const safetyHardStop = request.fixture === "safety_hard_stop";
    const actions = request.fixture === "action_out_of_bounds"
      ? [{
        action_code: "training_volume_adjustment",
        payload: {
          delta_percent: 35,
          explanation: "Fixture-controlled invalid increase.",
          reversible: true,
        },
      }]
      : [];

    return {
      schema_version: PHASE6A_RESPONSE_SCHEMA_VERSION,
      feature_code: request.feature_code,
      summary: `fixture:${request.fixture}:${request.feature_code}:${request.locale}`,
      observations: ["fixture_observation"],
      uncertainties: ["fixture_uncertainty"],
      recommendations: safetyHardStop ? ["seek_appropriate_professional_support"] : ["fixture_recommendation"],
      actions,
      safety: {
        status: safetyHardStop ? "hard_stop" : "clear",
        category: safetyHardStop ? "unclear_health" : "none",
        message_key: safetyHardStop ? "safety.professional_support" : "safety.clear",
        automatic_execution_blocked: safetyHardStop,
      },
    };
  }
}
