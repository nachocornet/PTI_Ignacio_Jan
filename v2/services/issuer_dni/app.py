"""
Aplicación FastAPI para issuer_dni.
Extiende issuer_base con rutas y validadores específicos DNI.
"""

import json
import os
from fastapi import FastAPI

from services.issuer_base.app import create_app
from services.issuer_base.services.database import init_db, SessionLocal
from services.issuer_dni.models import Base as DNIBase
from services.issuer_dni.routes import router as dni_router, set_dni_issuer_credentials

# Cargar credenciales del issuer
ISSUER_FILE = os.getenv("SSI_ISSUER_WALLET_FILE", "deployments/runtime/issuer_wallet.json")
if not os.path.exists(ISSUER_FILE):
    raise RuntimeError(f"Debe ejecutar setup_issuer.py primero. No existe: {ISSUER_FILE}")

with open(ISSUER_FILE, "r") as f:
    issuer_data = json.load(f)
    ISSUER_DID = issuer_data["did"]
    ISSUER_KEY = issuer_data["private_key"]

# Crear app base
app = create_app(
    title="VM1: Ministerio (Issuer DNI)",
    issuer_did=ISSUER_DID,
    issuer_key=ISSUER_KEY,
)

# Inicializar BD (crear tablas DNI)
init_db(DNIBase)

# Setear credenciales en rutas DNI
set_dni_issuer_credentials(ISSUER_DID, ISSUER_KEY)

# Incluir rutas específicas DNI
app.include_router(dni_router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SSI_ISSUER_PORT", "5010"))
    uvicorn.run(app, host="0.0.0.0", port=port)
