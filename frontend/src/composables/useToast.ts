import { readonly, ref } from "vue";

export type ToastType = "success" | "error" | "info";

export interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
}

// 模块级单例: 任何组件/模块都能直接调用 toast(),由全局 ToastHost 统一渲染
const toasts = ref<ToastItem[]>([]);
let nextId = 1;
let recentKey = "";
let recentAt = 0;

function removeToast(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id);
}

/** 全局轻量提示(success 2.6s / error 4s 自动消失;500ms 内重复消息去重) */
export function toast(message: string, type: ToastType = "info") {
  const key = `${type}:${message}`;
  const now = Date.now();
  if (key === recentKey && now - recentAt < 500) return;
  recentKey = key;
  recentAt = now;

  const id = nextId++;
  toasts.value.push({ id, type, message });
  const duration = type === "error" ? 4000 : 2600;
  setTimeout(() => removeToast(id), duration);
}

/** 供 ToastHost 读取(只读) */
export function useToast() {
  return { toasts: readonly(toasts) };
}
