"""Parametros del motor de priorizacion.

Todo lo que un Servicio de Salud podria querer calibrar vive aca. Los pesos
reproducen el ejemplo publicado en documentation.MD 4.2 (total 87.45 =
35.20 tiempo + 30.00 clinico + 15.00 oncologico + 7.25 vencimiento).
"""

from pathlib import Path

# --- Ponderaciones del puntaje total (documentation.MD 5, suma 1.0) ---------
W_TIEMPO = 0.35
W_CLINICO = 0.30
W_ONCOLOGICO = 0.20
W_VENCIMIENTO = 0.15

# --- Componente temporal ---------------------------------------------------
# S_tiempo = min(100, D/mediana * 50 + D/P75 * 30)
FACTOR_MEDIANA = 50
FACTOR_P75 = 30

# --- Componente clinico ----------------------------------------------------
SCORE_GES_RETRASADO = 100.0  # incumplimiento de garantia legal
SCORE_GES_VIGENTE_BASE = 60.0
SCORE_GES_VIGENTE_MAX = 95.0  # al borde del plazo
DIAS_ESCALADA_GES = 30  # ventana en que el GES vigente escala hacia el maximo

SCORE_SEVERIDAD = {"ALTA": 85.0, "MEDIA": 55.0, "BAJA": 40.0}
BONO_HOSPITALIZADO = 10.0  # el paciente hospitalizado ocupa una cama de la red

# --- Componente oncologico (Decreto 18/2026) -------------------------------
SCORE_ONCO_ETAPA_CRITICA = 100.0  # sospecha o diagnostico
SCORE_ONCO_OTRAS_ETAPAS = 70.0
MULTIPLICADOR_ESPECIALIDAD_CRITICA = 1.25

ESPECIALIDADES_CRITICAS_DECRETO_18 = {
    "ONCOLOGIA_MEDICA",
    "HEMATO_ONCOLOGIA",
    "GINECOLOGIA_ONCOLOGICA",
    "CIRUGIA_MAMA",
    "RADIOTERAPIA",
}

# --- Componente de obsolescencia diagnostica -------------------------------
DIAS_EXAMENES_VENCIDOS = 365  # sobre un anio: hay que repetir todo
DIAS_EXAMENES_POR_VENCER = 180  # entre 6 y 12 meses: validez dudosa
SCORE_EXAMENES_VENCIDOS = 100.0
SCORE_EXAMENES_POR_VENCER = 60.0

# --- Umbrales de badges (documentation.MD 6.1) -----------------------------
DIAS_PACIENTE_ANTIGUO = 300

# --- Tramos de prioridad ---------------------------------------------------
# Calibrados contra el rango efectivamente alcanzable, no contra el 0-100
# teorico: un paciente no oncologico llega como maximo a 80 puntos
# (35 + 30 + 0 + 15), asi que umbrales mas altos dejarian el tramo superior
# reservado de facto a un solo diagnostico.
UMBRAL_CRITICA = 85.0
UMBRAL_ALTA = 70.0
UMBRAL_MEDIA = 50.0

# Piso legal: una garantia GES vencida es un incumplimiento de la Ley 19.966,
# no una preferencia clinica. Por bajo que quede su puntaje, el paciente no
# puede rotularse como espera estandar mientras el Estado le deba la atencion.
PISO_GES_RETRASADO = "ALTA_PRIORIDAD"

# --- Datos y despliegue ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SEED_CSV_PATH = BASE_DIR / "data" / "pacientes_seed.csv"

# MVP con datos sinteticos y sin autenticacion: se abre CORS para que el static
# site de Render pueda consumir la API sin acoplar las dos URLs entre si.
CORS_ORIGINS = ["*"]

LIMITES_PAGINA_PERMITIDOS = (10, 20, 30, 50, 100)
