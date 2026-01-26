#!/usr/bin/env python3
"""Golden-query retrieval evaluation runner.

Two modes:
- live: run SearchManager for each case, then score vs expected URLs/domains
- offline: load results from a JSON file and score without network calls

Outputs a JSON report and exits non-zero if any case fails its thresholds.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path when executed directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.retrieval_eval import EvalCase, score_case  # noqa: E402
from src.retrieval_eval_reporting import (  # noqa: E402
    bucket_report,
    compare_cases_to_baseline,
    summarize_cases,
)
from src.search import SearchManager  # noqa: E402


_METRIC_ALLOW_DROP_KEYS: dict[str, str] = {
    "hit_at_k": "hit_at_k",
    "precision_at_k": "precision_at_k",
    "recall_at_k": "recall_at_k",
    "mrr": "mrr",
    "ndcg": "ndcg",
}


def _parse_allow_drops(thresholds: dict[str, Any]) -> dict[str, float]:
    """Extract optional baseline regression tolerances from thresholds.

    Supported keys per case:
      - max_drop_<metric>
      - allow_drop_<metric>
    where metric is one of: hit_at_k, precision_at_k, recall_at_k, mrr, ndcg
    """

    out: dict[str, float] = {}
    for metric in _METRIC_ALLOW_DROP_KEYS:
        for key in (f"max_drop_{metric}", f"allow_drop_{metric}"):
            if key not in thresholds:
                continue
            try:
                out[metric] = float(thresholds[key])
            except Exception:
                # Ignore invalid values; runner will fall back to global defaults.
                pass
    return out


def _load_cases(path: Path) -> tuple[list[EvalCase], dict[str, dict[str, float]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Cases file must be a JSON list")

    cases: list[EvalCase] = []
    allow_drop_per_case: dict[str, dict[str, float]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id") or item.get("name") or "").strip()
        query = str(item.get("query") or "").strip()
        if not cid or not query:
            continue
        k = int(item.get("k") or 10)

        expected_urls = tuple(item.get("expected_urls") or [])
        expected_domains = tuple(item.get("expected_domains") or [])

        thresholds = item.get("thresholds") or {}
        if not isinstance(thresholds, dict):
            thresholds = {}

        allow_drops = _parse_allow_drops(thresholds)
        if allow_drops:
            allow_drop_per_case[cid] = allow_drops

        cases.append(
            EvalCase(
                id=cid,
                query=query,
                k=k,
                expected_urls=tuple(str(x) for x in expected_urls),
                expected_domains=tuple(str(x) for x in expected_domains),
                theme=(str(item.get("theme")).strip() if item.get("theme") is not None else None),
                language=(
                    str(item.get("language")).strip() if item.get("language") is not None else None
                ),
                intent=(str(item.get("intent")).strip() if item.get("intent") is not None else None),
                difficulty=(
                    str(item.get("difficulty")).strip()
                    if item.get("difficulty") is not None
                    else None
                ),
                freshness=(
                    str(item.get("freshness")).strip() if item.get("freshness") is not None else None
                ),
                min_hit_at_k=thresholds.get("min_hit_at_k"),
                min_recall_at_k=thresholds.get("min_recall_at_k"),
                min_mrr=thresholds.get("min_mrr"),
                min_ndcg=thresholds.get("min_ndcg"),
            )
        )

    if not cases:
        raise ValueError("No valid cases found")
    return cases, allow_drop_per_case


def _load_offline_results(path: Path) -> dict[str, list[dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    # Accept either: {query: [results...]} or {id: [results...]}.
    if not isinstance(raw, dict):
        raise ValueError("Offline results must be a JSON object")

    out: dict[str, list[dict[str, Any]]] = {}
    for k, v in raw.items():
        if not isinstance(v, list):
            continue
        out[str(k)] = [x for x in v if isinstance(x, dict)]
    return out


async def _run_live(
    *,
    cases: list[EvalCase],
    engine: str,
) -> dict[str, list[dict[str, Any]]]:
    sm = SearchManager()
    results_map: dict[str, list[dict[str, Any]]] = {}

    for c in cases:
        res = await sm.search(c.query, num_results=c.k, engine=engine)
        # key by query and by id (so offline can use either)
        results_map[c.query] = res
        results_map[c.id] = res

    return results_map


def main() -> int:
    ap = argparse.ArgumentParser(description="Golden-query retrieval evaluation")
    ap.add_argument(
        "--cases",
        default=str(REPO_ROOT / "eval" / "golden_cases.json"),
        help="Path to golden cases JSON (default: eval/golden_cases.json)",
    )
    ap.add_argument(
        "--mode",
        choices=["live", "offline"],
        default="offline",
        help="Evaluation mode (default: offline)",
    )
    ap.add_argument(
        "--engine",
        default=os.environ.get("CRAWL4AI_EVAL_ENGINE", "all"),
        help="Engine for live mode (default: env CRAWL4AI_EVAL_ENGINE or 'all')",
    )
    ap.add_argument(
        "--offline-results",
        default=os.environ.get("CRAWL4AI_EVAL_RESULTS_JSON", ""),
        help="Offline results JSON (required for offline unless cases embed a map)",
    )
    ap.add_argument(
        "--out",
        default="",
        help="Write JSON report to this path (default: reports/retrieval_eval_<ts>.json)",
    )

    ap.add_argument(
        "--baseline",
        default=os.environ.get("CRAWL4AI_EVAL_BASELINE_REPORT", ""),
        help=(
            "Optional baseline report JSON to compare against. "
            "If provided, the script will fail when metrics regress beyond allowed drops. "
            "(env: CRAWL4AI_EVAL_BASELINE_REPORT)"
        ),
    )

    ap.add_argument(
        "--bucket-by",
        default=os.environ.get("CRAWL4AI_EVAL_BUCKET_BY", "theme,language,intent"),
        help=(
            "Comma-separated fields to bucket by in the report "
            "(default: theme,language,intent; env: CRAWL4AI_EVAL_BUCKET_BY). "
            "Use empty string to disable bucket output."
        ),
    )

    # Global allowed drops for baseline comparison (overridable per-case via thresholds).
    ap.add_argument("--allow-drop-hit-at-k", type=float, default=0.0)
    ap.add_argument("--allow-drop-precision-at-k", type=float, default=0.0)
    ap.add_argument("--allow-drop-recall-at-k", type=float, default=0.0)
    ap.add_argument("--allow-drop-mrr", type=float, default=0.0)
    ap.add_argument("--allow-drop-ndcg", type=float, default=0.0)

    args = ap.parse_args()

    cases_path = Path(args.cases)
    if not cases_path.exists():
        example = REPO_ROOT / "eval" / "golden_cases.example.json"
        sys.stderr.write(
            f"Cases file not found: {cases_path}\n"
            f"Create one (see: {example})\n"
        )
        return 2

    cases, allow_drop_per_case = _load_cases(cases_path)

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else (REPO_ROOT / "reports" / f"retrieval_eval_{ts}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "live":
        results_map = asyncio.run(_run_live(cases=cases, engine=args.engine))
    else:
        if not args.offline_results:
            sys.stderr.write(
                "offline mode requires --offline-results (or env CRAWL4AI_EVAL_RESULTS_JSON)\n"
            )
            return 2
        results_map = _load_offline_results(Path(args.offline_results))

    per_case: list[dict[str, Any]] = []
    failed = 0
    for c in cases:
        res = results_map.get(c.id) or results_map.get(c.query) or []
        scored = score_case(results=res, case=c)
        per_case.append(scored)
        if not scored.get("passed", True):
            failed += 1

    # Overall & bucket summaries.
    summary = summarize_cases(per_case)
    bucket_fields = [x.strip() for x in str(args.bucket_by).split(",") if x.strip()] if args.bucket_by is not None else []
    buckets = bucket_report(per_case, fields=bucket_fields) if bucket_fields else None

    # Optional baseline comparison.
    baseline_compare: dict[str, Any] | None = None
    regressions_count = 0
    if args.baseline:
        baseline_path = Path(args.baseline)
        if not baseline_path.exists():
            sys.stderr.write(f"Baseline report not found: {baseline_path}\n")
            return 2

        baseline_raw = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline_cases = baseline_raw.get("cases") if isinstance(baseline_raw, dict) else None
        if not isinstance(baseline_cases, list):
            sys.stderr.write("Baseline report must be a JSON object with a 'cases' list\n")
            return 2

        allow_drop_global = {
            "hit_at_k": float(args.allow_drop_hit_at_k),
            "precision_at_k": float(args.allow_drop_precision_at_k),
            "recall_at_k": float(args.allow_drop_recall_at_k),
            "mrr": float(args.allow_drop_mrr),
            "ndcg": float(args.allow_drop_ndcg),
        }

        baseline_compare = compare_cases_to_baseline(
            current_cases=per_case,
            baseline_cases=baseline_cases,
            allow_drop_global=allow_drop_global,
            allow_drop_per_case=allow_drop_per_case,
        )
        baseline_compare["baseline_path"] = str(baseline_path)
        baseline_compare["allow_drop_global"] = allow_drop_global
        regressions_count = int(baseline_compare.get("regressions_count") or 0)

    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mode": args.mode,
        "engine": args.engine,
        "cases_file": str(cases_path),
        "case_count": len(cases),
        "failed_cases": failed,
        "regressions": regressions_count,
        "summary": summary,
        "cases": per_case,
    }

    if buckets is not None:
        report["buckets"] = buckets
    if baseline_compare is not None:
        report["baseline_compare"] = baseline_compare

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote report: {out_path}")

    return 1 if (failed or regressions_count) else 0


if __name__ == "__main__":
    raise SystemExit(main())
