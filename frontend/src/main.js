// frontend/src/main.js

import { createApp } from 'vue';
import App from './App.vue'; // 引入根组件
import router from './router'; // 引入路由配置 (我们将在下一步创建它)
import { createPinia } from 'pinia'; // 引入 Pinia
import ElementPlus from 'element-plus' // If using Element Plus
import 'element-plus/dist/index.css'  // Element Plus styles
import './axios'; // 引入 Axios 配置 (假设你创建了 src/axios.js 来配置 baseURL 等)

// 引入全局样式 (根据你的文件结构调整路径)
// 例如: import './assets/main.css'; 或 import './index.css';
import './style.css'; // 假设你的全局样式在 src/style.css

// 创建 Pinia 实例
const pinia = createPinia();

// 创建 Vue 应用实例
const app = createApp(App);

// 使用 Pinia
app.use(pinia);

// 使用路由
app.use(router);

app.use(ElementPlus)  // Use Element Plus

// 挂载应用到 DOM
// 确保你的 public/index.html 中有一个 <div id="app"></div>
app.mount('#app');