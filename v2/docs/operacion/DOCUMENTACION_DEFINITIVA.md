# SSI v2 - Documentacion Definitiva

## 1. Que es este proyecto

SSI v2 implementa un flujo completo de identidad autosoberana:

- Emision de VC firmada por Issuer
- Presentacion VP firmada por Holder
- Verificacion criptografica + validacion on-chain
- Revocacion inmutable de credenciales

## 2. Arquitectura final

Componentes:

- Frontend: [frontend_portal.html](../../frontend/frontend_portal.html)
- Dashboards: [issuer_dashboard.html](../../frontend/issuer_dashboard.html) y [verifier_dashboard.html](../../frontend/verifier_dashboard.html)
- Variables frontend: [frontend.variables.js](frontend.variables.js)
- Config central: [settings.py](settings.py)
- Issuer API: [issuer.py](issuer.py)
- Verifier API: [verifier.py](verifier.py)
- Cliente blockchain: [blockchain_client.py](blockchain_client.py)
- Arranque completo: [start_all.py](start_all.py)
- Despliegue local: [scripts/deploy_local.sh](../../scripts/deploy_local.sh)
- Despliegue VMs: [scripts/deploy_vms.sh](../../scripts/deploy_vms.sh)
- Teardown: [scripts/teardown.sh](../../scripts/teardown.sh)

Flujo:

1. Holder carga wallet
2. Issuer emite VC
3. Frontend construye VP y firma con la wallet del holder
4. Verifier valida firmas y consulta blockchain
5. Issuer puede revocar VC

## 3. Configuracion sin hardcode

Toda la configuracion operativa se centraliza en [settings.py](settings.py).

Variables de entorno base:

- SSI_APP_HOST
- SSI_APP_BIND_HOST
- SSI_ISSUER_PORT
- SSI_VERIFIER_PORT
- SSI_FRONTEND_PORT
- SSI_BLOCKCHAIN_HOST
- SSI_BLOCKCHAIN_PORT
- SSI_ISSUER_WALLET_FILE
- SSI_HOLDER_WALLET_FILE
- SSI_CONTRACT_FILE
- SSI_CORS_ORIGINS (opcional)

Plantilla de ejemplo: [.env.example](.env.example)

## 4. Frontend limpio (sin JSON feo en paneles principales)

UI final:

- VC en formato humano (campos clave legibles)
- VP en formato humano (titular, hash, firma resumida)
- Resultado de operacion resumido (sin dump JSON)
- JSON solo en modo avanzado y opcional

Objetivo: que cualquier usuario entienda el flujo sin leer JSON crudo.

## 5. Wallet loading robusto

Comportamiento final:

- Carga automatica desde fuentes configuradas (walletSources)
- Diagnostico visible de rutas intentadas
- Boton de carga manual desde archivo
- Panel de estado con fuente real de carga, DID y address

## 6. Arranque y operacion

Setup inicial:

```bash
cd v2
python3 setup_complete.py
```

Arranque completo:

```bash
python3 start_all.py
```

El script genera automaticamente [frontend.variables.js](frontend.variables.js) a partir de [settings.py](settings.py).

## 7. Testing y calidad

Ejecucion:

```bash
cd v2
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
```

Estado validado:

- 27 tests pasando

Cobertura:

- Issuer API: emision, revocacion, errores blockchain
- Verifier API: firma VC/VP, checks on-chain, fallback hash
- Frontend contract tests: estructura, firma, feedback UX

## 8. Decisiones clave tomadas

- Eliminar hardcodes de puertos/hosts/rutas en backend y scripts
- Centralizar toda la configuracion en settings.py
- Priorizar UX legible por encima de dumps JSON
- Mantener JSON solo para casos avanzados y depuracion

## 9. Limitaciones actuales

- La orquestacion de nube privada depende de credenciales y red de Virtech
- La estrategia de produccion usa Sepolia, no un nodo blockchain local persistente
- La seguridad de entorno sigue pensada para laboratorio/demo + despliegue automatizado

## 10. Siguientes mejoras recomendadas

1. Consolidar observabilidad y alertas de release
2. Automatizar backup/restore de PostgreSQL
3. Ejecutar un rollback real de prueba en Virtech
4. Documentar el runbook de incidencias y recuperacion
