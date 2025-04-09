import axios from 'axios';

// 从环境变量获取后端 API 地址，或者使用默认值
// 在 .env 文件中设置 VITE_API_BASE_URL=http://localhost:8000 (或其他地址)
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'; // 假设有个 /api/v1 前缀，根据实际情况调整

const apiClient = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
    // 如果需要认证，可以在这里添加，或者使用拦截器动态添加
    // 'Authorization': `Bearer ${token}`
  },
});

// 可选：添加请求拦截器 (例如，动态添加 token)
// apiClient.interceptors.request.use(config => {
//   const token = localStorage.getItem('authToken'); // 示例：从 localStorage 获取 token
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// }, error => {
//   return Promise.reject(error);
// });

// 可选：添加响应拦截器 (例如，统一处理错误)
apiClient.interceptors.response.use(
  response => {
    // 直接返回响应数据部分
    return response;
  },
  error => {
    // 在这里可以做一些全局错误处理，比如 401 跳转登录页等
    console.error('API Error:', error.response || error.message);
    // 拒绝 Promise，让调用方可以 catch
    return Promise.reject(error);
  }
);

export default apiClient;