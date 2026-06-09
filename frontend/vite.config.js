import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy para o backend FastAPI durante o desenvolvimento
    proxy: {
      '/analisar':  'http://localhost:8000',
      '/base':      'http://localhost:8000',
      '/health':    'http://localhost:8000',
    },
  },
})
