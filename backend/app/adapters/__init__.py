"""Registro de adaptadores de interoperabilidad.

Conectar un sistema nuevo es escribir una subclase de `PatientRecordAdapter` y
sumarla a `_ADAPTADORES`. Nada mas del backend cambia.
"""

from .base import ErrorDeAdaptacion, PatientRecordAdapter
from .csv_adapter import CsvAdapter
from .fhir import FhirAdapter
from .sidra import SidraAdapter
from .sigges import SiggesAdapter
from .sigte import SigteAdapter

_ADAPTADORES: dict[str, PatientRecordAdapter] = {
    adaptador.name: adaptador
    for adaptador in (
        SidraAdapter(),
        SiggesAdapter(),
        SigteAdapter(),
        FhirAdapter(),
        CsvAdapter(),
    )
}


class AdaptadorDesconocido(KeyError):
    """El nombre de adaptador solicitado no esta registrado."""


def get_adapter(name: str) -> PatientRecordAdapter:
    """Adaptador registrado con ese nombre. Levanta AdaptadorDesconocido."""
    adaptador = _ADAPTADORES.get(name.strip().lower())
    if adaptador is None:
        disponibles = ", ".join(sorted(_ADAPTADORES))
        raise AdaptadorDesconocido(
            f"No existe el adaptador {name!r}. Disponibles: {disponibles}."
        )
    return adaptador


def listar_adaptadores() -> list[PatientRecordAdapter]:
    """Todos los adaptadores registrados."""
    return list(_ADAPTADORES.values())


__all__ = [
    "AdaptadorDesconocido",
    "CsvAdapter",
    "ErrorDeAdaptacion",
    "FhirAdapter",
    "PatientRecordAdapter",
    "SidraAdapter",
    "SiggesAdapter",
    "SigteAdapter",
    "get_adapter",
    "listar_adaptadores",
]
