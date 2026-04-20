import { Suspense, lazy, type ReactNode } from "react";

import type { ComputeResponse } from "../lib/api";
import { ErrorBoundary } from "./ErrorBoundary";
import { Button, Pill } from "./primitives";

// Plotly is a ~1.4 MB gzipped chunk; defer the download until the chart must
// render, so first paint isn't blocked. The dynamic import also removes the
// `modulepreload` hint from the initial HTML.
const FanChart = lazy(() =>
  import("./FanChart").then((m) => ({ default: m.FanChart })),
);

type ComputeState =
  | { status: "idle" }
  | { status: "warming" }
  | { status: "loading" }
  | { status: "success"; result: ComputeResponse }
  | { status: "error"; message: string; onRetry: () => void };

export function ChartPanel({ state }: { state: ComputeState }) {
  return (
    <section
      aria-label="Emissions trajectory"
      className="rounded-xl border border-[color:var(--color-ink-100)] bg-white shadow-sm"
    >
      <div className="flex items-start justify-between gap-3 border-b border-[color:var(--color-ink-100)] px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">
            Emissions trajectory (Mt CO₂)
          </h2>
          <p className="text-xs text-[color:var(--color-ink-500)]">
            BAU · median · 25/75 band · 5/95 band. Hover the chart for
            year-by-year detail.
          </p>
        </div>
        {state.status === "success" ? (
          <div className="flex items-center gap-2">
            <Pill tone="brand">
              N = {state.result.mc_n_effective.toLocaleString("en")}
            </Pill>
            <Pill tone="neutral">seed {state.result.mc_seed}</Pill>
          </div>
        ) : null}
      </div>
      <div className="p-2">
        {state.status === "success" ? (
          <ErrorBoundary
            fallback={({ error, reset }) => (
              <PlaceholderFrame>
                <div className="flex flex-col items-center gap-2 text-center">
                  <div className="text-[color:var(--color-crit-500)]">
                    Chart rendering failed: {error.message}
                  </div>
                  <div className="text-xs text-[color:var(--color-ink-500)]">
                    The compute response is still available — this is a
                    display-layer error.
                  </div>
                  <Button variant="secondary" onClick={reset}>
                    Try rendering again
                  </Button>
                </div>
              </PlaceholderFrame>
            )}
          >
            <Suspense
              fallback={<PlaceholderFrame>Loading chart library…</PlaceholderFrame>}
            >
              <FanChart result={state.result} />
            </Suspense>
          </ErrorBoundary>
        ) : (
          <PlaceholderFrame>{renderPlaceholder(state)}</PlaceholderFrame>
        )}
      </div>
    </section>
  );
}

function renderPlaceholder(state: ComputeState): ReactNode {
  if (state.status === "warming") {
    return (
      <div className="space-y-1">
        <div>Backend warming up…</div>
        <div className="text-xs text-[color:var(--color-ink-500)]">
          Render Free cold start can take up to 30 s. This happens at most once
          per session.
        </div>
      </div>
    );
  }
  if (state.status === "loading") {
    return <div>Computing scenario…</div>;
  }
  if (state.status === "error") {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="text-[color:var(--color-crit-500)]">
          Compute failed: {state.message}
        </div>
        <Button variant="secondary" onClick={state.onRetry}>
          Retry
        </Button>
      </div>
    );
  }
  return <div>Set inputs and click Compute to generate a scenario.</div>;
}

function PlaceholderFrame({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-[420px] flex-col items-center justify-center text-center text-sm text-[color:var(--color-ink-500)]">
      {children}
    </div>
  );
}

export type { ComputeState };
