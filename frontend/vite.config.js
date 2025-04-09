// frontend/vite.config.js
import {fileURLToPath, URL} from 'node:url'

import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

// --- 如果使用 Element Plus 按需导入 (可选) ---
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
// -----------------------------------------

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        // --- 如果使用 Element Plus 按需导入 (可选) ---
        AutoImport({
          resolvers: [ElementPlusResolver()],
        }),
        Components({
          resolvers: [ElementPlusResolver()],
        }),
        // -----------------------------------------
    ],
    resolve: {
        alias: {
            // 设置 `@` 指向 `src` 目录
            '@': fileURLToPath(new URL('./src', import.meta.url)) // 根据你的实际 src 路径调整
        }
    },
    server: {
        port: 3333, // 开发服务器端口 (可以自定义)
        host: '0.0.0.0', // 允许局域网访问开发服务器
        proxy: {
            // 配置 API 代理，解决开发环境跨域问题
            '/api': { // 以前端请求路径 /api 开头的都转发
                target: 'http://localhost:8000', // 后端 FastAPI 服务器地址
                changeOrigin: true, // 需要虚拟主机站点
                // 可选：如果后端 API 路径不带 /api 前缀，可以在这里重写
                // rewrite: (path) => path.replace(/^\/api/, '')
            }
            // 可以添加更多代理规则
            // '/other-api': { ... }
        }
    },
    build: {
        outDir: 'dist', // 构建输出目录
        sourcemap: process.env.NODE_ENV !== 'production', // 生产环境禁用 SourceMap，开发构建时开启
        rollupOptions: {
            // 可以进行更细粒度的 Rollup 配置
            output: {
                // 尝试将较大的库分割成单独的 chunk
                manualChunks(id) {
                    if (id.includes('node_modules')) {
                        // 将 Element Plus 单独打包 (如果使用)
                        if (id.toString().includes('element-plus')) {
                            return 'vendor_element-plus';
                        }
                        // 可以添加更多规则来分割其他大型库
                        return 'vendor'; // 其他第三方库打包到 vendor
                    }
                }
            }
        }
    },
    // --- 如果使用 CSS 预处理器 (可选) ---
    // css: {
    //   preprocessorOptions: {
    //     scss: {
    //       additionalData: `@import "@/assets/styles/variables.scss";` // 示例：全局导入 SCSS 变量
    //     }
    //   }
    // }
})