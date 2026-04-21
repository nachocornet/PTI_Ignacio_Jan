# SSI v2 - Identidad Autosoberana con Blockchain On-Chain

Proyecto completo de SSI (Self-Sovereign Identity) con infraestructura blockchain local, validación criptográfica y verificación on-chain.

## Resumen Ejecutivo

v2 es una arquitectura completa y operativa que:
- ✓ Emite credenciales verificables (VC) firmadas
- ✓ Registra credenciales y DIDs en blockchain local (Hardhat)
- ✓ Verifica con validación híbrida (cripto + on-chain)
- ✓ Revoca credenciales de forma inmutable on-chain
- ✓ Incluye frontend web funcional
- ✓ Deploy totalmente automatizado

**Startup rápido:**
```bash
python3 setup_complete.py  # Setup una sola vez
python3 start_all.py       # Levanta TODO
```

## Comparativa v1 vs v2

| Aspecto | v1 | v2 |
|---|---|---|
| Setup | Manual, muchos pasos | Automatizado (1 comando) |
| Despliegue | 4+ terminales | 1 comando (`start_all.py`) |
| Interfaz | CLI solo | Frontend web completo |
| Blockchain | No | Sí (Hardhat + Solidity) |
| Revocación | Ninguna | On-chain inmutable |
| Validación | Solo cripto | Cripto + on-chain |
| Documentación | Básica | Completa |

## Arquitectura

```
┌─────────────────────────────────────────┐
│  Frontend (HTML/CSS/JS)                 │
│  - Issue, Verify, Revoke                │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼────┐         ┌────▼────┐
│Issuer   │         │Verifier │
│(5010)   │         │(5011)   │
└────┬────┘         └────┬────┘
     │                   │
     └─────────┬─────────┘
               │
        ┌──────▼──────┐
        │  Blockchain │
        │  Client     │
        │  (Web3.py)  │
        └──────┬──────┘
               │
        ┌──────▼──────────┐
        │ Hardhat Node    │
        │ (8545)          │
        │                 │
        │ SSIRegistry.sol │
        └─────────────────┘
```

## Instalación Rápida

### Paso 1: Setup (Una sola vez)

```bash
cd v2
python3 setup_complete.py
```

Esto instala todo: dependencias Node/Python, compila contrato, crea wallets.

### Paso 2: Iniciar Sistema

```bash
python3 start_all.py
```

Esto levanta:
- Blockchain local (8545)
- Deploy contrato
- Issuer API (5010)
- Verifier API (5011)
- Frontend server HTTP (8080) + navegador automático

**¡Listo para usar!**

## Uso del Frontend (Guiado y Autoexplicativo)

El frontend ahora incluye explicaciones dentro de la propia interfaz, para que cualquier persona pueda entender el flujo sin abrir código:

- **Guía rápida superior (Paso 1..4):** resume qué hacer y en qué orden.
- **Tracker de flujo en vivo:** muestra si ya tienes wallet, VC emitida, VP firmada y verificación completada.
- **Bloques de explicación por sección:**
  - en Emisión/Revoación se explica qué se firma y qué se registra on-chain,
  - en Verificación se explica qué checks realiza el Verifier.
- **Panel de glosario VC vs VP:** deja claro qué es cada objeto y para qué sirve.

Flujo recomendado:

1. **Cargar wallet local del holder**
  - Botón `Cargar wallet local`
  - El frontend muestra mensaje explícito de carga de clave privada desde `wallet.json`.

2. **Emitir credencial (VC)**
  - Completa DID + DNI
  - Botón `Emitir credencial`
  - Se actualiza panel **VC Bonita** en formato legible (sin JSON crudo).

3. **Verificar presentación (VP)**
  - Botón `Verificar presentación`
  - El frontend firma VP localmente y muestra el proceso en banner + actividad.
  - Se visualiza la VP final en el panel **VP Firmada** con resumen humano.

4. **Revocar para probar rechazo on-chain**
  - Botón `Revocar credencial`
  - Una verificación posterior debe fallar con estado de revocación.

Nota: el frontend se sirve por HTTP en `http://127.0.0.1:8080/frontend.html` para que funcione correctamente la carga de `wallet.json` y las peticiones CORS al backend.

Actualizacion de seguridad: el frontend ya no usa `python -m http.server` con listado de directorio.
Ahora se sirve con `frontend_server.py`, que solo expone:

- `/frontend.html`
- `/frontend.variables.js`

No se exponen archivos internos del repositorio por HTTP.
La wallet del holder se carga manualmente desde archivo en la UI (no se sirve por endpoint publico).

## APIs Reference

### Issuer (5010)

**Emitir credencial:**
```bash
POST /api/credentials/issue_dni
{
  "did_ciudadano": "did:ethr:0x...",
  "numero_dni": "12345678A"
}
```

Respuesta:
```json
{
  "credential": { "...": "..." },
  "onchain": {
    "didStatusTx": "0x...",
    "registerCredentialTx": "0x..."
  }
}
```

**Revocar:**
```bash
POST /api/credentials/revoke
{
  "credential_hash": "0x...",
  "reason": "Usuario solicitó revocación"
}
```

### Verifier (5011)

**Verificar presentación:**
```bash
POST /api/verify_presentation
{
  "vp": {
    "verifiableCredential": { "...": "..." },
    "proof": { "proofValue": "0x..." }
  }
}
```

Respuesta exitosa (200):
```json
{
  "status": "success",
  "onchain": {
    "issuerAuthorized": true,
    "holderDidActive": true,
    "credentialRevoked": false
  }
}
```

Respuesta rechazada (401):
```json
{
  "detail": "Credencial revocada on-chain"
}
```

## Flujo Técnico Completo

### 1. Emisión

```
User solicita VC
  ↓
Issuer valida DID
  ↓
Issuer crea VC con credentialHash canónico
  ↓
Issuer firma VC con secp256k1
  ↓
Issuer escribe on-chain:
  - setDidStatus(holder, true)
  - registerCredential(hash, holder)
  ↓
Retorna VC + metadata on-chain
```

### 2. Verificación

```
Holder presenta VP (VC + firma del holder)
  ↓
Verifier valida firma del issuer en VC
  ↓
Verifier valida firma del holder en VP
  ↓
Verifier consulta blockchain:
  - ¿Issuer autorizado?
  - ¿Holder DID activo?
  - ¿Credencial NO revocada?
  ↓
Si TODO correcto: 200 OK
Si ALGUNO falla: 401 UNAUTHORIZED
```

### 3. Revocación

```
Issuer solicita revocación
  ↓
Issuer escribe on-chain:
  - revokeCredential(hash, reason)
  ↓
Siguiente verificación fallará (401)
```

## Smart Contract SSIRegistry

**Ubicación:** [blockchain/contracts/SSIRegistry.sol](blockchain/contracts/SSIRegistry.sol)

**Funciones principales:**

- `setIssuerAuthorization(address, bool)` - Admin autoriza emisor
- `setDidStatus(address, bool, bytes32)` - Issuer activa/desactiva DID
- `registerCredential(bytes32, address)` - Issuer registra credencial
- `revokeCredential(bytes32, bytes32)` - Issuer revoca credencial
- `isIssuerAuthorized(address)` - Lectura: ¿Emisor autorizado?
- `isDidActive(address)` - Lectura: ¿DID activo?
- `isCredentialRevoked(bytes32)` - Lectura: ¿Credencial revocada?

## Archivo de Credencial

Ejemplo de VC generada:

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1"],
  "id": "urn:uuid:...",
  "type": ["VerifiableCredential", "Over18Credential"],
  "issuer": "did:ethr:0x8C2270...",
  "issuanceDate": "2026-04-21T14:30:00Z",
  "credentialSubject": {
    "id": "did:ethr:0x3DFA12...",
    "isOver18": true
  },
  "credentialHash": "0xabc123def456...",
  "proof": {
    "type": "EcdsaSecp256k1RecoverySignature2020",
    "proofValue": "0x...",
    "verificationMethod": "did:ethr:0x8C2270..."
  }
}
```

## Seguridad

- **Firma:** ECDSA Secp256k1 (mismo que Ethereum/Bitcoin)
- **Hash:** Keccak-256 canonical JSON
- **Control de acceso:** On-chain via smart contract
- **Rate limiting:** 5-10 req/min por IP
- **Transacciones atómicas:** Falla total si blockchain falla

## Archivos Principales

### Setup y Deploy
- `setup_complete.py` - Setup automatizado
- `start_all.py` - Inicia TODO con 1 comando
- `frontend.html` - Interfaz web

### Backend
- `issuer.py` - API emisor (5010)
- `verifier.py` - API verificador (5011)
- `blockchain_client.py` - Cliente Web3

### Blockchain
- `blockchain/hardhat.config.js` - Config Hardhat
- `blockchain/contracts/SSIRegistry.sol` - Smart contract
- `blockchain/scripts/deploy_registry.js` - Deploy
- `blockchain/scripts/bootstrap_issuer.js` - Bootstrap

### Utilidades
- `seed_db.py` - Popula DB
- `setup_issuer.py` - Genera issuer wallet
- `generar_did.py` - Genera DIDs de prueba
- `check_blockchain.py` - Health check

## Prueba End-to-End Real

Se ejecutó y pasó exitosamente:

```
ISSUE_STATUS = 200 ✓
VERIFY_BEFORE_REVOKE = 200 ✓
REVOKE_STATUS = 200 ✓
VERIFY_AFTER_REVOKE = 401 ✓
```

Confirmado en ejecución real:
- ✓ Emisión: credencial registrada on-chain
- ✓ Verificación: validación cripto + on-chain exitosa
- ✓ Revocación: transacción on-chain confirmada
- ✓ Bloqueo: post-revocación rechazada correctamente

## Testing Automatizado (pytest)

Suite incluida en `tests/`:

- `tests/test_issuer_api.py`: emisión y revocación del Issuer
- `tests/test_verifier_api.py`: verificación criptográfica + estado on-chain
- `tests/test_blockchain_client.py`: hashing canónico y validaciones de utilidades
- `tests/test_frontend_interface.py`: contrato de interfaz, guía embebida, glosario y flujo de firma

Cobertura destacada reciente:

- Mensajes explícitos de seguridad UX:
  - carga de clave privada local,
  - firma de VP con wallet local.
- Casos de error API en Issuer:
  - mapeo a `400` para errores de entrada blockchain,
  - mapeo a `503` para fallos de disponibilidad blockchain.
- Casos de robustez en Verifier:
  - rechazo cuando falta `verifiableCredential`,
  - fallback correcto cuando no llega `credentialHash` (re-cálculo/verificación).

Ejecutar suite:

```bash
cd v2
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest
```

Nota: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` evita un conflicto conocido con plugins externos de `web3` en algunos entornos locales.

Resultado validado en este proyecto:

```text
23 passed
```

Smoke test de interfaz servida por HTTP:

```bash
curl -sSf http://127.0.0.1:8080/frontend.html | grep "SSI v2 Control Center"
```

## Requisitos

- Node.js >= 18.0
- Python >= 3.9
- npm

## Configuración Cloud-Ready

El backend permite orígenes CORS por variable de entorno:

```bash
export SSI_CORS_ORIGINS="https://tu-frontend.com,http://127.0.0.1:8080"
```

El frontend port del arranque automático también es configurable:

```bash
export SSI_FRONTEND_PORT=8080
python3 start_all.py
```

## Configuración Centralizada (sin hardcode en código)

Toda la configuración operativa se concentra en:

- `settings.py` (lectura única de entorno)
- `.env.example` (plantilla de variables)
- `frontend.variables.js` (variables de UI; se regenera automáticamente desde `start_all.py`)

Variables principales:

- `SSI_ISSUER_PORT`, `SSI_VERIFIER_PORT`, `SSI_FRONTEND_PORT`
- `SSI_BLOCKCHAIN_HOST`, `SSI_BLOCKCHAIN_PORT`
- `SSI_ISSUER_WALLET_FILE`, `SSI_HOLDER_WALLET_FILE`, `SSI_CONTRACT_FILE`

Ejemplo rápido:

```bash
export SSI_ISSUER_PORT=6010
export SSI_VERIFIER_PORT=6011
export SSI_FRONTEND_PORT=9080
python3 start_all.py
```

Con eso, APIs, cliente, setup, frontend y arranque usan la nueva configuración sin editar fuentes.

## Documentacion Final

Documentos recomendados para trabajo diario y entrega:

- [DOCUMENTACION_DEFINITIVA.md](DOCUMENTACION_DEFINITIVA.md): estado final del sistema, decisiones y operacion
- [GUIA_CODIGO_Y_CAMBIOS.md](GUIA_CODIGO_Y_CAMBIOS.md): guia para entender el codigo y todo lo implementado
- [GUIA_FRONTEND.md](GUIA_FRONTEND.md): uso funcional de la interfaz paso a paso

## Limitaciones Actuales

- Blockchain local (no testnet)
- Cuentas desbloqueadas en Hardhat
- Sin tests automatizados en CI

## Próximos Pasos

1. Deploy a testnet (Sepolia)
2. Audit de seguridad
3. Tests automatizados
4. Observabilidad y alertas
5. Persistencia distribuida

## Conclusión

v2 es una solución **completa, funcional y operativa** de SSI con:
- Infraestructura blockchain local robusta
- Validación híbrida (criptográfica + on-chain)
- Frontend web intuitivo
- Setup y deploy completamente automatizados
- Documentación exhaustiva

**Listo para producción local. Para mainnet requiere audit de seguridad.**

---

**Versión:** 2.2  
**Fecha:** 2026-04-21  
**Estado:** ✓ COMPLETO
