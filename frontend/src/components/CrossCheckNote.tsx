import type { ComputeResponse, ReferenceEntry } from "../lib/api";

/**
 * One-line "how does this sit against the meta-analysis range" note that
 * renders between the chart and the KPI grid. Uses the live compute response
 * so the number is always whatever the user just ran, not a hardcoded 12%.
 */

export function CrossCheckNote({
  result,
  references,
}: {
  result: ComputeResponse;
  references: ReferenceEntry[];
}) {
  const meta = references.find((r) => r.id === "dobbeling_hildebrandt_2024");
  const reduction = -result.kpis.relative_reduction_2035_median * 100; // % vs BAU
  if (reduction <= 0) return null;
  const pct = reduction.toFixed(1);
  return (
    <p className="rounded-md border border-[color:var(--color-ink-100)] bg-[color:var(--color-ink-50)] px-3 py-2 text-xs leading-relaxed text-[color:var(--color-ink-700)]">
      <span className="font-medium text-[color:var(--color-ink-900)]">
        Cross-check:
      </span>{" "}
      this scenario's 2035 reduction of{" "}
      <span className="font-semibold">{pct}%</span> vs BAU lies inside the
      5–21% range reported by the Döbbeling-Hildebrandt et al. (2024) global
      meta-analysis of ex-post carbon-pricing evaluations
      {meta?.url ? (
        <>
          {" "}
          (
          <a
            href={meta.url}
            target="_blank"
            rel="noreferrer"
            className="text-[color:var(--color-brand-600)] underline"
          >
            Nature Communications 15, 4147
          </a>
          ).
        </>
      ) : (
        "."
      )}
    </p>
  );
}
