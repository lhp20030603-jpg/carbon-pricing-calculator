# Carbon Pricing Policy Impact Calculator

## 项目概述
碳定价政策效果计算器。用户输入政策参数，工具估算对排放、电价、GDP 的边际影响。
面向政策研究者和学生。

## 技术栈
- 前端：React + TypeScript + Vite + **Plotly.js (react-plotly.js)**（图表）+ Tailwind CSS + shadcn/ui；状态 useState + nuqs + @tanstack/react-query
- 后端：Python 3.11 + FastAPI + Pydantic v2 + numpy；包管理用 **uv**（`pyproject.toml` + `uv.lock`），不用 `requirements.txt`
- 存储：SQLite 只读（系数/文献/预设场景），随仓库版本控制；无用户数据持久化
- 部署：Vercel（前端）+ Render Free（后端，有 30s 冷启动，前端 mount 时 ping `/api/health` 预热）

> **SPEC.md v1.1 是 source of truth**。此处任何一项与 SPEC 冲突以 SPEC 为准；技术栈选型依据见采访记录（R3 选 Plotly.js 是为了 fan chart / MAC / 敏感性分析）。

## 项目结构

完整目录树见 `SPEC.md §12`，此处只摘要关键约束：

```
carbon-pricing-calculator/
├── frontend/             # React + Vite (Vercel)
│   ├── src/
│   │   ├── components/   # UI 组件（PricePathEditor, FanChart, KPICards, ...）
│   │   ├── hooks/        # useCompute, useScenarioUrl
│   │   ├── lib/          # api.ts, json-export.ts, url-state.ts
│   │   └── types/        # 从后端 OpenAPI 生成
│   └── package.json
├── backend/              # FastAPI + uv (Render)
│   ├── app/
│   │   ├── main.py       # FastAPI entry
│   │   ├── schemas.py    # Pydantic v2
│   │   ├── compute/      # reduced_form.py, monte_carlo.py, bau.py, caveats.py
│   │   ├── db/           # queries.py（SQLite 读）
│   │   └── data/         # coefficients.db, references.db, scenarios.db
│   ├── tests/
│   ├── pyproject.toml    # uv 管理（非 requirements.txt）
│   ├── uv.lock
│   ├── Dockerfile        # Render 用
│   └── render.yaml
├── docs/
│   ├── methodology.tex / methodology.pdf
│   └── blog/en.md        # V1 英文博客
├── SPEC.md               # 产品规格 v1.1（source of truth）
├── CLAUDE.md             # 本文件（Claude Code 工作指令）
└── README.md
```

注意：没有 `models/` 或 `routers/` 子目录 —— SPEC §12 的模块边界是 `compute/` + `db/`；REST 路径集中在 `main.py`（`/compute` `/scenarios` `/references` `/health`），目前规模不需要单独 routers 层。

## 开发规范
- Python：PEP 8；全函数类型标注；docstrings；`ruff check` + `ruff format`（不用 black）；`mypy` 过关
- TypeScript：strict mode；named exports；类型从后端 OpenAPI 生成，不手写重复
- 所有计算逻辑在后端，前端只做展示与交互
- API：REST + JSON；前端用 `@tanstack/react-query` 包装 fetch，启用缓存 + 重试
- 每个模块写完跑一遍测试再继续；backend `compute/` 目录 V1 覆盖率目标 ≥ 80%
- commit message：Conventional Commits，英文，格式 `type(scope): description`（type ∈ feat/fix/docs/refactor/test/chore/perf/style）
- 文件大小纪律：`.py` / `.tsx` 上限约 300 行，超了就拆（SPEC §12 + 全局 coding-style rule）

## 常用命令
- 后端启动：`cd backend && uv run uvicorn app.main:app --reload`
- 前端启动：`cd frontend && npm install && npm run dev`
- 后端测试：`cd backend && uv run pytest`
- 后端类型检查：`cd backend && uv run mypy app`
- 后端格式化/lint：`cd backend && uv run ruff check . && uv run ruff format .`
- 前端 lint：`cd frontend && npm run lint`
- 前端类型：`cd frontend && npm run typecheck`
- OpenAPI → TS 类型重新生成：`cd frontend && npm run gen:types`（依赖后端已启动）

SPEC §9 criterion 10 明确 V1 不做 `docker compose up` 单命令启动；Docker 仅 `backend/Dockerfile` 供 Render 使用。

## 注意事项
- **SPEC.md v1.1 是 V1 scope 的冻结 source of truth**。改动若触及 scope / API 契约 / 数学模型，必须先 bump SPEC 版本再改代码。
- **模型校准锁点**（回归测试必测，防止 v1.0 的零减排 bug 回来）：
  - `P_ref = 45 CNY/tCO₂`，`λ = 0.3`，`ε = 1 CNY/t`
  - 免费配额 `f` 作用于响应幅度 `(1 − λ × f)`，**不是** 边际碳价折扣（旧写法 `EC = P × (1−f)` 是错的）
  - 初始条件：`Δln(E_{2020}) = 0`
  - `P_t ≤ P_ref` 时 ρ_t 钳位为 0（防反向 ETS 伪效应）
  - 默认 preset `current` (P 80→100, f=0.90) 跑出来 median reduction 必须非零
- 弹性系数和参数来源必须在代码注释中标注文献出处；backend 系数同时存入 `references.db` 并附 region/sector scope 字段。
- 所有数值计算需要 sanity check：碳价 0 或 P ≤ P_ref 时减排为 0；极端值（P_t > 1000 CNY/t）不应产生 E_t < 0 或 E_t > BAU_t。
- 前端 V1 是 **desktop-first**（≥ 1280px 优化），手机/平板 responsive 是 V2；移动端 V1 只保证"能看能读"，不保证交互完整（price path drag 在触屏会挂）。
- README 要写清楚：项目是什么、怎么用、模型假设和 §4.4 external validity caveats、引用作者论文。
- Caveat ID `price_above_training_range` 阈值钉死 **100 CNY/tCO₂**（SPEC §4.4 + §9 criterion 3 同字段），任何地方改值都要两处同步改 + 回归测试。
