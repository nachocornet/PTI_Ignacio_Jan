"""
Modelos base genéricos para cualquier issuer.
Los issuers específicos (ej. issuer_dni) extienden CitizenBase con campos adicionales.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class CitizenBase(Base):
    """
    Modelo base abstracto para ciudadanos/sujetos de credenciales.
    
    Cada issuer específico (ej. issuer_dni) extiende este con:
    - Campos adicionales (numero_dni, fecha_nacimiento, etc)
    - Validaciones específicas
    - Esquemas de credencial específicos
    """
    __tablename__ = "citizens"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, index=True)  # DNI, pasaporte, etc. Genérico.
    name = Column(String, index=True)
    extra_data = Column(JSON, nullable=True)  # Flexible para datos específicos por issuer
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AuthSession(Base):
    """Sesiones de autenticación para el portal de login."""
    __tablename__ = "auth_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    nonce = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
