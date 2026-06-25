# Crawl4AI MCP Server — AI Context Document (v0.7.0)

Multi-engine search + LLM-optimised web crawling MCP server.  Provides
`search`, `read_url`, `system_status`, `manage_cache`, and
`export_search_results` tools over MCP stdio or a FastAPI HTTP bridge.

## Source Layout

| File / Dir | Role |
|---|---|
| `src/index.py` | FastMCP app — registers 5 tools, orchestrates crawler + search |
| `src/search.py` | `SearchManager` (2,400+ lines) — multi-engine concurrency, RRF fusion, caching, circuit-breakers, bulkheads, query expansion |
| `src/rest_server.py` | FastAPI HTTP bridge (`/health`, `/search`, `/read_url`) with auth, rate limiting, request-id tracing |
| `src/utils.py` | `merge_and_deduplicate`, `canonicalize_url`, RRF scoring, relevance blending, title-based dedup |
| `src/cache.py` | In-memory LRU search cache |
| `src/persistent_cache.py` | SQLite persistent cache (WAL, thread-local connection) |
| `src/circuit_breaker.py` | Per-engine circuit breaker (CLOSED/OPEN/HALF_OPEN) |
| `src/compat.py` | `asyncio.timeout` polyfill for Python 3.10 |
| `src/fusion_terms.py` | Fusion/nuclear terminology provider — reads fusion-terms artifacts for query normalisation + relevance boost |
| `src/reranker.py` | Pluggable reranker (noop/token/cross-encoder) |
| `src/monitor.py` | Search metrics collector |
| `src/request_context.py` | Request-id context propagation |
| `src/retrieval_eval.py` | Golden-case retrieval evaluation |
| `docker/` | Dockerfile, compose (searxng + crawl4ai-http + autoheal), entrypoint, healthcheck |
| `tests/` | 70+ tests, 18 test modules |
| `.env.example` | 316-line config reference — **definitive** source for all env vars |

## Tools

### `search(query, num_results=10, engine="auto")`
Multi-engine concurrent search with RRF fusion.
- **Engines**: DuckDuckGo (free, no key), Google CSE, Brave, SearXNG
- **engine="auto"**: concurrent auto-merge across top 3 engines (default)
- **engine="all"**: all available engines, RRF merge
- **Fusion**: adaptive RRF k, default per-engine weights (google=1.0, brave=0.9, searxng=0.7, ddg=0.4), domain authority boosts, post-merge relevance scoring, title-based dedup
- **Infra**: negative caching, query-normalised cache keys, circuit breakers, token-bucket rate limiting, bulkhead concurrency, request coalescing, deadline-aware early return

### `read_url(url, format="markdown_with_citations")`
Crawls a URL via headless browser and returns LLM-optimised Markdown.
- **Formats**: raw_markdown, markdown_with_citations, references_markdown, fit_markdown, fit_html, markdown
- **Content cleaning**: excludes nav/footer/header/aside/script/style/noscript/iframe/form, `word_count_threshold=5`
- **Proxy**: direct-first with proxy fallback on network errors

### `system_status(check_type="health")`
Health, readiness, and metrics endpoints.

### `manage_cache(action="stats")`
Cache management: stats, clear, export, cleanup, vacuum.

### `export_search_results(query, ...)`
Export search results to JSON file.

## Key Configuration (env vars)

See `.env.example` for the complete reference.  Critical ones:

| Variable | Default | Notes |
|---|---|---|
| `GOOGLE_API_KEY` / `GOOGLE_CSE_ID` | — | Google CSE (optional) |
| `BRAVE_API_KEY` | — | Brave Search (optional) |
| `SEARXNG_BASE_URL` | `http://localhost:28981` | SearXNG instance (optional) |
| `CRAWL4AI_AUTO_MERGE` | `1` | Enable concurrent auto-merge |
| `CRAWL4AI_RRF_K` | `60` | RRF k (adaptive at runtime) |
| `CRAWL4AI_CACHE_BACKEND` | `memory` | `memory` or `persistent` (SQLite) |
| `CRAWL4AI_RERANKER` | `none` | `none`, `token`, or `cross-encoder` |
| `FUSION_TERMS_ARTIFACTS_DIR` | — | Path to fusion-terms artifacts for domain retrieval |

## Environment

- **Python**: >= 3.10
- **Key deps**: `crawl4ai>=0.7.7,<0.8`, `playwright>=1.56.0,<2.0`, `mcp>=1.12.0,<2.0`, `fastapi>=0.115.0,<1.0`

## Entry Points

- **MCP server**: `python -m src.index` or `scripts/run_mcp_with_env.sh`
- **HTTP bridge**: `docker compose up` (port 18080) or `python -m src.rest_server`
- **Docker**: `make docker-build && make docker-up`

## Testing

```bash
pytest tests/ -v --tb=short
# Skip live-engine tests with:
pytest tests/ -v --tb=short -k "not (search_llm or google_api or concurrent_search or searxng or brave)"
```

## Version History

- **v0.7.0** (2026-06-24): Python 3.10 compat, deep healthcheck, CI matrix
- **v0.7.0-dev** (unreleased): 14 search quality improvements, fusion-terms integration
- **v0.6.1** (2026-01-26): Domain authority boost, request-id, circuit breaker
- **v0.6.0** (2025-12-03): crawl4ai 0.7.7, playwright 1.56.0, proxy retry
