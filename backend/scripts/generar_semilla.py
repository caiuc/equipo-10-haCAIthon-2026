"""Genera la poblacion inicial de pacientes (`data/pacientes_seed.csv`).

Determinista: con la misma semilla produce siempre el mismo archivo, de modo que
la demostracion es reproducible y el CSV se puede versionar sin ruido en el diff.

Los pacientes son sinteticos. Los RUT tienen digito verificador valido porque la
API los valida, pero los cuerpos provienen de un rango reservado para pruebas y
las combinaciones de nombre y RUT no corresponden a personas reales.

    python scripts/generar_semilla.py
"""

from __future__ import annotations

import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rut import calcular_digito_verificador  # noqa: E402

SEMILLA = 20260814
FECHA_REFERENCIA = date(2026, 8, 14)
TOTAL_PACIENTES = 140
DESTINO = Path(__file__).resolve().parent.parent / "data" / "pacientes_seed.csv"

COLUMNAS = [
    "rut",
    "nombre_completo",
    "fecha_nacimiento",
    "regimen",
    "fecha_expiracion_ges",
    "tipo_paciente",
    "especialidad",
    "stage",
    "health_service_id",
    "diagnostico",
    "fecha_ingreso_lista",
    "fecha_ultimos_examenes",
    "es_oncologico",
    "severidad_clinica",
    "estadificacion",
    "telefono_contacto",
    "estado_registro_civil",
    "fecha_defuncion",
]

NOMBRES_F = [
    "Maria", "Ana", "Carmen", "Rosa", "Patricia", "Claudia", "Francisca", "Javiera",
    "Soledad", "Ximena", "Valentina", "Camila", "Paulina", "Marcela", "Andrea",
    "Gladys", "Ruth", "Ignacia", "Antonia", "Catalina", "Fernanda", "Constanza",
]
NOMBRES_M = [
    "Juan", "Luis", "Jorge", "Carlos", "Pedro", "Sergio", "Manuel", "Ramon",
    "Cristian", "Rodrigo", "Matias", "Sebastian", "Felipe", "Nelson", "Hector",
    "Ignacio", "Benjamin", "Vicente", "Osvaldo", "Rene", "Mauricio", "Alvaro",
]
SEGUNDOS_F = ["Elena", "Isabel", "Paz", "Belen", "Angelica", "Teresa", "Luisa", "Jesus", ""]
SEGUNDOS_M = ["Andres", "Alberto", "Antonio", "Ignacio", "Esteban", "Eduardo", "Tomas", ""]
APELLIDOS = [
    "Gonzalez", "Munoz", "Rojas", "Diaz", "Perez", "Soto", "Contreras", "Silva",
    "Martinez", "Sepulveda", "Morales", "Rodriguez", "Lopez", "Fuentes", "Hernandez",
    "Torres", "Araya", "Flores", "Espinoza", "Valenzuela", "Castillo", "Ramirez",
    "Reyes", "Gutierrez", "Castro", "Vergara", "Alvarez", "Vasquez", "Tapia",
    "Fernandez", "Riquelme", "Carrasco", "Bravo", "Cortes", "Miranda", "Herrera",
    "Nunez", "Salazar", "Aguilera", "Vega", "Campos", "Pino", "Saavedra", "Cardenas",
    "Quezada", "Navarro", "Yanez", "Poblete", "Figueroa", "Garrido", "Leiva",
]

# (codigo, peso relativo, es_oncologica, es_quirurgica)
# Los pesos siguen los volumenes del informe BCN 2024 citado en documentation.MD 3:
# Oftalmologia y Otorrinolaringologia lideran consultas, Traumatologia lidera cirugia.
ESPECIALIDADES = [
    ("OFTALMOLOGIA", 16, False, False),
    ("OTORRINOLARINGOLOGIA", 12, False, False),
    ("TRAUMATOLOGIA", 14, False, True),
    ("CIRUGIA_DIGESTIVA", 8, False, True),
    ("DERMATOLOGIA", 6, False, False),
    ("NEUROLOGIA", 5, False, False),
    ("CARDIOLOGIA", 5, False, False),
    ("ODONTOLOGIA", 7, False, False),
    ("MEDICINA_INTERNA", 4, False, False),
    ("UROLOGIA", 5, False, True),
    ("GINECOLOGIA", 5, False, True),
    ("CIRUGIA_CARDIOVASCULAR", 3, False, True),
    ("ONCOLOGIA_MEDICA", 10, True, False),
    ("CIRUGIA_MAMA", 7, True, True),
    ("GINECOLOGIA_ONCOLOGICA", 5, True, True),
    ("HEMATO_ONCOLOGIA", 4, True, False),
    ("RADIOTERAPIA", 5, True, False),
]

SERVICIOS = [
    ("SSMO", 18), ("SSMS", 16), ("SSMN", 12), ("SSMOC", 13),
    ("SSVQ", 12), ("SSCONCEPCION", 11), ("SS_ARAUCANIA_SUR", 9), ("SS_LOS_RIOS", 9),
]

DIAGNOSTICOS = {
    "OFTALMOLOGIA": [
        "Catarata senil bilateral con agudeza visual reducida",
        "Glaucoma cronico de angulo abierto en control",
        "Retinopatia diabetica no proliferativa moderada",
        "Pterigion nasal grado III ojo derecho",
    ],
    "OTORRINOLARINGOLOGIA": [
        "Hipoacusia sensorioneural bilateral progresiva",
        "Rinosinusitis cronica con poliposis nasal",
        "Otitis media cronica con perforacion timpanica",
        "Amigdalitis recurrente, indicacion de amigdalectomia",
    ],
    "TRAUMATOLOGIA": [
        "Gonartrosis severa bilateral, indicacion de artroplastia",
        "Coxartrosis derecha con limitacion funcional severa",
        "Hernia del nucleo pulposo L4-L5 con radiculopatia",
        "Sindrome del manguito rotador con ruptura completa",
        "Consolidacion viciosa de fractura de radio distal",
    ],
    "CIRUGIA_DIGESTIVA": [
        "Colelitiasis sintomatica con colicos a repeticion",
        "Hernia inguinal indirecta derecha reductible",
        "Enfermedad por reflujo gastroesofagico refractaria",
        "Hernia incisional post laparotomia media",
    ],
    "DERMATOLOGIA": [
        "Psoriasis en placas extensa sin respuesta a topicos",
        "Lesion pigmentada dorsal en estudio dermatoscopico",
        "Dermatitis atopica severa refractaria",
        "Hidradenitis supurativa axilar Hurley II",
    ],
    "NEUROLOGIA": [
        "Epilepsia focal farmacorresistente en estudio",
        "Cefalea cronica diaria con signos de alarma",
        "Deterioro cognitivo leve en evaluacion",
        "Polineuropatia distal de etiologia no precisada",
    ],
    "CARDIOLOGIA": [
        "Insuficiencia cardiaca con fraccion de eyeccion reducida",
        "Fibrilacion auricular paroxistica en estudio",
        "Estenosis aortica moderada en seguimiento",
        "Angina de esfuerzo estable clase funcional II",
    ],
    "ODONTOLOGIA": [
        "Rehabilitacion oral con protesis removible superior",
        "Periodontitis cronica generalizada avanzada",
        "Terceros molares retenidos con indicacion quirurgica",
        "Caries multiples con compromiso pulpar",
    ],
    "MEDICINA_INTERNA": [
        "Diabetes mellitus tipo 2 descompensada",
        "Hipotiroidismo en ajuste de terapia",
        "Anemia cronica en estudio etiologico",
        "Hipertension arterial refractaria a tres farmacos",
    ],
    "UROLOGIA": [
        "Hiperplasia prostatica benigna con retencion urinaria",
        "Litiasis renal recurrente con indicacion quirurgica",
        "Incontinencia urinaria de esfuerzo severa",
        "Estenosis de uretra bulbar",
    ],
    "GINECOLOGIA": [
        "Miomatosis uterina con metrorragia",
        "Prolapso genital grado III sintomatico",
        "Endometriosis pelvica con dolor cronico",
        "Quiste ovarico persistente en estudio",
    ],
    "CIRUGIA_CARDIOVASCULAR": [
        "Enfermedad coronaria de tres vasos, indicacion de puentes",
        "Aneurisma de aorta abdominal infrarrenal 5,4 cm",
        "Insuficiencia mitral severa sintomatica",
        "Insuficiencia venosa cronica C5 bilateral",
    ],
    "ONCOLOGIA_MEDICA": [
        "Adenocarcinoma gastrico confirmado, evaluacion de quimioterapia",
        "Cancer de pulmon no celulas pequenas en etapificacion",
        "Baja de peso y adenopatias, descartar sindrome linfoproliferativo",
        "Cancer colorrectal operado, evaluacion de adyuvancia",
        "Masa pancreatica en estudio con marcadores elevados",
    ],
    "CIRUGIA_MAMA": [
        "Nodulo mamario BIRADS 4, biopsia pendiente",
        "Carcinoma ductal infiltrante confirmado, cirugia pendiente",
        "Microcalcificaciones agrupadas BIRADS 4B",
        "Recidiva local post mastectomia en estudio",
    ],
    "GINECOLOGIA_ONCOLOGICA": [
        "Lesion intraepitelial de alto grado, conizacion pendiente",
        "Cancer cervicouterino confirmado, etapificacion en curso",
        "Masa anexial sospechosa con CA-125 elevado",
        "Hiperplasia endometrial con atipias",
    ],
    "HEMATO_ONCOLOGIA": [
        "Leucemia mieloide cronica en fase cronica",
        "Linfoma no Hodgkin en etapificacion",
        "Pancitopenia en estudio, mielograma pendiente",
        "Mieloma multiple con lesiones oseas",
    ],
    "RADIOTERAPIA": [
        "Cancer de prostata localizado, radioterapia radical pendiente",
        "Cancer de mama post cirugia, radioterapia adyuvante pendiente",
        "Metastasis oseas dolorosas, radioterapia paliativa",
        "Cancer de cabeza y cuello, tratamiento concomitante",
    ],
}

ETAPIFICACIONES = ["T1N0M0", "T2N0M0", "T2bN1M0", "T3N1M0", "T1cN0M0", "Etapa II", "Etapa IIIA"]


def _elegir_ponderado(rng: random.Random, opciones: list[tuple]) -> tuple:
    """Elige una opcion respetando los pesos relativos."""
    total = sum(o[1] for o in opciones)
    umbral = rng.uniform(0, total)
    acumulado = 0.0
    for opcion in opciones:
        acumulado += opcion[1]
        if umbral <= acumulado:
            return opcion
    return opciones[-1]


def _rut(rng: random.Random, usados: set[int]) -> str:
    """RUT unico con digito verificador valido."""
    while True:
        cuerpo = rng.randint(5_000_000, 25_999_999)
        if cuerpo not in usados:
            usados.add(cuerpo)
            return f"{cuerpo}-{calcular_digito_verificador(cuerpo)}"


def _nombre(rng: random.Random, femenino: bool) -> str:
    """Nombre completo chileno: uno o dos nombres de pila y dos apellidos."""
    primero = rng.choice(NOMBRES_F if femenino else NOMBRES_M)
    segundo = rng.choice(SEGUNDOS_F if femenino else SEGUNDOS_M)
    paterno, materno = rng.sample(APELLIDOS, 2)
    partes = [primero, segundo, paterno, materno] if segundo else [primero, paterno, materno]
    return " ".join(partes)


def _telefono(rng: random.Random) -> str:
    return f"+56 9 {rng.randint(3000, 9999)} {rng.randint(1000, 9999)}"


def generar() -> list[dict[str, str]]:
    """Construye la poblacion completa."""
    rng = random.Random(SEMILLA)
    usados: set[int] = set()
    filas: list[dict[str, str]] = []

    for indice in range(TOTAL_PACIENTES):
        codigo, _, es_onco_esp, es_quirurgica = _elegir_ponderado(rng, ESPECIALIDADES)
        servicio, _ = _elegir_ponderado(rng, SERVICIOS)

        # Coherencia clinica basica: las especialidades del aparato reproductor
        # femenino no reciben pacientes hombres, y Urologia es mayoritariamente
        # masculina en esta poblacion.
        if codigo in {"GINECOLOGIA", "GINECOLOGIA_ONCOLOGICA", "CIRUGIA_MAMA"}:
            femenino = True
        elif codigo == "UROLOGIA":
            femenino = rng.random() < 0.2
        else:
            femenino = rng.random() < 0.54
        nombre = _nombre(rng, femenino)

        es_oncologico = es_onco_esp or (rng.random() < 0.06)

        # La espera del area oncologica es mas corta en terminos absolutos, pero
        # se mide contra plazos mucho mas exigentes.
        if es_onco_esp:
            dias_espera = rng.choice(
                [rng.randint(18, 120), rng.randint(120, 320), rng.randint(320, 640)]
            )
        elif es_quirurgica:
            dias_espera = rng.choice(
                [rng.randint(60, 300), rng.randint(300, 700), rng.randint(700, 1400)]
            )
        else:
            dias_espera = rng.choice(
                [rng.randint(25, 250), rng.randint(250, 620), rng.randint(620, 1100)]
            )

        fecha_ingreso = FECHA_REFERENCIA - timedelta(days=dias_espera)

        # 32% GES, en linea con el peso del regimen garantizado en la red.
        es_ges = rng.random() < 0.32
        regimen = "GES" if es_ges else "NO_GES"

        fecha_expiracion = ""
        if es_ges:
            # El plazo legal se cuenta desde el otorgamiento de la garantia, asi
            # que casi toda garantia antigua nace vencida. Se rescata al 45% de
            # ellas con una reprogramacion hacia adelante para que la muestra
            # tenga tambien garantias vigentes y por vencer, no solo incumplidas.
            plazo_dias = rng.choice([30, 45, 60, 90, 120])
            limite = fecha_ingreso + timedelta(days=plazo_dias)
            if limite < FECHA_REFERENCIA and rng.random() < 0.45:
                limite = FECHA_REFERENCIA + timedelta(days=rng.randint(3, 90))
            fecha_expiracion = limite.isoformat()

        if es_oncologico:
            stage = rng.choices(
                ["SOSPECHA", "DIAGNOSTICO", "TRATAMIENTO", "SEGUIMIENTO"],
                weights=[28, 38, 24, 10],
            )[0]
        elif es_quirurgica:
            stage = rng.choices(
                ["SOSPECHA", "DIAGNOSTICO", "TRATAMIENTO", "SEGUIMIENTO"],
                weights=[8, 34, 48, 10],
            )[0]
        else:
            stage = rng.choices(
                ["SOSPECHA", "DIAGNOSTICO", "TRATAMIENTO", "SEGUIMIENTO"],
                weights=[22, 52, 16, 10],
            )[0]

        # Los examenes se tomaron en algun momento posterior al ingreso, o nunca.
        if rng.random() < 0.08:
            fecha_examenes = ""
        else:
            desde_ingreso = rng.randint(0, max(1, dias_espera))
            fecha_examenes = (fecha_ingreso + timedelta(days=desde_ingreso)).isoformat()

        severidad = rng.choices(["ALTA", "MEDIA", "BAJA"], weights=[26, 48, 26])[0]
        if es_oncologico:
            severidad = rng.choices(["ALTA", "MEDIA"], weights=[78, 22])[0]

        hospitalizado = rng.random() < (0.30 if es_quirurgica or es_oncologico else 0.12)

        edad = rng.randint(19, 89) if not es_oncologico else rng.randint(32, 86)
        nacimiento = FECHA_REFERENCIA - timedelta(days=edad * 365 + rng.randint(0, 364))

        # Datos faltantes: el 14% sin telefono y una parte de los oncologicos sin
        # etapificacion. Son los que la UI marca como informacion incompleta.
        telefono = "" if rng.random() < 0.14 else _telefono(rng)
        etapificacion = ""
        if es_oncologico and stage in {"DIAGNOSTICO", "TRATAMIENTO", "SEGUIMIENTO"}:
            etapificacion = "" if rng.random() < 0.32 else rng.choice(ETAPIFICACIONES)

        estado_rc, fecha_defuncion = "ALIVE", ""
        if indice % 23 == 7:
            # Marcado para verificacion y efectivamente fallecido: la
            # sincronizacion con Registro Civil lo va a purgar.
            estado_rc = "PENDING_VERIFICATION"
            fecha_defuncion = (
                FECHA_REFERENCIA - timedelta(days=rng.randint(20, 400))
            ).isoformat()
        elif indice % 37 == 11:
            # Marcado para verificacion pero vivo: la sincronizacion lo devuelve
            # a la lista activa.
            estado_rc = "PENDING_VERIFICATION"

        filas.append(
            {
                "rut": _rut(rng, usados),
                "nombre_completo": nombre,
                "fecha_nacimiento": nacimiento.isoformat(),
                "regimen": regimen,
                "fecha_expiracion_ges": fecha_expiracion,
                "tipo_paciente": "HOSPITALARIO" if hospitalizado else "AMBULATORIO",
                "especialidad": codigo,
                "stage": stage,
                "health_service_id": servicio,
                "diagnostico": rng.choice(DIAGNOSTICOS[codigo]),
                "fecha_ingreso_lista": fecha_ingreso.isoformat(),
                "fecha_ultimos_examenes": fecha_examenes,
                "es_oncologico": "true" if es_oncologico else "false",
                "severidad_clinica": severidad,
                "estadificacion": etapificacion,
                "telefono_contacto": telefono,
                "estado_registro_civil": estado_rc,
                "fecha_defuncion": fecha_defuncion,
            }
        )

    return filas


def main() -> None:
    filas = generar()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)

    with DESTINO.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)

    oncologicos = sum(1 for f in filas if f["es_oncologico"] == "true")
    ges = sum(1 for f in filas if f["regimen"] == "GES")
    ges_vencidos = sum(
        1
        for f in filas
        if f["fecha_expiracion_ges"]
        and date.fromisoformat(f["fecha_expiracion_ges"]) < FECHA_REFERENCIA
    )
    pendientes = sum(1 for f in filas if f["estado_registro_civil"] == "PENDING_VERIFICATION")
    fallecidos = sum(1 for f in filas if f["fecha_defuncion"])

    print(f"Escrito: {DESTINO}")
    print(f"  pacientes            {len(filas)}")
    print(f"  GES / No GES         {ges} / {len(filas) - ges}")
    print(f"  GES retrasados       {ges_vencidos}")
    print(f"  oncologicos          {oncologicos}")
    print(f"  por verificar en RC  {pendientes} (de ellos {fallecidos} fallecidos)")


if __name__ == "__main__":
    main()
