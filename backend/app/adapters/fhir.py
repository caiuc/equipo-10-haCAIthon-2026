"""Adaptador HL7 FHIR R4: la via de entrada para los HIS locales modernos.

Recibe un Bundle con un Patient y un ServiceRequest. A diferencia de los tres
sistemas nacionales, aca los datos vienen anidados y los codigos viajan dentro
de estructuras CodeableConcept.
"""

from __future__ import annotations

from typing import Any

from ..enums import CivilRegistryStatus, ClinicalSeverity, PatientType, Regimen, Stage
from ..models import PatientRecord
from .base import ErrorDeAdaptacion, PatientRecordAdapter, a_fecha, a_texto

_PRIORIDADES_FHIR = {
    "stat": ClinicalSeverity.ALTA,
    "asap": ClinicalSeverity.ALTA,
    "urgent": ClinicalSeverity.MEDIA,
    "routine": ClinicalSeverity.BAJA,
}

_CATEGORIAS_ETAPA = {
    "suspicion": Stage.SOSPECHA,
    "diagnostic": Stage.DIAGNOSTICO,
    "treatment": Stage.TRATAMIENTO,
    "follow-up": Stage.SEGUIMIENTO,
}


def _recursos(bundle: dict[str, Any], tipo: str) -> list[dict[str, Any]]:
    """Recursos de un tipo dentro del Bundle."""
    return [
        entrada.get("resource", {})
        for entrada in bundle.get("entry", [])
        if entrada.get("resource", {}).get("resourceType") == tipo
    ]


def _codigo(concepto: dict[str, Any] | None) -> str | None:
    """Primer code de un CodeableConcept, o su texto si no trae coding."""
    if not concepto:
        return None
    for coding in concepto.get("coding", []):
        if coding.get("code"):
            return str(coding["code"])
    return a_texto(concepto.get("text"))


class FhirAdapter(PatientRecordAdapter):
    """Bundles HL7 FHIR R4 provenientes de fichas clinicas electronicas locales."""

    name = "fhir"
    label = "HL7 FHIR R4 (HIS local)"
    description = (
        "Bundle con Patient y ServiceRequest. Es la via de entrada para las fichas "
        "clinicas electronicas locales que ya hablan un estandar internacional."
    )

    def to_canonical(self, raw: dict[str, Any]) -> PatientRecord:
        pacientes = _recursos(raw, "Patient")
        solicitudes = _recursos(raw, "ServiceRequest")
        if not pacientes or not solicitudes:
            raise ErrorDeAdaptacion(
                "El Bundle debe contener al menos un Patient y un ServiceRequest."
            )

        paciente, solicitud = pacientes[0], solicitudes[0]

        rut = None
        for identificador in paciente.get("identifier", []):
            if "run" in str(identificador.get("system", "")).lower() or identificador.get("value"):
                rut = identificador.get("value")
                break
        if not rut:
            raise ErrorDeAdaptacion("El recurso Patient no trae un identificador de RUN/RUT.")

        nombre = paciente.get("name", [{}])[0]
        nombre_completo = " ".join(
            [*nombre.get("given", []), *([nombre.get("family")] if nombre.get("family") else [])]
        ) or a_texto(nombre.get("text"))
        if not nombre_completo:
            raise ErrorDeAdaptacion("El recurso Patient no trae nombre.")

        categoria = _codigo((solicitud.get("category") or [{}])[0])
        prioridad = str(solicitud.get("priority") or "routine").lower()
        extensiones = {
            str(ext.get("url", "")).rsplit("/", 1)[-1]: ext
            for ext in solicitud.get("extension", [])
        }

        def _ext(clave: str) -> Any:
            ext = extensiones.get(clave)
            if not ext:
                return None
            for campo, valor in ext.items():
                if campo.startswith("value"):
                    return valor
            return None

        es_ges = bool(_ext("garantia-ges"))

        return PatientRecord(
            rut=str(rut),
            nombre_completo=nombre_completo,
            fecha_nacimiento=a_fecha(paciente.get("birthDate")),
            regimen=Regimen.GES if es_ges else Regimen.NO_GES,
            fecha_expiracion_ges=a_fecha(_ext("fecha-limite-garantia")) if es_ges else None,
            tipo_paciente=(
                PatientType.HOSPITALARIO
                if str(_ext("modalidad") or "").lower() in {"inpatient", "hospitalario"}
                else PatientType.AMBULATORIO
            ),
            especialidad=str(_codigo(solicitud.get("code")) or _ext("especialidad") or "").strip()
            or "MEDICINA_INTERNA",
            stage=_CATEGORIAS_ETAPA.get(str(categoria or "").lower(), Stage.DIAGNOSTICO),
            health_service_id=str(_ext("servicio-salud") or "SSMO"),
            diagnostico=a_texto((solicitud.get("reasonCode") or [{}])[0].get("text")) or "",
            fecha_ingreso_lista=a_fecha(solicitud.get("authoredOn"))
            or a_fecha(solicitud.get("occurrenceDateTime")),
            fecha_ultimos_examenes=a_fecha(_ext("fecha-ultimos-examenes")),
            es_oncologico=bool(_ext("sospecha-oncologica")),
            severidad_clinica=_PRIORIDADES_FHIR.get(prioridad, ClinicalSeverity.MEDIA),
            estadificacion=a_texto(_ext("etapificacion")),
            telefono_contacto=next(
                (
                    a_texto(contacto.get("value"))
                    for contacto in paciente.get("telecom", [])
                    if contacto.get("system") == "phone"
                ),
                None,
            ),
            estado_registro_civil=(
                CivilRegistryStatus.DECEASED
                if paciente.get("deceasedBoolean") or paciente.get("deceasedDateTime")
                else CivilRegistryStatus.ALIVE
            ),
            fecha_defuncion=a_fecha(paciente.get("deceasedDateTime")),
            origen=self.name,
        )

    def sample_payload(self) -> dict[str, Any]:
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "identifier": [
                            {"system": "http://minsal.cl/run", "value": "12940112-5"}
                        ],
                        "name": [{"given": ["Maria", "Fernanda"], "family": "Pereira Soto"}],
                        "birthDate": "1968-04-22",
                        "telecom": [{"system": "phone", "value": "+56 9 8123 4567"}],
                    }
                },
                {
                    "resource": {
                        "resourceType": "ServiceRequest",
                        "status": "active",
                        "intent": "order",
                        "priority": "asap",
                        "authoredOn": "2025-06-30",
                        "category": [{"coding": [{"code": "diagnostic"}]}],
                        "code": {"coding": [{"code": "CIRUGIA_MAMA"}]},
                        "reasonCode": [{"text": "Nodulo mamario BIRADS 4, biopsia pendiente"}],
                        "extension": [
                            {"url": "http://minsal.cl/fhir/servicio-salud", "valueString": "SSMO"},
                            {
                                "url": "http://minsal.cl/fhir/sospecha-oncologica",
                                "valueBoolean": True,
                            },
                            {
                                "url": "http://minsal.cl/fhir/fecha-ultimos-examenes",
                                "valueDate": "2024-09-15",
                            },
                            {"url": "http://minsal.cl/fhir/modalidad", "valueString": "outpatient"},
                        ],
                    }
                },
            ],
        }
