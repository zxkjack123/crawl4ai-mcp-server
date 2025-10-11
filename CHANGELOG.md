# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
