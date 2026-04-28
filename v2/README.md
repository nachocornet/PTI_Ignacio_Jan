# SSI v2 - Repositorio Completamente Automatizado

Repositorio de **Self-Sovereign Identity v2** con arquitectura de 3 tiers, deployment automatizado, CI/CD con GitHub Actions y documentación completa.

**Status:** ✅ **Producción Lista** (27/27 tests pasando)

---

## 🚀 Inicio Rápido (Local)

### 1. Preparación (primera vez)

```bash
cd /path/to/pti-v2/v2

# Virtual env + dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r config/requirements.txt

# Setup automático (dependencies, wallets, DB, contrato)
python3 scripts/setup_complete.py
```

### 2. Arranque automático

```bash
python3 scripts/start_all.py
```

Se abre automáticamente en: **http://127.0.0.1:8080/frontend_portal.html**

### 3. Parada

```bash
bash scripts/teardown.sh local
```

---

## 📚 Documentación Completa

### Tutoriales Prácticos

| Tutorial | Contenido |
|----------|-----------|
| [DESARROLLO_LOCAL.md](docs/tutoriales/DESARROLLO_LOCAL.md) | Flujo de desarrollo local completo con debug |
| [CI_CD_GITHUB_ACTIONS.md](docs/tutoriales/CI_CD_GITHUB_ACTIONS.md) | Setup de GitHub Actions + troubleshooting |
| [TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md) | Diagnóstico y resolución de problemas |
| [TESTNET_QUICKSTART.md](docs/tutoriales/TESTNET_QUICKSTART.md) | Deploy rápido a Sepolia |
| [GUIA_FRONTEND.md](docs/tutoriales/GUIA_FRONTEND.md) | Uso de la interfaz web |
| [FRONTENDS_SPLIT_GUIDE.md](docs/tutoriales/FRONTENDS_SPLIT_GUIDE.md) | Dashboards separados por rol |

### Documentación Operativa

| Doc | Contenido |
|-----|----------|
| [scripts/README.md](scripts/README.md) | Tutoriales de deploy local y 3 VMs |
| [docs/operacion/GUIA_PASO_A_PRO.md](docs/operacion/GUIA_PASO_A_PRO.md) | Paso a paso para producción |
| [docs/operacion/PROPUESTA_DESPLIEGUE_3VM.md](docs/operacion/PROPUESTA_DESPLIEGUE_3VM.md) | Arquitectura detallada 3 VMs |

### Referencia Técnica

| Doc | Contenido |
|-----|----------|
| [REPORT.md](REPORT.md) | Estado completo del proyecto ✨ NUEVO |
| [docs/indices/REPO_INDEX.md](docs/indices/REPO_INDEX.md) | Inventario de archivos |
| [docs/referencia/GUIA_CODIGO_Y_CAMBIOS.md](docs/referencia/GUIA_CODIGO_Y_CAMBIOS.md) | Cambios arquitectónicos |
| [docs/referencia/EU_PROFILE.md](docs/referencia/EU_PROFILE.md) | Alineación técnica europea |

---

## 🏗️ Estructura del Proyecto

```
v2/
├── services/                          # Microservicios FastAPI
│   ├── issuer/                        # API emisión de VC
│   └── verifier/                      # API verificación de VP
├── frontend/                          # Web estática segura
│   ├── frontend_portal.html           # Navegación
│   ├── issuer_dashboard.html          # Emisión
│   ├── verifier_dashboard.html        # Verificación
│   └── frontend_server.py             # Servidor sin directory listing
├── db/                                # Capa de datos SQLAlchemy
├── shared/                            # Código compartido
│   ├── settings.py                    # Config centralizada
│   └── blockchain_client.py           # Web3 wrapper
├── blockchain/                        # Hardhat + Solidity
│   └── contracts/SSIRegistry.sol      # Contrato inteligente
├── scripts/                           # Automatización
│   ├── setup_complete.py              # Setup inicial
│   ├── start_all.py                   # Arranque automático
│   ├── deploy_local.sh                # Deploy local
│   ├── deploy_vms.sh                  # Deploy remoto (3 VMs)
│   └── teardown.sh                    # Parada
├── config/                            # Configuración
│   ├── .env.example                   # Env básico
│   ├── .env.complete.example          # Documentación completa ✨
│   ├── requirements.txt               # Dependencias Python
│   └── compose_vms/                   # Docker Compose por VM
├── deployments/                       # Runtime (wallets, DB, artefactos)
├── tests/                             # 27 tests automatizados
├── docs/                              # Documentación completa
├── docker-compose-local.yml           # Stack local (1 comando)
├── Dockerfile                         # Imagen Python optimizada
├── REPORT.md                          # Estado completo ✨ NUEVO
└── .github/workflows/deploy.yml       # CI/CD GitHub Actions
```

---

## 🔧 Configuración (Variables de Entorno)

### Archivo de Ejemplo Básico

```bash
cat config/.env.example
```

### Documentación Exhaustiva

```bash
cat config/.env.complete.example    # Todas las variables disponibles
```

### Categorías principales:

- **Red local:** `SSI_APP_HOST`, `SSI_ISSUER_PORT`, `SSI_VERIFIER_PORT`, `SSI_FRONTEND_PORT`
- **Blockchain:** `SSI_BLOCKCHAIN_NETWORK` (local|sepolia), `SEPOLIA_RPC_URL`
- **Database:** `DATABASE_URL` (PostgreSQL producción, SQLite local por defecto)
- **VMs Virtech:** `NATTECH_HOST`, `SSH_USER`, `DEPLOY_PATH`, puertos SSH, credentials

---

## 📦 Deployment

### Local (1 comando)

```bash
bash scripts/deploy_local.sh
```

### Remote (3 VMs en Virtech)

```bash
# Setup env vars (ver scripts/README.md)
bash scripts/deploy_vms.sh
```

### CI/CD Automático (GitHub)

1. Configura secrets en GitHub (ver [CI_CD_GITHUB_ACTIONS.md](docs/tutoriales/CI_CD_GITHUB_ACTIONS.md))
2. Push a main → Pipeline automático

---

## ✅ Testing

```bash
# Todos los tests (27 pasando)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q

# Uno específico
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_issuer_api.py::test_issue_dni -v

# Con cobertura
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest --cov=services --cov=shared
```

---

## 🔍 Health Checks

```bash
# Issuer
curl http://127.0.0.1:5010/health

# Verifier
curl http://127.0.0.1:5011/health

# Frontend
curl -I http://127.0.0.1:8080/frontend_portal.html

# Blockchain (local)
curl -X POST http://127.0.0.1:8545 -d '{"jsonrpc":"2.0","method":"web3_clientVersion","id":1}'
```

---

## 🐛 Troubleshooting

### Problema: `Address already in use`

```bash
lsof -i :5010
kill -9 <PID>
```

### Problema: Tests fallan

```bash
# Asegúrate de que el stack está up
python3 scripts/start_all.py

# Espera 5 segundos y prueba de nuevo
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

**Ver más:** [docs/tutoriales/TROUBLESHOOTING.md](docs/tutoriales/TROUBLESHOOTING.md)

---

## 📊 Estado del Proyecto

**Status:** ✅ **Producción Lista**

| Componente | Status | Detalles |
|-----------|--------|---------|
| Backend | ✅ Prod | Issuer + Verifier + Rate limiting |
| Frontend | ✅ Prod | Portal + Dashboards (issuer/verifier) |
| Blockchain | ✅ Prod | Local + Sepolia |
| Database | ✅ Prod | SQLite local, PostgreSQL prod |
| Tests | ✅ 27/27 | Coverage completo |
| CI/CD | ✅ GitHub | Automático en push |
| Deployment | ✅ 3 VMs | SSH orchestrated |
| Docs | ✅ 11 docs | Completo |

**Ver más detalles:** [REPORT.md](REPORT.md) ✨

---

## 🎯 Cambios Recientes (28 Abril 2026)

✨ **Nuevos en este release:**

- 🔧 **Automatización mejorada**
  - Env variables centralizadas y documentadas
  - `config/.env.complete.example` con todas las opciones

- 📚 **3 nuevos tutoriales**
  - `DESARROLLO_LOCAL.md` - Desarrollo local completo
  - `CI_CD_GITHUB_ACTIONS.md` - Setup de CI/CD
  - `TROUBLESHOOTING.md` - Diagnóstico de problemas

- 📋 **REPORT.md** - Estado completo del proyecto

- ✅ **Limpieza final**
  - Eliminados frontends de compatibilidad temporal
  - Refs actualizadas
  - Tests refactorizados (27/27 pasando)

---

## 🤝 Próximos Pasos (Opcional)

Si quieres evolucionar el proyecto:

1. **Observabilidad:** Prometheus + Grafana
2. **Seguridad:** Vault para secrets, HTTPS/TLS
3. **Performance:** Redis cache, CDN
4. **Features:** Multi-chain, backup automático
5. **DevEx:** Devcontainers, pre-commit hooks

---

## 📖 Índice Completo de Docs

```
docs/
├── README.md
├── indices/
│   ├── README.md
│   └── REPO_INDEX.md
├── tutoriales/
│   ├── README.md
│   ├── DESARROLLO_LOCAL.md          ✨ NUEVO
│   ├── CI_CD_GITHUB_ACTIONS.md      ✨ NUEVO
│   ├── TROUBLESHOOTING.md           ✨ NUEVO
│   ├── TESTNET_QUICKSTART.md
│   ├── INFURA_SEPOLIA_GUIDE.md
│   ├── GUIA_FRONTEND.md
│   └── FRONTENDS_SPLIT_GUIDE.md
├── operacion/
│   ├── README.md
│   ├── DOCUMENTACION_DEFINITIVA.md
│   ├── GUIA_PASO_A_PRO.md
│   └── PROPUESTA_DESPLIEGUE_3VM.md
└── referencia/
    ├── README.md
    ├── GUIA_CODIGO_Y_CAMBIOS.md
    └── EU_PROFILE.md
```

---

## 🏆 Checklist de Productividad

- ✅ Backend 100% funcional
- ✅ Frontend limpio (portal + 2 dashboards)
- ✅ Tests automatizados (27/27 pasando)
- ✅ Deployment local (1 comando)
- ✅ Deployment remoto 3 VMs (SSH orchestrated)
- ✅ CI/CD automático (GitHub Actions)
- ✅ Env variables centralizadas
- ✅ Documentación completa (11+ documentos)
- ✅ Troubleshooting guide
- ✅ Seguridad (secrets management)

---

**Última actualización:** 28 de Abril de 2026  
**Versión:** 2.0  
**Status:** ✅ Completamente Funcional


## Test Suite

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

## Despliegue Sepolia

```bash
python3 scripts/deploy_testnet.py
```

## Documentacion

Punto de entrada recomendado: `docs/README.md`
