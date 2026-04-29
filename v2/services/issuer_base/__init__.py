"""
issuer_base: Librería genérica reutilizable para cualquier tipo de credencial.

Proporciona:
- Modelos base abstractos (CitizenBase)
- Servicios compartidos (Blockchain, Auth, Database)
- Rutas genéricas (health, admin CRUD, credentials issue/revoke)
- Aplicación FastAPI base extensible

Los issuers específicos (ej. issuer_dni) importan esta librería y extienden con
lógica especializada (validadores DNI, esquemas específicos, etc).
"""

__version__ = "1.0.0"
