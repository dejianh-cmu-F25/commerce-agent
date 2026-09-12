#!/usr/bin/env bash
# Start the commerce agent and open the browser (checkpoint demo).
# Uses the real provider from .env by default. Set NO_OPEN=1 to skip the browser.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

HOST="${WEB_HOST:-127.0.0.1}"
PORT="${WEB_PORT:-8000}"
# Bind to HOST but browse a reachable address (0.0.0.0 is not browsable).
BROWSE_HOST="$HOST"
if [ "$HOST" = "0.0.0.0" ] || [ "$HOST" = "::" ]; then BROWSE_HOST="127.0.0.1"; fi
URL="http://${BROWSE_HOST}:${PORT}"

echo "Starting commerce agent (provider: ${LLM_PROVIDER:-deepseek}) on ${URL} ..."
uv run uvicorn web.main:create_app --factory --host "$HOST" --port "$PORT" --log-level warning &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

ready=0
for _ in $(seq 1 30); do
  if curl -sf "${URL}/healthz" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" != "1" ]; then
  echo "Server did not become healthy on ${URL}." >&2
  exit 1
fi

echo "Ready: ${URL}"
echo "Budget: $(curl -s "${URL}/budget")"
if [ "$(uname)" = "Darwin" ] && [ "${NO_OPEN:-0}" != "1" ]; then
  open "$URL"
fi

wait "$SERVER_PID"
