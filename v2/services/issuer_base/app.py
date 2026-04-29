"""
Aplicación FastAPI base para cualquier issuer.
Inicializa middleware, rutas base, y proporciona hooks para que issuers específicos
extiendan la aplicación.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from shared.settings import SETTINGS
from services.issuer_base.routes import health, admin, credentials


def create_app(
    title: str = "Generic Issuer",
    issuer_did: str | None = None,
    issuer_key: str | None = None,
) -> FastAPI:
    """
    Factory function para crear la app FastAPI base.
    
    Args:
        title: Nombre de la aplicación (para Swagger)
        issuer_did: DID del issuer (se setea en credentials router)
        issuer_key: Private key del issuer (se setea en credentials router)
    
    Returns:
        FastAPI app configurada y lista para usar
    
    Uso:
        # En issuer_dni/app.py
        app = create_app(
            title="Issuer DNI",
            issuer_did=ISSUER_DID,
            issuer_key=ISSUER_KEY,
        )
        # Luego extender rutas específicas DNI
    """
    
    app = FastAPI(title=title)
    
    # Rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # CORS
    def _get_cors_origins() -> list[str]:
        origins = SETTINGS.cors_origins
        return origins if origins else ["*"]
    
    cors_origins = _get_cors_origins()
    allow_credentials = "*" not in cors_origins
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setear credenciales issuer (si se proporcionan)
    if issuer_did and issuer_key:
        credentials.set_issuer_credentials(issuer_did, issuer_key)
    
    # Incluir rutas base
    app.include_router(health.router)
    app.include_router(admin.router)
    app.include_router(credentials.router)
    
    return app
