import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "VITE_");
  const backendPort = env.VITE_BACKEND_PORT || "8000";

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
    },
    server: {
      port: 5174,
      // 开发期强制不缓存: 部分浏览器(360/搜狗/Edge 增强缓存)会忽略 no-cache
      // 导致「框架是旧的、资料空白」类问题,no-store 从根上禁止复用缓存
      headers: {
        "Cache-Control": "no-store",
      },
      proxy: {
        "/api": {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true,
          ws: true,
        },
      },
      hmr: {
        overlay: false,
      },
    },
  };
});
