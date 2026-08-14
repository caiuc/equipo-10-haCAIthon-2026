"""Cruce con el Registro Civil e Identificacion.

Segun el informe BCN citado en documentation.MD 3, una de las tres vias de
egreso de la lista de espera es el fallecimiento del usuario. Los registros que
no se depuran abultan la demanda declarada y desvian recursos hacia pacientes
que ya no estan.

Este modulo simula ese cruce. El unico punto que habria que reemplazar por la
integracion real es `consultar_defuncion`: el resto del flujo (lotes, purga
condicional, reporte de egresos) ya es el definitivo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from .enums import CivilRegistryStatus
from .models import (
    PatientRecord,
    PurgedPatient,
    SyncCivilRegistryRequest,
    SyncCivilRegistryResponse,
)
from .store import InMemoryStore


@dataclass(frozen=True)
class RespuestaRegistroCivil:
    """Lo que devuelve el servicio para un RUT consultado."""

    rut: str
    fallecido: bool
    fecha_defuncion: date | None


def consultar_defuncion(paciente: PatientRecord) -> RespuestaRegistroCivil:
    """Consulta simulada al Registro Civil por un RUT.

    En la semilla, un paciente marcado para verificacion que trae fecha de
    defuncion se confirma como fallecido; el que no la trae vuelve como vivo.
    Asi el resultado de la demostracion es reproducible y lo controla el CSV,
    no el azar.
    """
    fallecido = paciente.fecha_defuncion is not None
    return RespuestaRegistroCivil(
        rut=paciente.rut,
        fallecido=fallecido,
        fecha_defuncion=paciente.fecha_defuncion if fallecido else None,
    )


def sincronizar(
    store: InMemoryStore,
    peticion: SyncCivilRegistryRequest,
) -> SyncCivilRegistryResponse:
    """Procesa un lote de la lista contra el Registro Civil.

    Prioriza los registros que ya estaban marcados para verificacion, de modo
    que un lote chico igual resuelve primero lo que estaba pendiente.
    """
    candidatos = store.all()
    if peticion.health_service_id:
        objetivo = peticion.health_service_id.strip().upper()
        candidatos = [p for p in candidatos if p.health_service_id == objetivo]

    candidatos.sort(
        key=lambda p: p.estado_registro_civil is not CivilRegistryStatus.PENDING_VERIFICATION
    )
    lote = candidatos[: peticion.batch_size]

    purgados: list[PurgedPatient] = []
    vivos = 0

    for paciente in lote:
        respuesta = consultar_defuncion(paciente)

        if not respuesta.fallecido:
            vivos += 1
            if paciente.estado_registro_civil is not CivilRegistryStatus.ALIVE:
                paciente.estado_registro_civil = CivilRegistryStatus.ALIVE
                store.upsert(paciente)
            continue

        purgados.append(
            PurgedPatient(
                patient_id=paciente.patient_id,
                full_name=paciente.nombre_completo,
                date_of_death=respuesta.fecha_defuncion,
            )
        )

        if peticion.auto_purge_deceased:
            # Egreso administrativo: sale de la lista activa pero el registro se
            # conserva, porque el Servicio de Salud debe poder auditar por que
            # un paciente dejo de aparecer.
            paciente.estado_registro_civil = CivilRegistryStatus.DECEASED
            paciente.fecha_defuncion = respuesta.fecha_defuncion
            store.upsert(paciente)

    return SyncCivilRegistryResponse(
        processed_records=len(lote),
        alive_records=vivos,
        purged_deceased_records=len(purgados),
        purged_patients=purgados,
        synced_at=datetime.now(timezone.utc),
    )
