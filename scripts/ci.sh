#!/usr/bin/env bash
# Local CI gate (constitution GH-4).
#
# Runs the checks that used to run in GitHub Actions, on your machine:
#   Python   : ruff check + format, pyright, pytest (unit+integration),
#              spec self-review, agent-notes gate
#   Frontend : npm ci, lint, typecheck, test, build
#
# Usage:
#   scripts/ci.sh                 # full gate (npm ci)
#   scripts/ci.sh --fast          # skip npm ci (reuse node_modules)
#   scripts/ci.sh --with-image    # also build the Docker image (slow)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WITH_IMAGE=0
FAST=0
for arg in "$@"; do
  case "$arg" in
    --with-image) WITH_IMAGE=1 ;;
    --fast) FAST=1 ;;
    -h | --help)
      echo "usage: scripts/ci.sh [--fast] [--with-image]"
      echo "  --fast        skip 'npm ci' (reuse node_modules)"
      echo "  --with-image  also build the Docker image"
      exit 0
      ;;
    *)
      echo "unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

step() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }

step "Python: lint (ruff)"
uv run ruff check .
uv run ruff format --check .

step "Python: typecheck (pyright)"
uv run pyright

step "Python: tests (unit + integration)"
uv run pytest tests/unit tests/integration -q

step "Python: self-review (spec compliance)"
uv run python scripts/spec_review.py

step "Python: agent notes"
uv run python scripts/verify_notes.py

step "Frontend: install"
if [ "$FAST" -eq 1 ]; then
  echo "skipped (--fast)"
else
  (cd frontend && npm ci)
fi

step "Frontend: lint / typecheck / test / build"
(cd frontend && npm run lint && npm run typecheck && npm run test && npm run build)

if [ "$WITH_IMAGE" -eq 1 ]; then
  step "Docker image build"
  docker build -t commerce-agent:ci .
fi

printf '\n\033[1;32mOK: local CI passed\033[0m\n'
