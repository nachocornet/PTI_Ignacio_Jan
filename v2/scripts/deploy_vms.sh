#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${NATTECH_HOST:?NATTECH_HOST is required}"
: "${SSH_USER:?SSH_USER is required}"
: "${FRONTEND_SSH_PORT:?FRONTEND_SSH_PORT is required}"
: "${BACKEND_SSH_PORT:?BACKEND_SSH_PORT is required}"
: "${DB_SSH_PORT:?DB_SSH_PORT is required}"
: "${DEPLOY_PATH:?DEPLOY_PATH is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${ISSUER_WALLET_JSON_B64:?ISSUER_WALLET_JSON_B64 is required}"
: "${SEPOLIA_RPC_URL:?SEPOLIA_RPC_URL is required}"

POSTGRES_USER="${POSTGRES_USER:-ssi_user}"
POSTGRES_DB="${POSTGRES_DB:-ssi_db}"
FRONTEND_EXTERNAL_URL="${FRONTEND_EXTERNAL_URL:-http://nattech.fib.upc.edu:40560}"
BACKEND_EXTERNAL_URL="${BACKEND_EXTERNAL_URL:-http://nattech.fib.upc.edu:40570}"

SSH_COMMON=(-o BatchMode=yes -o StrictHostKeyChecking=yes)
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  current_branch="$(git branch --show-current 2>/dev/null || true)"
  if [[ -n "${current_branch}" ]]; then
    git pull --ff-only origin "${current_branch}" || true
  fi
fi

sync_repo() {
  local port="$1"
  rsync -az --delete \
    -e "ssh -p ${port} ${SSH_COMMON[*]}" \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '.pytest_cache/' \
    --exclude 'node_modules/' \
    --exclude 'config/node_modules/' \
    --exclude 'deployments/runtime/' \
    --exclude '*.pyc' \
    ./ "${SSH_USER}@${NATTECH_HOST}:${DEPLOY_PATH}/"
}

remote_cmd() {
  local port="$1"
  local command="$2"
  {
    printf '%s\n' 'set -euo pipefail'
    printf '%s\n' "${command}"
  } | ssh -p "${port}" "${SSH_COMMON[@]}" "${SSH_USER}@${NATTECH_HOST}" "bash -s"
}

copy_file() {
  local source="$1"
  local port="$2"
  local target="$3"
  rsync -az -e "ssh -p ${port} ${SSH_COMMON[*]}" "$source" "${SSH_USER}@${NATTECH_HOST}:${target}"
}

wait_remote_http() {
  local port="$1"
  local url="$2"
  remote_cmd "$port" "python3 - <<'PY'
import time
import urllib.request

url = '${url}'
for _ in range(40):
    try:
        urllib.request.urlopen(url, timeout=3).read()
        print('ready')
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit('Timed out waiting for ' + url)
PY"
}

wait_remote_tcp() {
  local port="$1"
  local host="$2"
  local service_port="$3"
  remote_cmd "$port" "python3 - <<'PY'
import socket
import time

host = '${host}'
service_port = ${service_port}
for _ in range(40):
    try:
        sock = socket.create_connection((host, service_port), timeout=3)
        sock.close()
        print('ready')
        break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit(f'Timed out waiting for {host}:{service_port}')
PY"
}

echo "[deploy-vms] Syncing repository to DB VM..."
remote_cmd "$DB_SSH_PORT" "mkdir -p '${DEPLOY_PATH}' '${DEPLOY_PATH}/deployments/runtime'"
sync_repo "$DB_SSH_PORT"
cat > "$TMPDIR/db.env" <<EOF
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_PASSWORD=${DB_PASSWORD}
EOF
copy_file "$TMPDIR/db.env" "$DB_SSH_PORT" "${DEPLOY_PATH}/.env"
remote_cmd "$DB_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose -f config/compose_vms/vm_db/docker_compose.yml down --remove-orphans || true && docker compose -f config/compose_vms/vm_db/docker_compose.yml up -d --build"
wait_remote_tcp "$DB_SSH_PORT" "127.0.0.1" "5432"

echo "[deploy-vms] Syncing repository to Backend VM..."
remote_cmd "$BACKEND_SSH_PORT" "mkdir -p '${DEPLOY_PATH}' '${DEPLOY_PATH}/deployments/runtime'"
sync_repo "$BACKEND_SSH_PORT"
printf '%s' "${ISSUER_WALLET_JSON_B64}" | base64 -d > "$TMPDIR/issuer_wallet.json"
copy_file "$TMPDIR/issuer_wallet.json" "$BACKEND_SSH_PORT" "${DEPLOY_PATH}/deployments/runtime/issuer_wallet.json"
cat > "$TMPDIR/backend.env" <<EOF
DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${DB_PASSWORD}@172.16.4.58:5432/${POSTGRES_DB}
SSI_BLOCKCHAIN_NETWORK=sepolia
SEPOLIA_RPC_URL=${SEPOLIA_RPC_URL}
SSI_CONTRACT_FILE=deployments/blockchain_contract.sepolia.json
SSI_ISSUER_WALLET_FILE=deployments/runtime/issuer_wallet.json
SSI_HOLDER_WALLET_FILE=deployments/runtime/wallet.json
SSI_CORS_ORIGINS=${FRONTEND_EXTERNAL_URL},${BACKEND_EXTERNAL_URL}
EOF
copy_file "$TMPDIR/backend.env" "$BACKEND_SSH_PORT" "${DEPLOY_PATH}/.env"
remote_cmd "$BACKEND_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose -f config/compose_vms/vm_servers/docker_compose.yml down --remove-orphans || true && docker compose -f config/compose_vms/vm_servers/docker_compose.yml up -d --build"
wait_remote_http "$BACKEND_SSH_PORT" "http://127.0.0.1:8080/health"
wait_remote_http "$BACKEND_SSH_PORT" "http://127.0.0.1:8080/health/verifier"

echo "[deploy-vms] Syncing repository to Frontend VM..."
remote_cmd "$FRONTEND_SSH_PORT" "mkdir -p '${DEPLOY_PATH}'"
sync_repo "$FRONTEND_SSH_PORT"
cat > "$TMPDIR/frontend.variables.js" <<EOF
window.SSI_CONFIG = {
  "appTitle": "SSI v2 Frontend",
  "appSubtitle": "Dashboard web para issuer y verifier",
  "urls": {
    "issuerApiBaseUrl": "${BACKEND_EXTERNAL_URL}",
    "verifierApiBaseUrl": "${BACKEND_EXTERNAL_URL}",
    "apiBaseUrl": "${BACKEND_EXTERNAL_URL}"
  },
  "defaults": {
    "dni": "12345678A",
    "refreshMs": 15000
  }
};
EOF
copy_file "$TMPDIR/frontend.variables.js" "$FRONTEND_SSH_PORT" "${DEPLOY_PATH}/frontend/frontend.variables.js"
remote_cmd "$FRONTEND_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose -f config/compose_vms/vm-frontend/docker_compose.yml down --remove-orphans || true && docker compose -f config/compose_vms/vm-frontend/docker_compose.yml up -d --build"
wait_remote_http "$FRONTEND_SSH_PORT" "http://127.0.0.1:8080/frontend_portal.html"

echo "[deploy-vms] Deployment completed successfully."
