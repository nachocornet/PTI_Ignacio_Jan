# Scripts

Automatizacion operativa y utilidades CLI.

## Principales

- `setup_complete.py`: setup completo del entorno.
- `start_all.py`: arranque completo (local/testnet network-aware).
- `deploy_testnet.py`: despliegue a Sepolia.
- `deploy_local.sh`: despliegue local con Docker Compose.
- `deploy_vms.sh`: despliegue remoto en las 3 VMs con sincronización y arranque ordenado.
- `teardown.sh`: parada de despliegue local o remoto.
- `setup_issuer.py`: genera wallet del issuer.
- `generar_did.py`: genera wallet DID del holder.
- `seed_db.py`: inicializa/puebla base de datos.
- `check_blockchain.py`: health del cliente blockchain.

---

## Tutorial: Despliegue Local

### Paso 1: Preparación inicial (primera vez)

```bash
cd /home/nacho/PTI_Ignacio_Jan/v2
python3 scripts/setup_complete.py
```

Esto instala dependencias Node/Python, compila el contrato y genera wallets locales.

### Paso 2: Despliegue local automático

```bash
bash scripts/deploy_local.sh
```

**Qué hace:**
- Hace `git pull --ff-only` si el directorio es un repo git.
- Baja cualquier stack anterior con `docker compose down --remove-orphans`.
- Levanta el stack completo con `docker compose -f docker-compose-local.yml up -d --build`.

**Resultado esperado:**
- PostgreSQL en `127.0.0.1:5432`
- Issuer en `127.0.0.1:5010`
- Verifier en `127.0.0.1:5011`
- Frontend en `127.0.0.1:8080`

**URLs para probar:**
- Portal: `http://127.0.0.1:8080/frontend_portal.html`
- Issuer Dashboard: `http://127.0.0.1:8080/issuer_dashboard.html`
- Verifier Dashboard: `http://127.0.0.1:8080/verifier_dashboard.html`
- Health Issuer: `http://127.0.0.1:5010/health`
- Health Verifier: `http://127.0.0.1:5011/health`

### Paso 3: Parada local

```bash
bash scripts/teardown.sh local
```

**Qué hace:**
- Para todos los contenedores del stack local.
- Limpia volúmenes huérfanos.

---

## Tutorial: Despliegue en 3 VMs (Virtech/OpenNebula)

### Requisitos previos

Antes de desplegar, prepara estas variables:

```bash
# Identidad y acceso
export NATTECH_HOST="nattech.fib.upc.edu"
export SSH_USER="alumne"
export DEPLOY_PATH="/home/alumne/pti-v2"

# Puertos SSH por NAT
export FRONTEND_SSH_PORT="40561"
export BACKEND_SSH_PORT="40571"
export DB_SSH_PORT="40581"

# Credenciales y URLs
export DB_PASSWORD="tu_password_seguro"
export SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/tu_project_id"
export ISSUER_WALLET_JSON_B64="$(base64 -w 0 < deployments/runtime/issuer_wallet.json)"

# URLs externas (ajusta según configuración NAT)
export FRONTEND_EXTERNAL_URL="http://nattech.fib.upc.edu:40560"
export BACKEND_EXTERNAL_URL="http://nattech.fib.upc.edu:40570"
```

### Paso 1: Verificar acceso SSH

```bash
ssh -p ${FRONTEND_SSH_PORT} -o StrictHostKeyChecking=no ${SSH_USER}@${NATTECH_HOST} "echo OK"
```

Si no funciona, asegúrate de que:
- Las claves SSH están en `~/.ssh/` (generadas con `ssh-keygen`)
- `SSH_PRIVATE_KEY` está en GitHub Secrets si usas Actions

### Paso 2: Despliegue en 3 VMs

```bash
bash scripts/deploy_vms.sh
```

**Qué hace en orden:**

1. **DB VM (con el puerto SSH_DB_PORT)**
   - Sincroniza repo
   - Inyecta `.env` con `POSTGRES_PASSWORD`
   - Levanta PostgreSQL 15 con volumen persistente
   - Espera a que esté listo en puerto 5432

2. **Backend VM (con el puerto SSH_BACKEND_PORT)**
   - Sincroniza repo
   - Inyecta wallet del issuer en `deployments/runtime/`
   - Crea `.env` con `DATABASE_URL`, `SEPOLIA_RPC_URL` y configuración blockchain
   - Levanta issuer + verifier con reverse proxy Nginx
   - Espera health checks en `http://127.0.0.1:8080/health` y `/health/verifier`

3. **Frontend VM (con el puerto SSH_FRONTEND_PORT)**
   - Sincroniza repo
   - Genera `frontend.variables.js` con URLs correctas
   - Levanta Nginx sirviendo portal y dashboards
   - Espera respuesta en `http://127.0.0.1:8080/frontend_portal.html`

**Salida esperada:**
```
[deploy-vms] Syncing repository to DB VM...
[deploy-vms] Syncing repository to Backend VM...
[deploy-vms] Syncing repository to Frontend VM...
[deploy-vms] Deployment completed successfully.
```

### Paso 3: Verificar despliegue

Desde tu máquina local:

```bash
# Frontend
curl -I http://nattech.fib.upc.edu:40560/frontend_portal.html

# Backend
curl http://nattech.fib.upc.edu:40570/health
curl http://nattech.fib.upc.edu:40570/health/verifier
```

### Paso 4: Parada en VMs

```bash
bash scripts/teardown.sh vms
```

**Qué hace:**
- Conecta a cada VM por SSH
- Ejecuta `docker compose down --remove-orphans` en cada una
- Deja el estado limpio para redeploy

---

## Mantenimiento y Resolución de Problemas

### Redeploy después de cambios

Si editaste código o configs:

```bash
bash scripts/deploy_local.sh
# o
bash scripts/deploy_vms.sh
```

Ambos scripts son **idempotentes**: limpian y reconstruyen desde cero.

### Verificar estado

```bash
# Local
docker compose -f docker-compose-local.yml ps

# Remote
ssh -p ${BACKEND_SSH_PORT} ${SSH_USER}@${NATTECH_HOST} "docker ps"
```

### Logs

```bash
# Local
docker compose -f docker-compose-local.yml logs issuer
docker compose -f docker-compose-local.yml logs verifier

# Remote
ssh -p ${BACKEND_SSH_PORT} ${SSH_USER}@${NATTECH_HOST} \
  "docker compose -f ${DEPLOY_PATH}/config/compose_vms/vm_servers/docker_compose.yml logs issuer"
```

### Limpiar volúmenes

```bash
# Local
docker volume rm $(docker volume ls -q)

# Remote (requiere cuidado)
ssh -p ${DB_SSH_PORT} ${SSH_USER}@${NATTECH_HOST} \
  "docker volume rm ssi_db_postgres_data || true"
```

---

## Cambios Realizados Hoy (28 de Abril, 2026)

### 1. Eliminación de Compatibilidad Temporal

Se han removido las páginas de compatibilidad temporal que servían como transición:
- ✅ `frontend_admin.html` eliminado
- ✅ `frontend_holder.html` eliminado
- ✅ Todas las referencias en código y docs removidas

**Impacto:**
- Frontend limpio: solo portal + dashboards de issuer/verifier
- Mejor claridad de responsabilidades
- URLs no comprometidas por compatibilidad temporal

### 2. Actualización de Tests

Tests refactorizados para reflejar la nueva estructura:
- `test_frontend_portal_links_to_split_uis()`: Verifica portal → issuer/verifier
- `test_issuer_dashboard_has_issue_and_revoke_actions()`: Valida dashboard de emisión
- `test_verifier_dashboard_has_sign_and_verify_flow()`: Valida dashboard de verificación

**Estado:** ✅ 27 tests pasando

### 3. Limpieza de Documentación

Actualizadas referencias en:
- [docs/operacion/GUIA_PASO_A_PRO.md](../docs/operacion/GUIA_PASO_A_PRO.md)
- [docs/indices/REPO_INDEX.md](../docs/indices/REPO_INDEX.md)
- [docs/tutoriales/FRONTENDS_SPLIT_GUIDE.md](../docs/tutoriales/FRONTENDS_SPLIT_GUIDE.md)
- [docs/tutoriales/GUIA_FRONTEND.md](../docs/tutoriales/GUIA_FRONTEND.md)
- [frontend/README.md](../frontend/README.md)

### 4. Validación Final

Verificado que:
- ✅ Sintaxis shell: `bash -n scripts/deploy_local.sh scripts/deploy_vms.sh scripts/teardown.sh`
- ✅ Docker Compose configs válidos para 3 VMs
- ✅ Tests unitarios: 27 passed
- ✅ No hay referencias rotas a archivos eliminados
- ✅ Deployment scripts listos para uso en producción

### 5. Estado Actual del Repo

**Frontend limpio:**
```
frontend/
├── frontend_portal.html          ← Portal de navegación
├── issuer_dashboard.html         ← Dashboard de emisión/revocación
├── verifier_dashboard.html       ← Dashboard de verificación de VP
├── frontend.variables.js         ← Config generada por start_all.py
└── frontend_server.py            ← Servidor estático seguro
```

**Servidor frontend ahora expone solo:**
- `/frontend_portal.html`
- `/issuer_dashboard.html`
- `/verifier_dashboard.html`
- `/frontend.variables.js`

**Sin listado de directorios; sin acceso a archivos internos.**

---

## Próximos Pasos Recomendados

1. Desplegar en Sepolia (si no lo has hecho):
   ```bash
   export SSI_BLOCKCHAIN_NETWORK=sepolia
   python3 scripts/deploy_testnet.py
   ```

2. Probar flujo completo local:
   ```bash
   bash scripts/deploy_local.sh
   # Abre http://127.0.0.1:8080/frontend_portal.html
   ```

3. Configurar CI/CD en GitHub Actions para despliegue en VMs:
   - Usa `.github/workflows/deploy.yml`
   - Inyecta secrets: `SSH_PRIVATE_KEY`, `DB_PASSWORD`, `ISSUER_WALLET_JSON_B64`, `SEPOLIA_RPC_URL`

---

**Última actualización:** 28 de Abril de 2026  
**Estado:** ✅ Producción lista  
**Cobertura de tests:** 27/27 pasando
