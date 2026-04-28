# Tests

Pruebas automatizadas del backend y contratos de interfaz frontend.

## Suite actual

- `test_issuer_api.py`: emision y revocacion.
- `test_verifier_api.py`: validacion de VP/VC y chequeos on-chain.
- `test_blockchain_client.py`: cliente blockchain Python.
- `test_frontend_interface.py`: validaciones de frontend tecnico.
- `test_frontend_split_interface.py`: validaciones de frontends separados (portal/admin/holder).

## Ejecucion

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```
