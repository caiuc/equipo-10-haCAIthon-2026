/** Formato de datos chilenos para presentacion. */

import type { PriorityLevel, Stage } from './types'

/** '12940112-5' -> '12.940.112-5' */
export function formatRut(rut: string): string {
  const limpio = rut.replace(/[^0-9kK]/g, '').toUpperCase()
  if (limpio.length < 2) return rut
  const cuerpo = limpio.slice(0, -1)
  const dv = limpio.slice(-1)
  return `${cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.')}-${dv}`
}

/** Digito verificador por modulo 11, para validar antes de consultar la API. */
export function digitoVerificador(cuerpo: string): string {
  let suma = 0
  let multiplicador = 2
  for (const digito of [...cuerpo].reverse()) {
    suma += Number(digito) * multiplicador
    multiplicador = multiplicador === 7 ? 2 : multiplicador + 1
  }
  const resto = 11 - (suma % 11)
  if (resto === 11) return '0'
  if (resto === 10) return 'K'
  return String(resto)
}

export function rutEsValido(rut: string): boolean {
  const limpio = rut.replace(/[^0-9kK]/g, '').toUpperCase()
  if (limpio.length < 7 || limpio.length > 9) return false
  const cuerpo = limpio.slice(0, -1)
  const dv = limpio.slice(-1)
  if (!/^\d+$/.test(cuerpo)) return false
  return digitoVerificador(cuerpo) === dv
}

/** '2026-07-22' -> '22 jul 2026' */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const [anio, mes, dia] = iso.slice(0, 10).split('-').map(Number)
  if (!anio || !mes || !dia) return '—'
  const meses = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  return `${String(dia).padStart(2, '0')} ${meses[mes - 1]} ${anio}`
}

/** Dias que faltan (o sobran) para una fecha, respecto de hoy. */
export function daysUntil(iso: string | null | undefined): number | null {
  if (!iso) return null
  const objetivo = new Date(`${iso.slice(0, 10)}T00:00:00`)
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  return Math.round((objetivo.getTime() - hoy.getTime()) / 86_400_000)
}

export function formatNumber(valor: number): string {
  return valor.toLocaleString('es-CL')
}

export const STAGE_LABEL: Record<Stage, string> = {
  SOSPECHA: 'Sospecha',
  DIAGNOSTICO: 'Diagnóstico',
  TRATAMIENTO: 'Tratamiento',
  SEGUIMIENTO: 'Seguimiento',
}

export const PRIORITY_LABEL: Record<PriorityLevel, string> = {
  CRITICA: 'Crítica',
  ALTA_PRIORIDAD: 'Alta',
  MEDIA_PRIORIDAD: 'Media',
  ESTANDAR: 'Estándar',
}

/**
 * Color del tramo de prioridad. Reutiliza los mismos tonos semanticos de las
 * insignias en vez de introducir una escala nueva: el tablero no deberia
 * ensenarle al usuario dos vocabularios de color distintos.
 */
export const PRIORITY_COLOR: Record<PriorityLevel, string> = {
  CRITICA: 'var(--color-onco)',
  ALTA_PRIORIDAD: 'var(--color-antiguo)',
  MEDIA_PRIORIDAD: 'var(--color-ges)',
  ESTANDAR: 'var(--color-estandar)',
}
