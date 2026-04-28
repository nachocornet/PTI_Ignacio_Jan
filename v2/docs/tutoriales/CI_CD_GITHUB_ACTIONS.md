# Tutorial: CI/CD con GitHub Actions

Este documento explica cómo configurar y usar el pipeline automático de CI/CD para despliegue en las 3 VMs de Virtech.

## 1. Configuración Inicial (Una sola vez)

### Paso 1.1: Preparar Secrets en GitHub

Ve a **Settings → Secrets and variables → Actions** en tu repositorio GitHub y crea estos secrets:

```
SSH_PRIVATE_KEY              ← Clave privada SSH (cat ~/.ssh/id_rsa)
SSH_KNOWN_HOSTS              ← Hosts conocidos (ssh-keyscan nattech.fib.upc.edu -p 40561,40571,40581)
DB_PASSWORD                  ← Password de PostgreSQL
ISSUER_WALLET_JSON_B64       ← Base64 del issuer wallet (base64 -w 0 < deployments/runtime/issuer_wallet.json)
SEPOLIA_RPC_URL              ← URL RPC de Sepolia (https://sepolia.infura.io/v3/...)
```

**Cómo obtener SSH_KNOWN_HOSTS:**

```bash
ssh-keyscan -t rsa nattech.fib.upc.edu -p 40561 >> ~/.ssh/known_hosts 2>/dev/null
ssh-keyscan -t rsa nattech.fib.upc.edu -p 40571 >> ~/.ssh/known_hosts 2>/dev/null
ssh-keyscan -t rsa nattech.fib.upc.edu -p 40581 >> ~/.ssh/known_hosts 2>/dev/null
cat ~/.ssh/known_hosts | tail -3
```

Copia la salida y pégala en el secret `SSH_KNOWN_HOSTS`.

### Paso 1.2: Verificar Acceso SSH

Desde tu máquina local:

```bash
ssh -i ~/.ssh/id_rsa -p 40561 alumne@nattech.fib.upc.edu "echo OK from Frontend"
ssh -i ~/.ssh/id_rsa -p 40571 alumne@nattech.fib.upc.edu "echo OK from Backend"
ssh -i ~/.ssh/id_rsa -p 40581 alumne@nattech.fib.upc.edu "echo OK from DB"
```

Si funcionan, los secrets están bien configurados.

## 2. Flujo de Despliegue Automático

### El workflow se ejecuta cuando:

- ✅ Haces **push a main** (trigger automático)
- ✅ Haces **manual trigger** (workflow_dispatch en GitHub UI)

### Qué ocurre en cada push a main:

```
1. Test Job (Ubuntu)
   └─ Checkout código
   └─ Setup Python 3.10
   └─ Instala dependencias
   └─ Ejecuta pytest (27 tests)
   └─ Si falla: pipeline se detiene
   
2. Deploy DB Job (depende de Test ✓)
   └─ SSH a DB VM (puerto 40581)
   └─ Sincroniza código
   └─ Inyecta .env con POSTGRES_PASSWORD
   └─ Levanta PostgreSQL 15
   └─ Espera health check
   
3. Deploy Backend Job (depende de Deploy DB ✓)
   └─ SSH a Backend VM (puerto 40571)
   └─ Sincroniza código
   └─ Inyecta issuer wallet
   └─ Inyecta .env con DATABASE_URL, SEPOLIA_RPC_URL
   └─ Levanta Issuer + Verifier + Nginx reverse proxy
   └─ Espera health checks
   
4. Deploy Frontend Job (depende de Deploy Backend ✓)
   └─ SSH a Frontend VM (puerto 40561)
   └─ Sincroniza código
   └─ Genera frontend.variables.js con URLs correctas
   └─ Levanta Nginx con portal + dashboards
   └─ Espera portal accesible
```

## 3. Monitoreo del Pipeline

### Desde GitHub UI:

1. Ve a **Actions**
2. Selecciona el workflow **Deploy SSI v2**
3. Verás los últimos runs con sus estados:
   - 🟢 Green = Todo OK
   - 🔴 Red = Fallo en algún job
   - 🟡 Yellow = En progreso

### Desde línea de comandos:

```bash
# Ver logs en tiempo real
gh run list --workflow deploy.yml --limit 1

# Ver detalles de un run específico
gh run view <RUN_ID> --log

# Re-ejecutar un run fallido
gh run rerun <RUN_ID>
```

## 4. Troubleshooting

### El test falla

```bash
# Verifica que pytest pasa localmente
cd /home/nacho/PTI_Ignacio_Jan/v2
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q

# Si falla localmente, arreglalo y haz push de nuevo
```

### La sincronización SSH falla

```
Error: "Could not resolve hostname"
```

**Solución:**
- Verifica que SSH_KNOWN_HOSTS tiene las 3 VMs
- Comprueba que SSH_PRIVATE_KEY es válida
- Asegúrate de que las claves SSH públicas están en `/home/alumne/.ssh/authorized_keys` en cada VM

### El backend falla por DATABASE_URL

```
Error: "could not translate host name "db" to address"
```

**Causa:** El DATABASE_URL no apunta a la IP correcta de DB VM

**Solución:** En `.github/workflows/deploy.yml`, asegúrate de que `DATABASE_URL` apunta a `172.16.4.58:5432` (IP interna de DB VM)

### El frontend no carga

```
Error: 404 on /frontend_portal.html
```

**Causa:** Nginx no está sirviendo los archivos

**Solución:**
```bash
ssh -p 40561 alumne@nattech.fib.upc.edu \
  "docker logs $(docker ps -q -f label=com.docker.compose.service=frontend)"
```

## 5. Despliegue Manual (Fallback)

Si el CI/CD falla y necesitas desplegar manualmente:

```bash
# Exportar todas las variables
export NATTECH_HOST="nattech.fib.upc.edu"
export SSH_USER="alumne"
export DEPLOY_PATH="/home/alumne/pti-v2"
export FRONTEND_SSH_PORT="40561"
export BACKEND_SSH_PORT="40571"
export DB_SSH_PORT="40581"
export DB_PASSWORD="tu_password"
export ISSUER_WALLET_JSON_B64="$(base64 -w 0 < deployments/runtime/issuer_wallet.json)"
export SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/..."

# Ejecutar despliegue local
bash scripts/deploy_vms.sh
```

## 6. Rollback Rápido

Si algo sale mal en producción:

```bash
# Opción 1: Teardown completo (más limpio)
export DB_SSH_PORT="40581"
export BACKEND_SSH_PORT="40571"
export FRONTEND_SSH_PORT="40561"
bash scripts/teardown.sh vms

# Opción 2: Revertir a commit anterior y re-desplegar
git revert HEAD
git push origin main
# → GitHub Actions ejecuta el nuevo pipeline automáticamente
```

## 7. Secretos Seguros (Mejores Prácticas)

### ✅ Hazlo así:

```bash
# Secrets en GitHub
SSH_PRIVATE_KEY: xxxxxxx (GitHub Secrets)
DB_PASSWORD: xxxxxxx (GitHub Secrets)

# Inyección en workflow
echo "${{ secrets.DB_PASSWORD }}" → variable de shell → .env → Docker
```

### ❌ No hagas esto:

```bash
# Nunca comitees credenciales
git add .env
git commit -m "Add credentials"  # ❌ NUNCA

# Nunca pongas secrets en logs
echo "DB_PASSWORD=${{ secrets.DB_PASSWORD }}"  # ❌ Visible en logs
```

### Limpiar secretos de logs:

En `.github/workflows/deploy.yml`, evita echo de secrets:

```yaml
# ❌ Malo - se ve en logs
- run: echo "SEPOLIA_RPC_URL=${{ secrets.SEPOLIA_RPC_URL }}"

# ✅ Bueno - se redacta automáticamente
env:
  SEPOLIA_RPC_URL: ${{ secrets.SEPOLIA_RPC_URL }}
run: ./scripts/deploy_vms.sh
```

## 8. Verificación Post-Despliegue

Una vez que GitHub Actions termina (verde):

```bash
# 1. Test frontend
curl -I http://nattech.fib.upc.edu:40560/frontend_portal.html

# 2. Test backend health
curl http://nattech.fib.upc.edu:40570/health
curl http://nattech.fib.upc.edu:40570/health/verifier

# 3. Test flujo completo (desde navegador)
# Abre: http://nattech.fib.upc.edu:40560/frontend_portal.html
# → Click "Issuer Dashboard"
# → Emite una VC
# → Click "Verifier Dashboard"
# → Verifica la VP
```

## 9. Estadísticas y Monitoreo

### Tiempo típico de despliegue:

- Test: ~1-2 minutos
- Deploy DB: ~3-4 minutos
- Deploy Backend: ~4-5 minutos
- Deploy Frontend: ~2-3 minutos
- **Total: ~10-15 minutos**

### Para acelerar:

1. Cachea las dependencias de Python
2. Usa buildkit de Docker (requiere premium de Actions)
3. Paraleliza Deploy Backend y Frontend (requiere cambios en workflow)

---

**Última actualización:** 28 de Abril de 2026
