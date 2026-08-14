/** Inicio: bienvenida y las dos acciones del flujo (UI.MD). */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { formatNumber } from '../lib/format'
import type { Stats } from '../lib/types'

export function Home() {
  const { sesion } = useAuth()
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    let vigente = true
    api
      .getStats()
      .then((d) => vigente && setStats(d))
      .catch(() => undefined)
    return () => {
      vigente = false
    }
  }, [])

  return (
    <div className="mx-auto max-w-[860px]">
      <p className="eyebrow">Bienvenido</p>
      <h1 className="mt-2 font-display text-[30px] leading-[1.1] font-bold tracking-[-0.025em] sm:text-[38px]">
        {sesion?.usuario}, la lista está priorizada y lista para revisar.
      </h1>
      <p className="mt-3 max-w-[620px] text-[15px] leading-relaxed text-ink-soft">
        PROCE-SALUD calcula un puntaje continuo para cada persona en espera combinando su tiempo
        acumulado contra la mediana de su propia especialidad, la severidad clínica, la garantía
        legal GES y el riesgo oncológico del Decreto 18. Puedes revisar el ranking completo o
        trabajar sobre la ficha de un paciente.
      </p>

      {/* Estado de la lista, en una linea de instrumento: sin tarjetas ni
          adornos, solo las cifras que cambian la decision del turno. */}
      {stats && (
        <div className="mt-8 grid grid-cols-2 gap-px border border-rule bg-rule sm:grid-cols-4">
          <Cifra etiqueta="En espera" valor={formatNumber(stats.total_waiting)} />
          <Cifra
            etiqueta="Oncológicos"
            valor={formatNumber(stats.oncologic)}
            color="var(--color-onco)"
          />
          <Cifra
            etiqueta="GES retrasados"
            valor={formatNumber(stats.ges_delayed)}
            color="var(--color-ges)"
          />
          <Cifra
            etiqueta="Mediana de espera"
            valor={`${formatNumber(stats.median_days_waiting)} d`}
          />
        </div>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Accion
          to="/paciente"
          numero="A"
          titulo="Ingreso de paciente"
          descripcion="Busca por RUT, revisa la ficha y actualiza el estado clínico para recalcular el puntaje."
        />
        <Accion
          to="/lista-espera"
          numero="B"
          titulo="Consultar lista de espera"
          descripcion="Ranking priorizado con filtros por especialidad, régimen y tipo de paciente."
        />
      </div>
    </div>
  )
}

function Cifra({
  etiqueta,
  valor,
  color,
}: {
  etiqueta: string
  valor: string
  color?: string
}) {
  return (
    <div className="bg-surface px-4 py-3">
      <div className="eyebrow">{etiqueta}</div>
      <div
        className="tabular mt-0.5 text-[22px] leading-none font-semibold"
        style={color ? { color } : undefined}
      >
        {valor}
      </div>
    </div>
  )
}

function Accion({
  to,
  numero,
  titulo,
  descripcion,
}: {
  to: string
  numero: string
  titulo: string
  descripcion: string
}) {
  return (
    <Link
      to={to}
      className="group block border border-rule bg-surface p-5 transition-colors hover:border-ink"
    >
      <div className="flex items-start gap-4">
        <span className="tabular text-[13px] leading-none font-semibold text-ink-faint transition-colors group-hover:text-onco">
          {numero}
        </span>
        <div className="min-w-0">
          <h2 className="font-display text-[16px] font-bold tracking-[-0.01em]">{titulo}</h2>
          <p className="mt-1.5 text-[13px] leading-relaxed text-ink-soft">{descripcion}</p>
          <span className="mt-3 inline-block font-display text-[10px] font-bold tracking-[0.1em] uppercase underline decoration-1 underline-offset-4 group-hover:text-ges">
            Abrir
          </span>
        </div>
      </div>
    </Link>
  )
}
