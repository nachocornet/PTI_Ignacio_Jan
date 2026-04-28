# Services

Microservicios FastAPI del sistema SSI.

## Estructura

- `issuer/app.py`: servicio de emision y revocacion de credenciales.
- `verifier/app.py`: servicio de verificacion de VP/VC.

## Ejecucion directa

```bash
python3 -m uvicorn services.issuer.app:app --host 127.0.0.1 --port 5010
python3 -m uvicorn services.verifier.app:app --host 127.0.0.1 --port 5011
```
