import { computed, ref, watch } from "vue";

export type Theme = "light" | "dark";

const STORAGE_KEY = "theme";

// 全局单例状态(跨组件共享)
const theme = ref<Theme>("light");

function applyTheme(t: Theme) {
  const root = document.documentElement;
  if (t === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

// 立即初始化（模块加载时执行）
const saved = localStorage.getItem(STORAGE_KEY);
if (saved === "dark" || saved === "light") {
  theme.value = saved;
} else {
  theme.value = window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}
applyTheme(theme.value);

// 监听变化并持久化
watch(theme, (t) => {
  applyTheme(t);
  try {
    localStorage.setItem(STORAGE_KEY, t);
  } catch {
    /* ignore */
  }
});

export function useTheme() {
  const isDark = computed(() => theme.value === "dark");

  function toggle() {
    theme.value = theme.value === "dark" ? "light" : "dark";
  }

  function setTheme(t: Theme) {
    theme.value = t;
  }

  return { theme, isDark, toggle, setTheme };
}
