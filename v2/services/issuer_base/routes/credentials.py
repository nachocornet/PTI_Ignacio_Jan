"""
Rutas de credenciales genéricas (issue/revoke).
Los issuers específicos importan esto y pueden extender con tipos específicos.
"""

import json
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from eth_account import Account
from eth_account.messages import encode_defunct
from slowapi import Limiter
from slowapi.util import get_remote_address
import os
import re

from shared.blockchain_client import SSIBlockchainClient
from services.issuer_base.services.database import get_db

router = APIRouter(prefix="/api/credentials", tags=["credentials"])
limiter = Limiter(key_func=get_remote_address)

DID_PATTERN = re.compile(r"^did:ethr:(0x[a-fA-F0-9]{40})$")

# Se obtienen en tiempo de ejecución (por el issuer específico)
ISSUER_DID = None
ISSUER_KEY = None


def set_issuer_credentials(did: str, key: str) -> None:
    """Fija las credenciales del issuer (debe llamarse en startup)."""
    global ISSUER_DID, ISSUER_KEY
    ISSUER_DID = did
    ISSUER_KEY = key


def _build_credential_status(credential_hash: str) -> dict:
    """Construye el status de credencial estándar."""
    return {
        "id": f"urn:ssi:status:{credential_hash}",
        "type": "OnChainStatus2026",
        "statusPurpose": "revocation",
        "statusListName": "SSIRegistryOnChain",
        "statusListIndex": 0,
        "statusListCredential": "urn:ssi:registry:onchain",
    }


def _build_credential_schema() -> dict:
    """Construye el schema de credencial genérico."""
    return {
        "id": "urn:ssi:schema:generic-credential:v1",
        "type": "JsonSchema",
    }


def _build_vc(
    credential_type: str | list,
    did_usuario: str,
    credential_subject: dict,
    extra_fields: dict | None = None,
) -> dict:
    """
    Construye una Verifiable Credential genérica.
    
    Args:
        credential_type: Ej. "Over18Credential" o ["VerifiableCredential", "Over18Credential"]
        did_usuario: DID del sujeto
        credential_subject: Datos adicionales del sujeto
        extra_fields: Campos adicionales a incluir en la VC (ej. termsOfUse)
    
    Returns:
        VC sin proof (se añade después de firmar)
    """
    if isinstance(credential_type, str):
        credential_type = [credential_type]
    
    if "VerifiableCredential" not in credential_type:
        credential_type = ["VerifiableCredential"] + credential_type

    vc = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "id": f"urn:uuid:{uuid.uuid4()}",
        "type": credential_type,
        "issuer": ISSUER_DID,
        "issuanceDate": datetime.datetime.utcnow().isoformat() + "Z",
        "validFrom": datetime.datetime.utcnow().isoformat() + "Z",
        "expirationDate": (datetime.datetime.utcnow() + datetime.timedelta(days=365)).isoformat() + "Z",
        "credentialSchema": _build_credential_schema(),
        "credentialSubject": {
            "id": did_usuario,
            **credential_subject
        }
    }
    
    if extra_fields:
        vc.update(extra_fields)
    
    return vc


@router.post("/issue")
@limiter.limit("5/minute")
async def issue_generic(request: Request, data: dict):
    """
    Emite una credencial genérica (sin lógica específica de dominio).
    Los issuers específicos (ej. issuer_dni) tienen sus propios endpoints como /issue_dni.
    """
    raise HTTPException(
        status_code=501,
        detail="Use /credentials/issue_<tipo> específico para su issuer"
    )


@router.post("/revoke")
@limiter.limit("5/minute")
async def revoke_credential(request: Request, data: dict):
    """
    Revoca una credencial en blockchain.
    Genérico para cualquier tipo de credencial.
    """
    credential_hash = data.get("credential_hash")
    reason = data.get("reason", "revoked")

    if not credential_hash:
        raise HTTPException(status_code=400, detail="credential_hash es obligatorio")

    if not ISSUER_KEY:
        raise HTTPException(status_code=500, detail="Issuer no configurado correctamente")

    try:
        bc = SSIBlockchainClient()
        tx_revoke = bc.revoke_credential(
            credential_hash=credential_hash,
            reason_text=reason,
            sender_private_key=ISSUER_KEY,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Entrada inválida para revocación: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Blockchain no disponible: {str(e)}")

    return {
        "status": "revoked",
        "credential_hash": credential_hash,
        "tx": tx_revoke,
    }
