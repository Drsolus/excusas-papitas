import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// GitHub Pages project site: https://drsolus.github.io/excusas-papitas/
export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? '/excusas-papitas/' : '/',
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 4321,
    strictPort: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 4321,
    strictPort: true,
  },
}))
