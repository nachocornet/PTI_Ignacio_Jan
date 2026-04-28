# Checklist de Producción

Use este documento como guía de validación antes de desplegar a Virtech.

---

## 🔍 Validación Pre-Deploy

### Código y Configuración

- [ ] ✅ Todos los tests pasan
  ```bash
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
  ```

- [ ] ✅ No hay secrets en código
  ```bash
  grep -r "password\|token\|secret" --include="*.py" services/ | grep -v "# " | wc -l
  # Debe ser 0
  ```

- [ ] ✅ Variables de entorno están documentadas
  ```bash
  ls -la config/.env.complete.example
  ```

- [ ] ✅ Docker Compose configs son válidos
  ```bash
  docker compose -f docker-compose-local.yml config > /dev/null
  for f in config/compose_vms/*/docker_compose.yml; do docker compose -f "$f" config > /dev/null; done
  ```

- [ ] ✅ Scripts shell son sintácticamente válidos
  ```bash
  for f in scripts/*.sh; do bash -n "$f"; done
  ```

### Frontend

- [ ] ✅ Frontend portal navega correctamente
  - Abre: http://127.0.0.1:8080/frontend_portal.html
  - Verifica: Links a dashboards funcionan

- [ ] ✅ Dashboards cargan variables correctamente
  - Issuer: http://127.0.0.1:8080/issuer_dashboard.html
  - Verifier: http://127.0.0.1:8080/verifier_dashboard.html
  - Ambos cargan `frontend.variables.js` sin errores 404

- [ ] ✅ No hay archivos legacy (deprecated frontend files)
  ```bash
  ls -la frontend/ | grep -i "admin\|holder"
  # Debe estar vacío
  ```

### Backend

- [ ] ✅ Issuer responde
  ```bash
  curl -s http://127.0.0.1:5010/health | jq .
  ```

- [ ] ✅ Verifier responde
  ```bash
  curl -s http://127.0.0.1:5011/health | jq .
  ```

- [ ] ✅ Endpoints principales sin errores
  ```bash
  # Test Issuer
  curl -X POST http://127.0.0.1:5010/api/credentials/issue_dni \
    -H "Content-Type: application/json" \
    -d '{"holder_address":"0x1234","dni":"12345678A","name":"Test"}'
  
  # Debe retornar 200 o error controlado (no 500)
  ```

### Blockchain

- [ ] ✅ Contrato está deployado
  ```bash
  ls -la deployments/blockchain_contract*.json | wc -l
  # Debe tener al menos 1 archivo
  ```

- [ ] ✅ Para Sepolia: RPC URL es válida
  ```bash
  curl -s -X POST $SEPOLIA_RPC_URL \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"web3_clientVersion","id":1}' \
    | jq .result
  # Debe retornar versión del cliente
  ```

### Base de Datos

- [ ] ✅ SQLite local funciona
  ```bash
  python3 -c "from db.database import SessionLocal; s = SessionLocal(); print('OK')"
  ```

- [ ] ✅ Tablas existen
  ```bash
  python3 scripts/seed_db.py --check
  ```

---

## 🔐 Seguridad Pre-Deploy

### Secrets y Credenciales

- [ ] ✅ Archivo .env no está en git
  ```bash
  git status | grep ".env"
  # Debe estar vacío
  ```

- [ ] ✅ Wallets están en .gitignore
  ```bash
  cat .gitignore | grep "wallet\|issuer"
  ```

- [ ] ✅ GitHub secrets están configurados
  ```bash
  gh secret list | grep -E "SSH_PRIVATE_KEY|DB_PASSWORD|ISSUER_WALLET|SEPOLIA_RPC"
  # Debe mostrar todos
  ```

- [ ] ✅ SSH keys tienen permisos correctos (local)
  ```bash
  ls -la ~/.ssh/id_rsa
  # Debe ser -rw------- (600)
  ```

### Access Control

- [ ] ✅ Frontend no lista directorios
  - http://127.0.0.1:8080/ debe retornar 403 o 404 (no listing)

- [ ] ✅ APIs no exponen stack traces
  ```bash
  # Trigger error deliberado
  curl http://127.0.0.1:5010/api/some-nonexistent-endpoint
  # Debe retornar mensaje genérico (no Python traceback)
  ```

---

## 🚀 Deployment Pre-Checks

### Local

- [ ] ✅ Stack local levanta sin errores
  ```bash
  bash scripts/deploy_local.sh
  # Espera ~2 minutos, verifica health
  bash scripts/teardown.sh local
  ```

### Remoto (3 VMs)

- [ ] ✅ Conectividad SSH a las 3 VMs
  ```bash
  ssh -i ~/.ssh/id_rsa -p 40561 alumne@nattech.fib.upc.edu "echo Frontend OK"
  ssh -i ~/.ssh/id_rsa -p 40571 alumne@nattech.fib.upc.edu "echo Backend OK"
  ssh -i ~/.ssh/id_rsa -p 40581 alumne@nattech.fib.upc.edu "echo DB OK"
  ```

- [ ] ✅ Espacio en disco en las VMs
  ```bash
  ssh -p 40581 alumne@nattech.fib.upc.edu "df -h / | tail -1"
  # Debe tener > 10GB libres
  ```

- [ ] ✅ Docker está disponible en VMs
  ```bash
  ssh -p 40561 alumne@nattech.fib.upc.edu "docker --version"
  ```

### CI/CD

- [ ] ✅ Último commit está en main
  ```bash
  git log --oneline -1 | grep main
  ```

- [ ] ✅ Workflow existe en GitHub
  ```bash
  gh workflow list | grep deploy
  ```

---

## 📊 Performance Checks

### Timing

- [ ] ✅ Tests se ejecutan en < 5 minutos
- [ ] ✅ Deploy local se ejecuta en < 5 minutos
- [ ] ✅ Deploy remoto se ejecuta en < 20 minutos

### Recursos

- [ ] ✅ Memoria: DB < 500MB, Backend < 300MB
- [ ] ✅ CPU: Usage normal (no > 80% continuo)
- [ ] ✅ Disco: Usage < 50% en todas las VMs

---

## 📋 Validación Post-Deploy

Después de desplegar a VMs, verifica:

### Frontend

- [ ] ✅ Portal accesible: http://nattech.fib.upc.edu:40560/frontend_portal.html
- [ ] ✅ Issuer dashboard carga
- [ ] ✅ Verifier dashboard carga
- [ ] ✅ No hay errores 404 en consola del navegador

### Backend

- [ ] ✅ Endpoints health responden
  ```bash
  curl -I http://nattech.fib.upc.edu:40570/health
  ```

### Database

- [ ] ✅ PostgreSQL está corriendo y accesible (desde Backend VM)
- [ ] ✅ Tablas existen
  ```bash
  ssh -p 40571 alumne@nattech.fib.upc.edu \
    "docker exec db psql -U ssi_user -d ssi_db -c '\dt'"
  ```

### E2E Flow

- [ ] ✅ **Emitir VC:**
  1. Abre Issuer Dashboard
  2. Llena formulario (DNI: 12345678A)
  3. Click "Issue"
  4. Recibe VC

- [ ] ✅ **Verificar VP:**
  1. Abre Verifier Dashboard
  2. Carga wallet local
  3. Firma VP con la VC recibida
  4. Click "Verify"
  5. Obtiene ✅ Verified

- [ ] ✅ **Revocar y re-verificar:**
  1. Vuelve a Issuer Dashboard
  2. Click "Revoke" sobre la VC
  3. Vuelve a Verifier Dashboard
  4. Intenta verificar la misma VC
  5. Obtiene ❌ Revoked

---

## 🔧 Troubleshooting Rápido

| Problema | Comando | Solución |
|----------|---------|----------|
| Tests fallan | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -v` | Ver detalles |
| Port conflict | `lsof -i :5010` | Matar proceso |
| SSH fail | `ssh -vvv ...` | Ver detalles SSH |
| DB connection | `psql -U user -d db` | Verificar credentials |
| Docker pull fail | `docker pull postgres:15` | Reintentar |

---

## ✅ Sign-Off

- [ ] **Desarrollador:** Todos los tests pasando
- [ ] **DevOps:** Deploy scripts validados
- [ ] **QA:** E2E flow verificado
- [ ] **Security:** Secrets seguros, no hardcoded
- [ ] **Product:** Features esperados funcionan

---

**Checklist de Producción**  
**Versión:** 1.0  
**Última actualización:** 28 de Abril de 2026
