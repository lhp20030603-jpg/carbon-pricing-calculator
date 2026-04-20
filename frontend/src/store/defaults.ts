/**
 * Default scenario inputs + parameter metadata for the UI.
 * Values mirror SPEC §4.1 slider ranges; must stay in lockstep with
 * backend Pydantic validation.
 */

import type { ScenarioInputs } from "../lib/api";

export const POLICY_YEARS: number[] = Array.from({ length: 15 }, (_, i) => 2021 + i);

export const DEFAULT_INPUTS: ScenarioInputs = {
  price_path: POLICY_YEARS.map((y, i) => ({
    year: y,
    price_cny: 80 + ((100 - 80) * i) / (POLICY_YEARS.length - 1),
  })),
  free_allocation_share: 0.9,
  coefficient_source: "author_did_2026",
  alpha: 0.3,
  gdp_growth: 0.045,
  energy_intensity_improvement: 0.02,
  electrification_rate: 0.005,
  mc_n: 10_000,
  mc_seed: 42,
  e_2020_mt: 5150.0,
};

export type SliderMeta = {
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  decimals: number;
  help: string;
};

export const SLIDER_META: Record<
  "free_allocation_share" | "alpha" | "gdp_growth" | "energy_intensity_improvement" | "electrification_rate",
  SliderMeta
> = {
  free_allocation_share: {
    label: "Free allocation share",
    unit: "",
    min: 0,
    max: 1,
    step: 0.05,
    decimals: 2,
    help:
      "Share of allowances issued free. Dampens behavioural response by (1 − λ·f), λ=0.3 — it does NOT alter the marginal carbon price.",
  },
  alpha: {
    label: "Partial adjustment (α)",
    unit: "",
    min: 0.1,
    max: 0.6,
    step: 0.05,
    decimals: 2,
    help: "Speed of convergence from short-run to long-run response (Koyck).",
  },
  gdp_growth: {
    label: "Real GDP growth (g)",
    unit: "%/yr",
    min: 0.02,
    max: 0.06,
    step: 0.005,
    decimals: 3,
    help: "Annual real GDP growth rate used in the BAU trajectory.",
  },
  energy_intensity_improvement: {
    label: "Energy intensity improvement (e)",
    unit: "%/yr",
    min: 0,
    max: 0.03,
    step: 0.0025,
    decimals: 4,
    help: "Annual reduction in energy consumed per unit of GDP.",
  },
  electrification_rate: {
    label: "Power-sector decarbonisation (η)",
    unit: "%/yr",
    min: 0,
    max: 0.02,
    step: 0.0025,
    decimals: 4,
    help: "Annual reduction in emissions per unit of electricity generated.",
  },
};

export const MC_N_OPTIONS: Array<{ value: number; label: string }> = [
  { value: 0, label: "0 — deterministic only" },
  { value: 1_000, label: "1,000 — quick preview" },
  { value: 10_000, label: "10,000 — full run (SPEC default)" },
];
