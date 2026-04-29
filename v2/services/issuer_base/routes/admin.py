"""
Rutas admin genéricas para CRUD de ciudadanos.
Los issuers específicos pueden extender este router.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.issuer_base.models import CitizenBase
from services.issuer_base.services.auth import require_admin
from services.issuer_base.services.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


def _serialize_citizen(citizen: CitizenBase) -> dict:
    """Serializa un ciudadano a dict. Reutilizable."""
    return {
        "id": citizen.id,
        "identifier": citizen.identifier,
        "name": citizen.name,
        "extra_data": citizen.extra_data,
        "created_at": citizen.created_at.isoformat() if citizen.created_at else None,
    }


@router.get("/citizens")
@limiter.limit("20/minute")
async def list_citizens(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Lista todos los ciudadanos (requiere autenticación admin)."""
    require_admin(authorization)
    citizens = db.query(CitizenBase).order_by(CitizenBase.id.desc()).all()
    return {"items": [_serialize_citizen(citizen) for citizen in citizens]}


@router.post("/citizens")
@limiter.limit("20/minute")
async def create_citizen_generic(
    request: Request,
    data: dict,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Crea un ciudadano genérico (requiere autenticación admin).
    Los issuers específicos pueden sobrescribir esto con lógica adicional.
    
    Espera:
    {
        "identifier": "generic-id-123",
        "name": "John Doe",
        "extra_data": {...}  # opcional
    }
    """
    require_admin(authorization)

    identifier = str(data.get("identifier", "")).strip()
    name = str(data.get("name", "")).strip()
    extra_data = data.get("extra_data", {})

    if not identifier:
        raise HTTPException(status_code=400, detail="identifier es obligatorio")
    if not name:
        raise HTTPException(status_code=400, detail="name es obligatorio")

    existing = db.query(CitizenBase).filter(CitizenBase.identifier == identifier).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un ciudadano con ese identifier")

    citizen = CitizenBase(
        identifier=identifier,
        name=name,
        extra_data=extra_data,
    )
    db.add(citizen)
    db.commit()
    db.refresh(citizen)

    return {"status": "created", "citizen": _serialize_citizen(citizen)}
