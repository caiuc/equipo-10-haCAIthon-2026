/** Marco comun: cabecera institucional con la cinta de alerta sanitaria. */

import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const NAV = [
  { to: '/', label: 'Inicio', end: true },
  { to: '/paciente', label: 'Ingreso de paciente', end: false },
  { to: '/lista-espera', label: 'Lista de espera', end: false },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const { sesion, salir } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col">
      <div className="hazard-strip" aria-hidden="true" />

      <header className="bg-ink text-ground">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
          <Link to="/" className="group flex items-baseline gap-2.5">
            <span className="font-display text-[19px] leading-none font-extrabold tracking-[-0.02em]">
              PROCE<span style={{ color: 'var(--color-onco)' }}>·</span>SALUD
            </span>
            <span className="hidden font-display text-[9.5px] font-bold tracking-[0.16em] text-ink-faint uppercase sm:inline">
              Priorización de listas de espera
            </span>
          </Link>

          <nav className="order-3 -mb-3 flex w-full gap-0 sm:order-none sm:mb-0 sm:w-auto">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  [
                    'border-b-2 px-3 py-2 font-display text-[11px] font-bold tracking-[0.07em] uppercase transition-colors',
                    isActive
                      ? 'border-onco text-ground'
                      : 'border-transparent text-ink-faint hover:text-ground',
                  ].join(' ')
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          {sesion && (
            <div className="ml-auto flex items-center gap-3">
              <div className="text-right leading-tight">
                <div className="tabular text-[12px] font-medium">{sesion.usuario}</div>
                <div className="font-display text-[9px] font-bold tracking-[0.1em] text-ink-faint uppercase">
                  {sesion.servicio}
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  salir()
                  navigate('/login', { replace: true })
                }}
                className="font-display text-[10px] font-bold tracking-[0.08em] text-ink-faint uppercase underline decoration-1 underline-offset-3 hover:text-ground"
              >
                Salir
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Contexto normativo vigente: no es decoracion, es el marco que explica
          por que los pacientes oncologicos suben en el ranking. */}
      <div className="border-b border-rule bg-surface">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center gap-x-3 gap-y-1 px-4 py-1.5 sm:px-6">
          <span
            className="h-[7px] w-[7px] shrink-0 rounded-full"
            style={{ backgroundColor: 'var(--color-onco)' }}
            aria-hidden="true"
          />
          <span className="font-display text-[9.5px] font-bold tracking-[0.12em] uppercase">
            Alerta sanitaria oncológica vigente
          </span>
          <span className="text-[11px] text-ink-soft">
            Decreto N° 18 / abril 2026 · Subsecretaría de Redes Asistenciales
          </span>
        </div>
      </div>

      <main className="mx-auto w-full max-w-[1240px] flex-1 px-4 py-6 sm:px-6 sm:py-8">
        {children}
      </main>

      <footer className="border-t border-rule">
        <div className="mx-auto flex max-w-[1240px] flex-wrap gap-x-5 gap-y-1 px-4 py-4 text-[11px] text-ink-faint sm:px-6">
          <span>PROCE-SALUD · API open-source bajo licencia MIT</span>
          <span className="hidden sm:inline">·</span>
          <span>Datos sintéticos de demostración. Ningún registro corresponde a una persona real.</span>
        </div>
      </footer>
    </div>
  )
}
