#!/usr/bin/env bash
#
# Integration tests for docker/healthcheck.sh
#
# Starts a mock HTTP server (tests/mock_http_server.py) and runs
# healthcheck.sh against it, verifying exit codes for:
#
#   1. Healthy server (both /health and /read_url work) → exit 0
#   2. /health down (500)                              → exit 1
#   3. /read_url returns error (no "content" key)      → exit 1
#   4. /read_url returns empty JSON (no "content")     → exit 1
#
# Usage:  bash tests/test_healthcheck.sh
# Requires: bash, python3, curl
#

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HEALTHCHECK="$PROJECT_ROOT/docker/healthcheck.sh"
MOCK_SERVER="$SCRIPT_DIR/mock_http_server.py"

PASS=0
FAIL=0
MOCK_PID=""

cleanup() {
    if [ -n "$MOCK_PID" ] && kill -0 "$MOCK_PID" 2>/dev/null; then
        kill "$MOCK_PID" 2>/dev/null || true
        wait "$MOCK_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

start_mock() {
    local mode="$1"
    python3 "$MOCK_SERVER" "$mode" &
    MOCK_PID=$!
    # Wait for the port to appear on stdout
    local tries=0
    while [ $tries -lt 50 ]; do
        if ! kill -0 "$MOCK_PID" 2>/dev/null; then
            echo "ERROR: mock server died during startup" >&2
            exit 1
        fi
        # Try to read the first line from the process stdout via /proc
        local cmdline
        cmdline=$(cat /proc/$MOCK_PID/cmdline 2>/dev/null | tr '\0' ' ' || true)
        # Just sleep briefly — the server prints port immediately
        sleep 0.3
        break
    done
}

get_mock_port() {
    # The mock server prints its port as the first line of stdout.
    # We capture it by reading from /proc/<pid>/fd/1 (best-effort).
    # Fallback: parse from a temp file approach.
    local port
    # Use a simpler approach: the server's first stdout line is the port.
    # We read it via a temporary fifo.
    port=$(timeout 2 bash -c "cat /proc/$MOCK_PID/fd/1" 2>/dev/null | head -1 || true)
    if [ -z "$port" ]; then
        # Fallback: use ss/netstat to find the listening port
        port=$(ss -tlnp 2>/dev/null | grep "$MOCK_PID" | grep -oP ':\K\d+' | head -1 || true)
    fi
    echo "$port"
}

run_healthcheck() {
    local port="$1"
    SERVER_MODE="http" HTTP_PORT="$port" bash "$HEALTHCHECK" 2>/dev/null
    return $?
}

assert_exit() {
    local expected="$1"
    local actual="$2"
    local name="$3"
    if [ "$actual" -eq "$expected" ]; then
        echo "  PASS: $name (exit=$actual)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (expected=$expected, got=$actual)"
        FAIL=$((FAIL + 1))
    fi
}

echo "Running healthcheck.sh integration tests..."
echo ""

# ── Test 1: Healthy server ─────────────────────────────────────────────────
echo "[1/4] Healthy server (both endpoints OK)"
python3 "$MOCK_SERVER" "healthy" > /tmp/hc_port_1.txt 2>/dev/null &
MOCK_PID=$!
sleep 0.5
PORT=$(cat /tmp/hc_port_1.txt 2>/dev/null || echo "")
if [ -z "$PORT" ]; then
    echo "  FAIL: could not get mock server port"
    FAIL=$((FAIL + 1))
else
    run_healthcheck "$PORT"
    assert_exit 0 $? "healthy server should exit 0"
fi
kill "$MOCK_PID" 2>/dev/null || true
wait "$MOCK_PID" 2>/dev/null || true
MOCK_PID=""
rm -f /tmp/hc_port_1.txt

# ── Test 2: /health is down ─────────────────────────────────────────────────
echo "[2/4] /health returns 500"
python3 "$MOCK_SERVER" "health_down" > /tmp/hc_port_2.txt 2>/dev/null &
MOCK_PID=$!
sleep 0.5
PORT=$(cat /tmp/hc_port_2.txt 2>/dev/null || echo "")
if [ -z "$PORT" ]; then
    echo "  FAIL: could not get mock server port"
    FAIL=$((FAIL + 1))
else
    run_healthcheck "$PORT"
    assert_exit 1 $? "health down should exit 1"
fi
kill "$MOCK_PID" 2>/dev/null || true
wait "$MOCK_PID" 2>/dev/null || true
MOCK_PID=""
rm -f /tmp/hc_port_2.txt

# ── Test 3: /read_url returns error ─────────────────────────────────────────
echo "[3/4] /read_url returns error response"
python3 "$MOCK_SERVER" "read_error" > /tmp/hc_port_3.txt 2>/dev/null &
MOCK_PID=$!
sleep 0.5
PORT=$(cat /tmp/hc_port_3.txt 2>/dev/null || echo "")
if [ -z "$PORT" ]; then
    echo "  FAIL: could not get mock server port"
    FAIL=$((FAIL + 1))
else
    run_healthcheck "$PORT"
    assert_exit 1 $? "read_url error should exit 1"
fi
kill "$MOCK_PID" 2>/dev/null || true
wait "$MOCK_PID" 2>/dev/null || true
MOCK_PID=""
rm -f /tmp/hc_port_3.txt

# ── Test 4: /read_url returns empty ──────────────────────────────────────────
echo "[4/4] /read_url returns empty JSON"
python3 "$MOCK_SERVER" "read_empty" > /tmp/hc_port_4.txt 2>/dev/null &
MOCK_PID=$!
sleep 0.5
PORT=$(cat /tmp/hc_port_4.txt 2>/dev/null || echo "")
if [ -z "$PORT" ]; then
    echo "  FAIL: could not get mock server port"
    FAIL=$((FAIL + 1))
else
    run_healthcheck "$PORT"
    assert_exit 1 $? "read_url empty should exit 1"
fi
kill "$MOCK_PID" 2>/dev/null || true
wait "$MOCK_PID" 2>/dev/null || true
MOCK_PID=""
rm -f /tmp/hc_port_4.txt

echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All tests passed!"
