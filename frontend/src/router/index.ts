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
        meta: { keepAlive: true },
      },
      {
        path: "chat",
        component: () => import("@/pages/chat/index.vue"),
        meta: { keepAlive: true },
      },
      {
        path: "teach",
        component: () => import("@/pages/teach/index.vue"),
        meta: { keepAlive: true },
      },
      {
        path: "solution",
        component: () => import("@/pages/solution/index.vue"),
        meta: { keepAlive: true },
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
      // ── 学习系统 (新增) ──
      {
        path: "learn",
        component: () => import("@/pages/learn/index.vue"),
      },
      {
        path: "learn/:unitId",
        component: () => import("@/pages/learn/[unitId].vue"),
      },
      {
        path: "practice",
        component: () => import("@/pages/practice/index.vue"),
      },
      {
        path: "qa",
        component: () => import("@/pages/qa/index.vue"),
      },
      {
        path: "progress",
        component: () => import("@/pages/progress/index.vue"),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
