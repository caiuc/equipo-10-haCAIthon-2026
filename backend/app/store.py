"""Repositorio en memoria de la lista de espera.

El MVP guarda los pacientes en un diccionario sembrado desde el CSV al arrancar.
Es deliberado: el despliegue de demostracion corre en un plan sin disco
persistente, y volver siempre a un estado limpio y conocido es preferible a
arrastrar cambios entre presentaciones. Sustituir esta clase por una con
Postgres detras no obliga a tocar el resto de la aplicacion.
"""

from __future__ import annotations

import threading
from datetime import date
from pathlib import Path

from . import benchmarks, scoring
from .enums import (
    CivilRegistryStatus,
    PatientType,
    PatientTypeFilter,
    Regimen,
    RegimenFilter,
    Stage,
    WaitlistOrder,
)
from .models import PatientRecord, WaitlistItem
from .rut import RutInvalido, normalizar
from .scoring import ScoreResult


class PacienteNoEncontrado(KeyError):
    """No hay ningun paciente con ese RUT en la lista."""


class PacienteDuplicado(ValueError):
    """Ya existe un paciente con ese RUT en la lista."""


class InMemoryStore:
    """Coleccion de pacientes indexada por RUT, con consulta priorizada."""

    def __init__(self) -> None:
        self._patients: dict[str, PatientRecord] = {}
        self._lock = threading.RLock()

    # -- Carga inicial -----------------------------------------------------
    def seed_from_csv(self, path: Path) -> int:
        """Carga el CSV semilla, reemplazando cualquier contenido previo."""
        from .adapters.csv_adapter import leer_csv

        registros = leer_csv(path)
        with self._lock:
            self._patients = {registro.rut: registro for registro in registros}
        return len(self._patients)

    # -- Acceso basico -----------------------------------------------------
    def __len__(self) -> int:
        return len(self._patients)

    def all(self) -> list[PatientRecord]:
        """Todos los registros, incluidos los egresados por fallecimiento."""
        with self._lock:
            return list(self._patients.values())

    def active(self) -> list[PatientRecord]:
        """Solo los pacientes que siguen efectivamente en lista de espera."""
        return [p for p in self.all() if scoring.esta_en_lista_activa(p)]

    def get(self, rut: str) -> PatientRecord:
        """Busca por RUT en cualquier formato. Levanta PacienteNoEncontrado."""
        try:
            clave = normalizar(rut)
        except RutInvalido as exc:
            raise PacienteNoEncontrado(str(exc)) from exc

        with self._lock:
            paciente = self._patients.get(clave)

        if paciente is None:
            raise PacienteNoEncontrado(f"No hay ningun paciente con RUT {clave} en la lista.")
        return paciente

    def exists(self, rut: str) -> bool:
        """True si el RUT esta en la lista (y es un RUT valido)."""
        try:
            self.get(rut)
        except PacienteNoEncontrado:
            return False
        return True

    def add(self, paciente: PatientRecord) -> PatientRecord:
        """Ingresa un paciente nuevo. Levanta PacienteDuplicado si ya existe."""
        with self._lock:
            if paciente.rut in self._patients:
                raise PacienteDuplicado(
                    f"El paciente con RUT {paciente.rut} ya esta en la lista de espera."
                )
            self._patients[paciente.rut] = paciente
        return paciente

    def upsert(self, paciente: PatientRecord) -> PatientRecord:
        """Ingresa o reemplaza el registro de un paciente."""
        with self._lock:
            self._patients[paciente.rut] = paciente
        return paciente

    def remove(self, rut: str) -> PatientRecord:
        """Retira un paciente de la lista y devuelve el registro retirado."""
        paciente = self.get(rut)
        with self._lock:
            self._patients.pop(paciente.rut, None)
        return paciente

    # -- Consulta priorizada ----------------------------------------------
    def scored(
        self,
        *,
        hoy: date | None = None,
        include_deceased: bool = False,
    ) -> list[tuple[PatientRecord, ScoreResult]]:
        """Todos los pacientes con su puntaje recalculado al dia de hoy."""
        hoy = hoy or date.today()
        universo = self.all() if include_deceased else self.active()
        return [(p, scoring.calcular(p, hoy)) for p in universo]

    def query(
        self,
        *,
        health_service: str | None = None,
        specialty: str | None = None,
        regimen: RegimenFilter = RegimenFilter.ALL,
        stage: Stage | None = None,
        patient_type: PatientTypeFilter = PatientTypeFilter.ALL,
        search: str | None = None,
        only_oncologic: bool = False,
        order: WaitlistOrder = WaitlistOrder.PRIORITY_DESC,
        hoy: date | None = None,
    ) -> list[tuple[PatientRecord, ScoreResult]]:
        """Filtra y ordena la lista completa. La paginacion se aplica despues.

        El ranking se calcula sobre el universo ya filtrado: el "#1" que ve el
        coordinador es el primero de lo que esta mirando, no una posicion
        nacional que cambiaria al tocar un filtro.
        """
        resultados = self.scored(hoy=hoy)

        if health_service:
            objetivo = health_service.strip().upper()
            resultados = [r for r in resultados if r[0].health_service_id == objetivo]

        if specialty:
            objetivo = specialty.strip().upper().replace(" ", "_")
            resultados = [r for r in resultados if r[0].especialidad == objetivo]

        if regimen is not RegimenFilter.ALL:
            objetivo_regimen = Regimen(regimen.value)
            resultados = [r for r in resultados if r[0].regimen is objetivo_regimen]

        if stage is not None:
            resultados = [r for r in resultados if r[0].stage is stage]

        if patient_type is not PatientTypeFilter.ALL:
            objetivo_tipo = PatientType(patient_type.value)
            resultados = [r for r in resultados if r[0].tipo_paciente is objetivo_tipo]

        if only_oncologic:
            resultados = [r for r in resultados if r[0].es_oncologico]

        if search:
            aguja = search.strip().lower()
            digitos = "".join(c for c in aguja if c.isalnum())
            resultados = [
                r
                for r in resultados
                if aguja in r[0].nombre_completo.lower()
                or (digitos and digitos in r[0].rut.replace("-", "").lower())
            ]

        return _ordenar(resultados, order)


def _ordenar(
    resultados: list[tuple[PatientRecord, ScoreResult]],
    order: WaitlistOrder,
) -> list[tuple[PatientRecord, ScoreResult]]:
    """Aplica el criterio de ordenamiento pedido.

    Los pacientes sin fecha de expiracion (todos los No GES) quedan siempre al
    final cuando se ordena por plazo, en cualquiera de las dos direcciones: no
    tienen garantia que vencer, asi que compararlos por fecha no significa nada.
    """
    if order in (WaitlistOrder.EXPIRATION_ASC, WaitlistOrder.EXPIRATION_DESC):
        descendente = order is WaitlistOrder.EXPIRATION_DESC
        con_plazo = [r for r in resultados if r[0].fecha_expiracion_ges is not None]
        sin_plazo = [r for r in resultados if r[0].fecha_expiracion_ges is None]
        con_plazo.sort(key=lambda r: r[0].fecha_expiracion_ges, reverse=descendente)
        sin_plazo.sort(key=lambda r: r[1].total, reverse=True)
        return con_plazo + sin_plazo

    claves = {
        WaitlistOrder.PRIORITY_DESC: (lambda r: r[1].total, True),
        WaitlistOrder.PRIORITY_ASC: (lambda r: r[1].total, False),
        WaitlistOrder.DAYS_DESC: (lambda r: r[1].days_waiting, True),
        WaitlistOrder.DAYS_ASC: (lambda r: r[1].days_waiting, False),
    }
    clave, descendente = claves[order]
    return sorted(resultados, key=clave, reverse=descendente)


def a_item(
    paciente: PatientRecord,
    resultado: ScoreResult,
    rank: int,
) -> WaitlistItem:
    """Convierte un par (paciente, puntaje) en la fila que consume la UI."""
    return WaitlistItem(
        rank=rank,
        patient_id=paciente.patient_id,
        national_id=paciente.rut,
        full_name=paciente.nombre_completo,
        specialty=paciente.especialidad,
        specialty_label=benchmarks.label_especialidad(paciente.especialidad),
        stage=paciente.stage,
        regimen=paciente.regimen,
        patient_type=paciente.tipo_paciente,
        health_service_id=paciente.health_service_id,
        health_service_label=benchmarks.label_servicio(paciente.health_service_id),
        ges_expiration_date=paciente.fecha_expiracion_ges,
        days_waiting=resultado.days_waiting,
        regional_median_days=resultado.median_days,
        regional_p75_days=resultado.p75_days,
        priority_score=resultado.total,
        priority_level=resultado.level,
        flags=resultado.flags,
    )


def paginar(
    resultados: list[tuple[PatientRecord, ScoreResult]],
    page: int,
    limit: int,
) -> tuple[list[WaitlistItem], int, int]:
    """Corta la pagina pedida y devuelve (filas, total de registros, total de paginas)."""
    total = len(resultados)
    total_paginas = max(1, -(-total // limit))  # division entera hacia arriba
    page = min(max(1, page), total_paginas)
    inicio = (page - 1) * limit

    filas = [
        a_item(paciente, resultado, rank=inicio + offset + 1)
        for offset, (paciente, resultado) in enumerate(resultados[inicio : inicio + limit])
    ]
    return filas, total, total_paginas


# Instancia unica que usan los routers. Se siembra en el startup de la app.
store = InMemoryStore()


def pacientes_fallecidos_pendientes() -> list[PatientRecord]:
    """Registros marcados para verificacion en el Registro Civil."""
    return [
        p
        for p in store.all()
        if p.estado_registro_civil is CivilRegistryStatus.PENDING_VERIFICATION
    ]
