"""
Ruta health check genérica.
"""

from fastapi import APIRouter
import os
from shared.settings import SETTINGS

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    issuer_name = os.getenv("SSI_ISSUER_NAME", "Generic Issuer")
    return {
        "status": "ok",
        "service": issuer_name,
        "network": SETTINGS.blockchain_network,
        "contractFile": SETTINGS.contract_file,
    }
