"""Contrato de la capa de adaptadores (documentation.MD 4.1).

No se puede imponer una base de datos unica a los 29 Servicios de Salud: cada
uno arrastra su propio HIS, y sobre ellos conviven SIDRA, SIGGES y SIGTE con
esquemas distintos para el mismo paciente. En vez de pedirles que cambien, la
API define una entidad canonica y un adaptador por sistema de origen.

Agregar un sistema nuevo es escribir una subclase de `PatientRecordAdapter` y
registrarla. El motor de puntaje no se entera.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from ..models import PatientRecord


class ErrorDeAdaptacion(ValueError):
    """El payload de origen no trae lo necesario para construir la entidad canonica."""


class PatientRecordAdapter(ABC):
    """Traduce el registro de un sistema de origen a la entidad canonica."""

    name: str
    label: str
    description: str

    @abstractmethod
    def to_canonical(self, raw: dict[str, Any]) -> PatientRecord:
        """Convierte un registro crudo del sistema de origen en un PatientRecord."""

    @abstractmethod
    def sample_payload(self) -> dict[str, Any]:
        """Ejemplo del formato que espera este adaptador, para documentar y probar."""

    def to_canonical_many(self, raws: list[dict[str, Any]]) -> list[PatientRecord]:
        """Traduce un lote completo."""
        return [self.to_canonical(raw) for raw in raws]


# --------------------------------------------------------------------------
# Utilidades de coercion compartidas por los adaptadores
# --------------------------------------------------------------------------
_VERDADEROS = {"1", "true", "t", "si", "sí", "s", "yes", "y", "verdadero"}
_FALSOS = {"0", "false", "f", "no", "n", "falso", ""}


def a_bool(valor: Any, por_defecto: bool = False) -> bool:
    """Interpreta los muchos dialectos de booleano que llegan desde los HIS."""
    if valor is None:
        return por_defecto
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)

    texto = str(valor).strip().lower()
    if texto in _VERDADEROS:
        return True
    if texto in _FALSOS:
        return False
    return por_defecto


def a_fecha(valor: Any) -> date | None:
    """Acepta ISO, dd-mm-aaaa y dd/mm/aaaa. Devuelve None si viene vacio."""
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()
    if not texto:
        return None

    # Un timestamp ISO completo tambien es aceptable: se toma la fecha.
    if "T" in texto:
        texto = texto.split("T", 1)[0]

    for separador in ("-", "/"):
        if separador in texto:
            partes = texto.split(separador)
            if len(partes) != 3:
                continue
            try:
                if len(partes[0]) == 4:
                    anio, mes, dia = (int(p) for p in partes)
                else:
                    dia, mes, anio = (int(p) for p in partes)
                return date(anio, mes, dia)
            except ValueError:
                continue

    raise ErrorDeAdaptacion(f"No se pudo interpretar la fecha {valor!r}.")


def a_texto(valor: Any) -> str | None:
    """Normaliza a texto, devolviendo None cuando el campo viene vacio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def requerido(raw: dict[str, Any], *claves: str) -> Any:
    """Primer valor no vacio entre varias claves posibles del sistema de origen."""
    for clave in claves:
        valor = raw.get(clave)
        if valor is not None and str(valor).strip():
            return valor
    raise ErrorDeAdaptacion(
        f"Falta un campo obligatorio. Se esperaba alguno de: {', '.join(claves)}."
    )


def opcional(raw: dict[str, Any], *claves: str) -> Any:
    """Primer valor no vacio entre varias claves, o None si ninguna viene."""
    for clave in claves:
        valor = raw.get(clave)
        if valor is not None and str(valor).strip():
            return valor
    return None
