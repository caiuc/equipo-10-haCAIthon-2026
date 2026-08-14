"""PROCE-SALUD — API de priorizacion dinamica de listas de espera.

Punto de entrada de la aplicacion: siembra la lista desde el CSV al arrancar y
monta los routers bajo /api/v1.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import __version__, config
from .routers import adapters, catalog, patients, waitlist
from .store import store

DESCRIPCION = """
API RESTful open-source (MIT) de priorizacion algoritmica de listas de espera
para el Sistema Nacional de Servicios de Salud de Chile.

Calcula un puntaje continuo 0-100 por paciente combinando cuatro criterios:
espera acumulada contra la mediana y el P75 de su propia especialidad y Servicio,
severidad clinica y garantia legal GES, riesgo oncologico segun el Decreto 18/2026,
y obsolescencia de los examenes diagnosticos.

La capa de adaptadores traduce los formatos de SIDRA, SIGGES, SIGTE y HL7 FHIR a
una entidad canonica unica, de modo que cada Servicio de Salud se conecta sin
cambiar sus sistemas heredados.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga la poblacion inicial antes de atender la primera peticion."""
    if config.SEED_CSV_PATH.exists():
        cargados = store.seed_from_csv(config.SEED_CSV_PATH)
        print(f"[startup] {cargados} pacientes cargados desde {config.SEED_CSV_PATH.name}")
    else:
        print(f"[startup] No se encontro el CSV semilla en {config.SEED_CSV_PATH}")
    yield


app = FastAPI(
    title="PROCE-SALUD API",
    description=DESCRIPCION,
    version=__version__,
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (patients.router, waitlist.router, catalog.router, adapters.router):
    app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def raiz() -> RedirectResponse:
    """La raiz lleva a la documentacion interactiva."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Sistema"], summary="Estado del servicio")
def health() -> dict[str, object]:
    """Healthcheck para el balanceador y para la UI."""
    return {
        "status": "ok",
        "version": __version__,
        "patients_loaded": len(store),
    }
