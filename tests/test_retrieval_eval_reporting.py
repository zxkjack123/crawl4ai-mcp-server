from src.retrieval_eval_reporting import bucket_report, compare_cases_to_baseline, summarize_cases


def test_summarize_cases_counts_and_means():
    cases = [
        {"id": "a", "passed": True, "hit_at_k": 1, "mrr": 1.0},
        {"id": "b", "passed": False, "hit_at_k": 0, "mrr": 0.5},
        {"id": "c", "passed": True, "hit_at_k": 1, "mrr": None},
    ]

    s = summarize_cases(cases)
    assert s["case_count"] == 3
    assert s["failed_cases"] == 1
    assert abs(s["pass_rate"] - (2.0 / 3.0)) < 1e-9

    # hit_at_k mean uses all non-null values
    assert abs(s["metrics_mean"]["hit_at_k"] - (2.0 / 3.0)) < 1e-9
    # mrr mean ignores None
    assert abs(s["metrics_mean"]["mrr"] - 0.75) < 1e-9


def test_bucket_report_groups_by_field_and_counts():
    cases = [
        {"id": "a", "passed": True, "theme": "t1", "hit_at_k": 1},
        {"id": "b", "passed": False, "theme": "t1", "hit_at_k": 0},
        {"id": "c", "passed": True, "theme": "t2", "hit_at_k": 1},
    ]

    br = bucket_report(cases, fields=["theme"])
    assert br["fields"] == ["theme"]
    grouping = br["groupings"]["theme"]
    assert grouping["bucket_count"] == 2
    assert grouping["buckets"]["t1"]["case_count"] == 2
    assert grouping["buckets"]["t1"]["failed_cases"] == 1
    assert grouping["buckets"]["t2"]["case_count"] == 1


def test_compare_cases_to_baseline_detects_regression_and_respects_allow_drop():
    baseline = [
        {"id": "a", "mrr": 1.0, "hit_at_k": 1},
        {"id": "b", "mrr": 0.5, "hit_at_k": 1},
    ]
    current = [
        {"id": "a", "mrr": 0.9, "hit_at_k": 1},
        {"id": "b", "mrr": 0.4, "hit_at_k": 0},
    ]

    # Allow small mrr drop globally, but no drop on hit_at_k.
    cmp = compare_cases_to_baseline(
        current_cases=current,
        baseline_cases=baseline,
        allow_drop_global={"mrr": 0.15, "hit_at_k": 0.0},
    )

    # a: drop 0.1 <= 0.15 OK
    # b: hit_at_k drops by 1 -> regression
    assert cmp["regressions_count"] == 1
    assert cmp["regressions"][0]["case_id"] == "b"
    assert cmp["regressions"][0]["metric"] == "hit_at_k"


def test_compare_cases_to_baseline_per_case_override():
    baseline = [{"id": "a", "mrr": 1.0}]
    current = [{"id": "a", "mrr": 0.8}]

    cmp = compare_cases_to_baseline(
        current_cases=current,
        baseline_cases=baseline,
        allow_drop_global={"mrr": 0.0},
        allow_drop_per_case={"a": {"mrr": 0.25}},
    )

    assert cmp["regressions_count"] == 0
