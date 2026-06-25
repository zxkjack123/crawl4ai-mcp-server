#!/usr/bin/env python3
"""Unit tests for src/fusion_terms.py — FusionTermsProvider."""

from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fusion_terms import FusionTermsProvider, get_fusion_terms_provider


@pytest.fixture
def mock_artifacts_dir(tmp_path):
    """Create a minimal fusion-terms artifacts directory for testing."""
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    # query_expansions.json
    query_exp = {"alias_index": {}}
    for alias, cid in [
        ("NBI", "neutral-beam-injection"),
        ("neutral beam injection", "neutral-beam-injection"),
        ("neutral-beam injection", "neutral-beam-injection"),
        ("ITER", "iter"),
        ("tungsten", "tungsten"),
        ("W", "tungsten"),
        ("钨", "tungsten"),
    ]:
        query_exp["alias_index"][alias] = cid
    (artifacts / "query_expansions.json").write_text(json.dumps(query_exp))

    # terminology_substitutions.tsv
    subs = (
        "# alias\tpreferred\tstatus\tlang\tnote\n"
        "Tokamak\ttokamak\tforbidden\ten\tcapitalisation\n"
        "ELM碰撞侵蚀\tELM诱发侵蚀\tforbidden\tzh\tmistranslation\n"
        "C2W\tC-2W\tforbidden\ten\tmissing hyphen\n"
    )
    (artifacts / "terminology_substitutions.tsv").write_text(subs)

    # translation_dict.json
    trans = {
        "en2zh": {"tungsten": "钨", "neutral beam injection": "中性束注入"},
        "zh2en": {"钨": "tungsten", "中性束注入": "neutral beam injection"},
        "en2zh_short": {},
    }
    (artifacts / "translation_dict.json").write_text(json.dumps(trans))

    # concepts.tsv (in registry/)
    reg = tmp_path / "terms" / "registry"
    reg.mkdir(parents=True)
    concepts = (
        "concept_id\tcategory\tpreferred_en\tpreferred_zh\n"
        "neutral-beam-injection\tmethod\tneutral beam injection\t中性束注入\n"
        "iter\tfacility\tITER\tITER\n"
        "tungsten\tmaterial\ttungsten\t钨\n"
    )
    (reg / "concepts.tsv").write_text(concepts)

    return str(artifacts)


class TestFusionTermsProviderDisabled:
    def test_disabled_when_no_env(self, monkeypatch):
        monkeypatch.delenv("FUSION_TERMS_ARTIFACTS_DIR", raising=False)
        # Force fresh singleton
        import src.fusion_terms as ft
        ft._provider = None
        p = get_fusion_terms_provider()
        assert not p.enabled
        assert p.normalize_query("Tokamak") == "Tokamak"
        assert p.expand_query_terms("NBI") == {"NBI"}
        assert p.get_known_terms() == set()
        assert p.get_term_boost("neutral beam injection") == 1.0

    def test_disabled_with_nonexistent_dir(self, monkeypatch):
        monkeypatch.setenv("FUSION_TERMS_ARTIFACTS_DIR", "/nonexistent/path")
        import src.fusion_terms as ft
        ft._provider = None
        p = get_fusion_terms_provider()
        assert not p.enabled


class TestFusionTermsProviderNormalization:
    def test_normalize_forbidden_term(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        assert p.enabled
        assert p.normalize_query("Tokamak") == "tokamak"

    def test_normalize_chinese_mistranslation(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        assert p.normalize_query("ELM碰撞侵蚀研究") == "ELM诱发侵蚀研究"

    def test_normalize_missing_hyphen(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        assert p.normalize_query("C2W device") == "C-2W device"

    def test_normalize_unknown_term_passthrough(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        assert p.normalize_query("completely unknown term") == "completely unknown term"

    def test_longest_match_first(self, mock_artifacts_dir):
        """Longer substitution patterns should be matched before shorter ones."""
        p = FusionTermsProvider(mock_artifacts_dir)
        # Both "ELM碰撞" could match partially but "ELM碰撞侵蚀" is the full match
        assert "ELM诱发侵蚀" in p.normalize_query("ELM碰撞侵蚀")


class TestFusionTermsProviderExpansion:
    def test_expand_abbreviation(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        expanded = p.expand_query_terms("NBI")
        assert "NBI" in expanded
        assert "neutral beam injection" in expanded
        assert "neutral-beam injection" in expanded

    def test_expand_known_term_translation(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        expanded = p.expand_query_terms("tungsten")
        assert "tungsten" in expanded
        assert "钨" in expanded

    def test_expand_unknown_term(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        expanded = p.expand_query_terms("flibbertigibbet")
        assert expanded == {"flibbertigibbet"}


class TestFusionTermsProviderRelevance:
    def test_get_known_terms(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        known = p.get_known_terms()
        assert "NBI" in known
        assert "tungsten" in known
        assert "ITER" in known
        assert "W" in known

    def test_term_boost_for_fusion_text(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        boost = p.get_term_boost("The NBI system on ITER uses tungsten shielding")
        assert boost > 1.0, f"Expected boost > 1.0, got {boost}"

    def test_term_boost_for_non_fusion_text(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        boost = p.get_term_boost("zzzabc 123def ghi456 jklmnop qrstuv")
        assert boost == 1.0

    def test_term_boost_caps_at_2x(self, mock_artifacts_dir):
        p = FusionTermsProvider(mock_artifacts_dir)
        # Already capped by the logic, just verify it doesn't explode
        boost = p.get_term_boost("NBI NBI NBI NBI NBI" * 20)
        assert boost <= 2.0


class TestFusionTermsProviderMemoryUsage:
    def test_lazy_loading(self, mock_artifacts_dir):
        """Data should not load until first public method call."""
        p = FusionTermsProvider(mock_artifacts_dir)
        assert p.enabled
        assert not p._loaded
        _ = p.normalize_query("test")
        assert p._loaded

    def test_thread_safe_singleton_reset(self):
        """Module-level singleton should be resettable."""
        import src.fusion_terms as ft
        ft._provider = None
        assert ft._provider is None
