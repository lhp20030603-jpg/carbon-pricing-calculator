import type { ComputeResponse } from "../lib/api";
import { LabeledValue } from "./primitives";

function formatGt(mt: number): string {
  return (mt / 1_000).toLocaleString("en", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatPct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

export function KPICards({ result }: { result: ComputeResponse }) {
  const k = result.kpis;
  const mcOn = result.mc_n_effective > 0;
  const kpis = [
    {
      label: "Cumulative reduction vs BAU",
      value: `${formatGt(k.cumulative_reduction_mt_median)} Gt`,
      hint: mcOn
        ? `5–95: ${formatGt(k.cumulative_reduction_mt_p5)} – ${formatGt(
            k.cumulative_reduction_mt_p95,
          )} Gt`
        : "Deterministic only (mc_n = 0)",
    },
    {
      label: "Peak year (median)",
      value: String(k.peak_year_median),
      hint: mcOn ? `Range ${k.peak_year_p5} – ${k.peak_year_p95}` : "Deterministic only",
    },
    {
      label: "2035 emissions",
      value: `${formatGt(k.emissions_2035_mt_median)} Gt`,
      hint: `${formatPct(k.relative_reduction_2035_median)} vs BAU`,
    },
  ];
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {kpis.map((kpi) => (
        <div
          key={kpi.label}
          className="rounded-xl border border-[color:var(--color-ink-100)] bg-white p-4 shadow-sm"
        >
          <LabeledValue label={kpi.label} value={kpi.value} hint={kpi.hint} />
        </div>
      ))}
    </div>
  );
}
