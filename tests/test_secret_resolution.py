#!/usr/bin/env python3
"""Unit tests for placeholder-aware secret resolution."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search import _resolve_secret


def test_resolve_secret_env_wins_over_config():
    assert _resolve_secret("CONFIG_VALUE", "ENV_VALUE") == "ENV_VALUE"


def test_resolve_secret_ignores_placeholders():
    assert _resolve_secret("YOUR_GOOGLE_API_KEY_HERE", None) is None
    assert _resolve_secret("YOUR_CUSTOM_SEARCH_ENGINE_ID_HERE", None) is None
    assert _resolve_secret("your-google-api-key-here", None) is None
    assert _resolve_secret("  YOUR_BRAVE_API_KEY  ", None) is None


def test_resolve_secret_accepts_real_strings():
    assert _resolve_secret("real", None) == "real"
    assert _resolve_secret("  real  ", None) == "real"


def test_resolve_secret_empty_is_none():
    assert _resolve_secret("", None) is None
    assert _resolve_secret("   ", None) is None
    assert _resolve_secret(None, "") is None


def test_resolve_secret_env_placeholder_does_not_override_config():
    # If env is set but is a placeholder, we should fall back to config.
    assert _resolve_secret("CONFIG_VALUE", "YOUR_GOOGLE_API_KEY") == "CONFIG_VALUE"
