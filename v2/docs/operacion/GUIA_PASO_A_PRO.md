# Guia Paso a Paso Pro

Esta guia resume el estado tecnico actual del repositorio y explica como probarlo hoy en local, y que secretos/datos debe preparar Nacho para el despliegue automatico en las 3 VMs de Virtech.

---

## 1) Que he cambiado en el repositorio

### Frontend

- He sustituido la idea de un unico frontend monolitico por dos dashboards de produccion:
  - [issuer_dashboard.html](../../frontend/issuer_dashboard.html)
  - [verifier_dashboard.html](../../frontend/verifier_dashboard.html)
- He mantenido una pagina de entrada:
  - [frontend_portal.html](../../frontend/frontend_portal.html)

### Docker

- He dejado un [Dockerfile](../../Dockerfile) de Python optimizado para issuer/verifier.
- He preparado tres `docker_compose.yml` separados por VM:
  - [vm-frontend/docker_compose.yml](../../config/compose_vms/vm-frontend/docker_compose.yml)
  - [vm_servers/docker_compose.yml](../../config/compose_vms/vm_servers/docker_compose.yml)
  - [vm_db/docker_compose.yml](../../config/compose_vms/vm_db/docker_compose.yml)

### Base de datos

- La capa SQLAlchemy usa `DATABASE_URL` si existe.
- Si no existe, hace fallback a SQLite para seguir desarrollando en local.
- En producción se usa PostgreSQL 15.

### Automatizacion

- He creado scripts separados para despliegue y parada:
  - [scripts/deploy_local.sh](../../scripts/deploy_local.sh)
  - [scripts/deploy_vms.sh](../../scripts/deploy_vms.sh)
  - [scripts/teardown.sh](../../scripts/teardown.sh)
- El despliegue en VMs hace:
  - sincronizacion del repo,
  - actualizacion por `git pull` si el repo ya existe en el entorno local de despliegue,
  - arranque ordenado BD -> backend -> frontend,
  - limpieza de stacks previos con `docker compose down --remove-orphans`.

### CI/CD

- He preparado un workflow de GitHub Actions para desplegar desde el repositorio.
- La idea es que GitHub Actions sea el orquestador y no tu ordenador.

### Blockchain

- En local puedes seguir usando el flujo con Hardhat y Sepolia.
- En produccion, el backend apunta a la red Sepolia mediante `SEPOLIA_RPC_URL`.
- El contrato on-chain se referencia por `SSI_CONTRACT_FILE`.
- La base de produccion ya no depende de desplegar blockchain localmente en cada release.

---

## 2) Como probarlo ahora mismo en tu ordenador local

### Paso 1: preparar el entorno

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r config/requirements.txt
```

### Paso 2: levantar el entorno local

Usa el script local:

```bash
bash scripts/deploy_local.sh
```

Si prefieres el compose local directo:

```bash
docker compose -f docker-compose-local.yml up -d --build
```

### Paso 3: comprobar las URLs

- Portal: http://127.0.0.1:8080/frontend_portal.html
- Issuer: http://127.0.0.1:8080/issuer_dashboard.html
- Verifier: http://127.0.0.1:8080/verifier_dashboard.html
- Health issuer: http://127.0.0.1:5010/health
- Health verifier: http://127.0.0.1:5011/health

### Paso 4: apagarlo todo

```bash
bash scripts/teardown.sh local
```

---

## 3) Que variables exactas debe preparar Nacho para Gemini

Estas son las variables/secretos recomendados para el despliegue automatizado en Virtech.

### Secrets en GitHub / Vault

- `SSH_PRIVATE_KEY`
  - Clave privada SSH que usara GitHub Actions para conectarse a las VMs.
- `SSH_KNOWN_HOSTS`
  - Salida de `ssh-keyscan nattech.fib.upc.edu -p 40561 -p 40571 -p 40581` o las claves host equivalentes.
- `DB_PASSWORD`
  - Password de PostgreSQL.
- `ISSUER_WALLET_JSON_B64`
  - Contenido base64 del fichero `deployments/runtime/issuer_wallet.json`.
- `SEPOLIA_RPC_URL`
  - RPC de Sepolia.
- `GITHUB_TOKEN` o Deploy Key si se decide hacer `git clone` con autenticacion externa.

### Variables de entorno de despliegue

- `NATTECH_HOST=nattech.fib.upc.edu`
- `SSH_USER=alumne`
- `FRONTEND_SSH_PORT=40561`
- `BACKEND_SSH_PORT=40571`
- `DB_SSH_PORT=40581`
- `DEPLOY_PATH=/home/alumne/pti-v2`
- `POSTGRES_USER=ssi_user`
- `POSTGRES_DB=ssi_db`
- `FRONTEND_EXTERNAL_URL=http://nattech.fib.upc.edu:40560`
- `BACKEND_EXTERNAL_URL=http://nattech.fib.upc.edu:40570`
- `SSI_CORS_ORIGINS=http://nattech.fib.upc.edu:40560,http://nattech.fib.upc.edu:40570`
- `DATABASE_URL=postgresql+psycopg2://ssi_user:<DB_PASSWORD>@172.16.4.58:5432/ssi_db`
- `SSI_BLOCKCHAIN_NETWORK=sepolia`
- `SSI_CONTRACT_FILE=deployments/blockchain_contract.sepolia.json`
- `SSI_ISSUER_WALLET_FILE=deployments/runtime/issuer_wallet.json`
- `SSI_HOLDER_WALLET_FILE=deployments/runtime/wallet.json`

### Variables internas por VM

#### VM1 Frontend

- `8080` para Nginx
- Publica solo el portal y los dashboards HTML

#### VM2 Backend

- `8080` interno para Nginx reverse proxy
- `5010` issuer
- `5011` verifier
- `DATABASE_URL` apuntando a la IP interna de la VM3

#### VM3 Database

- `5432` interno PostgreSQL
- Volumen persistente `postgres_data`

---

## 4) Como desplegara Gemini sin tocar tu ordenador local

La secuencia correcta es esta:

1. GitHub Actions hace checkout del repo.
2. Se inyectan secretos desde Vault/GitHub Secrets.
3. Se sincroniza el repo hacia las 3 VMs.
4. Se levanta primero PostgreSQL en VM3.
5. Se levanta luego backend en VM2.
6. Se levanta por ultimo frontend en VM1.
7. Se ejecutan health checks.
8. Si algo falla, se hace `docker compose down --remove-orphans` y se deja el sistema limpio para reintentar.

---

## 5) Que debe hacer Gemini en las 3 VMs

### VM3

- Crear la carpeta de despliegue.
- Levantar PostgreSQL 15.
- Montar volumen persistente.
- Exponer solo `5432` en la red interna.

### VM2

- Desplegar issuer y verifier.
- Exponer `8080` como proxy HTTP interno.
- Conectar a la BD por `172.16.4.58:5432`.
- Consumir Sepolia mediante `SEPOLIA_RPC_URL`.

### VM1

- Servir el portal y dashboards con Nginx.
- Exponer `8080` dentro de la VM, mapeado al puerto externo que corresponda.

---

## 6) Detalle importante sobre blockchain

### En desarrollo local

- Puedes seguir usando el flujo local si quieres probar Hardhat.
- Si ya hay contrato local vivo, `start_all.py` y el despliegue local reutilizan ese contrato.
- No redeployamos blockchain en cada arranque si ya está desplegada.

### En produccion

- No hace falta levantar blockchain local.
- El backend debe consumir Sepolia.
- El contrato se gestiona con el artefacto `blockchain_contract.sepolia.json`.
- La clave del issuer vive en el runtime de la VM de backend, no en el frontend.

### Regla de oro

- El frontend nunca firma en blockchain.
- El backend nunca expone claves privadas al navegador.
- La BD guarda estado transaccional, no secretos de firma.

---

## 7) Comandos recomendados de uso diario

```bash
bash scripts/deploy_local.sh
bash scripts/teardown.sh local
bash scripts/deploy_vms.sh
bash scripts/teardown.sh vms
```

---

## 8) Resumen corto

- Local: `deploy_local.sh` y `teardown.sh local`.
- VMs: `deploy_vms.sh` y `teardown.sh vms`.
- BD en prod: PostgreSQL 15.
- Blockchain en prod: Sepolia.
- Frontend separado por roles.
- CI/CD automatizado desde GitHub.
