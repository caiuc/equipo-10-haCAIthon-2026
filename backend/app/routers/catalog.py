"""Catalogos para los desplegables de la UI e indicadores de cabecera."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from fastapi import APIRouter

from .. import benchmarks
from ..enums import (
    ClinicalSeverity,
    PatientType,
    Regimen,
    Stage,
    WaitlistOrder,
)
from ..models import (
    CatalogEntry,
    CatalogResponse,
    SpecialtyCatalogEntry,
    SpecialtyStat,
    StatsResponse,
)
from ..store import store

router = APIRouter(tags=["Catalogos e indicadores"])

_ETIQUETAS_ETAPA = {
    Stage.SOSPECHA: "Sospecha",
    Stage.DIAGNOSTICO: "Diagnostico",
    Stage.TRATAMIENTO: "Tratamiento",
    Stage.SEGUIMIENTO: "Seguimiento",
}

_ETIQUETAS_ORDEN = {
    WaitlistOrder.PRIORITY_DESC: "Puntaje: mayor a menor",
    WaitlistOrder.PRIORITY_ASC: "Puntaje: menor a mayor",
    WaitlistOrder.EXPIRATION_ASC: "Expiracion: mas proxima primero",
    WaitlistOrder.EXPIRATION_DESC: "Expiracion: mas lejana primero",
    WaitlistOrder.DAYS_DESC: "Dias de espera: mayor a menor",
    WaitlistOrder.DAYS_ASC: "Dias de espera: menor a mayor",
}


@router.get("/catalog", response_model=CatalogResponse, summary="Catalogos de la interfaz")
def obtener_catalogos() -> CatalogResponse:
    """Opciones de filtros y formularios.

    Las especialidades salen del catalogo completo, no de los pacientes
    cargados: un filtro que aparece y desaparece segun quien este en lista es
    imposible de usar.
    """
    especialidades = sorted(
        (
            SpecialtyCatalogEntry(
                value=esp.codigo,
                label=esp.label,
                median_days=esp.mediana_dias,
                p75_days=esp.p75_dias,
                is_oncologic=esp.es_oncologica,
            )
            for esp in benchmarks.ESPECIALIDADES.values()
        ),
        key=lambda e: e.label,
    )

    servicios = sorted(
        (
            CatalogEntry(value=servicio.codigo, label=servicio.label)
            for servicio in benchmarks.SERVICIOS_DE_SALUD.values()
        ),
        key=lambda e: e.label,
    )

    return CatalogResponse(
        specialties=especialidades,
        health_services=servicios,
        stages=[CatalogEntry(value=e.value, label=_ETIQUETAS_ETAPA[e]) for e in Stage],
        patient_types=[
            CatalogEntry(value=PatientType.AMBULATORIO.value, label="Ambulatorio"),
            CatalogEntry(value=PatientType.HOSPITALARIO.value, label="Hospitalizado"),
        ],
        severities=[
            CatalogEntry(value=ClinicalSeverity.ALTA.value, label="Alta"),
            CatalogEntry(value=ClinicalSeverity.MEDIA.value, label="Media"),
            CatalogEntry(value=ClinicalSeverity.BAJA.value, label="Baja"),
        ],
        regimens=[
            CatalogEntry(value=Regimen.GES.value, label="GES"),
            CatalogEntry(value=Regimen.NO_GES.value, label="No GES"),
        ],
        orders=[CatalogEntry(value=o.value, label=_ETIQUETAS_ORDEN[o]) for o in WaitlistOrder],
    )


@router.get("/stats", response_model=StatsResponse, summary="Indicadores de la lista de espera")
def obtener_indicadores(health_service: str | None = None) -> StatsResponse:
    """Cifras de cabecera del tablero, calculadas sobre la lista activa."""
    resultados = store.scored()
    if health_service:
        objetivo = health_service.strip().upper()
        resultados = [r for r in resultados if r[0].health_service_id == objetivo]

    if not resultados:
        return StatsResponse(
            total_waiting=0,
            oncologic=0,
            ges_total=0,
            ges_delayed=0,
            ancient_patients=0,
            incomplete_info=0,
            pending_civil_registry=0,
            median_days_waiting=0,
            p75_days_waiting=0,
            average_score=0.0,
            top_specialties=[],
        )

    dias = sorted(r[1].days_waiting for r in resultados)
    indice_p75 = min(len(dias) - 1, int(round(0.75 * (len(dias) - 1))))

    por_especialidad: dict[str, list[int]] = defaultdict(list)
    for paciente, resultado in resultados:
        por_especialidad[paciente.especialidad].append(resultado.days_waiting)

    conteo = Counter({codigo: len(v) for codigo, v in por_especialidad.items()})
    top = [
        SpecialtyStat(
            specialty=codigo,
            label=benchmarks.label_especialidad(codigo),
            patients=cantidad,
            median_days_waiting=int(statistics.median(por_especialidad[codigo])),
        )
        for codigo, cantidad in conteo.most_common(5)
    ]

    return StatsResponse(
        total_waiting=len(resultados),
        oncologic=sum(1 for _, r in resultados if r.flags.is_oncologic),
        ges_total=sum(1 for p, _ in resultados if p.regimen is Regimen.GES),
        ges_delayed=sum(1 for _, r in resultados if r.flags.ges_delayed),
        ancient_patients=sum(1 for _, r in resultados if r.flags.is_ancient_patient),
        incomplete_info=sum(1 for _, r in resultados if r.flags.incomplete_info),
        pending_civil_registry=sum(
            1 for _, r in resultados if r.flags.civil_registry_status.value == "PENDING_VERIFICATION"
        ),
        median_days_waiting=int(statistics.median(dias)),
        p75_days_waiting=dias[indice_p75],
        average_score=round(statistics.fmean(r.total for _, r in resultados), 2),
        top_specialties=top,
    )
