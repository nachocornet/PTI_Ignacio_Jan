import json
import uuid
import datetime
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from eth_account import Account
from eth_account.messages import encode_defunct
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import models
import database

app = FastAPI(title="VM1: Ministerio (Issuer)")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ISSUER_FILE = "issuer_wallet.json"
if not os.path.exists(ISSUER_FILE):
    raise RuntimeError("Debe ejecutar setup_issuer.py primero")

with open(ISSUER_FILE, "r") as f:
    issuer_data = json.load(f)
    ISSUER_DID = issuer_data["did"]
    ISSUER_KEY = issuer_data["private_key"]

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/credentials/issue_dni")
@limiter.limit("5/minute")
async def issue_dni(request: Request, data: dict, db: Session = Depends(get_db)):
    numero_dni = data.get("numero_dni")
    did_usuario = data.get("did_ciudadano")
    
    ciudadano = db.query(models.CitizenDB).filter(models.CitizenDB.numero_dni == numero_dni).first()
    if not ciudadano:
        raise HTTPException(status_code=404, detail="Ciudadano no encontrado")

    nacimiento = datetime.datetime.strptime(ciudadano.fecha_nacimiento, "%Y-%m-%d")
    edad = (datetime.datetime.utcnow() - nacimiento).days // 365
    if edad < 18:
        raise HTTPException(status_code=403, detail="El ciudadano es menor de edad")

    vc = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "id": f"urn:uuid:{uuid.uuid4()}",
        "type": ["VerifiableCredential", "Over18Credential"],
        "issuer": ISSUER_DID,
        "issuanceDate": datetime.datetime.utcnow().isoformat() + "Z",
        "credentialSubject": {
            "id": did_usuario,
            "isOver18": True
        }
    }

    vc_canonical = json.dumps(vc, separators=(',', ':'), sort_keys=True)
    msg = encode_defunct(text=vc_canonical)
    signature = Account.sign_message(msg, private_key=ISSUER_KEY).signature.hex()

    vc["proof"] = {
        "type": "EcdsaSecp256k1RecoverySignature2020",
        "created": datetime.datetime.utcnow().isoformat() + "Z",
        "verificationMethod": ISSUER_DID,
        "proofPurpose": "assertionMethod",
        "proofValue": signature
    }
    
    return {"credential": vc}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5010)