<h1 align="center">PROCE·SALUD</h1>

<p align="center">
  <strong>Priorización dinámica de listas de espera para la red pública de salud chilena.</strong><br>
  Un puntaje objetivo, auditable y open-source para decidir a quién se atiende primero.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/licencia-MIT-0E1F23?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/API-FastAPI-1F5F8B?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/UI-React_+_Vite-1F5F8B?style=flat-square" alt="React">
  <img src="https://img.shields.io/badge/Decreto_18-Alerta_oncológica-C8352C?style=flat-square" alt="Decreto 18">
</p>

---

## El problema

| | |
|---:|:---|
| **2.555.918** | personas esperan una consulta nueva de especialidad |
| **255 días** | mediana de espera — 305 en cirugía, P75 de 579 |
| **18.123** | garantías GES oncológicas retrasadas (Decreto N° 18, 2026) |
| **~28.000** | muertes por cáncer al año en Chile |

Los 29 Servicios de Salud operan sistemas desconectados —SIDRA, SIGGES, SIGTE y fichas clínicas
locales— y no existe un criterio común para ordenar la espera. Hoy la decisión de a quién agendar
primero depende de cada equipo.

## Qué hace el sistema

PROCE-SALUD asigna a cada persona en espera un **puntaje continuo de 0 a 100** y ordena la lista con
él. El puntaje es explicable: siempre se puede desglosar en los cuatro factores que lo produjeron.

```
Puntaje = 0.35 · Tiempo  +  0.30 · Severidad  +  0.20 · Oncológico  +  0.15 · Vencimiento
```

| Componente | Qué mide |
|---|---|
| **Tiempo** | Días esperando ÷ la mediana y el P75 **de su propia especialidad y Servicio**. 400 días en Radioterapia no son 400 días en Traumatología. |
| **Severidad** | Severidad clínica declarada, o 100 puntos si la garantía GES está vencida (incumplimiento de la Ley 19.966). |
| **Oncológico** | Decreto 18/2026: máximo en sospecha y diagnóstico, con sesgo de +25% en las especialidades críticas del área del cáncer. |
| **Vencimiento** | Castigo por exámenes caducados, para que nadie quede varado repitiendo trámites. |

Además: **depura la lista contra el Registro Civil**, retirando a quienes fallecieron y dejan de ser
demanda real; y **traduce cuatro formatos de origen distintos** a una entidad canónica, de modo que
cada Servicio se conecta sin cambiar sus sistemas heredados.

## Indicadores visuales

| | Insignia | Significa |
|---|---|---|
| 🔴 | `ONCOLÓGICO · DECRETO 18` | Alerta sanitaria vigente. Prioridad máxima de agendamiento. |
| 🔵 | `GES RETRASADO` | Garantía legal de oportunidad vencida. Notificar a SIGGES. |
| 🟠 | `PACIENTE ANTIGUO` | Más de 300 días esperando y exámenes vencidos. Hay que repetirlos. |
| 🟡 | `INFO INCOMPLETA` | Faltan datos críticos. Bloquea la asignación definitiva. |
| 💀 | `VERIFICANDO REGISTRO CIVIL` | En proceso de depuración por fallecimiento. |
| ⚪ | `NO GES ESTÁNDAR` | Espera dentro de los márgenes de su especialidad. |

## Arquitectura

```
        ┌──────────────────────────────────────────────┐
        │  UI React · Login · Ficha · Tablero          │
        └───────────────────────┬──────────────────────┘
                                │ REST /api/v1
        ┌───────────────────────┴──────────────────────┐
        │  API FastAPI · Motor de puntaje y depuración │
        └───────────────────────┬──────────────────────┘
                                │
        ┌───────────────────────┴──────────────────────┐
        │  Capa de adaptadores → entidad canónica      │
        └──┬─────────┬──────────┬──────────┬───────────┘
           │         │          │          │
         SIDRA    SIGGES     SIGTE    HL7 FHIR / HIS local
```

Cada adaptador implementa `PatientRecordAdapter` y traduce su propio esquema. El motor de puntaje
nunca sabe de qué sistema vino un registro. Conectar uno nuevo es escribir una subclase.

## Endpoints

| | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/v1/waitlist` | Ranking paginado con filtros y ordenamiento |
| `GET` | `/api/v1/patients/{id}/score?breakdown=true` | Puntaje individual con desglose |
| `POST` | `/api/v1/waitlist/sync-civil-registry` | Depuración contra el Registro Civil |
| `GET` | `/api/v1/patients/{rut}` | Ficha completa del paciente |
| `POST` | `/api/v1/patients` | Alta en la lista de espera |
| `PUT` | `/api/v1/patients/{rut}/clinical-status` | Actualizar estado y recalcular |
| `GET` | `/api/v1/waitlist/export` | CSV priorizado |
| `GET` | `/api/v1/stats` · `/api/v1/catalog` | Indicadores y catálogos |
| `GET` | `/api/v1/adapters` · `POST` `/api/v1/adapters/{name}/ingest` | Interoperabilidad |

Documentación interactiva completa en `/docs`.

## Correrlo local

```bash
# API — http://127.0.0.1:8000/docs
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# UI — http://localhost:5173
cd frontend
npm install
npm run dev
```

El acceso es simulado: **cualquier usuario y contraseña entran**.

## Datos

`backend/data/pacientes_seed.csv` contiene 140 pacientes sintéticos que la API carga en memoria al
arrancar. Los RUT tienen dígito verificador válido —la API los valida por módulo 11— pero ninguna
combinación corresponde a una persona real. Se regenera con:

```bash
python backend/scripts/generar_semilla.py
```

## Decisiones del MVP

- **Persistencia en memoria.** Los cambios se pierden al reiniciar. Es deliberado: el despliegue de
  demostración no tiene disco persistente, y volver a un estado limpio y conocido en cada
  presentación es preferible a arrastrar ediciones. Cambiar `store.py` por una implementación con
  Postgres no obliga a tocar el resto.
- **Sin autenticación.** No hay datos que proteger. El login existe para mostrar el flujo, y CORS
  está abierto por la misma razón.
- **`CRÍTICA` es un tramo mayoritariamente oncológico.** No es un defecto de calibración: es la
  política del Decreto 18 hecha número. Un caso no oncológico llega como máximo a 80 puntos.
- **Los RUT de ejemplo de la documentación original no pasan la validación** de módulo 11. Los
  ejemplos de `/docs` usan versiones con el dígito corregido.

## Licencia

MIT. La fragmentación informática de la red pública no se resuelve con una plataforma cerrada más:
cualquier Servicio de Salud puede tomar este código, escribir su propio adaptador y usarlo.
