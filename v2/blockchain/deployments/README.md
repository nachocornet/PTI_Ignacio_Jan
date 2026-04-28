# Deployments

Metadatos de despliegues por red.

## Estructura

- `local/`: resultados de despliegue en red local de Hardhat.
- `sepolia/`: resultados de despliegue en testnet Sepolia.

## Notas

- Los archivos JSON aqui sirven para trazabilidad (address, tx hash, timestamp).
- El backend Python consume el artefacto puente en la raiz (`blockchain_contract.json` o variante por red).
