#!/usr/bin/env python3
"""Unit tests for URL canonicalization + dedup improvements."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import canonicalize_url, merge_and_deduplicate


def test_canonicalize_url_strips_tracking_and_normalizes():
    url = "http://www.Example.com/path/?utm_source=xx&id=1#frag"
    assert canonicalize_url(url) == "https://example.com/path?id=1"


def test_canonicalize_url_handles_root():
    assert canonicalize_url("https://example.com") == "https://example.com"
    assert canonicalize_url("https://www.example.com/") == "https://example.com"


def test_merge_and_deduplicate_prefers_higher_priority_engine_for_duplicates():
    all_results = {
        "duckduckgo": [
            {
                "title": "DDG result",
                "link": "https://www.example.com/article?utm_source=a",
                "snippet": "ddg",
                "engine": "duckduckgo",
            }
        ],
        "google": [
            {
                "title": "Google result",
                "link": "http://example.com/article",
                "snippet": "google",
                "engine": "google",
            }
        ],
    }

    merged = merge_and_deduplicate(all_results, num_results=10, canonicalize_links=True)
    assert len(merged) == 1
    assert merged[0]["engine"] == "google"
    assert merged[0]["title"] == "Google result"
