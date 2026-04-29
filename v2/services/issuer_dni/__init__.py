"""
issuer_dni: Issuer especializado para credenciales DNI español.

Extiende issuer_base con:
- Modelos ciudadanos DNI (numero_dni, fecha_nacimiento)
- Validadores DNI-específicos (formato, letra control, edad)
- Rutas Over18Credential
- Administración DNI

Arquitectura modular:
- issuer_base proporciona servicios compartidos
- issuer_dni importa y extiende con lógica DNI
"""

__version__ = "1.0.0"

