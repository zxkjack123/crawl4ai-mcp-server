"""Fusion domain terminology provider.

Reads fusion-terms artifact files from a configurable directory and exposes
methods for query enhancement, term normalization, and relevance scoring.
The provider is a pure data consumer — it does not import any fusion-terms
Python modules, only reads its static data artifacts.

Configuration:
    ``FUSION_TERMS_ARTIFACTS_DIR`` — path to the fusion-terms ``artifacts/``
    directory (and optionally ``terms/registry/``).  When unset the provider
    is a transparent no-op.

Data files consumed (all optional — missing files are skipped gracefully):
    query_expansions.json          alias → concept_id index
    translation_dict.json          zh ↔ en translation pairs
    terminology_substitutions.tsv  forbidden/deprecated → preferred
    tag_rules.jsonl                per-concept tagging rules
    concepts.tsv                   concept metadata (category, preferred name)
"""

from __future__ import annotations

import csv
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

# ── data containers ──────────────────────────────────────────────────────────

_Data = Dict[str, Any]

# ── public API ──────────────────────────────────────────────────────────────


class FusionTermsProvider:
    """Encapsulates loaded fusion-terms data and exposes query-enhancement APIs.

    Thread-safe after initial load.  All public methods are idempotent and never
    raise — errors are logged and the method degrades to a pass-through.
    """

    def __init__(self, artifacts_dir: Optional[str] = None):
        self._artifacts_dir: Optional[str] = None
        self._registry_dir: Optional[str] = None
        if artifacts_dir:
            d = os.path.expanduser(str(artifacts_dir))
            if os.path.isdir(d):
                self._artifacts_dir = d
                reg = os.path.join(d, "..", "terms", "registry")
                if os.path.isdir(reg):
                    self._registry_dir = reg
        self._loaded = False
        self._lock = threading.Lock()

        # ── data, populated by _ensure_loaded ──────────────────────────────
        self._alias_to_concept: Dict[str, str] = {}  # alias → concept_id
        self._concept_aliases: Dict[str, List[str]] = {}  # concept_id → [alias]
        self._substitutions: Dict[str, str] = {}  # forbidden/deprecated → preferred
        self._translations: Dict[str, str] = {}  # en→zh or zh→en (bidirectional)
        self._concept_category: Dict[str, str] = {}  # concept_id → category
        self._concept_pref_en: Dict[str, str] = {}  # concept_id → preferred_en
        self._concept_pref_zh: Dict[str, str] = {}  # concept_id → preferred_zh
        self._enabled = bool(self._artifacts_dir)

    # ── public methods ──────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return self._enabled

    def normalize_query(self, query: str) -> str:
        """Apply forbidden→preferred term corrections to *query*.

        Returns the original query when the provider is disabled.
        """
        if not self._enabled:
            return query
        self._ensure_loaded()
        if not self._substitutions:
            return query

        # Apply longest-match-first to avoid partial substitutions.
        # e.g. "ELM碰撞侵蚀" → "ELM诱发侵蚀" (not "ELM" first)
        sorted_keys = sorted(self._substitutions.keys(), key=len, reverse=True)
        result = query
        for alias in sorted_keys:
            if alias in result:
                result = result.replace(alias, self._substitutions[alias])
        return result

    def expand_query_terms(self, query: str) -> Set[str]:
        """Return expanded term variants to enrich search relevance scoring.

        For a query like "NBI", returns {"NBI", "neutral beam injection",
        "中性束注入"} — the original query plus known synonyms/translations.
        """
        if not self._enabled:
            return {query}
        self._ensure_loaded()

        terms: Set[str] = {query}
        norm = query.strip()

        # Direct alias lookup
        cid = self._alias_to_concept.get(norm)
        if not cid:
            cid = self._alias_to_concept.get(norm.lower())

        if cid:
            aliases = self._concept_aliases.get(cid, [])
            terms.update(aliases)

        # Translation lookup
        tr = self._translations.get(norm)
        if tr:
            terms.add(tr)
        tr_lower = self._translations.get(norm.lower())
        if tr_lower and tr_lower != tr:
            terms.add(tr_lower)

        return terms

    def get_known_terms(self) -> Set[str]:
        """Return the set of all known fusion-domain terms (aliases + preferred).

        Used for relevance scoring: results containing these terms get a boost.
        """
        if not self._enabled:
            return set()
        self._ensure_loaded()
        return set(self._alias_to_concept.keys())

    def get_term_boost(self, text: str) -> float:
        """Return a relevance boost multiplier for *text* based on fusion terminology.

        Higher boost when *text* contains known fusion terms.
        """
        if not self._enabled:
            return 1.0
        self._ensure_loaded()
        if not self._alias_to_concept:
            return 1.0

        lower = text.lower()
        unique_concepts: Set[str] = set()
        for alias, cid in self._alias_to_concept.items():
            if alias.lower() in lower:
                unique_concepts.add(cid)

        if not unique_concepts:
            return 1.0

        # Weight by concept count; cap at 2.0x to avoid over-boosting
        return min(2.0, 1.0 + len(unique_concepts) * 0.1)

    def get_facility_domains(self) -> Dict[str, float]:
        """Return known fusion facility domains suitable for domain boosting.

        Derived from concepts with category='facility' or organization-like names.
        """
        if not self._enabled:
            return {}
        self._ensure_loaded()

        boosts: Dict[str, float] = {}
        known_facilities = {
            "iter": "iter.org",
            "jet": "euro-fusion.org",
            "diii-d": "ga.com",
            "kstar": "nfri.re.kr",
            "east": "ipp.ac.cn",
            "west": "cea.fr",
            "jt-60sa": "qst.go.jp",
            "asdex": "ipp.mpg.de",
            "nstx": "pppl.gov",
            "lhd": "nifs.ac.jp",
            "stellarator": "ipp.mpg.de",
            "cfetr": "ipp.ac.cn",
            "demo": "euro-fusion.org",
        }
        for concept_id, domain in known_facilities.items():
            if concept_id in self._concept_aliases:
                boosts[domain] = 1.15

        return boosts

    # ── internal ─────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load()
            self._loaded = True

    def _load(self) -> None:
        d = self._artifacts_dir
        if not d:
            return

        self._load_query_expansions(d)
        self._load_substitutions(d)
        self._load_translations(d)
        self._load_concepts()

        logger.info(
            "FusionTermsProvider loaded: %d aliases, %d concepts, "
            "%d substitutions, %d translations",
            len(self._alias_to_concept),
            len(self._concept_aliases),
            len(self._substitutions),
            len(self._translations),
        )

    def _load_query_expansions(self, artifacts_dir: str) -> None:
        path = os.path.join(artifacts_dir, "query_expansions.json")
        if not os.path.isfile(path):
            logger.debug("query_expansions.json not found at %s", path)
            return
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            ai = data.get("alias_index", {})
            for alias, concept_id in ai.items():
                alias_str = str(alias).strip()
                cid = str(concept_id).strip()
                if alias_str and cid:
                    self._alias_to_concept[alias_str] = cid
                    self._concept_aliases.setdefault(cid, []).append(alias_str)
        except Exception as exc:
            logger.warning("Failed to load query_expansions.json: %s", exc)

    def _load_substitutions(self, artifacts_dir: str) -> None:
        path = os.path.join(artifacts_dir, "terminology_substitutions.tsv")
        if not os.path.isfile(path):
            logger.debug("terminology_substitutions.tsv not found at %s", path)
            return
        try:
            with open(path, encoding="utf-8") as fh:
                reader = csv.reader(fh, delimiter="\t")
                for row in reader:
                    if not row or row[0].startswith("#"):
                        continue
                    if len(row) < 2:
                        continue
                    alias = row[0].strip()
                    preferred = row[1].strip()
                    if alias and preferred and alias != preferred:
                        self._substitutions[alias] = preferred
        except Exception as exc:
            logger.warning("Failed to load substitutions: %s", exc)

    def _load_translations(self, artifacts_dir: str) -> None:
        path = os.path.join(artifacts_dir, "translation_dict.json")
        if not os.path.isfile(path):
            logger.debug("translation_dict.json not found at %s", path)
            return
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            # en2zh
            for en, zh in data.get("en2zh", {}).items():
                if en and zh:
                    self._translations[str(en).strip()] = str(zh).strip()
            # zh2en
            for zh, en in data.get("zh2en", {}).items():
                if zh and en:
                    self._translations[str(zh).strip()] = str(en).strip()
        except Exception as exc:
            logger.warning("Failed to load translation_dict: %s", exc)

    def _load_concepts(self) -> None:
        if not self._registry_dir:
            return
        path = os.path.join(self._registry_dir, "concepts.tsv")
        if not os.path.isfile(path):
            return
        try:
            with open(path, encoding="utf-8") as fh:
                reader = csv.DictReader(fh, delimiter="\t")
                for row in reader:
                    cid = (row.get("concept_id") or "").strip()
                    if not cid:
                        continue
                    cat = (row.get("category") or "").strip()
                    if cat:
                        self._concept_category[cid] = cat
                    pref_en = (row.get("preferred_en") or "").strip()
                    if pref_en:
                        self._concept_pref_en[cid] = pref_en
                    pref_zh = (row.get("preferred_zh") or "").strip()
                    if pref_zh:
                        self._concept_pref_zh[cid] = pref_zh
        except Exception as exc:
            logger.warning("Failed to load concepts.tsv: %s", exc)


# ── module-level singleton ───────────────────────────────────────────────────

_provider: Optional[FusionTermsProvider] = None
_provider_lock = threading.Lock()


def get_fusion_terms_provider() -> FusionTermsProvider:
    """Return the module-level FusionTermsProvider singleton.

    Configured via ``FUSION_TERMS_ARTIFACTS_DIR`` env var.  Returns a no-op
    provider when the env var is unset or the directory does not exist.
    """
    global _provider
    if _provider is not None:
        return _provider
    with _provider_lock:
        if _provider is not None:
            return _provider
        artifacts_dir = os.environ.get("FUSION_TERMS_ARTIFACTS_DIR", "")
        _provider = FusionTermsProvider(artifacts_dir or None)
        return _provider
