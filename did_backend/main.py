from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import secrets

app = FastAPI(title="DID Verifier Node")

# Base de datos temporal en memoria (En el futuro usaremos una base de datos real)
# Aquí guardaremos: {"session_id": "nonce_aleatorio"}
active_challenges = {}

# --- MODELOS DE DATOS (Lo que esperamos recibir en los JSON) ---
class VerifyRequest(BaseModel):
    session_id: str
    did: str
    signature: str
    presentation: dict  # Aquí vendrá el Verifiable Presentation que diseñe Jan

# --- RUTAS DE LA API ---

@app.get("/api/auth/challenge")
async def get_challenge():
    """
    Paso 1: El cliente pide entrar. Le generamos un ID de sesión y un Nonce (reto).
    """
    session_id = str(uuid.uuid4()) # ID único para este intento de login
    nonce = secrets.token_hex(16)  # Texto aleatorio seguro
    
    # Guardamos el reto temporalmente en nuestra "base de datos"
    active_challenges[session_id] = nonce
    
    print(f"[SERVER] Nuevo reto generado para sesión {session_id}: {nonce}")
    
    return {
        "session_id": session_id,
        "nonce": nonce
    }

@app.post("/api/auth/verify")
async def verify_presentation(data: VerifyRequest):
    """
    Paso 2: El cliente nos devuelve el JSON firmado. Comprobamos si es válido.
    """
    # 1. Comprobar si la sesión existe y no ha caducado
    if data.session_id not in active_challenges:
        raise HTTPException(status_code=400, detail="Sesión inválida o caducada.")
    
    expected_nonce = active_challenges[data.session_id]
    
    # 2. (PLACEHOLDER) Aquí es donde en la Semana 2 meteremos la magia matemática.
    # Leeremos la clave pública del DID de Jan y verificaremos la firma.
    is_signature_valid = dummy_crypto_check(data.did, data.signature, expected_nonce)
    
    if not is_signature_valid:
        raise HTTPException(status_code=401, detail="Firma criptográfica inválida.")
    
    # 3. Si todo va bien, borramos el reto (solo se usa una vez) y damos acceso
    del active_challenges[data.session_id]
    
    print(f"[SERVER] Autenticación exitosa para el DID: {data.did}")
    return {"status": "success", "message": f"Bienvenido, usuario {data.did}"}

# --- FUNCIONES AUXILIARES ---

def dummy_crypto_check(did: str, signature: str, expected_nonce: str) -> bool:
    """
    Simulador de verificación. De momento, se traga cualquier firma que no esté vacía.
    La semana que viene cambiaremos esto por código criptográfico real.
    """
    if signature == "firma_falsa":
        return False
    return True