#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-local}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Cargar variables de entorno automáticamente
for env_file in ".env" "config/.env" "config/.env.vms" "scripts/.env.vms"; do
  if [[ -f "$env_file" ]]; then
    set -a
    source "$env_file"
    set +a
  fi
done

case "$MODE" in
  local)
    echo "[teardown] Apagando entorno local..."
    docker compose -f docker-compose-local.yml down --remove-orphans
    ;;
  vms)
    echo "[teardown] Apagando máquinas en Virtech (Cloud)..."
    
    # Valores por defecto si no están en el .env
    NATTECH_HOST="${NATTECH_HOST:-nattech.fib.upc.edu}"
    SSH_USER="${SSH_USER:-alumne}"
    FRONTEND_SSH_PORT="${FRONTEND_SSH_PORT:-40561}"
    BACKEND_SSH_PORT="${BACKEND_SSH_PORT:-40571}"
    DB_SSH_PORT="${DB_SSH_PORT:-40581}"
    DEPLOY_PATH="${DEPLOY_PATH:-/home/alumne/pti-v2}"

    SSH_COMMON=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)
    
    remote_down() {
      local port="$1"
      local compose_file="$2"
      local name="$3"
      echo " -> Deteniendo $name (Puerto: $port)..."
      ssh -p "$port" "${SSH_COMMON[@]}" "${SSH_USER}@${NATTECH_HOST}" \
        "bash -lc 'cd ${DEPLOY_PATH} && docker compose --env-file .env -f ${compose_file} down --remove-orphans || true'"
    }

    # Apagamos en orden inverso al encendido
    remote_down "$FRONTEND_SSH_PORT" "config/compose_vms/vm-frontend/docker_compose.yml" "Frontend"
    remote_down "$BACKEND_SSH_PORT" "config/compose_vms/vm_servers/docker_compose.yml" "Backend"
    remote_down "$DB_SSH_PORT" "config/compose_vms/vm_db/docker_compose.yml" "Base de Datos"
    ;;
  *)
    echo "Uso: $0 [local|vms]" >&2
    exit 1
    ;;
esac

echo "Teardown completado para el modo: $MODE"