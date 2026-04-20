import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { ScenarioInputs, ScenarioPreset } from "../lib/api";
import { readUrlState, writeUrlState } from "../lib/url-state";
import { DEFAULT_INPUTS } from "../store/defaults";

/**
 * Central scenario-state hook.
 * - Seeds from URL state if present; otherwise from DEFAULT_INPUTS.
 * - Writes every change back to the URL (replaceState, not pushState).
 * - Derives the active preset id on the fly (no cascading renders).
 */
export function useScenarioState(presets: ScenarioPreset[]) {
  const [inputs, setInputs] = useState<ScenarioInputs>(() => {
    const urlState = readUrlState();
    return urlState ?? DEFAULT_INPUTS;
  });
  const skipUrlWrite = useRef(true);

  useEffect(() => {
    if (skipUrlWrite.current) {
      skipUrlWrite.current = false;
      return;
    }
    writeUrlState(inputs);
  }, [inputs]);

  const activePresetId = useMemo(() => {
    const match = presets.find((p) => inputsMatchPreset(inputs, p.inputs));
    return match?.id ?? null;
  }, [presets, inputs]);

  const patch = useCallback((diff: Partial<ScenarioInputs>) => {
    setInputs((prev) => ({ ...prev, ...diff }));
  }, []);

  const replace = useCallback((next: ScenarioInputs) => {
    setInputs(next);
  }, []);

  const applyPreset = useCallback((preset: ScenarioPreset) => {
    setInputs(preset.inputs);
  }, []);

  return { inputs, patch, replace, applyPreset, activePresetId };
}

function inputsMatchPreset(a: ScenarioInputs, b: ScenarioInputs): boolean {
  if (a.free_allocation_share !== b.free_allocation_share) return false;
  if (a.coefficient_source !== b.coefficient_source) return false;
  if (Math.abs(a.alpha - b.alpha) > 1e-6) return false;
  if (Math.abs(a.gdp_growth - b.gdp_growth) > 1e-6) return false;
  if (Math.abs(a.energy_intensity_improvement - b.energy_intensity_improvement) > 1e-6)
    return false;
  if (Math.abs(a.electrification_rate - b.electrification_rate) > 1e-6) return false;
  if (a.price_path.length !== b.price_path.length) return false;
  for (let i = 0; i < a.price_path.length; i++) {
    const pa = a.price_path[i];
    const pb = b.price_path[i];
    if (pa.year !== pb.year) return false;
    if (Math.abs(pa.price_cny - pb.price_cny) > 1e-3) return false;
  }
  return true;
}
