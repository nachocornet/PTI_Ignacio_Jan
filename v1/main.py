from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import secrets
import requests  # NUEVO: Para hablar con el Universal Resolver
from eth_account import Account
from eth_account.messages import encode_defunct

app = FastAPI(title="DID Verifier Node")

# Base de datos temporal de retos
active_challenges = {}

class VerifyRequest(BaseModel):
    session_id: str
    did: str
    signature: str
    presentation: dict

# --- NUEVAS FUNCIONES DEL SPRINT 2 ---

def resolve_did(did_string: str):
    """
    TAREA 1: Se conecta al Universal Resolver para descargar el DID Document.
    """
    resolver_url = f"https://dev.uniresolver.io/1.0/identifiers/{did_string}"
    print(f"[RESOLVER] Buscando DID en la red: {resolver_url}")
    
    try:
        response = requests.get(resolver_url, timeout=10) # 10 segundos de límite
        if response.status_code != 200:
            print(f"[ERROR] El Resolver devolvió estado {response.status_code}")
            return None
        return response.json()
    except Exception as e:
        print(f"[ERROR CRÍTICO] Fallo de conexión con el Resolver: {e}")
        return None

def extract_public_key(did_document: dict):
    """
    TAREA 2: Bucea en el JSON gigante para sacar la Clave Pública.
    """
    try:
        # Los DID Documents estándar guardan las claves en 'verificationMethod'
        doc = did_document.get("didDocument", {})
        methods = doc.get("verificationMethod", [])
        
        if not methods:
            return None
            
        # Cogemos la primera clave pública disponible
        first_method = methods[0]
        return first_method
    except Exception as e:
        print(f"[ERROR] No se pudo extraer la clave pública: {e}")
        return None

def verify_crypto_signature(expected_nonce: str, signature: str, did: str) -> bool:
    """
    Verificación real usando Criptografía de Curva Elíptica (Ethereum).
    """
    try:
        # 1. Reconstruimos el mensaje original que firmó Jan
        mensaje_preparado = encode_defunct(text=expected_nonce)

        # 2. Extraemos matemáticamente la dirección pública de quien hizo la firma
        direccion_recuperada = Account.recover_message(mensaje_preparado, signature=signature)

        # 3. Extraemos la dirección que Jan dice ser (la última parte de su DID)
        # Ej: de "did:ethr:sepolia:0xCA9..." sacamos "0xCA9..."
        direccion_del_did = did.split(":")[-1]

        print(f"[CRIPTO] Dirección recuperada de la firma: {direccion_recuperada}")
        print(f"[CRIPTO] Dirección esperada del DID: {direccion_del_did}")

        # 4. Comparamos ambas (las pasamos a minúsculas por si acaso)
        if direccion_recuperada.lower() == direccion_del_did.lower():
            return True
        else:
            return False

    except Exception as e:
        print(f"[ERROR CRIPTO] Fallo al procesar la firma: {e}")
        return False
    
    # IMPORTANTE PARA IGNACIO Y JAN:
    # Como Jan todavía no ha decidido si usará criptografía RSA, Ed25519 o Secp256k1,
    # dejamos la estructura preparada. La semana que viene, cuando Jan defina
    # su algoritmo, aquí meteremos las 3 líneas de la librería 'cryptography' de Python.
    
    if signature == "firma_falsa":
        return False
        
    return True # De momento lo damos por válido para que puedas probar el flujo completo

# --- RUTAS DE LA API (Actualizadas) ---

@app.get("/api/auth/challenge")
async def get_challenge():
    session_id = str(uuid.uuid4())
    nonce = secrets.token_hex(16)
    active_challenges[session_id] = nonce
    return {"session_id": session_id, "nonce": nonce}

@app.post("/api/auth/verify")
async def verify_presentation(data: VerifyRequest):
    # TAREA 4: Control de Errores (Si la sesión es falsa o caducó)
    if data.session_id not in active_challenges:
        raise HTTPException(status_code=400, detail="Sesión inválida o caducada.")
    
    expected_nonce = active_challenges[data.session_id]
    
    # 1. Hablar con el Resolver
    did_data = resolve_did(data.did)
    if not did_data:
        raise HTTPException(status_code=404, detail=f"El DID '{data.did}' no existe o la red está caída.")

    # 2. Extraer Clave Pública
    public_key_data = extract_public_key(did_data)
    if not public_key_data:
        raise HTTPException(status_code=400, detail="El DID document no contiene claves públicas válidas.")

    # 3. Comprobar Firma Criptográfica (NUEVO)
    is_valid = verify_crypto_signature(expected_nonce, data.signature, data.did)    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Firma inválida. ¡Acceso Denegado!")
    
    # 4. Éxito
    del active_challenges[data.session_id]
    return {
        "status": "success", 
        "message": f"¡Bienvenido! He resuelto tu DID y tu firma es correcta.",
        "resolved_public_key_id": public_key_data.get("id", "Desconocido")
    }