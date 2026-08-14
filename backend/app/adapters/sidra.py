"""Adaptador SIDRA: plataforma de agendamiento del MINSAL.

SIDRA entrega la solicitud de atencion en camelCase, con el RUT partido en
cuerpo y digito verificador y la especialidad como codigo de prestacion.
"""

from __future__ import annotations

from typing import Any

from ..enums import CivilRegistryStatus, ClinicalSeverity, PatientType, Regimen, Stage
from ..models import PatientRecord
from .base import PatientRecordAdapter, a_bool, a_fecha, a_texto, opcional, requerido

# SIDRA identifica la prestacion por codigo, no por nombre.
_CODIGOS_PRESTACION = {
    "0901001": "OFTALMOLOGIA",
    "0902001": "OTORRINOLARINGOLOGIA",
    "0903001": "TRAUMATOLOGIA",
    "0904001": "CIRUGIA_DIGESTIVA",
    "0905001": "ONCOLOGIA_MEDICA",
    "0906001": "CIRUGIA_MAMA",
    "0907001": "GINECOLOGIA_ONCOLOGICA",
    "0908001": "RADIOTERAPIA",
    "0909001": "CARDIOLOGIA",
    "0910001": "NEUROLOGIA",
}

_TIPO_ATENCION = {
    "AMB": PatientType.AMBULATORIO,
    "AMBULATORIA": PatientType.AMBULATORIO,
    "HOSP": PatientType.HOSPITALARIO,
    "CERRADA": PatientType.HOSPITALARIO,
}

_ETAPAS = {
    "SOS": Stage.SOSPECHA,
    "DIA": Stage.DIAGNOSTICO,
    "TRA": Stage.TRATAMIENTO,
    "SEG": Stage.SEGUIMIENTO,
}


class SidraAdapter(PatientRecordAdapter):
    """Solicitudes de atencion provenientes de SIDRA."""

    name = "sidra"
    label = "SIDRA (agendamiento MINSAL)"
    description = (
        "Sistema centralizado de agendamiento. Entrega el RUT separado en cuerpo y "
        "digito verificador y la especialidad como codigo de prestacion."
    )

    def to_canonical(self, raw: dict[str, Any]) -> PatientRecord:
        cuerpo = requerido(raw, "rutPaciente", "rut")
        dv = opcional(raw, "dvPaciente", "dv")
        rut = f"{cuerpo}-{dv}" if dv else str(cuerpo)

        codigo = str(requerido(raw, "codEspecialidad", "codPrestacion")).strip()
        especialidad = _CODIGOS_PRESTACION.get(codigo, codigo)

        regimen = (
            Regimen.GES if a_bool(opcional(raw, "tieneGarantiaGes")) else Regimen.NO_GES
        )
        tipo = _TIPO_ATENCION.get(
            str(opcional(raw, "tipoAtencion") or "AMB").strip().upper(),
            PatientType.AMBULATORIO,
        )
        etapa = _ETAPAS.get(
            str(opcional(raw, "etapaClinica") or "DIA").strip().upper(),
            Stage.DIAGNOSTICO,
        )

        return PatientRecord(
            rut=rut,
            nombre_completo=" ".join(
                parte
                for parte in [
                    a_texto(raw.get("nombres")),
                    a_texto(raw.get("apellidoPaterno")),
                    a_texto(raw.get("apellidoMaterno")),
                ]
                if parte
            )
            or str(requerido(raw, "nombreCompleto")),
            fecha_nacimiento=a_fecha(opcional(raw, "fechaNacimiento")),
            regimen=regimen,
            fecha_expiracion_ges=(
                a_fecha(opcional(raw, "fechaLimiteGarantia")) if regimen is Regimen.GES else None
            ),
            tipo_paciente=tipo,
            especialidad=especialidad,
            stage=etapa,
            health_service_id=str(requerido(raw, "codServicioSalud", "servicioSalud")),
            diagnostico=a_texto(raw.get("hipotesisDiagnostica")) or "",
            fecha_ingreso_lista=a_fecha(requerido(raw, "fechaSolicitud", "fechaIngresoLE")),
            fecha_ultimos_examenes=a_fecha(opcional(raw, "fechaUltimoExamen")),
            es_oncologico=a_bool(opcional(raw, "sospechaOncologica")),
            severidad_clinica=ClinicalSeverity(
                str(opcional(raw, "prioridadDerivador") or "MEDIA").strip().upper()
            ),
            estadificacion=a_texto(raw.get("etapificacion")),
            telefono_contacto=a_texto(opcional(raw, "telefonoContacto", "fonoPaciente")),
            estado_registro_civil=CivilRegistryStatus.ALIVE,
            origen=self.name,
        )

    def sample_payload(self) -> dict[str, Any]:
        return {
            "rutPaciente": "18492041",
            "dvPaciente": "7",
            "nombres": "Jorge Andres",
            "apellidoPaterno": "Morales",
            "apellidoMaterno": "Silva",
            "fechaNacimiento": "1971-03-08",
            "codEspecialidad": "0905001",
            "codServicioSalud": "SSMO",
            "tipoAtencion": "AMB",
            "etapaClinica": "SOS",
            "tieneGarantiaGes": False,
            "fechaSolicitud": "2025-10-06",
            "fechaUltimoExamen": "2023-11-10",
            "sospechaOncologica": True,
            "prioridadDerivador": "ALTA",
            "hipotesisDiagnostica": "Baja de peso y adenopatias, descartar linfoma",
            "telefonoContacto": "+56 9 7412 8890",
        }
