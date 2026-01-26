#!/usr/bin/env bash
set -euo pipefail

# Run Crawl4AI MCP server with environment loaded from the repo .env.
# This is useful for MCP clients (VS Code / Cherry Studio / etc.) so you can
# keep tuning knobs in one place.

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

# Host vs Docker reminder:
# - Docker bridge should use SEARXNG_BASE_URL=http://searxng:8080
# - Host MCP should use the published port on localhost
export SERVER_MODE="mcp"
export SEARXNG_BASE_URL="${SEARXNG_BASE_URL_HOST:-http://localhost:28981}"

exec "$REPO_ROOT/.venv/bin/python" -m src.index
