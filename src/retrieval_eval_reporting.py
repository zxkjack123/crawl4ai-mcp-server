"""Report-level helpers for golden-query retrieval evaluation.

This module operates on the JSON-like dicts produced by `score_case()` and the
report structure produced by `scripts/retrieval_eval.py`.

It intentionally stays stdlib-only so it can run in CI without extra deps.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


_METRICS: tuple[str, ...] = (
    "hit_at_k",
    "precision_at_k",
    "recall_at_k",
    "mrr",
    "ndcg",
)


def _as_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return float(1.0 if x else 0.0)
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x))
    except Exception:
        return None


def summarize_cases(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compute overall summary statistics for a set of scored cases."""

    case_list = list(cases)
    total = len(case_list)
    failed = sum(1 for c in case_list if not bool(c.get("passed", True)))

    metric_sums: dict[str, float] = defaultdict(float)
    metric_counts: dict[str, int] = defaultdict(int)

    for c in case_list:
        for m in _METRICS:
            v = _as_float(c.get(m))
            if v is None:
                continue
            metric_sums[m] += v
            metric_counts[m] += 1

    metrics_mean: dict[str, float] = {}
    for m in _METRICS:
        if metric_counts.get(m, 0) > 0:
            metrics_mean[m] = metric_sums[m] / float(metric_counts[m])

    out: dict[str, Any] = {
        "case_count": total,
        "failed_cases": failed,
        "pass_rate": (1.0 - (failed / float(total))) if total else 0.0,
        "metrics_mean": metrics_mean,
        "metrics_counts": dict(metric_counts),
    }
    return out


def bucket_cases(
    cases: Iterable[dict[str, Any]],
    *,
    field: str,
    missing_label: str = "(missing)",
) -> dict[str, Any]:
    """Group cases by a field and return summary per bucket."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in cases:
        raw = c.get(field)
        key = missing_label if raw is None or str(raw).strip() == "" else str(raw)
        groups[key].append(c)

    buckets: dict[str, Any] = {}
    for key, items in sorted(groups.items(), key=lambda kv: kv[0]):
        buckets[key] = summarize_cases(items)

    return {
        "field": field,
        "bucket_count": len(buckets),
        "buckets": buckets,
    }


def bucket_report(
    cases: Iterable[dict[str, Any]],
    *,
    fields: list[str],
    missing_label: str = "(missing)",
) -> dict[str, Any]:
    """Return multiple bucket groupings for the provided fields."""

    out: dict[str, Any] = {
        "fields": list(fields),
        "groupings": {},
    }
    for f in fields:
        out["groupings"][f] = bucket_cases(cases, field=f, missing_label=missing_label)
    return out


def compare_cases_to_baseline(
    *,
    current_cases: Iterable[dict[str, Any]],
    baseline_cases: Iterable[dict[str, Any]],
    allow_drop_global: dict[str, float] | None = None,
    allow_drop_per_case: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Compare current scored cases to a baseline.

    A regression is recorded when:
        baseline_value - current_value > allowed_drop
    i.e. current is worse by more than allowed.

    Metrics with None values are skipped.
    Cases are matched by `id`.
    """

    allow_drop_global = allow_drop_global or {}
    allow_drop_per_case = allow_drop_per_case or {}

    base_by_id: dict[str, dict[str, Any]] = {}
    for c in baseline_cases:
        cid = str(c.get("id") or "").strip()
        if cid:
            base_by_id[cid] = c

    regressions: list[dict[str, Any]] = []
    missing_in_baseline: list[str] = []

    for cur in current_cases:
        cid = str(cur.get("id") or "").strip()
        if not cid:
            continue

        base = base_by_id.get(cid)
        if not base:
            missing_in_baseline.append(cid)
            continue

        per_case_allow = allow_drop_per_case.get(cid, {})

        for metric in _METRICS:
            b = _as_float(base.get(metric))
            c = _as_float(cur.get(metric))
            if b is None or c is None:
                continue

            allowed = per_case_allow.get(metric)
            if allowed is None:
                allowed = allow_drop_global.get(metric, 0.0)
            allowed = float(allowed)

            drop = b - c
            if drop > allowed:
                regressions.append(
                    {
                        "case_id": cid,
                        "metric": metric,
                        "baseline": b,
                        "current": c,
                        "delta": c - b,
                        "allowed_drop": allowed,
                    }
                )

    return {
        "regressions": regressions,
        "regressions_count": len(regressions),
        "missing_in_baseline": sorted(set(missing_in_baseline)),
        "missing_in_baseline_count": len(set(missing_in_baseline)),
    }
