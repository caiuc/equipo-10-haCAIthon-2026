"""Entidad canonica del paciente y esquemas de entrada/salida de la API.

`PatientRecord` es el formato unico al que todos los adaptadores traducen
(SIDRA, SIGGES, SIGTE, HIS/FHIR). El resto del sistema no sabe de que sistema de
origen vino un registro.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import (
    CivilRegistryStatus,
    ClinicalSeverity,
    PatientType,
    PriorityLevel,
    Regimen,
    Stage,
)
from .rut import RutInvalido, a_patient_id, normalizar


# --------------------------------------------------------------------------
# Entidad canonica
# --------------------------------------------------------------------------
class PatientRecord(BaseModel):
    """Un paciente en lista de espera, ya normalizado desde su sistema de origen."""

    model_config = ConfigDict(validate_assignment=True)

    rut: str = Field(description="RUT normalizado, formato 18492041-K")
    nombre_completo: str
    fecha_nacimiento: date | None = None

    regimen: Regimen
    fecha_expiracion_ges: date | None = Field(
        default=None,
        description="Plazo legal de la garantia. Solo existe en regimen GES.",
    )
    tipo_paciente: PatientType
    especialidad: str
    stage: Stage
    health_service_id: str
    diagnostico: str = ""

    fecha_ingreso_lista: date
    fecha_ultimos_examenes: date | None = None

    es_oncologico: bool = False
    severidad_clinica: ClinicalSeverity = ClinicalSeverity.MEDIA
    estadificacion: str | None = Field(
        default=None, description="Etapificacion TNM u otra. Critica en casos oncologicos."
    )
    telefono_contacto: str | None = None

    estado_registro_civil: CivilRegistryStatus = CivilRegistryStatus.ALIVE
    fecha_defuncion: date | None = None

    origen: str = Field(default="csv", description="Adaptador por el que entro el registro.")

    @field_validator("rut")
    @classmethod
    def _normalizar_rut(cls, valor: str) -> str:
        try:
            return normalizar(valor)
        except RutInvalido as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("especialidad", "health_service_id")
    @classmethod
    def _normalizar_codigo(cls, valor: str) -> str:
        return valor.strip().upper().replace(" ", "_")

    @property
    def patient_id(self) -> str:
        """Identificador publico del paciente: 'CL-18492041-K'."""
        return a_patient_id(self.rut)

    def dias_esperando(self, referencia: date | None = None) -> int:
        """Dias transcurridos desde el ingreso a la lista. Nunca negativo."""
        hoy = referencia or date.today()
        return max(0, (hoy - self.fecha_ingreso_lista).days)


# --------------------------------------------------------------------------
# Endpoint 1: puntaje individual (documentation.MD 4.2)
# --------------------------------------------------------------------------
class PatientFlags(BaseModel):
    """Los indicadores visuales de documentation.MD 6.1, en forma de datos."""

    is_oncologic: bool
    is_ancient_patient: bool
    incomplete_info: bool
    ges_delayed: bool
    civil_registry_status: CivilRegistryStatus


class ScoreBreakdown(BaseModel):
    """Aporte ya ponderado de cada componente. Los cuatro suman el total."""

    time_waiting_score: float
    clinical_severity_score: float
    oncologic_risk_score: float
    diagnostic_validity_penalty: float


class ScoreMetadata(BaseModel):
    """Contexto que explica de donde salio el puntaje."""

    days_waiting: int
    regional_median_days: float
    regional_p75_days: float
    exams_expired: bool
    last_evaluation_date: datetime | None = None
    calculated_at: datetime


class PatientScoreResponse(BaseModel):
    """Respuesta de GET /patients/{patient_id}/score."""

    patient_id: str
    national_id: str
    regimen: Regimen
    stage: Stage
    specialty: str
    health_service_id: str
    total_score: float
    priority_level: PriorityLevel
    flags: PatientFlags
    breakdown: ScoreBreakdown | None = None
    metadata: ScoreMetadata


# --------------------------------------------------------------------------
# Endpoint 2: lista de espera priorizada
# --------------------------------------------------------------------------
class WaitlistItem(BaseModel):
    """Una fila del ranking. Incluye todo lo que la UI muestra sin pedir mas datos."""

    rank: int
    patient_id: str
    national_id: str
    full_name: str
    specialty: str
    specialty_label: str
    stage: Stage
    regimen: Regimen
    patient_type: PatientType
    health_service_id: str
    health_service_label: str
    ges_expiration_date: date | None
    days_waiting: int
    regional_median_days: float
    regional_p75_days: float
    priority_score: float
    priority_level: PriorityLevel
    flags: PatientFlags


class WaitlistResponse(BaseModel):
    """Respuesta paginada de GET /waitlist."""

    total_records: int
    page: int
    limit: int
    total_pages: int
    data: list[WaitlistItem]


# --------------------------------------------------------------------------
# Endpoint 3: depuracion con Registro Civil
# --------------------------------------------------------------------------
class SyncCivilRegistryRequest(BaseModel):
    """Cuerpo de POST /waitlist/sync-civil-registry."""

    batch_size: int = Field(default=500, ge=1, le=5000)
    auto_purge_deceased: bool = True
    health_service_id: str | None = None


class PurgedPatient(BaseModel):
    """Paciente retirado de la lista tras confirmar el deceso."""

    patient_id: str
    full_name: str
    date_of_death: date | None
    purged_reason: str = "EGRESO_ADMINISTRATIVO_FALLECIMIENTO"


class SyncCivilRegistryResponse(BaseModel):
    """Resultado del cruce con el Registro Civil."""

    processed_records: int
    alive_records: int
    purged_deceased_records: int
    purged_patients: list[PurgedPatient]
    synced_at: datetime


# --------------------------------------------------------------------------
# Ficha del paciente y escritura
# --------------------------------------------------------------------------
class PatientDetail(BaseModel):
    """Ficha completa que ve el administrativo en 'Ingreso de paciente'."""

    patient_id: str
    national_id: str
    national_id_formatted: str
    full_name: str
    birth_date: date | None
    age: int | None
    regimen: Regimen
    ges_expiration_date: date | None
    patient_type: PatientType
    specialty: str
    specialty_label: str
    stage: Stage
    health_service_id: str
    health_service_label: str
    diagnosis: str
    entry_date: date
    days_waiting: int
    last_exams_date: date | None
    is_oncologic: bool
    clinical_severity: ClinicalSeverity
    staging: str | None
    contact_phone: str | None
    civil_registry_status: CivilRegistryStatus
    date_of_death: date | None
    source_adapter: str
    score: PatientScoreResponse


class PatientCreate(BaseModel):
    """Alta de un paciente que todavia no esta en la lista."""

    rut: str
    nombre_completo: str
    regimen: Regimen
    especialidad: str
    stage: Stage
    health_service_id: str
    tipo_paciente: PatientType = PatientType.AMBULATORIO
    fecha_ingreso_lista: date | None = None
    fecha_expiracion_ges: date | None = None
    fecha_nacimiento: date | None = None
    fecha_ultimos_examenes: date | None = None
    diagnostico: str = ""
    es_oncologico: bool = False
    severidad_clinica: ClinicalSeverity = ClinicalSeverity.MEDIA
    estadificacion: str | None = None
    telefono_contacto: str | None = None


class ClinicalStatusUpdate(BaseModel):
    """Campos editables desde 'Actualizar Estado'.

    Todos son opcionales: la UI envia solo lo que el administrativo cambio, y
    el puntaje se recalcula con el resultado.
    """

    regimen: Regimen | None = None
    fecha_expiracion_ges: date | None = None
    tipo_paciente: PatientType | None = None
    especialidad: str | None = None
    stage: Stage | None = None
    health_service_id: str | None = None
    diagnostico: str | None = None
    fecha_ultimos_examenes: date | None = None
    es_oncologico: bool | None = None
    severidad_clinica: ClinicalSeverity | None = None
    estadificacion: str | None = None
    telefono_contacto: str | None = None
    estado_registro_civil: CivilRegistryStatus | None = None


# --------------------------------------------------------------------------
# Catalogos, metricas y adaptadores
# --------------------------------------------------------------------------
class CatalogEntry(BaseModel):
    """Una opcion de un desplegable de la UI."""

    value: str
    label: str


class SpecialtyCatalogEntry(CatalogEntry):
    """Especialidad con sus referencias de espera, para dibujar la regla."""

    median_days: int
    p75_days: int
    is_oncologic: bool


class CatalogResponse(BaseModel):
    """Todo lo que la UI necesita para poblar filtros y formularios."""

    specialties: list[SpecialtyCatalogEntry]
    health_services: list[CatalogEntry]
    stages: list[CatalogEntry]
    patient_types: list[CatalogEntry]
    severities: list[CatalogEntry]
    regimens: list[CatalogEntry]
    orders: list[CatalogEntry]


class SpecialtyStat(BaseModel):
    """Carga de una especialidad dentro del universo filtrado."""

    specialty: str
    label: str
    patients: int
    median_days_waiting: int


class StatsResponse(BaseModel):
    """Indicadores de cabecera del tablero."""

    total_waiting: int
    oncologic: int
    ges_total: int
    ges_delayed: int
    ancient_patients: int
    incomplete_info: int
    pending_civil_registry: int
    median_days_waiting: int
    p75_days_waiting: int
    average_score: float
    top_specialties: list[SpecialtyStat]


class AdapterInfo(BaseModel):
    """Un adaptador registrado en la capa de interoperabilidad."""

    name: str
    label: str
    description: str
    sample_payload: dict[str, Any]


class AdapterIngestResponse(BaseModel):
    """Resultado de normalizar un payload crudo a la entidad canonica."""

    adapter: str
    canonical: dict[str, Any]
    score: PatientScoreResponse
    persisted: bool
