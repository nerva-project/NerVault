import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  root: fileURLToPath(new URL('./src/frontend', import.meta.url)),
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
