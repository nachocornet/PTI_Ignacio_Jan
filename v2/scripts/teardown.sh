#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-local}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

case "$MODE" in
  local)
    docker compose -f docker-compose-local.yml down --remove-orphans
    ;;
  vms)
    : "${NATTECH_HOST:?NATTECH_HOST is required}"
    : "${SSH_USER:?SSH_USER is required}"
    : "${FRONTEND_SSH_PORT:?FRONTEND_SSH_PORT is required}"
    : "${BACKEND_SSH_PORT:?BACKEND_SSH_PORT is required}"
    : "${DB_SSH_PORT:?DB_SSH_PORT is required}"
    : "${DEPLOY_PATH:?DEPLOY_PATH is required}"

    SSH_COMMON=(-o BatchMode=yes -o StrictHostKeyChecking=yes)
    remote_down() {
      local port="$1"
      local compose_file="$2"
      ssh -p "$port" "${SSH_COMMON[@]}" "${SSH_USER}@${NATTECH_HOST}" \
        "bash -lc 'cd ${DEPLOY_PATH} && docker compose -f ${compose_file} down --remove-orphans || true'"
    }

    remote_down "$FRONTEND_SSH_PORT" "config/compose_vms/vm-frontend/docker_compose.yml"
    remote_down "$BACKEND_SSH_PORT" "config/compose_vms/vm_servers/docker_compose.yml"
    remote_down "$DB_SSH_PORT" "config/compose_vms/vm_db/docker_compose.yml"
    ;;
  *)
    echo "Usage: $0 [local|vms]" >&2
    exit 1
    ;;
esac

echo "Teardown completed for mode: $MODE"
