/**
 * La regla de espera.
 *
 * Muestra los dias que lleva el paciente contra la mediana y el P75 de su
 * propia especialidad y Servicio de Salud. Esas dos marcas son exactamente los
 * divisores del componente temporal del puntaje, que aporta el 35% del total,
 * asi que la barra no ilustra el dato: es el dato. Se ve al paciente cruzar el
 * umbral en el que su espera dejo de ser normal donde se atiende.
 */

import { PRIORITY_COLOR, formatNumber } from '../lib/format'
import type { PriorityLevel } from '../lib/types'

interface Props {
  days: number
  median: number
  p75: number
  level: PriorityLevel
  compact?: boolean
}

export function WaitRuler({ days, median, p75, level, compact = false }: Props) {
  // La escala llega hasta el P75 con holgura, o hasta la espera del paciente si
  // ya lo dejo atras. Escalar siempre al maximo global aplastaria las esperas
  // cortas del area oncologica, que es justo donde 90 dias ya son graves.
  const tope = Math.max(days, p75 * 1.15)
  const pct = (valor: number) => `${Math.min(100, (valor / tope) * 100)}%`

  const color = PRIORITY_COLOR[level]
  const superaMediana = days >= median
  const superaP75 = days >= p75

  const descripcion = superaP75
    ? `${formatNumber(days)} días esperando, sobre el percentil 75 de ${formatNumber(Math.round(p75))} días`
    : superaMediana
      ? `${formatNumber(days)} días esperando, sobre la mediana de ${formatNumber(Math.round(median))} días`
      : `${formatNumber(days)} días esperando, bajo la mediana de ${formatNumber(Math.round(median))} días`

  return (
    <div className={compact ? '' : 'min-w-0'}>
      <div
        className="relative h-[22px] w-full border border-rule bg-sunken"
        role="img"
        aria-label={descripcion}
      >
        {/* Espera acumulada */}
        <div
          className="absolute inset-y-0 left-0"
          style={{ width: pct(days), backgroundColor: color, opacity: 0.85 }}
        />

        {/* Marca de la mediana regional */}
        <Marca posicion={pct(median)} etiqueta="med" />

        {/* Marca del percentil 75 */}
        <Marca posicion={pct(p75)} etiqueta="p75" fuerte />

        {/* Lectura de dias, dentro de la barra si hay espacio */}
        <span
          className="tabular absolute top-1/2 -translate-y-1/2 text-[11px] font-semibold tracking-tight"
          style={
            days / tope > 0.28
              ? { left: '0.4rem', color: 'var(--color-surface)' }
              : { left: `calc(${pct(days)} + 0.4rem)`, color: 'var(--color-ink-soft)' }
          }
        >
          {formatNumber(days)} d
        </span>
      </div>

      {!compact && (
        <div className="mt-1 flex justify-between text-[10px] text-ink-faint">
          <span className="tabular">
            mediana {formatNumber(Math.round(median))} d · p75 {formatNumber(Math.round(p75))} d
          </span>
          {superaP75 ? (
            <span className="eyebrow" style={{ color: 'var(--color-onco)' }}>
              Sobre P75
            </span>
          ) : superaMediana ? (
            <span className="eyebrow" style={{ color: 'var(--color-antiguo)' }}>
              Sobre mediana
            </span>
          ) : null}
        </div>
      )}
    </div>
  )
}

function Marca({
  posicion,
  etiqueta,
  fuerte = false,
}: {
  posicion: string
  etiqueta: string
  fuerte?: boolean
}) {
  return (
    <span
      className="absolute inset-y-0 w-px"
      style={{
        left: posicion,
        backgroundColor: fuerte ? 'var(--color-ink)' : 'var(--color-ink-faint)',
      }}
      aria-hidden="true"
    >
      <span
        className="absolute -top-[1px] left-[1px] px-[2px] text-[8px] leading-[10px] font-semibold tracking-wider uppercase"
        style={{
          color: fuerte ? 'var(--color-ink)' : 'var(--color-ink-faint)',
          backgroundColor: 'color-mix(in srgb, var(--color-surface) 78%, transparent)',
        }}
      >
        {etiqueta}
      </span>
    </span>
  )
}
