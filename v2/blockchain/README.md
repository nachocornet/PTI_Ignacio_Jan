# Entrega 1 - Blockchain Local SSI (Hardhat)

Esta carpeta implementa la base de blockchain local para:

- Autorizar DID de emisores confiables.
- Consultar estado activo/revocado de DIDs.
- Registrar y revocar credenciales por hash canónico.

## 1) Instalar dependencias Node

```bash
cd blockchain
npm install
```

## 2) Compilar contrato

```bash
npm run compile
```

## 3) Levantar nodo local

En una terminal separada:

```bash
cd blockchain
npm run node
```

## 4) Desplegar contrato en localhost

En otra terminal:

```bash
cd blockchain
npm run deploy:local
```

Esto genera:

- `blockchain/deployments/local/ssi_registry.json`
- `blockchain/artifacts_export/ssi_registry_abi.json`
- `blockchain_contract.json` (puente para Python en la raiz del proyecto)

## 4b) Desplegar contrato en Sepolia

Antes de desplegar a testnet necesitas:

1. Crear un wallet de despliegue:

```bash
cd v2
node blockchain/scripts/generate_testnet_wallet.js
```

2. Fondear el address mostrado con un faucet de Sepolia.

3. Exportar variables de entorno:

```bash
export SSI_BLOCKCHAIN_NETWORK=sepolia
export SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/TU_PROJECT_ID
export SEPOLIA_DEPLOYER_PRIVATE_KEY=0x...
```

4. Compilar y desplegar:

```bash
cd blockchain
npm run compile
npm run deploy:testnet
npm run bootstrap:testnet
```

Esto genera:

- `blockchain/deployments/sepolia/ssi_registry.json`
- `blockchain/deployments/sepolia/bootstrap_issuer.json`
- `blockchain_contract.sepolia.json`

El archivo `blockchain_contract.json` tambien se actualiza como puente activo para el cliente Python.

Guía rápida completa: [TESTNET_QUICKSTART.md](../docs/tutoriales/TESTNET_QUICKSTART.md)

## 5) Bootstrap del Issuer

```bash
cd blockchain
npm run bootstrap:local
```

Lee `issuer_wallet.json` de la raiz y autoriza ese DID como Issuer confiable.

## 6) Validar conectividad desde Python

Instalar dependencias Python (si no lo has hecho):

```bash
pip install -r requirements.txt
```

Luego:

```bash
python3 check_blockchain.py
```

## Flujo de lectura para Verifier (siguiente entrega)

El `verifier.py` debera combinar:

1. Verificacion criptografica VC/VP.
2. `isIssuerAuthorized(issuerDid)`.
3. `isDidActive(holderDid)`.
4. `isCredentialRevoked(credentialHash)`.

## Estructura principal

- `contracts/SSIRegistry.sol`: contrato de estado SSI.
- `scripts/deploy_registry.js`: despliegue y export ABI/address.
- `scripts/bootstrap_issuer.js`: autoriza DID del Ministerio.
