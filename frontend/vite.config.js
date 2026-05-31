import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  define: {
    VITE_BACKEND_URL: JSON.stringify(`${process.env.VITE_BACKEND_URL}`),
  },
  server: {
    port: 5173,
    proxy: {
      '/predict': 'http://localhost:8000',
      '/scans': 'http://localhost:8000'
    }
  }
})
