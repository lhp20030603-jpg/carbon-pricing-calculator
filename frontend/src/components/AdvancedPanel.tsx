import { useState } from "react";

import type { ScenarioInputs } from "../lib/api";
import { MC_N_OPTIONS, SLIDER_META } from "../store/defaults";
import { SliderControl } from "./SliderControl";

export function AdvancedPanel({
  inputs,
  onPatch,
}: {
  inputs: ScenarioInputs;
  onPatch: (patch: Partial<ScenarioInputs>) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <details
      open={open}
      onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}
      className="rounded-lg border border-[color:var(--color-ink-100)] bg-white"
    >
      <summary className="cursor-pointer select-none px-3 py-2 text-sm font-semibold text-[color:var(--color-ink-700)]">
        Advanced parameters
      </summary>
      <div className="space-y-4 border-t border-[color:var(--color-ink-100)] px-3 py-3">
        <SliderControl
          value={inputs.alpha}
          meta={SLIDER_META.alpha}
          onChange={(v) => onPatch({ alpha: v })}
        />
        <SliderControl
          value={inputs.gdp_growth}
          meta={SLIDER_META.gdp_growth}
          onChange={(v) => onPatch({ gdp_growth: v })}
        />
        <SliderControl
          value={inputs.energy_intensity_improvement}
          meta={SLIDER_META.energy_intensity_improvement}
          onChange={(v) => onPatch({ energy_intensity_improvement: v })}
        />
        <SliderControl
          value={inputs.electrification_rate}
          meta={SLIDER_META.electrification_rate}
          onChange={(v) => onPatch({ electrification_rate: v })}
        />

        <div className="grid grid-cols-2 gap-2 text-sm">
          <label className="flex flex-col">
            <span className="mb-1 font-medium text-[color:var(--color-ink-700)]">
              Monte Carlo N
            </span>
            <select
              value={inputs.mc_n}
              onChange={(e) => onPatch({ mc_n: Number(e.target.value) })}
              className="rounded border border-[color:var(--color-ink-300)] bg-white px-2 py-1.5"
            >
              {MC_N_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col">
            <span className="mb-1 font-medium text-[color:var(--color-ink-700)]">
              Random seed
            </span>
            <input
              type="number"
              min={0}
              max={2 ** 31 - 1}
              step={1}
              value={inputs.mc_seed}
              onChange={(e) => onPatch({ mc_seed: Math.max(0, Number(e.target.value) || 0) })}
              className="rounded border border-[color:var(--color-ink-300)] px-2 py-1.5 tabular-nums"
            />
          </label>
        </div>
        <p className="text-xs leading-relaxed text-[color:var(--color-ink-500)]">
          MC = 0 runs the deterministic model only — used by the SPEC §9
          determinism gate. Seed is URL-encoded so a shared link reproduces the
          exact fan.
        </p>
      </div>
    </details>
  );
}
