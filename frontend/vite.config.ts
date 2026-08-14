import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      // En desarrollo la API corre aparte. El proxy evita tener que levantar
      // CORS local y mantiene las rutas identicas a las de produccion.
      proxy: {
        '/api': {
          target: env.VITE_DEV_API || 'http://127.0.0.1:8077',
          changeOrigin: true,
        },
      },
    },
  }
})
