import { readFileSync } from 'node:fs'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

const pyproject = readFileSync(
  fileURLToPath(new URL('./pyproject.toml', import.meta.url)),
  'utf-8',
)
const version = pyproject.match(/^version\s*=\s*"([^"]+)"/m)?.[1] ?? '0.0.0'

export default defineConfig({
  root: fileURLToPath(new URL('./src/frontend', import.meta.url)),
  define: {
    __APP_VERSION__: JSON.stringify(version),
  },
  server: {
    host: '127.0.0.1',
    port: 3000,
    proxy: {
      '/v1': 'http://127.0.0.1:8080',
    },
  },
  plugins: [vue(), tailwindcss()],
  build: {
    outDir: fileURLToPath(new URL('./dist', import.meta.url)),
    emptyOutDir: true,
  },
})
