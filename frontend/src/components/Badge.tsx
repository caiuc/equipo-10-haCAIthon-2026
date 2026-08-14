/**
 * Insignias de estado (documentation.MD 6.1).
 *
 * Son la unica fuente de color del tablero. Cada una corresponde a una decision
 * que el coordinador tiene que tomar, no a un adorno: por eso llevan texto y no
 * solo un punto de color, y por eso el titulo explica que hacer con ellas.
 */

import type { PatientFlags } from '../lib/types'

type Tono = 'onco' | 'antiguo' | 'incompleta' | 'ges' | 'estandar' | 'registro'

const COLOR: Record<Tono, string> = {
  onco: 'var(--color-onco)',
  antiguo: 'var(--color-antiguo)',
  incompleta: 'var(--color-incompleta)',
  ges: 'var(--color-ges)',
  estandar: 'var(--color-estandar)',
  registro: 'var(--color-registro)',
}

export function Badge({
  tono,
  children,
  title,
}: {
  tono: Tono
  children: React.ReactNode
  title?: string
}) {
  const color = COLOR[tono]
  return (
    <span
      title={title}
      className="inline-flex items-center gap-1 border px-[6px] py-[2px] font-display text-[9.5px] font-bold tracking-[0.09em] whitespace-nowrap uppercase"
      style={{
        color,
        borderColor: `color-mix(in srgb, ${color} 40%, transparent)`,
        backgroundColor: `color-mix(in srgb, ${color} 8%, transparent)`,
      }}
    >
      <span
        aria-hidden="true"
        className="h-[5px] w-[5px] shrink-0 rounded-full"
        style={{ backgroundColor: color }}
      />
      {children}
    </span>
  )
}

/** Traduce las banderas de un paciente al conjunto de insignias que le tocan. */
export function FlagBadges({ flags, compact = false }: { flags: PatientFlags; compact?: boolean }) {
  const insignias: React.ReactNode[] = []

  if (flags.is_oncologic) {
    insignias.push(
      <Badge key="onco" tono="onco" title="Alerta sanitaria oncológica. Prioridad máxima de agendamiento.">
        Oncológico · Decreto 18
      </Badge>,
    )
  }

  if (flags.ges_delayed) {
    insignias.push(
      <Badge key="ges" tono="ges" title="Garantía legal de oportunidad vencida. Notificar a SIGGES.">
        GES retrasado
      </Badge>,
    )
  }

  if (flags.is_ancient_patient) {
    insignias.push(
      <Badge
        key="antiguo"
        tono="antiguo"
        title="Más de 300 días esperando y exámenes vencidos. Hay que repetirlos antes de agendar."
      >
        Paciente antiguo
      </Badge>,
    )
  }

  if (flags.incomplete_info) {
    insignias.push(
      <Badge
        key="info"
        tono="incompleta"
        title="Faltan datos críticos. Bloquea la asignación definitiva hasta completar la ficha."
      >
        Info incompleta
      </Badge>,
    )
  }

  if (flags.civil_registry_status === 'PENDING_VERIFICATION') {
    insignias.push(
      <Badge key="rc" tono="registro" title="En proceso de depuración con el Registro Civil.">
        Verificando Registro Civil
      </Badge>,
    )
  }

  if (insignias.length === 0) {
    insignias.push(
      <Badge key="std" tono="estandar" title="Espera dentro de los márgenes de su especialidad.">
        No GES estándar
      </Badge>,
    )
  }

  return (
    <div className={`flex flex-wrap items-center ${compact ? 'gap-1' : 'gap-1.5'}`}>{insignias}</div>
  )
}
