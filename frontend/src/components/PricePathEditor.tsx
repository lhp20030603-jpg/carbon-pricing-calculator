import { useState } from "react";

import type { PricePoint } from "../lib/api";
import { Button } from "./primitives";

export function PricePathEditor({
  path,
  onChange,
}: {
  path: PricePoint[];
  onChange: (next: PricePoint[]) => void;
}) {
  const [start, setStart] = useState<number>(Math.round(path[0]?.price_cny ?? 0));
  const [end, setEnd] = useState<number>(
    Math.round(path[path.length - 1]?.price_cny ?? 0),
  );

  const applyLinear = () => {
    if (path.length < 2) return;
    const n = path.length;
    const step = (end - start) / (n - 1);
    onChange(
      path.map((p, i) => ({
        year: p.year,
        price_cny: Math.max(0, Math.round((start + step * i) * 100) / 100),
      })),
    );
  };

  const setAllFlat = (value: number) => {
    onChange(path.map((p) => ({ year: p.year, price_cny: Math.max(0, value) })));
  };

  const updateYear = (year: number, value: number) => {
    onChange(
      path.map((p) =>
        p.year === year
          ? { year: p.year, price_cny: Math.max(0, Math.min(10_000, value)) }
          : p,
      ),
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-2 text-sm">
        <label className="flex flex-col">
          <span className="text-xs text-[color:var(--color-ink-500)]">2021 start</span>
          <input
            type="number"
            min={0}
            max={10_000}
            step={1}
            value={start}
            onChange={(e) => setStart(Number(e.target.value))}
            className="w-24 rounded border border-[color:var(--color-ink-300)] px-2 py-1 tabular-nums"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-xs text-[color:var(--color-ink-500)]">2035 end</span>
          <input
            type="number"
            min={0}
            max={10_000}
            step={1}
            value={end}
            onChange={(e) => setEnd(Number(e.target.value))}
            className="w-24 rounded border border-[color:var(--color-ink-300)] px-2 py-1 tabular-nums"
          />
        </label>
        <Button variant="secondary" onClick={applyLinear} className="py-1">
          Apply linear ramp
        </Button>
        <Button
          variant="ghost"
          onClick={() => setAllFlat(start)}
          className="py-1"
          title="Set every year to the start value"
        >
          Flat
        </Button>
      </div>
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 xl:grid-cols-5">
        {path.map((p) => (
          <label key={p.year} className="flex flex-col text-xs">
            <span className="text-[color:var(--color-ink-500)]">{p.year}</span>
            <input
              type="number"
              min={0}
              max={10_000}
              step={1}
              value={Math.round(p.price_cny * 100) / 100}
              onChange={(e) => updateYear(p.year, Number(e.target.value))}
              className="mt-0.5 rounded border border-[color:var(--color-ink-300)] px-2 py-1 text-right tabular-nums text-[color:var(--color-ink-900)]"
              aria-label={`price in ${p.year}`}
            />
          </label>
        ))}
      </div>
      <p className="text-xs text-[color:var(--color-ink-500)]">
        Values in CNY/tCO₂. A warning caveat appears below the chart when any
        year exceeds 100 — the upper edge of the DID training range.
      </p>
    </div>
  );
}
