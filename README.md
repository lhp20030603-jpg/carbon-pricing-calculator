# Carbon Pricing Policy Impact Calculator

A prospective web calculator for China's national ETS. You set a carbon price path
from 2021 to 2035, pick a free-allocation share, and the tool returns year-by-year
power-sector CO₂ emissions with a Monte Carlo uncertainty fan. The headline
coefficient (β̂ = −0.2273, SE 0.0793) comes from my BSc dissertation — a
matched-DID estimate on China's pilot ETS, 2013–2020 — so the tool is really a way
to push that single number out to stylised 2035 trajectories with honest
uncertainty bands.

It is not a forecast, and it is not a substitute for an IAM or CGE model. The
whole point is to show what the dissertation's estimate implies at policy-relevant
prices, with the caveats kept visible at every step.

**Live demo**: _to be added_ · **Methodology report**: `docs/methodology.pdf` (V1 in progress)

## Screenshots

Screenshots and the live URL go here once the V1 deploy is up.

## Quickstart

Backend — Python 3.11 + FastAPI, managed with `uv`:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Frontend — Vite + React 18 + TypeScript:

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api/*` to `http://localhost:8000`, so the frontend fetches
the same relative paths it will use in production.

OpenAPI → TypeScript types (run while the backend is up):

```bash
cd frontend
npm run gen:types
```

## What the model does

At each year `t` in 2021–2035:

1. **Business-as-usual trajectory**
   `BAU_t = E_2020 × (1 + g − e − η)^(t − 2020)`, where `g` is GDP growth,
   `e` is energy-intensity improvement, `η` is power-sector decarbonisation.
2. **Short-run log response to price**
   `ρ_t = ln((P_t + ε) / P_ref)`, clamped to 0 when `P_t ≤ P_ref = 45 CNY/tCO₂`,
   and scaled by `β̂ × (1 − λ · f)`. Free allocation (`f`) is treated as a
   behavioural dampener, not as a discount on the marginal carbon price.
3. **Long-run adjustment**
   `Δln(E_t) = α · short_t + (1 − α) · Δln(E_{t−1})` with `Δln(E_{2020}) = 0`.
4. **Policy-adjusted emissions**
   `E_t = BAU_t × exp(Δln(E_t))`.

Monte Carlo (default N = 10,000) draws `β` from a truncated normal, and `α`, `g`,
`e`, `η` from bounded uniforms around the user's point estimates. Percentile bands
(5 / 25 / 50 / 75 / 95) are what you see in the fan chart. Set `N = 0` to get a
single deterministic run — this is also the canonical determinism gate used by the
acceptance tests.

## Model assumptions and what to trust

The estimate is from the **pilot phase**, not the national ETS, so the tool is
explicit about three kinds of extrapolation risk:

- **Price range**: the DID sample mostly covers prices in 20–80 CNY/tCO₂. Above
  100 CNY/tCO₂ the tool raises a warning caveat. Scenarios like IEA NZE-China
  reach 500 CNY/tCO₂ by 2035 — useful as a sensitivity exercise, not a forecast.
- **Regime transfer**: pilot and national ETS differ in stringency, benchmark
  design, and market liquidity. β̂ is a stylised parameter, not a validated
  national-ETS elasticity.
- **Structural change**: β̂ assumes an approximately stationary fuel mix.
  Projections past 2030 are best read as "what happens if the elasticity still
  held" rather than as actual paths.

Thermal power only. Multi-sector expansion (steel, cement, aluminum) is on the
V2 list.

## Coefficient provenance

| Source | β̂ | SE | Region | Sector | Method |
| --- | --- | --- | --- | --- | --- |
| Liu (2026) BSc dissertation, Glasgow | **−0.2273** | 0.0793 | China | Thermal power | Matched DID, 6 provinces, 2013–2020 |
| Green (2021), *Environ. Res. Lett.* | −0.05 | 0.03 | OECD avg. | Cross-sector | Systematic review (stylised mid-range) |
| Best, Burke, Jotzo (2020), *ERE* | −0.08 | 0.025 | Cross-country panel | Cross-sector | Panel FE, 1997–2017 |

Applying a non-China coefficient triggers a scope-mismatch warning in the UI.
The exact provenance is in the coefficient card next to the chart and in
`backend/app/data/references.db`. Numerical values for literature alternates are
stylised summaries pending a fuller literature review; they are flagged as such.

## Tech stack

- **Backend** — Python 3.11, FastAPI, Pydantic v2, numpy. Package management via
  `uv` (`pyproject.toml` + `uv.lock`).
- **Frontend** — React 18, TypeScript strict mode, Vite, Tailwind v4,
  react-plotly.js, `@tanstack/react-query`, nuqs-style URL state via lz-string.
- **Storage** — three read-only SQLite files shipped in the repo
  (`coefficients.db`, `references.db`, `scenarios.db`), rebuilt by
  `backend/scripts/build_data.py`.
- **Deploy** — Vercel for the static frontend, Render Free for the FastAPI
  backend (Dockerfile + `render.yaml` provided). Frontend pings `/api/health` on
  page load to pre-warm the Render cold start.

## Acceptance status

Backend V1 is test-covered at 97% on `compute/` (above the 80% bar in SPEC §9):

```bash
cd backend
uv run pytest --cov=app/compute   # 56/56 passing, 97% coverage
uv run ruff check . && uv run mypy app
```

Frontend builds clean with strict TS and ESLint. End-to-end smoke tests with the
Vite proxy return a valid fan-chart payload and the expected caveat chips.

## Design document

`SPEC.md` is the frozen v1.1 source of truth for scope, math, API contract, and
acceptance criteria. Anything in this README conflicts with SPEC.md, SPEC wins —
please open an issue.

## Citation

If you use the coefficient or the calculator in something you publish, please cite:

> Liu, H. (2026). *The Impacts of Carbon Emissions Trading on Decoupling in
> China's Provincial Power Sector.* BSc dissertation, University of Glasgow.

## Licence

MIT. See `LICENSE`.

## Author

Haopeng Liu — lhp20030603@gmail.com. The tool is part of a public portfolio
aimed at ESG consulting / carbon-market roles. I'm happy to take pull requests
that improve the methodology doc or add sector coverage.
