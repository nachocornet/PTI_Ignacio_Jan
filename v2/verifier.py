import json
import copy
from fastapi import FastAPI, HTTPException, Request
from eth_account import Account
from eth_account.messages import encode_defunct
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI(title="VM3: Verificador (Service)")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/verify_presentation")
@limiter.limit("10/minute")
async def verify_presentation(request: Request, data: dict):
    vp = data.get("vp")
    if not vp:
        raise HTTPException(status_code=400, detail="Formato de presentacion invalido")
    
    vc = vp.get("verifiableCredential")
    if not vc:
        raise HTTPException(status_code=400, detail="Falta verifiableCredential en la presentacion")
    
    try:
        # 1. Verificar firma del Emisor en la VC
        vc_payload = copy.deepcopy(vc)
        vc_proof = vc_payload.pop("proof")
        vc_canonical = json.dumps(vc_payload, separators=(',', ':'), sort_keys=True)
        issuer_recovered = Account.recover_message(
            encode_defunct(text=vc_canonical), 
            signature=vc_proof["proofValue"]
        )
        if f"did:ethr:{issuer_recovered.lower()}" != vc_payload["issuer"].lower():
            raise HTTPException(status_code=401, detail="Firma del Emisor no valida")

        # 2. Verificar firma del Poseedor en la VP
        vp_payload = copy.deepcopy(vp)
        vp_proof = vp_payload.pop("proof")
        vp_canonical = json.dumps(vp_payload, separators=(',', ':'), sort_keys=True)
        holder_recovered = Account.recover_message(
            encode_defunct(text=vp_canonical), 
            signature=vp_proof["proofValue"]
        )
        
        # Validacion de pertenencia (DUEÑO REAL)
        if f"did:ethr:{holder_recovered.lower()}" != vc_payload["credentialSubject"]["id"].lower():
            raise HTTPException(status_code=401, detail="El poseedor no es el titular de la credencial")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en validacion criptografica: {str(e)}")

    return {"status": "success", "message": "Verificacion completada. Acceso concedido."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5031)