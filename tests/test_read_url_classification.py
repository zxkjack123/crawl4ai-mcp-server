"""Unit tests for read_url failure classification (2026-10-19)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from index import _ReadUrlFailure, _classify_content, _classify_read_failure  # noqa: E402


def test_status_403_is_blocked_by_target():
    cls, retryable, _ = _classify_read_failure(
        _ReadUrlFailure("403 Forbidden", status_code=403)
    )
    assert cls == "BLOCKED_BY_TARGET"
    assert retryable is False


def test_connection_error_is_network_fail():
    cls, retryable, _ = _classify_read_failure(
        _ReadUrlFailure("Page.goto: net::ERR_CONNECTION_CLOSED")
    )
    assert cls == "NETWORK_FAIL"
    assert retryable is True


def test_timeout_is_network_fail():
    cls, retryable, _ = _classify_read_failure(
        _ReadUrlFailure("Page.goto: Timeout 60000ms exceeded.")
    )
    assert cls == "NETWORK_FAIL"
    assert retryable is True


def test_short_login_page_is_blocked():
    assert _classify_content("Sign in to continue to your account") == "BLOCKED_BY_TARGET"


def test_short_blocked_page_is_blocked():
    assert _classify_content("You've been blocked by network security") == "BLOCKED_BY_TARGET"


def test_empty_content():
    assert _classify_content("   ") == "EMPTY_CONTENT"


def test_normal_content_is_not_classified():
    text = "Fusion power is a proposed form of power generation. " * 40
    assert _classify_content(text) is None
