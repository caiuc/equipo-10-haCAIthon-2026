"""Vocabulario canonico del sistema.

Los valores son los que viajan por la API y los que trae el CSV semilla, de modo
que un mismo string sirve para el filtro de la UI, la fila del CSV y el enum.
"""

from enum import Enum


class Regimen(str, Enum):
    """Regimen de atencion. Determina si existe garantia legal de oportunidad."""

    GES = "GES"
    NO_GES = "NO_GES"


class Stage(str, Enum):
    """Las cuatro etapas del continuo del paciente (documentation.MD 2.2)."""

    SOSPECHA = "SOSPECHA"
    DIAGNOSTICO = "DIAGNOSTICO"
    TRATAMIENTO = "TRATAMIENTO"
    SEGUIMIENTO = "SEGUIMIENTO"


class PatientType(str, Enum):
    """Ambulatorio u hospitalizado. El hospitalizado ocupa una cama de la red."""

    AMBULATORIO = "AMBULATORIO"
    HOSPITALARIO = "HOSPITALARIO"


class ClinicalSeverity(str, Enum):
    """Severidad clinica declarada por el derivador."""

    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class PriorityLevel(str, Enum):
    """Tramo de prioridad derivado del puntaje total."""

    CRITICA = "CRITICA"
    ALTA_PRIORIDAD = "ALTA_PRIORIDAD"
    MEDIA_PRIORIDAD = "MEDIA_PRIORIDAD"
    ESTANDAR = "ESTANDAR"


class CivilRegistryStatus(str, Enum):
    """Resultado del cruce con el Registro Civil."""

    ALIVE = "ALIVE"
    DECEASED = "DECEASED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class WaitlistOrder(str, Enum):
    """Criterios de ordenamiento expuestos en la lista de espera."""

    PRIORITY_DESC = "priority_desc"
    PRIORITY_ASC = "priority_asc"
    EXPIRATION_ASC = "expiration_asc"
    EXPIRATION_DESC = "expiration_desc"
    DAYS_DESC = "days_desc"
    DAYS_ASC = "days_asc"


class RegimenFilter(str, Enum):
    """Filtro de regimen: incluye ALL para no filtrar."""

    GES = "GES"
    NO_GES = "NO_GES"
    ALL = "ALL"


class PatientTypeFilter(str, Enum):
    """Filtro de tipo de paciente: incluye ALL para no filtrar."""

    AMBULATORIO = "AMBULATORIO"
    HOSPITALARIO = "HOSPITALARIO"
    ALL = "ALL"
