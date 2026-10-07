"""AI engine for valuation and market commentary.

Uses the official Anthropic SDK when `ANTHROPIC_API_KEY` is set, and otherwise
falls back to a transparent deterministic quant model so the platform always
returns useful output (and clones run with zero configuration). The response
always reports which `engine` produced it.
"""
import os
import json
import logging

from anthropic import Anthropic

logger = logging.getLogger("artha.ai")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

ENGINE_LIVE = "Claude (Anthropic)"
ENGINE_FALLBACK = "Quant model (set ANTHROPIC_API_KEY for AI)"

SYSTEM = (
    "You are the senior investment strategist engine inside Artha AI, an "
    "institutional investment-intelligence platform. You write concise, "
    "precise, compliance-aware research-desk commentary for portfolio "
    "managers — never retail financial advice. Always return strictly valid "
    "JSON with no markdown fences."
)

# Sector reference P/E anchors used by the fallback quant model
SECTOR_PE = {
    "Technology": 30, "Health Care": 16, "Financials": 13,
    "Consumer Staples": 20, "Consumer Discretionary": 21,
    "Industrials": 22, "Commodities": 0,
}


def ai_available() -> bool:
    return _client is not None


def _complete(prompt: str, max_tokens: int = 1200):
    if not _client:
        return None
    try:
        msg = _client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    except Exception as e:
        logger.warning("Anthropic call failed, using fallback: %s", e)
        return None


def _parse_json(text: str):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start:end + 1]
    return json.loads(t)


# --------------------------- Valuation ---------------------------
def valuation(sec: dict):
    prompt = (
        f"Perform an institutional valuation check on this security.\n"
        f"Ticker: {sec['ticker']} | {sec['name']} ({sec['sector']}, {sec['exchange']})\n"
        f"Price: {sec['currency']} {sec['price']} | Day change: {sec['changePct']:+.2f}%\n"
        f"EPS: {sec['eps']} | P/E: {sec['pe']} | P/B: {sec['pb']} | "
        f"Dividend yield: {sec['divYield']}% | Beta: {sec['beta']}\n"
        f"52w range: {sec['low52']} – {sec['high52']} | Market cap: {sec['marketCap']/1e9:.1f}B\n\n"
        "Return strictly valid JSON with keys: fairValue (number, intrinsic value "
        "per share, same currency), upsidePct (number vs current price), rating "
        "('Buy'/'Hold'/'Sell'), confidence ('High'/'Medium'/'Low'), thesis "
        "(3-4 sentences), valuationNote (1-2 sentences on the multiple/DCF "
        "reasoning), bullCase (array of 3 short strings), bearCase (array of 3 "
        "short strings), keyRisks (array of 3 short strings)."
    )
    raw = _complete(prompt)
    if raw:
        try:
            data = _parse_json(raw)
            return _shape_valuation(sec, data), ENGINE_LIVE
        except Exception as e:
            logger.warning("valuation JSON parse failed, using fallback: %s", e)
    return _heuristic_valuation(sec), ENGINE_FALLBACK


def _shape_valuation(sec, d):
    return {
        "fairValue": d.get("fairValue"),
        "upsidePct": d.get("upsidePct"),
        "rating": d.get("rating", "Hold"),
        "confidence": d.get("confidence", "Medium"),
        "thesis": d.get("thesis", ""),
        "valuationNote": d.get("valuationNote", ""),
        "bullCase": d.get("bullCase", []),
        "bearCase": d.get("bearCase", []),
        "keyRisks": d.get("keyRisks", []),
    }


def _heuristic_valuation(sec):
    price = sec["price"]
    eps = sec["eps"]
    if eps and eps > 0:
        anchor = SECTOR_PE.get(sec["sector"]) or sec["pe"] or 18
        target_pe = (sec["pe"] + anchor) / 2 if sec["pe"] else anchor
        fair = round(eps * target_pe, 2)
    else:
        # No earnings (e.g. commodity): anchor to mid of 52-week range
        fair = round((sec["high52"] + sec["low52"]) / 2, 2)
    upside = round((fair / price - 1) * 100, 2) if price else 0.0
    rating = "Buy" if upside > 10 else "Sell" if upside < -10 else "Hold"
    pos52 = ((price - sec["low52"]) / (sec["high52"] - sec["low52"]) * 100) if sec["high52"] > sec["low52"] else 50
    beta_desc = "high" if sec["beta"] > 1.1 else "moderate" if sec["beta"] > 0.7 else "low"
    thesis = (
        f"{sec['name']} trades at {sec['currency']} {price:.2f}, "
        f"{pos52:.0f}% of its 52-week range, on a {sec['pe']:.1f}x P/E versus a "
        f"{sector_label(sec['sector'])} sector anchor near {SECTOR_PE.get(sec['sector'], 18)}x. "
        f"A blended multiple model implies fair value of {sec['currency']} {fair:.2f}, "
        f"a {upside:+.1f}% gap to the current quote. With {beta_desc} beta ({sec['beta']}) "
        f"and a {sec['divYield']:.1f}% yield, the risk/reward is assessed as {rating.lower()}."
    )
    return {
        "fairValue": fair,
        "upsidePct": upside,
        "rating": rating,
        "confidence": "Medium",
        "thesis": thesis,
        "valuationNote": (
            f"Fair value derived from a sector-anchored P/E ({SECTOR_PE.get(sec['sector'], 18)}x) "
            f"blended with the stock's current {sec['pe']:.1f}x multiple on {sec['currency']} {eps:.2f} EPS."
            if eps and eps > 0 else
            "Fair value anchored to the mid-point of the trailing 52-week trading range (no earnings base)."
        ),
        "bullCase": [
            f"Trades {abs(upside):.0f}% {'below' if upside > 0 else 'above'} modelled fair value",
            f"{sector_label(sec['sector'])} exposure with {beta_desc} market sensitivity",
            f"{sec['divYield']:.1f}% dividend yield supports total return" if sec["divYield"] else "Scale and balance-sheet quality",
        ],
        "bearCase": [
            f"{sec['pe']:.1f}x P/E leaves limited margin for an earnings miss" if sec["pe"] else "Valuation sensitive to macro inputs",
            f"Beta of {sec['beta']} amplifies drawdowns in risk-off regimes",
            f"Currently at {pos52:.0f}% of 52-week range — momentum may be extended" if pos52 > 70 else "Near-term catalysts limited",
        ],
        "keyRisks": [
            "Multiple de-rating on rates / macro",
            f"{sector_label(sec['sector'])}-specific regulatory or cyclical risk",
            "FX translation on non-base-currency exposure",
        ],
    }


def sector_label(s):
    return s.lower()


# --------------------------- Market brief ---------------------------
def market_brief(movers: dict):
    g = ", ".join(f"{s['name']} {s['changePct']:+.2f}%" for s in movers["gainers"][:3])
    l = ", ".join(f"{s['name']} {s['changePct']:+.2f}%" for s in movers["losers"][:3])
    prompt = (
        f"Market breadth: {movers['advancers']} advancers vs {movers['decliners']} "
        f"decliners (breadth {movers['breadth']}%, regime {movers['sentiment']}). "
        f"Top up: {g}. Top down: {l}. Produce a research-desk brief as JSON with "
        "keys: headline (<=12 words), summary (2-3 sentences of macro context), "
        "themes (array of 3 objects with 'title' and 'detail'), watchItems "
        "(array of 3 short strings a PM should monitor)."
    )
    raw = _complete(prompt, max_tokens=900)
    if raw:
        try:
            d = _parse_json(raw)
            return {
                "headline": d.get("headline", "Markets digest mixed signals"),
                "summary": d.get("summary", ""),
                "themes": d.get("themes", []),
                "watchItems": d.get("watchItems", []),
            }, ENGINE_LIVE
        except Exception as e:
            logger.warning("brief JSON parse failed, using fallback: %s", e)
    return _heuristic_brief(movers), ENGINE_FALLBACK


def _heuristic_brief(m):
    top = m["gainers"][0] if m["gainers"] else None
    bot = m["losers"][0] if m["losers"] else None
    headline = f"{m['sentiment']} tape as breadth holds near {m['breadth']:.0f}%"
    summary = (
        f"Market breadth is {m['breadth']:.0f}% with {m['advancers']} names advancing "
        f"and {m['decliners']} declining, consistent with a {m['sentiment'].lower()} regime. "
        + (f"{top['name']} leads gainers ({top['changePct']:+.2f}%)" if top else "")
        + (f" while {bot['name']} lags ({bot['changePct']:+.2f}%)." if bot else ".")
    )
    themes = []
    if top:
        themes.append({"title": "Leadership", "detail": f"{top['sector']} strength led by {top['name']} ({top['changePct']:+.2f}%)."})
    if bot:
        themes.append({"title": "Laggards", "detail": f"Pressure in {bot['name']} ({bot['changePct']:+.2f}%) weighs on {bot['sector']}."})
    themes.append({"title": "Breadth", "detail": f"{m['advancers']}/{m['advancers'] + m['decliners']} names higher — regime reads {m['sentiment']}."})
    return {
        "headline": headline,
        "summary": summary,
        "themes": themes[:3],
        "watchItems": [
            "Rates path and central-bank commentary",
            f"Follow-through in {top['sector'] if top else 'leadership'} names",
            "CHF / EUR / USD cross moves on the book",
        ],
    }
