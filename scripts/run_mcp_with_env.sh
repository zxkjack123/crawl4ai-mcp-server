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

# NOTE: MCP runs over stdio and will typically appear "idle" when launched
# manually. That's expected: it waits for the client to send requests.
echo "[run_mcp_with_env] repo=$REPO_ROOT" >&2
echo "[run_mcp_with_env] starting MCP server (stdio); this process stays running" >&2

# If .env is Docker-oriented, it often uses host.docker.internal for proxies.
# On Linux host runs, that name may not resolve; rewrite to 127.0.0.1 so host MCP
# doesn't hang on proxy connect.
if ! getent hosts host.docker.internal >/dev/null 2>&1; then
  for var in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy CRAWL4AI_HTTP_PROXY CRAWL4AI_HTTPS_PROXY; do
    v=${!var-}
    if [[ -n "${v}" && "${v}" == *"host.docker.internal"* ]]; then
      export "$var"="${v//host.docker.internal/127.0.0.1}"
    fi
  done
fi

# Host vs Docker reminder:
# - Docker bridge should use SEARXNG_BASE_URL=http://searxng:8080
# - Host MCP should use the published port on localhost
export SERVER_MODE="mcp"
export SEARXNG_BASE_URL="${SEARXNG_BASE_URL_HOST:-http://localhost:28981}"

# Ensure Python logs flush promptly when routed to stderr by the runtime.
export PYTHONUNBUFFERED=1

exec "$REPO_ROOT/.venv/bin/python" -m src.index
