"""Pluggable reranking interface for search results.

Provides a hook for LLM-based or cross-encoder-based reranking after
RRF fusion. Enabled via ``CRAWL4AI_RERANKER`` env var.

Supported backends:
- ``none`` (default): no reranking
- ``token``: lightweight token-overlap scoring (stdlib only)
- ``cross-encoder``: uses sentence-transformers if installed
"""

from __future__ import annotations

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _token_relevance(query: str, result: Dict[str, Any]) -> float:
    """Token-overlap relevance score (title=3, snippet=1)."""
    terms = set(query.strip().lower().split())
    if not terms:
        return 0.0
    title = (result.get("title") or "").lower()
    snippet = (result.get("snippet") or "").lower()
    score = 0.0
    for t in terms:
        if len(t) < 2:
            continue
        if t in title:
            score += 3.0
        if t in snippet:
            score += 1.0
    return score


class Reranker(ABC):
    """Abstract reranking interface."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Rerank *results* for *query*, return top *top_k*."""
        ...


class NoopReranker(Reranker):
    """Pass-through reranker — no-op."""

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        return results[:top_k]


class TokenReranker(Reranker):
    """Lightweight token-overlap reranker (stdlib only)."""

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        if not results:
            return results[:top_k]

        scored = [
            (_token_relevance(query, r), r) for r in results
        ]
        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:top_k]]


class CrossEncoderReranker(Reranker):
    """Cross-encoder reranker using sentence-transformers.

    Lazily loads the model on first use. Requires the
    ``sentence-transformers`` package.
    """

    _model = None

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name

    def _ensure_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self.__class__._model = CrossEncoder(self.model_name)
                logger.info("Loaded cross-encoder model: %s", self.model_name)
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed; "
                    "cross-encoder reranking disabled"
                )
                self.__class__._model = False  # type: ignore[assignment]

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        if not results:
            return results[:top_k]

        self._ensure_model()
        if self._model is False:
            return results[:top_k]

        pairs = [
            [query, f"{r.get('title', '')} {r.get('snippet', '')}"]
            for r in results
        ]
        scores = await asyncio.to_thread(self._model.predict, pairs)
        scored = list(zip(scores, results))
        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:top_k]]


def get_reranker() -> Reranker:
    """Factory: return reranker based on env config."""
    name = (os.environ.get("CRAWL4AI_RERANKER") or "none").strip().lower()
    if name in {"", "none", "off"}:
        return NoopReranker()
    if name == "token":
        return TokenReranker()
    if name in {"cross-encoder", "cross_encoder", "ce"}:
        model = os.environ.get("CRAWL4AI_RERANKER_MODEL", "")
        return CrossEncoderReranker(model) if model else CrossEncoderReranker()
    logger.warning("Unknown reranker '%s'; using noop", name)
    return NoopReranker()
