"""Investment-platform data layer.

Orchestrates a live market-data provider (with a resilient simulated fallback)
and derives the portfolio, data-pipeline and monitoring datasets consumed by
the API. The active provider is swappable — see `providers.py`.
"""
import random
from datetime import datetime, timezone, timedelta

from providers import YahooFinanceProvider, SimulatedProvider
import validation

# ---------------------------------------------------------------------------
# Reference universe. `yahoo` maps our Bloomberg-style ticker to a live symbol;
# `base` and the fundamentals seed the simulated fallback and valuation inputs.
# ---------------------------------------------------------------------------
SECURITIES = [
    {"ticker": "NESN:SW", "yahoo": "NESN.SW", "name": "Nestlé S.A.", "exchange": "SIX", "sector": "Consumer Staples", "currency": "CHF", "base": 104.20, "eps": 4.85, "pe": 21.5, "pb": 6.1, "divYield": 2.9, "marketCap": 268e9, "beta": 0.42},
    {"ticker": "ROG:SW", "yahoo": "ROG.SW", "name": "Roche Holding AG", "exchange": "SIX", "sector": "Health Care", "currency": "CHF", "base": 248.60, "eps": 18.6, "pe": 13.4, "pb": 4.8, "divYield": 3.8, "marketCap": 205e9, "beta": 0.38},
    {"ticker": "NOVN:SW", "yahoo": "NOVN.SW", "name": "Novartis AG", "exchange": "SIX", "sector": "Health Care", "currency": "CHF", "base": 92.15, "eps": 6.2, "pe": 14.9, "pb": 3.5, "divYield": 3.4, "marketCap": 190e9, "beta": 0.45},
    {"ticker": "UBSG:SW", "yahoo": "UBSG.SW", "name": "UBS Group AG", "exchange": "SIX", "sector": "Financials", "currency": "CHF", "base": 27.84, "eps": 2.1, "pe": 13.3, "pb": 1.1, "divYield": 2.2, "marketCap": 94e9, "beta": 1.05},
    {"ticker": "CFR:SW", "yahoo": "CFR.SW", "name": "Compagnie Financière Richemont", "exchange": "SIX", "sector": "Consumer Discretionary", "currency": "CHF", "base": 138.95, "eps": 7.4, "pe": 18.8, "pb": 2.9, "divYield": 2.1, "marketCap": 79e9, "beta": 0.98},
    {"ticker": "ABBN:SW", "yahoo": "ABBN.SW", "name": "ABB Ltd", "exchange": "SIX", "sector": "Industrials", "currency": "CHF", "base": 51.30, "eps": 1.9, "pe": 27.0, "pb": 5.2, "divYield": 1.8, "marketCap": 94e9, "beta": 1.12},
    {"ticker": "ZURN:SW", "yahoo": "ZURN.SW", "name": "Zurich Insurance Group", "exchange": "SIX", "sector": "Financials", "currency": "CHF", "base": 512.40, "eps": 35.8, "pe": 14.3, "pb": 2.4, "divYield": 4.6, "marketCap": 74e9, "beta": 0.72},
    {"ticker": "MC:FP", "yahoo": "MC.PA", "name": "LVMH Moët Hennessy", "exchange": "EN Paris", "sector": "Consumer Discretionary", "currency": "EUR", "base": 668.80, "eps": 30.4, "pe": 22.0, "pb": 4.9, "divYield": 1.9, "marketCap": 334e9, "beta": 1.08},
    {"ticker": "ASML:NA", "yahoo": "ASML.AS", "name": "ASML Holding N.V.", "exchange": "EN Amsterdam", "sector": "Technology", "currency": "EUR", "base": 712.50, "eps": 20.6, "pe": 34.6, "pb": 19.4, "divYield": 1.0, "marketCap": 285e9, "beta": 1.34},
    {"ticker": "AAPL:US", "yahoo": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology", "currency": "USD", "base": 228.40, "eps": 6.9, "pe": 33.1, "pb": 51.2, "divYield": 0.5, "marketCap": 3470e9, "beta": 1.21},
    {"ticker": "MSFT:US", "yahoo": "MSFT", "name": "Microsoft Corp.", "exchange": "NASDAQ", "sector": "Technology", "currency": "USD", "base": 418.90, "eps": 11.8, "pe": 35.5, "pb": 12.1, "divYield": 0.7, "marketCap": 3115e9, "beta": 0.93},
    {"ticker": "NVDA:US", "yahoo": "NVDA", "name": "NVIDIA Corp.", "exchange": "NASDAQ", "sector": "Technology", "currency": "USD", "base": 134.20, "eps": 2.9, "pe": 46.3, "pb": 48.7, "divYield": 0.02, "marketCap": 3290e9, "beta": 1.67},
    {"ticker": "BRK/B:US", "yahoo": "BRK-B", "name": "Berkshire Hathaway B", "exchange": "NYSE", "sector": "Financials", "currency": "USD", "base": 456.10, "eps": 25.1, "pe": 18.2, "pb": 1.6, "divYield": 0.0, "marketCap": 985e9, "beta": 0.87},
    {"ticker": "XAU:CUR", "yahoo": "GC=F", "name": "Gold Spot / USD oz", "exchange": "COMEX", "sector": "Commodities", "currency": "USD", "base": 2648.00, "eps": 0.0, "pe": 0.0, "pb": 0.0, "divYield": 0.0, "marketCap": 0.0, "beta": 0.11},
]

_REF = {s["ticker"]: s for s in SECURITIES}

LIVE = YahooFinanceProvider()
SIM = SimulatedProvider(SECURITIES)

_last_source_map: dict[str, str] = {}


def _merge(sec, quote, source):
    change = round(quote["price"] - quote["prevClose"], 2)
    change_pct = round((change / quote["prevClose"]) * 100, 2) if quote["prevClose"] else 0.0
    return {
        "ticker": sec["ticker"],
        "name": sec["name"],
        "exchange": sec["exchange"],
        "sector": sec["sector"],
        "currency": quote.get("currency", sec["currency"]),
        "price": quote["price"],
        "prevClose": quote["prevClose"],
        "change": change,
        "changePct": change_pct,
        "dayHigh": quote["dayHigh"],
        "dayLow": quote["dayLow"],
        "high52": quote["high52"],
        "low52": quote["low52"],
        "volume": quote["volume"],
        "eps": sec["eps"],
        "pe": sec["pe"],
        "pb": sec["pb"],
        "divYield": sec["divYield"],
        "marketCap": sec["marketCap"],
        "beta": sec["beta"],
        "source": source,
    }


def get_universe():
    """Live quotes where available, simulated fallback otherwise."""
    live = LIVE.get_quotes(SECURITIES)
    sim = SIM.get_quotes(SECURITIES)
    out = []
    _last_source_map.clear()
    for s in SECURITIES:
        if s["ticker"] in live:
            q, src = live[s["ticker"]], "live"
        else:
            q, src = sim[s["ticker"]], "simulated"
        _last_source_map[s["ticker"]] = src
        out.append(_merge(s, q, src))
    return out


def get_security(ticker):
    for s in get_universe():
        if s["ticker"].lower() == ticker.lower():
            return s
    return None


def feed_status():
    uni = get_universe()
    live_count = len([s for s in uni if s["source"] == "live"])
    is_live = live_count > 0
    return {
        "source": LIVE.name if is_live else SIM.name,
        "connected": True,
        "live": is_live,
        "liveCount": live_count,
        "total": len(uni),
        "lastTick": datetime.now(timezone.utc).isoformat(),
        "securitiesTracked": len(SECURITIES),
        "latencyMs": LIVE.last_latency_ms if is_live else round(random.uniform(8, 24), 1),
    }


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------
HOLDINGS = [
    {"ticker": "NESN:SW", "quantity": 4200, "costBasis": 92.40},
    {"ticker": "ROG:SW", "quantity": 1500, "costBasis": 231.80},
    {"ticker": "NOVN:SW", "quantity": 3100, "costBasis": 84.10},
    {"ticker": "UBSG:SW", "quantity": 18000, "costBasis": 22.65},
    {"ticker": "CFR:SW", "quantity": 2600, "costBasis": 121.30},
    {"ticker": "MC:FP", "quantity": 520, "costBasis": 712.00},
    {"ticker": "ASML:NA", "quantity": 340, "costBasis": 598.40},
    {"ticker": "MSFT:US", "quantity": 1900, "costBasis": 342.70},
    {"ticker": "NVDA:US", "quantity": 6400, "costBasis": 88.20},
    {"ticker": "XAU:CUR", "quantity": 850, "costBasis": 2310.00},
]


def get_portfolio():
    universe = {s["ticker"]: s for s in get_universe()}
    positions, total_value, total_cost, day_pnl = [], 0.0, 0.0, 0.0
    sector_alloc = {}
    for h in HOLDINGS:
        snap = universe.get(h["ticker"])
        if not snap:
            continue
        mkt_value = snap["price"] * h["quantity"]
        cost_value = h["costBasis"] * h["quantity"]
        pnl = mkt_value - cost_value
        day_pnl += snap["change"] * h["quantity"]
        total_value += mkt_value
        total_cost += cost_value
        sector_alloc[snap["sector"]] = sector_alloc.get(snap["sector"], 0) + mkt_value
        positions.append({
            "ticker": snap["ticker"], "name": snap["name"], "sector": snap["sector"],
            "currency": snap["currency"], "quantity": h["quantity"], "costBasis": h["costBasis"],
            "price": snap["price"], "changePct": snap["changePct"],
            "marketValue": round(mkt_value, 2), "pnl": round(pnl, 2),
            "pnlPct": round((pnl / cost_value) * 100, 2) if cost_value else 0,
        })
    positions.sort(key=lambda p: p["marketValue"], reverse=True)
    for p in positions:
        p["weight"] = round((p["marketValue"] / total_value) * 100, 2) if total_value else 0
    allocation = [
        {"sector": k, "value": round(v, 2), "weight": round((v / total_value) * 100, 2)}
        for k, v in sorted(sector_alloc.items(), key=lambda x: -x[1])
    ]
    total_pnl = total_value - total_cost
    return {
        "mandate": "ĀRYA Global Balanced — Discretionary CHF",
        "baseCurrency": "CHF",
        "totalValue": round(total_value, 2),
        "totalCost": round(total_cost, 2),
        "totalPnl": round(total_pnl, 2),
        "totalPnlPct": round((total_pnl / total_cost) * 100, 2) if total_cost else 0,
        "dayPnl": round(day_pnl, 2),
        "dayPnlPct": round((day_pnl / total_value) * 100, 2) if total_value else 0,
        "positions": positions,
        "allocation": allocation,
        "performance": _performance_series(),
    }


def _performance_series():
    r = random.Random(7)
    days, port, bench, out = 180, 100.0, 100.0, []
    start = datetime.now(timezone.utc) - timedelta(days=days)
    for i in range(days + 1):
        port *= (1 + r.gauss(0.0006, 0.0075))
        bench *= (1 + r.gauss(0.0004, 0.0068))
        if i % 3 == 0 or i == days:
            out.append({
                "date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                "portfolio": round(port, 2), "benchmark": round(bench, 2),
            })
    return out


# ---------------------------------------------------------------------------
# Market movers / breadth
# ---------------------------------------------------------------------------
def get_movers():
    uni = get_universe()
    ranked = sorted(uni, key=lambda s: s["changePct"], reverse=True)
    advancers = len([s for s in uni if s["changePct"] > 0])
    decliners = len([s for s in uni if s["changePct"] < 0])
    breadth = round((advancers / len(uni)) * 100, 1) if uni else 0
    sentiment = "Risk-On" if breadth >= 60 else "Risk-Off" if breadth <= 40 else "Neutral"
    return {
        "gainers": ranked[:5], "losers": ranked[-5:][::-1],
        "advancers": advancers, "decliners": decliners,
        "breadth": breadth, "sentiment": sentiment,
    }


# ---------------------------------------------------------------------------
# Data pipelines + automated validation
# ---------------------------------------------------------------------------
PIPELINES = [
    {"id": "equity-eod", "name": "Equity EOD Prices", "schedule": "0 18 * * 1-5", "owner": "data-eng"},
    {"id": "fx-intraday", "name": "FX & Rates Intraday Tick", "schedule": "*/5 * * * *", "owner": "data-eng"},
    {"id": "fundamentals-sync", "name": "Fundamentals & Ratios Sync", "schedule": "0 2 * * *", "owner": "data-eng"},
    {"id": "corp-actions", "name": "Corporate Actions Reconciliation", "schedule": "0 6 * * *", "owner": "ops"},
    {"id": "private-mkt-nav", "name": "Private Markets NAV Ingestion", "schedule": "0 4 1 * *", "owner": "pm-team"},
]

CHECK_NAMES = [
    ("schema_valid", "Schema & type validation"),
    ("not_null", "Null / completeness check"),
    ("freshness", "Freshness SLA (< 15 min)"),
    ("range_bounds", "Price range / outlier bounds"),
    ("row_count", "Row-count drift vs 30d avg"),
    ("duplicates", "Duplicate key detection"),
]


LIVE_PIPELINE_IDS = {"equity-eod", "fx-intraday", "fundamentals-sync"}


def _assemble(p, check_dicts, live, rows_processed):
    failed = len([c for c in check_dicts if c["status"] == "fail"])
    warned = len([c for c in check_dicts if c["status"] == "warn"])
    passed = len([c for c in check_dicts if c["status"] == "pass"])
    status = "failed" if failed else ("degraded" if warned else "healthy")
    completeness = next((c["metric"] for c in check_dicts
                         if c["key"] == "not_null" and c["metric"] is not None), 100.0)
    fresh = next((c["metric"] for c in check_dicts if c["key"] == "freshness"), 1)
    return {
        **p, "live": live, "status": status, "checks": check_dicts,
        "passed": passed, "warned": warned, "failed": failed,
        "rowsProcessed": rows_processed,
        "completeness": round(completeness, 2),
        "freshnessMin": int(fresh) if fresh is not None else 1,
        "durationMs": random.randint(820, 7400),
        "lastRun": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 20))).isoformat(),
    }


def _simulated_checks(p, force_issue):
    r = random.Random(hash(p["id"]) & 0xFFFF)
    checks = []
    for key, label in CHECK_NAMES:
        roll = random.random()
        if force_issue and key in ("freshness", "range_bounds"):
            status = "fail"
        elif roll < 0.06:
            status = "fail"
        elif roll < 0.16:
            status = "warn"
        else:
            status = "pass"
        checks.append({"key": key, "label": label, "status": status,
                       "detail": "representative sample (no live source)", "metric": None,
                       "rows": int(r.uniform(1.2, 48.0) * 1000) + random.randint(0, 500)})
    return checks


def get_pipelines(force_issue=False):
    """Run data-quality validation. Market-data-backed pipelines validate the
    live quote feed with the real `validation` engine; others run representative
    checks. `force_issue` injects a corrupted batch to demo an incident."""
    records = get_universe()
    age_min = round(LIVE.age_seconds() / 60.0, 1)
    results = []
    for p in PIPELINES:
        if p["id"] in LIVE_PIPELINE_IDS:
            recs, fmin = records, age_min
            if force_issue:
                recs = [dict(x) for x in records]
                recs[0] = {**recs[0], "price": -1, "prevClose": None}
                fmin = 32.0
            res = validation.run_all(recs, expected_rows=len(SECURITIES), freshness_min=fmin)
            results.append(_assemble(p, [c.as_dict() for c in res], live=True, rows_processed=len(recs)))
        else:
            checks = _simulated_checks(p, force_issue)
            results.append(_assemble(p, checks, live=False, rows_processed=sum(c["rows"] for c in checks)))
    total_checks = sum(len(p["checks"]) for p in results)
    total_pass = sum(p["passed"] for p in results)
    return {
        "pipelines": results,
        "summary": {
            "total": len(results),
            "healthy": len([p for p in results if p["status"] == "healthy"]),
            "degraded": len([p for p in results if p["status"] == "degraded"]),
            "failed": len([p for p in results if p["status"] == "failed"]),
            "checksPassRate": round((total_pass / total_checks) * 100, 1) if total_checks else 100,
            "rowsToday": sum(p["rowsProcessed"] for p in results),
        },
    }


# ---------------------------------------------------------------------------
# Platform monitoring / reliability
# ---------------------------------------------------------------------------
SERVICES = [
    {"name": "API Gateway", "component": "FastAPI"},
    {"name": "Market Data Feed", "component": "Yahoo Finance Adapter"},
    {"name": "AI Valuation Engine", "component": "Anthropic Claude"},
    {"name": "MongoDB Cluster", "component": "Primary"},
    {"name": "Pipeline Scheduler", "component": "Cron / Airflow"},
    {"name": "Private Markets Store", "component": "TimescaleDB"},
]


def get_monitoring():
    services = []
    for s in SERVICES:
        roll = random.random()
        status = "operational" if roll > 0.08 else ("degraded" if roll > 0.03 else "down")
        services.append({**s, "status": status,
                         "uptime": round(random.uniform(99.82, 99.999), 3),
                         "latencyMs": round(random.uniform(12, 180), 1),
                         "errorRate": round(random.uniform(0.0, 0.9), 3)})
    return {
        "services": services,
        "latencySeries": [{"t": i, "ms": round(random.uniform(30, 120), 1)} for i in range(30)],
        "requestsPerMin": random.randint(1800, 4200),
        "p95LatencyMs": round(random.uniform(90, 160), 1),
        "activeSessions": random.randint(18, 64),
        "logs": _logs(),
    }


def _logs():
    samples = [
        ("INFO", "equity-eod", "Ingested 12,842 rows, validation passed"),
        ("INFO", "ai-valuation", "Valuation generated for NVDA:US in 2.1s"),
        ("WARN", "fx-intraday", "Freshness SLA at 13m, threshold 15m"),
        ("INFO", "api-gateway", "GET /api/portfolio 200 in 41ms"),
        ("ERROR", "corp-actions", "Reconciliation mismatch on CFR:SW dividend — queued retry"),
        ("INFO", "pipeline-scheduler", "Triggered fundamentals-sync (cron 0 2 * * *)"),
        ("WARN", "mongodb", "Replication lag 220ms on secondary"),
        ("INFO", "market-data", "Yahoo feed heartbeat OK"),
    ]
    now = datetime.now(timezone.utc)
    return [{"ts": (now - timedelta(seconds=i * 37)).isoformat(), "level": lvl,
             "service": svc, "message": msg} for i, (lvl, svc, msg) in enumerate(samples)]
