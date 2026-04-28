# Scripts Blockchain

Scripts de Hardhat para despliegue y bootstrap.

## Archivos

- `deploy_registry.js`: despliega `SSIRegistry` en la red activa.
- `bootstrap_issuer.js`: autoriza DID del issuer en contrato ya desplegado.
- `generate_testnet_wallet.js`: crea wallet de deployer para Sepolia.

## Comandos utiles

Desde `blockchain/`:

```bash
npm run deploy:local
npm run bootstrap:local
npm run deploy:testnet
npm run bootstrap:testnet
```
