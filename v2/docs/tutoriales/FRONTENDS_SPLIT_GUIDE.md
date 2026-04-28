# Guía de Frontends Separados

## Objetivo

Separar interfaz de operación interna (admin/issuer) de interfaz de titular (holder/verifier) para un despliegue más realista.

## URLs

Con `start_all.py` activo:

- Portal: `/frontend_portal.html`
- Issuer Dashboard: `/issuer_dashboard.html`
- Verifier Dashboard: `/verifier_dashboard.html`

## Qué hace cada frontend

### Issuer Dashboard

- Emite VC (`/api/credentials/issue_dni`)
- Revoca VC (`/api/credentials/revoke`)
- Muestra hash y tx hashes

### Verifier Dashboard

- Carga wallet local del titular
- Firma VP localmente
- Verifica VP (`/api/verify_presentation`)

## Recomendación de despliegue

1. `frontend_admin` en un dominio interno/restringido.
2. `verifier_dashboard` en dominio público de usuario final.
3. CORS limitado por origen y sin listado de archivos en frontend server.

## Comprobaciones rápidas

- Issuer health: `GET /health`
- Verifier health: `GET /health`
- Contrato activo: `python3 check_blockchain.py`
