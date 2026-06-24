#!/usr/bin/env bash
set -euo pipefail

MODE=${SERVER_MODE:-http}

if [[ "$MODE" == "http" ]]; then
  PORT=${HTTP_PORT:-8080}
  # Basic API liveness check
  curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null || exit 1

  # Deep check: verify browser/crawl actually works (every healthcheck interval)
  # Use a lightweight page to minimize overhead
  RESULT=$(curl -sS -X POST "http://127.0.0.1:${PORT}/read_url" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "timeout": 20}' \
    --max-time 25 2>&1) || exit 1

  # Verify we got actual content back (not an error detail)
  if echo "$RESULT" | grep -q '"content"'; then
    exit 0
  else
    echo "healthcheck: crawl returned no content: $RESULT" >&2
    exit 1
  fi
else
  python - <<'PY'
import os, sys
sys.exit(0 if os.path.exists('/app/src/index.py') else 1)
PY
fi
