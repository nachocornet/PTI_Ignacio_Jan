"""
Modelos específicos para DNI.
CitizenDNI extiende CitizenBase con campos DNI-specific.
"""

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class CitizenDNI(Base):
    """
    Modelo para ciudadanos DNI.
    Extiende el concepto de CitizenBase pero con tabla específica DNI.
    
    En una arquitectura más compleja, podrías usar Single Table Inheritance
    o Multi-Table Inheritance con SQLAlchemy, pero por simplicidad
    mantenemos tabla separada y mapeamos cuando es necesario.
    """
    __tablename__ = "citizens_dni"
    
    # Campos de CitizenBase
    id = Column(Integer, primary_key=True, index=True)
    numero_dni = Column(String, unique=True, index=True)
    nombre = Column(String, index=True)
    fecha_nacimiento = Column(String)  # Formato YYYY-MM-DD
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
