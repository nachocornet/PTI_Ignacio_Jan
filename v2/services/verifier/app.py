import json
import copy
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from eth_account import Account
from eth_account.messages import encode_defunct
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from shared.blockchain_client import SSIBlockchainClient
from shared.settings import SETTINGS

app = FastAPI(title="VM3: Verificador (Service)")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _get_cors_origins() -> list[str]:
    return SETTINGS.cors_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
blockchain_client = None


def get_blockchain_client() -> SSIBlockchainClient:
    global blockchain_client
    if blockchain_client is None:
        blockchain_client = SSIBlockchainClient()
    return blockchain_client


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "verifier",
        "network": SETTINGS.blockchain_network,
        "contractFile": SETTINGS.contract_file,
    }


def _normalize_credential_status(vc_payload: dict) -> dict | None:
    status = vc_payload.get("credentialStatus")
    if not isinstance(status, dict):
        return None
    return {
        "id": status.get("id"),
        "type": status.get("type"),
        "statusPurpose": status.get("statusPurpose"),
        "statusListName": status.get("statusListName"),
        "statusListIndex": status.get("statusListIndex"),
        "statusListCredential": status.get("statusListCredential"),
    }
@app.post("/api/verify_presentation")
@limiter.limit("10/minute")
async def verify_presentation(request: Request, data: dict):
    vp = data.get("vp")
    if not vp:
        raise HTTPException(status_code=400, detail="Formato de presentacion invalido")
    
    vc = vp.get("verifiableCredential")
    if not vc:
        raise HTTPException(status_code=400, detail="Falta verifiableCredential en la presentacion")

    vc_payload = None

    try:
        # 1. Verificar firma del Emisor en la VC
        vc_payload = copy.deepcopy(vc)
        vc_proof = vc_payload.pop("proof")
        vc_canonical = json.dumps(vc_payload, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
        issuer_recovered = Account.recover_message(
            encode_defunct(text=vc_canonical), 
            signature=vc_proof["proofValue"]
        )
        if f"did:ethr:{issuer_recovered.lower()}" != vc_payload["issuer"].lower():
            raise HTTPException(status_code=401, detail="Firma del Emisor no valida")

        # 2. Verificar firma del Poseedor en la VP
        vp_payload = copy.deepcopy(vp)
        vp_proof = vp_payload.pop("proof")
        vp_canonical = json.dumps(vp_payload, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
        holder_recovered = Account.recover_message(
            encode_defunct(text=vp_canonical), 
            signature=vp_proof["proofValue"]
        )
        
        holder_did = f"did:ethr:{holder_recovered.lower()}"
        subject_did = vc_payload["credentialSubject"]["id"].lower()
        
        if holder_did != subject_did:
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "El poseedor no es el titular de la credencial",
                    "esperado_subject_id": subject_did,
                    "obtenido_de_la_firma": holder_did
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en validacion criptografica: {str(e)}")
    
    try:
        bc = get_blockchain_client()
        issuer_did = vc_payload["issuer"]
        holder_did = vc_payload["credentialSubject"]["id"]
        credential_hash = vc_payload.get("credentialHash")
        if not credential_hash:
            vc_for_hash = copy.deepcopy(vc_payload)
            vc_for_hash.pop("credentialHash", None)
            credential_hash = SSIBlockchainClient.canonical_credential_hash(vc_for_hash)

        if not bc.is_issuer_authorized(issuer_did):
            raise HTTPException(status_code=401, detail="Issuer DID no autorizado on-chain")

        if not bc.is_did_active(holder_did):
            raise HTTPException(status_code=401, detail="DID del titular inactivo o revocado on-chain")

        if bc.is_credential_revoked(credential_hash):
            raise HTTPException(status_code=401, detail="Credencial revocada on-chain")

        _normalize_credential_status(vc_payload)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error consultando blockchain: {str(e)}")

    return {
        "status": "success",
        "message": "Verificacion completada. Acceso concedido.",
        "onchain": {
            "issuerAuthorized": True,
            "holderDidActive": True,
            "credentialRevoked": False,
        },
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SETTINGS.app_bind_host, port=SETTINGS.verifier_port)