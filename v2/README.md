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
- Frontend (navegador automático)

**¡Listo para usar!**

## Uso del Frontend

1. **Emitir Credencial:**
   - Carga DID (botón 📂)
   - Ingresa DNI
   - Click 🎫

2. **Verificar Credencial:**
   - La credencial se carga automáticamente
   - Click 🔍 para verificar
   - Recibe ✓ o ❌ on-chain

3. **Revocar Credencial:**
   - Click ❌ para revocar
   - Verificación posterior fallará (401)

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

## Requisitos

- Node.js >= 18.0
- Python >= 3.9
- npm

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
