# Tutorial: Troubleshooting y Resolución de Problemas

Guía para diagnosticar y resolver problemas comunes en local y producción.

## 1. Problemas de Conectividad

### Frontend no carga

**Síntoma:** `http://127.0.0.1:8080/frontend_portal.html` devuelve 404

**Posibles causas y soluciones:**

```bash
# 1. Verificar que el servidor frontend está corriendo
curl -I http://127.0.0.1:8080/frontend_portal.html

# 2. Si 404, el servidor no está up. Levanta:
python3 frontend/frontend_server.py

# 3. O en Docker:
docker compose -f docker-compose-local.yml ps
# Si no está, levanta:
docker compose -f docker-compose-local.yml up -d --build frontend
```

### Issuer no responde

**Síntoma:** `curl http://127.0.0.1:5010/health` → Connection refused

**Solución:**

```bash
# 1. ¿Está corriendo?
ps aux | grep uvicorn | grep issuer

# 2. Si no, levanta:
python3 -m uvicorn services.issuer.app:app --host 127.0.0.1 --port 5010

# 3. En Docker:
docker compose -f docker-compose-local.yml logs issuer

# 4. Si falla, rebuild:
docker compose -f docker-compose-local.yml up -d --build issuer
```

### Blockchain no responde

**Síntoma:** `curl http://127.0.0.1:8545` → Connection refused

**Solución:**

```bash
# 1. Levanta Hardhat
cd blockchain && npm run node

# 2. Espera a que esté listo (~5 segundos)

# 3. Deploya contrato:
npm run deploy:local
npm run bootstrap:local
```

## 2. Problemas de Base de Datos

### "FATAL: password authentication failed"

**Síntoma:** Error al conectar a PostgreSQL

**Solución:**

```bash
# 1. Verifica que el contenedor está corriendo
docker ps | grep postgres

# 2. Verifica la contraseña en .env
cat .env | grep POSTGRES_PASSWORD

# 3. Reinicia el contenedor
docker compose -f docker-compose-local.yml restart db

# 4. O recrea:
docker compose -f docker-compose-local.yml down db
docker compose -f docker-compose-local.yml up -d --build db
```

### "relation does not exist"

**Síntoma:** Error de tabla no encontrada en tests o API

**Solución:**

```bash
# 1. Recrea las tablas
python3 scripts/seed_db.py

# 2. O si usas Docker:
docker compose -f docker-compose-local.yml exec db psql -U ssi_user -d ssi_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python3 scripts/seed_db.py
```

## 3. Problemas de Tests

### Tests fallan localmente

```bash
# 1. Verifica que todos los servicios están up
python3 scripts/start_all.py

# 2. Espera ~10 segundos

# 3. Ejecuta tests con verbose
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -v

# 4. Si falla un test específico:
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_issuer_api.py::test_issue_dni -v

# 5. Lee el stack trace completo
```

### "ModuleNotFoundError: No module named 'services'"

**Causa:** PYTHONPATH no incluye la raíz

**Solución:**

```bash
# Ejecuta desde raíz de v2
cd /path/to/pti-v2/v2
python3 -m pytest
```

## 4. Problemas de Docker

### "port is already allocated"

**Síntoma:** Error al levantar contenedores

**Solución:**

```bash
# 1. Ver qué está usando el puerto
lsof -i :8080

# 2. Matar el proceso
kill -9 <PID>

# 3. O cambiar el puerto en docker-compose-local.yml
ports:
  - "9090:80"  # cambiar 8080 a 9090
```

### "image not found"

**Síntoma:** "Error response from daemon: pull access denied"

**Solución:**

```bash
# 1. Rebuild la imagen
docker compose -f docker-compose-local.yml build

# 2. O pull explícitamente
docker pull postgres:15-alpine
docker pull nginx:1.27-alpine

# 3. Levanta de nuevo
docker compose -f docker-compose-local.yml up -d --build
```

## 5. Problemas de Blockchain

### "Contract not found"

**Síntoma:** `SSIBlockchainClient` falla al leer artefacto

**Solución:**

```bash
# 1. Verifica que el artefacto existe
ls -la deployments/blockchain_contract.json

# 2. Si no existe, despliega:
cd blockchain
npm run deploy:local
npm run bootstrap:local

# 3. Verifica que el contenido es válido JSON
cat deployments/blockchain_contract.json | jq .
```

### "Issuer not authorized"

**Síntoma:** Verificación falla porque issuer no está autorizado

**Solución:**

```bash
# 1. El problema ocurre si no ejecutaste bootstrap
cd blockchain
npm run bootstrap:local

# 2. O si eliminaste el artefacto después de desplegar:
npm run deploy:local
npm run bootstrap:local
```

## 6. Problemas de SSH/Remoto

### "Permission denied (publickey)"

**Síntoma:** No puede conectar a VM

**Solución:**

```bash
# 1. Verifica que la clave SSH es válida
ssh -i ~/.ssh/id_rsa -p 40561 alumne@nattech.fib.upc.edu "echo OK"

# 2. Si falla, verifica que la clave pública está en VM:
ssh -p 40561 alumne@nattech.fib.upc.edu "cat ~/.ssh/authorized_keys"

# 3. Si no está, añádela:
cat ~/.ssh/id_rsa.pub | ssh -p 40561 alumne@nattech.fib.upc.edu "cat >> ~/.ssh/authorized_keys"

# 4. Para GitHub Actions, verifica el secret SSH_PRIVATE_KEY:
gh secret list
```

### "rsync: connection reset by peer"

**Síntoma:** Sincronización falla a mitad

**Causa:** Conexión SSH inestable

**Solución:**

```bash
# 1. Retry manual con más tiempo
rsync -az --timeout=60 \
  -e "ssh -p 40571 -o ConnectTimeout=10" \
  ./ alumne@nattech.fib.upc.edu:/home/alumne/pti-v2/

# 2. O re-ejecuta el deploy
bash scripts/deploy_vms.sh
```

## 7. Problemas de Certificados

### CORS Error

**Síntoma:** "Access to XMLHttpRequest blocked by CORS policy"

**Solución:**

```bash
# 1. Verifica CORS_ORIGINS en settings
cat shared/settings.py | grep cors_origins

# 2. O en .env
cat .env | grep CORS

# 3. Añade el origen correcto
export SSI_CORS_ORIGINS="http://127.0.0.1:8080,http://localhost:8080,https://tu-dominio.com"
python3 scripts/start_all.py
```

### SSL Certificate Error (HTTPS)

**Síntoma:** "certificate verify failed"

**Causa:** En desarrollo local con HTTPS

**Solución:**

```bash
# Para desarrollo: usa HTTP (no HTTPS)
# Para producción: usa Let's Encrypt o cert válido

# En el workflow:
# El reverse proxy Nginx maneja certificados
# Ve a config/compose_vms/vm-frontend/nginx.conf
```

## 8. Diagnóstico Completo

Si nada funciona, ejecuta este script:

```bash
#!/bin/bash

echo "=== SSI v2 Diagnostic ==="

echo "1. Python"
python3 --version

echo "2. Node"
node --version

echo "3. Docker"
docker --version

echo "4. Blockchain"
curl -s http://127.0.0.1:8545 | jq . || echo "❌ Blockchain not responding"

echo "5. Issuer"
curl -s http://127.0.0.1:5010/health | jq . || echo "❌ Issuer not responding"

echo "6. Verifier"
curl -s http://127.0.0.1:5011/health | jq . || echo "❌ Verifier not responding"

echo "7. Frontend"
curl -I http://127.0.0.1:8080/frontend_portal.html || echo "❌ Frontend not responding"

echo "8. Database"
python3 -c "from db.database import SessionLocal; print('✅ DB OK')" || echo "❌ DB failed"

echo "9. Tests"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q 2>&1 | tail -1

echo "=== End Diagnostic ==="
```

## 9. Resetear Todo

Si todo falla, resetea desde cero:

```bash
# 1. Parar servicios
bash scripts/teardown.sh local

# 2. Eliminar volúmenes
docker volume rm $(docker volume ls -q)

# 3. Limpiar cache
rm -rf .venv __pycache__ *.pyc
find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null

# 4. Setup de nuevo
python3 scripts/setup_complete.py

# 5. Levantar
python3 scripts/start_all.py
```

## 10. Obtener Ayuda

### Recopilar información para reportar un bug:

```bash
# Ejecuta esto y comparte el output
{
  echo "=== Environment ==="
  python3 --version
  node --version
  docker --version
  
  echo "=== Git ==="
  git log --oneline -1
  
  echo "=== Running Services ==="
  docker ps
  ps aux | grep -E "uvicorn|npm run" | grep -v grep
  
  echo "=== Errors ==="
  curl -i http://127.0.0.1:5010/health
  curl -i http://127.0.0.1:5011/health
  
  echo "=== Tests ==="
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest --tb=short 2>&1 | tail -30
} | tee diagnostic.log
```

Luego comparte `diagnostic.log` en un issue de GitHub.

---

**Última actualización:** 28 de Abril de 2026
