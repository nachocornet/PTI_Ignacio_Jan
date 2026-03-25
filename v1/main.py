from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import secrets
import requests
import datetime
from eth_account import Account
from eth_account.messages import encode_defunct
import json
import os
from contextlib import asynccontextmanager

# --- Escudo Anti-DDoS (Rate Limiting) ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- Base de Datos ---
from database import SessionLocal, engine
import models

# 1. INICIALIZACIÓN DE BASE DE DATOS
# Crea el archivo ssi_sessions.db y las tablas si no existen
models.Base.metadata.create_all(bind=engine)

# 2. CONFIGURACIÓN DEL LIMITADOR DE TASA (Anti-DDoS)
limiter = Limiter(key_func=get_remote_address)

# 3. INICIALIZACIÓN DE LA APP FASTAPI
app = FastAPI(title="SSI Authenticator Node")

# Conectamos el limitador a la aplicación
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 4. CONFIGURACIÓN CORS (Para conectar con un futuro Frontend web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite conexiones desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"], # Permite todas las cabeceras
)

ISSUER_WALLET_FILE = "issuer_wallet.json"
ISSUER_DID = None
ISSUER_PRIVATE_KEY = None

# Verificamos si el servidor tiene su identidad creada antes de arrancar
if not os.path.exists(ISSUER_WALLET_FILE):
    print("ADVERTENCIA: No se encontró issuer_wallet.json. Ejecuta setup_issuer.py primero.")
else:
    with open(ISSUER_WALLET_FILE, "r") as f:
        wallet = json.load(f)
        ISSUER_DID = wallet["did"]
        ISSUER_PRIVATE_KEY = wallet["private_key"]
        print(f"Identidad del Emisor cargada correctamente: {ISSUER_DID}")

# 5. DEPENDENCIA DE BASE DE DATOS
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 6. MODELOS DE VALIDACIÓN (Pydantic)
class VerifyRequest(BaseModel):
    did: str
    session_id: str
    signature: str

# 7. FUNCIONES AUXILIARES
def resolve_did(did: str):
    url = f"https://dev.uniresolver.io/1.0/identifiers/{did}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        if did.startswith("did:ethr:"):
            return did.split(":")[-1]
    except Exception:
        return None
    return None

# ==========================================
# ENDPOINTS DE LA API
# ==========================================

# --- HEALTH CHECK ---
@app.get("/health")
@limiter.exempt # Exento de límites para poder monitorizarlo siempre
def health_check(db: Session = Depends(get_db)):
    try:
        # Petición básica a la BD para asegurar que está conectada y viva
        db.execute(text("SELECT 1"))
        db_status = "conectada"
    except Exception:
        db_status = "error"
        raise HTTPException(status_code=503, detail="La base de datos SQLite no responde")
        
    return {
        "status": "online",
        "database": db_status,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# --- GENERACIÓN DE RETO (CHALLENGE) ---
@app.get("/api/auth/challenge")
@limiter.limit("5/minute") # Límite: 5 peticiones por minuto por IP
def get_challenge(request: Request, db: Session = Depends(get_db)):
    
    # 1. Limpieza Pasiva (Garbage Collection): Borrar retos más viejos de 10 min
    tiempo_limite = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
    db.query(models.AuthSession).filter(models.AuthSession.created_at < tiempo_limite).delete()
    db.commit()
    
    # 2. Generar el nuevo reto
    session_id = str(uuid.uuid4())
    nonce = secrets.token_hex(16)
    
    # 3. Guardar en SQLite
    db_session = models.AuthSession(session_id=session_id, nonce=nonce)
    db.add(db_session)
    db.commit()
    
    return {"session_id": session_id, "nonce": nonce}

# --- VERIFICACIÓN DE FIRMA (VERIFY) ---
@app.post("/api/auth/verify")
@limiter.limit("10/minute") # Límite: 10 peticiones por minuto por IP
def verify_signature(request: Request, req: VerifyRequest, db: Session = Depends(get_db)):
    
    # 1. Buscar la sesión en SQLite
    db_session = db.query(models.AuthSession).filter(models.AuthSession.session_id == req.session_id).first()
    
    if not db_session:
        raise HTTPException(status_code=400, detail="Sesión inválida o inexistente")
    
    # 2. Comprobar Caducidad (TTL de 10 minutos)
    tiempo_actual = datetime.datetime.utcnow()
    diferencia_tiempo = tiempo_actual - db_session.created_at
    
    if diferencia_tiempo.total_seconds() > 600:
        db.delete(db_session)
        db.commit()
        raise HTTPException(status_code=401, detail="El reto ha caducado (Máximo 10 minutos). Vuelve a solicitar acceso.")
    
    nonce = db_session.nonce
    
    # 3. Matemáticas de Curva Elíptica (Recuperar clave pública de la firma)
    try:
        message = encode_defunct(text=nonce)
        recovered_address = Account.recover_message(message, signature=req.signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Firma criptográfica malformada")
        
    # 4. Validar Identidad (Comparar dirección recuperada con la del DID)
    expected_address = req.did.split(":")[-1]
    
    if recovered_address.lower() != expected_address.lower():
        raise HTTPException(status_code=401, detail="Acceso Denegado: La firma no corresponde a este DID")
        
    # 5. Destruir el reto tras su uso (Prevenir Replay Attacks)
    db.delete(db_session)
    db.commit()
    
    return {"status": "success", "message": "Autenticación correcta validada", "did": req.did}