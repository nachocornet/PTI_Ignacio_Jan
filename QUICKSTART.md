# SSI v2 - Guía de Inicio Rápido

## Estado del Proyecto

✅ **COMPLETO Y OPERATIVO**

Se han terminado:
- ✓ Entrega 1: Blockchain local + Smart contract + Deploy
- ✓ Entrega 2: Verificación on-chain + Revocación
- ✓ Refactorización: Setup automatizado + Frontend web
- ✓ Documentación: README completo + APIs documentadas

## Para Mañana: Comienza Aquí

### 1. Clone/Pull el Código

```bash
# Si es la primera vez:
git clone https://github.com/nachocornet/PTI_Ignacio_Jan.git
cd PTI_Ignacio_Jan/v2

# Si ya tienes el repo:
cd v2
git pull origin main
```

### 2. Setup (Una sola vez)

```bash
python3 setup_complete.py
```

Esto automaticamente:
- Instala dependencias Node y Python
- Compila el contrato Solidity
- Crea wallets de issuer y holder
- Prepara la base de datos

**Tiempo estimado: 3-5 minutos**

### 3. Inicia TODO

```bash
python3 start_all.py
```

Esto levanta:
- 🔗 Blockchain local (Hardhat)
- 📋 Issuer API (5010)
- ✅ Verifier API (5011)
- 🌐 Frontend server (8080) y apertura automática en navegador

**Tiempo estimado: 30 segundos**

### 4. Usa el Sistema

1. **Emitir**: Botón 🎫 en sección Emisor
2. **Verificar**: Botón 🔍 en sección Verificador
3. **Revocar**: Botón ❌ en sección Emisor
4. **Verificar después**: Confirmará rechazo (401)

## Arquitectura Entregada

```
v2/
├── frontend.html           ← Abre en navegador
├── issuer.py              ← API (5010)
├── verifier.py            ← API (5011)
├── blockchain_client.py   ← Cliente Web3
├── setup_complete.py      ← Setup automatizado
├── start_all.py          ← Inicia TODO
├── blockchain/
│   ├── contracts/SSIRegistry.sol
│   ├── scripts/deploy_registry.js
│   ├── scripts/bootstrap_issuer.js
│   └── hardhat.config.js
└── README.md             ← Documentación completa
```

## Comandos Importantes

| Tarea | Comando |
|---|---|
| Setup | `python3 setup_complete.py` |
| Iniciar | `python3 start_all.py` |
| Manual nodo | `cd blockchain && npm run node` |
| Manual APIs | `python3 -m uvicorn issuer:app --host 127.0.0.1 --port 5010` |
| Tests rápidos e2e | `python3 client.py` |
| Suite pytest | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest` |

## API Endpoints

### Issuer (5010)

```bash
# Emitir
curl -X POST http://127.0.0.1:5010/api/credentials/issue_dni \
  -H "Content-Type: application/json" \
  -d '{"did_ciudadano":"did:ethr:0x...","numero_dni":"12345678A"}'

# Revocar
curl -X POST http://127.0.0.1:5010/api/credentials/revoke \
  -H "Content-Type: application/json" \
  -d '{"credential_hash":"0x...","reason":"test"}'
```

### Verifier (5011)

```bash
# Verificar
curl -X POST http://127.0.0.1:5011/api/verify_presentation \
  -H "Content-Type: application/json" \
  -d '{"vp":{"verifiableCredential":{...},...}}'
```

## Validación End-to-End

Se ejecutó y pasó:

```
✓ ISSUE_STATUS = 200 (credencial emitida y registrada on-chain)
✓ VERIFY_BEFORE = 200 (verificación exitosa)
✓ REVOKE_STATUS = 200 (revocación confirmada on-chain)
✓ VERIFY_AFTER = 401 (rechazo después de revocación)
```

## Para Producción/Testnet

Los siguientes pasos se pueden hacer DESPUÉS:

1. Cambiar red de Hardhat local a testnet (Sepolia, etc)
2. Audit de seguridad del contrato
3. Implementar tests CI/CD
4. Agregar observabilidad

## Configuración Cloud

Para desplegar backend + frontend separados en cloud:

```bash
export SSI_CORS_ORIGINS="https://tu-frontend.com"
```

En local puedes mantener:

```bash
export SSI_CORS_ORIGINS="http://127.0.0.1:8080,http://localhost:8080"
```

## Ayuda

- 📖 Ver [v2/README.md](v2/README.md) para detalles técnicos
- 🐛 Problema: Blockchain no inicia → `cd v2/blockchain && npm install`
- 🐛 Problema: APIs no responden → Esperar 5 segundos y recargar
- 🐛 Problema: Frontend en blanco → Abrir en nueva ventana y sin caché

## Estado Actual del Repo

```
Commits principales:
- 34deda9: Entrega 1 - Blockchain + contrato
- b0199e4: Entrega 2 - Verificación on-chain
- dfe6c39: Refactor - Setup + Frontend + Docs
```

## Próximos Pasos (Opcional Mañana)

Si necesitas más features mañana, estos están listos para implementar:

- [ ] Tests automáticos
- [ ] Docker deployment
- [ ] Multi-chain support
- [ ] Batch operations
- [ ] Audit trail
- [ ] Admin panel

---

**Listo para empezar. ¡Ejecuta `python3 setup_complete.py` && `python3 start_all.py` en v2/**
