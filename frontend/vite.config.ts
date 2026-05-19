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
      '/rao/api/static': {
        target: 'http://localhost:8000',
        rewrite: (path: string) => path.replace('/rao/api', ''),
      },
    },
  },
})
