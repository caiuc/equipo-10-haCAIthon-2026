"""Endpoints de la capa de interoperabilidad.

Permiten ver que adaptadores estan registrados y probar en vivo la traduccion de
un payload crudo de cualquiera de los sistemas de origen a la entidad canonica.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, status

from .. import scoring
from ..adapters import AdaptadorDesconocido, get_adapter, listar_adaptadores
from ..adapters.base import ErrorDeAdaptacion
from ..models import AdapterInfo, AdapterIngestResponse
from ..store import store

router = APIRouter(prefix="/adapters", tags=["Interoperabilidad"])


@router.get("", response_model=list[AdapterInfo], summary="Adaptadores registrados")
def listar() -> list[AdapterInfo]:
    """Sistemas de origen que la API sabe traducir hoy."""
    return [
        AdapterInfo(
            name=adaptador.name,
            label=adaptador.label,
            description=adaptador.description,
            sample_payload=adaptador.sample_payload(),
        )
        for adaptador in listar_adaptadores()
    ]


@router.post(
    "/{adapter_name}/ingest",
    response_model=AdapterIngestResponse,
    summary="Normalizar un registro crudo y puntuarlo",
)
def ingerir(
    adapter_name: str,
    raw: dict[str, Any] = Body(..., description="Registro en el formato del sistema de origen."),
    persist: bool = Query(
        default=False, description="Si es true, incorpora el paciente a la lista de espera."
    ),
) -> AdapterIngestResponse:
    """Traduce un payload de SIDRA, SIGGES, SIGTE, FHIR o CSV y devuelve su puntaje.

    Es el punto de entrada real de un Servicio de Salud que quiera conectarse:
    manda sus registros en su propio formato y recibe la priorizacion de vuelta.
    """
    try:
        adaptador = get_adapter(adapter_name)
    except AdaptadorDesconocido as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        paciente = adaptador.to_canonical(raw)
    except (ErrorDeAdaptacion, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if persist:
        store.upsert(paciente)

    resultado = scoring.calcular(paciente)
    return AdapterIngestResponse(
        adapter=adaptador.name,
        canonical=paciente.model_dump(mode="json"),
        score=scoring.a_respuesta(paciente, resultado),
        persisted=persist,
    )
