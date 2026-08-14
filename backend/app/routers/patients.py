"""Endpoints de paciente individual: puntaje, ficha, alta y actualizacion de estado."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from .. import benchmarks, scoring
from ..adapters import AdaptadorDesconocido, get_adapter
from ..models import (
    ClinicalStatusUpdate,
    PatientCreate,
    PatientDetail,
    PatientRecord,
    PatientScoreResponse,
)
from ..rut import RutInvalido, desde_patient_id, formatear
from ..store import PacienteDuplicado, PacienteNoEncontrado, store

router = APIRouter(prefix="/patients", tags=["Pacientes"])


def _resolver(patient_id: str) -> PatientRecord:
    """Busca el paciente aceptando 'CL-18492041-K', '18.492.041-K' o '18492041K'."""
    try:
        rut = desde_patient_id(patient_id)
    except RutInvalido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        return store.get(rut)
    except PacienteNoEncontrado as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"No hay ningun paciente con RUT {formatear(rut)} en la lista de espera.",
        ) from exc


def _edad(nacimiento: date | None, hoy: date) -> int | None:
    if nacimiento is None:
        return None
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def _detalle(paciente: PatientRecord) -> PatientDetail:
    hoy = date.today()
    resultado = scoring.calcular(paciente, hoy)

    return PatientDetail(
        patient_id=paciente.patient_id,
        national_id=paciente.rut,
        national_id_formatted=formatear(paciente.rut),
        full_name=paciente.nombre_completo,
        birth_date=paciente.fecha_nacimiento,
        age=_edad(paciente.fecha_nacimiento, hoy),
        regimen=paciente.regimen,
        ges_expiration_date=paciente.fecha_expiracion_ges,
        patient_type=paciente.tipo_paciente,
        specialty=paciente.especialidad,
        specialty_label=benchmarks.label_especialidad(paciente.especialidad),
        stage=paciente.stage,
        health_service_id=paciente.health_service_id,
        health_service_label=benchmarks.label_servicio(paciente.health_service_id),
        diagnosis=paciente.diagnostico,
        entry_date=paciente.fecha_ingreso_lista,
        days_waiting=resultado.days_waiting,
        last_exams_date=paciente.fecha_ultimos_examenes,
        is_oncologic=paciente.es_oncologico,
        clinical_severity=paciente.severidad_clinica,
        staging=paciente.estadificacion,
        contact_phone=paciente.telefono_contacto,
        civil_registry_status=paciente.estado_registro_civil,
        date_of_death=paciente.fecha_defuncion,
        source_adapter=paciente.origen,
        score=scoring.a_respuesta(paciente, resultado),
    )


@router.get(
    "/{patient_id}/score",
    response_model=PatientScoreResponse,
    response_model_exclude_none=True,
    summary="Puntaje individual y desglose parametrico",
)
def obtener_puntaje(
    patient_id: str,
    breakdown: bool = Query(
        default=False, description="Incluye el desglose ponderado de los cuatro componentes."
    ),
    adapter: str | None = Query(
        default=None,
        description="Adaptador de origen a declarar. Solo se valida que exista.",
    ),
) -> PatientScoreResponse:
    """Puntaje de priorizacion de un paciente (documentation.MD 4.2, endpoint 1)."""
    if adapter is not None:
        try:
            get_adapter(adapter)
        except AdaptadorDesconocido as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    paciente = _resolver(patient_id)
    resultado = scoring.calcular(paciente)
    return scoring.a_respuesta(paciente, resultado, incluir_desglose=breakdown)


@router.get(
    "/{patient_id}",
    response_model=PatientDetail,
    summary="Ficha completa del paciente",
)
def obtener_paciente(patient_id: str) -> PatientDetail:
    """Ficha que se muestra al buscar por RUT en 'Ingreso de paciente'."""
    return _detalle(_resolver(patient_id))


@router.post(
    "",
    response_model=PatientDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Ingresar un paciente nuevo a la lista de espera",
)
def crear_paciente(datos: PatientCreate) -> PatientDetail:
    """Da de alta un paciente que todavia no figura en la lista."""
    try:
        paciente = PatientRecord(
            rut=datos.rut,
            nombre_completo=datos.nombre_completo,
            fecha_nacimiento=datos.fecha_nacimiento,
            regimen=datos.regimen,
            # Una fecha de expiracion en un paciente No GES seria una garantia
            # inexistente: la UI la mostraria como plazo legal.
            fecha_expiracion_ges=(
                datos.fecha_expiracion_ges if datos.regimen.value == "GES" else None
            ),
            tipo_paciente=datos.tipo_paciente,
            especialidad=datos.especialidad,
            stage=datos.stage,
            health_service_id=datos.health_service_id,
            diagnostico=datos.diagnostico,
            fecha_ingreso_lista=datos.fecha_ingreso_lista or date.today(),
            fecha_ultimos_examenes=datos.fecha_ultimos_examenes,
            es_oncologico=datos.es_oncologico,
            severidad_clinica=datos.severidad_clinica,
            estadificacion=datos.estadificacion,
            telefono_contacto=datos.telefono_contacto,
            origen="api",
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        store.add(paciente)
    except PacienteDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _detalle(paciente)


@router.put(
    "/{patient_id}/clinical-status",
    response_model=PatientDetail,
    summary="Actualizar el estado clinico y recalcular el puntaje",
)
def actualizar_estado(patient_id: str, cambios: ClinicalStatusUpdate) -> PatientDetail:
    """Aplica los cambios enviados desde 'Actualizar Estado' y recalcula el puntaje.

    Solo se tocan los campos presentes en el cuerpo: la UI envia lo que el
    administrativo edito, no la ficha completa.
    """
    paciente = _resolver(patient_id)
    actualizados = cambios.model_dump(exclude_unset=True)

    try:
        for campo, valor in actualizados.items():
            setattr(paciente, campo, valor)

        # Si el paciente paso a No GES, su plazo legal deja de existir.
        if paciente.regimen.value == "NO_GES":
            paciente.fecha_expiracion_ges = None
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    store.upsert(paciente)
    return _detalle(paciente)
