import type { Caveat } from "../lib/api";
import { Pill } from "./primitives";

export function CaveatsPanel({ caveats }: { caveats: Caveat[] }) {
  if (caveats.length === 0) {
    return (
      <div className="text-xs text-[color:var(--color-ink-500)]">
        No extrapolation caveats triggered for this scenario.
      </div>
    );
  }
  return (
    <ul className="space-y-2">
      {caveats.map((c) => (
        <li
          key={c.id}
          className="flex gap-2 rounded-lg border border-[color:var(--color-ink-100)] bg-white p-2"
        >
          <div className="shrink-0">
            <Pill
              tone={
                c.severity === "critical"
                  ? "crit"
                  : c.severity === "warning"
                    ? "warn"
                    : "neutral"
              }
            >
              {c.severity}
            </Pill>
          </div>
          <div className="min-w-0 text-xs leading-relaxed text-[color:var(--color-ink-700)]">
            <div className="font-semibold text-[color:var(--color-ink-900)]">
              {c.id.replace(/_/g, " ")}
            </div>
            <div>{c.message}</div>
          </div>
        </li>
      ))}
    </ul>
  );
}
