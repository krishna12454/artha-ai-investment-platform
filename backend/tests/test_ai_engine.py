"""Tests for the AI engine's deterministic fallback (no API key required)."""
import ai_engine


SEC = {
    "ticker": "NVDA:US", "name": "NVIDIA Corp.", "sector": "Technology",
    "exchange": "NASDAQ", "currency": "USD", "price": 134.2, "changePct": 1.1,
    "eps": 2.9, "pe": 46.3, "pb": 48.7, "divYield": 0.02, "beta": 1.67,
    "high52": 160.0, "low52": 100.0, "marketCap": 3290e9,
}

MOVERS = {
    "gainers": [{"name": "A", "sector": "Tech", "changePct": 2.1, "ticker": "A", "price": 10}],
    "losers": [{"name": "B", "sector": "Health", "changePct": -1.8, "ticker": "B", "price": 20}],
    "advancers": 8, "decliners": 6, "breadth": 57.0, "sentiment": "Neutral",
}


def test_heuristic_valuation_structure():
    r = ai_engine._heuristic_valuation(SEC)
    assert r["rating"] in ("Buy", "Hold", "Sell")
    assert isinstance(r["fairValue"], (int, float))
    assert len(r["bullCase"]) == 3 and len(r["bearCase"]) == 3 and len(r["keyRisks"]) == 3
    assert r["thesis"]


def test_heuristic_brief_structure():
    b = ai_engine._heuristic_brief(MOVERS)
    assert b["headline"]
    assert len(b["themes"]) <= 3
    assert len(b["watchItems"]) == 3
