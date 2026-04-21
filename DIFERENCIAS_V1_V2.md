# Diferencias Entre v1 y v2

## Resumen

Este documento describe de forma clara la evolución del proyecto desde la versión v1 (MVP SSI básico) a la versión v2 (SSI con estado de confianza en blockchain local y frontend interactivo).

## Comparativa rápida

| Área | v1 | v2 |
|---|---|---|
| Arquitectura | Servicio único | Servicios separados (Issuer + Verifier) |
| Flujo SSI | Challenge/response DID | Emisión VC + VP + verificación híbrida |
| Blockchain | No | Sí, Hardhat local |
| Revocación | No | Sí, on-chain |
| Estado de confianza | Local | On-chain (contrato SSIRegistry) |
| Frontend | No | Sí, interfaz web completa |
| Setup | Manual | Automatizado |
| Testing | Básico/manual | pytest + e2e validado |

## Cambios técnicos clave

## 1. Arquitectura backend

### v1
- Núcleo en un único archivo principal.
- Funcionalidad centrada en autenticación con DID y firma.
- Sin lógica de credenciales verificables persistidas on-chain.

### v2
- `issuer.py`: emite credenciales y revoca.
- `verifier.py`: verifica firmas y estado blockchain.
- `blockchain_client.py`: puente Web3 entre Python y contrato.

## 2. Contrato inteligente y red

### v1
- No existía capa de smart contract.

### v2
- Contrato `SSIRegistry.sol` con:
  - autorización de issuer,
  - estado de DID,
  - registro de credential hash,
  - revocación de credenciales.
- Hardhat local en `127.0.0.1:8545`.

## 3. Validación de credenciales

### v1
- Validación criptográfica de firma y DID.

### v2
- Validación de dos capas:
  1. Criptográfica (firma VC y VP).
  2. On-chain (`isIssuerAuthorized`, `isDidActive`, `isCredentialRevoked`).

## 4. Frontend y UX

### v1
- Flujo principalmente por scripts/CLI.

### v2
- `frontend.html` con:
  - emisión,
  - verificación,
  - revocación,
  - panel de estado,
  - actividad y payloads,
  - firma real de VP con wallet local.

## 5. Calidad y pruebas

### v1
- Pruebas manuales de flujo básico.

### v2
- Suite `pytest` incluida:
  - `test_issuer_api.py`
  - `test_verifier_api.py`
  - `test_blockchain_client.py`
  - `test_frontend_interface.py`
- Flujo e2e validado: 200/200/200/401.

## 6. Estado actual

La versión v2 deja como siguiente gran paso pendiente:
- Migrar de Hardhat local a testnet (ejemplo: Sepolia) y completar despliegue cloud final.
