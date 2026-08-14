"""RUT chileno: normalizacion, digito verificador (modulo 11) y formato.

El RUT es la llave del paciente en toda la red publica, asi que la API lo acepta
en cualquiera de las formas en que llega desde los sistemas de origen
("18.492.041-K", "18492041k", "184920 41-K") y lo guarda siempre normalizado.
"""

import re

_LIMPIEZA = re.compile(r"[^0-9kK]")


class RutInvalido(ValueError):
    """El RUT no tiene forma valida o su digito verificador no cuadra."""


def calcular_digito_verificador(numero: int) -> str:
    """Digito verificador por modulo 11, con la serie de multiplicadores 2..7."""
    suma = 0
    multiplicador = 2
    for digito in reversed(str(numero)):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def normalizar(rut: str) -> str:
    """Devuelve el RUT como '18492041-K': sin puntos, con guion, DV en mayuscula.

    Levanta RutInvalido si el largo no calza o si el digito verificador no
    corresponde al cuerpo.
    """
    if not rut:
        raise RutInvalido("El RUT viene vacio.")

    limpio = _LIMPIEZA.sub("", rut).upper()
    if len(limpio) < 2:
        raise RutInvalido(f"RUT demasiado corto: {rut!r}")

    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit():
        raise RutInvalido(f"El cuerpo del RUT no es numerico: {rut!r}")
    if not 6 <= len(cuerpo) <= 8:
        raise RutInvalido(f"El cuerpo del RUT debe tener entre 6 y 8 digitos: {rut!r}")

    esperado = calcular_digito_verificador(int(cuerpo))
    if dv != esperado:
        raise RutInvalido(
            f"Digito verificador incorrecto para {rut!r}: se esperaba {esperado}."
        )

    return f"{int(cuerpo)}-{dv}"


def es_valido(rut: str) -> bool:
    """True si el RUT pasa la validacion de modulo 11."""
    try:
        normalizar(rut)
    except RutInvalido:
        return False
    return True


def formatear(rut: str) -> str:
    """Formato de presentacion con puntos: '18.492.041-K'."""
    normalizado = normalizar(rut)
    cuerpo, dv = normalizado.split("-")
    with_dots = f"{int(cuerpo):,}".replace(",", ".")
    return f"{with_dots}-{dv}"


def a_patient_id(rut: str) -> str:
    """Identificador interno usado por la API: 'CL-18492041-K'."""
    return f"CL-{normalizar(rut)}"


def desde_patient_id(patient_id: str) -> str:
    """Acepta tanto 'CL-18492041-K' como '18.492.041-K' y devuelve el RUT normalizado."""
    candidato = patient_id[3:] if patient_id.upper().startswith("CL-") else patient_id
    return normalizar(candidato)
