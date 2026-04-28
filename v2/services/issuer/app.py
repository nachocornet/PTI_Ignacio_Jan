import json
import uuid
import datetime
import os
import re
import base64
import binascii
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from eth_account import Account
from eth_account.messages import encode_defunct
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from db import models
from db import database
from shared.blockchain_client import SSIBlockchainClient
from shared.settings import SETTINGS

app = FastAPI(title="VM1: Ministerio (Issuer)")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _get_cors_origins() -> list[str]:
    origins = SETTINGS.cors_origins
    return origins if origins else ["*"]


cors_origins = _get_cors_origins()
allow_credentials = "*" not in cors_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

ISSUER_FILE = SETTINGS.issuer_wallet_file
if not os.path.exists(ISSUER_FILE):
    raise RuntimeError("Debe ejecutar setup_issuer.py primero")

with open(ISSUER_FILE, "r") as f:
    issuer_data = json.load(f)
    ISSUER_DID = issuer_data["did"]
    ISSUER_KEY = issuer_data["private_key"]

DID_PATTERN = re.compile(r"^did:ethr:(0x[a-fA-F0-9]{40})$")
blockchain_client = None
ADMIN_USER = os.getenv("SSI_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("SSI_ADMIN_PASSWORD", "admin123")


def _build_credential_status(credential_hash: str) -> dict:
    return {
        "id": f"urn:ssi:status:{credential_hash}",
        "type": "OnChainStatus2026",
        "statusPurpose": "revocation",
        "statusListName": "SSIRegistryOnChain",
        "statusListIndex": 0,
        "statusListCredential": "urn:ssi:registry:onchain",
    }


def _build_credential_schema() -> dict:
    return {
        "id": "urn:ssi:schema:over18-credential:v1",
        "type": "JsonSchema",
    }


def _admin_auth_error() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Credenciales admin invalidas",
        headers={"WWW-Authenticate": "Basic"},
    )


def _require_admin(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Basic "):
        raise _admin_auth_error()

    encoded = authorization.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except (ValueError, binascii.Error, UnicodeDecodeError):
        raise _admin_auth_error()

    if ":" not in decoded:
        raise _admin_auth_error()

    username, password = decoded.split(":", 1)
    if username != ADMIN_USER or password != ADMIN_PASSWORD:
        raise _admin_auth_error()


def _serialize_citizen(citizen: models.CitizenDB) -> dict:
    return {
        "id": citizen.id,
        "numero_dni": citizen.numero_dni,
        "nombre": citizen.nombre,
        "fecha_nacimiento": citizen.fecha_nacimiento,
    }


def _fecha_from_edad(edad: int) -> str:
    if edad < 0 or edad > 130:
        raise HTTPException(status_code=400, detail="edad fuera de rango (0-130)")
    year = datetime.datetime.utcnow().year - edad
    return f"{year:04d}-01-01"

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_blockchain_client() -> SSIBlockchainClient:
    global blockchain_client
    if blockchain_client is None:
        blockchain_client = SSIBlockchainClient()
    return blockchain_client


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "issuer",
        "network": SETTINGS.blockchain_network,
        "contractFile": SETTINGS.contract_file,
    }


@app.get("/api/admin/citizens")
@limiter.limit("20/minute")
async def list_citizens(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization)
    citizens = db.query(models.CitizenDB).order_by(models.CitizenDB.id.desc()).all()
    return {"items": [_serialize_citizen(citizen) for citizen in citizens]}


@app.post("/api/admin/citizens")
@limiter.limit("20/minute")
async def create_citizen(
    request: Request,
    data: dict,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(authorization)

    numero_dni = str(data.get("numero_dni", "")).strip().upper()
    nombre = str(data.get("nombre", "")).strip()
    fecha_nacimiento = str(data.get("fecha_nacimiento", "")).strip()
    edad_raw = data.get("edad")

    if not numero_dni:
        raise HTTPException(status_code=400, detail="numero_dni es obligatorio")
    if not nombre:
        raise HTTPException(status_code=400, detail="nombre es obligatorio")

    if not fecha_nacimiento and edad_raw is not None and str(edad_raw).strip() != "":
        try:
            fecha_nacimiento = _fecha_from_edad(int(edad_raw))
        except ValueError:
            raise HTTPException(status_code=400, detail="edad debe ser un numero entero")

    if not fecha_nacimiento:
        raise HTTPException(status_code=400, detail="fecha_nacimiento o edad es obligatorio")

    try:
        datetime.datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="fecha_nacimiento debe tener formato YYYY-MM-DD")

    existing = db.query(models.CitizenDB).filter(models.CitizenDB.numero_dni == numero_dni).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un ciudadano con ese numero_dni")

    citizen = models.CitizenDB(
        numero_dni=numero_dni,
        nombre=nombre,
        fecha_nacimiento=fecha_nacimiento,
    )
    db.add(citizen)
    db.commit()
    db.refresh(citizen)

    return {"status": "created", "citizen": _serialize_citizen(citizen)}

@app.post("/api/credentials/issue_dni")
@limiter.limit("5/minute")
async def issue_dni(request: Request, data: dict, db: Session = Depends(get_db)):
    numero_dni = data.get("numero_dni")
    did_usuario = data.get("did_ciudadano")

    if not isinstance(did_usuario, str) or not DID_PATTERN.match(did_usuario):
        raise HTTPException(status_code=400, detail="did_ciudadano invalido")
    
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
        "validFrom": datetime.datetime.utcnow().isoformat() + "Z",
        "expirationDate": (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat() + "Z",
        "credentialSchema": _build_credential_schema(),
        "credentialSubject": {
            "id": did_usuario,
            "isOver18": True
        },
        "termsOfUse": [
            {
                "type": "IssuerPolicy",
                "profile": "eidas-aligned-demo",
                "readable": "Uso limitado a demostracion SSI y validacion on-chain."
            }
        ]
    }

    vc_hash = SSIBlockchainClient.canonical_credential_hash(vc)
    vc["credentialHash"] = vc_hash
    vc["credentialStatus"] = _build_credential_status(vc_hash)

    try:
        bc = get_blockchain_client()
        tx_did = bc.set_did_status(
            holder_did=did_usuario,
            active=True,
            metadata_text=f"issue_dni:{numero_dni}",
            sender_private_key=ISSUER_KEY,
        )
        tx_register = bc.register_credential(
            credential_hash=vc_hash,
            subject_did=did_usuario,
            sender_private_key=ISSUER_KEY,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error de datos blockchain: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Blockchain no disponible para emitir: {str(e)}")

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

    return {
        "credential": vc,
        "onchain": {
            "didStatusTx": tx_did,
            "registerCredentialTx": tx_register
        }
    }


@app.post("/api/credentials/revoke")
@limiter.limit("5/minute")
async def revoke_credential(request: Request, data: dict):
    credential_hash = data.get("credential_hash")
    reason = data.get("reason", "revoked")

    try:
        bc = get_blockchain_client()
        tx_revoke = bc.revoke_credential(
            credential_hash=credential_hash,
            reason_text=reason,
            sender_private_key=ISSUER_KEY,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Entrada invalida para revocacion: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Blockchain no disponible para revocar: {str(e)}")

    return {
        "status": "revoked",
        "credential_hash": credential_hash,
        "tx": tx_revoke,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SETTINGS.app_bind_host, port=SETTINGS.issuer_port)