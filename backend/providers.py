"""Market-data provider abstraction.

The platform talks to a single `MarketDataProvider` interface, so the data
source can be swapped without touching the API or AI layers. Three providers
are shipped:

  * YahooFinanceProvider  – live public quotes (no API key required)
  * SimulatedProvider     – deterministic random-walk fallback
  * BloombergProvider     – documented stub showing where a Terminal / B-PIPE
                            (blpapi) integration would plug in

In production a bank would register `BloombergProvider`; everything downstream
stays identical.
"""
from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


class MarketDataProvider(ABC):
    """Common contract every data source must implement."""

    name: str = "abstract"

    @abstractmethod
    def get_quotes(self, reference: list[dict]) -> dict[str, dict]:
        """Return {internal_ticker: quote_dict} for the securities we can price.

        A quote_dict contains: price, prevClose, dayHigh, dayLow, high52,
        low52, volume, currency. Securities that cannot be priced are simply
        omitted so the caller can fall back to another provider.
        """
        raise NotImplementedError


class YahooFinanceProvider(MarketDataProvider):
    """Live quotes via Yahoo Finance's public chart endpoint.

    Results are cached for a short TTL to keep the UI responsive and avoid
    hammering the upstream service.
    """

    name = "Yahoo Finance (live)"
    _CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"

    def __init__(self, ttl_seconds: int = 20, timeout: float = 6.0):
        self.ttl = ttl_seconds
        self.timeout = timeout
        self._cache: dict[str, dict] = {}
        self._cache_ts: float = 0.0
        self.last_latency_ms: float = 0.0
        self.last_count: int = 0
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})

    def _fetch_one(self, sec: dict):
        sym = sec["yahoo"]
        try:
            r = self._session.get(
                self._CHART.format(sym=sym),
                params={"range": "1d", "interval": "1d"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            m = r.json()["chart"]["result"][0]["meta"]
            price = m.get("regularMarketPrice")
            prev = m.get("chartPreviousClose") or m.get("previousClose")
            if price is None or prev is None:
                return sec["ticker"], None
            return sec["ticker"], {
                "price": round(float(price), 2),
                "prevClose": round(float(prev), 2),
                "dayHigh": round(float(m.get("regularMarketDayHigh") or price), 2),
                "dayLow": round(float(m.get("regularMarketDayLow") or price), 2),
                "high52": round(float(m.get("fiftyTwoWeekHigh") or price * 1.2), 2),
                "low52": round(float(m.get("fiftyTwoWeekLow") or price * 0.8), 2),
                "volume": int(m.get("regularMarketVolume") or 0),
                "currency": m.get("currency") or sec["currency"],
            }
        except Exception:
            return sec["ticker"], None

    def get_quotes(self, reference: list[dict]) -> dict[str, dict]:
        now = time.time()
        if self._cache and (now - self._cache_ts) < self.ttl:
            return self._cache
        start = now
        results: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(self._fetch_one, s) for s in reference]
            for f in as_completed(futures):
                ticker, quote = f.result()
                if quote is not None:
                    results[ticker] = quote
        self.last_latency_ms = round((time.time() - start) * 1000, 1)
        self.last_count = len(results)
        self._cache = results
        self._cache_ts = time.time()
        return results

    def age_seconds(self):
        return max(0.0, time.time() - self._cache_ts) if self._cache_ts else 0.0


class SimulatedProvider(MarketDataProvider):
    """Deterministic intraday random-walk used as a resilient fallback."""

    name = "Simulated (B-PIPE style)"

    def __init__(self, reference: list[dict], seed: int = 42):
        rng = random.Random(seed)
        self._state: dict[str, dict] = {}
        for s in reference:
            open_px = round(s["base"] * (1 + rng.uniform(-0.012, 0.012)), 2)
            self._state[s["ticker"]] = {
                "prevClose": open_px, "price": open_px,
                "high": open_px, "low": open_px,
                "volume": int(rng.uniform(0.4, 8.0) * 1e6),
            }
        self._ref = {s["ticker"]: s for s in reference}

    def get_quotes(self, reference: list[dict]) -> dict[str, dict]:
        out = {}
        for s in reference:
            st = self._state[s["ticker"]]
            vol = 0.0009 * max(s["beta"], 0.3)
            st["price"] = round(max(0.01, st["price"] * (1 + random.gauss(0, vol))), 2)
            st["high"] = max(st["high"], st["price"])
            st["low"] = min(st["low"], st["price"])
            st["volume"] += int(random.uniform(1e3, 9e4))
            out[s["ticker"]] = {
                "price": st["price"], "prevClose": st["prevClose"],
                "dayHigh": st["high"], "dayLow": st["low"],
                "high52": round(s["base"] * 1.22, 2), "low52": round(s["base"] * 0.74, 2),
                "volume": st["volume"], "currency": s["currency"],
            }
        return out


class BloombergProvider(MarketDataProvider):
    """Placeholder for a Bloomberg Terminal / B-PIPE integration.

    A production deployment inside the bank would implement this using the
    official `blpapi` SDK against a licensed Terminal or Server API session,
    e.g.::

        import blpapi
        session = blpapi.Session()
        session.openService("//blp/refdata")
        request = ...  # ReferenceDataRequest with fields PX_LAST, CHG_PCT_1D ...

    The public method signature is identical to the other providers, so the
    rest of the platform requires zero changes to go live on Bloomberg.
    """

    name = "Bloomberg Terminal (blpapi)"

    def get_quotes(self, reference: list[dict]) -> dict[str, dict]:  # pragma: no cover
        raise NotImplementedError(
            "BloombergProvider requires a licensed Terminal/B-PIPE session via blpapi."
        )
