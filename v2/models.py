from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    nonce = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CitizenDB(Base):
    __tablename__ = "citizens"
    id = Column(Integer, primary_key=True, index=True)
    numero_dni = Column(String, unique=True, index=True)
    nombre = Column(String)
    fecha_nacimiento = Column(String) # Formato YYYY-MM-DD