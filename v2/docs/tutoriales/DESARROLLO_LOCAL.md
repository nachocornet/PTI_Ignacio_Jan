# Tutorial: Desarrollo Local Completo

Guía paso a paso para desarrollar y probar cambios localmente antes de hacer push.

## 1. Setup Inicial (Primera Vez)

### Paso 1: Clonar y entrar en directorio

```bash
git clone https://github.com/tu_usuario/pti-v2.git
cd pti-v2/v2
```

### Paso 2: Setup Python y Node

```bash
# Python virtual env
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r config/requirements.txt

# Node (blockchain)
cd blockchain
npm install
npm run compile
cd ..
```

### Paso 3: Setup completo automático

```bash
python3 scripts/setup_complete.py
```

Esto:
- ✅ Genera wallet del Issuer
- ✅ Genera wallet del Holder
- ✅ Compila contrato Solidity
- ✅ Puebla base de datos con datos de prueba

## 2. Desarrollo Local

### Opción A: Stack completo automático (recomendado)

```bash
# Levanta todo: Hardhat + Issuer + Verifier + Frontend
python3 scripts/start_all.py
```

Se abre automáticamente en `http://127.0.0.1:8080/frontend_portal.html`

**Ventajas:**
- Una sola línea
- Network-aware (local vs Sepolia)
- Reutiliza servicios si ya están corriendo
- Termina con Ctrl+C

### Opción B: Stack por Docker Compose (para cambios en services)

```bash
# Baja cualquier stack anterior
docker compose -f docker-compose-local.yml down --remove-orphans

# Levanta todo con rebuild
docker compose -f docker-compose-local.yml up -d --build

# Ver logs
docker compose -f docker-compose-local.yml logs -f issuer

# Parar
docker compose -f docker-compose-local.yml down
```

### Opción C: Servicios por terminal (para debug)

```bash
# Terminal 1: Hardhat
cd blockchain
npm run node

# Terminal 2: Deploy contrato
cd blockchain
npm run deploy:local
npm run bootstrap:local

# Terminal 3: Issuer
python3 -m uvicorn services.issuer.app:app --reload --host 127.0.0.1 --port 5010

# Terminal 4: Verifier
python3 -m uvicorn services.verifier.app:app --reload --host 127.0.0.1 --port 5011

# Terminal 5: Frontend
python3 frontend/frontend_server.py

# Terminal 6: Abre frontend
open http://127.0.0.1:8080/frontend_portal.html
```

**Ventajas de esta opción:**
- `--reload` detecta cambios en el código automáticamente
- Ves logs en tiempo real
- Perfecto para debugging con breakpoints

## 3. Workflow Típico de Desarrollo

### Día de trabajo normal:

```bash
# Mañana: Levantar stack
python3 scripts/start_all.py

# Editar código en tu editor favorito
# Cambios en services/ se recargan automáticamente (--reload)
# Cambios en frontend/ requieren refresh del navegador

# Hacer cambios en base de datos
python3 scripts/seed_db.py

# Probar manualmente
# 1. Abre http://127.0.0.1:8080/frontend_portal.html
# 2. Emite VC
# 3. Verifica VP
# 4. Revoca y re-verifica

# Ejecutar tests antes de push
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -v

# Cuando termines
bash scripts/teardown.sh local
```

## 4. Testing

### Tests unitarios

```bash
# Ejecutar todos
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q

# Ejecutar uno específico
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_issuer_api.py -v

# Con cobertura
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest --cov=services --cov=shared
```

### Tests manuales (desde navegador)

1. **Issuer Dashboard:**
   - Emite VC con DNI "12345678A"
   - Revoca la VC
   - Verifica que no se pueda usar después

2. **Verifier Dashboard:**
   - Carga wallet
   - Firma VP
   - Verifica que blockchain valida todo

3. **Frontend funcional:**
   - Portal navega a dashboards
   - Variablesde frontend.variables.js se cargan
   - No hay errores en consola del navegador

## 5. Cambios Comunes

### Cambiar puertos

Edita `config/.env` o exporta variables:

```bash
export SSI_ISSUER_PORT=6010
export SSI_VERIFIER_PORT=6011
python3 scripts/start_all.py
```

### Cambiar base de datos

```bash
# Usar PostgreSQL local
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/ssi_dev"
python3 scripts/start_all.py

# Volver a SQLite
unset DATABASE_URL
python3 scripts/start_all.py
```

### Cambiar blockchain (local vs Sepolia)

```bash
# Local (defecto)
export SSI_BLOCKCHAIN_NETWORK=local
python3 scripts/start_all.py

# Sepolia
export SSI_BLOCKCHAIN_NETWORK=sepolia
export SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/YOUR_ID"
python3 scripts/start_all.py
```

## 6. Debugging

### Logs del backend

```bash
# En la terminal donde corre Uvicorn con --reload
# Ves los logs en tiempo real

# O si usas Docker:
docker compose logs -f issuer
docker compose logs -f verifier
```

### Logs del blockchain

```bash
docker logs $(docker ps -q -f ancestor=trufflesuite/ganache-cli) -f
```

### Debugger Python

Añade breakpoint en tu código:

```python
def issue_dni(...):
    breakpoint()  # Se pausa aquí
    # Ahora puedes inspeccionar variables en la terminal
```

### Inspeccionar requests HTTP

```bash
# Terminal: activa verbose logging
curl -v http://127.0.0.1:5010/health

# O usa Chrome DevTools
# 1. Abre DevTools (F12)
# 2. Tab Network
# 3. Emite VC desde el frontend
# 4. Ves todas las requests/responses
```

## 7. Limpieza

### Limpiar todo

```bash
# Parar servicios
bash scripts/teardown.sh local

# Limpiar volúmenes
docker volume rm $(docker volume ls -q)

# Limpiar caché Python
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -name "*.pyc" -delete

# Limpiar node_modules
rm -rf blockchain/node_modules
```

### Resetear base de datos

```bash
# SQLite
rm -f deployments/runtime/ssi_sessions.db
python3 scripts/seed_db.py

# PostgreSQL
psql -U ssi_user -d ssi_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python3 scripts/seed_db.py
```

## 8. Troubleshooting

### "Address already in use"

```bash
# Puerto 5010 (Issuer) ya en uso
lsof -i :5010
kill -9 <PID>

# O cambiar puerto
export SSI_ISSUER_PORT=6010
```

### "Cannot find module"

```bash
# Asegúrate de que PYTHONPATH incluye la raíz
export PYTHONPATH="/path/to/pti-v2/v2:$PYTHONPATH"
python3 scripts/start_all.py
```

### "Blockchain connection failed"

```bash
# Espera un momento a que Hardhat levante
sleep 5
python3 scripts/start_all.py

# O inicia manualmente Hardhat primero
cd blockchain && npm run node &
sleep 2
cd .. && python3 scripts/start_all.py
```

## 9. Mejores Prácticas

✅ **Hazlo así:**
- Ejecuta tests antes de push
- Cambia una cosa a la vez
- Haz commits pequeños y descritos
- Documenta cambios importantes en el código

❌ **No hagas esto:**
- Debuguear directamente en producción
- Commitear archivos `.env` o secrets
- Cambiar múltiples componentes a la vez
- Hacer push sin pasar tests locales

---

**Última actualización:** 28 de Abril de 2026
