import type { ReferenceEntry } from "../lib/api";
import { Pill } from "./primitives";

/**
 * Rebuilt as a *literature browser*: picking an entry does NOT change the
 * coefficient used for compute (Liu 2026 is the only one). It only drives
 * which reference the card below the dropdown shows in detail. The
 * LiteratureComparison panel below the chart renders all entries side-by-side.
 */

function methodTypeLabel(t: ReferenceEntry["method_type"]): string {
  switch (t) {
    case "log_log_elasticity":
      return "Log-log semi-elasticity";
    case "att_pct_reduction":
      return "Meta-analysis ATT";
    case "semi_elasticity_growth":
      return "Growth-rate semi-elasticity";
  }
}

export function CoefficientSelect({
  references,
  value,
  onChange,
}: {
  references: ReferenceEntry[];
  value: string;
  onChange: (id: string) => void;
}) {
  const active = references.find((r) => r.id === value);
  return (
    <div className="space-y-1 text-sm">
      <label className="flex flex-col">
        <span className="mb-1 font-medium text-[color:var(--color-ink-700)]">
          Coefficient &amp; literature context
        </span>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="rounded border border-[color:var(--color-ink-300)] bg-white px-2 py-1.5"
        >
          {references.length === 0 ? (
            <option value={value}>Loading…</option>
          ) : null}
          {references.map((ref) => (
            <option key={ref.id} value={ref.id}>
              {ref.id === "author_did_2026" ? "★ " : ""}
              {ref.citation.split(".")[0]} · {ref.region}
            </option>
          ))}
        </select>
      </label>
      <p className="text-xs leading-relaxed text-[color:var(--color-ink-500)]">
        The simulation always runs with Liu (2026) β̂ = −0.2273. This dropdown
        surfaces literature context only — it does not swap the coefficient.
      </p>
      {active ? (
        <div className="rounded-md border border-[color:var(--color-ink-100)] bg-[color:var(--color-ink-50)] p-2 text-xs leading-relaxed">
          <div className="mb-1 flex flex-wrap items-center gap-1">
            <Pill
              tone={active.method_type === "log_log_elasticity" ? "brand" : "neutral"}
            >
              {methodTypeLabel(active.method_type)}
            </Pill>
            {active.warning_label ? <Pill tone="warn">context only</Pill> : null}
          </div>
          {active.coefficient != null && active.std_err != null ? (
            <div className="font-medium text-[color:var(--color-ink-700)]">
              β̂ = {active.coefficient.toFixed(4)} (SE {active.std_err.toFixed(4)})
            </div>
          ) : null}
          <div className="text-[color:var(--color-ink-500)]">
            {active.region} · {active.sector} · {active.method}
          </div>
          {active.headline_finding ? (
            <div className="mt-1 text-[color:var(--color-ink-700)]">
              {active.headline_finding}
            </div>
          ) : null}
          {active.url ? (
            <a
              href={active.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-block text-[color:var(--color-brand-600)] underline"
            >
              Source ↗
            </a>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
