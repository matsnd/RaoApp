import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      { find: '@', replacement: fileURLToPath(new URL('./src', import.meta.url)) },
      // QA workaround: redirect broken import in fakturownia.ts to a stub
      // so vi.mock() can intercept it. Production code still has BUG #1.
      {
        find: /^\.\.\/utils\/api$/,
        replacement: fileURLToPath(new URL('./src/stores/__tests__/__mocks__/api-stub.ts', import.meta.url)),
      },
    ],
  },
  test: {
    environment: 'happy-dom',
    globals: true,
  },
})
