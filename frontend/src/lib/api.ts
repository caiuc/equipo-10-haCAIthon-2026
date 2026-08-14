/** Cliente HTTP de la API de PROCE-SALUD. */

import type {
  Catalog,
  ClinicalStatusUpdate,
  PatientCreate,
  PatientDetail,
  Stats,
  SyncResult,
  WaitlistFilters,
  WaitlistResponse,
} from './types'

// En produccion la URL de la API llega por variable de entorno del build. En
// desarrollo queda vacia y el proxy de Vite redirige /api al backend local.
const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function url(path: string, params?: Record<string, string | number | boolean | undefined>): string {
  const query = new URLSearchParams()
  for (const [clave, valor] of Object.entries(params ?? {})) {
    if (valor !== undefined && valor !== '' && valor !== 'ALL') {
      query.set(clave, String(valor))
    }
  }
  const cadena = query.toString()
  return `${BASE}/api/v1${path}${cadena ? `?${cadena}` : ''}`
}

async function request<T>(destino: string, init?: RequestInit): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(destino, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(
      'No se pudo contactar la API. Revisa que el servicio este arriba y vuelve a intentar.',
      0,
    )
  }

  if (!respuesta.ok) {
    // FastAPI devuelve el motivo en `detail`, que a veces es texto y a veces la
    // lista de errores de validacion de Pydantic.
    let detalle = `La API respondio ${respuesta.status}.`
    try {
      const cuerpo = await respuesta.json()
      if (typeof cuerpo.detail === 'string') {
        detalle = cuerpo.detail
      } else if (Array.isArray(cuerpo.detail)) {
        detalle = cuerpo.detail
          .map((e: { loc?: string[]; msg?: string }) => `${e.loc?.slice(-1)[0] ?? ''}: ${e.msg}`)
          .join(' · ')
      }
    } catch {
      /* sin cuerpo JSON: se usa el mensaje generico */
    }
    throw new ApiError(detalle, respuesta.status)
  }

  return respuesta.json() as Promise<T>
}

export const api = {
  getCatalog: () => request<Catalog>(url('/catalog')),

  getStats: (healthService?: string) =>
    request<Stats>(url('/stats', { health_service: healthService })),

  getWaitlist: (filtros: WaitlistFilters) =>
    request<WaitlistResponse>(
      url('/waitlist', {
        specialty: filtros.specialty,
        patient_type: filtros.patient_type,
        regimen: filtros.regimen,
        stage: filtros.stage,
        health_service: filtros.health_service,
        q: filtros.q,
        order: filtros.order,
        page: filtros.page,
        limit: filtros.limit,
      }),
    ),

  getPatient: (rut: string) => request<PatientDetail>(url(`/patients/${encodeURIComponent(rut)}`)),

  createPatient: (datos: PatientCreate) =>
    request<PatientDetail>(url('/patients'), {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  updateClinicalStatus: (rut: string, cambios: ClinicalStatusUpdate) =>
    request<PatientDetail>(url(`/patients/${encodeURIComponent(rut)}/clinical-status`), {
      method: 'PUT',
      body: JSON.stringify(cambios),
    }),

  syncCivilRegistry: () =>
    request<SyncResult>(url('/waitlist/sync-civil-registry'), {
      method: 'POST',
      body: JSON.stringify({ batch_size: 500, auto_purge_deceased: true }),
    }),

  /** URL de descarga del CSV priorizado, con los filtros vigentes aplicados. */
  exportUrl: (filtros: WaitlistFilters) =>
    url('/waitlist/export', {
      specialty: filtros.specialty,
      patient_type: filtros.patient_type,
      regimen: filtros.regimen,
      stage: filtros.stage,
      health_service: filtros.health_service,
      q: filtros.q,
      order: filtros.order,
    }),
}
