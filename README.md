<div align="center">

<img src="docs/logo.png" alt="Artha AI" width="110" height="110" />

# Artha AI — Investment Intelligence Platform

**AI-powered market insights, investment valuation, data-quality pipelines and platform monitoring — in one institutional-grade dashboard.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248?logo=mongodb&logoColor=white)
![Claude](https://img.shields.io/badge/AI-Anthropic%20Claude-D97757)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-black)

</div>

---

## Overview

**Artha** (Sanskrit: *wealth, purpose*) is a full-stack prototype of the internal platform a
modern investment team relies on. It unifies five capabilities a portfolio manager and a
data-engineering team care about:

| Module | What it does |
|---|---|
| 📊 **Portfolio Management** | Live holdings valuation, sector allocation, P&L, performance vs benchmark |
| 🧠 **AI Investment Valuation** | On-demand fair-value checks + research thesis (Buy / Hold / Sell, bull & bear, risks) with **PDF export** |
| 📰 **Market Intelligence** | Quantitative market-breadth dashboard + AI-written research-desk brief (PDF export) |
| 🔧 **Data Quality & Pipelines** | Ingestion pipelines running a **real automated-validation engine** on the live feed |
| 📡 **Platform Reliability** | Service health, latency, throughput and a live log stream |

## ✨ Highlights for reviewers

- **Real data-quality validation** — not mocked. `validation.py` runs schema, completeness,
  freshness-SLA, outlier-bounds, row-count-drift and duplicate checks against the live quote
  feed, and is fully covered by unit tests (`pytest`, green in CI).
- **Live market data with a provider abstraction** — a single `MarketDataProvider` interface
  means the source is swappable. A documented `BloombergProvider` stub shows exactly where a
  licensed Terminal / B-PIPE (`blpapi`) feed plugs in — nothing downstream changes.
- **AI that degrades gracefully** — uses the official **Anthropic Claude** SDK when a key is
  present, and a transparent deterministic quant model otherwise, so a fresh clone runs with
  zero configuration. Every response reports which `engine` produced it.
- **Ships like a real service** — Dockerfiles, `docker-compose`, GitHub Actions CI, tests and
  an MIT license.

## 🏗 Architecture

```
┌──────────────────────┐        REST /api        ┌──────────────────────────┐
│   React Frontend      │  ───────────────────▶   │   FastAPI Backend          │
│   dashboards · charts │                          │   server.py     (routes)   │
│   recharts · framer   │  ◀───────────────────   │   ai_engine.py  (Claude)   │
└──────────────────────┘        JSON              │   market_data.py (orchestr)│
                                                    │   providers.py  (feeds)   │
                                                    │   validation.py (quality) │
                                                    │   pdf_export.py (reports) │
                                                    └───────────┬───────────────┘
                                   ┌───────────────────────────┼───────────────────────────┐
                           ┌───────▼──────┐          ┌──────────▼───────┐        ┌──────────▼───────┐
                           │ Yahoo Finance │          │     MongoDB       │        │  Anthropic Claude │
                           │ (live quotes) │          │ valuations, runs  │        │   (AI analysis)   │
                           └──────────────┘          └──────────────────┘        └──────────────────┘
```

## 🧰 Tech stack

- **Backend:** FastAPI · Motor (async MongoDB) · Pydantic · `requests`/`yfinance` · ReportLab · Python 3.11
- **AI:** Anthropic Claude (official SDK) with a deterministic quant fallback
- **Frontend:** React 19 · TanStack Query · Recharts · Framer Motion · Tailwind CSS
- **Quality:** `pytest` unit tests · GitHub Actions CI
- **Ops:** Docker · docker-compose

## 🔌 Key API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/api/market/securities` | Security universe with live quotes + feed status |
| `GET`  | `/api/portfolio` | Holdings, allocation, P&L and performance series |
| `POST` | `/api/valuation` | AI fair-value check (rating, thesis, bull/bear, risks) |
| `GET`  | `/api/valuation/{id}/pdf` | Download a valuation as a branded PDF |
| `GET`  | `/api/market/insights` | Market breadth + AI research-desk brief |
| `GET`  | `/api/market/insights/pdf` | Download the market brief as a PDF |
| `GET`  | `/api/pipelines` · `POST /api/pipelines/run` | Pipeline inventory + run data-quality checks |
| `GET`  | `/api/monitoring` | Service health, latency, throughput, logs |

## ✅ Automated data-quality checks

Each ingestion run validates the live feed and reports every check as `pass` / `warn` / `fail`:

| Check | Rule |
|---|---|
| Schema & type | every record carries the required fields |
| Null / completeness | required price fields populated (→ completeness %) |
| Freshness SLA | data arrived within 15 min |
| Range / outlier bounds | prices positive and within statistical bounds |
| Row-count drift | ingested rows vs expected |
| Duplicate keys | no double-ingested records |

All rules live in `backend/validation.py` and are covered by `backend/tests/test_validation.py`.

## 🚀 Running locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env            # ANTHROPIC_API_KEY optional
uvicorn server:app --host 0.0.0.0 --port 8001
```

**Frontend**
```bash
cd frontend
yarn install
cp .env.example .env            # REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```

**Docker (everything at once)**
```bash
docker compose up --build       # frontend :3000 · backend :8001 · mongo :27017
```

## 🧪 Tests

```bash
cd backend
pytest -q
```

## 📁 Project structure

```
backend/
  server.py          FastAPI routes
  market_data.py     orchestrates providers → portfolio / pipelines / monitoring
  providers.py       Yahoo (live) · Simulated (fallback) · Bloomberg (stub)
  validation.py      automated data-quality engine
  ai_engine.py       Anthropic Claude + deterministic fallback
  pdf_export.py      branded PDF reports (ReportLab)
  tests/             pytest suite
frontend/
  src/views/         Portfolio · Valuation · Insights · Pipelines · Monitoring
  src/components/     Header, UI kit
.github/workflows/   CI
docker-compose.yml
```

---

<div align="center">
<sub>A portfolio project exploring how AI and data engineering support real investment decisions.</sub>
</div>
