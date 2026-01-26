"""Retrieval evaluation helpers.

This module supports "golden query" evaluation: predefined queries with a
curated expected answer set (URLs and/or domains), scored using IR metrics.

Design goals:
- Lightweight (stdlib only)
- Works with live search results or offline saved results
- Canonicalizes URLs using existing project logic to reduce noise
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlsplit

try:
    from src.utils import canonicalize_url
except Exception:  # pragma: no cover
    # Fallback for direct execution contexts.
    try:
        from .utils import canonicalize_url  # type: ignore
    except Exception:  # pragma: no cover
        from utils import canonicalize_url


def _norm_host(host: str | None) -> str | None:
    if not host:
        return None
    h = host.strip().lower()
    if h.startswith("www."):
        h = h[4:]
    return h or None


def _result_url(result: dict[str, Any]) -> str | None:
    # Search results in this repo use 'link' as canonical URL field.
    url = result.get("link") or result.get("url")
    if url is None:
        return None
    s = str(url).strip()
    return s or None


def _canonical_result_urls(results: Iterable[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for r in results:
        u = canonicalize_url(_result_url(r))
        if u:
            out.append(u)
    return out


def _result_hosts(results: Iterable[dict[str, Any]]) -> list[str]:
    hosts: list[str] = []
    for r in results:
        u = canonicalize_url(_result_url(r))
        if not u:
            continue
        try:
            h = _norm_host(urlsplit(u).hostname)
        except Exception:
            h = None
        if h:
            hosts.append(h)
    return hosts


def precision_at_k(hits: list[bool], k: int) -> float:
    if k <= 0:
        return 0.0
    top = hits[:k]
    if not top:
        return 0.0
    return float(sum(1 for x in top if x)) / float(k)


def recall_at_k(hits: list[bool], relevant_total: int, k: int) -> float:
    if relevant_total <= 0 or k <= 0:
        return 0.0
    return float(sum(1 for x in hits[:k] if x)) / float(relevant_total)


def mrr(hits: list[bool], k: int) -> float:
    if k <= 0:
        return 0.0
    for i, h in enumerate(hits[:k], start=1):
        if h:
            return 1.0 / float(i)
    return 0.0


def ndcg_binary(hits: list[bool], relevant_total: int, k: int) -> float:
    """nDCG@k for binary relevance.

    rel_i in {0,1}. IDCG assumes all relevant items are ranked first.
    """
    if k <= 0 or relevant_total <= 0:
        return 0.0

    import math

    def dcg(vals: list[bool]) -> float:
        s = 0.0
        for i, rel in enumerate(vals[:k], start=1):
            if not rel:
                continue
            s += 1.0 / math.log2(i + 1)
        return s

    ideal_len = min(k, relevant_total)
    idcg = dcg([True] * ideal_len)
    if idcg <= 0:
        return 0.0
    return dcg(hits) / idcg


@dataclass(frozen=True)
class EvalCase:
    id: str
    query: str
    k: int = 10
    expected_urls: tuple[str, ...] = ()
    expected_domains: tuple[str, ...] = ()

    # Optional taxonomy/metadata fields (for reporting & bucketed summaries).
    theme: str | None = None
    language: str | None = None
    intent: str | None = None
    difficulty: str | None = None
    freshness: str | None = None

    # Optional per-case thresholds (missing means "report only").
    # min_hit_at_k: require at least one expected URL/domain to appear in top-k.
    # This is usually the most stable gate for "official entrypoint" checks.
    min_hit_at_k: float | None = None
    min_recall_at_k: float | None = None
    min_mrr: float | None = None
    min_ndcg: float | None = None


def score_case(
    *,
    results: list[dict[str, Any]],
    case: EvalCase,
) -> dict[str, Any]:
    k = max(1, int(case.k))

    expected_urls = {
        canonicalize_url(u) for u in case.expected_urls if canonicalize_url(u)
    }
    expected_domains = {
        _norm_host(d) for d in case.expected_domains if _norm_host(d)
    }

    urls = _canonical_result_urls(results)
    hosts = _result_hosts(results)

    url_hits = [u in expected_urls for u in urls[:k]] if expected_urls else []
    domain_hits = [h in expected_domains for h in hosts[:k]] if expected_domains else []

    # Prefer URL-level hits when provided; else fall back to domain-level hits.
    if expected_urls:
        hits = url_hits
        relevant_total = len(expected_urls)
        match_level = "url"
    elif expected_domains:
        hits = domain_hits
        relevant_total = len(expected_domains)
        match_level = "domain"
    else:
        hits = []
        relevant_total = 0
        match_level = "none"

    out: dict[str, Any] = {
        "id": case.id,
        "query": case.query,
        "k": k,
        "match_level": match_level,
        "expected_urls": sorted(expected_urls),
        "expected_domains": sorted(d for d in expected_domains if d),
        "result_count": len(results),
        "topk_urls": urls[:k],
    }

    # Attach metadata fields when provided.
    if case.theme is not None:
        out["theme"] = case.theme
    if case.language is not None:
        out["language"] = case.language
    if case.intent is not None:
        out["intent"] = case.intent
    if case.difficulty is not None:
        out["difficulty"] = case.difficulty
    if case.freshness is not None:
        out["freshness"] = case.freshness

    hit_at_k: int | None
    if relevant_total > 0:
        hit_at_k = 1 if any(hits[:k]) else 0
    else:
        hit_at_k = None
    out["hit_at_k"] = hit_at_k

    if relevant_total > 0:
        out.update(
            {
                "precision_at_k": precision_at_k(hits, k),
                "recall_at_k": recall_at_k(hits, relevant_total, k),
                "mrr": mrr(hits, k),
                "ndcg": ndcg_binary(hits, relevant_total, k),
            }
        )
    else:
        out.update(
            {
                "precision_at_k": None,
                "recall_at_k": None,
                "mrr": None,
                "ndcg": None,
            }
        )

    # Threshold checks (optional)
    failed: list[str] = []
    if out["hit_at_k"] is not None and case.min_hit_at_k is not None:
        if float(out["hit_at_k"]) < float(case.min_hit_at_k):
            failed.append("hit_at_k")
    if out["recall_at_k"] is not None and case.min_recall_at_k is not None:
        if float(out["recall_at_k"]) < float(case.min_recall_at_k):
            failed.append("recall_at_k")
    if out["mrr"] is not None and case.min_mrr is not None:
        if float(out["mrr"]) < float(case.min_mrr):
            failed.append("mrr")
    if out["ndcg"] is not None and case.min_ndcg is not None:
        if float(out["ndcg"]) < float(case.min_ndcg):
            failed.append("ndcg")

    out["failed_metrics"] = failed
    out["passed"] = len(failed) == 0
    return out
