import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  base: '/rao/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // RAO-P3-002: proxy logo firmy w dev (prod: nginx obsługuje /rao/api/static)
      // UWAGA: musi być PRZED ogólnym /rao/api — Vite dopasowuje najdłuższy prefix
      '/rao/api/static': {
        target: 'http://localhost:8000',
        rewrite: (path: string) => path.replace('/rao/api', ''),
      },
      // Proxy dla całego API — strip /rao/api prefix (backend serwuje pod /contracts, /stats, etc.)
      // Dev odpowiednik nginx reverse proxy z produkcji
      '/rao/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/rao\/api/, ''),
      },
    },
  },
})
