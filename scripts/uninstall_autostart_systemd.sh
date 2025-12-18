#!/usr/bin/env bash
set -euo pipefail

UNIT_NAME="crawl4ai-mcp.service"
UNIT_DST="/etc/systemd/system/$UNIT_NAME"

echo "Stopping and disabling $UNIT_NAME (if present)"
sudo systemctl disable --now "$UNIT_NAME" >/dev/null 2>&1 || true

if [[ -f "$UNIT_DST" ]]; then
  echo "Removing $UNIT_DST"
  sudo rm -f "$UNIT_DST"
fi

echo "Reloading systemd daemon"
sudo systemctl daemon-reload

echo "Done."
