import type { ReferenceEntry } from "../lib/api";
import { Card, Pill, SectionTitle } from "./primitives";

/**
 * Side-by-side literature comparison rendered beneath the KPI row. The three
 * non-log-log entries are carried purely for external validation — they are
 * *not* substitutable for Liu (2026) in compute. Each card makes the
 * dimensional-mismatch explicit via a warning chip.
 */

const METHOD_LABEL: Record<ReferenceEntry["method_type"], string> = {
  log_log_elasticity: "Log-log semi-elasticity",
  att_pct_reduction: "Meta-analysis ATT",
  semi_elasticity_growth: "Growth-rate semi-elasticity",
};

export function LiteratureComparison({
  references,
}: {
  references: ReferenceEntry[];
}) {
  const external = references.filter((r) => r.method_type !== "log_log_elasticity");
  if (external.length === 0) return null;

  return (
    <Card>
      <SectionTitle
        title="Literature context — external validation"
        help="These studies are reported for comparison only; their estimates use different functional forms and cannot be substituted into the simulation."
      />
      <p className="mb-3 text-xs leading-relaxed text-[color:var(--color-ink-500)]">
        The simulation above runs with Liu (2026) β̂ = −0.2273. Each entry
        below uses a different estimator, so numbers are not directly
        substitutable — the aim is to check whether the tool's output lies in
        a plausible band.
      </p>
      <ul className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {external.map((ref) => (
          <li
            key={ref.id}
            className="flex h-full flex-col rounded-lg border border-[color:var(--color-ink-100)] bg-white p-3"
          >
            <div className="mb-1 flex flex-wrap items-center gap-1">
              <Pill tone="neutral">{METHOD_LABEL[ref.method_type]}</Pill>
              {ref.warning_label ? <Pill tone="warn">context only</Pill> : null}
            </div>
            <div className="text-xs font-semibold text-[color:var(--color-ink-900)]">
              {ref.citation.split(".").slice(0, 2).join(".")}
            </div>
            <div className="mt-0.5 text-xs text-[color:var(--color-ink-500)]">
              {ref.region} · {ref.sector}
            </div>
            {ref.headline_finding ? (
              <div className="mt-2 text-xs leading-relaxed text-[color:var(--color-ink-700)]">
                <span className="font-medium text-[color:var(--color-ink-900)]">
                  Finding:{" "}
                </span>
                {ref.headline_finding}
              </div>
            ) : null}
            {ref.comparison_note ? (
              <div className="mt-2 text-xs leading-relaxed text-[color:var(--color-ink-700)]">
                <span className="font-medium text-[color:var(--color-ink-900)]">
                  Comparison:{" "}
                </span>
                {ref.comparison_note}
              </div>
            ) : null}
            {ref.warning_label ? (
              <div className="mt-2 rounded-md bg-[color:var(--color-warn-100)] p-2 text-xs leading-relaxed text-[color:var(--color-warn-500)]">
                {ref.warning_label}
              </div>
            ) : null}
            {ref.url ? (
              <a
                href={ref.url}
                target="_blank"
                rel="noreferrer"
                className="mt-auto pt-2 text-xs text-[color:var(--color-brand-600)] underline"
              >
                DOI / source ↗
              </a>
            ) : null}
          </li>
        ))}
      </ul>
    </Card>
  );
}
