"""
Servicio de base de datos genérico.
Reutilizable por todos los issuers.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Si existe DATABASE_URL (ej. en Docker), úsala. Si no, usa SQLite local.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ssi_issuer.db")

# SQLite necesita 'check_same_thread', pero Postgres da error si se lo pasas.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency injection para obtener sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(base_declarative):
    """Inicializa las tablas en la base de datos."""
    base_declarative.metadata.create_all(bind=engine)
