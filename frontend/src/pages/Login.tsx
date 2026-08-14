/**
 * Ingreso al sistema.
 *
 * El acceso es simulado y acepta cualquier credencial. El panel izquierdo no es
 * relleno: muestra la espera real de la red segun el informe BCN de agosto de
 * 2024, dibujada con la misma regla que despues ordena la lista. Quien entra ya
 * sabe contra que se esta midiendo.
 */

import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const SERVICIOS = [
  { value: 'SSMO', label: 'S.S. Metropolitano Oriente' },
  { value: 'SSMS', label: 'S.S. Metropolitano Sur' },
  { value: 'SSMN', label: 'S.S. Metropolitano Norte' },
  { value: 'SSMOC', label: 'S.S. Metropolitano Occidente' },
  { value: 'SSVQ', label: 'S.S. Valparaíso - San Antonio' },
  { value: 'SSCONCEPCION', label: 'S.S. Concepción' },
  { value: 'SS_ARAUCANIA_SUR', label: 'S.S. Araucanía Sur' },
  { value: 'SS_LOS_RIOS', label: 'S.S. Los Ríos' },
]

/** Mediana de espera por especialidad, informe BCN a junio de 2024. */
const ESPERA_REAL = [
  { especialidad: 'Traumatología', dias: 454 },
  { especialidad: 'Cirugía cardiovascular', dias: 415 },
  { especialidad: 'Cirugía digestiva', dias: 318 },
  { especialidad: 'Oftalmología', dias: 268 },
  { especialidad: 'Otorrinolaringología', dias: 259 },
  { especialidad: 'Oncología médica', dias: 92 },
]

const MAXIMO = Math.max(...ESPERA_REAL.map((e) => e.dias))

export function Login() {
  const { ingresar } = useAuth()
  const navigate = useNavigate()
  const ubicacion = useLocation()
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? '/'

  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const [servicio, setServicio] = useState('SSMO')

  function enviar(evento: FormEvent) {
    evento.preventDefault()
    ingresar(usuario.trim() || 'Coordinador de red', servicio)
    navigate(destino, { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col">
      <div className="hazard-strip" aria-hidden="true" />

      <div className="grid flex-1 lg:grid-cols-[1.15fr_1fr]">
        {/* Panel de contexto */}
        <section className="flex flex-col justify-between bg-ink px-6 py-10 text-ground sm:px-10 lg:py-14">
          <div>
            <div className="font-display text-[26px] leading-none font-extrabold tracking-[-0.025em] sm:text-[32px]">
              PROCE<span style={{ color: 'var(--color-onco)' }}>·</span>SALUD
            </div>
            <p className="mt-2 font-display text-[10px] font-bold tracking-[0.18em] text-ink-faint uppercase">
              Priorización dinámica de listas de espera · GES y No GES
            </p>
          </div>

          <div className="my-10 max-w-[520px] lg:my-0">
            <h1 className="font-display text-[24px] leading-[1.15] font-semibold tracking-[-0.02em] sm:text-[30px]">
              2.555.918 personas esperan una consulta de especialidad.
              <span className="text-ink-faint"> El sistema decide a quién atender primero.</span>
            </h1>

            <div className="mt-8">
              <div className="font-display text-[9.5px] font-bold tracking-[0.14em] text-ink-faint uppercase">
                Mediana de espera por especialidad
              </div>

              <ul className="mt-3 space-y-[7px]">
                {ESPERA_REAL.map((fila) => (
                  <li key={fila.especialidad} className="grid grid-cols-[1fr_auto] items-center gap-3">
                    <div className="min-w-0">
                      <div className="mb-[3px] truncate text-[12px] text-ground/80">
                        {fila.especialidad}
                      </div>
                      <div className="h-[3px] w-full bg-white/10">
                        <div
                          className="h-full"
                          style={{
                            width: `${(fila.dias / MAXIMO) * 100}%`,
                            backgroundColor:
                              fila.dias > 300 ? 'var(--color-onco)' : 'rgba(255,255,255,0.45)',
                          }}
                        />
                      </div>
                    </div>
                    <span className="tabular text-[13px] font-medium">{fila.dias} d</span>
                  </li>
                ))}
              </ul>

              <p className="mt-4 text-[10.5px] text-ink-faint">
                Informe Biblioteca del Congreso Nacional, junio 2024. La oncología espera menos
                días — y por eso mismo cada día pesa más.
              </p>
            </div>
          </div>

          <p className="hidden text-[11px] text-ink-faint lg:block">
            Licencia MIT · Datos sintéticos de demostración
          </p>
        </section>

        {/* Formulario */}
        <section className="flex items-center justify-center px-6 py-10 sm:px-10">
          <form onSubmit={enviar} className="w-full max-w-[360px]">
            <h2 className="font-display text-[20px] font-bold tracking-[-0.01em]">
              Ingreso al sistema
            </h2>
            <p className="mt-1.5 text-[13px] text-ink-soft">
              Acceso para coordinadores de red y personal de SOME.
            </p>

            <div className="mt-7 space-y-4">
              <div>
                <label htmlFor="usuario" className="eyebrow mb-1.5 block">
                  Usuario
                </label>
                <input
                  id="usuario"
                  className="field"
                  value={usuario}
                  onChange={(e) => setUsuario(e.target.value)}
                  placeholder="nombre.apellido"
                  autoComplete="username"
                />
              </div>

              <div>
                <label htmlFor="clave" className="eyebrow mb-1.5 block">
                  Contraseña
                </label>
                <input
                  id="clave"
                  type="password"
                  className="field"
                  value={clave}
                  onChange={(e) => setClave(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>

              <div>
                <label htmlFor="servicio" className="eyebrow mb-1.5 block">
                  Servicio de Salud
                </label>
                <select
                  id="servicio"
                  className="field"
                  value={servicio}
                  onChange={(e) => setServicio(e.target.value)}
                >
                  {SERVICIOS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary mt-6 w-full">
              Entrar
            </button>

            <p className="mt-4 border-l-2 border-rule-strong pl-3 text-[11.5px] leading-relaxed text-ink-faint">
              Demostración: cualquier usuario y contraseña dan acceso. No hay autenticación real ni
              datos personales en el sistema.
            </p>
          </form>
        </section>
      </div>
    </div>
  )
}
