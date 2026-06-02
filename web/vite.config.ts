import { defineConfig } from 'vite'

// 本地桌面 EXE: base = './' (相对路径, 让 pywebview/file:// 也能找到), GitHub Pages: '/han-empire/'
export default defineConfig({
  base: './',
  // GitHub Pages 静态部署 = 演示模式 (无后端)
  env: {
    VITE_DEMO_MODE: 'true',
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      external: [],
    },
  },
  esbuild: {
    jsx: 'automatic',
  },
})