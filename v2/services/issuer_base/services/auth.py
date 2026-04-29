"""
Autenticación base: Basic Auth para admin.
Reutilizable por todos los issuers.
"""

import base64
import binascii
import os
from fastapi import HTTPException


def get_admin_credentials() -> tuple[str, str]:
    """Obtiene credenciales admin desde variables de entorno."""
    username = os.getenv("SSI_ADMIN_USER", "admin")
    password = os.getenv("SSI_ADMIN_PASSWORD", "admin123")
    return username, password


def admin_auth_error() -> HTTPException:
    """Excepción estándar para error de autenticación admin."""
    return HTTPException(
        status_code=401,
        detail="Credenciales admin inválidas",
        headers={"WWW-Authenticate": "Basic"},
    )


def require_admin(authorization: str | None) -> None:
    """
    Valida que el header Authorization sea correcto.
    Lanza excepción si no es válido.
    
    Args:
        authorization: Header Authorization (ej: "Basic YWRtaW46YWRtaW4xMjM=")
    
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    if not authorization or not authorization.startswith("Basic "):
        raise admin_auth_error()

    encoded = authorization.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except (ValueError, binascii.Error, UnicodeDecodeError):
        raise admin_auth_error()

    if ":" not in decoded:
        raise admin_auth_error()

    username, password = decoded.split(":", 1)
    expected_user, expected_pass = get_admin_credentials()
    
    if username != expected_user or password != expected_pass:
        raise admin_auth_error()
