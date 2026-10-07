"""Automated data-quality validation for market-data ingestion.

Pure, dependency-free check functions that each return a structured
`CheckResult`. The ingestion pipelines run these against the live quote feed,
and the suite is fully covered by unit tests (`tests/test_validation.py`).

Checks implemented:
  * schema_valid  — every record carries the required fields
  * not_null      — required numeric fields are populated (-> completeness %)
  * freshness     — data arrived within the freshness SLA
  * range_bounds  — prices are positive and within sane statistical bounds
  * row_count     — ingested row count has not drifted from expectation
  * duplicates    — no duplicate primary keys
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

REQUIRED_FIELDS = ("ticker", "price", "prevClose", "currency")
FRESHNESS_SLA_MIN = 15.0


@dataclass
class CheckResult:
    key: str
    label: str
    status: str  # "pass" | "warn" | "fail"
    detail: str
    metric: Optional[float] = None
    rows: int = 0

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
            "metric": self.metric,
            "rows": self.rows,
        }


def check_schema(records: list[dict]) -> CheckResult:
    missing = [r.get("ticker", "?") for r in records
               if any(f not in r for f in REQUIRED_FIELDS)]
    if missing:
        return CheckResult("schema_valid", "Schema & type validation", "fail",
                           f"{len(missing)} record(s) missing required fields", rows=len(records))
    return CheckResult("schema_valid", "Schema & type validation", "pass",
                       f"all {len(records)} records match contract", rows=len(records))


def check_not_null(records: list[dict]) -> CheckResult:
    n = len(records) or 1
    nulls = sum(1 for r in records if r.get("price") is None or r.get("prevClose") is None)
    completeness = round((n - nulls) / n * 100, 2)
    if nulls:
        return CheckResult("not_null", "Null / completeness check", "fail",
                           f"{nulls} null price field(s) — {completeness}% complete",
                           metric=completeness, rows=len(records))
    return CheckResult("not_null", "Null / completeness check", "pass",
                       f"{completeness}% complete", metric=completeness, rows=len(records))


def check_freshness(freshness_min: float, sla: float = FRESHNESS_SLA_MIN) -> CheckResult:
    f = round(freshness_min, 1)
    if freshness_min > sla:
        return CheckResult("freshness", f"Freshness SLA (< {int(sla)} min)", "fail",
                           f"{f} min old — SLA breached", metric=f)
    if freshness_min > sla * 0.8:
        return CheckResult("freshness", f"Freshness SLA (< {int(sla)} min)", "warn",
                           f"{f} min old — approaching SLA", metric=f)
    return CheckResult("freshness", f"Freshness SLA (< {int(sla)} min)", "pass",
                       f"{f} min old", metric=f)


def check_price_bounds(records: list[dict]) -> CheckResult:
    violations = 0
    for r in records:
        p = r.get("price")
        if p is None:
            continue
        if p <= 0:
            violations += 1
            continue
        lo, hi = r.get("low52"), r.get("high52")
        if lo and hi and hi > lo and not (lo * 0.5 <= p <= hi * 1.5):
            violations += 1
    if violations:
        return CheckResult("range_bounds", "Price range / outlier bounds", "fail",
                           f"{violations} price(s) outside expected bounds", rows=len(records))
    return CheckResult("range_bounds", "Price range / outlier bounds", "pass",
                       "all prices within bounds", rows=len(records))


def check_row_count(actual: int, expected: int, warn: float = 0.1, fail: float = 0.3) -> CheckResult:
    expected = expected or 1
    drift = abs(actual - expected) / expected
    pct = round(drift * 100, 1)
    if drift > fail:
        return CheckResult("row_count", "Row-count drift vs expected", "fail",
                           f"{actual}/{expected} rows — {pct}% drift", metric=pct, rows=actual)
    if drift > warn:
        return CheckResult("row_count", "Row-count drift vs expected", "warn",
                           f"{actual}/{expected} rows — {pct}% drift", metric=pct, rows=actual)
    return CheckResult("row_count", "Row-count drift vs expected", "pass",
                       f"{actual}/{expected} rows", metric=pct, rows=actual)


def check_duplicates(records: list[dict], key: str = "ticker") -> CheckResult:
    keys = [r.get(key) for r in records]
    dups = len(keys) - len(set(keys))
    if dups:
        return CheckResult("duplicates", "Duplicate key detection", "fail",
                           f"{dups} duplicate key(s)", rows=len(records))
    return CheckResult("duplicates", "Duplicate key detection", "pass",
                       "no duplicate keys", rows=len(records))


def run_all(records: list[dict], expected_rows: int, freshness_min: float = 0.0) -> list[CheckResult]:
    """Run the full validation suite against a batch of market-data records."""
    return [
        check_schema(records),
        check_not_null(records),
        check_freshness(freshness_min),
        check_price_bounds(records),
        check_row_count(len(records), expected_rows),
        check_duplicates(records),
    ]
