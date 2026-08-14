<script setup lang="ts">
import type { ToolStatus } from "@/types/response";
import { CheckCircle2, Loader2, XCircle } from "lucide-vue-next";
/**
 * 工具状态指示器 — 紧凑的状态徽章
 *
 * 三种状态：
 *   running → 旋转 Loader2 + "执行中"（amber）
 *   success → CheckCircle2 + "完成"（emerald）
 *   error   → XCircle + "失败"（rose）
 */
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    status?: ToolStatus;
  }>(),
  {
    status: undefined,
  },
);

const config = computed(() => {
  switch (props.status) {
    case "running":
      return {
        icon: Loader2,
        label: "执行中",
        iconClass: "animate-spin",
        badgeClass:
          "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800",
      };
    case "success":
      return {
        icon: CheckCircle2,
        label: "完成",
        iconClass: "",
        badgeClass:
          "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800",
      };
    case "error":
      return {
        icon: XCircle,
        label: "失败",
        iconClass: "",
        badgeClass:
          "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-800",
      };
    default:
      return null;
  }
});
</script>

<template>
  <span
    v-if="config"
    class="inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider shrink-0"
    :class="config.badgeClass"
  >
    <component :is="config.icon" class="h-2.5 w-2.5" :class="config.iconClass" />
    <span>{{ config.label }}</span>
  </span>
</template>