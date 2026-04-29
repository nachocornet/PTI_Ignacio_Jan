"""
Rutas específicas para issuer_dni.
Importa y extiende rutas base, añadiendo lógica DNI-specific.
"""

import datetime
import json
import uuid
import re
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from sqlalchemy.orm import Session
from eth_account import Account
from eth_account.messages import encode_defunct
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

from shared.blockchain_client import SSIBlockchainClient
from services.issuer_base.services.auth import require_admin
from services.issuer_base.services.database import get_db
from services.issuer_base.routes.credentials import (
    _build_vc,
    _build_credential_status,
    set_issuer_credentials,
)

# Importar validadores DNI
from services.issuer_dni.validators import (
    validate_dni_format,
    validate_dni_checksum,
    validate_age,
    validate_fecha_format,
)
from services.issuer_dni.models import CitizenDNI

router = APIRouter(tags=["credentials_dni"])
limiter = Limiter(key_func=get_remote_address)

DID_PATTERN = re.compile(r"^did:ethr:(0x[a-fA-F0-9]{40})$")

# Se setean por issuer_dni/app.py
ISSUER_DID = None
ISSUER_KEY = None


def set_dni_issuer_credentials(did: str, key: str) -> None:
    """Fija credenciales del issuer DNI."""
    global ISSUER_DID, ISSUER_KEY
    ISSUER_DID = did
    ISSUER_KEY = key
    set_issuer_credentials(did, key)  # También notificar a rutas base


def _serialize_citizen_dni(citizen: CitizenDNI) -> dict:
    """Serializa un ciudadano DNI a dict."""
    return {
        "id": citizen.id,
        "numero_dni": citizen.numero_dni,
        "nombre": citizen.nombre,
        "fecha_nacimiento": citizen.fecha_nacimiento,
        "created_at": citizen.created_at.isoformat() if citizen.created_at else None,
    }


def _fecha_from_edad(edad: int) -> str:
    """Calcula fecha de nacimiento a partir de edad."""
    if edad < 0 or edad > 130:
        raise HTTPException(status_code=400, detail="edad fuera de rango (0-130)")
    year = datetime.datetime.utcnow().year - edad
    return f"{year:04d}-01-01"


@router.get("/api/admin/citizens_dni")
@limiter.limit("20/minute")
async def list_citizens_dni(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Lista ciudadanos DNI (requiere admin auth)."""
    require_admin(authorization)
    citizens = db.query(CitizenDNI).order_by(CitizenDNI.id.desc()).all()
    return {"items": [_serialize_citizen_dni(citizen) for citizen in citizens]}


@router.post("/api/admin/citizens_dni")
@limiter.limit("20/minute")
async def create_citizen_dni(
    request: Request,
    data: dict,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Crea un ciudadano DNI con validaciones específicas.
    
    Espera:
    {
        "numero_dni": "12345678A",
        "nombre": "John Doe",
        "fecha_nacimiento": "1990-01-15"  // o "edad": 35
    }
    """
    require_admin(authorization)

    numero_dni = str(data.get("numero_dni", "")).strip().upper()
    nombre = str(data.get("nombre", "")).strip()
    fecha_nacimiento = str(data.get("fecha_nacimiento", "")).strip()
    edad_raw = data.get("edad")

    # Validaciones
    if not numero_dni:
        raise HTTPException(status_code=400, detail="numero_dni es obligatorio")
    
    if not validate_dni_format(numero_dni):
        raise HTTPException(status_code=400, detail="Formato DNI inválido (debe ser 8 dígitos + letra)")
    
    if not validate_dni_checksum(numero_dni):
        raise HTTPException(status_code=400, detail="Letra de control DNI inválida")
    
    if not nombre:
        raise HTTPException(status_code=400, detail="nombre es obligatorio")

    # Si no hay fecha, intentar calcularla desde edad
    if not fecha_nacimiento and edad_raw is not None and str(edad_raw).strip() != "":
        try:
            fecha_nacimiento = _fecha_from_edad(int(edad_raw))
        except ValueError:
            raise HTTPException(status_code=400, detail="edad debe ser un número entero")

    if not fecha_nacimiento:
        raise HTTPException(status_code=400, detail="fecha_nacimiento o edad es obligatorio")

    # Validar formato fecha
    if not validate_fecha_format(fecha_nacimiento):
        raise HTTPException(status_code=400, detail="fecha_nacimiento debe tener formato YYYY-MM-DD")

    # Verificar que no exista
    existing = db.query(CitizenDNI).filter(CitizenDNI.numero_dni == numero_dni).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un ciudadano con ese DNI")

    # Crear
    citizen = CitizenDNI(
        numero_dni=numero_dni,
        nombre=nombre,
        fecha_nacimiento=fecha_nacimiento,
    )
    db.add(citizen)
    db.commit()
    db.refresh(citizen)

    return {"status": "created", "citizen": _serialize_citizen_dni(citizen)}


@router.post("/api/credentials/issue_dni")
@limiter.limit("5/minute")
async def issue_dni(request: Request, data: dict, db: Session = Depends(get_db)):
    """
    Emite una credencial Over18 para un ciudadano DNI.
    
    Espera:
    {
        "numero_dni": "12345678A",
        "did_ciudadano": "did:ethr:0x..."
    }
    """
    numero_dni = data.get("numero_dni")
    did_usuario = data.get("did_ciudadano")

    # Validar DID
    if not isinstance(did_usuario, str) or not DID_PATTERN.match(did_usuario):
        raise HTTPException(status_code=400, detail="did_ciudadano inválido")
    
    # Buscar ciudadano
    ciudadano = db.query(CitizenDNI).filter(CitizenDNI.numero_dni == numero_dni.upper()).first()
    if not ciudadano:
        raise HTTPException(status_code=404, detail="Ciudadano DNI no encontrado")

    # Construir VC Over18
    es_mayor = validate_age(ciudadano.fecha_nacimiento, min_age=18) # Cálculo dinámico
    vc = _build_vc(
        credential_type="Over18Credential",
        did_usuario=did_usuario,
        credential_subject={"isOver18": es_mayor}, # <--- Aquí se guarda True o False
        extra_fields={
            "termsOfUse": [
                {
                    "type": "IssuerPolicy",
                    "profile": "eidas-aligned-demo",
                    "readable": "Uso limitado a demostración SSI y validación on-chain."
                }
            ]
        }
    )

    # Hash y status en blockchain
    vc_hash = SSIBlockchainClient.canonical_credential_hash(vc)
    vc["credentialHash"] = vc_hash
    vc["credentialStatus"] = _build_credential_status(vc_hash)

    # Transacciones blockchain
    try:
        bc = SSIBlockchainClient()
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
        raise HTTPException(status_code=503, detail=f"Blockchain no disponible: {str(e)}")

    # Firmar VC
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
