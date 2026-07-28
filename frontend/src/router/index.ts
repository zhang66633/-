import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import AppLayout from "@/components/AppLayout.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    component: () => import("@/pages/login/index.vue"),
  },
  {
    path: "/auth/callback",
    component: () => import("@/pages/auth/callback.vue"),
  },
  // 内页统一套 AppLayout
  {
    path: "/",
    component: AppLayout,
    children: [
      {
        path: "",
        component: () => import("@/pages/index.vue"),
      },
      {
        path: "chat",
        component: () => import("@/pages/chat/index.vue"),
      },
      {
        path: "teach",
        component: () => import("@/pages/teach/index.vue"),
      },
      {
        path: "solution",
        component: () => import("@/pages/solution/index.vue"),
      },
      {
        path: "archive/:id",
        component: () => import("@/pages/archive/[id].vue"),
        props: true,
      },
      {
        path: "knowledge",
        component: () => import("@/pages/knowledge/index.vue"),
      },
      {
        path: "apikeys",
        component: () => import("@/pages/apikeys/index.vue"),
      },
      {
        path: "settings",
        component: () => import("@/pages/settings/index.vue"),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
