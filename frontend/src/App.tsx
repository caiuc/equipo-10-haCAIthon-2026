import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { useAuth } from './lib/auth'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Patient } from './pages/Patient'
import { Waitlist } from './pages/Waitlist'

/** Envuelve las rutas del sistema: sin sesion, devuelve al ingreso. */
function Protegida({ children }: { children: React.ReactNode }) {
  const { sesion } = useAuth()
  const ubicacion = useLocation()

  if (!sesion) {
    return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  }
  return <AppShell>{children}</AppShell>
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Protegida>
            <Home />
          </Protegida>
        }
      />
      <Route
        path="/paciente"
        element={
          <Protegida>
            <Patient />
          </Protegida>
        }
      />
      <Route
        path="/lista-espera"
        element={
          <Protegida>
            <Waitlist />
          </Protegida>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
