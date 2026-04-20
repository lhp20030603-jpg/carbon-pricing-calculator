import { useMemo } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";

import type { ComputeResponse } from "../lib/api";

// React-plotly's factory + plotly.js-dist-min is the officially recommended
// pairing for browser bundlers. It avoids the CJS default-import ambiguity
// that caused React error #130 when using `import Plot from 'react-plotly.js'`
// under Vite/Rolldown.
const Plot = createPlotlyComponent(Plotly as object);

const BAND_INNER = "rgba(20, 184, 166, 0.30)";
const BAND_OUTER = "rgba(20, 184, 166, 0.15)";
const MEDIAN_LINE = "#0f766e";
const BAU_LINE = "#64748b";

export function FanChart({ result }: { result: ComputeResponse }) {
  const traces = useMemo(() => buildTraces(result), [result]);
  return (
    <div
      aria-label="Emissions fan chart: BAU, median, and percentile bands (5/25/75/95)"
      role="img"
    >
      <Plot
        data={traces}
        layout={{
          autosize: true,
          height: 420,
          margin: { l: 56, r: 16, t: 24, b: 44 },
          hovermode: "x unified",
          xaxis: {
            title: { text: "Year" },
            showgrid: false,
            tickvals: result.years.filter((y) => y % 2 === 1),
            zeroline: false,
          },
          yaxis: {
            title: { text: "CO₂ emissions (Mt)" },
            rangemode: "tozero",
            gridcolor: "rgba(15, 23, 42, 0.06)",
            zeroline: false,
          },
          legend: {
            orientation: "h",
            yanchor: "bottom",
            y: 1.04,
            xanchor: "right",
            x: 1,
          },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: { family: "Inter, system-ui, sans-serif" },
        }}
        config={{ displayModeBar: false, responsive: true }}
        useResizeHandler
        style={{ width: "100%", height: "420px" }}
      />
    </div>
  );
}

function buildTraces(result: ComputeResponse): Plotly.Data[] {
  const { years, bau_mt, deterministic_mt, percentiles_mt } = result;

  const traces: Plotly.Data[] = [
    {
      x: years,
      y: bau_mt,
      mode: "lines",
      type: "scatter",
      name: "BAU",
      line: { color: BAU_LINE, dash: "dot", width: 2 },
      hovertemplate: "%{x}<br>BAU: %{y:.1f} Mt<extra></extra>",
    },
  ];

  if (percentiles_mt) {
    traces.push(
      {
        x: years,
        y: percentiles_mt.p95,
        mode: "lines",
        type: "scatter",
        name: "5/95 band",
        line: { color: "transparent" },
        showlegend: true,
        hovertemplate: "%{x}<br>p95: %{y:.1f} Mt<extra></extra>",
      },
      {
        x: years,
        y: percentiles_mt.p5,
        mode: "lines",
        type: "scatter",
        name: "5/95 band",
        fill: "tonexty",
        fillcolor: BAND_OUTER,
        line: { color: "transparent" },
        showlegend: false,
        hovertemplate: "%{x}<br>p5: %{y:.1f} Mt<extra></extra>",
      },
      {
        x: years,
        y: percentiles_mt.p75,
        mode: "lines",
        type: "scatter",
        name: "25/75 band",
        line: { color: "transparent" },
        showlegend: true,
        hovertemplate: "%{x}<br>p75: %{y:.1f} Mt<extra></extra>",
      },
      {
        x: years,
        y: percentiles_mt.p25,
        mode: "lines",
        type: "scatter",
        name: "25/75 band",
        fill: "tonexty",
        fillcolor: BAND_INNER,
        line: { color: "transparent" },
        showlegend: false,
        hovertemplate: "%{x}<br>p25: %{y:.1f} Mt<extra></extra>",
      },
    );
  }

  traces.push({
    x: years,
    y: percentiles_mt?.p50 ?? deterministic_mt,
    mode: "lines",
    type: "scatter",
    name: percentiles_mt ? "Median" : "Deterministic",
    line: { color: MEDIAN_LINE, width: 3 },
    hovertemplate: "%{x}<br>%{y:.1f} Mt<extra></extra>",
  });

  return traces;
}
