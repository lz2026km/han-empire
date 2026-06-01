import { defineConfig } from 'vite'

// GitHub Pages base: /han-empire/ (仓库名)
// 静态部署启用 mock 演示数据
export default defineConfig({
  base: '/han-empire/',
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