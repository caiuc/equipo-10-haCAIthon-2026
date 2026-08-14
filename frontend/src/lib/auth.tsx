/**
 * Sesion simulada para la demostracion.
 *
 * Acepta cualquier credencial a proposito: el MVP no tiene autenticacion real
 * ni datos que proteger. En una instalacion real esto se reemplaza por Clave
 * Unica o por el directorio del Servicio de Salud, y la API pasa a exigir token.
 */

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

const CLAVE_SESION = 'proce-salud.sesion'

interface Sesion {
  usuario: string
  servicio: string
}

interface AuthContextValue {
  sesion: Sesion | null
  ingresar: (usuario: string, servicio: string) => void
  salir: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

function leerSesion(): Sesion | null {
  try {
    const guardada = sessionStorage.getItem(CLAVE_SESION)
    return guardada ? (JSON.parse(guardada) as Sesion) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(leerSesion)

  const ingresar = useCallback((usuario: string, servicio: string) => {
    const nueva = { usuario, servicio }
    sessionStorage.setItem(CLAVE_SESION, JSON.stringify(nueva))
    setSesion(nueva)
  }, [])

  const salir = useCallback(() => {
    sessionStorage.removeItem(CLAVE_SESION)
    setSesion(null)
  }, [])

  const valor = useMemo(() => ({ sesion, ingresar, salir }), [sesion, ingresar, salir])

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth debe usarse dentro de AuthProvider.')
  return contexto
}
