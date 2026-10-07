"""Unit tests for the data-quality validation engine.

Pure and deterministic — no network, DB or API keys required.
"""
import validation as v


def _rec(ticker="AAPL:US", price=100.0, prev=99.0, cur="USD", lo=70.0, hi=130.0):
    return {"ticker": ticker, "price": price, "prevClose": prev,
            "currency": cur, "low52": lo, "high52": hi}


def test_schema_pass():
    assert v.check_schema([_rec(), _rec("MSFT:US")]).status == "pass"


def test_schema_fail_on_missing_field():
    bad = {"ticker": "X", "price": 10}  # missing prevClose, currency
    assert v.check_schema([bad]).status == "fail"


def test_not_null_completeness():
    res = v.check_not_null([_rec(), _rec(price=None)])
    assert res.status == "fail"
    assert res.metric == 50.0


def test_not_null_pass():
    res = v.check_not_null([_rec(), _rec("MSFT:US")])
    assert res.status == "pass"
    assert res.metric == 100.0


def test_freshness_pass_warn_fail():
    assert v.check_freshness(2.0).status == "pass"
    assert v.check_freshness(13.0).status == "warn"
    assert v.check_freshness(30.0).status == "fail"


def test_price_bounds_flags_negative_and_outliers():
    assert v.check_price_bounds([_rec(price=-5)]).status == "fail"
    assert v.check_price_bounds([_rec(price=1000, lo=70, hi=130)]).status == "fail"
    assert v.check_price_bounds([_rec(price=100)]).status == "pass"


def test_row_count_drift():
    assert v.check_row_count(14, 14).status == "pass"
    assert v.check_row_count(16, 14).status == "warn"
    assert v.check_row_count(5, 14).status == "fail"


def test_duplicates():
    assert v.check_duplicates([_rec(), _rec()]).status == "fail"
    assert v.check_duplicates([_rec(), _rec("MSFT:US")]).status == "pass"


def test_run_all_shape():
    results = v.run_all([_rec(), _rec("MSFT:US")], expected_rows=2, freshness_min=1.0)
    assert len(results) == 6
    assert all(r.status in ("pass", "warn", "fail") for r in results)
    assert all("key" in r.as_dict() for r in results)
