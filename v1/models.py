from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    # session_id es lo que le enviamos al cliente (UUID)
    session_id = Column(String, unique=True, index=True)
    # nonce es el reto matemático que el cliente debe firmar
    nonce = Column(String)
    # Guardamos la fecha para, en el futuro, poder borrar sesiones caducadas
    created_at = Column(DateTime, default=datetime.datetime.utcnow)