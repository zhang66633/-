/**
 * 工具渲染器注册表 — 按 tool_name 映射到异步 Vue 组件
 *
 * 未注册的工具自动回退到 GenericRenderer。
 * 每个渲染器接收 { input, output, status } 三个 props。
 */
import type { Component } from "vue";

const toolRendererMap: Record<string, () => Promise<Component>> = {
  run_code: () => import("./renderers/RunCodeRenderer.vue"),
  web_search: () => import("./renderers/SearchRenderer.vue"),
  search_method_cards: () => import("./renderers/SearchRenderer.vue"),
  search_similar_papers: () => import("./renderers/SearchRenderer.vue"),
  get_analysis_template: () => import("./renderers/SearchRenderer.vue"),
  sympy_compute: () => import("./renderers/MathRenderer.vue"),
  solve_optimization: () => import("./renderers/MathRenderer.vue"),
};

/** 根据 tool_name 获取渲染器加载函数，未注册返回 null */
export function getToolRenderer(
  toolName: string,
): (() => Promise<Component>) | null {
  return toolRendererMap[toolName] ?? null;
}
