"""Adaptador de archivo plano: el formato en que los Servicios exportan hoy.

Es tambien el que carga la poblacion inicial (`data/pacientes_seed.csv`), asi
que las columnas del CSV son los nombres canonicos y no hay traduccion que
hacer mas alla de tipos.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..enums import CivilRegistryStatus, ClinicalSeverity, PatientType, Regimen, Stage
from ..models import PatientRecord
from .base import PatientRecordAdapter, a_bool, a_fecha, a_texto, requerido


class CsvAdapter(PatientRecordAdapter):
    """Registros exportados como CSV plano con las columnas canonicas."""

    name = "csv"
    label = "Archivo plano (CSV)"
    description = (
        "Exportacion CSV con los nombres de campo canonicos. Es el formato de la "
        "poblacion inicial y el que usan los Servicios para entregar sus listas."
    )

    def to_canonical(self, raw: dict[str, Any]) -> PatientRecord:
        regimen = Regimen(str(requerido(raw, "regimen")).strip().upper())

        return PatientRecord(
            rut=str(requerido(raw, "rut")),
            nombre_completo=str(requerido(raw, "nombre_completo")).strip(),
            fecha_nacimiento=a_fecha(raw.get("fecha_nacimiento")),
            regimen=regimen,
            # Solo el regimen GES tiene plazo legal. Si un No GES trae fecha, se
            # descarta: dejarla pasar haria que la UI mostrara una garantia que
            # no existe.
            fecha_expiracion_ges=(
                a_fecha(raw.get("fecha_expiracion_ges")) if regimen is Regimen.GES else None
            ),
            tipo_paciente=PatientType(str(requerido(raw, "tipo_paciente")).strip().upper()),
            especialidad=str(requerido(raw, "especialidad")),
            stage=Stage(str(requerido(raw, "stage")).strip().upper()),
            health_service_id=str(requerido(raw, "health_service_id")),
            diagnostico=a_texto(raw.get("diagnostico")) or "",
            fecha_ingreso_lista=a_fecha(requerido(raw, "fecha_ingreso_lista")),
            fecha_ultimos_examenes=a_fecha(raw.get("fecha_ultimos_examenes")),
            es_oncologico=a_bool(raw.get("es_oncologico")),
            severidad_clinica=ClinicalSeverity(
                str(raw.get("severidad_clinica") or "MEDIA").strip().upper()
            ),
            estadificacion=a_texto(raw.get("estadificacion")),
            telefono_contacto=a_texto(raw.get("telefono_contacto")),
            estado_registro_civil=CivilRegistryStatus(
                str(raw.get("estado_registro_civil") or "ALIVE").strip().upper()
            ),
            fecha_defuncion=a_fecha(raw.get("fecha_defuncion")),
            origen=self.name,
        )

    def sample_payload(self) -> dict[str, Any]:
        return {
            "rut": "12940112-5",
            "nombre_completo": "Maria Fernanda Pereira Soto",
            "fecha_nacimiento": "1968-04-22",
            "regimen": "NO_GES",
            "fecha_expiracion_ges": "",
            "tipo_paciente": "AMBULATORIO",
            "especialidad": "CIRUGIA_MAMA",
            "stage": "DIAGNOSTICO",
            "health_service_id": "SSMO",
            "diagnostico": "Nodulo mamario en estudio, BIRADS 4",
            "fecha_ingreso_lista": "2025-06-30",
            "fecha_ultimos_examenes": "2024-09-15",
            "es_oncologico": "true",
            "severidad_clinica": "ALTA",
            "estadificacion": "",
            "telefono_contacto": "+56 9 8123 4567",
            "estado_registro_civil": "ALIVE",
            "fecha_defuncion": "",
        }


def leer_csv(path: Path) -> list[PatientRecord]:
    """Lee el archivo semilla completo y devuelve entidades canonicas.

    Una fila mal formada no bota la carga: se informa por consola y el resto de
    la lista entra igual. En produccion esas filas irian a una cola de rechazos.
    """
    adaptador = CsvAdapter()
    registros: list[PatientRecord] = []
    rechazos: list[str] = []

    with path.open(encoding="utf-8-sig", newline="") as archivo:
        for numero, fila in enumerate(csv.DictReader(archivo), start=2):
            try:
                registros.append(adaptador.to_canonical(fila))
            except Exception as exc:  # noqa: BLE001 - se reporta y se sigue
                rechazos.append(f"  linea {numero}: {exc}")

    if rechazos:
        print(f"[seed] {len(rechazos)} fila(s) rechazada(s) en {path.name}:")
        for detalle in rechazos[:10]:
            print(detalle)

    return registros
