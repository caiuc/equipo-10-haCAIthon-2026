"""Endpoints de la lista de espera: ranking priorizado, exportacion y depuracion."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from .. import benchmarks, civil_registry
from ..enums import PatientTypeFilter, RegimenFilter, Stage, WaitlistOrder
from ..models import SyncCivilRegistryRequest, SyncCivilRegistryResponse, WaitlistResponse
from ..store import paginar, store

router = APIRouter(prefix="/waitlist", tags=["Lista de espera"])


@router.get(
    "",
    response_model=WaitlistResponse,
    summary="Lista de espera priorizada",
)
def obtener_lista(
    health_service: str | None = Query(default=None, description="Codigo del Servicio de Salud."),
    specialty: str | None = Query(default=None, description="Codigo de especialidad."),
    regimen: RegimenFilter = Query(default=RegimenFilter.ALL),
    stage: Stage | None = Query(default=None),
    patient_type: PatientTypeFilter = Query(default=PatientTypeFilter.ALL),
    oncologic_only: bool = Query(default=False, description="Solo pacientes oncologicos."),
    q: str | None = Query(default=None, description="Busca por RUT o por nombre."),
    order: WaitlistOrder = Query(default=WaitlistOrder.PRIORITY_DESC),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> WaitlistResponse:
    """Ranking paginado (documentation.MD 4.2, endpoint 2).

    Los pacientes egresados por fallecimiento no aparecen: ya salieron de la
    lista activa.
    """
    resultados = store.query(
        health_service=health_service,
        specialty=specialty,
        regimen=regimen,
        stage=stage,
        patient_type=patient_type,
        search=q,
        only_oncologic=oncologic_only,
        order=order,
    )
    filas, total, total_paginas = paginar(resultados, page, limit)

    return WaitlistResponse(
        total_records=total,
        page=min(max(1, page), total_paginas),
        limit=limit,
        total_pages=total_paginas,
        data=filas,
    )


@router.get(
    "/export",
    summary="Exportar la lista priorizada como CSV",
    response_class=StreamingResponse,
)
def exportar_csv(
    health_service: str | None = Query(default=None),
    specialty: str | None = Query(default=None),
    regimen: RegimenFilter = Query(default=RegimenFilter.ALL),
    stage: Stage | None = Query(default=None),
    patient_type: PatientTypeFilter = Query(default=PatientTypeFilter.ALL),
    oncologic_only: bool = Query(default=False),
    q: str | None = Query(default=None),
    order: WaitlistOrder = Query(default=WaitlistOrder.PRIORITY_DESC),
) -> StreamingResponse:
    """Descarga la lista completa con los filtros aplicados, sin paginar.

    Es el archivo que el coordinador lleva a la reunion de red, asi que incluye
    el desglose del puntaje: cada fila tiene que poder defenderse sola.
    """
    resultados = store.query(
        health_service=health_service,
        specialty=specialty,
        regimen=regimen,
        stage=stage,
        patient_type=patient_type,
        search=q,
        only_oncologic=oncologic_only,
        order=order,
    )

    buffer = io.StringIO()
    escritor = csv.writer(buffer, lineterminator="\n")
    escritor.writerow(
        [
            "prioridad",
            "rut",
            "nombre_completo",
            "regimen",
            "fecha_expiracion_ges",
            "tipo_paciente",
            "especialidad",
            "etapa",
            "servicio_salud",
            "dias_espera",
            "mediana_referencia",
            "p75_referencia",
            "puntaje",
            "nivel_prioridad",
            "oncologico",
            "paciente_antiguo",
            "info_incompleta",
            "ges_retrasado",
        ]
    )

    for rank, (paciente, resultado) in enumerate(resultados, start=1):
        escritor.writerow(
            [
                rank,
                paciente.rut,
                paciente.nombre_completo,
                paciente.regimen.value,
                paciente.fecha_expiracion_ges.isoformat() if paciente.fecha_expiracion_ges else "",
                paciente.tipo_paciente.value,
                benchmarks.label_especialidad(paciente.especialidad),
                paciente.stage.value,
                paciente.health_service_id,
                resultado.days_waiting,
                resultado.median_days,
                resultado.p75_days,
                f"{resultado.total:.2f}",
                resultado.level.value,
                "SI" if resultado.flags.is_oncologic else "NO",
                "SI" if resultado.flags.is_ancient_patient else "NO",
                "SI" if resultado.flags.incomplete_info else "NO",
                "SI" if resultado.flags.ges_delayed else "NO",
            ]
        )

    buffer.seek(0)
    nombre = f"lista-espera-priorizada-{date.today().isoformat()}.csv"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.post(
    "/sync-civil-registry",
    response_model=SyncCivilRegistryResponse,
    summary="Depurar la lista contra el Registro Civil",
)
def sincronizar_registro_civil(
    peticion: SyncCivilRegistryRequest | None = None,
) -> SyncCivilRegistryResponse:
    """Cruza un lote de la lista con el Registro Civil (documentation.MD 4.2, endpoint 3).

    Los fallecidos confirmados egresan administrativamente: dejan de contar como
    demanda y liberan el cupo que estaban ocupando en las estadisticas.
    """
    return civil_registry.sincronizar(store, peticion or SyncCivilRegistryRequest())


@router.get("/last-sync", summary="Marca de tiempo del proceso", include_in_schema=False)
def marca_de_tiempo() -> dict[str, datetime]:
    """Utilitario para que la UI pueda mostrar cuando se consulto por ultima vez."""
    return {"server_time": datetime.now()}
