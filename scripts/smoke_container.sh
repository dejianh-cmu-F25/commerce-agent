#!/usr/bin/env bash
# Keyless container smoke test (constitution DP-3/DP-4/DP-5, P8).
#
# Runs the built image with a mock model and in-memory stores, then asserts the
# container's HTTP surface (liveness, readiness, SPA, a chat turn) and that the
# process is non-root. No API key and no .env are used.
#
# Usage: scripts/smoke_container.sh [IMAGE]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE="${1:-${IMAGE:-commerce-agent:ci}}"
PORT="${SMOKE_PORT:-18080}"
NAME="commerce-agent-smoke-$$"
URL="http://127.0.0.1:${PORT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for the container smoke test" >&2
  exit 2
fi

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

fail() {
  echo "FAIL: $1" >&2
  docker logs "$NAME" >&2 2>/dev/null || true
  exit 1
}

echo "== container smoke: image ${IMAGE} =="
docker run -d --name "$NAME" -p "${PORT}:8000" \
  -e LLM_PROVIDER=mock \
  -e STOREFRONT_PROVIDER=memory \
  -e SESSION_STORE=memory \
  -e MEMORY_PROVIDER=memory \
  -e KNOWLEDGE_PROVIDER=memory \
  -e TRACE_FILE=/tmp/traces.jsonl \
  "$IMAGE" >/dev/null

ready=0
for _ in $(seq 1 40); do
  if curl -sf "${URL}/healthz" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" != "true" ]; then
    fail "container exited before becoming healthy"
  fi
  sleep 1
done
[ "$ready" = "1" ] || fail "container did not become healthy within 40s"

echo "healthz: ok"
readiness="$(curl -s "${URL}/readyz")"
echo "readyz:  ${readiness}"
echo "$readiness" | grep -q '"memory":"memory"' || fail "readyz did not report the memory provider"

curl -s "${URL}/" | grep -q "<title>Commerce Agent</title>" || fail "SPA shell was not served"
echo "spa:     ok"

chat="$(curl -s -N -X POST "${URL}/chat" -H 'Content-Type: application/json' -d '{"message":"hi"}')"
echo "$chat" | grep -q '"type": "TurnEnd"' || fail "chat turn did not complete"
echo "chat:    ok"

uid="$(docker exec "$NAME" id -u)"
[ "$uid" != "0" ] || fail "container runs as root"
echo "user:    uid ${uid} (non-root)"

echo "OK: container smoke passed"
