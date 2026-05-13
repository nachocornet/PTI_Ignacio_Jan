# SSI v2 - Memoria de entrega

Este directorio contiene la documentación de entrega del proyecto, sin código fuente.

## Resumen

SSI v2 es una plataforma de identidad autosoberana para emitir y verificar credenciales verificables (W3C VC) con apoyo de blockchain.

El sistema está compuesto por:
- un portal de entrada y dos paneles web,
- un issuer genérico,
- un issuer específico para DNI,
- un verificador de credenciales,
- utilidades compartidas para blockchain y configuración,
- scripts de despliegue y arranque.

Portal público de demostración:
- http://nattech.fib.upc.edu:40560/frontend_portal.html

## Estructura del proyecto

### Raíz
- `README.md`: guía general del proyecto.
- `README.md` de entrega: este documento.

### Frontend
- `frontend/frontend_portal.html`: punto de entrada visual.
- `frontend/issuer_dashboard.html`: emisión y revocación.
- `frontend/verifier_dashboard.html`: verificación de credenciales.
- `frontend/frontend_server.py`: servidor HTTP para servir los HTML.

### Servicios
- `services/issuer_base/`: base común del issuer.
- `services/issuer_dni/`: issuer DNI y validaciones de edad/DNI.
- `services/verifier/`: verificación de presentaciones.

### Compartido
- `shared/blockchain_client.py`: cliente Web3 para lectura y escritura on-chain.
- `shared/settings.py`: carga centralizada de configuración.

### Scripts
- `scripts/start_all.py`: arranque completo en local.
- `scripts/setup_complete.py`: configuración inicial.
- `scripts/deploy_vms.sh`: despliegue en VMs.
- `scripts/teardown.sh`: parada limpia.

### Blockchain
- `blockchain/`: contratos, bootstrap y despliegues.

### Configuración y datos
- `config/`: variables de entorno, dependencias y despliegues VMs.
- `deployments/`: wallets, ABI y contratos generados.
- `db/`: artefactos de base de datos.

### Tests
- `tests/`: suite automatizada de pytest.

## Cómo se usa

### 1. Preparación local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r config/requirements.txt
python3 scripts/setup_complete.py
```

### 2. Arranque
```bash
python3 scripts/start_all.py
```

### 3. Acceso
- Portal: `http://127.0.0.1:8080/frontend_login.html`
- Portal público: `http://nattech.fib.upc.edu:40560/frontend_portal.html`

### 4. Flujo funcional
1. Crear ciudadano desde el panel de administración.
2. Emitir credencial DNI / Over18.
3. Guardar el wallet del holder.
4. Verificar la presentación con el verificador.

## Imágenes incluidas

Las siguientes imágenes son esquemas visuales del proyecto y de sus pantallas principales:

![Visión general](images/overview.svg)

![Portal frontend](images/frontend_portal.svg)

![Issuer dashboard](images/issuer_dashboard.svg)

![Verifier dashboard](images/verifier_dashboard.svg)

## Qué incluye este paquete de entrega

Este directorio está pensado para entregar solo la documentación necesaria:
- descripción del proyecto,
- explicación de cada carpeta,
- instrucciones de uso,
- imágenes integradas.

No incluye código fuente.

## Observación final

Si necesitas una versión final en ZIP, la carpeta a comprimir es `readme_entrega/`.
