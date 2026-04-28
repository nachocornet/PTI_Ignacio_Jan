# Guia para Entender Todo el Codigo y Cambios

## 1. Mapa de carpetas y archivos

Nucleo de negocio:

- [issuer.py](issuer.py): emision y revocacion de credenciales
- [verifier.py](verifier.py): validacion de presentaciones
- [blockchain_client.py](blockchain_client.py): wrapper Web3 y contrato
- [models.py](models.py): modelo de datos SQLAlchemy
- [database.py](database.py): conexion/sesion de DB

Orquestacion y setup:

- [setup_complete.py](setup_complete.py): prepara dependencias y recursos
- [start_all.py](start_all.py): arranca stack completo
- [setup_issuer.py](setup_issuer.py): genera wallet de issuer
- [generar_did.py](generar_did.py): genera wallet DID holder

Interfaz:

- [frontend/issuer_dashboard.html](../../frontend/issuer_dashboard.html): dashboard de emision y revocacion
- [frontend/verifier_dashboard.html](../../frontend/verifier_dashboard.html): dashboard de verificacion
- [frontend/frontend_portal.html](../../frontend/frontend_portal.html): portal de entrada
- [frontend.variables.js](../../frontend/frontend.variables.js): variables del frontend

Configuracion:

- [settings.py](settings.py): unica fuente de verdad para puertos/hosts/rutas
- [.env.example](.env.example): ejemplo de variables

Testing:

- [tests/test_issuer_api.py](tests/test_issuer_api.py)
- [tests/test_verifier_api.py](tests/test_verifier_api.py)
- [tests/test_frontend_interface.py](tests/test_frontend_interface.py)
- [tests/test_blockchain_client.py](tests/test_blockchain_client.py)

## 2. Flujo de emision (issuer.py)

1. Recibe DID + DNI
2. Valida formato DID
3. Busca ciudadano en DB
4. Comprueba mayoria de edad
5. Construye VC
6. Calcula hash canonico de VC
7. Registra DID/VC on-chain
8. Firma VC con clave privada issuer
9. Devuelve VC + txs on-chain

## 3. Flujo de verificacion (verifier.py)

1. Recibe VP
2. Extrae VC
3. Verifica firma del issuer sobre VC
4. Verifica firma del holder sobre VP
5. Consulta blockchain:
   - issuer autorizado
   - DID holder activo
   - VC no revocada
6. Devuelve success o error 401/503 segun caso

## 4. Flujo de frontend (dashboards separados)

1. `frontend_portal.html` enlaza a los dashboards de issuer y verifier.
2. `issuer_dashboard.html` apunta a `issuer` para emitir y revocar.
3. `verifier_dashboard.html` firma la VP localmente y consulta `verifier`.
4. `frontend.variables.js` aporta URLs base y defaults.
5. El frontend nunca toca claves privadas del issuer.

## 5. Cambios realizados en esta iteracion

Refactor de configuracion global:

- Se eliminaron valores hardcodeados de puertos/hosts/rutas en servicios y scripts
- Se incorporo [settings.py](../../settings.py)
- Se agrego [.env.example](../../.env.example)

Mejora UX frontend:

- Se redujo JSON visible en UI principal
- VC/VP/resultados ahora aparecen resumidos en lenguaje humano
- JSON queda solo como modo avanzado

Wallet handling:

- Carga automatica por lista de fuentes
- Diagnostico de rutas intentadas
- Fallback de carga manual por archivo

Documentacion:

- Se actualizo README
- Se incorporo [GUIA_FRONTEND.md](../tutoriales/GUIA_FRONTEND.md)
- Se incorpora esta guia de codigo

## 6. Donde tocar cada cosa si quieres evolucionar

Cambiar puertos/host/rutas:

- [settings.py](../../settings.py)

Cambiar textos o flujo visual de UI:

- [frontend.variables.js](../../frontend.variables.js)
- [frontend/issuer_dashboard.html](../../frontend/issuer_dashboard.html)
- [frontend/verifier_dashboard.html](../../frontend/verifier_dashboard.html)
- [scripts/deploy_local.sh](../../scripts/deploy_local.sh)
- [scripts/deploy_vms.sh](../../scripts/deploy_vms.sh)
- [scripts/teardown.sh](../../scripts/teardown.sh)

Cambiar reglas de emision:

- [issuer.py](../../issuer.py)
- [models.py](../../models.py)

Cambiar reglas de verificacion:

- [verifier.py](../../verifier.py)
- [blockchain_client.py](../../blockchain_client.py)

## 7. Checklist de validacion rapido

1. Ejecutar setup: python3 setup_complete.py
2. Arrancar stack: python3 start_all.py
3. Probar flujo issue -> verify -> revoke -> verify
4. Ejecutar tests: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
