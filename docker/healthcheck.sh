#!/usr/bin/env bash
set -euo pipefail

MODE=${SERVER_MODE:-http}

if [[ "$MODE" == "http" ]]; then
  PORT=${HTTP_PORT:-8080}
  curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null
else
  python - <<'PY'
import os, sys
sys.exit(0 if os.path.exists('/app/src/index.py') else 1)
PY
fi
