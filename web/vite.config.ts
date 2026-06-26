import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'
import path from 'node:path'

export default defineConfig({
  plugins: [
    vue(),
    Components({
      resolvers: [AntDesignVueResolver({ importStyle: false })],
      dts: 'src/types/components.d.ts',
    }),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 4173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2020',
    sourcemap: false,
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 拆分第三方依赖，改善长效缓存命中与首屏：业务代码更新时 vendor chunk 不失效
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return
          if (id.includes('ant-design-vue') || id.includes('@ant-design')) return 'antdv'
          if (
            id.includes('node_modules/vue/') ||
            id.includes('node_modules/vue-router/') ||
            id.includes('node_modules/pinia/') ||
            id.includes('node_modules/@vue/')
          ) {
            return 'vue'
          }
          return 'vendor'
        },
      },
    },
  },
})
