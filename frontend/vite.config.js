import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': { target: 'http://localhost:8001', changeOrigin: true },
      '/inventario': { target: 'http://localhost:8002', changeOrigin: true },
      '/ventas': { target: 'http://localhost:8003', changeOrigin: true },
      '/compras': { target: 'http://localhost:8004', changeOrigin: true },
      '/analisis': { target: 'http://localhost:8005', changeOrigin: true },
    },
  },
})
