import type { ReferenceEntry } from "../lib/api";

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
          Coefficient source
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
      {active ? (
        <div className="rounded-md border border-[color:var(--color-ink-100)] bg-[color:var(--color-ink-50)] p-2 text-xs leading-relaxed">
          <div className="font-medium text-[color:var(--color-ink-700)]">
            β̂ = {active.coefficient.toFixed(4)} (SE {active.std_err.toFixed(4)})
          </div>
          <div className="text-[color:var(--color-ink-500)]">
            {active.region} · {active.sector} · {active.method}
          </div>
          {active.notes ? (
            <div className="mt-1 text-[color:var(--color-ink-500)]">{active.notes}</div>
          ) : null}
          {active.url ? (
            <a
              href={active.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-block text-[color:var(--color-brand-600)] underline"
            >
              Source
            </a>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
