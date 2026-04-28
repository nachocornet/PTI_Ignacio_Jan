# Índice de Archivos del Repositorio (v2)

## 1) Arranque y operación

- `start_all.py`: arranque automático network-aware (`local` o `sepolia`)
- `setup_complete.py`: instalación inicial de dependencias y recursos
- `deploy_testnet.py`: despliegue one-shot en Sepolia (compile + deploy + bootstrap)
- `check_blockchain.py`: health check del cliente blockchain

## 2) Configuración

- `settings.py`: configuración centralizada por variables de entorno
- `.env.example`: ejemplo de variables generales
- `blockchain/.env.example`: ejemplo de variables de Hardhat/Sepolia

## 3) Backend SSI

- `issuer.py`: emisión/revocación de credenciales
- `verifier.py`: verificación de VP/VC + validaciones on-chain
- `blockchain_client.py`: cliente Web3 para `SSIRegistry`
- `client.py`: cliente de prueba para flujo básico

## 4) Modelo y datos

- `models.py`: modelos SQLAlchemy
- `database.py`: conexión de base de datos
- `seed_db.py`: datos iniciales

## 5) Identidades y wallets

- `setup_issuer.py`: genera wallet del issuer
- `generar_did.py`: genera wallet/DID de holder
- `issuer_wallet.json`: wallet del issuer (local)
- `wallet.json`: wallet del holder (local)
- `sepolia_deployer_wallet.json`: wallet de deployer de Sepolia (local, no versionar)

## 6) Frontend

- `frontend_portal.html`: portal de navegación de frontends
- `issuer_dashboard.html`: interfaz de emisión/revocación
- `verifier_dashboard.html`: interfaz de verificación de VP
- `frontend_portal.html`, `issuer_dashboard.html` y `verifier_dashboard.html`: interfaces web de produccion
- `frontend.variables.js`: configuración renderizada para frontend
- `frontend_server.py`: servidor estático seguro (sin listado de directorios)

### Health operativos

- `GET /health` en `issuer.py`
- `GET /health` en `verifier.py`

## 7) Blockchain (Hardhat)

- `blockchain/contracts/SSIRegistry.sol`: contrato inteligente
- `blockchain/hardhat.config.js`: configuración de redes (`localhost`, `sepolia`)
- `blockchain/scripts/deploy_registry.js`: script de despliegue
- `blockchain/scripts/bootstrap_issuer.js`: autorización del issuer
- `blockchain/scripts/generate_testnet_wallet.js`: creación wallet deployer
- `blockchain/deployments/local/*.json`: metadatos local
- `blockchain/deployments/sepolia/*.json`: metadatos Sepolia

## 8) Artefactos de contrato

- `blockchain_contract.json`: artefacto activo (bridge para Python)
- `blockchain_contract.localhost.json`: artefacto de despliegue local
- `blockchain_contract.sepolia.json`: artefacto de despliegue Sepolia

## 9) Tests

- `tests/test_issuer_api.py`
- `tests/test_verifier_api.py`
- `tests/test_blockchain_client.py`
- `tests/test_frontend_interface.py`
- `tests/test_frontend_split_interface.py`

## 10) Documentación

- `README.md`: guía principal
- `docs/tutoriales/TESTNET_QUICKSTART.md`: operación en Sepolia
- `docs/tutoriales/INFURA_SEPOLIA_GUIDE.md`: obtención de RPC con Infura
- `docs/referencia/EU_PROFILE.md`: alineación técnica con perfil europeo
- `docs/tutoriales/GUIA_FRONTEND.md`: uso del frontend
- `docs/referencia/GUIA_CODIGO_Y_CAMBIOS.md`: guía interna de arquitectura/cambios
- `docs/operacion/DOCUMENTACION_DEFINITIVA.md`: consolidado de estado
- `docs/README.md`: navegación de documentación por carpetas

## 11) Dónde verlo visualmente

- Contrato en explorer:
  - `https://sepolia.etherscan.io/address/<address>`
- Tx de despliegue:
  - `https://sepolia.etherscan.io/tx/<deploymentTxHash>`

Valores reales:

- `blockchain/deployments/sepolia/ssi_registry.json`
