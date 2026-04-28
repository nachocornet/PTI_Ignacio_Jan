import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Si existe la variable DATABASE_URL (ej. en Docker), úsala. Si no, usa SQLite local.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ssi_sessions.db")

# SQLite necesita 'check_same_thread', pero Postgres da error si se lo pasas.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()