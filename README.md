# PTI_Ignacio_Jan - SSI con DID, VC y Blockchain

Repositorio de trabajo para una implementación de Self-Sovereign Identity (SSI) en dos etapas:

- `v1/`: MVP de autenticación con DID y firma.
- `v2/`: versión completa con emisión de credenciales, verificación híbrida (firma + on-chain), revocación y frontend.

## Documentación principal

- [README raíz](README.md)
- [Diferencias v1 vs v2](DIFERENCIAS_V1_V2.md)
- [Guía de despliegue](DESPLIEGUE.md)
- [Guía y explicación de uso](GUIA_Y_EXPLICACION.md)
- [Explicación general](EXPLICACION_GENERAL.md)
- [Quickstart operativo](QUICKSTART.md)
- [README técnico de v2](v2/README.md)

## Estructura del repositorio

```text
PTI_Ignacio_Jan/
├── README.md
├── QUICKSTART.md
├── DIFERENCIAS_V1_V2.md
├── DESPLIEGUE.md
├── GUIA_Y_EXPLICACION.md
├── EXPLICACION_GENERAL.md
├── v1/
└── v2/
```

## Qué es cada carpeta

## `v1/`

Primera versión del sistema. Incluye autenticación con DID en flujo challenge/response, sin blockchain para revocación de credenciales.

### Archivos principales en `v1/`

- `main.py`: servidor FastAPI principal de autenticación DID.
- `client.py`: cliente que solicita challenge, firma y verifica acceso.
- `generar_did.py`: genera una identidad local y archivo wallet.
- `setup_issuer.py`: inicialización de identidad del emisor.
- `database.py`: configuración de SQLite con SQLAlchemy.
- `models.py`: modelos de datos (sesiones y ciudadanos).
- `requirements.txt`: dependencias Python de v1.
- `wallet.json`: identidad local del usuario (privada, no subir a remoto).
- `ssi_sessions.db`: base de datos local.
- `README.md`: documentación específica de v1.

## `v2/`

Versión avanzada del sistema SSI con estado de confianza on-chain y frontend interactivo.

### Backend y lógica SSI en `v2/`

- `issuer.py`: API de emisión y revocación de credenciales.
- `verifier.py`: API de verificación de presentaciones.
- `blockchain_client.py`: cliente Web3 para lecturas/escrituras del contrato.
- `client.py`: script de cliente para pruebas rápidas de flujo.
- `database.py`: motor y sesión SQLAlchemy.
- `models.py`: modelos de base de datos.
- `seed_db.py`: carga ciudadanos de prueba en SQLite.
- `setup_issuer.py`: genera identidad del emisor.
- `generar_did.py`: genera DID de holder.
- `check_blockchain.py`: health check de conectividad blockchain.
- `setup_complete.py`: setup automatizado completo.
- `start_all.py`: arranque integral (blockchain + APIs + frontend server).
- `frontend.html`: interfaz web principal del sistema.

### Blockchain en `v2/blockchain/`

- `contracts/SSIRegistry.sol`: smart contract de estado SSI.
- `scripts/deploy_registry.js`: despliegue del contrato.
- `scripts/bootstrap_issuer.js`: autorización inicial del issuer.
- `hardhat.config.js`: configuración de Hardhat.
- `package.json`: scripts npm de compilación/despliegue.
- `.env.example`: ejemplo de variables de entorno para redes.
- `README.md`: guía específica de blockchain local.

### Testing en `v2/tests/`

- `test_issuer_api.py`: pruebas de endpoints del issuer.
- `test_verifier_api.py`: pruebas de verificación y reglas on-chain.
- `test_blockchain_client.py`: pruebas unitarias de utilidades blockchain.
- `test_frontend_interface.py`: pruebas estáticas de contrato de interfaz.
- `conftest.py`: helpers y utilidades compartidas de tests.
- `pytest.ini`: configuración de pytest.

## Estado actual del proyecto

- v1: estable como referencia del MVP inicial.
- v2: funcional en local con flujo end-to-end validado.
- Pruebas pytest: disponibles y ejecutables.
- Pendiente estratégico principal: migración de red local Hardhat a testnet (por ejemplo Sepolia) y despliegue cloud final.

## Comandos clave (v2)

```bash
cd v2
python3 setup_complete.py
python3 start_all.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest
```

## Nota de seguridad

No subir claves privadas ni archivos sensibles (`wallet.json`, `issuer_wallet.json`, `.env` reales) al repositorio público.