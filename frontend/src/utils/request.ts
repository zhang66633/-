import axios from "axios";

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 60000,
});

// Attach JWT token to every request
service.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem("mma:token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      /* ignore */
    }
    return config;
  },
  (error) => {
    console.log(error);
    return Promise.reject(error);
  },
);

// 401 全局处理：清会话 + 跳登录入口。
// 排除 /auth/* 接口本身（登录/回调/会话校验返回 401 是正常流程，不应触发跳转），
// 并用模块级标志防多请求并发时重复跳转。
let _authRedirecting = false;

service.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url: string = error?.config?.url ?? "";
    if (status === 401 && !url.includes("/auth") && !_authRedirecting) {
      _authRedirecting = true;
      // 立即清本地会话（token / 持久化聊天记录），后续请求不再携带失效凭据
      try {
        localStorage.removeItem("mma:token");
        localStorage.removeItem("mma-chat-sessions");
        localStorage.removeItem("mma:nickname");
      } catch {
        /* ignore */
      }
      // 清内存态会话（动态 import 防循环依赖；失败也不阻塞跳转）
      import("@/stores/auth")
        .then(({ useAuthStore }) => useAuthStore().logout())
        .catch(() => {});
      // 跳登录入口（登录页不在 /auth 路径下，不会再次触发拦截）
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default service;
export { service as request };
