#!/usr/bin/env python3
"""Unit tests for Reciprocal Rank Fusion merge strategy."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import merge_and_deduplicate


def test_rrf_ranks_items_supported_by_multiple_engines_higher():
    # A appears in both engines, B only in google, C only in ddg.
    all_results = {
        "google": [
            {"title": "A", "link": "https://example.com/a", "snippet": "", "engine": "google"},
            {"title": "B", "link": "https://example.com/b", "snippet": "", "engine": "google"},
        ],
        "duckduckgo": [
            {"title": "A dup", "link": "https://www.example.com/a?utm_source=x", "snippet": "", "engine": "duckduckgo"},
            {"title": "C", "link": "https://example.com/c", "snippet": "", "engine": "duckduckgo"},
        ],
    }

    fused = merge_and_deduplicate(
        all_results,
        num_results=3,
        fusion_method="rrf",
        rrf_k=0,
        canonicalize_links=True,
    )

    assert len(fused) == 3
    # A should be first because it gets contributions from both engines.
    assert fused[0]["link"].startswith("https://")
    assert fused[0]["link"].rstrip("/") == "https://example.com/a"


def test_rrf_engine_weights_can_downweight_an_engine():
    all_results = {
        "google": [
            {"title": "A", "link": "https://example.com/a", "snippet": "", "engine": "google"},
            {"title": "B", "link": "https://example.com/b", "snippet": "", "engine": "google"},
        ],
        "duckduckgo": [
            {"title": "A dup", "link": "https://example.com/a", "snippet": "", "engine": "duckduckgo"},
        ],
    }

    fused = merge_and_deduplicate(
        all_results,
        num_results=2,
        fusion_method="rrf",
        rrf_k=0,
        engine_weights={"duckduckgo": 0.0, "google": 1.0},
        canonicalize_links=True,
    )

    assert len(fused) == 2
    # With ddg weight=0, ranking is purely from google list.
    assert fused[0]["link"].rstrip("/") == "https://example.com/a"


def test_rrf_domain_boost_can_promote_official_site():
    # Without a domain boost, rank=1 usually beats rank=2 for k=0.
    # With an official-domain multiplier, an official link can be promoted.
    all_results = {
        "google": [
            {"title": "Unofficial", "link": "https://example.com/x", "snippet": "", "engine": "google"},
            {"title": "ITER", "link": "https://www.iter.org/", "snippet": "", "engine": "google"},
        ]
    }

    fused = merge_and_deduplicate(
        all_results,
        num_results=2,
        fusion_method="rrf",
        rrf_k=0,
        canonicalize_links=True,
        domain_boosts={"iter.org": 2.2},
    )

    assert fused[0]["link"].rstrip("/") == "https://www.iter.org"
