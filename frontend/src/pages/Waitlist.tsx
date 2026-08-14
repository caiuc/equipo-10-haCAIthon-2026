/**
 * Lista de espera priorizada.
 *
 * Cumple lo que pide UI.MD: ranking por puntaje, filtros por especialidad y
 * tipo de paciente, vista de solo GES o solo No GES, ordenamiento por puntaje y
 * por fecha de expiracion en ambas direcciones, y paginado de 10, 20 o 30.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { FlagBadges } from '../components/Badge'
import { WaitRuler } from '../components/WaitRuler'
import { api, ApiError } from '../lib/api'
import {
  PRIORITY_COLOR,
  PRIORITY_LABEL,
  STAGE_LABEL,
  daysUntil,
  formatDate,
  formatNumber,
  formatRut,
} from '../lib/format'
import type {
  Catalog,
  SyncResult,
  WaitlistFilters,
  WaitlistItem,
  WaitlistOrder,
  WaitlistResponse,
} from '../lib/types'

const FILTROS_INICIALES: WaitlistFilters = {
  specialty: 'ALL',
  patient_type: 'ALL',
  regimen: 'ALL',
  stage: 'ALL',
  health_service: 'ALL',
  q: '',
  order: 'priority_desc',
  page: 1,
  limit: 20,
}

const ORDENES: { value: WaitlistOrder; label: string }[] = [
  { value: 'priority_desc', label: 'Puntaje: mayor a menor' },
  { value: 'priority_asc', label: 'Puntaje: menor a mayor' },
  { value: 'expiration_asc', label: 'Expiración: más próxima' },
  { value: 'expiration_desc', label: 'Expiración: más lejana' },
  { value: 'days_desc', label: 'Días de espera: mayor a menor' },
  { value: 'days_asc', label: 'Días de espera: menor a mayor' },
]

export function Waitlist() {
  const [filtros, setFiltros] = useState<WaitlistFilters>(FILTROS_INICIALES)
  const [busqueda, setBusqueda] = useState('')
  const [catalogo, setCatalogo] = useState<Catalog | null>(null)
  const [datos, setDatos] = useState<WaitlistResponse | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sync, setSync] = useState<SyncResult | null>(null)
  const [sincronizando, setSincronizando] = useState(false)

  const listaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.getCatalog().then(setCatalogo).catch(() => undefined)
  }, [])

  // El texto de busqueda se aplica con retardo para no disparar una consulta
  // por cada tecla, y siempre vuelve a la primera pagina.
  useEffect(() => {
    const temporizador = setTimeout(() => {
      setFiltros((f) => (f.q === busqueda ? f : { ...f, q: busqueda, page: 1 }))
    }, 300)
    return () => clearTimeout(temporizador)
  }, [busqueda])

  useEffect(() => {
    let vigente = true
    setCargando(true)
    api
      .getWaitlist(filtros)
      .then((d) => {
        if (!vigente) return
        setDatos(d)
        setError(null)
      })
      .catch((e: unknown) => {
        if (!vigente) return
        setError(e instanceof ApiError ? e.message : 'No se pudo cargar la lista de espera.')
      })
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [filtros])

  const actualizar = useCallback((cambios: Partial<WaitlistFilters>) => {
    // Cualquier cambio de filtro invalida la pagina actual: quedarse en la
    // pagina 7 de un resultado que ahora tiene 2 muestra una lista vacia.
    setFiltros((f) => ({ ...f, ...cambios, page: cambios.page ?? 1 }))
  }, [])

  const irAPagina = useCallback((page: number) => {
    setFiltros((f) => ({ ...f, page }))
    listaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  async function sincronizarRegistroCivil() {
    setSincronizando(true)
    try {
      const resultado = await api.syncCivilRegistry()
      setSync(resultado)
      setFiltros((f) => ({ ...f }))
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No se pudo sincronizar con el Registro Civil.')
    } finally {
      setSincronizando(false)
    }
  }

  const hayFiltros = useMemo(
    () =>
      filtros.specialty !== 'ALL' ||
      filtros.patient_type !== 'ALL' ||
      filtros.regimen !== 'ALL' ||
      filtros.stage !== 'ALL' ||
      filtros.health_service !== 'ALL' ||
      filtros.q !== '',
    [filtros],
  )

  return (
    <div>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Tablero de priorización</p>
          <h1 className="mt-1 font-display text-[26px] leading-none font-bold tracking-[-0.02em] sm:text-[30px]">
            Lista de espera
          </h1>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={sincronizarRegistroCivil}
            disabled={sincronizando}
          >
            {sincronizando ? 'Sincronizando…' : 'Sincronizar Registro Civil'}
          </button>
          <a className="btn btn-primary" href={api.exportUrl(filtros)}>
            Exportar CSV priorizado
          </a>
        </div>
      </header>

      {sync && (
        <div
          className="mt-4 border-l-2 bg-surface px-4 py-3"
          style={{ borderColor: 'var(--color-registro)' }}
          role="status"
        >
          <p className="font-display text-[11px] font-bold tracking-[0.08em] uppercase">
            Depuración con Registro Civil
          </p>
          <p className="mt-1 text-[13px] text-ink-soft">
            {formatNumber(sync.processed_records)} registros procesados ·{' '}
            {formatNumber(sync.alive_records)} vigentes ·{' '}
            <strong className="font-semibold text-ink">
              {formatNumber(sync.purged_deceased_records)} egresos administrativos por
              fallecimiento
            </strong>
            .
          </p>
          {sync.purged_patients.length > 0 && (
            <ul className="mt-2 space-y-0.5">
              {sync.purged_patients.slice(0, 4).map((p) => (
                <li key={p.patient_id} className="tabular text-[11.5px] text-ink-faint">
                  {formatRut(p.patient_id.replace(/^CL-/, ''))} · {p.full_name} · defunción{' '}
                  {formatDate(p.date_of_death)}
                </li>
              ))}
              {sync.purged_patients.length > 4 && (
                <li className="text-[11.5px] text-ink-faint">
                  y {sync.purged_patients.length - 4} más.
                </li>
              )}
            </ul>
          )}
          <button
            type="button"
            className="mt-2 font-display text-[10px] font-bold tracking-[0.08em] text-ink-faint uppercase underline underline-offset-3 hover:text-ink"
            onClick={() => setSync(null)}
          >
            Cerrar
          </button>
        </div>
      )}

      {/* Filtros */}
      <section
        className="mt-5 border border-rule bg-surface p-4"
        aria-label="Filtros de la lista de espera"
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Campo etiqueta="Especialidad" id="f-especialidad">
            <select
              id="f-especialidad"
              className="field"
              value={filtros.specialty}
              onChange={(e) => actualizar({ specialty: e.target.value })}
            >
              <option value="ALL">Todas las especialidades</option>
              {catalogo?.specialties.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </Campo>

          <Campo etiqueta="Tipo de paciente" id="f-tipo">
            <select
              id="f-tipo"
              className="field"
              value={filtros.patient_type}
              onChange={(e) => actualizar({ patient_type: e.target.value })}
            >
              <option value="ALL">Ambulatorios y hospitalizados</option>
              <option value="AMBULATORIO">Solo ambulatorios</option>
              <option value="HOSPITALARIO">Solo hospitalizados</option>
            </select>
          </Campo>

          <Campo etiqueta="Servicio de Salud" id="f-servicio">
            <select
              id="f-servicio"
              className="field"
              value={filtros.health_service}
              onChange={(e) => actualizar({ health_service: e.target.value })}
            >
              <option value="ALL">Todos los servicios</option>
              {catalogo?.health_services.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </Campo>

          <Campo etiqueta="Etapa" id="f-etapa">
            <select
              id="f-etapa"
              className="field"
              value={filtros.stage}
              onChange={(e) => actualizar({ stage: e.target.value })}
            >
              <option value="ALL">Todas las etapas</option>
              {catalogo?.stages.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </Campo>

          <Campo etiqueta="Buscar por RUT o nombre" id="f-busqueda">
            <input
              id="f-busqueda"
              className="field"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="12.345.678-9 o apellido"
              type="search"
            />
          </Campo>

          <Campo etiqueta="Ordenar por" id="f-orden">
            <select
              id="f-orden"
              className="field"
              value={filtros.order}
              onChange={(e) => actualizar({ order: e.target.value as WaitlistOrder })}
            >
              {ORDENES.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </Campo>

          {/* El regimen se maneja como conmutador y no como desplegable: es el
              corte que el coordinador cambia mas seguido. */}
          <Campo etiqueta="Régimen" id="f-regimen">
            <div className="flex" role="group" id="f-regimen">
              {[
                { value: 'ALL', label: 'Todos' },
                { value: 'GES', label: 'GES' },
                { value: 'NO_GES', label: 'No GES' },
              ].map((opcion, indice) => {
                const activo = filtros.regimen === opcion.value
                return (
                  <button
                    key={opcion.value}
                    type="button"
                    aria-pressed={activo}
                    onClick={() => actualizar({ regimen: opcion.value })}
                    className={[
                      'flex-1 border px-2 py-[9px] font-display text-[11px] font-bold tracking-[0.05em] uppercase transition-colors',
                      indice > 0 ? '-ml-px' : '',
                      activo
                        ? 'border-ink bg-ink text-ground'
                        : 'border-rule bg-surface text-ink-soft hover:border-rule-strong',
                    ].join(' ')}
                  >
                    {opcion.label}
                  </button>
                )
              })}
            </div>
          </Campo>

          <Campo etiqueta="Pacientes por página" id="f-limite">
            <div className="flex" role="group" id="f-limite">
              {[10, 20, 30].map((n, indice) => {
                const activo = filtros.limit === n
                return (
                  <button
                    key={n}
                    type="button"
                    aria-pressed={activo}
                    onClick={() => actualizar({ limit: n })}
                    className={[
                      'tabular flex-1 border px-2 py-[9px] text-[12px] font-semibold transition-colors',
                      indice > 0 ? '-ml-px' : '',
                      activo
                        ? 'border-ink bg-ink text-ground'
                        : 'border-rule bg-surface text-ink-soft hover:border-rule-strong',
                    ].join(' ')}
                  >
                    {n}
                  </button>
                )
              })}
            </div>
          </Campo>
        </div>

        {hayFiltros && (
          <button
            type="button"
            className="mt-3 font-display text-[10px] font-bold tracking-[0.08em] text-ink-faint uppercase underline underline-offset-3 hover:text-ink"
            onClick={() => {
              setBusqueda('')
              setFiltros(FILTROS_INICIALES)
            }}
          >
            Limpiar filtros
          </button>
        )}
      </section>

      {/* Resumen del universo filtrado */}
      <div
        ref={listaRef}
        className="mt-5 flex flex-wrap items-baseline justify-between gap-2 border-b border-rule pb-2"
      >
        <p className="text-[13px] text-ink-soft">
          {cargando && !datos ? (
            'Cargando…'
          ) : datos ? (
            <>
              <strong className="tabular font-semibold text-ink">
                {formatNumber(datos.total_records)}
              </strong>{' '}
              {datos.total_records === 1 ? 'paciente' : 'pacientes'}
              {hayFiltros ? ' con los filtros aplicados' : ' en lista activa'} · página{' '}
              <span className="tabular">{datos.page}</span> de{' '}
              <span className="tabular">{datos.total_pages}</span>
            </>
          ) : null}
        </p>
        {cargando && datos && (
          <span className="eyebrow" aria-live="polite">
            Actualizando…
          </span>
        )}
      </div>

      {error && (
        <div
          className="mt-4 border-l-2 bg-surface px-4 py-3 text-[13px]"
          style={{ borderColor: 'var(--color-onco)' }}
          role="alert"
        >
          <p className="font-display text-[11px] font-bold tracking-[0.08em] uppercase">
            No se pudo cargar la lista
          </p>
          <p className="mt-1 text-ink-soft">{error}</p>
        </div>
      )}

      {/* Encabezado de columnas, solo en pantallas anchas */}
      {datos && datos.data.length > 0 && (
        <div className="hidden grid-cols-[52px_minmax(0,1fr)_132px_268px_86px] gap-4 px-3 pt-3 pb-1.5 lg:grid">
          <span className="eyebrow">#</span>
          <span className="eyebrow">Paciente / Especialidad</span>
          <span className="eyebrow">Régimen</span>
          <span className="eyebrow">Espera contra su especialidad</span>
          <span className="eyebrow text-right">Puntaje</span>
        </div>
      )}

      <div className="divide-y divide-rule border-y border-rule">
        {datos?.data.map((item) => <Fila key={item.patient_id} item={item} />)}
      </div>

      {datos && datos.data.length === 0 && !cargando && (
        <div className="border border-rule bg-surface px-5 py-10 text-center">
          <p className="font-display text-[15px] font-bold">Ningún paciente calza con estos filtros</p>
          <p className="mx-auto mt-1.5 max-w-[420px] text-[13px] text-ink-soft">
            Prueba con un rango más amplio: quita la especialidad o vuelve al régimen «Todos».
          </p>
          <button
            type="button"
            className="btn btn-ghost mt-4"
            onClick={() => {
              setBusqueda('')
              setFiltros(FILTROS_INICIALES)
            }}
          >
            Limpiar filtros
          </button>
        </div>
      )}

      {datos && datos.total_pages > 1 && (
        <Paginacion
          page={datos.page}
          totalPages={datos.total_pages}
          onChange={irAPagina}
        />
      )}
    </div>
  )
}

function Campo({
  etiqueta,
  id,
  children,
}: {
  etiqueta: string
  id: string
  children: React.ReactNode
}) {
  return (
    <div>
      <label htmlFor={id} className="eyebrow mb-1.5 block">
        {etiqueta}
      </label>
      {children}
    </div>
  )
}

function Fila({ item }: { item: WaitlistItem }) {
  const color = PRIORITY_COLOR[item.priority_level]
  const restantes = daysUntil(item.ges_expiration_date)

  return (
    <article className="grid grid-cols-1 gap-3 bg-surface px-3 py-4 transition-colors hover:bg-ground/40 lg:grid-cols-[52px_minmax(0,1fr)_132px_268px_86px] lg:items-center lg:gap-4">
      {/* Posicion en el ranking */}
      <div className="tabular text-[26px] leading-none font-semibold text-ink-faint lg:text-[30px]">
        {String(item.rank).padStart(2, '0')}
      </div>

      {/* Identidad, especialidad y alertas */}
      <div className="min-w-0">
        <h2 className="truncate font-display text-[15px] leading-tight font-bold tracking-[-0.01em]">
          {item.full_name}
        </h2>
        <p className="tabular mt-0.5 text-[12.5px] text-ink-soft">
          {formatRut(item.national_id)}
        </p>
        <p className="mt-1.5 text-[13px]">
          {item.specialty_label}
          <span className="text-ink-faint">
            {' · '}
            {STAGE_LABEL[item.stage]}
            {' · '}
            {item.patient_type === 'HOSPITALARIO' ? 'Hospitalizado' : 'Ambulatorio'}
          </span>
        </p>
        <p className="mt-0.5 text-[11.5px] text-ink-faint">{item.health_service_label}</p>
        <div className="mt-2">
          <FlagBadges flags={item.flags} compact />
        </div>
      </div>

      {/* Regimen. UI.MD: GES en grande, y nada cuando no lo es. */}
      <div>
        {item.regimen === 'GES' ? (
          <>
            <div
              className="font-display text-[30px] leading-none font-extrabold tracking-[-0.03em]"
              style={{ color: 'var(--color-ges)' }}
            >
              GES
            </div>
            <div className="eyebrow mt-1">Expira</div>
            <div className="tabular text-[12.5px] font-medium">
              {formatDate(item.ges_expiration_date)}
            </div>
            {restantes !== null && (
              <div
                className="tabular text-[11px]"
                style={{ color: restantes < 0 ? 'var(--color-onco)' : 'var(--color-ink-faint)' }}
              >
                {restantes < 0
                  ? `Vencida hace ${formatNumber(Math.abs(restantes))} d`
                  : `Quedan ${formatNumber(restantes)} d`}
              </div>
            )}
          </>
        ) : (
          <span className="sr-only">Régimen No GES, sin garantía de plazo</span>
        )}
      </div>

      {/* La regla de espera */}
      <div>
        <WaitRuler
          days={item.days_waiting}
          median={item.regional_median_days}
          p75={item.regional_p75_days}
          level={item.priority_level}
        />
      </div>

      {/* Puntaje y tramo */}
      <div className="lg:text-right">
        <div className="tabular text-[24px] leading-none font-semibold" style={{ color }}>
          {item.priority_score.toFixed(2)}
        </div>
        <div
          className="mt-1 font-display text-[9.5px] font-bold tracking-[0.1em] uppercase"
          style={{ color }}
        >
          {PRIORITY_LABEL[item.priority_level]}
        </div>
      </div>
    </article>
  )
}

function Paginacion({
  page,
  totalPages,
  onChange,
}: {
  page: number
  totalPages: number
  onChange: (page: number) => void
}) {
  // Ventana de paginas alrededor de la actual, con los extremos siempre
  // visibles para poder saltar al final de la lista.
  const ventana = new Set<number>([1, totalPages, page, page - 1, page + 1])
  const paginas = [...ventana].filter((n) => n >= 1 && n <= totalPages).sort((a, b) => a - b)

  return (
    <nav className="mt-5 flex flex-wrap items-center justify-between gap-3" aria-label="Paginación">
      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        Anterior
      </button>

      <div className="flex flex-wrap items-center gap-1">
        {paginas.map((n, indice) => (
          <span key={n} className="flex items-center gap-1">
            {indice > 0 && n - paginas[indice - 1] > 1 && (
              <span className="px-1 text-[12px] text-ink-faint">…</span>
            )}
            <button
              type="button"
              aria-current={n === page ? 'page' : undefined}
              onClick={() => onChange(n)}
              className={[
                'tabular min-w-[34px] border px-2 py-1.5 text-[12px] font-semibold transition-colors',
                n === page
                  ? 'border-ink bg-ink text-ground'
                  : 'border-rule bg-surface text-ink-soft hover:border-ink hover:text-ink',
              ].join(' ')}
            >
              {n}
            </button>
          </span>
        ))}
      </div>

      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
      >
        Siguiente
      </button>
    </nav>
  )
}
