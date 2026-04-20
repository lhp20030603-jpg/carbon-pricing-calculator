import { useEffect, useMemo } from "react";

import { ActionButtons } from "./components/ActionButtons";
import { AdvancedPanel } from "./components/AdvancedPanel";
import { CaveatsPanel } from "./components/CaveatsPanel";
import { ChartPanel, type ComputeState } from "./components/ChartPanel";
import { CoefficientSelect } from "./components/CoefficientSelect";
import { Header } from "./components/Header";
import { KPICards } from "./components/KPICards";
import { MethodologyAccordion } from "./components/MethodologyAccordion";
import { PricePathEditor } from "./components/PricePathEditor";
import { ScenarioCards } from "./components/ScenarioCards";
import { SliderControl } from "./components/SliderControl";
import { Card, SectionTitle } from "./components/primitives";
import {
  useComputeMutation,
  useHealthPing,
  useReferences,
  useScenarioPresets,
} from "./hooks/useBackendData";
import { useScenarioState } from "./hooks/useScenarioState";
import { SLIDER_META } from "./store/defaults";

function App() {
  const health = useHealthPing();
  const presets = useScenarioPresets();
  const references = useReferences();
  const compute = useComputeMutation();
  const { inputs, patch, replace, applyPreset, activePresetId } = useScenarioState(
    presets.data ?? [],
  );

  // Auto-run Compute once the preset library lands so the chart is populated
  // without forcing a click just to see the default scenario.
  useEffect(() => {
    if (presets.isSuccess && !compute.data && !compute.isPending) {
      compute.mutate(inputs);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [presets.isSuccess]);

  const backendOnline = health.isSuccess ? true : health.isError ? false : null;

  const chartState = useMemo<ComputeState>(() => {
    if (compute.isPending) return { status: "loading" };
    if (compute.data) return { status: "success", result: compute.data };
    if (compute.isError) {
      return {
        status: "error",
        message: compute.error instanceof Error ? compute.error.message : "Unknown error",
        onRetry: () => compute.mutate(inputs),
      };
    }
    if (backendOnline === null) return { status: "warming" };
    return { status: "idle" };
  }, [compute, backendOnline, inputs]);

  return (
    <div className="min-h-full">
      <Header backendOnline={backendOnline} />
      <main className="mx-auto grid max-w-[1440px] grid-cols-1 gap-4 p-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <Card>
            <SectionTitle title="Scenario presets" help="Curated starting points" />
            <ScenarioCards
              presets={presets.data ?? []}
              activeId={activePresetId}
              onSelect={applyPreset}
            />
          </Card>

          <Card>
            <SectionTitle
              title="Carbon price path (CNY/tCO₂)"
              help="15-year trajectory; extrapolation warning fires above 100"
            />
            <PricePathEditor
              path={inputs.price_path}
              onChange={(next) => patch({ price_path: next })}
            />
          </Card>

          <Card>
            <SectionTitle title="Primary inputs" />
            <div className="space-y-4">
              <SliderControl
                value={inputs.free_allocation_share}
                meta={SLIDER_META.free_allocation_share}
                onChange={(v) => patch({ free_allocation_share: v })}
              />
              <CoefficientSelect
                references={references.data ?? []}
                value={inputs.coefficient_source}
                onChange={(id) => patch({ coefficient_source: id })}
              />
            </div>
          </Card>

          <AdvancedPanel inputs={inputs} onPatch={patch} />

          <Card>
            <ActionButtons
              inputs={inputs}
              onCompute={() => compute.mutate(inputs)}
              onImport={replace}
              computing={compute.isPending}
            />
          </Card>
        </aside>

        <section className="space-y-4">
          <ChartPanel state={chartState} />

          {compute.data ? (
            <>
              <KPICards result={compute.data} />
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card>
                  <SectionTitle title="External validity caveats" />
                  <CaveatsPanel caveats={compute.data.caveats} />
                </Card>
                <Card>
                  <SectionTitle title="Coefficient used" />
                  <div className="text-sm leading-relaxed">
                    <div className="font-semibold text-[color:var(--color-ink-900)]">
                      {compute.data.coefficient.label}
                    </div>
                    <div className="text-xs text-[color:var(--color-ink-500)]">
                      β̂ = {compute.data.coefficient.beta.toFixed(4)} (SE{" "}
                      {compute.data.coefficient.std_err.toFixed(4)})
                      <br />
                      {compute.data.coefficient.region} ·{" "}
                      {compute.data.coefficient.sector}
                    </div>
                    <div className="mt-1 text-xs text-[color:var(--color-ink-700)]">
                      {compute.data.coefficient.citation}
                    </div>
                  </div>
                </Card>
              </div>
            </>
          ) : null}

          <MethodologyAccordion />
        </section>
      </main>
      <footer className="mx-auto max-w-[1440px] px-4 pb-8 text-xs text-[color:var(--color-ink-500)]">
        <p>
          Built from Liu (2026) BSc dissertation, University of Glasgow.
          Deterministic model + Monte Carlo uncertainty. Caveats in
          methodology.pdf.{" "}
          <span className="italic">Policy exploration, not a forecast.</span>
        </p>
      </footer>
    </div>
  );
}

export default App;
