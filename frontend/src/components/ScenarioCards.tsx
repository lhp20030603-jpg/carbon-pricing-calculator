import clsx from "clsx";

import type { ScenarioPreset } from "../lib/api";

export function ScenarioCards({
  presets,
  activeId,
  onSelect,
}: {
  presets: ScenarioPreset[];
  activeId: string | null;
  onSelect: (preset: ScenarioPreset) => void;
}) {
  if (presets.length === 0) {
    return (
      <div className="text-sm text-[color:var(--color-ink-500)]">
        Loading preset library…
      </div>
    );
  }
  return (
    <ul className="flex flex-col gap-1.5">
      {presets.map((preset) => {
        const active = preset.id === activeId;
        return (
          <li key={preset.id}>
            <button
              onClick={() => onSelect(preset)}
              title={preset.description}
              aria-pressed={active}
              className={clsx(
                "block w-full rounded-lg border px-3 py-2 text-left transition-colors",
                active
                  ? "border-[color:var(--color-brand-500)] bg-[color:var(--color-brand-100)]"
                  : "border-[color:var(--color-ink-300)] bg-white hover:bg-[color:var(--color-ink-100)]",
              )}
            >
              <div className="text-sm font-semibold text-[color:var(--color-ink-900)]">
                {preset.name}
              </div>
              <div className="mt-0.5 line-clamp-2 text-xs text-[color:var(--color-ink-500)]">
                {preset.description}
              </div>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
