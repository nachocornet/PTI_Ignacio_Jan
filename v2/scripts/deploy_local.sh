#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  current_branch="$(git branch --show-current 2>/dev/null || true)"
  if [[ -n "${current_branch}" ]]; then
    git pull --ff-only origin "${current_branch}" || true
  fi
fi

echo "[deploy-local] Bringing down any previous local stack..."
docker compose -f docker-compose-local.yml down --remove-orphans || true

echo "[deploy-local] Building and starting local stack..."
docker compose -f docker-compose-local.yml up -d --build

echo "[deploy-local] Local deployment is up."
