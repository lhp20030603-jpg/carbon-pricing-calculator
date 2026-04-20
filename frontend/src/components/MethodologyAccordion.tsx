export function MethodologyAccordion() {
  return (
    <details className="rounded-xl border border-[color:var(--color-ink-100)] bg-white open:bg-white">
      <summary className="cursor-pointer select-none px-4 py-3 text-sm font-semibold text-[color:var(--color-ink-700)]">
        Methodology & caveats
      </summary>
      <div className="space-y-4 border-t border-[color:var(--color-ink-100)] px-4 py-4 text-sm leading-relaxed text-[color:var(--color-ink-700)]">
        <section>
          <h3 className="mb-1 text-sm font-semibold">Model</h3>
          <p>
            A reduced-form partial-adjustment model applied to China's thermal
            power sector. At each year the log-price signal
            ρ<sub>t</sub> = ln((P<sub>t</sub>+ε)/P<sub>ref</sub>) is clamped to
            zero when P<sub>t</sub> ≤ P<sub>ref</sub>, multiplied by the
            semi-elasticity β̂ and the free-allocation dampener (1 − λ·f), and
            then smoothed through the Koyck adjustment
            Δln(E<sub>t</sub>) = α·short<sub>t</sub> + (1 − α)·Δln(E<sub>t−1</sub>).
          </p>
          <p className="mt-1 text-xs text-[color:var(--color-ink-500)]">
            P<sub>ref</sub> = 45 CNY/tCO₂, λ = 0.3, ε = 1 CNY/t, Δln(E
            <sub>2020</sub>) = 0. Free allocation is a behavioural dampener, not
            a marginal-price discount — see methodology.pdf § Free-allocation
            treatment.
          </p>
        </section>
        <section>
          <h3 className="mb-1 text-sm font-semibold">Coefficient provenance</h3>
          <p>
            Default β̂ = −0.2273 (SE 0.0793) from Liu (2026) matched-DID on six
            treated provinces across China's pilot ETS (2013–2020). Alternate
            coefficients are served from the backend <code>references.db</code>
            {" "}and carry their own region/sector context; applying a non-China
            coefficient triggers an explicit scope mismatch warning.
          </p>
        </section>
        <section>
          <h3 className="mb-1 text-sm font-semibold">External validity caveats</h3>
          <ul className="list-disc space-y-1 pl-5 text-xs">
            <li>
              Training sample covers prices mostly in 20–80 CNY/tCO₂. Prices
              above 100 CNY/tCO₂ trigger a visual warning chip.
            </li>
            <li>
              β̂ is a stylised parameter, not a validated national-ETS
              elasticity. Regime-transfer risk is non-trivial.
            </li>
            <li>
              Projections past 2030 assume approximately stationary fuel mix
              and should be read as policy exploration rather than forecasts.
            </li>
            <li>
              Applies only to thermal power. Multi-sector expansion is V2.
            </li>
          </ul>
        </section>
        <section>
          <h3 className="mb-1 text-sm font-semibold">Further reading</h3>
          <p className="text-xs">
            Download the full methodology report (LaTeX source + PDF) and read
            the companion English blog for the dissertation → tool framing.
          </p>
        </section>
      </div>
    </details>
  );
}
