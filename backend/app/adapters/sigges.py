"""Adaptador SIGGES: sistema de monitoreo de las Garantias Explicitas en Salud.

Todo lo que sale de SIGGES es, por definicion, regimen GES: su unidad de
registro es el folio de garantia con su fecha limite legal (Ley 19.966).
"""

from __future__ import annotations

from typing import Any

from ..enums import CivilRegistryStatus, ClinicalSeverity, PatientType, Regimen, Stage
from ..models import PatientRecord
from .base import PatientRecordAdapter, a_bool, a_fecha, a_texto, opcional, requerido

# SIGGES nombra la etapa por el hito de la garantia.
_HITOS = {
    "SOSPECHA": Stage.SOSPECHA,
    "CONFIRMACION_DIAGNOSTICA": Stage.DIAGNOSTICO,
    "CONFIRMACION": Stage.DIAGNOSTICO,
    "INICIO_TRATAMIENTO": Stage.TRATAMIENTO,
    "TRATAMIENTO": Stage.TRATAMIENTO,
    "SEGUIMIENTO": Stage.SEGUIMIENTO,
}

# Los problemas de salud GES del area oncologica segun el Decreto 18/2026.
_PROBLEMAS_ONCOLOGICOS = {
    "CANCER_DE_MAMA",
    "CANCER_CERVICOUTERINO",
    "CANCER_GASTRICO",
    "CANCER_COLORRECTAL",
    "CANCER_DE_PROSTATA",
    "CANCER_DE_PULMON",
    "LEUCEMIA",
    "LINFOMA",
    "CANCER_INFANTIL",
}


class SiggesAdapter(PatientRecordAdapter):
    """Garantias GES exportadas desde SIGGES."""

    name = "sigges"
    label = "SIGGES (garantias GES)"
    description = (
        "Monitoreo de Garantias Explicitas en Salud. Su unidad de registro es el folio "
        "de garantia con fecha limite legal, por lo que todo registro entra como GES."
    )

    def to_canonical(self, raw: dict[str, Any]) -> PatientRecord:
        problema = str(opcional(raw, "problemaSalud", "glosaProblemaSalud") or "").strip().upper()
        problema_normalizado = problema.replace(" ", "_")

        hito = str(opcional(raw, "hitoGarantia") or "CONFIRMACION_DIAGNOSTICA").strip().upper()

        return PatientRecord(
            rut=str(requerido(raw, "runBeneficiario", "rut")),
            nombre_completo=str(requerido(raw, "nombreBeneficiario", "nombre_completo")).strip(),
            fecha_nacimiento=a_fecha(opcional(raw, "fechaNacimientoBeneficiario")),
            regimen=Regimen.GES,
            fecha_expiracion_ges=a_fecha(
                requerido(raw, "fechaLimiteGarantia", "fechaVencimientoGarantia")
            ),
            tipo_paciente=(
                PatientType.HOSPITALARIO
                if a_bool(opcional(raw, "pacienteHospitalizado"))
                else PatientType.AMBULATORIO
            ),
            especialidad=str(requerido(raw, "especialidadResolutora", "especialidad")),
            stage=_HITOS.get(hito, Stage.DIAGNOSTICO),
            health_service_id=str(requerido(raw, "codServicioSalud", "servicioSalud")),
            diagnostico=problema.replace("_", " ").title(),
            fecha_ingreso_lista=a_fecha(requerido(raw, "fechaOtorgamientoGarantia", "fechaInicio")),
            fecha_ultimos_examenes=a_fecha(opcional(raw, "fechaUltimaPrestacion")),
            es_oncologico=problema_normalizado in _PROBLEMAS_ONCOLOGICOS
            or a_bool(opcional(raw, "esOncologico")),
            # Una garantia GES retrasada ya es incumplimiento legal: el motor de
            # puntaje la trata como severidad maxima sin mirar este campo, pero
            # se conserva por trazabilidad.
            severidad_clinica=ClinicalSeverity.ALTA,
            estadificacion=a_texto(opcional(raw, "etapificacionTNM", "estadificacion")),
            telefono_contacto=a_texto(opcional(raw, "telefonoBeneficiario")),
            estado_registro_civil=CivilRegistryStatus.ALIVE,
            origen=self.name,
        )

    def sample_payload(self) -> dict[str, Any]:
        return {
            "folioGarantia": "GES-2025-4471932",
            "runBeneficiario": "9382102-5",
            "nombreBeneficiario": "Ana Gomez Rojas",
            "fechaNacimientoBeneficiario": "1959-11-30",
            "problemaSalud": "CANCER_CERVICOUTERINO",
            "hitoGarantia": "CONFIRMACION_DIAGNOSTICA",
            "fechaOtorgamientoGarantia": "2026-06-07",
            "fechaLimiteGarantia": "2026-07-22",
            "fechaUltimaPrestacion": "2026-06-10",
            "especialidadResolutora": "GINECOLOGIA_ONCOLOGICA",
            "codServicioSalud": "SSMO",
            "pacienteHospitalizado": False,
            "etapificacionTNM": "T2bN1M0",
            "telefonoBeneficiario": "+56 9 6301 2244",
        }
