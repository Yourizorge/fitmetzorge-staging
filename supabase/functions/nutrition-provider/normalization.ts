import {
  ACCEPTED_DATA_TYPES,
  MAPPING_VERSION,
  MAX_NUTRIENT_ENTRIES,
  MAX_PORTIONS,
  MAX_SEARCH_RESULTS,
  NUTRIENT_IDS,
  PROVIDER_ATTRIBUTION_URL,
  PROVIDER_CODE,
  PROVIDER_LABEL,
} from "./constants.ts";
import type { AcceptedDataType } from "./constants.ts";
import { createCandidateId } from "./crypto.ts";
import type { NutrientDerivation, SafeCandidate, SafePortion } from "./types.ts";
import { ProviderError } from "./types.ts";

type UnknownRecord = Record<string, unknown>;

// deno-lint-ignore no-control-regex -- provider text is normalized before use or disclosure.
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/gu;
const FDC_ID_PATTERN = /^[1-9][0-9]{0,15}$/u;

function record(value: unknown): UnknownRecord | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as UnknownRecord
    : null;
}

function boundedText(value: unknown, maxLength: number): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.replace(CONTROL_CHARACTERS, " ").replace(/\s+/gu, " ").trim();
  if (!normalized || normalized.length > maxLength) return null;
  return normalized;
}

function finiteNumber(value: unknown): number | null {
  const parsed = typeof value === "number"
    ? value
    : typeof value === "string" && value.trim() !== ""
    ? Number(value)
    : Number.NaN;
  return Number.isFinite(parsed) ? parsed : null;
}

function safeRound(value: number, precision = 3): number {
  const factor = 10 ** precision;
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

function acceptedDataType(value: unknown): AcceptedDataType | null {
  return typeof value === "string" && ACCEPTED_DATA_TYPES.includes(value as AcceptedDataType)
    ? value as AcceptedDataType
    : null;
}

function nutrientEntries(food: UnknownRecord): UnknownRecord[] {
  if (!Array.isArray(food.foodNutrients) || food.foodNutrients.length > MAX_NUTRIENT_ENTRIES) {
    return [];
  }
  return food.foodNutrients.map(record).filter((entry): entry is UnknownRecord => entry !== null);
}

interface NutrientValue {
  amount: number;
  unit: string | null;
}

function nutrientMap(food: UnknownRecord): Map<number, NutrientValue> {
  const values = new Map<number, NutrientValue>();
  for (const entry of nutrientEntries(food)) {
    const nested = record(entry.nutrient);
    const id = finiteNumber(entry.nutrientId ?? nested?.id);
    const amount = finiteNumber(entry.value ?? entry.amount);
    if (id === null || amount === null || !Number.isSafeInteger(id) || values.has(id)) continue;
    values.set(id, {
      amount,
      unit: boundedText(entry.unitName ?? nested?.unitName, 12)?.toUpperCase() ?? null,
    });
  }
  return values;
}

function readMacro(
  values: Map<number, NutrientValue>,
  id: number,
  required: boolean,
): number | null {
  const value = values.get(id);
  if (value === undefined) {
    if (required) {
      throw new ProviderError(
        "candidate_missing_macros",
        "Required nutrient data is unavailable.",
        502,
      );
    }
    return null;
  }
  if (value.unit && value.unit !== "G" && value.unit !== "GRAM") {
    throw new ProviderError("candidate_invalid_unit", "Nutrient unit is invalid.", 502);
  }
  if (value.amount < 0 || value.amount > 100) {
    throw new ProviderError(
      "candidate_invalid_macros",
      "Nutrient data is outside safe bounds.",
      502,
    );
  }
  return safeRound(value.amount);
}

function selectEnergy(
  values: Map<number, NutrientValue>,
  dataType: AcceptedDataType,
): { kcal: number; derivation: NutrientDerivation } {
  const preferred = dataType === "Foundation"
    ? [
      [NUTRIENT_IDS.energyAtwaterSpecificKcal, "2048_kcal"],
      [NUTRIENT_IDS.energyAtwaterGeneralKcal, "2047_kcal"],
      [NUTRIENT_IDS.energyLegacyKcal, "1008_kcal"],
    ] as const
    : [[NUTRIENT_IDS.energyLegacyKcal, "1008_kcal"]] as const;

  let selected: { kcal: number; source: NutrientDerivation["energy"] } | null = null;
  for (const [id, source] of preferred) {
    const value = values.get(id);
    if (value !== undefined) {
      if (value.unit && value.unit !== "KCAL") {
        throw new ProviderError("candidate_invalid_unit", "Energy unit is invalid.", 502);
      }
      selected = { kcal: value.amount, source };
      break;
    }
  }
  const energyKjValue = values.get(NUTRIENT_IDS.energyKj);
  if (energyKjValue?.unit && energyKjValue.unit !== "KJ") {
    throw new ProviderError("candidate_invalid_unit", "Energy unit is invalid.", 502);
  }
  const energyKj = energyKjValue?.amount;
  if (!selected && energyKj !== undefined) {
    selected = { kcal: energyKj / 4.184, source: "1062_kj_converted" };
  }
  if (!selected || selected.kcal < 0 || selected.kcal > 1_500) {
    throw new ProviderError(
      "candidate_invalid_energy",
      "Energy data is unavailable or invalid.",
      502,
    );
  }
  if (energyKj !== undefined) {
    const converted = energyKj / 4.184;
    if (converted < 0 || converted > 1_500) {
      throw new ProviderError("candidate_invalid_energy", "Energy data is invalid.", 502);
    }
    const tolerance = Math.max(25, selected.kcal * 0.2);
    if (
      selected.source !== "1062_kj_converted" && Math.abs(converted - selected.kcal) > tolerance
    ) {
      throw new ProviderError("candidate_conflicting_energy", "Energy sources conflict.", 502);
    }
  }
  return {
    kcal: safeRound(selected.kcal),
    derivation: { energy: selected.source, reference_basis: "per_100_g" },
  };
}

function normalizePortions(food: UnknownRecord): SafePortion[] {
  if (!Array.isArray(food.foodPortions)) return [];
  const portions: SafePortion[] = [];
  for (const rawPortion of food.foodPortions.slice(0, MAX_PORTIONS * 2)) {
    const portion = record(rawPortion);
    if (!portion) continue;
    const amount = finiteNumber(portion.amount);
    const gramWeight = finiteNumber(portion.gramWeight);
    const modifier = boundedText(portion.modifier, 80);
    const measureUnit = record(portion.measureUnit);
    const measureName = boundedText(measureUnit?.name, 60);
    const label = modifier ?? measureName;
    if (!label || amount === null || amount <= 0 || amount > 10_000) continue;
    if (gramWeight === null || gramWeight <= 0 || gramWeight > 100_000) continue;
    portions.push({
      label,
      amount: safeRound(amount),
      unit: "serving",
      equivalent_amount: safeRound(gramWeight),
      equivalent_unit: "g",
    });
    if (portions.length === MAX_PORTIONS) break;
  }
  return portions;
}

export async function normalizeUsdaFood(
  rawFood: unknown,
  retrievedAt: Date,
): Promise<SafeCandidate> {
  const food = record(rawFood);
  if (!food) {
    throw new ProviderError("candidate_malformed", "Provider candidate is malformed.", 502);
  }

  const providerFoodIdValue = finiteNumber(food.fdcId);
  const providerFoodId = providerFoodIdValue !== null && Number.isSafeInteger(providerFoodIdValue)
    ? String(providerFoodIdValue)
    : typeof food.fdcId === "string"
    ? food.fdcId.trim()
    : "";
  const dataType = acceptedDataType(food.dataType);
  const name = boundedText(food.description, 180);
  if (!FDC_ID_PATTERN.test(providerFoodId) || !dataType || !name) {
    throw new ProviderError("candidate_identity_invalid", "Provider identity is invalid.", 502);
  }

  const nutrients = nutrientMap(food);
  if (nutrients.size === 0) {
    throw new ProviderError(
      "candidate_missing_nutrients",
      "Provider nutrient data is unavailable.",
      502,
    );
  }
  const energy = selectEnergy(nutrients, dataType);
  const sourceVersion = boundedText(food.publicationDate ?? food.releaseDate, 120);

  return {
    candidate_id: await createCandidateId(providerFoodId),
    provider: PROVIDER_CODE,
    provider_label: PROVIDER_LABEL,
    provider_food_id: providerFoodId,
    name,
    brand: boundedText(food.brandOwner ?? food.brandName, 120),
    data_type: dataType,
    mapping_version: MAPPING_VERSION,
    reference_amount: 100,
    reference_unit: "g",
    kcal: energy.kcal,
    protein: readMacro(nutrients, NUTRIENT_IDS.protein, true) as number,
    carbohydrates: readMacro(nutrients, NUTRIENT_IDS.carbohydrates, true) as number,
    fat: readMacro(nutrients, NUTRIENT_IDS.fat, true) as number,
    fiber: readMacro(nutrients, NUTRIENT_IDS.fiber, false),
    portions: normalizePortions(food),
    derivation: energy.derivation,
    quality: "candidate",
    attribution: {
      label: PROVIDER_LABEL,
      license: "CC0 1.0",
      url: PROVIDER_ATTRIBUTION_URL,
    },
    provenance: {
      provider: PROVIDER_CODE,
      provider_food_id: providerFoodId,
      data_type: dataType,
      mapping_version: MAPPING_VERSION,
      retrieved_at: retrievedAt.toISOString(),
      source_version: sourceVersion,
    },
  };
}

export interface NormalizedSearchResult {
  candidates: SafeCandidate[];
  rejectedCount: number;
}

export async function normalizeUsdaSearchPayload(
  rawPayload: unknown,
  retrievedAt: Date,
): Promise<NormalizedSearchResult> {
  const payload = record(rawPayload);
  if (!payload || !Array.isArray(payload.foods)) {
    throw new ProviderError("provider_response_malformed", "Provider response is malformed.", 502);
  }
  const candidates: SafeCandidate[] = [];
  let rejectedCount = 0;
  for (const food of payload.foods.slice(0, MAX_SEARCH_RESULTS * 3)) {
    try {
      const candidate = await normalizeUsdaFood(food, retrievedAt);
      if (!candidates.some((existing) => existing.candidate_id === candidate.candidate_id)) {
        candidates.push(candidate);
      }
    } catch (error) {
      if (!(error instanceof ProviderError)) throw error;
      rejectedCount += 1;
    }
    if (candidates.length === MAX_SEARCH_RESULTS) break;
  }
  return { candidates, rejectedCount };
}
