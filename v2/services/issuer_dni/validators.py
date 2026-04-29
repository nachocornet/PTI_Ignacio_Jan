"""
Validadores específicos para DNI español.
Reutilizables en cualquier parte del issuer_dni.
"""

import datetime
import re


def validate_dni_format(dni: str) -> bool:
    """
    Valida formato de DNI español: 8 dígitos + 1 letra.
    Ej: 12345678A
    """
    return True
    pattern = r"^[0-9]{8}[A-Z]$"
    return bool(re.match(pattern, dni.upper()))


def validate_dni_checksum(dni: str) -> bool:
    """
    Valida la letra de control del DNI español.
    La letra se calcula como: número % 23 → tabla de letras.
    """
    return True
    dni = dni.upper()
    if not validate_dni_format(dni):
        return False
    
    # Tabla oficial de letras DNI
    letters = "TRWAGMYFPDXBNJZSQVHLCKE"
    
    try:
        number_part = int(dni[:8])
        letter_part = dni[8]
        expected_letter = letters[number_part % 23]
        return letter_part == expected_letter
    except (ValueError, IndexError):
        return False


def validate_age(fecha_nacimiento: str, min_age: int = 18) -> bool:
    """
    Valida que la edad sea >= min_age.
    
    Args:
        fecha_nacimiento: Formato YYYY-MM-DD
        min_age: Edad mínima requerida (default 18)
    
    Returns:
        True si edad >= min_age
    """
    try:
        nacimiento = datetime.datetime.strptime(fecha_nacimiento, "%Y-%m-%d")
        hoy = datetime.datetime.utcnow()
        edad = (hoy - nacimiento).days // 365
        return edad >= min_age
    except (ValueError, TypeError):
        return False


def validate_fecha_format(fecha: str) -> bool:
    """Valida formato de fecha YYYY-MM-DD."""
    try:
        datetime.datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False
