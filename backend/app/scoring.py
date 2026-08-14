"""Motor de priorizacion dinamica (documentation.MD 5).

    Puntaje = W_T * S_tiempo + W_C * S_clinico + W_O * S_oncologico + W_V * S_vencimiento

Cada componente se calcula en escala 0-100 y se pondera; los cuatro aportes
ponderados suman el puntaje final, tambien en 0-100. El desglose que devuelve la
API es exactamente esa descomposicion, de modo que un coordinador siempre puede
responder por que un paciente esta donde esta.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone

from . import benchmarks, config
from .enums import CivilRegistryStatus, PriorityLevel, Regimen, Stage
from .models import (
    PatientFlags,
    PatientRecord,
    PatientScoreResponse,
    ScoreBreakdown,
    ScoreMetadata,
)

_ETAPAS_CRITICAS_ONCO = {Stage.SOSPECHA, Stage.DIAGNOSTICO}


@dataclass(frozen=True)
class ScoreResult:
    """Puntaje calculado de un paciente, con todo lo necesario para explicarlo."""

    total: float
    level: PriorityLevel
    breakdown: ScoreBreakdown
    flags: PatientFlags
    days_waiting: int
    median_days: float
    p75_days: float
    exams_expired: bool


# --------------------------------------------------------------------------
# Componentes
# --------------------------------------------------------------------------
def score_tiempo(dias: int, mediana: float, p75: float) -> float:
    """S_tiempo: la espera del paciente medida contra la de sus pares.

    Se normaliza contra la mediana y el P75 de su especialidad y Servicio, no
    contra una constante nacional: 400 dias en Radioterapia y 400 dias en
    Traumatologia no significan lo mismo.
    """
    bruto = (dias / mediana) * config.FACTOR_MEDIANA + (dias / p75) * config.FACTOR_P75
    return min(100.0, bruto)


def score_clinico(paciente: PatientRecord, hoy: date) -> float:
    """S_clinico: severidad y garantia legal de oportunidad.

    El regimen GES manda sobre la severidad declarada, porque una garantia
    vencida no es una opinion clinica sino un incumplimiento de la Ley 19.966.
    """
    if paciente.regimen is Regimen.GES:
        limite = paciente.fecha_expiracion_ges
        if limite is None:
            base = config.SCORE_GES_VIGENTE_BASE
        elif limite < hoy:
            base = config.SCORE_GES_RETRASADO
        else:
            # Dentro de la ventana previa al plazo, el puntaje escala de forma
            # lineal hacia el maximo: mientras mas cerca del vencimiento, mas
            # urgente agendar antes de que se convierta en incumplimiento.
            restantes = (limite - hoy).days
            if restantes >= config.DIAS_ESCALADA_GES:
                base = config.SCORE_GES_VIGENTE_BASE
            else:
                avance = (config.DIAS_ESCALADA_GES - restantes) / config.DIAS_ESCALADA_GES
                rango = config.SCORE_GES_VIGENTE_MAX - config.SCORE_GES_VIGENTE_BASE
                base = config.SCORE_GES_VIGENTE_BASE + rango * avance
    else:
        base = config.SCORE_SEVERIDAD[paciente.severidad_clinica.value]

    if paciente.tipo_paciente.value == "HOSPITALARIO":
        base += config.BONO_HOSPITALIZADO

    return min(100.0, base)


def score_oncologico(paciente: PatientRecord) -> float:
    """S_oncologico: sesgo del Decreto 18/2026 sobre el area del cancer."""
    if not paciente.es_oncologico:
        return 0.0

    base = (
        config.SCORE_ONCO_ETAPA_CRITICA
        if paciente.stage in _ETAPAS_CRITICAS_ONCO
        else config.SCORE_ONCO_OTRAS_ETAPAS
    )

    if paciente.especialidad in config.ESPECIALIDADES_CRITICAS_DECRETO_18:
        base *= config.MULTIPLICADOR_ESPECIALIDAD_CRITICA

    return min(100.0, base)


def score_vencimiento(paciente: PatientRecord, hoy: date) -> float:
    """S_vencimiento: castigo por exameneres caducados.

    Un paciente cuyos examenes ya no sirven no puede ser operado aunque le
    asignen hora: hay que repetirle todo antes. Sin este componente queda
    atrapado en un bucle administrativo, bajando de prioridad cada vez que su
    caso se revisa.
    """
    if paciente.fecha_ultimos_examenes is None:
        # Sin registro de examenes se asume lo peor: hay que evaluarlo de nuevo.
        return config.SCORE_EXAMENES_VENCIDOS

    antiguedad = (hoy - paciente.fecha_ultimos_examenes).days
    if antiguedad > config.DIAS_EXAMENES_VENCIDOS:
        return config.SCORE_EXAMENES_VENCIDOS
    if antiguedad > config.DIAS_EXAMENES_POR_VENCER:
        return config.SCORE_EXAMENES_POR_VENCER
    return 0.0


# --------------------------------------------------------------------------
# Flags y tramos
# --------------------------------------------------------------------------
def _examenes_vencidos(paciente: PatientRecord, hoy: date) -> bool:
    if paciente.fecha_ultimos_examenes is None:
        return True
    return (hoy - paciente.fecha_ultimos_examenes).days > config.DIAS_EXAMENES_VENCIDOS


def _info_incompleta(paciente: PatientRecord) -> bool:
    """Falta un dato que bloquea la asignacion definitiva de hora."""
    if not paciente.telefono_contacto:
        return True
    if paciente.es_oncologico and not paciente.estadificacion:
        return True
    return False


def _ges_retrasado(paciente: PatientRecord, hoy: date) -> bool:
    return (
        paciente.regimen is Regimen.GES
        and paciente.fecha_expiracion_ges is not None
        and paciente.fecha_expiracion_ges < hoy
    )


_ORDEN_TRAMOS = [
    PriorityLevel.ESTANDAR,
    PriorityLevel.MEDIA_PRIORIDAD,
    PriorityLevel.ALTA_PRIORIDAD,
    PriorityLevel.CRITICA,
]


def nivel_prioridad(total: float, ges_retrasado: bool = False) -> PriorityLevel:
    """Tramo de prioridad al que corresponde un puntaje.

    El puntaje ordena la lista; el tramo la rotula. Una garantia GES vencida
    impone un piso sobre el rotulo aunque el puntaje quede bajo: mostrar
    "espera estandar" junto a la insignia de incumplimiento legal seria una
    contradiccion para quien tiene que decidir a quien agendar.
    """
    if total >= config.UMBRAL_CRITICA:
        tramo = PriorityLevel.CRITICA
    elif total >= config.UMBRAL_ALTA:
        tramo = PriorityLevel.ALTA_PRIORIDAD
    elif total >= config.UMBRAL_MEDIA:
        tramo = PriorityLevel.MEDIA_PRIORIDAD
    else:
        tramo = PriorityLevel.ESTANDAR

    if ges_retrasado:
        piso = PriorityLevel(config.PISO_GES_RETRASADO)
        if _ORDEN_TRAMOS.index(tramo) < _ORDEN_TRAMOS.index(piso):
            return piso

    return tramo


# --------------------------------------------------------------------------
# Calculo completo
# --------------------------------------------------------------------------
def calcular(paciente: PatientRecord, hoy: date | None = None) -> ScoreResult:
    """Puntaje total del paciente con su desglose ponderado y sus banderas."""
    hoy = hoy or date.today()
    dias = paciente.dias_esperando(hoy)
    mediana, p75 = benchmarks.referencias(paciente.especialidad, paciente.health_service_id)

    aporte_tiempo = config.W_TIEMPO * score_tiempo(dias, mediana, p75)
    aporte_clinico = config.W_CLINICO * score_clinico(paciente, hoy)
    aporte_onco = config.W_ONCOLOGICO * score_oncologico(paciente)
    aporte_vencimiento = config.W_VENCIMIENTO * score_vencimiento(paciente, hoy)

    total = round(aporte_tiempo + aporte_clinico + aporte_onco + aporte_vencimiento, 2)
    vencidos = _examenes_vencidos(paciente, hoy)
    ges_retrasado = _ges_retrasado(paciente, hoy)

    return ScoreResult(
        total=total,
        level=nivel_prioridad(total, ges_retrasado),
        breakdown=ScoreBreakdown(
            time_waiting_score=round(aporte_tiempo, 2),
            clinical_severity_score=round(aporte_clinico, 2),
            oncologic_risk_score=round(aporte_onco, 2),
            diagnostic_validity_penalty=round(aporte_vencimiento, 2),
        ),
        flags=PatientFlags(
            is_oncologic=paciente.es_oncologico,
            is_ancient_patient=dias > config.DIAS_PACIENTE_ANTIGUO and vencidos,
            incomplete_info=_info_incompleta(paciente),
            ges_delayed=ges_retrasado,
            civil_registry_status=paciente.estado_registro_civil,
        ),
        days_waiting=dias,
        median_days=round(mediana, 1),
        p75_days=round(p75, 1),
        exams_expired=vencidos,
    )


def a_respuesta(
    paciente: PatientRecord,
    resultado: ScoreResult,
    incluir_desglose: bool = True,
) -> PatientScoreResponse:
    """Empaqueta un ScoreResult en la respuesta publica de la API."""
    ultima_evaluacion = (
        datetime.combine(paciente.fecha_ultimos_examenes, datetime.min.time(), tzinfo=timezone.utc)
        if paciente.fecha_ultimos_examenes
        else None
    )

    return PatientScoreResponse(
        patient_id=paciente.patient_id,
        national_id=paciente.rut,
        regimen=paciente.regimen,
        stage=paciente.stage,
        specialty=paciente.especialidad,
        health_service_id=paciente.health_service_id,
        total_score=resultado.total,
        priority_level=resultado.level,
        flags=resultado.flags,
        breakdown=resultado.breakdown if incluir_desglose else None,
        metadata=ScoreMetadata(
            days_waiting=resultado.days_waiting,
            regional_median_days=resultado.median_days,
            regional_p75_days=resultado.p75_days,
            exams_expired=resultado.exams_expired,
            last_evaluation_date=ultima_evaluacion,
            calculated_at=datetime.now(timezone.utc),
        ),
    )


def esta_en_lista_activa(paciente: PatientRecord) -> bool:
    """False si el paciente ya egreso administrativamente por fallecimiento."""
    return paciente.estado_registro_civil is not CivilRegistryStatus.DECEASED
