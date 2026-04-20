import type { ChangeEvent } from "react";

import type { SliderMeta } from "../store/defaults";

export function SliderControl({
  value,
  meta,
  onChange,
}: {
  value: number;
  meta: SliderMeta;
  onChange: (v: number) => void;
}) {
  const display = meta.decimals >= 3
    ? (value * (meta.unit.includes("%") ? 100 : 1)).toFixed(
        meta.unit.includes("%") ? Math.max(meta.decimals - 2, 1) : meta.decimals,
      )
    : value.toFixed(meta.decimals);
  const unit = meta.unit;

  const handle = (e: ChangeEvent<HTMLInputElement>) => {
    const next = Number(e.target.value);
    if (!Number.isNaN(next)) onChange(next);
  };

  return (
    <label className="block text-sm">
      <div className="mb-1 flex items-baseline justify-between gap-2">
        <span
          className="font-medium text-[color:var(--color-ink-700)]"
          title={meta.help}
        >
          {meta.label}
        </span>
        <span className="tabular-nums text-[color:var(--color-ink-900)]">
          {display}
          {unit ? ` ${unit}` : ""}
        </span>
      </div>
      <input
        type="range"
        min={meta.min}
        max={meta.max}
        step={meta.step}
        value={value}
        onChange={handle}
        aria-label={meta.label}
      />
    </label>
  );
}
