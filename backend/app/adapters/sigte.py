"""Adaptador SIGTE: repositorio de tiempos de espera No GES.

SIGTE es el reverso de SIGGES: registra justamente lo que no tiene garantia
legal de oportunidad. Usa snake_case y mide la espera en dias acumulados en vez
de entregar la fecha de ingreso, de modo que aca se reconstruye la fecha.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..enums import CivilRegistryStatus, ClinicalSeverity, PatientType, Regimen, Stage
from ..models import PatientRecord
from .base import PatientRecordAdapter, a_bool, a_fecha, a_texto, opcional, requerido

_PRIORIDADES = {
    "1": ClinicalSeverity.ALTA,
    "2": ClinicalSeverity.MEDIA,
    "3": ClinicalSeverity.BAJA,
    "URGENTE": ClinicalSeverity.ALTA,
    "PREFERENTE": ClinicalSeverity.MEDIA,
    "HABITUAL": ClinicalSeverity.BAJA,
}

_TIPOS_REGISTRO = {
    "CONSULTA_NUEVA_ESPECIALIDAD": Stage.DIAGNOSTICO,
    "CONSULTA_NUEVA": Stage.DIAGNOSTICO,
    "PROCEDIMIENTO": Stage.DIAGNOSTICO,
    "INTERVENCION_QUIRURGICA": Stage.TRATAMIENTO,
    "CIRUGIA": Stage.TRATAMIENTO,
    "CONTROL": Stage.SEGUIMIENTO,
}


class SigteAdapter(PatientRecordAdapter):
    """Registros de lista de espera No GES exportados desde SIGTE."""

    name = "sigte"
    label = "SIGTE (lista de espera No GES)"
    description = (
        "Repositorio de tiempos de espera No GES. Reporta la espera como dias "
        "acumulados; el adaptador reconstruye la fecha de ingreso a partir de ese dato."
    )

    def to_canonical(self, raw: dict[str, Any]) -> PatientRecord:
        # SIGTE entrega dias acumulados, no fecha de ingreso. Si ademas viene la
        # fecha, se prefiere la fecha por ser el dato de origen.
        fecha_ingreso = a_fecha(opcional(raw, "fecha_entrada_le", "fecha_ingreso"))
        if fecha_ingreso is None:
            dias = int(float(requerido(raw, "dias_espera_acumulados")))
            fecha_ingreso = date.today() - timedelta(days=dias)

        tipo_registro = str(opcional(raw, "tipo_registro") or "CONSULTA_NUEVA").strip().upper()
        prioridad = str(opcional(raw, "prioridad_derivacion") or "2").strip().upper()

        return PatientRecord(
            rut=str(requerido(raw, "run_usuario", "rut")),
            nombre_completo=str(requerido(raw, "nombre_usuario", "nombre_completo")).strip(),
            fecha_nacimiento=a_fecha(opcional(raw, "fecha_nacimiento")),
            regimen=Regimen.NO_GES,
            fecha_expiracion_ges=None,  # por definicion, No GES no tiene plazo legal
            tipo_paciente=(
                PatientType.HOSPITALARIO
                if str(opcional(raw, "modalidad_atencion") or "").strip().upper()
                in {"CERRADA", "HOSPITALIZADO", "HOSPITALARIA"}
                else PatientType.AMBULATORIO
            ),
            especialidad=str(requerido(raw, "especialidad_destino", "especialidad")),
            stage=_TIPOS_REGISTRO.get(tipo_registro, Stage.DIAGNOSTICO),
            health_service_id=str(requerido(raw, "cod_servicio_salud", "servicio_salud")),
            diagnostico=a_texto(raw.get("glosa_diagnostico")) or "",
            fecha_ingreso_lista=fecha_ingreso,
            fecha_ultimos_examenes=a_fecha(opcional(raw, "fecha_ultimos_examenes")),
            es_oncologico=a_bool(opcional(raw, "sospecha_cancer", "es_oncologico")),
            severidad_clinica=_PRIORIDADES.get(prioridad, ClinicalSeverity.MEDIA),
            estadificacion=a_texto(raw.get("etapificacion")),
            telefono_contacto=a_texto(opcional(raw, "telefono_usuario", "fono_contacto")),
            estado_registro_civil=CivilRegistryStatus.ALIVE,
            origen=self.name,
        )

    def sample_payload(self) -> dict[str, Any]:
        return {
            "id_registro_lista": "SIGTE-SSMS-8841027",
            "run_usuario": "15022931-6",
            "nombre_usuario": "Juan Carlos Soto Soto",
            "fecha_nacimiento": "1974-07-19",
            "especialidad_destino": "TRAUMATOLOGIA",
            "cod_servicio_salud": "SSMS",
            "tipo_registro": "INTERVENCION_QUIRURGICA",
            "modalidad_atencion": "ABIERTA",
            "dias_espera_acumulados": 590,
            "fecha_ultimos_examenes": "2024-02-11",
            "prioridad_derivacion": "1",
            "sospecha_cancer": False,
            "glosa_diagnostico": "Gonartrosis severa bilateral, indicacion de artroplastia",
            "telefono_usuario": "+56 9 5544 1120",
        }
