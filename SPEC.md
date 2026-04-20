# Carbon Pricing Policy Impact Calculator · Design Spec

| Field         | Value                                                                 |
| ------------- | --------------------------------------------------------------------- |
| Author        | Haopeng Liu (lhp20030603@gmail.com)                                   |
| Version       | 1.1 (calibration + deploy-gate consistency fix)                       |
| Date          | 2026-04-20                                                            |
| Status        | Approved design, pending implementation plan                          |
| Changelog     | 1.0 → 1.1: corrected free-allocation treatment (marginal vs burden); added `Δln(E_{2020})` initial condition; reconciled α MC range with slider; pinned caveat threshold to 100 CNY/t; replaced `docker compose up` with explicit two-command startup. |
| Repository    | `my-project/carbon-pricing-calculator/` (subdir of dissertation repo) |
| Target deploy | Vercel (frontend) + Render Free (backend)                             |
| V1 ETA        | 4–5 weeks part-time                                                   |

---

## 0. Purpose of This Document

This SPEC captures the full set of design decisions reached through structured brainstorming on 2026-04-20. It is the single source of truth for the V1 build and freezes scope. Any scope change after approval requires a new revision number.

---

## 1. Executive Summary

A web-based **prospective** policy impact calculator for China's national carbon emissions trading system (ETS, 2021+). Users input a multi-year carbon price path (2021–2035), a uniform free-allocation share, and BAU macro parameters; the tool returns year-by-year CO₂ emissions trajectories for the thermal power sector, with Monte Carlo uncertainty fans derived from the author's published DID estimate (β̂ = −0.2273, SE = 0.0793) plus a small literature library for comparison.

The project doubles as a portfolio piece for ESG-consulting / carbon-market job applications. It deliberately avoids being a generic calculator by: showing uncertainty as fan charts rather than point estimates, exposing coefficient provenance, and publishing a methodology PDF alongside the live tool.

---

## 2. Positioning & Audience

### 2.1 Audience (V1)

| Audience                           | Priority  | V1 treatment                                                                          |
| ---------------------------------- | --------- | ------------------------------------------------------------------------------------- |
| Policy researchers / ESG analysts  | Primary   | Full UI, all parameters exposed, methodology prominent                                |
| Carbon-market practitioners        | Primary   | Scenario presets anchored on realistic price paths (NDC-aligned, IEA NZE)             |
| Potential employers (ESG consult.) | Primary   | README + methodology.pdf + English blog serve as portfolio entry points               |
| Students / first-time ETS learners | Secondary | V1 is usable with default scenarios; dedicated `/learn` interactive page is V2        |

### 2.2 Portfolio framing

The project frames the author as **"translator between academic evidence and policy-grade tooling"**: a dissertation-derived β̂ coefficient is deployed inside a production-grade simulator with honest uncertainty. The README explicitly names this bridge and links to both the dissertation and the methodology PDF.

---

## 3. Scope & Non-Goals

### 3.1 V1 in-scope

- **Geography**: China only.
- **Policy phase**: National ETS (2021+), prospective (forward-looking).
- **Sector**: Thermal Power & Heat Supply (matches dissertation definition).
- **Time dimension**: Multi-year price path, 2021–2035.
- **Modelling form**: Reduced-form with partial-adjustment dynamics.
- **Uncertainty**: Monte Carlo (N = 10,000) over coefficient + BAU parameter distributions.
- **Coefficient sources**: Author's DID β̂ (default) + ≥ 2 literature alternates via dropdown.
- **Free allocation**: Single uniform slider 0–100%.
- **Outputs**: Annual CO₂ emissions (Mt), cumulative reduction vs BAU (%), peak year.
- **Scenario sharing**: JSON export/import + URL-encoded state (nuqs, lz-string compression).
- **Preset library**: 3–5 curated scenarios.

### 3.2 V1 explicitly NOT in scope (deferred to V2+)

- Multi-sector coverage (steel, cement, aluminum, chemicals, paper, aviation, non-ferrous).
- MAC-curve cross-check panel.
- Leakage / rebound effects advanced toggle.
- Electricity price pass-through module.
- `/learn` interactive tutorial page.
- Chinese UI language toggle.
- Marketing landing page (app opens directly on the calculator).
- User accounts, server-side scenario persistence, share-via-short-ID.
- Multi-country comparison (EU ETS, California, RGGI, etc.).
- GDP / employment / welfare outputs.
- Sectoral heterogeneity within power (e.g., coal vs gas split).
- Chinese-language blog post (V2; V1 ships English blog only).

### 3.3 Non-goals (never)

- Financial / trading recommendations.
- Claim of replacing IAM / CGE models.
- Legal / compliance advice on ETS participation.

---

## 4. Mathematical Model

### 4.1 Notation

| Symbol   | Meaning                                                            | V1 source / default                  |
| -------- | ------------------------------------------------------------------ | ------------------------------------ |
| `t`      | Year, 2021–2035                                                    | user-defined range                   |
| `P_t`    | Carbon price in year t (CNY/tCO₂)                                  | user input (path editor)             |
| `P_ref`  | Log-reference price = 45 CNY/tCO₂ (national ETS 2021 open)         | constant                             |
| `f`      | Free-allocation share, ∈ [0, 1]                                    | user slider, default 0.90            |
| `λ`      | Free-allocation dampening factor on behavioral response            | fixed at 0.3 in V1 (not in UI)       |
| `β̂`     | Price semi-elasticity of emissions (log-log)                       | default −0.2273 (author's DID)       |
| `σ_β`    | Standard error of β̂                                                | default 0.0793                       |
| `α`      | Partial-adjustment coefficient                                     | default 0.30; user slider 0.10–0.60  |
| `g`      | Real GDP growth (%/yr)                                             | default 4.5%; slider 2–6%            |
| `e`      | Energy-intensity improvement rate (%/yr)                           | default 2.0%; slider 0–3%            |
| `η`      | Power-sector electrification / decarb rate (%/yr)                  | default 0.5%; slider 0–2%            |
| `E_t`    | Power-sector CO₂ emissions (Mt)                                    | output                               |
| `E_2020` | Baseline reference (user-locked, from CEADs)                       | default 5,150 Mt (China power 2020)  |

**Note on free allocation**: In well-designed benchmark-based ETS, free allocation is a lump-sum transfer that does **not** alter the marginal carbon price firms face. It does, however, empirically dampen behavioral response via (i) weaker political pressure on long-position firms, (ii) incomplete price pass-through under regulated power tariffs, (iii) reduced investment urgency when compliance cost is low. V1 captures this as a single dampening factor `λ = 0.3` applied multiplicatively to the log-price response — **not** as a discount on the marginal price itself. This is documented in `methodology.pdf § Free-allocation treatment`.

### 4.2 Core equations

**Step 1 — BAU trajectory** (no-ETS counterfactual):
```
BAU_t = E_2020 × (1 + g − e − η)^(t − 2020),  for t ∈ {2021, …, 2035}
```

**Step 2 — short-run log response to carbon price**:
```
ρ_t = ln((P_t + ε) / P_ref)                          # log-price signal
         clamped:  ρ_t = max(ρ_t, 0)                 # no reverse-ETS effect when P_t ≤ P_ref
Δln(E_t)_short = β̂ × ρ_t × (1 − λ × f)
```
where:
- `P_ref = 45 CNY/tCO₂` is the national ETS 2021 opening clearing price, serving as the log anchor.
- `ε = 1 CNY/t` provides numerical stability when `P_t = 0` (BAU scenarios).
- `(1 − λ × f)` is the free-allocation dampening factor: at `f = 0` (full auctioning) firms see 100% of the log-price response; at `f = 1` (fully free) the response magnitude is reduced by `λ = 30%`.
- When `P_t ≤ P_ref`, the response is clamped to 0; this prevents the perverse "lower-than-reference price drives emissions up" artifact from β̂ < 0 combined with a negative log ratio.
- Exact calibration conventions are documented in `methodology.pdf § Calibration` and unit-tested in `backend/tests/test_reduced_form.py`.

**Step 3 — long-run adjustment** (Koyck / partial-adjustment), with explicit initial condition:
```
Δln(E_{2020}) = 0                                    # boundary: no ETS effect before national ETS launch
Δln(E_t) = α × Δln(E_t)_short + (1 − α) × Δln(E_{t−1}),  for t ≥ 2021
```

**Step 4 — policy-adjusted emissions**:
```
E_t = BAU_t × exp(Δln(E_t))
```

**Step 5 — derived metrics**:
- Cumulative reduction: `Σ(BAU_t − E_t)` over 2021–2035 (Mt CO₂).
- Relative reduction: `(E_t − BAU_t) / BAU_t` (unitless, shown as %).
- Peak year: `argmax_t(E_t)` over 2021–2035.

**Sanity-check illustrative calculation** (locked in `test_reduced_form.py::test_illustrative_calibration`):
Independent of preset paths; fixed inputs P = 100 CNY/tCO₂ constant, f = 0.90, λ = 0.3, α = 0.3, β̂ = −0.2273:
```
ρ         = ln(101 / 45)        = 0.808
dampener  = 1 − 0.3 × 0.90      = 0.73
Δln_short = −0.2273 × 0.808 × 0.73 = −0.134   # ≈ −13.4% short-run
```
After partial adjustment converges (~ Δln ≈ Δln_short since input is constant), `E_t ≈ 0.875 × BAU_t`, i.e. **~12.5% reduction vs BAU in the long run**. Non-zero, directionally correct, within plausibility. This replaces the v1.0 formulation which incorrectly clamped to 0 at realistic free-allocation defaults (headline bug fixed in v1.1).

### 4.3 Monte Carlo

- **Draws**: N = 10,000 per `/compute` call. Tunable down to 1,000 for "draft" preview. **`N = 0` disables MC and returns a single deterministic trajectory** (used by the determinism acceptance test, see §9 criterion 2).
- **Sampled parameters**:
  - `β ~ Normal(β̂, σ_β²)`, truncated to `β < 0` to preserve sign.
  - `α ~ Uniform(max(0.10, α_user − 0.10), min(0.60, α_user + 0.10))`, where `α_user` is the user-selected point (clips align with the §4.1 slider range).
  - `g, e, η ~ Uniform(point ± 0.5pp)` around user inputs, clipped to their respective slider ranges.
- **Correlations**: parameters treated as independent in V1 (acknowledged simplification; discussed in methodology.pdf § Limitations).
- **Output**: 5th / 25th / 50th / 75th / 95th percentile trajectories → Plotly fan chart.
- **Seed**: user-settable (default = 42) for reproducibility; URL-encoded for exact replication.
- **Server-side budget**: target p95 < 2.5 s for N = 10,000 over 15 years.

### 4.4 External validity caveat (REQUIRED disclosure)

The headline coefficient β̂ = −0.2273 is estimated from China's **pilot** ETS phase (2013–2020), matched-DID on 6 treated provinces, thermal-power sector only, with observed carbon prices mostly in the 20–80 CNY/tCO₂ range. Users should be aware of the following extrapolation risks, which are surfaced in-app via tooltips and formally documented in `methodology.pdf § Limitations`:

1. **Price-range extrapolation**: the DID training sample covers pilot prices mostly in the 20–80 CNY/tCO₂ band. The tool does not cap price input, but emits a caveat (`price_above_training_range`) and renders a visual warning band whenever **`P_t > 100 CNY/tCO₂`** (this threshold is pinned; see §9 criterion 3). Extrapolating response at P_t ≥ 500 CNY/tCO₂ (upper edge of IEA NZE-China scenarios) should be read as stylised sensitivity, not a forecast.
2. **Regime transfer**: the pilot phase differed from the national ETS in compliance stringency, benchmark design, and market liquidity. β̂ is treated as a **stylised parameter** rather than a validated national-ETS elasticity.
3. **Structural change**: China's power sector is mid-transition (renewables ramp, coal phase-down). β̂ assumes approximately stationary fuel mix; projections past ~2030 should be read as "policy exploration" rather than forecasts.
4. **Sectoral non-transfer**: β̂ applies only to thermal power. V2 expansion to steel/cement/etc. will require sector-specific coefficients and will be clearly flagged.

The `/compute` response includes a `caveats[]` array populated with any triggered conditions (e.g., "price exceeds training range") so the UI can render them contextually.

### 4.5 MAC curve (V2 only, documented for continuity)

V2 will add an independent abatement estimate based on a China-specific MAC curve (Tsinghua iGDP + CECC / NDRC data), displayed side-by-side with the reduced-form result as a cross-check. No V1 work on this module; V1 code must leave a clean interface (`/compute` returns a `method: "reduced_form"` field, enabling `method: "mac_curve"` later without API breakage).

---

## 5. Data & Coefficient Sources

### 5.1 Primary source (default coefficient)

- **Label**: `Author's DID estimate (Liu, 2026)`.
- **Value**: β̂ = −0.2273, SE = 0.0793, p = 0.006.
- **Scope**: China pilot ETS, thermal power, 2013–2020.
- **Reference**: Liu, H. (2026). *The Impacts of Carbon Emissions Trading on Decoupling in China's Provincial Power Sector*. BSc dissertation, University of Glasgow.

### 5.2 Literature alternates (V1 ≥ 2 entries)

All entries stored in `backend/data/references.db` with the following schema: `id | citation | region | sector | coefficient | std_err | method | notes | url`.

**V1 seed list (minimum 2 of these, target 3)**:

1. Green, J. F. (2021). Does carbon pricing reduce emissions? A review of ex-post analyses. *Environmental Research Letters*, 16(4).
2. Best, R., Burke, P. J., & Jotzo, F. (2020). Carbon pricing efficacy: Cross-country evidence. *Environmental and Resource Economics*, 77(1).
3. IPCC AR6 WGIII Ch.13 — Policies and Institutions (2022), summarised elasticity range.
4. (Optional) Cao, J. et al. (2021). China's 2020 carbon market: A literature review of price impacts.

Each reference's coefficient is recorded with its region / sector context; the UI renders a "scope warning" chip when the user applies a non-China coefficient to China (e.g., Green 2021 OECD average).

### 5.3 Baseline CO₂ (E_2020)

- China power-sector CO₂, 2020: ~5,150 Mt (from CEADs provincial inventory, row 53 "Thermal Power & Heat Supply", aggregated across all provinces; already processed in the dissertation repo).
- Stored as a versioned constant in `backend/data/coefficients.db`. User cannot edit in V1 (shown read-only with source tooltip).

### 5.4 Data provenance policy

Every numeric default surfaces its source in a tooltip (question-mark icon). The methodology PDF reproduces the full list with URLs. Any value the user cannot attribute to a citation is flagged as a design bug.

---

## 6. Architecture

### 6.1 Component topology

```
┌── Frontend (Vercel, static) ─────────────────────────────────┐
│  React 18 + TypeScript + Vite                                 │
│  react-plotly.js (Plotly.js bundle lazy-loaded)               │
│  Tailwind CSS + shadcn/ui                                     │
│  State: useState + nuqs (URL sync) + @tanstack/react-query    │
│  Export: JSON download (native Blob API)                      │
└──────────────────────────────────────────────────────────────┘
                          │
                          │  POST /api/compute  (JSON, ~2 KB req, ~200 KB resp)
                          │  GET  /api/references
                          │  GET  /api/scenarios
                          ▼
┌── Backend (Render Free, uvicorn) ────────────────────────────┐
│  FastAPI (Python 3.11, managed with uv)                       │
│  numpy for Monte Carlo sampling                               │
│  Pydantic v2 for request/response schemas                     │
│  SQLite (read-only, version-controlled in repo):              │
│    • coefficients.db  — default β̂ + alternates                │
│    • references.db    — citation metadata                     │
│    • scenarios.db     — curated preset library                │
│  No auth, no user data storage                                │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 API surface (V1)

| Method | Path             | Purpose                                                              |
| ------ | ---------------- | -------------------------------------------------------------------- |
| POST   | `/api/compute`   | Accept scenario JSON, return deterministic + MC fan-chart data       |
| GET    | `/api/scenarios` | List curated scenario presets                                        |
| GET    | `/api/references`| List literature coefficient alternates                               |
| GET    | `/api/health`    | Readiness probe (also used by Vercel to warm Render instance)        |

All endpoints documented via FastAPI's auto-generated OpenAPI at `/docs`.

### 6.3 Frontend / backend contract

Types are shared by generating TypeScript interfaces from the FastAPI OpenAPI schema at build time (`openapi-typescript`). The SPEC does not pin the exact build command; that belongs in the implementation plan.

### 6.4 Deployment specifics

- **Vercel**: single project, build command `npm run build`, output `frontend/dist`.
- **Render Free tier**:
  - Cold start up to 30 s after idle.
  - Mitigation: (a) README "first compute takes ~30 s" note; (b) frontend fires a warm-up `GET /api/health` on page mount so the click feels instant.
  - No disk persistence needed beyond the repo-bundled SQLite files.
- **No CI-deployed database**: SQLite ships in the container image, fully version-controlled.

### 6.5 Performance targets

- p95 `/compute` end-to-end (incl. network) < 4 s warm, < 35 s cold.
- Frontend first contentful paint < 1.5 s on fast 3G (Vercel edge).
- Plotly fan chart interaction < 16 ms per hover (60 fps).

### 6.6 Observability (V1)

- Backend: structured JSON logs via `logging`, no external APM in V1.
- Frontend: Vercel Analytics (default), no external error tracker in V1 (Sentry is V2).

---

## 7. UI / UX Design

### 7.1 Layout (single-page app, desktop-first; responsive is V2 polish)

```
┌──────────────────────────────────────────────────────────────┐
│ Header: logo · "Carbon Pricing Impact Calculator" · GitHub · │
│         Methodology PDF link                                 │
├──────────────┬───────────────────────────────────────────────┤
│ Left rail    │  Main canvas                                  │
│ (~320 px)    │                                               │
│              │  ┌── Scenario preset cards (3–5) ──────────┐ │
│ Inputs:      │  │ [Current policy] [NDC] [NZE] [BAU]      │ │
│ • Preset     │  └──────────────────────────────────────────┘ │
│   dropdown   │                                                │
│ • Price path │  ┌── Price path editor (drag-able line) ───┐ │
│   editor     │  │                                          │ │
│   button     │  └──────────────────────────────────────────┘ │
│ • Free alloc │                                                │
│   slider     │  ┌── Emissions fan chart (Plotly) ─────────┐ │
│ • β source   │  │  BAU line + median + 25/75 + 5/95 bands │ │
│   dropdown   │  │                                          │ │
│ • Advanced:  │  └──────────────────────────────────────────┘ │
│   α, g,e,η   │                                                │
│ • MC seed    │  ┌── Headline KPIs ────────────────────────┐ │
│              │  │ Cumulative reduction: 12.4 Gt [±3.1]    │ │
│ Actions:     │  │ Peak year (median): 2027 [2025–2029]    │ │
│ [Compute]    │  │ 2035 emissions: 3.8 Gt (−26% vs BAU)    │ │
│ [Export]     │  └──────────────────────────────────────────┘ │
│ [Import]     │                                                │
│ [Share URL]  │  ┌── Methodology accordion ────────────────┐ │
│              │  │ > Model equations                        │ │
│              │  │ > Coefficient provenance                 │ │
│              │  │ > External validity caveats              │ │
│              │  │ > Download methodology.pdf               │ │
│              │  └──────────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────────┘
```

### 7.2 Interaction contract

- **Compute is explicit** (button press), not live-updating. Rationale: MC is expensive, live re-compute on every slider move feels janky.
- **Price path editor**: line chart with 15 draggable points (2021–2035). Double-click a point opens a numeric input; "Shift+drag" applies a linear ramp across the range.
- **Share URL**: copies the current URL (with nuqs-encoded state) to clipboard, toast confirmation.
- **Export**: produces `scenario_<timestamp>.json` conforming to §8.2 schema.
- **Import**: JSON file picker; invalid files rejected with a diff-style error ("missing field: price_path").

### 7.3 Accessibility (V1 baseline)

- All inputs keyboard-navigable.
- Plotly configured with `aria-label` on the chart container.
- Color palette passes WCAG AA (fan bands use distinguishable luminance, not hue-only).
- No sound / flashing elements.

### 7.4 Empty / error states

- First visit (no scenario): default "Current policy" preset auto-selected.
- Compute error (backend down): toast "Server warming up, retrying in 10 s" with a single auto-retry.
- Invalid input (e.g., negative price): inline validation prevents submit; no server round trip.
- Cold start first load: skeleton chart + progress caption "Backend warming up — this only happens once per session".

---

## 8. Scenario Management

### 8.1 Curated presets (V1, shipped in `scenarios.db`)

| ID          | Name                    | Price path (CNY/t)              | Free alloc | Purpose                             |
| ----------- | ----------------------- | ------------------------------- | ---------- | ----------------------------------- |
| `current`   | Current policy (2024)   | 80 flat → 100 by 2035           | 0.90       | Baseline reality                    |
| `ndc`       | NDC-aligned             | 90 → 200 linear by 2035         | 0.80       | Plausible policy tightening         |
| `nze_china` | IEA NZE-China           | 100 → 500 convex by 2035        | 0.50       | 1.5°C-consistent aggressive path    |
| `bau`       | BAU (no ETS)            | 0 flat                          | 1.00       | Counterfactual reference            |
| `peak`      | Ambitious peak-2028     | 120 → 300 rapid ramp            | 0.70       | Story-driven "what if" scenario     |

Each preset includes a short (≤50-word) narrative description shown on card hover.

### 8.2 Scenario JSON schema v1

```json
{
  "schema_version": "1.0",
  "meta": {
    "name": "string, user-editable",
    "created_at": "ISO-8601",
    "notes": "string, optional"
  },
  "inputs": {
    "price_path": [{"year": 2021, "price_cny": 50}, ...],
    "free_allocation_share": 0.85,
    "coefficient_source": "author_did_2026",
    "alpha": 0.30,
    "gdp_growth": 0.045,
    "energy_intensity_improvement": 0.020,
    "electrification_rate": 0.005,
    "mc_n": 10000,
    "mc_seed": 42
  }
}
```

### 8.3 URL state (nuqs)

Same field set as §8.2 `inputs`, lz-string-compressed and base64-urlsafe-encoded into a single `?s=...` query param to avoid URL length limits.

---

## 9. V1 Acceptance Criteria

V1 ships when **all** of the following are demonstrably true:

1. **Functional** — a user can select any of the 5 presets, adjust all inputs, click Compute, and see a Plotly fan chart with 5 percentile bands plus headline KPIs in under 4 s (warm).
2. **Correctness / determinism** — with request payload `mc_n = 0` and all other inputs fixed, two successive `/compute` calls return identical output to 6 decimal places. This is the canonical determinism gate — it does **not** rely on the α slider reaching 1.0 (out of UI range) and does **not** require a seed because no sampling occurs.
3. **Uncertainty honesty** — the 5/95 fan band visually widens as price path moves farther from the training range; the `price_above_training_range` caveat chip appears **iff `max_t(P_t) > 100 CNY/tCO₂`**, the single pinned threshold shared with §4.4 caveat 1.
4. **Coefficient attribution** — every numeric input and output has a visible source label or tooltip.
5. **Share-ability** — JSON export/import round-trips losslessly; URL share restores exact state after page reload.
6. **Deployed** — live URL reachable at a Vercel domain, backed by a Render instance, with a working `/api/health` endpoint (pinged by the frontend on mount to pre-warm cold starts).
7. **Documented** — README with screenshots + live link; `docs/methodology.pdf` (LaTeX, ≥ 8 pages) covering §4 math, §5 sources, §4.4 caveats, and the free-allocation dampening rationale.
8. **Portfolio** — English blog post drafted (≥ 2,000 words) linking dissertation → tool → design decisions.
9. **Tested** — backend ≥ 80% line coverage on `compute/` modules; one golden-path integration test that POSTs the `current` preset and asserts (a) schema validity, (b) non-zero median reduction (guards against the v1.0 calibration bug), (c) `peak_year` ∈ {2021, …, 2035}.
10. **Reproducible** — `README.md` quickstart produces a running stack from a clean clone via the two documented commands: `cd backend && uv run uvicorn app.main:app --reload` and `cd frontend && npm install && npm run dev`. Docker orchestration is V2; V1 ships a `Dockerfile` in `backend/` for Render only.

---

## 10. V2 Roadmap (non-binding)

Ordered by estimated user value / effort ratio:

1. Multi-sector expansion: add steel, cement, aluminum (matches 2024 national ETS expansion).
2. MAC curve cross-check panel (Tsinghua iGDP data).
3. Leakage / rebound advanced toggle.
4. Electricity price pass-through module.
5. `/learn` interactive tutorial (5–7 scrollable cards with embedded mini-calculators).
6. Chinese UI toggle + Chinese blog post.
7. Scenario gallery page (10+ curated scenarios).
8. Multi-country comparison (EU ETS, California, RGGI).
9. User accounts + server-side scenario persistence.
10. Sector heterogeneity within power (coal vs gas split).

---

## 11. Delivery Artifacts

| Artifact                   | Format         | V1 | V2 | Notes                                           |
| -------------------------- | -------------- | -- | -- | ----------------------------------------------- |
| GitHub repository (MIT)    | public         | ✓  |    | README is the portfolio entry point             |
| Live demo                  | Vercel + Render| ✓  |    | Named in README                                 |
| Methodology technical report | PDF (LaTeX)    | ✓  |    | ~10 pages, English                              |
| English blog post          | Markdown       | ✓  |    | ~2,500 words; publishable on personal site / Medium |
| Chinese blog post          | Markdown       |    | ✓  | Targets 知乎 / 微信 audience                    |
| Chinese UI                 | i18n           |    | ✓  |                                                 |

---

## 12. Directory Structure

```
carbon-pricing-calculator/
├── README.md
├── SPEC.md                              # this file
├── LICENSE                              # MIT
├── .gitignore
├── docs/
│   ├── methodology.tex
│   ├── methodology.pdf                  # built artifact (tracked)
│   └── blog/
│       └── en.md                        # V1
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── vercel.json
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── PricePathEditor.tsx
│       │   ├── FanChart.tsx
│       │   ├── KPICards.tsx
│       │   ├── ScenarioCards.tsx
│       │   ├── AdvancedPanel.tsx
│       │   └── MethodologyAccordion.tsx
│       ├── hooks/
│       │   ├── useCompute.ts
│       │   └── useScenarioUrl.ts
│       ├── lib/
│       │   ├── api.ts                   # generated types consumer
│       │   ├── json-export.ts
│       │   └── url-state.ts
│       └── types/
│           └── api.ts                   # generated from openapi
├── backend/
│   ├── pyproject.toml                   # uv-managed
│   ├── uv.lock
│   ├── render.yaml
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI entry
│   │   ├── schemas.py                   # Pydantic models
│   │   ├── compute/
│   │   │   ├── __init__.py
│   │   │   ├── reduced_form.py
│   │   │   ├── monte_carlo.py
│   │   │   ├── bau.py
│   │   │   └── caveats.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── queries.py
│   │   └── data/
│   │       ├── coefficients.db
│   │       ├── references.db
│   │       └── scenarios.db
│   └── tests/
│       ├── test_reduced_form.py
│       ├── test_monte_carlo.py
│       ├── test_bau.py
│       ├── test_schemas.py
│       └── test_api_integration.py
└── .github/
    └── workflows/
        ├── ci.yml                       # lint + type + test
        └── deploy.yml                   # optional Render deploy hook
```

**File-size discipline** (per coding-style rule): every `.py` and `.tsx` file caps at ~300 lines; split further if exceeded. All packages expose explicit `__all__`.

---

## 13. Risks & Mitigations

| Risk                                                           | Likelihood | Impact | Mitigation                                                                                   |
| -------------------------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------------------- |
| Render Free cold start degrades first-impression UX            | High       | Medium | Warm-up ping on page load; visible "warming" UI state; README disclosure                     |
| Dissertation deadline (2026-04-17) conflicts with build time   | Known past | High   | Dissertation already submitted (2026-04-17); V1 start safe on/after 2026-04-21               |
| Monte Carlo p95 > 4 s hurts usability                          | Medium     | Medium | Default N = 10k but offer 1k "quick preview"; numpy vectorisation mandatory                  |
| Coefficient extrapolation produces implausible results         | High       | High   | Caveats array + visual warning band + methodology.pdf limitations section                    |
| Plotly bundle size tanks LCP                                   | Medium     | Low    | Code-split the chart panel; static HTML shows skeleton until user clicks Compute             |
| Scope creep (V2 features leaking into V1)                      | High       | High   | Any new feature request = V2 by default; SPEC revision required to move items into V1        |
| β̂ misinterpretation by users ("this is a forecast")           | High       | High   | Tool labelled "policy exploration" throughout; caveats prominent; methodology PDF linked     |
| SQLite commit bloat in repo                                    | Low        | Low    | DBs kept < 1 MB each; generated from `scripts/build_data.py` + source CSVs tracked           |

---

## 14. Timeline (part-time, ~4–5 weeks)

| Week | Milestone                                                                                           |
| ---- | ---------------------------------------------------------------------------------------------------- |
| 1    | Backend scaffold (uv, FastAPI, Pydantic schemas), reduced-form + BAU modules, unit tests             |
| 2    | Monte Carlo + caveats + SQLite data layer; `/compute` endpoint hits acceptance 4-sec warm budget     |
| 3    | Frontend scaffold (Vite + React + Tailwind); price path editor; fan chart; scenario presets         |
| 4    | URL state + JSON export/import; methodology accordion; integration testing; Vercel + Render deploy   |
| 5    | methodology.pdf (LaTeX); English blog post; README polish; end-to-end QA + portfolio screenshots     |

Buffer: no explicit buffer week — slippage absorbed by cutting the blog post to an outline and shipping it post-V1 if needed.

---

## 15. Open Questions (resolved 2026-04-20)

| Question                                                             | Resolution                                         |
| -------------------------------------------------------------------- | -------------------------------------------------- |
| Chinese UI toggle in V1?                                             | No, V2                                             |
| Marketing landing page in V1?                                        | No, app opens directly on calculator               |
| Repository location?                                                 | `my-project/carbon-pricing-calculator/` subdir     |
| Chinese blog post in V1?                                             | V2 (V1 ships English blog only)                    |
| Any decision that conflicts with this spec?                          | Revise SPEC + bump version                         |

---

## 16. Approval

Design reviewed and approved on 2026-04-20 through structured brainstorming with the user. Any subsequent change triggers a SPEC revision (v1.x) — minor clarifications as 1.1, scope changes as 2.0.

**Next step**: create the implementation plan via `superpowers:writing-plans`.
