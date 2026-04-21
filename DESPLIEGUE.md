# Guía de Despliegue

Este documento explica cómo desplegar y ejecutar el sistema en local (modo actual) y cómo preparar el salto a testnet/cloud.

## Requisitos

- Python 3.9+
- Node.js 18+
- npm
- Acceso a terminal bash

## Despliegue local (recomendado)

## Opción 1: setup y arranque automático

1. Entrar en la versión activa:

```bash
cd v2
```

2. Setup inicial:

```bash
python3 setup_complete.py
```

3. Arranque completo:

```bash
python3 start_all.py
```

Esto levanta:
- nodo Hardhat (8545),
- deploy + bootstrap,
- issuer API (5010),
- verifier API (5011),
- servidor frontend (8080).

## Opción 2: manual por servicios

### Terminal 1 - Hardhat

```bash
cd v2/blockchain
npm run node
```

### Terminal 2 - Deploy y bootstrap

```bash
cd v2/blockchain
npm run deploy:local
npm run bootstrap:local
```

### Terminal 3 - Issuer API

```bash
cd v2
python3 -m uvicorn issuer:app --host 127.0.0.1 --port 5010
```

### Terminal 4 - Verifier API

```bash
cd v2
python3 -m uvicorn verifier:app --host 127.0.0.1 --port 5011
```

### Terminal 5 - Frontend

```bash
cd v2
python3 -m http.server 8080 --bind 127.0.0.1
```

Abrir:

```text
http://127.0.0.1:8080/frontend.html
```

## Verificación de despliegue

## Salud blockchain

```bash
cd v2
python3 check_blockchain.py
```

## Smoke frontend

```bash
curl -sSf http://127.0.0.1:8080/frontend.html | head -n 5
```

## Prueba e2e (scripts/API)

```bash
cd v2
python3 client.py
```

## Variables de entorno relevantes

## CORS para cloud

```bash
export SSI_CORS_ORIGINS="https://tu-frontend.com"
```

## Puerto frontend automático

```bash
export SSI_FRONTEND_PORT=8080
```

## Paso siguiente (fuera del local)

Para pasar a testnet (Sepolia):
- configurar RPC y claves en `blockchain/.env`,
- añadir red en Hardhat,
- desplegar contrato en testnet,
- actualizar `blockchain_contract.json` con dirección/ABI reales,
- desplegar APIs y frontend en cloud.
