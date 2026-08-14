"""Referencias de tiempo de espera por especialidad y por Servicio de Salud.

El componente temporal del puntaje no compara al paciente contra una constante
nacional sino contra la realidad de su propia especialidad y su propio Servicio
(documentation.MD, Tabla 2): sin eso, un paciente de un servicio congestionado
desplazaria siempre a uno de un servicio agil, aunque ambos esperen lo mismo
respecto de lo que es normal donde se atienden.

Las cifras salen del informe BCN (agosto 2024) citado en documentation.MD 3:
mediana 255 dias en consulta nueva de especialidad, 305 dias en cirugia No GES
(Traumatologia 454, Cardiovascular 415), P75 nacional de 579 dias en cirugia.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Especialidad:
    """Una especialidad de la red, con sus tiempos de espera de referencia."""

    codigo: str
    label: str
    mediana_dias: int
    p75_dias: int
    es_quirurgica: bool = False
    es_oncologica: bool = False


ESPECIALIDADES: dict[str, Especialidad] = {
    e.codigo: e
    for e in [
        # --- Consulta nueva de especialidad (mediana nacional 255 dias) ------
        Especialidad("OFTALMOLOGIA", "Oftalmologia", 268, 601),
        Especialidad("OTORRINOLARINGOLOGIA", "Otorrinolaringologia", 259, 578),
        Especialidad("DERMATOLOGIA", "Dermatologia", 241, 533),
        Especialidad("NEUROLOGIA", "Neurologia", 233, 512),
        Especialidad("CARDIOLOGIA", "Cardiologia", 198, 447),
        Especialidad("ODONTOLOGIA", "Odontologia", 224, 496),
        Especialidad("MEDICINA_INTERNA", "Medicina Interna", 212, 470),
        # --- Cirugia electiva No GES (mediana nacional 305 dias) -------------
        Especialidad("TRAUMATOLOGIA", "Traumatologia", 454, 902, es_quirurgica=True),
        Especialidad("CIRUGIA_DIGESTIVA", "Cirugia Digestiva", 318, 640, es_quirurgica=True),
        Especialidad("CIRUGIA_CARDIOVASCULAR", "Cirugia Cardiovascular", 415, 831, es_quirurgica=True),
        Especialidad("UROLOGIA", "Urologia", 296, 587, es_quirurgica=True),
        Especialidad("GINECOLOGIA", "Ginecologia", 271, 549, es_quirurgica=True),
        # --- Area oncologica: plazos mas cortos, riesgo vital ----------------
        # Decreto 18/2026. La referencia es agresiva a proposito: superar 90
        # dias en sospecha oncologica ya es una desviacion grave.
        Especialidad("ONCOLOGIA_MEDICA", "Oncologia Medica", 92, 188, es_oncologica=True),
        Especialidad("HEMATO_ONCOLOGIA", "Hemato-Oncologia", 74, 152, es_oncologica=True),
        Especialidad(
            "CIRUGIA_MAMA", "Cirugia de Mama", 108, 214, es_quirurgica=True, es_oncologica=True
        ),
        Especialidad(
            "GINECOLOGIA_ONCOLOGICA",
            "Ginecologia Oncologica",
            96,
            197,
            es_quirurgica=True,
            es_oncologica=True,
        ),
        Especialidad("RADIOTERAPIA", "Radioterapia", 66, 141, es_oncologica=True),
    ]
}

# Mediana y P75 por defecto cuando llega una especialidad que el catalogo no
# conoce: se usan las cifras nacionales de consulta nueva del informe BCN.
MEDIANA_POR_DEFECTO = 255
P75_POR_DEFECTO = 579


@dataclass(frozen=True)
class ServicioDeSalud:
    """Uno de los 29 Servicios de Salud del SNSS.

    `factor_congestion` escala las referencias nacionales a la realidad local.
    SS Los Rios registra un P75 de 1.214 dias contra los 579 nacionales
    (documentation.MD, Tabla 1), de ahi su factor 2.1.
    """

    codigo: str
    label: str
    factor_congestion: float = 1.0


SERVICIOS_DE_SALUD: dict[str, ServicioDeSalud] = {
    s.codigo: s
    for s in [
        ServicioDeSalud("SSMO", "S.S. Metropolitano Oriente", 0.95),
        ServicioDeSalud("SSMS", "S.S. Metropolitano Sur", 1.12),
        ServicioDeSalud("SSMN", "S.S. Metropolitano Norte", 1.05),
        ServicioDeSalud("SSMOC", "S.S. Metropolitano Occidente", 1.18),
        ServicioDeSalud("SSVQ", "S.S. Valparaiso - San Antonio", 1.24),
        ServicioDeSalud("SSCONCEPCION", "S.S. Concepcion", 1.09),
        ServicioDeSalud("SS_ARAUCANIA_SUR", "S.S. Araucania Sur", 1.41),
        ServicioDeSalud("SS_LOS_RIOS", "S.S. Los Rios", 2.10),
    ]
}


def referencias(especialidad: str, health_service_id: str) -> tuple[float, float]:
    """Mediana y P75 de dias de espera aplicables a un paciente concreto.

    Devuelve siempre valores > 0 para que el motor de puntaje pueda dividir sin
    resguardos adicionales.
    """
    esp = ESPECIALIDADES.get(especialidad)
    mediana = esp.mediana_dias if esp else MEDIANA_POR_DEFECTO
    p75 = esp.p75_dias if esp else P75_POR_DEFECTO

    servicio = SERVICIOS_DE_SALUD.get(health_service_id)
    factor = servicio.factor_congestion if servicio else 1.0

    return max(1.0, mediana * factor), max(1.0, p75 * factor)


def label_especialidad(codigo: str) -> str:
    """Nombre legible de la especialidad, o el codigo si no esta en catalogo."""
    esp = ESPECIALIDADES.get(codigo)
    return esp.label if esp else codigo.replace("_", " ").title()


def label_servicio(codigo: str) -> str:
    """Nombre legible del Servicio de Salud, o el codigo si no esta en catalogo."""
    servicio = SERVICIOS_DE_SALUD.get(codigo)
    return servicio.label if servicio else codigo


def es_especialidad_oncologica(codigo: str) -> bool:
    """True si la especialidad pertenece al area del cancer."""
    esp = ESPECIALIDADES.get(codigo)
    return bool(esp and esp.es_oncologica)
