/**
 * Ingreso de paciente (UI.MD).
 *
 * Busca por RUT, muestra la ficha si el paciente ya esta en la lista y permite
 * actualizar las variables que alimentan el puntaje. Si el RUT no existe,
 * ofrece darlo de alta en vez de dejar al administrativo en un callejon.
 */

import { useEffect, useState, type FormEvent } from 'react'
import { FlagBadges } from '../components/Badge'
import { WaitRuler } from '../components/WaitRuler'
import { ApiError, api } from '../lib/api'
import { useAuth } from '../lib/auth'
import {
  PRIORITY_COLOR,
  PRIORITY_LABEL,
  STAGE_LABEL,
  daysUntil,
  formatDate,
  formatNumber,
  formatRut,
  rutEsValido,
} from '../lib/format'
import type {
  Catalog,
  ClinicalStatusUpdate,
  PatientCreate,
  PatientDetail,
  ScoreBreakdown,
} from '../lib/types'

type Vista = 'busqueda' | 'ficha' | 'alta'

export function Patient() {
  const { sesion } = useAuth()
  const [catalogo, setCatalogo] = useState<Catalog | null>(null)
  const [rut, setRut] = useState('')
  const [vista, setVista] = useState<Vista>('busqueda')
  const [paciente, setPaciente] = useState<PatientDetail | null>(null)
  const [editando, setEditando] = useState(false)
  const [buscando, setBuscando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  useEffect(() => {
    api.getCatalog().then(setCatalogo).catch(() => undefined)
  }, [])

  async function buscar(evento: FormEvent) {
    evento.preventDefault()
    const consulta = rut.trim()

    if (!rutEsValido(consulta)) {
      setError('El RUT no es válido. Revisa el dígito verificador.')
      setPaciente(null)
      setVista('busqueda')
      return
    }

    setBuscando(true)
    setError(null)
    setAviso(null)
    setEditando(false)

    try {
      const encontrado = await api.getPatient(consulta)
      setPaciente(encontrado)
      setVista('ficha')
    } catch (e) {
      setPaciente(null)
      if (e instanceof ApiError && e.status === 404) {
        setVista('alta')
        setError(null)
      } else {
        setVista('busqueda')
        setError(e instanceof ApiError ? e.message : 'No se pudo consultar el paciente.')
      }
    } finally {
      setBuscando(false)
    }
  }

  function reiniciar() {
    setRut('')
    setPaciente(null)
    setVista('busqueda')
    setEditando(false)
    setError(null)
    setAviso(null)
  }

  return (
    <div className="mx-auto max-w-[900px]">
      <header>
        <p className="eyebrow">Ficha clínica</p>
        <h1 className="mt-1 font-display text-[26px] leading-none font-bold tracking-[-0.02em] sm:text-[30px]">
          Ingreso de paciente
        </h1>
        <p className="mt-2 max-w-[560px] text-[14px] text-ink-soft">
          Busca por RUT para ver la ficha y el puntaje vigente. Si el paciente no está en la lista,
          puedes ingresarlo.
        </p>
      </header>

      <form onSubmit={buscar} className="mt-6 border border-rule bg-surface p-4">
        <label htmlFor="rut" className="eyebrow mb-1.5 block">
          RUT del paciente
        </label>
        <div className="flex flex-wrap gap-2">
          <input
            id="rut"
            className="field tabular max-w-[260px] flex-1"
            value={rut}
            onChange={(e) => {
              setRut(e.target.value)
              setError(null)
            }}
            placeholder="12.345.678-9"
            autoComplete="off"
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? 'rut-error' : undefined}
          />
          <button type="submit" className="btn btn-primary" disabled={buscando || !rut.trim()}>
            {buscando ? 'Buscando…' : 'Buscar'}
          </button>
          {(paciente || vista === 'alta') && (
            <button type="button" className="btn btn-ghost" onClick={reiniciar}>
              Nueva búsqueda
            </button>
          )}
        </div>
        {error && (
          <p id="rut-error" className="mt-2 text-[12.5px]" style={{ color: 'var(--color-onco)' }}>
            {error}
          </p>
        )}
      </form>

      {aviso && (
        <div
          className="mt-4 border-l-2 bg-surface px-4 py-3 text-[13px] text-ink-soft"
          style={{ borderColor: 'var(--color-ges)' }}
          role="status"
        >
          {aviso}
        </div>
      )}

      {vista === 'alta' && (
        <AltaPaciente
          rut={rut.trim()}
          catalogo={catalogo}
          servicioPorDefecto={sesion?.servicio ?? 'SSMO'}
          onCreado={(nuevo) => {
            setPaciente(nuevo)
            setVista('ficha')
            setAviso(`${nuevo.full_name} quedó ingresado en la lista de espera.`)
          }}
          onCancelar={reiniciar}
        />
      )}

      {vista === 'ficha' && paciente && (
        <>
          <Ficha paciente={paciente} onEditar={() => setEditando((v) => !v)} editando={editando} />
          {editando && (
            <ActualizarEstado
              paciente={paciente}
              catalogo={catalogo}
              onGuardado={(actualizado) => {
                setPaciente(actualizado)
                setEditando(false)
                setAviso(
                  `Estado actualizado. Puntaje recalculado: ${actualizado.score.total_score.toFixed(2)} (${PRIORITY_LABEL[actualizado.score.priority_level]}).`,
                )
              }}
              onCancelar={() => setEditando(false)}
            />
          )}
        </>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Ficha                                                               */
/* ------------------------------------------------------------------ */

function Ficha({
  paciente,
  onEditar,
  editando,
}: {
  paciente: PatientDetail
  onEditar: () => void
  editando: boolean
}) {
  const score = paciente.score
  const color = PRIORITY_COLOR[score.priority_level]
  const restantes = daysUntil(paciente.ges_expiration_date)

  return (
    <section className="mt-4 border border-rule bg-surface">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-rule p-5">
        <div className="min-w-0">
          <h2 className="font-display text-[22px] leading-tight font-bold tracking-[-0.02em]">
            {paciente.full_name}
          </h2>
          <p className="tabular mt-1 text-[13px] text-ink-soft">
            {paciente.national_id_formatted}
            {paciente.age !== null && ` · ${paciente.age} años`}
          </p>
          <div className="mt-3">
            <FlagBadges flags={score.flags} />
          </div>
        </div>

        <div className="flex items-start gap-5">
          {paciente.regimen === 'GES' && (
            <div>
              <div
                className="font-display text-[34px] leading-none font-extrabold tracking-[-0.03em]"
                style={{ color: 'var(--color-ges)' }}
              >
                GES
              </div>
              <div className="eyebrow mt-1">Expira</div>
              <div className="tabular text-[13px] font-medium">
                {formatDate(paciente.ges_expiration_date)}
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
            </div>
          )}

          <div className="text-right">
            <div className="eyebrow">Puntaje</div>
            <div className="tabular text-[36px] leading-none font-semibold" style={{ color }}>
              {score.total_score.toFixed(2)}
            </div>
            <div
              className="mt-0.5 font-display text-[10px] font-bold tracking-[0.1em] uppercase"
              style={{ color }}
            >
              {PRIORITY_LABEL[score.priority_level]}
            </div>
          </div>
        </div>
      </div>

      {/* La regla de espera del paciente */}
      <div className="border-b border-rule p-5">
        <div className="eyebrow mb-2">
          Espera contra la mediana de {paciente.specialty_label} en {paciente.health_service_id}
        </div>
        <WaitRuler
          days={paciente.days_waiting}
          median={score.metadata.regional_median_days}
          p75={score.metadata.regional_p75_days}
          level={score.priority_level}
        />
      </div>

      <dl className="grid gap-x-6 gap-y-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
        <Dato etiqueta="Especialidad" valor={paciente.specialty_label} />
        <Dato etiqueta="Etapa" valor={STAGE_LABEL[paciente.stage]} />
        <Dato
          etiqueta="Tipo de paciente"
          valor={paciente.patient_type === 'HOSPITALARIO' ? 'Hospitalizado' : 'Ambulatorio'}
        />
        <Dato etiqueta="Servicio de Salud" valor={paciente.health_service_label} />
        <Dato etiqueta="Régimen" valor={paciente.regimen === 'GES' ? 'GES' : 'No GES'} />
        <Dato etiqueta="Severidad clínica" valor={paciente.clinical_severity} />
        <Dato etiqueta="Ingreso a la lista" valor={formatDate(paciente.entry_date)} mono />
        <Dato
          etiqueta="Días esperando"
          valor={formatNumber(paciente.days_waiting)}
          mono
        />
        <Dato
          etiqueta="Últimos exámenes"
          valor={formatDate(paciente.last_exams_date)}
          mono
          alerta={score.metadata.exams_expired}
        />
        <Dato etiqueta="Oncológico" valor={paciente.is_oncologic ? 'Sí' : 'No'} />
        <Dato etiqueta="Etapificación" valor={paciente.staging ?? '—'} mono />
        <Dato
          etiqueta="Teléfono de contacto"
          valor={paciente.contact_phone ?? '—'}
          mono
          alerta={!paciente.contact_phone}
        />
        <div className="sm:col-span-2 lg:col-span-3">
          <Dato etiqueta="Diagnóstico" valor={paciente.diagnosis || '—'} />
        </div>
      </dl>

      {score.breakdown && <Desglose breakdown={score.breakdown} total={score.total_score} />}

      <div className="flex flex-wrap items-center gap-3 border-t border-rule p-5">
        <button type="button" className="btn btn-primary" onClick={onEditar} aria-expanded={editando}>
          {editando ? 'Cerrar formulario' : 'Actualizar estado'}
        </button>
        <p className="text-[12px] text-ink-faint">
          Los cambios recalculan el puntaje y reordenan la lista de inmediato.
        </p>
      </div>
    </section>
  )
}

function Dato({
  etiqueta,
  valor,
  mono = false,
  alerta = false,
}: {
  etiqueta: string
  valor: string
  mono?: boolean
  alerta?: boolean
}) {
  return (
    <div>
      <dt className="eyebrow">{etiqueta}</dt>
      <dd
        className={`mt-0.5 text-[14px] ${mono ? 'tabular' : ''}`}
        style={alerta ? { color: 'var(--color-antiguo)' } : undefined}
      >
        {valor}
      </dd>
    </div>
  )
}

/**
 * Desglose del puntaje. Es lo que permite que el coordinador defienda la
 * decision: cada barra es el aporte ya ponderado de un componente, y los cuatro
 * suman exactamente el total.
 */
function Desglose({ breakdown, total }: { breakdown: ScoreBreakdown; total: number }) {
  const componentes = [
    {
      etiqueta: 'Tiempo acumulado',
      valor: breakdown.time_waiting_score,
      peso: '35%',
      color: 'var(--color-ges)',
      nota: 'Días esperando contra la mediana y el P75 de su especialidad',
    },
    {
      etiqueta: 'Severidad y garantía',
      valor: breakdown.clinical_severity_score,
      peso: '30%',
      color: 'var(--color-estandar)',
      nota: 'Severidad clínica, o incumplimiento de la garantía GES',
    },
    {
      etiqueta: 'Riesgo oncológico',
      valor: breakdown.oncologic_risk_score,
      peso: '20%',
      color: 'var(--color-onco)',
      nota: 'Decreto 18/2026, con sesgo por especialidad crítica',
    },
    {
      etiqueta: 'Exámenes vencidos',
      valor: breakdown.diagnostic_validity_penalty,
      peso: '15%',
      color: 'var(--color-antiguo)',
      nota: 'Riesgo de quedar varado repitiendo exámenes caducados',
    },
  ]

  return (
    <div className="border-t border-rule p-5">
      <div className="eyebrow mb-3">Cómo se compone el puntaje</div>

      {/* Barra apilada: la proporcion visible es la del aporte real al total. */}
      <div className="mb-4 flex h-[10px] w-full overflow-hidden border border-rule bg-sunken">
        {componentes.map((c) => (
          <span
            key={c.etiqueta}
            style={{ width: `${c.valor}%`, backgroundColor: c.color }}
            title={`${c.etiqueta}: ${c.valor.toFixed(2)} puntos`}
          />
        ))}
      </div>

      <ul className="space-y-2.5">
        {componentes.map((c) => (
          <li key={c.etiqueta} className="grid grid-cols-[10px_1fr_auto] items-baseline gap-2.5">
            <span
              className="mt-[5px] h-[9px] w-[9px] shrink-0"
              style={{ backgroundColor: c.color }}
              aria-hidden="true"
            />
            <span>
              <span className="text-[13.5px] font-medium">{c.etiqueta}</span>
              <span className="ml-1.5 text-[11px] text-ink-faint">ponderación {c.peso}</span>
              <span className="block text-[11.5px] text-ink-faint">{c.nota}</span>
            </span>
            <span className="tabular text-[14px] font-semibold">{c.valor.toFixed(2)}</span>
          </li>
        ))}
      </ul>

      <div className="mt-3 flex items-baseline justify-between border-t border-rule pt-3">
        <span className="font-display text-[11px] font-bold tracking-[0.08em] uppercase">
          Puntaje total
        </span>
        <span className="tabular text-[16px] font-semibold">{total.toFixed(2)}</span>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Actualizar estado                                                   */
/* ------------------------------------------------------------------ */

function ActualizarEstado({
  paciente,
  catalogo,
  onGuardado,
  onCancelar,
}: {
  paciente: PatientDetail
  catalogo: Catalog | null
  onGuardado: (actualizado: PatientDetail) => void
  onCancelar: () => void
}) {
  const [form, setForm] = useState({
    regimen: paciente.regimen,
    fecha_expiracion_ges: paciente.ges_expiration_date ?? '',
    tipo_paciente: paciente.patient_type,
    especialidad: paciente.specialty,
    stage: paciente.stage,
    health_service_id: paciente.health_service_id,
    severidad_clinica: paciente.clinical_severity,
    es_oncologico: paciente.is_oncologic,
    estadificacion: paciente.staging ?? '',
    fecha_ultimos_examenes: paciente.last_exams_date ?? '',
    telefono_contacto: paciente.contact_phone ?? '',
    diagnostico: paciente.diagnosis,
  })
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof typeof form>(campo: K, valor: (typeof form)[K]) {
    setForm((f) => ({ ...f, [campo]: valor }))
  }

  async function guardar(evento: FormEvent) {
    evento.preventDefault()
    setGuardando(true)
    setError(null)

    const cambios: ClinicalStatusUpdate = {
      regimen: form.regimen,
      tipo_paciente: form.tipo_paciente,
      especialidad: form.especialidad,
      stage: form.stage,
      health_service_id: form.health_service_id,
      severidad_clinica: form.severidad_clinica,
      es_oncologico: form.es_oncologico,
      diagnostico: form.diagnostico,
      // Los campos vacios se envian como null para poder borrar un dato, no
      // como cadena vacia: el backend espera una fecha valida o nada.
      fecha_expiracion_ges: form.regimen === 'GES' ? form.fecha_expiracion_ges || null : null,
      fecha_ultimos_examenes: form.fecha_ultimos_examenes || null,
      estadificacion: form.estadificacion || null,
      telefono_contacto: form.telefono_contacto || null,
    }

    try {
      onGuardado(await api.updateClinicalStatus(paciente.national_id, cambios))
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No se pudo guardar el cambio.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={guardar} className="mt-4 border border-ink bg-surface">
      <div className="border-b border-rule bg-ink px-5 py-3">
        <h3 className="font-display text-[13px] font-bold tracking-[0.06em] text-ground uppercase">
          Actualizar estado clínico
        </h3>
        <p className="mt-0.5 text-[12px] text-ink-faint">
          Estos son los campos que alimentan el cálculo del puntaje.
        </p>
      </div>

      <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
        <Campo etiqueta="Régimen" id="e-regimen">
          <select
            id="e-regimen"
            className="field"
            value={form.regimen}
            onChange={(e) => set('regimen', e.target.value as typeof form.regimen)}
          >
            <option value="GES">GES</option>
            <option value="NO_GES">No GES</option>
          </select>
        </Campo>

        <Campo
          etiqueta="Fecha de expiración GES"
          id="e-expiracion"
          ayuda={form.regimen === 'NO_GES' ? 'Solo aplica al régimen GES' : undefined}
        >
          <input
            id="e-expiracion"
            type="date"
            className="field tabular"
            value={form.fecha_expiracion_ges}
            disabled={form.regimen !== 'GES'}
            onChange={(e) => set('fecha_expiracion_ges', e.target.value)}
          />
        </Campo>

        <Campo etiqueta="Tipo de paciente" id="e-tipo">
          <select
            id="e-tipo"
            className="field"
            value={form.tipo_paciente}
            onChange={(e) => set('tipo_paciente', e.target.value as typeof form.tipo_paciente)}
          >
            <option value="AMBULATORIO">Ambulatorio</option>
            <option value="HOSPITALARIO">Hospitalizado</option>
          </select>
        </Campo>

        <Campo etiqueta="Especialidad" id="e-especialidad">
          <select
            id="e-especialidad"
            className="field"
            value={form.especialidad}
            onChange={(e) => set('especialidad', e.target.value)}
          >
            {catalogo?.specialties.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Etapa" id="e-etapa">
          <select
            id="e-etapa"
            className="field"
            value={form.stage}
            onChange={(e) => set('stage', e.target.value as typeof form.stage)}
          >
            {catalogo?.stages.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Servicio de Salud" id="e-servicio">
          <select
            id="e-servicio"
            className="field"
            value={form.health_service_id}
            onChange={(e) => set('health_service_id', e.target.value)}
          >
            {catalogo?.health_services.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Severidad clínica" id="e-severidad">
          <select
            id="e-severidad"
            className="field"
            value={form.severidad_clinica}
            onChange={(e) => set('severidad_clinica', e.target.value as typeof form.severidad_clinica)}
          >
            <option value="ALTA">Alta</option>
            <option value="MEDIA">Media</option>
            <option value="BAJA">Baja</option>
          </select>
        </Campo>

        <Campo etiqueta="Fecha de últimos exámenes" id="e-examenes">
          <input
            id="e-examenes"
            type="date"
            className="field tabular"
            value={form.fecha_ultimos_examenes}
            onChange={(e) => set('fecha_ultimos_examenes', e.target.value)}
          />
        </Campo>

        <Campo etiqueta="Teléfono de contacto" id="e-telefono">
          <input
            id="e-telefono"
            className="field tabular"
            value={form.telefono_contacto}
            onChange={(e) => set('telefono_contacto', e.target.value)}
            placeholder="+56 9 0000 0000"
          />
        </Campo>

        <Campo etiqueta="Etapificación" id="e-etapificacion" ayuda="TNM u otra. Requerida en casos oncológicos.">
          <input
            id="e-etapificacion"
            className="field tabular"
            value={form.estadificacion}
            onChange={(e) => set('estadificacion', e.target.value)}
            placeholder="T2N1M0"
          />
        </Campo>

        <div className="flex items-end">
          <label className="flex cursor-pointer items-center gap-2.5 pb-2">
            <input
              type="checkbox"
              className="h-4 w-4 accent-[var(--color-onco)]"
              checked={form.es_oncologico}
              onChange={(e) => set('es_oncologico', e.target.checked)}
            />
            <span className="text-[13.5px]">Caso oncológico (Decreto 18)</span>
          </label>
        </div>

        <div className="sm:col-span-2 lg:col-span-3">
          <Campo etiqueta="Diagnóstico" id="e-diagnostico">
            <input
              id="e-diagnostico"
              className="field"
              value={form.diagnostico}
              onChange={(e) => set('diagnostico', e.target.value)}
            />
          </Campo>
        </div>
      </div>

      {error && (
        <p className="px-5 pb-3 text-[12.5px]" style={{ color: 'var(--color-onco)' }} role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2 border-t border-rule p-5">
        <button type="submit" className="btn btn-primary" disabled={guardando}>
          {guardando ? 'Guardando…' : 'Guardar y recalcular'}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

/* ------------------------------------------------------------------ */
/* Alta de paciente                                                    */
/* ------------------------------------------------------------------ */

function AltaPaciente({
  rut,
  catalogo,
  servicioPorDefecto,
  onCreado,
  onCancelar,
}: {
  rut: string
  catalogo: Catalog | null
  servicioPorDefecto: string
  onCreado: (paciente: PatientDetail) => void
  onCancelar: () => void
}) {
  const [form, setForm] = useState({
    nombre_completo: '',
    regimen: 'NO_GES' as 'GES' | 'NO_GES',
    fecha_expiracion_ges: '',
    tipo_paciente: 'AMBULATORIO' as 'AMBULATORIO' | 'HOSPITALARIO',
    especialidad: 'OFTALMOLOGIA',
    stage: 'DIAGNOSTICO' as PatientCreate['stage'],
    health_service_id: servicioPorDefecto,
    severidad_clinica: 'MEDIA' as 'ALTA' | 'MEDIA' | 'BAJA',
    es_oncologico: false,
    fecha_ingreso_lista: new Date().toISOString().slice(0, 10),
    fecha_ultimos_examenes: '',
    telefono_contacto: '',
    diagnostico: '',
  })
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof typeof form>(campo: K, valor: (typeof form)[K]) {
    setForm((f) => ({ ...f, [campo]: valor }))
  }

  async function crear(evento: FormEvent) {
    evento.preventDefault()
    setGuardando(true)
    setError(null)

    try {
      onCreado(
        await api.createPatient({
          rut,
          nombre_completo: form.nombre_completo.trim(),
          regimen: form.regimen,
          especialidad: form.especialidad,
          stage: form.stage,
          health_service_id: form.health_service_id,
          tipo_paciente: form.tipo_paciente,
          severidad_clinica: form.severidad_clinica,
          es_oncologico: form.es_oncologico,
          diagnostico: form.diagnostico,
          fecha_ingreso_lista: form.fecha_ingreso_lista || null,
          fecha_expiracion_ges: form.regimen === 'GES' ? form.fecha_expiracion_ges || null : null,
          fecha_ultimos_examenes: form.fecha_ultimos_examenes || null,
          telefono_contacto: form.telefono_contacto || null,
        }),
      )
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No se pudo ingresar el paciente.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={crear} className="mt-4 border border-rule bg-surface">
      <div className="border-b border-rule p-5">
        <h2 className="font-display text-[17px] font-bold tracking-[-0.01em]">
          Este RUT no está en la lista de espera
        </h2>
        <p className="mt-1 text-[13px] text-ink-soft">
          Ingresa a <span className="tabular font-medium">{formatRut(rut)}</span> completando su
          derivación. El puntaje se calcula al guardar.
        </p>
      </div>

      <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
        <div className="sm:col-span-2">
          <Campo etiqueta="Nombre completo" id="a-nombre">
            <input
              id="a-nombre"
              className="field"
              value={form.nombre_completo}
              onChange={(e) => set('nombre_completo', e.target.value)}
              placeholder="Nombres y dos apellidos"
              required
            />
          </Campo>
        </div>

        <Campo etiqueta="Régimen" id="a-regimen">
          <select
            id="a-regimen"
            className="field"
            value={form.regimen}
            onChange={(e) => set('regimen', e.target.value as typeof form.regimen)}
          >
            <option value="NO_GES">No GES</option>
            <option value="GES">GES</option>
          </select>
        </Campo>

        <Campo
          etiqueta="Fecha de expiración GES"
          id="a-expiracion"
          ayuda={form.regimen === 'NO_GES' ? 'Solo aplica al régimen GES' : undefined}
        >
          <input
            id="a-expiracion"
            type="date"
            className="field tabular"
            value={form.fecha_expiracion_ges}
            disabled={form.regimen !== 'GES'}
            onChange={(e) => set('fecha_expiracion_ges', e.target.value)}
          />
        </Campo>

        <Campo etiqueta="Especialidad" id="a-especialidad">
          <select
            id="a-especialidad"
            className="field"
            value={form.especialidad}
            onChange={(e) => set('especialidad', e.target.value)}
          >
            {catalogo?.specialties.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Etapa" id="a-etapa">
          <select
            id="a-etapa"
            className="field"
            value={form.stage}
            onChange={(e) => set('stage', e.target.value as typeof form.stage)}
          >
            {catalogo?.stages.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Servicio de Salud" id="a-servicio">
          <select
            id="a-servicio"
            className="field"
            value={form.health_service_id}
            onChange={(e) => set('health_service_id', e.target.value)}
          >
            {catalogo?.health_services.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Tipo de paciente" id="a-tipo">
          <select
            id="a-tipo"
            className="field"
            value={form.tipo_paciente}
            onChange={(e) => set('tipo_paciente', e.target.value as typeof form.tipo_paciente)}
          >
            <option value="AMBULATORIO">Ambulatorio</option>
            <option value="HOSPITALARIO">Hospitalizado</option>
          </select>
        </Campo>

        <Campo etiqueta="Severidad clínica" id="a-severidad">
          <select
            id="a-severidad"
            className="field"
            value={form.severidad_clinica}
            onChange={(e) => set('severidad_clinica', e.target.value as typeof form.severidad_clinica)}
          >
            <option value="ALTA">Alta</option>
            <option value="MEDIA">Media</option>
            <option value="BAJA">Baja</option>
          </select>
        </Campo>

        <Campo etiqueta="Fecha de ingreso a la lista" id="a-ingreso">
          <input
            id="a-ingreso"
            type="date"
            className="field tabular"
            value={form.fecha_ingreso_lista}
            onChange={(e) => set('fecha_ingreso_lista', e.target.value)}
          />
        </Campo>

        <Campo etiqueta="Fecha de últimos exámenes" id="a-examenes">
          <input
            id="a-examenes"
            type="date"
            className="field tabular"
            value={form.fecha_ultimos_examenes}
            onChange={(e) => set('fecha_ultimos_examenes', e.target.value)}
          />
        </Campo>

        <Campo etiqueta="Teléfono de contacto" id="a-telefono">
          <input
            id="a-telefono"
            className="field tabular"
            value={form.telefono_contacto}
            onChange={(e) => set('telefono_contacto', e.target.value)}
            placeholder="+56 9 0000 0000"
          />
        </Campo>

        <div className="flex items-end">
          <label className="flex cursor-pointer items-center gap-2.5 pb-2">
            <input
              type="checkbox"
              className="h-4 w-4 accent-[var(--color-onco)]"
              checked={form.es_oncologico}
              onChange={(e) => set('es_oncologico', e.target.checked)}
            />
            <span className="text-[13.5px]">Caso oncológico (Decreto 18)</span>
          </label>
        </div>

        <div className="sm:col-span-2 lg:col-span-3">
          <Campo etiqueta="Diagnóstico o hipótesis diagnóstica" id="a-diagnostico">
            <input
              id="a-diagnostico"
              className="field"
              value={form.diagnostico}
              onChange={(e) => set('diagnostico', e.target.value)}
            />
          </Campo>
        </div>
      </div>

      {error && (
        <p className="px-5 pb-3 text-[12.5px]" style={{ color: 'var(--color-onco)' }} role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2 border-t border-rule p-5">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={guardando || !form.nombre_completo.trim()}
        >
          {guardando ? 'Ingresando…' : 'Ingresar a la lista'}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

function Campo({
  etiqueta,
  id,
  ayuda,
  children,
}: {
  etiqueta: string
  id: string
  ayuda?: string
  children: React.ReactNode
}) {
  return (
    <div>
      <label htmlFor={id} className="eyebrow mb-1.5 block">
        {etiqueta}
      </label>
      {children}
      {ayuda && <p className="mt-1 text-[11px] text-ink-faint">{ayuda}</p>}
    </div>
  )
}
