#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UNIT_SRC="$REPO_ROOT/docker/crawl4ai-mcp.service"
UNIT_NAME="crawl4ai-mcp.service"
UNIT_DST="/etc/systemd/system/$UNIT_NAME"

if [[ ! -f "$UNIT_SRC" ]]; then
  echo "ERROR: unit file not found: $UNIT_SRC" >&2
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "ERROR: systemctl not found (systemd not available?)" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found" >&2
  exit 1
fi

if [[ ! -f "$REPO_ROOT/docker/docker-compose.yml" ]]; then
  echo "ERROR: docker compose file not found: $REPO_ROOT/docker/docker-compose.yml" >&2
  exit 1
fi

echo "Installing systemd unit to $UNIT_DST"
tmp_unit="$(mktemp)"
trap 'rm -f "$tmp_unit"' EXIT

# Render template placeholders.
sed -e "s|@REPO_ROOT@|$REPO_ROOT|g" "$UNIT_SRC" >"$tmp_unit"

sudo cp "$tmp_unit" "$UNIT_DST"
sudo chmod 0644 "$UNIT_DST"

echo "Reloading systemd daemon"
sudo systemctl daemon-reload

echo "Enabling docker (if not enabled)"
sudo systemctl enable docker >/dev/null || true

echo "Enabling and starting $UNIT_NAME"
sudo systemctl enable --now "$UNIT_NAME"

echo
sudo systemctl --no-pager --full status "$UNIT_NAME" || true

echo
echo "Done. On next reboot, docker will start and systemd will run: docker compose up -d"
