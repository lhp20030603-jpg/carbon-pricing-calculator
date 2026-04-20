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
    <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-5">
      {presets.map((preset) => {
        const active = preset.id === activeId;
        return (
          <button
            key={preset.id}
            onClick={() => onSelect(preset)}
            title={preset.description}
            className={clsx(
              "rounded-lg border p-3 text-left text-sm transition-colors",
              active
                ? "border-[color:var(--color-brand-500)] bg-[color:var(--color-brand-100)]"
                : "border-[color:var(--color-ink-300)] bg-white hover:bg-[color:var(--color-ink-100)]",
            )}
          >
            <div className="font-semibold text-[color:var(--color-ink-900)]">
              {preset.name}
            </div>
            <div className="mt-1 line-clamp-2 text-xs text-[color:var(--color-ink-500)]">
              {preset.description}
            </div>
          </button>
        );
      })}
    </div>
  );
}
