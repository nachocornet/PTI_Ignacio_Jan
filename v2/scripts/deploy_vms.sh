#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for env_file in ".env" "config/.env" "config/.env.vms" "scripts/.env.vms"; do
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
done

NATTECH_HOST="${NATTECH_HOST:-nattech.fib.upc.edu}"
SSH_USER="${SSH_USER:-alumne}"
FRONTEND_SSH_PORT="${FRONTEND_SSH_PORT:-40561}"
BACKEND_SSH_PORT="${BACKEND_SSH_PORT:-40571}"
DB_SSH_PORT="${DB_SSH_PORT:-40581}"
DEPLOY_PATH="${DEPLOY_PATH:-/home/alumne/pti-v2}"
DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-}}"
DB_RESET_ON_AUTH_FAIL="${DB_RESET_ON_AUTH_FAIL:-1}"

POSTGRES_USER="${POSTGRES_USER:-ssi_user}"
POSTGRES_DB="${POSTGRES_DB:-ssi_db}"
FRONTEND_EXTERNAL_URL="${FRONTEND_EXTERNAL_URL:-http://${NATTECH_HOST}:40560}"
BACKEND_EXTERNAL_URL="${BACKEND_EXTERNAL_URL:-http://${NATTECH_HOST}:40570}"

if [[ -z "${ISSUER_WALLET_JSON_B64:-}" && -f "deployments/runtime/issuer_wallet.json" ]]; then
  if base64 --help 2>/dev/null | grep -q -- '-w'; then
    ISSUER_WALLET_JSON_B64="$(base64 -w 0 deployments/runtime/issuer_wallet.json)"
  else
    ISSUER_WALLET_JSON_B64="$(base64 < deployments/runtime/issuer_wallet.json | tr -d '\n')"
  fi
fi

if [[ -z "${DB_PASSWORD:-}" && -t 0 ]]; then
  read -r -s -p "DB_PASSWORD: " DB_PASSWORD
  echo
fi

if [[ -z "${SEPOLIA_RPC_URL:-}" && -t 0 ]]; then
  read -r -p "SEPOLIA_RPC_URL: " SEPOLIA_RPC_URL
fi

if [[ -z "${ISSUER_WALLET_JSON_B64:-}" && -t 0 ]]; then
  read -r -p "Path issuer wallet JSON [deployments/runtime/issuer_wallet.json]: " wallet_file
  wallet_file="${wallet_file:-deployments/runtime/issuer_wallet.json}"
  if [[ -f "$wallet_file" ]]; then
    if base64 --help 2>/dev/null | grep -q -- '-w'; then
      ISSUER_WALLET_JSON_B64="$(base64 -w 0 "$wallet_file")"
    else
      ISSUER_WALLET_JSON_B64="$(base64 < "$wallet_file" | tr -d '\n')"
    fi
  fi
fi

missing=()
for var_name in DB_PASSWORD ISSUER_WALLET_JSON_B64 SEPOLIA_RPC_URL; do
  if [[ -z "${!var_name:-}" ]]; then
    missing+=("$var_name")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "[deploy-vms] Missing required vars: ${missing[*]}" >&2
  echo "[deploy-vms] Export them or create ${ROOT}/.env with those keys." >&2
  exit 1
fi

SSH_STRICT_HOST_KEY_CHECKING="${SSH_STRICT_HOST_KEY_CHECKING:-accept-new}"
SSH_COMMON=(-o BatchMode=yes -o StrictHostKeyChecking="${SSH_STRICT_HOST_KEY_CHECKING}")
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

ensure_remote_docker() {
  local port="$1"
  remote_cmd "$port" "if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  exit 0
fi

echo '[deploy-vms] Docker/Compose missing on target VM. Trying auto-install...' >&2

if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker.io docker-compose-plugin
elif [[ \"\$(id -u)\" == \"0\" ]]; then
  apt-get update -y
  apt-get install -y docker.io docker-compose-plugin
else
  echo '[deploy-vms] Cannot auto-install Docker (no sudo without password).' >&2
  echo '[deploy-vms] Install manually and retry:' >&2
  echo '  sudo apt-get update -y && sudo apt-get install -y docker.io docker-compose-plugin' >&2
  exit 1
fi

docker compose version >/dev/null 2>&1"
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

verify_remote_db_auth() {
  local port="$1"
  remote_cmd "$port" "docker exec ssi_postgres sh -lc \"PGPASSWORD='${DB_PASSWORD}' psql -h 127.0.0.1 -U '${POSTGRES_USER}' -d '${POSTGRES_DB}' -c 'select 1;' >/dev/null\""
}

sync_remote_db_password() {
  local port="$1"
  remote_cmd "$port" "docker exec ssi_postgres sh -lc \"psql -v ON_ERROR_STOP=1 -U '${POSTGRES_USER}' -d '${POSTGRES_DB}' -c \\\"ALTER USER \\\\\\\"${POSTGRES_USER}\\\\\\\" WITH PASSWORD '${DB_PASSWORD}';\\\"\""
}

echo "[deploy-vms] Syncing repository to DB VM..."
remote_cmd "$DB_SSH_PORT" "mkdir -p '${DEPLOY_PATH}' '${DEPLOY_PATH}/deployments/runtime'"
ensure_remote_docker "$DB_SSH_PORT"
sync_repo "$DB_SSH_PORT"
cat > "$TMPDIR/db.env" <<EOF
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_PASSWORD=${DB_PASSWORD}
EOF
copy_file "$TMPDIR/db.env" "$DB_SSH_PORT" "${DEPLOY_PATH}/.env"
remote_cmd "$DB_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose --env-file .env -f config/compose_vms/vm_db/docker_compose.yml down --remove-orphans || true && docker compose --env-file .env -f config/compose_vms/vm_db/docker_compose.yml up -d --build"
wait_remote_tcp "$DB_SSH_PORT" "127.0.0.1" "5432"
sync_remote_db_password "$DB_SSH_PORT"
if ! verify_remote_db_auth "$DB_SSH_PORT"; then
  if [[ "$DB_RESET_ON_AUTH_FAIL" == "1" ]]; then
    echo "[deploy-vms] DB auth mismatch detected (likely stale postgres volume). Recreating DB volume..."
    remote_cmd "$DB_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose --env-file .env -f config/compose_vms/vm_db/docker_compose.yml down -v --remove-orphans || true && docker compose --env-file .env -f config/compose_vms/vm_db/docker_compose.yml up -d --build"
    wait_remote_tcp "$DB_SSH_PORT" "127.0.0.1" "5432"
    verify_remote_db_auth "$DB_SSH_PORT"
  else
    echo "[deploy-vms] DB auth mismatch detected and DB_RESET_ON_AUTH_FAIL=0."
    echo "[deploy-vms] Run with DB_RESET_ON_AUTH_FAIL=1 or recreate DB volume manually:"
    echo "[deploy-vms] docker compose --env-file .env -f config/compose_vms/vm_db/docker_compose.yml down -v && docker compose --env-file .env -f config/compose_vms/vm_db/docker_compose.yml up -d --build"
    exit 1
  fi
fi

echo "[deploy-vms] Syncing repository to Backend VM..."
remote_cmd "$BACKEND_SSH_PORT" "mkdir -p '${DEPLOY_PATH}' '${DEPLOY_PATH}/deployments/runtime'"
ensure_remote_docker "$BACKEND_SSH_PORT"
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
remote_cmd "$BACKEND_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose --env-file .env -f config/compose_vms/vm_servers/docker_compose.yml down --remove-orphans || true && docker compose --env-file .env -f config/compose_vms/vm_servers/docker_compose.yml up -d --build"
remote_cmd "$BACKEND_SSH_PORT" "docker exec ssi_issuer python /app/scripts/seed_db.py"
wait_remote_http "$BACKEND_SSH_PORT" "http://127.0.0.1:8080/health"
wait_remote_http "$BACKEND_SSH_PORT" "http://127.0.0.1:8080/health/verifier"

echo "[deploy-vms] Syncing repository to Frontend VM..."
remote_cmd "$FRONTEND_SSH_PORT" "mkdir -p '${DEPLOY_PATH}'"
ensure_remote_docker "$FRONTEND_SSH_PORT"
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
remote_cmd "$FRONTEND_SSH_PORT" "cd '${DEPLOY_PATH}' && docker compose --env-file .env -f config/compose_vms/vm-frontend/docker_compose.yml down --remove-orphans || true && docker compose --env-file .env -f config/compose_vms/vm-frontend/docker_compose.yml up -d --build"
wait_remote_http "$FRONTEND_SSH_PORT" "http://127.0.0.1:8080/frontend_portal.html"

echo "[deploy-vms] Deployment completed successfully."
