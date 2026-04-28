# Guía rápida: RPC de Sepolia con Infura

## Qué es el RPC

El RPC es la URL del nodo Ethereum al que Hardhat se conecta para enviar transacciones a Sepolia.
Sin ese endpoint no se puede desplegar el contrato en la testnet.

## Lo que necesitas

- Una cuenta de Infura
- Un proyecto nuevo
- La URL RPC de Sepolia
- ETH de prueba en el wallet de despliegue

## Paso 1: Crear cuenta y proyecto

1. Entra en Infura.
2. Crea una cuenta o inicia sesión.
3. Crea un nuevo proyecto.
4. Activa soporte para Sepolia.

## Paso 2: Obtener el RPC URL

Infura te dará una URL parecida a esta:

```text
https://sepolia.infura.io/v3/TU_PROJECT_ID
```

Guárdala porque la usarás como `SEPOLIA_RPC_URL`.

## Paso 3: Fondear el wallet de despliegue

Ya tienes un wallet generado en:

- `sepolia_deployer_wallet.json`

Abre ese archivo y copia el `address`.
Luego pide ETH de prueba en un faucet de Sepolia.

## Paso 4: Configurar variables de entorno

En tu terminal:

```bash
export SSI_BLOCKCHAIN_NETWORK=sepolia
export SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/TU_PROJECT_ID
export SEPOLIA_DEPLOYER_PRIVATE_KEY=0xTU_PRIVATE_KEY
export SSI_CONTRACT_FILE=blockchain_contract.sepolia.json
```

## Paso 5: Desplegar

```bash
cd v2/blockchain
npm run compile
npm run deploy:testnet
npm run bootstrap:testnet
```

## Paso 6: Verificar

Comprueba que se generó:

- `blockchain/deployments/sepolia/ssi_registry.json`
- `blockchain/deployments/sepolia/bootstrap_issuer.json`
- `blockchain_contract.sepolia.json`

Y luego prueba el health check:

```bash
cd v2
python3 check_blockchain.py
```

## Problemas comunes

- `SEPOLIA_RPC_URL` vacío:
  - Hardhat falla antes de desplegar.
- `private key` sin ETH:
  - La transacción no entra en la red.
- `wallet` incorrecto:
  - Asegúrate de usar el `privateKey` del wallet de despliegue y no el del issuer.
