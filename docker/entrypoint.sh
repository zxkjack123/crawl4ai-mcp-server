#!/usr/bin/env bash
set -euo pipefail

MODE=${SERVER_MODE:-http}
HTTP_PORT=${HTTP_PORT:-8080}
HTTP_HOST=${HTTP_HOST:-0.0.0.0}
WORKERS=${UVICORN_WORKERS:-1}

cd /app

if [[ "$MODE" == "mcp" ]]; then
  echo "[entrypoint] Starting Crawl4AI MCP server"
  exec python -m src.index
else
  echo "[entrypoint] Starting Crawl4AI HTTP bridge on ${HTTP_HOST}:${HTTP_PORT} (workers=${WORKERS})"
  exec uvicorn src.rest_server:app \
    --host "${HTTP_HOST}" \
    --port "${HTTP_PORT}" \
    --workers "${WORKERS}"
fi
