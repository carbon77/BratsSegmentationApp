import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
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
