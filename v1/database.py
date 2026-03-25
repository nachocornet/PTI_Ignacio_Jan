from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Esto creará un archivo oculto llamado "ssi_sessions.db" en tu directorio
SQLALCHEMY_DATABASE_URL = "sqlite:///./ssi_sessions.db"

# check_same_thread=False es vital en FastAPI con SQLite para que no se bloqueen las peticiones
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Esta es la "fábrica" de sesiones. Cada vez que alguien entra a la web, creamos una sesión.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán nuestros modelos (tablas)
Base = declarative_base()