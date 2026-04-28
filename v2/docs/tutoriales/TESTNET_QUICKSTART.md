# Quickstart de despliegue en testnet

## Estado

El proyecto ya está preparado para publicar el contrato en una red de prueba de Ethereum (por ejemplo Sepolia).
Hardhat sigue siendo la herramienta de compilación y despliegue, pero la transacción se envía a la testnet real.

Una vez desplegado, el contrato queda fijo en Sepolia y no debes redeployar cada arranque de APIs.

Si quieres usar Infura, sigue esta guía específica:

- [INFURA_SEPOLIA_GUIDE.md](INFURA_SEPOLIA_GUIDE.md)

## Lo que ya está preparado

- Soporte de red en [blockchain/hardhat.config.js](blockchain/hardhat.config.js)
- Scripts testnet:
  - `npm run deploy:testnet`
  - `npm run bootstrap:testnet`
- Wallet local de despliegue generado:
  - `sepolia_deployer_wallet.json`

## Lo único que falta para desplegar de verdad

Necesitas el RPC URL real de Sepolia y la clave privada del wallet de despliegue con gas suficiente.

Variables necesarias:

```bash
export SSI_BLOCKCHAIN_NETWORK=sepolia
export SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/TU_PROJECT_ID
export SEPOLIA_DEPLOYER_PRIVATE_KEY=0xTU_PRIVATE_KEY
```

## Pasos

1. Fondea el wallet generado en `sepolia_deployer_wallet.json`.
2. Exporta las variables anteriores.
3. Ejecuta:

```bash
cd v2
python3 deploy_testnet.py
```

Alternativa manual (equivalente):

```bash
cd v2/blockchain
npm run compile
npm run deploy:testnet
npm run bootstrap:testnet
```

## Resultados esperados

- `blockchain/deployments/sepolia/ssi_registry.json`
- `blockchain/deployments/sepolia/bootstrap_issuer.json`
- `blockchain_contract.sepolia.json`

## Cómo usar el resto del stack después

- El backend Python leerá el artefacto configurado por `SSI_CONTRACT_FILE`.
- Si quieres usar la red desplegada, exporta también:

```bash
export SSI_BLOCKCHAIN_NETWORK=sepolia
export SSI_CONTRACT_FILE=blockchain_contract.sepolia.json
```

Y para arrancar sin redeploy de blockchain:

```bash
python3 start_all.py
```

## Dónde verlo visualmente

1. Abre `blockchain/deployments/sepolia/ssi_registry.json`.
2. Copia `address` y `deploymentTxHash`.
3. Consulta en Sepolia Etherscan:

```text
https://sepolia.etherscan.io/address/<address>
https://sepolia.etherscan.io/tx/<deploymentTxHash>
```

## Nota importante

Si falta `SEPOLIA_RPC_URL` o `SEPOLIA_DEPLOYER_PRIVATE_KEY`, Hardhat ahora falla con un mensaje claro antes de intentar desplegar.
