#!/bin/sh
set -e

# Propagate host-side proxy variables into standard HTTP(S)_PROXY envs
# so the upstream engines can reach the public internet.
if [ -n "$CRAWL4AI_HTTP_PROXY" ]; then
  echo "[proxy-entrypoint] HTTP_PROXY -> $CRAWL4AI_HTTP_PROXY"
  export HTTP_PROXY="$CRAWL4AI_HTTP_PROXY"
fi
if [ -n "$CRAWL4AI_HTTPS_PROXY" ]; then
  echo "[proxy-entrypoint] HTTPS_PROXY -> $CRAWL4AI_HTTPS_PROXY"
  export HTTPS_PROXY="$CRAWL4AI_HTTPS_PROXY"
fi
if [ -n "$CRAWL4AI_NO_PROXY" ]; then
  echo "[proxy-entrypoint] NO_PROXY -> $CRAWL4AI_NO_PROXY"
  export NO_PROXY="$CRAWL4AI_NO_PROXY"
fi

exec /usr/local/searxng/entrypoint.sh "$@"
