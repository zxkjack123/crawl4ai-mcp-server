# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2026-06-25

### Added
- **14 Search Retrieval Improvements**:
  - Default engine weights for RRF (google=1.0, brave=0.9, searxng=0.7, ddg=0.4) — prevents low-quality engines from diluting results
  - Concurrent auto-merge enabled by default — P99 latency from sum-of-failures to max-of-concurrent
  - Negative caching — empty results cached with 60s TTL, stops repeated upstream calls for failing queries
  - Query normalization for cache keys — strip/lowercase/collapse whitespace so equivalent queries share cache entries
  - Adaptive RRF k — uses k = max_rank//2 for small result sets, preserving score differentiation
  - Default domain boosts — pre-configured fusion/nuclear authority sites (iter.org, iaea.org, etc.)
  - Post-merge relevance scoring — blends token-overlap score with RRF (alpha=0.7)
  - Fetch 2x candidates per engine — gives RRF a larger fusion pool before trimming
  - Title-based near-duplicate removal — catches mirror sites, AMP vs non-AMP URLs
  - URL canonicalization improvements — sort query params, strip session IDs, normalize mobile/AMP subdomains
  - SQLite connection reuse — thread-local persistent connection with WAL mode
  - read_url content cleaning — lowered word_count_threshold to 5, excluded more noise tags
  - Pluggable reranker — `src/reranker.py` with NoopReranker, TokenReranker, CrossEncoderReranker; env `CRAWL4AI_RERANKER`
  - Deadline-aware early return — uses 30% of remaining time budget as adaptive grace period
- **Fusion Terms Integration** (`src/fusion_terms.py`): Reads fusion-terms static data artifacts for domain retrieval quality:
  - Query normalization: forbidden→preferred term corrections (e.g. `Tokamak`→`tokamak`, `ELM碰撞侵蚀`→`ELM诱发侵蚀`)
  - Query expansion: abbreviation→full name + zh↔en translation for relevance scoring
  - Term-aware relevance boost: results containing known fusion terms get up to 2.0x position-weighted boost
  - Facility domain boosts from known fusion facilities
  - Configured via `FUSION_TERMS_ARTIFACTS_DIR` env var; no-op when unset
- **Tests**: 16 FusionTermsProvider unit tests, 2 import path fixes, 3 test deadline adjustments for deadline-aware early return

### Changed
- **Dockerfile HEALTHCHECK**: Parameters aligned with docker-compose.yml (30s/10s/40s → 60s/30s/60s)
- **Dependencies**: Upper bounds added to all 15 deps in `requirements.txt` and `pyproject.toml`; `pyproject.toml` synced with full runtime+dev deps; `requires-python` bumped to `>=3.10`
- **Version**: Unified to single source (pyproject.toml, index.py ×4, rest_server.py) at 0.7.0, now 0.8.0

### Fixed
- **Documentation**:
  - Deleted stale `docs/README.md` (v2025.02 duplicate)
  - Rewrote `docs/PROJ_INFO_4AI.md` with current v0.8.0 engines, versions, module layout
  - Fixed `docs/DEPLOYMENT_GUIDE.md`: Python 3.9→3.10, `config_demo.json`→`config.example.json`, added Brave/SearXNG
  - Fixed `README.md`: Python version 3.9→3.10
  - Added `FUSION_TERMS_ARTIFACTS_DIR` to `.env.example`
  - Updated `smithery.yaml`: all keys now optional, added Brave/SearXNG
  - Moved 11 historical docs to `docs/archive/`

## [0.7.0] - 2026-06-24

### Added
- **Python 3.10 Compatibility**: Extracted `asyncio.timeout` polyfill into `src/compat.py`, imported uniformly by both `rest_server.py` and `search.py`. Previously `search.py` used `asyncio.timeout` without polyfill protection, causing `AttributeError` on Python 3.10.
- **Healthcheck Shell Integration Tests**: Added `tests/test_healthcheck.sh` with mock HTTP server (`tests/mock_http_server.py`) covering healthy server, `/health` down, `/read_url` error, and `/read_url` empty response scenarios.
- **Polyfill Unit Tests**: Added `tests/test_compat.py` with 6 tests covering normal completion, timeout firing, handle cleanup, and polyfill-vs-builtin semantic parity.
- **CI Matrix**: Added `.github/workflows/ci.yml` with Python 3.10/3.11/3.12 matrix, dedicated compat shim verification job, and shell healthcheck test step.

### Changed
- **Docker Healthcheck**: Deepened `docker/healthcheck.sh` to not only check `/health` liveness but also verify browser/crawl functionality via `/read_url` against `example.com`. Tuned `docker-compose.yml` healthcheck intervals (60s/30s/60s) and added `autoheal` container for automatic restart of unhealthy services.
- **Dockerfile HEALTHCHECK**: Existing `HEALTHCHECK` directive parameters should be updated to match `docker-compose.yml` (currently still at 30s/10s/40s).

## [0.6.1] - 2026-01-26

### Added
- **Domain Authority Boosting (RRF)**: Optional per-domain score multiplier for the RRF fusion path, configurable via `CRAWL4AI_DOMAIN_BOOSTS` (exact host + suffix match, `www.` normalized).
- **Request ID Propagation**: End-to-end request-id support (context + logs + HTTP headers) to improve traceability in concurrent workloads.
- **Engine Circuit Breaker**: Per-engine circuit breaker (CLOSED/OPEN/HALF_OPEN) to reduce cascading failures and improve stability.
- **Golden Query Evaluation**: Golden-case runner + scoring and baseline compare utilities to track relevance regression over time.

### Changed
- **Runtime Tuning via .env**: Search timeouts, bulkhead concurrency limits, engine weights, and domain boosts are now configurable via env in both Docker and host MCP workflows.
- **Host MCP Launch (Linux-friendly)**: Added a wrapper script to source `.env` and run MCP mode reliably even when Docker-only hostnames (e.g. `host.docker.internal`) are present in proxy settings.

### Fixed
- **Multi-engine Fusion Early-Return**: Improved concurrent early-return behavior for multi-engine search to reduce tail latency while preserving merge quality.

## [0.6.0] - 2025-12-03

### Added
- **Dependency Upgrade**: Upgraded `Crawl4AI` to v0.7.7 and `Playwright` to v1.56.0.
- **Proxy Retry Logic**: Implemented robust retry mechanism for `read_url`. If a direct connection fails (e.g., blocked by firewall), the system automatically retries using the configured proxy.
- **Markdown V2 Support**: Added native support for `markdown_v2` structured output from Crawl4AI v0.7.x, ensuring better compatibility and richer content extraction.
- **Concurrency Safety**: Added `asyncio.Lock` to initialization routines (`initialize_crawler`, `initialize_search_manager`) to prevent race conditions during high concurrency.

### Changed
- **Docker Base Image**: Updated Dockerfile to install fresh browser binaries compatible with Playwright v1.56.0.
- **Error Handling**: Improved error messages for missing content or initialization failures.
- **Version Bump**: Project version updated to 0.6.0.

### Fixed
- **Proxy Connection**: Resolved `net::ERR_PROXY_CONNECTION_FAILED` by ensuring the host proxy binds to `0.0.0.0` and the container uses `host.docker.internal`.
- **Markdown Extraction**: Fixed `AttributeError` when accessing `markdown_v2` on older library versions (now fully upgraded).

## [0.5.10] - 2025-11-26

### Added
- 🧩 VS Code 集成文档现在包含完整的 MCP 配置示例,明确区分 **容器内 HTTP Bridge** (`SEARXNG_BASE_URL=http://searxng:8080`) 与 **宿主机直连 MCP 服务器** (`SEARXNG_BASE_URL=http://localhost:28981`, `SERVER_MODE=mcp`), 确保 Copilot 使用 MCP 时与 HTTP `/search` 行为保持一致。

### Changed
- 🧪 并发搜索集成测试(`tests/test_concurrent_search.py`)在所有引擎均返回空结果(例如: CI / 离线环境或未启动 SearXNG)时,会自动 **skip** 而不是失败,避免把网络/环境问题误判为功能回归;在至少一个引擎可用时,仍严格校验行为。

### Tested
- ✅ `.venv/bin/pytest -q` — 75 tests 通过,2 个并发搜索集成测试在无可用搜索引擎时被自动跳过(离线环境),在实际在线环境中仍会完整执行。

## [0.5.9] - 2025-11-19

### Added
- 📡 Finalized the FastAPI HTTP bridge (`src/rest_server.py`) with dedicated smoke and integration tests, so external services can rely on `/health`, `/search`, and `/read_url` just like MCP tools.

### Changed
- 🔧 Default SearXNG host binding now uses port `28981` (instead of `8080`) to avoid conflicts with services like Dify; all docs, examples, and config defaults were updated accordingly.
- 🐳 Makefile + Docker Compose workflows now document the bridged ports (`18080/28981`) and inherit `.env` proxy/API settings for zero-config deployments.
- 📝 README release highlights bumped to v0.5.9, emphasizing the new HTTP workflow and SearXNG port guidance.

### Tested
- ✅ `.venv/bin/pytest` — 77 tests passed in 1567s on Linux (Python 3.12.3).

## [0.5.5] - 2025-10-12

### Tested
- ✅ **Continuous validation** - All tests passing
- ✅ Unit tests: 21/21 passed (0.96s)
- ✅ Persistent cache: 7/7 passed (4.27s)
- ✅ Health checks: 4/4 passed
- ✅ Export functionality: 4/4 passed (6.63s)
- **Total: 36/36 tests passing** (100% success rate)

### Maintenance
- Regular cleanup of Python cache files
- Test artifacts cleaned
- Confirmed stability after v0.5.3-0.5.4 tool consolidation

## [0.5.4] - 2025-10-11

### Tested
- ✅ **Full test suite validation** after tool consolidation
- ✅ Unit tests: 21/21 passed (100%)
- ✅ Persistent cache: 7/7 passed (100%)
- ✅ Health checks: 4/4 passed (100%) - including new `check_type="all"`
- ✅ Export functionality: 4/4 passed (100%)
- **Total: 36/36 tests passing** (100% success rate)

### Verified
- Tool consolidation working correctly
- All `system_status` check types functioning: health, readiness, metrics, all
- No regressions from v0.5.3 changes
- Cache persistence maintained
- Export functionality intact

## [0.5.3] - 2025-10-11

### Changed
- ♻️ **Tool Consolidation**: Reduced MCP tool count from 7 to 5 (29% reduction)
- Merged 3 monitoring tools into unified `system_status` tool:
  - `health_check` → `system_status(check_type="health")`
  - `readiness_check` → `system_status(check_type="readiness")`
  - `metrics` → `system_status(check_type="metrics")`
  - New `check_type="all"` returns all checks in one call

### Benefits
- **Copilot Compatibility**: Better fits within Copilot's 128-tool limit
- **Simpler API**: One endpoint for all monitoring needs
- **Backward Compatible**: All original data structures preserved
- **More Flexible**: `check_type="all"` enables comprehensive health checks

### Current Tools (5)
1. `read_url` - Crawl and read webpage content
2. `search` - Search the web using multiple engines
3. `system_status` - **NEW** Unified system monitoring (health/readiness/metrics)
4. `manage_cache` - Cache management operations
5. `export_search_results` - Export search results to JSON

### Tested
- ✅ All 4 check types verified: health, readiness, metrics, all
- ✅ Updated test suite: `tests/test_health_checks.py` (4/4 tests passing)
- ✅ No functionality loss - all original data structures maintained

## [0.5.2] - 2025-10-11

### Fixed
- **Critical**: Fixed ModuleNotFoundError preventing MCP server startup
- Fixed import errors in `src/index.py` - changed from absolute to relative/fallback imports
- Fixed cascading import errors in `src/search.py` for cache, utils, and monitor modules
- All modules now use try/except pattern for imports (relative → direct fallback)

### Added
- Comprehensive test results documentation (`docs/TEST_RESULTS_v0.5.2.md`)
- Full test suite execution with 35/35 tests passing

### Tested
- ✅ Unit tests: 21/21 passed (81% coverage)
- ✅ Persistent cache: 7/7 passed
- ✅ Health checks: 3/3 passed
- ✅ Export functionality: 4/4 passed

### Technical Details
**Import Pattern**:
```python
try:
    from .module import Class  # Relative import
except ImportError:
    from module import Class   # Direct import fallback
```

This ensures compatibility with:
- MCP Server execution context
- Direct Python script execution
- Test runner execution
- Module imports

---

## [0.5.1] - 2025-10-11

### Changed
- Updated README.md with v0.5.0 feature highlights
- Improved feature organization and documentation
- Added link to full CHANGELOG in README

### Fixed
- Removed .coverage from git tracking
- Added coverage reports to .gitignore
- Cleaned up Python cache files

---

## [0.5.0] - 2025-10-11

### Added

#### Priority 5: Cache Persistence ⭐⭐⭐⭐⭐
- **PersistentCache Class** (600+ lines)
  - SQLite-based persistent storage with cross-session support
  - Dual-layer caching architecture (memory + database)
  - LRU automatic eviction strategy when reaching max_size
  - TTL expiration mechanism (default 3600 seconds)
  - Cache warmup functionality for pre-population
  - JSON export/import capabilities with full metadata
  - Database optimization with VACUUM command
  - 75% performance improvement with memory cache layer (0.04ms → 0.01ms)

- **MCP Cache Management Tool** (`manage_cache`)
  - 5 operations: stats, clear, export, cleanup, vacuum
  - Unified JSON response format
  - Support for both in-memory and persistent cache backends

- **Comprehensive Testing**
  - 7 test cases with 100% pass rate
  - Tests cover: persistence, expiration, export/import, LRU eviction, memory cache, cleanup
  - Cross-session data recovery validated

#### Priority 6: Unit Test Coverage ⭐⭐⭐⭐
- **Unit Test Suite** (320+ lines)
  - 21 unit tests with 100% pass rate
  - 81% code coverage (exceeding 80% target)
  - 7 test categories: Deduplication, Sorting, Merge, AsyncRetry, RateLimiter, MultiRateLimiter, EdgeCases
  - pytest-based framework with async support
  - HTML coverage report generation

- **Test Documentation**
  - `docs/UNIT_TEST_COVERAGE.md` - Detailed coverage analysis
  - Missing lines analysis with improvement suggestions
  - Test strategy and methodology documentation

### Changed
- Version bumped from 0.4.0 to 0.5.0
- Updated all version strings across codebase

### Documentation
- Added `docs/PRIORITY_5_6_COMPLETE.md` - Comprehensive completion report
- Added `docs/UNIT_TEST_COVERAGE.md` - Test coverage analysis
- Updated `docs/QUICK_WINS_PROGRESS.md` - Progress tracking

### Technical Highlights
- **Database Schema**: Optimized with indices on timestamp and query_engine
- **Performance**: 75% response time improvement with memory cache
- **Reliability**: Cross-session persistence, zero data loss on restart
- **Maintainability**: 81% test coverage ensures code quality
- **Scalability**: Clear architecture for future enhancements

---

## [0.4.0] - 2025-10-11

### Added

#### Quick Win #1: Dockerfile Improvements
- Upgraded Python from 3.9 to 3.11
- Added non-root user (appuser, uid 1000) for security
- Optimized Playwright installation (Chromium only with --with-deps)
- Enhanced health checks with file existence validation
- Created resource directories: /app/logs, /app/cache, /app/reports
- Added `docker-compose.yml` with Redis support
- Added `.dockerignore` for optimized builds
- Added `.env.example` for configuration templates

#### Quick Win #2: Health Check Endpoints
- `health_check` tool - Basic service status, version, uptime, component status
- `readiness_check` tool - Readiness validation, config file check, search engine availability
- `metrics` tool - System resource usage (CPU, memory), performance metrics
- Added psutil dependency for system monitoring
- Complete test suite with 100% pass rate

#### Quick Win #3: JSON Export
- `export_search_results` tool - Export search results to JSON with metadata
- Optional metadata: timestamps, engine info, performance data, version info
- Automatic directory creation
- Custom output path support
- Comprehensive test coverage

#### Priority 4: Concurrent Search Optimization ⭐⭐⭐⭐⭐
- Implemented `asyncio.gather()` for parallel search execution
- All-engine mode queries all engines concurrently
- Fixed deduplication key from 'url' to 'link'
- Performance tests and benchmarks
- Complete documentation in `docs/CONCURRENT_SEARCH_SUMMARY.md`

### Fixed
- Deduplication key inconsistency (url → link)
- Search result merging logic

### Documentation
- Added `docs/CONCURRENT_SEARCH_SUMMARY.md`
- Updated `docs/QUICK_WINS_PROGRESS.md`
- Test result documentation

---

## [0.3.0] - 2025-10-XX

### Added
- Phase 2 features: Deduplication, retry, monitoring, rate limiting
- Basic search functionality with multiple engines
- DuckDuckGo, Google API, Brave, SearXNG support
- Web crawling with Crawl4AI integration
- MCP server implementation

---

[0.5.0]: https://github.com/zxkjack123/crawl4ai-mcp-server/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/zxkjack123/crawl4ai-mcp-server/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/zxkjack123/crawl4ai-mcp-server/releases/tag/v0.3.0

## [0.5.6] - 2025-10-15
## [0.5.8] - 2025-11-18

### Added
- Highlighted the 0.5.8 release in `README.md`, including Docker `SERVER_MODE=http_bridge` guidance and Makefile-driven workflows for the HTTP bridge + SearXNG stack.

### Changed
- Expanded `docs/SEARXNG_INTEGRATION.md` with proxy-entrypoint context, automated rewrite explanations, and `make` helpers to simplify local spin-ups.
- Refreshed bundled export samples under `output/` so their metadata matches the 0.5.8 release and new proxy guidance.
- Updated the SearXNG user-agent string to `Crawl4AI-HTTP-Bridge/0.5.8` for clearer telemetry.

### Fixed
- `_extract_proxy_from_cfg` now normalizes dicts/strings before rewrites, ensuring host proxy values load correctly from `config.json`.

### Maintenance
- Synchronized every version string (code, metadata, pyproject, docs) to 0.5.8 for a clean release cut.

### Tested
- ✅ `.venv/bin/pytest` — 77 tests passed in 1458s on Linux (Python 3.12.3).

## [0.5.7] - 2025-10-29

### Added
- Crawler explicit proxy support in `read_url`:
  - New config precedence: `crawler.proxy` (per-crawler) > global `proxy` > env (HTTP[S]_PROXY)
  - Direct-first attempt, then retry via proxy on network errors
  - Lazy-init proxied crawler to avoid overhead when direct works
  - Documented in `examples/config.example.json` (new `crawler.proxy` section)
- Config.json-driven proxy for search engines (per-engine > global > env)

### Changed
- Modernized `httpx` usage with `proxy=` and `trust_env=False` for clean direct attempts
- Prefer `ddgs` package with fallback to `duckduckgo_search`; aligned DuckDuckGo call signature
- Code cleanup: removed unused imports/`global` declarations; fixed long lines and minor spacing
- Added `.flake8` (max-line-length=100; ignore W293) and resolved lints for `src/index.py` and `src/search.py`
- Aligned version strings across system status and export metadata (0.5.7)

### Tested
- Full test suite passing (66 tests)
- Flake8 passes for `src/index.py` and `src/search.py` with repo config
