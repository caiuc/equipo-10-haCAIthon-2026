# Propuesta Técnica y Marco de Integración: API Open-Source (Licencia MIT) de Priorización Dinámica de Listas de Espera (GES y No GES) en el Sistema de Salud Chileno

## 1. Resumen Ejecutivo y Contexto Sanitario

El Sistema Nacional de Servicios de Salud (SNSS) de Chile enfrenta una de las crisis estructurales más severas en materia de oportunidad de atención de salud. La gestión de listas de espera para consultas nuevas de especialidad médica/odontológica e intervenciones quirúrgicas electivas representa un desafío crítico de salud pública, gobernanza de datos e interoperabilidad tecnológica.

La coexistencia de dos regímenes de atención con marcos normativos, mecanismos de financiamiento y sistemas de información diferenciados —las **Garantías Explícitas en Salud (GES / AUGE)** regidas por la Ley 19.966 y monitoreadas vía **SIGGES**, frente al **Régimen No GES** gestionado a través de **SIGTE**— ha generado profundas asimetrías en el acceso, la oportunidad y la equidad en la atención. Mientras que las desviaciones en patologías GES son catalogadas como incumplimientos legales con plazos perentorios, las patologías No GES carecen de garantías explícitas de tiempo, derivando en tiempos de espera medidos en cientos de días.

Adicionalmente, el perfil epidemiológico nacional muestra un aumento sostenido en la incidencia y mortalidad por patologías oncológicas (~28.000 fallecimientos anuales), lo que motivó la dictación del **Decreto N° 18 (abril 2026)** de Alerta Sanitaria Oncológica. Dicho decreto reconoce formalmente la emergencia de salud pública originada por las garantías GES oncológicas retrasadas y la acumulación de pacientes No GES en especialidades del área del cáncer.

Para abordar la atomización y desarticulación de los sistemas informáticos en los 29 Servicios de Salud del país y la heterogeneidad de los repositorios locales conectados al sistema centralizado de agendamiento **SIDRA**, se propone el desarrollo de una **API RESTful open-source (Licencia MIT)** de priorización algorítmica y gestión inteligente de listas de espera. Esta solución incorpora adaptadores flexibles de datos, depuración automatizada con el Registro Civil, evaluación multicriterio de urgencia clínica y temporal, y un tablero UI con indicadores visuales de alerta.

---

## 2. Marco Normativo, Redes Asistenciales y Ciclo de Atención

### 2.1. Estructura de las Redes Asistenciales en Chile
De acuerdo con el modelo de **Redes Integradas de Servicios de Salud (RISS)** impulsado por la Organización Panamericana de la Salud (OPS) e implementado por la Subsecretaría de Redes Asistenciales (DIGERA, 2022), el territorio nacional se organiza en **29 Servicios de Salud**, los cuales operan en distintos niveles de articulación:

*   **Redes Locales (Servicio de Salud):** Integran establecimientos de atención primaria (CESFAM, CECOSF), secundaria (CRS, CDT, Hospitales de Mediana Complejidad) y terciaria (Hospitales de Alta Complejidad) de una misma jurisdicción.
*   **Macrozonas:** Agrupación territorial de Servicios de Salud para compartir oferta de especialidades (Norte, Centro Norte, Centro, Centro Sur, Sur y Extremo Sur).
*   **Macrorredes (Alta Complejidad):** Polos de desarrollo especializado para patologías de baja frecuencia y alta tecnología (Cardiocirugía, Neurocirugía, Oncología, Trasplantes, Neonatología y ECMO).
*   **Redes Ley Ricarte Soto (LRS):** Protección financiera para diagnósticos y tratamientos de alto costo con prestadores acreditados públicos, privados y FFAA.

### 2.2. El Continuo del Paciente en Cuatro Etapas Clínicas
Para el seguimiento operativo en la red y la plataforma SIDRA, todo requerimiento de atención debe ser visibilizado y categorizado transversalmente en cuatro etapas continuas:

```
+-------------------+      +-------------------+      +-------------------+      +-------------------+
|    1. SOSPECHA    | ---> |  2. DIAGNÓSTICO   | ---> |  3. TRATAMIENTO   | ---> |  4. SEGUIMIENTO   |
| (APS / Urgencia)  |      | (Especialidad/CDT)|      | (Cirugía/Onco/etc)|      | (Control Continuo)|
+-------------------+      +-------------------+      +-------------------+      +-------------------+
```

1.  **SOSPECHA:** Identificación inicial del problema de salud en Atención Primaria de Salud (APS) o Unidades de Emergencia Hospitalaria (UEH). Emisión de la orden de derivación o interconsulta.
2.  **DIAGNÓSTICO:** Confirmación o descarte del cuadro clínico mediante evaluación por especialista y exámenes diagnósticos (laboratorio, imagenología, biopsias).
3.  **TRATAMIENTO:** Ejecución del plan terapéutico (intervención quirúrgica, farmacoterapia de alta complejidad, quimioterapia, radioterapia).
4.  **SEGUIMIENTO:** Monitoreo post-tratamiento, controles periódicos, rehabilitación y cuidados paliativos.

### 2.3. Mecanismos de Referencia y Contrarreferencia
El flujo asistencial se sostiene sobre el **Sistema de Referencia y Contrarreferencia**:
*   **Referencia (Derivación):** Solicitud formal de evaluación o tratamiento efectuada por un centro de menor capacidad resolutiva hacia uno de mayor complejidad.
*   **Contrarreferencia (Rescate/Retorno):** Respuesta del especialista al establecimiento de origen con el plan de manejo, o retorno del paciente tras el alta de la atención cerrada.
*   **Gestión de Camas y Urgencias:** Las derivaciones de emergencia crítica se articulan mediante los Gestores de Camas locales y la **Unidad de Gestión Centralizada de Camas (UGCC)** de MINSAL.

### 2.4. Impacto del Decreto 18 (2026): Alerta Sanitaria Oncológica
El Decreto N° 18 faculta a la Subsecretaría de Redes Asistenciales y a los 29 Servicios de Salud para adoptar medidas excepcionales en la resolución de listas de espera oncológicas GES y No GES:
*   **Integración Público-Privada Obligatoria:** Mandata a prestadores privados a otorgar prestaciones bajo precios convenidos regulados en la Licitación **LP 591-3-LR 24** mediante mecanismo **GRD (Grupos Relacionados por el Diagnóstico)** para cirugías, y arancel Fonasa para prestaciones específicas oncológicas.
*   **Flexibilidad de Contratación y Compras:** Exención de licitación pública para adquisición directa de insumos, contratación de personal bajo Art. 10 del Código Sanitario y reincorporación de personal retirado.

---

## 3. Diagnóstico Cuantitativo de Listas de Espera (BCN 2024 vs. Decreto 18/2026)

El análisis comparativo entre los datos del Informe de la Biblioteca del Congreso Nacional (BCN, agosto 2024) y el Decreto N° 18 (abril 2026) evidencia la magnitud de la brecha asistencial en Chile:

### Tabla 1: Comparativa de Datos de Lista de Espera y Garantías Retrasadas

| Indicador Sanitarios | Datos BCN (A Junio 2024) | Datos Decreto 18 (A Diciembre 2025 / 2026) |
| :--- | :--- | :--- |
| **Consultas Nuevas Especialidad No GES** | 2.555.918 registros (2,06M médicas / 490k dental) | Concentración severa en especialidades oncológicas |
| **Intervenciones Quirúrgicas No GES** | 365.257 registros | N/A (Foco en aceleración vía GRD/Privados) |
| **Especialidades Médicas Más Demandadas** | Oftalmología (368k), Otorrinolaringología (260k) | Oncología Médica, Cirugía Mama, Ginecología Onco |
| **Cirugías No GES Más Frecuentes** | Traumatología (82,1k), Cirugía Digestiva (55,1k) | Cirugía Oncológica y Procedimientos Biopsia |
| **Mediana de Espera - Consulta Especialidad** | 255 días | N/A |
| **Mediana de Espera - Cirugía No GES** | 305 días (Traumato: 454 días, Cardiovasc: 415 d) | N/A |
| **Percentil 75 (Casos Extremos) Cirugía** | 579 días (~91.314 pacientes esperando >1.5 años) | N/A (SS Los Ríos registra P75 de 1.214 días) |
| **Garantías GES Retrasadas Totales** | N/A (Tratadas como incumplimiento legal) | 78.594 garantías retrasadas (76.719 personas) |
| **Garantías GES Oncológicas Retrasadas** | N/A | **18.123 garantías** (23,6% del total de retrasos GES) |
| **Consultas Oncológicas No GES en Espera** | N/A | **6.309 registros** (Hemato-onco, Radioterapia, etc.) |
| **Mortalidad Anual por Cáncer en Chile** | N/A | **~28.000 fallecimientos anuales** |

### Criterios de Egreso de Listas de Espera
De acuerdo con las orientaciones de MINSAL y el análisis de la BCN, los egresos de las listas de espera No GES ocurren por tres vías principales:
1.  **Egreso por Atención Resuelta:** Ocurre cuando el paciente recibe efectivamente la consulta, procedimiento o intervención quirúrgica.
2.  **Egreso Administrativo por Fallecimiento:** Retiro del registro tras corroborar el deceso del usuario.
3.  **Egreso Administrativo por Inubicabilidad o Solución Alternativa:** Retiro del paciente tras reiterados intentos fallidos de contacto o constatación de resolución por otra vía (ej. sistema privado independiente).

---

## 4. Arquitectura de Integración e Interoperabilidad (API Open-Source MIT)

### 4.1. Estrategia de Adaptación (Adapter Pattern)
Dada la alta fragmentación de los sistemas informáticos en la red pública de salud chilena —donde coexisten **SIDRA** (sistema de agendamiento), **SIGGES** (garantías GES), **SIGTE** (tiempos de espera No GES) y múltiples **HIS/CDT locales** (Ficha Clínica Electrónica)—, la API adopta el patrón de diseño **Adapter (Adaptador)**.

```
+-----------------------------------------------------------------------------------+
|                                  API RESTful CORE                                 |
|                         (Licencia MIT - Priorización Dinámica)                    |
+-----------------------------------------------------------------------------------+
                                          |
                        +-----------------+-----------------+
                        |  Capa de Adaptadores Intercambiables |
                        +-----------------+-----------------+
                                          |
         +--------------------+-----------+-----------+--------------------+
         |                    |                       |                    |
+-----------------+  +-----------------+     +-----------------+  +-----------------+
| Adaptador SIDRA |  | Adaptador SIGGES|     | Adaptador SIGTE |  | Adaptador HIS   |
| (Agendamiento)  |  |  (Garantías)    |     |  (Lista No GES) |  | Local / FHIR    |
+-----------------+  +-----------------+     +-----------------+  +-----------------+
```

La arquitectura desacopla el motor de reglas y scoring del modelo de datos de origen mediante adaptadores reutilizables. Cada adaptador implementa una interfaz genérica `PatientRecordAdapter`, convirtiendo estructuras JSON/XML heterogéneas a una entidad canónica estandarizada.

### 4.2. Definición de Endpoints de la API

La API sigue los principios RESTful y entrega respuestas codificadas en JSON.

#### Endpoint 1: Obtención de Puntaje Individual y Desglose Paramétrico
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/patients/{patient_id}/score`
*   **Query Parameters:**
    *   `breakdown` (boolean, opcional, default `false`): Si es `true`, retorna el desglose detallado de los factores que componen el puntaje.
    *   `adapter` (string, opcional): Especifica el adaptador de datos a utilizar (ej. `sidra`, `sigges`, `sigte`, `fhir`).

*   **Ejemplo de Respuesta (`GET /api/v1/patients/CL-18492041-K/score?breakdown=true`):**

```json
{
  "patient_id": "CL-18492041-K",
  "national_id": "18492041-K",
  "regimen": "NO_GES",
  "stage": "DIAGNOSTICO",
  "specialty": "ONCOLOGIA_MEDICA",
  "health_service_id": "SSMO",
  "total_score": 87.45,
  "priority_level": "ALTA_PRIORIDAD",
  "flags": {
    "is_oncologic": true,
    "is_ancient_patient": true,
    "incomplete_info": false,
    "civil_registry_status": "ALIVE"
  },
  "breakdown": {
    "time_waiting_score": 35.20,
    "clinical_severity_score": 30.00,
    "oncologic_risk_score": 15.00,
    "diagnostic_validity_penalty": 7.25
  },
  "metadata": {
    "days_waiting": 312,
    "regional_median_days": 255,
    "exams_expired": true,
    "last_evaluation_date": "2023-11-10T14:30:00Z",
    "calculated_at": "2026-08-14T15:00:00Z"
  }
}
```

#### Endpoint 2: Obtención de Lista de Espera Priorizada
*   **HTTP Method:** `GET`
*   **Path:** `/api/v1/waitlist`
*   **Query Parameters:**
    *   `health_service` (string, opcional): Filtro por Servicio de Salud (ej. `SSMO`, `SSRíos`).
    *   `specialty` (string, opcional): Filtro por especialidad (ej. `TRAUMATOLOGIA`, `ONCOLOGIA`).
    *   `regimen` (string, opcional): `GES`, `NO_GES` o `ALL`.
    *   `stage` (string, opcional): `SOSPECHA`, `DIAGNOSTICO`, `TRATAMIENTO`, `SEGUIMIENTO`.
    *   `order` (string, default `priority_desc`): Criterio de ordenamiento.
    *   `limit` (integer, default `50`): Paginación.
    *   `page` (integer, default `1`).

*   **Ejemplo de Respuesta (`GET /api/v1/waitlist?health_service=SSMO&regimen=NO_GES&limit=2`):**

```json
{
  "total_records": 1240,
  "page": 1,
  "limit": 2,
  "data": [
    {
      "patient_id": "CL-12940112-3",
      "full_name": "María Transitada Perez",
      "specialty": "CIRUGIA_MAMA",
      "stage": "DIAGNOSTICO",
      "days_waiting": 410,
      "priority_score": 94.10,
      "flags": {
        "is_oncologic": true,
        "is_ancient_patient": true,
        "incomplete_info": false
      }
    },
    {
      "patient_id": "CL-15022931-8",
      "full_name": "Juan Carlos Soto",
      "specialty": "TRAUMATOLOGIA",
      "stage": "TRATAMIENTO",
      "days_waiting": 590,
      "priority_score": 88.30,
      "flags": {
        "is_oncologic": false,
        "is_ancient_patient": true,
        "incomplete_info": false
      }
    }
  ]
}
```

#### Endpoint 3: Depuración y Verificación con Registro Civil
*   **HTTP Method:** `POST`
*   **Path:** `/api/v1/waitlist/sync-civil-registry`
*   **Request Body:**

```json
{
  "batch_size": 500,
  "auto_purge_deceased": true,
  "health_service_id": "SSMO"
}
```

*   **Ejemplo de Respuesta:**

```json
{
  "processed_records": 500,
  "alive_records": 488,
  "purged_deceased_records": 12,
  "purged_patients": [
    {
      "patient_id": "CL-8392019-4",
      "date_of_death": "2026-02-14",
      "purged_reason": "EGRESO_ADMINISTRATIVO_FALLECIMIENTO"
    }
  ],
  "synced_at": "2026-08-14T15:05:00Z"
}
```

---

## 5. Modelo Algorítmico de Scoring y Priorización Dinámica

El modelo de priorización asigna una puntuación continua $P \in [0, 100]$ a cada paciente en espera. El cálculo combina criterios temporales, severidad clínica, riesgo oncológico y caducidad diagnóstica:

$$	ext{Puntaje Total} = W_T \cdot S_{	ext{tiempo}} + W_C \cdot S_{	ext{clínico}} + W_O \cdot S_{	ext{oncológico}} + W_V \cdot S_{	ext{vencimiento}}$$

Donde la suma de ponderaciones cumple $\sum W_i = 1.0$.

### 5.1. Componentes del Scoring Algorítmico

1.  **Puntaje por Tiempo Acumulado ($S_{	ext{tiempo}}$):**
    Evalúa la espera efectiva del paciente ($D_{	ext{espera}}$) ajustada a la mediana regional de tiempo de espera ($M_{	ext{región}}$) y al percentil 75 ($P75_{	ext{región}}$) de la especialidad correspondiente:
    $$S_{	ext{tiempo}} = \min\left(100, \left( rac{D_{	ext{espera}}}{M_{	ext{región}}} 	imes 50 
ight) + \left( rac{D_{	ext{espera}}}{P75_{	ext{región}}} 	imes 30 
ight) 
ight)$$

2.  **Puntaje por Severidad Clínica y Garantía Legal ($S_{	ext{clínico}}$):**
    *   **GES Retrasado:** 100 puntos inmediatos (por incumplimiento de garantía legal de oportunidad).
    *   **No GES Alta Complejidad / Riesgo Funcional / Dolor Severo:** 70 - 90 puntos.
    *   **No GES Electivo Estándar:** 30 - 50 puntos.

3.  **Puntaje por Riesgo Oncológico ($S_{	ext{oncológico}}$):**
    Aplicación de las directrices del **Decreto N° 18 (2026)**.
    *   Patología Oncológica Confirmada o Sospecha de Alta Malignidad (Etapas Sospecha/Diagnóstico): 100 puntos.
    *   Especialidades críticas (Oncología Médica, Hemato-oncología Pediátrica, Ginecología Oncológica, Cirugía de Mama, Radioterapia): Multiplicador de sesgo $+25\%$.

4.  **Penalización por Obsolescencia / "Paciente Antiguo" ($S_{	ext{vencimiento}}$):**
    Si la espera supera la validez clínica de exámenes preoperatorios o imágenes diagnósticas (>6 a 12 meses):
    *   Se suma un factor de riesgo extra (+15 a +20 puntos) por la necesidad imperiosa de **repetir exámenes**, evitando que el paciente quede varado en un bucle administrativo.

---

## 6. Diseño de Interfaz de Usuario (UI Simple) e Indicadores Visuales

La interfaz web (Dashboard) está diseñada de manera austera y limpia para coordinadores de red y administrativos de SOME/agendamiento.

### 6.1. Badges e Indicadores de Estado
Cada paciente en la lista incluye insignias de alerta visual claramente diferenciadas:

*   🔴 **`ONCOLÓGICO / DECRETO 18`:** Alerta sanitaria oncológica. Prioridad máxima de agendamiento.
*   🟠 **`PACIENTE ANTIGUO (Repetir Exámenes)`:** Indica que el paciente supera los 300 días de espera y sus exámenes diagnósticos de laboratorio/imagen están vencidos. Requiere reevaluación rápida.
*   🟡 **`INFORMACIÓN INCOMPLETA`:** Faltan variables clínicas críticas (ej. sin estadificación o sin contacto telefónico actualizado). Bloquea la asignación definitiva hasta completar ficha.
*   🔵 **`GES RETRASADO`:** Garantía legal de oportunidad vencida (notificación a SIGGES).
*   ⚪ **`NO GES ESTÁNDAR`:** Espera dentro de márgenes normales.
*   💀 **`VERIFICANDO REGISTRO CIVIL`:** Paciente en proceso de depuración por fallecimiento.

### 6.2. Mockup de Interfaz de Lista Ordenada (Vista Dashboard)

```
====================================================================================================
  SISTEMA CENTRALIZADO DE PRIORIZACIÓN DE LISTAS DE ESPERA (API SIDRA ADAPTER v1.0)
  Servicio de Salud Metropolitano Oriente (SSMO) | Alerta Sanitaria Activa (Decreto 18)
====================================================================================================

  Filtros: [ Todos los Servicios v ] [ No GES v ] [ Etapa: Diagnóstico v ] [ Buscar por RUT... ]

----------------------------------------------------------------------------------------------------
  PRIORIDAD | RUT / PACIENTE       | ESPECIALIDAD / ETAPA   | DÍAS | PUNTAJE | INDICADORES / ALERTAS
----------------------------------------------------------------------------------------------------
    #1      | 12.940.112-3         | Cirugía de Mama        |  410 |  94.10  | [🔴 ONCOLÓGICO] 
            | Transitada Perez, M. | DIAGNÓSTICO            |      |         | [🟠 PACIENTE ANTIGUO]
----------------------------------------------------------------------------------------------------
    #2      | 18.492.041-K         | Oncología Médica       |  312 |  87.45  | [🔴 ONCOLÓGICO]
            | Morales Silva, J.    | SOSPECHA               |      |         | [🟡 INFO INCOMPLETA]
----------------------------------------------------------------------------------------------------
    #3      | 15.022.931-8         | Traumatología          |  590 |  88.30  | [🔵 NO GES]
            | Soto Soto, C.        | TRATAMIENTO (Cirugía)  |      |         | [🟠 PACIENTE ANTIGUO]
----------------------------------------------------------------------------------------------------
    #4      | 9.382.102-4          | Ginecología Oncológica |   68 |  82.15  | [🔴 ONCOLÓGICO]
            | Gómez Rojas, A.      | DIAGNÓSTICO            |      |         | [🔵 GES RETRASADO]
----------------------------------------------------------------------------------------------------

  Acciones Globales:
  [ 🔄 Sincronizar con Registro Civil ]   [ 📥 Exportar CSV Priorizado ]   [ ⚙️ Configurar Adaptador SIDRA ]
====================================================================================================
```

---

## 7. Matriz de Interrelación entre la Documentación y la Propuesta

A continuación se sintetizan las relaciones clave entre los documentos analizados y la API planteada:

```
+------------------------------------+       +------------------------------------+
|          DOCUMENTO BCN 2024        |       |        DECRETO N° 18 (2026)        |
| - 2.55M Consultas No GES           |       | - Alerta Sanitaria Oncológica      |
| - 365k Cirugías No GES             |       | - 18.123 Garantías GES Retrasadas  |
| - Mediana 255/305 días             |       | - 6.309 Consultas Onco No GES      |
| - P75 = 579 días (Casos Extremos)  |       | - Compras directas + Convenio GRD  |
+------------------------------------+       +------------------------------------+
                  \                                     /
                   \                                   /
                    v                                 v
+---------------------------------------------------------------------------------+
|                       PROPUESTA DE API Y SISTEMA DE PRIORIZACIÓN                 |
| - Algoritmo de Scoring Dinámico (Variables: Días vs Mediana/P75 + Onco + GES)   |
| - Interfaz Adaptadora MIT (Interoperabilidad con SIDRA, SIGGES y SIGTE)         |
| - Depuración Automatizada con Registro Civil (Eliminación de Sesgos/Fallecidos) |
| - Tablero Visual UI con Indicadores (Paciente Antiguo, Info Incompleta, Cáncer) |
+---------------------------------------------------------------------------------+
                    ^                                 ^
                   /                                                     /                                     +------------------------------------+       +------------------------------------+
|        REDES DIGERA / GES 2022     |       |          PROMPT & SIDRA             |
| - RISS: 29 Servicios de Salud      |       | - Sistema de Agendamiento Minsal   |
| - Macrorredes y Macrozonas         |       | - 4 Etapas: Sospecha, Diagnóstico, |
| - Flujos Referencia/Contrarrefer.  |       |   Tratamiento, Seguimiento.        |
| - Guías Clínicas DIPRECE           |       | - Flexibilidad / Adaptadores MIT   |
+------------------------------------+       +------------------------------------+
```

### Tabla 2: Matriz Cruzada de Puntos de Contacto e Integración

| Fuente / Documento | Concepto Clave Extraído | Problema o Restricción Identificada | Solución Técnica Implementada en la API |
| :--- | :--- | :--- | :--- |
| **BCN (2024)** | Métrica de Mediana y Percentil 75 por Servicio de Salud. | Asimetrías regionales extremas (ej. SS Los Ríos con P75 > 3 años). | El algoritmo calcula el score dividiendo los días del paciente por la mediana y P75 de su propio Servicio de Salud. |
| **BCN (2024)** | Criterio de egreso por fallecimiento (Egreso Administrativo). | Registros "fantasma" que abultan las listas y distorsionan la demanda real. | Endpoint `/sync-civil-registry` para cruzamiento automático con el Registro Civil y purga programada. |
| **Decreto 18 (2026)** | Alerta Sanitaria por urgencia oncológica No GES y GES retrasado. | Riesgo vital por retraso en oportunidad diagnóstica y terapéutica (~28k muertes/año). | Multiplicador directo de scoring (+25% a +100%) para patologías oncológicas en etapas de Sospecha/Diagnóstico. |
| **Redes DIGERA (2022)** | Estructura RISS, Macrorredes y Referencia/Contrarreferencia. | Desarticulación entre prestadores primarios, secundarios y macrorredes terciarias. | Mapeo explícito de derivación por Servicio de Salud y tipo de cáncer en el adaptador de la API. |
| **Prompt & SSMO** | Seguimiento transversal en 4 etapas (Sospecha, Diag, Trat, Seg). | Falta de visibilidad de en qué etapa exacta el paciente está estancado. | Atributo obligatorio `stage` en la entidad canónica y diferenciación de prioridad según etapa. |
| **Prompt & SIDRA** | Heterogeneidad de sistemas informáticos en los Servicios. | Imposibilidad de imponer una base de datos única a nivel nacional. | Arquitectura basada en **Adapter Pattern** bajo licencia **MIT**, permitiendo conectores personalizados. |

---

## 8. Conclusiones y Hoja de Ruta para la Implementación

1.  **Resolución de la Fragmentación Informática:** La creación de una API abierta con **licencia MIT** proporciona una capa de abstracción neutral. Esto permite a los 29 Servicios de Salud integrar sus plataformas informáticas locales y SIDRA sin necesidad de reemplazar sus sistemas heredados (*legacy*).
2.  **Priorización Objetiva y Equitativa:** Al combinar las garantías GES retrasadas del **Decreto 18** con las métricas de variabilidad regional del reporte de la **BCN (2024)**, el sistema evita la arbitrariedad en la asignación de horas médicas y quirúrgicas.
3.  **Transparencia Asistencial y Calidad de Datos:** La funcionalidad de depuración con el Registro Civil limpia las listas de espera reales, reduciendo el volumen ficticio y permitiendo enfocar los recursos extraordinarios liberados por la Alerta Sanitaria en los pacientes de mayor riesgo relativo.
4.  **Sostenibilidad y Mantenibilidad:** La arquitectura por adaptadores garantiza que la herramienta pueda actualizarse conforme se promulguen nuevos Decretos GES (actualización trienal) o cambien los protocolos de derivación de los Servicios de Salud.