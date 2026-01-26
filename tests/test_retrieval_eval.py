from src.retrieval_eval import EvalCase, score_case


def test_hit_at_k_domain_normalizes_www():
    case = EvalCase(
        id="t",
        query="q",
        k=5,
        expected_domains=("www.iaea.org", "iaea.org"),
        min_hit_at_k=1.0,
    )

    results = [
        {"title": "x", "link": "https://iaea.org/some/page"},
    ]

    scored = score_case(results=results, case=case)
    assert scored["hit_at_k"] == 1
    assert scored["passed"] is True


def test_hit_at_k_fails_when_no_expected_domain_in_topk():
    case = EvalCase(
        id="t",
        query="q",
        k=3,
        expected_domains=("iter.org",),
        min_hit_at_k=1.0,
    )

    results = [
        {"title": "x", "link": "https://example.com/a"},
        {"title": "y", "link": "https://example.com/b"},
    ]

    scored = score_case(results=results, case=case)
    assert scored["hit_at_k"] == 0
    assert scored["passed"] is False
    assert "hit_at_k" in scored["failed_metrics"]
