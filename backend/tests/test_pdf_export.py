"""Tests for PDF generation (ReportLab) — verify valid PDF bytes are produced."""
import pdf_export


VALUATION = {
    "ticker": "ROG:SW", "name": "Roche Holding AG", "currency": "CHF",
    "price": 248.6, "fairValue": 300.0, "upsidePct": 20.7, "rating": "Buy",
    "confidence": "Medium", "engine": "Quant model", "thesis": "Test thesis.",
    "valuationNote": "Test note.", "bullCase": ["a", "b", "c"],
    "bearCase": ["d", "e", "f"], "keyRisks": ["g", "h", "i"],
    "generatedAt": "2026-01-01T00:00:00+00:00",
}

BRIEF = {
    "headline": "Test headline", "summary": "Test summary.",
    "themes": [{"title": "T", "detail": "d"}],
    "watchItems": ["w1", "w2"], "engine": "Quant model",
    "generatedAt": "2026-01-01T00:00:00+00:00",
    "movers": {"sentiment": "Neutral", "breadth": 50.0, "advancers": 7, "decliners": 7,
               "gainers": [{"ticker": "A", "name": "Alpha", "price": 10, "changePct": 1.0}],
               "losers": [{"ticker": "B", "name": "Beta", "price": 20, "changePct": -1.0}]},
}


def test_valuation_pdf_is_valid():
    data = pdf_export.valuation_pdf(VALUATION)
    assert data[:4] == b"%PDF"
    assert len(data) > 1000


def test_market_brief_pdf_is_valid():
    data = pdf_export.market_brief_pdf(BRIEF)
    assert data[:4] == b"%PDF"
    assert len(data) > 1000
